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

// Rate limiting per API protection
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: {
    error: 'Too many requests, please try again later.',
    retryAfter: 15
  },
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/api/', apiLimiter);

// JSON parsing with size limit
app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ extended: true, limit: '1mb' }));

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

// Business Processes API (anonimized workflows)
app.get('/api/business/processes', async (req, res) => {
  try {
    const result = await dbPool.query(`
      SELECT 
        w.id as process_id,
        w.name as process_name,
        w.active as is_active,
        w.created_at as created_date,
        w.updated_at as last_modified,
        
        -- Business analytics from our schema
        COALESCE(ba.success_rate, 0) as success_rate,
        COALESCE(ba.avg_duration_ms, 0) as avg_duration_ms,
        COALESCE(ba.total_executions, 0) as total_executions,
        ba.last_execution,
        ba.trend_direction,
        ba.business_impact_score,
        
        -- Real-time metrics
        (
          SELECT COUNT(*) 
          FROM n8n.execution_entity e 
          WHERE e.workflow_id = w.id 
          AND e.started_at >= CURRENT_DATE
        ) as executions_today,
        
        -- Health status
        CASE 
          WHEN COALESCE(ba.success_rate, 0) >= 98 THEN 'Excellent'
          WHEN COALESCE(ba.success_rate, 0) >= 85 THEN 'Good'
          WHEN COALESCE(ba.success_rate, 0) >= 70 THEN 'Fair'
          ELSE 'Needs Attention'
        END as health_status
        
      FROM n8n.workflow_entity w
      LEFT JOIN pilotpros.business_analytics ba ON w.id = ba.n8n_workflow_id
      WHERE w.active = true
      ORDER BY ba.business_impact_score DESC NULLS LAST, w.updated_at DESC
    `);
    
    res.json({
      data: result.rows,
      total: result.rows.length,
      summary: {
        active: result.rows.length,
        totalExecutionsToday: result.rows.reduce((sum, row) => sum + (row.executions_today || 0), 0),
        avgSuccessRate: result.rows.reduce((sum, row) => sum + (row.success_rate || 0), 0) / result.rows.length || 0
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
        WHEN e.finished = true AND e.data->>'error' IS NULL THEN 'completed'
        WHEN e.finished = false AND e.data->>'error' IS NOT NULL THEN 'failed'
        WHEN e.finished = false THEN 'running'
        ELSE 'unknown'
      END = $${paramCount}`;
      params.push(status);
    }
    
    if (processId) {
      paramCount++;
      whereClause += ` AND e.workflow_id = $${paramCount}`;
      params.push(processId);
    }
    
    paramCount++;
    params.push(parseInt(limit));
    paramCount++;
    params.push(parseInt(offset));
    
    const result = await dbPool.query(`
      SELECT 
        e.id as run_id,
        e.workflow_id as process_id,
        w.name as process_name,
        e.started_at as start_time,
        e.stopped_at as end_time,
        e.finished as is_completed,
        
        -- Business-friendly status
        CASE 
          WHEN e.finished = true AND e.data->>'error' IS NULL THEN 'Completed Successfully'
          WHEN e.finished = false AND e.data->>'error' IS NOT NULL THEN 'Requires Attention'
          WHEN e.finished = false THEN 'In Progress'
          ELSE 'Unknown Status'
        END as business_status,
        
        -- Duration calculation
        CASE 
          WHEN e.stopped_at IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (e.stopped_at - e.started_at)) * 1000
          ELSE NULL
        END as duration_ms,
        
        -- Error information (business-friendly)
        CASE 
          WHEN e.data->>'error' IS NOT NULL THEN 'Process encountered an issue'
          ELSE NULL
        END as issue_description
        
      FROM n8n.execution_entity e
      JOIN n8n.workflow_entity w ON e.workflow_id = w.id
      ${whereClause}
      ORDER BY e.started_at DESC
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

// Business Analytics API
app.get('/api/business/analytics', async (req, res) => {
  try {
    const result = await dbPool.query(`
      SELECT 
        -- Process overview
        COUNT(DISTINCT w.id) as total_processes,
        COUNT(DISTINCT CASE WHEN w.active = true THEN w.id END) as active_processes,
        
        -- Execution metrics
        COUNT(e.id) as total_executions,
        COUNT(CASE WHEN e.finished = true AND e.data->>'error' IS NULL THEN 1 END) as successful_executions,
        COUNT(CASE WHEN e.finished = false OR e.data->>'error' IS NOT NULL THEN 1 END) as failed_executions,
        
        -- Performance metrics
        AVG(EXTRACT(EPOCH FROM (e.stopped_at - e.started_at)) * 1000) as avg_duration_ms,
        
        -- Business metrics (estimated from execution data)
        COUNT(CASE WHEN e.data->>'type' = 'customer_onboarding' THEN 1 END) as customers_processed,
        COUNT(CASE WHEN e.data->>'type' = 'order_processing' THEN 1 END) as orders_processed,
        COUNT(CASE WHEN e.data->>'type' = 'support_ticket' THEN 1 END) as tickets_processed,
        
        -- Time saved calculation (assumendo 5 minuti per operazione manuale)
        COUNT(CASE WHEN e.finished = true THEN 1 END) * 5 as minutes_saved
        
      FROM n8n.workflow_entity w
      LEFT JOIN n8n.execution_entity e ON w.id = e.workflow_id
      WHERE e.started_at >= NOW() - INTERVAL '7 days' OR e.started_at IS NULL
    `);
    
    const data = result.rows[0];
    const successRate = data.total_executions > 0 
      ? (data.successful_executions / data.total_executions * 100) 
      : 0;
    
    res.json({
      overview: {
        totalProcesses: parseInt(data.total_processes),
        activeProcesses: parseInt(data.active_processes),
        totalExecutions: parseInt(data.total_executions),
        successRate: Math.round(successRate * 10) / 10,
        avgDurationSeconds: Math.round((data.avg_duration_ms || 0) / 1000)
      },
      
      businessImpact: {
        customersProcessed: parseInt(data.customers_processed || 0),
        ordersProcessed: parseInt(data.orders_processed || 0),
        ticketsProcessed: parseInt(data.tickets_processed || 0),
        timeSavedHours: Math.round((data.minutes_saved || 0) / 60),
        estimatedCostSavings: Math.round((data.minutes_saved || 0) * 0.5) // €0.50 per minuto risparmiato
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
      ]
    });
  } catch (error) {
    console.error('❌ Error fetching business analytics:', error);
    res.status(500).json({ 
      error: 'Failed to fetch business analytics',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
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

// Global error handler
app.use((error, req, res, next) => {
  console.error('❌ Unhandled error:', error);
  
  res.status(500).json({
    error: 'Internal system error',
    message: 'Business process system encountered an issue',
    timestamp: new Date().toISOString(),
    // Only show details in development
    details: process.env.NODE_ENV === 'development' ? error.message : undefined
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    message: 'The requested business operation is not available',
    availableEndpoints: [
      '/api/business/processes',
      '/api/business/process-runs', 
      '/api/business/analytics',
      '/api/ai-agent/chat'
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
// SERVER STARTUP
// ============================================================================

app.listen(port, host, () => {
  console.log('🚀 PilotProOS Backend API Server');
  console.log('================================');
  console.log(`✅ Server: http://${host}:${port}`);
  console.log(`✅ Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`✅ Database: ${process.env.DB_NAME || 'pilotpros_db'}`);
  console.log(`✅ AI Agent: Enabled`);
  console.log(`✅ Security: Enterprise-grade`);
  console.log('');
  console.log('🎯 Business Process Operating System Ready!');
  console.log('Ready to serve business automation requests...');
});

export default app;