/**
 * MILHENA - AI Agent Server
 * Manager Intelligente con LangChain.js (ZERO custom code)
 * 
 * Following ZERO CUSTOM CODE policy - using battle-tested libraries only
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import pino from 'pino';
import { ChatOllama } from '@langchain/community/chat_models/ollama';
import { ChatPromptTemplate } from '@langchain/core/prompts';
import { StringOutputParser } from '@langchain/core/output_parsers';
import { RunnableSequence } from '@langchain/core/runnables';
import { ofetch } from 'ofetch';

// Setup Pino logger (following project standards)
const logger = pino({
  level: 'info',
  transport: {
    target: 'pino-pretty',
    options: {
      colorize: true,
      translateTime: 'SYS:standard',
      ignore: 'pid,hostname'
    }
  }
});

// Initialize Express app with security
const app = express();
const PORT = process.env.PORT || 3002;

// Middleware stack (following project patterns)
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true
}));
app.use(express.json({ limit: '10mb' }));

// Backend API client using OFETCH (following project HTTP client standard)
const backendUrl = process.env.BACKEND_URL || 'http://localhost:3001';
const apiClient = ofetch.create({
  baseURL: backendUrl,
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'MILHENA-AI-Agent/1.0.0'
  },
  timeout: 10000,
  onRequestError: ({ error }) => {
    logger.error('Backend API Error:', error.message);
  }
});

// Initialize Ollama with LangChain (battle-tested AI framework)
const llm = new ChatOllama({
  baseUrl: process.env.OLLAMA_URL || 'http://localhost:11434',
  model: 'gemma:2b', // Ultra-light model for speed
  temperature: 0.3,   // Consistent business responses
  maxTokens: 500,     // Limit for concise answers
});

// Business terminology sanitization (following project security patterns)
const BUSINESS_TERMINOLOGY = {
  'n8n': 'automation engine',
  'postgresql': 'business database',
  'postgres': 'business database', 
  'docker': 'service container',
  'workflow': 'business process',
  'execution': 'process operation',
  'node': 'process step',
  'trigger': 'event handler',
  'webhook': 'integration endpoint'
};

function sanitizeBusinessResponse(response) {
  let sanitized = response;
  
  // Apply business terminology translation
  Object.entries(BUSINESS_TERMINOLOGY).forEach(([tech, business]) => {
    const regex = new RegExp(tech, 'gi');
    sanitized = sanitized.replace(regex, business);
  });
  
  return sanitized;
}

// MILHENA Chat Prompt Template (Italian business-focused)
const chatPrompt = ChatPromptTemplate.fromTemplate(`
Sei MILHENA, Manager Intelligente per automazione processi business italiani.

REGOLE FONDAMENTALI:
- Rispondi SEMPRE in italiano professionale
- Massimo 3 frasi concise e utili
- USA SOLO terminologia business (mai termini tecnici)
- Se non hai informazioni specifiche, suggerisci di controllare la dashboard

CONTESTO SISTEMA: {context}
DOMANDA UTENTE: {question}

RISPOSTA MILHENA:`);

// Create LangChain processing chain (zero custom logic)
const processingChain = RunnableSequence.from([
  chatPrompt,
  llm,
  new StringOutputParser(),
]);

// Intent classification with LangChain
const intentPrompt = ChatPromptTemplate.fromTemplate(`
Classifica questa richiesta business italiana in UNA categoria:

CATEGORIE VALIDE:
- process_status: stato processi, sistema operativo, health check
- analytics: report, statistiche, metriche, performance
- management: avvia/ferma processi, controllo workflow
- troubleshooting: errori, problemi, diagnosi

QUERY: {query}

RISPONDI SOLO CON LA CATEGORIA (es: "process_status")`);

const intentChain = RunnableSequence.from([
  intentPrompt,
  llm,
  new StringOutputParser(),
]);

// Main MILHENA chat endpoint
app.post('/api/chat', async (req, res) => {
  try {
    const { query, context = {} } = req.body;
    
    if (!query?.trim()) {
      return res.status(400).json({ 
        error: 'Query richiesta',
        message: 'Dimmi cosa posso fare per te!'
      });
    }

    logger.info('MILHENA Processing Query', { 
      query: query.substring(0, 100),
      contextKeys: Object.keys(context)
    });

    // Step 1: Classify intent using LangChain
    const intent = await intentChain.invoke({ 
      query: query.trim().toLowerCase() 
    });
    
    const cleanIntent = intent.trim().toLowerCase();
    logger.info('Intent Classified', { intent: cleanIntent });

    // Step 2: Get business data from backend APIs (using existing endpoints)
    let businessData = {};
    
    try {
      switch (cleanIntent) {
        case 'process_status':
          businessData = await apiClient('/api/business/workflows/status');
          break;
          
        case 'analytics':
          businessData = await apiClient('/api/business/analytics/dashboard');
          break;
          
        case 'troubleshooting':
          businessData = await apiClient('/api/business/executions?status=error&limit=10');
          break;
          
        case 'management':
          businessData = await apiClient('/api/business/workflows');
          break;
          
        default:
          businessData = { message: 'Informazioni generali disponibili nella dashboard' };
      }
    } catch (apiError) {
      logger.warn('Backend API unavailable, using fallback', { error: apiError.message });
      businessData = { 
        fallback: true,
        message: 'Dati temporaneamente non disponibili, sistema operativo normale' 
      };
    }

    // Step 3: Generate business response using LangChain
    const contextString = JSON.stringify({
      intent: cleanIntent,
      data: businessData,
      timestamp: new Date().toISOString()
    });

    const response = await processingChain.invoke({
      context: contextString,
      question: query
    });

    // Step 4: Apply business terminology sanitization
    const sanitizedResponse = sanitizeBusinessResponse(response);

    logger.info('MILHENA Response Generated', { 
      intent: cleanIntent,
      responseLength: sanitizedResponse.length 
    });

    res.json({
      response: sanitizedResponse,
      intent: cleanIntent,
      timestamp: new Date().toISOString(),
      source: 'milhena-langchain'
    });

  } catch (error) {
    logger.error('MILHENA Processing Error', { 
      error: error.message,
      stack: error.stack 
    });
    
    // Emergency fallback (following project security patterns)
    res.status(500).json({
      response: 'Mi dispiace, ho avuto un problema tecnico. Il sistema di automazione business continua a funzionare normalmente. Riprova tra qualche istante.',
      error: 'processing_error',
      timestamp: new Date().toISOString()
    });
  }
});

// Health check endpoint
app.get('/api/health', async (req, res) => {
  try {
    // Test Ollama connection
    const ollamaTest = await llm.invoke('test');
    
    // Test backend connection  
    let backendStatus = 'unknown';
    try {
      await apiClient('/api/health');
      backendStatus = 'healthy';
    } catch {
      backendStatus = 'degraded';
    }

    res.json({
      status: 'healthy',
      milhena: 'operational',
      ollama: ollamaTest ? 'connected' : 'disconnected', 
      backend: backendStatus,
      model: 'gemma:2b',
      framework: 'langchain',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error('Health Check Failed', { error: error.message });
    
    res.status(503).json({
      status: 'unhealthy',
      milhena: 'degraded',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Start server
app.listen(PORT, () => {
  logger.info(`🤖 MILHENA AI Agent Server running on port ${PORT}`);
  logger.info('🔗 Using LangChain.js with Ollama Gemma:2b');
  logger.info('📡 Backend API:', backendUrl);
  logger.info('🧠 Model: Ultra-light Gemma:2b for Italian business queries');
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('MILHENA shutting down gracefully');
  process.exit(0);
});

export default app;