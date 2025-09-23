/**
 * Authentication Error Handler
 *
 * Centralized error handling for authentication system
 */

import businessLogger from '../utils/logger.js';

/**
 * Authentication error types
 */
export const AuthErrorType = {
  INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  TOKEN_INVALID: 'TOKEN_INVALID',
  NO_TOKEN: 'NO_TOKEN',
  INSUFFICIENT_PERMISSIONS: 'INSUFFICIENT_PERMISSIONS',
  ACCOUNT_LOCKED: 'ACCOUNT_LOCKED',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
  SESSION_EXPIRED: 'SESSION_EXPIRED',
  MFA_REQUIRED: 'MFA_REQUIRED',
  DATABASE_ERROR: 'DATABASE_ERROR',
  INTERNAL_ERROR: 'INTERNAL_ERROR'
};

/**
 * Error messages mapping
 */
const errorMessages = {
  [AuthErrorType.INVALID_CREDENTIALS]: 'Credenziali non valide',
  [AuthErrorType.TOKEN_EXPIRED]: 'Token scaduto, effettua nuovamente il login',
  [AuthErrorType.TOKEN_INVALID]: 'Token non valido',
  [AuthErrorType.NO_TOKEN]: 'Token di autenticazione richiesto',
  [AuthErrorType.INSUFFICIENT_PERMISSIONS]: 'Permessi insufficienti per questa operazione',
  [AuthErrorType.ACCOUNT_LOCKED]: 'Account bloccato per troppi tentativi falliti',
  [AuthErrorType.RATE_LIMIT_EXCEEDED]: 'Troppe richieste, riprova più tardi',
  [AuthErrorType.SESSION_EXPIRED]: 'Sessione scaduta, effettua nuovamente il login',
  [AuthErrorType.MFA_REQUIRED]: 'Autenticazione a due fattori richiesta',
  [AuthErrorType.DATABASE_ERROR]: 'Errore di connessione al database',
  [AuthErrorType.INTERNAL_ERROR]: 'Errore interno del server'
};

/**
 * Get HTTP status code for error type
 */
const getStatusCode = (errorType) => {
  switch (errorType) {
    case AuthErrorType.INVALID_CREDENTIALS:
    case AuthErrorType.TOKEN_EXPIRED:
    case AuthErrorType.TOKEN_INVALID:
    case AuthErrorType.NO_TOKEN:
    case AuthErrorType.SESSION_EXPIRED:
      return 401;
    case AuthErrorType.INSUFFICIENT_PERMISSIONS:
      return 403;
    case AuthErrorType.RATE_LIMIT_EXCEEDED:
      return 429;
    case AuthErrorType.ACCOUNT_LOCKED:
      return 423;
    case AuthErrorType.DATABASE_ERROR:
    case AuthErrorType.INTERNAL_ERROR:
    default:
      return 500;
  }
};

/**
 * Create auth error response
 */
export const createAuthError = (type, details = null) => {
  const error = {
    success: false,
    error: type,
    message: errorMessages[type] || 'Errore di autenticazione',
    timestamp: new Date().toISOString()
  };

  if (details && process.env.NODE_ENV === 'development') {
    error.details = details;
  }

  return error;
};

/**
 * Log authentication error
 */
export const logAuthError = (req, errorType, details = {}) => {
  const logData = {
    type: 'auth_error',
    errorType,
    ip: req.ip,
    userAgent: req.get('user-agent'),
    path: req.path,
    method: req.method,
    ...details
  };

  // Log based on severity
  if (errorType === AuthErrorType.INTERNAL_ERROR ||
      errorType === AuthErrorType.DATABASE_ERROR) {
    businessLogger.error('Authentication system error', logData);
  } else if (errorType === AuthErrorType.ACCOUNT_LOCKED ||
             errorType === AuthErrorType.RATE_LIMIT_EXCEEDED) {
    businessLogger.warn('Authentication security event', logData);
  } else {
    businessLogger.info('Authentication attempt failed', logData);
  }
};

/**
 * Express middleware for handling auth errors
 */
export const authErrorHandler = (err, req, res, next) => {
  // JWT errors
  if (err.name === 'JsonWebTokenError') {
    logAuthError(req, AuthErrorType.TOKEN_INVALID, { error: err.message });
    return res.status(401).json(createAuthError(AuthErrorType.TOKEN_INVALID));
  }

  if (err.name === 'TokenExpiredError') {
    logAuthError(req, AuthErrorType.TOKEN_EXPIRED, { expiredAt: err.expiredAt });
    return res.status(401).json(createAuthError(AuthErrorType.TOKEN_EXPIRED));
  }

  // Passport errors
  if (err.name === 'AuthenticationError') {
    const errorType = err.message.includes('credentials')
      ? AuthErrorType.INVALID_CREDENTIALS
      : AuthErrorType.TOKEN_INVALID;
    logAuthError(req, errorType);
    return res.status(401).json(createAuthError(errorType));
  }

  // Database errors
  if (err.code && err.code.startsWith('ECONN')) {
    logAuthError(req, AuthErrorType.DATABASE_ERROR, { code: err.code });
    return res.status(500).json(createAuthError(AuthErrorType.DATABASE_ERROR));
  }

  // Default error
  logAuthError(req, AuthErrorType.INTERNAL_ERROR, {
    error: err.message,
    stack: process.env.NODE_ENV === 'development' ? err.stack : undefined
  });

  res.status(500).json(createAuthError(AuthErrorType.INTERNAL_ERROR));
};

/**
 * Audit log for successful authentication
 */
export const logAuthSuccess = (req, user) => {
  businessLogger.info('Authentication successful', {
    type: 'auth_success',
    userId: user.id,
    email: user.email,
    role: user.role,
    ip: req.ip,
    userAgent: req.get('user-agent'),
    timestamp: new Date().toISOString()
  });
};

export default authErrorHandler;