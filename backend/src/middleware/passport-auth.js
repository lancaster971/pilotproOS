/**
 * Passport.js Authentication Middleware
 *
 * Modern authentication middleware using Passport.js
 * Replaces custom JWT implementation for better security and maintainability
 */

import passport from '../auth/passport-config.js';

/**
 * JWT Authentication Middleware
 * Uses Passport.js JWT strategy for API authentication
 */
export const authenticateJWT = (req, res, next) => {
  passport.authenticate('jwt', { session: false }, (err, user, info) => {
    if (err) {
      console.error('❌ JWT Authentication error:', err);
      return res.status(500).json({
        success: false,
        message: 'Errore di autenticazione'
      });
    }

    if (!user) {
      return res.status(401).json({
        success: false,
        message: info?.message || 'Token di autenticazione non valido'
      });
    }

    // Add user to request object
    req.user = user;
    next();
  })(req, res, next);
};

/**
 * Local Authentication Middleware
 * Uses Passport.js Local strategy for login
 */
export const authenticateLocal = (req, res, next) => {
  passport.authenticate('local', { session: false }, (err, user, info) => {
    if (err) {
      console.error('❌ Local Authentication error:', err);
      return res.status(500).json({
        success: false,
        message: 'Errore di autenticazione'
      });
    }

    if (!user) {
      return res.status(401).json({
        success: false,
        message: info?.message || 'Credenziali non valide'
      });
    }

    // Add user to request object
    req.user = user;
    next();
  })(req, res, next);
};

/**
 * Require admin role
 */
export const requireAdmin = (req, res, next) => {
  if (req.user?.role !== 'admin') {
    return res.status(403).json({
      success: false,
      message: 'Accesso negato: permessi amministratore richiesti'
    });
  }
  next();
};

/**
 * Require specific role
 */
export const requireRole = (role) => (req, res, next) => {
  if (req.user?.role !== role) {
    return res.status(403).json({
      success: false,
      message: `Accesso negato: ruolo ${role} richiesto`
    });
  }
  next();
};

/**
 * Require specific permission
 */
export const requirePermission = (permission) => (req, res, next) => {
  if (!req.user?.permissions?.includes(permission)) {
    return res.status(403).json({
      success: false,
      message: `Accesso negato: permesso ${permission} richiesto`
    });
  }
  next();
};

// Backward compatibility - keep the old name for existing routes
export const authenticateToken = authenticateJWT;