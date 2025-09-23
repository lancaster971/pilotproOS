/**
 * Passport.js Authentication Controller
 *
 * Modern authentication controller using Passport.js strategies
 * Replaces custom JWT implementation for better security
 */

import express from 'express';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
// import { dbPool } from '../db/connection.js'; // Using pgPool instead
import { authenticateLocal, blacklistToken } from '../middleware/passport-auth.js';
import {
  loginRateLimiter,
  progressiveDelay,
  recordFailedLogin,
  clearFailedAttempts,
  registrationLimiter,
  passwordResetLimiter
} from '../middleware/auth-rate-limiting.js';
import { dbPool } from '../db/pg-pool.js';
import { logAuthSuccess, logAuthError, AuthErrorType, createAuthError } from '../middleware/auth-error-handler.js';
import refreshTokenService from '../services/refresh-token.service.js';

const router = express.Router();

/**
 * Login endpoint using Passport.js Local Strategy
 */
router.post('/login', loginRateLimiter, progressiveDelay, authenticateLocal, async (req, res, next) => {
  try {
    const user = req.user;

      // Clear failed login attempts on successful login
      await clearFailedAttempts(req.ip);

      // Log successful authentication
      logAuthSuccess(req, user);

      // Generate JWT token
      const payload = {
        userId: user.id,
        email: user.email,
        role: user.role
      };

      const token = jwt.sign(payload, process.env.JWT_SECRET, {
        expiresIn: '30m' // 30 minutes for security
      });

      // Generate refresh token
      const refreshToken = await refreshTokenService.generateRefreshToken(user.id);

      // Set HTTP-only cookie for additional security
      res.cookie('jwt_token', token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 30 * 60 * 1000 // 30 minutes
      });

      // Set refresh token as HTTP-only cookie
      res.cookie('refresh_token', refreshToken, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days
      });

      res.json({
        success: true,
        message: 'Login effettuato con successo',
        user: {
          id: user.id,
          email: user.email,
          role: user.role
        },
        token, // Also send token for Bearer authentication
        expiresIn: '30m'
      });

  } catch (error) {
    console.error('❌ Login error:', error);
    await recordFailedLogin(req.ip);
    logAuthError(req, AuthErrorType.INTERNAL_ERROR, { error: error.message });

    res.status(500).json(createAuthError(AuthErrorType.INTERNAL_ERROR));
  }
});

/**
 * User registration endpoint
 */
router.post('/register', registrationLimiter, async (req, res) => {
  try {
    const { email, password, confirmPassword, role = 'user' } = req.body;

    // Validation
    if (!email || !password || !confirmPassword) {
      return res.status(400).json({
        success: false,
        message: 'Email, password e conferma password sono richiesti'
      });
    }

    if (password !== confirmPassword) {
      return res.status(400).json({
        success: false,
        message: 'Le password non corrispondono'
      });
    }

    if (password.length < 8) {
      return res.status(400).json({
        success: false,
        message: 'La password deve essere di almeno 8 caratteri'
      });
    }

    // Check if user already exists
    const existingUser = await dbPool.query(
      'SELECT id FROM pilotpros.users WHERE email = $1',
      [email]
    );

    if (existingUser.rows.length > 0) {
      return res.status(409).json({
        success: false,
        message: 'Utente già esistente con questa email'
      });
    }

    // Hash password
    const saltRounds = parseInt(process.env.BCRYPT_ROUNDS || '12');
    const hashedPassword = await bcrypt.hash(password, saltRounds);

    // Create user
    const result = await dbPool.query(
      `INSERT INTO pilotpros.users (email, password_hash, role, is_active, created_at)
       VALUES ($1, $2, $3, true, CURRENT_TIMESTAMP)
       RETURNING id, email, role, created_at`,
      [email, hashedPassword, role]
    );

    const newUser = result.rows[0];

    res.status(201).json({
      success: true,
      message: 'Utente registrato con successo',
      data: {
        user: {
          id: newUser.id,
          email: newUser.email,
          role: newUser.role,
          created_at: newUser.created_at
        }
      }
    });

  } catch (error) {
    console.error('❌ Registration error:', error);
    res.status(500).json({
      success: false,
      message: 'Errore interno durante la registrazione'
    });
  }
});

/**
 * Logout endpoint - revokes all tokens
 */
router.post('/logout', async (req, res) => {
  try {
    // Get user from token if present
    const authHeader = req.headers.authorization;
    const token = authHeader?.split(' ')[1] || req.cookies.jwt_token;

    if (token) {
      try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        // Revoke all refresh tokens for this user
        await refreshTokenService.revokeAllUserTokens(decoded.userId);
        // Blacklist the access token
        await blacklistToken(token);
      } catch (err) {
        // Token invalid - continue with logout anyway
      }
    }

    // Clear cookies
    res.clearCookie('jwt_token', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict'
    });

    res.clearCookie('refresh_token', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict'
    });

    // Destroy session if exists
    if (req.session) {
      req.session.destroy((err) => {
        if (err) {
          console.error('❌ Session destruction error:', err);
        }
      });
    }

    res.json({
      success: true,
      message: 'Logout effettuato con successo'
    });
  } catch (error) {
    console.error('❌ Logout error:', error);
    res.status(500).json({
      success: false,
      message: 'Errore durante il logout'
    });
  }
});

/**
 * Get current user profile
 */
router.get('/profile', async (req, res) => {
  try {
    // This would be called after authentication middleware
    if (!req.user) {
      return res.status(401).json({
        success: false,
        message: 'Utente non autenticato'
      });
    }

    res.json({
      success: true,
      data: {
        user: req.user
      }
    });

  } catch (error) {
    console.error('❌ Profile error:', error);
    res.status(500).json({
      success: false,
      message: 'Errore nel recupero del profilo'
    });
  }
});

/**
 * Verify token endpoint
 */
router.post('/verify', async (req, res) => {
  try {
    const authHeader = req.headers.authorization;
    const token = authHeader?.split(' ')[1] || req.cookies.jwt_token;

    if (!token) {
      return res.status(401).json({
        success: false,
        message: 'Token non fornito'
      });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // Check if user still exists and is active
    const result = await dbPool.query(
      'SELECT id, email, role FROM pilotpros.users WHERE id = $1 AND is_active = true',
      [decoded.userId]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({
        success: false,
        message: 'Utente non trovato o non attivo'
      });
    }

    res.json({
      success: true,
      message: 'Token valido',
      data: {
        user: result.rows[0],
        expiresAt: new Date(decoded.exp * 1000)
      }
    });

  } catch (error) {
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

    console.error('❌ Token verification error:', error);
    res.status(500).json({
      success: false,
      message: 'Errore nella verifica del token'
    });
  }
});

/**
 * Refresh token endpoint
 */
router.post('/refresh', async (req, res) => {
  try {
    const refreshToken = req.cookies.refresh_token || req.body.refreshToken;

    if (!refreshToken) {
      return res.status(401).json({
        success: false,
        message: 'Refresh token non fornito'
      });
    }

    // Rotate refresh token
    const { accessToken, refreshToken: newRefreshToken } =
      await refreshTokenService.rotateRefreshToken(refreshToken);

    // Set new tokens
    res.cookie('jwt_token', accessToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 30 * 60 * 1000 // 30 minutes
    });

    res.cookie('refresh_token', newRefreshToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days
    });

    res.json({
      success: true,
      message: 'Token rinnovato con successo',
      token: accessToken,
      expiresIn: '30m'
    });

  } catch (error) {
    console.error('❌ Token refresh error:', error);

    // Clear invalid tokens
    res.clearCookie('jwt_token');
    res.clearCookie('refresh_token');

    res.status(401).json({
      success: false,
      message: error.message || 'Impossibile rinnovare il token'
    });
  }
});

export default router;