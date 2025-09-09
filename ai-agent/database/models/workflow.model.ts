/**
 * Workflow Model
 * 
 * Definisce le interfacce TypeScript per la tabella workflows e tabelle correlate.
 * Questi modelli rappresentano la struttura dei dati nel database.
 */

/**
 * Interfaccia principale per la tabella workflows
 * Contiene tutti i campi del workflow incluse metriche calcolate
 */
export interface WorkflowModel {
  // Campi identificativi
  id: string;
  name: string;
  description?: string;
  active: boolean;
  is_archived: boolean;          // Se il workflow è archiviato (nascosto dall'UI)
  
  // Ownership e organizzazione
  project_id?: string;            // ID del progetto di appartenenza
  owner_email?: string;           // Email del proprietario
  modified_by?: string;           // Ultimo utente che ha modificato
  
  // Timestamp
  created_at: Date;
  updated_at: Date;
  
  // Metriche calcolate (scores da 0 a 100)
  complexity_score: number;      // Complessità basata su nodi e connessioni
  reliability_score: number;     // Affidabilità basata su success rate
  efficiency_score: number;      // Efficienza basata su tempi esecuzione
  health_score: number;          // Salute generale (media ponderata)
  
  // Statistiche esecuzione
  execution_count: number;       // Totale esecuzioni
  success_count: number;         // Esecuzioni con successo
  failure_count: number;         // Esecuzioni fallite
  avg_duration_ms: number;       // Durata media in millisecondi
  min_duration_ms: number;       // Durata minima
  max_duration_ms: number;       // Durata massima
  last_execution_at?: Date;      // Ultima esecuzione
  last_success_at?: Date;        // Ultimo successo
  last_failure_at?: Date;        // Ultimo fallimento
  
  // Contatori struttura
  node_count: number;            // Numero totale di nodi
  connection_count: number;      // Numero di connessioni
  unique_node_types: number;     // Tipi di nodi unici utilizzati
  trigger_count: number;         // Numero di trigger nel workflow
  ai_node_count: number;         // Numero di nodi AI/LLM
  database_node_count: number;   // Numero di nodi database
  http_node_count: number;       // Numero di nodi HTTP
  
  // Metadati JSON
  tags?: any;                    // Array di tags
  settings?: any;                // Settings completi del workflow
  static_data?: any;             // Dati statici del workflow
  pinned_data?: any;             // Dati pinned per testing
  meta?: any;                    // Metadata del workflow (es. templateCredsSetupCompleted)
  shared?: any;                  // Info su ownership e condivisione
  
  // Versioning e template
  version_id?: string;           // ID versione corrente
  is_latest: boolean;            // Se è la versione più recente
  template_id?: string;          // ID del template di origine
  
  // Classificazione
  workflow_type?: string;        // Tipo: webhook, scheduled, manual, form, etc.
  has_error_handler: boolean;    // Se ha gestione errori
}

/**
 * Interfaccia per la tabella workflow_nodes
 * Rappresenta i singoli nodi all'interno di un workflow
 */
export interface WorkflowNodeModel {
  id: number;
  workflow_id: string;
  node_id: string;               // ID univoco del nodo nel workflow
  node_type: string;             // Tipo del nodo (es. n8n-nodes-base.httpRequest)
  node_name: string;             // Nome assegnato al nodo
  
  // Configurazione
  parameters?: any;              // Parametri JSON del nodo
  position?: any;                // Posizione {x, y} nel canvas
  type_version: number;          // Versione del tipo di nodo
  credentials?: any;             // ID delle credenziali utilizzate
  
  // Metriche nodo
  execution_count: number;       // Quante volte è stato eseguito
  success_count: number;         // Esecuzioni con successo
  failure_count: number;         // Esecuzioni fallite
  avg_execution_time_ms: number; // Tempo medio di esecuzione
  error_rate: number;            // Tasso di errore percentuale
  
  // Metadati
  disabled: boolean;             // Se il nodo è disabilitato
  notes?: string;                // Note sul nodo
  color?: string;                // Colore personalizzato HEX
  
  created_at: Date;
  updated_at: Date;
}

/**
 * Interfaccia per la tabella workflow_connections
 * Mappa le connessioni tra i nodi di un workflow
 */
export interface WorkflowConnectionModel {
  id: number;
  workflow_id: string;
  
  // Nodo sorgente
  source_node: string;           // ID del nodo sorgente
  source_type?: string;          // Tipo del nodo sorgente
  source_output: number;         // Indice output del nodo sorgente
  
  // Nodo destinazione
  target_node: string;           // ID del nodo destinazione
  target_type?: string;          // Tipo del nodo destinazione
  target_input: number;          // Indice input del nodo destinazione
  
  // Tipo connessione
  connection_type: string;       // 'main', 'error', etc.
  
  created_at: Date;
}

/**
 * Interfaccia per la tabella workflow_audit_log
 * Traccia tutte le modifiche ai workflow
 */
export interface WorkflowAuditLogModel {
  id: number;
  workflow_id: string;
  
  // Dettagli azione
  action: 'created' | 'updated' | 'deleted' | 'activated' | 'deactivated';
  user_id?: string;              // Chi ha fatto la modifica
  user_email?: string;
  
  // Cambiamenti
  changes?: any;                 // Diff dei cambiamenti JSON
  old_values?: any;              // Valori precedenti JSON
  new_values?: any;              // Nuovi valori JSON
  
  // Versioning
  version_before?: string;
  version_after?: string;
  
  // Metadati
  ip_address?: string;
  user_agent?: string;
  
  performed_at: Date;
}

/**
 * Interfaccia per query di ricerca workflow
 * Utilizzata per filtrare i workflow
 */
export interface WorkflowSearchParams {
  active?: boolean;              // Filtra per stato attivo
  is_archived?: boolean;         // Filtra per stato archiviato
  tag?: string;                  // Filtra per tag
  minReliability?: number;       // Affidabilità minima
  maxComplexity?: number;        // Complessità massima
  hasErrors?: boolean;           // Solo workflow con errori recenti
  unused?: boolean;              // Workflow non usati da X giorni
  limit?: number;                // Limite risultati
  offset?: number;               // Offset per paginazione
  orderBy?: WorkflowOrderBy;     // Campo per ordinamento
  orderDir?: 'ASC' | 'DESC';     // Direzione ordinamento
}

/**
 * Enum per ordinamento workflow
 */
export enum WorkflowOrderBy {
  NAME = 'name',
  CREATED_AT = 'created_at',
  UPDATED_AT = 'updated_at',
  EXECUTION_COUNT = 'execution_count',
  RELIABILITY_SCORE = 'reliability_score',
  COMPLEXITY_SCORE = 'complexity_score',
  HEALTH_SCORE = 'health_score',
  LAST_EXECUTION = 'last_execution_at'
}

/**
 * Interfaccia per statistiche aggregate workflow
 * Utilizzata per dashboard e report
 */
export interface WorkflowStats {
  totalWorkflows: number;
  activeWorkflows: number;
  inactiveWorkflows: number;
  archivedWorkflows: number;
  avgComplexityScore: number;
  avgReliabilityScore: number;
  avgHealthScore: number;
  totalExecutions: number;
  successRate: number;
  workflowsWithErrors: number;
  unusedWorkflows: number;
}

/**
 * Interfaccia per la vista workflow_health
 * Vista materializzata per performance
 */
export interface WorkflowHealthView {
  id: string;
  name: string;
  active: boolean;
  is_archived: boolean;
  health_score: number;
  complexity_score: number;
  reliability_score: number;
  efficiency_score: number;
  execution_count: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
  avg_duration_ms: number;
  last_execution_at?: Date;
  health_status: 'Ottima' | 'Buona' | 'Attenzione' | 'Critica';
  activity_status: 'Mai eseguito' | 'Attivo' | 'Recente' | 'Inattivo' | 'Dormiente';
}

/**
 * Type guard per verificare se un oggetto è un WorkflowModel
 */
export function isWorkflowModel(obj: any): obj is WorkflowModel {
  return (
    typeof obj === 'object' &&
    typeof obj.id === 'string' &&
    typeof obj.name === 'string' &&
    typeof obj.active === 'boolean' &&
    typeof obj.complexity_score === 'number' &&
    typeof obj.reliability_score === 'number'
  );
}

/**
 * Factory per creare un WorkflowModel con valori di default
 */
export function createWorkflowModel(partial: Partial<WorkflowModel>): WorkflowModel {
  const now = new Date();
  return {
    id: partial.id || '',
    name: partial.name || 'New Workflow',
    description: partial.description,
    active: partial.active ?? false,
    is_archived: partial.is_archived ?? false,
    created_at: partial.created_at || now,
    updated_at: partial.updated_at || now,
    
    // Scores di default
    complexity_score: partial.complexity_score ?? 0,
    reliability_score: partial.reliability_score ?? 100,
    efficiency_score: partial.efficiency_score ?? 100,
    health_score: partial.health_score ?? 100,
    
    // Statistiche di default
    execution_count: partial.execution_count ?? 0,
    success_count: partial.success_count ?? 0,
    failure_count: partial.failure_count ?? 0,
    avg_duration_ms: partial.avg_duration_ms ?? 0,
    min_duration_ms: partial.min_duration_ms ?? 0,
    max_duration_ms: partial.max_duration_ms ?? 0,
    
    // Contatori di default
    node_count: partial.node_count ?? 0,
    connection_count: partial.connection_count ?? 0,
    unique_node_types: partial.unique_node_types ?? 0,
    trigger_count: partial.trigger_count ?? 0,
    ai_node_count: partial.ai_node_count ?? 0,
    database_node_count: partial.database_node_count ?? 0,
    http_node_count: partial.http_node_count ?? 0,
    
    // Flags e classificazione
    has_error_handler: partial.has_error_handler ?? false,
    workflow_type: partial.workflow_type,
    
    // Versioning
    is_latest: partial.is_latest ?? true,
    template_id: partial.template_id,
    
    // Optional fields
    last_execution_at: partial.last_execution_at,
    last_success_at: partial.last_success_at,
    last_failure_at: partial.last_failure_at,
    
    // Ownership
    project_id: partial.project_id,
    owner_email: partial.owner_email,
    modified_by: partial.modified_by,
    
    // Metadata
    tags: partial.tags,
    settings: partial.settings,
    static_data: partial.static_data,
    pinned_data: partial.pinned_data,
    meta: partial.meta,
    shared: partial.shared,
    version_id: partial.version_id,
  };
}