// PilotProOS AI Agent - MCP Integration Server
// Integrates with existing MCP server from PilotProMT for AI conversational interface
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import express from 'express';
import { spawn } from 'child_process';
import winston from 'winston';

// ============================================================================
// LOGGER CONFIGURATION
// ============================================================================

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.printf(({ timestamp, level, message, ...meta }) => {
      return `[${timestamp}] [AI-AGENT] ${level.toUpperCase()}: ${message} ${Object.keys(meta).length ? JSON.stringify(meta, null, 2) : ''}`;
    })
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: '../logs/ai-agent.log' })
  ]
});

// ============================================================================
// MCP CLIENT INTEGRATION
// ============================================================================

class PilotProOSAIAgent {
  constructor() {
    this.mcpClient = null;
    this.isConnected = false;
    this.mcpProcess = null;
  }
  
  async initialize() {
    try {
      logger.info('🤖 Initializing PilotProOS AI Agent...');
      
      // Start MCP server process (from PilotProMT)
      await this.startMCPServer();
      
      // Connect to MCP server
      await this.connectToMCPServer();
      
      logger.info('✅ AI Agent initialized successfully');
      return true;
    } catch (error) {
      logger.error('❌ AI Agent initialization failed:', error);
      return false;
    }
  }
  
  async startMCPServer() {
    logger.info('🔄 Starting MCP server from PilotProMT...');
    
    // Start MCP server using existing codebase with tsx for TypeScript execution
    this.mcpProcess = spawn('npx', ['tsx', './src/index.ts'], {
      cwd: process.cwd(),
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        ...process.env,
        // PilotProOS specific configuration
        MCP_MODE: 'pilotpros',
        AI_AGENT_INTEGRATION: 'true'
      }
    });
    
    this.mcpProcess.stdout.on('data', (data) => {
      logger.info(`MCP Server: ${data.toString().trim()}`);
    });
    
    this.mcpProcess.stderr.on('data', (data) => {
      logger.warn(`MCP Server Error: ${data.toString().trim()}`);
    });
    
    this.mcpProcess.on('close', (code) => {
      logger.warn(`MCP Server process exited with code ${code}`);
      this.isConnected = false;
    });
    
    // Wait for MCP server to be ready
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    logger.info('✅ MCP server started');
  }
  
  async connectToMCPServer() {
    logger.info('🔗 Connecting to MCP server...');
    
    const transport = new StdioClientTransport({
      command: 'npx',
      args: ['tsx', './src/index.ts'],
      env: {
        ...process.env,
        MCP_MODE: 'pilotpros'
      }
    });
    
    this.mcpClient = new Client({
      name: 'pilotpros-ai-agent',
      version: '1.0.0'
    }, {
      capabilities: {
        tools: {}
      }
    });
    
    await this.mcpClient.connect(transport);
    this.isConnected = true;
    
    logger.info('✅ Connected to MCP server');
    
    // List available tools
    const tools = await this.mcpClient.listTools();
    logger.info(`📋 Available MCP tools: ${tools.tools.map(t => t.name).join(', ')}`);
  }
  
  async processBusinessQuery(query, context = {}) {
    if (!this.isConnected) {
      throw new Error('MCP server not connected');
    }
    
    logger.info(`🗣️ Processing query: "${query}"`);
    
    try {
      // 1. Parse intent from natural language
      const intent = this.parseBusinessIntent(query);
      logger.info(`🎯 Intent detected: ${intent.type} (confidence: ${intent.confidence})`);
      
      // 2. Route to MCP tools
      const mcpCalls = this.routeIntentToMCPTools(intent);
      logger.info(`🔧 MCP calls planned: ${mcpCalls.length} tools`);
      
      // 3. Execute MCP tool calls
      const mcpResults = await this.executeMCPCalls(mcpCalls);
      
      // 4. Generate business-friendly response
      const businessResponse = this.generateBusinessResponse(intent, mcpResults, query);
      
      logger.info('✅ Query processed successfully');
      return businessResponse;
      
    } catch (error) {
      logger.error('❌ Error processing business query:', error);
      throw error;
    }
  }
  
  parseBusinessIntent(query) {
    const lowerQuery = query.toLowerCase();
    
    // Pattern matching per linguaggio italiano business
    const patterns = {
      process_status: [
        /mostra.*processi?\s*(attivi?)?/i,
        /stato.*processi?/i,
        /processi?\s*(in\s+)?esecuzione/i,
        /quanti?\s*processi?/i
      ],
      
      analytics_report: [
        /report\s*(di\s*|del\s*)?/i,
        /statistiche?\s*(di\s*|del\s*)?/i,
        /performance\s*(di\s*|del\s*)?/i,
        /analisi\s*(di\s*|del\s*)?/i,
        /trend/i
      ],
      
      business_metrics: [
        /quanti?\s*clienti?\s*processati?/i,
        /quanti?\s*ordini?\s*gestiti?/i,
        /quanto\s*tempo\s*risparmiato/i,
        /volume\s*(di\s*)?operazioni?/i
      ],
      
      troubleshooting: [
        /errori?\s*(recenti?)?/i,
        /problemi?\s*(di\s*)?/i,
        /perch[eé]\s*(il\s*)?processo/i,
        /fallimenti?/i,
        /cosa\s*non\s*funziona/i
      ],
      
      process_management: [
        /avvia\s*(il\s*)?processo/i,
        /ferma\s*(il\s*)?processo/i,
        /attiva\s*(il\s*)?processo/i,
        /disattiva\s*(il\s*)?processo/i
      ]
    };
    
    // Find matching pattern
    for (const [intentType, patternList] of Object.entries(patterns)) {
      for (const pattern of patternList) {
        if (pattern.test(lowerQuery)) {
          return {
            type: intentType,
            confidence: 0.8,
            originalQuery: query,
            entities: this.extractEntities(query)
          };
        }
      }
    }
    
    // Default intent
    return {
      type: 'general_help',
      confidence: 0.3,
      originalQuery: query,
      entities: {}
    };
  }
  
  extractEntities(query) {
    const entities = {};
    
    // Extract time references
    const timePatterns = {
      'oggi': 'today',
      'ieri': 'yesterday', 
      'questa settimana': '7d',
      'settimana scorsa': '7d-ago',
      'questo mese': '30d',
      'mese scorso': '30d-ago',
      'ultimi? \\d+ giorni?': 'Nd'
    };
    
    for (const [pattern, value] of Object.entries(timePatterns)) {
      if (new RegExp(pattern, 'i').test(query)) {
        entities.timeframe = value;
        break;
      }
    }
    
    // Extract process names (if mentioned)
    const processKeywords = ['onboarding', 'fatturazione', 'ordini', 'supporto', 'clienti'];
    for (const keyword of processKeywords) {
      if (query.toLowerCase().includes(keyword)) {
        entities.processCategory = keyword;
        break;
      }
    }
    
    return entities;
  }
  
  routeIntentToMCPTools(intent) {
    const calls = [];
    
    switch (intent.type) {
      case 'process_status':
        calls.push({
          tool: 'workflow.list',
          parameters: { active: true }
        });
        calls.push({
          tool: 'analytics.dashboard-overview',
          parameters: {}
        });
        break;
        
      case 'analytics_report':
        calls.push({
          tool: 'analytics.workflow-analytics',
          parameters: { 
            timeframe: intent.entities.timeframe || '7d'
          }
        });
        calls.push({
          tool: 'execution.list',
          parameters: {
            limit: 100,
            timeframe: intent.entities.timeframe || '7d'
          }
        });
        break;
        
      case 'business_metrics':
        calls.push({
          tool: 'execution.list',
          parameters: { 
            limit: 1000,
            timeframe: intent.entities.timeframe || '1d'
          }
        });
        calls.push({
          tool: 'analytics.dashboard-overview',
          parameters: {}
        });
        break;
        
      case 'troubleshooting':
        calls.push({
          tool: 'execution.list',
          parameters: {
            status: 'error',
            limit: 50
          }
        });
        calls.push({
          tool: 'analytics.error-analytics',
          parameters: {}
        });
        break;
        
      case 'process_management':
        // This would require additional MCP tools for management
        calls.push({
          tool: 'workflow.list',
          parameters: {}
        });
        break;
        
      default:
        calls.push({
          tool: 'analytics.dashboard-overview',
          parameters: {}
        });
    }
    
    return calls;
  }
  
  async executeMCPCalls(mcpCalls) {
    const results = [];
    
    for (const call of mcpCalls) {
      try {
        logger.info(`🔧 Executing MCP tool: ${call.tool}`);
        
        const result = await this.mcpClient.callTool({
          name: call.tool,
          arguments: call.parameters || {}
        });
        
        results.push({
          tool: call.tool,
          success: true,
          data: result.content,
          parameters: call.parameters
        });
        
        logger.info(`✅ MCP tool ${call.tool} executed successfully`);
      } catch (error) {
        logger.error(`❌ MCP tool ${call.tool} failed:`, error);
        
        results.push({
          tool: call.tool,
          success: false,
          error: error.message,
          parameters: call.parameters
        });
      }
    }
    
    return results;
  }
  
  generateBusinessResponse(intent, mcpResults, originalQuery) {
    const successfulResults = mcpResults.filter(r => r.success);
    
    if (successfulResults.length === 0) {
      return {
        textResponse: '🚨 **Sistema temporaneamente non disponibile**\n\nRiprova tra qualche istante, o contatta il supporto se il problema persiste.',
        actionSuggestions: [
          'Verifica stato del sistema',
          'Riprova la richiesta',
          'Contatta supporto tecnico'
        ]
      };
    }
    
    // Generate response based on intent type
    switch (intent.type) {
      case 'process_status':
        return this.generateProcessStatusResponse(successfulResults);
        
      case 'analytics_report':
        return this.generateAnalyticsResponse(successfulResults, intent.entities);
        
      case 'business_metrics':
        return this.generateBusinessMetricsResponse(successfulResults, intent.entities);
        
      case 'troubleshooting':
        return this.generateTroubleshootingResponse(successfulResults);
        
      default:
        return this.generateHelpResponse();
    }
  }
  
  generateProcessStatusResponse(results) {
    const workflows = results.find(r => r.tool === 'workflow.list')?.data || [];
    const dashboard = results.find(r => r.tool === 'analytics.dashboard-overview')?.data || {};
    
    const activeCount = workflows.filter(w => w.active).length;
    const totalExecutions = dashboard.totalExecutions || 0;
    const successRate = dashboard.successRate || 0;
    
    return {
      textResponse: `🎯 **Stato dei tuoi Processi Aziendali:**\n\n` +
                   `• **${activeCount} processi attivi** su ${workflows.length} totali\n` +
                   `• **${totalExecutions} esecuzioni** completate\n` +
                   `• **${successRate.toFixed(1)}% tasso di successo** ${this.getPerformanceEmoji(successRate)}\n` +
                   `• **Ultimo aggiornamento:** ${new Date().toLocaleString('it-IT')}\n\n` +
                   `${this.getStatusSummary(successRate, activeCount)}`,
      
      visualData: {
        metrics: [
          { label: 'Processi Attivi', value: activeCount, trend: 'stable' },
          { label: 'Esecuzioni Totali', value: totalExecutions, trend: 'up' },
          { label: 'Tasso Successo', value: `${successRate.toFixed(1)}%`, trend: successRate > 90 ? 'up' : 'stable' }
        ],
        table: {
          headers: ['Nome Processo', 'Stato', 'Esecuzioni', 'Ultima Attività'],
          rows: workflows.slice(0, 5).map(w => [
            w.name,
            w.active ? '✅ Attivo' : '⏸️ Pausa',
            w.executionCount || 0,
            w.lastExecution ? new Date(w.lastExecution).toLocaleString('it-IT') : 'Mai'
          ])
        }
      },
      
      actionSuggestions: [
        'Mostra dettagli del processo più utilizzato',
        'Crea report performance settimanale',
        'Verifica se ci sono errori da risolvere'
      ],
      
      quickActions: [
        { label: '📊 Report Dettagliato', query: 'Crea un report completo delle performance' },
        { label: '⚠️ Controlla Errori', query: 'Mostra errori e problemi recenti' },
        { label: '🚀 Ottimizza', query: 'Suggerimenti per ottimizzare i processi' }
      ]
    };
  }
  
  generateAnalyticsResponse(results, entities) {
    const analytics = results.find(r => r.tool === 'analytics.workflow-analytics')?.data || {};
    const executions = results.find(r => r.tool === 'execution.list')?.data || [];
    
    const timeframe = entities.timeframe || '7d';
    const timeframeLabel = this.getTimeframeLabel(timeframe);
    
    const totalExecutions = executions.length;
    const successfulExecutions = executions.filter(e => e.finished && !e.error).length;
    const avgDuration = executions.reduce((sum, e) => sum + (e.duration || 0), 0) / totalExecutions || 0;
    
    return {
      textResponse: `📊 **Report Analisi ${timeframeLabel}:**\n\n` +
                   `• **${totalExecutions} operazioni** completate\n` +
                   `• **${successfulExecutions} successi** (${(successfulExecutions/totalExecutions*100).toFixed(1)}%)\n` +
                   `• **Tempo medio:** ${(avgDuration/1000).toFixed(1)} secondi\n` +
                   `• **Performance:** ${this.getPerformanceLabel(successfulExecutions/totalExecutions)}\n\n` +
                   `**💡 Insights Business:**\n${this.generateBusinessInsights(analytics, executions).join('\n')}`,
      
      visualData: {
        metrics: [
          { label: 'Operazioni', value: totalExecutions, trend: 'up' },
          { label: 'Successo %', value: `${(successfulExecutions/totalExecutions*100).toFixed(1)}%`, trend: 'stable' },
          { label: 'Tempo Medio', value: `${(avgDuration/1000).toFixed(1)}s`, trend: 'down' }
        ]
      },
      
      actionSuggestions: [
        'Confronta con periodo precedente',
        'Analizza processi più lenti',
        'Identifica opportunità di miglioramento'
      ]
    };
  }
  
  generateHelpResponse() {
    return {
      textResponse: `🤖 **Assistente Processi Aziendali PilotProOS**\n\n` +
                   `Sono qui per aiutarti a gestire e monitorare i tuoi processi automatizzati.\n\n` +
                   `**💡 Cosa posso fare per te:**\n` +
                   `• Mostrarti lo stato dei processi attivi\n` +
                   `• Generare report e analisi performance\n` +
                   `• Identificare errori e problemi\n` +
                   `• Calcolare metriche business (clienti processati, tempo risparmiato)\n` +
                   `• Suggerire ottimizzazioni e miglioramenti\n\n` +
                   `**🗣️ Parla con me in linguaggio naturale!**`,
      
      quickActions: [
        { label: '📊 Stato Processi', query: 'Mostra lo stato dei miei processi aziendali' },
        { label: '📈 Report Settimanale', query: 'Crea un report delle performance di questa settimana' },
        { label: '🔍 Controlla Errori', query: 'Ci sono errori o problemi da controllare?' },
        { label: '💰 Impatto Business', query: 'Quanto tempo e denaro ho risparmiato con l\'automazione?' }
      ]
    };
  }
  
  // Helper methods
  getPerformanceEmoji(rate) {
    if (rate >= 95) return '🎉';
    if (rate >= 85) return '👍';
    if (rate >= 70) return '⚠️';
    return '🚨';
  }
  
  getStatusSummary(successRate, activeCount) {
    if (successRate >= 95 && activeCount > 0) {
      return '🎉 **Eccellente!** I tuoi processi stanno funzionando perfettamente.';
    } else if (successRate >= 85) {
      return '👍 **Bene!** Performance solide con margini di miglioramento.';
    } else if (successRate >= 70) {
      return '⚠️ **Attenzione!** Alcuni processi potrebbero aver bisogno di ottimizzazione.';
    } else {
      return '🚨 **Azione richiesta!** Ci sono problemi che richiedono la tua attenzione immediata.';
    }
  }
  
  getTimeframeLabel(timeframe) {
    const labels = {
      'today': 'di oggi',
      '1d': 'di oggi',
      '7d': 'di questa settimana',
      '30d': 'di questo mese',
      '7d-ago': 'della settimana scorsa',
      '30d-ago': 'del mese scorso'
    };
    return labels[timeframe] || 'del periodo selezionato';
  }
  
  getPerformanceLabel(rate) {
    if (rate >= 0.95) return 'Eccellente';
    if (rate >= 0.85) return 'Buona'; 
    if (rate >= 0.70) return 'Discreta';
    return 'Da migliorare';
  }
  
  generateBusinessInsights(analytics, executions) {
    const insights = [];
    
    if (executions.length > 0) {
      const avgDuration = executions.reduce((sum, e) => sum + (e.duration || 0), 0) / executions.length;
      const timeSavedHours = Math.round(executions.length * 5 / 60); // 5 min per operazione manuale
      
      insights.push(`• **${timeSavedHours} ore** di lavoro manuale risparmiato`);
      
      if (avgDuration < 30000) {
        insights.push('• **Performance eccellenti** - processi veloci e efficienti');
      }
      
      const errorRate = executions.filter(e => e.error).length / executions.length;
      if (errorRate < 0.05) {
        insights.push('• **Affidabilità alta** - pochissimi errori rilevati');
      }
    }
    
    return insights;
  }
  
  // Graceful shutdown
  async shutdown() {
    logger.info('🔄 Shutting down AI Agent...');
    
    if (this.mcpClient) {
      await this.mcpClient.close();
    }
    
    if (this.mcpProcess) {
      this.mcpProcess.kill('SIGTERM');
    }
    
    logger.info('✅ AI Agent shutdown complete');
  }
}

// ============================================================================
// EXPRESS API SERVER
// ============================================================================

const app = express();
const port = process.env.AI_AGENT_PORT || 3002;

app.use(express.json());

// Initialize AI Agent
const aiAgent = new PilotProOSAIAgent();
let agentReady = false;

// Initialize AI Agent on startup
aiAgent.initialize().then((success) => {
  agentReady = success;
  if (success) {
    logger.info('🚀 AI Agent ready for business queries');
  } else {
    logger.error('❌ AI Agent failed to initialize');
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: agentReady ? 'ready' : 'initializing',
    mcpConnected: aiAgent.isConnected,
    timestamp: new Date().toISOString()
  });
});

// Process business query endpoint
app.post('/chat', async (req, res) => {
  try {
    const { query, context } = req.body;
    
    if (!agentReady) {
      return res.status(503).json({
        error: 'AI Agent still initializing',
        message: 'Please wait a moment and try again'
      });
    }
    
    if (!query || !query.trim()) {
      return res.status(400).json({
        error: 'Query is required',
        example: 'Try: "Mostra i processi attivi"'
      });
    }
    
    const response = await aiAgent.processBusinessQuery(query, context);
    res.json(response);
    
  } catch (error) {
    logger.error('❌ Chat endpoint error:', error);
    res.status(500).json({
      error: 'AI Agent error',
      message: 'The AI assistant encountered an issue processing your request',
      fallback: 'Try simpler questions like "Show active processes" or "Weekly report"'
    });
  }
});

// Start AI Agent API server (internal)
app.listen(port, '127.0.0.1', () => {
  logger.info('🤖 PilotProOS AI Agent API Server');
  logger.info('=================================');
  logger.info(`✅ Server: http://127.0.0.1:${port}`);
  logger.info('✅ MCP Integration: PilotProMT tools');
  logger.info('✅ Natural Language: Italian business queries');
  logger.info('✅ Response Format: Business-friendly');
  logger.info('');
  logger.info('🎯 Ready to process business automation queries!');
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('🔄 SIGTERM received, shutting down...');
  await aiAgent.shutdown();
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('🔄 SIGINT received, shutting down...');
  await aiAgent.shutdown();
  process.exit(0);
});

export default aiAgent;