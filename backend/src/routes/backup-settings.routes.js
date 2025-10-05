import express from 'express';
import { dbPool } from '../db/pg-pool.js';
import autoBackupService from '../services/auto-backup.service.js';

const router = express.Router();

/**
 * @route GET /api/backup-settings
 * @desc Get current backup configuration
 */
router.get('/', async (req, res) => {
  try {
    const result = await dbPool.query('SELECT * FROM backup_settings LIMIT 1');

    if (result.rows.length === 0) {
      // Return default settings if none exist
      return res.json({
        success: true,
        settings: {
          backup_directory: '/app/backups',
          auto_backup_enabled: false,
          auto_backup_schedule: '0 2 * * *',
          retention_days: 30
        }
      });
    }

    res.json({
      success: true,
      settings: result.rows[0]
    });
  } catch (error) {
    console.error('Get backup settings error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route PUT /api/backup-settings
 * @desc Update backup configuration
 */
router.put('/', async (req, res) => {
  try {
    const {
      backup_directory,
      auto_backup_enabled,
      auto_backup_schedule,
      retention_days
    } = req.body;

    // Validate backup_directory
    if (backup_directory && typeof backup_directory !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'backup_directory must be a string'
      });
    }

    // Validate retention_days
    if (retention_days !== undefined && (typeof retention_days !== 'number' || retention_days < 1)) {
      return res.status(400).json({
        success: false,
        error: 'retention_days must be a positive number'
      });
    }

    // Build dynamic UPDATE query
    const updates = [];
    const values = [];
    let paramCount = 1;

    if (backup_directory !== undefined) {
      updates.push(`backup_directory = $${paramCount++}`);
      values.push(backup_directory);
    }
    if (auto_backup_enabled !== undefined) {
      updates.push(`auto_backup_enabled = $${paramCount++}`);
      values.push(auto_backup_enabled);
    }
    if (auto_backup_schedule !== undefined) {
      updates.push(`auto_backup_schedule = $${paramCount++}`);
      values.push(auto_backup_schedule);
    }
    if (retention_days !== undefined) {
      updates.push(`retention_days = $${paramCount++}`);
      values.push(retention_days);
    }

    if (updates.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No valid fields to update'
      });
    }

    const query = `
      UPDATE backup_settings
      SET ${updates.join(', ')}
      WHERE id = (SELECT id FROM backup_settings LIMIT 1)
      RETURNING *
    `;

    const result = await dbPool.query(query, values);

    // Restart auto-backup scheduler if settings changed
    try {
      await autoBackupService.restart();
    } catch (error) {
      console.error('Failed to restart auto-backup service:', error);
    }

    res.json({
      success: true,
      settings: result.rows[0]
    });
  } catch (error) {
    console.error('Update backup settings error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route POST /api/backup-settings/validate-directory
 * @desc Validate if directory path is accessible
 */
router.post('/validate-directory', async (req, res) => {
  try {
    const { directory } = req.body;

    if (!directory || typeof directory !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Directory path is required'
      });
    }

    // Basic path validation
    if (!directory.startsWith('/')) {
      return res.status(400).json({
        success: false,
        error: 'Directory must be an absolute path (starting with /)'
      });
    }

    // Check for dangerous paths
    const dangerousPaths = ['/etc', '/bin', '/sbin', '/usr/bin', '/usr/sbin', '/root'];
    if (dangerousPaths.some(dp => directory.startsWith(dp))) {
      return res.status(400).json({
        success: false,
        error: 'Cannot use system directories for backups'
      });
    }

    res.json({
      success: true,
      valid: true,
      message: 'Directory path is valid'
    });
  } catch (error) {
    console.error('Validate directory error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

export default router;
