/**
 * JWT Authentication
 * 
 * Sistema di autenticazione per API multi-tenant con JWT tokens
 */

import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';
import crypto from 'crypto';
import { DatabaseConnection } from '../database/connection.js';

export const defaultAuthConfig = {
  jwtSecret: process.env.JWT_SECRET || crypto.randomBytes(64).toString('hex'),
  jwtExpiresIn: process.env.JWT_EXPIRES_IN || '24h',
  saltRounds: parseInt(process.env.SALT_ROUNDS || '12'),
  apiKeyLength: 32
};

// JWT Payload structure: { userId, tenantId?, role, permissions, iat?, exp? }
// AuthUser structure: { id, email, role, tenant_id?, api_key?, permissions, created_at, last_login_at? }

/**
 * JWT Authentication Service
 */
export class JwtAuthService {
  constructor(config) {
    this.config = { ...defaultAuthConfig, ...config };
    this.db = DatabaseConnection.getInstance();
    
    if (this.config.jwtSecret.length < 32) {
      throw new Error('JWT_SECRET deve essere almeno 32 caratteri');
    }
  }

  /**
   * Genera JWT token per utente
   */
  generateToken(user) {
    const payload = {
      userId: user.id,
      tenantId: user.tenant_id,
      role: user.role,
      permissions: user.permissions
    };

    return jwt.sign(payload, this.config.jwtSecret, {
      expiresIn: this.config.jwtExpiresIn,
      algorithm: 'HS256'
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
   * Login utente con email/password
   */
  async login(email, password) {
    try {
      const userRecord = await this.db.getOne(`
        SELECT 
          id, email, password_hash, role, tenant_id,
          permissions, created_at, last_login
        FROM pilotpros.users 
        WHERE email = $1 AND is_active = true
      `, [email]);

      if (!userRecord) {
        throw new Error('Credenziali non valide');
      }

      const isValidPassword = await this.verifyPassword(password, userRecord.password_hash);
      if (!isValidPassword) {
        throw new Error('Credenziali non valide');
      }

      // Update last login
      await this.db.query(`
        UPDATE pilotpros.users SET last_login = CURRENT_TIMESTAMP WHERE id = $1
      `, [userRecord.id]);

      const user = {
        id: userRecord.id,
        email: userRecord.email,
        role: userRecord.role,
        tenant_id: userRecord.tenant_id,
        permissions: this.safeJsonParse(userRecord.permissions),
        created_at: userRecord.created_at,
        last_login_at: new Date()
      };

      const token = this.generateToken(user);
      
      return { user, token };
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
      const userRecord = await this.db.getOne(`
        SELECT 
          u.id, u.email, u.role, u.tenant_id, u.permissions, u.created_at, u.last_login
        FROM pilotpros.users u
        JOIN pilotpros.api_keys ak ON u.id = ak.user_id
        WHERE ak.api_key = $1 AND ak.is_active = true AND u.is_active = true
      `, [apiKey]);

      if (!userRecord) {
        return null;
      }

      return {
        id: userRecord.id,
        email: userRecord.email,
        role: userRecord.role,
        tenant_id: userRecord.tenant_id,
        permissions: this.safeJsonParse(userRecord.permissions),
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
      tenant_id,
      permissions = []
    } = userData;

    try {
      // Check if user exists
      const existingUser = await this.db.getOne(`
        SELECT id FROM pilotpros.users WHERE email = $1
      `, [email]);

      if (existingUser) {
        throw new Error('Utente già esistente');
      }

      const passwordHash = await this.hashPassword(password);
      const defaultPermissions = this.getDefaultPermissions(role);
      const userPermissions = [...new Set([...defaultPermissions, ...permissions])];

      const userRecord = await this.db.getOne(`
        INSERT INTO pilotpros.users (
          email, password_hash, role, tenant_id, permissions
        ) VALUES ($1, $2, $3, $4, $5)
        RETURNING id, email, role, tenant_id, permissions, created_at
      `, [email, passwordHash, role, tenant_id, JSON.stringify(userPermissions)]);

      const user = {
        id: userRecord.id,
        email: userRecord.email,
        role: userRecord.role,
        tenant_id: userRecord.tenant_id,
        permissions: userPermissions,
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
   * Middleware per autenticazione JWT/API Key
   */
  authenticateToken() {
    return async (req, res, next) => {
      try {
        const authHeader = req.headers.authorization;
        let user = null;

        if (authHeader?.startsWith('Bearer ')) {
          // JWT Token authentication
          const token = authHeader.substring(7);
          const payload = this.verifyToken(token);
          user = await this.getUserById(payload.userId);
        } else if (authHeader?.startsWith('ApiKey ')) {
          // API Key authentication  
          const apiKey = authHeader.substring(7);
          user = await this.verifyApiKey(apiKey);
        } else if (req.headers['x-api-key']) {
          // API Key in custom header
          user = await this.verifyApiKey(req.headers['x-api-key']);
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
   * Middleware per controllo accesso tenant
   */
  requireTenantAccess(tenantIdParam = 'tenantId') {
    return (req, res, next) => {
      if (!req.user) {
        return res.status(401).json({
          success: false,
          message: 'Autenticazione richiesta'
        });
      }

      // Admin can access any tenant
      if (req.user.role === 'admin') {
        return next();
      }

      const requestedTenantId = req.params[tenantIdParam];
      if (req.user.tenant_id !== requestedTenantId) {
        return res.status(403).json({
          success: false,
          message: 'Accesso tenant non autorizzato'
        });
      }

      next();
    };
  }

  /**
   * Get user by ID
   */
  async getUserById(userId) {
    try {
      const userRecord = await this.db.getOne(`
        SELECT 
          id, email, role, tenant_id, permissions, created_at, last_login
        FROM pilotpros.users 
        WHERE id = $1 AND is_active = true
      `, [userId]);

      if (!userRecord) {
        return null;
      }

      return {
        id: userRecord.id,
        email: userRecord.email,
        role: userRecord.role,
        tenant_id: userRecord.tenant_id,
        permissions: this.safeJsonParse(userRecord.permissions),
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