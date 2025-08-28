#!/usr/bin/env node

/**
 * N8N Icon Mapping Generator
 * 
 * This script scans all n8n SVG icons and creates a definitive mapping
 * between nodeTypes and their corresponding icon files.
 * 
 * Usage: node generate-icon-mapping.js
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
 * Recursively scan directory for SVG files
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
          // Store relative path from icons base
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
      console.warn(`⚠️ Cannot read directory ${currentDir}:`, error.message);
    }
  }
  
  scanRecursive(dir);
  return svgFiles;
}

/**
 * Extract nodeType from SVG filename using various patterns
 */
function extractNodeTypeFromFilename(filename, relativePath) {
  const possibleNodeTypes = [];
  
  // Remove .svg extension
  const baseName = filename.replace('.svg', '');
  
  // Pattern 1: Direct name (supabase.svg → supabase)
  possibleNodeTypes.push(baseName);
  
  // Pattern 2: n8n-nodes-base prefix (n8n-nodes-base.code.svg → n8n-nodes-base.code)
  if (baseName.startsWith('n8n-nodes-base.')) {
    possibleNodeTypes.push(baseName);
  }
  
  // Pattern 3: Remove n8n-nodes-base prefix (n8n-nodes-base.code.svg → code)
  if (baseName.startsWith('n8n-nodes-base.')) {
    const withoutPrefix = baseName.replace('n8n-nodes-base.', '');
    possibleNodeTypes.push(withoutPrefix);
    possibleNodeTypes.push(`n8n-nodes-base.${withoutPrefix}`);
  }
  
  // Pattern 4: @n8n prefix variations (@n8n_n8n-nodes-langchain.vectorStoreSupabase.svg)
  if (baseName.startsWith('@n8n_') || baseName.startsWith('_n8n_')) {
    const cleanName = baseName.replace(/^[@_]n8n_/, '@n8n/');
    possibleNodeTypes.push(cleanName);
  }
  
  // Pattern 5: Subdirectory context (base-nodes/Supabase/supabase.svg)
  if (relativePath.includes('base-nodes/')) {
    const pathParts = relativePath.split('/');
    if (pathParts.length >= 3) {
      const serviceName = pathParts[1].toLowerCase();
      possibleNodeTypes.push(serviceName);
      possibleNodeTypes.push(`n8n-nodes-base.${serviceName}`);
    }
  }
  
  // Pattern 6: LangChain variations - ENHANCED
  if (relativePath.includes('langchain-nodes/')) {
    const pathParts = relativePath.split('/');
    for (let i = 0; i < pathParts.length; i++) {
      if (pathParts[i] === 'langchain-nodes' && i + 1 < pathParts.length) {
        // Direct mapping from directory structure
        const category = pathParts[i + 1]; // e.g., 'llms', 'embeddings', 'agents'
        const nodeDir = pathParts[i + 2]; // e.g., 'LMChatOpenAi', 'EmbeddingsOpenAi'
        
        if (category && nodeDir) {
          // Convert directory names to node types
          let nodeType = '';
          
          // Map common patterns
          switch (category) {
            case 'llms':
              if (nodeDir.startsWith('LMChat') || nodeDir.startsWith('LmChat')) {
                nodeType = nodeDir.replace(/^LMChat|^LmChat/, 'lmChat');
              } else if (nodeDir.startsWith('LM') || nodeDir.startsWith('Lm')) {
                nodeType = nodeDir.replace(/^LM|^Lm/, 'lm');
              }
              break;
            case 'embeddings':
              if (nodeDir.startsWith('Embeddings')) {
                nodeType = nodeDir.replace(/^Embeddings/, 'embeddings');
              }
              break;
            case 'agents':
              if (nodeDir === 'Agent') {
                nodeType = 'agent';
              } else if (nodeDir === 'OpenAiAssistant') {
                nodeType = 'openAiAssistant';
              }
              break;
            case 'chains':
              if (nodeDir === 'ChainLLM') {
                nodeType = 'chainLlm';
              } else if (nodeDir === 'ChainSummarization') {
                nodeType = 'chainSummarization';
              } else if (nodeDir === 'ChainRetrievalQA') {
                nodeType = 'chainRetrievalQa';
              }
              break;
            case 'memory':
              if (nodeDir === 'MemoryBufferWindow') {
                nodeType = 'memoryBufferWindow';
              } else if (nodeDir === 'MemoryPostgresChat') {
                nodeType = 'memoryPostgresChat';
              } else if (nodeDir.startsWith('Memory')) {
                nodeType = nodeDir.replace(/^Memory/, 'memory');
              }
              break;
            case 'tools':
              if (nodeDir.startsWith('Tool')) {
                nodeType = nodeDir.replace(/^Tool/, 'tool');
              }
              break;
            case 'trigger':
              if (nodeDir === 'ChatTrigger') {
                nodeType = 'chatTrigger';
              }
              break;
            case 'document_loaders':
              if (nodeDir === 'DocumentDefaultDataLoader') {
                nodeType = 'documentDefaultDataLoader';
              } else if (nodeDir.startsWith('Document')) {
                nodeType = nodeDir.replace(/^Document/, 'document').replace(/Loader$/, 'DataLoader');
              }
              break;
            case 'output_parser':
              if (nodeDir === 'OutputParserStructured') {
                nodeType = 'outputParserStructured';
              } else if (nodeDir.startsWith('OutputParser')) {
                nodeType = nodeDir.replace(/^OutputParser/, 'outputParser');
              }
              break;
            case 'vector_store':
              if (nodeDir.startsWith('VectorStore')) {
                nodeType = nodeDir.replace(/^VectorStore/, 'vectorStore');
              }
              break;
            case 'text_splitters':
              if (nodeDir === 'TextSplitterTokenSplitter') {
                nodeType = 'textSplitterTokenSplitter';
              } else if (nodeDir.startsWith('TextSplitter')) {
                nodeType = nodeDir.replace(/^TextSplitter/, 'textSplitter');
              }
              break;
            case 'mcp':
              if (nodeDir === 'McpClientTool') {
                nodeType = 'mcpClientTool';
              }
              break;
            default:
              nodeType = nodeDir.charAt(0).toLowerCase() + nodeDir.slice(1);
          }
          
          if (nodeType) {
            possibleNodeTypes.push(`@n8n/n8n-nodes-langchain.${nodeType}`);
          }
        }
        
        // Fallback - try the old method
        const langchainType = pathParts.slice(i + 1).join('.').replace('.svg', '');
        possibleNodeTypes.push(`@n8n/n8n-nodes-langchain.${langchainType}`);
      }
    }
  }
  
  // Pattern 7: Service variations (.dark, capitalization)
  if (baseName.includes('.dark')) {
    const withoutDark = baseName.replace('.dark', '');
    possibleNodeTypes.push(withoutDark);
    possibleNodeTypes.push(`n8n-nodes-base.${withoutDark}`);
  }
  
  // Remove duplicates and return
  return [...new Set(possibleNodeTypes)];
}

/**
 * Query database for all existing nodeTypes
 */
async function getDatabaseNodeTypes() {
  try {
    // First, let's get all workflows with nodes
    const query = `
      SELECT id, name, nodes
      FROM n8n.workflow_entity 
      WHERE nodes IS NOT NULL 
        AND json_array_length(nodes) > 0
    `;
    
    const result = await dbPool.query(query);
    const allNodeTypes = new Set();
    
    console.log(`Processing ${result.rows.length} workflows...`);
    
    for (const row of result.rows) {
      try {
        // Parse nodes JSON
        const nodes = row.nodes; // Already parsed by pg
        
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
    
    const nodeTypesArray = Array.from(allNodeTypes).sort();
    console.log(`Found ${nodeTypesArray.length} unique node types`);
    
    // Show some examples
    if (nodeTypesArray.length > 0) {
      console.log('Sample node types:');
      nodeTypesArray.slice(0, 10).forEach((type, idx) => {
        console.log(`  ${idx + 1}. ${type}`);
      });
    }
    
    return nodeTypesArray;
    
  } catch (error) {
    console.error('❌ Database query failed:', error.message);
    console.error('Error details:', error);
    return [];
  }
}

/**
 * Generate the mapping object
 */
function generateMapping(svgFiles, databaseNodeTypes) {
  const mapping = {};
  const unmapped = [];
  const stats = {
    totalSVGs: svgFiles.length,
    totalNodeTypes: databaseNodeTypes.length,
    mapped: 0,
    unmappedSVGs: 0,
    unmappedNodeTypes: 0
  };
  
  console.log('\n🔍 Generating mapping...');
  console.log(`Found ${svgFiles.length} SVG files`);
  console.log(`Found ${databaseNodeTypes.length} database node types`);
  
  // Map SVG files to possible nodeTypes
  for (const svgFile of svgFiles) {
    const possibleNodeTypes = extractNodeTypeFromFilename(svgFile.filename, svgFile.relativePath);
    let mapped = false;
    
    for (const nodeType of possibleNodeTypes) {
      if (databaseNodeTypes.includes(nodeType)) {
        mapping[nodeType] = svgFile.dockerPath;
        mapped = true;
        stats.mapped++;
        console.log(`✅ ${nodeType} → ${svgFile.relativePath}`);
        break;
      }
    }
    
    if (!mapped) {
      unmapped.push({
        file: svgFile.relativePath,
        possibleTypes: possibleNodeTypes
      });
      stats.unmappedSVGs++;
    }
  }
  
  // Find nodeTypes without icons
  const mappedNodeTypes = Object.keys(mapping);
  const unmappedNodeTypes = databaseNodeTypes.filter(type => !mappedNodeTypes.includes(type));
  stats.unmappedNodeTypes = unmappedNodeTypes.length;
  
  return { mapping, unmapped, unmappedNodeTypes, stats };
}

/**
 * Write mapping file
 */
function writeMappingFile(mapping, stats, unmapped, unmappedNodeTypes) {
  // Ensure data directory exists
  const dataDir = path.dirname(OUTPUT_FILE);
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  
  const content = `// N8N Icon Mapping - Generated automatically
// Generated on: ${new Date().toISOString()}
// Total SVGs: ${stats.totalSVGs}
// Total NodeTypes: ${stats.totalNodeTypes}  
// Mapped: ${stats.mapped}
// Unmapped SVGs: ${stats.unmappedSVGs}
// Unmapped NodeTypes: ${stats.unmappedNodeTypes}

export const iconMapping = ${JSON.stringify(mapping, null, 2)};

// Statistics
export const mappingStats = ${JSON.stringify(stats, null, 2)};

// Unmapped SVG files (no matching nodeType in database)
export const unmappedSVGs = ${JSON.stringify(unmapped, null, 2)};

// NodeTypes without icons (found in database but no matching SVG)
export const unmappedNodeTypes = ${JSON.stringify(unmappedNodeTypes, null, 2)};

// Helper function to get icon path
export function getIconPath(nodeType) {
  return iconMapping[nodeType] || null;
}

// Default export
export default iconMapping;
`;
  
  fs.writeFileSync(OUTPUT_FILE, content, 'utf8');
  console.log(`\n💾 Mapping saved to: ${OUTPUT_FILE}`);
}

/**
 * Main execution
 */
async function main() {
  console.log('🚀 N8N Icon Mapping Generator');
  console.log('================================\n');
  
  try {
    // Step 1: Scan for SVG files
    console.log('📁 Scanning for SVG files...');
    const svgFiles = scanForSVGFiles(LOCAL_ICON_PATH);
    console.log(`Found ${svgFiles.length} SVG files`);
    
    // Step 2: Get database nodeTypes
    console.log('\n🗄️ Querying database for nodeTypes...');
    const databaseNodeTypes = await getDatabaseNodeTypes();
    console.log(`Found ${databaseNodeTypes.length} unique nodeTypes in database`);
    
    // Step 3: Generate mapping
    const { mapping, unmapped, unmappedNodeTypes, stats } = generateMapping(svgFiles, databaseNodeTypes);
    
    // Step 4: Write mapping file
    writeMappingFile(mapping, stats, unmapped, unmappedNodeTypes);
    
    // Step 5: Summary
    console.log('\n📊 SUMMARY');
    console.log('==========');
    console.log(`✅ Successfully mapped: ${stats.mapped} nodeTypes to icons`);
    console.log(`⚠️ Unmapped SVGs: ${stats.unmappedSVGs}`);
    console.log(`⚠️ NodeTypes without icons: ${stats.unmappedNodeTypes}`);
    console.log(`📈 Coverage: ${(stats.mapped / stats.totalNodeTypes * 100).toFixed(1)}%`);
    
    if (unmappedNodeTypes.length > 0) {
      console.log('\n🔍 NodeTypes without icons:');
      unmappedNodeTypes.slice(0, 10).forEach(type => console.log(`  • ${type}`));
      if (unmappedNodeTypes.length > 10) {
        console.log(`  ... and ${unmappedNodeTypes.length - 10} more`);
      }
    }
    
    console.log('\n✅ Icon mapping generation completed!');
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  } finally {
    await dbPool.end();
  }
}

// Run the script
main().catch(console.error);