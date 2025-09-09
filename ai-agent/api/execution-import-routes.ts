/**
 * Execution Import Routes
 * 
 * API routes per importazione execution data completi da n8n API
 * con includeData=true per AI Agent Transparency
 */

import { Router, Request, Response, NextFunction } from 'express';
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

/**
 * POST /api/execution-import/active-workflows
 * 
 * Importa execution data completi per tutti i workflow attivi
 */
router.post('/execution-import/active-workflows', authMiddleware, async (req: Request, res: Response) => {
  try {
    const { limit = 50 } = req.body;
    console.log(`🔄 Starting import of execution data for active workflows (limit: ${limit})`);
    
    const importService = new ExecutionImportService();
    const enrichedExecutions = await importService.importActiveWorkflowExecutions(limit);
    
    res.json({
      success: true,
      message: `Successfully imported ${enrichedExecutions.length} executions`,
      data: {
        totalImported: enrichedExecutions.length,
        executions: enrichedExecutions.map(e => ({
          executionId: e.executionId,
          workflowId: e.workflowId,
          totalNodes: e.totalNodes,
          successfulNodes: e.successfulNodes,
          failedNodes: e.failedNodes,
          businessContext: Object.keys(e.businessContext).length
        }))
      },
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('❌ Error importing active workflow executions:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to import execution data',
      message: (error as any).message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /api/execution-import/workflow/:workflowId
 * 
 * Importa execution data completi per un workflow specifico
 */
router.post('/execution-import/workflow/:workflowId', authMiddleware, async (req: Request, res: Response) => {
  try {
    const { workflowId } = req.params;
    const { limit = 20 } = req.body;
    
    console.log(`🔄 Starting import for workflow: ${workflowId} (limit: ${limit})`);
    
    const importService = new ExecutionImportService();
    const enrichedExecutions = await importService.importWorkflowExecutions(workflowId, limit);
    
    res.json({
      success: true,
      message: `Successfully imported ${enrichedExecutions.length} executions for workflow ${workflowId}`,
      data: {
        workflowId,
        totalImported: enrichedExecutions.length,
        executions: enrichedExecutions.map(e => ({
          executionId: e.executionId,
          totalNodes: e.totalNodes,
          successfulNodes: e.successfulNodes,
          failedNodes: e.failedNodes,
          businessContext: Object.keys(e.businessContext).length
        }))
      },
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error(`❌ Error importing executions for workflow ${req.params.workflowId}:`, error);
    res.status(500).json({
      success: false,
      error: 'Failed to import workflow executions',
      message: (error as any).message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/execution-import/status
 * 
 * Stato dell'import e statistiche execution data arricchiti
 */
router.get('/execution-import/status', authMiddleware, async (req: Request, res: Response) => {
  try {
    const importService = new ExecutionImportService();
    const { tenantId } = (req as any).user;
    
    // Ottieni statistiche execution data arricchiti
    const enrichedExecutions = await importService.getEnrichedExecutions(tenantId, 100);
    
    const stats = {
      totalEnrichedExecutions: enrichedExecutions.length,
      executions: enrichedExecutions.map(e => ({
        executionId: e.id,
        workflowId: e.workflow_id,
        workflowName: e.workflow_name,
        status: e.status,
        startedAt: e.started_at,
        duration: e.duration_ms,
        totalNodes: e.total_nodes,
        successfulNodes: e.successful_nodes,
        failedNodes: e.failed_nodes,
        hasBusinessContext: !!e.business_context && Object.keys(e.business_context).length > 0
      }))
    };
    
    res.json({
      success: true,
      data: stats,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('❌ Error getting import status:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get import status',
      message: (error as any).message,
      timestamp: new Date().toISOString()
    });
  }
});

export default router;