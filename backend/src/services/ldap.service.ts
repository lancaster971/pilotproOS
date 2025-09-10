/**
 * LDAP Authentication Service
 * 
 * Battle-tested LDAP integration using ldapts library
 * Supports Active Directory, OpenLDAP, Azure AD
 */

import { Client } from 'ldapts';
import { authenticate } from 'ldap-authentication';
import { DatabaseService } from './database.js';

export interface LDAPConfig {
  id: number;
  name: string;
  server_url: string;
  bind_dn?: string;
  bind_password?: string;
  user_search_base: string;
  user_filter: string;
  group_search_base?: string;
  group_filter?: string;
  enabled: boolean;
  ssl_enabled: boolean;
}

export interface LDAPUser {
  dn: string;
  email: string;
  fullName?: string;
  groups?: string[];
  attributes: Record<string, any>;
}

export class LDAPService {
  private dbService: DatabaseService;

  constructor() {
    this.dbService = DatabaseService.getInstance();
  }

  /**
   * Get active LDAP configuration
   */
  async getLDAPConfig(): Promise<LDAPConfig | null> {
    try {
      const config = await this.dbService.getOne(`
        SELECT * FROM pilotpros.ldap_config 
        WHERE enabled = true 
        ORDER BY created_at DESC 
        LIMIT 1
      `);
      
      return config || null;
    } catch (error) {
      console.error('Failed to get LDAP config:', error);
      return null;
    }
  }

  /**
   * Authenticate user with LDAP
   * Uses ldap-authentication for simple authentication
   */
  async authenticateUser(email: string, password: string): Promise<LDAPUser | null> {
    try {
      const config = await this.getLDAPConfig();
      if (!config) {
        throw new Error('LDAP not configured');
      }

      // LDAP authentication options
      const options = {
        ldapOpts: {
          url: config.server_url,
          tlsOptions: config.ssl_enabled ? {
            rejectUnauthorized: false, // For self-signed certs in dev
          } : undefined,
        },
        adminDn: config.bind_dn,
        adminPassword: config.bind_password,
        userPassword: password,
        userSearchBase: config.user_search_base,
        usernameAttribute: 'mail', // Search by email
        username: email,
        // Attributes to retrieve
        attributes: ['dn', 'mail', 'displayName', 'cn', 'sAMAccountName', 'memberOf'],
      };

      // Perform authentication
      const user = await authenticate(options);
      
      if (!user) {
        return null;
      }

      // Parse LDAP user response
      const ldapUser: LDAPUser = {
        dn: user.dn,
        email: user.mail || email,
        fullName: user.displayName || user.cn,
        groups: this.parseGroups(user.memberOf),
        attributes: user,
      };

      console.log('✅ LDAP authentication successful:', ldapUser.email);
      return ldapUser;

    } catch (error) {
      console.error('❌ LDAP authentication failed:', error);
      return null;
    }
  }

  /**
   * Test LDAP connection
   */
  async testConnection(config: Partial<LDAPConfig>): Promise<boolean> {
    try {
      const client = new Client({
        url: config.server_url!,
        timeout: 5000,
        connectTimeout: 5000,
      });

      await client.bind(config.bind_dn || '', config.bind_password || '');
      await client.unbind();
      
      console.log('✅ LDAP connection test successful');
      return true;
    } catch (error) {
      console.error('❌ LDAP connection test failed:', error);
      return false;
    }
  }

  /**
   * Search for users in LDAP
   */
  async searchUsers(searchTerm: string, config?: LDAPConfig): Promise<LDAPUser[]> {
    try {
      const ldapConfig = config || await this.getLDAPConfig();
      if (!ldapConfig) {
        throw new Error('LDAP not configured');
      }

      const client = new Client({
        url: ldapConfig.server_url,
        timeout: 10000,
      });

      await client.bind(ldapConfig.bind_dn || '', ldapConfig.bind_password || '');

      // Search filter for users matching search term
      const filter = `(&(objectClass=person)(|(mail=*${searchTerm}*)(cn=*${searchTerm}*)))`;
      
      const searchResult = await client.search(ldapConfig.user_search_base, {
        scope: 'sub',
        filter,
        attributes: ['dn', 'mail', 'displayName', 'cn', 'sAMAccountName'],
      });

      await client.unbind();

      // Parse search results
      const users: LDAPUser[] = searchResult.searchEntries.map((entry: any) => ({
        dn: entry.dn,
        email: entry.mail,
        fullName: entry.displayName || entry.cn,
        groups: [],
        attributes: entry,
      }));

      console.log(`✅ LDAP search found ${users.length} users for term: ${searchTerm}`);
      return users;

    } catch (error) {
      console.error('❌ LDAP search failed:', error);
      return [];
    }
  }

  /**
   * Sync LDAP user to local database
   */
  async syncUserToDatabase(ldapUser: LDAPUser): Promise<string> {
    try {
      // Check if user already exists
      const existingUser = await this.dbService.getOne(`
        SELECT id FROM pilotpros.users 
        WHERE email = $1 OR ldap_dn = $2
      `, [ldapUser.email, ldapUser.dn]);

      let userId: string;

      if (existingUser) {
        // Update existing user
        await this.dbService.query(`
          UPDATE pilotpros.users SET
            full_name = $1,
            ldap_dn = $2,
            auth_method = 'ldap',
            last_ldap_sync = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
          WHERE id = $3
        `, [ldapUser.fullName, ldapUser.dn, existingUser.id]);
        
        userId = existingUser.id;
        console.log('✅ Updated existing LDAP user:', ldapUser.email);
      } else {
        // Create new user
        const newUser = await this.dbService.getOne(`
          INSERT INTO pilotpros.users (
            email, full_name, ldap_dn, auth_method, 
            password_hash, role, last_ldap_sync
          ) VALUES ($1, $2, $3, 'ldap', '', 'user', CURRENT_TIMESTAMP)
          RETURNING id
        `, [ldapUser.email, ldapUser.fullName, ldapUser.dn]);
        
        userId = newUser.id;
        console.log('✅ Created new LDAP user:', ldapUser.email);
      }

      // Update/create user auth method
      await this.dbService.query(`
        INSERT INTO pilotpros.user_auth_methods (user_id, method, ldap_dn, enabled)
        VALUES ($1, 'ldap', $2, true)
        ON CONFLICT (user_id, method) 
        DO UPDATE SET ldap_dn = $2, enabled = true
      `, [userId, ldapUser.dn]);

      return userId;
    } catch (error) {
      console.error('❌ Failed to sync LDAP user to database:', error);
      throw error;
    }
  }

  /**
   * Parse LDAP groups from memberOf attribute
   */
  private parseGroups(memberOf: string | string[]): string[] {
    if (!memberOf) return [];
    
    const groups = Array.isArray(memberOf) ? memberOf : [memberOf];
    
    // Extract CN from DN format: CN=GroupName,OU=...
    return groups.map(dn => {
      const match = dn.match(/^CN=([^,]+)/i);
      return match ? match[1] : dn;
    });
  }

  /**
   * Save/Update LDAP configuration
   */
  async saveLDAPConfig(config: Omit<LDAPConfig, 'id' | 'created_at' | 'updated_at'>): Promise<number> {
    try {
      const result = await this.dbService.getOne(`
        INSERT INTO pilotpros.ldap_config (
          name, server_url, bind_dn, bind_password,
          user_search_base, user_filter, group_search_base,
          group_filter, enabled, ssl_enabled
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING id
      `, [
        config.name,
        config.server_url,
        config.bind_dn,
        config.bind_password,
        config.user_search_base,
        config.user_filter,
        config.group_search_base,
        config.group_filter,
        config.enabled,
        config.ssl_enabled
      ]);

      console.log('✅ LDAP configuration saved with ID:', result.id);
      return result.id;
    } catch (error) {
      console.error('❌ Failed to save LDAP config:', error);
      throw error;
    }
  }
}

// Singleton pattern
let ldapServiceInstance: LDAPService | null = null;

export function getLDAPService(): LDAPService {
  if (!ldapServiceInstance) {
    ldapServiceInstance = new LDAPService();
  }
  return ldapServiceInstance;
}