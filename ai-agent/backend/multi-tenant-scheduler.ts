/**
 * Multi-Tenant Scheduler
 * 
 * Scheduler che gestisce la sincronizzazione per tutti i tenant registrati.
 * Coordina sync parallelo di multiple istanze n8n.
 */

import { createMultiTenantApiClient } from '../api/multi-tenant-client.js';
import { DatabaseConnection } from '../database/connection.js';
// import { TenantSchemaDiscovery, MultiTenantDiscovery } from '../../scripts/tenant-schema-discovery.js';
import * as cron from 'node-cron';

export interface MultiTenantSchedulerConfig {
  // Intervalli sync (in minuti)
  intervals: {
    tenantSync: number;        // Sync dati per ogni tenant
    schemaDiscovery: number;   // Discovery schema per nuovi tenant
    healthCheck: number;       // Health check tutti i tenant
    cleanup: number;           // Cleanup dati vecchi
  };
  
  // Limiti performance
  limits: {
    maxConcurrentTenants: number;    // Max tenant in sync parallelo
    maxWorkflowsPerTenant: number;   // Max workflows per sync
    maxExecutionsPerTenant: number;  // Max executions per sync
  };
  
  // Configurazioni tenant
  tenantConfig: {
    enableAutoDiscovery: boolean;    // Auto-discovery nuovi tenant
    enableHealthMonitoring: boolean; // Monitoring salute tenant
    enableCleanup: boolean;          // Cleanup automatico
  };
}

export const defaultMultiTenantConfig: MultiTenantSchedulerConfig = {
  intervals: {
    tenantSync: 5,           // Ogni 5 minuti
    schemaDiscovery: 60,     // Ogni ora
    healthCheck: 15,         // Ogni 15 minuti
    cleanup: 1440            // Ogni giorno (1440 min)
  },
  limits: {
    maxConcurrentTenants: 5,
    maxWorkflowsPerTenant: 1000,
    maxExecutionsPerTenant: 500
  },
  tenantConfig: {
    enableAutoDiscovery: true,
    enableHealthMonitoring: true,
    enableCleanup: true
  }
};

/**
 * Risultato sync multi-tenant
 */
export interface MultiTenantSyncResult {
  timestamp: string;
  totalTenants: number;
  successfulTenants: number;
  failedTenants: number;
  totalWorkflowsSynced: number;
  totalExecutionsSynced: number;
  duration_ms: number;
  errors: Array<{
    tenantId: string;
    error: string;
    timestamp: string;
  }>;
}

/**
 * Scheduler per gestione multi-tenant
 */
export class MultiTenantScheduler {
  private config: MultiTenantSchedulerConfig;
  private client: any; // MultiTenantApiClient
  private db: DatabaseConnection;
  private scheduledTasks: Map<string, cron.ScheduledTask>;
  private isRunning: boolean = false;
  
  // Stats correnti
  private stats = {
    totalSyncRuns: 0,
    lastSyncTime: null as Date | null,
    activeTenants: 0,
    totalWorkflowsSynced: 0,
    totalExecutionsSynced: 0,
    lastErrors: [] as string[]
  };

  constructor(config?: Partial<MultiTenantSchedulerConfig>) {
    this.config = { ...defaultMultiTenantConfig, ...config };
    this.client = createMultiTenantApiClient();
    this.db = DatabaseConnection.getInstance();
    this.scheduledTasks = new Map();
  }

  /**
   * Avvia scheduler multi-tenant
   */
  async start(): Promise<void> {
    console.log('🚀 AVVIO MULTI-TENANT SCHEDULER');
    console.log('='.repeat(50));
    
    try {
      // Inizializza connessioni
      await this.db.connect();
      
      // Carica tenant dal database
      await this.client.loadTenantsFromDatabase();
      
      // Conta tenant attivi
      const tenants = await this.getActiveTenants();
      this.stats.activeTenants = tenants.length;
      
      console.log(`📊 Tenant attivi: ${this.stats.activeTenants}`);
      
      // Configura scheduler
      this.setupScheduler();
      
      // Esegui sync iniziale
      await this.initialSync();
      
      this.isRunning = true;
      console.log('✅ Multi-Tenant Scheduler avviato');
      
    } catch (error) {
      console.error('❌ Errore avvio scheduler:', error);
      throw error;
    }
  }

  /**
   * Ferma scheduler
   */
  async stop(): Promise<void> {
    console.log('🛑 Arresto Multi-Tenant Scheduler...');
    
    // Ferma tutti i task schedulati
    this.scheduledTasks.forEach(task => task.stop());
    this.scheduledTasks.clear();
    
    await this.db.disconnect();
    this.isRunning = false;
    
    console.log('✅ Multi-Tenant Scheduler arrestato');
  }

  /**
   * Configura tutti i task schedulati
   */
  private setupScheduler(): void {
    console.log('⏰ Configurazione scheduler...');
    
    // 1. Sync tenant ogni X minuti
    if (this.config.intervals.tenantSync > 0) {
      const syncCron = this.minutesToCron(this.config.intervals.tenantSync);
      const syncTask = cron.schedule(syncCron, async () => {
        await this.runTenantSync();
      });
      this.scheduledTasks.set('tenantSync', syncTask);
      console.log(`📅 Tenant sync: ogni ${this.config.intervals.tenantSync} min`);
    }

    // 2. Schema discovery ogni X minuti
    if (this.config.intervals.schemaDiscovery > 0 && this.config.tenantConfig.enableAutoDiscovery) {
      const discoveryCron = this.minutesToCron(this.config.intervals.schemaDiscovery);
      const discoveryTask = cron.schedule(discoveryCron, async () => {
        await this.runSchemaDiscovery();
      });
      this.scheduledTasks.set('schemaDiscovery', discoveryTask);
      console.log(`📅 Schema discovery: ogni ${this.config.intervals.schemaDiscovery} min`);
    }

    // 3. Health check ogni X minuti
    if (this.config.intervals.healthCheck > 0 && this.config.tenantConfig.enableHealthMonitoring) {
      const healthCron = this.minutesToCron(this.config.intervals.healthCheck);
      const healthTask = cron.schedule(healthCron, async () => {
        await this.runHealthCheck();
      });
      this.scheduledTasks.set('healthCheck', healthTask);
      console.log(`📅 Health check: ogni ${this.config.intervals.healthCheck} min`);
    }

    // 4. Cleanup giornaliero
    if (this.config.intervals.cleanup > 0 && this.config.tenantConfig.enableCleanup) {
      // Esegui alle 02:00 ogni giorno
      const cleanupTask = cron.schedule('0 2 * * *', async () => {
        await this.runCleanup();
      });
      this.scheduledTasks.set('cleanup', cleanupTask);
      console.log('📅 Cleanup: ogni giorno alle 02:00');
    }

    console.log(`✅ ${this.scheduledTasks.size} task schedulati configurati`);
  }

  /**
   * Sync iniziale all'avvio
   */
  private async initialSync(): Promise<void> {
    console.log('📊 Sync iniziale multi-tenant...');
    
    try {
      const result = await this.syncAllTenants();
      console.log(`✅ Sync iniziale: ${result.successfulTenants}/${result.totalTenants} tenant`);
      
      if (result.failedTenants > 0) {
        console.warn(`⚠️ ${result.failedTenants} tenant con errori nel sync iniziale`);
      }
      
    } catch (error) {
      console.error('❌ Errore sync iniziale:', error);
    }
  }

  /**
   * Esegue sync per tutti i tenant
   */
  async syncAllTenants(): Promise<MultiTenantSyncResult> {
    const startTime = Date.now();
    const timestamp = new Date().toISOString();
    
    console.log('🔄 Avvio sync tutti i tenant...');
    
    const result: MultiTenantSyncResult = {
      timestamp,
      totalTenants: 0,
      successfulTenants: 0,
      failedTenants: 0,
      totalWorkflowsSynced: 0,
      totalExecutionsSynced: 0,
      duration_ms: 0,
      errors: []
    };

    try {
      // Ottieni tenant attivi
      const tenants = await this.getActiveTenants();
      result.totalTenants = tenants.length;

      if (tenants.length === 0) {
        console.log('ℹ️ Nessun tenant attivo da sincronizzare');
        result.duration_ms = Date.now() - startTime;
        return result;
      }

      // Sync in batch paralleli per performance
      const batchSize = this.config.limits.maxConcurrentTenants;
      
      for (let i = 0; i < tenants.length; i += batchSize) {
        const batch = tenants.slice(i, i + batchSize);
        
        console.log(`📦 Processing batch ${Math.floor(i/batchSize) + 1}: ${batch.length} tenant`);
        
        // Sync parallelo del batch
        const promises = batch.map(tenant => this.syncSingleTenant(tenant));
        const batchResults = await Promise.allSettled(promises);
        
        // Processa risultati batch
        batchResults.forEach((batchResult, index) => {
          const tenant = batch[index];
          
          if (batchResult.status === 'fulfilled') {
            const syncResult = batchResult.value;
            result.successfulTenants++;
            result.totalWorkflowsSynced += syncResult.workflowsSynced;
            result.totalExecutionsSynced += syncResult.executionsSynced;
            
            console.log(`✅ ${tenant.id}: ${syncResult.workflowsSynced}w, ${syncResult.executionsSynced}e`);
          } else {
            result.failedTenants++;
            const error = batchResult.reason?.message || 'Unknown error';
            result.errors.push({
              tenantId: tenant.id,
              error,
              timestamp: new Date().toISOString()
            });
            
            console.error(`❌ ${tenant.id}: ${error}`);
          }
        });
      }

      // Aggiorna statistiche globali
      this.stats.totalSyncRuns++;
      this.stats.lastSyncTime = new Date();
      this.stats.totalWorkflowsSynced += result.totalWorkflowsSynced;
      this.stats.totalExecutionsSynced += result.totalExecutionsSynced;
      this.stats.lastErrors = result.errors.map(e => e.error).slice(0, 10);

      result.duration_ms = Date.now() - startTime;
      
      console.log(`✅ Sync completato: ${result.successfulTenants}/${result.totalTenants} tenant (${result.duration_ms}ms)`);
      
      // Salva risultati nel database
      await this.saveSyncResult(result);
      
    } catch (error) {
      console.error('❌ Errore durante sync multi-tenant:', error);
      result.errors.push({
        tenantId: 'scheduler',
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      });
    }

    return result;
  }

  /**
   * Sync singolo tenant
   */
  public async syncSingleTenant(tenant: any): Promise<{
    tenantId: string;
    workflowsSynced: number;
    executionsSynced: number;
    errors: string[];
  }> {
    try {
      const syncResult = await this.client.syncTenantData(tenant.id);
      
      return {
        tenantId: tenant.id,
        workflowsSynced: syncResult.workflowsSynced,
        executionsSynced: syncResult.executionsSynced,
        errors: syncResult.errors
      };
      
    } catch (error) {
      console.error(`❌ Errore sync tenant ${tenant.id}:`, error);
      throw error;
    }
  }

  /**
   * Esegue schema discovery per tutti i tenant
   */
  private async runSchemaDiscovery(): Promise<void> {
    console.log('🔍 Schema discovery multi-tenant...');
    
    try {
      const tenants = await this.getActiveTenants();
      
      // TODO: Implementare schema discovery quando necessario
      console.log(`✅ Schema discovery: ${tenants.length} tenant processati (implementazione temporaneamente disabilitata)`);
      
      // Salva risultati nel database - TODO implementare quando discovery è attiva
      // for (const result of results) {
      //   await this.saveSchemaDiscovery(result);
      // }
      
    } catch (error) {
      console.error('❌ Errore schema discovery:', error);
    }
  }

  /**
   * Esegue health check su tutti i tenant
   */
  private async runHealthCheck(): Promise<void> {
    console.log('💊 Health check multi-tenant...');
    
    try {
      const tenants = await this.getActiveTenants();
      let healthyCount = 0;
      let unhealthyCount = 0;
      
      for (const tenant of tenants) {
        try {
          // Test connessione API
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 10000);
          
          const response = await fetch(tenant.n8n_api_url.replace('/api/v1', '/healthz'), {
            signal: controller.signal
          });
          
          clearTimeout(timeoutId);
          
          if (response.ok) {
            healthyCount++;
            await this.updateTenantHealth(tenant.id, 'healthy');
          } else {
            unhealthyCount++;
            await this.updateTenantHealth(tenant.id, 'unhealthy', `HTTP ${response.status}`);
          }
          
        } catch (error) {
          unhealthyCount++;
          const errorMsg = error instanceof Error ? error.message : 'Connection failed';
          await this.updateTenantHealth(tenant.id, 'unhealthy', errorMsg);
          console.warn(`⚠️ ${tenant.id}: ${errorMsg}`);
        }
      }
      
      console.log(`✅ Health check: ${healthyCount} healthy, ${unhealthyCount} unhealthy`);
      
    } catch (error) {
      console.error('❌ Errore health check:', error);
    }
  }

  /**
   * Esegue cleanup dati vecchi per tutti i tenant
   */
  private async runCleanup(): Promise<void> {
    console.log('🧹 Cleanup multi-tenant...');
    
    try {
      const tenants = await this.getActiveTenants();
      let totalCleaned = 0;
      
      for (const tenant of tenants) {
        try {
          // Cleanup executions vecchie (30 giorni)
          const cleaned = await this.db.query(`
            DELETE FROM tenant_executions 
            WHERE tenant_id = $1 
              AND started_at < NOW() - INTERVAL '30 days'
          `, [tenant.id]);
          
          const deletedCount = cleaned.rowCount || 0;
          totalCleaned += deletedCount;
          
          if (deletedCount > 0) {
            console.log(`🗑️ ${tenant.id}: ${deletedCount} executions eliminate`);
          }
          
        } catch (error) {
          console.error(`❌ Errore cleanup ${tenant.id}:`, error);
        }
      }
      
      console.log(`✅ Cleanup completato: ${totalCleaned} record eliminati`);
      
    } catch (error) {
      console.error('❌ Errore durante cleanup:', error);
    }
  }

  /**
   * Wrapper per i metodi schedulati
   */
  private async runTenantSync(): Promise<void> {
    if (!this.isRunning) return;
    
    try {
      console.log('⏱️ Sync schedulato multi-tenant...');
      await this.syncAllTenants();
    } catch (error) {
      console.error('❌ Errore sync schedulato:', error);
    }
  }

  // =====================================================
  // UTILITY METHODS
  // =====================================================

  /**
   * Ottieni tenant attivi dal database
   */
  private async getActiveTenants(): Promise<any[]> {
    return await this.db.getMany(`
      SELECT id, name, n8n_api_url, n8n_version, sync_enabled, last_sync_at
      FROM tenants 
      WHERE sync_enabled = true
      ORDER BY last_sync_at ASC NULLS FIRST
    `);
  }

  /**
   * Salva risultato sync nel database
   */
  private async saveSyncResult(result: MultiTenantSyncResult): Promise<void> {
    try {
      // Crea log separato per ogni tenant + un log aggregato in una tabella dedicata
      const tenants = await this.getActiveTenants();
      
      // Salva log per ogni tenant
      for (const tenant of tenants) {
        await this.db.query(`
          INSERT INTO tenant_sync_logs (
            tenant_id, sync_type, started_at, completed_at, status,
            items_processed, items_added, items_updated, duration_ms,
            error_message, error_details
          ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
          )
        `, [
          tenant.id,
          'multi_tenant_sync',
          new Date(result.timestamp),
          new Date(),
          result.failedTenants === 0 ? 'completed' : 'partial',
          Math.floor((result.totalWorkflowsSynced + result.totalExecutionsSynced) / result.totalTenants),
          Math.floor(result.totalWorkflowsSynced / result.totalTenants),
          Math.floor(result.totalExecutionsSynced / result.totalTenants),
          result.duration_ms,
          result.errors.find(e => e.tenantId === tenant.id)?.error || null,
          null
        ]);
      }
      
      // Salva log aggregato in tabella separata (TODO: creare multi_tenant_sync_logs)
      console.log(`📝 Sync result: ${result.successfulTenants}/${result.totalTenants} tenant, ${result.totalWorkflowsSynced}w + ${result.totalExecutionsSynced}e`);
      
    } catch (error) {
      console.warn('⚠️ Impossibile salvare sync result:', error);
    }
  }

  /**
   * Salva schema discovery nel database
   */
  private async saveSchemaDiscovery(discovery: any): Promise<void> {
    try {
      await this.db.query(`
        INSERT INTO tenant_schema_discoveries (
          tenant_id, discovery_date, n8n_version_detected,
          available_endpoints, workflow_fields, execution_fields,
          custom_nodes, supports_webhooks, supports_credentials,
          supports_tags, total_workflows_analyzed, total_executions_analyzed
        ) VALUES (
          $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
        ) ON CONFLICT (tenant_id) DO UPDATE SET
          discovery_date = $2,
          n8n_version_detected = $3,
          available_endpoints = $4,
          workflow_fields = $5,
          execution_fields = $6,
          custom_nodes = $7,
          supports_webhooks = $8,
          supports_credentials = $9,
          supports_tags = $10,
          total_workflows_analyzed = $11,
          total_executions_analyzed = $12
      `, [
        discovery.tenantId,
        new Date(discovery.discoveryDate),
        discovery.n8nVersion,
        JSON.stringify(discovery.availableEndpoints || []),
        JSON.stringify(discovery.workflowFields || []),
        JSON.stringify(discovery.executionFields || []),
        JSON.stringify(discovery.customNodes || []),
        discovery.capabilities?.supportsWebhooks || false,
        discovery.capabilities?.supportsCredentials || false,
        discovery.capabilities?.supportsTags || false,
        discovery.stats?.totalWorkflowsAnalyzed || 0,
        discovery.stats?.totalExecutionsAnalyzed || 0
      ]);
      
    } catch (error) {
      console.warn(`⚠️ Impossibile salvare discovery per ${discovery.tenantId}:`, error);
    }
  }

  /**
   * Aggiorna stato salute tenant
   */
  private async updateTenantHealth(tenantId: string, status: 'healthy' | 'unhealthy', error?: string): Promise<void> {
    try {
      await this.db.query(`
        UPDATE tenants 
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
      `, [tenantId]);
      
      // TODO: Implementare tabella tenant_health se necessario
      
    } catch (err) {
      console.warn(`⚠️ Impossibile aggiornare health per ${tenantId}:`, err);
    }
  }

  /**
   * Converte minuti in espressione cron
   */
  private minutesToCron(minutes: number): string {
    if (minutes < 60) {
      return `*/${minutes} * * * *`;
    } else if (minutes < 1440) {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      if (remainingMinutes === 0) {
        return `0 */${hours} * * *`;
      } else {
        return `${remainingMinutes} */${hours} * * *`;
      }
    } else {
      const days = Math.floor(minutes / 1440);
      return `0 0 */${days} * *`;
    }
  }

  /**
   * Ottieni statistiche scheduler
   */
  getStats(): {
    isRunning: boolean;
    config: MultiTenantSchedulerConfig;
    scheduledTasks: string[];
    stats: {
      totalSyncRuns: number;
      lastSyncTime: Date | null;
      activeTenants: number;
      totalWorkflowsSynced: number;
      totalExecutionsSynced: number;
      lastErrors: string[];
    };
  } {
    return {
      isRunning: this.isRunning,
      config: this.config,
      scheduledTasks: Array.from(this.scheduledTasks.keys()),
      stats: { ...this.stats }
    };
  }

  /**
   * Forza sync manuale
   */
  async forceSyncAllTenants(): Promise<MultiTenantSyncResult> {
    console.log('🔄 Forzando sync manuale tutti i tenant...');
    return await this.syncAllTenants();
  }

  /**
   * Health check completo
   */
  async healthCheck(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    checks: Record<string, boolean>;
    tenantHealth: Record<string, boolean>;
    message?: string;
  }> {
    const checks = {
      scheduler: this.isRunning,
      database: false,
      tenants: false
    };

    const tenantHealth: Record<string, boolean> = {};

    try {
      // Check database
      await this.db.query('SELECT 1');
      checks.database = true;
    } catch (error) {
      console.error('Health check DB failed:', error);
    }

    try {
      // Check tenant connectivity
      const tenants = await this.getActiveTenants();
      let healthyTenants = 0;

      for (const tenant of tenants.slice(0, 3)) { // Test primi 3 per performance
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 5000);
          
          const response = await fetch(tenant.n8n_api_url.replace('/api/v1', '/healthz'), {
            signal: controller.signal
          });
          
          clearTimeout(timeoutId);
          tenantHealth[tenant.id] = response.ok;
          if (response.ok) healthyTenants++;
        } catch (error) {
          tenantHealth[tenant.id] = false;
        }
      }

      checks.tenants = healthyTenants > 0;
    } catch (error) {
      console.error('Health check tenants failed:', error);
    }

    // Determina status
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

    return { status, checks, tenantHealth, message };
  }
}

/**
 * Istanza singleton dello scheduler multi-tenant
 */
let schedulerInstance: MultiTenantScheduler | null = null;

/**
 * Ottieni istanza singleton dello scheduler
 */
export function getMultiTenantScheduler(config?: Partial<MultiTenantSchedulerConfig>): MultiTenantScheduler {
  if (!schedulerInstance) {
    schedulerInstance = new MultiTenantScheduler(config);
  }
  return schedulerInstance;
}

/**
 * Entry point per avvio standalone
 */
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log('🚀 Avvio Multi-Tenant Scheduler in modalità standalone...');

  const scheduler = getMultiTenantScheduler();

  // Gestione shutdown
  const shutdown = async (signal: string) => {
    console.log(`\n📛 Ricevuto ${signal}, arresto scheduler...`);
    await scheduler.stop();
    process.exit(0);
  };

  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));

  // Avvia scheduler
  scheduler.start().catch(error => {
    console.error('❌ Errore fatale:', error);
    process.exit(1);
  });
}