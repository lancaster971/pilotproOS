/**
 * SIMPLE AUTH CONTROLLER
 *
 * No bullshit. Just JWT in localStorage.
 * This is how EVERYONE does it in 2024.
 */

import express from 'express';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
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

    // Generate JWT token (7 days expiry is fine)
    const token = jwt.sign(
      {
        userId: user.id,
        email: user.email,
        role: user.role
      },
      config.security.jwtSecret,
      { expiresIn: config.security.jwtExpiresIn }
    );

    // Set HttpOnly cookie (SECURITY: XSS protection)
    res.cookie('access_token', token, {
      httpOnly: true,          // Cannot be accessed by JavaScript
      secure: config.server.isProduction, // HTTPS only in production
      sameSite: 'strict',      // CSRF protection
      maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days in milliseconds
    });

    // Return token and user data (BACKWARD COMPATIBLE - will remove later)
    res.json({
      success: true,
      token, // Keep for backward compatibility with localStorage clients
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
 * LOGOUT - Clear HttpOnly cookie
 */
router.post('/logout', (req, res) => {
  // Clear HttpOnly cookie
  res.clearCookie('access_token', {
    httpOnly: true,
    secure: config.server.isProduction,
    sameSite: 'strict'
  });

  res.json({
    success: true,
    message: 'Logged out successfully'
  });
});

export default router;