/**
 * Enhanced Authentication Controller
 * 
 * REST endpoints for LDAP + MFA authentication
 * Extends existing auth endpoints with enterprise features
 */

import express from 'express';
import { getEnhancedAuthService } from '../services/enhanced-auth.service.js';
// import { getLDAPService } from '../services/ldap.service.js'; // Temporarily disabled
import { getMFAService } from '../services/mfa.service.js';
import { getAuthService } from '../auth/jwt-auth.js';

const router = express.Router();
const enhancedAuthService = getEnhancedAuthService();
// const ldapService = getLDAPService(); // Temporarily disabled
const mfaService = getMFAService();
const authService = getAuthService();

/**
 * @swagger
 * /auth/enhanced/login:
 *   post:
 *     summary: Enhanced login with LDAP + MFA support
 *     description: Authenticate user with automatic LDAP detection and MFA verification
 *     tags: [Enhanced Authentication]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email
 *               - password
 *             properties:
 *               email:
 *                 type: string
 *                 format: email
 *               password:
 *                 type: string
 *               method:
 *                 type: string
 *                 enum: [local, ldap, auto]
 *                 default: auto
 *     responses:
 *       200:
 *         description: Authentication successful or MFA required
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                 user:
 *                   type: object
 *                 token:
 *                   type: string
 *                 requiresMFA:
 *                   type: boolean
 *                 mfaSession:
 *                   type: string
 *       401:
 *         description: Authentication failed
 */
router.post('/login', async (req, res) => {
  try {
    const { email, password, method = 'auto' } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        success: false,
        message: 'Email and password required'
      });
    }

    const result = await enhancedAuthService.enhancedLogin(email, password, { method });

    if (result.requiresMFA) {
      // MFA required - don't return full token yet
      return res.json({
        success: true,
        message: 'MFA verification required',
        user: {
          id: result.user.id,
          email: result.user.email,
          role: result.user.role
        },
        requiresMFA: true,
        mfaSession: result.mfaSession
      });
    }

    // Full authentication successful
    res.json({
      success: true,
      message: 'Authentication successful',
      user: {
        id: result.user.id,
        email: result.user.email,
        role: result.user.role,
        tenant_id: result.user.tenant_id
      },
      token: result.token,
      requiresMFA: false
    });

  } catch (error) {
    console.error('❌ Enhanced login failed:', error);
    res.status(401).json({
      success: false,
      message: error instanceof Error ? error.message : 'Authentication failed'
    });
  }
});

/**
 * @swagger
 * /auth/enhanced/mfa/verify:
 *   post:
 *     summary: Verify MFA token and complete authentication
 *     description: Complete authentication flow after MFA token verification
 *     tags: [Enhanced Authentication]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - mfaSession
 *               - mfaToken
 *             properties:
 *               mfaSession:
 *                 type: string
 *               mfaToken:
 *                 type: string
 *     responses:
 *       200:
 *         description: MFA verification successful
 *       401:
 *         description: Invalid MFA token or session
 */
router.post('/mfa/verify', async (req, res) => {
  try {
    const { mfaSession, mfaToken } = req.body;

    if (!mfaSession || !mfaToken) {
      return res.status(400).json({
        success: false,
        message: 'MFA session and token required'
      });
    }

    const result = await enhancedAuthService.verifyMFAAndCompleteAuth(mfaSession, mfaToken);

    res.json({
      success: true,
      message: 'MFA verification successful',
      user: {
        id: result.user.id,
        email: result.user.email,
        role: result.user.role,
        tenant_id: result.user.tenant_id
      },
      token: result.token
    });

  } catch (error) {
    console.error('❌ MFA verification failed:', error);
    res.status(401).json({
      success: false,
      message: error instanceof Error ? error.message : 'MFA verification failed'
    });
  }
});

/**
 * @swagger
 * /auth/enhanced/mfa/setup:
 *   post:
 *     summary: Setup MFA for authenticated user
 *     description: Generate MFA secret and QR code for user setup
 *     tags: [MFA Management]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: MFA setup data generated
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 secret:
 *                   type: string
 *                 qrCodeUrl:
 *                   type: string
 *                 backupCodes:
 *                   type: array
 *                   items:
 *                     type: string
 */
router.post('/mfa/setup',
  authService.authenticateToken(),
  async (req, res) => {
    try {
      const userId = req.user.id;
      const setupResult = await enhancedAuthService.setupMFA(userId);

      res.json({
        success: true,
        message: 'MFA setup prepared',
        ...setupResult
      });

    } catch (error) {
      console.error('❌ MFA setup failed:', error);
      res.status(500).json({
        success: false,
        message: error instanceof Error ? error.message : 'MFA setup failed'
      });
    }
  }
);

/**
 * @swagger
 * /auth/enhanced/mfa/verify-setup:
 *   post:
 *     summary: Verify MFA setup token
 *     description: Verify TOTP token during MFA setup to enable MFA
 *     tags: [MFA Management]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - token
 *             properties:
 *               token:
 *                 type: string
 *     responses:
 *       200:
 *         description: MFA setup verified and enabled
 */
router.post('/mfa/verify-setup',
  authService.authenticateToken(),
  async (req, res) => {
    try {
      const userId = req.user.id;
      const { token } = req.body;

      if (!token) {
        return res.status(400).json({
          success: false,
          message: 'Token required'
        });
      }

      const verified = await enhancedAuthService.verifyMFASetup(userId, token);

      if (verified) {
        res.json({
          success: true,
          message: 'MFA setup verified and enabled'
        });
      } else {
        res.status(400).json({
          success: false,
          message: 'Invalid verification token'
        });
      }

    } catch (error) {
      console.error('❌ MFA setup verification failed:', error);
      res.status(500).json({
        success: false,
        message: 'MFA setup verification failed'
      });
    }
  }
);

/**
 * @swagger
 * /auth/enhanced/mfa/disable:
 *   post:
 *     summary: Disable MFA for user
 *     description: Disable MFA authentication for the authenticated user
 *     tags: [MFA Management]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: MFA disabled successfully
 */
router.post('/mfa/disable',
  authService.authenticateToken(),
  async (req, res) => {
    try {
      const userId = req.user.id;
      await enhancedAuthService.disableMFA(userId);

      res.json({
        success: true,
        message: 'MFA disabled successfully'
      });

    } catch (error) {
      console.error('❌ MFA disable failed:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to disable MFA'
      });
    }
  }
);

/**
 * @swagger
 * /auth/enhanced/status:
 *   get:
 *     summary: Get authentication status
 *     description: Get user's authentication configuration and capabilities
 *     tags: [Authentication Status]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Authentication status
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 ldapEnabled:
 *                   type: boolean
 *                 mfaEnabled:
 *                   type: boolean
 *                 authMethod:
 *                   type: string
 */
router.get('/status',
  authService.authenticateToken(),
  async (req, res) => {
    try {
      const userId = req.user.id;
      const status = await enhancedAuthService.getAuthStatus(userId);

      res.json({
        success: true,
        ...status
      });

    } catch (error) {
      console.error('❌ Failed to get auth status:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get authentication status'
      });
    }
  }
);

/**
 * @swagger
 * /auth/enhanced/ldap/test:
 *   post:
 *     summary: Test LDAP connection
 *     description: Test LDAP server connection with provided configuration
 *     tags: [LDAP Management]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - server_url
 *               - user_search_base
 *             properties:
 *               server_url:
 *                 type: string
 *               bind_dn:
 *                 type: string
 *               bind_password:
 *                 type: string
 *               user_search_base:
 *                 type: string
 *     responses:
 *       200:
 *         description: LDAP connection test result
 */
router.post('/ldap/test',
  authService.authenticateToken(),
  authService.requirePermission('system:admin'),
  async (req, res) => {
    try {
      const ldapConfig = req.body;
      const connectionOk = await ldapService.testConnection(ldapConfig);

      res.json({
        success: connectionOk,
        message: connectionOk ? 'LDAP connection successful' : 'LDAP connection failed'
      });

    } catch (error) {
      console.error('❌ LDAP test failed:', error);
      res.status(500).json({
        success: false,
        message: 'LDAP connection test failed'
      });
    }
  }
);

/**
 * @swagger
 * /auth/enhanced/ldap/config:
 *   post:
 *     summary: Save LDAP configuration
 *     description: Save or update LDAP server configuration
 *     tags: [LDAP Management]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - name
 *               - server_url
 *               - user_search_base
 *             properties:
 *               name:
 *                 type: string
 *               server_url:
 *                 type: string
 *               bind_dn:
 *                 type: string
 *               bind_password:
 *                 type: string
 *               user_search_base:
 *                 type: string
 *               user_filter:
 *                 type: string
 *               enabled:
 *                 type: boolean
 *     responses:
 *       200:
 *         description: LDAP configuration saved
 */
router.post('/ldap/config',
  authService.authenticateToken(),
  authService.requirePermission('system:admin'),
  async (req, res) => {
    try {
      const config = req.body;
      const configId = await ldapService.saveLDAPConfig(config);

      res.json({
        success: true,
        message: 'LDAP configuration saved',
        configId
      });

    } catch (error) {
      console.error('❌ LDAP config save failed:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to save LDAP configuration'
      });
    }
  }
);

/**
 * @swagger
 * /auth/enhanced/backup-codes:
 *   post:
 *     summary: Regenerate backup codes
 *     description: Generate new backup codes for MFA
 *     tags: [MFA Management]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: New backup codes generated
 */
router.post('/backup-codes',
  authService.authenticateToken(),
  async (req, res) => {
    try {
      const userId = req.user.id;
      const backupCodes = await mfaService.regenerateBackupCodes(userId);

      res.json({
        success: true,
        message: 'Backup codes regenerated',
        backupCodes
      });

    } catch (error) {
      console.error('❌ Backup codes regeneration failed:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to regenerate backup codes'
      });
    }
  }
);

export default router;