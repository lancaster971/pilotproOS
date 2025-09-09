/**
 * Execution Model
 * 
 * Definisce le interfacce TypeScript per la tabella executions e tabelle correlate.
 * Gestisce il tracking completo delle esecuzioni dei workflow.
 */

/**
 * Interfaccia principale per la tabella executions
 * Rappresenta una singola esecuzione di un workflow
 */
export interface ExecutionModel {
  id: string;
  workflow_id: string;
  
  // Timing dell'esecuzione
  started_at: Date;              // Quando è iniziata
  finished_at?: Date;            // Quando è terminata (null se in corso)
  duration_ms?: number;          // Durata totale in millisecondi
  
  // Status dell'esecuzione
  status: ExecutionStatus;       // Stato corrente
  mode?: ExecutionMode;          // Modalità di esecuzione
  retry_of?: string;             // ID esecuzione che sta ritentando
  retry_success_id?: string;     // ID del retry che ha avuto successo
  
  // Dati esecuzione
  data?: any;                    // Dati completi esecuzione (JSON)
  wait_till?: Date;              // Per esecuzioni in attesa
  
  // Gestione errori
  error_message?: string;        // Messaggio di errore
  error_node?: string;           // ID del nodo che ha causato l'errore
  error_stack?: string;          // Stack trace completo
  
  // Metriche volume dati
  data_in_kb: number;            // Dimensione dati input in KB
  data_out_kb: number;           // Dimensione dati output in KB
  nodes_executed: number;        // Numero di nodi eseguiti
  
  created_at: Date;
}

/**
 * Enum per lo status dell'esecuzione
 */
export enum ExecutionStatus {
  RUNNING = 'running',           // In esecuzione
  SUCCESS = 'success',           // Completata con successo
  ERROR = 'error',               // Terminata con errore
  STOPPED = 'stopped',           // Fermata manualmente
  WAITING = 'waiting',           // In attesa
  CANCELED = 'canceled'          // Cancellata
}

/**
 * Enum per la modalità di esecuzione
 */
export enum ExecutionMode {
  MANUAL = 'manual',             // Esecuzione manuale
  TRIGGER = 'trigger',           // Avviata da trigger
  WEBHOOK = 'webhook',           // Avviata da webhook
  CLI = 'cli',                   // Avviata da CLI
  SCHEDULE = 'schedule',         // Avviata da schedule/cron
  RETRY = 'retry',               // Retry automatico
  TEST = 'test'                  // Esecuzione di test
}

/**
 * Interfaccia per la tabella execution_node_results
 * Risultati di esecuzione per ogni singolo nodo
 */
export interface ExecutionNodeResultModel {
  id: number;
  execution_id: string;
  workflow_id: string;
  node_id: string;               // ID del nodo eseguito
  node_type: string;             // Tipo del nodo
  
  // Timing del nodo
  started_at?: Date;
  finished_at?: Date;
  execution_time_ms?: number;    // Tempo di esecuzione del nodo
  
  // Status del nodo
  status?: NodeExecutionStatus;
  
  // Dati processati
  items_input: number;           // Numero items ricevuti in input
  items_output: number;          // Numero items prodotti in output
  data?: any;                    // Dati output del nodo (JSON)
  
  // Errori specifici del nodo
  error_message?: string;
  error_details?: any;           // Dettagli errore (JSON)
  
  created_at: Date;
}

/**
 * Enum per lo status di esecuzione del nodo
 */
export enum NodeExecutionStatus {
  SUCCESS = 'success',
  ERROR = 'error',
  SKIPPED = 'skipped',           // Nodo saltato (es. per condizioni)
  WAITING = 'waiting'
}

/**
 * Interfaccia per la tabella error_logs
 * Log dettagliato di tutti gli errori
 */
export interface ErrorLogModel {
  id: number;
  workflow_id: string;
  execution_id?: string;
  node_id?: string;
  
  // Classificazione errore
  error_type?: string;           // Tipo/categoria errore
  error_code?: string;           // Codice errore specifico
  error_message: string;         // Messaggio di errore
  error_stack?: string;          // Stack trace completo
  
  // Contesto aggiuntivo
  context?: any;                 // Contesto JSON con info extra
  
  // Gestione errore
  severity: ErrorSeverity;       // Gravità dell'errore
  is_resolved: boolean;          // Se è stato risolto
  resolved_at?: Date;            // Quando è stato risolto
  resolution_notes?: string;     // Note sulla risoluzione
  
  occurred_at: Date;             // Quando si è verificato l'errore
  created_at: Date;
}

/**
 * Enum per la gravità degli errori
 */
export enum ErrorSeverity {
  LOW = 'low',                   // Bassa gravità
  MEDIUM = 'medium',             // Media gravità
  HIGH = 'high',                 // Alta gravità
  CRITICAL = 'critical'          // Critica
}

/**
 * Interfaccia per parametri di ricerca esecuzioni
 */
export interface ExecutionSearchParams {
  workflow_id?: string;          // Filtra per workflow
  status?: ExecutionStatus;      // Filtra per status
  mode?: ExecutionMode;          // Filtra per modalità
  startedAfter?: Date;           // Esecuzioni iniziate dopo
  startedBefore?: Date;          // Esecuzioni iniziate prima
  hasError?: boolean;            // Solo esecuzioni con errori
  minDuration?: number;          // Durata minima in ms
  maxDuration?: number;          // Durata massima in ms
  limit?: number;                // Limite risultati
  offset?: number;               // Offset per paginazione
  orderBy?: ExecutionOrderBy;    // Campo per ordinamento
  orderDir?: 'ASC' | 'DESC';     // Direzione ordinamento
}

/**
 * Enum per ordinamento esecuzioni
 */
export enum ExecutionOrderBy {
  STARTED_AT = 'started_at',
  FINISHED_AT = 'finished_at',
  DURATION = 'duration_ms',
  STATUS = 'status',
  WORKFLOW_ID = 'workflow_id'
}

/**
 * Interfaccia per statistiche aggregate esecuzioni
 */
export interface ExecutionStats {
  totalExecutions: number;
  runningExecutions: number;
  successfulExecutions: number;
  failedExecutions: number;
  avgDurationMs: number;
  minDurationMs: number;
  maxDurationMs: number;
  successRate: number;
  errorRate: number;
  avgDataInKb: number;
  avgDataOutKb: number;
  totalNodesExecuted: number;
}

/**
 * Interfaccia per statistiche temporali delle esecuzioni
 */
export interface ExecutionTimeStats {
  period: string;                // Periodo (es. '2024-01-01')
  hour?: number;                 // Ora del giorno (0-23)
  executions: number;            // Numero di esecuzioni
  successes: number;             // Esecuzioni con successo
  failures: number;              // Esecuzioni fallite
  avgDurationMs: number;         // Durata media
  peakConcurrent: number;        // Picco esecuzioni concorrenti
}

/**
 * Interfaccia per la vista execution_trends
 * Trend giornalieri delle esecuzioni
 */
export interface ExecutionTrendsView {
  execution_date: Date;
  workflow_id: string;
  workflow_name: string;
  total_executions: number;
  successful: number;
  failed: number;
  avg_duration_ms: number;
  min_duration_ms: number;
  max_duration_ms: number;
  avg_data_in_kb: number;
  avg_data_out_kb: number;
}

/**
 * Type guard per verificare se un oggetto è un ExecutionModel
 */
export function isExecutionModel(obj: any): obj is ExecutionModel {
  return (
    typeof obj === 'object' &&
    typeof obj.id === 'string' &&
    typeof obj.workflow_id === 'string' &&
    obj.started_at instanceof Date &&
    typeof obj.status === 'string'
  );
}

/**
 * Factory per creare un ExecutionModel con valori di default
 */
export function createExecutionModel(partial: Partial<ExecutionModel>): ExecutionModel {
  const now = new Date();
  return {
    id: partial.id || '',
    workflow_id: partial.workflow_id || '',
    started_at: partial.started_at || now,
    finished_at: partial.finished_at,
    duration_ms: partial.duration_ms,
    status: partial.status || ExecutionStatus.RUNNING,
    mode: partial.mode,
    retry_of: partial.retry_of,
    retry_success_id: partial.retry_success_id,
    data: partial.data,
    wait_till: partial.wait_till,
    error_message: partial.error_message,
    error_node: partial.error_node,
    error_stack: partial.error_stack,
    data_in_kb: partial.data_in_kb ?? 0,
    data_out_kb: partial.data_out_kb ?? 0,
    nodes_executed: partial.nodes_executed ?? 0,
    created_at: partial.created_at || now
  };
}

/**
 * Helper per calcolare la durata di un'esecuzione
 */
export function calculateExecutionDuration(execution: ExecutionModel): number | null {
  if (!execution.finished_at) {
    return null; // Ancora in corso
  }
  return execution.finished_at.getTime() - execution.started_at.getTime();
}

/**
 * Helper per determinare se un'esecuzione è completata
 */
export function isExecutionComplete(execution: ExecutionModel): boolean {
  return [
    ExecutionStatus.SUCCESS,
    ExecutionStatus.ERROR,
    ExecutionStatus.STOPPED,
    ExecutionStatus.CANCELED
  ].includes(execution.status);
}

/**
 * Helper per determinare se un'esecuzione ha avuto successo
 */
export function isExecutionSuccessful(execution: ExecutionModel): boolean {
  return execution.status === ExecutionStatus.SUCCESS;
}

/**
 * Helper per categorizzare la durata dell'esecuzione
 */
export function categorizeExecutionDuration(durationMs: number): string {
  if (durationMs < 1000) return 'Molto veloce';       // < 1 secondo
  if (durationMs < 5000) return 'Veloce';             // < 5 secondi
  if (durationMs < 30000) return 'Normale';           // < 30 secondi
  if (durationMs < 60000) return 'Lenta';             // < 1 minuto
  if (durationMs < 300000) return 'Molto lenta';      // < 5 minuti
  return 'Estremamente lenta';                        // >= 5 minuti
}