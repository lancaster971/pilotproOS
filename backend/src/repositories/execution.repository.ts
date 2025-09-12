/**
 * Execution Repository
 * 
 * Repository per la gestione delle esecuzioni nel database.
 * Fornisce metodi specifici per query e operazioni sulle esecuzioni.
 */

import { BaseRepository } from './base.repository.js';
import {
  ExecutionModel,
  ExecutionStatus,
  ExecutionMode,
  ExecutionNodeResultModel,
  ErrorLogModel,
  ErrorSeverity,
  ExecutionSearchParams,
  ExecutionOrderBy,
  ExecutionStats,
  ExecutionTimeStats,
  ExecutionTrendsView,
  PaginatedResult
} from '../models/index.js';

/**
 * Repository per la gestione delle esecuzioni
 */
export class ExecutionRepository extends BaseRepository<ExecutionModel> {
  constructor() {
    super('executions');
  }

  /**
   * Trova esecuzioni per workflow ID
   * 
   * @param workflowId - ID del workflow
   * @param limit - Limite risultati
   * @returns Array di esecuzioni
   */
  async findByWorkflowId(workflowId: string, limit?: number): Promise<ExecutionModel[]> {
    let query = `
      SELECT * FROM executions 
      WHERE workflow_id = $1
      ORDER BY started_at DESC
    `;
    
    if (limit) {
      query += ` LIMIT ${limit}`;
    }
    
    return await this.db.getMany<ExecutionModel>(query, [workflowId]);
  }

  /**
   * Trova esecuzioni in corso
   * 
   * @returns Array di esecuzioni running
   */
  async findRunning(): Promise<ExecutionModel[]> {
    const query = `
      SELECT * FROM executions 
      WHERE status = $1
      ORDER BY started_at DESC
    `;
    
    return await this.db.getMany<ExecutionModel>(query, [ExecutionStatus.RUNNING]);
  }

  /**
   * Trova esecuzioni fallite recenti
   * 
   * @param hours - Ore da considerare
   * @param limit - Limite risultati
   * @returns Array di esecuzioni fallite
   */
  async findRecentFailures(hours: number = 24, limit?: number): Promise<ExecutionModel[]> {
    let query = `
      SELECT * FROM executions 
      WHERE status = $1
        AND started_at > NOW() - INTERVAL '${hours} hours'
      ORDER BY started_at DESC
    `;
    
    if (limit) {
      query += ` LIMIT ${limit}`;
    }
    
    return await this.db.getMany<ExecutionModel>(query, [ExecutionStatus.ERROR]);
  }

  /**
   * Cerca esecuzioni con filtri avanzati
   * 
   * @param params - Parametri di ricerca
   * @returns Risultato paginato
   */
  async search(params: ExecutionSearchParams): Promise<PaginatedResult<ExecutionModel>> {
    const conditions: string[] = [];
    const queryParams: any[] = [];
    let paramIndex = 1;

    // Costruisci condizioni WHERE
    if (params.workflow_id) {
      conditions.push(`workflow_id = $${paramIndex++}`);
      queryParams.push(params.workflow_id);
    }

    if (params.status) {
      conditions.push(`status = $${paramIndex++}`);
      queryParams.push(params.status);
    }

    if (params.mode) {
      conditions.push(`mode = $${paramIndex++}`);
      queryParams.push(params.mode);
    }

    if (params.startedAfter) {
      conditions.push(`started_at >= $${paramIndex++}`);
      queryParams.push(params.startedAfter);
    }

    if (params.startedBefore) {
      conditions.push(`started_at <= $${paramIndex++}`);
      queryParams.push(params.startedBefore);
    }

    if (params.hasError) {
      conditions.push(`(status = '${ExecutionStatus.ERROR}' OR error_message IS NOT NULL)`);
    }

    if (params.minDuration !== undefined) {
      conditions.push(`duration_ms >= $${paramIndex++}`);
      queryParams.push(params.minDuration);
    }

    if (params.maxDuration !== undefined) {
      conditions.push(`duration_ms <= $${paramIndex++}`);
      queryParams.push(params.maxDuration);
    }

    // Costruisci query
    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
    
    // Conteggio totale
    const countQuery = `SELECT COUNT(*) as total FROM executions ${whereClause}`;
    const countResult = await this.db.getOne<{ total: string }>(countQuery, queryParams);
    const total = parseInt(countResult?.total || '0');

    // Query dati con paginazione
    const orderBy = params.orderBy || ExecutionOrderBy.STARTED_AT;
    const orderDir = params.orderDir || 'DESC';
    const limit = params.limit || 20;
    const offset = params.offset || 0;

    const dataQuery = `
      SELECT * FROM executions 
      ${whereClause}
      ORDER BY ${orderBy} ${orderDir}
      LIMIT ${limit} OFFSET ${offset}
    `;

    const data = await this.db.getMany<ExecutionModel>(dataQuery, queryParams);

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
   * Ottiene risultati dei nodi per un'esecuzione
   * 
   * @param executionId - ID dell'esecuzione
   * @returns Array di risultati nodi
   */
  async getNodeResults(executionId: string): Promise<ExecutionNodeResultModel[]> {
    const query = `
      SELECT * FROM execution_node_results 
      WHERE execution_id = $1
      ORDER BY started_at
    `;
    
    return await this.db.getMany<ExecutionNodeResultModel>(query, [executionId]);
  }

  /**
   * Salva risultato di un nodo
   * 
   * @param nodeResult - Risultato del nodo da salvare
   * @returns Risultato salvato
   */
  async saveNodeResult(nodeResult: Partial<ExecutionNodeResultModel>): Promise<ExecutionNodeResultModel> {
    const query = `
      INSERT INTO execution_node_results (
        execution_id, workflow_id, node_id, node_type,
        started_at, finished_at, execution_time_ms,
        status, items_input, items_output, data,
        error_message, error_details
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
      RETURNING *
    `;

    const values = [
      nodeResult.execution_id,
      nodeResult.workflow_id,
      nodeResult.node_id,
      nodeResult.node_type,
      nodeResult.started_at,
      nodeResult.finished_at,
      nodeResult.execution_time_ms,
      nodeResult.status,
      nodeResult.items_input || 0,
      nodeResult.items_output || 0,
      JSON.stringify(nodeResult.data || {}),
      nodeResult.error_message,
      JSON.stringify(nodeResult.error_details || {})
    ];

    return await this.db.insert<ExecutionNodeResultModel>(query, values);
  }

  /**
   * Aggiorna stato di un'esecuzione
   * 
   * @param executionId - ID dell'esecuzione
   * @param status - Nuovo stato
   * @param additionalData - Dati aggiuntivi da aggiornare
   * @returns Numero di record aggiornati
   */
  async updateStatus(
    executionId: string, 
    status: ExecutionStatus,
    additionalData?: {
      finished_at?: Date;
      duration_ms?: number;
      error_message?: string;
      error_node?: string;
      error_stack?: string;
    }
  ): Promise<number> {
    const fields = [`status = $2`];
    const values: any[] = [executionId, status];
    let paramIndex = 3;

    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        if (value !== undefined) {
          fields.push(`${key} = $${paramIndex++}`);
          values.push(value);
        }
      });
    }

    const query = `
      UPDATE executions 
      SET ${fields.join(', ')}
      WHERE id = $1
    `;

    return await this.db.update(query, values);
  }

  /**
   * Registra un errore
   * 
   * @param error - Errore da registrare
   * @returns Errore registrato
   */
  async logError(error: Partial<ErrorLogModel>): Promise<ErrorLogModel> {
    const query = `
      INSERT INTO error_logs (
        workflow_id, execution_id, node_id,
        error_type, error_code, error_message, error_stack,
        context, severity, is_resolved, occurred_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
      RETURNING *
    `;

    const values = [
      error.workflow_id,
      error.execution_id || null,
      error.node_id || null,
      error.error_type || 'Unknown',
      error.error_code || null,
      error.error_message,
      error.error_stack || null,
      JSON.stringify(error.context || {}),
      error.severity || ErrorSeverity.MEDIUM,
      error.is_resolved || false,
      error.occurred_at || new Date()
    ];

    return await this.db.insert<ErrorLogModel>(query, values);
  }

  /**
   * Ottiene errori non risolti
   * 
   * @param workflowId - Filtra per workflow (opzionale)
   * @param limit - Limite risultati
   * @returns Array di errori non risolti
   */
  async getUnresolvedErrors(workflowId?: string, limit: number = 50): Promise<ErrorLogModel[]> {
    let query = `
      SELECT * FROM error_logs 
      WHERE is_resolved = false
    `;
    
    const params: any[] = [];
    if (workflowId) {
      query += ` AND workflow_id = $1`;
      params.push(workflowId);
    }
    
    query += ` ORDER BY occurred_at DESC LIMIT ${limit}`;
    
    return await this.db.getMany<ErrorLogModel>(query, params);
  }

  /**
   * Marca errori come risolti
   * 
   * @param errorIds - IDs degli errori da risolvere
   * @param resolutionNotes - Note sulla risoluzione
   * @returns Numero di errori risolti
   */
  async resolveErrors(errorIds: number[], resolutionNotes?: string): Promise<number> {
    const query = `
      UPDATE error_logs 
      SET is_resolved = true,
          resolved_at = CURRENT_TIMESTAMP,
          resolution_notes = $2
      WHERE id = ANY($1)
    `;
    
    return await this.db.update(query, [errorIds, resolutionNotes || null]);
  }

  /**
   * Ottiene statistiche delle esecuzioni
   * 
   * @param workflowId - Filtra per workflow (opzionale)
   * @param days - Giorni da considerare
   * @returns Statistiche esecuzioni
   */
  async getStats(workflowId?: string, days: number = 7): Promise<ExecutionStats> {
    let query = `
      SELECT 
        COUNT(*) as total_executions,
        COUNT(CASE WHEN status = '${ExecutionStatus.RUNNING}' THEN 1 END) as running_executions,
        COUNT(CASE WHEN status = '${ExecutionStatus.SUCCESS}' THEN 1 END) as successful_executions,
        COUNT(CASE WHEN status = '${ExecutionStatus.ERROR}' THEN 1 END) as failed_executions,
        AVG(duration_ms) as avg_duration_ms,
        MIN(duration_ms) as min_duration_ms,
        MAX(duration_ms) as max_duration_ms,
        AVG(data_in_kb) as avg_data_in_kb,
        AVG(data_out_kb) as avg_data_out_kb,
        SUM(nodes_executed) as total_nodes_executed
      FROM executions
      WHERE started_at > NOW() - INTERVAL '${days} days'
    `;
    
    const params: any[] = [];
    if (workflowId) {
      query += ` AND workflow_id = $1`;
      params.push(workflowId);
    }

    const result = await this.db.getOne<any>(query, params);
    
    const total = parseInt(result?.total_executions || '0');
    const successful = parseInt(result?.successful_executions || '0');
    const failed = parseInt(result?.failed_executions || '0');
    
    return {
      totalExecutions: total,
      runningExecutions: parseInt(result?.running_executions || '0'),
      successfulExecutions: successful,
      failedExecutions: failed,
      avgDurationMs: parseFloat(result?.avg_duration_ms || '0'),
      minDurationMs: parseFloat(result?.min_duration_ms || '0'),
      maxDurationMs: parseFloat(result?.max_duration_ms || '0'),
      successRate: total > 0 ? (successful / total) * 100 : 0,
      errorRate: total > 0 ? (failed / total) * 100 : 0,
      avgDataInKb: parseFloat(result?.avg_data_in_kb || '0'),
      avgDataOutKb: parseFloat(result?.avg_data_out_kb || '0'),
      totalNodesExecuted: parseInt(result?.total_nodes_executed || '0')
    };
  }

  /**
   * Ottiene statistiche temporali (per ora o giorno)
   * 
   * @param groupBy - 'hour' o 'day'
   * @param workflowId - Filtra per workflow (opzionale)
   * @param days - Giorni da considerare
   * @returns Array di statistiche temporali
   */
  async getTimeStats(
    groupBy: 'hour' | 'day',
    workflowId?: string,
    days: number = 7
  ): Promise<ExecutionTimeStats[]> {
    const dateFormat = groupBy === 'hour' 
      ? "DATE_TRUNC('hour', started_at)" 
      : "DATE_TRUNC('day', started_at)";
    
    let query = `
      SELECT 
        ${dateFormat} as period,
        ${groupBy === 'hour' ? 'EXTRACT(HOUR FROM started_at) as hour,' : ''}
        COUNT(*) as executions,
        COUNT(CASE WHEN status = '${ExecutionStatus.SUCCESS}' THEN 1 END) as successes,
        COUNT(CASE WHEN status = '${ExecutionStatus.ERROR}' THEN 1 END) as failures,
        AVG(duration_ms) as avg_duration_ms
      FROM executions
      WHERE started_at > NOW() - INTERVAL '${days} days'
    `;
    
    const params: any[] = [];
    if (workflowId) {
      query += ` AND workflow_id = $1`;
      params.push(workflowId);
    }
    
    query += `
      GROUP BY period ${groupBy === 'hour' ? ', hour' : ''}
      ORDER BY period DESC
    `;
    
    const results = await this.db.getMany<any>(query, params);
    
    return results.map(r => ({
      period: r.period.toISOString(),
      hour: r.hour,
      executions: parseInt(r.executions),
      successes: parseInt(r.successes),
      failures: parseInt(r.failures),
      avgDurationMs: parseFloat(r.avg_duration_ms || '0'),
      peakConcurrent: await this.calculatePeakConcurrent(r.hour)
    }));
  }

  /**
   * Calcola il picco di esecuzioni concorrenti per un'ora specifica
   * 
   * @param hour - Ora da analizzare
   * @returns Numero massimo di esecuzioni concorrenti
   */
  private async calculatePeakConcurrent(hour: string): Promise<number> {
    try {
      const query = `
        SELECT COUNT(*) as concurrent
        FROM n8n.execution_entity e
        WHERE 
          DATE_TRUNC('hour', e."startedAt") = $1::timestamp
          AND e."stoppedAt" IS NOT NULL
          AND EXISTS (
            SELECT 1 FROM n8n.execution_entity e2
            WHERE e2.id != e.id
            AND e2."startedAt" <= e."stoppedAt"
            AND e2."stoppedAt" >= e."startedAt"
          )
      `;
      
      const result = await this.db.getOne<{ concurrent: string }>(query, [hour]);
      return parseInt(result?.concurrent || '0');
    } catch (error) {
      console.error('Error calculating peak concurrent:', error);
      return 0;
    }
  }

  /**
   * Ottiene trend dalle viste
   * 
   * @param days - Giorni da considerare
   * @returns Array di trend giornalieri
   */
  async getTrends(days: number = 30): Promise<ExecutionTrendsView[]> {
    const query = `
      SELECT * FROM execution_trends
      WHERE execution_date > NOW() - INTERVAL '${days} days'
      ORDER BY execution_date DESC, total_executions DESC
    `;
    
    return await this.db.getMany<ExecutionTrendsView>(query);
  }

  /**
   * Sincronizza esecuzione da API n8n
   * 
   * @param executionData - Dati dell'esecuzione da API
   * @returns Esecuzione sincronizzata
   */
  async syncFromApi(executionData: any): Promise<ExecutionModel> {
    const existingExecution = await this.findById(executionData.id);
    
    // Calcola durata se finita
    let duration_ms: number | undefined;
    if (executionData.startedAt && executionData.stoppedAt) {
      duration_ms = new Date(executionData.stoppedAt).getTime() - 
                   new Date(executionData.startedAt).getTime();
    }
    
    // Determina status
    let status = ExecutionStatus.RUNNING;
    if (executionData.finished) {
      status = executionData.data?.resultData?.error 
        ? ExecutionStatus.ERROR 
        : ExecutionStatus.SUCCESS;
    } else if (executionData.stoppedAt) {
      status = ExecutionStatus.STOPPED;
    }
    
    const executionModel: Partial<ExecutionModel> = {
      id: executionData.id,
      workflow_id: executionData.workflowId,
      started_at: new Date(executionData.startedAt),
      finished_at: executionData.stoppedAt ? new Date(executionData.stoppedAt) : undefined,
      duration_ms,
      status,
      mode: executionData.mode as ExecutionMode,
      data: executionData.data,
      error_message: executionData.data?.resultData?.error?.message,
      error_node: executionData.data?.resultData?.error?.node,
      nodes_executed: executionData.data?.resultData?.runData 
        ? Object.keys(executionData.data.resultData.runData).length 
        : 0
    };
    
    if (existingExecution) {
      // Aggiorna esecuzione esistente
      await this.update(executionData.id, executionModel);
      return (await this.findById(executionData.id))!;
    } else {
      // Crea nuova esecuzione
      return await this.create(executionModel);
    }
  }

  /**
   * Pulisce vecchie esecuzioni
   * 
   * @param daysToKeep - Giorni da mantenere
   * @param keepFailed - Se mantenere le esecuzioni fallite
   * @returns Numero di esecuzioni eliminate
   */
  async cleanOldExecutions(daysToKeep: number, keepFailed: boolean = true): Promise<number> {
    let query = `
      DELETE FROM executions
      WHERE started_at < NOW() - INTERVAL '${daysToKeep} days'
    `;
    
    if (keepFailed) {
      query += ` AND status != '${ExecutionStatus.ERROR}'`;
    }
    
    return await this.db.delete(query);
  }
}