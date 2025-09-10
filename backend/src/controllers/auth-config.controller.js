import { dbPool } from '../db/connection.js';

class AuthConfigController {
  constructor() {
    this.db = dbPool;
  }

  // Get current authentication configuration
  getAuthConfig = async (req, res) => {
    try {
      // Check if user is admin
      if (req.user?.role !== 'admin') {
        return res.status(403).json({
          success: false,
          message: 'Accesso negato: permessi amministratore richiesti'
        });
      }

      const result = await dbPool`
        SELECT * FROM pilotpros.auth_config 
        WHERE id = 1
      `;

      if (result.length === 0) {
        // Return default configuration
        return res.json({
          success: true,
          config: {
            method: 'local',
            ldap: null,
            mfa: null
          }
        });
      }

      const config = result[0];
      
      res.json({
        success: true,
        config: {
          method: config.auth_method,
          ldap: config.ldap_config,
          mfa: config.mfa_config
        }
      });

    } catch (error) {
      console.error('Error getting auth config:', error);
      res.status(500).json({
        success: false,
        message: 'Errore nel recupero della configurazione'
      });
    }
  };

  // Save authentication configuration
  saveAuthConfig = async (req, res) => {
    try {
      // Check if user is admin
      if (req.user?.role !== 'admin') {
        return res.status(403).json({
          success: false,
          message: 'Accesso negato: permessi amministratore richiesti'
        });
      }

      const { method, ldap, mfa } = req.body;

      // Validate method
      if (!['local', 'ldap', 'ldap_mfa'].includes(method)) {
        return res.status(400).json({
          success: false,
          message: 'Metodo di autenticazione non valido'
        });
      }

      // Validate LDAP config if needed
      if (method !== 'local' && (!ldap || !ldap.server || !ldap.baseDN)) {
        return res.status(400).json({
          success: false,
          message: 'Configurazione LDAP incompleta'
        });
      }

      // Check if configuration exists
      const existing = await dbPool`
        SELECT id FROM pilotpros.auth_config WHERE id = 1
      `;

      if (existing.length > 0) {
        // Update existing configuration
        await dbPool`
          UPDATE pilotpros.auth_config 
          SET 
            auth_method = ${method},
            ldap_config = ${method !== 'local' ? JSON.stringify(ldap) : null},
            mfa_config = ${method === 'ldap_mfa' ? JSON.stringify(mfa) : null},
            updated_at = NOW()
          WHERE id = 1
        `;
      } else {
        // Insert new configuration
        await dbPool`
          INSERT INTO pilotpros.auth_config (id, auth_method, ldap_config, mfa_config, created_at, updated_at)
          VALUES (1, ${method}, ${method !== 'local' ? JSON.stringify(ldap) : null}, ${method === 'ldap_mfa' ? JSON.stringify(mfa) : null}, NOW(), NOW())
        `;
      }

      res.json({
        success: true,
        message: 'Configurazione salvata con successo'
      });

    } catch (error) {
      console.error('Error saving auth config:', error);
      res.status(500).json({
        success: false,
        message: 'Errore nel salvataggio della configurazione'
      });
    }
  };

  // Test authentication configuration
  testAuthConfig = async (req, res) => {
    try {
      // Check if user is admin
      if (req.user?.role !== 'admin') {
        return res.status(403).json({
          success: false,
          message: 'Accesso negato: permessi amministratore richiesti'
        });
      }

      const { method, ldap, mfa } = req.body;

      if (method === 'local') {
        return res.json({
          success: true,
          message: 'Autenticazione locale sempre disponibile'
        });
      }

      if (method === 'ldap' || method === 'ldap_mfa') {
        const testResult = await this.testLdapConnection(ldap);
        
        if (!testResult.success) {
          return res.json({
            success: false,
            message: testResult.message
          });
        }

        // If LDAP+MFA, also validate MFA config
        if (method === 'ldap_mfa') {
          const mfaValid = this.validateMfaConfig(mfa);
          if (!mfaValid.success) {
            return res.json({
              success: false,
              message: mfaValid.message
            });
          }
        }
      }

      res.json({
        success: true,
        message: 'Test configurazione completato con successo'
      });

    } catch (error) {
      console.error('Error testing auth config:', error);
      res.status(500).json({
        success: false,
        message: 'Errore durante il test della configurazione'
      });
    }
  };

  // Test LDAP connection
  async testLdapConnection(ldapConfig) {
    try {
      const LdapAuth = require('ldapauth-fork');
      
      return new Promise((resolve) => {
        const auth = new LdapAuth({
          url: `${ldapConfig.useSSL ? 'ldaps' : 'ldap'}://${ldapConfig.server}:${ldapConfig.port}`,
          bindDN: ldapConfig.userDN,
          bindCredentials: ldapConfig.password,
          searchBase: ldapConfig.baseDN,
          searchFilter: '(uid={{username}})',
          reconnect: false,
          timeout: 5000,
          connectTimeout: 5000,
          tlsOptions: {
            rejectUnauthorized: false
          }
        });

        // Test connection by trying to authenticate with admin credentials
        auth.authenticate(ldapConfig.userDN, ldapConfig.password, (err, user) => {
          auth.close(); // Always close connection
          
          if (err) {
            resolve({
              success: false,
              message: `Errore test LDAP: ${err.message}`
            });
          } else {
            resolve({
              success: true,
              message: 'Test connessione LDAP completato con successo'
            });
          }
        });
      });

    } catch (error) {
      return {
        success: false,
        message: `Errore configurazione LDAP: ${error.message}`
      };
    }
  }

  // Validate MFA configuration
  validateMfaConfig(mfaConfig) {
    if (!mfaConfig || !mfaConfig.method) {
      return {
        success: false,
        message: 'Metodo MFA non specificato'
      };
    }

    const validMethods = ['totp', 'sms', 'email'];
    if (!validMethods.includes(mfaConfig.method)) {
      return {
        success: false,
        message: 'Metodo MFA non valido'
      };
    }

    if (!mfaConfig.timeout || mfaConfig.timeout < 60 || mfaConfig.timeout > 600) {
      return {
        success: false,
        message: 'Timeout MFA deve essere tra 60 e 600 secondi'
      };
    }

    return {
      success: true,
      message: 'Configurazione MFA valida'
    };
  }
}

export default new AuthConfigController();