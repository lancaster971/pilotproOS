/**
 * Settings Service - Sistema avanzato per gestione configurazioni frontend remoto
 * 
 * Features:
 * - Auto-discovery backend endpoints
 * - Real-time connectivity validation
 * - localStorage cache per configurazioni
 * - Fallback e recovery automatico
 */

export interface BackendEndpoint {
  url: string;
  status: 'online' | 'offline' | 'checking';
  responseTime?: number;
  version?: string;
  features?: string[];
  lastChecked?: Date;
}

export interface ConnectionSettings {
  primaryBackend: string;
  fallbackBackends: string[];
  timeout: number;
  retryAttempts: number;
  autoDiscovery: boolean;
  healthCheckInterval: number;
}

export class SettingsService {
  private static instance: SettingsService;
  private settings: ConnectionSettings;
  private endpoints: Map<string, BackendEndpoint> = new Map();
  private healthCheckInterval?: NodeJS.Timeout;

  constructor() {
    this.settings = this.loadSettings();
    this.startHealthChecks();
  }

  static getInstance(): SettingsService {
    if (!SettingsService.instance) {
      SettingsService.instance = new SettingsService();
    }
    return SettingsService.instance;
  }

  /**
   * Carica settings da localStorage con fallback
   */
  private loadSettings(): ConnectionSettings {
    try {
      const stored = localStorage.getItem('pilotpro_settings');
      if (stored) {
        return { ...this.getDefaultSettings(), ...JSON.parse(stored) };
      }
    } catch (error) {
      console.warn('Errore caricamento settings da localStorage:', error);
    }
    
    return this.getDefaultSettings();
  }

  /**
   * Salva settings in localStorage
   */
  private saveSettings(): void {
    try {
      localStorage.setItem('pilotpro_settings', JSON.stringify(this.settings));
    } catch (error) {
      console.error('Errore salvataggio settings:', error);
    }
  }

  /**
   * Settings di default
   */
  private getDefaultSettings(): ConnectionSettings {
    return {
      primaryBackend: 'http://localhost:3001',
      fallbackBackends: ['http://localhost:3002', 'http://127.0.0.1:3001'],
      timeout: 5000,
      retryAttempts: 3,
      autoDiscovery: true,
      healthCheckInterval: 30000 // 30 secondi
    };
  }

  /**
   * Auto-discovery di backend disponibili
   */
  async discoverBackends(baseUrls: string[] = []): Promise<BackendEndpoint[]> {
    const urlsToTest = [
      ...baseUrls,
      ...this.settings.fallbackBackends,
      this.settings.primaryBackend
    ];

    // Rimuovi duplicati
    const uniqueUrls = Array.from(new Set(urlsToTest));
    
    const discoveries = await Promise.allSettled(
      uniqueUrls.map(url => this.checkEndpoint(url))
    );

    const availableEndpoints: BackendEndpoint[] = [];
    
    discoveries.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        availableEndpoints.push(result.value);
      } else {
        availableEndpoints.push({
          url: uniqueUrls[index],
          status: 'offline',
          lastChecked: new Date()
        });
      }
    });

    return availableEndpoints;
  }

  /**
   * Check singolo endpoint con dettagli
   */
  async checkEndpoint(url: string): Promise<BackendEndpoint> {
    const startTime = Date.now();
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.settings.timeout);

      const response = await fetch(`${url}/health`, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          'User-Agent': 'PilotPro-Frontend-Discovery/1.0'
        }
      });

      clearTimeout(timeoutId);
      const responseTime = Date.now() - startTime;

      if (response.ok) {
        const data = await response.json();
        
        const endpoint: BackendEndpoint = {
          url,
          status: 'online',
          responseTime,
          version: data.version || 'unknown',
          features: data.features || [],
          lastChecked: new Date()
        };

        this.endpoints.set(url, endpoint);
        return endpoint;
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error: any) {
      const endpoint: BackendEndpoint = {
        url,
        status: 'offline',
        responseTime: Date.now() - startTime,
        lastChecked: new Date()
      };

      this.endpoints.set(url, endpoint);
      return endpoint;
    }
  }

  /**
   * Ottieni il miglior backend disponibile
   */
  async getBestBackend(): Promise<string> {
    // Controlla primary backend
    const primaryEndpoint = await this.checkEndpoint(this.settings.primaryBackend);
    if (primaryEndpoint.status === 'online') {
      return this.settings.primaryBackend;
    }

    // Prova fallbacks
    for (const fallbackUrl of this.settings.fallbackBackends) {
      const endpoint = await this.checkEndpoint(fallbackUrl);
      if (endpoint.status === 'online') {
        return fallbackUrl;
      }
    }

    // Nessun backend disponibile, restituisci primary comunque
    return this.settings.primaryBackend;
  }

  /**
   * Aggiorna configurazione connessione
   */
  updateConnectionSettings(newSettings: Partial<ConnectionSettings>): void {
    this.settings = { ...this.settings, ...newSettings };
    this.saveSettings();
    
    // Riavvia health checks se interval è cambiato
    if (newSettings.healthCheckInterval) {
      this.stopHealthChecks();
      this.startHealthChecks();
    }
  }

  /**
   * Ottieni settings correnti
   */
  getSettings(): ConnectionSettings {
    return { ...this.settings };
  }

  /**
   * Ottieni stato endpoint
   */
  getEndpoints(): BackendEndpoint[] {
    return Array.from(this.endpoints.values());
  }

  /**
   * Avvia health checks periodici
   */
  private startHealthChecks(): void {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }

    this.healthCheckInterval = setInterval(async () => {
      if (this.settings.autoDiscovery) {
        await this.discoverBackends();
      }
    }, this.settings.healthCheckInterval);
  }

  /**
   * Ferma health checks
   */
  private stopHealthChecks(): void {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = undefined;
    }
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    this.stopHealthChecks();
  }
}

// Service singleton
export const settingsService = SettingsService.getInstance();