/**
 * Multi-Tenant n8n API Client
 * 
 * Questo client si adatta automaticamente a diverse istanze n8n
 * gestendo schema diversi, versioni, e capacità per ogni tenant.
 */

import { N8nApiClient } from './client.js';
import { EnvConfig, getEnvConfig } from '../config/environment.js';
import { Workflow, Execution } from '../types/index.js';
import { DatabaseConnection } from '../database/connection.js';

/**
 * Configurazione per un tenant specifico
 */
export interface TenantConfig {
  tenantId: string;
  apiUrl: string;
  apiKey: string;
  n8nVersion?: string;
  capabilities?: TenantCapabilities;
  schemaSignature?: string;
}

/**
 * Capacità rilevate per un tenant
 */
export interface TenantCapabilities {
  supportsWebhooks: boolean;
  supportsCredentials: boolean;
  supportsTags: boolean;
  supportsProjects: boolean;
  supportsUsers: boolean;
  supportsVariables: boolean;
  supportsAudit: boolean;
  availableEndpoints: string[];
  customNodes: string[];
}

/**
 * Risultato normalizzato che funziona per tutti i tenant
 */
export interface NormalizedWorkflow {
  id: string;
  name: string;
  active: boolean;
  createdAt?: string;
  updatedAt?: string;
  tenantId: string;
  rawData: Record<string, any>; // Dati originali completi
  // Campi calcolati comuni
  nodeCount?: number;
  hasWebhook?: boolean;
  isArchived?: boolean;
}

export interface NormalizedExecution {
  id: string;
  workflowId: string;
  startedAt: string;
  status: string;
  mode: string;
  tenantId: string;
  rawData: Record<string, any>; // Dati originali completi
  // Campi calcolati comuni
  finished?: boolean;
  stoppedAt?: string;
  durationMs?: number;
  hasError?: boolean;
}

/**
 * Client API Multi-Tenant che si adatta a ogni istanza n8n
 */
export class MultiTenantApiClient {
  private clients: Map<string, N8nApiClient> = new Map();
  private capabilities: Map<string, TenantCapabilities> = new Map();
  private db: DatabaseConnection;

  constructor() {
    this.db = DatabaseConnection.getInstance();
  }

  /**
   * Registra un nuovo tenant con le sue configurazioni
   */
  async registerTenant(config: TenantConfig): Promise<void> {
    // Crea client specifico per questo tenant usando config esistente come base
    const baseConfig = getEnvConfig();
    const envConfig: EnvConfig = {
      ...baseConfig,
      n8nApiUrl: config.apiUrl,
      n8nApiKey: config.apiKey,
      n8nWebhookUsername: baseConfig.n8nWebhookUsername,
      n8nWebhookPassword: baseConfig.n8nWebhookPassword
    };

    const client = new N8nApiClient(envConfig);
    this.clients.set(config.tenantId, client);

    // Salva capabilities se fornite
    if (config.capabilities) {
      this.capabilities.set(config.tenantId, config.capabilities);
    }

    // Salva configurazione nel database
    await this.saveTenantConfig(config);

    console.log(`✅ Tenant registrato: ${config.tenantId}`);
  }

  /**
   * Carica tutti i tenant dal database
   */
  async loadTenantsFromDatabase(): Promise<void> {
    await this.db.connect();
    
    const tenants = await this.db.getMany(`
      SELECT id, name, n8n_api_url, n8n_version, api_capabilities 
      FROM tenants 
      WHERE sync_enabled = true
    `);

    for (const tenant of tenants) {
      // Per ora usiamo una API key di test - in produzione verrebbe da vault sicuro
      const config: TenantConfig = {
        tenantId: tenant.id,
        apiUrl: tenant.n8n_api_url,
        apiKey: process.env.N8N_API_KEY || '', // TODO: Gestire chiavi per tenant
        n8nVersion: tenant.n8n_version,
        capabilities: tenant.api_capabilities || {}
      };

      await this.registerTenant(config);
    }

    console.log(`📊 Caricati ${tenants.length} tenant dal database`);
  }

  /**
   * Ottiene client per un tenant specifico
   */
  private getClientForTenant(tenantId: string): N8nApiClient {
    const client = this.clients.get(tenantId);
    if (!client) {
      throw new Error(`Tenant non registrato: ${tenantId}`);
    }
    return client;
  }

  /**
   * Ottiene capabilities per un tenant specifico
   */
  private getCapabilitiesForTenant(tenantId: string): TenantCapabilities | null {
    return this.capabilities.get(tenantId) || null;
  }

  /**
   * Lista workflows per un tenant con normalizzazione automatica
   */
  async getWorkflowsForTenant(tenantId: string): Promise<NormalizedWorkflow[]> {
    const client = this.getClientForTenant(tenantId);
    const capabilities = this.getCapabilitiesForTenant(tenantId);

    try {
      const rawWorkflows = await client.getWorkflows();
      
      return rawWorkflows.map(workflow => this.normalizeWorkflow(workflow, tenantId));
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`❌ Errore caricamento workflows per ${tenantId}:`, errorMessage);
      
      // Gestione graceful: ritorna workflows dal database se API non funziona
      return await this.getWorkflowsFromDatabase(tenantId);
    }
  }

  /**
   * Ottiene workflow specifico per tenant
   */
  async getWorkflowForTenant(tenantId: string, workflowId: string): Promise<NormalizedWorkflow> {
    const client = this.getClientForTenant(tenantId);

    try {
      const rawWorkflow = await client.getWorkflow(workflowId);
      return this.normalizeWorkflow(rawWorkflow, tenantId);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`❌ Errore caricamento workflow ${workflowId} per ${tenantId}:`, errorMessage);
      
      // Fallback: cerca nel database
      const dbWorkflow = await this.getWorkflowFromDatabase(tenantId, workflowId);
      if (!dbWorkflow) throw error;
      
      return dbWorkflow;
    }
  }

  /**
   * Lista executions per tenant
   */
  async getExecutionsForTenant(tenantId: string, options?: { 
    workflowId?: string; 
    limit?: number; 
    status?: string 
  }): Promise<NormalizedExecution[]> {
    const client = this.getClientForTenant(tenantId);

    try {
      const rawExecutions = await client.getExecutions();
      let normalized = rawExecutions.map(exec => this.normalizeExecution(exec, tenantId));

      // Applica filtri
      if (options?.workflowId) {
        normalized = normalized.filter(e => e.workflowId === options.workflowId);
      }
      if (options?.status) {
        normalized = normalized.filter(e => e.status === options.status);
      }
      if (options?.limit) {
        normalized = normalized.slice(0, options.limit);
      }

      return normalized;
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`❌ Errore caricamento executions per ${tenantId}:`, errorMessage);
      
      // Fallback: cerca nel database
      return await this.getExecutionsFromDatabase(tenantId, options);
    }
  }

  /**
   * Esegue workflow per tenant specifico
   */
  async executeWorkflowForTenant(
    tenantId: string, 
    workflowId: string, 
    data?: Record<string, any>
  ): Promise<any> {
    const client = this.getClientForTenant(tenantId);
    const capabilities = this.getCapabilitiesForTenant(tenantId);

    // Adatta i dati in base alle capabilities del tenant
    const adaptedData = this.adaptExecutionData(data, capabilities);

    return await client.executeWorkflow(workflowId, adaptedData);
  }

  /**
   * Crea workflow per tenant con schema adattivo
   */
  async createWorkflowForTenant(
    tenantId: string, 
    workflow: Record<string, any>
  ): Promise<NormalizedWorkflow> {
    const client = this.getClientForTenant(tenantId);
    const capabilities = this.getCapabilitiesForTenant(tenantId);

    // Adatta schema workflow alle capabilities del tenant
    const adaptedWorkflow = this.adaptWorkflowSchema(workflow, capabilities);

    const created = await client.createWorkflow(adaptedWorkflow);
    return this.normalizeWorkflow(created, tenantId);
  }

  /**
   * Sincronizza tutti i dati per un tenant nel database multi-tenant
   */
  async syncTenantData(tenantId: string): Promise<{
    workflowsSynced: number;
    executionsSynced: number;
    errors: string[];
  }> {
    const results = {
      workflowsSynced: 0,
      executionsSynced: 0,
      errors: [] as string[]
    };

    try {
      console.log(`🔄 Sync tenant: ${tenantId}`);

      // 1. Sync workflows
      const workflows = await this.getWorkflowsForTenant(tenantId);
      for (const workflow of workflows) {
        try {
          const wasUpdated = await this.saveWorkflowToDatabase(workflow);
          if (wasUpdated) {
            results.workflowsSynced++;
          }
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          results.errors.push(`Workflow ${workflow.id}: ${errorMessage}`);
        }
      }

      // 2. Sync recent executions
      const executions = await this.getExecutionsForTenant(tenantId, { limit: 1000 });
      for (const execution of executions) {
        try {
          await this.saveExecutionToDatabase(execution);
          results.executionsSynced++;
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          results.errors.push(`Execution ${execution.id}: ${errorMessage}`);
        }
      }

      // 3. Update tenant sync timestamp
      await this.db.query(`
        UPDATE tenants 
        SET last_sync_at = CURRENT_TIMESTAMP,
            total_workflows = $2,
            total_executions = $3
        WHERE id = $1
      `, [tenantId, results.workflowsSynced, results.executionsSynced]);

      console.log(`✅ Sync completato: ${results.workflowsSynced} workflows, ${results.executionsSynced} executions`);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      results.errors.push(`Sync generale: ${errorMessage}`);
    }

    return results;
  }

  // =====================================================
  // METODI PRIVATI - Normalizzazione e Adattamento
  // =====================================================

  /**
   * Normalizza workflow da qualsiasi formato API a formato standard
   */
  private normalizeWorkflow(rawWorkflow: any, tenantId: string): NormalizedWorkflow {
    return {
      id: rawWorkflow.id,
      name: rawWorkflow.name,
      active: Boolean(rawWorkflow.active),
      createdAt: rawWorkflow.createdAt || rawWorkflow.created_at,
      updatedAt: rawWorkflow.updatedAt || rawWorkflow.updated_at,
      tenantId,
      rawData: rawWorkflow,
      // Campi calcolati
      nodeCount: rawWorkflow.nodes ? rawWorkflow.nodes.length : 0,
      hasWebhook: this.detectWebhookInWorkflow(rawWorkflow),
      isArchived: Boolean(rawWorkflow.isArchived || rawWorkflow.is_archived)
    };
  }

  /**
   * Normalizza execution da qualsiasi formato API
   */
  private normalizeExecution(rawExecution: any, tenantId: string): NormalizedExecution {
    return {
      id: rawExecution.id,
      workflowId: rawExecution.workflowId || rawExecution.workflow_id,
      startedAt: rawExecution.startedAt || rawExecution.started_at,
      status: rawExecution.status,
      mode: rawExecution.mode,
      tenantId,
      rawData: rawExecution,
      // Campi calcolati
      finished: Boolean(rawExecution.finished),
      stoppedAt: rawExecution.stoppedAt || rawExecution.stopped_at,
      durationMs: this.calculateExecutionDuration(rawExecution),
      hasError: rawExecution.status === 'error'
    };
  }

  /**
   * Rileva se un workflow ha nodi webhook
   */
  private detectWebhookInWorkflow(workflow: any): boolean {
    if (!workflow.nodes) return false;
    
    return workflow.nodes.some((node: any) => 
      node.type && (
        node.type.includes('webhook') ||
        node.type.includes('Webhook') ||
        node.type === 'n8n-nodes-base.webhook'
      )
    );
  }

  /**
   * Calcola durata execution da timestamps
   */
  private calculateExecutionDuration(execution: any): number | undefined {
    const startedAt = execution.startedAt || execution.started_at;
    const stoppedAt = execution.stoppedAt || execution.stopped_at;
    
    if (!startedAt || !stoppedAt) return undefined;
    
    const start = new Date(startedAt).getTime();
    const stop = new Date(stoppedAt).getTime();
    
    return stop - start;
  }

  /**
   * Adatta dati di esecuzione alle capabilities del tenant
   */
  private adaptExecutionData(data: Record<string, any> | undefined, capabilities: TenantCapabilities | null): Record<string, any> | undefined {
    if (!data) return data;
    
    // Se il tenant non supporta certe funzioni, rimuovile
    const adapted = { ...data };
    
    if (capabilities && !capabilities.supportsWebhooks) {
      delete adapted.webhook;
      delete adapted.webhookData;
    }
    
    return adapted;
  }

  /**
   * Adatta schema workflow alle capabilities del tenant
   */
  private adaptWorkflowSchema(workflow: Record<string, any>, capabilities: TenantCapabilities | null): Record<string, any> {
    const adapted = { ...workflow };
    
    if (capabilities) {
      // Se non supporta progetti, rimuovi projectId
      if (!capabilities.supportsProjects) {
        delete adapted.projectId;
        delete adapted.project;
      }
      
      // Se non supporta tags, rimuovi tags
      if (!capabilities.supportsTags) {
        delete adapted.tags;
      }
    }
    
    return adapted;
  }

  // =====================================================
  // METODI DATABASE
  // =====================================================

  /**
   * Salva configurazione tenant nel database
   */
  private async saveTenantConfig(config: TenantConfig): Promise<void> {
    await this.db.query(`
      INSERT INTO tenants (id, name, n8n_api_url, n8n_version, api_capabilities, schema_signature)
      VALUES ($1, $2, $3, $4, $5, $6)
      ON CONFLICT (id) DO UPDATE SET
        n8n_api_url = $3,
        n8n_version = $4,
        api_capabilities = $5,
        schema_signature = $6,
        updated_at = CURRENT_TIMESTAMP
    `, [
      config.tenantId,
      `Tenant ${config.tenantId}`,
      config.apiUrl,
      config.n8nVersion,
      JSON.stringify(config.capabilities || {}),
      config.schemaSignature
    ]);
  }

  /**
   * Salva workflow normalizzato nel database multi-tenant
   */
  private async saveWorkflowToDatabase(workflow: NormalizedWorkflow): Promise<boolean> {
    // Check if workflow actually changed by comparing raw_data and updatedAt
    const existingResult = await this.db.query(`
      SELECT raw_data, updated_at FROM tenant_workflows 
      WHERE id = $1 AND tenant_id = $2
    `, [workflow.id, workflow.tenantId]);
    
    const newRawData = JSON.stringify(workflow.rawData);
    const isNewWorkflow = existingResult.rows.length === 0;
    
    let hasChanged = isNewWorkflow;
    if (!isNewWorkflow) {
      const existingRawData = JSON.stringify(existingResult.rows[0].raw_data);
      const existingUpdatedAt = new Date(existingResult.rows[0].updated_at);
      const newUpdatedAt = workflow.updatedAt ? new Date(workflow.updatedAt) : new Date();
      
      // Consider changed if: raw_data differs OR n8n updatedAt is newer
      hasChanged = existingRawData !== newRawData || newUpdatedAt > existingUpdatedAt;
    }
    
    if (!hasChanged) {
      console.log(`📄 Workflow ${workflow.id} unchanged, skipping update`);
      return false;
    }
    
    await this.db.query(`
      INSERT INTO tenant_workflows (id, tenant_id, name, active, created_at, updated_at, raw_data, last_synced_at)
      VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)
      ON CONFLICT (tenant_id, id) DO UPDATE SET
        name = $3,
        active = $4,
        updated_at = $6,
        raw_data = $7,
        last_synced_at = CURRENT_TIMESTAMP
    `, [
      workflow.id,
      workflow.tenantId,
      workflow.name,
      workflow.active,
      workflow.createdAt ? new Date(workflow.createdAt) : new Date(),
      workflow.updatedAt ? new Date(workflow.updatedAt) : new Date(),
      newRawData
    ]);
    
    console.log(`✅ Workflow ${workflow.id} updated successfully`);
    return true;
  }

  /**
   * Salva execution normalizzata nel database multi-tenant
   */
  private async saveExecutionToDatabase(execution: NormalizedExecution): Promise<void> {
    await this.db.query(`
      INSERT INTO tenant_executions (id, tenant_id, workflow_id, started_at, status, mode, raw_data, last_synced_at)
      VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)
      ON CONFLICT (tenant_id, id) DO UPDATE SET
        status = $5,
        raw_data = $7,
        last_synced_at = CURRENT_TIMESTAMP
    `, [
      execution.id,
      execution.tenantId,
      execution.workflowId,
      new Date(execution.startedAt),
      execution.status,
      execution.mode,
      JSON.stringify(execution.rawData)
    ]);
  }

  /**
   * Recupera workflows dal database come fallback
   */
  private async getWorkflowsFromDatabase(tenantId: string): Promise<NormalizedWorkflow[]> {
    const workflows = await this.db.getMany(`
      SELECT id, name, active, created_at, updated_at, raw_data
      FROM tenant_workflows 
      WHERE tenant_id = $1
      ORDER BY updated_at DESC
    `, [tenantId]);

    return workflows.map(w => ({
      id: w.id,
      name: w.name,
      active: w.active,
      createdAt: w.created_at?.toISOString(),
      updatedAt: w.updated_at?.toISOString(),
      tenantId,
      rawData: w.raw_data,
      nodeCount: w.raw_data?.nodes?.length || 0,
      hasWebhook: this.detectWebhookInWorkflow(w.raw_data),
      isArchived: Boolean(w.raw_data?.isArchived)
    }));
  }

  /**
   * Recupera workflow specifico dal database
   */
  private async getWorkflowFromDatabase(tenantId: string, workflowId: string): Promise<NormalizedWorkflow | null> {
    const workflow = await this.db.getOne(`
      SELECT id, name, active, created_at, updated_at, raw_data
      FROM tenant_workflows 
      WHERE tenant_id = $1 AND id = $2
    `, [tenantId, workflowId]);

    if (!workflow) return null;

    return {
      id: workflow.id,
      name: workflow.name,
      active: workflow.active,
      createdAt: workflow.created_at?.toISOString(),
      updatedAt: workflow.updated_at?.toISOString(),
      tenantId,
      rawData: workflow.raw_data,
      nodeCount: workflow.raw_data?.nodes?.length || 0,
      hasWebhook: this.detectWebhookInWorkflow(workflow.raw_data),
      isArchived: Boolean(workflow.raw_data?.isArchived)
    };
  }

  /**
   * Recupera executions dal database con filtri
   */
  private async getExecutionsFromDatabase(
    tenantId: string, 
    options?: { workflowId?: string; limit?: number; status?: string }
  ): Promise<NormalizedExecution[]> {
    let query = `
      SELECT id, workflow_id, started_at, status, mode, raw_data
      FROM tenant_executions 
      WHERE tenant_id = $1
    `;
    const params: any[] = [tenantId];

    if (options?.workflowId) {
      query += ` AND workflow_id = $${params.length + 1}`;
      params.push(options.workflowId);
    }

    if (options?.status) {
      query += ` AND status = $${params.length + 1}`;
      params.push(options.status);
    }

    query += ` ORDER BY started_at DESC`;

    if (options?.limit) {
      query += ` LIMIT $${params.length + 1}`;
      params.push(options.limit);
    }

    const executions = await this.db.getMany(query, params);

    return executions.map(e => ({
      id: e.id,
      workflowId: e.workflow_id,
      startedAt: e.started_at.toISOString(),
      status: e.status,
      mode: e.mode,
      tenantId,
      rawData: e.raw_data,
      finished: Boolean(e.raw_data?.finished),
      stoppedAt: e.raw_data?.stoppedAt,
      durationMs: this.calculateExecutionDuration(e.raw_data),
      hasError: e.status === 'error'
    }));
  }
}

/**
 * Factory function per creare client multi-tenant
 */
export function createMultiTenantApiClient(): MultiTenantApiClient {
  return new MultiTenantApiClient();
}