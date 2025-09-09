/**
 * Tenant-specific Statistics API
 * 
 * Endpoints per ottenere statistiche filtrate per singolo tenant
 */

import { Router, Request, Response, NextFunction } from 'express';
import { DatabaseConnection } from '../database/connection.js';

// Semplice middleware auth per development
const authMiddleware = (req: Request, res: Response, next: NextFunction) => {
  // Per ora passa sempre, in produzione verifica JWT
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

/**
 * @swagger
 * /api/tenant/{tenantId}/stats:
 *   get:
 *     summary: Statistiche per singolo tenant
 *     description: Ottieni statistiche complete per un tenant specifico
 *     tags: [Tenants]
 *     parameters:
 *       - in: path
 *         name: tenantId
 *         required: true
 *         schema:
 *           type: string
 *         description: ID del tenant
 *     responses:
 *       200:
 *         description: Tenant statistics
 */
router.get('/tenant/:tenantId/stats', authMiddleware, async (req: Request, res: Response) => {
  try {
    const { tenantId } = req.params;
    const user = (req as any).user;
    
    // Verifica che l'utente possa vedere questo tenant
    if (user.role !== 'admin' && user.tenantId !== tenantId) {
      return res.status(403).json({ error: 'Access denied to this tenant' });
    }
    
    // Stats workflows - SOLO QUELLI ATTIVI!
    const workflowStats = await db.getOne(`
      SELECT 
        COUNT(*) as total_workflows,
        COUNT(*) as active_workflows,
        COUNT(*) FILTER (WHERE has_webhook = true) as webhook_workflows,
        COUNT(*) FILTER (WHERE is_archived = false) as production_workflows
      FROM tenant_workflows
      WHERE tenant_id = $1 AND active = true
    `, [tenantId]);
    
    // Stats executions (ultimi 30 giorni)
    const executionStats = await db.getOne(`
      SELECT 
        COUNT(*) as total_executions,
        COUNT(*) FILTER (WHERE status = 'success') as successful_executions,
        COUNT(*) FILTER (WHERE status = 'error') as failed_executions,
        COUNT(*) FILTER (WHERE status = 'running') as running_executions,
        AVG(CASE WHEN duration_ms IS NOT NULL THEN duration_ms ELSE 0 END) as avg_duration_ms
      FROM tenant_executions
      WHERE tenant_id = $1
        AND started_at > NOW() - INTERVAL '30 days'
    `, [tenantId]);
    
    // Activity per ore (ultime 24 ore)
    const hourlyActivity = await db.getMany(`
      SELECT 
        DATE_TRUNC('hour', started_at) as hour,
        COUNT(*) as executions,
        COUNT(DISTINCT workflow_id) as unique_workflows
      FROM tenant_executions
      WHERE tenant_id = $1
        AND started_at > NOW() - INTERVAL '24 hours'
      GROUP BY DATE_TRUNC('hour', started_at)
      ORDER BY hour DESC
    `, [tenantId]);
    
    // Top workflows by executions
    const topWorkflows = await db.getMany(`
      SELECT 
        tw.name,
        tw.id,
        tw.active,
        COUNT(te.id) as execution_count,
        AVG(te.duration_ms) as avg_duration
      FROM tenant_workflows tw
      LEFT JOIN tenant_executions te ON tw.id = te.workflow_id
      WHERE tw.tenant_id = $1
        AND te.started_at > NOW() - INTERVAL '7 days'
      GROUP BY tw.id, tw.name, tw.active
      ORDER BY execution_count DESC
      LIMIT 5
    `, [tenantId]);
    
    // Success rate
    const successRate = executionStats.total_executions > 0
      ? ((executionStats.successful_executions / executionStats.total_executions) * 100).toFixed(1)
      : '100';
    
    res.json({
      tenantId,
      timestamp: new Date().toISOString(),
      workflows: {
        total: parseInt(workflowStats.total_workflows),
        active: parseInt(workflowStats.active_workflows),
        webhook: parseInt(workflowStats.webhook_workflows),
        production: parseInt(workflowStats.production_workflows),
      },
      executions: {
        total: parseInt(executionStats.total_executions),
        successful: parseInt(executionStats.successful_executions),
        failed: parseInt(executionStats.failed_executions),
        running: parseInt(executionStats.running_executions),
        avgDuration: Math.round(executionStats.avg_duration_ms || 0),
        successRate: parseFloat(successRate),
      },
      activity: {
        hourly: hourlyActivity,
        topWorkflows,
      },
    });
  } catch (error) {
    console.error('Error getting tenant stats:', error);
    res.status(500).json({ error: 'Failed to get tenant statistics' });
  }
});

/**
 * @swagger
 * /api/tenant/{tenantId}/workflows:
 *   get:
 *     summary: Lista workflows per tenant
 *     description: Ottieni lista workflows di un tenant specifico
 *     tags: [Tenants]
 */
router.get('/tenant/:tenantId/workflows', authMiddleware, async (req: Request, res: Response) => {
  try {
    const { tenantId } = req.params;
    const user = (req as any).user;
    
    // Verifica permessi
    if (user.role !== 'admin' && user.tenantId !== tenantId) {
      return res.status(403).json({ error: 'Access denied to this tenant' });
    }
    
    const workflows = await db.getMany(`
      SELECT 
        id,
        name,
        active,
        has_webhook,
        is_archived,
        created_at,
        updated_at,
        node_count,
        (SELECT COUNT(*) FROM tenant_executions WHERE workflow_id = tw.id) as execution_count,
        (SELECT MAX(started_at) FROM tenant_executions WHERE workflow_id = tw.id) as last_execution
      FROM tenant_workflows tw
      WHERE tenant_id = $1
      ORDER BY 
        CASE 
          WHEN active = true THEN 1
          WHEN is_archived = true THEN 3
          ELSE 2
        END,
        name ASC
    `, [tenantId]);
    
    res.json({
      tenantId,
      workflows,
      total: workflows.length,
    });
  } catch (error) {
    console.error('Error getting tenant workflows:', error);
    res.status(500).json({ error: 'Failed to get workflows' });
  }
});

/**
 * @swagger
 * /api/tenant/{tenantId}/executions:
 *   get:
 *     summary: Lista esecuzioni per tenant
 *     description: Ottieni lista esecuzioni di un tenant specifico
 *     tags: [Tenants]
 */
router.get('/tenant/:tenantId/executions', authMiddleware, async (req: Request, res: Response) => {
  try {
    const { tenantId } = req.params;
    const { limit = 20, offset = 0 } = req.query;
    const user = (req as any).user;
    
    // Verifica permessi
    if (user.role !== 'admin' && user.tenantId !== tenantId) {
      return res.status(403).json({ error: 'Access denied to this tenant' });
    }
    
    const executions = await db.getMany(`
      SELECT 
        te.id,
        te.workflow_id,
        tw.name as workflow_name,
        CASE 
          WHEN te.stopped_at IS NULL THEN 'running'
          WHEN te.has_error = true THEN 'error' 
          WHEN te.stopped_at IS NOT NULL THEN 'success'
          ELSE 'waiting'
        END as status,
        te.mode,
        te.started_at,
        te.stopped_at,
        te.duration_ms,
        te.has_error
      FROM tenant_executions te
      JOIN tenant_workflows tw ON te.workflow_id = tw.id
      WHERE te.tenant_id = $1
      ORDER BY te.started_at DESC
      LIMIT $2 OFFSET $3
    `, [tenantId, limit, offset]);
    
    const total = await db.getOne(
      'SELECT COUNT(*) as count FROM tenant_executions WHERE tenant_id = $1',
      [tenantId]
    );
    
    res.json({
      tenantId,
      executions,
      pagination: {
        limit: Number(limit),
        offset: Number(offset),
        total: parseInt(total.count),
      },
    });
  } catch (error) {
    console.error('Error getting tenant executions:', error);
    res.status(500).json({ error: 'Failed to get executions' });
  }
});

/**
 * @swagger
 * /api/tenant/{tenantId}/workflows/{workflowId}/details:
 *   get:
 *     summary: Dettagli completi workflow
 *     description: Ottieni tutti i dettagli di un workflow specifico con analisi nodi e performance
 *     tags: [Workflows]
 */
router.get('/tenant/:tenantId/workflows/:workflowId/details', authMiddleware, async (req: Request, res: Response) => {
  try {
    const { tenantId, workflowId } = req.params;
    const user = (req as any).user;
    
    // Verifica permessi
    if (user.role !== 'admin' && user.tenantId !== tenantId) {
      return res.status(403).json({ error: 'Access denied to this tenant' });
    }
    
    // Ottieni dettagli workflow
    const workflow = await db.getOne(`
      SELECT 
        id,
        name,
        active,
        has_webhook,
        is_archived,
        created_at,
        updated_at,
        node_count,
        raw_data,
        raw_data->'nodes' as nodes,
        raw_data->'connections' as connections,
        raw_data->'settings' as settings,
        raw_data->'pinData' as pinned_data,
        (SELECT COUNT(*) FROM tenant_executions WHERE workflow_id = tw.id) as execution_count,
        (SELECT MAX(started_at) FROM tenant_executions WHERE workflow_id = tw.id) as last_execution
      FROM tenant_workflows tw
      WHERE id = $1 AND tenant_id = $2
    `, [workflowId, tenantId]);
    
    if (!workflow) {
      return res.status(404).json({ error: 'Workflow not found' });
    }
    
    // Analisi nodi
    let nodeAnalysis = {
      totalNodes: workflow.node_count || 0,
      nodesByType: {} as Record<string, number>,
      triggers: [] as any[],
      outputs: [] as any[],
      aiAgents: [] as any[],
      tools: [] as any[],
      subWorkflows: [] as any[],
      connections: [] as any[],
      stickyNotes: [] as any[],
      description: null as string | null
    };
    
    if (workflow.nodes) {
      // nodes è già un oggetto JSON dal database PostgreSQL
      const nodes = Array.isArray(workflow.nodes) ? workflow.nodes : [];
      
      // Count nodes by type - simplified categories
      let simplifiedCategories = {
        'Triggers': 0,
        'Data Processing': 0,
        'External Services': 0,
        'Output/Response': 0,
        'AI/ML': 0,
        'Other': 0
      };
      
      nodes.forEach((node: any) => {
        const nodeType = node.type || 'unknown';
        const nodeName = node.name || 'Unnamed';
        const nodeParameters = node.parameters || {};
        
        // Capture Sticky Notes (documentation nodes)
        if (nodeType === 'n8n-nodes-base.stickyNote') {
          nodeAnalysis.stickyNotes.push({
            content: nodeParameters.content || '',
            height: nodeParameters.height,
            width: nodeParameters.width,
            color: nodeParameters.color
          });
        }
        // Identify AI Agents specifically
        else
        if (nodeType.includes('.agent') || 
            nodeType.includes('aiAgent') ||
            nodeName.toLowerCase().includes('agent') ||
            nodeName.toLowerCase().includes('assistente')) {
          
          // Estrai informazioni dettagliate sull'agente
          const agentInfo: any = {
            name: nodeName,
            type: nodeType.split('.').pop() || nodeType,
            model: nodeParameters.model || nodeParameters.modelId || 'unknown',
            temperature: nodeParameters.temperature,
            systemPrompt: nodeParameters.systemPrompt ? 'Configured' : 'Default',
            tools: []
          };
          
          // Cerca i tools connessi all'agente nelle connections
          if (workflow.connections && workflow.connections[nodeName]) {
            const agentConnections = workflow.connections[nodeName];
            if (agentConnections.ai_tool) {
              agentInfo.toolCount = agentConnections.ai_tool.length;
            }
          }
          
          nodeAnalysis.aiAgents.push(agentInfo);
          simplifiedCategories['AI/ML']++;
        }
        // Identify AI Tools (used by agents) - INCLUDING VECTOR STORES
        else if (nodeType.includes('toolWorkflow') || 
                 (nodeType.includes('tool') && nodeType.includes('langchain')) ||
                 nodeType.includes('vectorStore') ||
                 nodeType.includes('embedding') ||
                 nodeType.includes('retriever')) {
          nodeAnalysis.tools.push({
            name: nodeName,
            type: nodeType.split('.').pop() || nodeType,
            description: nodeParameters.description || nodeParameters.toolDescription || nodeParameters.name || nodeName
          });
          simplifiedCategories['AI/ML']++;
        }
        // Identify Sub-Workflows
        else if (nodeType.includes('executeWorkflow') || 
                 nodeType.includes('subworkflow')) {
          nodeAnalysis.subWorkflows.push({
            name: nodeName,
            workflowId: nodeParameters.workflowId || nodeParameters.id || 'unknown',
            mode: nodeParameters.mode || 'default'
          });
          simplifiedCategories['External Services']++;
        }
        // Identify triggers (input)
        else if (nodeType.toLowerCase().includes('trigger') || 
            nodeType.toLowerCase().includes('webhook') ||
            nodeType === 'n8n-nodes-base.formTrigger' ||
            nodeType === 'n8n-nodes-base.scheduleTrigger') {
          nodeAnalysis.triggers.push({
            name: nodeName,
            type: nodeType.split('.').pop() || nodeType,
            triggerType: nodeType.includes('webhook') ? 'webhook' : 
                  nodeType.includes('form') ? 'form' : 
                  nodeType.includes('schedule') ? 'schedule' : 
                  nodeType.includes('email') ? 'email' : 'manual'
          });
          simplifiedCategories['Triggers']++;
        } 
        // Identify outputs (where data goes)
        else if (nodeType.toLowerCase().includes('email') || 
                 nodeType.toLowerCase().includes('outlook') ||
                 nodeType.toLowerCase().includes('gmail') ||
                 nodeType.toLowerCase().includes('slack') ||
                 nodeType.toLowerCase().includes('telegram') ||
                 nodeType.toLowerCase().includes('response') ||
                 nodeType.toLowerCase().includes('webhook.respond') ||
                 nodeName.toLowerCase().includes('respond') ||
                 nodeName.toLowerCase().includes('reply') ||
                 nodeName.toLowerCase().includes('send')) {
          nodeAnalysis.outputs.push({
            name: nodeName,
            type: nodeType.split('.').pop() || nodeType,
            outputType: nodeType.includes('email') || nodeType.includes('outlook') ? 'email' :
                  nodeType.includes('slack') ? 'slack' :
                  nodeType.includes('telegram') ? 'telegram' :
                  nodeType.includes('response') ? 'response' : 'send'
          });
          simplifiedCategories['Output/Response']++;
        }
        // Other AI/ML nodes (language models, etc - excluding tools)
        else if (nodeType.includes('langchain') || 
                 nodeType.includes('openai') || 
                 nodeType.includes('ChatModel') ||
                 nodeType.includes('LanguageModel')) {
          simplifiedCategories['AI/ML']++;
        }
        // External services (excluding vector stores which are tools)
        else if (nodeType.includes('http') || 
                 nodeType.includes('api') ||
                 nodeType.includes('postgres') ||
                 nodeType.includes('mysql') ||
                 nodeType.includes('supabase')) {
          simplifiedCategories['External Services']++;
        }
        // Data processing
        else if (nodeType.includes('code') || 
                 nodeType.includes('merge') ||
                 nodeType.includes('split') ||
                 nodeType.includes('filter') ||
                 nodeType.includes('format')) {
          simplifiedCategories['Data Processing']++;
        }
        // Other
        else {
          simplifiedCategories['Other']++;
        }
      });
      
      // Analizza le connessioni per collegare tools agli agents
      if (workflow.connections) {
        nodeAnalysis.aiAgents.forEach((agent: any) => {
          const agentConnections = workflow.connections[agent.name];
          if (agentConnections) {
            // Trova i tools connessi a questo agent
            agent.connectedTools = [];
            nodes.forEach((node: any) => {
              if (node.type && node.type.includes('tool')) {
                // Verifica se questo tool è connesso all'agent
                const toolConnections = workflow.connections[node.name];
                if (toolConnections && toolConnections.ai_tool) {
                  toolConnections.ai_tool.forEach((connections: any) => {
                    connections.forEach((conn: any) => {
                      if (conn.node === agent.name) {
                        agent.connectedTools.push(node.name);
                      }
                    });
                  });
                }
              }
            });
          }
        });
      }
      
      // Remove empty categories
      nodeAnalysis.nodesByType = Object.fromEntries(
        Object.entries(simplifiedCategories).filter(([_, count]) => count > 0)
      );
      
      // Parse connections if available
      if (workflow.connections) {
        const connections = workflow.connections;
        nodeAnalysis.connections = connections && Object.keys(connections).length > 0 ? connections : [];
      }
    }
    
    // Extract workflow description from settings or generate one
    if (workflow.settings && typeof workflow.settings === 'object') {
      nodeAnalysis.description = workflow.settings.description || null;
    }
    
    // If no description, try to generate one from components
    if (!nodeAnalysis.description && (nodeAnalysis.triggers.length > 0 || nodeAnalysis.aiAgents.length > 0)) {
      let autoDescription = 'This workflow ';
      
      // Describe triggers
      if (nodeAnalysis.triggers.length > 0) {
        const triggerTypes = [...new Set(nodeAnalysis.triggers.map((t: any) => t.triggerType))];
        autoDescription += `starts from ${triggerTypes.join(' or ')} triggers`;
      }
      
      // Describe AI agents
      if (nodeAnalysis.aiAgents.length > 0) {
        autoDescription += nodeAnalysis.triggers.length > 0 ? ', uses ' : 'uses ';
        autoDescription += `${nodeAnalysis.aiAgents.length} AI agent${nodeAnalysis.aiAgents.length > 1 ? 's' : ''}`;
        if (nodeAnalysis.tools.length > 0) {
          autoDescription += ` with ${nodeAnalysis.tools.length} tool${nodeAnalysis.tools.length > 1 ? 's' : ''}`;
        }
      }
      
      // Describe outputs
      if (nodeAnalysis.outputs.length > 0) {
        const outputTypes = [...new Set(nodeAnalysis.outputs.map((o: any) => o.outputType))];
        autoDescription += `, and sends responses via ${outputTypes.join(', ')}`;
      }
      
      autoDescription += '.';
      nodeAnalysis.description = autoDescription;
    }
    
    // Stats esecuzioni
    const executionStats = await db.getOne(`
      SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status = 'success') as successful,
        COUNT(*) FILTER (WHERE status = 'error') as failed,
        AVG(duration_ms) as average_duration,
        MIN(duration_ms) as min_duration,
        MAX(duration_ms) as max_duration
      FROM tenant_executions
      WHERE workflow_id = $1 AND tenant_id = $2
    `, [workflowId, tenantId]);
    
    // Esecuzioni recenti
    const recentExecutions = await db.getMany(`
      SELECT 
        id,
        status,
        mode,
        started_at,
        stopped_at,
        duration_ms,
        has_error,
        CASE 
          WHEN has_error = true THEN raw_data->>'error' 
          ELSE NULL 
        END as error_message
      FROM tenant_executions
      WHERE workflow_id = $1 AND tenant_id = $2
      ORDER BY started_at DESC
      LIMIT 20
    `, [workflowId, tenantId]);
    
    // Trend giornaliero (ultimi 7 giorni)
    const dailyTrend = await db.getMany(`
      SELECT 
        DATE(started_at) as date,
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status = 'success') as successful,
        COUNT(*) FILTER (WHERE status = 'error') as failed
      FROM tenant_executions
      WHERE workflow_id = $1 
        AND tenant_id = $2
        AND started_at > NOW() - INTERVAL '7 days'
      GROUP BY DATE(started_at)
      ORDER BY date DESC
    `, [workflowId, tenantId]);
    
    // Errori comuni
    const commonErrors = await db.getMany(`
      SELECT 
        raw_data->>'error' as error_message,
        COUNT(*) as count,
        MAX(started_at) as last_occurred
      FROM tenant_executions
      WHERE workflow_id = $1 
        AND tenant_id = $2 
        AND has_error = true
        AND raw_data->>'error' IS NOT NULL
      GROUP BY raw_data->>'error'
      ORDER BY count DESC
      LIMIT 5
    `, [workflowId, tenantId]);
    
    res.json({
      workflow: {
        ...workflow,
        nodes: undefined, // Remove raw JSON
        connections: undefined, // Remove raw JSON
        settings: undefined, // Remove raw JSON
        pinned_data: undefined, // Remove raw JSON
        raw_data: undefined // Remove raw JSON
      },
      nodeAnalysis,
      executionStats: {
        total: parseInt(executionStats.total || '0'),
        successful: parseInt(executionStats.successful || '0'),
        failed: parseInt(executionStats.failed || '0'),
        averageDuration: Math.round(executionStats.average_duration || 0),
        lastExecution: workflow.last_execution,
        recentExecutions,
        dailyTrend,
      },
      performance: {
        minExecutionTime: parseInt(executionStats.min_duration || '0'),
        avgExecutionTime: Math.round(executionStats.average_duration || 0),
        maxExecutionTime: parseInt(executionStats.max_duration || '0'),
        errorRate: executionStats.total > 0 
          ? ((parseInt(executionStats.failed) / parseInt(executionStats.total)) * 100).toFixed(1)
          : '0',
        commonErrors: commonErrors.map(err => ({
          message: err.error_message,
          count: parseInt(err.count),
          lastOccurred: err.last_occurred
        }))
      }
    });
  } catch (error) {
    console.error('Error getting workflow details:', error);
    res.status(500).json({ error: 'Failed to get workflow details' });
  }
});

/**
 * @swagger
 * /api/tenant/{tenantId}/dashboard:
 *   get:
 *     summary: Dashboard data per tenant
 *     description: Tutti i dati necessari per la dashboard di un tenant
 *     tags: [Tenants]
 */
router.get('/tenant/:tenantId/dashboard', authMiddleware, async (req: Request, res: Response) => {
  try {
    const { tenantId } = req.params;
    const user = (req as any).user;
    
    // Per utenti non admin, usa sempre il loro tenant
    const effectiveTenantId = user.role === 'admin' ? tenantId : user.tenantId || 'default_tenant';
    
    // Ottieni info tenant
    const tenant = await db.getOne(
      'SELECT * FROM tenants WHERE id = $1',
      [effectiveTenantId]
    );
    
    if (!tenant) {
      return res.status(404).json({ error: 'Tenant not found' });
    }
    
    // Raccogli tutte le stats in parallelo
    const [workflowStats, executionStats, recentExecutions, statusDistribution] = await Promise.all([
      // Workflow stats - SOLO ATTIVI!
      db.getOne(`
        SELECT 
          COUNT(*) as total,
          COUNT(*) as active,
          COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as new_this_week
        FROM tenant_workflows
        WHERE tenant_id = $1 AND active = true
      `, [effectiveTenantId]),
      
      // Execution stats
      db.getOne(`
        SELECT 
          COUNT(*) as total,
          COUNT(*) FILTER (WHERE status = 'success') as successful,
          COUNT(*) FILTER (WHERE status = 'error') as failed,
          COUNT(*) FILTER (WHERE started_at > NOW() - INTERVAL '24 hours') as last_24h
        FROM tenant_executions
        WHERE tenant_id = $1
      `, [effectiveTenantId]),
      
      // Recent executions - SOLO DA WORKFLOW ATTIVI!
      db.getMany(`
        SELECT 
          te.*, 
          tw.name as workflow_name
        FROM tenant_executions te
        JOIN tenant_workflows tw ON te.workflow_id = tw.id
        WHERE te.tenant_id = $1 AND tw.active = true
        ORDER BY te.started_at DESC
        LIMIT 10
      `, [effectiveTenantId]),
      
      // Status distribution
      db.getMany(`
        SELECT 
          status,
          COUNT(*) as count
        FROM tenant_executions
        WHERE tenant_id = $1
          AND started_at > NOW() - INTERVAL '7 days'
        GROUP BY status
      `, [effectiveTenantId]),
    ]);
    
    // Calcola metriche
    const successRate = executionStats.total > 0
      ? ((executionStats.successful / executionStats.total) * 100).toFixed(1)
      : '100';
    
    res.json({
      tenant: {
        id: tenant.id,
        name: tenant.name,
      },
      stats: {
        workflows: {
          total: parseInt(workflowStats.total),
          active: parseInt(workflowStats.active),
          newThisWeek: parseInt(workflowStats.new_this_week),
        },
        executions: {
          total: parseInt(executionStats.total),
          successful: parseInt(executionStats.successful),
          failed: parseInt(executionStats.failed),
          last24h: parseInt(executionStats.last_24h),
          successRate: parseFloat(successRate),
        },
        statusDistribution: statusDistribution.reduce((acc: any, item: any) => {
          acc[item.status] = parseInt(item.count);
          return acc;
        }, {}),
      },
      recentActivity: recentExecutions,
    });
  } catch (error) {
    console.error('Error getting tenant dashboard:', error);
    res.status(500).json({ error: 'Failed to get dashboard data' });
  }
});

export default router;