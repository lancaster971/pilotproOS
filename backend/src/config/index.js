/**
 * Central Configuration Management
 * Loads and validates all environment variables in one place
 * This file resolves CONFIG-001 technical debt
 */

import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '../../../.env') });

/**
 * Parse boolean environment variable
 */
const parseBoolean = (value, defaultValue = false) => {
  if (value === undefined || value === null) return defaultValue;
  return value === 'true' || value === '1';
};

/**
 * Parse integer environment variable
 */
const parseInteger = (value, defaultValue) => {
  const parsed = parseInt(value);
  return isNaN(parsed) ? defaultValue : parsed;
};

/**
 * Central configuration object
 * All environment variables are accessed through this object
 */
const config = {
  // ============================================================================
  // SERVER CONFIGURATION
  // ============================================================================
  server: {
    port: parseInteger(process.env.PORT, 3001),
    host: process.env.HOST || '127.0.0.1',
    nodeEnv: process.env.NODE_ENV || 'development',
    isDevelopment: process.env.NODE_ENV !== 'production',
    isProduction: process.env.NODE_ENV === 'production',
  },

  // ============================================================================
  // DATABASE CONFIGURATION
  // ============================================================================
  database: {
    host: process.env.DB_HOST || 'localhost',
    port: parseInteger(process.env.DB_PORT, 5432),
    name: process.env.DB_NAME || 'pilotpros_db',
    user: process.env.DB_USER || 'pilotpros_user',
    password: process.env.DB_PASSWORD || 'pilotpros_secure_pass_2025',
    ssl: parseBoolean(process.env.DB_SSL, false),
    pool: {
      size: parseInteger(process.env.DB_POOL_SIZE, 20),
      idleTimeoutMillis: parseInteger(process.env.DB_IDLE_TIMEOUT, 30000),
      connectionTimeoutMillis: parseInteger(process.env.DB_CONNECTION_TIMEOUT, 5000),
    },
  },

  // ============================================================================
  // N8N AUTOMATION ENGINE
  // ============================================================================
  n8n: {
    url: process.env.N8N_URL || 'http://localhost:5678',
    apiKey: process.env.N8N_API_KEY,
    adminUser: process.env.N8N_ADMIN_USER || 'admin',
    adminPassword: process.env.N8N_ADMIN_PASSWORD || 'pilotpros_admin_2025',
    user: process.env.N8N_USER || 'admin',
    password: process.env.N8N_PASSWORD || 'pilotpros_admin_2025',
  },

  // ============================================================================
  // CORS & SECURITY
  // ============================================================================
  security: {
    corsOrigins: process.env.CORS_ORIGINS
      ? process.env.CORS_ORIGINS.split(',').map(origin => origin.trim())
      : [
          'http://localhost:3000',
          'http://127.0.0.1:3000',
          'http://localhost:5173',
          'http://127.0.0.1:5173'
        ],
    frontendUrl: process.env.FRONTEND_URL || 'http://localhost:3000',
    sessionSecret: process.env.SESSION_SECRET || 'default-session-secret-change-in-production',
    jwtSecret: process.env.JWT_SECRET || 'default-jwt-secret-change-in-production',
    jwtExpiresIn: process.env.JWT_EXPIRES_IN || '7d',
    refreshTokenSecret: process.env.REFRESH_TOKEN_SECRET || 'default-refresh-secret-change-in-production',
    refreshTokenExpiresIn: process.env.REFRESH_TOKEN_EXPIRES_IN || '30d',
  },

  // ============================================================================
  // COMPANY BRANDING
  // ============================================================================
  branding: {
    companyName: process.env.COMPANY_NAME || 'PilotProOS',
    domain: process.env.DOMAIN || 'localhost',
    appTitle: process.env.APP_TITLE || 'PilotPro OS',
    appDescription: process.env.APP_DESCRIPTION || 'Business Process Operating System',
  },

  // ============================================================================
  // ERROR NOTIFICATION SYSTEM
  // ============================================================================
  notifications: {
    email: {
      enabled: parseBoolean(process.env.EMAIL_NOTIFICATIONS_ENABLED, false),
      user: process.env.SUPPORT_EMAIL_USER,
      password: process.env.SUPPORT_EMAIL_PASS,
      recipients: process.env.SUPPORT_EMAIL_TO
        ? process.env.SUPPORT_EMAIL_TO.split(',').map(email => email.trim())
        : [],
      smtp: {
        host: process.env.SMTP_HOST || 'smtp.gmail.com',
        port: parseInteger(process.env.SMTP_PORT, 587),
        secure: parseBoolean(process.env.SMTP_SECURE, false),
      },
    },
    webhook: {
      enabled: parseBoolean(process.env.WEBHOOK_NOTIFICATIONS_ENABLED, false),
      url: process.env.ERROR_WEBHOOK_URL,
      timeout: parseInteger(process.env.WEBHOOK_TIMEOUT, 5000),
    },
  },

  // ============================================================================
  // MONITORING & PERFORMANCE
  // ============================================================================
  monitoring: {
    logLevel: process.env.LOG_LEVEL || 'info',
    logFormat: process.env.LOG_FORMAT || 'json',
    logToFile: parseBoolean(process.env.LOG_TO_FILE, false),
    logFilePath: process.env.LOG_FILE_PATH || './logs/app.log',
    enableMetrics: parseBoolean(process.env.ENABLE_METRICS, true),
    metricsPort: parseInteger(process.env.METRICS_PORT, 9090),
    requestTimeout: parseInteger(process.env.REQUEST_TIMEOUT, 30000),
    maxRequestSize: process.env.MAX_REQUEST_SIZE || '10mb',
  },

  // ============================================================================
  // RATE LIMITING
  // ============================================================================
  rateLimit: {
    enabled: parseBoolean(process.env.RATE_LIMIT_ENABLED, false),
    windowMs: parseInteger(process.env.RATE_LIMIT_WINDOW_MS, 60000),
    maxRequests: parseInteger(process.env.RATE_LIMIT_MAX_REQUESTS, 100),
  },

  // ============================================================================
  // CACHE CONFIGURATION (Redis)
  // ============================================================================
  redis: {
    enabled: parseBoolean(process.env.REDIS_ENABLED, false),
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInteger(process.env.REDIS_PORT, 6379),
    password: process.env.REDIS_PASSWORD,
    db: parseInteger(process.env.REDIS_DB, 0),
    cacheTTL: parseInteger(process.env.CACHE_TTL, 3600),
  },

  // ============================================================================
  // BUSINESS INTELLIGENCE
  // ============================================================================
  businessIntelligence: {
    enabled: parseBoolean(process.env.BI_ENABLED, true),
    cacheDuration: parseInteger(process.env.BI_CACHE_DURATION, 300000),
    maxTimelineItems: parseInteger(process.env.BI_MAX_TIMELINE_ITEMS, 1000),
    patternAnalysisEnabled: parseBoolean(process.env.BI_PATTERN_ANALYSIS_ENABLED, true),
    charsPerPage: parseInteger(process.env.BI_CHARS_PER_PAGE, 3000),
    metrics: {
      fastThresholdMs: parseInteger(process.env.METRICS_FAST_THRESHOLD_MS, 30000),
    },
  },

  // ============================================================================
  // FEATURE FLAGS
  // ============================================================================
  features: {
    timeline: parseBoolean(process.env.FEATURE_TIMELINE, true),
    aiAnalysis: parseBoolean(process.env.FEATURE_AI_ANALYSIS, false),
    excelExport: parseBoolean(process.env.FEATURE_EXCEL_EXPORT, false),
    mfa: parseBoolean(process.env.FEATURE_MFA, false),
    ldap: parseBoolean(process.env.FEATURE_LDAP, false),
  },

  // ============================================================================
  // DEVELOPMENT TOOLS
  // ============================================================================
  development: {
    debug: parseBoolean(process.env.DEBUG, false),
    debugSQL: parseBoolean(process.env.DEBUG_SQL, false),
    debugPerformance: parseBoolean(process.env.DEBUG_PERFORMANCE, false),
  },

  // ============================================================================
  // BACKUP & RECOVERY
  // ============================================================================
  backup: {
    enabled: parseBoolean(process.env.BACKUP_ENABLED, false),
    schedule: process.env.BACKUP_SCHEDULE || '0 2 * * *',
    retentionDays: parseInteger(process.env.BACKUP_RETENTION_DAYS, 30),
    path: process.env.BACKUP_PATH || './backups',
  },
};

/**
 * Validate critical configuration
 * Throws an error if required configuration is missing
 */
const validateConfig = () => {
  const errors = [];

  // Check critical database config
  if (!config.database.password) {
    errors.push('Database password (DB_PASSWORD) is required');
  }

  // Check security in production
  if (config.server.isProduction) {
    if (config.security.sessionSecret === 'default-session-secret-change-in-production') {
      errors.push('SESSION_SECRET must be set in production');
    }
    if (config.security.jwtSecret === 'default-jwt-secret-change-in-production') {
      errors.push('JWT_SECRET must be set in production');
    }
    if (config.security.refreshTokenSecret === 'default-refresh-secret-change-in-production') {
      errors.push('REFRESH_TOKEN_SECRET must be set in production');
    }
  }

  if (errors.length > 0) {
    throw new Error(`Configuration validation failed:\n${errors.join('\n')}`);
  }
};

// Validate configuration on load
try {
  validateConfig();
} catch (error) {
  console.error('Configuration Error:', error.message);
  if (config.server.isProduction) {
    process.exit(1);
  }
}

// Log configuration summary (without sensitive data)
if (config.development.debug) {
  console.log('Configuration loaded:', {
    server: {
      port: config.server.port,
      host: config.server.host,
      environment: config.server.nodeEnv,
    },
    database: {
      host: config.database.host,
      port: config.database.port,
      name: config.database.name,
    },
    features: config.features,
  });
}

export default config;
export { config };