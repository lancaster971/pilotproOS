/**
 * Execution Enrichment Routes
 * 
 * API routes per arricchimento execution data esistenti nel database
 * per AI Agent Transparency (no external API calls)
 */

import { Router, Request, Response, NextFunction } from 'express';
import { ExecutionEnrichmentService } from './execution-enrichment-service.js';

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
 * POST /api/execution-enrichment/enrich-database
 * 
 * Arricchisce execution data esistenti nel database usando raw_data
 */
router.post('/execution-enrichment/enrich-database', authMiddleware, async (req: Request, res: Response) => {
  try {
    const { limit = 50 } = req.body;
    console.log(`🔄 Starting enrichment of database execution data (limit: ${limit})`);
    
    const enrichmentService = new ExecutionEnrichmentService();
    const enrichedExecutions = await enrichmentService.enrichActiveWorkflowExecutions(limit);
    
    res.json({
      success: true,
      message: `Successfully enriched ${enrichedExecutions.length} executions from database`,
      data: {
        totalEnriched: enrichedExecutions.length,
        executions: enrichedExecutions.map(e => ({
          executionId: e.executionId,
          workflowId: e.workflowId,
          totalNodes: e.totalNodes,
          successfulNodes: e.successfulNodes,
          failedNodes: e.failedNodes,
          businessContextItems: Object.keys(e.businessContext).length,
          extractedEmails: e.businessContext.extractedEmails?.length || 0,
          extractedIds: e.businessContext.extractedIds?.length || 0,
          processedAmounts: e.businessContext.processedAmounts?.length || 0
        }))
      },
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('❌ Error enriching database execution data:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to enrich execution data from database',
      message: (error as any).message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/execution-enrichment/stats/:tenantId
 * 
 * Statistiche enrichment per tenant
 */
router.get('/execution-enrichment/stats/:tenantId', authMiddleware, async (req: Request, res: Response) => {
  try {
    const { tenantId } = req.params;
    const user = (req as any).user;
    
    // Verifica permessi
    if (user.role !== 'admin' && user.tenantId !== tenantId) {
      return res.status(403).json({ error: 'Access denied to this tenant' });
    }
    
    const enrichmentService = new ExecutionEnrichmentService();
    const stats = await enrichmentService.getEnrichmentStats(tenantId);
    
    res.json({
      success: true,
      tenantId,
      data: stats,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('❌ Error getting enrichment stats:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get enrichment stats',
      message: (error as any).message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/execution-enrichment/enriched/:tenantId
 * 
 * Lista execution data arricchiti per tenant
 */
router.get('/execution-enrichment/enriched/:tenantId', authMiddleware, async (req: Request, res: Response) => {
  try {
    const { tenantId } = req.params;
    const { limit = 20 } = req.query;
    const user = (req as any).user;
    
    // Verifica permessi
    if (user.role !== 'admin' && user.tenantId !== tenantId) {
      return res.status(403).json({ error: 'Access denied to this tenant' });
    }
    
    const enrichmentService = new ExecutionEnrichmentService();
    const enrichedExecutions = await enrichmentService.getEnrichedExecutions(tenantId, Number(limit));
    
    res.json({
      success: true,
      tenantId,
      data: {
        totalFound: enrichedExecutions.length,
        executions: enrichedExecutions
      },
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('❌ Error getting enriched executions:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get enriched executions',
      message: (error as any).message,
      timestamp: new Date().toISOString()
    });
  }
});

export default router;