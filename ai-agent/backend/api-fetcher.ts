/**
 * API Fetcher
 * 
 * Wrapper per chiamate all'API n8n con rate limiting,
 * retry logic e gestione paginazione.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { SyncConfig, calculateRetryDelay } from './sync-config.js';
import { getEnvConfig } from '../config/environment.js';

/**
 * Risposta paginata da n8n API
 */
interface PaginatedResponse<T> {
  data: T[];
  nextCursor?: string;
}

/**
 * Rate limiter semplice
 */
class RateLimiter {
  private requests: number[] = [];
  private maxPerSecond: number;
  
  constructor(maxPerSecond: number) {
    this.maxPerSecond = maxPerSecond;
  }
  
  async throttle(): Promise<void> {
    const now = Date.now();
    const oneSecondAgo = now - 1000;
    
    // Rimuovi richieste vecchie
    this.requests = this.requests.filter(time => time > oneSecondAgo);
    
    // Se abbiamo raggiunto il limite, aspetta
    if (this.requests.length >= this.maxPerSecond) {
      const oldestRequest = this.requests[0];
      const waitTime = 1000 - (now - oldestRequest) + 100; // +100ms buffer
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
    
    this.requests.push(Date.now());
  }
}

/**
 * Classe per gestire chiamate API n8n
 */
export class ApiFetcher {
  private client: AxiosInstance;
  private rateLimiter: RateLimiter;
  private config: SyncConfig;
  
  constructor(config: SyncConfig) {
    this.config = config;
    const envConfig = getEnvConfig();
    
    // Inizializza client axios
    this.client = axios.create({
      baseURL: envConfig.n8nApiUrl,
      timeout: config.performance.requestTimeout,
      headers: {
        'X-N8N-API-KEY': envConfig.n8nApiKey,
        'Content-Type': 'application/json'
      }
    });
    
    // Inizializza rate limiter
    this.rateLimiter = new RateLimiter(config.performance.rateLimitPerSecond);
    
    // Interceptor per logging
    this.setupInterceptors();
  }
  
  /**
   * Configura interceptors per request/response
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      async (config) => {
        // Applica rate limiting
        await this.rateLimiter.throttle();
        
        // Log richiesta
        console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
        
        return config;
      },
      (error) => {
        console.error('❌ Request error:', error);
        return Promise.reject(error);
      }
    );
    
    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        console.log(`✅ API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error: AxiosError) => {
        console.error(`❌ API Error: ${error.response?.status} ${error.config?.url}`);
        return Promise.reject(error);
      }
    );
  }
  
  /**
   * Esegue chiamata con retry logic
   */
  private async executeWithRetry<T>(
    operation: () => Promise<T>,
    retryCount: number = 0
  ): Promise<T> {
    try {
      return await operation();
    } catch (error) {
      const axiosError = error as AxiosError;
      
      // Non fare retry per errori client (4xx)
      if (axiosError.response && axiosError.response.status >= 400 && axiosError.response.status < 500) {
        throw error;
      }
      
      // Verifica se possiamo fare retry
      if (retryCount < this.config.limits.maxRetries) {
        const delay = calculateRetryDelay(retryCount, this.config);
        console.log(`⏳ Retry ${retryCount + 1}/${this.config.limits.maxRetries} dopo ${delay}ms`);
        
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.executeWithRetry(operation, retryCount + 1);
      }
      
      throw error;
    }
  }
  
  /**
   * Ottiene lista di tutti i workflow
   */
  async getWorkflows(limit?: number): Promise<any[]> {
    return this.executeWithRetry(async () => {
      const params: any = {};
      if (limit) params.limit = limit;
      
      const response = await this.client.get('/workflows', { params });
      return response.data.data || [];
    });
  }
  
  /**
   * Ottiene dettagli completi di un workflow
   */
  async getWorkflowDetails(workflowId: string): Promise<any> {
    return this.executeWithRetry(async () => {
      const response = await this.client.get(`/workflows/${workflowId}`);
      return response.data;
    });
  }
  
  /**
   * Ottiene workflow modificati dopo una data
   */
  async getWorkflowsModifiedAfter(date: Date, limit?: number): Promise<any[]> {
    // n8n API non supporta filtro per data, quindi prendiamo tutti
    // e filtriamo lato client (non ottimale ma necessario)
    const workflows = await this.getWorkflows(limit);
    
    return workflows.filter(w => {
      const updatedAt = new Date(w.updatedAt);
      return updatedAt > date;
    });
  }
  
  /**
   * Ottiene lista di esecuzioni
   */
  async getExecutions(options?: {
    workflowId?: string;
    status?: string;
    limit?: number;
    cursor?: string;
  }): Promise<PaginatedResponse<any>> {
    return this.executeWithRetry(async () => {
      const params: any = {};
      
      if (options?.workflowId) params.workflowId = options.workflowId;
      if (options?.status) params.status = options.status;
      if (options?.limit) params.limit = options.limit;
      if (options?.cursor) params.cursor = options.cursor;
      
      const response = await this.client.get('/executions', { params });
      
      return {
        data: response.data.data || [],
        nextCursor: response.data.nextCursor
      };
    });
  }
  
  /**
   * Ottiene dettagli di un'esecuzione
   */
  async getExecutionDetails(executionId: string): Promise<any> {
    return this.executeWithRetry(async () => {
      const response = await this.client.get(`/executions/${executionId}`);
      return response.data;
    });
  }
  
  /**
   * Ottiene esecuzioni recenti (ultime N ore)
   */
  async getRecentExecutions(hours: number = 1, limit: number = 100): Promise<any[]> {
    // Fetch esecuzioni e filtra per tempo
    const cutoffTime = new Date(Date.now() - hours * 60 * 60 * 1000);
    const result = await this.getExecutions({ limit });
    
    return result.data.filter(e => {
      const startedAt = new Date(e.startedAt);
      return startedAt > cutoffTime;
    });
  }
  
  /**
   * Ottiene tutte le esecuzioni con paginazione
   */
  async getAllExecutions(
    options?: {
      workflowId?: string;
      status?: string;
      maxTotal?: number;
    },
    onBatch?: (executions: any[]) => Promise<void>
  ): Promise<any[]> {
    const allExecutions: any[] = [];
    let cursor: string | undefined;
    let totalFetched = 0;
    const batchSize = 100;
    const maxTotal = options?.maxTotal || this.config.limits.maxExecutionsPerSync;
    
    do {
      // Fetch batch
      const response = await this.getExecutions({
        workflowId: options?.workflowId,
        status: options?.status,
        limit: batchSize,
        cursor
      });
      
      // Processa batch se callback fornito
      if (onBatch) {
        await onBatch(response.data);
      } else {
        allExecutions.push(...response.data);
      }
      
      totalFetched += response.data.length;
      cursor = response.nextCursor;
      
      // Controlla limite
      if (totalFetched >= maxTotal) {
        console.log(`📊 Raggiunto limite di ${maxTotal} esecuzioni`);
        break;
      }
      
    } while (cursor);
    
    return allExecutions;
  }
  
  /**
   * Ottiene statistiche aggregate (se disponibili)
   */
  async getStats(): Promise<any> {
    try {
      // Endpoint potrebbe non esistere in tutte le versioni n8n
      const response = await this.client.get('/stats');
      return response.data;
    } catch (error) {
      console.warn('⚠️ Stats endpoint non disponibile');
      return null;
    }
  }
  
  /**
   * Test connessione API
   */
  async testConnection(): Promise<boolean> {
    try {
      await this.executeWithRetry(async () => {
        const response = await this.client.get('/workflows', { 
          params: { limit: 1 } 
        });
        return response.data;
      });
      
      console.log('✅ Connessione API n8n verificata');
      return true;
    } catch (error) {
      console.error('❌ Connessione API n8n fallita:', error);
      return false;
    }
  }
  
  /**
   * Ottiene metriche utilizzo API
   */
  getApiMetrics(): {
    totalCalls: number;
    failedCalls: number;
    avgResponseTime: number;
  } {
    // TODO: Implementare tracking metriche
    return {
      totalCalls: 0,
      failedCalls: 0,
      avgResponseTime: 0
    };
  }
}