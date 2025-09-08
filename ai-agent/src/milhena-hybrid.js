/**
 * MILHENA Hybrid AI Agent
 * Local Ollama (privacy) + External API fallback (quality)
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

const logger = pino({ level: 'info', transport: { target: 'pino-pretty' } });
const app = express();
const PORT = process.env.PORT || 3002;

app.use(helmet());
app.use(cors());
app.use(express.json());

// Backend API client
const apiClient = ofetch.create({
  baseURL: process.env.BACKEND_URL || 'http://localhost:3001',
  timeout: 10000,
});

// Local Ollama (primary)
const localLLM = new ChatOllama({
  baseUrl: process.env.OLLAMA_URL || 'http://localhost:11434',
  model: 'gemma3:4b',
  temperature: 0.2,
  maxTokens: 800,
});

// External API fallback (if enabled)
const externalApiKey = process.env.CLAUDE_API_KEY || process.env.OPENAI_API_KEY;
const useExternalFallback = !!externalApiKey;

// Business prompt template
const businessPrompt = ChatPromptTemplate.fromTemplate(`
RISPONDERE SEMPRE IN ITALIANO BUSINESS PROFESSIONALE.

Tu sei MILHENA, Manager Intelligente aziendale.

DATI BUSINESS REALI:
{businessData}

DOMANDA: {query}

ISTRUZIONI:
1. ANALIZZA i dati numerici specifici
2. ESTRAI insights business concreti  
3. RISPONDI con metriche precise
4. BUSINESS language only (no tech terms)
5. PROATTIVO con next steps

RISPOSTA MILHENA:`);

// Intent classification
function classifyIntent(query) {
  const q = query.toLowerCase();
  
  if (q.includes('report') || q.includes('analytics') || q.includes('settimana') || q.includes('statistiche')) {
    return 'analytics';
  }
  if (q.includes('processi') || q.includes('stato') || q.includes('come va')) {
    return 'process_status';
  }
  if (q.includes('errori') || q.includes('problemi')) {
    return 'troubleshooting';
  }
  if (q.includes('avvia') || q.includes('ferma')) {
    return 'management';
  }
  
  return 'process_status';
}

// Get business data
async function getBusinessData(intent) {
  try {
    switch (intent) {
      case 'process_status':
        return await apiClient('/api/business/processes');
        
      case 'analytics':
        return await apiClient('/api/business/analytics');
        
      case 'troubleshooting':
        return await apiClient('/api/business/process-runs', { params: { status: 'error' } });
        
      case 'management':
        return await apiClient('/api/business/processes');
        
      default:
        return { message: 'System operational' };
    }
  } catch (error) {
    logger.warn('API Error:', error.message);
    throw new Error('Backend data unavailable');
  }
}

// External API fallback
async function callExternalAI(prompt, businessData) {
  if (!useExternalFallback) {
    throw new Error('External AI not configured');
  }

  const fullPrompt = `${prompt}\n\nDATI: ${JSON.stringify(businessData)}`;
  
  if (process.env.CLAUDE_API_KEY) {
    // Claude API call
    const response = await ofetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.CLAUDE_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: {
        model: 'claude-3-haiku-20240307',
        max_tokens: 500,
        messages: [{ role: 'user', content: fullPrompt }]
      }
    });
    
    return response.content[0].text;
  }
  
  throw new Error('No external AI configured');
}

// Main chat endpoint
app.post('/api/chat', async (req, res) => {
  try {
    const { query } = req.body;
    
    if (!query?.trim()) {
      return res.status(400).json({ error: 'Query required' });
    }

    logger.info('MILHENA Hybrid Processing:', { query: query.substring(0, 100) });

    // Step 1: Intent classification
    const intent = classifyIntent(query);
    
    // Step 2: Get real business data
    const businessData = await getBusinessData(intent);
    
    // Step 3: Try local AI first
    let response;
    let source = 'local-ollama';
    
    try {
      const chain = RunnableSequence.from([
        businessPrompt,
        localLLM,
        new StringOutputParser(),
      ]);

      response = await chain.invoke({
        businessData: JSON.stringify(businessData, null, 2),
        query
      });
      
    } catch (ollamaError) {
      logger.warn('Local Ollama failed, trying external API:', ollamaError.message);
      
      if (useExternalFallback) {
        try {
          response = await callExternalAI(
            'RISPONDERE IN ITALIANO BUSINESS. Tu sei MILHENA, consulente aziendale. Analizza i dati e rispondi con insights specifici in 2-3 frasi.',
            businessData
          );
          source = 'external-api';
        } catch (externalError) {
          throw new Error('Both local and external AI failed');
        }
      } else {
        throw ollamaError;
      }
    }

    // Step 4: Sanitize response
    const sanitizedResponse = response
      .replace(/n8n/gi, 'automation engine')
      .replace(/workflow/gi, 'business process')
      .replace(/execution/gi, 'operation');

    logger.info('MILHENA Response generated:', { source, intent });

    res.json({
      response: sanitizedResponse,
      intent,
      source,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error('MILHENA Hybrid Error:', error.message);
    
    res.status(500).json({
      response: 'Mi dispiace, ho avuto un problema tecnico. Il sistema business opera normalmente.',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Health check
app.get('/api/health', async (req, res) => {
  try {
    const localTest = await localLLM.invoke('test');
    
    res.json({
      status: 'healthy',
      milhena: 'operational',
      localAI: !!localTest,
      externalFallback: useExternalFallback,
      model: 'gemma3:4b + external fallback',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(503).json({
      status: 'degraded',
      error: error.message
    });
  }
});

// Start server
app.listen(PORT, () => {
  logger.info(`🚀 MILHENA Hybrid AI Server running on port ${PORT}`);
  logger.info(`🧠 Local: gemma3:4b | External: ${useExternalFallback ? 'enabled' : 'disabled'}`);
});

export default app;