/**
 * JWT Authentication
 * 
 * Sistema di autenticazione per API multi-tenant con JWT tokens
 */

import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';
import crypto from 'crypto';
import { Request, Response, NextFunction } from 'express';
import { DatabaseConnection } from '../database/connection.js';

export interface AuthConfig {
  jwtSecret: string;
  jwtExpiresIn: string;
  saltRounds: number;
  apiKeyLength: number;
}

export const defaultAuthConfig: AuthConfig = {
  jwtSecret: process.env.JWT_SECRET || crypto.randomBytes(64).toString('hex'),
  jwtExpiresIn: process.env.JWT_EXPIRES_IN || '24h',
  saltRounds: parseInt(process.env.SALT_ROUNDS || '12'),
  apiKeyLength: 32
};

export interface JwtPayload {
  userId: string;
  tenantId?: string;
  role: 'admin' | 'tenant' | 'readonly';
  permissions: string[];
  iat?: number;
  exp?: number;
}

export interface AuthUser {
  id: string;
  email: string;
  role: 'admin' | 'tenant' | 'readonly';
  tenant_id?: string;
  api_key?: string;
  permissions: string[];
  created_at: Date;
  last_login_at?: Date;
}

/**
 * JWT Authentication Service
 */
export class JwtAuthService {
  private config: AuthConfig;
  private db: DatabaseConnection;

  constructor(config?: Partial<AuthConfig>) {
    this.config = { ...defaultAuthConfig, ...config };
    this.db = DatabaseConnection.getInstance();
    
    if (this.config.jwtSecret.length < 32) {
      throw new Error('JWT_SECRET deve essere almeno 32 caratteri');
    }
  }

  /**
   * Genera JWT token per utente
   */
  generateToken(user: AuthUser): string {
    const payload: JwtPayload = {
      userId: user.id,
      tenantId: user.tenant_id,
      role: user.role,
      permissions: user.permissions
    };

    return jwt.sign(payload, this.config.jwtSecret, {
      expiresIn: this.config.jwtExpiresIn,
      issuer: 'n8n-mcp-server',
      subject: user.id
    } as jwt.SignOptions);
  }

  /**
   * Verifica e decodifica JWT token
   */
  verifyToken(token: string): JwtPayload {
    try {
      return jwt.verify(token, this.config.jwtSecret) as JwtPayload;
    } catch (error) {
      if (error instanceof jwt.JsonWebTokenError) {
        throw new Error('Token JWT non valido');
      } else if (error instanceof jwt.TokenExpiredError) {
        throw new Error('Token JWT scaduto');
      } else {
        throw new Error('Errore verifica token');
      }
    }
  }

  /**
   * Hash password con bcrypt
   */
  async hashPassword(password: string): Promise<string> {
    return await bcrypt.hash(password, this.config.saltRounds);
  }

  /**
   * Verifica password
   */
  async verifyPassword(password: string, hash: string): Promise<boolean> {
    return await bcrypt.compare(password, hash);
  }

  /**
   * Genera API key sicura
   */
  generateApiKey(): string {
    return crypto.randomBytes(this.config.apiKeyLength).toString('hex');
  }

  /**
   * Login utente con email/password
   */
  async login(email: string, password: string): Promise<{ user: AuthUser; token: string }> {
    try {
      // Cerca utente nel database
      const userRecord = await this.db.getOne(`
        SELECT 
          id, email, password_hash, role, tenant_id, permissions,
          api_key, created_at, last_login_at
        FROM auth_users 
        WHERE email = $1 AND active = true
      `, [email.toLowerCase()]);

      if (!userRecord) {
        throw new Error('Credenziali non valide');
      }

      // Verifica password
      const passwordValid = await this.verifyPassword(password, userRecord.password_hash);
      if (!passwordValid) {
        throw new Error('Credenziali non valide');
      }

      // Aggiorna ultimo login
      await this.db.query(`
        UPDATE auth_users 
        SET last_login_at = CURRENT_TIMESTAMP
        WHERE id = $1
      `, [userRecord.id]);

      // Crea user object (senza password)
      const user: AuthUser = {
        id: userRecord.id,
        email: userRecord.email,
        role: userRecord.role,
        tenant_id: userRecord.tenant_id,
        api_key: userRecord.api_key,
        permissions: typeof userRecord.permissions === 'string' ? JSON.parse(userRecord.permissions) : userRecord.permissions || [],
        created_at: userRecord.created_at,
        last_login_at: new Date()
      };

      // Genera token
      const token = this.generateToken(user);

      return { user, token };

    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  /**
   * Verifica API Key
   */
  async verifyApiKey(apiKey: string): Promise<AuthUser | null> {
    try {
      const userRecord = await this.db.getOne(`
        SELECT 
          id, email, role, tenant_id, permissions,
          api_key, created_at, last_login_at
        FROM auth_users 
        WHERE api_key = $1 AND active = true
      `, [apiKey]);

      if (!userRecord) {
        return null;
      }

      return {
        id: userRecord.id,
        email: userRecord.email,
        role: userRecord.role,
        tenant_id: userRecord.tenant_id,
        api_key: userRecord.api_key,
        permissions: typeof userRecord.permissions === 'string' ? JSON.parse(userRecord.permissions) : userRecord.permissions || [],
        created_at: userRecord.created_at,
        last_login_at: userRecord.last_login_at
      };

    } catch (error) {
      console.error('API Key verification error:', error);
      return null;
    }
  }

  /**
   * Crea nuovo utente
   */
  async createUser(userData: {
    email: string;
    password: string;
    role: 'admin' | 'tenant' | 'readonly';
    tenant_id?: string;
    permissions?: string[];
  }): Promise<AuthUser> {
    try {
      // Verifica che l'email non esista già
      const existing = await this.db.getOne(
        'SELECT id FROM auth_users WHERE email = $1',
        [userData.email.toLowerCase()]
      );

      if (existing) {
        throw new Error('Email già registrata');
      }

      // Hash password
      const passwordHash = await this.hashPassword(userData.password);
      
      // Genera API key
      const apiKey = this.generateApiKey();

      // Definisci permessi di default basati su ruolo
      const defaultPermissions = this.getDefaultPermissions(userData.role);
      const permissions = userData.permissions || defaultPermissions;

      // Inserisci utente
      const userRecord = await this.db.getOne(`
        INSERT INTO auth_users (
          id, email, password_hash, role, tenant_id, permissions,
          api_key, active, created_at
        ) VALUES (
          gen_random_uuid(), $1, $2, $3, $4, $5, $6, true, CURRENT_TIMESTAMP
        ) RETURNING 
          id, email, role, tenant_id, permissions, api_key, created_at
      `, [
        userData.email.toLowerCase(),
        passwordHash,
        userData.role,
        userData.tenant_id,
        JSON.stringify(permissions),
        apiKey
      ]);

      return {
        id: userRecord.id,
        email: userRecord.email,
        role: userRecord.role,
        tenant_id: userRecord.tenant_id,
        api_key: userRecord.api_key,
        permissions: JSON.parse(userRecord.permissions),
        created_at: userRecord.created_at
      };

    } catch (error) {
      console.error('Create user error:', error);
      throw error;
    }
  }

  /**
   * Ottieni permessi di default per ruolo
   */
  private getDefaultPermissions(role: string): string[] {
    switch (role) {
      case 'admin':
        return [
          'scheduler:read', 'scheduler:write', 'scheduler:control',
          'tenants:read', 'tenants:write', 'tenants:delete',
          'users:read', 'users:write', 'users:delete',
          'logs:read', 'stats:read', 'system:read'
        ];
      case 'tenant':
        return [
          'scheduler:read', 'tenants:read', 'logs:read', 'stats:read'
        ];
      case 'readonly':
        return [
          'scheduler:read', 'tenants:read', 'logs:read', 'stats:read'
        ];
      default:
        return ['scheduler:read'];
    }
  }

  /**
   * Middleware Express per autenticazione JWT
   */
  authenticateToken() {
    return async (req: Request & { user?: AuthUser }, res: Response, next: NextFunction) => {
      try {
        const authHeader = req.headers['authorization'];
        const apiKey = req.headers['x-api-key'] as string;

        let user: AuthUser | null = null;

        if (apiKey) {
          // Autenticazione con API Key
          user = await this.verifyApiKey(apiKey);
          if (!user) {
            return res.status(401).json({
              error: 'Unauthorized',
              message: 'API Key non valida'
            });
          }
        } else if (authHeader?.startsWith('Bearer ')) {
          // Autenticazione con JWT Token
          const token = authHeader.substring(7);
          const payload = this.verifyToken(token);
          
          // Recupera utente completo dal database
          user = await this.getUserById(payload.userId);
          if (!user) {
            return res.status(401).json({
              error: 'Unauthorized',
              message: 'Utente non trovato'
            });
          }
        } else {
          return res.status(401).json({
            error: 'Unauthorized',
            message: 'Token di autenticazione richiesto'
          });
        }

        // Aggiungi user alla request
        req.user = user;
        next();

      } catch (error) {
        return res.status(401).json({
          error: 'Unauthorized',
          message: error instanceof Error ? error.message : 'Autenticazione fallita'
        });
      }
    };
  }

  /**
   * Middleware per verifica permessi
   */
  requirePermission(permission: string) {
    return (req: Request & { user?: AuthUser }, res: Response, next: NextFunction) => {
      if (!req.user) {
        return res.status(401).json({
          error: 'Unauthorized',
          message: 'Autenticazione richiesta'
        });
      }

      if (!req.user.permissions.includes(permission)) {
        return res.status(403).json({
          error: 'Forbidden',
          message: `Permesso richiesto: ${permission}`
        });
      }

      next();
    };
  }

  /**
   * Middleware per isolamento tenant
   */
  requireTenantAccess(tenantIdParam: string = 'tenantId') {
    return (req: Request & { user?: AuthUser }, res: Response, next: NextFunction) => {
      if (!req.user) {
        return res.status(401).json({
          error: 'Unauthorized',
          message: 'Autenticazione richiesta'
        });
      }

      const requestedTenantId = req.params[tenantIdParam] || req.body.tenantId;

      // Admin può accedere a tutti i tenant
      if (req.user.role === 'admin') {
        return next();
      }

      // Altri ruoli possono accedere solo al proprio tenant
      if (req.user.tenant_id !== requestedTenantId) {
        return res.status(403).json({
          error: 'Forbidden',
          message: 'Accesso negato a questo tenant'
        });
      }

      next();
    };
  }

  /**
   * Ottieni utente per ID
   */
  private async getUserById(userId: string): Promise<AuthUser | null> {
    try {
      const userRecord = await this.db.getOne(`
        SELECT 
          id, email, role, tenant_id, permissions,
          api_key, created_at, last_login_at
        FROM auth_users 
        WHERE id = $1 AND active = true
      `, [userId]);

      if (!userRecord) {
        return null;
      }

      return {
        id: userRecord.id,
        email: userRecord.email,
        role: userRecord.role,
        tenant_id: userRecord.tenant_id,
        api_key: userRecord.api_key,
        permissions: typeof userRecord.permissions === 'string' ? JSON.parse(userRecord.permissions) : userRecord.permissions || [],
        created_at: userRecord.created_at,
        last_login_at: userRecord.last_login_at
      };

    } catch (error) {
      console.error('Get user by ID error:', error);
      return null;
    }
  }
}

/**
 * Istanza singleton del servizio auth
 */
let authServiceInstance: JwtAuthService | null = null;

/**
 * Ottieni istanza singleton del servizio auth
 */
export function getAuthService(config?: Partial<AuthConfig>): JwtAuthService {
  if (!authServiceInstance) {
    authServiceInstance = new JwtAuthService(config);
  }
  return authServiceInstance;
}