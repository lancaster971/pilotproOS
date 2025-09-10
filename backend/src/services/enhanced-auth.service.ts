/**
 * Enhanced Authentication Service
 * 
 * Integrates existing JWT auth with LDAP + MFA capabilities
 * Extends JwtAuthService with enterprise authentication features
 */

import { JwtAuthService, AuthUser } from '../auth/jwt-auth.js';
import { getLDAPService, LDAPUser } from './ldap.service.js';
import { getMFAService, MFASetupResult } from './mfa.service.js';
import { DatabaseService } from './database.js';

export interface EnhancedAuthResult {
  user: AuthUser;
  token?: string;
  requiresMFA?: boolean;
  mfaSession?: string;
}

export interface LoginOptions {
  method?: 'local' | 'ldap' | 'auto';
  skipMFA?: boolean;
}

export class EnhancedAuthService extends JwtAuthService {
  private ldapService = getLDAPService();
  private mfaService = getMFAService();
  private dbService = DatabaseService.getInstance();

  /**
   * Enhanced login with LDAP + MFA support
   */
  async enhancedLogin(
    email: string, 
    password: string, 
    options: LoginOptions = {}
  ): Promise<EnhancedAuthResult> {
    try {
      const { method = 'auto', skipMFA = false } = options;
      let authResult: EnhancedAuthResult;

      // Determine authentication method
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
            mfaSession,
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
  private async authenticateWithLDAP(email: string, password: string): Promise<EnhancedAuthResult> {
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
  private async authenticateLocal(email: string, password: string): Promise<EnhancedAuthResult> {
    try {
      const { user } = await this.login(email, password);
      return { user };
    } catch (error) {
      console.error('❌ Local authentication failed:', error);
      throw error;
    }
  }

  /**
   * Verify MFA and complete authentication
   */
  async verifyMFAAndCompleteAuth(mfaSession: string, mfaToken: string): Promise<EnhancedAuthResult> {
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

      // Mark MFA session as verified
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
  async setupMFA(userId: string): Promise<MFASetupResult> {
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
  async verifyMFASetup(userId: string, token: string): Promise<boolean> {
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
  async disableMFA(userId: string): Promise<void> {
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
  private async shouldUseLDAP(email: string): Promise<boolean> {
    try {
      // Check if user exists with LDAP auth method
      const user = await this.dbService.getOne(`
        SELECT auth_method FROM pilotpros.users WHERE email = $1
      `, [email]);

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
  private async createMFASession(userId: string): Promise<string> {
    try {
      const sessionToken = this.generateApiKey(); // Reuse API key generation
      const expiresAt = new Date(Date.now() + 10 * 60 * 1000); // 10 minutes

      await this.dbService.query(`
        INSERT INTO pilotpros.mfa_sessions (user_id, session_token, expires_at)
        VALUES ($1, $2, $3)
      `, [userId, sessionToken, expiresAt]);

      return sessionToken;
    } catch (error) {
      console.error('❌ Failed to create MFA session:', error);
      throw error;
    }
  }

  /**
   * Get MFA session
   */
  private async getMFASession(sessionToken: string): Promise<any> {
    try {
      return await this.dbService.getOne(`
        SELECT * FROM pilotpros.mfa_sessions 
        WHERE session_token = $1 AND mfa_verified = false
      `, [sessionToken]);
    } catch (error) {
      console.error('❌ Failed to get MFA session:', error);
      return null;
    }
  }

  /**
   * Mark MFA session as verified
   */
  private async verifyMFASession(sessionToken: string): Promise<void> {
    try {
      await this.dbService.query(`
        UPDATE pilotpros.mfa_sessions 
        SET mfa_verified = true 
        WHERE session_token = $1
      `, [sessionToken]);
    } catch (error) {
      console.error('❌ Failed to verify MFA session:', error);
      throw error;
    }
  }

  /**
   * Get user by ID (override to handle UUID)
   */
  private async getUserById(userId: string): Promise<AuthUser | null> {
    try {
      const userRecord = await this.dbService.getOne(`
        SELECT 
          id, email, role, full_name,
          auth_method, ldap_dn, mfa_enabled,
          created_at, last_login, preferences
        FROM pilotpros.users 
        WHERE id = $1 AND is_active = true
      `, [userId]);

      if (!userRecord) {
        return null;
      }

      // Map to AuthUser interface
      return {
        id: userRecord.id,
        email: userRecord.email,
        role: userRecord.role || 'user',
        tenant_id: 'pilotpros', // Single tenant mode
        permissions: this.getDefaultPermissions(userRecord.role || 'user'),
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
  async getAuthStatus(userId: string): Promise<{
    ldapEnabled: boolean;
    mfaEnabled: boolean;
    authMethod: string;
  }> {
    try {
      const user = await this.dbService.getOne(`
        SELECT auth_method, mfa_enabled FROM pilotpros.users WHERE id = $1
      `, [userId]);

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
let enhancedAuthServiceInstance: EnhancedAuthService | null = null;

export function getEnhancedAuthService(): EnhancedAuthService {
  if (!enhancedAuthServiceInstance) {
    enhancedAuthServiceInstance = new EnhancedAuthService();
  }
  return enhancedAuthServiceInstance;
}