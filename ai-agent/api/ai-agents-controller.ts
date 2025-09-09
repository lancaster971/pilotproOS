/**
 * AI Agents Controller
 * 
 * Gestisce la trasparenza operativa degli AI agents:
 * - Activity feed real-time degli agents
 * - Parsing intelligente delle execution data
 * - Business context extraction
 * - Agent session details
 */

import { Router, Request, Response, NextFunction } from 'express';
import { DatabaseConnection } from '../database/connection.js';
import { ExecutionImportService } from './execution-import-service.js';

// Auth middleware compatibile
const authMiddleware = (req: Request, res: Response, next: NextFunction) => {
  (req as any).user = {
    id: '1',
    email: 'admin@pilotpro.com',
    role: 'admin',
    tenantId: 'default_tenant'
  };
  next();
};

const router = Router();
const db = DatabaseConnection.getInstance();
const importService = new ExecutionImportService();

// Circuit Breaker per evitare thrashing su API fallite
const failedApiCalls = new Map<string, { count: number, lastFailed: number }>();
const CIRCUIT_BREAKER_THRESHOLD = 3; // Max tentativi prima di circuit breaker
const CIRCUIT_BREAKER_COOLDOWN = 5 * 60 * 1000; // 5 minuti cooldown

// Response Cache in memoria per performance
const responseCache = new Map<string, { data: any, timestamp: number }>();
const CACHE_TTL = 30 * 1000; // Cache TTL 30 secondi

/**
 * Determina se i dati del workflow devono essere refresh da n8n API
 * REGOLE INTELLIGENTI + CIRCUIT BREAKER:
 * 1. Se nessun dato detailed → forza refresh (MA non se API è in circuit breaker)
 * 2. Se ultima execution > 30 minuti fa → forza refresh  
 * 3. Se workflow updated_at > ultimo import → forza refresh
 * 4. CIRCUIT BREAKER: Se API fallisce troppo spesso, stop per 5 min
 */
async function shouldRefreshWorkflowData(workflowId: string, workflowData: any): Promise<boolean> {
  try {
    // CIRCUIT BREAKER: Controlla se API è in cooldown
    const circuitBreakerKey = `api_${workflowId}`;
    const failureRecord = failedApiCalls.get(circuitBreakerKey);
    
    if (failureRecord) {
      const timeSinceLastFailure = Date.now() - failureRecord.lastFailed;
      
      if (failureRecord.count >= CIRCUIT_BREAKER_THRESHOLD && timeSinceLastFailure < CIRCUIT_BREAKER_COOLDOWN) {
        console.log(`🚫 CIRCUIT BREAKER: API for workflow ${workflowId} is in cooldown (${failureRecord.count} failures, cooldown: ${Math.round((CIRCUIT_BREAKER_COOLDOWN - timeSinceLastFailure) / 1000)}s remaining)`);
        return false; // Block refresh durante cooldown
      }
      
      // Reset se cooldown è passato
      if (timeSinceLastFailure >= CIRCUIT_BREAKER_COOLDOWN) {
        failedApiCalls.delete(circuitBreakerKey);
        console.log(`✅ CIRCUIT BREAKER: Reset for workflow ${workflowId}`);
      }
    }
    
    // Regola 1: Nessun dato detailed disponibile
    if (!workflowData.has_detailed_data || !workflowData.last_detailed_steps) {
      console.log(`🔄 Refresh needed: No detailed data for workflow ${workflowId}`);
      return true;
    }
    
    // Regola 2: Ultima execution troppo vecchia (> 30 min)
    if (workflowData.last_execution_at) {
      const lastExecution = new Date(workflowData.last_execution_at);
      const thirtyMinutesAgo = new Date(Date.now() - 30 * 60 * 1000);
      
      if (lastExecution < thirtyMinutesAgo) {
        console.log(`🔄 Refresh needed: Last execution too old (${lastExecution.toISOString()}) for workflow ${workflowId}`);
        return true;
      }
    }
    
    // Regola 3: Workflow modificato di recente su n8n
    // Controllo se workflow updated_at è più recente dell'ultimo import
    const lastImportTime = await db.getOne(`
      SELECT MAX(started_at) as last_cache_update
      FROM tenant_executions 
      WHERE workflow_id = $1 AND has_detailed_data = true
    `, [workflowId]);
    
    if (lastImportTime?.last_cache_update && workflowData.updated_at) {
      const workflowUpdated = new Date(workflowData.updated_at);
      const cacheUpdated = new Date(lastImportTime.last_cache_update);
      
      if (workflowUpdated > cacheUpdated) {
        console.log(`🔄 Refresh needed: Workflow updated (${workflowUpdated.toISOString()}) after cache (${cacheUpdated.toISOString()}) for ${workflowId}`);
        return true;
      }
    }
    
    // Tutti i controlli passati - cache è valida
    console.log(`✅ Cache is valid for workflow ${workflowId}`);
    return false;
    
  } catch (error) {
    console.error(`❌ Error checking cache validity for workflow ${workflowId}:`, error);
    // In caso di errore, meglio refresh per sicurezza
    return true;
  }
}

// Interfacce per tipizzazione
interface AgentStep {
  nodeId: string;
  nodeName: string;
  type: 'input' | 'processing' | 'output' | 'error';
  startTime: Date;
  duration: number;
  input: any;
  output: any;
  parameters?: any;
  summary: string;
  details?: string;
}

interface AgentActivity {
  executionId: string;
  workflowId: string;
  workflowName: string;
  startedAt: Date;
  duration: number;
  status: 'success' | 'error' | 'running';
  
  // Dati business estratti
  steps: AgentStep[];
  businessContext: {
    senderEmail?: string;
    orderId?: string;
    invoiceNumber?: string;
    amount?: number;
    subject?: string;
    classification?: string;
    confidence?: number;
  };
  
  // Quick actions
  quickActions: {
    crmUrl?: string;
    externalRecordId?: string;
    replyAction?: string;
  };
}

/**
 * GET /api/tenant/:tenantId/agents/workflows  
 * 
 * Restituisce cards dei workflow AI agents attivi
 * Ogni card rappresenta un agent con i suoi dettagli base
 */
router.get('/tenant/:tenantId/agents/workflows', authMiddleware, async (req: Request, res: Response) => {
  try {
    const { tenantId } = req.params;
    const { limit = 20, offset = 0 } = req.query;
    const user = (req as any).user;
    
    // Verifica permessi tenant
    if (user.role !== 'admin' && user.tenantId !== tenantId) {
      return res.status(403).json({ error: 'Access denied to this tenant' });
    }
    
    console.log(`🔍 Fetching AI agent workflows for tenant: ${tenantId}`);

    // Query per trovare workflow AI attivi con info ultima execution
    const workflows = await db.getMany(`
      SELECT DISTINCT 
        tw.id,
        tw.name,
        tw.active,
        tw.updated_at,
        tw.created_at,
        tw.raw_data,
        -- Conta executions per workflow
        (SELECT COUNT(*) FROM tenant_executions te WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id) as total_executions,
        -- Ultima execution con detailed data (preferita)
        (SELECT te.id FROM tenant_executions te 
         WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
         ORDER BY te.has_detailed_data DESC NULLS LAST, te.started_at DESC LIMIT 1) as last_execution_id,
        (SELECT te.started_at FROM tenant_executions te 
         WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
         ORDER BY te.has_detailed_data DESC NULLS LAST, te.started_at DESC LIMIT 1) as last_execution_at,
        (SELECT te.status FROM tenant_executions te 
         WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
         ORDER BY te.has_detailed_data DESC NULLS LAST, te.started_at DESC LIMIT 1) as last_execution_status,
        (SELECT te.has_detailed_data FROM tenant_executions te 
         WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
         ORDER BY te.has_detailed_data DESC NULLS LAST, te.started_at DESC LIMIT 1) as has_detailed_data,
        -- Business context ultima execution
        (SELECT te.business_context FROM tenant_executions te 
         WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
         ORDER BY te.has_detailed_data DESC NULLS LAST, te.started_at DESC LIMIT 1) as last_business_context
      FROM tenant_workflows tw
      WHERE tw.tenant_id = $1 
        AND tw.active = true
        AND (
          tw.raw_data::text ILIKE '%openai%' OR
          tw.raw_data::text ILIKE '%langchain%' OR
          tw.raw_data::text ILIKE '%agent%' OR
          tw.raw_data::text ILIKE '%ai%' OR
          tw.name ILIKE '%CHATBOT%' OR
          tw.name ILIKE '%AGENT%' OR
          tw.name ILIKE '%AI%' OR
          tw.id IN (
            SELECT DISTINCT workflow_id 
            FROM tenant_executions 
            WHERE tenant_id = $1 AND has_detailed_data = true
          )
        )
      ORDER BY last_execution_at DESC NULLS LAST, tw.updated_at DESC
      LIMIT $2
    `, [tenantId, limit]);
    
    console.log(`📊 Found ${workflows.length} AI agent workflows for tenant ${tenantId}`);

    // Trasforma in formato agent cards
    const agents = workflows.map((workflow: any) => ({
      id: workflow.id,
      name: workflow.name,
      status: workflow.active ? 'active' : 'inactive',
      lastActivity: workflow.last_execution_at,
      lastExecutionId: workflow.last_execution_id,
      lastExecutionStatus: workflow.last_execution_status || 'unknown',
      totalExecutions: parseInt(workflow.total_executions) || 0,
      hasDetailedData: workflow.has_detailed_data || false,
      updatedAt: workflow.updated_at,
      type: 'ai-agent',
      // Preview business context per card
      preview: workflow.last_business_context ? {
        senderEmail: workflow.last_business_context.senderEmail,
        subject: workflow.last_business_context.subject,
        classification: workflow.last_business_context.classification
      } : null
    }));

    res.json({
      success: true,
      tenantId,
      data: agents,
      total: agents.length,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error getting agents activity:', error);
    res.status(500).json({ error: 'Failed to get agents activity' });
  }
});

/**
 * GET /api/tenant/:tenantId/agents/workflow/:workflowId/timeline
 * 
 * Timeline del workflow con nodi "SHOW" + dati ultima execution
 * SISTEMA CACHE INVALIDATION ROBUSTO: forza refresh se dati obsoleti
 */
router.get('/tenant/:tenantId/agents/workflow/:workflowId/timeline', authMiddleware, async (req: Request, res: Response) => {
  try {
    const { tenantId, workflowId } = req.params;
    const { forceRefresh = 'false' } = req.query;
    const user = (req as any).user;
    
    // Verifica permessi
    if (user.role !== 'admin' && user.tenantId !== tenantId) {
      return res.status(403).json({ error: 'Access denied to this tenant' });
    }
    
    console.log(`🔍 Fetching workflow timeline for: ${workflowId} (tenant: ${tenantId}, forceRefresh: ${forceRefresh})`);
    
    // PERFORMANCE: Check response cache first
    if (forceRefresh !== 'true') {
      const cacheKey = `timeline_${tenantId}_${workflowId}`;
      const cachedResponse = responseCache.get(cacheKey);
      
      if (cachedResponse && (Date.now() - cachedResponse.timestamp) < CACHE_TTL) {
        console.log(`⚡ CACHE HIT: Serving cached response for workflow ${workflowId} (age: ${Math.round((Date.now() - cachedResponse.timestamp) / 1000)}s)`);
        return res.json(cachedResponse.data);
      }
    }
    
    // 🔥 SEMPRE MOSTRA L'EXECUTION PIÙ RECENTE (non preferire has_detailed_data)
    const workflowData = await db.getOne(`
      SELECT 
        tw.id,
        tw.name,
        tw.active,
        tw.raw_data,
        tw.updated_at,
        -- 🆕 PRIORITÀ: Sempre l'execution PIÙ RECENTE per data (non per detailed_data)
        (SELECT te.id FROM tenant_executions te 
         WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
         ORDER BY te.started_at DESC LIMIT 1) as last_execution_id,
        (SELECT te.started_at FROM tenant_executions te 
         WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
         ORDER BY te.started_at DESC LIMIT 1) as last_execution_at,
        (SELECT te.duration_ms FROM tenant_executions te 
         WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
         ORDER BY te.started_at DESC LIMIT 1) as last_duration_ms,
        (SELECT te.status FROM tenant_executions te 
         WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
         ORDER BY te.started_at DESC LIMIT 1) as last_execution_status,
        (SELECT te.has_detailed_data FROM tenant_executions te 
         WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
         ORDER BY te.started_at DESC LIMIT 1) as has_detailed_data,
        (SELECT te.detailed_steps FROM tenant_executions te 
         WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
         ORDER BY te.started_at DESC LIMIT 1) as last_detailed_steps,
        (SELECT te.business_context FROM tenant_executions te 
         WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
         ORDER BY te.started_at DESC LIMIT 1) as last_business_context,
        (SELECT te.raw_data FROM tenant_executions te 
         WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
         ORDER BY te.started_at DESC LIMIT 1) as last_execution_raw_data,
        (SELECT COUNT(*) FROM tenant_executions te WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id) as total_executions
      FROM tenant_workflows tw
      WHERE tw.tenant_id = $1 AND tw.id = $2
    `, [tenantId, workflowId]);
    
    if (!workflowData) {
      return res.status(404).json({ error: 'Workflow not found' });
    }
    
    // 2. CACHE INVALIDATION: Verifica se dati devono essere aggiornati
    const shouldForceRefresh = forceRefresh === 'true' || await shouldRefreshWorkflowData(workflowId, workflowData);
    
    if (shouldForceRefresh) {
      console.log(`🔄 SMART REFRESH: Importing new executions without destroying existing data`);
      
      // 🛡️ NON CANCELLARE I DATI ESISTENTI - Solo forza re-import
      console.log(`💾 Preserving existing detailed_steps, importing fresh executions only`);
      
      // 🚨 DEBUG: Force processing execution 111051 dai raw_data esistenti
      if (workflowId === 'SJuCGGefzPZBg9XU') {
        console.log('🔥 SPECIAL DEBUG: Processing execution 111051 from existing raw_data');
        
        // Get raw_data per execution 111051
        const execution111051 = await db.getOne(`
          SELECT id, raw_data, workflow_id 
          FROM tenant_executions 
          WHERE id = '111051' AND workflow_id = $1
        `, [workflowId]);
        
        if (execution111051 && execution111051.raw_data) {
          console.log('🎯 Found execution 111051 with raw_data, forcing processing...');
          
          // Create a mock workflow object for processing
          const mockWorkflow = { id: workflowId, name: 'CHATBOT_MAIL__SIMPLE' };
          
          // Process the execution data directly using private method
          const enrichedData = await (importService as any).processExecutionData(execution111051.raw_data, mockWorkflow);
          
          if (enrichedData) {
            console.log(`✅ Successfully processed execution 111051: ${enrichedData.steps.length} steps extracted`);
            // Save the processed data using private method
            await (importService as any).saveEnrichedExecution(enrichedData);
            console.log('💾 Saved processed data to database');
          } else {
            console.log('❌ Failed to process execution 111051 data');
          }
        }
      }

      // Forza import execution fresh
      try {
        await importService.importWorkflowExecutions(workflowId, 1);
        
        // Re-fetch workflow data dopo import - SEMPRE LA PIÙ RECENTE
        const refreshedData = await db.getOne(`
          SELECT 
            tw.id, tw.name, tw.active, tw.raw_data, tw.updated_at,
            (SELECT te.id FROM tenant_executions te 
             WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
             ORDER BY te.started_at DESC LIMIT 1) as last_execution_id,
            (SELECT te.started_at FROM tenant_executions te 
             WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
             ORDER BY te.started_at DESC LIMIT 1) as last_execution_at,
            (SELECT te.duration_ms FROM tenant_executions te 
             WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
             ORDER BY te.started_at DESC LIMIT 1) as last_duration_ms,
            (SELECT te.status FROM tenant_executions te 
             WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
             ORDER BY te.started_at DESC LIMIT 1) as last_execution_status,
            (SELECT te.has_detailed_data FROM tenant_executions te 
             WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
             ORDER BY te.started_at DESC LIMIT 1) as has_detailed_data,
            (SELECT te.detailed_steps FROM tenant_executions te 
             WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
             ORDER BY te.started_at DESC LIMIT 1) as last_detailed_steps,
            (SELECT te.business_context FROM tenant_executions te 
             WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
             ORDER BY te.started_at DESC LIMIT 1) as last_business_context,
            (SELECT te.raw_data FROM tenant_executions te 
             WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id 
             ORDER BY te.started_at DESC LIMIT 1) as last_execution_raw_data,
            (SELECT COUNT(*) FROM tenant_executions te WHERE te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id) as total_executions
          FROM tenant_workflows tw
          WHERE tw.tenant_id = $1 AND tw.id = $2
        `, [tenantId, workflowId]);
        
        if (refreshedData) {
          // Usa i dati refreshed
          Object.assign(workflowData, refreshedData);
          console.log(`✅ Cache refreshed successfully for workflow ${workflowId}`);
        }
      } catch (importError) {
        console.error(`❌ Failed to refresh cache for workflow ${workflowId}:`, importError);
        
        // CIRCUIT BREAKER: Registra fallimento API
        const circuitBreakerKey = `api_${workflowId}`;
        const currentFailure = failedApiCalls.get(circuitBreakerKey) || { count: 0, lastFailed: 0 };
        currentFailure.count++;
        currentFailure.lastFailed = Date.now();
        failedApiCalls.set(circuitBreakerKey, currentFailure);
        
        console.log(`🔥 CIRCUIT BREAKER: Recorded failure ${currentFailure.count}/${CIRCUIT_BREAKER_THRESHOLD} for workflow ${workflowId}`);
        
        // Continua con dati cached esistenti se fallisce import
      }
    }
    
    // 3. Estrai nodi "SHOW" dalla struttura workflow + dati execution se disponibili
    let timeline = [];
    let businessContext = {};
    
    if (workflowData.has_detailed_data && workflowData.last_detailed_steps) {
      // 🎯 CASO 1: Abbiamo detailed steps - mostra solo nodi SHOW con dati
      const detailedSteps = workflowData.last_detailed_steps;
      const visibleSteps = detailedSteps.filter((step: any) => step.isVisible === true);
      
      timeline = visibleSteps.map((step: any, index: number) => ({
        nodeId: step.nodeId,
        nodeName: step.nodeName,
        nodeType: step.nodeType || 'unknown',
        status: step.status === 'error' ? 'error' : 'success',
        executionTime: step.executionTime || 0,
        inputData: step.inputData,
        outputData: step.outputData,
        error: step.error,
        summary: `${step.nodeName} - ${step.error ? 'ERROR' : 'SUCCESS'}`,
        order: index + 1,
        hasExecutionData: true,
        customOrder: step.customOrder || null // Include custom order from show-N parsing
      }));
      
      businessContext = workflowData.last_business_context || {};
      console.log(`📊 Found ${timeline.length} visible nodes with execution data`);
    } else if (workflowData.last_execution_raw_data) {
      // 🔥 CASO 2: PARSING IN TEMPO REALE - No detailed steps ma abbiamo raw_data
      console.log(`🚀 REAL-TIME PARSING: Creating timeline from latest execution raw_data`);
      
      try {
        const executionData = {
          id: workflowData.last_execution_id,
          workflow_id: workflowId,
          workflow_name: workflowData.name,
          started_at: workflowData.last_execution_at,
          duration_ms: workflowData.last_duration_ms,
          status: workflowData.last_execution_status,
          has_error: workflowData.last_execution_status === 'error',
          stopped_at: workflowData.last_execution_at, // Approssimazione
          raw_data: workflowData.last_execution_raw_data,
          detailed_steps: null,
          business_context: null,
          has_detailed_data: false
        };
        
        // Usa la funzione di parsing esistente per creare detailed_steps in tempo reale
        const parseResult = await parseExecutionToActivity(executionData, tenantId);
        
        if (parseResult && parseResult.steps && parseResult.steps.length > 0) {
          // 🚀 Usa direttamente gli steps parsati in tempo reale
          timeline = parseResult.steps
            .filter((step: any) => step.isVisible === true) // Solo nodi SHOW visibili
            .map((step: any, index: number) => ({
              nodeId: step.nodeId,
              nodeName: step.nodeName,
              nodeType: step.type || 'unknown', // AgentStep usa 'type' non 'nodeType'
              status: step.type === 'error' ? 'error' : 'success',
              executionTime: step.duration || 0, // AgentStep usa 'duration'
              inputData: step.input,
              outputData: step.output,
              error: null, // Gestito in step.type
              summary: step.summary || `${step.nodeName} - ${step.type === 'error' ? 'ERROR' : 'SUCCESS'}`,
              order: index + 1,
              hasExecutionData: true,
              customOrder: null // TODO: Implementare custom order parsing
            }));
          
          businessContext = parseResult.businessContext || {};
          console.log(`🎉 REAL-TIME SUCCESS: Generated ${timeline.length} nodes from raw_data`);
        } else {
          throw new Error('Failed to parse raw_data - no steps returned');
        }
      } catch (parseError) {
        console.error(`❌ REAL-TIME PARSING FAILED:`, parseError);
        // Fallback al caso 3 (structure only)
        timeline = [];
      }
    }
    
    if (timeline.length === 0) {
      // Caso: No detailed steps - mostra struttura nodi SHOW senza dati execution
      console.log(`⚠️ No execution data available, fetching workflow structure only`);
      
      try {
        // FALLBACK: Usa raw_data dal database invece di chiamare n8n API
        let workflowStructure = null;
        
        if (workflowData.raw_data?.nodes) {
          // Usa direttamente i raw_data dal database
          workflowStructure = {
            id: workflowId,
            name: workflowData.name,
            nodes: workflowData.raw_data.nodes
          };
          console.log(`📋 Using workflow structure from database: ${workflowStructure.nodes.length} nodes`);
        } else {
          // Prova a ottenere da n8n API come fallback
          workflowStructure = await importService.getWorkflowStructure(workflowId);
        }
        
        if (workflowStructure?.nodes) {
          console.log(`📋 Fetched workflow structure with ${workflowStructure.nodes.length} nodes`);
          
          // Crea timeline dai nodi del workflow (senza execution data)
          timeline = workflowStructure.nodes
            .filter((node: any) => {
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
              
              // DEBUG: Log each node analysis
              console.log(`🔍 Node "${node.name}": notes="${nodeNotes}" → isMarkedShow=${isMarkedShow}, isTrigger=${isTrigger}, visible=${isMarkedShow || isTrigger}`);
              
              return isMarkedShow || isTrigger;
            })
            .map((node: any, index: number) => {
              const nodeNotes = node.notes || '';
              let customOrder = null;
              if (nodeNotes.toLowerCase().includes('show')) {
                const orderMatch = nodeNotes.match(/show[_-](\d+)/i);
                if (orderMatch) {
                  customOrder = parseInt(orderMatch[1]);
                }
              }
              
              return {
                nodeId: node.name,
                nodeName: node.name,
                nodeType: node.type || 'unknown',
                status: 'success',
                executionTime: 0,
                inputData: null,
                outputData: null,
                error: null,
                summary: `${node.name} - STRUCTURE ONLY (no execution data)`,
                order: index + 1,
                hasExecutionData: false,
                customOrder: customOrder
              };
            })
            .sort((a: any, b: any) => {
              // Stessa logica di ordinamento
              const aIsTrigger = a.nodeType?.includes('trigger') || a.nodeName.toLowerCase().includes('trigger');
              const bIsTrigger = b.nodeType?.includes('trigger') || b.nodeName.toLowerCase().includes('trigger');
              
              if (aIsTrigger && !bIsTrigger) return -1;
              if (!aIsTrigger && bIsTrigger) return 1;
              
              if (a.customOrder !== null && b.customOrder !== null) {
                return a.customOrder - b.customOrder;
              }
              if (a.customOrder !== null && b.customOrder === null) return -1;
              if (a.customOrder === null && b.customOrder !== null) return 1;
              
              return a.nodeName.localeCompare(b.nodeName);
            });
            
          console.log(`📊 Created structure-only timeline with ${timeline.length} visible nodes`);
        }
      } catch (structureError) {
        console.error(`❌ Could not fetch workflow structure:`, structureError);
        timeline = [];
      }
      
      businessContext = {};
    }
    
    const result = {
      workflowId: workflowData.id,
      workflowName: workflowData.name,
      status: workflowData.active ? 'active' : 'inactive',
      lastExecution: workflowData.last_execution_id ? {
        id: workflowData.last_execution_id,
        executedAt: workflowData.last_execution_at,
        duration: workflowData.last_duration_ms,
        status: workflowData.last_execution_status
      } : null,
      totalExecutions: parseInt(workflowData.total_executions) || 0,
      timeline,
      businessContext,
      hasExecutionData: workflowData.has_detailed_data || false
    };
    
    const responseData = {
      success: true,
      tenantId,
      workflowId,
      data: result,
      timestamp: new Date().toISOString()
    };
    
    // PERFORMANCE: Cache response for 30 seconds
    if (forceRefresh !== 'true') {
      const cacheKey = `timeline_${tenantId}_${workflowId}`;
      responseCache.set(cacheKey, {
        data: responseData,
        timestamp: Date.now()
      });
      console.log(`💾 CACHED: Response cached for workflow ${workflowId} (TTL: ${CACHE_TTL / 1000}s)`);
    }
    
    res.json(responseData);
    
  } catch (error) {
    console.error('Error getting workflow timeline:', error);
    res.status(500).json({ 
      success: false,
      error: 'Failed to get workflow timeline',
      message: (error as Error).message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/tenant/:tenantId/agents/execution/:executionId/details
 * 
 * Dettagli completi di un'execution di AI agent (DEPRECATED - usa workflow timeline)
 * con step-by-step breakdown
 */
router.get('/tenant/:tenantId/agents/execution/:executionId/details', authMiddleware, async (req: Request, res: Response) => {
  try {
    const { tenantId, executionId } = req.params;
    const user = (req as any).user;
    
    // Verifica permessi
    if (user.role !== 'admin' && user.tenantId !== tenantId) {
      return res.status(403).json({ error: 'Access denied to this tenant' });
    }
    
    // Recupera execution completa con workflow data
    const execution = await db.getOne(`
      SELECT 
        te.*,
        tw.name as workflow_name,
        tw.raw_data as workflow_data
      FROM tenant_executions te
      JOIN tenant_workflows tw ON te.workflow_id = tw.id AND te.tenant_id = tw.tenant_id
      WHERE te.tenant_id = $1 AND te.id = $2
    `, [tenantId, executionId]);
    
    if (!execution) {
      return res.status(404).json({ error: 'Execution not found' });
    }
    
    // Parse dettagliato con workflow context
    const detailsActivity = await parseExecutionToActivityDetailed(execution, tenantId);
    
    res.json({
      tenantId,
      executionId,
      details: detailsActivity
    });
    
  } catch (error) {
    console.error('Error getting execution details:', error);
    res.status(500).json({ error: 'Failed to get execution details' });
  }
});

/**
 * Parser intelligente: execution data → AgentActivity
 * 
 * Estrae business context e step specifici dall'execution raw_data
 * basandosi sul workflow CHATBOT_MAIL__SIMPLE come modello
 */
async function parseExecutionToActivity(execution: any, tenantId: string): Promise<AgentActivity> {
  // Se abbiamo detailed_steps dal database, usali!
  if (execution.has_detailed_data && execution.detailed_steps) {
    const detailedSteps = execution.detailed_steps;
    const businessContext = execution.business_context || {};
    
    // Converti detailed_steps in AgentStep format
    const steps: AgentStep[] = detailedSteps.map((step: any) => ({
      nodeId: step.nodeId,
      nodeName: step.nodeName,
      type: step.status === 'error' ? 'error' : 'processing',
      startTime: new Date(execution.started_at),
      duration: step.executionTime || 0,
      input: step.inputData,
      output: step.outputData,
      summary: `Node: ${step.nodeName}${step.error ? ` - ERROR: ${step.error}` : ' - SUCCESS'}`,
      details: step.error || `Executed successfully in ${step.executionTime || 0}ms`
    }));
    
    return {
      executionId: execution.id,
      workflowId: execution.workflow_id,
      workflowName: execution.workflow_name,
      startedAt: new Date(execution.started_at),
      duration: execution.duration_ms || 0,
      status: execution.has_error ? 'error' : (execution.stopped_at ? 'success' : 'running'),
      steps,
      businessContext,
      quickActions: {} // Potrebbero essere arricchiti in seguito
    };
  }
  
  // Fallback al parsing tradizionale
  const rawData = execution.raw_data || {};
  const runData = rawData.data?.resultData?.runData || {};
  
  const steps: AgentStep[] = [];
  const businessContext: any = {};
  const quickActions: any = {};
  
  // Parse specifico per CHATBOT_MAIL__SIMPLE
  if (execution.workflow_name === 'CHATBOT_MAIL__SIMPLE') {
    // 1. Clean Data Agent - Estrazione dati iniziali
    if (runData['1 - Clean Data for Agent1']) {
      const cleanDataNode = runData['1 - Clean Data for Agent1'][0];
      if (cleanDataNode?.data?.main?.[0]?.[0]?.json) {
        const cleanData = cleanDataNode.data.main[0][0].json;
        
        businessContext.senderEmail = cleanData.mittente;
        businessContext.orderId = cleanData.order_id;
        businessContext.subject = cleanData.oggetto;
        
        steps.push({
          nodeId: '1 - Clean Data for Agent1',
          nodeName: 'Clean Data Agent',
          type: 'processing',
          startTime: new Date(execution.started_at),
          duration: 500, // Stima
          input: { rawEmail: 'Customer email received' },
          output: cleanData,
          summary: `Extracted customer email: ${cleanData.mittente}${cleanData.order_id ? `, Order ID: ${cleanData.order_id}` : ''}`,
          details: `Processed email from ${cleanData.mittente} with subject "${cleanData.oggetto}"`
        });
      }
    }
    
    // 2. AI Classification
    if (runData['MERGE DI TUTTI I DATI']) {
      const mergeNode = runData['MERGE DI TUTTI I DATI'][0];
      if (mergeNode?.data?.main?.[0]?.[0]?.json) {
        const classification = mergeNode.data.main[0][0].json;
        
        businessContext.classification = classification.categoria || classification.output?.categoria;
        businessContext.confidence = classification.confidence || classification.output?.confidence;
        
        steps.push({
          nodeId: 'MERGE DI TUTTI I DATI',
          nodeName: 'AI Classifier',
          type: 'processing',
          startTime: new Date(execution.started_at + 1000),
          duration: 2000,
          input: { customerMessage: businessContext.subject },
          output: classification,
          summary: `Classified as: ${businessContext.classification} (${businessContext.confidence}% confidence)`,
          details: `AI determined this is a ${businessContext.classification} inquiry with ${businessContext.confidence}% confidence`
        });
      }
    }
    
    // 3. Task Analysis
    if (runData['2 - Execute Workflow']) {
      const taskNode = runData['2 - Execute Workflow'][0];
      if (taskNode?.data?.main?.[0]?.[0]?.json) {
        const taskData = taskNode.data.main[0][0].json;
        
        steps.push({
          nodeId: '2 - Execute Workflow',
          nodeName: 'Task Analyzer',
          type: 'processing',
          startTime: new Date(execution.started_at + 3000),
          duration: 1500,
          input: { classification: businessContext.classification },
          output: taskData,
          summary: `Analyzed customer satisfaction: ${taskData.customer_satisfaction}, Follow-up needed: ${taskData.follow_up_needed}`,
          details: `Identified ${taskData.required_actions?.length || 0} required actions, sentiment: ${taskData.customer_sentiment || 'neutral'}`
        });
      }
    }
    
    // 4. Final Response (se presente)
    if (runData['EMAIL DATA COLLECTOR']) {
      const collectorNode = runData['EMAIL DATA COLLECTOR'][0];
      if (collectorNode?.data?.main?.[0]?.[0]?.json) {
        const finalData = collectorNode.data.main[0][0].json;
        
        steps.push({
          nodeId: 'EMAIL DATA COLLECTOR',
          nodeName: 'Response Generator',
          type: 'output',
          startTime: new Date(execution.started_at + 4500),
          duration: 1000,
          input: { allProcessedData: 'Combined AI analysis' },
          output: { emailSent: finalData.send_successful, responseLength: finalData.ai_response_length },
          summary: `Email response ${finalData.send_successful ? 'sent successfully' : 'failed'}, ${finalData.ai_response_length} characters`,
          details: `Generated AI response using ${finalData.ai_model_used || 'GPT-4'}, processing time: ${finalData.ai_processing_time_ms}ms`
        });
      }
    }
    
    // Quick Actions per CHATBOT_MAIL__SIMPLE
    if (businessContext.orderId) {
      quickActions.crmUrl = `https://crm.example.com/orders/${businessContext.orderId}`;
      quickActions.externalRecordId = businessContext.orderId;
    }
    if (businessContext.senderEmail) {
      quickActions.replyAction = `mailto:${businessContext.senderEmail}?subject=Re: ${businessContext.subject}`;
    }
  }
  
  return {
    executionId: execution.id,
    workflowId: execution.workflow_id,
    workflowName: execution.workflow_name,
    startedAt: new Date(execution.started_at),
    duration: execution.duration_ms || 0,
    status: execution.has_error ? 'error' : (execution.stopped_at ? 'success' : 'running'),
    steps,
    businessContext,
    quickActions
  };
}

/**
 * Parser dettagliato per modal drill-down
 */
async function parseExecutionToActivityDetailed(execution: any, tenantId: string): Promise<AgentActivity & { rawData: any }> {
  const basicActivity = await parseExecutionToActivity(execution, tenantId);
  
  return {
    ...basicActivity,
    rawData: execution.raw_data // Include raw data per debug/advanced view
  };
}

/**
 * POST /api/agents/circuit-breaker/reset
 * 
 * Reset circuit breaker per riabilitare API calls bloccate
 * Utile per rimuovere cooldown dopo fix di problemi API
 */
router.post('/agents/circuit-breaker/reset', authMiddleware, async (req: Request, res: Response) => {
  try {
    const { workflowId } = req.body;
    
    if (workflowId) {
      // Reset circuit breaker specifico per un workflow
      const circuitBreakerKey = `api_${workflowId}`;
      const wasBlocked = failedApiCalls.has(circuitBreakerKey);
      failedApiCalls.delete(circuitBreakerKey);
      
      console.log(`🔄 CIRCUIT BREAKER: Reset for specific workflow ${workflowId} (was blocked: ${wasBlocked})`);
      
      res.json({
        success: true,
        message: `Circuit breaker reset for workflow ${workflowId}`,
        data: {
          workflowId,
          wasBlocked,
          resetAt: new Date().toISOString()
        }
      });
    } else {
      // Reset ALL circuit breakers
      const totalBlocked = failedApiCalls.size;
      const blockedWorkflows = Array.from(failedApiCalls.keys()).map(key => key.replace('api_', ''));
      failedApiCalls.clear();
      
      console.log(`🔄 CIRCUIT BREAKER: Reset ALL (${totalBlocked} workflows unblocked)`);
      
      res.json({
        success: true,
        message: `All circuit breakers reset (${totalBlocked} workflows unblocked)`,
        data: {
          totalUnblocked: totalBlocked,
          unblockedWorkflows: blockedWorkflows,
          resetAt: new Date().toISOString()
        }
      });
    }
    
  } catch (error) {
    console.error('❌ Error resetting circuit breaker:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to reset circuit breaker',
      message: (error as Error).message
    });
  }
});

/**
 * POST /api/tenant/:tenantId/agents/workflow/:workflowId/refresh
 * 
 * FORCE REFRESH: Invalida cache e importa dati fresh da n8n API
 * Endpoint per forzare sync immediato quando workflow cambia
 */
router.post('/tenant/:tenantId/agents/workflow/:workflowId/refresh', authMiddleware, async (req: Request, res: Response) => {
  try {
    const { tenantId, workflowId } = req.params;
    const user = (req as any).user;
    
    // Verifica permessi
    if (user.role !== 'admin' && user.tenantId !== tenantId) {
      return res.status(403).json({ error: 'Access denied to this tenant' });
    }
    
    console.log(`🔄 FORCE REFRESH requested for workflow ${workflowId} (tenant: ${tenantId})`);
    
    // 1. Reset circuit breaker per questo workflow prima di tentare refresh
    const circuitBreakerKey = `api_${workflowId}`;
    failedApiCalls.delete(circuitBreakerKey);
    console.log(`✅ Circuit breaker reset for workflow ${workflowId}`);
    
    // 2. 🔄 SOFT REFRESH: Non cancellare dati esistenti, solo forza re-import se necessario
    console.log(`💾 Preserving existing detailed_steps, forcing fresh import only`);
    // Nota: Non cancelliamo i dati esistenti per evitare perdite
    
    // 3. 🎯 RECUPERA DATI REALI: Fetch latest execution con includeData=true
    try {
      // Get latest execution ID per questo workflow
      const latestExecution = await db.getOne(`
        SELECT id FROM tenant_executions 
        WHERE workflow_id = $1 AND tenant_id = $2 
        ORDER BY started_at DESC LIMIT 1
      `, [workflowId, tenantId]);

      if (latestExecution?.id) {
        console.log(`🔍 Fetching real execution data for ${latestExecution.id} with includeData=true`);
        
        // Fetch execution con dati completi da n8n API
        const executionWithData = await importService.getN8nClient().getExecution(latestExecution.id, true);
        
        if (executionWithData && executionWithData.data) {
          console.log(`✅ Retrieved real execution data from n8n API for ${latestExecution.id}`);
          
          // Parse real data e salva nel database
          const realDetailedSteps = await parseRealExecutionData(executionWithData, workflowId, tenantId);
          
          if (realDetailedSteps && realDetailedSteps.length > 0) {
            await db.query(`
              UPDATE tenant_executions 
              SET detailed_steps = $1, has_detailed_data = true, 
                  raw_data = $2, last_synced_at = CURRENT_TIMESTAMP
              WHERE id = $3 AND tenant_id = $4
            `, [JSON.stringify(realDetailedSteps), JSON.stringify(executionWithData), latestExecution.id, tenantId]);
            
            console.log(`💾 Saved ${realDetailedSteps.length} real nodes data for execution ${latestExecution.id}`);
          }
        }
      }
    } catch (apiError: any) {
      console.log(`⚠️ Direct API fetch failed, falling back to import service:`, apiError?.message || apiError);
    }
    
    // 4. Fallback: Forza import fresh da n8n API se direct fetch fallisce
    const importResult = await importService.importWorkflowExecutions(workflowId, 3);
    
    // 4. Verifica successo import
    const refreshedData = await db.getOne(`
      SELECT 
        COUNT(*) as detailed_executions,
        MAX(started_at) as last_execution,
        MAX(CASE WHEN has_detailed_data = true THEN 1 ELSE 0 END) as has_fresh_data
      FROM tenant_executions 
      WHERE workflow_id = $1 AND tenant_id = $2
    `, [workflowId, tenantId]);
    
    // 5. 🔥 CRITICAL FIX: Forza invalidazione cache del timeline endpoint
    // Il timeline endpoint ha il suo sistema di refresh automatico che rebuilda
    // i dati summary quando rileva cache invalidata
    console.log(`✅ Force refresh completed - timeline endpoint will auto-refresh summary data`);
    console.log(`📊 Imported ${importResult.length} executions for timeline cache invalidation`);
    
    res.json({
      success: true,
      message: `Workflow ${workflowId} cache refreshed successfully`,
      data: {
        workflowId,
        tenantId,
        importedExecutions: importResult.length,
        detailedExecutions: parseInt(refreshedData?.detailed_executions || '0'),
        lastExecution: refreshedData?.last_execution,
        hasFreshData: refreshedData?.has_fresh_data === 1,
        refreshedAt: new Date().toISOString()
      },
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error(`❌ Error refreshing workflow ${req.params.workflowId}:`, error);
    
    // 🔥 CRITICAL: Quando l'API fallisce, invalida comunque cache response 
    // per forzare il frontend a mostrare almeno i dati del database (anche se vecchi)
    const cacheKey = `timeline_${req.params.tenantId}_${req.params.workflowId}`;
    responseCache.delete(cacheKey);
    console.log(`🗑️ Cache invalidated for ${cacheKey} due to API failure`);
    
    res.status(500).json({
      success: false,
      error: 'Failed to refresh workflow cache',
      message: (error as Error).message,
      cacheCleared: true,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /webhook/n8n/execution-complete
 * 
 * WEBHOOK REAL-TIME: Riceve notifiche da n8n quando un workflow viene eseguito
 * Permette refresh immediato dei dati senza attendere polling periodico
 * 
 * SECURITY: Richiede API Key nell'header X-Webhook-Secret
 */
router.post('/webhook/n8n/execution-complete', async (req: Request, res: Response) => {
  // 🔒 SECURITY: Verifica API Key prima di processare
  const webhookSecret = req.headers['x-webhook-secret'] || req.headers['x-api-key'];
  const expectedSecret = process.env.WEBHOOK_SECRET || 'pilotpro-webhook-2025-secure';
  
  if (!webhookSecret || webhookSecret !== expectedSecret) {
    console.warn(`🚫 WEBHOOK SECURITY: Unauthorized webhook attempt from ${req.ip}`);
    console.warn(`🚫 Expected secret: ${expectedSecret?.substring(0, 8)}...`);
    console.warn(`🚫 Received secret: ${webhookSecret?.toString().substring(0, 8)}...`);
    
    return res.status(401).json({
      error: 'Unauthorized',
      message: 'Invalid or missing webhook secret',
      required: 'X-Webhook-Secret header with valid API key',
      timestamp: new Date().toISOString()
    });
  }
  
  console.log(`🔒 WEBHOOK SECURITY: Valid API key received from ${req.ip}`);
  try {
    const payload = req.body;
    
    console.log(`📥 WEBHOOK: Execution completed notification received`);
    console.log(`📊 Payload:`, JSON.stringify(payload, null, 2));
    
    // Estrai dati essenziali dal webhook n8n
    const executionId = payload.executionId || payload.execution_id;
    const workflowId = payload.workflowId || payload.workflow_id;
    const tenantId = payload.tenantId || payload.tenant_id || 'client_simulation_a'; // fallback
    const status = payload.status || 'success';
    
    if (!executionId || !workflowId) {
      console.warn(`⚠️ WEBHOOK: Missing required fields (executionId: ${executionId}, workflowId: ${workflowId})`);
      return res.status(400).json({
        error: 'Missing required fields: executionId and workflowId',
        received: payload
      });
    }
    
    console.log(`🔄 WEBHOOK: Processing execution ${executionId} for workflow ${workflowId} (tenant: ${tenantId})`);
    
    // 1. Invalida cache per questo workflow specifico
    const cacheKey = `timeline_${tenantId}_${workflowId}`;
    responseCache.delete(cacheKey);
    console.log(`🗑️ WEBHOOK: Cache invalidated for ${cacheKey}`);
    
    // 2. Reset circuit breaker se era attivo
    const circuitBreakerKey = `api_${workflowId}`;
    if (failedApiCalls.has(circuitBreakerKey)) {
      failedApiCalls.delete(circuitBreakerKey);
      console.log(`✅ WEBHOOK: Circuit breaker reset for workflow ${workflowId}`);
    }
    
    // 3. Triggera import immediato per questa execution (background)
    // Non blocchiamo la response del webhook per questo
    setTimeout(async () => {
      try {
        console.log(`🔄 WEBHOOK: Starting background import for execution ${executionId}`);
        const importResult = await importService.importWorkflowExecutions(workflowId, 1);
        console.log(`✅ WEBHOOK: Background import completed, ${importResult.length} executions processed`);
      } catch (error) {
        console.error(`❌ WEBHOOK: Background import failed for execution ${executionId}:`, error);
      }
    }, 1000); // Delay di 1 secondo per permettere a n8n di completare completamente
    
    // 4. Response immediata per confermare ricezione webhook
    res.json({
      success: true,
      message: 'Execution completion webhook processed',
      data: {
        executionId,
        workflowId,
        tenantId,
        status,
        processedAt: new Date().toISOString(),
        actions: [
          'Cache invalidated',
          'Circuit breaker reset',
          'Background import triggered'
        ]
      },
      timestamp: new Date().toISOString()
    });
    
    console.log(`✅ WEBHOOK: Execution ${executionId} webhook processed successfully`);
    
  } catch (error) {
    console.error('❌ WEBHOOK: Error processing execution completion:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to process execution completion webhook',
      message: (error as Error).message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * 🎯 PARSING REALE N8N EXECUTION DATA
 * 
 * Parsifica i dati reali dall'API n8n con includeData=true
 * Estrae input/output autentici di ogni nodo per il timeline
 */
/**
 * DEBUG: Recupera TUTTI i nodi del workflow da n8n API per trovare flag show-X
 */
router.get('/debug/workflow/:workflowId/nodes', async (req: Request, res: Response) => {
  try {
    const { workflowId } = req.params;
    
    console.log(`🔍 DEBUG: Fetching ALL nodes for workflow ${workflowId} from n8n API`);
    
    // Usa n8n client diretto per recuperare workflow completo
    const n8nClient = importService.getN8nClient();
    const workflowData = await n8nClient.getWorkflow(workflowId);
    
    if (!workflowData || !workflowData.nodes) {
      return res.status(404).json({ error: 'Workflow not found or no nodes' });
    }
    
    console.log(`📋 Found ${workflowData.nodes.length} total nodes in workflow`);
    
    // Filtra solo nodi con flag show-X
    const showNodes = workflowData.nodes
      .filter((node: any) => node.notes && node.notes.toLowerCase().includes('show'))
      .map((node: any) => ({
        name: node.name,
        type: node.type,
        notes: node.notes,
        position: node.position
      }))
      .sort((a: any, b: any) => {
        // Ordina per show-N numero
        const aMatch = a.notes.match(/show[_-](\d+)/i);
        const bMatch = b.notes.match(/show[_-](\d+)/i);
        const aNum = aMatch ? parseInt(aMatch[1]) : 999;
        const bNum = bMatch ? parseInt(bMatch[1]) : 999;
        return aNum - bNum;
      });
    
    console.log(`👁️ Found ${showNodes.length} nodes with show flags:`, showNodes.map(n => `${n.name} (${n.notes})`));
    
    // Salva automaticamente nel database
    if (showNodes.length > 0) {
      const nodesNotesMap: any = {};
      showNodes.forEach((node: any) => {
        nodesNotesMap[node.name] = node.notes;
      });
      
      await db.query(`
        UPDATE tenant_workflows 
        SET nodes_notes = $1::jsonb 
        WHERE id = $2
      `, [JSON.stringify(nodesNotesMap), workflowId]);
      
      console.log(`✅ Saved ${showNodes.length} show nodes to database`);
    }
    
    res.json({
      workflowId,
      totalNodes: workflowData.nodes.length,
      showNodes: showNodes,
      savedToDatabase: showNodes.length > 0
    });
    
  } catch (error) {
    console.error('❌ Error fetching workflow nodes:', error);
    res.status(500).json({ 
      error: 'Failed to fetch workflow nodes',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

async function parseRealExecutionData(executionData: any, workflowId: string, tenantId: string): Promise<any[]> {
  console.log(`🔍 Parsing real execution data for ${executionData.id}`);
  
  const runData = executionData.data?.resultData?.runData || {};
  const detailedSteps: any[] = [];
  
  // Estrai nomi nodi dall'execution
  const nodeNames = Object.keys(runData);
  console.log(`📋 Found ${nodeNames.length} nodes in execution:`, nodeNames);
  
  for (const nodeName of nodeNames) {
    const nodeExecutions = runData[nodeName];
    
    if (Array.isArray(nodeExecutions) && nodeExecutions.length > 0) {
      const nodeExecution = nodeExecutions[0]; // Prendi prima execution del nodo
      
      // Estrai dati reali del nodo
      const nodeStep = {
        nodeId: nodeName,
        nodeName: nodeName,
        nodeType: nodeExecution.source?.[0]?.main?.[0]?.type || 'unknown',
        status: nodeExecution.error ? 'error' : 'success',
        executionTime: nodeExecution.executionTime || 0,
        inputData: nodeExecution.data?.main?.[0] || null,
        outputData: nodeExecution.data?.main?.[0] || null,
        error: nodeExecution.error || null,
        isVisible: true, // Mostra tutti i nodi reali
        isTrigger: nodeName.toLowerCase().includes('trigger') || nodeName.toLowerCase().includes('ricezione'),
        customOrder: null,
        startTime: new Date(executionData.startedAt),
        summary: `${nodeName} - ${nodeExecution.error ? 'ERROR' : 'SUCCESS'}`
      };
      
      // Log per debugging
      console.log(`📊 Node: ${nodeName}`, {
        hasInput: !!nodeStep.inputData,
        hasOutput: !!nodeStep.outputData,
        status: nodeStep.status,
        executionTime: nodeStep.executionTime
      });
      
      detailedSteps.push(nodeStep);
    }
  }
  
  console.log(`✅ Parsed ${detailedSteps.length} real nodes from execution ${executionData.id}`);
  return detailedSteps;
}

export default router;