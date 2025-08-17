/**
 * Authentication Controller
 * 
 * Endpoints REST per gestione autenticazione e utenti
 */

import express, { Request, Response } from 'express';
import { getAuthService, AuthUser } from '../auth/jwt-auth.js';
import { DatabaseConnection } from '../database/connection.js';
import { resolveTenantId, validateTenantId, getTenantConfig } from '../config/tenant-config.js';

const router = express.Router();
const authService = getAuthService();
const db = DatabaseConnection.getInstance();

/**
 * @swagger
 * /auth/login:
 *   post:
 *     summary: Login utente
 *     description: Autentica un utente con email e password, restituisce JWT token
 *     tags: [Authentication]
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
 *                 example: admin@n8n-mcp.local
 *               password:
 *                 type: string
 *                 format: password
 *                 example: admin123
 *     responses:
 *       200:
 *         description: Login successful
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 user:
 *                   $ref: '#/components/schemas/User'
 *                 token:
 *                   type: string
 *                 expiresIn:
 *                   type: string
 *       401:
 *         description: Invalid credentials
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.post('/login', async (req: Request, res: Response) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'Email e password richiesti'
      });
    }

    const { user, token } = await authService.login(email, password);

    // Log audit
    await logAuditAction({
      userId: user.id,
      action: 'login',
      success: true,
      ip: req.ip,
      userAgent: req.get('User-Agent')
    });

    res.json({
      message: 'Login successful',
      user: {
        id: user.id,
        email: user.email,
        role: user.role,
        tenantId: user.tenant_id,
        permissions: user.permissions
      },
      token,
      expiresIn: '24h'
    });

  } catch (error) {
    // Log audit fallimento
    await logAuditAction({
      action: 'login',
      success: false,
      errorMessage: error instanceof Error ? error.message : 'Unknown error',
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      details: { email: req.body.email }
    });

    res.status(401).json({
      error: 'Unauthorized',
      message: error instanceof Error ? error.message : 'Login failed'
    });
  }
});

/**
 * @swagger
 * /auth/register:
 *   post:
 *     summary: Registra nuovo utente
 *     description: Crea un nuovo utente nel sistema (solo admin)
 *     tags: [Authentication]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email
 *               - password
 *               - role
 *             properties:
 *               email:
 *                 type: string
 *                 format: email
 *               password:
 *                 type: string
 *                 minLength: 8
 *               role:
 *                 type: string
 *                 enum: [admin, tenant, readonly]
 *               tenantId:
 *                 type: string
 *                 nullable: true
 *               permissions:
 *                 type: array
 *                 items:
 *                   type: string
 *     responses:
 *       201:
 *         description: User created successfully
 *       400:
 *         description: Bad request
 *       401:
 *         description: Unauthorized
 */
router.post('/register', 
  authService.authenticateToken(),
  authService.requirePermission('users:write'),
  async (req: Request & { user?: AuthUser }, res: Response) => {
    try {
      const { email, password, role, tenantId, permissions } = req.body;

      if (!email || !password || !role) {
        return res.status(400).json({
          error: 'Bad Request',
          message: 'Email, password e role richiesti'
        });
      }

      // Risolvi tenant ID utilizzando la configurazione mono/multi-tenant
      const resolvedTenantId = resolveTenantId(tenantId);
      const tenantConfig = getTenantConfig();

      // Valida tenant ID
      if (!validateTenantId(resolvedTenantId)) {
        return res.status(400).json({
          error: 'Bad Request',
          message: tenantConfig.isMultiTenantMode 
            ? 'Invalid tenant ID' 
            : `Invalid tenant ID. System is configured for mono-tenant mode with tenant: ${tenantConfig.defaultTenantId}`
        });
      }

      const user = await authService.createUser({
        email,
        password,
        role,
        tenant_id: resolvedTenantId,
        permissions
      });

      // Log audit
      await logAuditAction({
        userId: req.user!.id,
        action: 'create_user',
        resourceType: 'auth_users',
        resourceId: user.id,
        success: true,
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        details: { 
          targetEmail: email, 
          targetRole: role, 
          targetTenant: resolvedTenantId,
          monoTenantMode: !tenantConfig.isMultiTenantMode
        }
      });

      res.status(201).json({
        message: 'User created successfully',
        user: {
          id: user.id,
          email: user.email,
          role: user.role,
          tenantId: user.tenant_id,
          apiKey: user.api_key,
          permissions: user.permissions
        }
      });

    } catch (error) {
      // Log audit fallimento
      await logAuditAction({
        userId: req.user?.id,
        action: 'create_user',
        success: false,
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        details: req.body
      });

      res.status(400).json({
        error: 'Bad Request',
        message: error instanceof Error ? error.message : 'User creation failed'
      });
    }
  }
);

/**
 * @swagger
 * /auth/profile:
 *   get:
 *     summary: Ottieni profilo utente
 *     description: Restituisce il profilo dell'utente autenticato
 *     tags: [Authentication]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: User profile
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 user:
 *                   $ref: '#/components/schemas/User'
 *       401:
 *         description: Unauthorized
 */
router.get('/profile',
  authService.authenticateToken(),
  async (req: Request & { user?: AuthUser }, res: Response) => {
    try {
      const user = req.user!;

      res.json({
        user: {
          id: user.id,
          email: user.email,
          role: user.role,
          tenantId: user.tenant_id,
          permissions: user.permissions,
          createdAt: user.created_at,
          lastLoginAt: user.last_login_at
        }
      });

    } catch (error) {
      res.status(500).json({
        error: 'Internal Server Error',
        message: 'Failed to get profile'
      });
    }
  }
);

/**
 * @swagger
 * /auth/profile:
 *   put:
 *     summary: Aggiorna profilo utente
 *     description: Modifica password dell'utente autenticato
 *     tags: [Authentication]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - currentPassword
 *               - newPassword
 *             properties:
 *               currentPassword:
 *                 type: string
 *               newPassword:
 *                 type: string
 *                 minLength: 8
 *     responses:
 *       200:
 *         description: Password updated successfully
 *       400:
 *         description: Invalid current password
 *       401:
 *         description: Unauthorized
 */
router.put('/profile',
  authService.authenticateToken(),
  async (req: Request & { user?: AuthUser }, res: Response) => {
    try {
      const { currentPassword, newPassword } = req.body;
      const userId = req.user!.id;

      if (newPassword) {
        if (!currentPassword) {
          return res.status(400).json({
            error: 'Bad Request',
            message: 'Password corrente richiesta per cambio password'
          });
        }

        // Verifica password corrente
        const userRecord = await db.getOne(
          'SELECT password_hash FROM auth_users WHERE id = $1',
          [userId]
        );

        const isValid = await authService.verifyPassword(currentPassword, userRecord.password_hash);
        if (!isValid) {
          return res.status(400).json({
            error: 'Bad Request',
            message: 'Password corrente non valida'
          });
        }

        // Hash nuova password
        const newPasswordHash = await authService.hashPassword(newPassword);

        // Aggiorna password
        await db.query(
          'UPDATE auth_users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2',
          [newPasswordHash, userId]
        );

        // Log audit
        await logAuditAction({
          userId,
          action: 'change_password',
          success: true,
          ip: req.ip,
          userAgent: req.get('User-Agent')
        });

        res.json({
          message: 'Password updated successfully'
        });
      } else {
        res.status(400).json({
          error: 'Bad Request',
          message: 'No updates provided'
        });
      }

    } catch (error) {
      res.status(500).json({
        error: 'Internal Server Error',
        message: error instanceof Error ? error.message : 'Profile update failed'
      });
    }
  }
);

/**
 * @swagger
 * /auth/users:
 *   get:
 *     summary: Lista utenti
 *     description: Restituisce lista di tutti gli utenti (richiede permesso users:read)
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Users list
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 users:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/User'
 *                 total:
 *                   type: integer
 *       401:
 *         description: Unauthorized
 *       403:
 *         description: Forbidden - insufficient permissions
 */
router.get('/users',
  authService.authenticateToken(),
  authService.requirePermission('users:read'),
  async (req: Request, res: Response) => {
    try {
      const users = await db.getMany(`
        SELECT 
          u.id, u.email, u.role, u.tenant_id, u.permissions, u.active,
          u.created_at, u.last_login_at,
          t.name as tenant_name
        FROM auth_users u
        LEFT JOIN tenants t ON u.tenant_id = t.id
        WHERE u.active = true
        ORDER BY u.created_at DESC
      `);

      const usersResponse = users.map(user => ({
        id: user.id,
        email: user.email,
        role: user.role,
        tenantId: user.tenant_id,
        tenantName: user.tenant_name,
        permissions: typeof user.permissions === 'string' ? JSON.parse(user.permissions) : user.permissions || [],
        active: user.active,
        createdAt: user.created_at,
        lastLoginAt: user.last_login_at
      }));

      res.json({
        users: usersResponse,
        total: usersResponse.length
      });

    } catch (error) {
      res.status(500).json({
        error: 'Internal Server Error',
        message: 'Failed to get users'
      });
    }
  }
);

/**
 * @swagger
 * /auth/users/{id}:
 *   delete:
 *     summary: Disabilita utente
 *     description: Disabilita un utente (soft delete, richiede permesso users:delete)
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *           format: uuid
 *         description: User ID to disable
 *     responses:
 *       200:
 *         description: User disabled successfully
 *       400:
 *         description: Cannot delete your own account
 *       401:
 *         description: Unauthorized
 *       403:
 *         description: Forbidden - insufficient permissions
 */
router.delete('/users/:id',
  authService.authenticateToken(),
  authService.requirePermission('users:delete'),
  async (req: Request & { user?: AuthUser }, res: Response) => {
    try {
      const { id } = req.params;

      if (id === req.user!.id) {
        return res.status(400).json({
          error: 'Bad Request',
          message: 'Cannot delete your own account'
        });
      }

      // Disabilita invece di eliminare (soft delete)
      await db.query(
        'UPDATE auth_users SET active = false, updated_at = CURRENT_TIMESTAMP WHERE id = $1',
        [id]
      );

      // Log audit
      await logAuditAction({
        userId: req.user!.id,
        action: 'delete_user',
        resourceType: 'auth_users',
        resourceId: id,
        success: true,
        ip: req.ip,
        userAgent: req.get('User-Agent')
      });

      res.json({
        message: 'User disabled successfully'
      });

    } catch (error) {
      res.status(500).json({
        error: 'Internal Server Error',
        message: 'Failed to delete user'
      });
    }
  }
);

/**
 * @swagger
 * /auth/audit:
 *   get:
 *     summary: Audit logs
 *     description: Restituisce i log di audit del sistema (richiede permesso system:read)
 *     tags: [Monitoring]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           default: 50
 *         description: Number of logs to return
 *       - in: query
 *         name: offset
 *         schema:
 *           type: integer
 *           default: 0
 *         description: Offset for pagination
 *       - in: query
 *         name: userId
 *         schema:
 *           type: string
 *         description: Filter by user ID
 *       - in: query
 *         name: action
 *         schema:
 *           type: string
 *         description: Filter by action type
 *     responses:
 *       200:
 *         description: Audit logs
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 logs:
 *                   type: array
 *                   items:
 *                     type: object
 *                 pagination:
 *                   type: object
 *                   properties:
 *                     limit:
 *                       type: integer
 *                     offset:
 *                       type: integer
 *                     total:
 *                       type: integer
 *       401:
 *         description: Unauthorized
 *       403:
 *         description: Forbidden - insufficient permissions
 */
router.get('/audit',
  authService.authenticateToken(),
  authService.requirePermission('system:read'),
  async (req: Request, res: Response) => {
    try {
      const { limit = 50, offset = 0, userId, action } = req.query;

      let query = `
        SELECT 
          a.*, 
          u.email as user_email
        FROM auth_audit_log a
        LEFT JOIN auth_users u ON a.user_id = u.id
      `;
      const params: any[] = [];

      const conditions: string[] = [];
      if (userId) {
        conditions.push(`a.user_id = $${params.length + 1}`);
        params.push(userId);
      }
      if (action) {
        conditions.push(`a.action = $${params.length + 1}`);
        params.push(action);
      }

      if (conditions.length > 0) {
        query += ` WHERE ${conditions.join(' AND ')}`;
      }

      query += ` ORDER BY a.created_at DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
      params.push(parseInt(limit as string), parseInt(offset as string));

      const auditLogs = await db.getMany(query, params);

      res.json({
        logs: auditLogs,
        pagination: {
          limit: parseInt(limit as string),
          offset: parseInt(offset as string),
          total: auditLogs.length
        }
      });

    } catch (error) {
      res.status(500).json({
        error: 'Internal Server Error',
        message: 'Failed to get audit logs'
      });
    }
  }
);

/**
 * Utility per log audit
 */
async function logAuditAction(data: {
  userId?: string;
  action: string;
  resourceType?: string;
  resourceId?: string;
  success: boolean;
  errorMessage?: string;
  ip?: string;
  userAgent?: string;
  details?: any;
}) {
  try {
    await db.query(`
      INSERT INTO auth_audit_log (
        user_id, action, resource_type, resource_id,
        details, ip_address, user_agent, success, error_message
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    `, [
      data.userId || null,
      data.action,
      data.resourceType || null,
      data.resourceId || null,
      data.details ? JSON.stringify(data.details) : null,
      data.ip || null,
      data.userAgent || null,
      data.success,
      data.errorMessage || null
    ]);
  } catch (error) {
    console.error('Failed to log audit action:', error);
  }
}

export default router;