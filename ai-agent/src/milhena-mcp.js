/**
 * MILHENA MCP Integration Server
 * Combines MCP tools with LangChain + Ollama for business intelligence
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import pino from 'pino';
import { ChatOllama } from '@langchain/community/chat_models/ollama';
import { ChatPromptTemplate } from '@langchain/core/prompts';
import { StringOutputParser } from '@langchain/core/output_parsers';
import { RunnableSequence } from '@langchain/core/runnables';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { spawn } from 'child_process';

// Setup logger
const logger = pino({
  level: 'info',
  transport: {
    target: 'pino-pretty',
    options: { colorize: true }
  }
});

// Initialize Express
const app = express();
const PORT = process.env.PORT || 3002;

app.use(helmet());
app.use(cors());
app.use(express.json());

// Initialize Ollama with performance model
const llm = new ChatOllama({
  baseUrl: process.env.OLLAMA_URL || 'http://localhost:11434',
  model: process.env.MODEL_NAME || 'gemma3:4b', // High-performance model
  temperature: 0.2,
  maxTokens: 800,
});

// MCP Client for data tools
class MilhenaMCPClient {
  constructor() {
    this.client = null;
    this.mcpProcess = null;
    this.isConnected = false;
  }

  async initialize() {
    try {
      logger.info('🔗 Starting MCP Server...');
      
      // Start MCP server process
      this.mcpProcess = spawn('node', ['src/index.js'], {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: process.cwd()
      });

      // Create MCP client
      const transport = new StdioClientTransport({
        reader: this.mcpProcess.stdout,
        writer: this.mcpProcess.stdin
      });

      this.client = new Client(
        { name: "milhena-ai", version: "1.0.0" },
        { capabilities: {} }
      );

      await this.client.connect(transport);
      this.isConnected = true;
      
      logger.info('✅ MCP Client connected');
      return true;
      
    } catch (error) {
      logger.error('❌ MCP initialization failed:', error.message);
      return false;
    }
  }

  async callTool(name, args) {
    if (!this.isConnected) {
      throw new Error('MCP Client not connected');
    }

    try {
      const result = await this.client.callTool({ name, arguments: args });
      return result;
    } catch (error) {
      logger.error(`MCP Tool Error [${name}]:`, error.message);
      throw error;
    }
  }

  async getBusinessData(intent) {
    try {
      switch (intent) {
        case 'process_status':
          return await this.callTool('workflow.list', { active: true });
          
        case 'analytics':
          return await this.callTool('analytics.dashboard-overview', {});
          
        case 'troubleshooting':
          return await this.callTool('execution.list', { status: 'error', limit: 10 });
          
        case 'management':
          return await this.callTool('workflow.list', {});
          
        default:
          return { message: 'General system information available' };
      }
    } catch (error) {
      logger.warn('MCP data retrieval failed:', error.message);
      return { 
        error: 'Data temporarily unavailable',
        message: 'Business automation system operating normally'
      };
    }
  }
}

// Business prompt with data integration
const businessPrompt = ChatPromptTemplate.fromTemplate(`
RISPONDERE SEMPRE IN ITALIANO BUSINESS PROFESSIONALE.

Tu sei MILHENA, Manager Intelligente per processi aziendali.

ANALIZZA QUESTI DATI BUSINESS REALI:
{businessData}

DOMANDA: {query}

ISTRUZIONI OBBLIGATORIE:
1. ESTRAI informazioni specifiche dai dati
2. RISPONDI con numeri e metriche concrete
3. USA terminologia business (mai tecnica)
4. MASSIMO 3 frasi utili
5. CONCLUDI con domanda proattiva

ESEMPIO RISPOSTA CORRETTA:
"Hai 4 processi attivi con 99.5% successo. Processate 2280 operazioni risparmiando 189 ore. Vuoi vedere i dettagli di un processo specifico?"

RISPOSTA MILHENA:`);

// Initialize MCP client
const mcpClient = new MilhenaMCPClient();

// Main chat endpoint with MCP integration
app.post('/api/chat', async (req, res) => {
  try {
    const { query } = req.body;
    
    if (!query?.trim()) {
      return res.status(400).json({ 
        error: 'Query required',
        message: 'Dimmi cosa posso fare per te!'
      });
    }

    logger.info('MILHENA MCP Processing:', { query: query.substring(0, 100) });

    // Step 1: Classify intent
    const intent = classifyIntent(query);
    logger.info('Intent classified:', intent);

    // Step 2: Get business data via MCP
    const businessData = await mcpClient.getBusinessData(intent);
    logger.info('Business data retrieved via MCP');

    // Step 3: Generate response with LangChain
    const chain = RunnableSequence.from([
      businessPrompt,
      llm,
      new StringOutputParser(),
    ]);

    const response = await chain.invoke({
      businessData: JSON.stringify(businessData, null, 2),
      query
    });

    // Step 4: Sanitize response
    const sanitizedResponse = sanitizeBusinessTerms(response);

    logger.info('MILHENA MCP Response generated');

    res.json({
      response: sanitizedResponse,
      intent,
      source: 'milhena-mcp',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error('MILHENA MCP Error:', error.message);
    
    res.status(500).json({
      response: 'Mi dispiace, ho avuto un problema. Il sistema business opera normalmente. Riprova tra poco.',
      error: 'mcp_processing_error',
      timestamp: new Date().toISOString()
    });
  }
});

// Intent classification function
function classifyIntent(query) {
  const lowerQuery = query.toLowerCase();
  
  if (lowerQuery.includes('report') || lowerQuery.includes('analytics') || 
      lowerQuery.includes('settimana') || lowerQuery.includes('statistiche')) {
    return 'analytics';
  }
  
  if (lowerQuery.includes('processi') || lowerQuery.includes('stato') || 
      lowerQuery.includes('come va') || lowerQuery.includes('sistema')) {
    return 'process_status';
  }
  
  if (lowerQuery.includes('errori') || lowerQuery.includes('problemi')) {
    return 'troubleshooting';
  }
  
  if (lowerQuery.includes('avvia') || lowerQuery.includes('ferma') || lowerQuery.includes('attiva')) {
    return 'management';
  }
  
  return 'process_status';
}

// Business terminology sanitization
function sanitizeBusinessTerms(response) {
  const terminology = {
    'n8n': 'automation engine',
    'workflow': 'business process',
    'execution': 'operation',
    'node': 'step'
  };

  let sanitized = response;
  Object.entries(terminology).forEach(([tech, business]) => {
    const regex = new RegExp(tech, 'gi');
    sanitized = sanitized.replace(regex, business);
  });

  return sanitized;
}

// Health check
app.get('/api/health', async (req, res) => {
  try {
    const mcpStatus = mcpClient.isConnected ? 'connected' : 'disconnected';
    const modelTest = await llm.invoke('test');
    
    res.json({
      status: 'healthy',
      milhena: 'operational',
      mcp: mcpStatus,
      model: process.env.MODEL_NAME || 'gemma3:4b',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Initialize and start server
async function startServer() {
  try {
    logger.info('🤖 Starting MILHENA MCP Server...');
    
    // Initialize MCP client
    await mcpClient.initialize();
    
    app.listen(PORT, () => {
      logger.info(`🚀 MILHENA MCP Server running on port ${PORT}`);
      logger.info('🔗 MCP tools integrated for business data');
      logger.info(`🧠 Model: ${process.env.MODEL_NAME || 'gemma3:4b'} (high-performance)`);
    });
    
  } catch (error) {
    logger.error('Server startup failed:', error.message);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('MILHENA MCP shutting down...');
  if (mcpClient.mcpProcess) {
    mcpClient.mcpProcess.kill();
  }
  process.exit(0);
});

// Start the server
startServer();

export default app;