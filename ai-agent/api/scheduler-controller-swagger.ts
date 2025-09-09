/**
 * Scheduler Controller with Swagger Documentation
 * 
 * REST API endpoints per controllo multi-tenant scheduler
 */

import express, { Request, Response } from 'express';
import { getMultiTenantScheduler } from '../backend/multi-tenant-scheduler.js';
import { createMultiTenantApiClient } from './multi-tenant-client.js';
import { DatabaseConnection } from '../database/connection.js';
import { getAuthService, AuthUser } from '../auth/jwt-auth.js';

const router = express.Router();
const scheduler = getMultiTenantScheduler();
const client = createMultiTenantApiClient();
const db = DatabaseConnection.getInstance();
const authService = getAuthService();

/**
 * @swagger
 * /api/scheduler/status:
 *   get:
 *     summary: Status scheduler
 *     description: Ottieni stato completo dello scheduler e statistiche sistema
 *     tags: [Scheduler]
 *     responses:
 *       200:
 *         description: Scheduler status
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/SchedulerStatus'
 *       500:
 *         description: Internal server error
 */
router.get('/scheduler/status', async (req: Request, res: Response) => {
  try {
    const stats = scheduler.getStats();
    const health = await scheduler.healthCheck();
    
    res.json({
      timestamp: new Date().toISOString(),
      scheduler: {
        isRunning: stats.isRunning,
        scheduledTasks: stats.scheduledTasks,
        config: stats.config
      },
      stats: stats.stats,
      health: health,
      system: {
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        version: process.version
      }
    });
    
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get scheduler status',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * @swagger
 * /api/scheduler/start:
 *   post:
 *     summary: Avvia scheduler
 *     description: Avvia lo scheduler per sincronizzazione automatica (richiede permesso scheduler:control)
 *     tags: [Scheduler]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Scheduler started successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 timestamp:
 *                   type: string
 *                   format: date-time
 *                 status:
 *                   type: object
 *       400:
 *         description: Scheduler already running
 *       401:
 *         description: Unauthorized
 *       403:
 *         description: Forbidden - insufficient permissions
 */
router.post('/scheduler/start', 
  authService.authenticateToken(),
  authService.requirePermission('scheduler:control'),
  async (req: Request, res: Response) => {
  try {
    const stats = scheduler.getStats();
    
    if (stats.isRunning) {
      return res.status(400).json({
        error: 'Scheduler already running',
        message: 'Use /restart to restart the scheduler'
      });
    }
    
    await scheduler.start();
    
    res.json({
      message: 'Scheduler started successfully',
      timestamp: new Date().toISOString(),
      status: scheduler.getStats()
    });
    
  } catch (error) {
    res.status(500).json({
      error: 'Failed to start scheduler',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * @swagger
 * /api/scheduler/stop:
 *   post:
 *     summary: Ferma scheduler
 *     description: Ferma lo scheduler (richiede permesso scheduler:control)
 *     tags: [Scheduler]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Scheduler stopped successfully
 *       400:
 *         description: Scheduler not running
 *       401:
 *         description: Unauthorized
 *       403:
 *         description: Forbidden - insufficient permissions
 */
router.post('/scheduler/stop', 
  authService.authenticateToken(),
  authService.requirePermission('scheduler:control'),
  async (req: Request, res: Response) => {
  try {
    const stats = scheduler.getStats();
    
    if (!stats.isRunning) {
      return res.status(400).json({
        error: 'Scheduler not running',
        message: 'Scheduler is already stopped'
      });
    }
    
    await scheduler.stop();
    
    res.json({
      message: 'Scheduler stopped successfully',
      timestamp: new Date().toISOString(),
      status: scheduler.getStats()
    });
    
  } catch (error) {
    res.status(500).json({
      error: 'Failed to stop scheduler',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * @swagger
 * /api/scheduler/restart:
 *   post:
 *     summary: Riavvia scheduler
 *     description: Riavvia lo scheduler fermandolo e riavviandolo
 *     tags: [Scheduler]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Scheduler restarted successfully
 *       401:
 *         description: Unauthorized
 *       500:
 *         description: Failed to restart scheduler
 */
router.post('/scheduler/restart', async (req: Request, res: Response) => {
  try {
    const stats = scheduler.getStats();
    
    if (stats.isRunning) {
      await scheduler.stop();
    }
    
    await scheduler.start();
    
    res.json({
      message: 'Scheduler restarted successfully',
      timestamp: new Date().toISOString(),
      status: scheduler.getStats()
    });
    
  } catch (error) {
    res.status(500).json({
      error: 'Failed to restart scheduler',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * @swagger
 * /api/scheduler/sync:
 *   post:
 *     summary: Sincronizzazione manuale
 *     description: Esegui sincronizzazione manuale per uno o tutti i tenant
 *     tags: [Scheduler]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               tenantId:
 *                 type: string
 *                 description: ID tenant specifico (vuoto per tutti)
 *     responses:
 *       200:
 *         description: Sync completed
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 timestamp:
 *                   type: string
 *                 result:
 *                   type: object
 *       401:
 *         description: Unauthorized
 *       500:
 *         description: Sync failed
 */
router.post('/scheduler/sync', async (req: Request, res: Response) => {
  try {
    const { tenantId } = req.body;
    
    if (tenantId) {
      // Sync singolo tenant
      const result = await client.syncTenantData(tenantId);
      
      res.json({
        message: `Sync completed for tenant ${tenantId}`,
        timestamp: new Date().toISOString(),
        result: {
          tenantId,
          workflowsSynced: result.workflowsSynced,
          executionsSynced: result.executionsSynced,
          errors: result.errors
        }
      });
    } else {
      // Sync tutti i tenant
      const result = await scheduler.forceSyncAllTenants();
      
      res.json({
        message: 'Multi-tenant sync completed',
        timestamp: new Date().toISOString(),
        result: {
          totalTenants: result.totalTenants,
          successfulTenants: result.successfulTenants,
          failedTenants: result.failedTenants,
          totalWorkflowsSynced: result.totalWorkflowsSynced,
          totalExecutionsSynced: result.totalExecutionsSynced,
          duration_ms: result.duration_ms,
          errors: result.errors
        }
      });
    }
    
  } catch (error) {
    res.status(500).json({
      error: 'Sync failed',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * @swagger
 * /api/tenants:
 *   get:
 *     summary: Lista tenant
 *     description: Ottieni lista di tutti i tenant con statistiche
 *     tags: [Tenants]
 *     responses:
 *       200:
 *         description: Tenants list
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 timestamp:
 *                   type: string
 *                 tenants:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/Tenant'
 *                 total:
 *                   type: integer
 *       500:
 *         description: Failed to get tenants
 */
router.get('/tenants', async (req: Request, res: Response) => {
  try {
    const tenants = await db.getMany(`
      SELECT 
        id, name, n8n_api_url, n8n_version,
        sync_enabled, created_at, updated_at, last_sync_at
      FROM tenants 
      ORDER BY name
    `);
    
    // Aggiungi statistiche per ogni tenant
    const tenantsWithStats = await Promise.all(
      tenants.map(async (tenant) => {
        const workflowsCount = await db.getOne(
          'SELECT COUNT(*) as count FROM tenant_workflows WHERE tenant_id = $1',
          [tenant.id]
        );
        
        const executionsCount = await db.getOne(
          'SELECT COUNT(*) as count FROM tenant_executions WHERE tenant_id = $1',
          [tenant.id]
        );
        
        return {
          ...tenant,
          stats: {
            workflows: parseInt(workflowsCount.count),
            executions: parseInt(executionsCount.count)
          }
        };
      })
    );
    
    res.json({
      timestamp: new Date().toISOString(),
      tenants: tenantsWithStats,
      total: tenantsWithStats.length
    });
    
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get tenants',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * @swagger
 * /api/tenants:
 *   post:
 *     summary: Registra tenant
 *     description: Registra un nuovo tenant nel sistema
 *     tags: [Tenants]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - id
 *               - name
 *               - n8n_api_url
 *             properties:
 *               id:
 *                 type: string
 *               name:
 *                 type: string
 *               n8n_api_url:
 *                 type: string
 *                 format: uri
 *               n8n_version:
 *                 type: string
 *     responses:
 *       201:
 *         description: Tenant registered successfully
 *       400:
 *         description: Missing required fields
 *       401:
 *         description: Unauthorized
 *       500:
 *         description: Failed to register tenant
 */
router.post('/tenants', async (req: Request, res: Response) => {
  try {
    const { id, name, n8n_api_url, n8n_version } = req.body;
    
    // Validazione input
    if (!id || !name || !n8n_api_url) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'id, name, and n8n_api_url are required'
      });
    }
    
    // Registra tenant direttamente nel database
    await db.query(`
      INSERT INTO tenants (id, name, n8n_api_url, n8n_version, sync_enabled, created_at)
      VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
    `, [id, name, n8n_api_url, n8n_version || 'unknown', true]);
    
    res.status(201).json({
      message: 'Tenant registered successfully',
      timestamp: new Date().toISOString(),
      tenant: { id, name, n8n_api_url, n8n_version }
    });
    
  } catch (error) {
    res.status(500).json({
      error: 'Failed to register tenant',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * @swagger
 * /api/tenants/{id}/sync:
 *   put:
 *     summary: Toggle sync tenant
 *     description: Abilita o disabilita la sincronizzazione per un tenant
 *     tags: [Tenants]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: Tenant ID
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - enabled
 *             properties:
 *               enabled:
 *                 type: boolean
 *     responses:
 *       200:
 *         description: Sync status updated
 *       400:
 *         description: Invalid input
 *       401:
 *         description: Unauthorized
 *       500:
 *         description: Failed to update tenant
 */
router.put('/tenants/:id/sync', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const { enabled } = req.body;
    
    if (typeof enabled !== 'boolean') {
      return res.status(400).json({
        error: 'Invalid input',
        message: 'enabled must be a boolean'
      });
    }
    
    await db.query(
      'UPDATE tenants SET sync_enabled = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2',
      [enabled, id]
    );
    
    res.json({
      message: `Sync ${enabled ? 'enabled' : 'disabled'} for tenant ${id}`,
      timestamp: new Date().toISOString(),
      tenantId: id,
      syncEnabled: enabled
    });
    
  } catch (error) {
    res.status(500).json({
      error: 'Failed to update tenant sync status',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * @swagger
 * /api/logs:
 *   get:
 *     summary: Sync logs
 *     description: Ottieni i log di sincronizzazione
 *     tags: [Monitoring]
 *     parameters:
 *       - in: query
 *         name: tenantId
 *         schema:
 *           type: string
 *         description: Filter by tenant ID
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           default: 50
 *       - in: query
 *         name: offset
 *         schema:
 *           type: integer
 *           default: 0
 *     responses:
 *       200:
 *         description: Sync logs
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 timestamp:
 *                   type: string
 *                 logs:
 *                   type: array
 *                   items:
 *                     type: object
 *                 pagination:
 *                   type: object
 *       500:
 *         description: Failed to get logs
 */
router.get('/logs', async (req: Request, res: Response) => {
  try {
    const { tenantId, limit = 50, offset = 0 } = req.query;
    
    let query = `
      SELECT 
        l.*, t.name as tenant_name
      FROM tenant_sync_logs l
      JOIN tenants t ON l.tenant_id = t.id
    `;
    const params: any[] = [];
    
    if (tenantId) {
      query += ' WHERE l.tenant_id = $1';
      params.push(tenantId);
    }
    
    query += ` ORDER BY l.started_at DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
    params.push(parseInt(limit as string), parseInt(offset as string));
    
    const logs = await db.getMany(query, params);
    
    res.json({
      timestamp: new Date().toISOString(),
      logs,
      pagination: {
        limit: parseInt(limit as string),
        offset: parseInt(offset as string),
        total: logs.length
      }
    });
    
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get logs',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * @swagger
 * /api/stats:
 *   get:
 *     summary: Statistiche sistema
 *     description: Ottieni statistiche complete del sistema multi-tenant
 *     tags: [Monitoring]
 *     responses:
 *       200:
 *         description: System statistics
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/SystemStats'
 *       500:
 *         description: Failed to get stats
 */
router.get('/stats', async (req: Request, res: Response) => {
  try {
    // Stats database
    const totalTenants = await db.getOne('SELECT COUNT(*) as count FROM tenants');
    const activeTenants = await db.getOne('SELECT COUNT(*) as count FROM tenants WHERE sync_enabled = true');
    const totalWorkflows = await db.getOne('SELECT COUNT(*) as count FROM tenant_workflows');
    const totalExecutions = await db.getOne('SELECT COUNT(*) as count FROM tenant_executions');
    
    // Stats scheduler
    const schedulerStats = scheduler.getStats();
    const health = await scheduler.healthCheck();
    
    // Recent sync stats
    const recentSyncs = await db.getMany(`
      SELECT 
        DATE_TRUNC('hour', started_at) as hour,
        COUNT(*) as syncs,
        AVG(duration_ms) as avg_duration,
        SUM(items_processed) as items_processed
      FROM tenant_sync_logs 
      WHERE started_at > NOW() - INTERVAL '24 hours'
      GROUP BY DATE_TRUNC('hour', started_at)
      ORDER BY hour DESC
      LIMIT 24
    `);
    
    res.json({
      timestamp: new Date().toISOString(),
      database: {
        totalTenants: parseInt(totalTenants.count),
        activeTenants: parseInt(activeTenants.count),
        totalWorkflows: parseInt(totalWorkflows.count),
        totalExecutions: parseInt(totalExecutions.count)
      },
      scheduler: {
        isRunning: schedulerStats.isRunning,
        activeTenants: schedulerStats.stats.activeTenants,
        totalSyncRuns: schedulerStats.stats.totalSyncRuns,
        lastSyncTime: schedulerStats.stats.lastSyncTime,
        totalWorkflowsSynced: schedulerStats.stats.totalWorkflowsSynced,
        totalExecutionsSynced: schedulerStats.stats.totalExecutionsSynced
      },
      health: health,
      recentActivity: recentSyncs,
      system: {
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        nodeVersion: process.version
      }
    });
    
  } catch (error) {
    res.status(500).json({
      error: 'Failed to get stats',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * @swagger
 * /api/scheduler/refresh-workflow:
 *   post:
 *     tags: [Scheduler]
 *     summary: Force refresh specific workflow
 *     description: Forces immediate sync of a specific workflow from n8n, bypassing cache
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - tenantId
 *               - workflowId
 *             properties:
 *               tenantId:
 *                 type: string
 *                 description: Tenant ID
 *               workflowId:
 *                 type: string
 *                 description: Workflow ID to refresh
 *     responses:
 *       200:
 *         description: Workflow refreshed successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                 workflow:
 *                   type: object
 *                 timestamp:
 *                   type: string
 *       400:
 *         description: Invalid request parameters
 *       500:
 *         description: Failed to refresh workflow
 */
router.post('/refresh-workflow', async (req: Request, res: Response) => {
  try {
    const { tenantId, workflowId } = req.body;
    
    if (!tenantId || !workflowId) {
      return res.status(400).json({
        error: 'Missing required parameters',
        message: 'tenantId and workflowId are required'
      });
    }
    
    console.log(`🔄 Force refreshing workflow ${workflowId} for tenant ${tenantId}`);
    
    // Force immediate sync by resetting the last_synced_at timestamp
    await db.query(`
      UPDATE tenant_workflows 
      SET last_synced_at = '2000-01-01'
      WHERE id = $1 AND tenant_id = $2
    `, [workflowId, tenantId]);
    
    // Trigger sync for this tenant
    const result = await scheduler.syncSingleTenant({ id: tenantId });
    
    res.json({
      success: true,
      workflow: {
        id: workflowId,
        tenantId: tenantId,
        synced: result.workflowsSynced > 0
      },
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    res.status(500).json({
      error: 'Failed to refresh workflow',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router;