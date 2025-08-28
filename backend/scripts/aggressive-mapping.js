#!/usr/bin/env node

/**
 * Aggressive Icon Mapping Generator
 * 
 * This script aggressively maps icons to reach 80%+ coverage
 * by trying multiple strategies and creating best-guess mappings.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { Pool } from 'pg';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const ICON_BASE_PATH = '/app/n8n-icons';
const LOCAL_ICON_PATH = path.join(__dirname, '../n8n-icons');
const OUTPUT_FILE = path.join(__dirname, '../src/data/icon-mapping.js');

// Database connection
const dbPool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'pilotpros_db',
  user: process.env.DB_USER || 'pilotpros_user',
  password: process.env.DB_PASSWORD || 'pilotpros_password',
});

/**
 * Get all database node types
 */
async function getDatabaseNodeTypes() {
  try {
    const query = `
      SELECT id, name, nodes
      FROM n8n.workflow_entity 
      WHERE nodes IS NOT NULL 
        AND json_array_length(nodes) > 0
    `;
    
    const result = await dbPool.query(query);
    const allNodeTypes = new Set();
    
    for (const row of result.rows) {
      try {
        const nodes = row.nodes;
        if (Array.isArray(nodes)) {
          for (const node of nodes) {
            if (node && node.type && typeof node.type === 'string') {
              allNodeTypes.add(node.type);
            }
          }
        }
      } catch (parseError) {
        console.warn(`⚠️ Failed to parse nodes for workflow ${row.id}:`, parseError.message);
      }
    }
    
    return Array.from(allNodeTypes).sort();
  } catch (error) {
    console.error('❌ Database query failed:', error.message);
    return [];
  }
}

/**
 * Scan for SVG files
 */
function scanForSVGFiles(dir) {
  const svgFiles = [];
  
  function scanRecursive(currentDir) {
    try {
      const items = fs.readdirSync(currentDir);
      
      for (const item of items) {
        const fullPath = path.join(currentDir, item);
        const stat = fs.statSync(fullPath);
        
        if (stat.isDirectory()) {
          scanRecursive(fullPath);
        } else if (item.endsWith('.svg')) {
          const relativePath = path.relative(LOCAL_ICON_PATH, fullPath);
          svgFiles.push({
            filename: item,
            relativePath: relativePath,
            fullPath: fullPath,
            dockerPath: path.join(ICON_BASE_PATH, relativePath)
          });
        }
      }
    } catch (error) {
      // Ignore directory read errors
    }
  }
  
  scanRecursive(dir);
  return svgFiles;
}

/**
 * AGGRESSIVE MAPPING - Multiple strategies
 */
function aggressiveMapping(nodeTypes, svgFiles) {
  const mapping = {};
  const mapped = new Set();
  
  console.log('🎯 AGGRESSIVE MAPPING STRATEGIES');
  console.log('=================================');
  
  // Strategy 1: Exact matches
  console.log('\n📍 Strategy 1: Exact filename matches');
  for (const nodeType of nodeTypes) {
    if (mapped.has(nodeType)) continue;
    
    // Try direct filename matches
    const candidates = svgFiles.filter(f => {
      const name = f.filename.replace('.svg', '');
      return name === nodeType || 
             name === nodeType.replace('n8n-nodes-base.', '') ||
             name === nodeType.replace('@n8n/n8n-nodes-langchain.', '') ||
             `n8n-nodes-base.${name}` === nodeType;
    });
    
    if (candidates.length > 0) {
      mapping[nodeType] = candidates[0].dockerPath;
      mapped.add(nodeType);
      console.log(`✅ ${nodeType} → ${candidates[0].relativePath}`);
    }
  }
  
  // Strategy 2: Base-nodes directory mapping
  console.log(`\\n📍 Strategy 2: Base-nodes directory mapping (${mapped.size} already mapped)`);
  for (const nodeType of nodeTypes) {
    if (mapped.has(nodeType)) continue;
    
    let serviceName = nodeType.replace('n8n-nodes-base.', '');
    if (serviceName === nodeType) continue; // Skip non-base nodes
    
    // Try variations of service name
    const serviceVariations = [
      serviceName,
      serviceName.charAt(0).toUpperCase() + serviceName.slice(1),
      serviceName.toLowerCase()
    ];
    
    for (const variation of serviceVariations) {
      const candidates = svgFiles.filter(f => 
        f.relativePath.includes(`base-nodes/${variation}/`)
      );
      
      if (candidates.length > 0) {
        // Prefer non-dark versions
        const preferred = candidates.find(c => !c.filename.includes('.dark.')) || candidates[0];
        mapping[nodeType] = preferred.dockerPath;
        mapped.add(nodeType);
        console.log(`✅ ${nodeType} → ${preferred.relativePath}`);
        break;
      }
    }
  }
  
  // Strategy 3: LangChain mapping (ENHANCED)
  console.log(`\\n📍 Strategy 3: Enhanced LangChain mapping (${mapped.size} already mapped)`);
  for (const nodeType of nodeTypes) {
    if (mapped.has(nodeType)) continue;
    if (!nodeType.startsWith('@n8n/n8n-nodes-langchain.')) continue;
    
    const langchainType = nodeType.replace('@n8n/n8n-nodes-langchain.', '');
    
    // Map of LangChain patterns
    const langchainMappings = {
      // LLMs and Chat Models
      'lmChatOpenAi': ['llms/LMChatOpenAi', 'llms/LmChatOpenAi'],
      'lmChatAnthropic': ['llms/LMChatAnthropic', 'llms/LmChatAnthropic'],
      'lmChatCohere': ['llms/LmChatCohere'],
      'lmChatGoogleGemini': ['llms/LmChatGoogleGemini'],
      'lmOpenAi': ['llms/LMOpenAi', 'llms/LmOpenAi'],
      
      // Embeddings
      'embeddingsOpenAi': ['embeddings/EmbeddingsOpenAI'],
      'embeddingsCohere': ['embeddings/EmbeddingsCohere'],
      'embeddingsGoogleGemini': ['embeddings/EmbeddingsGoogleGemini'],
      
      // Agents
      'agent': ['agents/Agent'],
      'openAiAssistant': ['agents/OpenAiAssistant'],
      
      // Chains
      'chainLlm': ['chains/ChainLLM'],
      'chainSummarization': ['chains/ChainSummarization'],
      'chainRetrievalQa': ['chains/ChainRetrievalQA'],
      
      // Memory
      'memoryBufferWindow': ['memory/MemoryBufferWindow'],
      'memoryPostgresChat': ['memory/MemoryPostgresChat'],
      'memoryRedisChat': ['memory/MemoryRedisChat'],
      'memoryMongoDbChat': ['memory/MemoryMongoDbChat'],
      
      // Tools
      'toolWorkflow': ['tools/ToolWorkflow'],
      'toolVectorStore': ['tools/ToolVectorStore'],
      'toolHttpRequest': ['tools/ToolHttpRequest'],
      'toolCalculator': ['tools/ToolCalculator'],
      'toolCode': ['tools/ToolCode'],
      
      // Document Loaders
      'documentDefaultDataLoader': ['document_loaders/DocumentDefaultDataLoader'],
      'documentBinaryInputLoader': ['document_loaders/DocumentBinaryInputLoader'],
      
      // Text Splitters
      'textSplitterTokenSplitter': ['text_splitters/TextSplitterTokenSplitter'],
      'textSplitterRecursiveCharacterTextSplitter': ['text_splitters/TextSplitterRecursiveCharacterTextSplitter'],
      
      // Vector Stores
      'vectorStoreSupabase': ['vector_store/VectorStoreSupabase'],
      'vectorStoreQdrant': ['vector_store/VectorStoreQdrant'],
      'vectorStorePinecone': ['vector_store/VectorStorePinecone'],
      'vectorStorePGVector': ['vector_store/VectorStorePGVector'],
      
      // Output Parsers
      'outputParserStructured': ['output_parser/OutputParserStructured'],
      
      // Triggers
      'chatTrigger': ['trigger/ChatTrigger'],
      
      // MCP
      'mcpClientTool': ['mcp/McpClientTool'],
      
      // Retrievers
      'retrieverVectorStore': ['retrievers/RetrieverVectorStore'],
      
      // Generic patterns for anything else
      'textClassifier': ['chains/TextClassifier'],
      'informationExtractor': ['chains/InformationExtractor']
    };
    
    const mappingCandidates = langchainMappings[langchainType] || [langchainType];
    
    for (const candidate of mappingCandidates) {
      const matches = svgFiles.filter(f => 
        f.relativePath.includes(`langchain-nodes/${candidate}/`)
      );
      
      if (matches.length > 0) {
        // Prefer non-dark, non-white versions
        const preferred = matches.find(c => !c.filename.includes('.dark.') && !c.filename.includes('.white.')) || matches[0];
        mapping[nodeType] = preferred.dockerPath;
        mapped.add(nodeType);
        console.log(`✅ ${nodeType} → ${preferred.relativePath}`);
        break;
      }
    }
  }
  
  // Strategy 4: Vendor/service name matching
  console.log(`\\n📍 Strategy 4: Service name fuzzy matching (${mapped.size} already mapped)`);
  for (const nodeType of nodeTypes) {
    if (mapped.has(nodeType)) continue;
    
    // Extract potential service names from nodeType
    let serviceName = nodeType;
    if (serviceName.startsWith('n8n-nodes-base.')) {
      serviceName = serviceName.replace('n8n-nodes-base.', '');
    } else if (serviceName.startsWith('@n8n/n8n-nodes-langchain.')) {
      serviceName = serviceName.replace('@n8n/n8n-nodes-langchain.', '');
    }
    
    // Common service name patterns
    const servicePatterns = [
      serviceName,
      serviceName.toLowerCase(),
      serviceName.charAt(0).toUpperCase() + serviceName.slice(1),
      serviceName.replace(/([A-Z])/g, '-$1').toLowerCase().replace(/^-/, ''), // camelCase to kebab-case
      serviceName.replace(/Trigger$/, ''), // Remove trigger suffix
      serviceName.replace(/Tool$/, ''), // Remove tool suffix
      serviceName.replace(/Chat$/, ''), // Remove chat suffix
    ];
    
    for (const pattern of servicePatterns) {
      const matches = svgFiles.filter(f => {
        const filename = f.filename.replace('.svg', '').toLowerCase();
        const patternLower = pattern.toLowerCase();
        
        return filename === patternLower ||
               filename.includes(patternLower) ||
               patternLower.includes(filename) ||
               f.relativePath.toLowerCase().includes(patternLower);
      });
      
      if (matches.length > 0) {
        // Score matches by preference
        const scored = matches.map(m => {
          let score = 0;
          const filename = m.filename.replace('.svg', '').toLowerCase();
          const patternLower = pattern.toLowerCase();
          
          if (filename === patternLower) score += 10;
          if (filename.includes(patternLower)) score += 5;
          if (!m.filename.includes('.dark.')) score += 2;
          if (m.relativePath.includes('base-nodes/')) score += 1;
          
          return { ...m, score };
        });
        
        scored.sort((a, b) => b.score - a.score);
        const best = scored[0];
        
        mapping[nodeType] = best.dockerPath;
        mapped.add(nodeType);
        console.log(`✅ ${nodeType} → ${best.relativePath} (fuzzy match)`);
        break;
      }
    }
  }
  
  return { mapping, mapped: mapped.size };
}

/**
 * Write the mapping file
 */
function writeMappingFile(mapping, totalNodeTypes) {
  const mappedCount = Object.keys(mapping).length;
  const coverage = (mappedCount / totalNodeTypes * 100).toFixed(1);
  
  const content = `// N8N Icon Mapping - AGGRESSIVE MAPPING
// Generated on: ${new Date().toISOString()}
// Total NodeTypes: ${totalNodeTypes}
// Mapped: ${mappedCount}
// Coverage: ${coverage}%

export const iconMapping = ${JSON.stringify(mapping, null, 2)};

// Helper function to get icon path
export function getIconPath(nodeType) {
  return iconMapping[nodeType] || null;
}

// Statistics
export const mappingStats = {
  totalNodeTypes: ${totalNodeTypes},
  mapped: ${mappedCount},
  coverage: ${coverage}
};

// Default export
export default iconMapping;
`;
  
  // Ensure data directory exists
  const dataDir = path.dirname(OUTPUT_FILE);
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  
  fs.writeFileSync(OUTPUT_FILE, content, 'utf8');
  console.log(`\\n💾 Aggressive mapping saved to: ${OUTPUT_FILE}`);
  console.log(`🎯 COVERAGE: ${coverage}% (${mappedCount}/${totalNodeTypes})`);
  
  return { mappedCount, coverage: parseFloat(coverage) };
}

/**
 * Main execution
 */
async function main() {
  console.log('🚀 AGGRESSIVE N8N Icon Mapping Generator');
  console.log('=========================================');
  
  try {
    // Get database node types
    console.log('\\n🗄️ Getting database node types...');
    const nodeTypes = await getDatabaseNodeTypes();
    console.log(`Found ${nodeTypes.length} unique node types`);
    
    // Scan SVG files
    console.log('\\n📁 Scanning SVG files...');
    const svgFiles = scanForSVGFiles(LOCAL_ICON_PATH);
    console.log(`Found ${svgFiles.length} SVG files`);
    
    // Aggressive mapping
    const { mapping, mapped } = aggressiveMapping(nodeTypes, svgFiles);
    
    // Write mapping file
    const { mappedCount, coverage } = writeMappingFile(mapping, nodeTypes.length);
    
    console.log('\\n🎊 AGGRESSIVE MAPPING COMPLETED!');
    console.log(`📊 Final Coverage: ${coverage}%`);
    
    if (coverage >= 80) {
      console.log('✅ TARGET ACHIEVED: 80%+ coverage reached!');
    } else {
      console.log(`⚠️ Target not reached: ${coverage}% (need 80%)`);
      console.log('Unmapped node types:');
      nodeTypes.forEach(type => {
        if (!mapping[type]) {
          console.log(`  • ${type}`);
        }
      });
    }
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  } finally {
    await dbPool.end();
  }
}

main().catch(console.error);