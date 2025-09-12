/**
 * JWT Authentication
 * 
 * Sistema di autenticazione per API con JWT tokens
 */

import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import crypto from 'crypto';
import { dbPool } from '../db/connection.js';

export const defaultAuthConfig = {
  jwtSecret: process.env.JWT_SECRET || crypto.randomBytes(64).toString('hex'),
  jwtExpiresIn: process.env.JWT_EXPIRES_IN || '15m', // Short-lived access tokens
  refreshTokenExpiresIn: process.env.REFRESH_TOKEN_EXPIRES_IN || '7d', // Long-lived refresh tokens
  saltRounds: parseInt(process.env.SALT_ROUNDS || '12'),
  apiKeyLength: 32
};

// JWT Payload structure: { userId, role, permissions, iat?, exp? }
// AuthUser structure: { id, email, role, permissions, created_at, last_login_at? }

/**
 * JWT Authentication Service
 */
export class JwtAuthService {
  constructor(config) {
    this.config = { ...defaultAuthConfig, ...config };
    this.db = dbPool;
    
    if (this.config.jwtSecret.length < 32) {
      throw new Error('JWT_SECRET deve essere almeno 32 caratteri');
    }
  }

  /**
   * Genera JWT access token per utente (short-lived)
   */
  generateToken(user) {
    const payload = {
      userId: user.id,
      role: user.role,
      permissions: user.permissions,
      type: 'access'
    };

    return jwt.sign(payload, this.config.jwtSecret, {
      expiresIn: this.config.jwtExpiresIn,
      algorithm: 'HS256'
    });
  }

  /**
   * Genera refresh token (long-lived)
   */
  generateRefreshToken(user) {
    const payload = {
      userId: user.id,
      type: 'refresh',
      tokenId: crypto.randomUUID() // Unique token ID for revocation
    };

    return jwt.sign(payload, this.config.jwtSecret, {
      expiresIn: this.config.refreshTokenExpiresIn,
      algorithm: 'HS256'
    });
  }

  /**
   * Set secure HttpOnly cookies for authentication
   */
  setAuthCookies(res, accessToken, refreshToken) {
    const isProduction = process.env.NODE_ENV === 'production';
    
    // Access token cookie (short-lived, HttpOnly)
    res.cookie('access_token', accessToken, {
      httpOnly: true,
      secure: isProduction, // HTTPS only in production
      sameSite: 'lax', // CSRF protection
      maxAge: 15 * 60 * 1000, // 15 minutes
      path: '/'
    });

    // Refresh token cookie (long-lived, HttpOnly)
    res.cookie('refresh_token', refreshToken, {
      httpOnly: true,
      secure: isProduction, // HTTPS only in production  
      sameSite: 'lax', // CSRF protection
      maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
      path: '/api/auth/refresh' // Only accessible to refresh endpoint
    });
  }

  /**
   * Clear authentication cookies
   */
  clearAuthCookies(res) {
    res.clearCookie('access_token', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/'
    });
    
    res.clearCookie('refresh_token', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/api/auth/refresh'
    });
  }

  /**
   * Verifica validità JWT token
   */
  verifyToken(token) {
    try {
      return jwt.verify(token, this.config.jwtSecret);
    } catch (error) {
      throw new Error(`Token non valido: ${error.message}`);
    }
  }

  /**
   * Hash password usando bcrypt
   */
  async hashPassword(password) {
    return bcrypt.hash(password, this.config.saltRounds);
  }

  /**
   * Verifica password contro hash
   */
  async verifyPassword(password, hash) {
    return bcrypt.compare(password, hash);
  }

  /**
   * Genera API key random
   */
  generateApiKey() {
    return crypto.randomBytes(this.config.apiKeyLength).toString('hex');
  }

  /**
   * Login utente con email/password con tracking tentativi falliti
   */
  async login(email, password, clientIP = null) {
    try {
      // Check for rate limiting based on failed attempts
      await this.checkLoginRateLimit(email, clientIP);

      const result = await this.db`
        SELECT 
          id, email, password_hash, role,
          created_at, last_login
        FROM pilotpros.users 
        WHERE email = ${email} AND is_active = true
      `;
      const userRecord = result[0];

      if (!userRecord) {
        await this.recordFailedLogin(email, clientIP, 'USER_NOT_FOUND');
        throw new Error('Credenziali non valide');
      }

      const isValidPassword = await this.verifyPassword(password, userRecord.password_hash);
      if (!isValidPassword) {
        await this.recordFailedLogin(email, clientIP, 'INVALID_PASSWORD');
        throw new Error('Credenziali non valide');
      }

      // Clear failed attempts on successful login
      await this.clearFailedAttempts(email, clientIP);

      // Update last login
      await this.db`
        UPDATE pilotpros.users SET last_login = CURRENT_TIMESTAMP WHERE id = ${userRecord.id}
      `;

      const user = {
        id: userRecord.id,
        email: userRecord.email,
        role: userRecord.role,
        permissions: this.getDefaultPermissions(userRecord.role),
        created_at: userRecord.created_at,
        last_login_at: new Date()
      };

      const accessToken = this.generateToken(user);
      const refreshToken = this.generateRefreshToken(user);
      
      // Track active session for concurrent session control
      await this.createActiveSession(user.id, refreshToken, clientIP);
      
      // Cleanup and limit concurrent sessions
      await this.cleanupAndLimitSessions(user.id);
      
      return { user, accessToken, refreshToken };
    } catch (error) {
      console.error('❌ Login failed:', error);
      throw error;
    }
  }

  /**
   * Verifica API key
   */
  async verifyApiKey(apiKey) {
    try {
      const result = await this.db`
        SELECT 
          u.id, u.email, u.role, u.created_at, u.last_login
        FROM pilotpros.users u
        JOIN pilotpros.api_keys ak ON u.id = ak.user_id
        WHERE ak.api_key = ${apiKey} AND ak.is_active = true AND u.is_active = true
      `;
      const userRecord = result[0];

      if (!userRecord) {
        return null;
      }

      return {
        id: userRecord.id,
        email: userRecord.email,
        role: userRecord.role,
        permissions: this.getDefaultPermissions(userRecord.role),
        created_at: userRecord.created_at,
        last_login_at: userRecord.last_login
      };
    } catch (error) {
      console.error('❌ API key verification failed:', error);
      return null;
    }
  }

  /**
   * Registra nuovo utente
   */
  async register(userData) {
    const {
      email,
      password,
      role = 'user',
      permissions = []
    } = userData;

    try {
      // Check if user exists
      const existingUsers = await this.db`
        SELECT id FROM pilotpros.users WHERE email = ${email}
      `;
      const existingUser = existingUsers[0];

      if (existingUser) {
        throw new Error('Utente già esistente');
      }

      const passwordHash = await this.hashPassword(password);
      const defaultPermissions = this.getDefaultPermissions(role);
      const userPermissions = [...new Set([...defaultPermissions, ...permissions])];

      const result = await this.db`
        INSERT INTO pilotpros.users (
          email, password_hash, role
        ) VALUES (${email}, ${passwordHash}, ${role})
        RETURNING id, email, role, created_at
      `;
      const userRecord = result[0];

      const user = {
        id: userRecord.id,
        email: userRecord.email,
        role: userRecord.role,
        permissions: this.getDefaultPermissions(userRecord.role),
        created_at: userRecord.created_at,
        last_login_at: null
      };

      const token = this.generateToken(user);
      
      return { user, token };
    } catch (error) {
      console.error('❌ Registration failed:', error);
      throw error;
    }
  }

  /**
   * Parse JSON sicuro per permissions
   */
  safeJsonParse(jsonString) {
    if (!jsonString) return [];
    if (Array.isArray(jsonString)) return jsonString;
    
    try {
      return JSON.parse(jsonString);
    } catch {
      return [];
    }
  }

  /**
   * Get default permissions per role
   */
  getDefaultPermissions(role) {
    const rolePermissions = {
      'admin': [
        'users:read', 'users:write', 'users:delete',
        'workflows:read', 'workflows:write', 'workflows:delete',
        'system:read', 'system:write'
      ],
      'user': [
        'workflows:read', 'workflows:write',
        'executions:read'
      ],
      'readonly': [
        'workflows:read', 'executions:read'
      ]
    };

    return rolePermissions[role] || [];
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshAccessToken(refreshToken) {
    try {
      const payload = this.verifyToken(refreshToken);
      
      if (payload.type !== 'refresh') {
        throw new Error('Token type non valido');
      }

      const user = await this.getUserById(payload.userId);
      if (!user) {
        throw new Error('Utente non trovato');
      }

      const newAccessToken = this.generateToken(user);
      const newRefreshToken = this.generateRefreshToken(user);
      
      return { user, accessToken: newAccessToken, refreshToken: newRefreshToken };
    } catch (error) {
      console.error('❌ Token refresh failed:', error);
      throw error;
    }
  }

  /**
   * Middleware per autenticazione JWT/API Key con cookie support
   */
  authenticateToken() {
    return async (req, res, next) => {
      try {
        const authHeader = req.headers.authorization;
        let user = null;
        let token = null;

        // Priority: 1. Authorization header, 2. HttpOnly cookie, 3. API Key
        if (authHeader?.startsWith('Bearer ')) {
          // JWT Token authentication (fallback for API calls)
          token = authHeader.substring(7);
        } else if (req.cookies?.access_token) {
          // HttpOnly cookie authentication (primary method)
          token = req.cookies.access_token;
        } else if (authHeader?.startsWith('ApiKey ')) {
          // API Key authentication  
          const apiKey = authHeader.substring(7);
          user = await this.verifyApiKey(apiKey);
        } else if (req.headers['x-api-key']) {
          // API Key in custom header
          user = await this.verifyApiKey(req.headers['x-api-key']);
        }

        // Process JWT token (from header or cookie)
        if (token && !user) {
          const payload = this.verifyToken(token);
          if (payload.type === 'access') {
            user = await this.getUserById(payload.userId);
          }
        }

        if (!user) {
          return res.status(401).json({
            success: false,
            message: 'Token di autenticazione richiesto'
          });
        }

        req.user = user;
        next();
      } catch (error) {
        console.error('❌ Authentication failed:', error);
        
        // If token expired, try to refresh automatically
        if (error.message.includes('expired') && req.cookies?.refresh_token) {
          try {
            const refreshResult = await this.refreshAccessToken(req.cookies.refresh_token);
            this.setAuthCookies(res, refreshResult.accessToken, refreshResult.refreshToken);
            req.user = refreshResult.user;
            return next();
          } catch (refreshError) {
            console.error('❌ Auto-refresh failed:', refreshError);
            this.clearAuthCookies(res);
          }
        }
        
        return res.status(401).json({
          success: false,
          message: 'Token non valido'
        });
      }
    };
  }

  /**
   * Middleware per controllo permessi
   */
  requirePermission(permission) {
    return (req, res, next) => {
      if (!req.user) {
        return res.status(401).json({
          success: false,
          message: 'Autenticazione richiesta'
        });
      }

      const userPermissions = req.user.permissions || [];
      const hasPermission = userPermissions.includes(permission) || 
                           userPermissions.includes('*') ||
                           req.user.role === 'admin';

      if (!hasPermission) {
        return res.status(403).json({
          success: false,
          message: `Permesso richiesto: ${permission}`
        });
      }

      next();
    };
  }

  /**
   * Middleware per controllo accesso (single-tenant mode)
   */
  requireAccess() {
    return (req, res, next) => {
      if (!req.user) {
        return res.status(401).json({
          success: false,
          message: 'Autenticazione richiesta'
        });
      }

      // In single-tenant mode, all authenticated users have access
      next();
    };
  }

  /**
   * Check login rate limiting based on failed attempts
   */
  async checkLoginRateLimit(email, clientIP) {
    try {
      const failedAttempts = await this.db`
        SELECT COUNT(*) as count
        FROM pilotpros.failed_login_attempts 
        WHERE (email = ${email} OR ip_address = ${clientIP})
        AND created_at > NOW() - INTERVAL '1 minute'
      `;
      
      const attemptCount = parseInt(failedAttempts[0]?.count || 0);
      
      if (attemptCount >= 5) {
        throw new Error('Troppi tentativi falliti. Riprova tra 1 minuto.');
      }
    } catch (error) {
      // If table doesn't exist, create it
      if (error.message.includes('does not exist')) {
        await this.createFailedAttemptsTable();
        return; // First attempt after table creation
      }
      throw error;
    }
  }

  /**
   * Record failed login attempt
   */
  async recordFailedLogin(email, clientIP, reason) {
    try {
      await this.db`
        INSERT INTO pilotpros.failed_login_attempts (email, ip_address, reason, created_at)
        VALUES (${email}, ${clientIP}, ${reason}, CURRENT_TIMESTAMP)
      `;
    } catch (error) {
      console.error('Failed to record login attempt:', error);
    }
  }

  /**
   * Clear failed attempts on successful login
   */
  async clearFailedAttempts(email, clientIP) {
    try {
      await this.db`
        DELETE FROM pilotpros.failed_login_attempts 
        WHERE email = ${email} OR ip_address = ${clientIP}
      `;
    } catch (error) {
      console.error('Failed to clear login attempts:', error);
    }
  }

  /**
   * Create failed attempts table if it doesn't exist
   */
  async createFailedAttemptsTable() {
    try {
      await this.db`
        CREATE TABLE IF NOT EXISTS pilotpros.failed_login_attempts (
          id SERIAL PRIMARY KEY,
          email VARCHAR(255),
          ip_address INET,
          reason VARCHAR(50),
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_failed_attempts_email_time 
        ON pilotpros.failed_login_attempts(email, created_at);
        
        CREATE INDEX IF NOT EXISTS idx_failed_attempts_ip_time 
        ON pilotpros.failed_login_attempts(ip_address, created_at);
      `;
      console.log('✅ Failed login attempts table created');
    } catch (error) {
      console.error('❌ Failed to create login attempts table:', error);
    }
  }

  /**
   * Create active session tracking
   */
  async createActiveSession(userId, refreshToken, clientIP) {
    try {
      // Extract token ID from refresh token
      const payload = jwt.verify(refreshToken, this.config.jwtSecret);
      const tokenId = payload.tokenId;
      
      await this.db`
        INSERT INTO pilotpros.active_sessions (user_id, token_id, ip_address, created_at, last_activity)
        VALUES (${userId}, ${tokenId}, ${clientIP}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id, token_id) DO UPDATE SET
          ip_address = EXCLUDED.ip_address,
          last_activity = CURRENT_TIMESTAMP
      `;
    } catch (error) {
      if (error.message.includes('does not exist')) {
        await this.createActiveSessionsTable();
        return this.createActiveSession(userId, refreshToken, clientIP);
      }
      console.error('Failed to create active session:', error);
    }
  }

  /**
   * Clean expired and limit concurrent sessions
   */
  async cleanupAndLimitSessions(userId) {
    try {
      // Clean expired sessions (refresh tokens older than 7 days)
      await this.db`
        DELETE FROM pilotpros.active_sessions 
        WHERE user_id = ${userId} 
        AND created_at < NOW() - INTERVAL '7 days'
      `;
      
      // Limit to max 3 concurrent sessions per user
      const sessions = await this.db`
        SELECT token_id FROM pilotpros.active_sessions 
        WHERE user_id = ${userId} 
        ORDER BY last_activity DESC
      `;
      
      if (sessions.length > 3) {
        const oldSessionIds = sessions.slice(3).map(s => s.token_id);
        await this.db`
          DELETE FROM pilotpros.active_sessions 
          WHERE user_id = ${userId} 
          AND token_id = ANY(${oldSessionIds})
        `;
        console.log(`✅ Limited user ${userId} to 3 concurrent sessions`);
      }
    } catch (error) {
      console.error('Failed to cleanup sessions:', error);
    }
  }

  /**
   * Revoke session on logout
   */
  async revokeSession(refreshToken) {
    try {
      const payload = jwt.verify(refreshToken, this.config.jwtSecret);
      await this.db`
        DELETE FROM pilotpros.active_sessions 
        WHERE token_id = ${payload.tokenId}
      `;
    } catch (error) {
      console.error('Failed to revoke session:', error);
    }
  }

  /**
   * Create active sessions table
   */
  async createActiveSessionsTable() {
    try {
      await this.db`
        CREATE TABLE IF NOT EXISTS pilotpros.active_sessions (
          id SERIAL PRIMARY KEY,
          user_id UUID NOT NULL,
          token_id UUID NOT NULL,
          ip_address INET,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(user_id, token_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_active_sessions_user_activity 
        ON pilotpros.active_sessions(user_id, last_activity DESC);
        
        CREATE INDEX IF NOT EXISTS idx_active_sessions_token 
        ON pilotpros.active_sessions(token_id);
      `;
      console.log('✅ Active sessions table created');
    } catch (error) {
      console.error('❌ Failed to create active sessions table:', error);
    }
  }

  /**
   * Get user by ID
   */
  async getUserById(userId) {
    try {
      const result = await this.db`
        SELECT 
          id, email, role, created_at, last_login
        FROM pilotpros.users 
        WHERE id = ${userId} AND is_active = true
      `;
      const userRecord = result[0];

      if (!userRecord) {
        return null;
      }

      return {
        id: userRecord.id,
        email: userRecord.email,
        role: userRecord.role,
        permissions: this.getDefaultPermissions(userRecord.role),
        created_at: userRecord.created_at,
        last_login_at: userRecord.last_login
      };
    } catch (error) {
      console.error('❌ Failed to get user by ID:', error);
      return null;
    }
  }
}

// Singleton instance
let authServiceInstance = null;

export function getAuthService(config) {
  if (!authServiceInstance) {
    authServiceInstance = new JwtAuthService(config);
  }
  return authServiceInstance;
}