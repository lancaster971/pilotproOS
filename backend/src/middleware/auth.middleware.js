/**
 * SIMPLE AUTH MIDDLEWARE
 *
 * Just validate JWT from Authorization header.
 * No Redis. No sessions. No bullshit.
 */

import jwt from 'jsonwebtoken';

/**
 * Validate JWT token from Authorization header
 * Usage: app.get('/api/protected', authenticate, handler)
 */
export const authenticate = (req, res, next) => {
  try {
    // Get token from Authorization header
    const authHeader = req.headers.authorization;
    const token = authHeader?.startsWith('Bearer ')
      ? authHeader.substring(7)
      : null;

    if (!token) {
      return res.status(401).json({
        success: false,
        message: 'Authentication required'
      });
    }

    // Verify token
    const decoded = jwt.verify(
      token,
      process.env.JWT_SECRET || 'dev-secret-change-in-production'
    );

    // Add user info to request
    req.user = {
      id: decoded.userId,
      email: decoded.email,
      role: decoded.role
    };

    // Continue to next middleware
    next();

  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({
        success: false,
        message: 'Token expired'
      });
    }

    if (error.name === 'JsonWebTokenError') {
      return res.status(401).json({
        success: false,
        message: 'Invalid token'
      });
    }

    // Other errors
    console.error('Auth middleware error:', error);
    res.status(500).json({
      success: false,
      message: 'Authentication error'
    });
  }
};

/**
 * Optional: Require specific role
 */
export const requireRole = (role) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        message: 'Authentication required'
      });
    }

    if (req.user.role !== role) {
      return res.status(403).json({
        success: false,
        message: `Role ${role} required`
      });
    }

    next();
  };
};

/**
 * Optional: Require admin role
 */
export const requireAdmin = (req, res, next) => {
  return requireRole('admin')(req, res, next);
};