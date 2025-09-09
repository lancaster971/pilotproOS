/**
 * Workflow Repository
 * 
 * Repository per la gestione dei workflow nel database.
 * Fornisce metodi specifici per query e operazioni sui workflow.
 */

import { BaseRepository } from './base.repository.js';
import {
  WorkflowModel,
  WorkflowNodeModel,
  WorkflowConnectionModel,
  WorkflowAuditLogModel,
  WorkflowSearchParams,
  WorkflowOrderBy,
  WorkflowStats,
  WorkflowHealthView,
  PaginatedResult
} from '../models/index.js';

/**
 * Repository per la gestione dei workflow
 */
export class WorkflowRepository extends BaseRepository<WorkflowModel> {
  constructor() {
    super('workflows');
  }

  /**
   * Trova workflow per ID con tutti i dettagli (nodi e connessioni)
   * 
   * @param workflowId - ID del workflow
   * @returns Workflow con nodi e connessioni o null
   */
  async findByIdWithDetails(workflowId: string): Promise<{
    workflow: WorkflowModel;
    nodes: WorkflowNodeModel[];
    connections: WorkflowConnectionModel[];
  } | null> {
    const workflow = await this.findById(workflowId);
    if (!workflow) {
      return null;
    }

    // Ottieni nodi e connessioni in parallelo
    const [nodes, connections] = await Promise.all([
      this.getWorkflowNodes(workflowId),
      this.getWorkflowConnections(workflowId)
    ]);

    return { workflow, nodes, connections };
  }

  /**
   * Trova workflow attivi
   * 
   * @param limit - Limite risultati
   * @returns Array di workflow attivi
   */
  async findActive(limit?: number): Promise<WorkflowModel[]> {
    let query = `
      SELECT * FROM workflows 
      WHERE active = true 
      ORDER BY last_execution_at DESC NULLS LAST
    `;
    
    if (limit) {
      query += ` LIMIT ${limit}`;
    }
    
    return await this.db.getMany<WorkflowModel>(query);
  }

  /**
   * Trova workflow inattivi da più di X giorni
   * 
   * @param days - Giorni di inattività
   * @returns Array di workflow inattivi
   */
  async findUnused(days: number): Promise<WorkflowModel[]> {
    const query = `
      SELECT * FROM workflows 
      WHERE last_execution_at < NOW() - INTERVAL '${days} days'
         OR last_execution_at IS NULL
      ORDER BY last_execution_at ASC NULLS FIRST
    `;
    
    return await this.db.getMany<WorkflowModel>(query);
  }

  /**
   * Cerca workflow con filtri avanzati
   * 
   * @param params - Parametri di ricerca
   * @returns Risultato paginato
   */
  async search(params: WorkflowSearchParams): Promise<PaginatedResult<WorkflowModel>> {
    const conditions: string[] = [];
    const queryParams: any[] = [];
    let paramIndex = 1;

    // Costruisci condizioni WHERE
    if (params.active !== undefined) {
      conditions.push(`active = $${paramIndex++}`);
      queryParams.push(params.active);
    }

    if (params.minReliability !== undefined) {
      conditions.push(`reliability_score >= $${paramIndex++}`);
      queryParams.push(params.minReliability);
    }

    if (params.maxComplexity !== undefined) {
      conditions.push(`complexity_score <= $${paramIndex++}`);
      queryParams.push(params.maxComplexity);
    }

    if (params.hasErrors) {
      conditions.push(`failure_count > 0`);
    }

    if (params.unused) {
      conditions.push(`(last_execution_at < NOW() - INTERVAL '30 days' OR last_execution_at IS NULL)`);
    }

    if (params.tag) {
      conditions.push(`
        EXISTS (
          SELECT 1 FROM workflow_tags wt
          JOIN tags t ON wt.tag_id = t.id
          WHERE wt.workflow_id = workflows.id
            AND t.name = $${paramIndex++}
        )
      `);
      queryParams.push(params.tag);
    }

    // Costruisci query base
    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
    
    // Query per conteggio totale
    const countQuery = `SELECT COUNT(*) as total FROM workflows ${whereClause}`;
    const countResult = await this.db.getOne<{ total: string }>(countQuery, queryParams);
    const total = parseInt(countResult?.total || '0');

    // Query per dati con paginazione
    const orderBy = params.orderBy || WorkflowOrderBy.UPDATED_AT;
    const orderDir = params.orderDir || 'DESC';
    const limit = params.limit || 20;
    const offset = params.offset || 0;

    const dataQuery = `
      SELECT * FROM workflows 
      ${whereClause}
      ORDER BY ${orderBy} ${orderDir}
      LIMIT ${limit} OFFSET ${offset}
    `;

    const data = await this.db.getMany<WorkflowModel>(dataQuery, queryParams);

    return {
      data,
      total,
      page: Math.floor(offset / limit) + 1,
      pageSize: limit,
      totalPages: Math.ceil(total / limit),
      hasNext: offset + limit < total,
      hasPrev: offset > 0
    };
  }

  /**
   * Ottiene i nodi di un workflow
   * 
   * @param workflowId - ID del workflow
   * @returns Array di nodi
   */
  async getWorkflowNodes(workflowId: string): Promise<WorkflowNodeModel[]> {
    const query = `
      SELECT * FROM workflow_nodes 
      WHERE workflow_id = $1
      ORDER BY node_name
    `;
    
    return await this.db.getMany<WorkflowNodeModel>(query, [workflowId]);
  }

  /**
   * Ottiene le connessioni di un workflow
   * 
   * @param workflowId - ID del workflow
   * @returns Array di connessioni
   */
  async getWorkflowConnections(workflowId: string): Promise<WorkflowConnectionModel[]> {
    const query = `
      SELECT * FROM workflow_connections 
      WHERE workflow_id = $1
      ORDER BY id
    `;
    
    return await this.db.getMany<WorkflowConnectionModel>(query, [workflowId]);
  }

  /**
   * Ottiene l'audit log di un workflow
   * 
   * @param workflowId - ID del workflow
   * @param limit - Limite risultati
   * @returns Array di audit log entries
   */
  async getAuditLog(workflowId: string, limit: number = 50): Promise<WorkflowAuditLogModel[]> {
    const query = `
      SELECT * FROM workflow_audit_log 
      WHERE workflow_id = $1
      ORDER BY performed_at DESC
      LIMIT $2
    `;
    
    return await this.db.getMany<WorkflowAuditLogModel>(query, [workflowId, limit]);
  }

  /**
   * Aggiorna metriche di un workflow
   * 
   * @param workflowId - ID del workflow
   * @param metrics - Metriche da aggiornare
   * @returns Numero di record aggiornati
   */
  async updateMetrics(workflowId: string, metrics: {
    execution_count?: number;
    success_count?: number;
    failure_count?: number;
    avg_duration_ms?: number;
    last_execution_at?: Date;
  }): Promise<number> {
    const fields: string[] = [];
    const values: any[] = [workflowId];
    let paramIndex = 2;

    if (metrics.execution_count !== undefined) {
      fields.push(`execution_count = $${paramIndex++}`);
      values.push(metrics.execution_count);
    }

    if (metrics.success_count !== undefined) {
      fields.push(`success_count = $${paramIndex++}`);
      values.push(metrics.success_count);
    }

    if (metrics.failure_count !== undefined) {
      fields.push(`failure_count = $${paramIndex++}`);
      values.push(metrics.failure_count);
    }

    if (metrics.avg_duration_ms !== undefined) {
      fields.push(`avg_duration_ms = $${paramIndex++}`);
      values.push(metrics.avg_duration_ms);
    }

    if (metrics.last_execution_at !== undefined) {
      fields.push(`last_execution_at = $${paramIndex++}`);
      values.push(metrics.last_execution_at);
    }

    if (fields.length === 0) {
      return 0;
    }

    const query = `
      UPDATE workflows 
      SET ${fields.join(', ')}, updated_at = CURRENT_TIMESTAMP
      WHERE id = $1
    `;

    return await this.db.update(query, values);
  }

  /**
   * Aggiorna scores di un workflow
   * 
   * @param workflowId - ID del workflow
   * @param scores - Scores da aggiornare
   * @returns Numero di record aggiornati
   */
  async updateScores(workflowId: string, scores: {
    complexity_score?: number;
    reliability_score?: number;
    efficiency_score?: number;
    health_score?: number;
  }): Promise<number> {
    const fields: string[] = [];
    const values: any[] = [workflowId];
    let paramIndex = 2;

    Object.entries(scores).forEach(([key, value]) => {
      if (value !== undefined) {
        fields.push(`${key} = $${paramIndex++}`);
        values.push(value);
      }
    });

    if (fields.length === 0) {
      return 0;
    }

    const query = `
      UPDATE workflows 
      SET ${fields.join(', ')}, updated_at = CURRENT_TIMESTAMP
      WHERE id = $1
    `;

    return await this.db.update(query, values);
  }

  /**
   * Attiva un workflow
   * 
   * @param workflowId - ID del workflow
   * @returns true se attivato con successo
   */
  async activate(workflowId: string): Promise<boolean> {
    const query = `
      UPDATE workflows 
      SET active = true, updated_at = CURRENT_TIMESTAMP
      WHERE id = $1
    `;
    
    const result = await this.db.update(query, [workflowId]);
    return result > 0;
  }

  /**
   * Disattiva un workflow
   * 
   * @param workflowId - ID del workflow
   * @returns true se disattivato con successo
   */
  async deactivate(workflowId: string): Promise<boolean> {
    const query = `
      UPDATE workflows 
      SET active = false, updated_at = CURRENT_TIMESTAMP
      WHERE id = $1
    `;
    
    const result = await this.db.update(query, [workflowId]);
    return result > 0;
  }

  /**
   * Ottiene statistiche aggregate dei workflow
   * 
   * @returns Statistiche workflow
   */
  async getStats(): Promise<WorkflowStats> {
    const query = `
      SELECT 
        COUNT(*) as total_workflows,
        COUNT(CASE WHEN active = true THEN 1 END) as active_workflows,
        COUNT(CASE WHEN active = false THEN 1 END) as inactive_workflows,
        COUNT(CASE WHEN is_archived = true THEN 1 END) as archived_workflows,
        AVG(complexity_score) as avg_complexity_score,
        AVG(reliability_score) as avg_reliability_score,
        AVG(health_score) as avg_health_score,
        SUM(execution_count) as total_executions,
        AVG(CASE WHEN execution_count > 0 
          THEN success_count::float / execution_count * 100 
          ELSE 0 END) as success_rate,
        COUNT(CASE WHEN failure_count > 0 THEN 1 END) as workflows_with_errors,
        COUNT(CASE WHEN last_execution_at < NOW() - INTERVAL '30 days' 
          OR last_execution_at IS NULL THEN 1 END) as unused_workflows
      FROM workflows
    `;

    const result = await this.db.getOne<any>(query);
    
    return {
      totalWorkflows: parseInt(result?.total_workflows || '0'),
      activeWorkflows: parseInt(result?.active_workflows || '0'),
      inactiveWorkflows: parseInt(result?.inactive_workflows || '0'),
      archivedWorkflows: parseInt(result?.archived_workflows || '0'),
      avgComplexityScore: parseFloat(result?.avg_complexity_score || '0'),
      avgReliabilityScore: parseFloat(result?.avg_reliability_score || '0'),
      avgHealthScore: parseFloat(result?.avg_health_score || '0'),
      totalExecutions: parseInt(result?.total_executions || '0'),
      successRate: parseFloat(result?.success_rate || '0'),
      workflowsWithErrors: parseInt(result?.workflows_with_errors || '0'),
      unusedWorkflows: parseInt(result?.unused_workflows || '0')
    };
  }

  /**
   * Ottiene workflow dalla vista health
   * 
   * @param healthStatus - Filtra per stato salute
   * @returns Array di workflow con info salute
   */
  async getWorkflowHealth(healthStatus?: string): Promise<WorkflowHealthView[]> {
    let query = `SELECT * FROM workflow_health`;
    const params: any[] = [];
    
    if (healthStatus) {
      query += ` WHERE health_status = $1`;
      params.push(healthStatus);
    }
    
    query += ` ORDER BY health_score ASC`;
    
    return await this.db.getMany<WorkflowHealthView>(query, params);
  }

  /**
   * Registra un'azione nell'audit log
   * 
   * @param auditEntry - Entry da registrare
   * @returns Entry creata
   */
  async logAuditAction(auditEntry: Partial<WorkflowAuditLogModel>): Promise<WorkflowAuditLogModel> {
    const query = `
      INSERT INTO workflow_audit_log (
        workflow_id, action, user_id, user_email,
        changes, old_values, new_values,
        version_before, version_after,
        ip_address, user_agent, performed_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
      RETURNING *
    `;

    const values = [
      auditEntry.workflow_id,
      auditEntry.action,
      auditEntry.user_id || null,
      auditEntry.user_email || null,
      JSON.stringify(auditEntry.changes || {}),
      JSON.stringify(auditEntry.old_values || {}),
      JSON.stringify(auditEntry.new_values || {}),
      auditEntry.version_before || null,
      auditEntry.version_after || null,
      auditEntry.ip_address || null,
      auditEntry.user_agent || null,
      auditEntry.performed_at || new Date()
    ];

    return await this.db.insert<WorkflowAuditLogModel>(query, values);
  }

  /**
   * Sincronizza workflow da API n8n
   * 
   * @param workflowData - Dati del workflow da API
   * @returns Workflow sincronizzato
   */
  async syncFromApi(workflowData: any): Promise<WorkflowModel> {
    const existingWorkflow = await this.findById(workflowData.id);
    
    if (existingWorkflow) {
      // Aggiorna workflow esistente
      await this.update(workflowData.id, {
        name: workflowData.name,
        description: workflowData.description,
        active: workflowData.active,
        settings: workflowData.settings,
        static_data: workflowData.staticData,
        node_count: workflowData.nodes?.length || 0,
        connection_count: workflowData.connections ? Object.keys(workflowData.connections).length : 0,
        updated_at: new Date()
      });
      
      return (await this.findById(workflowData.id))!;
    } else {
      // Crea nuovo workflow
      return await this.create({
        id: workflowData.id,
        name: workflowData.name,
        description: workflowData.description,
        active: workflowData.active,
        settings: workflowData.settings,
        static_data: workflowData.staticData,
        node_count: workflowData.nodes?.length || 0,
        connection_count: workflowData.connections ? Object.keys(workflowData.connections).length : 0,
        created_at: new Date(workflowData.createdAt),
        updated_at: new Date(workflowData.updatedAt)
      });
    }
  }
}