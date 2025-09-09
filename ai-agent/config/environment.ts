/**
 * Environment Configuration
 * 
 * This module handles loading and validating environment variables
 * required for connecting to the n8n API.
 */

import dotenv from 'dotenv';
import findConfig from 'find-config';
import path from 'path';
import { McpError } from '@modelcontextprotocol/sdk/types.js';
import { ErrorCode } from '../errors/error-codes.js';

// Environment variable names
export const ENV_VARS = {
  // n8n API
  N8N_API_URL: 'N8N_API_URL',
  N8N_API_KEY: 'N8N_API_KEY',
  N8N_WEBHOOK_USERNAME: 'N8N_WEBHOOK_USERNAME',
  N8N_WEBHOOK_PASSWORD: 'N8N_WEBHOOK_PASSWORD',
  
  // Database
  DB_TYPE: 'DB_TYPE',
  DB_HOST: 'DB_HOST',
  DB_PORT: 'DB_PORT',
  DB_NAME: 'DB_NAME',
  DB_USER: 'DB_USER',
  DB_PASSWORD: 'DB_PASSWORD',
  DB_SSL: 'DB_SSL',
  
  // Backend Service
  SYNC_INTERVAL: 'SYNC_INTERVAL',
  KPI_RETENTION_DAYS: 'KPI_RETENTION_DAYS',
  ENABLE_SCHEDULER: 'ENABLE_SCHEDULER',
  LOG_LEVEL: 'LOG_LEVEL',
  
  DEBUG: 'DEBUG',
};

// Interface for validated environment variables
export interface EnvConfig {
  // Configurazione API n8n
  n8nApiUrl: string;
  n8nApiKey: string;
  n8nWebhookUsername?: string; // Made optional
  n8nWebhookPassword?: string; // Made optional
  
  // Configurazione Database
  dbType: 'postgres' | 'mysql';
  dbHost: string;
  dbPort: number;
  dbName: string;
  dbUser: string;
  dbPassword: string;
  dbSsl: boolean;
  
  // Configurazione Backend Service
  syncInterval: number;
  kpiRetentionDays: number;
  enableScheduler: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  
  debug: boolean;
}

/**
 * Load environment variables from .env file if present
 */
export function loadEnvironmentVariables(): void {
  const {
    N8N_API_URL,
    N8N_API_KEY,
    N8N_WEBHOOK_USERNAME,
    N8N_WEBHOOK_PASSWORD
  } = process.env;

  if (
    !N8N_API_URL &&
    !N8N_API_KEY &&
    !N8N_WEBHOOK_USERNAME &&
    !N8N_WEBHOOK_PASSWORD
  ) {
    const projectRoot = findConfig('package.json');
    if (projectRoot) {
      const envPath = path.resolve(path.dirname(projectRoot), '.env');
      dotenv.config({ path: envPath });
    }
  }
}

/**
 * Validate and retrieve required environment variables
 * 
 * @returns Validated environment configuration
 * @throws {McpError} If required environment variables are missing
 */
export function getEnvConfig(): EnvConfig {
  // n8n API configuration
  const n8nApiUrl = process.env[ENV_VARS.N8N_API_URL];
  const n8nApiKey = process.env[ENV_VARS.N8N_API_KEY];
  const n8nWebhookUsername = process.env[ENV_VARS.N8N_WEBHOOK_USERNAME];
  const n8nWebhookPassword = process.env[ENV_VARS.N8N_WEBHOOK_PASSWORD];
  
  // Database configuration
  const dbType = (process.env[ENV_VARS.DB_TYPE] as 'postgres' | 'mysql') || 'postgres';
  const dbHost = process.env[ENV_VARS.DB_HOST] || 'localhost';
  const dbPort = parseInt(process.env[ENV_VARS.DB_PORT] || '5432');
  const dbName = process.env[ENV_VARS.DB_NAME] || 'n8n_analytics';
  const dbUser = process.env[ENV_VARS.DB_USER] || 'postgres';
  const dbPassword = process.env[ENV_VARS.DB_PASSWORD] || '';
  const dbSsl = process.env[ENV_VARS.DB_SSL]?.toLowerCase() === 'true';
  
  // Backend service configuration
  const syncInterval = parseInt(process.env[ENV_VARS.SYNC_INTERVAL] || '5');
  const kpiRetentionDays = parseInt(process.env[ENV_VARS.KPI_RETENTION_DAYS] || '90');
  const enableScheduler = process.env[ENV_VARS.ENABLE_SCHEDULER]?.toLowerCase() !== 'false';
  const logLevel = (process.env[ENV_VARS.LOG_LEVEL] as 'debug' | 'info' | 'warn' | 'error') || 'info';
  
  const debug = process.env[ENV_VARS.DEBUG]?.toLowerCase() === 'true';

  // Validate required core environment variables
  if (!n8nApiUrl) {
    throw new McpError(
      ErrorCode.InitializationError,
      `Missing required environment variable: ${ENV_VARS.N8N_API_URL}`
    );
  }

  if (!n8nApiKey) {
    throw new McpError(
      ErrorCode.InitializationError,
      `Missing required environment variable: ${ENV_VARS.N8N_API_KEY}`
    );
  }

  // Validate database configuration
  if (!dbUser) {
    throw new McpError(
      ErrorCode.InitializationError,
      `Missing required environment variable: ${ENV_VARS.DB_USER}`
    );
  }

  // N8N_WEBHOOK_USERNAME and N8N_WEBHOOK_PASSWORD are now optional at startup.
  // Tools requiring them should perform checks at the point of use.

  // Validate URL format
  try {
    new URL(n8nApiUrl);
  } catch (error) {
    throw new McpError(
      ErrorCode.InitializationError,
      `Invalid URL format for ${ENV_VARS.N8N_API_URL}: ${n8nApiUrl}`
    );
  }

  return {
    // n8n API
    n8nApiUrl,
    n8nApiKey,
    n8nWebhookUsername: n8nWebhookUsername || undefined,
    n8nWebhookPassword: n8nWebhookPassword || undefined,
    
    // Database
    dbType,
    dbHost,
    dbPort,
    dbName,
    dbUser,
    dbPassword,
    dbSsl,
    
    // Backend service
    syncInterval,
    kpiRetentionDays,
    enableScheduler,
    logLevel,
    
    debug,
  };
}
