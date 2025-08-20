/**
 * Environment Configuration for PilotProOS AI Agent
 * 
 * Loads and validates environment variables for MCP integration
 */

import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Load environment variables from multiple possible locations
 */
export function loadEnvironmentVariables() {
  // Try loading from different locations
  const envPaths = [
    path.join(process.cwd(), '.env'),
    path.join(__dirname, '../../../.env'),
    path.join(__dirname, '../../.env')
  ];
  
  for (const envPath of envPaths) {
    try {
      const result = dotenv.config({ path: envPath });
      if (result.parsed) {
        console.error(`Environment loaded from: ${envPath}`);
        break;
      }
    } catch (error) {
      // Continue to next path
    }
  }
  
  // Set default values for MCP integration
  setDefaultEnvironmentValues();
}

/**
 * Set default environment values for PilotProOS integration
 */
function setDefaultEnvironmentValues() {
  const defaults = {
    // Database configuration (same as backend)
    DB_TYPE: 'postgres',
    DB_HOST: process.env.DB_HOST || 'localhost',
    DB_PORT: process.env.DB_PORT || '5432', 
    DB_NAME: process.env.DB_NAME || 'pilotpros_db',
    DB_USER: process.env.DB_USER || 'pilotpros_user',
    DB_PASSWORD: process.env.DB_PASSWORD || 'pilotpros_secure_pass_2025',
    
    // n8n configuration
    N8N_URL: process.env.N8N_URL || 'http://localhost:5678',
    N8N_API_KEY: process.env.N8N_API_KEY || '',
    
    // AI Agent specific
    AI_AGENT_PORT: process.env.AI_AGENT_PORT || '3002',
    AI_AGENT_MODE: process.env.AI_AGENT_MODE || 'development',
    
    // MCP configuration
    MCP_MODE: process.env.MCP_MODE || 'pilotpros',
    MCP_LOG_LEVEL: process.env.MCP_LOG_LEVEL || 'info'
  };
  
  // Set defaults only if not already set
  for (const [key, value] of Object.entries(defaults)) {
    if (!process.env[key]) {
      process.env[key] = value;
    }
  }
}

/**
 * Get environment configuration object
 */
export function getEnvironmentConfig() {
  return {
    database: {
      type: process.env.DB_TYPE,
      host: process.env.DB_HOST,
      port: parseInt(process.env.DB_PORT || '5432'),
      database: process.env.DB_NAME,
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD
    },
    
    n8n: {
      url: process.env.N8N_URL,
      apiKey: process.env.N8N_API_KEY
    },
    
    aiAgent: {
      port: parseInt(process.env.AI_AGENT_PORT || '3002'),
      mode: process.env.AI_AGENT_MODE,
      logLevel: process.env.MCP_LOG_LEVEL
    },
    
    mcp: {
      mode: process.env.MCP_MODE,
      serverPath: process.env.MCP_SERVER_PATH || './src/index.ts'
    }
  };
}

/**
 * Validate required environment variables
 */
export function validateEnvironment() {
  const required = [
    'DB_HOST',
    'DB_NAME', 
    'DB_USER',
    'DB_PASSWORD'
  ];
  
  const missing = required.filter(key => !process.env[key]);
  
  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }
  
  return true;
}