/**
 * Database Models Index
 * 
 * Esporta tutti i modelli del database per un accesso centralizzato.
 * I modelli rappresentano la struttura delle tabelle nel database.
 */

// Esporta modelli Workflow
export {
  WorkflowModel,
  WorkflowNodeModel,
  WorkflowConnectionModel,
  WorkflowAuditLogModel,
  WorkflowSearchParams,
  WorkflowOrderBy,
  WorkflowStats,
  WorkflowHealthView,
  isWorkflowModel,
  createWorkflowModel
} from './workflow.model.js';

// Esporta modelli Execution
export {
  ExecutionModel,
  ExecutionStatus,
  ExecutionMode,
  ExecutionNodeResultModel,
  NodeExecutionStatus,
  ErrorLogModel,
  ErrorSeverity,
  ExecutionSearchParams,
  ExecutionOrderBy,
  ExecutionStats,
  ExecutionTimeStats,
  ExecutionTrendsView,
  isExecutionModel,
  createExecutionModel,
  calculateExecutionDuration,
  isExecutionComplete,
  isExecutionSuccessful,
  categorizeExecutionDuration
} from './execution.model.js';

// Esporta modelli KPI e Metriche
export {
  KpiSnapshotModel,
  PeriodType,
  HourlyStatsModel,
  PerformanceBenchmarkModel,
  TagModel,
  WorkflowTagModel,
  GlobalMetrics,
  TrendDirection,
  TemporalPattern,
  PatternType,
  KpiComparison,
  calculatePercentile,
  calculateMTBF,
  calculateMTTR,
  detectTrend,
  calculateGlobalHealthScore
} from './kpi.model.js';

// Importa i tipi necessari per DatabaseModel
import type { 
  WorkflowModel, 
  WorkflowNodeModel, 
  WorkflowConnectionModel 
} from './workflow.model.js';
import type { 
  ExecutionModel, 
  ExecutionNodeResultModel, 
  ErrorLogModel 
} from './execution.model.js';
import type { 
  KpiSnapshotModel, 
  HourlyStatsModel, 
  PerformanceBenchmarkModel, 
  TagModel 
} from './kpi.model.js';

/**
 * Type per rappresentare qualsiasi modello del database
 */
export type DatabaseModel = 
  | WorkflowModel 
  | WorkflowNodeModel 
  | WorkflowConnectionModel
  | ExecutionModel
  | ExecutionNodeResultModel
  | ErrorLogModel
  | KpiSnapshotModel
  | HourlyStatsModel
  | PerformanceBenchmarkModel
  | TagModel;

/**
 * Interface per risultati paginati
 * Utilizzata per query che restituiscono risultati paginati
 */
export interface PaginatedResult<T> {
  data: T[];                     // Array di risultati
  total: number;                 // Totale elementi disponibili
  page: number;                  // Pagina corrente (1-based)
  pageSize: number;              // Elementi per pagina
  totalPages: number;            // Totale pagine disponibili
  hasNext: boolean;              // Se esiste pagina successiva
  hasPrev: boolean;              // Se esiste pagina precedente
}

/**
 * Interface per risultati aggregati
 * Utilizzata per query di aggregazione
 */
export interface AggregatedResult<T> {
  groupBy: string;               // Campo di raggruppamento
  results: T[];                  // Risultati aggregati
  totals: {                      // Totali complessivi
    count: number;
    sum?: number;
    avg?: number;
    min?: number;
    max?: number;
  };
}

/**
 * Interface per batch operations
 * Utilizzata per operazioni su multipli record
 */
export interface BatchOperationResult {
  successful: number;            // Numero operazioni riuscite
  failed: number;                // Numero operazioni fallite
  errors: Array<{                // Dettagli errori
    id: string | number;
    error: string;
  }>;
  duration_ms: number;           // Durata totale operazione
}

/**
 * Interface per query filters generici
 * Base per tutti i filtri di ricerca
 */
export interface QueryFilters {
  limit?: number;                // Limite risultati
  offset?: number;               // Offset per paginazione
  orderBy?: string;              // Campo ordinamento
  orderDir?: 'ASC' | 'DESC';     // Direzione ordinamento
  includeDeleted?: boolean;      // Includi record eliminati
  fields?: string[];             // Campi da includere nella risposta
}

/**
 * Interface per audit trail generico
 */
export interface AuditEntry {
  entity_type: string;           // Tipo di entità (workflow, execution, etc.)
  entity_id: string;             // ID dell'entità
  action: string;                // Azione eseguita
  user_id?: string;              // Utente che ha eseguito l'azione
  timestamp: Date;               // Quando è avvenuta l'azione
  changes?: any;                 // Cambiamenti effettuati (JSON)
  metadata?: any;                // Metadati aggiuntivi (JSON)
}

/**
 * Helper per creare risultato paginato
 */
export function createPaginatedResult<T>(
  data: T[],
  total: number,
  page: number,
  pageSize: number
): PaginatedResult<T> {
  const totalPages = Math.ceil(total / pageSize);
  
  return {
    data,
    total,
    page,
    pageSize,
    totalPages,
    hasNext: page < totalPages,
    hasPrev: page > 1
  };
}

/**
 * Helper per validare parametri di paginazione
 */
export function validatePaginationParams(
  page?: number,
  pageSize?: number
): { page: number; pageSize: number; offset: number } {
  const validPage = Math.max(1, page || 1);
  const validPageSize = Math.min(100, Math.max(1, pageSize || 20));
  const offset = (validPage - 1) * validPageSize;
  
  return {
    page: validPage,
    pageSize: validPageSize,
    offset
  };
}

/**
 * Helper per sanitizzare campi ordinamento
 * Previene SQL injection validando i campi
 */
export function sanitizeOrderByField(
  field: string,
  allowedFields: string[]
): string | null {
  const sanitized = field.toLowerCase().replace(/[^a-z0-9_]/g, '');
  return allowedFields.includes(sanitized) ? sanitized : null;
}

/**
 * Helper per costruire clausola WHERE da filtri
 */
export function buildWhereClause(filters: Record<string, any>): {
  clause: string;
  params: any[];
} {
  const conditions: string[] = [];
  const params: any[] = [];
  let paramIndex = 1;
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        // IN clause per array
        const placeholders = value.map(() => `$${paramIndex++}`).join(', ');
        conditions.push(`${key} IN (${placeholders})`);
        params.push(...value);
      } else if (typeof value === 'object' && value.min !== undefined && value.max !== undefined) {
        // BETWEEN per range
        conditions.push(`${key} BETWEEN $${paramIndex} AND $${paramIndex + 1}`);
        params.push(value.min, value.max);
        paramIndex += 2;
      } else {
        // Uguaglianza semplice
        conditions.push(`${key} = $${paramIndex++}`);
        params.push(value);
      }
    }
  });
  
  return {
    clause: conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '',
    params
  };
}