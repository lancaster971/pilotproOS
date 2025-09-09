/**
 * Data Transformer
 * 
 * Trasforma i dati dall'API n8n nei modelli del database.
 * Calcola metriche e scores derivati.
 */

import {
  WorkflowModel,
  WorkflowNodeModel,
  WorkflowConnectionModel,
  ExecutionModel,
  ExecutionStatus,
  ExecutionMode,
  ExecutionNodeResultModel,
  NodeExecutionStatus
} from '../database/models/index.js';

/**
 * Classe per trasformare dati API in modelli DB
 */
export class DataTransformer {
  
  /**
   * Trasforma workflow API in modello database
   */
  transformWorkflow(apiWorkflow: any): Partial<WorkflowModel> {
    // Calcola complexity score basato su nodi e connessioni
    const nodeCount = apiWorkflow.nodes?.length || 0;
    const connectionCount = this.countConnections(apiWorkflow.connections);
    const complexityScore = this.calculateComplexityScore(nodeCount, connectionCount, apiWorkflow.nodes);
    
    // Estrai informazioni sui trigger e tipi di nodi
    const triggerNodes = apiWorkflow.nodes?.filter((n: any) => 
      n.type?.toLowerCase().includes('trigger') || 
      n.type?.toLowerCase().includes('webhook')
    ) || [];
    
    // Conta nodi per tipo
    const aiNodeCount = apiWorkflow.nodes?.filter((n: any) => 
      n.type?.toLowerCase().includes('ai') || 
      n.type?.toLowerCase().includes('openai') ||
      n.type?.toLowerCase().includes('chatgpt')
    ).length || 0;
    
    const dbNodeCount = apiWorkflow.nodes?.filter((n: any) => 
      n.type?.toLowerCase().includes('database') || 
      n.type?.toLowerCase().includes('postgres') ||
      n.type?.toLowerCase().includes('mysql') ||
      n.type?.toLowerCase().includes('supabase')
    ).length || 0;
    
    const httpNodeCount = apiWorkflow.nodes?.filter((n: any) => 
      n.type?.toLowerCase().includes('http')
    ).length || 0;
    
    // Determina se ha error handler
    const hasErrorHandler = apiWorkflow.nodes?.some((n: any) => 
      n.type?.toLowerCase().includes('error') ||
      n.name?.toLowerCase().includes('error')
    ) || false;
    
    // Estrai owner_email da shared se presente
    let ownerEmail = null;
    if (apiWorkflow.shared && Array.isArray(apiWorkflow.shared) && apiWorkflow.shared.length > 0) {
      const projectRelations = apiWorkflow.shared[0]?.project?.projectRelations;
      if (projectRelations && projectRelations.length > 0) {
        ownerEmail = projectRelations[0]?.user?.email;
      }
    }
    
    // Estrai project_id
    const projectId = apiWorkflow.shared?.[0]?.projectId || null;
    
    return {
      id: apiWorkflow.id,
      name: apiWorkflow.name,
      description: apiWorkflow.description || null,
      active: apiWorkflow.active || false,
      is_archived: apiWorkflow.isArchived || false,  // Campo per workflow archiviati
      
      // Ownership
      project_id: projectId,
      owner_email: ownerEmail,
      
      // Struttura workflow
      node_count: nodeCount,
      connection_count: connectionCount,
      unique_node_types: this.countUniqueNodeTypes(apiWorkflow.nodes),
      trigger_count: apiWorkflow.triggerCount || triggerNodes.length,
      ai_node_count: aiNodeCount,
      database_node_count: dbNodeCount,
      http_node_count: httpNodeCount,
      has_error_handler: hasErrorHandler,
      
      // Scores (gli altri verranno calcolati dal metrics calculator)
      complexity_score: complexityScore,
      reliability_score: 50, // Default, verrà aggiornato
      efficiency_score: 50,  // Default, verrà aggiornato
      health_score: 50,      // Default, verrà aggiornato
      
      // Statistiche esecuzione (verranno aggiornate dal sync)
      execution_count: 0,
      success_count: 0,
      failure_count: 0,
      avg_duration_ms: 0,
      min_duration_ms: 0,
      max_duration_ms: 0,
      
      // Flags
      is_latest: true,
      
      // Metadata
      settings: apiWorkflow.settings || {},
      static_data: apiWorkflow.staticData || {},
      pinned_data: apiWorkflow.pinnedData || {},
      meta: apiWorkflow.meta || {},
      shared: apiWorkflow.shared || [],
      tags: apiWorkflow.tags || [],
      version_id: apiWorkflow.versionId || null,
      
      // Timestamp
      created_at: apiWorkflow.createdAt ? new Date(apiWorkflow.createdAt) : new Date(),
      updated_at: apiWorkflow.updatedAt ? new Date(apiWorkflow.updatedAt) : new Date()
    };
  }
  
  /**
   * Trasforma nodi del workflow
   */
  transformWorkflowNodes(workflowId: string, apiNodes: any[]): WorkflowNodeModel[] {
    if (!apiNodes || !Array.isArray(apiNodes)) return [];
    
    return apiNodes.map(node => ({
      id: 0, // Auto-increment dal DB
      workflow_id: workflowId,
      node_id: node.id,
      node_name: node.name,
      node_type: node.type,
      
      // Configurazione
      parameters: node.parameters || {},
      position: node.position || [0, 0],
      type_version: node.typeVersion || 1,
      credentials: node.credentials || {},
      
      // Metriche nodo (default, verranno aggiornate)
      execution_count: 0,
      success_count: 0,
      failure_count: 0,
      avg_execution_time_ms: 0,
      error_rate: 0,
      
      // Metadati
      disabled: node.disabled || false,
      notes: node.notes || null,
      color: node.color || null,
      
      created_at: new Date(),
      updated_at: new Date()
    }));
  }
  
  /**
   * Trasforma connessioni del workflow
   */
  transformWorkflowConnections(workflowId: string, apiConnections: any): WorkflowConnectionModel[] {
    if (!apiConnections) return [];
    
    const connections: WorkflowConnectionModel[] = [];
    
    // Le connessioni in n8n sono organizzate per nodo sorgente
    Object.entries(apiConnections).forEach(([sourceNode, nodeConnections]: [string, any]) => {
      if (!nodeConnections || !nodeConnections.main) return;
      
      // Ogni output del nodo può avere multiple connessioni
      nodeConnections.main.forEach((outputConnections: any[], outputIndex: number) => {
        if (!outputConnections) return;
        
        outputConnections.forEach((conn: any) => {
          connections.push({
            id: 0, // Auto-increment dal DB
            workflow_id: workflowId,
            source_node: sourceNode,
            source_output: outputIndex,
            target_node: conn.node,
            target_input: conn.index || 0,
            connection_type: 'main', // Default type
            created_at: new Date()
          });
        });
      });
    });
    
    return connections;
  }
  
  /**
   * Trasforma esecuzione API in modello database
   */
  transformExecution(apiExecution: any): Partial<ExecutionModel> {
    // Determina status
    const status = this.mapExecutionStatus(apiExecution);
    
    // Calcola durata se disponibile
    let duration_ms: number | undefined;
    if (apiExecution.startedAt && apiExecution.stoppedAt) {
      const started = new Date(apiExecution.startedAt).getTime();
      const stopped = new Date(apiExecution.stoppedAt).getTime();
      duration_ms = stopped - started;
    }
    
    // Estrai informazioni errore
    const errorData = apiExecution.data?.resultData?.error;
    
    // Conta nodi eseguiti
    const nodesExecuted = apiExecution.data?.resultData?.runData 
      ? Object.keys(apiExecution.data.resultData.runData).length 
      : 0;
    
    // Calcola dimensione dati (approssimativa)
    const dataSize = this.estimateDataSize(apiExecution.data);
    
    return {
      id: apiExecution.id,
      workflow_id: apiExecution.workflowId,
      
      // Timing
      started_at: apiExecution.startedAt ? new Date(apiExecution.startedAt) : new Date(),
      finished_at: apiExecution.stoppedAt ? new Date(apiExecution.stoppedAt) : undefined,
      duration_ms,
      
      // Status
      status,
      mode: (apiExecution.mode || 'manual') as ExecutionMode,
      retry_of: apiExecution.retryOf || null,
      retry_success_id: apiExecution.retrySuccessId || null,
      
      // Dati esecuzione
      data: apiExecution.data || {},
      nodes_executed: nodesExecuted,
      
      // Errore se presente
      error_message: errorData?.message || null,
      error_node: errorData?.node || null,
      error_stack: errorData?.stack || null,
      
      // Metriche dati
      data_in_kb: dataSize.input,
      data_out_kb: dataSize.output,
      
      created_at: new Date()
    };
  }
  
  /**
   * Trasforma risultati dei nodi dell'esecuzione
   */
  transformNodeResults(
    executionId: string, 
    workflowId: string,
    runData: any
  ): ExecutionNodeResultModel[] {
    if (!runData) return [];
    
    const results: ExecutionNodeResultModel[] = [];
    
    Object.entries(runData).forEach(([nodeId, nodeData]: [string, any]) => {
      // Ogni nodo può avere multiple esecuzioni (retry)
      const executions = Array.isArray(nodeData) ? nodeData : [nodeData];
      
      executions.forEach((execution: any, index: number) => {
        // Calcola stato del nodo
        const status = this.mapNodeExecutionStatus(execution);
        
        // Calcola timing
        let executionTime = 0;
        if (execution.startTime && execution.executionTime) {
          executionTime = execution.executionTime;
        }
        
        results.push({
          id: 0, // Auto-increment dal DB
          execution_id: executionId,
          workflow_id: workflowId,
          node_id: nodeId,
          node_type: execution.source?.[0]?.type || 'unknown',
          
          // Timing
          started_at: execution.startTime ? new Date(execution.startTime) : new Date(),
          finished_at: execution.startTime && executionTime 
            ? new Date(new Date(execution.startTime).getTime() + executionTime)
            : new Date(),
          execution_time_ms: executionTime,
          
          // Status
          status,
          
          // Dati
          items_input: execution.data?.main?.[0]?.length || 0,
          items_output: execution.data?.main?.[0]?.length || 0,
          data: execution.data || {},
          
          // Errore se presente
          error_message: execution.error?.message || null,
          error_details: execution.error || {},
          
          created_at: new Date()
        });
      });
    });
    
    return results;
  }
  
  /**
   * Calcola complexity score di un workflow
   */
  private calculateComplexityScore(
    nodeCount: number, 
    connectionCount: number,
    nodes?: any[]
  ): number {
    let score = 0;
    
    // Base score da numero di nodi (0-40 punti)
    if (nodeCount <= 5) score += 10;
    else if (nodeCount <= 10) score += 20;
    else if (nodeCount <= 20) score += 30;
    else score += 40;
    
    // Connessioni (0-30 punti)
    const avgConnectionsPerNode = connectionCount / Math.max(nodeCount, 1);
    if (avgConnectionsPerNode <= 1) score += 10;
    else if (avgConnectionsPerNode <= 2) score += 20;
    else score += 30;
    
    // Tipi di nodi complessi (0-30 punti)
    if (nodes) {
      const complexNodeTypes = [
        'loop', 'switch', 'if', 'merge', 'split',
        'code', 'function', 'execute-workflow'
      ];
      
      const complexNodes = nodes.filter(n => 
        complexNodeTypes.some(type => 
          n.type?.toLowerCase().includes(type)
        )
      );
      
      const complexityRatio = complexNodes.length / nodeCount;
      score += Math.min(30, complexityRatio * 40);
    }
    
    return Math.round(score);
  }
  
  /**
   * Conta tipi di nodi unici
   */
  private countUniqueNodeTypes(nodes: any[]): number {
    if (!nodes || !Array.isArray(nodes)) return 0;
    const types = new Set(nodes.map(n => n.type));
    return types.size;
  }

  /**
   * Conta connessioni totali
   */
  private countConnections(connections: any): number {
    if (!connections) return 0;
    
    let count = 0;
    Object.values(connections).forEach((nodeConn: any) => {
      if (nodeConn?.main) {
        nodeConn.main.forEach((output: any[]) => {
          if (Array.isArray(output)) {
            count += output.length;
          }
        });
      }
    });
    
    return count;
  }
  
  /**
   * Determina se un nodo è un trigger
   */
  private isNodeTrigger(nodeType: string): boolean {
    if (!nodeType) return false;
    
    const triggerTypes = [
      'trigger', 'webhook', 'schedule', 'cron',
      'start', 'manual', 'interval'
    ];
    
    const type = nodeType.toLowerCase();
    return triggerTypes.some(t => type.includes(t));
  }
  
  /**
   * Mappa status esecuzione da API a enum
   */
  private mapExecutionStatus(apiExecution: any): ExecutionStatus {
    if (apiExecution.status) {
      // Se l'API fornisce già lo status
      switch (apiExecution.status.toLowerCase()) {
        case 'success': return ExecutionStatus.SUCCESS;
        case 'error': return ExecutionStatus.ERROR;
        case 'running': return ExecutionStatus.RUNNING;
        case 'waiting': return ExecutionStatus.WAITING;
        case 'canceled': return ExecutionStatus.STOPPED;
        default: return ExecutionStatus.RUNNING; // Default invece di UNKNOWN
      }
    }
    
    // Deduce status da altri campi
    if (!apiExecution.finished) {
      return ExecutionStatus.RUNNING;
    }
    
    if (apiExecution.data?.resultData?.error) {
      return ExecutionStatus.ERROR;
    }
    
    if (apiExecution.stoppedAt && !apiExecution.finished) {
      return ExecutionStatus.STOPPED;
    }
    
    return ExecutionStatus.SUCCESS;
  }
  
  /**
   * Mappa status esecuzione nodo
   */
  private mapNodeExecutionStatus(nodeExecution: any): NodeExecutionStatus {
    if (nodeExecution.error) {
      return NodeExecutionStatus.ERROR;
    }
    
    if (nodeExecution.data?.main?.[0]?.length > 0) {
      return NodeExecutionStatus.SUCCESS;
    }
    
    return NodeExecutionStatus.SKIPPED;
  }
  
  /**
   * Stima dimensione dati in KB
   */
  private estimateDataSize(data: any): { input: number; output: number } {
    if (!data) return { input: 0, output: 0 };
    
    // Stima approssimativa basata su JSON stringify
    try {
      const inputData = data.inputData || {};
      const outputData = data.resultData?.runData || {};
      
      const inputSize = JSON.stringify(inputData).length / 1024;
      const outputSize = JSON.stringify(outputData).length / 1024;
      
      return {
        input: Math.round(inputSize * 10) / 10,
        output: Math.round(outputSize * 10) / 10
      };
    } catch {
      return { input: 0, output: 0 };
    }
  }
  
  /**
   * Calcola hash per confronto versioni
   */
  calculateWorkflowHash(workflow: any): string {
    // Crea hash semplice per verificare modifiche
    const relevantData = {
      nodes: workflow.nodes?.length,
      connections: this.countConnections(workflow.connections),
      settings: workflow.settings,
      active: workflow.active
    };
    
    const str = JSON.stringify(relevantData);
    
    // Hash semplice (non crittografico)
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    
    return hash.toString(16);
  }
}