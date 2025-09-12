/**
 * Business Sanitization Middleware
 * 
 * Middleware che garantisce che TUTTE le response API siano sanitizzate
 * con terminologia business e MAI espongano dettagli tecnici.
 */

import { 
  sanitizeBusinessData, 
  getBusinessStatus,
  sanitizeErrorMessage,
  formatBusinessDuration,
  generateBusinessInsights
} from '../utils/business-terminology.js';
import businessLogger from '../utils/logger.js';
import { BusinessRepository } from '../repositories/business.repository.js';

/**
 * Middleware di sanitizzazione response
 * Intercetta TUTTE le response e le sanitizza automaticamente
 */
export function businessSanitizer() {
  return (req, res, next) => {
    // Intercetta res.json per sanitizzare automaticamente
    const originalJson = res.json;
    
    res.json = function(data) {
      // Sanitizza i dati prima dell'invio
      const sanitizedData = sanitizeResponseData(data, req);
      
      // Aggiungi metadata business standard
      const enhancedData = addBusinessMetadata(sanitizedData, req);
      
      // Log della sanitizzazione (solo in development)
      if (process.env.NODE_ENV === 'development') {
        businessLogger.info('Response sanitized', { method: req.method, path: req.path });
      }
      
      return originalJson.call(this, enhancedData);
    };
    
    next();
  };
}

/**
 * Sanitizza i dati di response completi
 * 
 * @param {any} data - Dati da sanitizzare
 * @param {Object} req - Request object per context
 * @returns {any} Dati sanitizzati
 */
function sanitizeResponseData(data, req) {
  if (!data) return data;
  
  // Se è un errore, sanitizza il messaggio
  if (data.error) {
    return sanitizeErrorResponse(data, req);
  }
  
  // Se è un array, sanitizza ogni elemento
  if (Array.isArray(data)) {
    return data.map(item => sanitizeBusinessData(item));
  }
  
  // Se è un oggetto con data array (formato paginato)
  if (data.data && Array.isArray(data.data)) {
    return {
      ...data,
      data: data.data.map(item => sanitizeBusinessData(item))
    };
  }
  
  // Sanitizzazione generica
  return sanitizeBusinessData(data);
}

/**
 * Sanitizza response di errore
 * 
 * @param {Object} errorData - Dati di errore
 * @param {Object} req - Request object
 * @returns {Object} Errore sanitizzato
 */
function sanitizeErrorResponse(errorData, req) {
  const sanitized = {
    error: errorData.error,
    message: sanitizeErrorMessage(errorData.message || errorData.error),
    timestamp: errorData.timestamp || new Date().toISOString(),
    requestId: req.id || 'unknown'
  };
  
  // Aggiungi suggerimenti business-friendly
  sanitized.suggestions = generateErrorSuggestions(errorData, req);
  
  // Solo in development, includi dettagli tecnici
  if (process.env.NODE_ENV === 'development' && errorData.details) {
    sanitized.technicalDetails = errorData.details;
  }
  
  return sanitized;
}

/**
 * Genera suggerimenti business per errori
 * 
 * @param {Object} errorData - Dati di errore
 * @param {Object} req - Request object
 * @returns {Array} Array di suggerimenti
 */
function generateErrorSuggestions(errorData, req) {
  const suggestions = [];
  
  if (req.path.includes('/processes')) {
    suggestions.push('Check if your business processes are properly configured');
    suggestions.push('Verify that required connections are active');
  }
  
  if (req.path.includes('/process-runs')) {
    suggestions.push('Review process execution logs for details');
    suggestions.push('Contact support if the issue persists');
  }
  
  if (req.path.includes('/analytics')) {
    suggestions.push('Try refreshing the analytics data');
    suggestions.push('Check date range parameters');
  }
  
  // Suggerimenti generici
  suggestions.push('Try again in a few moments');
  suggestions.push('Contact technical support if needed');
  
  return suggestions;
}

/**
 * Aggiunge metadata business standard a tutte le response
 * 
 * @param {any} data - Dati della response
 * @param {Object} req - Request object
 * @returns {any} Dati con metadata business
 */
function addBusinessMetadata(data, req) {
  // Se è un errore, non aggiungere metadata
  if (data.error) return data;
  
  // Se è già un oggetto complesso, aggiungi metadata
  if (typeof data === 'object' && data !== null && !Array.isArray(data)) {
    return {
      ...data,
      _metadata: {
        system: 'Business Process Operating System',
        timestamp: new Date().toISOString(),
        endpoint: req.path,
        sanitized: true,
        businessTerminology: true
      }
    };
  }
  
  return data;
}

/**
 * Middleware per sanitizzazione parametri in ingresso
 * Evita che terminologia tecnica arrivi alle API
 */
export function sanitizeBusinessParams() {
  return (req, res, next) => {
    // Sanitizza query parameters
    if (req.query) {
      req.businessQuery = sanitizeInputParams(req.query);
    }
    
    // Sanitizza body parameters
    if (req.body) {
      req.businessBody = sanitizeInputParams(req.body);
    }
    
    next();
  };
}

/**
 * Sanitizza parametri in input convertendo terminologia business → tecnica
 * 
 * @param {Object} params - Parametri da sanitizzare
 * @returns {Object} Parametri convertiti per uso interno
 */
function sanitizeInputParams(params) {
  const businessToTechnical = {
    // Business → Technical mapping
    process_id: 'workflow_id',
    process_name: 'workflow_name',
    run_id: 'execution_id',
    business_status: 'status',
    process_type: 'workflow_type'
  };
  
  const sanitized = {};
  
  for (const [key, value] of Object.entries(params)) {
    const technicalKey = businessToTechnical[key] || key;
    sanitized[technicalKey] = value;
  }
  
  return sanitized;
}

/**
 * Middleware di validazione business
 * Assicura che i dati in input siano validi per business use
 */
export function validateBusinessData() {
  return (req, res, next) => {
    const errors = [];
    
    // Validazioni specifiche per endpoint business
    if (req.path.includes('/processes') && req.method === 'POST') {
      if (!req.body.process_name || req.body.process_name.trim().length === 0) {
        errors.push('Process name is required');
      }
      
      if (req.body.process_name && req.body.process_name.length > 100) {
        errors.push('Process name must be less than 100 characters');
      }
    }
    
    if (req.path.includes('/process-runs') && req.query.limit) {
      const limit = parseInt(req.query.limit);
      if (isNaN(limit) || limit < 1 || limit > 1000) {
        errors.push('Limit must be between 1 and 1000');
      }
    }
    
    // Se ci sono errori, ritorna response sanitizzata
    if (errors.length > 0) {
      return res.status(400).json({
        error: 'Invalid business data provided',
        message: 'Please check your input parameters',
        validationErrors: errors,
        suggestions: [
          'Verify all required fields are provided',
          'Check data format and limits',
          'Contact support for assistance'
        ]
      });
    }
    
    next();
  };
}

/**
 * Middleware per logging business operations
 * Log tutte le operazioni business per analytics
 */
export function businessOperationLogger() {
  return (req, res, next) => {
    const startTime = Date.now();
    
    // Intercetta la fine della response
    const originalSend = res.send;
    res.send = function(data) {
      const duration = Date.now() - startTime;
      
      // Log operazione business
      logBusinessOperation({
        method: req.method,
        endpoint: req.path,
        duration,
        statusCode: res.statusCode,
        userAgent: req.get('User-Agent'),
        ip: req.ip,
        success: res.statusCode < 400
      });
      
      return originalSend.call(this, data);
    };
    
    next();
  };
}

/**
 * Log operazione business per analytics
 * 
 * @param {Object} operation - Dettagli operazione
 */
async function logBusinessOperation(operation) {
  try {
    // Save business analytics to database (DATA-001 FIXED)
    if (operation.workflowId) {
      const businessRepo = new BusinessRepository();
      
      // Calculate and save analytics for this workflow
      await businessRepo.calculateAndSaveBusinessAnalytics(operation.workflowId, 30);
      
      businessLogger.api('Business analytics saved to database', {
        workflowId: operation.workflowId,
        endpoint: operation.endpoint
      });
    }
    
    // Log the operation
    if (process.env.NODE_ENV === 'production') {
      businessLogger.api('Business operation logged', operation);
    } else {
      // In development, log semplice
      businessLogger.api('Business API call completed', {
        method: operation.method,
        endpoint: operation.endpoint, 
        duration: operation.duration,
        statusCode: operation.statusCode
      });
    }
  } catch (error) {
    businessLogger.error('Failed to log business operation', error);
  }
}

/**
 * Middleware error handler business-friendly
 * Garantisce che anche gli errori non gestiti siano sanitizzati
 */
export function businessErrorHandler() {
  return (error, req, res, next) => {
    businessLogger.error('Business API Error', error);
    
    // Determina il tipo di errore business
    let businessError = {
      error: 'Business Process System Error',
      message: 'The business process system encountered an issue',
      timestamp: new Date().toISOString(),
      suggestions: [
        'Try the operation again in a moment',
        'Check if all required data is provided',
        'Contact technical support if the issue persists'
      ]
    };
    
    // Personalizza based on error type
    if (error.code === 'ECONNREFUSED') {
      businessError.message = 'Business process engine is temporarily unavailable';
      businessError.suggestions = [
        'The system is restarting - try again in a moment',
        'Contact support if the issue continues'
      ];
    } else if (error.name === 'ValidationError') {
      businessError.message = 'Invalid business data provided';
      businessError.suggestions = [
        'Check that all required fields are provided',
        'Verify data format matches expectations'
      ];
    }
    
    // Status code appropriato
    const statusCode = error.statusCode || error.status || 500;
    
    res.status(statusCode).json(businessError);
  };
}