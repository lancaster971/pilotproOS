/**
 * Execution Enrichment Service
 * 
 * Arricchisce execution data ESISTENTI nel database con parsing avanzato
 * per AI Agent Transparency - nessuna chiamata API esterna necessaria
 */

import { DatabaseConnection } from '../database/connection.js';

export interface ExecutionStepData {
  nodeId: string;
  nodeName: string;
  nodeType: string;
  executionTime?: number;
  inputData?: any;
  outputData?: any;
  status: 'success' | 'error' | 'running';
  error?: string;
}

export interface EnrichedExecutionData {
  executionId: string;
  workflowId: string;
  detailedData: any;
  steps: ExecutionStepData[];
  totalNodes: number;
  successfulNodes: number;
  failedNodes: number;
  businessContext: {
    extractedEmails?: string[];
    extractedIds?: string[];
    processedAmounts?: number[];
    classifications?: string[];
    [key: string]: any;
  };
}

/**
 * Service per arricchire execution data esistenti nel database
 * utilizzando i raw_data già sincronizzati
 */
export class ExecutionEnrichmentService {
  private db: DatabaseConnection;

  constructor() {
    this.db = DatabaseConnection.getInstance();
  }

  /**
   * Arricchisce execution data per tutti i workflow attivi
   * utilizzando i raw_data già presenti nel database
   */
  async enrichActiveWorkflowExecutions(limit = 50): Promise<EnrichedExecutionData[]> {
    console.log(`🔄 Starting enrichment of execution data from database (limit: ${limit})`);

    try {
      // 1. Trova executions recenti con raw_data per workflow attivi
      const executions = await this.db.getMany(`
        SELECT 
          te.id,
          te.workflow_id,
          tw.name as workflow_name,
          te.status,
          te.started_at,
          te.stopped_at,
          te.duration_ms,
          te.has_error,
          te.raw_data,
          te.tenant_id
        FROM tenant_executions te
        JOIN tenant_workflows tw ON te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id
        WHERE tw.active = true
          AND te.raw_data IS NOT NULL
          AND te.raw_data != '{}'::jsonb
          AND te.started_at >= NOW() - INTERVAL '7 days'
          AND (te.has_detailed_data IS NULL OR te.has_detailed_data = false)
        ORDER BY te.started_at DESC
        LIMIT $1
      `, [limit]);

      console.log(`📊 Found ${executions.length} executions to enrich from database`);

      const enrichedExecutions: EnrichedExecutionData[] = [];

      // 2. Processa ogni execution usando raw_data esistenti
      for (const execution of executions) {
        try {
          const enrichedData = await this.processExecutionFromDatabase(execution);
          if (enrichedData) {
            enrichedExecutions.push(enrichedData);
            
            // 3. Salva nel database
            await this.saveEnrichedExecution(enrichedData, execution.tenant_id);
          }
        } catch (error) {
          console.error(`❌ Error processing execution ${execution.id}:`, error);
          continue; // Continua con il prossimo
        }
      }

      console.log(`✅ Enrichment completed. Processed ${enrichedExecutions.length} executions`);
      return enrichedExecutions;

    } catch (error) {
      console.error('❌ Failed to enrich execution data:', error);
      throw error;
    }
  }

  /**
   * Processa execution data dal database usando raw_data
   */
  private async processExecutionFromDatabase(execution: any): Promise<EnrichedExecutionData | null> {
    try {
      const executionId = execution.id.toString();
      const rawData = execution.raw_data || {};
      
      // Estrai runData dal raw_data esistente
      const runData = rawData.data?.resultData?.runData || {};
      const steps: ExecutionStepData[] = [];
      
      let totalNodes = 0;
      let successfulNodes = 0;
      let failedNodes = 0;

      // Processa ogni nodo eseguito
      for (const [nodeName, nodeExecutions] of Object.entries(runData)) {
        totalNodes++;
        
        const nodeExecution = (nodeExecutions as any[])[0]; // Prima esecuzione del nodo
        if (!nodeExecution) continue;

        const hasError = nodeExecution.error;
        const status = hasError ? 'error' : 'success';
        
        if (hasError) {
          failedNodes++;
        } else {
          successfulNodes++;
        }

        const stepData: ExecutionStepData = {
          nodeId: nodeName,
          nodeName: nodeName,
          nodeType: 'unknown', // Potremmo arricchire con workflow definition
          executionTime: nodeExecution.executionTime || 0,
          inputData: nodeExecution.data?.main?.[0] || null,
          outputData: nodeExecution.data?.main?.[0] || null,
          status,
          error: hasError ? nodeExecution.error.message : undefined
        };

        steps.push(stepData);
      }

      // Estrai business context
      const businessContext = this.extractBusinessContext(steps);

      const enrichedData: EnrichedExecutionData = {
        executionId,
        workflowId: execution.workflow_id,
        detailedData: rawData,
        steps,
        totalNodes,
        successfulNodes,
        failedNodes,
        businessContext
      };

      console.log(`✅ Processed execution ${executionId}: ${successfulNodes}/${totalNodes} nodes successful`);
      return enrichedData;

    } catch (error) {
      console.error(`❌ Error processing execution ${execution.id}:`, error);
      return null;
    }
  }

  /**
   * Estrae business context dai step data (emails, order IDs, amounts, etc.)
   */
  private extractBusinessContext(steps: ExecutionStepData[]): any {
    const context: any = {
      extractedEmails: [],
      extractedIds: [],
      processedAmounts: [],
      classifications: []
    };

    for (const step of steps) {
      try {
        // Estrai emails
        const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
        const stepDataString = JSON.stringify(step.outputData || step.inputData || {});
        const emails = stepDataString.match(emailRegex);
        if (emails) {
          context.extractedEmails.push(...emails);
        }

        // Estrai Order IDs e simili
        const idRegex = /(order|invoice|ticket|id)[_-]?(\d+|[A-Z0-9]{6,})/gi;
        const ids = stepDataString.match(idRegex);
        if (ids) {
          context.extractedIds.push(...ids);
        }

        // Estrai amounts/prezzi
        const amountRegex = /(\d+[.,]\d{2}|\d+\.\d+)/g;
        const amounts = stepDataString.match(amountRegex);
        if (amounts) {
          const numericAmounts = amounts.map(a => parseFloat(a.replace(',', '.'))).filter(n => !isNaN(n) && n > 0);
          context.processedAmounts.push(...numericAmounts);
        }

        // Cerca classificazioni/categorie
        if (step.outputData && typeof step.outputData === 'object') {
          const data = Array.isArray(step.outputData) ? step.outputData[0] : step.outputData;
          if (data?.json?.categoria || data?.json?.classification || data?.json?.category) {
            const classification = data.json.categoria || data.json.classification || data.json.category;
            context.classifications.push(classification);
          }
        }

      } catch (error) {
        // Ignora errori di parsing per singoli step
        continue;
      }
    }

    // Rimuovi duplicati
    context.extractedEmails = [...new Set(context.extractedEmails)];
    context.extractedIds = [...new Set(context.extractedIds)];
    context.classifications = [...new Set(context.classifications)];

    return context;
  }

  /**
   * Salva execution data arricchiti nel database
   */
  private async saveEnrichedExecution(data: EnrichedExecutionData, tenantId: string): Promise<void> {
    try {
      // Aggiorna execution esistente con dati arricchiti
      await this.db.query(`
        UPDATE tenant_executions 
        SET 
          has_detailed_data = true,
          detailed_steps = $2::jsonb,
          business_context = $3::jsonb,
          total_nodes = $4,
          successful_nodes = $5,
          failed_nodes = $6,
          updated_at = NOW()
        WHERE id = $1 AND tenant_id = $7
      `, [
        data.executionId,
        JSON.stringify(data.steps),
        JSON.stringify(data.businessContext),
        data.totalNodes,
        data.successfulNodes,
        data.failedNodes,
        tenantId
      ]);

      console.log(`✅ Updated execution ${data.executionId} with enriched data`);

    } catch (error) {
      console.error(`❌ Error saving enriched execution ${data.executionId}:`, error);
      throw error;
    }
  }

  /**
   * Ottieni execution data arricchiti dal database
   */
  async getEnrichedExecutions(tenantId: string, limit = 20): Promise<any[]> {
    try {
      return await this.db.getMany(`
        SELECT 
          te.id,
          te.workflow_id,
          tw.name as workflow_name,
          te.status,
          te.started_at,
          te.stopped_at,
          te.duration_ms,
          te.has_error,
          te.has_detailed_data,
          te.detailed_steps,
          te.business_context,
          te.total_nodes,
          te.successful_nodes,
          te.failed_nodes
        FROM tenant_executions te
        JOIN tenant_workflows tw ON te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id
        WHERE te.tenant_id = $1 
          AND te.has_detailed_data = true
        ORDER BY te.started_at DESC
        LIMIT $2
      `, [tenantId, limit]);
    } catch (error) {
      console.error('❌ Error getting enriched executions:', error);
      throw error;
    }
  }

  /**
   * Ottieni statistiche enrichment
   */
  async getEnrichmentStats(tenantId: string): Promise<any> {
    try {
      const stats = await this.db.getOne(`
        SELECT 
          COUNT(*) as total_executions,
          COUNT(*) FILTER (WHERE has_detailed_data = true) as enriched_executions,
          COUNT(*) FILTER (WHERE raw_data IS NOT NULL AND raw_data != '{}'::jsonb) as executions_with_raw_data,
          COUNT(DISTINCT workflow_id) as unique_workflows
        FROM tenant_executions te
        JOIN tenant_workflows tw ON te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id
        WHERE te.tenant_id = $1
          AND te.started_at >= NOW() - INTERVAL '7 days'
      `, [tenantId]);

      return {
        totalExecutions: parseInt(stats.total_executions),
        enrichedExecutions: parseInt(stats.enriched_executions),
        executionsWithRawData: parseInt(stats.executions_with_raw_data),
        uniqueWorkflows: parseInt(stats.unique_workflows),
        enrichmentPercentage: stats.total_executions > 0 
          ? Math.round((stats.enriched_executions / stats.total_executions) * 100)
          : 0
      };
    } catch (error) {
      console.error('❌ Error getting enrichment stats:', error);
      throw error;
    }
  }
}

export default ExecutionEnrichmentService;