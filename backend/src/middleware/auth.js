/**
 * Authentication Middleware
 * 
 * JWT token verification middleware for protected routes
 */

import jwt from 'jsonwebtoken';
import { dbPool } from '../db/connection.js';

/**
 * Verify JWT token and load user data
 */
export const authenticateToken = async (req, res, next) => {
  try {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

    if (!token) {
      return res.status(401).json({
        success: false,
        message: 'Token di autenticazione richiesto'
      });
    }

    // Verify JWT token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // Load user from database to ensure user still exists and is active
    const users = await dbPool`
      SELECT id, email, role, is_active
      FROM pilotpros.users 
      WHERE id = ${decoded.userId} AND is_active = true
    `;

    if (users.length === 0) {
      return res.status(401).json({
        success: false,
        message: 'Utente non trovato o non attivo'
      });
    }

    // Add user data to request object
    req.user = {
      userId: users[0].id,
      email: users[0].email,
      role: users[0].role,
      permissions: decoded.permissions || []
    };

    next();
  } catch (error) {
    console.error('❌ Authentication middleware error:', error);
    
    if (error.name === 'JsonWebTokenError') {
      return res.status(401).json({
        success: false,
        message: 'Token non valido'
      });
    }
    
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({
        success: false,
        message: 'Token scaduto'
      });
    }

    return res.status(500).json({
      success: false,
      message: 'Errore di autenticazione'
    });
  }
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