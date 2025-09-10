/**
 * User Management Controller
 * 
 * Handles CRUD operations for user management in Settings page
 * Admin-only endpoints for creating, updating, deleting users
 */

import { dbPool } from '../db/connection.js';
import bcrypt from 'bcrypt';
import { v4 as uuidv4 } from 'uuid';

// Available roles and their permissions
const ROLES = {
  admin: ['users:read', 'users:write', 'users:delete', 'workflows:read', 'workflows:write', 'workflows:delete', 'system:read', 'system:write'],
  editor: ['users:read', 'workflows:read', 'workflows:write', 'system:read'],
  viewer: ['workflows:read', 'system:read']
};

/**
 * Get all users (admin only)
 */
export const getUsers = async (req, res) => {
  try {
    // Check if user is admin
    if (req.user?.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Accesso negato: permessi amministratore richiesti'
      });
    }

    const users = await dbPool`
      SELECT 
        id, email, role, is_active, 
        created_at, last_login, preferences
      FROM pilotpros.users 
      ORDER BY created_at DESC
    `;

    // Add permissions to each user
    const usersWithPermissions = users.map(user => ({
      ...user,
      permissions: ROLES[user.role] || [],
      last_login_at: user.last_login
    }));

    res.json({
      success: true,
      users: usersWithPermissions,
      total: users.length
    });

  } catch (error) {
    console.error('❌ Failed to get users:', error);
    res.status(500).json({
      success: false,
      message: 'Errore nel caricamento utenti'
    });
  }
};

/**
 * Create new user (admin only)
 */
export const createUser = async (req, res) => {
  try {
    // Check if user is admin
    if (req.user?.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Accesso negato: permessi amministratore richiesti'
      });
    }

    const { email, password, role = 'viewer' } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        success: false,
        message: 'Email e password sono richieste'
      });
    }

    // Validate role
    if (!Object.keys(ROLES).includes(role)) {
      return res.status(400).json({
        success: false,
        message: 'Ruolo non valido'
      });
    }

    // Check if user already exists
    const existingUser = await dbPool`
      SELECT id FROM pilotpros.users WHERE email = ${email}
    `;

    if (existingUser.length > 0) {
      return res.status(409).json({
        success: false,
        message: 'Utente già esistente con questa email'
      });
    }

    // Hash password
    const passwordHash = await bcrypt.hash(password, 10);
    const userId = uuidv4();

    // Create user
    await dbPool`
      INSERT INTO pilotpros.users (
        id, email, password_hash, role, is_active, created_at
      ) VALUES (
        ${userId}, ${email}, ${passwordHash}, ${role}, true, NOW()
      )
    `;

    // Get the created user
    const newUser = await dbPool`
      SELECT id, email, role, is_active, created_at
      FROM pilotpros.users 
      WHERE id = ${userId}
    `;

    res.status(201).json({
      success: true,
      message: 'Utente creato con successo',
      user: {
        ...newUser[0],
        permissions: ROLES[role]
      }
    });

  } catch (error) {
    console.error('❌ Failed to create user:', error);
    res.status(500).json({
      success: false,
      message: 'Errore nella creazione utente'
    });
  }
};

/**
 * Update user (admin only)
 */
export const updateUser = async (req, res) => {
  try {
    // Check if user is admin
    if (req.user?.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Accesso negato: permessi amministratore richiesti'
      });
    }

    const { userId } = req.params;
    const { email, role, is_active, password } = req.body;

    // Validate role if provided
    if (role && !Object.keys(ROLES).includes(role)) {
      return res.status(400).json({
        success: false,
        message: 'Ruolo non valido'
      });
    }

    // Check if user exists
    const existingUser = await dbPool`
      SELECT id, email, role FROM pilotpros.users WHERE id = ${userId}
    `;

    if (existingUser.length === 0) {
      return res.status(404).json({
        success: false,
        message: 'Utente non trovato'
      });
    }

    // Build update fields
    const updates = {};
    if (email) updates.email = email;
    if (role) updates.role = role;
    if (typeof is_active === 'boolean') updates.is_active = is_active;
    
    // Hash new password if provided
    if (password) {
      updates.password_hash = await bcrypt.hash(password, 10);
    }

    // Update user
    if (Object.keys(updates).length > 0) {
      const setClause = Object.keys(updates).map(key => `${key} = $${key}`).join(', ');
      await dbPool.query(
        `UPDATE pilotpros.users SET ${setClause} WHERE id = $userId`,
        { ...updates, userId }
      );
    }

    // Get updated user
    const updatedUser = await dbPool`
      SELECT id, email, role, is_active, created_at, last_login
      FROM pilotpros.users 
      WHERE id = ${userId}
    `;

    res.json({
      success: true,
      message: 'Utente aggiornato con successo',
      user: {
        ...updatedUser[0],
        permissions: ROLES[updatedUser[0].role]
      }
    });

  } catch (error) {
    console.error('❌ Failed to update user:', error);
    res.status(500).json({
      success: false,
      message: 'Errore nell\'aggiornamento utente'
    });
  }
};

/**
 * Delete user (admin only)
 */
export const deleteUser = async (req, res) => {
  try {
    // Check if user is admin
    if (req.user?.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: 'Accesso negato: permessi amministratore richiesti'
      });
    }

    const { userId } = req.params;

    // Prevent admin from deleting themselves
    if (req.user?.userId === userId) {
      return res.status(400).json({
        success: false,
        message: 'Non puoi eliminare il tuo stesso account'
      });
    }

    // Check if user exists
    const existingUser = await dbPool`
      SELECT id, email, role FROM pilotpros.users WHERE id = ${userId}
    `;

    if (existingUser.length === 0) {
      return res.status(404).json({
        success: false,
        message: 'Utente non trovato'
      });
    }

    // Delete user (cascade will handle related records)
    await dbPool`
      DELETE FROM pilotpros.users WHERE id = ${userId}
    `;

    res.json({
      success: true,
      message: 'Utente eliminato con successo'
    });

  } catch (error) {
    console.error('❌ Failed to delete user:', error);
    res.status(500).json({
      success: false,
      message: 'Errore nell\'eliminazione utente'
    });
  }
};

/**
 * Get available roles and permissions
 */
export const getRolesAndPermissions = async (req, res) => {
  try {
    res.json({
      success: true,
      roles: Object.keys(ROLES).map(role => ({
        name: role,
        permissions: ROLES[role]
      }))
    });
  } catch (error) {
    console.error('❌ Failed to get roles:', error);
    res.status(500).json({
      success: false,
      message: 'Errore nel caricamento ruoli'
    });
  }
};