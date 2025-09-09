/**
 * Sync Manager
 * 
 * Orchestrazione del processo di sincronizzazione.
 * Coordina API fetcher, transformer e database operations.
 */

import { ApiFetcher } from './api-fetcher.js';
import { DataTransformer } from './data-transformer.js';
import { SyncStateManager } from './sync-state.js';
import { 
  SyncConfig, 
  SyncType, 
  SyncStatus, 
  SyncResult,
  SyncPriority,
  calculateSyncPriority 
} from './sync-config.js';
import { repositories } from '../database/repositories/index.js';
import { DatabaseConnection } from '../database/connection.js';

/**
 * Manager principale per orchestrazione sync
 */
export class SyncManager {
  private config: SyncConfig;
  private apiFetcher: ApiFetcher;
  private transformer: DataTransformer;
  private stateManager: SyncStateManager;
  private db: DatabaseConnection;
  
  // Statistiche correnti
  private currentStats = {
    workflowsProcessed: 0,
    workflowsCreated: 0,
    workflowsUpdated: 0,
    workflowsFailed: 0,
    executionsProcessed: 0,
    executionsCreated: 0,
    executionsUpdated: 0,
    executionsFailed: 0,
    totalApiCalls: 0,
    totalDbOperations: 0
  };
  
  constructor(config: SyncConfig) {
    this.config = config;
    this.apiFetcher = new ApiFetcher(config);
    this.transformer = new DataTransformer();
    this.stateManager = new SyncStateManager();
    this.db = DatabaseConnection.getInstance();
  }
  
  /**
   * Inizializza sync manager
   */
  async initialize(): Promise<void> {
    console.log('🚀 Inizializzazione Sync Manager...');
    
    // Inizializza stato
    await this.stateManager.initialize();
    
    // Test connessione API
    const apiConnected = await this.apiFetcher.testConnection();
    if (!apiConnected) {
      throw new Error('Impossibile connettersi all\'API n8n');
    }
    
    // Test connessione database
    await this.db.connect();
    
    console.log('✅ Sync Manager inizializzato');
  }
  
  /**
   * Esegue sync workflow
   */
  async syncWorkflows(type: SyncType = SyncType.INCREMENTAL): Promise<SyncResult> {
    console.log(`📊 Avvio sync workflow (${type})...`);
    
    const startTime = new Date();
    this.resetStats();
    
    try {
      await this.stateManager.startSync(type);
      
      // Determina workflow da sincronizzare
      let workflows: any[];
      
      if (type === SyncType.FULL || type === SyncType.FORCED) {
        // Full sync: tutti i workflow
        workflows = await this.apiFetcher.getWorkflows(this.config.limits.maxWorkflowsPerSync);
        this.currentStats.totalApiCalls++;
      } else {
        // Incremental: solo modificati
        const lastSync = this.stateManager['state'].lastWorkflowSync || new Date(0);
        workflows = await this.apiFetcher.getWorkflowsModifiedAfter(
          lastSync,
          this.config.limits.maxWorkflowsPerSync
        );
        this.currentStats.totalApiCalls++;
      }
      
      console.log(`📥 Trovati ${workflows.length} workflow da sincronizzare`);
      
      // Ordina per priorità se abilitato
      if (this.config.features.smartPriority) {
        workflows = this.prioritizeWorkflows(workflows);
      }
      
      // Processa workflow in batch
      const batchSize = this.config.performance.batchSize;
      for (let i = 0; i < workflows.length; i += batchSize) {
        const batch = workflows.slice(i, i + batchSize);
        await this.processWorkflowBatch(batch);
        
        // Aggiorna progresso
        const progress = Math.round((i + batch.length) / workflows.length * 100);
        await this.stateManager.updateProgress(progress);
      }
      
      // Completa sync
      const endTime = new Date();
      const result: SyncResult = {
        type,
        status: SyncStatus.COMPLETED,
        startTime,
        endTime,
        duration_ms: endTime.getTime() - startTime.getTime(),
        stats: { ...this.currentStats },
        errors: []
      };
      
      await this.stateManager.completeSync(result);
      
      console.log(`✅ Sync workflow completato: ${this.currentStats.workflowsProcessed} processati`);
      return result;
      
    } catch (error) {
      console.error('❌ Errore durante sync workflow:', error);
      
      const result: SyncResult = {
        type,
        status: SyncStatus.FAILED,
        startTime,
        endTime: new Date(),
        duration_ms: Date.now() - startTime.getTime(),
        stats: { ...this.currentStats },
        errors: [{
          entity: 'sync',
          entityId: 'workflows',
          error: error instanceof Error ? error.message : 'Errore sconosciuto',
          timestamp: new Date()
        }]
      };
      
      await this.stateManager.completeSync(result);
      throw error;
    }
  }
  
  /**
   * Esegue sync esecuzioni
   */
  async syncExecutions(type: SyncType = SyncType.INCREMENTAL): Promise<SyncResult> {
    console.log(`📊 Avvio sync esecuzioni (${type})...`);
    
    const startTime = new Date();
    this.resetStats();
    
    try {
      await this.stateManager.startSync(type);
      
      // Determina intervallo temporale
      let hoursBack = 1; // Default: ultima ora
      
      if (type === SyncType.FULL) {
        hoursBack = 24 * 7; // Full: ultima settimana
      } else if (this.stateManager['state'].lastExecutionSync) {
        // Incremental: dal ultimo sync
        const hoursSinceLastSync = (Date.now() - this.stateManager['state'].lastExecutionSync.getTime()) / (1000 * 60 * 60);
        hoursBack = Math.min(hoursSinceLastSync * 1.5, 24); // Max 24 ore
      }
      
      // Fetch esecuzioni recenti
      const executions = await this.apiFetcher.getRecentExecutions(
        hoursBack,
        this.config.limits.maxExecutionsPerSync
      );
      this.currentStats.totalApiCalls++;
      
      console.log(`📥 Trovate ${executions.length} esecuzioni da sincronizzare`);
      
      // Processa in batch
      const batchSize = this.config.performance.batchSize;
      for (let i = 0; i < executions.length; i += batchSize) {
        const batch = executions.slice(i, i + batchSize);
        await this.processExecutionBatch(batch);
        
        // Aggiorna progresso
        const progress = Math.round((i + batch.length) / executions.length * 100);
        await this.stateManager.updateProgress(progress);
      }
      
      // Completa sync
      const endTime = new Date();
      const result: SyncResult = {
        type,
        status: SyncStatus.COMPLETED,
        startTime,
        endTime,
        duration_ms: endTime.getTime() - startTime.getTime(),
        stats: { ...this.currentStats },
        errors: []
      };
      
      await this.stateManager.completeSync(result);
      
      console.log(`✅ Sync esecuzioni completato: ${this.currentStats.executionsProcessed} processate`);
      return result;
      
    } catch (error) {
      console.error('❌ Errore durante sync esecuzioni:', error);
      
      const result: SyncResult = {
        type,
        status: SyncStatus.FAILED,
        startTime,
        endTime: new Date(),
        duration_ms: Date.now() - startTime.getTime(),
        stats: { ...this.currentStats },
        errors: [{
          entity: 'sync',
          entityId: 'executions',
          error: error instanceof Error ? error.message : 'Errore sconosciuto',
          timestamp: new Date()
        }]
      };
      
      await this.stateManager.completeSync(result);
      throw error;
    }
  }
  
  /**
   * Processa batch di workflow
   */
  private async processWorkflowBatch(workflows: any[]): Promise<void> {
    for (const workflow of workflows) {
      try {
        // Fetch dettagli completi
        const fullWorkflow = await this.apiFetcher.getWorkflowDetails(workflow.id);
        this.currentStats.totalApiCalls++;
        
        // Trasforma in modello database
        const workflowModel = this.transformer.transformWorkflow(fullWorkflow);
        const nodes = this.transformer.transformWorkflowNodes(workflow.id, fullWorkflow.nodes);
        const connections = this.transformer.transformWorkflowConnections(workflow.id, fullWorkflow.connections);
        
        // Salva in transazione
        await this.db.transaction(async () => {
          // Verifica se esiste
          const existing = await repositories.workflows.findById(workflow.id);
          
          if (existing) {
            // Aggiorna workflow esistente
            await repositories.workflows.update(workflow.id, workflowModel);
            this.currentStats.workflowsUpdated++;
            
            // Elimina vecchi nodi e connessioni
            await this.db.query('DELETE FROM workflow_nodes WHERE workflow_id = $1', [workflow.id]);
            await this.db.query('DELETE FROM workflow_connections WHERE workflow_id = $1', [workflow.id]);
          } else {
            // Crea nuovo workflow
            await repositories.workflows.create(workflowModel);
            this.currentStats.workflowsCreated++;
          }
          
          // Inserisci nodi
          for (const node of nodes) {
            await this.db.query(
              `INSERT INTO workflow_nodes (
                workflow_id, node_id, node_name, node_type,
                parameters, position, type_version, credentials,
                execution_count, success_count, failure_count,
                avg_execution_time_ms, error_rate,
                disabled, notes, color
              ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)`,
              [
                node.workflow_id, node.node_id, node.node_name, node.node_type,
                JSON.stringify(node.parameters), JSON.stringify(node.position), 
                node.type_version, JSON.stringify(node.credentials),
                node.execution_count, node.success_count, node.failure_count,
                node.avg_execution_time_ms, node.error_rate,
                node.disabled, node.notes, node.color
              ]
            );
          }
          
          // Inserisci connessioni
          for (const conn of connections) {
            await this.db.query(
              `INSERT INTO workflow_connections (
                workflow_id, source_node, source_output, target_node, target_input, connection_type
              ) VALUES ($1, $2, $3, $4, $5, $6)`,
              [
                conn.workflow_id, conn.source_node, conn.source_output,
                conn.target_node, conn.target_input, conn.connection_type
              ]
            );
          }
          
          this.currentStats.totalDbOperations += 2 + nodes.length + connections.length;
        });
        
        this.currentStats.workflowsProcessed++;
        
        // Checkpoint per recovery
        await this.stateManager.setCheckpoint(workflow.id, undefined);
        
      } catch (error) {
        console.error(`❌ Errore processando workflow ${workflow.id}:`, error);
        this.currentStats.workflowsFailed++;
        
        // Aggiungi per retry
        await this.stateManager.addRetry(
          'workflow',
          workflow.id,
          error instanceof Error ? error.message : 'Errore sconosciuto'
        );
      }
    }
  }
  
  /**
   * Processa batch di esecuzioni
   */
  private async processExecutionBatch(executions: any[]): Promise<void> {
    for (const execution of executions) {
      try {
        // Trasforma in modello database
        const executionModel = this.transformer.transformExecution(execution);
        const nodeResults = this.transformer.transformNodeResults(
          execution.id,
          execution.workflowId,
          execution.data?.resultData?.runData
        );
        
        // Salva in transazione
        await this.db.transaction(async () => {
          // Usa repository per salvare/aggiornare
          await repositories.executions.syncFromApi(execution);
          
          // Salva risultati nodi
          for (const result of nodeResults) {
            await repositories.executions.saveNodeResult(result);
          }
          
          this.currentStats.totalDbOperations += 1 + nodeResults.length;
        });
        
        this.currentStats.executionsProcessed++;
        
        // Aggiorna metriche workflow
        await this.updateWorkflowMetrics(execution.workflowId);
        
        // Checkpoint per recovery
        await this.stateManager.setCheckpoint(undefined, execution.id);
        
      } catch (error) {
        console.error(`❌ Errore processando esecuzione ${execution.id}:`, error);
        this.currentStats.executionsFailed++;
        
        // Aggiungi per retry
        await this.stateManager.addRetry(
          'execution',
          execution.id,
          error instanceof Error ? error.message : 'Errore sconosciuto'
        );
      }
    }
  }
  
  /**
   * Aggiorna metriche workflow basate su esecuzioni
   */
  private async updateWorkflowMetrics(workflowId: string): Promise<void> {
    try {
      // Calcola statistiche dalle esecuzioni
      const stats = await repositories.executions.getStats(workflowId, 30);
      
      // Aggiorna metriche workflow
      await repositories.workflows.updateMetrics(workflowId, {
        execution_count: stats.totalExecutions,
        success_count: stats.successfulExecutions,
        failure_count: stats.failedExecutions,
        avg_duration_ms: stats.avgDurationMs,
        last_execution_at: new Date()
      });
      
      // Calcola e aggiorna scores
      const reliabilityScore = Math.round(stats.successRate);
      const efficiencyScore = this.calculateEfficiencyScore(stats.avgDurationMs);
      const healthScore = Math.round((reliabilityScore + efficiencyScore) / 2);
      
      await repositories.workflows.updateScores(workflowId, {
        reliability_score: reliabilityScore,
        efficiency_score: efficiencyScore,
        health_score: healthScore
      });
      
    } catch (error) {
      console.warn(`⚠️ Impossibile aggiornare metriche per workflow ${workflowId}:`, error);
    }
  }
  
  /**
   * Calcola efficiency score basato su durata
   */
  private calculateEfficiencyScore(avgDurationMs: number): number {
    // Score basato su durata media
    // < 1s = 100, < 5s = 80, < 10s = 60, < 30s = 40, > 30s = 20
    if (avgDurationMs < 1000) return 100;
    if (avgDurationMs < 5000) return 80;
    if (avgDurationMs < 10000) return 60;
    if (avgDurationMs < 30000) return 40;
    return 20;
  }
  
  /**
   * Prioritizza workflow per sync
   */
  private prioritizeWorkflows(workflows: any[]): any[] {
    return workflows.sort((a, b) => {
      const priorityA = calculateSyncPriority(
        a.active,
        a.updatedAt ? new Date(a.updatedAt) : undefined
      );
      const priorityB = calculateSyncPriority(
        b.active,
        b.updatedAt ? new Date(b.updatedAt) : undefined
      );
      
      // Ordina per priorità (critical first)
      const priorityOrder = {
        [SyncPriority.CRITICAL]: 0,
        [SyncPriority.HIGH]: 1,
        [SyncPriority.MEDIUM]: 2,
        [SyncPriority.LOW]: 3
      };
      
      return priorityOrder[priorityA] - priorityOrder[priorityB];
    });
  }
  
  /**
   * Processa retry pendenti
   */
  async processRetries(): Promise<void> {
    const retries = this.stateManager.getReadyRetries();
    
    if (retries.length === 0) return;
    
    console.log(`🔄 Processando ${retries.length} retry...`);
    
    for (const retry of retries) {
      try {
        if (retry.entityType === 'workflow') {
          const workflow = await this.apiFetcher.getWorkflowDetails(retry.entityId);
          await this.processWorkflowBatch([workflow]);
        } else {
          const execution = await this.apiFetcher.getExecutionDetails(retry.entityId);
          await this.processExecutionBatch([execution]);
        }
        
        // Rimuovi retry se successo
        await this.stateManager.removeRetry(retry.entityType, retry.entityId);
        
      } catch (error) {
        console.error(`❌ Retry fallito per ${retry.entityType} ${retry.entityId}:`, error);
        
        if (retry.retryCount >= this.config.limits.maxRetries) {
          // Rimuovi dopo max retry
          await this.stateManager.removeRetry(retry.entityType, retry.entityId);
        }
      }
    }
  }
  
  /**
   * Reset statistiche correnti
   */
  private resetStats(): void {
    this.currentStats = {
      workflowsProcessed: 0,
      workflowsCreated: 0,
      workflowsUpdated: 0,
      workflowsFailed: 0,
      executionsProcessed: 0,
      executionsCreated: 0,
      executionsUpdated: 0,
      executionsFailed: 0,
      totalApiCalls: 0,
      totalDbOperations: 0
    };
  }
  
  /**
   * Ottiene statistiche sync
   */
  getStats() {
    return {
      current: this.currentStats,
      state: this.stateManager.getStats()
    };
  }
}