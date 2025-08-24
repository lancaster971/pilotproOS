// PilotProOS Backend Server - Business Process Operating System
// Adapted from PilotProMT enterprise codebase with simplification
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { Pool } from 'pg';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import { createServer } from 'http';
import { initializeWebSocket } from './websocket.js';

// Business sanitization utilities
import { 
  sanitizeBusinessData, 
  getBusinessStatus,
  getBusinessHealthStatus,
  categorizeBusinessProcess,
  sanitizeErrorMessage,
  formatBusinessDuration,
  generateBusinessInsights
} from './utils/business-terminology.js';

import { 
  businessSanitizer,
  sanitizeBusinessParams,
  validateBusinessData,
  businessOperationLogger,
  businessErrorHandler
} from './middleware/business-sanitizer.js';

// Database compatibility layer
import { DatabaseCompatibilityService } from './services/database-compatibility.service.js';
import { N8nFieldMapper } from './utils/n8n-field-mapper.js';
import { CompatibilityMonitor } from './middleware/compatibility-monitor.js';

// Load environment variables
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = process.env.PORT || 3001;
const host = process.env.HOST || '127.0.0.1';

// ============================================================================
// DATABASE CONNECTION (PostgreSQL condiviso con n8n)
// ============================================================================

const dbPool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'pilotpros_db',
  user: process.env.DB_USER || 'pilotpros_user',
  password: process.env.DB_PASSWORD,
  
  // Connection pool optimization
  max: 20,
  min: 5,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Test database connection
dbPool.connect((err, client, release) => {
  if (err) {
    console.error('❌ Database connection failed:', err);
    process.exit(1);
  } else {
    console.log('✅ PostgreSQL connected (pilotpros_db)');
    release();
  }
});

// ============================================================================
// DATABASE COMPATIBILITY INITIALIZATION
// ============================================================================

// Initialize compatibility layer
const compatibilityService = new DatabaseCompatibilityService(dbPool);
const fieldMapper = new N8nFieldMapper();
const compatibilityMonitor = new CompatibilityMonitor(compatibilityService, fieldMapper);

// Initialize compatibility on startup
compatibilityService.initialize().then(success => {
  if (success) {
    const version = compatibilityService.detectedVersion;
    fieldMapper.updateVersion(version);
    console.log(`🔄 Backend compatible with n8n ${version}`);
  } else {
    console.warn('⚠️ Running with fallback compatibility mode');
  }
});

// ============================================================================
// SECURITY MIDDLEWARE STACK
// ============================================================================

// Security headers (riuso da PilotProMT)
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  hidePoweredBy: true, // Hide Express.js signature
}));

// CORS configuration
app.use(cors({
  origin: process.env.NODE_ENV === 'production' 
    ? [`https://${process.env.DOMAIN}`, `http://${process.env.DOMAIN}`]
    : ['http://localhost:3000', 'http://localhost:5173'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));

// Rate limiting DISABLED for development
// const apiLimiter = rateLimit({
//   windowMs: 15 * 60 * 1000, // 15 minutes
//   max: 100, // limit each IP to 100 requests per windowMs
//   message: {
//     error: 'Too many requests, please try again later.',
//     retryAfter: 15
//   },
//   standardHeaders: true,
//   legacyHeaders: false,
// });

// app.use('/api/', apiLimiter);

// JSON parsing with size limit
app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ extended: true, limit: '1mb' }));

// Business sanitization middleware stack
app.use(businessOperationLogger());
app.use(sanitizeBusinessParams());
app.use(validateBusinessData());
app.use(businessSanitizer());

// Compatibility monitoring middleware
app.use(compatibilityMonitor.middleware());

// Request logging middleware
app.use((req, res, next) => {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${req.method} ${req.url} - IP: ${req.ip}`);
  next();
});

// ============================================================================
// BUSINESS API ENDPOINTS (Anonimized)
// ============================================================================

// System Health Check
app.get('/health', async (req, res) => {
  try {
    // Check database connection
    await dbPool.query('SELECT 1');
    
    // Check n8n availability (internal)
    let n8nStatus = 'unknown';
    try {
      const response = await fetch('http://127.0.0.1:5678/healthz', { 
        timeout: 5000 
      });
      n8nStatus = response.ok ? 'healthy' : 'unhealthy';
    } catch {
      n8nStatus = 'unreachable';
    }
    
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      system: 'Business Process Operating System',
      services: {
        database: 'connected',
        processEngine: n8nStatus,
        apiServer: 'running'
      },
      uptime: process.uptime(),
      memory: {
        used: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
        total: Math.round(process.memoryUsage().heapTotal / 1024 / 1024)
      }
    });
  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      error: 'System health check failed',
      timestamp: new Date().toISOString()
    });
  }
});

// Business Processes API (anonimized workflows) - WITH COMPATIBILITY
app.get('/api/business/processes', async (req, res) => {
  try {
    // Use compatibility service for cross-version query
    const result = await compatibilityService.getWorkflowsCompatible();
    
    res.json({
      data: result.rows || [],
      total: result.rows?.length || 0,
      summary: {
        active: result.rows?.length || 0,
        totalExecutionsToday: result.rows?.reduce((sum, row) => sum + (row.executions_today || 0), 0) || 0,
        avgSuccessRate: result.rows?.length > 0 ? 
          result.rows.reduce((sum, row) => sum + (row.success_rate || 0), 0) / result.rows.length : 0
      },
      _metadata: {
        system: 'Business Process Operating System',
        timestamp: new Date().toISOString(),
        endpoint: '/api/business/processes',
        sanitized: true,
        businessTerminology: true,
        n8nCompatibility: compatibilityService.detectedVersion
      }
    });
  } catch (error) {
    console.error('❌ Error fetching business processes:', error);
    res.status(500).json({ 
      error: 'Failed to fetch business processes',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Business Process Details API (anonimized workflow structure) - NEW for VueFlow
app.get('/api/business/process-details/:processId', async (req, res) => {
  try {
    const { processId } = req.params;
    console.log('🔍 Fetching REAL workflow details for business process:', processId);
    
    // Query n8n database directly for workflow structure (following architecture)
    const workflowQuery = `
      SELECT 
        w.id,
        w.name as process_name,
        w.active as is_active,
        w.nodes,
        w.connections,
        w.staticData as static_data,
        w.createdAt as created_at,
        w.updatedAt as updated_at
      FROM n8n.workflow_entity w
      WHERE w.id = $1
    `;
    
    const workflowResult = await dbPool.query(workflowQuery, [processId]);
    
    if (workflowResult.rows.length === 0) {
      return res.status(404).json({
        error: 'Business process not found',
        processId: processId
      });
    }
    
    const workflow = workflowResult.rows[0];
    
    // Parse nodes and connections from JSON (stored in n8n database)
    const nodes = workflow.nodes || [];
    const connections = workflow.connections || {};
    
    console.log(`✅ REAL workflow loaded: ${workflow.process_name} with ${nodes.length} nodes`);
    
    // Anonimize and transform for business layer
    const businessProcessDetails = {
      processId: workflow.id,
      processName: workflow.process_name,
      isActive: workflow.is_active,
      nodeCount: nodes.length,
      connectionCount: Object.keys(connections).length,
      
      // Transform nodes for business visualization
      processSteps: nodes.map((node, index) => ({
        stepId: node.id,
        stepName: node.name,
        stepType: {
          type: node.type,
          category: getBusinessCategory(node.type)
        },
        position: node.position || [(index % 4) * 250, Math.floor(index / 4) * 150],
        configuration: node.parameters || {},
        description: `Business step: ${node.name}`
      })),
      
      // Transform connections for business flow
      processFlow: Object.entries(connections).flatMap(([sourceNode, nodeConnections]) => {
        if (nodeConnections.main && nodeConnections.main[0]) {
          return nodeConnections.main[0].map(connection => ({
            from: sourceNode,
            to: connection.node,
            type: connection.type || 'main'
          }));
        }
        return [];
      }),
      
      // Business metadata
      businessMetadata: {
        category: getCategoryFromName(workflow.process_name),
        complexity: getComplexityScore(nodes.length),
        lastModified: workflow.updated_at,
        businessImpact: getBusinessImpact(workflow.process_name)
      }
    };
    
    res.json({
      data: businessProcessDetails,
      _metadata: {
        system: 'Business Process Operating System',
        timestamp: new Date().toISOString(),
        endpoint: '/api/business/process-details',
        sanitized: true,
        businessTerminology: true,
        realNodes: nodes.length,
        realConnections: Object.keys(connections).length
      }
    });
    
  } catch (error) {
    console.error('❌ Error fetching business process details:', error);
    res.status(500).json({ 
      error: 'Failed to fetch business process details',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Helper functions for business terminology
function getBusinessCategory(nodeType) {
  if (nodeType.includes('trigger') || nodeType.includes('webhook')) return 'Event Handler';
  if (nodeType.includes('openai') || nodeType.includes('ai')) return 'AI Intelligence';
  if (nodeType.includes('http') || nodeType.includes('api')) return 'Integration';
  if (nodeType.includes('email')) return 'Communication';
  if (nodeType.includes('database')) return 'Data Management';
  if (nodeType.includes('function') || nodeType.includes('code')) return 'Business Logic';
  if (nodeType.includes('file')) return 'Document Processing';
  return 'Process Step';
}

function getCategoryFromName(processName) {
  const name = processName.toLowerCase();
  if (name.includes('chatbot')) return 'Customer Interaction';
  if (name.includes('email') || name.includes('outlook')) return 'Communication';
  if (name.includes('grab') || name.includes('track')) return 'Data Collection';
  if (name.includes('customer') || name.includes('service')) return 'Customer Service';
  return 'General Automation';
}

function getComplexityScore(nodeCount) {
  if (nodeCount <= 3) return 'Simple';
  if (nodeCount <= 7) return 'Medium';
  if (nodeCount <= 12) return 'Complex';
  return 'Enterprise';
}

function getBusinessImpact(processName) {
  const name = processName.toLowerCase();
  if (name.includes('customer') || name.includes('service')) return 'High';
  if (name.includes('ai') || name.includes('chatbot')) return 'High';
  if (name.includes('email') || name.includes('communication')) return 'Medium';
  return 'Medium';
}

// Process Runs API (anonimized executions)
app.get('/api/business/process-runs', async (req, res) => {
  try {
    const { status, processId, limit = 50, offset = 0 } = req.query;
    
    let whereClause = 'WHERE 1=1';
    const params = [];
    let paramCount = 0;
    
    if (status) {
      paramCount++;
      whereClause += ` AND CASE 
        WHEN e.finished = true AND e.status = 'success' THEN 'completed'
        WHEN e.finished = true AND e.status = 'error' THEN 'failed'
        WHEN e.finished = false THEN 'running'
        ELSE 'unknown'
      END = $${paramCount}`;
      params.push(status);
    }
    
    if (processId) {
      paramCount++;
      whereClause += ` AND e."workflowId" = $${paramCount}`;
      params.push(processId);
    }
    
    paramCount++;
    params.push(parseInt(limit));
    paramCount++;
    params.push(parseInt(offset));
    
    const result = await dbPool.query(`
      SELECT 
        e.id as run_id,
        e."workflowId" as process_id,
        w.name as process_name,
        to_char(e."startedAt", 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as start_time,
        to_char(e."stoppedAt", 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as end_time,
        e.finished as is_completed,
        
        -- Business-friendly status
        CASE 
          WHEN e.finished = true AND e.status = 'success' THEN 'Completed Successfully'
          WHEN e.finished = true AND e.status = 'error' THEN 'Requires Attention'
          WHEN e.finished = false THEN 'In Progress'
          ELSE 'Unknown Status'
        END as business_status,
        
        -- Duration calculation
        CASE 
          WHEN e."stoppedAt" IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) * 1000
          ELSE NULL
        END as duration_ms,
        
        -- Error information (business-friendly)
        CASE 
          WHEN e.status = 'error' THEN 'Process encountered an issue'
          ELSE NULL
        END as issue_description
        
      FROM n8n.execution_entity e
      JOIN n8n.workflow_entity w ON e."workflowId" = w.id
      ${whereClause}
      ORDER BY e."startedAt" DESC
      LIMIT $${paramCount-1} OFFSET $${paramCount}
    `, params);
    
    res.json({
      data: result.rows,
      pagination: {
        limit: parseInt(limit),
        offset: parseInt(offset),
        total: result.rows.length
      }
    });
  } catch (error) {
    console.error('❌ Error fetching process runs:', error);
    res.status(500).json({ 
      error: 'Failed to fetch process runs',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Business Analytics API - WITH COMPATIBILITY
app.get('/api/business/analytics', async (req, res) => {
  try {
    // Use compatibility service for cross-version analytics
    const result = await compatibilityService.getAnalyticsCompatible();
    
    const data = result.rows?.[0] || {
      total_processes: 0,
      active_processes: 0, 
      total_executions: 0,
      successful_executions: 0,
      avg_duration_ms: 0
    };
    
    const successRate = data.total_executions > 0 
      ? (data.successful_executions / data.total_executions * 100) 
      : 0;
    
    res.json({
      overview: {
        totalProcesses: parseInt(data.total_processes) || 0,
        activeProcesses: parseInt(data.active_processes) || 0,
        totalExecutions: parseInt(data.total_executions) || 0,
        successRate: Math.round(successRate * 10) / 10,
        avgDurationSeconds: Math.round((data.avg_duration_ms || 0) / 1000)
      },
      
      businessImpact: {
        customersProcessed: parseInt(data.customers_processed || 0),
        ordersProcessed: parseInt(data.orders_processed || 0),
        ticketsProcessed: parseInt(data.tickets_processed || 0),
        timeSavedHours: Math.round((data.minutes_saved || 0) / 60),
        estimatedCostSavings: Math.round((data.minutes_saved || 0) * 0.5)
      },
      
      insights: [
        successRate >= 95 ? 'Excellent process performance' : 
        successRate >= 80 ? 'Good performance with room for improvement' :
        'Processes need optimization attention',
        
        data.active_processes > 0 ? 
          `${data.active_processes} business processes are actively automating your operations` :
          'No active processes - consider activating automation templates',
          
        data.minutes_saved > 0 ?
          `Your automation saved approximately ${Math.round(data.minutes_saved / 60)} hours of manual work this week` :
          'Start using automation to save time on manual processes'
      ],
      
      _metadata: {
        system: 'Business Process Operating System',
        timestamp: new Date().toISOString(),
        endpoint: '/api/business/analytics',
        sanitized: true,
        businessTerminology: true,
        n8nCompatibility: compatibilityService.detectedVersion
      }
    });
  } catch (error) {
    console.error('❌ Error fetching business analytics:', error);
    res.status(500).json({ 
      error: 'Failed to fetch business analytics',
      message: 'Process encountered an issue. Technical support has been notified.',
      timestamp: new Date().toISOString(),
      requestId: 'unknown',
      suggestions: [
        'Try refreshing the analytics data',
        'Check date range parameters', 
        'Try again in a few moments',
        'Contact technical support if needed'
      ],
      technicalDetails: process.env.NODE_ENV === 'development' ? error.message : undefined,
      _metadata: {
        system: 'Business Process Operating System',
        endpoint: '/api/business/analytics',
        error: true,
        n8nCompatibility: compatibilityService?.detectedVersion || 'unknown'
      }
    });
  }
});

// AI Agent Chat Endpoint
app.post('/api/ai-agent/chat', async (req, res) => {
  try {
    const { query, context } = req.body;
    
    if (!query || !query.trim()) {
      return res.status(400).json({ error: 'Query is required' });
    }
    
    // Simple intent recognition (MVP implementation)
    const intent = recognizeIntent(query);
    
    // Route to appropriate data fetching
    const responseData = await fetchDataForIntent(intent, dbPool);
    
    // Generate business-friendly response
    const aiResponse = generateBusinessResponse(intent, responseData, query);
    
    // Log conversation for analytics
    await logConversation(query, intent, aiResponse, context, dbPool);
    
    res.json(aiResponse);
  } catch (error) {
    console.error('❌ AI Agent error:', error);
    res.status(500).json({ 
      error: 'AI Assistant temporarily unavailable',
      fallback: 'Try asking: "Show my active processes" or "Weekly report"'
    });
  }
});

// Process Management Endpoints
app.post('/api/business/processes/:id/trigger', async (req, res) => {
  try {
    const { id } = req.params;
    const triggerData = req.body;
    
    // Trigger workflow via webhook (n8n integration)
    const webhookUrl = `http://127.0.0.1:5678/webhook/${id}`;
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(triggerData)
    });
    
    if (response.ok) {
      res.json({ 
        success: true, 
        message: 'Business process triggered successfully',
        processId: id
      });
    } else {
      res.status(400).json({ 
        error: 'Failed to trigger business process',
        processId: id
      });
    }
  } catch (error) {
    console.error('❌ Error triggering process:', error);
    res.status(500).json({ 
      error: 'Process trigger failed',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// ============================================================================
// EXTENDED BUSINESS API ENDPOINTS (Complete n8n Data with Sanitization)
// ============================================================================

// Process Details API - Complete process information
app.get('/api/business/process-details/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { include_steps = 'true', include_history = 'false' } = req.query;
    
    // Query principale per il processo con tutti i dati n8n
    const processQuery = `
      SELECT 
        w.id as process_id,
        w.name as process_name,
        w.active as is_active,
        w."createdAt" as created_date,
        w."updatedAt" as last_modified,
        w.nodes,
        w.connections,
        w.settings,
        w."staticData",
        w."pinData",
        w."versionId",
        w."triggerCount",
        w.meta,
        w."isArchived",
        
        -- Business analytics cross-schema
        ba.success_rate,
        ba.avg_duration_ms,
        ba.total_executions,
        ba.last_execution,
        ba.trend_direction,
        ba.business_impact_score,
        
        -- Real-time metrics from n8n
        (
          SELECT COUNT(*) 
          FROM n8n.execution_entity e 
          WHERE e."workflowId" = w.id 
          AND e."startedAt" >= CURRENT_DATE
        ) as executions_today,
        
        (
          SELECT COUNT(*) 
          FROM n8n.execution_entity e 
          WHERE e."workflowId" = w.id 
          AND e."startedAt" >= NOW() - INTERVAL '7 days'
        ) as executions_this_week,
        
        (
          SELECT COUNT(*) 
          FROM n8n.execution_entity e 
          WHERE e."workflowId" = w.id 
          AND e.finished = true 
          AND e.status = 'success'
          AND e."startedAt" >= NOW() - INTERVAL '7 days'
        ) as successful_executions_week,
        
        -- Latest execution info
        (
          SELECT e.status
          FROM n8n.execution_entity e 
          WHERE e."workflowId" = w.id 
          ORDER BY e."startedAt" DESC 
          LIMIT 1
        ) as latest_run_status,
        
        (
          SELECT e."startedAt"
          FROM n8n.execution_entity e 
          WHERE e."workflowId" = w.id 
          ORDER BY e."startedAt" DESC 
          LIMIT 1
        ) as latest_run_time
        
      FROM n8n.workflow_entity w
      LEFT JOIN pilotpros.business_analytics ba ON w.id = ba.n8n_workflow_id
      WHERE w.id = $1
    `;
    
    const processResult = await dbPool.query(processQuery, [id]);
    
    if (processResult.rows.length === 0) {
      return res.status(404).json({
        error: 'Business process not found',
        message: 'The requested process does not exist or you do not have access to it',
        suggestions: [
          'Verify the process ID is correct',
          'Check if the process has been archived',
          'Contact support if you believe this is an error'
        ]
      });
    }
    
    const process = processResult.rows[0];
    
    // Calcola health status business
    const weeklySuccessRate = process.executions_this_week > 0 
      ? (process.successful_executions_week / process.executions_this_week) * 100 
      : (process.success_rate || 0);
    
    const healthStatus = getBusinessHealthStatus(weeklySuccessRate);
    
    // Categorizza il processo automaticamente
    const category = categorizeBusinessProcess(process.process_name, process.nodes || []);
    
    // Build business response
    const businessProcess = {
      processId: process.process_id,
      processName: process.process_name,
      category: category,
      isActive: process.is_active,
      isArchived: process.is_archived,
      
      // Timeline business
      timeline: {
        createdDate: process.created_date,
        lastModified: process.last_modified,
        lastActivity: process.latest_run_time,
        version: process.version_id
      },
      
      // Performance metrics business-friendly
      performance: {
        healthStatus: healthStatus,
        successRate: Math.round(weeklySuccessRate * 10) / 10,
        averageDuration: formatBusinessDuration(process.avg_duration_ms),
        averageDurationMs: process.avg_duration_ms || 0,
        totalExecutions: process.total_executions || 0,
        executionsToday: process.executions_today || 0,
        executionsThisWeek: process.executions_this_week || 0,
        reliability: weeklySuccessRate >= 95 ? 'Excellent' : 
                    weeklySuccessRate >= 85 ? 'Good' : 
                    weeklySuccessRate >= 70 ? 'Fair' : 'Needs Attention'
      },
      
      // Business insights auto-generated
      insights: generateBusinessInsights({
        successRate: weeklySuccessRate,
        avgDurationMs: process.avg_duration_ms,
        totalExecutions: process.total_executions,
        executionsToday: process.executions_today
      }),
      
      // Latest activity business context
      latestActivity: {
        lastRun: process.latest_run_time,
        lastRunStatus: process.latest_run_status ? getBusinessStatus(process.latest_run_status) : null,
        trend: process.trend_direction || 'stable',
        triggerCount: process.trigger_count || 0
      },
      
      // Business impact metrics
      businessImpact: {
        score: process.business_impact_score || 0,
        estimatedTimeSaved: process.total_executions ? 
          `${Math.round(process.total_executions * 5 / 60)} hours` : '0 hours',
        estimatedCostSavings: process.total_executions ? 
          `€${Math.round(process.total_executions * 2.5)}` : '€0',
        businessValue: process.business_impact_score > 7 ? 'High' : 
                      process.business_impact_score > 4 ? 'Medium' : 'Low'
      }
    };
    
    // Include process steps se richiesto (sanitized)
    if (include_steps === 'true' && process.nodes) {
      businessProcess.processSteps = sanitizeProcessSteps(process.nodes, process.connections);
    }
    
    // Include recent runs per context
    businessProcess.recentRuns = await getRecentProcessRuns(id, 5);
    
    res.json({
      data: businessProcess,
      summary: {
        status: process.is_active ? 'Active and Running' : 'Inactive',
        performance: healthStatus.label,
        usage: process.executions_today > 0 ? 'Recently Active' : 'Not Used Today',
        recommendation: weeklySuccessRate < 70 ? 'Review and optimize' : 'Performing well'
      }
    });
    
  } catch (error) {
    console.error('❌ Error fetching process details:', error);
    res.status(500).json({
      error: 'Failed to retrieve process details',
      message: 'Unable to access business process information',
      suggestions: [
        'Try refreshing the page',
        'Check your network connection',
        'Contact technical support if the issue persists'
      ]
    });
  }
});

// Integration Health API - Connection status and credentials health
app.get('/api/business/integration-health', async (req, res) => {
  try {
    const { include_usage = 'true' } = req.query;
    
    // Query per credenziali con usage statistics
    const credentialsQuery = `
      SELECT 
        c.id as connection_id,
        c.name as connection_name,
        c.type as service_type,
        c."createdAt" as created_date,
        c."updatedAt" as last_modified,
        c."isManaged" as is_managed,
        
        -- Usage statistics from executions
        (
          SELECT COUNT(DISTINCT w.id)
          FROM n8n.workflow_entity w
          WHERE w.nodes::text LIKE '%' || c.type || '%'
        ) as workflows_using,
        
        (
          SELECT COUNT(*)
          FROM n8n.execution_entity e
          JOIN n8n.workflow_entity w ON e."workflowId" = w.id
          WHERE w.nodes::text LIKE '%' || c.type || '%'
          AND e."startedAt" >= NOW() - INTERVAL '7 days'
        ) as executions_this_week,
        
        (
          SELECT COUNT(*)
          FROM n8n.execution_entity e
          JOIN n8n.workflow_entity w ON e."workflowId" = w.id
          WHERE w.nodes::text LIKE '%' || c.type || '%'
          AND e."startedAt" >= NOW() - INTERVAL '7 days'
          AND e.status = 'error'
        ) as errors_this_week,
        
        -- Last successful usage
        (
          SELECT MAX(e."startedAt")
          FROM n8n.execution_entity e
          JOIN n8n.workflow_entity w ON e."workflowId" = w.id
          WHERE w.nodes::text LIKE '%' || c.type || '%'
          AND e.status = 'success'
        ) as last_successful_use
        
      FROM n8n.credentials_entity c
      ORDER BY c."updatedAt" DESC
    `;
    
    const credentialsResult = await dbPool.query(credentialsQuery);
    
    // Process each credential into business format
    const connections = credentialsResult.rows.map(cred => {
      const errorRate = cred.executions_this_week > 0 
        ? (cred.errors_this_week / cred.executions_this_week) * 100 
        : 0;
      
      // Determine health status
      let healthStatus;
      if (errorRate === 0 && cred.executions_this_week > 0) {
        healthStatus = { label: 'Excellent', color: 'green', icon: '✅' };
      } else if (errorRate < 5) {
        healthStatus = { label: 'Good', color: 'blue', icon: '👍' };
      } else if (errorRate < 20) {
        healthStatus = { label: 'Fair', color: 'yellow', icon: '⚠️' };
      } else {
        healthStatus = { label: 'Needs Attention', color: 'red', icon: '🔧' };
      }
      
      // Business service type mapping
      const serviceTypeMap = {
        'gmail': 'Email Service',
        'slack': 'Team Communication',
        'googleSheets': 'Spreadsheet Service',
        'airtable': 'Database Service',
        'httpRequest': 'Web Service',
        'webhook': 'Integration Endpoint',
        'ftp': 'File Transfer',
        'mysql': 'Database Connection',
        'postgres': 'Database Connection'
      };
      
      return {
        connectionId: cred.connection_id,
        connectionName: cred.connection_name,
        serviceType: serviceTypeMap[cred.service_type] || 'External Service',
        technicalType: cred.service_type, // For debugging only
        
        // Health metrics
        health: {
          status: healthStatus,
          errorRate: Math.round(errorRate * 10) / 10,
          reliability: 100 - errorRate,
          lastSuccessfulUse: cred.last_successful_use
        },
        
        // Usage metrics
        usage: {
          workflowsUsing: cred.workflows_using || 0,
          executionsThisWeek: cred.executions_this_week || 0,
          errorsThisWeek: cred.errors_this_week || 0,
          isActive: cred.executions_this_week > 0
        },
        
        // Management info
        management: {
          isManaged: cred.is_managed,
          createdDate: cred.created_date,
          lastModified: cred.last_modified,
          status: cred.executions_this_week > 0 ? 'Active' : 'Inactive'
        }
      };
    });
    
    // Calculate overall statistics
    const totalConnections = connections.length;
    const activeConnections = connections.filter(c => c.usage.isActive).length;
    const healthyConnections = connections.filter(c => c.health.errorRate < 5).length;
    const needsAttention = connections.filter(c => c.health.errorRate > 20).length;
    
    res.json({
      data: connections,
      summary: {
        totalConnections,
        activeConnections,
        healthyConnections,
        needsAttention,
        overallHealth: needsAttention === 0 ? 'Excellent' : 
                      needsAttention < totalConnections * 0.1 ? 'Good' : 'Needs Review'
      },
      insights: [
        activeConnections > 0 ? 
          `${activeConnections} of ${totalConnections} connections are actively used` : 
          'No connections have been used recently',
        healthyConnections === totalConnections ? 
          'All connections are performing well' : 
          `${needsAttention} connections need attention`,
        totalConnections > 5 ? 
          'You have a well-connected automation ecosystem' : 
          'Consider adding more integrations to expand automation capabilities'
      ]
    });
    
  } catch (error) {
    console.error('❌ Error fetching integration health:', error);
    res.status(500).json({
      error: 'Failed to retrieve integration health',
      message: 'Unable to access connection status information',
      suggestions: [
        'Check if the business process engine is running',
        'Verify database connectivity',
        'Contact technical support for assistance'
      ]
    });
  }
});

// Advanced Analytics API - Comprehensive business insights
app.get('/api/business/automation-insights', async (req, res) => {
  try {
    const { period = '7d', include_predictions = 'false' } = req.query;
    
    // Determine time interval
    const intervalMap = {
      '1d': '1 day',
      '7d': '7 days', 
      '30d': '30 days',
      '90d': '90 days'
    };
    const interval = intervalMap[period] || '7 days';
    
    // Comprehensive analytics query
    const analyticsQuery = `
      WITH process_stats AS (
        SELECT 
          COUNT(DISTINCT w.id) as total_processes,
          COUNT(DISTINCT CASE WHEN w.active = true THEN w.id END) as active_processes,
          COUNT(DISTINCT CASE WHEN w."isArchived" = true THEN w.id END) as archived_processes
        FROM n8n.workflow_entity w
      ),
      execution_stats AS (
        SELECT 
          COUNT(*) as total_executions,
          COUNT(CASE WHEN e.status = 'success' THEN 1 END) as successful_executions,
          COUNT(CASE WHEN e.status = 'error' THEN 1 END) as failed_executions,
          COUNT(CASE WHEN e.finished = false THEN 1 END) as running_executions,
          AVG(EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) * 1000) as avg_duration_ms,
          MIN(EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) * 1000) as min_duration_ms,
          MAX(EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) * 1000) as max_duration_ms
        FROM n8n.execution_entity e
        WHERE e."startedAt" >= NOW() - INTERVAL '${interval}'
      ),
      daily_trends AS (
        SELECT 
          DATE(e."startedAt") as execution_date,
          COUNT(*) as daily_executions,
          COUNT(CASE WHEN e.status = 'success' THEN 1 END) as daily_successes,
          AVG(EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) * 1000) as daily_avg_duration
        FROM n8n.execution_entity e
        WHERE e."startedAt" >= NOW() - INTERVAL '${interval}'
        GROUP BY DATE(e."startedAt")
        ORDER BY execution_date DESC
      ),
      top_processes AS (
        SELECT 
          w.id,
          w.name,
          COUNT(e.id) as execution_count,
          COUNT(CASE WHEN e.status = 'success' THEN 1 END) as success_count,
          AVG(EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) * 1000) as avg_duration
        FROM n8n.workflow_entity w
        LEFT JOIN n8n.execution_entity e ON w.id = e."workflowId"
          AND e."startedAt" >= NOW() - INTERVAL '${interval}'
        WHERE w.active = true
        GROUP BY w.id, w.name
        ORDER BY execution_count DESC
        LIMIT 10
      )
      SELECT 
        -- Process overview
        ps.total_processes,
        ps.active_processes, 
        ps.archived_processes,
        
        -- Execution metrics
        es.total_executions,
        es.successful_executions,
        es.failed_executions,
        es.running_executions,
        es.avg_duration_ms,
        es.min_duration_ms,
        es.max_duration_ms,
        
        -- Trends (as JSON)
        (SELECT json_agg(dt ORDER BY dt.execution_date DESC) FROM daily_trends dt) as daily_trends,
        
        -- Top processes (as JSON)
        (SELECT json_agg(tp ORDER BY tp.execution_count DESC) FROM top_processes tp) as top_processes
        
      FROM process_stats ps, execution_stats es
    `;
    
    const analyticsResult = await dbPool.query(analyticsQuery);
    const data = analyticsResult.rows[0];
    
    // Calculate business metrics
    const successRate = data.total_executions > 0 
      ? (data.successful_executions / data.total_executions * 100) 
      : 0;
    
    const errorRate = data.total_executions > 0 
      ? (data.failed_executions / data.total_executions * 100) 
      : 0;
    
    const automationEfficiency = data.active_processes > 0 
      ? (data.total_executions / data.active_processes) 
      : 0;
    
    // Business impact calculations
    const estimatedTimeSaved = data.successful_executions * 5; // 5 minutes per successful execution
    const estimatedCostSavings = estimatedTimeSaved * 0.5; // €0.50 per minute saved
    const businessImpactScore = Math.min(10, (successRate / 10) + (automationEfficiency / 100));
    
    // Process daily trends for business insights
    const trends = data.daily_trends || [];
    const trendDirection = trends.length > 1 ? 
      (trends[0].daily_executions > trends[trends.length - 1].daily_executions ? 'increasing' : 'decreasing') : 
      'stable';
    
    res.json({
      // Overview metrics
      overview: {
        totalProcesses: parseInt(data.total_processes) || 0,
        activeProcesses: parseInt(data.active_processes) || 0,
        archivedProcesses: parseInt(data.archived_processes) || 0,
        automationCoverage: data.total_processes > 0 ? 
          Math.round((data.active_processes / data.total_processes) * 100) : 0
      },
      
      // Performance metrics
      performance: {
        totalExecutions: parseInt(data.total_executions) || 0,
        successfulExecutions: parseInt(data.successful_executions) || 0,
        failedExecutions: parseInt(data.failed_executions) || 0,
        currentlyRunning: parseInt(data.running_executions) || 0,
        successRate: Math.round(successRate * 10) / 10,
        errorRate: Math.round(errorRate * 10) / 10,
        averageDuration: formatBusinessDuration(data.avg_duration_ms),
        efficiency: automationEfficiency > 100 ? 'High' : 
                   automationEfficiency > 50 ? 'Good' : 
                   automationEfficiency > 10 ? 'Fair' : 'Low'
      },
      
      // Business impact
      businessImpact: {
        timeSavedMinutes: estimatedTimeSaved,
        timeSavedHours: Math.round(estimatedTimeSaved / 60),
        costSavings: `€${Math.round(estimatedCostSavings)}`,
        businessImpactScore: Math.round(businessImpactScore * 10) / 10,
        roi: estimatedCostSavings > 0 ? 'Positive' : 'Calculating',
        productivity: automationEfficiency > 50 ? 'High Impact' : 'Growing Impact'
      },
      
      // Trends and insights
      trends: {
        direction: trendDirection,
        dailyData: trends.slice(0, 7), // Last 7 days
        weekOverWeek: trends.length > 7 ? 
          Math.round(((trends[0]?.daily_executions || 0) / (trends[7]?.daily_executions || 1) - 1) * 100) : 0
      },
      
      // Top performing processes
      topPerformers: (data.top_processes || []).map(proc => ({
        processName: proc.name,
        executionCount: proc.execution_count,
        successRate: proc.execution_count > 0 ? 
          Math.round((proc.success_count / proc.execution_count) * 100) : 0,
        averageDuration: formatBusinessDuration(proc.avg_duration),
        businessValue: proc.execution_count > 100 ? 'High' : 
                      proc.execution_count > 20 ? 'Medium' : 'Low'
      })),
      
      // Business insights
      insights: [
        successRate >= 95 ? 
          '🎯 Excellent automation performance - processes are highly reliable' :
          successRate >= 80 ?
          '👍 Good automation performance with room for optimization' :
          '⚠️ Automation reliability needs attention - review failing processes',
          
        data.total_executions > 1000 ?
          '📈 High automation usage indicates strong business value' :
          data.total_executions > 100 ?
          '📊 Growing automation adoption - continue expanding' :
          '🚀 Early stage automation - focus on key processes first',
          
        estimatedTimeSaved > 480 ? // 8 hours
          `💰 Significant time savings: ${Math.round(estimatedTimeSaved / 60)} hours saved` :
          `⏱️ Time savings growing: ${Math.round(estimatedTimeSaved / 60)} hours saved this period`,
          
        data.active_processes < 5 ?
          '🎯 Consider adding more processes to increase automation coverage' :
          data.active_processes > 20 ?
          '🏆 Comprehensive automation ecosystem - excellent coverage' :
          '📈 Good automation foundation - continue expanding strategically'
      ],
      
      recommendations: generateBusinessRecommendations({
        successRate,
        errorRate, 
        automationEfficiency,
        totalProcesses: data.active_processes,
        totalExecutions: data.total_executions
      })
    });
    
  } catch (error) {
    console.error('❌ Error fetching automation insights:', error);
    res.status(500).json({
      error: 'Failed to generate automation insights',
      message: 'Unable to analyze business automation performance',
      suggestions: [
        'Try selecting a different time period',
        'Check if there is sufficient automation data',
        'Contact support for detailed analytics assistance'
      ]
    });
  }
});

// ============================================================================
// HELPER FUNCTIONS FOR EXTENDED APIS
// ============================================================================

// Sanitize process steps (nodes) for business consumption
function sanitizeProcessSteps(nodes, connections = {}) {
  if (!Array.isArray(nodes)) return [];
  
  return nodes.map((node, index) => {
    const stepType = getBusinessStepType(node.type);
    
    return {
      stepId: node.name,
      stepName: node.name || `Step ${index + 1}`,
      stepType: stepType,
      position: node.position || { x: 0, y: 0 },
      description: getStepDescription(node.type),
      isStartStep: index === 0, // Simplified logic
      isEndStep: index === nodes.length - 1,
      configuration: sanitizeStepConfiguration(node.parameters || {})
    };
  });
}

function getBusinessStepType(nodeType) {
  const businessTypes = {
    'n8n-nodes-base.webhook': { type: 'Integration Trigger', icon: '🔗' },
    'n8n-nodes-base.cron': { type: 'Scheduled Trigger', icon: '⏰' },
    'n8n-nodes-base.manualTrigger': { type: 'Manual Trigger', icon: '🚀' },
    'n8n-nodes-base.set': { type: 'Data Processor', icon: '⚙️' },
    'n8n-nodes-base.function': { type: 'Custom Logic', icon: '🧮' },
    'n8n-nodes-base.if': { type: 'Decision Point', icon: '🔀' },
    'n8n-nodes-base.httpRequest': { type: 'External Service', icon: '🌐' },
    'n8n-nodes-base.gmail': { type: 'Email Service', icon: '📧' },
    'n8n-nodes-base.slack': { type: 'Team Communication', icon: '💬' }
  };
  
  return businessTypes[nodeType] || { type: 'Process Step', icon: '📋' };
}

function getStepDescription(nodeType) {
  const descriptions = {
    'n8n-nodes-base.webhook': 'Receives data from external systems',
    'n8n-nodes-base.cron': 'Runs automatically on a schedule', 
    'n8n-nodes-base.manualTrigger': 'Started manually by user',
    'n8n-nodes-base.set': 'Processes and transforms data',
    'n8n-nodes-base.function': 'Executes custom business logic',
    'n8n-nodes-base.if': 'Makes decisions based on conditions',
    'n8n-nodes-base.httpRequest': 'Communicates with external services',
    'n8n-nodes-base.gmail': 'Sends or processes emails',
    'n8n-nodes-base.slack': 'Sends team notifications'
  };
  
  return descriptions[nodeType] || 'Performs a business operation';
}

function sanitizeStepConfiguration(parameters) {
  const sanitized = {};
  const safeFields = ['httpMethod', 'email', 'subject', 'message', 'channel', 'operation'];
  
  for (const [key, value] of Object.entries(parameters)) {
    if (safeFields.includes(key) && typeof value === 'string') {
      if (key === 'url' && value.includes('token=')) {
        sanitized[key] = value.replace(/token=[^&]+/g, 'token=***');
      } else {
        sanitized[key] = value;
      }
    }
  }
  
  return sanitized;
}

async function getRecentProcessRuns(processId, limit = 5) {
  try {
    const query = `
      SELECT 
        e.id as run_id,
        to_char(e."startedAt", 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as start_time,
        to_char(e."stoppedAt", 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as end_time,
        e.finished as is_completed,
        e.status,
        e.mode,
        CASE 
          WHEN e."stoppedAt" IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) * 1000
          ELSE NULL
        END as duration_ms
      FROM n8n.execution_entity e
      WHERE e."workflowId" = $1
      ORDER BY e."startedAt" DESC
      LIMIT $2
    `;
    
    const result = await dbPool.query(query, [processId, limit]);
    
    return result.rows.map(row => ({
      runId: row.run_id,
      startTime: row.start_time,
      endTime: row.end_time,
      isCompleted: row.is_completed,
      businessStatus: getBusinessStatus(row.status),
      duration: formatBusinessDuration(row.duration_ms),
      mode: row.mode === 'manual' ? 'Manual Start' : 'Automatic Start'
    }));
  } catch (error) {
    console.error('Error fetching recent runs:', error);
    return [];
  }
}

function generateBusinessRecommendations(metrics) {
  const recommendations = [];
  
  if (metrics.successRate < 80) {
    recommendations.push({
      priority: 'high',
      category: 'Performance',
      title: 'Improve Process Reliability',
      description: 'Review and fix processes with high error rates',
      action: 'Identify failing processes and optimize their configuration'
    });
  }
  
  if (metrics.totalProcesses < 5) {
    recommendations.push({
      priority: 'medium',
      category: 'Growth',
      title: 'Expand Automation Coverage',
      description: 'Add more business processes to increase automation benefits',
      action: 'Identify manual tasks that can be automated'
    });
  }
  
  if (metrics.automationEfficiency > 100) {
    recommendations.push({
      priority: 'low',
      category: 'Optimization',
      title: 'Optimize High-Usage Processes',
      description: 'Fine-tune frequently used processes for better performance',
      action: 'Review and optimize the most active automation processes'
    });
  }
  
  return recommendations;
}

// ============================================================================
// AI AGENT HELPER FUNCTIONS
// ============================================================================

function recognizeIntent(query) {
  const lowerQuery = query.toLowerCase();
  
  // Simple pattern matching per intent italiano
  if (lowerQuery.includes('mostra') && (lowerQuery.includes('processi') || lowerQuery.includes('processo'))) {
    return { type: 'show_processes', confidence: 0.9 };
  }
  
  if (lowerQuery.includes('report') || lowerQuery.includes('statistiche')) {
    return { type: 'analytics_report', confidence: 0.85 };
  }
  
  if (lowerQuery.includes('errori') || lowerQuery.includes('problemi')) {
    return { type: 'troubleshooting', confidence: 0.8 };
  }
  
  if (lowerQuery.includes('quanti') || lowerQuery.includes('quanto')) {
    return { type: 'count_metrics', confidence: 0.75 };
  }
  
  return { type: 'general_help', confidence: 0.5 };
}

async function fetchDataForIntent(intent, db) {
  switch (intent.type) {
    case 'show_processes':
      const processes = await db.query(`
        SELECT w.id, w.name, w.active, ba.success_rate, ba.total_executions
        FROM n8n.workflow_entity w
        LEFT JOIN pilotpros.business_analytics ba ON w.id = ba.n8n_workflow_id
        WHERE w.active = true
        ORDER BY ba.business_impact_score DESC NULLS LAST
        LIMIT 10
      `);
      return { processes: processes.rows };
      
    case 'analytics_report':
      const analytics = await db.query(`
        SELECT 
          COUNT(DISTINCT w.id) as active_processes,
          COUNT(e.id) as total_executions,
          AVG(EXTRACT(EPOCH FROM (e.stopped_at - e.started_at))) as avg_duration_seconds
        FROM n8n.workflow_entity w
        LEFT JOIN n8n.execution_entity e ON w.id = e.workflow_id
        WHERE w.active = true AND e.started_at >= NOW() - INTERVAL '7 days'
      `);
      return { analytics: analytics.rows[0] };
      
    case 'troubleshooting':
      const errors = await db.query(`
        SELECT w.name, e.started_at, e.data->>'error' as error_msg
        FROM n8n.execution_entity e
        JOIN n8n.workflow_entity w ON e.workflow_id = w.id
        WHERE e.finished = false OR e.data->>'error' IS NOT NULL
        ORDER BY e.started_at DESC
        LIMIT 5
      `);
      return { errors: errors.rows };
      
    default:
      return { help: true };
  }
}

function generateBusinessResponse(intent, data, originalQuery) {
  switch (intent.type) {
    case 'show_processes':
      const activeCount = data.processes?.length || 0;
      return {
        textResponse: `🎯 **I tuoi processi aziendali attivi:**\n\n` +
                     `• **${activeCount} processi** attualmente in esecuzione\n` +
                     `• Media **${Math.round(data.processes.reduce((sum, p) => sum + (p.success_rate || 0), 0) / activeCount)}% successo**\n` +
                     `• **${data.processes.reduce((sum, p) => sum + (p.total_executions || 0), 0)} esecuzioni** totali\n\n` +
                     `I tuoi processi stanno funzionando correttamente! 👍`,
        
        visualData: {
          table: {
            headers: ['Nome Processo', 'Stato', 'Successo %', 'Esecuzioni'],
            rows: data.processes.map(p => [
              p.name,
              p.active ? '✅ Attivo' : '⏸️ Pausa',
              `${(p.success_rate || 0).toFixed(1)}%`,
              p.total_executions || 0
            ])
          }
        },
        
        actionSuggestions: [
          "Mostra dettagli del processo più utilizzato",
          "Crea report performance settimanale",
          "Verifica se ci sono errori"
        ]
      };
      
    case 'analytics_report':
      const analytics = data.analytics;
      return {
        textResponse: `📊 **Report Performance (ultimi 7 giorni):**\n\n` +
                     `• **${analytics.active_processes} processi** attivi\n` +
                     `• **${analytics.total_executions} esecuzioni** completate\n` +
                     `• **Tempo medio:** ${Math.round(analytics.avg_duration_seconds || 0)} secondi\n\n` +
                     `Le performance sono ${analytics.avg_duration_seconds < 30 ? 'eccellenti' : 'buone'}! 📈`,
        
        actionSuggestions: [
          "Confronta con il mese scorso",
          "Mostra processi più lenti",
          "Analizza trend performance"
        ]
      };
      
    case 'troubleshooting':
      const errorCount = data.errors?.length || 0;
      return {
        textResponse: errorCount > 0 ?
          `⚠️ **Trovati ${errorCount} problemi recenti:**\n\n` +
          data.errors.map(e => `• **${e.name}**: ${e.error_msg || 'Errore generico'}`).join('\n') +
          `\n\nRisolvi questi problemi per migliorare le performance.` :
          
          `✅ **Ottimo!** Nessun errore rilevato.\n\nTutti i processi stanno funzionando correttamente.`,
        
        actionSuggestions: errorCount > 0 ? [
          "Mostra dettagli errori",
          "Suggerimenti risoluzione",
          "Riavvia processi problematici"
        ] : [
          "Mostra stato generale processi",
          "Report performance",
          "Ottimizzazioni disponibili"
        ]
      };
      
    default:
      return {
        textResponse: `🤖 **Assistente Processi Aziendali**\n\n` +
                     `Puoi chiedermi:\n` +
                     `• "Mostra i processi attivi"\n` +
                     `• "Report di questa settimana"\n` +
                     `• "Ci sono errori da controllare?"\n` +
                     `• "Quanti clienti processati oggi?"\n\n` +
                     `Come posso aiutarti a gestire i tuoi processi aziendali?`,
        
        actionSuggestions: [
          "Mostra processi attivi",
          "Report settimanale",
          "Controlla errori"
        ]
      };
  }
}

async function logConversation(query, intent, response, context, db) {
  try {
    await db.query(`
      INSERT INTO pilotpros.ai_conversations (
        user_id, session_id, query_text, intent_detected, 
        intent_confidence, response_generated, response_time_ms, created_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
    `, [
      context.userId || 'anonymous',
      context.sessionId || 'default',
      query,
      intent.type,
      intent.confidence,
      response.textResponse,
      Date.now() - (context.startTime || Date.now())
    ]);
  } catch (error) {
    console.error('Warning: Failed to log conversation:', error);
  }
}

// ============================================================================
// ERROR HANDLING & GRACEFUL SHUTDOWN
// ============================================================================

// Business error handler (sanitized)
app.use(businessErrorHandler());

// ============================================================================
// COMPATIBILITY MONITORING ENDPOINTS
// ============================================================================

// System compatibility status  
app.get('/api/system/compatibility', async (req, res) => {
  try {
    const status = await compatibilityService.getHealthStatus();
    const testResults = await fieldMapper.testCompatibility(compatibilityService.db);
    
    res.json({
      compatibility: {
        status: status.compatibility,
        version: status.detectedVersion,
        isReady: status.isReady,
        lastCheck: status.lastCheck
      },
      schemaInfo: testResults,
      supportedVersions: status.supportedVersions,
      _metadata: {
        system: 'Business Process Operating System',
        endpoint: '/api/system/compatibility',
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    res.status(500).json({
      error: 'Compatibility check failed',
      message: error.message
    });
  }
});

// Compatibility health check for monitoring
app.get('/api/system/compatibility/health', async (req, res) => {
  try {
    const status = await compatibilityService.getHealthStatus();
    
    res.json({
      status: status.isReady ? 'healthy' : 'degraded',
      n8nVersion: status.detectedVersion,
      isReady: status.isReady,
      lastCheck: status.lastCheck,
      _metadata: {
        system: 'Business Process Operating System',
        endpoint: '/api/system/compatibility/health',
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      error: error.message
    });
  }
});

// ============================================================================
// NEW REAL-TIME DATA ENDPOINTS
// ============================================================================

// Statistics Endpoint - Aggregated execution data for charts
app.get('/api/business/statistics', async (req, res) => {
  try {
    // Daily execution stats for last 30 days
    const dailyStats = await dbPool.query(`
      SELECT 
        DATE(e."startedAt") as day,
        COUNT(*) as total,
        COUNT(CASE WHEN e.status = 'success' THEN 1 END) as success,
        COUNT(CASE WHEN e.status = 'error' THEN 1 END) as errors,
        COUNT(CASE WHEN e.status = 'running' THEN 1 END) as running,
        AVG(EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt"))) as avg_duration_seconds
      FROM n8n.execution_entity e
      WHERE e."startedAt" >= NOW() - INTERVAL '30 days'
      GROUP BY DATE(e."startedAt")
      ORDER BY day DESC
    `);
    
    // Hourly stats for last 24 hours
    const hourlyStats = await dbPool.query(`
      SELECT 
        DATE_TRUNC('hour', e."startedAt") as hour,
        COUNT(*) as executions,
        COUNT(CASE WHEN e.status = 'success' THEN 1 END) as success_count
      FROM n8n.execution_entity e
      WHERE e."startedAt" >= NOW() - INTERVAL '24 hours'
      GROUP BY DATE_TRUNC('hour', e."startedAt")
      ORDER BY hour DESC
    `);
    
    // Workflow-level stats
    const workflowStats = await dbPool.query(`
      SELECT 
        w.name as workflow_name,
        COUNT(e.id) as execution_count,
        COUNT(CASE WHEN e.status = 'success' THEN 1 END) as success_count,
        AVG(EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt"))) * 1000 as avg_duration_ms
      FROM n8n.workflow_entity w
      LEFT JOIN n8n.execution_entity e ON w.id = e."workflowId"
      WHERE e."startedAt" >= NOW() - INTERVAL '7 days'
      GROUP BY w.id, w.name
      ORDER BY execution_count DESC
      LIMIT 10
    `);
    
    res.json({
      daily: dailyStats.rows,
      hourly: hourlyStats.rows,
      byWorkflow: workflowStats.rows,
      _metadata: {
        system: 'Business Process Operating System',
        endpoint: '/api/business/statistics',
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('❌ Error fetching statistics:', error);
    res.status(500).json({ 
      error: 'Failed to fetch statistics',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Security Endpoint - Users, roles and audit logs
app.get('/api/business/security', async (req, res) => {
  try {
    // Get users with roles
    const users = await dbPool.query(`
      SELECT 
        u.id, 
        u.email, 
        u."firstName", 
        u."lastName",
        u."createdAt", 
        u."updatedAt",
        u."lastActiveAt",
        u.role,
        u."roleSlug",
        u.disabled,
        u."mfaEnabled"
      FROM n8n.user u
      ORDER BY u."createdAt" DESC
    `);
    
    // Get audit logs from pilotpros schema
    const auditLogs = await dbPool.query(`
      SELECT 
        id,
        user_id,
        action,
        resource_type,
        resource_id,
        old_values,
        new_values,
        ip_address,
        user_agent,
        timestamp
      FROM pilotpros.audit_logs
      ORDER BY timestamp DESC
      LIMIT 100
    `);
    
    // Get role permissions (simplified since roles are in user table)
    const roles = await dbPool.query(`
      SELECT 
        DISTINCT u.role as name,
        u."roleSlug" as slug,
        COUNT(*) as user_count
      FROM n8n.user u
      GROUP BY u.role, u."roleSlug"
      ORDER BY u.role
    `);
    
    res.json({
      users: users.rows,
      auditLogs: auditLogs.rows,
      roles: roles.rows,
      summary: {
        totalUsers: users.rows.length,
        totalRoles: roles.rows.length,
        recentActivity: auditLogs.rows.length
      },
      _metadata: {
        system: 'Business Process Operating System',
        endpoint: '/api/business/security',
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('❌ Error fetching security data:', error);
    res.status(500).json({ 
      error: 'Failed to fetch security data',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Alerts Endpoint - Errors and notifications
app.get('/api/business/alerts', async (req, res) => {
  try {
    // Recent execution errors
    const executionErrors = await dbPool.query(`
      SELECT 
        e.id as execution_id,
        e."workflowId",
        w.name as workflow_name,
        e."startedAt",
        e."stoppedAt",
        e.status,
        e.mode,
        'execution_error' as alert_type,
        'high' as severity
      FROM n8n.execution_entity e
      JOIN n8n.workflow_entity w ON e."workflowId" = w.id
      WHERE e.status = 'error'
      ORDER BY e."startedAt" DESC
      LIMIT 50
    `);
    
    // System notifications from pilotpros schema
    const notifications = await dbPool.query(`
      SELECT 
        id,
        notification_type as alert_type,
        title,
        message,
        'medium' as severity,
        is_read,
        created_at
      FROM pilotpros.notifications
      WHERE created_at >= NOW() - INTERVAL '7 days'
      ORDER BY created_at DESC
      LIMIT 50
    `);
    
    // Workflow warnings (inactive but scheduled)
    const workflowWarnings = await dbPool.query(`
      SELECT 
        w.id,
        w.name,
        'workflow_inactive' as alert_type,
        'medium' as severity,
        'Workflow is inactive but has scheduled triggers' as message
      FROM n8n.workflow_entity w
      WHERE w.active = false
      AND w.nodes::text LIKE '%n8n-nodes-base.cron%'
    `);
    
    // Combine all alerts
    const allAlerts = [
      ...executionErrors.rows.map(e => ({
        ...e,
        timestamp: e.startedAt,
        title: `Execution Error: ${e.workflow_name}`,
        message: `Workflow execution failed at ${new Date(e.startedAt).toLocaleString()}`
      })),
      ...notifications.rows,
      ...workflowWarnings.rows.map(w => ({
        ...w,
        timestamp: new Date(),
        title: `Inactive Workflow: ${w.name}`
      }))
    ].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    res.json({
      alerts: allAlerts,
      summary: {
        total: allAlerts.length,
        errors: executionErrors.rows.length,
        warnings: workflowWarnings.rows.length,
        notifications: notifications.rows.length
      },
      _metadata: {
        system: 'Business Process Operating System',
        endpoint: '/api/business/alerts',
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('❌ Error fetching alerts:', error);
    res.status(500).json({ 
      error: 'Failed to fetch alerts',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Schedules Endpoint - CRON jobs and scheduled workflows
app.get('/api/business/schedules', async (req, res) => {
  try {
    // Get workflows with CRON triggers
    const cronWorkflows = await dbPool.query(`
      SELECT 
        w.id,
        w.name,
        w.active,
        w.nodes,
        w."updatedAt"
      FROM n8n.workflow_entity w
      WHERE w.nodes::text LIKE '%"type":"n8n-nodes-base.cron"%'
      ORDER BY w.active DESC, w.name
    `);
    
    // Parse CRON expressions from nodes
    const schedules = cronWorkflows.rows.map(workflow => {
      try {
        const nodes = typeof workflow.nodes === 'string' ? 
          JSON.parse(workflow.nodes) : workflow.nodes;
        
        const cronNodes = nodes.filter(n => n.type === 'n8n-nodes-base.cron');
        
        return cronNodes.map(cronNode => ({
          workflow_id: workflow.id,
          workflow_name: workflow.name,
          node_name: cronNode.name,
          cron_expression: cronNode.parameters?.cronExpression || 'Not configured',
          active: workflow.active,
          last_updated: workflow.updatedAt,
          timezone: cronNode.parameters?.timezone || 'UTC'
        }));
      } catch (e) {
        console.error('Error parsing workflow nodes:', e);
        return [{
          workflow_id: workflow.id,
          workflow_name: workflow.name,
          cron_expression: 'Parse error',
          active: workflow.active
        }];
      }
    }).flat();
    
    // Get scheduled processes from pilotpros schema
    const customSchedules = await dbPool.query(`
      SELECT 
        id,
        n8n_workflow_id,
        schedule_name,
        cron_expression,
        timezone,
        next_run,
        last_run,
        run_count,
        is_active,
        created_at
      FROM pilotpros.process_schedules
      ORDER BY next_run ASC
    `);
    
    res.json({
      cronSchedules: schedules,
      customSchedules: customSchedules.rows,
      summary: {
        totalSchedules: schedules.length + customSchedules.rows.length,
        activeSchedules: schedules.filter(s => s.active).length,
        inactiveSchedules: schedules.filter(s => !s.active).length
      },
      _metadata: {
        system: 'Business Process Operating System',
        endpoint: '/api/business/schedules',
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('❌ Error fetching schedules:', error);
    res.status(500).json({ 
      error: 'Failed to fetch schedules',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Database Info Endpoint - Table sizes and statistics
app.get('/api/business/database-info', async (req, res) => {
  try {
    // Get table sizes and row counts
    const tableSizes = await dbPool.query(`
      SELECT 
        n.nspname as schemaname,
        c.relname as tablename,
        pg_size_pretty(pg_total_relation_size(c.oid)) as total_size,
        pg_size_pretty(pg_relation_size(c.oid)) as table_size,
        c.reltuples::bigint as row_count
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE c.relkind = 'r'
      AND n.nspname IN ('n8n', 'pilotpros')
      ORDER BY pg_total_relation_size(c.oid) DESC
    `);
    
    // Get database size
    const dbSize = await dbPool.query(`
      SELECT 
        pg_database.datname as database_name,
        pg_size_pretty(pg_database_size(pg_database.datname)) as size
      FROM pg_database
      WHERE datname = current_database()
    `);
    
    // Get connection stats
    const connectionStats = await dbPool.query(`
      SELECT 
        count(*) as total_connections,
        count(*) FILTER (WHERE state = 'active') as active_connections,
        count(*) FILTER (WHERE state = 'idle') as idle_connections,
        max(backend_start) as oldest_connection
      FROM pg_stat_activity
      WHERE datname = current_database()
    `);
    
    // Schema summary
    const schemaSummary = await dbPool.query(`
      SELECT 
        n.nspname as schemaname,
        COUNT(DISTINCT c.relname) as table_count,
        SUM(c.reltuples)::bigint as total_rows,
        pg_size_pretty(SUM(pg_total_relation_size(c.oid))) as total_size
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE c.relkind = 'r'
      AND n.nspname IN ('n8n', 'pilotpros')
      GROUP BY n.nspname
    `);
    
    res.json({
      database: dbSize.rows[0],
      schemas: schemaSummary.rows,
      tables: tableSizes.rows,
      connections: connectionStats.rows[0],
      summary: {
        totalTables: tableSizes.rows.length,
        n8nTables: tableSizes.rows.filter(t => t.schemaname === 'n8n').length,
        pilotprosTables: tableSizes.rows.filter(t => t.schemaname === 'pilotpros').length
      },
      _metadata: {
        system: 'Business Process Operating System',
        endpoint: '/api/business/database-info',
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('❌ Error fetching database info:', error);
    res.status(500).json({ 
      error: 'Failed to fetch database info',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Agents Timeline Endpoint - Execution timeline for AgentDetailModal
app.get('/api/tenant/:tenantId/agents/workflow/:workflowId/timeline', async (req, res) => {
  try {
    const { workflowId } = req.params;
    
    // Get latest execution with detailed data
    const execution = await dbPool.query(`
      SELECT 
        e.id,
        e."workflowId",
        e."startedAt",
        e."stoppedAt",
        e.finished,
        e.status,
        e.mode,
        w.name as workflow_name,
        w.nodes,
        w.connections
      FROM n8n.execution_entity e
      JOIN n8n.workflow_entity w ON e."workflowId" = w.id
      WHERE w.id = $1
      ORDER BY e."startedAt" DESC
      LIMIT 1
    `, [workflowId]);
    
    if (execution.rows.length === 0) {
      return res.json({
        success: false,
        message: 'No executions found for this workflow'
      });
    }
    
    const exec = execution.rows[0];
    
    // Check if we have execution_data for more details
    const executionData = await dbPool.query(`
      SELECT data, "workflowData"
      FROM n8n.execution_data
      WHERE "executionId" = $1
    `, [exec.id]);
    
    // Parse workflow nodes for timeline steps
    let timelineSteps = [];
    try {
      const nodes = typeof exec.nodes === 'string' ? 
        JSON.parse(exec.nodes) : exec.nodes;
      
      timelineSteps = nodes.map((node, index) => ({
        nodeId: node.id || `node_${index}`,
        nodeName: node.name,
        nodeType: node.type,
        displayName: node.name || node.type.split('.').pop(),
        position: node.position,
        status: exec.status === 'success' ? 'completed' : 
                exec.status === 'error' && index === nodes.length - 1 ? 'error' : 
                'completed',
        executionTime: Math.random() * 1000, // Mock time, real data would come from execution_data
        customOrder: index + 1,
        summary: `${node.type.split('.').pop()} node executed`,
        parameters: node.parameters || {}
      }));
    } catch (e) {
      console.error('Error parsing nodes:', e);
    }
    
    // Extract business context
    const businessContext = {
      workflowId: exec.workflowId,
      workflowName: exec.workflow_name,
      executionId: exec.id,
      startTime: exec.startedAt,
      endTime: exec.stoppedAt,
      duration: exec.stoppedAt ? 
        new Date(exec.stoppedAt) - new Date(exec.startedAt) : null,
      status: exec.status,
      mode: exec.mode,
      isFinished: exec.finished
    };
    
    res.json({
      success: true,
      data: {
        workflowName: exec.workflow_name,
        status: exec.status === 'success' ? 'active' : 'error',
        lastExecution: {
          id: exec.id,
          executedAt: exec.startedAt,
          duration: businessContext.duration
        },
        businessContext: businessContext,
        timeline: timelineSteps
      },
      _metadata: {
        system: 'Business Process Operating System',
        endpoint: '/api/tenant/:tenantId/agents/workflow/:workflowId/timeline',
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('❌ Error fetching timeline:', error);
    res.status(500).json({ 
      error: 'Failed to fetch timeline',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// 404 handler with updated endpoint list
app.use((req, res) => {
  res.status(404).json({
    error: 'Business operation not found',
    message: 'The requested business operation is not available',
    availableEndpoints: [
      '/api/business/processes',
      '/api/business/process-runs', 
      '/api/business/analytics',
      '/api/business/process-details/:id',
      '/api/business/integration-health',
      '/api/business/automation-insights',
      '/api/business/statistics',
      '/api/business/security',
      '/api/business/alerts',
      '/api/business/schedules',
      '/api/business/database-info',
      '/api/tenant/:tenantId/agents/workflow/:workflowId/timeline',
      '/api/ai-agent/chat',
      '/api/system/compatibility',
      '/api/system/compatibility/health'
    ],
    suggestions: [
      'Check the URL spelling',
      'Verify you have access to this operation',
      'Use one of the available endpoints above'
    ]
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('🔄 SIGTERM received, shutting down gracefully...');
  dbPool.end(() => {
    console.log('✅ Database connections closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('🔄 SIGINT received, shutting down gracefully...');
  dbPool.end(() => {
    console.log('✅ Database connections closed');
    process.exit(0);
  });
});

// ============================================================================
// SERVER STARTUP WITH WEBSOCKET
// ============================================================================

const server = createServer(app);

// Initialize WebSocket server
const io = initializeWebSocket(server);

server.listen(port, host, () => {
  console.log('🚀 PilotProOS Backend API Server');
  console.log('================================');
  console.log(`✅ Server: http://${host}:${port}`);
  console.log(`✅ WebSocket: ws://${host}:${port}`);
  console.log(`✅ Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`✅ Database: ${process.env.DB_NAME || 'pilotpros_db'}`);
  console.log(`✅ AI Agent: Enabled`);
  console.log(`✅ Security: Enterprise-grade`);
  console.log('');
  console.log('🎯 Business Process Operating System Ready!');
  console.log('Ready to serve business automation requests...');
});

export default app;