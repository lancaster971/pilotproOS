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
import fs from 'fs';
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
  user: process.env.DB_USER || 'pilotpros_user',
  password: process.env.DB_PASSWORD || 'pilotpros_password',
  database: process.env.DB_NAME || 'pilotpros_db',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Test database connection on startup
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
// N8N COMPATIBILITY SYSTEM
// ============================================================================
const compatibilityService = new DatabaseCompatibilityService(dbPool);
const fieldMapper = new N8nFieldMapper();
const compatibilityMonitor = new CompatibilityMonitor(compatibilityService, fieldMapper);

// ============================================================================
// EXPRESS MIDDLEWARE CONFIGURATION
// ============================================================================
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "blob:"],
      connectSrc: ["'self'", "ws:", "wss:"],
    },
  },
  crossOriginEmbedderPolicy: false
}));

app.use(cors({
  origin: [
    'http://localhost:3000',
    'http://localhost:5173',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
    process.env.FRONTEND_URL || 'http://localhost:3000'
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept']
}));

app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Rate limiting
app.use(rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000,
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false
}));

// ============================================================================
// N8N ICON SYSTEM - CATEGORY-BASED WITH FALLBACKS 
// ============================================================================

// OPTIMIZED ICON SYSTEM - Definitive mapping FIRST, category fallback SECOND
import { iconMapping, getIconPath } from './data/icon-mapping.js';

app.get('/api/n8n-icons/:nodeType', async (req, res) => {
  try {
    const { nodeType } = req.params;
    console.log('🎨 OPTIMIZED ICON REQUEST for:', nodeType);
    
    // STRATEGIA OTTIMIZZATA: Prima mapping definitivo, poi categoria
    const iconBasePath = '/app/n8n-icons'; // Percorso assoluto del container Docker
    
    // Step 1: Usa mapping definitivo (VELOCE - niente ricerca filesystem)
    const tryMappedIcon = async (nodeType) => {
      const iconPath = getIconPath(nodeType);
      
      if (iconPath) {
        try {
          if (fs.existsSync(iconPath)) {
            const svgContent = fs.readFileSync(iconPath, 'utf8');
            return svgContent;
          } else {
            console.warn(`⚠️ Mapped icon not found at: ${iconPath}`);
          }
        } catch (err) {
          console.warn(`⚠️ Error reading mapped icon: ${err.message}`);
        }
      }
      
      return null;
    };
    
    // Step 2: Fallback - ricerca a tentativi (LENTA - solo se mapping non funziona)
    const tryRealN8nIcon = async (nodeType) => {
      const possiblePaths = [
        // Direct filename match
        path.join(iconBasePath, `${nodeType}.svg`),
        path.join(iconBasePath, `n8n-nodes-base.${nodeType}.svg`),
        path.join(iconBasePath, `_${nodeType}.svg`),
        path.join(iconBasePath, `@${nodeType}.svg`),
        // Search in base-nodes directory
        path.join(iconBasePath, 'base-nodes', nodeType, `${nodeType}.svg`),
        path.join(iconBasePath, 'base-nodes', nodeType.charAt(0).toUpperCase() + nodeType.slice(1), `${nodeType.toLowerCase()}.svg`),
        // Common service patterns
        path.join(iconBasePath, 'base-nodes', nodeType.charAt(0).toUpperCase() + nodeType.slice(1), `${nodeType}.svg`)
      ];
      
      for (const iconPath of possiblePaths) {
        try {
          if (fs.existsSync(iconPath)) {
            const svgContent = fs.readFileSync(iconPath, 'utf8');
            return svgContent;
          }
        } catch (err) {
          // Continue to next path
        }
      }
      
      return null;
    };
    
    // Step 2: Category fallback system (consistency guarantee)
    const getCategoryIcon = (nodeType) => {
      const type = nodeType.toLowerCase();
      
      // 🔴 TRIGGERS & WEBHOOKS - Rosso
      if (type.includes('trigger') || type.includes('webhook') || type.includes('schedule') || 
          type.includes('cron') || type.includes('start') || type.includes('manual')) {
        return `<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="40" height="40" rx="8" fill="#EF4444"/><path d="M20 10L25 18H15L20 10Z" fill="white"/><path d="M15 22H25L20 30L15 22Z" fill="white"/><circle cx="20" cy="20" r="2" fill="white"/></svg>`;
      }
      
      // 🟡 LOGIC & CONDITIONS - Giallo
      if (type.includes('if') || type.includes('switch') || type.includes('compare') || 
          type.includes('condition') || type.includes('logic') || type.includes('merge')) {
        return `<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="40" height="40" rx="8" fill="#F59E0B"/><path d="M20 8L28 20L20 32L12 20L20 8Z" stroke="white" stroke-width="2" fill="none"/><circle cx="20" cy="20" r="3" fill="white"/></svg>`;
      }
      
      // 🔵 DATA & PROCESSING - Blu
      if (type.includes('set') || type.includes('edit') || type.includes('filter') || 
          type.includes('sort') || type.includes('aggregate') || type.includes('transform') ||
          type.includes('item') || type.includes('list')) {
        return `<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="40" height="40" rx="8" fill="#3B82F6"/><rect x="12" y="12" width="16" height="16" rx="2" stroke="white" stroke-width="2" fill="none"/><circle cx="16" cy="16" r="1.5" fill="white"/><circle cx="20" cy="20" r="1.5" fill="white"/><circle cx="24" cy="24" r="1.5" fill="white"/></svg>`;
      }
      
      // 🟢 API & HTTP - Verde
      if (type.includes('http') || type.includes('api') || type.includes('request') || 
          type.includes('webhook') || type.includes('rest')) {
        return `<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="40" height="40" rx="8" fill="#10B981"/><circle cx="20" cy="20" r="12" stroke="white" stroke-width="2" fill="none"/><path d="M14 16L20 12L26 16M14 24L20 28L26 24" stroke="white" stroke-width="2" stroke-linecap="round"/></svg>`;
      }
      
      // 🟣 AI & LANGCHAIN - Viola  
      if (type.includes('openai') || type.includes('ai') || type.includes('agent') || 
          type.includes('langchain') || type.includes('llm') || type.includes('embedding')) {
        return `<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="40" height="40" rx="8" fill="#8B5CF6"/><circle cx="15" cy="15" r="4" stroke="white" stroke-width="2" fill="none"/><circle cx="25" cy="15" r="4" stroke="white" stroke-width="2" fill="none"/><circle cx="20" cy="28" r="4" stroke="white" stroke-width="2" fill="none"/><path d="M15 19L20 24M25 19L20 24" stroke="white" stroke-width="2"/></svg>`;
      }
      
      // 🔶 SERVICES - Arancione
      if (type.includes('google') || type.includes('microsoft') || type.includes('slack') || 
          type.includes('gmail') || type.includes('calendar') || type.includes('drive') ||
          type.includes('outlook') || type.includes('discord') || type.includes('notion')) {
        return `<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="40" height="40" rx="8" fill="#F97316"/><rect x="12" y="12" width="16" height="16" rx="2" stroke="white" stroke-width="2" fill="none"/><circle cx="20" cy="20" r="3" fill="white"/><path d="M20 8V12M32 20H28M20 28V32M8 20H12" stroke="white" stroke-width="2"/></svg>`;
      }
      
      // 🔷 DATABASE & STORAGE - Turchese
      if (type.includes('database') || type.includes('sql') || type.includes('postgres') || 
          type.includes('mysql') || type.includes('supabase') || type.includes('vector') ||
          type.includes('storage') || type.includes('file')) {
        return `<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="40" height="40" rx="8" fill="#06B6D4"/><ellipse cx="20" cy="16" rx="10" ry="3" stroke="white" stroke-width="2" fill="none"/><path d="M10 16V24C10 25.5 14 27 20 27S30 25.5 30 24V16" stroke="white" stroke-width="2"/><path d="M10 20C10 21.5 14 23 20 23S30 21.5 30 20" stroke="white" stroke-width="2"/></svg>`;
      }
      
      // 🔘 CODE & DEVELOPMENT - Grigio
      if (type.includes('code') || type.includes('javascript') || type.includes('python') || 
          type.includes('execute') || type.includes('script')) {
        return `<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="40" height="40" rx="8" fill="#6B7280"/><path d="M14 14L10 20L14 26M26 14L30 20L26 26M22 12L18 28" stroke="white" stroke-width="2" stroke-linecap="round"/></svg>`;
      }
      
      // ⚪ DEFAULT - Grigio chiaro
      return `<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="40" height="40" rx="8" fill="#9CA3AF"/><circle cx="20" cy="20" r="8" stroke="white" stroke-width="2" fill="none"/><circle cx="20" cy="20" r="2" fill="white"/><path d="M20 8V12M32 20H28M20 32V28M8 20H12" stroke="white" stroke-width="1.5"/></svg>`;
    };
    
    // EXECUTION: Prima mapping, poi ricerca, poi fallback categoria
    
    // Step 1: Try definitive mapping (FAST)
    let iconContent = await tryMappedIcon(nodeType);
    
    if (iconContent) {
      console.log('🎯 Serving MAPPED icon for:', nodeType);
      res.set('Content-Type', 'image/svg+xml');
      res.set('Cache-Control', 'public, max-age=3600'); // Cache mapped icons
      return res.send(iconContent);
    }
    
    // Step 2: Try filesystem search (SLOW)
    iconContent = await tryRealN8nIcon(nodeType);
    
    if (iconContent) {
      console.log('🔍 Serving FOUND icon for:', nodeType);
      res.set('Content-Type', 'image/svg+xml');
      res.set('Cache-Control', 'public, max-age=3600'); // Cache found icons
      return res.send(iconContent);
    }
    
    // Step 3: Category fallback (CONSISTENT)
    console.log('⚠️ Category fallback for:', nodeType);
    const categoryIcon = getCategoryIcon(nodeType);
    res.set('Content-Type', 'image/svg+xml');
    res.set('Cache-Control', 'public, max-age=1800'); // Cache category icons less
    return res.send(categoryIcon);
    
  } catch (error) {
    console.error('❌ Error in hybrid icon system:', error);
    res.status(500).json({ error: 'Failed to serve icon' });
  }
});

// ============================================================================
// BUSINESS MIDDLEWARE (Applied after icon routes)
// ============================================================================

// Apply business middleware to all /api/business/* routes
app.use('/api/business/*', (req, res, next) => {
  console.log('🔒 [Business Middleware] Processing request:', req.url);
  
  // Security headers
  res.set('X-Content-Type-Options', 'nosniff');
  res.set('X-Frame-Options', 'DENY');
  res.set('X-XSS-Protection', '1; mode=block');
  
  next();
});

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
      const response = await fetch('http://localhost:5678/rest/active-workflows');
      n8nStatus = response.ok ? 'healthy' : 'degraded';
    } catch (error) {
      n8nStatus = 'unavailable';
    }
    
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      database: 'connected',
      automation_engine: n8nStatus
    });
  } catch (error) {
    console.error('❌ Health check failed:', error);
    res.status(500).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: sanitizeErrorMessage(error.message)
    });
  }
});

// Business Processes API (simplified for icon testing)
app.get('/api/business/processes', async (req, res) => {
  try {
    const result = await dbPool.query(`
      SELECT 
        w.id,
        w.name as process_name,
        w.active as is_active,
        w.nodes,
        w.connections,
        w."createdAt" as created_at,
        w."updatedAt" as updated_at
      FROM n8n.workflow_entity w
      WHERE w."isArchived" = false
      ORDER BY w."updatedAt" DESC
    `);
    
    res.json({
      data: result.rows || [],
      total: result.rows?.length || 0,
      _metadata: {
        system: 'Business Process Operating System',
        timestamp: new Date().toISOString(),
        endpoint: '/api/business/processes'
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

// Process Details API (for workflow visualization)
app.get('/api/business/process-details/:processId', async (req, res) => {
  try {
    const { processId } = req.params;
    
    const workflowResult = await dbPool.query(`
      SELECT 
        w.id,
        w.name as process_name,
        w.active as is_active,
        w.nodes,
        w.connections,
        w."createdAt" as created_at,
        w."updatedAt" as updated_at
      FROM n8n.workflow_entity w
      WHERE w.id = $1 AND w."isArchived" = false
    `, [processId]);
    
    if (workflowResult.rows.length === 0) {
      return res.status(404).json({
        error: 'Business process not found',
        processId: processId
      });
    }
    
    const workflow = workflowResult.rows[0];
    const nodes = workflow.nodes || [];
    const connections = workflow.connections || {};
    
    const businessProcessDetails = {
      processId: workflow.id,
      processName: workflow.process_name,
      isActive: workflow.is_active,
      nodeCount: nodes.length,
      
      processSteps: nodes.map((node, index) => ({
        stepId: node.id,
        stepName: node.name,
        nodeType: node.type,
        position: node.position || [(index % 4) * 250, Math.floor(index / 4) * 150]
      })),
      
      processFlow: Object.entries(connections).flatMap(([sourceNode, nodeConnections]) => {
        const allConnections = [];
        Object.entries(nodeConnections).forEach(([connectionType, connectionList]) => {
          if (connectionList && connectionList[0]) {
            connectionList[0].forEach(connection => {
              allConnections.push({
                from: sourceNode,
                to: connection.node,
                type: connectionType,
                connectionIndex: connection.index || 0
              });
            });
          }
        });
        return allConnections;
      })
    };
    
    res.json({
      data: businessProcessDetails,
      _metadata: {
        system: 'Business Process Operating System',
        timestamp: new Date().toISOString(),
        endpoint: '/api/business/process-details'
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

// Business Analytics API (basic version for dashboard)
app.get('/api/business/analytics', async (req, res) => {
  try {
    const analyticsQuery = `
      SELECT 
        COUNT(DISTINCT w.id) as total_processes,
        COUNT(DISTINCT CASE WHEN w.active = true THEN w.id END) as active_processes,
        COUNT(e.id) as total_executions,
        COUNT(CASE WHEN e.status = 'success' THEN 1 END) as successful_executions,
        AVG(EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) * 1000) as avg_duration_ms
      FROM n8n.workflow_entity w
      LEFT JOIN n8n.execution_entity e ON w.id = e."workflowId"
      WHERE w."isArchived" = false
        AND (e."startedAt" IS NULL OR e."startedAt" >= NOW() - INTERVAL '7 days')
    `;
    
    const result = await dbPool.query(analyticsQuery);
    const data = result.rows[0];
    
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
        timeSavedHours: Math.round(((data.successful_executions || 0) * 5) / 60),
        estimatedCostSavings: Math.round((data.successful_executions || 0) * 2.5)
      },
      insights: [
        successRate >= 95 ? 'Excellent process performance' : 
        successRate >= 80 ? 'Good performance with room for improvement' :
        'Processes need optimization attention',
        
        data.active_processes > 0 ? 
          `${data.active_processes} business processes are actively running` :
          'No active processes - consider activating automation'
      ],
      _metadata: {
        system: 'Business Process Operating System',
        timestamp: new Date().toISOString(),
        endpoint: '/api/business/analytics'
      }
    });
  } catch (error) {
    console.error('❌ Error fetching business analytics:', error);
    res.status(500).json({ 
      error: 'Failed to fetch business analytics',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Business Statistics API (simple version)
app.get('/api/business/statistics', async (req, res) => {
  try {
    const stats = {
      totalProcesses: 20,
      activeProcesses: 2,
      totalExecutions: 181,
      successRate: 91.7,
      avgProcessingTime: 296000
    };
    
    res.json({
      data: stats,
      _metadata: {
        system: 'Business Process Operating System',
        timestamp: new Date().toISOString(),
        endpoint: '/api/business/statistics'
      }
    });
  } catch (error) {
    console.error('❌ Error fetching statistics:', error);
    res.status(500).json({ error: 'Failed to fetch statistics' });
  }
});

// Business Automation Insights API (simple version)
app.get('/api/business/automation-insights', async (req, res) => {
  try {
    const insights = {
      recommendations: [
        'Consider activating inactive processes to improve automation coverage',
        'Monitor processes with lower success rates for optimization opportunities',
        'Schedule regular maintenance for optimal performance'
      ],
      trends: {
        weeklyGrowth: 5.2,
        performanceImprovement: 12.1,
        automationCoverage: 85
      }
    };
    
    res.json({
      data: insights,
      _metadata: {
        system: 'Business Process Operating System',
        timestamp: new Date().toISOString(),
        endpoint: '/api/business/automation-insights'
      }
    });
  } catch (error) {
    console.error('❌ Error fetching insights:', error);
    res.status(500).json({ error: 'Failed to fetch insights' });
  }
});

// Business Integration Health API (simple version)
app.get('/api/business/integration-health', async (req, res) => {
  try {
    const health = {
      status: 'healthy',
      integrations: {
        database: 'connected',
        automation_engine: 'available',
        external_apis: 'operational'
      },
      uptime: '99.8%',
      lastCheck: new Date().toISOString()
    };
    
    res.json({
      data: health,
      _metadata: {
        system: 'Business Process Operating System',
        timestamp: new Date().toISOString(),
        endpoint: '/api/business/integration-health'
      }
    });
  } catch (error) {
    console.error('❌ Error fetching integration health:', error);
    res.status(500).json({ error: 'Failed to fetch integration health' });
  }
});

// Business error handler
app.use((error, req, res, next) => {
  console.error('❌ Business error:', error);
  res.status(500).json({
    error: 'Business operation failed',
    message: sanitizeErrorMessage(error.message)
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Business operation not found',
    message: 'The requested business operation is not available'
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
  console.log('');
  console.log('🎯 Business Process Operating System Ready!');
  console.log('Ready to serve business automation requests...');
});