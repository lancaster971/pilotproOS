/**
 * Health Controller
 * 
 * API endpoints per health monitoring e metriche
 */

import express, { Request, Response } from 'express';
import { getHealthMonitor } from '../monitoring/health-monitor.js';

const router = express.Router();
const monitor = getHealthMonitor();

/**
 * @swagger
 * /health/check:
 *   get:
 *     summary: Health check completo
 *     description: Esegue un health check completo del sistema con tutti i componenti
 *     tags: [Monitoring]
 *     responses:
 *       200:
 *         description: Health check result
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   enum: [healthy, degraded, unhealthy]
 *                 timestamp:
 *                   type: string
 *                   format: date-time
 *                 checks:
 *                   type: object
 *                   properties:
 *                     database:
 *                       $ref: '#/components/schemas/ComponentHealth'
 *                     scheduler:
 *                       $ref: '#/components/schemas/ComponentHealth'
 *                     memory:
 *                       $ref: '#/components/schemas/ComponentHealth'
 *                     disk:
 *                       $ref: '#/components/schemas/ComponentHealth'
 *                     api:
 *                       $ref: '#/components/schemas/ComponentHealth'
 *                 metrics:
 *                   $ref: '#/components/schemas/SystemMetrics'
 *                 alerts:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/Alert'
 *       503:
 *         description: Service unhealthy
 */
router.get('/check', async (req: Request, res: Response) => {
  try {
    const healthCheck = await monitor.performHealthCheck();
    
    // Return appropriate status code based on health
    const statusCode = healthCheck.status === 'healthy' ? 200 : 
                      healthCheck.status === 'degraded' ? 200 : 503;
    
    res.status(statusCode).json(healthCheck);
    
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Health check failed'
    });
  }
});

/**
 * @swagger
 * /health/live:
 *   get:
 *     summary: Liveness probe
 *     description: Simple liveness check per Kubernetes/Docker
 *     tags: [Monitoring]
 *     responses:
 *       200:
 *         description: Service is alive
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   example: ok
 *                 timestamp:
 *                   type: string
 *                   format: date-time
 *       503:
 *         description: Service is not alive
 */
router.get('/live', (req: Request, res: Response) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString()
  });
});

/**
 * @swagger
 * /health/ready:
 *   get:
 *     summary: Readiness probe
 *     description: Verifica se il servizio è pronto per ricevere traffico
 *     tags: [Monitoring]
 *     responses:
 *       200:
 *         description: Service is ready
 *       503:
 *         description: Service is not ready
 */
router.get('/ready', async (req: Request, res: Response) => {
  try {
    const healthCheck = await monitor.performHealthCheck();
    
    // Service is ready only if healthy or degraded (not unhealthy)
    if (healthCheck.status === 'unhealthy') {
      res.status(503).json({
        status: 'not_ready',
        timestamp: new Date().toISOString(),
        reason: 'System unhealthy',
        checks: healthCheck.checks
      });
    } else {
      res.json({
        status: 'ready',
        timestamp: new Date().toISOString()
      });
    }
    
  } catch (error) {
    res.status(503).json({
      status: 'not_ready',
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Readiness check failed'
    });
  }
});

/**
 * @swagger
 * /health/metrics:
 *   get:
 *     summary: Metriche Prometheus
 *     description: Esporta metriche in formato Prometheus
 *     tags: [Monitoring]
 *     produces:
 *       - text/plain
 *     responses:
 *       200:
 *         description: Prometheus metrics
 *         content:
 *           text/plain:
 *             schema:
 *               type: string
 *               example: |
 *                 # HELP n8n_mcp_health_status Overall health status
 *                 # TYPE n8n_mcp_health_status gauge
 *                 n8n_mcp_health_status 1
 */
router.get('/metrics', async (req: Request, res: Response) => {
  try {
    const prometheusMetrics = await monitor.getPrometheusMetrics();
    
    res.set('Content-Type', 'text/plain; version=0.0.4');
    res.send(prometheusMetrics);
    
  } catch (error) {
    res.status(500).json({
      error: 'Failed to generate metrics',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * @swagger
 * /health/dashboard:
 *   get:
 *     summary: Dashboard data
 *     description: Dati completi per dashboard di monitoring
 *     tags: [Monitoring]
 *     responses:
 *       200:
 *         description: Dashboard data
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 health:
 *                   type: object
 *                 metrics:
 *                   type: object
 *                 trends:
 *                   type: object
 *                 alerts:
 *                   type: array
 */
router.get('/dashboard', async (req: Request, res: Response) => {
  try {
    const healthCheck = await monitor.performHealthCheck();
    
    // Get trend data from database
    const db = (await import('../database/connection.js')).DatabaseConnection.getInstance();
    
    // Sync trends (last 7 days)
    const syncTrends = await db.getMany(`
      SELECT 
        DATE(started_at) as date,
        COUNT(*) as total_syncs,
        COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_syncs,
        COUNT(CASE WHEN status = 'error' THEN 1 END) as failed_syncs,
        AVG(duration_ms) as avg_duration_ms
      FROM tenant_sync_logs
      WHERE started_at > NOW() - INTERVAL '7 days'
      GROUP BY DATE(started_at)
      ORDER BY date DESC
    `);
    
    // Workflow trends
    const workflowTrends = await db.getMany(`
      SELECT 
        DATE(created_at) as date,
        COUNT(*) as workflows_created
      FROM tenant_workflows
      WHERE created_at > NOW() - INTERVAL '7 days'
      GROUP BY DATE(created_at)
      ORDER BY date DESC
    `);
    
    // Execution trends
    const executionTrends = await db.getMany(`
      SELECT 
        DATE(started_at) as date,
        COUNT(*) as executions,
        COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
        COUNT(CASE WHEN status = 'error' THEN 1 END) as failed
      FROM tenant_executions
      WHERE started_at > NOW() - INTERVAL '7 days'
      GROUP BY DATE(started_at)
      ORDER BY date DESC
    `);
    
    res.json({
      timestamp: new Date().toISOString(),
      health: {
        status: healthCheck.status,
        checks: healthCheck.checks,
        alerts: healthCheck.alerts
      },
      metrics: healthCheck.metrics,
      trends: {
        sync: syncTrends,
        workflows: workflowTrends,
        executions: executionTrends
      }
    });
    
  } catch (error) {
    res.status(500).json({
      error: 'Failed to generate dashboard data',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * @swagger
 * components:
 *   schemas:
 *     ComponentHealth:
 *       type: object
 *       properties:
 *         status:
 *           type: string
 *           enum: [healthy, degraded, unhealthy]
 *         message:
 *           type: string
 *         latency_ms:
 *           type: number
 *         details:
 *           type: object
 *     
 *     SystemMetrics:
 *       type: object
 *       properties:
 *         uptime_seconds:
 *           type: number
 *         memory:
 *           type: object
 *           properties:
 *             used_mb:
 *               type: number
 *             total_mb:
 *               type: number
 *             percentage:
 *               type: number
 *         cpu:
 *           type: object
 *         process:
 *           type: object
 *         database:
 *           type: object
 *         scheduler:
 *           type: object
 *         tenants:
 *           type: object
 *     
 *     Alert:
 *       type: object
 *       properties:
 *         severity:
 *           type: string
 *           enum: [warning, critical]
 *         component:
 *           type: string
 *         message:
 *           type: string
 *         timestamp:
 *           type: string
 *           format: date-time
 */

export default router;