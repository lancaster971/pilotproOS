/**
 * SIMPLE AUTH CONTROLLER
 *
 * No bullshit. Just JWT in localStorage.
 * This is how EVERYONE does it in 2024.
 */

import express from 'express';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import crypto from 'crypto';
import { dbPool } from '../db/pg-pool.js';
import config from '../config/index.js';

const router = express.Router();

/**
 * LOGIN - Returns JWT token to store in localStorage
 * NO COOKIES. NO SESSION. JUST TOKEN.
 */
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    // Validate input
    if (!email || !password) {
      return res.status(400).json({
        success: false,
        message: 'Email and password required'
      });
    }

    // Get user from database
    const result = await dbPool.query(
      'SELECT id, email, password_hash, role FROM pilotpros.users WHERE email = $1 AND is_active = true',
      [email]
    );

    const user = result.rows[0];

    // Verify password (or fail safely to prevent timing attacks)
    const isValid = user
      ? await bcrypt.compare(password, user.password_hash)
      : await bcrypt.compare(password, '$2a$12$dummyhashfortimingprotection');

    if (!user || !isValid) {
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials'
      });
    }

    // Generate Access Token (30 minutes - SHORT LIVED)
    const accessToken = jwt.sign(
      {
        userId: user.id,
        email: user.email,
        role: user.role
      },
      config.security.jwtSecret,
      { expiresIn: '30m' } // Changed from 7 days to 30 minutes
    );

    // Generate Refresh Token (cryptographically secure random - 7 days)
    const refreshToken = crypto.randomBytes(32).toString('hex');
    const refreshExpiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days

    // Store refresh token in database
    await dbPool.query(
      `INSERT INTO pilotpros.refresh_tokens (user_id, token, expires_at)
       VALUES ($1, $2, $3)`,
      [user.id, refreshToken, refreshExpiresAt]
    );

    // Set Access Token cookie (30 minutes - SHORT LIVED)
    res.cookie('access_token', accessToken, {
      httpOnly: true,          // Cannot be accessed by JavaScript
      secure: config.server.isProduction, // HTTPS only in production
      sameSite: 'strict',      // CSRF protection
      maxAge: 30 * 60 * 1000   // 30 minutes in milliseconds
    });

    // Set Refresh Token cookie (7 days - LONG LIVED)
    res.cookie('refresh_token', refreshToken, {
      httpOnly: true,          // Cannot be accessed by JavaScript
      secure: config.server.isProduction, // HTTPS only in production
      sameSite: 'strict',      // CSRF protection
      maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days in milliseconds
    });

    // Return token and user data (BACKWARD COMPATIBLE - will remove later)
    res.json({
      success: true,
      token: accessToken, // Keep for backward compatibility with localStorage clients
      user: {
        id: user.id,
        email: user.email,
        role: user.role
      }
    });

  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({
      success: false,
      message: 'Internal server error'
    });
  }
});

/**
 * VERIFY TOKEN - Check if token (from cookie or header) is still valid
 */
router.get('/verify', async (req, res) => {
  try {
    // Get token from Authorization header OR HttpOnly cookie
    const authHeader = req.headers.authorization;
    const headerToken = authHeader?.split(' ')[1];
    const token = headerToken || req.cookies?.access_token;

    if (!token) {
      return res.status(401).json({
        success: false,
        message: 'No token provided'
      });
    }

    // Verify token
    const decoded = jwt.verify(
      token,
      config.security.jwtSecret
    );

    // Token is valid
    res.json({
      success: true,
      user: {
        id: decoded.userId,
        email: decoded.email,
        role: decoded.role
      }
    });

  } catch (error) {
    // Token is invalid or expired
    res.status(401).json({
      success: false,
      message: 'Invalid or expired token'
    });
  }
});

/**
 * REFRESH TOKEN - Generate new access token from refresh token
 */
router.post('/refresh', async (req, res) => {
  try {
    const refreshToken = req.cookies?.refresh_token;

    if (!refreshToken) {
      return res.status(401).json({
        success: false,
        message: 'No refresh token provided'
      });
    }

    // Check if refresh token exists and is not revoked
    const result = await dbPool.query(
      `SELECT user_id, expires_at, revoked_at
       FROM pilotpros.refresh_tokens
       WHERE token = $1`,
      [refreshToken]
    );

    const tokenRecord = result.rows[0];

    // Validate token exists
    if (!tokenRecord) {
      return res.status(403).json({
        success: false,
        message: 'Invalid refresh token'
      });
    }

    // Validate token not revoked
    if (tokenRecord.revoked_at) {
      return res.status(403).json({
        success: false,
        message: 'Refresh token has been revoked'
      });
    }

    // Validate token not expired
    if (new Date(tokenRecord.expires_at) < new Date()) {
      return res.status(403).json({
        success: false,
        message: 'Refresh token has expired'
      });
    }

    // Get user details
    const userResult = await dbPool.query(
      'SELECT id, email, role FROM pilotpros.users WHERE id = $1 AND is_active = true',
      [tokenRecord.user_id]
    );

    const user = userResult.rows[0];

    if (!user) {
      return res.status(403).json({
        success: false,
        message: 'User not found or inactive'
      });
    }

    // Generate new access token (30 minutes)
    const newAccessToken = jwt.sign(
      {
        userId: user.id,
        email: user.email,
        role: user.role
      },
      config.security.jwtSecret,
      { expiresIn: '30m' }
    );

    // Set new access token cookie
    res.cookie('access_token', newAccessToken, {
      httpOnly: true,
      secure: config.server.isProduction,
      sameSite: 'strict',
      maxAge: 30 * 60 * 1000 // 30 minutes
    });

    res.json({
      success: true,
      message: 'Access token refreshed successfully',
      user: {
        id: user.id,
        email: user.email,
        role: user.role
      }
    });

  } catch (error) {
    console.error('Refresh error:', error);
    res.status(500).json({
      success: false,
      message: 'Internal server error'
    });
  }
});

/**
 * LOGOUT - Clear HttpOnly cookies and revoke refresh token
 */
router.post('/logout', async (req, res) => {
  try {
    const refreshToken = req.cookies?.refresh_token;

    // Revoke refresh token in database if exists
    if (refreshToken) {
      await dbPool.query(
        `UPDATE pilotpros.refresh_tokens
         SET revoked_at = CURRENT_TIMESTAMP
         WHERE token = $1 AND revoked_at IS NULL`,
        [refreshToken]
      );
    }

    // Clear both cookies
    res.clearCookie('access_token', {
      httpOnly: true,
      secure: config.server.isProduction,
      sameSite: 'strict'
    });

    res.clearCookie('refresh_token', {
      httpOnly: true,
      secure: config.server.isProduction,
      sameSite: 'strict'
    });

    res.json({
      success: true,
      message: 'Logged out successfully'
    });

  } catch (error) {
    console.error('Logout error:', error);
    // Still clear cookies even if DB update fails
    res.clearCookie('access_token', {
      httpOnly: true,
      secure: config.server.isProduction,
      sameSite: 'strict'
    });

    res.clearCookie('refresh_token', {
      httpOnly: true,
      secure: config.server.isProduction,
      sameSite: 'strict'
    });

    res.status(500).json({
      success: false,
      message: 'Logout completed with warnings'
    });
  }
});

export default router;