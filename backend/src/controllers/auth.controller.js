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

    // Return token and user data (NO COOKIES!)
    res.json({
      success: true,
      token,
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
 * VERIFY TOKEN - Optional endpoint to check if token is still valid
 * Frontend can use this on app init if needed
 */
router.get('/verify', async (req, res) => {
  try {
    // Get token from Authorization header
    const token = req.headers.authorization?.split(' ')[1];

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
 * LOGOUT - Frontend just clears localStorage
 * But we can have this endpoint for consistency
 */
router.post('/logout', (req, res) => {
  // Nothing to do server-side. Frontend clears localStorage.
  res.json({
    success: true,
    message: 'Logged out successfully'
  });
});

export default router;