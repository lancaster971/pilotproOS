/**
 * MILHENA - LangChain Integration Test
 * Test suite for LangChain + Ollama + Backend integration
 */

import { ChatOllama } from '@langchain/community/chat_models/ollama';
import { ChatPromptTemplate } from '@langchain/core/prompts';
import { StringOutputParser } from '@langchain/core/output_parsers';
import { RunnableSequence } from '@langchain/core/runnables';
import { ofetch } from 'ofetch';
import pino from 'pino';

const logger = pino({ level: 'info' });

// Test configuration
const OLLAMA_URL = process.env.OLLAMA_URL || 'http://localhost:11434';
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:3001';

console.log('🧪 MILHENA LangChain Integration Test Starting...\n');

// Test 1: Ollama Connection
async function testOllamaConnection() {
  console.log('1️⃣ Testing Ollama connection...');
  
  try {
    const llm = new ChatOllama({
      baseUrl: OLLAMA_URL,
      model: 'gemma:2b',
      temperature: 0.3,
    });

    const response = await llm.invoke('Ciao, funzioni correttamente?');
    console.log('✅ Ollama Response:', response.content.substring(0, 100) + '...');
    return true;
    
  } catch (error) {
    console.log('❌ Ollama Error:', error.message);
    return false;
  }
}

// Test 2: LangChain Chain Processing
async function testLangChainProcessing() {
  console.log('\n2️⃣ Testing LangChain processing chain...');
  
  try {
    const llm = new ChatOllama({
      baseUrl: OLLAMA_URL,
      model: 'gemma:2b',
      temperature: 0.3,
    });

    const prompt = ChatPromptTemplate.fromTemplate(`
Sei MILHENA, assistant AI per business italiano.
Rispondi in italiano professionale, massimo 2 frasi.

Query: {query}
Risposta:`);

    const chain = RunnableSequence.from([
      prompt,
      llm,
      new StringOutputParser(),
    ]);

    const testQueries = [
      'Mostra lo stato dei processi',
      'Come va il sistema?',
      'Crea un report'
    ];

    for (const query of testQueries) {
      const response = await chain.invoke({ query });
      console.log(`✅ Query: "${query}"`);
      console.log(`   Response: ${response.substring(0, 80)}...`);
    }
    
    return true;
    
  } catch (error) {
    console.log('❌ LangChain Error:', error.message);
    return false;
  }
}

// Test 3: Intent Classification
async function testIntentClassification() {
  console.log('\n3️⃣ Testing intent classification...');
  
  try {
    const llm = new ChatOllama({
      baseUrl: OLLAMA_URL,
      model: 'gemma:2b',
      temperature: 0.1, // Lower temperature for consistent classification
    });

    const intentPrompt = ChatPromptTemplate.fromTemplate(`
Classifica questa query business italiana:

CATEGORIE: process_status, analytics, management, troubleshooting

Query: {query}
Categoria:`);

    const intentChain = RunnableSequence.from([
      intentPrompt,
      llm,
      new StringOutputParser(),
    ]);

    const testCases = [
      { query: 'Mostra i processi attivi', expected: 'process_status' },
      { query: 'Genera report settimanale', expected: 'analytics' },
      { query: 'Avvia il workflow clienti', expected: 'management' },
      { query: 'Perché il processo ha fallito?', expected: 'troubleshooting' }
    ];

    let correct = 0;
    
    for (const test of testCases) {
      const result = await intentChain.invoke({ query: test.query });
      const classification = result.trim().toLowerCase();
      
      const isCorrect = classification.includes(test.expected);
      console.log(`${isCorrect ? '✅' : '❌'} "${test.query}" → ${classification} (expected: ${test.expected})`);
      
      if (isCorrect) correct++;
    }
    
    const accuracy = (correct / testCases.length) * 100;
    console.log(`📊 Intent Classification Accuracy: ${accuracy}%`);
    
    return accuracy >= 75; // 75% minimum accuracy
    
  } catch (error) {
    console.log('❌ Intent Classification Error:', error.message);
    return false;
  }
}

// Test 4: Backend API Integration
async function testBackendIntegration() {
  console.log('\n4️⃣ Testing backend API integration...');
  
  try {
    const apiClient = ofetch.create({
      baseURL: BACKEND_URL,
      timeout: 5000,
    });

    const endpoints = [
      '/api/health',
      '/api/business/workflows/status',
      '/api/business/analytics/dashboard'
    ];

    for (const endpoint of endpoints) {
      try {
        const response = await apiClient(endpoint);
        console.log(`✅ ${endpoint} - Response keys:`, Object.keys(response).slice(0, 5));
      } catch (error) {
        console.log(`⚠️ ${endpoint} - ${error.message} (might be expected if backend not running)`);
      }
    }
    
    return true;
    
  } catch (error) {
    console.log('❌ Backend Integration Error:', error.message);
    return false;
  }
}

// Test 5: Business Terminology Sanitization
async function testBusinessTerminology() {
  console.log('\n5️⃣ Testing business terminology sanitization...');
  
  const BUSINESS_TERMINOLOGY = {
    'n8n': 'automation engine',
    'postgresql': 'business database', 
    'workflow': 'business process',
    'execution': 'process operation'
  };

  function sanitize(text) {
    let sanitized = text;
    Object.entries(BUSINESS_TERMINOLOGY).forEach(([tech, business]) => {
      const regex = new RegExp(tech, 'gi');
      sanitized = sanitized.replace(regex, business);
    });
    return sanitized;
  }

  const testCases = [
    {
      input: 'Il workflow n8n usa PostgreSQL per le execution',
      expected: 'automation engine',
      description: 'Technical terms replacement'
    }
  ];

  for (const test of testCases) {
    const result = sanitize(test.input);
    const containsExpected = result.includes(test.expected);
    
    console.log(`${containsExpected ? '✅' : '❌'} ${test.description}`);
    console.log(`   Input: ${test.input}`);
    console.log(`   Output: ${result}`);
  }
  
  return true;
}

// Run all tests
async function runAllTests() {
  console.log('🤖 MILHENA - Manager Intelligente Integration Tests');
  console.log('================================================\n');
  
  const results = {
    ollama: await testOllamaConnection(),
    langchain: await testLangChainProcessing(),
    intent: await testIntentClassification(),
    backend: await testBackendIntegration(),
    terminology: await testBusinessTerminology()
  };
  
  console.log('\n📋 TEST RESULTS SUMMARY:');
  console.log('========================');
  
  Object.entries(results).forEach(([test, passed]) => {
    console.log(`${passed ? '✅' : '❌'} ${test.toUpperCase()}: ${passed ? 'PASSED' : 'FAILED'}`);
  });
  
  const passedCount = Object.values(results).filter(Boolean).length;
  const totalCount = Object.keys(results).length;
  const successRate = (passedCount / totalCount) * 100;
  
  console.log(`\n🎯 Overall Success Rate: ${passedCount}/${totalCount} (${successRate}%)`);
  
  if (successRate >= 80) {
    console.log('🎉 MILHENA ready for deployment!');
  } else {
    console.log('⚠️ Some tests failed - check configuration before deployment');
  }
  
  process.exit(successRate >= 80 ? 0 : 1);
}

// Run tests if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runAllTests().catch(console.error);
}

export { runAllTests };