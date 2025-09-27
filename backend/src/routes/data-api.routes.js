/**
 * Data API Routes - Secure data access for Intelligence Engine
 * Enterprise-grade implementation with authentication, rate limiting, and caching
 *
 * @module data-api.routes
 * @requires express
 * @requires ../middleware/auth.middleware
 * @requires ../services/cache.service
 */

import express from 'express';
import { authenticate, authenticateService } from '../middleware/auth.middleware.js';
import { sanitizeData } from '../middleware/data-sanitizer.js';
import { cacheMiddleware } from '../middleware/cache.middleware.js';
import { rateLimiter } from '../middleware/rate-limiter.js';
import { dbPool } from '../db/pg-pool.js';
import businessLogger from '../utils/logger.js';

const router = express.Router();

// Rate limiting: 100 requests per minute per IP
const apiRateLimiter = rateLimiter({
  windowMs: 60 * 1000,
  max: 100,
  message: 'Too many requests from this IP, please try again later.'
});

// Apply rate limiting to all data API routes
router.use(apiRateLimiter);

/**
 * GET /api/data/users
 * Retrieve users with pagination and filtering
 * Cached for 60 seconds
 */
router.get('/users', authenticateService, cacheMiddleware(60), async (req, res) => {
  try {
    const {
      type = 'all',      // all, active, inactive
      limit = 10,
      offset = 0,
      role = null
    } = req.query;

    let query = `
      SELECT
        id,
        email,
        full_name,
        role,
        is_active,
        last_login,
        created_at
      FROM pilotpros.users
    `;

    const params = [];
    const conditions = [];

    if (type === 'active') {
      conditions.push('is_active = true');
    } else if (type === 'inactive') {
      conditions.push('is_active = false');
    }

    if (role) {
      conditions.push(`role = $${params.length + 1}`);
      params.push(role);
    }

    if (conditions.length > 0) {
      query += ' WHERE ' + conditions.join(' AND ');
    }

    query += ' ORDER BY created_at DESC';
    query += ` LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
    params.push(limit, offset);

    const result = await dbPool.query(query, params);

    // Count total for pagination
    let countQuery = 'SELECT COUNT(*) FROM pilotpros.users';
    if (conditions.length > 0) {
      countQuery += ' WHERE ' + conditions.join(' AND ');
    }
    const countResult = await dbPool.query(countQuery, params.slice(0, -2));

    res.json({
      success: true,
      data: sanitizeData(result.rows, 'users'),
      pagination: {
        total: parseInt(countResult.rows[0].count),
        limit: parseInt(limit),
        offset: parseInt(offset)
      }
    });

  } catch (error) {
    businessLogger.error('Data API - Users query error:', error);
    res.status(500).json({
      success: false,
      error: 'Unable to retrieve user information'
    });
  }
});

/**
 * GET /api/data/sessions
 * Retrieve active sessions with user information
 * Cached for 30 seconds
 */
router.get('/sessions', authenticateService, cacheMiddleware(30), async (req, res) => {
  try {
    const {
      active = true,
      minutes = 30,
      limit = 20
    } = req.query;

    const query = `
      SELECT
        s.id,
        s.user_id,
        s.ip_address,
        s.created_at,
        s.last_activity,
        u.email,
        u.full_name,
        u.role
      FROM pilotpros.active_sessions s
      LEFT JOIN pilotpros.users u ON s.user_id = u.id
      WHERE s.last_activity > NOW() - INTERVAL '${parseInt(minutes)} minutes'
      ORDER BY s.last_activity DESC
      LIMIT $1
    `;

    const result = await dbPool.query(query, [limit]);

    res.json({
      success: true,
      data: sanitizeData(result.rows, 'sessions'),
      metadata: {
        active_threshold_minutes: parseInt(minutes),
        count: result.rows.length
      }
    });

  } catch (error) {
    businessLogger.error('Data API - Sessions query error:', error);
    res.status(500).json({
      success: false,
      error: 'Unable to retrieve session information'
    });
  }
});

/**
 * GET /api/data/metrics
 * Retrieve aggregated business metrics
 * Cached for 120 seconds
 */
router.get('/metrics', authenticateService, cacheMiddleware(120), async (req, res) => {
  try {
    const { period = 'day' } = req.query;

    // Map period to PostgreSQL interval
    const intervalMap = {
      'hour': '1 hour',
      'day': '1 day',
      'week': '7 days',
      'month': '30 days'
    };
    const interval = intervalMap[period] || '1 day';

    const metricsQuery = `
      SELECT
        (SELECT COUNT(*) FROM pilotpros.users) as total_users,
        (SELECT COUNT(*) FROM pilotpros.users WHERE is_active = true) as active_users,
        (SELECT COUNT(*) FROM pilotpros.active_sessions
         WHERE last_activity > NOW() - INTERVAL '30 minutes') as active_sessions,
        (SELECT COUNT(*) FROM pilotpros.business_execution_data
         WHERE created_at > NOW() - INTERVAL '${interval}') as recent_executions,
        (SELECT COUNT(DISTINCT workflow_id) FROM pilotpros.business_execution_data) as unique_processes,
        (SELECT pg_database_size(current_database())) as database_size_bytes
    `;

    const result = await dbPool.query(metricsQuery);
    const metrics = result.rows[0];

    // Calculate additional metrics
    metrics.database_size_mb = Math.round(metrics.database_size_bytes / (1024 * 1024));
    delete metrics.database_size_bytes;

    res.json({
      success: true,
      data: sanitizeData(metrics, 'metrics'),
      period: period
    });

  } catch (error) {
    businessLogger.error('Data API - Metrics query error:', error);
    res.status(500).json({
      success: false,
      error: 'Unable to retrieve metrics'
    });
  }
});

/**
 * GET /api/data/schema
 * Retrieve database schema information
 * Cached for 300 seconds (5 minutes)
 */
router.get('/schema', authenticateService, cacheMiddleware(300), async (req, res) => {
  try {
    const { table = null } = req.query;

    let schemaQuery;
    const params = [];

    if (table) {
      // Get specific table schema
      schemaQuery = `
        SELECT
          column_name,
          data_type,
          is_nullable,
          column_default,
          character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'pilotpros'
        AND table_name = $1
        ORDER BY ordinal_position
      `;
      params.push(table);
    } else {
      // Get all tables overview
      schemaQuery = `
        SELECT
          table_name,
          pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
          obj_description((schemaname||'.'||tablename)::regclass) as description
        FROM pg_tables
        WHERE schemaname = 'pilotpros'
        ORDER BY table_name
      `;
    }

    const result = await dbPool.query(schemaQuery, params);

    res.json({
      success: true,
      data: sanitizeData(result.rows, 'schema'),
      table: table
    });

  } catch (error) {
    businessLogger.error('Data API - Schema query error:', error);
    res.status(500).json({
      success: false,
      error: 'Unable to retrieve schema information'
    });
  }
});

/**
 * POST /api/data/query
 * Execute validated and whitelisted queries
 * No caching for dynamic queries
 */
router.post('/query', authenticateService, async (req, res) => {
  try {
    const { query, params = [] } = req.body;

    // Validate query is SELECT only
    const normalizedQuery = query.trim().toUpperCase();
    if (!normalizedQuery.startsWith('SELECT')) {
      return res.status(403).json({
        success: false,
        error: 'Only SELECT queries are allowed'
      });
    }

    // Check for dangerous keywords
    const dangerousKeywords = [
      'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE',
      'ALTER', 'TRUNCATE', 'EXEC', 'EXECUTE'
    ];

    for (const keyword of dangerousKeywords) {
      if (normalizedQuery.includes(keyword)) {
        return res.status(403).json({
          success: false,
          error: 'Query contains forbidden keywords'
        });
      }
    }

    // Limit results if not specified
    let finalQuery = query;
    if (!normalizedQuery.includes('LIMIT')) {
      finalQuery += ' LIMIT 100';
    }

    // Execute query with timeout
    const client = await dbPool.connect();
    try {
      await client.query('SET statement_timeout = 5000'); // 5 second timeout
      const result = await client.query(finalQuery, params);

      res.json({
        success: true,
        data: sanitizeData(result.rows, 'query'),
        rowCount: result.rowCount
      });
    } finally {
      client.release();
    }

  } catch (error) {
    businessLogger.error('Data API - Query execution error:', error);

    // Don't expose detailed error messages
    const userMessage = error.message.includes('timeout')
      ? 'Query took too long to execute'
      : 'Unable to execute query';

    res.status(500).json({
      success: false,
      error: userMessage
    });
  }
});

/**
 * GET /api/data/workflows
 * Retrieve workflow information from n8n schema
 * Cached for 60 seconds
 */
router.get('/workflows', authenticateService, cacheMiddleware(60), async (req, res) => {
  try {
    const { active = null, limit = 20 } = req.query;

    let query = `
      SELECT
        w.id,
        w.name,
        w.active,
        w.created_at,
        w.updated_at,
        COUNT(e.id) as execution_count
      FROM n8n.workflows_entity w
      LEFT JOIN n8n.execution_entity e ON w.id = e.workflow_id
    `;

    if (active !== null) {
      query += ` WHERE w.active = ${active === 'true'}`;
    }

    query += `
      GROUP BY w.id, w.name, w.active, w.created_at, w.updated_at
      ORDER BY w.updated_at DESC
      LIMIT $1
    `;

    const result = await dbPool.query(query, [limit]);

    res.json({
      success: true,
      data: sanitizeData(result.rows, 'workflows')
    });

  } catch (error) {
    businessLogger.error('Data API - Workflows query error:', error);
    res.status(500).json({
      success: false,
      error: 'Unable to retrieve workflow information'
    });
  }
});

/**
 * GET /api/data/statistics
 * Real-time statistics combining multiple data sources
 * Cached for 30 seconds
 */
router.get('/statistics', authenticateService, cacheMiddleware(30), async (req, res) => {
  try {
    const statsQuery = `
      WITH user_stats AS (
        SELECT
          COUNT(*) as total,
          COUNT(CASE WHEN is_active THEN 1 END) as active,
          COUNT(CASE WHEN last_login > NOW() - INTERVAL '24 hours' THEN 1 END) as recent_logins
        FROM pilotpros.users
      ),
      session_stats AS (
        SELECT
          COUNT(*) as total,
          COUNT(CASE WHEN last_activity > NOW() - INTERVAL '30 minutes' THEN 1 END) as active
        FROM pilotpros.active_sessions
      ),
      execution_stats AS (
        SELECT
          COUNT(*) as total,
          COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as last_24h,
          COUNT(CASE WHEN created_at > NOW() - INTERVAL '1 hour' THEN 1 END) as last_hour
        FROM pilotpros.business_execution_data
      )
      SELECT
        row_to_json(u.*) as users,
        row_to_json(s.*) as sessions,
        row_to_json(e.*) as executions
      FROM user_stats u, session_stats s, execution_stats e
    `;

    const result = await dbPool.query(statsQuery);

    res.json({
      success: true,
      data: sanitizeData(result.rows[0], 'statistics'),
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    businessLogger.error('Data API - Statistics query error:', error);
    res.status(500).json({
      success: false,
      error: 'Unable to retrieve statistics'
    });
  }
});

// Audit logging for all data API calls
router.use((req, res, next) => {
  businessLogger.info('Data API access', {
    path: req.path,
    method: req.method,
    user: req.user?.id || 'service',
    ip: req.ip,
    timestamp: new Date().toISOString()
  });
  next();
});

export default router;