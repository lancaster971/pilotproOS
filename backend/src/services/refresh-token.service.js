/**
 * Refresh Token Service
 *
 * Secure refresh token management with rotation
 */

import jwt from 'jsonwebtoken';
import crypto from 'crypto';
import { dbPool } from '../db/pg-pool.js';
import businessLogger from '../utils/logger.js';

/**
 * Refresh token configuration
 */
const REFRESH_TOKEN_EXPIRY = '7d'; // 7 days
const ACCESS_TOKEN_EXPIRY = '30m'; // 30 minutes
const TOKEN_FAMILY_SIZE = 5; // Max tokens per user

/**
 * Generate secure refresh token
 */
export const generateRefreshToken = async (userId) => {
  try {
    // Generate unique token ID
    const tokenId = crypto.randomBytes(16).toString('hex');

    // Create token payload
    const payload = {
      userId,
      tokenId,
      type: 'refresh',
      family: crypto.randomBytes(8).toString('hex')
    };

    // Sign token
    const token = jwt.sign(payload, process.env.JWT_REFRESH_SECRET || process.env.JWT_SECRET, {
      expiresIn: REFRESH_TOKEN_EXPIRY
    });

    // Store in database
    await dbPool.query(
      `INSERT INTO pilotpros.refresh_tokens
       (id, user_id, token_hash, family, expires_at, created_at)
       VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)`,
      [
        tokenId,
        userId,
        crypto.createHash('sha256').update(token).digest('hex'),
        payload.family,
        new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days
      ]
    );

    // Clean up old tokens
    await cleanupOldTokens(userId);

    return token;
  } catch (error) {
    businessLogger.error('Failed to generate refresh token', {
      userId,
      error: error.message
    });
    throw error;
  }
};

/**
 * Verify and rotate refresh token
 */
export const rotateRefreshToken = async (token) => {
  try {
    // Verify token signature
    const decoded = jwt.verify(token, process.env.JWT_REFRESH_SECRET || process.env.JWT_SECRET);

    // Check if token exists in database
    const tokenHash = crypto.createHash('sha256').update(token).digest('hex');
    const result = await dbPool.query(
      `SELECT * FROM pilotpros.refresh_tokens
       WHERE token_hash = $1 AND user_id = $2 AND revoked = false`,
      [tokenHash, decoded.userId]
    );

    if (result.rows.length === 0) {
      // Token not found or revoked - possible reuse attack
      await revokeTokenFamily(decoded.family);
      throw new Error('Invalid refresh token - possible security breach');
    }

    const storedToken = result.rows[0];

    // Check expiry
    if (new Date(storedToken.expires_at) < new Date()) {
      await revokeToken(storedToken.id);
      throw new Error('Refresh token expired');
    }

    // Revoke old token
    await revokeToken(storedToken.id);

    // Generate new tokens
    const newRefreshToken = await generateRefreshToken(decoded.userId);
    const newAccessToken = generateAccessToken(decoded.userId);

    // Log rotation
    businessLogger.info('Refresh token rotated', {
      userId: decoded.userId,
      oldTokenId: storedToken.id,
      family: decoded.family
    });

    return {
      accessToken: newAccessToken,
      refreshToken: newRefreshToken
    };
  } catch (error) {
    if (error.name === 'JsonWebTokenError' || error.name === 'TokenExpiredError') {
      throw new Error('Invalid refresh token');
    }
    throw error;
  }
};

/**
 * Generate new access token
 */
const generateAccessToken = (userId) => {
  // Get user data
  const payload = {
    userId,
    type: 'access'
  };

  return jwt.sign(payload, process.env.JWT_SECRET, {
    expiresIn: ACCESS_TOKEN_EXPIRY
  });
};

/**
 * Revoke single token
 */
const revokeToken = async (tokenId) => {
  await dbPool.query(
    'UPDATE pilotpros.refresh_tokens SET revoked = true WHERE id = $1',
    [tokenId]
  );
};

/**
 * Revoke entire token family (security breach response)
 */
const revokeTokenFamily = async (family) => {
  const result = await dbPool.query(
    'UPDATE pilotpros.refresh_tokens SET revoked = true WHERE family = $1 RETURNING user_id',
    [family]
  );

  if (result.rows.length > 0) {
    businessLogger.warn('Token family revoked - possible security breach', {
      family,
      userId: result.rows[0].user_id
    });
  }
};

/**
 * Clean up old tokens for user
 */
const cleanupOldTokens = async (userId) => {
  // Keep only the latest N tokens
  await dbPool.query(
    `DELETE FROM pilotpros.refresh_tokens
     WHERE user_id = $1 AND id NOT IN (
       SELECT id FROM pilotpros.refresh_tokens
       WHERE user_id = $1
       ORDER BY created_at DESC
       LIMIT $2
     )`,
    [userId, TOKEN_FAMILY_SIZE]
  );

  // Delete expired tokens
  await dbPool.query(
    'DELETE FROM pilotpros.refresh_tokens WHERE expires_at < CURRENT_TIMESTAMP'
  );
};

/**
 * Revoke all tokens for user (logout all sessions)
 */
export const revokeAllUserTokens = async (userId) => {
  await dbPool.query(
    'UPDATE pilotpros.refresh_tokens SET revoked = true WHERE user_id = $1',
    [userId]
  );

  businessLogger.info('All refresh tokens revoked for user', { userId });
};

/**
 * Create refresh tokens table if not exists
 */
export const createRefreshTokenTable = async () => {
  try {
    await dbPool.query(`
      CREATE TABLE IF NOT EXISTS pilotpros.refresh_tokens (
        id VARCHAR(32) PRIMARY KEY,
        user_id UUID NOT NULL REFERENCES pilotpros.users(id) ON DELETE CASCADE,
        token_hash VARCHAR(64) NOT NULL,
        family VARCHAR(16) NOT NULL,
        revoked BOOLEAN DEFAULT false,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(token_hash)
      )
    `);

    await dbPool.query(`
      CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user
      ON pilotpros.refresh_tokens(user_id)
      WHERE revoked = false
    `);

    console.log('✅ Refresh tokens table ready');
  } catch (error) {
    console.error('❌ Failed to create refresh tokens table:', error);
  }
};

export default {
  generateRefreshToken,
  rotateRefreshToken,
  revokeAllUserTokens,
  createRefreshTokenTable
};