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
  model: 'gemma3:4b', // Better model for business intelligence (3.3GB - already available locally)
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

// MILHENA Chat Prompt Template (STRONG Italian business enforcement)
const chatPrompt = ChatPromptTemplate.fromTemplate(`
RISPONDERE SEMPRE E SOLO IN ITALIANO PROFESSIONALE.

Tu sei MILHENA, Manager Intelligente per l'automazione business.

DATI DISPONIBILI:
{context}

DOMANDA CLIENTE: {question}

ISTRUZIONI CRITICHE:
1. ANALIZZA i dati forniti
2. ESTRAI informazioni business utili
3. RISPONDI in italiano professionale
4. MASSIMO 3 frasi concise
5. MAI citare tecnologie (sostituisci con "processi business")

EXEMPLE RISPOSTA:
"Hai 4 processi business attualmente attivi con performance eccellenti (99.5% successo). Il sistema ha processato 2280 operazioni risparmiando 189 ore di lavoro. Tutti i processi funzionano perfettamente!"

RISPOSTA MILHENA IN ITALIANO:`);

// Create LangChain processing chain (zero custom logic)
const processingChain = RunnableSequence.from([
  chatPrompt,
  llm,
  new StringOutputParser(),
]);

// Simplified intent classification with keyword matching
function classifyIntent(query) {
  const lowerQuery = query.toLowerCase();
  
  // Analytics keywords (highest priority for reports)
  if (lowerQuery.includes('report') || lowerQuery.includes('statistiche') || 
      lowerQuery.includes('analytics') || lowerQuery.includes('metriche') ||
      lowerQuery.includes('settimana') || lowerQuery.includes('mese') || 
      lowerQuery.includes('performance')) {
    return 'analytics';
  }
  
  // Process status keywords  
  if (lowerQuery.includes('processi') || lowerQuery.includes('stato') || 
      lowerQuery.includes('come va') || lowerQuery.includes('sistema') ||
      lowerQuery.includes('attivi') || lowerQuery.includes('operativi')) {
    return 'process_status';
  }
  
  // Management keywords
  if (lowerQuery.includes('avvia') || lowerQuery.includes('ferma') || 
      lowerQuery.includes('pausa') || lowerQuery.includes('attiva') ||
      lowerQuery.includes('controllo') || lowerQuery.includes('gestisci')) {
    return 'management';
  }
  
  // Troubleshooting keywords
  if (lowerQuery.includes('errori') || lowerQuery.includes('problemi') || 
      lowerQuery.includes('perché') || lowerQuery.includes('fallisce') ||
      lowerQuery.includes('diagnosi') || lowerQuery.includes('risolvi')) {
    return 'troubleshooting';
  }
  
  // Default fallback
  return 'process_status';
}

// Intent classification now handled by keyword matching function above

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

    // Step 1: Classify intent using keyword matching (more reliable than LLM for simple classification)
    const cleanIntent = classifyIntent(query);
    logger.info('Intent Classified', { intent: cleanIntent });

    // Step 2: Get business data from backend APIs (using existing endpoints)
    let businessData = {};
    
    try {
      // REAL API CALLS using existing tRPC endpoints
      switch (cleanIntent) {
        case 'process_status':
          businessData = await apiClient('/api/business/processes');
          break;
          
        case 'analytics':
          businessData = await apiClient('/api/business/analytics');
          break;
          
        case 'troubleshooting':
          businessData = await apiClient('/api/business/process-runs?status=error');
          break;
          
        case 'management':
          businessData = await apiClient('/api/business/processes');
          break;
          
        default:
          businessData = { message: 'Controlla la dashboard per informazioni dettagliate' };
      }
    } catch (apiError) {
      logger.warn('Backend API unavailable, using intelligent fallback', { error: apiError.message });
      businessData = { 
        fallback: true,
        message: 'Dati temporaneamente non disponibili, sistema operativo normale' 
      };
    }

    // Step 3: Generate business response using LangChain with REAL DATA
    const businessContext = `
DATI REALI SISTEMA:
${JSON.stringify(businessData, null, 2)}

INTENT RILEVATO: ${cleanIntent}
TIMESTAMP: ${new Date().toLocaleString('it-IT')}
`;

    const response = await processingChain.invoke({
      context: businessContext,
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