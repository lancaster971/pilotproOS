import express from 'express';
import { exec } from 'child_process';
import util from 'util';
import fs from 'fs/promises';
import path from 'path';
import { dbPool } from '../db/pg-pool.js';

const router = express.Router();
const execPromise = util.promisify(exec);

/**
 * Get configured backup directory from database
 */
async function getBackupDirectory() {
  try {
    const result = await dbPool.query('SELECT backup_directory FROM backup_settings LIMIT 1');
    return result.rows[0]?.backup_directory || '/app/backups';
  } catch (error) {
    console.error('Error fetching backup directory:', error);
    return '/app/backups'; // Fallback to default
  }
}

/**
 * @route POST /api/backup/create
 * @desc Create full database backup
 */
router.post('/create', async (req, res) => {
  try {
    const BACKUP_DIR = await getBackupDirectory();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `backup-${timestamp}.sql`;
    const filepath = path.join(BACKUP_DIR, filename);

    // Ensure backup directory exists
    await fs.mkdir(BACKUP_DIR, { recursive: true });

    // Create PostgreSQL backup using pg_dump with TCP connection
    const dbHost = process.env.POSTGRES_HOST || 'pilotpros-postgres-dev';
    const dbPort = process.env.POSTGRES_PORT || '5432';
    const dbUser = process.env.POSTGRES_USER || 'pilotpros_user';
    const dbName = process.env.POSTGRES_DB || 'pilotpros_db';
    const dbPassword = process.env.POSTGRES_PASSWORD || 'pilotpros_secure_pass_2025';

    const { stdout, stderr } = await execPromise(
      `PGPASSWORD="${dbPassword}" pg_dump -h ${dbHost} -p ${dbPort} -U ${dbUser} ${dbName} > ${filepath}`
    );

    const stats = await fs.stat(filepath);

    res.json({
      success: true,
      backup: {
        filename,
        size: stats.size,
        created: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('Backup error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route GET /api/backup/list
 * @desc List all available backups
 */
router.get('/list', async (req, res) => {
  try {
    const BACKUP_DIR = await getBackupDirectory();
    await fs.mkdir(BACKUP_DIR, { recursive: true });
    const files = await fs.readdir(BACKUP_DIR);
    
    const backups = await Promise.all(
      files
        .filter(f => f.endsWith('.sql'))
        .map(async (filename) => {
          const filepath = path.join(BACKUP_DIR, filename);
          const stats = await fs.stat(filepath);
          return {
            filename,
            size: stats.size,
            created: stats.birthtime.toISOString()
          };
        })
    );

    // Sort by date descending
    backups.sort((a, b) => new Date(b.created) - new Date(a.created));

    res.json({
      success: true,
      backups
    });
  } catch (error) {
    console.error('List backups error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route POST /api/backup/restore/:filename
 * @desc Restore database from backup
 */
router.post('/restore/:filename', async (req, res) => {
  try {
    const BACKUP_DIR = await getBackupDirectory();
    const { filename } = req.params;
    const filepath = path.join(BACKUP_DIR, filename);

    // Verify file exists
    await fs.access(filepath);

    // Restore database using psql with TCP connection
    const dbHost = process.env.POSTGRES_HOST || 'pilotpros-postgres-dev';
    const dbPort = process.env.POSTGRES_PORT || '5432';
    const dbUser = process.env.POSTGRES_USER || 'pilotpros_user';
    const dbName = process.env.POSTGRES_DB || 'pilotpros_db';
    const dbPassword = process.env.POSTGRES_PASSWORD || 'pilotpros_secure_pass_2025';

    const { stdout, stderr } = await execPromise(
      `PGPASSWORD="${dbPassword}" psql -h ${dbHost} -p ${dbPort} -U ${dbUser} ${dbName} < ${filepath}`
    );

    res.json({
      success: true,
      message: `Database restored from ${filename}`,
      restored: new Date().toISOString()
    });
  } catch (error) {
    console.error('Restore error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route DELETE /api/backup/delete/:filename
 * @desc Delete a backup file
 */
router.delete('/delete/:filename', async (req, res) => {
  try {
    const BACKUP_DIR = await getBackupDirectory();
    const { filename } = req.params;
    const filepath = path.join(BACKUP_DIR, filename);

    await fs.unlink(filepath);

    res.json({
      success: true,
      message: `Backup ${filename} deleted`
    });
  } catch (error) {
    console.error('Delete backup error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * @route GET /api/backup/download/:filename
 * @desc Download a backup file
 */
router.get('/download/:filename', async (req, res) => {
  try {
    const BACKUP_DIR = await getBackupDirectory();
    const { filename } = req.params;
    const filepath = path.join(BACKUP_DIR, filename);

    await fs.access(filepath);

    res.download(filepath, filename);
  } catch (error) {
    console.error('Download backup error:', error);
    res.status(404).json({
      success: false,
      error: 'Backup file not found'
    });
  }
});

export default router;
