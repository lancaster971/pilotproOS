/**
 * Sync Service Configuration
 * 
 * Configurazione per il servizio di sincronizzazione backend.
 * Definisce intervalli, limiti e parametri di performance.
 */

/**
 * Configurazione del servizio di sincronizzazione
 */
export interface SyncConfig {
  // Intervalli di sincronizzazione (in secondi)
  intervals: {
    executions: number;        // Sync esecuzioni (default: 60s)
    workflows: number;         // Sync workflow (default: 300s)
    fullSync: number;         // Full sync (default: 3600s)
    kpiHourly: number;        // KPI orari (default: 3600s)
    kpiDaily: number;         // KPI giornalieri (default: 86400s)
    cleanup: number;          // Pulizia dati vecchi (default: 86400s)
  };
  
  // Limiti per operazione
  limits: {
    maxWorkflowsPerSync: number;     // Max workflow per sync
    maxExecutionsPerSync: number;    // Max esecuzioni per sync
    maxRetries: number;              // Max tentativi retry
    retryDelayMs: number;            // Delay base per retry (ms)
    maxRetryDelayMs: number;         // Max delay retry (ms)
  };
  
  // Performance tuning
  performance: {
    batchSize: number;               // Record per batch
    parallelWorkers: number;         // Worker paralleli
    rateLimitPerSecond: number;      // Rate limit API calls/sec
    connectionTimeout: number;       // Timeout connessione (ms)
    requestTimeout: number;          // Timeout richiesta (ms)
  };
  
  // Feature flags
  features: {
    incrementalSync: boolean;        // Abilita sync incrementale
    smartPriority: boolean;          // Priorità intelligente
    adaptiveInterval: boolean;       // Intervalli adattivi
    errorRecovery: boolean;          // Recovery automatico errori
    metricsCollection: boolean;      // Raccolta metriche sync
    healthCheck: boolean;            // Health check endpoint
  };
  
  // Data retention
  retention: {
    executionsDays: number;          // Giorni retention esecuzioni
    kpiSnapshotsDays: number;        // Giorni retention KPI
    errorLogsDays: number;           // Giorni retention error logs
    auditLogsDays: number;           // Giorni retention audit logs
  };
}

/**
 * Configurazione di default
 */
export const defaultSyncConfig: SyncConfig = {
  intervals: {
    executions: 60,              // 1 minuto
    workflows: 300,              // 5 minuti
    fullSync: 3600,             // 1 ora
    kpiHourly: 3600,            // 1 ora
    kpiDaily: 86400,            // 24 ore
    cleanup: 86400              // 24 ore
  },
  
  limits: {
    maxWorkflowsPerSync: 100,
    maxExecutionsPerSync: 500,
    maxRetries: 3,
    retryDelayMs: 1000,
    maxRetryDelayMs: 30000
  },
  
  performance: {
    batchSize: 50,
    parallelWorkers: 5,
    rateLimitPerSecond: 10,
    connectionTimeout: 5000,
    requestTimeout: 30000
  },
  
  features: {
    incrementalSync: true,
    smartPriority: true,
    adaptiveInterval: false,
    errorRecovery: true,
    metricsCollection: true,
    healthCheck: true
  },
  
  retention: {
    executionsDays: 30,
    kpiSnapshotsDays: 90,
    errorLogsDays: 7,
    auditLogsDays: 365
  }
};

/**
 * Priorità di sincronizzazione
 */
export enum SyncPriority {
  CRITICAL = 'critical',    // Sync immediato
  HIGH = 'high',            // Alta priorità
  MEDIUM = 'medium',        // Media priorità
  LOW = 'low'              // Bassa priorità
}

/**
 * Stati del processo di sync
 */
export enum SyncStatus {
  IDLE = 'idle',                   // In attesa
  RUNNING = 'running',             // In esecuzione
  COMPLETED = 'completed',         // Completato
  FAILED = 'failed',              // Fallito
  PARTIAL = 'partial',            // Parzialmente completato
  CANCELLED = 'cancelled'         // Cancellato
}

/**
 * Tipi di sincronizzazione
 */
export enum SyncType {
  INCREMENTAL = 'incremental',     // Solo modifiche
  FULL = 'full',                  // Completo
  FORCED = 'forced',              // Forzato (ignora cache)
  RECOVERY = 'recovery'           // Recovery dopo errore
}

/**
 * Risultato di un'operazione di sync
 */
export interface SyncResult {
  type: SyncType;
  status: SyncStatus;
  startTime: Date;
  endTime?: Date;
  duration_ms?: number;
  
  // Statistiche
  stats: {
    workflowsProcessed: number;
    workflowsCreated: number;
    workflowsUpdated: number;
    workflowsFailed: number;
    
    executionsProcessed: number;
    executionsCreated: number;
    executionsUpdated: number;
    executionsFailed: number;
    
    totalApiCalls: number;
    totalDbOperations: number;
  };
  
  // Errori
  errors: Array<{
    entity: string;
    entityId: string;
    error: string;
    timestamp: Date;
  }>;
  
  // Metadata
  metadata?: Record<string, any>;
}

/**
 * Stato della sincronizzazione
 */
export interface SyncState {
  lastWorkflowSync?: Date;         // Ultimo sync workflow
  lastExecutionSync?: Date;        // Ultimo sync esecuzioni
  lastFullSync?: Date;             // Ultimo full sync
  lastKpiCalculation?: Date;       // Ultimo calcolo KPI
  
  // Checkpoint per recovery
  lastProcessedWorkflowId?: string;
  lastProcessedExecutionId?: string;
  
  // Contatori
  totalSyncs: number;
  successfulSyncs: number;
  failedSyncs: number;
  
  // Stato corrente
  currentSync?: {
    type: SyncType;
    status: SyncStatus;
    startTime: Date;
    progress: number;  // Percentuale 0-100
  };
  
  // Errori pendenti per retry
  pendingRetries: Array<{
    entityType: 'workflow' | 'execution';
    entityId: string;
    retryCount: number;
    lastError: string;
    nextRetryAt: Date;
  }>;
}

/**
 * Metriche di performance del sync
 */
export interface SyncMetrics {
  // Timing
  avgSyncDuration_ms: number;
  minSyncDuration_ms: number;
  maxSyncDuration_ms: number;
  
  // Throughput
  recordsPerSecond: number;
  apiCallsPerMinute: number;
  
  // Affidabilità
  successRate: number;
  errorRate: number;
  retryRate: number;
  
  // Risorse
  avgMemoryUsage_mb: number;
  avgCpuUsage_percent: number;
  
  // Coda
  queueSize: number;
  queueDelay_ms: number;
}

/**
 * Helper per calcolare delay con exponential backoff
 */
export function calculateRetryDelay(
  retryCount: number, 
  config: SyncConfig
): number {
  const delay = Math.min(
    config.limits.retryDelayMs * Math.pow(2, retryCount),
    config.limits.maxRetryDelayMs
  );
  
  // Aggiungi jitter per evitare thundering herd
  const jitter = Math.random() * 0.3 * delay;
  return Math.floor(delay + jitter);
}

/**
 * Helper per determinare se è necessario un sync
 */
export function shouldSync(
  lastSync: Date | undefined,
  intervalSeconds: number
): boolean {
  if (!lastSync) return true;
  
  const now = Date.now();
  const lastSyncTime = lastSync.getTime();
  const intervalMs = intervalSeconds * 1000;
  
  return (now - lastSyncTime) >= intervalMs;
}

/**
 * Helper per calcolare priorità dinamica
 */
export function calculateSyncPriority(
  workflowActive: boolean,
  lastExecution?: Date,
  errorRate?: number
): SyncPriority {
  // Workflow con errori alti = priorità critica
  if (errorRate && errorRate > 50) {
    return SyncPriority.CRITICAL;
  }
  
  // Workflow attivi = alta priorità
  if (workflowActive) {
    return SyncPriority.HIGH;
  }
  
  // Workflow eseguiti recentemente = media priorità
  if (lastExecution) {
    const hoursSinceExecution = (Date.now() - lastExecution.getTime()) / (1000 * 60 * 60);
    if (hoursSinceExecution < 24) {
      return SyncPriority.MEDIUM;
    }
  }
  
  // Default = bassa priorità
  return SyncPriority.LOW;
}