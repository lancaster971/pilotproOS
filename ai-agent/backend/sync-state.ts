/**
 * Sync State Manager
 * 
 * Gestisce lo stato della sincronizzazione, checkpoint per recovery
 * e tracking delle operazioni.
 */

import { DatabaseConnection } from '../database/connection.js';
import { SyncState, SyncType, SyncStatus, SyncResult } from './sync-config.js';

/**
 * Manager per stato sincronizzazione
 */
export class SyncStateManager {
  private db: DatabaseConnection;
  private state: SyncState;
  private stateFile: string = '.sync-state.json'; // File locale per backup stato
  
  constructor() {
    this.db = DatabaseConnection.getInstance();
    this.state = this.getDefaultState();
  }
  
  /**
   * Inizializza stato dal database o file
   */
  async initialize(): Promise<void> {
    try {
      // Prova a caricare stato dal database
      await this.loadFromDatabase();
    } catch (error) {
      console.warn('⚠️ Impossibile caricare stato da DB, uso default:', error);
      this.state = this.getDefaultState();
    }
  }
  
  /**
   * Ottiene stato default
   */
  private getDefaultState(): SyncState {
    return {
      totalSyncs: 0,
      successfulSyncs: 0,
      failedSyncs: 0,
      pendingRetries: []
    };
  }
  
  /**
   * Carica stato dal database
   */
  private async loadFromDatabase(): Promise<void> {
    const query = `
      SELECT * FROM sync_state 
      WHERE id = 'main'
      LIMIT 1
    `;
    
    const result = await this.db.getOne<any>(query);
    
    if (result) {
      this.state = {
        lastWorkflowSync: result.last_workflow_sync ? new Date(result.last_workflow_sync) : undefined,
        lastExecutionSync: result.last_execution_sync ? new Date(result.last_execution_sync) : undefined,
        lastFullSync: result.last_full_sync ? new Date(result.last_full_sync) : undefined,
        lastKpiCalculation: result.last_kpi_calculation ? new Date(result.last_kpi_calculation) : undefined,
        lastProcessedWorkflowId: result.last_processed_workflow_id,
        lastProcessedExecutionId: result.last_processed_execution_id,
        totalSyncs: result.total_syncs || 0,
        successfulSyncs: result.successful_syncs || 0,
        failedSyncs: result.failed_syncs || 0,
        currentSync: result.current_sync ? JSON.parse(result.current_sync) : undefined,
        pendingRetries: result.pending_retries ? JSON.parse(result.pending_retries) : []
      };
    }
  }
  
  /**
   * Salva stato nel database
   */
  async save(): Promise<void> {
    const query = `
      INSERT INTO sync_state (
        id, last_workflow_sync, last_execution_sync, last_full_sync,
        last_kpi_calculation, last_processed_workflow_id, last_processed_execution_id,
        total_syncs, successful_syncs, failed_syncs,
        current_sync, pending_retries, updated_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, CURRENT_TIMESTAMP)
      ON CONFLICT (id) DO UPDATE SET
        last_workflow_sync = EXCLUDED.last_workflow_sync,
        last_execution_sync = EXCLUDED.last_execution_sync,
        last_full_sync = EXCLUDED.last_full_sync,
        last_kpi_calculation = EXCLUDED.last_kpi_calculation,
        last_processed_workflow_id = EXCLUDED.last_processed_workflow_id,
        last_processed_execution_id = EXCLUDED.last_processed_execution_id,
        total_syncs = EXCLUDED.total_syncs,
        successful_syncs = EXCLUDED.successful_syncs,
        failed_syncs = EXCLUDED.failed_syncs,
        current_sync = EXCLUDED.current_sync,
        pending_retries = EXCLUDED.pending_retries,
        updated_at = CURRENT_TIMESTAMP
    `;
    
    const values = [
      'main', // ID fisso per stato principale
      this.state.lastWorkflowSync || null,
      this.state.lastExecutionSync || null,
      this.state.lastFullSync || null,
      this.state.lastKpiCalculation || null,
      this.state.lastProcessedWorkflowId || null,
      this.state.lastProcessedExecutionId || null,
      this.state.totalSyncs,
      this.state.successfulSyncs,
      this.state.failedSyncs,
      this.state.currentSync ? JSON.stringify(this.state.currentSync) : null,
      JSON.stringify(this.state.pendingRetries)
    ];
    
    await this.db.query(query, values);
  }
  
  /**
   * Inizia nuovo sync
   */
  async startSync(type: SyncType): Promise<void> {
    this.state.currentSync = {
      type,
      status: SyncStatus.RUNNING,
      startTime: new Date(),
      progress: 0
    };
    
    await this.save();
  }
  
  /**
   * Aggiorna progresso sync
   */
  async updateProgress(progress: number): Promise<void> {
    if (this.state.currentSync) {
      this.state.currentSync.progress = Math.min(100, Math.max(0, progress));
      await this.save();
    }
  }
  
  /**
   * Completa sync corrente
   */
  async completeSync(result: SyncResult): Promise<void> {
    // Aggiorna timestamp in base al tipo
    const now = new Date();
    
    if (result.type === SyncType.FULL) {
      this.state.lastFullSync = now;
    }
    
    // Aggiorna contatori
    this.state.totalSyncs++;
    
    if (result.status === SyncStatus.COMPLETED) {
      this.state.successfulSyncs++;
      
      // Aggiorna timestamp specifici se sync completato
      if (result.stats.workflowsProcessed > 0) {
        this.state.lastWorkflowSync = now;
      }
      if (result.stats.executionsProcessed > 0) {
        this.state.lastExecutionSync = now;
      }
    } else if (result.status === SyncStatus.FAILED) {
      this.state.failedSyncs++;
    }
    
    // Reset sync corrente
    this.state.currentSync = undefined;
    
    // Salva risultato nel database per storico
    await this.saveSyncResult(result);
    
    // Salva stato aggiornato
    await this.save();
  }
  
  /**
   * Salva risultato sync per storico
   */
  private async saveSyncResult(result: SyncResult): Promise<void> {
    const query = `
      INSERT INTO sync_history (
        sync_type, status, started_at, finished_at, duration_ms,
        workflows_processed, workflows_created, workflows_updated, workflows_failed,
        executions_processed, executions_created, executions_updated, executions_failed,
        total_api_calls, total_db_operations, errors, metadata
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
    `;
    
    const values = [
      result.type,
      result.status,
      result.startTime,
      result.endTime || new Date(),
      result.duration_ms || 0,
      result.stats.workflowsProcessed,
      result.stats.workflowsCreated,
      result.stats.workflowsUpdated,
      result.stats.workflowsFailed,
      result.stats.executionsProcessed,
      result.stats.executionsCreated,
      result.stats.executionsUpdated,
      result.stats.executionsFailed,
      result.stats.totalApiCalls,
      result.stats.totalDbOperations,
      JSON.stringify(result.errors),
      JSON.stringify(result.metadata || {})
    ];
    
    await this.db.query(query, values);
  }
  
  /**
   * Imposta checkpoint per recovery
   */
  async setCheckpoint(workflowId?: string, executionId?: string): Promise<void> {
    if (workflowId) {
      this.state.lastProcessedWorkflowId = workflowId;
    }
    if (executionId) {
      this.state.lastProcessedExecutionId = executionId;
    }
    
    // Salva solo periodicamente per performance
    if (Math.random() < 0.1) { // 10% delle volte
      await this.save();
    }
  }
  
  /**
   * Aggiunge entità per retry
   */
  async addRetry(
    entityType: 'workflow' | 'execution',
    entityId: string,
    error: string
  ): Promise<void> {
    // Trova retry esistente
    const existingIndex = this.state.pendingRetries.findIndex(
      r => r.entityType === entityType && r.entityId === entityId
    );
    
    if (existingIndex >= 0) {
      // Incrementa contatore retry
      this.state.pendingRetries[existingIndex].retryCount++;
      this.state.pendingRetries[existingIndex].lastError = error;
      this.state.pendingRetries[existingIndex].nextRetryAt = this.calculateNextRetry(
        this.state.pendingRetries[existingIndex].retryCount
      );
    } else {
      // Aggiungi nuovo retry
      this.state.pendingRetries.push({
        entityType,
        entityId,
        retryCount: 1,
        lastError: error,
        nextRetryAt: this.calculateNextRetry(1)
      });
    }
    
    await this.save();
  }
  
  /**
   * Ottiene retry pronti per essere riprocessati
   */
  getReadyRetries(): Array<{
    entityType: 'workflow' | 'execution';
    entityId: string;
    retryCount: number;
  }> {
    const now = new Date();
    
    return this.state.pendingRetries
      .filter(r => r.nextRetryAt <= now)
      .map(r => ({
        entityType: r.entityType,
        entityId: r.entityId,
        retryCount: r.retryCount
      }));
  }
  
  /**
   * Rimuove retry completato
   */
  async removeRetry(entityType: 'workflow' | 'execution', entityId: string): Promise<void> {
    this.state.pendingRetries = this.state.pendingRetries.filter(
      r => !(r.entityType === entityType && r.entityId === entityId)
    );
    
    await this.save();
  }
  
  /**
   * Calcola prossimo retry time con exponential backoff
   */
  private calculateNextRetry(retryCount: number): Date {
    const baseDelay = 60000; // 1 minuto
    const maxDelay = 3600000; // 1 ora
    
    const delay = Math.min(baseDelay * Math.pow(2, retryCount - 1), maxDelay);
    return new Date(Date.now() + delay);
  }
  
  /**
   * Verifica se è necessario un sync
   */
  shouldSyncWorkflows(intervalSeconds: number): boolean {
    if (!this.state.lastWorkflowSync) return true;
    
    const elapsed = Date.now() - this.state.lastWorkflowSync.getTime();
    return elapsed >= intervalSeconds * 1000;
  }
  
  shouldSyncExecutions(intervalSeconds: number): boolean {
    if (!this.state.lastExecutionSync) return true;
    
    const elapsed = Date.now() - this.state.lastExecutionSync.getTime();
    return elapsed >= intervalSeconds * 1000;
  }
  
  shouldFullSync(intervalSeconds: number): boolean {
    if (!this.state.lastFullSync) return true;
    
    const elapsed = Date.now() - this.state.lastFullSync.getTime();
    return elapsed >= intervalSeconds * 1000;
  }
  
  /**
   * Ottiene statistiche sync
   */
  getStats(): {
    totalSyncs: number;
    successRate: number;
    lastSync?: Date;
    isRunning: boolean;
    progress?: number;
  } {
    const lastSync = this.state.lastWorkflowSync || this.state.lastExecutionSync;
    
    return {
      totalSyncs: this.state.totalSyncs,
      successRate: this.state.totalSyncs > 0 
        ? (this.state.successfulSyncs / this.state.totalSyncs) * 100 
        : 0,
      lastSync,
      isRunning: this.state.currentSync?.status === SyncStatus.RUNNING,
      progress: this.state.currentSync?.progress
    };
  }
  
  /**
   * Reset stato (per testing o recovery)
   */
  async reset(): Promise<void> {
    this.state = this.getDefaultState();
    await this.save();
  }
}