/**
 * LDAP Authentication Service
 * 
 * Battle-tested LDAP integration using ldapts library
 * Supports Active Directory, OpenLDAP, Azure AD
 */

import { Client } from 'ldapts';
import { authenticate } from 'ldap-authentication';
import { dbPool } from '../db/connection.js';

export class LDAPService {
  constructor() {
    this.db = dbPool;
  }

  /**
   * Get active LDAP configuration
   */
  async getLDAPConfig() {
    try {
      const result = await this.db`
        SELECT * FROM pilotpros.ldap_config 
        WHERE enabled = true 
        ORDER BY created_at DESC 
        LIMIT 1
      `;
      const config = result[0];
      
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
  async authenticateUser(email, password) {
    try {
      const config = await this.getLDAPConfig();
      if (!config) {
        throw new Error('LDAP not configured');
      }

      // LDAP authentication options
      const options = {
        ldapOpts: {
          url: config.server_url,
          tlsOptions: {
            rejectUnauthorized: false, // For self-signed certs in dev
          },
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
      const ldapUser = {
        dn: user.dn,
        email: user.mail || email,
        fullName: user.displayName || user.cn || email,
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
  async testConnection(config) {
    try {
      const client = new Client({
        url: config.server_url,
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
  async searchUsers(searchTerm, config) {
    try {
      const ldapConfig = config || await this.getLDAPConfig();
      if (!ldapConfig) {
        throw new Error('LDAP not configured');
      }

      const client = new Client({
        url: ldapConfig.server_url,
        timeout: 5000,
      });

      await client.bind(ldapConfig.bind_dn || '', ldapConfig.bind_password || '');

      // Search filter for users matching search term
      const filter = `(&(objectClass=person)(|(mail=*${searchTerm}*)(cn=*${searchTerm}*)))`;
      
      const searchResult = await client.search(ldapConfig.user_search_base, {
        scope: 'sub',
        filter: filter,
        attributes: ['dn', 'mail', 'displayName', 'cn', 'sAMAccountName'],
      });

      await client.unbind();

      // Parse search results
      const users = searchResult.searchEntries.map((entry) => ({
        dn: entry.dn,
        email: entry.mail,
        fullName: entry.displayName || entry.cn,
        groups: this.parseGroups(entry.memberOf),
        attributes: entry,
      }));

      console.log(`✅ LDAP search found ${users.length} users for term:`, searchTerm);
      return users;

    } catch (error) {
      console.error('❌ LDAP search failed:', error);
      return [];
    }
  }

  /**
   * Sync LDAP user to local database
   */
  async syncUserToDatabase(ldapUser) {
    try {
      // Check if user already exists
      const existingUsers = await this.db`
        SELECT id FROM pilotpros.users 
        WHERE email = ${ldapUser.email} OR ldap_dn = ${ldapUser.dn}
      `;
      const existingUser = existingUsers[0];

      let userId;
      if (existingUser) {
        // Update existing user
        await this.db`
          UPDATE pilotpros.users SET
            full_name = ${ldapUser.fullName},
            ldap_dn = ${ldapUser.dn},
            auth_method = 'ldap',
            last_ldap_sync = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
          WHERE id = ${existingUser.id}
        `;
        
        userId = existingUser.id;
        console.log('✅ Updated existing LDAP user:', ldapUser.email);
      } else {
        // Create new user
        const newUserResult = await this.db`
          INSERT INTO pilotpros.users (
            email, full_name, ldap_dn, auth_method, 
            password_hash, role, last_ldap_sync
          ) VALUES (${ldapUser.email}, ${ldapUser.fullName}, ${ldapUser.dn}, 'ldap', '', 'user', CURRENT_TIMESTAMP)
          RETURNING id
        `;
        const newUser = newUserResult[0];
        
        userId = newUser.id;
        console.log('✅ Created new LDAP user:', ldapUser.email);
      }

      // Update/create user auth method
      await this.db`
        INSERT INTO pilotpros.user_auth_methods (user_id, method, ldap_dn, enabled)
        VALUES (${userId}, 'ldap', ${ldapUser.dn}, true)
        ON CONFLICT (user_id, method) 
        DO UPDATE SET ldap_dn = ${ldapUser.dn}, enabled = true
      `;

      return userId;
    } catch (error) {
      console.error('❌ Failed to sync LDAP user to database:', error);
      throw error;
    }
  }

  /**
   * Parse LDAP groups from memberOf attribute
   */
  parseGroups(memberOf) {
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
  async saveLDAPConfig(config) {
    try {
      const resultArray = await this.db`
        INSERT INTO pilotpros.ldap_config (
          name, server_url, bind_dn, bind_password,
          user_search_base, user_filter, group_search_base,
          group_filter, enabled, ssl_enabled
        ) VALUES (${config.name}, ${config.server_url}, ${config.bind_dn}, ${config.bind_password},
          ${config.user_search_base}, ${config.user_filter || '(objectClass=person)'}, ${config.group_search_base},
          ${config.group_filter || '(objectClass=group)'}, ${config.enabled !== false}, ${config.ssl_enabled || false})
        RETURNING id
      `;
      const result = resultArray[0];

      console.log('✅ LDAP configuration saved with ID:', result.id);
      return result.id;
    } catch (error) {
      console.error('❌ Failed to save LDAP config:', error);
      throw error;
    }
  }
}

// Singleton pattern
let ldapServiceInstance = null;

export function getLDAPService() {
  if (!ldapServiceInstance) {
    ldapServiceInstance = new LDAPService();
  }
  return ldapServiceInstance;
}