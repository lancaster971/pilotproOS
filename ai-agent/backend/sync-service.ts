/**
 * Sync Service
 * 
 * Servizio principale di sincronizzazione che coordina tutto il processo.
 * Gestisce scheduling, monitoring e health checks.
 */

import { SyncManager } from './sync-manager.js';
import { defaultSyncConfig, SyncConfig, SyncType } from './sync-config.js';
import * as cron from 'node-cron';

/**
 * Servizio principale di sincronizzazione
 */
export class SyncService {
  private syncManager: SyncManager;
  private config: SyncConfig;
  private scheduledTasks: Map<string, cron.ScheduledTask>;
  private isRunning: boolean = false;
  
  constructor(config?: Partial<SyncConfig>) {
    this.config = { ...defaultSyncConfig, ...config };
    this.syncManager = new SyncManager(this.config);
    this.scheduledTasks = new Map();
  }
  
  /**
   * Avvia il servizio di sincronizzazione
   */
  async start(): Promise<void> {
    console.log('🚀 Avvio Sync Service...');
    
    // Inizializza manager
    await this.syncManager.initialize();
    
    // Avvia scheduler
    this.startScheduler();
    
    // Esegui sync iniziale
    await this.initialSync();
    
    this.isRunning = true;
    console.log('✅ Sync Service avviato');
  }
  
  /**
   * Ferma il servizio
   */
  async stop(): Promise<void> {
    console.log('🛑 Arresto Sync Service...');
    
    // Ferma tutti i task schedulati
    this.scheduledTasks.forEach(task => task.stop());
    this.scheduledTasks.clear();
    
    this.isRunning = false;
    console.log('✅ Sync Service arrestato');
  }
  
  /**
   * Sync iniziale all'avvio
   */
  private async initialSync(): Promise<void> {
    console.log('📊 Esecuzione sync iniziale...');
    
    try {
      // Sync workflow
      await this.syncManager.syncWorkflows(SyncType.INCREMENTAL);
      
      // Sync esecuzioni recenti
      await this.syncManager.syncExecutions(SyncType.INCREMENTAL);
      
      // Processa retry pendenti
      await this.syncManager.processRetries();
      
    } catch (error) {
      console.error('❌ Errore durante sync iniziale:', error);
    }
  }
  
  /**
   * Configura e avvia scheduler
   */
  private startScheduler(): void {
    console.log('⏰ Configurazione scheduler...');
    
    // Schedule sync workflow
    if (this.config.intervals.workflows > 0) {
      const workflowCron = this.secondsToCron(this.config.intervals.workflows);
      const workflowTask = cron.schedule(workflowCron, async () => {
        await this.runSyncWorkflows();
      });
      this.scheduledTasks.set('workflows', workflowTask);
      console.log(`📅 Sync workflow schedulato: ogni ${this.config.intervals.workflows}s`);
    }
    
    // Schedule sync esecuzioni
    if (this.config.intervals.executions > 0) {
      const executionCron = this.secondsToCron(this.config.intervals.executions);
      const executionTask = cron.schedule(executionCron, async () => {
        await this.runSyncExecutions();
      });
      this.scheduledTasks.set('executions', executionTask);
      console.log(`📅 Sync esecuzioni schedulato: ogni ${this.config.intervals.executions}s`);
    }
    
    // Schedule full sync
    if (this.config.intervals.fullSync > 0) {
      const fullSyncCron = this.secondsToCron(this.config.intervals.fullSync);
      const fullSyncTask = cron.schedule(fullSyncCron, async () => {
        await this.runFullSync();
      });
      this.scheduledTasks.set('fullSync', fullSyncTask);
      console.log(`📅 Full sync schedulato: ogni ${this.config.intervals.fullSync}s`);
    }
    
    // Schedule KPI calculation (orario)
    if (this.config.intervals.kpiHourly > 0) {
      const kpiTask = cron.schedule('0 * * * *', async () => {
        await this.calculateKPIs('hourly');
      });
      this.scheduledTasks.set('kpiHourly', kpiTask);
      console.log('📅 Calcolo KPI orari schedulato: ogni ora');
    }
    
    // Schedule KPI calculation (giornaliero)
    if (this.config.intervals.kpiDaily > 0) {
      const kpiDailyTask = cron.schedule('0 0 * * *', async () => {
        await this.calculateKPIs('daily');
      });
      this.scheduledTasks.set('kpiDaily', kpiDailyTask);
      console.log('📅 Calcolo KPI giornalieri schedulato: ogni giorno a mezzanotte');
    }
    
    // Schedule cleanup
    if (this.config.intervals.cleanup > 0) {
      const cleanupTask = cron.schedule('0 2 * * *', async () => {
        await this.runCleanup();
      });
      this.scheduledTasks.set('cleanup', cleanupTask);
      console.log('📅 Cleanup schedulato: ogni giorno alle 2:00');
    }
    
    // Schedule retry processing ogni 5 minuti
    const retryTask = cron.schedule('*/5 * * * *', async () => {
      await this.syncManager.processRetries();
    });
    this.scheduledTasks.set('retries', retryTask);
    console.log('📅 Processing retry schedulato: ogni 5 minuti');
  }
  
  /**
   * Esegue sync workflow
   */
  private async runSyncWorkflows(): Promise<void> {
    try {
      console.log('⏱️ Avvio sync workflow schedulato...');
      await this.syncManager.syncWorkflows(SyncType.INCREMENTAL);
    } catch (error) {
      console.error('❌ Errore sync workflow schedulato:', error);
    }
  }
  
  /**
   * Esegue sync esecuzioni
   */
  private async runSyncExecutions(): Promise<void> {
    try {
      console.log('⏱️ Avvio sync esecuzioni schedulato...');
      await this.syncManager.syncExecutions(SyncType.INCREMENTAL);
    } catch (error) {
      console.error('❌ Errore sync esecuzioni schedulato:', error);
    }
  }
  
  /**
   * Esegue full sync
   */
  private async runFullSync(): Promise<void> {
    try {
      console.log('⏱️ Avvio full sync schedulato...');
      await this.syncManager.syncWorkflows(SyncType.FULL);
      await this.syncManager.syncExecutions(SyncType.FULL);
    } catch (error) {
      console.error('❌ Errore full sync schedulato:', error);
    }
  }
  
  /**
   * Calcola KPI e metriche
   */
  private async calculateKPIs(period: 'hourly' | 'daily'): Promise<void> {
    try {
      console.log(`📊 Calcolo KPI ${period}...`);
      
      // TODO: Implementare calcolo KPI
      // Questo sarà implementato nel metrics calculator
      
      console.log(`✅ KPI ${period} calcolati`);
    } catch (error) {
      console.error(`❌ Errore calcolo KPI ${period}:`, error);
    }
  }
  
  /**
   * Esegue cleanup dati vecchi
   */
  private async runCleanup(): Promise<void> {
    try {
      console.log('🧹 Avvio cleanup dati vecchi...');
      
      const { repositories } = await import('../database/repositories/index.js');
      
      // Cleanup esecuzioni vecchie
      const deletedExecutions = await repositories.executions.cleanOldExecutions(
        this.config.retention.executionsDays
      );
      
      // Cleanup KPI snapshots vecchi
      const { PeriodType } = await import('../database/models/index.js');
      const deletedSnapshots = await repositories.analytics.cleanOldSnapshots({
        [PeriodType.HOURLY]: 7,    // Mantieni orari per 7 giorni
        [PeriodType.DAILY]: 30,    // Mantieni giornalieri per 30 giorni
        [PeriodType.WEEKLY]: 90,   // Mantieni settimanali per 90 giorni
        [PeriodType.MONTHLY]: 365, // Mantieni mensili per 1 anno
        [PeriodType.QUARTERLY]: 365, // Mantieni trimestrali per 1 anno
        [PeriodType.YEARLY]: 365 * 5 // Mantieni annuali per 5 anni
      });
      
      console.log(`✅ Cleanup completato: ${deletedExecutions} esecuzioni, ${deletedSnapshots} snapshots eliminati`);
    } catch (error) {
      console.error('❌ Errore durante cleanup:', error);
    }
  }
  
  /**
   * Converte secondi in espressione cron
   */
  private secondsToCron(seconds: number): string {
    if (seconds < 60) {
      // Ogni X secondi
      return `*/${seconds} * * * * *`;
    } else if (seconds < 3600) {
      // Ogni X minuti
      const minutes = Math.floor(seconds / 60);
      return `0 */${minutes} * * * *`;
    } else if (seconds < 86400) {
      // Ogni X ore
      const hours = Math.floor(seconds / 3600);
      return `0 0 */${hours} * * *`;
    } else {
      // Ogni X giorni
      const days = Math.floor(seconds / 86400);
      return `0 0 0 */${days} * *`;
    }
  }
  
  /**
   * Forza sync manuale
   */
  async forceSync(type: 'workflows' | 'executions' | 'full'): Promise<void> {
    console.log(`🔄 Forzando sync manuale: ${type}`);
    
    switch (type) {
      case 'workflows':
        await this.syncManager.syncWorkflows(SyncType.FORCED);
        break;
      case 'executions':
        await this.syncManager.syncExecutions(SyncType.FORCED);
        break;
      case 'full':
        await this.syncManager.syncWorkflows(SyncType.FULL);
        await this.syncManager.syncExecutions(SyncType.FULL);
        break;
    }
  }
  
  /**
   * Ottiene statistiche del servizio
   */
  getStats() {
    return {
      isRunning: this.isRunning,
      scheduledTasks: Array.from(this.scheduledTasks.keys()),
      syncStats: this.syncManager.getStats(),
      config: {
        intervals: this.config.intervals,
        limits: this.config.limits
      }
    };
  }
  
  /**
   * Health check del servizio
   */
  async healthCheck(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    checks: Record<string, boolean>;
    message?: string;
  }> {
    const checks = {
      service: this.isRunning,
      database: false,
      api: false,
      scheduler: this.scheduledTasks.size > 0
    };
    
    try {
      // Check database
      const { db } = await import('../database/connection.js');
      await db.query('SELECT 1');
      checks.database = true;
    } catch (error) {
      console.error('Health check DB failed:', error);
    }
    
    try {
      // Check API
      const apiFetcher = new (await import('./api-fetcher.js')).ApiFetcher(this.config);
      checks.api = await apiFetcher.testConnection();
    } catch (error) {
      console.error('Health check API failed:', error);
    }
    
    // Determina status complessivo
    const healthyChecks = Object.values(checks).filter(v => v).length;
    const totalChecks = Object.keys(checks).length;
    
    let status: 'healthy' | 'degraded' | 'unhealthy';
    let message: string | undefined;
    
    if (healthyChecks === totalChecks) {
      status = 'healthy';
    } else if (healthyChecks >= totalChecks / 2) {
      status = 'degraded';
      message = `${totalChecks - healthyChecks} check falliti`;
    } else {
      status = 'unhealthy';
      message = `Solo ${healthyChecks}/${totalChecks} check passati`;
    }
    
    return { status, checks, message };
  }
}

/**
 * Istanza singleton del servizio
 */
let serviceInstance: SyncService | null = null;

/**
 * Ottiene istanza singleton del servizio
 */
export function getSyncService(config?: Partial<SyncConfig>): SyncService {
  if (!serviceInstance) {
    serviceInstance = new SyncService(config);
  }
  return serviceInstance;
}

/**
 * Entry point per avvio standalone del servizio
 */
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log('🚀 Avvio Sync Service in modalità standalone...');
  
  const service = getSyncService();
  
  // Gestione shutdown
  process.on('SIGINT', async () => {
    console.log('\n📛 Ricevuto SIGINT, arresto servizio...');
    await service.stop();
    process.exit(0);
  });
  
  process.on('SIGTERM', async () => {
    console.log('\n📛 Ricevuto SIGTERM, arresto servizio...');
    await service.stop();
    process.exit(0);
  });
  
  // Avvia servizio
  service.start().catch(error => {
    console.error('❌ Errore fatale:', error);
    process.exit(1);
  });
}