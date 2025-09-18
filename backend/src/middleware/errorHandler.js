/**
 * Global Error Handler Middleware
 * Centralized error handling for the entire application
 * Resolves error handling technical debt
 */

import config from '../config/index.js';
import businessLogger from '../utils/logger.js';

/**
 * Custom Error Classes
 */
export class AppError extends Error {
  constructor(message, statusCode = 500, code = 'INTERNAL_ERROR', details = null) {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.details = details;
    this.isOperational = true;
    Error.captureStackTrace(this, this.constructor);
  }
}

export class ValidationError extends AppError {
  constructor(message, details = null) {
    super(message, 400, 'VALIDATION_ERROR', details);
  }
}

export class AuthenticationError extends AppError {
  constructor(message = 'Authentication required') {
    super(message, 401, 'AUTH_ERROR');
  }
}

export class AuthorizationError extends AppError {
  constructor(message = 'Insufficient permissions') {
    super(message, 403, 'AUTHORIZATION_ERROR');
  }
}

export class NotFoundError extends AppError {
  constructor(resource = 'Resource') {
    super(`${resource} not found`, 404, 'NOT_FOUND');
  }
}

export class ConflictError extends AppError {
  constructor(message) {
    super(message, 409, 'CONFLICT');
  }
}

export class RateLimitError extends AppError {
  constructor(message = 'Too many requests') {
    super(message, 429, 'RATE_LIMIT_EXCEEDED');
  }
}

export class ExternalServiceError extends AppError {
  constructor(service, message) {
    super(`External service error (${service}): ${message}`, 502, 'EXTERNAL_SERVICE_ERROR');
    this.service = service;
  }
}

/**
 * Async error handler wrapper
 * Wraps async route handlers to catch errors
 */
export const asyncHandler = (fn) => {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};

/**
 * Error logger middleware
 * Logs error details before handling
 */
export const errorLogger = (err, req, res, next) => {
  const errorInfo = {
    message: err.message,
    code: err.code || 'UNKNOWN_ERROR',
    statusCode: err.statusCode || 500,
    stack: config.server.isDevelopment ? err.stack : undefined,
    path: req.path,
    method: req.method,
    ip: req.ip,
    user: req.user?.id,
    timestamp: new Date().toISOString(),
  };

  // Log based on severity
  if (err.statusCode >= 500 || !err.isOperational) {
    businessLogger.error('Server Error', errorInfo);
  } else if (err.statusCode >= 400) {
    businessLogger.warn('Client Error', errorInfo);
  } else {
    businessLogger.info('Handled Error', errorInfo);
  }

  next(err);
};

/**
 * Global error handler middleware
 * Must be the last middleware in the chain
 */
export const globalErrorHandler = (err, req, res, next) => {
  // Set default values
  let statusCode = err.statusCode || 500;
  let message = err.message || 'Internal Server Error';
  let code = err.code || 'INTERNAL_ERROR';
  let details = err.details || null;

  // Handle specific error types
  if (err.name === 'ValidationError' && err.errors) {
    // Mongoose validation error
    statusCode = 400;
    code = 'VALIDATION_ERROR';
    message = 'Validation failed';
    details = Object.values(err.errors).map(e => ({
      field: e.path,
      message: e.message,
    }));
  } else if (err.name === 'CastError') {
    // Mongoose cast error
    statusCode = 400;
    code = 'INVALID_ID';
    message = 'Invalid ID format';
  } else if (err.name === 'MongoError' && err.code === 11000) {
    // MongoDB duplicate key error
    statusCode = 409;
    code = 'DUPLICATE_ENTRY';
    message = 'Resource already exists';
  } else if (err.name === 'JsonWebTokenError') {
    // JWT error
    statusCode = 401;
    code = 'INVALID_TOKEN';
    message = 'Invalid authentication token';
  } else if (err.name === 'TokenExpiredError') {
    // JWT expired
    statusCode = 401;
    code = 'TOKEN_EXPIRED';
    message = 'Authentication token expired';
  } else if (err.type === 'entity.too.large') {
    // Request body too large
    statusCode = 413;
    code = 'PAYLOAD_TOO_LARGE';
    message = 'Request body too large';
  } else if (err.code === 'ECONNREFUSED') {
    // Database connection error
    statusCode = 503;
    code = 'SERVICE_UNAVAILABLE';
    message = 'Service temporarily unavailable';
  }

  // Sanitize error message in production
  if (config.server.isProduction && !err.isOperational) {
    message = 'An error occurred while processing your request';
    details = null;
  }

  // Send error response
  res.status(statusCode).json({
    error: {
      message,
      code,
      details,
      ...(config.server.isDevelopment && {
        stack: err.stack,
        originalError: err.message,
      }),
    },
    timestamp: new Date().toISOString(),
    path: req.path,
    requestId: req.id || 'N/A',
  });
};

/**
 * 404 Not Found handler
 * Use this before the global error handler
 */
export const notFoundHandler = (req, res, next) => {
  const error = new NotFoundError(`Route ${req.originalUrl}`);
  next(error);
};

/**
 * Unhandled rejection handler
 * Catches unhandled promise rejections
 */
export const unhandledRejectionHandler = () => {
  process.on('unhandledRejection', (reason, promise) => {
    businessLogger.error('Unhandled Rejection', {
      reason: reason instanceof Error ? reason.message : reason,
      stack: reason instanceof Error ? reason.stack : undefined,
      promise,
    });

    // In production, exit gracefully
    if (config.server.isProduction) {
      process.exit(1);
    }
  });
};

/**
 * Uncaught exception handler
 * Catches uncaught exceptions
 */
export const uncaughtExceptionHandler = () => {
  process.on('uncaughtException', (error) => {
    businessLogger.error('Uncaught Exception', {
      message: error.message,
      stack: error.stack,
    });

    // Always exit on uncaught exceptions
    process.exit(1);
  });
};

/**
 * Initialize all error handlers
 */
export const initializeErrorHandlers = () => {
  unhandledRejectionHandler();
  uncaughtExceptionHandler();
};

/**
 * Express error handling setup
 * Call this after all routes
 */
export const setupErrorHandling = (app) => {
  // 404 handler
  app.use(notFoundHandler);

  // Error logger
  app.use(errorLogger);

  // Global error handler
  app.use(globalErrorHandler);
};

export default {
  AppError,
  ValidationError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  ConflictError,
  RateLimitError,
  ExternalServiceError,
  asyncHandler,
  errorLogger,
  globalErrorHandler,
  notFoundHandler,
  initializeErrorHandlers,
  setupErrorHandling,
};