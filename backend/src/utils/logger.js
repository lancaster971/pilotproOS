/**
 * Pino Logger Configuration - PilotProOS
 * Replaces Winston with high-performance structured logging
 * 3x faster than Winston with zero configuration
 */

import pino from 'pino'

// Pino configuration
const loggerConfig = {
  level: process.env.LOG_LEVEL || 'info',
  
  // Development transport (pretty printing)
  transport: process.env.NODE_ENV === 'development' ? {
    target: 'pino-pretty',
    options: {
      colorize: true,
      translateTime: 'SYS:yyyy-mm-dd HH:MM:ss',
      ignore: 'pid,hostname'
    }
  } : undefined,

  // Base configuration
  base: {
    service: 'pilotpros-backend',
    version: process.env.npm_package_version || '1.0.0'
  },

  // Serializers for request/response objects
  serializers: {
    req: pino.stdSerializers.req,
    res: pino.stdSerializers.res,
    err: pino.stdSerializers.err
  }
}

// Create logger instance
const logger = pino(loggerConfig)

// Business-friendly logging methods
export const businessLogger = {
  
  // Info logging for business operations
  info: (message, data = {}) => {
    logger.info({ 
      ...data, 
      type: 'business_operation' 
    }, `🏢 ${message}`)
  },

  // Success operations
  success: (message, data = {}) => {
    logger.info({ 
      ...data, 
      type: 'business_success' 
    }, `✅ ${message}`)
  },

  // Warning for business issues
  warn: (message, data = {}) => {
    logger.warn({ 
      ...data, 
      type: 'business_warning' 
    }, `⚠️ ${message}`)
  },

  // Error for business failures
  error: (message, error = null, data = {}) => {
    logger.error({ 
      ...data,
      err: error,
      type: 'business_error' 
    }, `❌ ${message}`)
  },

  // Debug for development
  debug: (message, data = {}) => {
    logger.debug({ 
      ...data, 
      type: 'business_debug' 
    }, `🐛 ${message}`)
  },

  // Process workflow operations
  workflow: (message, workflowData = {}) => {
    logger.info({
      ...workflowData,
      type: 'workflow_operation'
    }, `🔄 ${message}`)
  },

  // Database operations
  database: (message, dbData = {}) => {
    logger.info({
      ...dbData,
      type: 'database_operation'
    }, `🗄️ ${message}`)
  },

  // API operations  
  api: (message, apiData = {}) => {
    logger.info({
      ...apiData,
      type: 'api_operation'
    }, `🌐 ${message}`)
  }
}

// Raw logger for direct access
export { logger }

// Default export
export default businessLogger