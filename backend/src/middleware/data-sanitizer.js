/**
 * Data Sanitizer Middleware
 * Removes sensitive data and masks technical terminology
 * Enterprise-grade implementation for PII protection
 *
 * @module data-sanitizer
 */

import businessLogger from '../utils/logger.js';

/**
 * Technical to Business terminology mapping
 * CRITICAL: Never expose technical terms to end users
 */
const TECH_TO_BUSINESS = {
  // Database terminology
  'workflow': 'Business Process',
  'workflow_id': 'Process ID',
  'execution': 'Process Run',
  'execution_id': 'Run ID',
  'node': 'Process Step',
  'webhook': 'Integration Point',
  'trigger': 'Process Initiator',
  'credentials': 'Secure Connection',

  // Technical status
  'failed': 'Requires Attention',
  'success': 'Completed Successfully',
  'running': 'In Progress',
  'waiting': 'Pending',
  'error': 'Issue Detected',
  'crashed': 'Interrupted',

  // Database/System terms
  'postgresql': 'Data Storage System',
  'postgres': 'Data Storage',
  'n8n': 'Automation Engine',
  'redis': 'Performance Cache',
  'docker': 'Container System',
  'database': 'Data Repository',
  'table': 'Data Category',
  'schema': 'Data Structure',
  'query': 'Data Request',
  'index': 'Performance Optimizer',

  // User/Auth terms
  'token': 'Access Credential',
  'jwt': 'Security Token',
  'hash': 'Encrypted Value',
  'password_hash': 'Secured Password',
  'api_key': 'Access Key',
  'secret': 'Confidential Data',

  // Operations
  'SELECT': 'Retrieve',
  'INSERT': 'Add',
  'UPDATE': 'Modify',
  'DELETE': 'Remove',
  'JOIN': 'Combine'
};

/**
 * Fields to always remove (security critical)
 */
const FIELDS_TO_REMOVE = [
  'password_hash',
  'token',
  'token_hash',
  'refresh_token',
  'api_key',
  'secret',
  'private_key',
  'credentials',
  'auth_token',
  'session_token',
  'bearer_token',
  'access_token',
  'client_secret',
  'webhook_secret'
];

/**
 * Fields to partially mask (PII protection)
 */
const FIELDS_TO_MASK = {
  'email': maskEmail,
  'ip_address': maskIP,
  'phone': maskPhone,
  'ssn': maskSSN,
  'credit_card': maskCreditCard
};

/**
 * Mask email address
 * @param {string} email - Email to mask
 * @returns {string} Masked email
 */
function maskEmail(email) {
  if (!email || typeof email !== 'string') return email;
  const parts = email.split('@');
  if (parts.length !== 2) return email;

  const localPart = parts[0];
  const domain = parts[1];

  if (localPart.length <= 3) {
    return '***@' + domain;
  }

  return localPart.substring(0, 2) + '***@' + domain;
}

/**
 * Mask IP address
 * @param {string} ip - IP address to mask
 * @returns {string} Masked IP
 */
function maskIP(ip) {
  if (!ip || typeof ip !== 'string') return ip;
  const parts = ip.split('.');
  if (parts.length !== 4) return ip;
  return parts[0] + '.' + parts[1] + '.***.' + '***';
}

/**
 * Mask phone number
 * @param {string} phone - Phone to mask
 * @returns {string} Masked phone
 */
function maskPhone(phone) {
  if (!phone || typeof phone !== 'string') return phone;
  const digits = phone.replace(/\D/g, '');
  if (digits.length < 10) return phone;
  return '***-***-' + digits.slice(-4);
}

/**
 * Mask SSN
 * @param {string} ssn - SSN to mask
 * @returns {string} Masked SSN
 */
function maskSSN(ssn) {
  return '***-**-****';
}

/**
 * Mask credit card
 * @param {string} card - Credit card to mask
 * @returns {string} Masked card
 */
function maskCreditCard(card) {
  if (!card || typeof card !== 'string') return card;
  const digits = card.replace(/\D/g, '');
  if (digits.length < 12) return '****';
  return '**** **** **** ' + digits.slice(-4);
}

/**
 * Replace technical terms with business terminology
 * @param {any} value - Value to process
 * @returns {any} Processed value
 */
function replaceTechnicalTerms(value) {
  if (typeof value === 'string') {
    let result = value;

    // Replace exact matches
    for (const [tech, business] of Object.entries(TECH_TO_BUSINESS)) {
      const regex = new RegExp(`\\b${tech}\\b`, 'gi');
      result = result.replace(regex, business);
    }

    return result;
  }

  if (typeof value === 'object' && value !== null) {
    if (Array.isArray(value)) {
      return value.map(item => replaceTechnicalTerms(item));
    }

    const result = {};
    for (const [key, val] of Object.entries(value)) {
      // Replace key if it's technical
      const newKey = TECH_TO_BUSINESS[key] || key;
      result[newKey] = replaceTechnicalTerms(val);
    }
    return result;
  }

  return value;
}

/**
 * Sanitize a single data object
 * @param {object} data - Data to sanitize
 * @param {string} context - Context for logging
 * @returns {object} Sanitized data
 */
function sanitizeObject(data, context) {
  if (!data || typeof data !== 'object') return data;

  const sanitized = {};

  for (const [key, value] of Object.entries(data)) {
    // Skip sensitive fields entirely
    if (FIELDS_TO_REMOVE.includes(key.toLowerCase())) {
      continue;
    }

    // Apply masking if needed
    if (FIELDS_TO_MASK[key.toLowerCase()]) {
      sanitized[key] = FIELDS_TO_MASK[key.toLowerCase()](value);
    } else {
      sanitized[key] = value;
    }
  }

  return sanitized;
}

/**
 * Main sanitization function
 * @param {any} data - Data to sanitize (object, array, or primitive)
 * @param {string} context - Context for logging (e.g., 'users', 'sessions')
 * @returns {any} Sanitized and business-masked data
 */
export function sanitizeData(data, context = 'unknown') {
  try {
    // Handle arrays
    if (Array.isArray(data)) {
      const sanitized = data.map(item => sanitizeObject(item, context));
      return replaceTechnicalTerms(sanitized);
    }

    // Handle single objects
    if (typeof data === 'object' && data !== null) {
      const sanitized = sanitizeObject(data, context);
      return replaceTechnicalTerms(sanitized);
    }

    // Handle primitives
    return replaceTechnicalTerms(data);

  } catch (error) {
    businessLogger.error(`Sanitization error in context ${context}:`, error);
    // In case of error, return empty data rather than exposing raw data
    return Array.isArray(data) ? [] : {};
  }
}

/**
 * Validate that no technical terms leaked through
 * @param {string} text - Text to validate
 * @returns {boolean} True if clean, false if technical terms found
 */
export function validateNoTechLeak(text) {
  if (typeof text !== 'string') return true;

  const technicalPatterns = [
    /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/,  // IP addresses
    /:\d{4,5}\b/,  // Port numbers
    /[a-f0-9]{32,}/i,  // Hashes/tokens
    /SELECT|INSERT|UPDATE|DELETE|DROP|CREATE/i,  // SQL
    /postgresql:|mongodb:|redis:/i,  // Connection strings
    /localhost|127\.0\.0\.1/i,  // Local references
    /docker|kubernetes|container/i,  // Infrastructure
    /\bn8n\b/i,  // Specific tech names
    /error\s+at\s+\w+/i,  // Stack traces
    /\.(js|py|java|cpp|go|rs)\b/i  // Code file extensions
  ];

  for (const pattern of technicalPatterns) {
    if (pattern.test(text)) {
      businessLogger.warn('Technical term leak detected:', {
        pattern: pattern.toString(),
        text: text.substring(0, 100)
      });
      return false;
    }
  }

  return true;
}

/**
 * Middleware function for Express routes
 */
export function sanitizerMiddleware(req, res, next) {
  // Override res.json to automatically sanitize responses
  const originalJson = res.json.bind(res);

  res.json = function(data) {
    const context = req.path.split('/').pop() || 'unknown';
    const sanitized = sanitizeData(data, context);

    // Validate no tech leak in stringified response
    const responseStr = JSON.stringify(sanitized);
    if (!validateNoTechLeak(responseStr)) {
      businessLogger.error('Technical leak detected in response!', {
        path: req.path,
        method: req.method
      });
    }

    return originalJson(sanitized);
  };

  next();
}

export default {
  sanitizeData,
  validateNoTechLeak,
  sanitizerMiddleware
};