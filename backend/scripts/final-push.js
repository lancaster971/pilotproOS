#!/usr/bin/env node

/**
 * Final Push - Map the remaining 18 nodes to reach 80%
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const OUTPUT_FILE = path.join(__dirname, '../src/data/icon-mapping.js');
const LOCAL_ICON_PATH = path.join(__dirname, '../n8n-icons');

// The 18 unmapped nodes
const unmappedNodes = [
  '@n8n/n8n-nodes-langchain.chainLlm',
  '@n8n/n8n-nodes-langchain.chainSummarization', 
  '@n8n/n8n-nodes-langchain.memoryBufferWindow',
  '@n8n/n8n-nodes-langchain.outputParserStructured',
  '@n8n/n8n-nodes-langchain.retrieverVectorStore',
  '@n8n/n8n-nodes-langchain.toolVectorStore',
  'n8n-nodes-base.cron',
  'n8n-nodes-base.dateTimeTool',
  'n8n-nodes-base.emailReadImap',
  'n8n-nodes-base.emailSend',
  'n8n-nodes-base.function',
  'n8n-nodes-base.manualTrigger',
  'n8n-nodes-base.noOp',
  'n8n-nodes-base.scheduleTrigger',
  'n8n-nodes-base.splitInBatches',
  'n8n-nodes-base.stickyNote',
  'n8n-nodes-base.switch',
  'n8n-nodes-base.wait'
];

console.log('🎯 FINAL PUSH - Mapping remaining 18 nodes');
console.log('==========================================');

// Manual curated mappings for the remaining nodes
const manualMappings = {
  // LangChain nodes - use semantic matching
  '@n8n/n8n-nodes-langchain.chainLlm': '/app/n8n-icons/langchain-nodes/chains/ChainLLM/chainLLM.svg', // Generic chain icon
  '@n8n/n8n-nodes-langchain.chainSummarization': '/app/n8n-icons/langchain-nodes/chains/ChainSummarization/chainSummarization.svg', // Summary icon
  '@n8n/n8n-nodes-langchain.memoryBufferWindow': '/app/n8n-icons/langchain-nodes/memory/MemoryBufferWindow/buffer.svg', // Memory icon
  '@n8n/n8n-nodes-langchain.outputParserStructured': '/app/n8n-icons/langchain-nodes/output_parser/OutputParserStructured/parser.svg', // Parser icon
  '@n8n/n8n-nodes-langchain.retrieverVectorStore': '/app/n8n-icons/langchain-nodes/retrievers/RetrieverVectorStore/retriever.svg', // Retriever icon
  '@n8n/n8n-nodes-langchain.toolVectorStore': '/app/n8n-icons/langchain-nodes/tools/ToolVectorStore/vectorstore.svg', // Vector tool icon
  
  // n8n base nodes - find the best matches from available icons
  'n8n-nodes-base.cron': '/app/n8n-icons/base-nodes/Cron/cron.svg', // Time/schedule icon
  'n8n-nodes-base.dateTimeTool': '/app/n8n-icons/base-nodes/DateTime/dateTime.svg', // Date/time icon
  'n8n-nodes-base.emailReadImap': '/app/n8n-icons/base-nodes/EmailReadImap/emailReadImap.svg', // Email read icon
  'n8n-nodes-base.emailSend': '/app/n8n-icons/base-nodes/EmailSend/emailSend.svg', // Email send icon  
  'n8n-nodes-base.function': '/app/n8n-icons/base-nodes/Function/function.svg', // Function icon
  'n8n-nodes-base.manualTrigger': '/app/n8n-icons/base-nodes/ManualTrigger/manualTrigger.svg', // Manual trigger icon
  'n8n-nodes-base.noOp': '/app/n8n-icons/base-nodes/NoOp/noOp.svg', // No-op icon
  'n8n-nodes-base.scheduleTrigger': '/app/n8n-icons/base-nodes/ScheduleTrigger/scheduleTrigger.svg', // Schedule trigger icon
  'n8n-nodes-base.splitInBatches': '/app/n8n-icons/base-nodes/SplitInBatches/splitInBatches.svg', // Split icon
  'n8n-nodes-base.stickyNote': '/app/n8n-icons/base-nodes/StickyNote/stickyNote.svg', // Sticky note icon
  'n8n-nodes-base.switch': '/app/n8n-icons/base-nodes/Switch/switch.svg', // Switch/condition icon
  'n8n-nodes-base.wait': '/app/n8n-icons/base-nodes/Wait/wait.svg' // Wait/delay icon
};

// Function to find best available icons
function findBestIcon(nodeType) {
  // Try manual mapping first
  if (manualMappings[nodeType]) {
    const iconPath = manualMappings[nodeType];
    const localPath = iconPath.replace('/app/n8n-icons/', '');
    const fullLocalPath = path.join(LOCAL_ICON_PATH, localPath);
    
    if (fs.existsSync(fullLocalPath)) {
      return iconPath;
    }
  }
  
  // Fallback strategies for each node type
  const fallbackStrategies = {
    // LangChain fallbacks
    '@n8n/n8n-nodes-langchain.chainLlm': [
      '/app/n8n-icons/langchain-nodes/llms/LMChatOpenAi/openAiLight.svg',
      '/app/n8n-icons/base-nodes/OpenAi/openAi.svg'
    ],
    '@n8n/n8n-nodes-langchain.chainSummarization': [
      '/app/n8n-icons/langchain-nodes/llms/LMChatOpenAi/openAiLight.svg',
      '/app/n8n-icons/base-nodes/Transform/aggregate.svg'
    ],
    '@n8n/n8n-nodes-langchain.memoryBufferWindow': [
      '/app/n8n-icons/langchain-nodes/memory/MemoryPostgresChat/postgres.svg',
      '/app/n8n-icons/base-nodes/Redis/redis.svg'
    ],
    '@n8n/n8n-nodes-langchain.outputParserStructured': [
      '/app/n8n-icons/base-nodes/Transform/aggregate.svg',
      '/app/n8n-icons/base-nodes/Code/code.svg'
    ],
    '@n8n/n8n-nodes-langchain.retrieverVectorStore': [
      '/app/n8n-icons/langchain-nodes/vector_store/VectorStoreQdrant/qdrant.svg',
      '/app/n8n-icons/base-nodes/Postgres/postgres.svg'
    ],
    '@n8n/n8n-nodes-langchain.toolVectorStore': [
      '/app/n8n-icons/langchain-nodes/vector_store/VectorStoreSupabase/supabase.svg',
      '/app/n8n-icons/base-nodes/Supabase/supabase.svg'
    ],
    
    // Base nodes fallbacks  
    'n8n-nodes-base.cron': [
      '/app/n8n-icons/base-nodes/Transform/schedule.svg',
      '/app/n8n-icons/base-nodes/DateTime/dateTime.svg',
      '/app/n8n-icons/base-nodes/Timer/timer.svg'
    ],
    'n8n-nodes-base.dateTimeTool': [
      '/app/n8n-icons/base-nodes/DateTime/dateTime.svg',
      '/app/n8n-icons/base-nodes/Transform/aggregate.svg'
    ],
    'n8n-nodes-base.emailReadImap': [
      '/app/n8n-icons/base-nodes/Email/email.svg',
      '/app/n8n-icons/base-nodes/Google/Gmail/gmail.svg',
      '/app/n8n-icons/base-nodes/Microsoft/Outlook/outlook.svg'
    ],
    'n8n-nodes-base.emailSend': [
      '/app/n8n-icons/base-nodes/EmailSend/emailSend.svg',
      '/app/n8n-icons/base-nodes/Google/Gmail/gmail.svg',
      '/app/n8n-icons/base-nodes/Microsoft/Outlook/outlook.svg'
    ],
    'n8n-nodes-base.function': [
      '/app/n8n-icons/base-nodes/Code/code.svg',
      '/app/n8n-icons/base-nodes/Function/function.svg'
    ],
    'n8n-nodes-base.manualTrigger': [
      '/app/n8n-icons/base-nodes/ManualTrigger/manualTrigger.svg',
      '/app/n8n-icons/base-nodes/Webhook/webhook.svg',
      '/app/n8n-icons/base-nodes/Start/start.svg'
    ],
    'n8n-nodes-base.noOp': [
      '/app/n8n-icons/base-nodes/NoOp/noOp.svg',
      '/app/n8n-icons/base-nodes/Debug/debug.svg'
    ],
    'n8n-nodes-base.scheduleTrigger': [
      '/app/n8n-icons/base-nodes/Cron/cron.svg',
      '/app/n8n-icons/base-nodes/Timer/timer.svg',
      '/app/n8n-icons/base-nodes/DateTime/dateTime.svg'
    ],
    'n8n-nodes-base.splitInBatches': [
      '/app/n8n-icons/base-nodes/SplitInBatches/splitInBatches.svg',
      '/app/n8n-icons/base-nodes/Transform/SplitOut/splitOut.svg'
    ],
    'n8n-nodes-base.stickyNote': [
      '/app/n8n-icons/base-nodes/StickyNote/stickyNote.svg',
      '/app/n8n-icons/base-nodes/PostBin/postbin.svg'
    ],
    'n8n-nodes-base.switch': [
      '/app/n8n-icons/base-nodes/Switch/switch.svg',
      '/app/n8n-icons/base-nodes/If/if.svg'
    ],
    'n8n-nodes-base.wait': [
      '/app/n8n-icons/base-nodes/Wait/wait.svg',
      '/app/n8n-icons/base-nodes/Timer/timer.svg'
    ]
  };
  
  const fallbacks = fallbackStrategies[nodeType] || [];
  
  for (const iconPath of fallbacks) {
    const localPath = iconPath.replace('/app/n8n-icons/', '');
    const fullLocalPath = path.join(LOCAL_ICON_PATH, localPath);
    
    if (fs.existsSync(fullLocalPath)) {
      return iconPath;
    }
  }
  
  return null;
}

// Import current mapping
import { iconMapping } from '../src/data/icon-mapping.js';

console.log('\\nMapping remaining nodes...');

let newMappings = 0;
const finalMapping = { ...iconMapping };

// No need for duplicated mapping - using imported iconMapping

for (const nodeType of unmappedNodes) {
  const iconPath = findBestIcon(nodeType);
  
  if (iconPath) {
    finalMapping[nodeType] = iconPath;
    newMappings++;
    console.log(`✅ ${nodeType} → ${iconPath.replace('/app/n8n-icons/', '')}`);
  } else {
    console.log(`❌ ${nodeType} → No suitable icon found`);
  }
}

// Calculate final coverage
const totalNodes = 64;
const mappedNodes = Object.keys(finalMapping).length;
const coverage = (mappedNodes / totalNodes * 100).toFixed(1);

console.log(`\\n🎊 FINAL PUSH COMPLETED!`);
console.log(`📊 New mappings: ${newMappings}`);
console.log(`📊 Total mapped: ${mappedNodes}/${totalNodes}`);
console.log(`📊 Final coverage: ${coverage}%`);

// Write the final mapping
const finalContent = `// N8N Icon Mapping - FINAL VERSION
// Generated on: ${new Date().toISOString()}
// Total NodeTypes: ${totalNodes}
// Mapped: ${mappedNodes}
// Coverage: ${coverage}%

export const iconMapping = ${JSON.stringify(finalMapping, null, 2)};

// Helper function to get icon path
export function getIconPath(nodeType) {
  return iconMapping[nodeType] || null;
}

// Statistics
export const mappingStats = {
  totalNodeTypes: ${totalNodes},
  mapped: ${mappedNodes},
  coverage: ${parseFloat(coverage)}
};

// Default export
export default iconMapping;
`;

fs.writeFileSync(OUTPUT_FILE, finalContent, 'utf8');

if (parseFloat(coverage) >= 80) {
  console.log('\\n🎉 SUCCESS: 80%+ coverage achieved!');
} else {
  console.log(`\\n⚠️ Close but not quite: ${coverage}% (need 80%)`);
}