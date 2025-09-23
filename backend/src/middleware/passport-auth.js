/**
 * Passport.js Authentication Middleware
 *
 * Modern authentication middleware using Passport.js
 * Replaces custom JWT implementation for better security and maintainability
 */

import passport from '../auth/passport-config.js';
import { createClient } from 'redis';
import jwt from 'jsonwebtoken';

// Redis client for token blacklist
const redisClient = createClient({
  socket: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379')
  }
});

redisClient.connect().catch(console.error);

/**
 * JWT Authentication Middleware
 * Uses Passport.js JWT strategy for API authentication
 */
export const authenticateJWT = (req, res, next) => {
  passport.authenticate('jwt', { session: false }, async (err, user, info) => {
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

    // Check if token is blacklisted
    const token = req.headers.authorization?.split(' ')[1] || req.cookies?.jwt_token;
    if (token) {
      try {
        const isBlacklisted = await redisClient.get(`blacklist:${token}`);
        if (isBlacklisted) {
          return res.status(401).json({
            success: false,
            message: 'Token revocato'
          });
        }
      } catch (redisErr) {
        console.error('Redis blacklist check error:', redisErr);
        // Continue if Redis fails
      }
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

    // Add user to request object (no blacklist check for login)
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

// Export function to blacklist a token
export const blacklistToken = async (token) => {
  try {
    // Extract expiry from token
    const decoded = jwt.decode(token);
    if (decoded && decoded.exp) {
      const ttl = decoded.exp - Math.floor(Date.now() / 1000);
      if (ttl > 0) {
        await redisClient.setEx(`blacklist:${token}`, ttl, '1');
        console.log(`Token blacklisted for ${ttl} seconds`);
      }
    }
  } catch (error) {
    console.error('Error blacklisting token:', error);
  }
};