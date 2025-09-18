/**
 * Health Check Controller
 * Comprehensive health monitoring endpoints
 * Resolves health monitoring technical debt
 */

import { Router } from 'express';
import { Pool } from 'pg';
import config from '../config/index.js';
import businessLogger from '../utils/logger.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import os from 'os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = Router();

/**
 * @swagger
 * /api/health:
 *   get:
 *     tags:
 *       - Health
 *     summary: System health check
 *     description: Check overall system health and status
 *     responses:
 *       200:
 *         description: System health status
 */
router.get('/', async (req, res) => {
  const startTime = Date.now();
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0',
    environment: config.server.nodeEnv,
    uptime: process.uptime(),
    services: {},
    metrics: {},
  };

  try {
    // Check database
    const dbHealth = await checkDatabase();
    health.services.database = dbHealth;

    // Check n8n
    const n8nHealth = await checkN8n();
    health.services.n8n = n8nHealth;

    // Check Redis (if enabled)
    if (config.redis.enabled) {
      const redisHealth = await checkRedis();
      health.services.redis = redisHealth;
    }

    // System metrics
    health.metrics = getSystemMetrics();

    // Determine overall health status
    const unhealthyServices = Object.values(health.services).filter(
      (service) => service.status === 'unhealthy'
    );

    if (unhealthyServices.length > 0) {
      health.status = 'degraded';
    }

    // Response time
    health.responseTime = Date.now() - startTime;

    res.status(health.status === 'healthy' ? 200 : 503).json(health);
  } catch (error) {
    businessLogger.error('Health check failed', error);
    health.status = 'unhealthy';
    health.error = error.message;
    res.status(503).json(health);
  }
});

/**
 * @swagger
 * /api/health/database:
 *   get:
 *     tags:
 *       - Health
 *     summary: Database health check
 *     description: Check database connection and performance
 */
router.get('/database', async (req, res) => {
  try {
    const health = await checkDatabase(true);
    res.status(health.status === 'healthy' ? 200 : 503).json(health);
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      error: error.message,
    });
  }
});

/**
 * @swagger
 * /api/health/n8n:
 *   get:
 *     tags:
 *       - Health
 *     summary: n8n health check
 *     description: Check n8n automation engine status
 */
router.get('/n8n', async (req, res) => {
  try {
    const health = await checkN8n(true);
    res.status(health.status === 'healthy' ? 200 : 503).json(health);
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      error: error.message,
    });
  }
});

/**
 * @swagger
 * /api/health/ready:
 *   get:
 *     tags:
 *       - Health
 *     summary: Readiness probe
 *     description: Check if the service is ready to accept requests
 */
router.get('/ready', async (req, res) => {
  try {
    // Check critical services
    const dbHealth = await checkDatabase();

    if (dbHealth.status !== 'healthy') {
      return res.status(503).json({
        ready: false,
        reason: 'Database not ready',
      });
    }

    res.status(200).json({
      ready: true,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    res.status(503).json({
      ready: false,
      error: error.message,
    });
  }
});

/**
 * @swagger
 * /api/health/live:
 *   get:
 *     tags:
 *       - Health
 *     summary: Liveness probe
 *     description: Check if the service is alive
 */
router.get('/live', (req, res) => {
  // Simple liveness check - if we can respond, we're alive
  res.status(200).json({
    alive: true,
    timestamp: new Date().toISOString(),
    pid: process.pid,
  });
});

/**
 * @swagger
 * /api/health/metrics:
 *   get:
 *     tags:
 *       - Health
 *     summary: System metrics
 *     description: Get detailed system metrics
 */
router.get('/metrics', (req, res) => {
  try {
    const metrics = getDetailedSystemMetrics();
    res.status(200).json(metrics);
  } catch (error) {
    res.status(500).json({
      error: 'Failed to collect metrics',
      message: error.message,
    });
  }
});

// Helper functions

/**
 * Check database health
 */
async function checkDatabase(detailed = false) {
  const startTime = Date.now();
  const health = {
    status: 'unknown',
    responseTime: 0,
  };

  try {
    const pool = new Pool({
      host: config.database.host,
      port: config.database.port,
      user: config.database.user,
      password: config.database.password,
      database: config.database.name,
      connectionTimeoutMillis: 5000,
    });

    const client = await pool.connect();

    // Simple query to check connection
    const result = await client.query('SELECT NOW() as time, version() as version');

    if (detailed) {
      // Get additional database stats
      const stats = await client.query(`
        SELECT
          (SELECT count(*) FROM pg_stat_activity) as connections,
          (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
          pg_database_size(current_database()) as database_size
      `);

      health.details = {
        time: result.rows[0].time,
        version: result.rows[0].version,
        connections: stats.rows[0].connections,
        activeConnections: stats.rows[0].active_connections,
        databaseSize: stats.rows[0].database_size,
      };
    }

    client.release();
    await pool.end();

    health.status = 'healthy';
    health.responseTime = Date.now() - startTime;
  } catch (error) {
    health.status = 'unhealthy';
    health.error = error.message;
    health.responseTime = Date.now() - startTime;
  }

  return health;
}

/**
 * Check n8n health
 */
async function checkN8n(detailed = false) {
  const startTime = Date.now();
  const health = {
    status: 'unknown',
    responseTime: 0,
  };

  try {
    const n8nUrl = config.n8n.url;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${n8nUrl}/rest/health`, {
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      },
    });

    clearTimeout(timeout);

    if (response.ok) {
      health.status = 'healthy';

      if (detailed) {
        try {
          // Try to get workflow stats
          const workflowResponse = await fetch(`${n8nUrl}/rest/workflows`, {
            headers: {
              'X-N8N-API-KEY': config.n8n.apiKey || '',
            },
          });

          if (workflowResponse.ok) {
            const workflows = await workflowResponse.json();
            health.details = {
              totalWorkflows: workflows.data?.length || 0,
              activeWorkflows: workflows.data?.filter(w => w.active).length || 0,
            };
          }
        } catch (detailError) {
          // Details are optional, don't fail the health check
          health.details = { error: 'Could not fetch details' };
        }
      }
    } else {
      health.status = response.status >= 500 ? 'unhealthy' : 'degraded';
    }

    health.responseTime = Date.now() - startTime;
  } catch (error) {
    health.status = 'unhealthy';
    health.error = error.message;
    health.responseTime = Date.now() - startTime;
  }

  return health;
}

/**
 * Check Redis health (placeholder)
 */
async function checkRedis(detailed = false) {
  // TODO: Implement when Redis is configured
  return {
    status: 'not_configured',
    message: 'Redis health check not implemented',
  };
}

/**
 * Get basic system metrics
 */
function getSystemMetrics() {
  return {
    memory: {
      used: process.memoryUsage().heapUsed,
      total: process.memoryUsage().heapTotal,
      rss: process.memoryUsage().rss,
    },
    cpu: {
      usage: process.cpuUsage(),
    },
    uptime: process.uptime(),
  };
}

/**
 * Get detailed system metrics
 */
function getDetailedSystemMetrics() {
  const memoryUsage = process.memoryUsage();
  const cpuUsage = process.cpuUsage();

  return {
    timestamp: new Date().toISOString(),
    process: {
      pid: process.pid,
      version: process.version,
      uptime: process.uptime(),
      title: process.title,
    },
    memory: {
      heap: {
        used: memoryUsage.heapUsed,
        total: memoryUsage.heapTotal,
        percentage: ((memoryUsage.heapUsed / memoryUsage.heapTotal) * 100).toFixed(2),
      },
      rss: memoryUsage.rss,
      external: memoryUsage.external,
      arrayBuffers: memoryUsage.arrayBuffers,
      system: {
        total: os.totalmem(),
        free: os.freemem(),
        used: os.totalmem() - os.freemem(),
        percentage: (((os.totalmem() - os.freemem()) / os.totalmem()) * 100).toFixed(2),
      },
    },
    cpu: {
      user: cpuUsage.user,
      system: cpuUsage.system,
      cores: os.cpus().length,
      model: os.cpus()[0]?.model,
      speed: os.cpus()[0]?.speed,
      loadAverage: os.loadavg(),
    },
    system: {
      platform: os.platform(),
      arch: os.arch(),
      hostname: os.hostname(),
      release: os.release(),
      networkInterfaces: Object.keys(os.networkInterfaces()).length,
    },
    environment: {
      nodeEnv: config.server.nodeEnv,
      port: config.server.port,
      host: config.server.host,
    },
  };
}

export default router;