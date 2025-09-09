/**
 * Execution Import Service
 * 
 * Importa execution data completi dall'API n8n nel database PostgreSQL
 * - Chiama API n8n con includeData=true per ottenere step-by-step data
 * - Arricchisce le execution esistenti nel database con dati dettagliati
 * - Supporta sync per workflow attivi e specifici
 */

import { N8nApiService } from './n8n-client.js';
import { DatabaseConnection } from '../database/connection.js';
import { EnvConfig } from '../config/environment.js';

export interface ExecutionStepData {
  nodeId: string;
  nodeName: string;
  nodeType: string;
  executionTime?: number;
  inputData?: any;
  outputData?: any;
  status: 'success' | 'error' | 'running';
  error?: string;
  isVisible?: boolean; // Nuovo campo per visibilità basata su note "show"
  isTrigger?: boolean; // Campo per identificare nodi trigger
  position?: { x: number; y: number }; // Posizione nel canvas per ordinamento
  customOrder?: number; // Ordinamento esplicito da show-N (es: show-1, show-2)
}

export interface EnrichedExecutionData {
  executionId: string;
  workflowId: string;
  detailedData: any; // Raw n8n execution data with includeData=true
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
 * Service per importare e arricchire execution data dal n8n API
 */
export class ExecutionImportService {
  private n8nApi: N8nApiService;
  private db: DatabaseConnection;

  constructor() {
    const config = {
      n8nApiUrl: process.env.N8N_API_URL || 'http://localhost:5678/api/v1',
      n8nApiKey: process.env.N8N_API_KEY || '',
      debug: process.env.NODE_ENV === 'development'
    };
    this.n8nApi = new N8nApiService(config as any);
    this.db = DatabaseConnection.getInstance();
  }

  /**
   * Exposes n8n API client for direct access
   */
  getN8nClient(): N8nApiService {
    return this.n8nApi;
  }

  /**
   * Importa execution data completi per workflow attivi
   * 
   * @param limit Numero massimo di executions da importare
   * @returns Array di execution data arricchiti
   */
  async importActiveWorkflowExecutions(limit = 50): Promise<EnrichedExecutionData[]> {
    console.log(`🔄 Starting import of execution data (limit: ${limit})`);

    try {
      // 1. Ottieni workflow attivi dal database
      const activeWorkflows = await this.db.getMany(`
        SELECT id, name, updated_at
        FROM tenant_workflows 
        WHERE active = true
        ORDER BY updated_at DESC
      `);

      console.log(`📊 Found ${activeWorkflows.length} active workflows to process`);

      const enrichedExecutions: EnrichedExecutionData[] = [];

      // 2. Per ogni workflow attivo, importa le ultime executions
      for (const workflow of activeWorkflows) {
        try {
          console.log(`🔍 Processing workflow: ${workflow.name} (${workflow.id})`);
          
          // Chiama API n8n con includeData=true
          const executionsData = await this.n8nApi.getExecutions({
            includeData: true,
            workflowId: workflow.id,
            limit: Math.min(10, limit), // Max 10 per workflow
            status: 'success' // Solo executions di successo per ora
          });

          console.log(`📥 Retrieved ${executionsData.length} executions for ${workflow.name}`);

          // 3. Processa ogni execution
          for (const execution of executionsData) {
            const enrichedData = await this.processExecutionData(execution, workflow);
            if (enrichedData) {
              enrichedExecutions.push(enrichedData);
              
              // 4. Salva nel database
              await this.saveEnrichedExecution(enrichedData);
            }
          }

        } catch (workflowError) {
          console.error(`❌ Error processing workflow ${workflow.name}:`, workflowError);
          continue; // Continua con il prossimo workflow
        }
      }

      console.log(`✅ Import completed. Processed ${enrichedExecutions.length} executions`);
      return enrichedExecutions;

    } catch (error) {
      console.error('❌ Failed to import execution data:', error);
      throw error;
    }
  }

  /**
   * Importa execution data per un workflow specifico
   * 
   * @param workflowId ID del workflow
   * @param limit Numero di executions da importare
   */
  async importWorkflowExecutions(workflowId: string, limit = 20): Promise<EnrichedExecutionData[]> {
    console.log(`🔄 Importing executions for workflow: ${workflowId}`);

    try {
      // Ottieni info workflow dal database
      const workflow = await this.db.getOne(`
        SELECT id, name FROM tenant_workflows WHERE id = $1
      `, [workflowId]);

      if (!workflow) {
        throw new Error(`Workflow ${workflowId} not found in database`);
      }

      // Chiama API n8n con includeData=true
      const executionsData = await this.n8nApi.getExecutions({
        includeData: true,
        workflowId: workflowId,
        limit: limit
      });

      console.log(`📥 Retrieved ${executionsData.length} executions for ${workflow.name}`);

      const enrichedExecutions: EnrichedExecutionData[] = [];

      for (const execution of executionsData) {
        const enrichedData = await this.processExecutionData(execution, workflow);
        if (enrichedData) {
          enrichedExecutions.push(enrichedData);
          await this.saveEnrichedExecution(enrichedData);
        }
      }

      return enrichedExecutions;

    } catch (error) {
      console.error(`❌ Failed to import executions for workflow ${workflowId}:`, error);
      throw error;
    }
  }

  /**
   * Processa execution data da n8n API ed estrae informazioni strutturate
   */
  private async processExecutionData(execution: any, workflow: any): Promise<EnrichedExecutionData | null> {
    try {
      const executionId = execution.id.toString();
      
      // 🔥 DEBUG: Log execution data per identificare data corruption
      console.log(`🔍 Processing execution ${executionId} for workflow ${workflow.id}`);
      const runData = execution.data?.resultData?.runData || {};
      console.log(`📊 RunData keys for execution ${executionId}:`, Object.keys(runData));
      
      // 🔥 DEBUG: Se è l'execution 111051, logga il contenuto del primo nodo
      if (executionId === '111051') {
        console.log(`🚨 DEBUGGING EXECUTION 111051:`);
        const firstNodeName = Object.keys(runData)[0];
        if (firstNodeName && runData[firstNodeName] && runData[firstNodeName][0]) {
          const firstNodeData = runData[firstNodeName][0];
          const emailContent = firstNodeData.data?.main?.[0]?.[0]?.json?.body?.content;
          if (emailContent) {
            const preview = emailContent.substring(0, 100);
            console.log(`📧 Email content preview for 111051: "${preview}..."`);
          }
        }
      }
      
      // Ottieni workflow completo dall'API per accedere alle note dei nodi
      let workflowDefinition = null;
      try {
        workflowDefinition = await this.n8nApi.getWorkflow(workflow.id);
        console.log(`📋 Fetched workflow definition for ${workflow.id}, found ${workflowDefinition?.nodes?.length || 0} nodes`);
      } catch (workflowError) {
        console.warn(`Could not fetch workflow definition for ${workflow.id}:`, workflowError);
        
        // 🔥 FALLBACK: Usa note del workflow dal database
        console.log(`🗂️ FALLBACK: Trying to get workflow notes from database`);
        const dbWorkflow = await this.db.getOne(`
          SELECT nodes_notes FROM tenant_workflows 
          WHERE id = $1 LIMIT 1
        `, [workflow.id]);
        
        if (dbWorkflow?.nodes_notes) {
          console.log(`✅ Found workflow notes in database:`, dbWorkflow.nodes_notes);
          // Crea una mock workflow definition con le note dal database
          workflowDefinition = {
            id: workflow.id,
            nodes: Object.keys(dbWorkflow.nodes_notes).map(nodeName => ({
              name: nodeName,
              notes: dbWorkflow.nodes_notes[nodeName]
            }))
          };
          console.log(`📋 Created mock workflow definition with ${workflowDefinition.nodes.length} nodes from database`);
        }
      }
      
      // Crea una mappa delle note dei nodi per determinare la visibilità
      const nodeNotesMap = new Map<string, string>();
      if (workflowDefinition?.nodes) {
        console.log(`📋 Workflow definition has ${workflowDefinition.nodes.length} nodes total`);
        for (const node of workflowDefinition.nodes) {
          if (node.notes) {
            nodeNotesMap.set(node.name, node.notes);
            console.log(`📝 Node "${node.name}" has notes: "${node.notes}"`);
          }
          console.log(`📌 All node names: "${node.name}" (id: ${node.id})`);
        }
      }
      console.log(`🗂️ Created notes map with ${nodeNotesMap.size} entries`)
      
      // Debug: Log execution runData node names (reuse existing runData)
      console.log(`🔍 RunData contains nodes:`, Object.keys(runData));
      
      const steps: ExecutionStepData[] = [];
      
      let totalNodes = 0;
      let successfulNodes = 0;
      let failedNodes = 0;

      // NUOVO APPROCCIO: Parti dalla definizione del workflow per includere TUTTI i nodi SHOW
      if (workflowDefinition?.nodes) {
        console.log(`📋 Processing ${workflowDefinition.nodes.length} nodes from workflow definition`);
        
        for (const node of workflowDefinition.nodes) {
          totalNodes++;
          
          // Determina visibilità basata sulle note del nodo + tipo trigger
          const nodeNotes = node.notes || '';
          const isMarkedShow = nodeNotes.toLowerCase().includes('show');
          const isTrigger = node.type && (
            node.type.includes('trigger') || 
            node.type === 'n8n-nodes-base.emailReadImap' ||
            node.type === 'n8n-nodes-base.webhook' ||
            node.type === 'n8n-nodes-base.cron' ||
            node.type === 'n8n-nodes-base.manualTrigger' ||
            node.name.toLowerCase().includes('ricezione') ||
            node.name.toLowerCase().includes('trigger')
          );
          
          const isVisible = isMarkedShow || isTrigger;
          
          // Estrai numero ordinamento da show-N (es: "show-1", "show-2", etc.)
          let customOrder = null;
          if (isMarkedShow) {
            const orderMatch = nodeNotes.match(/show[_-](\d+)/i);
            if (orderMatch) {
              customOrder = parseInt(orderMatch[1]);
              console.log(`🔢 Node "${node.name}" has custom order: show-${customOrder}`);
            }
          }
          
          if (isVisible) {
            const reason = isTrigger ? 'TRIGGER NODE' : `SHOW: "${nodeNotes}"`;
            console.log(`👁️ Node "${node.name}" marked as VISIBLE (${reason})`);
          }
          
          // Cerca dati execution per questo nodo (se disponibili)
          const nodeExecution = runData[node.name] ? runData[node.name][0] : null;
          
          let status: 'success' | 'error' | 'running' = 'success';
          let executionTime = 0;
          let inputData = null;
          let outputData = null;
          let errorMessage = undefined;
          
          if (nodeExecution) {
            const hasError = nodeExecution.error;
            status = hasError ? 'error' : 'success';
            executionTime = nodeExecution.executionTime || 0;
            // FIX: outputData è quello che il nodo ha prodotto
            // Alcuni nodi (come INFO ORDINI) usano ai_tool invece di main
            outputData = nodeExecution.data?.main?.[0] || 
                        nodeExecution.data?.ai_tool?.[0] || 
                        null;
            // FIX: inputData lo popoleremo dopo in base all'ordine dei nodi
            inputData = null; // Verrà popolato dopo l'ordinamento
            errorMessage = hasError ? nodeExecution.error.message : undefined;
            
            if (hasError) {
              failedNodes++;
            } else {
              successfulNodes++;
            }
          } else {
            // Nodo non eseguito - segnalo come "not-executed" se SHOW
            if (isVisible) {
              console.log(`⚠️ Node "${node.name}" marked SHOW but no execution data available`);
              status = 'not-executed' as any; // Stato speciale per nodi non eseguiti
            }
          }

          const stepData: ExecutionStepData = {
            nodeId: node.name,
            nodeName: node.name,
            nodeType: node.type || 'unknown',
            executionTime,
            inputData,
            outputData,
            status,
            error: errorMessage,
            isVisible, // Campo per filtro whitelist
            isTrigger: isTrigger, // Aggiunto per ordinamento
            position: node.position || { x: 0, y: 0 }, // Posizione nel canvas per ordinamento
            customOrder: customOrder // Ordinamento esplicito da show-N
          } as any;

          steps.push(stepData);
        }
        
        // Ordina gli step con nuovo sistema show-N per controllo preciso sequenza
        steps.sort((a: any, b: any) => {
          // Priorità 1: trigger sempre per primi
          if (a.isTrigger && !b.isTrigger) return -1;
          if (!a.isTrigger && b.isTrigger) return 1;
          
          // Priorità 2: ordinamento esplicito show-N (show-1, show-2, etc.)
          if (a.customOrder !== null && b.customOrder !== null) {
            return a.customOrder - b.customOrder;
          }
          if (a.customOrder !== null && b.customOrder === null) return -1;
          if (a.customOrder === null && b.customOrder !== null) return 1;
          
          // Priorità 3: nodi con execution data first (solo per quelli senza custom order)
          if (a.executionTime > 0 && b.executionTime === 0) return -1;
          if (a.executionTime === 0 && b.executionTime > 0) return 1;
          
          // Priorità 4: ordina per posizione Y (top-to-bottom workflow flow)
          if (a.position && b.position) {
            return a.position.y - b.position.y;
          }
          
          // Priorità 5: ordine alfabetico per nomi
          return a.nodeName.localeCompare(b.nodeName);
        });
        
        console.log(`📊 Processed ${totalNodes} nodes total, ${steps.filter(s => s.isVisible).length} marked as VISIBLE (sorted by trigger → custom-order → execution → flow)`);
        
        // Debug: log dell'ordine finale con custom order
        const visibleSteps = steps.filter(s => s.isVisible);
        console.log(`🔀 Final order: ${visibleSteps.map(s => {
          let label = s.nodeName;
          if (s.isTrigger) label += ' (TRIGGER)';
          if (s.customOrder !== null) label += ` (show-${s.customOrder})`;
          return label;
        }).join(' → ')}`);
        
        // FIX: Popola inputData con l'output del nodo precedente nell'ordine
        for (let i = 0; i < steps.length; i++) {
          const currentStep = steps[i];
          
          // Skip se non è visibile
          if (!currentStep.isVisible) continue;
          
          // Per i trigger node, l'input è sempre vuoto o un messaggio speciale
          if (currentStep.isTrigger) {
            currentStep.inputData = null; // I trigger non hanno input
            continue;
          }
          
          // Per gli altri nodi, cerca il nodo precedente visibile
          let prevVisibleStep = null;
          for (let j = i - 1; j >= 0; j--) {
            if (steps[j].isVisible) {
              prevVisibleStep = steps[j];
              break;
            }
          }
          
          // Se c'è un nodo precedente visibile, usa il suo output come input
          if (prevVisibleStep && prevVisibleStep.outputData) {
            currentStep.inputData = prevVisibleStep.outputData;
            console.log(`🔗 Connected input of "${currentStep.nodeName}" to output of "${prevVisibleStep.nodeName}"`);
          }
        }
        
        console.log(`✅ Input/Output chain connected for ${steps.filter(s => s.isVisible).length} visible nodes`);
      } else {
        // Fallback al vecchio approccio se non abbiamo workflow definition
        console.log(`⚠️ No workflow definition available, falling back to execution data only`);
        
        for (const [nodeName, nodeExecutions] of Object.entries(runData)) {
          totalNodes++;
          
          const nodeExecution = (nodeExecutions as any[])[0];
          if (!nodeExecution) continue;

          const hasError = nodeExecution.error;
          const status = hasError ? 'error' : 'success';
          
          if (hasError) {
            failedNodes++;
          } else {
            successfulNodes++;
          }

          // Determina visibilità basata sulle note del nodo + trigger detection
          const nodeNotes = nodeNotesMap.get(nodeName) || '';
          const isMarkedShow = nodeNotes.toLowerCase().includes('show');
          
          // CRITICAL FIX: Forza visibility per trigger nodes anche senza note
          const isTrigger = nodeName.toLowerCase().includes('ricezione') || 
                           nodeName.toLowerCase().includes('trigger') ||
                           nodeName.toLowerCase().includes('webhook') ||
                           nodeName.toLowerCase().includes('mail');
          
          const isVisible = isMarkedShow || isTrigger;
          console.log(`🔍 Node "${nodeName}": notes="${nodeNotes}" → isMarkedShow=${isMarkedShow}, isTrigger=${isTrigger}, visible=${isVisible}`);

          const stepData: ExecutionStepData = {
            nodeId: nodeName,
            nodeName: nodeName,
            nodeType: 'unknown',
            executionTime: nodeExecution.executionTime || 0,
            inputData: null, // FIX: Verrà popolato dopo
            outputData: nodeExecution.data?.main?.[0] || null, // FIX: Solo output data
            status,
            error: hasError ? nodeExecution.error.message : undefined,
            isVisible
          };

          steps.push(stepData);
        }
      }

      // Estrai business context (emails, IDs, amount, etc.)
      const businessContext = this.extractBusinessContext(steps);

      const enrichedData: EnrichedExecutionData = {
        executionId,
        workflowId: workflow.id,
        detailedData: execution,
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
      classifications: [],
      senderEmail: null,
      subject: null,
      classification: null,
      confidence: null,
      aiResponse: null,
      responseLength: null
    };

    for (const step of steps) {
      try {
        const stepDataString = JSON.stringify(step.outputData || step.inputData || {});
        
        // Estrai emails con regex più aggressiva
        const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
        const emails = stepDataString.match(emailRegex);
        if (emails) {
          context.extractedEmails.push(...emails);
          // Primo email trovato come sender email
          if (!context.senderEmail && emails.length > 0) {
            context.senderEmail = emails[0];
          }
        }

        // Estrazione SPECIFICA per dati nested nei JSON
        if (step.outputData && Array.isArray(step.outputData) && step.outputData.length > 0) {
          const data = step.outputData[0];
          
          // Cerca in tutti i livelli del JSON per email mittente
          this.deepSearchAndExtract(data, context, 'mittente', 'senderEmail');
          this.deepSearchAndExtract(data, context, 'email', 'senderEmail');
          this.deepSearchAndExtract(data, context, 'oggetto', 'subject');
          this.deepSearchAndExtract(data, context, 'subject', 'subject');
          this.deepSearchAndExtract(data, context, 'categoria', 'classification');
          this.deepSearchAndExtract(data, context, 'classification', 'classification');
          this.deepSearchAndExtract(data, context, 'category', 'classification');
          this.deepSearchAndExtract(data, context, 'confidence', 'confidence');
          this.deepSearchAndExtract(data, context, 'ai_response', 'aiResponse');
          this.deepSearchAndExtract(data, context, 'response', 'aiResponse');
          this.deepSearchAndExtract(data, context, 'ai_response_length', 'responseLength');
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

        // Cerca classificazioni/categorie anche nei dati diretti
        if (step.outputData && typeof step.outputData === 'object') {
          const data = Array.isArray(step.outputData) ? step.outputData[0] : step.outputData;
          if (data?.json?.categoria || data?.json?.classification || data?.json?.category) {
            const classification = data.json.categoria || data.json.classification || data.json.category;
            context.classifications.push(classification);
            if (!context.classification) {
              context.classification = classification;
            }
          }
        }

      } catch (error) {
        // Ignora errori di parsing per singoli step
        continue;
      }
    }

    // Rimuovi duplicati dagli array
    context.extractedEmails = [...new Set(context.extractedEmails)];
    context.extractedIds = [...new Set(context.extractedIds)];
    context.classifications = [...new Set(context.classifications)];

    return context;
  }

  /**
   * Ricerca ricorsiva nei dati JSON nested per estrarre valori specifici
   */
  private deepSearchAndExtract(obj: any, context: any, searchKey: string, contextKey: string): void {
    if (!obj || typeof obj !== 'object') return;

    // Se è un array, cerca in ogni elemento
    if (Array.isArray(obj)) {
      for (const item of obj) {
        this.deepSearchAndExtract(item, context, searchKey, contextKey);
      }
      return;
    }

    // Cerca la chiave nell'oggetto corrente
    for (const [key, value] of Object.entries(obj)) {
      if (key.toLowerCase().includes(searchKey.toLowerCase()) && value && !context[contextKey]) {
        context[contextKey] = value;
        return;
      }
      
      // Ricerca ricorsiva negli oggetti nested
      if (typeof value === 'object') {
        this.deepSearchAndExtract(value, context, searchKey, contextKey);
      }
    }
  }

  /**
   * Salva execution data arricchiti nel database
   */
  private async saveEnrichedExecution(data: EnrichedExecutionData): Promise<void> {
    try {
      // Controlla se l'execution già esiste nella tabella tenant_executions
      const existingExecution = await this.db.getOne(`
        SELECT id FROM tenant_executions WHERE id = $1
      `, [data.executionId]);

      if (existingExecution) {
        // Aggiorna execution esistente con dati arricchiti
        await this.db.query(`
          UPDATE tenant_executions 
          SET 
            raw_data = $2::jsonb,
            has_detailed_data = true,
            detailed_steps = $3::jsonb,
            business_context = $4::jsonb,
            total_nodes = $5,
            successful_nodes = $6,
            failed_nodes = $7
          WHERE id = $1
        `, [
          data.executionId,
          JSON.stringify(data.detailedData),
          JSON.stringify(data.steps),
          JSON.stringify(data.businessContext),
          data.totalNodes,
          data.successfulNodes,
          data.failedNodes
        ]);

        console.log(`✅ Updated execution ${data.executionId} with enriched data`);
      } else {
        // Inserisci nuova execution con tutti i dati necessari dall'API n8n
        const executionData = data.detailedData;
        const startedAt = executionData.startedAt || new Date().toISOString();
        const stoppedAt = executionData.stoppedAt || executionData.finishedAt || null;
        const duration = stoppedAt ? new Date(stoppedAt).getTime() - new Date(startedAt).getTime() : null;
        
        // Trova il tenant_id dal workflow (usa client_simulation_a per frontend testing)
        const workflow = await this.db.getOne(`
          SELECT tenant_id FROM tenant_workflows WHERE id = $1 AND tenant_id = 'client_simulation_a'
        `, [data.workflowId]);
        
        const tenantId = workflow?.tenant_id || 'client_simulation_a';
        
        await this.db.query(`
          INSERT INTO tenant_executions (
            id, workflow_id, tenant_id,
            status, mode, started_at, stopped_at, duration_ms,
            has_error,
            raw_data, has_detailed_data, detailed_steps, business_context,
            total_nodes, successful_nodes, failed_nodes
          ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
          )
        `, [
          data.executionId,
          data.workflowId,
          tenantId,
          executionData.status || 'success',
          executionData.mode || 'trigger',
          startedAt,
          stoppedAt,
          duration,
          data.failedNodes > 0,
          JSON.stringify(data.detailedData),
          true,
          JSON.stringify(data.steps),
          JSON.stringify(data.businessContext),
          data.totalNodes,
          data.successfulNodes,
          data.failedNodes
        ]);

        console.log(`✅ Inserted new execution ${data.executionId} with enriched data (tenant: ${tenantId})`);
      }

    } catch (error) {
      console.error(`❌ Error saving enriched execution ${data.executionId}:`, error);
      throw error;
    }
  }

  /**
   * Ottieni struttura workflow da n8n API (senza execution data)
   * Usato come fallback quando non abbiamo execution data
   */
  async getWorkflowStructure(workflowId: string): Promise<any> {
    try {
      console.log(`📋 Fetching workflow structure for: ${workflowId}`);
      const workflow = await this.n8nApi.getWorkflow(workflowId);
      
      if (workflow?.nodes) {
        console.log(`✅ Fetched workflow structure: ${workflow.nodes.length} nodes`);
        return {
          id: workflowId,
          name: workflow.name,
          nodes: workflow.nodes
        };
      }
      
      return null;
    } catch (error) {
      console.error(`❌ Failed to fetch workflow structure for ${workflowId}:`, error);
      return null;
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
}

export default ExecutionImportService;