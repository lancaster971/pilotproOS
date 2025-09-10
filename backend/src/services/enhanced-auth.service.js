/**
 * Enhanced Authentication Service
 * 
 * Integrates existing JWT auth with LDAP + MFA capabilities
 * Extends JwtAuthService with enterprise authentication features
 */

import { JwtAuthService } from '../auth/jwt-auth.js';
import { getLDAPService } from './ldap.service.js';
import { getMFAService } from './mfa.service.js';
import { dbPool } from '../db/connection.js';

export class EnhancedAuthService extends JwtAuthService {
  constructor() {
    super();
    this.ldapService = getLDAPService();
    this.mfaService = getMFAService();
    this.db = dbPool;
  }

  /**
   * Enhanced login with LDAP + MFA support
   */
  async enhancedLogin(email, password, options = {}) {
    try {
      const { method = 'auto', skipMFA = false } = options;
      let authResult = null;

      if (method === 'ldap' || (method === 'auto' && await this.shouldUseLDAP(email))) {
        authResult = await this.authenticateWithLDAP(email, password);
      } else {
        authResult = await this.authenticateLocal(email, password);
      }

      // Check MFA requirement
      if (!skipMFA && authResult.user) {
        const mfaRequired = await this.mfaService.isMFAEnabled(authResult.user.id);
        
        if (mfaRequired) {
          // Create MFA session
          const mfaSession = await this.createMFASession(authResult.user.id);
          
          return {
            user: authResult.user,
            requiresMFA: true,
            mfaSession: mfaSession,
            // Don't return full JWT token until MFA is verified
          };
        }
      }

      // Generate full JWT token
      if (authResult.user) {
        authResult.token = this.generateToken(authResult.user);
      }

      return authResult;
    } catch (error) {
      console.error('❌ Enhanced authentication failed:', error);
      throw error;
    }
  }

  /**
   * Authenticate with LDAP
   */
  async authenticateWithLDAP(email, password) {
    try {
      // Authenticate with LDAP server
      const ldapUser = await this.ldapService.authenticateUser(email, password);
      
      if (!ldapUser) {
        throw new Error('LDAP authentication failed');
      }

      // Sync LDAP user to local database
      const userId = await this.ldapService.syncUserToDatabase(ldapUser);
      
      // Get user from database
      const user = await this.getUserById(userId);
      if (!user) {
        throw new Error('Failed to create/update user record');
      }

      console.log('✅ LDAP authentication successful for:', email);
      return { user };

    } catch (error) {
      console.error('❌ LDAP authentication failed:', error);
      throw error;
    }
  }

  /**
   * Authenticate with local credentials
   */
  async authenticateLocal(email, password) {
    try {
      // Get user from database
      const userRecord = await this.db`
        SELECT id, email, password_hash, role, is_active, 
               created_at, last_login, preferences
        FROM pilotpros.users 
        WHERE email = ${email} AND is_active = true
        LIMIT 1
      `;

      if (userRecord.length === 0) {
        throw new Error('Credenziali non valide');
      }

      const user = userRecord[0];

      // Verify password
      const isPasswordValid = await this.verifyPassword(password, user.password_hash);
      if (!isPasswordValid) {
        throw new Error('Credenziali non valide');
      }

      // Update last login
      await this.db`
        UPDATE pilotpros.users 
        SET last_login = NOW() 
        WHERE id = ${user.id}
      `;

      return {
        user: {
          id: user.id,
          email: user.email,
          role: user.role,
          permissions: this.getDefaultPermissions(user.role),
          created_at: user.created_at,
          last_login_at: user.last_login,
          preferences: user.preferences || {}
        }
      };
    } catch (error) {
      console.error('❌ Local authentication failed:', error);
      throw error;
    }
  }

  /**
   * Verify MFA and complete authentication
   */
  async verifyMFAAndCompleteAuth(mfaSession, mfaToken) {
    try {
      // Get MFA session
      const session = await this.getMFASession(mfaSession);
      if (!session || session.expires_at < new Date()) {
        throw new Error('Invalid or expired MFA session');
      }

      // Verify MFA token
      const mfaValid = await this.mfaService.verifyAuthToken(session.user_id, mfaToken);
      if (!mfaValid) {
        throw new Error('Invalid MFA token');
      }

      // Mark MFA session as used
      await this.verifyMFASession(mfaSession);

      // Get user and generate full JWT token
      const user = await this.getUserById(session.user_id);
      if (!user) {
        throw new Error('User not found');
      }

      const token = this.generateToken(user);

      console.log('✅ MFA verification successful for user:', user.email);
      
      return { user, token };
    } catch (error) {
      console.error('❌ MFA verification failed:', error);
      throw error;
    }
  }

  /**
   * Setup MFA for user
   */
  async setupMFA(userId) {
    try {
      const user = await this.getUserById(userId);
      if (!user) {
        throw new Error('User not found');
      }

      return await this.mfaService.setupMFA(userId, user.email);
    } catch (error) {
      console.error('❌ MFA setup failed:', error);
      throw error;
    }
  }

  /**
   * Verify MFA setup token
   */
  async verifyMFASetup(userId, token) {
    try {
      return await this.mfaService.verifySetupToken(userId, token);
    } catch (error) {
      console.error('❌ MFA setup verification failed:', error);
      return false;
    }
  }

  /**
   * Disable MFA for user
   */
  async disableMFA(userId) {
    try {
      await this.mfaService.disableMFA(userId);
      console.log('✅ MFA disabled for user:', userId);
    } catch (error) {
      console.error('❌ Failed to disable MFA:', error);
      throw error;
    }
  }

  /**
   * Check if email should use LDAP authentication
   */
  async shouldUseLDAP(email) {
    try {
      // Check if user exists with LDAP auth method
      const result = await this.db`
        SELECT auth_method FROM pilotpros.users WHERE email = ${email}
      `;
      const user = result[0];

      if (user && user.auth_method === 'ldap') {
        return true;
      }

      // Check LDAP configuration
      const ldapConfig = await this.ldapService.getLDAPConfig();
      return ldapConfig?.enabled || false;
    } catch (error) {
      console.error('❌ Failed to determine auth method:', error);
      return false;
    }
  }

  /**
   * Create MFA session
   */
  async createMFASession(userId) {
    try {
      const sessionToken = this.generateApiKey(); // Reuse API key generation
      const expiresAt = new Date(Date.now() + 10 * 60 * 1000); // 10 minutes

      await this.db`
        INSERT INTO pilotpros.mfa_sessions (user_id, session_token, expires_at)
        VALUES (${userId}, ${sessionToken}, ${expiresAt})
      `;

      return sessionToken;
    } catch (error) {
      console.error('❌ Failed to create MFA session:', error);
      throw error;
    }
  }

  /**
   * Get MFA session
   */
  async getMFASession(sessionToken) {
    try {
      const result = await this.db`
        SELECT * FROM pilotpros.mfa_sessions 
        WHERE session_token = ${sessionToken} AND mfa_verified = false
      `;
      return result[0];
    } catch (error) {
      console.error('❌ Failed to get MFA session:', error);
      return null;
    }
  }

  /**
   * Mark MFA session as verified
   */
  async verifyMFASession(sessionToken) {
    try {
      await this.db`
        UPDATE pilotpros.mfa_sessions 
        SET mfa_verified = true 
        WHERE session_token = ${sessionToken}
      `;
    } catch (error) {
      console.error('❌ Failed to verify MFA session:', error);
      throw error;
    }
  }

  /**
   * Get user by ID (override to handle UUID)
   */
  async getUserById(userId) {
    try {
      const result = await this.db`
        SELECT 
          id, email, role, full_name,
          auth_method, ldap_dn, mfa_enabled,
          created_at, last_login, preferences
        FROM pilotpros.users 
        WHERE id = ${userId} AND is_active = true
      `;
      const userRecord = result[0];

      if (!userRecord) {
        return null;
      }

      // Map to AuthUser interface
      return {
        id: userRecord.id,
        email: userRecord.email,
        role: userRecord.role,
        tenant_id: null, // Single tenant mode
        permissions: [], // Add permissions if needed
        created_at: userRecord.created_at,
        last_login_at: userRecord.last_login
      };
    } catch (error) {
      console.error('❌ Failed to get user by ID:', error);
      return null;
    }
  }

  /**
   * Get authentication status for user
   */
  async getAuthStatus(userId) {
    try {
      const result = await this.db`
        SELECT auth_method, mfa_enabled FROM pilotpros.users WHERE id = ${userId}
      `;
      const user = result[0];

      const ldapConfig = await this.ldapService.getLDAPConfig();

      return {
        ldapEnabled: ldapConfig?.enabled || false,
        mfaEnabled: user?.mfa_enabled || false,
        authMethod: user?.auth_method || 'local',
      };
    } catch (error) {
      console.error('❌ Failed to get auth status:', error);
      return {
        ldapEnabled: false,
        mfaEnabled: false,
        authMethod: 'local',
      };
    }
  }
}

// Singleton pattern
let enhancedAuthServiceInstance = null;

export function getEnhancedAuthService() {
  if (!enhancedAuthServiceInstance) {
    enhancedAuthServiceInstance = new EnhancedAuthService();
  }
  return enhancedAuthServiceInstance;
}