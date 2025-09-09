/**
 * MILHENA MCP Server
 * Complete n8n-mcp tools implementation with Claude API
 * EXACT COPY of n8n-mcp but using Claude API instead of Claude Desktop
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import pino from 'pino';
import { MilhenaN8nMCPTools } from './milhena-n8n-mcp-tools.js';

const logger = pino({
  level: 'info',
  transport: { target: 'pino-pretty', options: { colorize: true } }
});

const app = express();
const PORT = process.env.PORT || 3002;

app.use(helmet());
app.use(cors());
app.use(express.json());

// Initialize MILHENA with COMPLETE n8n-mcp tools
const mcpTools = new MilhenaN8nMCPTools();

// Intent classification (fast keyword matching)
function classifyIntent(query) {
  const q = query.toLowerCase();
  
  logger.info(`🔍 Classifying intent for query: "${query.substring(0, 50)}..."`);
  
  // Specific error queries
  if (q.includes('ultimo errore') || q.includes('ultimi errori') || q.includes('error') || q.includes('fallimenti')) {
    logger.info('→ Intent: errors');
    return 'errors';
  }
  
  // Analytics and reporting
  if (q.includes('report') || q.includes('analytics') || q.includes('statistiche') || q.includes('metriche')) {
    logger.info('→ Intent: analytics');
    return 'analytics';
  }
  
  // Process status
  if (q.includes('processi') || q.includes('stato') || q.includes('come va') || q.includes('attivi')) {
    logger.info('→ Intent: process_status');
    return 'process_status';
  }
  
  // Troubleshooting
  if (q.includes('problemi') || q.includes('troubleshoot') || q.includes('debug')) {
    logger.info('→ Intent: troubleshooting');
    return 'troubleshooting';
  }
  
  // Executions
  if (q.includes('esecuzioni') || q.includes('execution') || q.includes('operazioni')) {
    logger.info('→ Intent: executions');
    return 'executions';
  }
  
  // Management
  if (q.includes('avvia') || q.includes('ferma') || q.includes('gestisci')) {
    logger.info('→ Intent: management');
    return 'management';
  }
  
  // Technology stack questions
  if (q.includes('stack') || q.includes('tecnolog') || q.includes('sistema')) {
    logger.info('→ Intent: general');
    return 'general';
  }
  
  logger.info('→ Intent: general (default)');
  return 'general';
}

// Main MILHENA chat endpoint - COMPLETE n8n-mcp implementation
app.post('/api/chat', async (req, res) => {
  try {
    const { query } = req.body;
    
    if (!query?.trim()) {
      return res.status(400).json({ 
        error: 'Query required',
        message: 'Dimmi cosa posso fare per te!'
      });
    }

    logger.info('🚀 MILHENA n8n-MCP Processing:', { query: query.substring(0, 100) });
    const startTime = Date.now();

    // Process query with COMPLETE n8n-mcp tools
    const result = await mcpTools.processQuery(query);
    
    const processingTime = Date.now() - startTime;

    logger.info('✅ MILHENA Response:', { 
      toolsUsed: result.toolsUsed,
      processingTime: `${processingTime}ms`
    });

    res.json({
      response: result.response,
      toolsUsed: result.toolsUsed,
      processingTime: `${processingTime}ms`,
      source: 'milhena-n8n-mcp',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error('❌ MILHENA n8n-MCP Error:', error.message);
    
    res.status(500).json({
      response: 'Mi dispiace, ho avuto un problema tecnico. Riprova tra poco.',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Health check
app.get('/api/health', async (req, res) => {
  try {
    // Test backend connectivity
    await mcpTools.backendApi('/health');
    
    res.json({
      status: 'healthy',
      milhena: 'operational',
      tools: Object.keys(mcpTools.tools),
      backend: 'connected',
      ai: 'claude-api-mcp',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(503).json({
      status: 'degraded',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// List ALL available n8n-mcp tools
app.get('/api/tools', (req, res) => {
  const toolCategories = {
    system: ['tools_documentation', 'n8n_diagnostic', 'n8n_health_check', 'n8n_list_available_tools'],
    discovery: ['search_nodes', 'list_nodes', 'list_ai_tools', 'get_database_statistics'],
    configuration: ['get_node_essentials', 'get_node_info', 'get_node_documentation', 'search_node_properties'],
    validation: ['validate_node_minimal', 'validate_workflow', 'validate_workflow_connections'],
    templates: ['search_templates', 'get_template', 'list_node_templates'],
    workflow_management: ['n8n_list_workflows', 'n8n_get_workflow', 'n8n_list_executions'],
    business_intelligence: ['workflow_status', 'analytics_dashboard', 'execution_errors']
  };
  
  res.json({
    totalTools: Object.keys(mcpTools.tools).length,
    categories: toolCategories,
    tools: Object.keys(mcpTools.tools).map(name => ({
      name,
      description: `n8n-mcp tool: ${name}`,
      category: Object.entries(toolCategories).find(([cat, tools]) => 
        tools.includes(name))?.[0] || 'other'
    })),
    source: 'milhena-n8n-mcp',
    timestamp: new Date().toISOString()
  });
});

// Start server
app.listen(PORT, () => {
  logger.info(`🚀 MILHENA n8n-MCP Server running on port ${PORT}`);
  logger.info('🔧 COMPLETE n8n-mcp tools implementation with Claude API');
  logger.info(`📊 ${Object.keys(mcpTools.tools).length} tools available:`);
  logger.info('  • System: health_check, diagnostic, tools_documentation');
  logger.info('  • Discovery: search_nodes, list_nodes, list_ai_tools');
  logger.info('  • Configuration: get_node_info, get_node_essentials');
  logger.info('  • Validation: validate_workflow, validate_node_minimal');
  logger.info('  • Workflow Management: n8n_list_workflows, n8n_get_workflow');
  logger.info('  • Business Intelligence: workflow_status, analytics_dashboard');
  logger.info('⚡ Real-time data from PostgreSQL database');
});

export default app;