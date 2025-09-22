/**
 * Business API Authentication Middleware
 *
 * CLEAN VERSION - Uses ONLY Passport.js authentication
 * NO MORE CUSTOM JWT CODE
 */

import { authenticateJWT, requireAdmin, requireRole, requirePermission } from './passport-auth.js';
import rateLimit from 'express-rate-limit';

/**
 * Rate limiting per operazioni critiche
 */
export const criticalOperationLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minuto
  max: 10, // max 10 richieste per finestra
  message: 'Too many requests for critical operations',
  standardHeaders: true,
  legacyHeaders: false,
});

/**
 * Business API Authentication Middleware
 * Uses ONLY Passport.js - NO CUSTOM CODE
 */
export const businessAuthMiddleware = (req, res, next) => {
  // Simply use Passport.js JWT authentication for all business routes
  return authenticateJWT(req, res, next);
};

/**
 * Admin-only middleware for critical operations
 */
export const businessAdminMiddleware = (req, res, next) => {
  authenticateJWT(req, res, (err) => {
    if (err) return next(err);
    requireAdmin(req, res, next);
  });
};

export default businessAuthMiddleware;