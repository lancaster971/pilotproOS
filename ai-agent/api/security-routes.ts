/**
 * Security Routes - Router per Security Controller Premium
 * 
 * Definisce le route per le funzionalità Security Premium:
 * - Security audit completi
 * - Compliance reporting  
 * - Security metrics e scoring
 * - Security configuration management
 */

import { Router } from 'express';
import { SecurityController } from './security-controller.js';
import { N8nApiService } from './n8n-client.js';
import { DatabaseConnection } from '../database/connection.js';
import { EnvConfig } from '../config/environment.js';

// Inizializza dipendenze
const envConfig: EnvConfig = {
  n8nApiUrl: process.env.N8N_API_URL || 'https://your-n8n-instance.com/api/v1',
  n8nApiKey: process.env.N8N_API_KEY || '',
  debug: process.env.DEBUG === 'true',
  dbType: 'postgres',
  dbHost: process.env.DB_HOST || 'localhost',
  dbPort: parseInt(process.env.DB_PORT || '5432'),
  dbName: process.env.DB_NAME || 'n8n_mcp',
  dbUser: process.env.DB_USER || '',
  dbPassword: process.env.DB_PASSWORD || '',
  dbSsl: process.env.DB_SSL === 'true',
  syncInterval: parseInt(process.env.SYNC_INTERVAL || '30'),
  kpiRetentionDays: parseInt(process.env.KPI_RETENTION_DAYS || '30'),
  enableScheduler: process.env.ENABLE_SCHEDULER !== 'false',
  logLevel: (process.env.LOG_LEVEL as 'debug' | 'info' | 'warn' | 'error') || 'info'
};

const n8nService = new N8nApiService(envConfig);
const dbConnection = DatabaseConnection.getInstance();
const securityController = new SecurityController(n8nService, dbConnection);

const router = Router();

/**
 * @swagger
 * components:
 *   schemas:
 *     SecurityAuditReport:
 *       type: object
 *       properties:
 *         overview:
 *           type: object
 *           properties:
 *             securityScore:
 *               type: integer
 *               minimum: 0
 *               maximum: 100
 *             riskLevel:
 *               type: string
 *               enum: [LOW, MEDIUM, HIGH, CRITICAL]
 *             lastAuditDate:
 *               type: string
 *               format: date-time
 *             totalIssues:
 *               type: integer
 *             criticalIssues:
 *               type: integer
 *         categories:
 *           type: object
 *         recommendations:
 *           type: array
 *           items:
 *             $ref: '#/components/schemas/SecurityRecommendation'
 *         complianceStatus:
 *           $ref: '#/components/schemas/ComplianceStatus'
 * 
 *     SecurityRecommendation:
 *       type: object
 *       properties:
 *         priority:
 *           type: string
 *           enum: [HIGH, MEDIUM, LOW]
 *         category:
 *           type: string
 *         title:
 *           type: string
 *         description:
 *           type: string
 *         effort:
 *           type: string
 *           enum: [LOW, MEDIUM, HIGH]
 *         impact:
 *           type: string
 *           enum: [LOW, MEDIUM, HIGH]
 * 
 *     ComplianceStatus:
 *       type: object
 *       properties:
 *         gdpr:
 *           type: object
 *           properties:
 *             compliant:
 *               type: boolean
 *             score:
 *               type: integer
 *             issues:
 *               type: array
 *               items:
 *                 type: string
 *         soc2:
 *           type: object
 *           properties:
 *             compliant:
 *               type: boolean
 *             score:
 *               type: integer
 *             issues:
 *               type: array
 *               items:
 *                 type: string
 */

/**
 * @swagger
 * /api/tenant/{tenantId}/security/audit:
 *   post:
 *     summary: Generate comprehensive security audit
 *     description: Esegue un audit completo della sicurezza usando n8n API e analisi avanzate
 *     tags: [Security Premium]
 *     parameters:
 *       - in: path
 *         name: tenantId
 *         required: true
 *         schema:
 *           type: string
 *         description: Tenant ID
 *       - in: query
 *         name: categories
 *         schema:
 *           type: string
 *           example: "credentials,database,nodes"
 *         description: Comma-separated list of audit categories
 *       - in: query
 *         name: daysAbandonedWorkflow
 *         schema:
 *           type: integer
 *           default: 30
 *         description: Days for workflow to be considered abandoned
 *     responses:
 *       200:
 *         description: Security audit completed successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                 data:
 *                   $ref: '#/components/schemas/SecurityAuditReport'
 *                 timestamp:
 *                   type: string
 *                   format: date-time
 *       500:
 *         description: Error during security audit
 */
router.post('/tenant/:tenantId/security/audit', securityController.generateSecurityAudit.bind(securityController));

/**
 * @swagger
 * /api/tenant/{tenantId}/security/score-history:
 *   get:
 *     summary: Get security score history
 *     description: Retrieve historical security scores for trending analysis
 *     tags: [Security Premium]
 *     parameters:
 *       - in: path
 *         name: tenantId
 *         required: true
 *         schema:
 *           type: string
 *         description: Tenant ID
 *       - in: query
 *         name: days
 *         schema:
 *           type: integer
 *           default: 30
 *         description: Number of days of history to retrieve
 *     responses:
 *       200:
 *         description: Security score history retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                 data:
 *                   type: object
 *                   properties:
 *                     history:
 *                       type: array
 *                       items:
 *                         type: object
 *                         properties:
 *                           date:
 *                             type: string
 *                             format: date
 *                           avg_score:
 *                             type: number
 *                           max_score:
 *                             type: number
 *                           min_score:
 *                             type: number
 *                           audit_count:
 *                             type: integer
 *                     period:
 *                       type: string
 *                     totalAudits:
 *                       type: integer
 */
router.get('/tenant/:tenantId/security/score-history', securityController.getSecurityScoreHistory.bind(securityController));

/**
 * @swagger
 * /api/tenant/{tenantId}/security/compliance:
 *   get:
 *     summary: Get compliance report
 *     description: Generate compliance report for specified standards (GDPR, SOC2, ISO27001)
 *     tags: [Security Premium]
 *     parameters:
 *       - in: path
 *         name: tenantId
 *         required: true
 *         schema:
 *           type: string
 *         description: Tenant ID
 *       - in: query
 *         name: standard
 *         schema:
 *           type: string
 *           enum: [gdpr, soc2, iso27001, all]
 *           default: all
 *         description: Compliance standard to report on
 *     responses:
 *       200:
 *         description: Compliance report generated successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                 data:
 *                   $ref: '#/components/schemas/ComplianceStatus'
 *                 auditDate:
 *                   type: string
 *                   format: date-time
 *       404:
 *         description: No security audit found - run audit first
 */
router.get('/tenant/:tenantId/security/compliance', securityController.getComplianceReport.bind(securityController));

/**
 * @swagger
 * /api/security/overview:
 *   get:
 *     summary: Get security overview for all tenants
 *     description: Get aggregated security overview using the security_overview view
 *     tags: [Security Premium]
 *     responses:
 *       200:
 *         description: Security overview retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                 data:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       tenant_id:
 *                         type: string
 *                       current_score:
 *                         type: integer
 *                       current_risk:
 *                         type: string
 *                       total_issues:
 *                         type: integer
 *                       critical_issues:
 *                         type: integer
 *                       last_audit:
 *                         type: string
 *                         format: date-time
 *                       score_trend:
 *                         type: integer
 *                       open_incidents:
 *                         type: integer
 *                       pending_recommendations:
 *                         type: integer
 */
router.get('/security/overview', async (req, res) => {
  try {
    const result = await dbConnection.query('SELECT * FROM security_overview ORDER BY current_score ASC');
    
    res.json({
      success: true,
      data: result.rows,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Errore security overview:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get security overview'
    });
  }
});

/**
 * @swagger
 * /api/tenant/{tenantId}/security/metrics:
 *   get:
 *     summary: Get security metrics for tenant
 *     description: Retrieve time-series security metrics for analytics
 *     tags: [Security Premium]
 *     parameters:
 *       - in: path
 *         name: tenantId
 *         required: true
 *         schema:
 *           type: string
 *         description: Tenant ID
 *       - in: query
 *         name: metricType
 *         schema:
 *           type: string
 *           example: "credentials_count,workflows_active"
 *         description: Comma-separated list of metric types to retrieve
 *       - in: query
 *         name: hours
 *         schema:
 *           type: integer
 *           default: 24
 *         description: Number of hours of metrics to retrieve
 *     responses:
 *       200:
 *         description: Security metrics retrieved successfully
 */
router.get('/tenant/:tenantId/security/metrics', async (req, res) => {
  try {
    const { tenantId } = req.params;
    const { metricType, hours = 24 } = req.query;
    
    let whereClause = 'WHERE tenant_id = $1 AND recorded_at >= NOW() - INTERVAL \'${hours} hours\'';
    let params = [tenantId];
    
    if (metricType) {
      const types = (metricType as string).split(',');
      whereClause += ' AND metric_type = ANY($2)';
      params.push(types as any);
    }
    
    const result = await dbConnection.query(`
      SELECT metric_type, metric_value, metric_metadata, recorded_at
      FROM security_metrics 
      ${whereClause}
      ORDER BY recorded_at DESC
      LIMIT 1000
    `, params);
    
    res.json({
      success: true,
      data: result.rows,
      period: `${hours} hours`,
      count: result.rows.length
    });
  } catch (error) {
    console.error('❌ Errore security metrics:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get security metrics'
    });
  }
});

/**
 * @swagger
 * /api/tenant/{tenantId}/security/incidents:
 *   get:
 *     summary: Get security incidents for tenant
 *     description: Retrieve security incidents with optional filtering
 *     tags: [Security Premium]
 *     parameters:
 *       - in: path
 *         name: tenantId
 *         required: true
 *         schema:
 *           type: string
 *         description: Tenant ID
 *       - in: query
 *         name: status
 *         schema:
 *           type: string
 *           enum: [OPEN, INVESTIGATING, RESOLVED, CLOSED]
 *         description: Filter by incident status
 *       - in: query
 *         name: severity
 *         schema:
 *           type: string
 *           enum: [LOW, MEDIUM, HIGH, CRITICAL]
 *         description: Filter by severity level
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           default: 50
 *         description: Maximum number of incidents to return
 *     responses:
 *       200:
 *         description: Security incidents retrieved successfully
 */
router.get('/tenant/:tenantId/security/incidents', async (req, res) => {
  try {
    const { tenantId } = req.params;
    const { status, severity, limit = 50 } = req.query;
    
    let whereClause = 'WHERE tenant_id = $1';
    let params: any[] = [tenantId];
    let paramIndex = 2;
    
    if (status) {
      whereClause += ` AND status = $${paramIndex}`;
      params.push(status);
      paramIndex++;
    }
    
    if (severity) {
      whereClause += ` AND severity = $${paramIndex}`;
      params.push(severity);
      paramIndex++;
    }
    
    const result = await dbConnection.query(`
      SELECT id, incident_type, severity, title, description, 
             affected_resources, detection_method, status, 
             assigned_to, detected_at, resolved_at
      FROM security_incidents 
      ${whereClause}
      ORDER BY detected_at DESC
      LIMIT $${paramIndex}
    `, [...params, limit]);
    
    res.json({
      success: true,
      data: result.rows,
      filters: { status, severity, limit },
      count: result.rows.length
    });
  } catch (error) {
    console.error('❌ Errore security incidents:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get security incidents'
    });
  }
});

export default router;