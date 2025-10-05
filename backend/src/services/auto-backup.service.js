import cron from 'node-cron';
import { exec } from 'child_process';
import util from 'util';
import fs from 'fs/promises';
import path from 'path';
import { dbPool } from '../db/pg-pool.js';

const execPromise = util.promisify(exec);

/**
 * Auto-Backup Service
 * Manages scheduled automatic database backups
 */
class AutoBackupService {
  constructor() {
    this.cronJob = null;
    this.isRunning = false;
  }

  /**
   * Get backup configuration from database
   */
  async getBackupConfig() {
    try {
      const result = await dbPool.query('SELECT * FROM backup_settings LIMIT 1');
      return result.rows[0] || {
        backup_directory: '/app/backups',
        auto_backup_enabled: false,
        auto_backup_schedule: '0 2 * * *',
        retention_days: 30
      };
    } catch (error) {
      console.error('❌ Error fetching backup config:', error);
      return null;
    }
  }

  /**
   * Create database backup
   */
  async createBackup() {
    try {
      const config = await this.getBackupConfig();
      if (!config) {
        console.error('❌ Cannot create backup: config not available');
        return { success: false, error: 'Config not available' };
      }

      const BACKUP_DIR = config.backup_directory;
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `auto-backup-${timestamp}.sql`;
      const filepath = path.join(BACKUP_DIR, filename);

      // Ensure backup directory exists
      await fs.mkdir(BACKUP_DIR, { recursive: true });

      // Database credentials
      const dbHost = process.env.POSTGRES_HOST || 'pilotpros-postgres-dev';
      const dbPort = process.env.POSTGRES_PORT || '5432';
      const dbUser = process.env.POSTGRES_USER || 'pilotpros_user';
      const dbName = process.env.POSTGRES_DB || 'pilotpros_db';
      const dbPassword = process.env.POSTGRES_PASSWORD || 'pilotpros_secure_pass_2025';

      // Execute pg_dump
      await execPromise(
        `PGPASSWORD="${dbPassword}" pg_dump -h ${dbHost} -p ${dbPort} -U ${dbUser} ${dbName} > ${filepath}`
      );

      const stats = await fs.stat(filepath);

      console.log(`✅ Auto-backup created: ${filename} (${Math.round(stats.size / 1024)}KB)`);

      // Cleanup old backups based on retention_days
      await this.cleanupOldBackups(BACKUP_DIR, config.retention_days);

      return {
        success: true,
        backup: {
          filename,
          size: stats.size,
          created: new Date().toISOString()
        }
      };
    } catch (error) {
      console.error('❌ Auto-backup error:', error.message);
      return { success: false, error: error.message };
    }
  }

  /**
   * Cleanup old backups based on retention days
   */
  async cleanupOldBackups(backupDir, retentionDays) {
    try {
      const files = await fs.readdir(backupDir);
      const now = Date.now();
      const maxAge = retentionDays * 24 * 60 * 60 * 1000; // Convert days to ms

      let deletedCount = 0;

      for (const filename of files) {
        if (!filename.endsWith('.sql')) continue;

        const filepath = path.join(backupDir, filename);
        const stats = await fs.stat(filepath);
        const fileAge = now - stats.birthtimeMs;

        if (fileAge > maxAge) {
          await fs.unlink(filepath);
          deletedCount++;
          console.log(`🗑️  Deleted old backup: ${filename} (${Math.round(fileAge / (24 * 60 * 60 * 1000))} days old)`);
        }
      }

      if (deletedCount > 0) {
        console.log(`✅ Cleanup complete: ${deletedCount} old backup(s) deleted`);
      }
    } catch (error) {
      console.error('❌ Cleanup error:', error.message);
    }
  }

  /**
   * Start auto-backup scheduler
   */
  async start() {
    if (this.isRunning) {
      console.log('⚠️  Auto-backup scheduler already running');
      return;
    }

    const config = await this.getBackupConfig();
    if (!config) {
      console.error('❌ Cannot start auto-backup: config not available');
      return;
    }

    if (!config.auto_backup_enabled) {
      console.log('⏸️  Auto-backup is disabled in settings');
      return;
    }

    // Validate cron schedule
    if (!cron.validate(config.auto_backup_schedule)) {
      console.error(`❌ Invalid cron schedule: ${config.auto_backup_schedule}`);
      return;
    }

    // Stop existing job if any
    if (this.cronJob) {
      this.cronJob.stop();
    }

    // Create new cron job
    this.cronJob = cron.schedule(
      config.auto_backup_schedule,
      async () => {
        console.log('🔄 Auto-backup triggered by schedule');
        await this.createBackup();
      },
      {
        scheduled: true,
        timezone: 'Europe/Rome' // Italian timezone
      }
    );

    this.isRunning = true;
    console.log(`✅ Auto-backup scheduler started: ${config.auto_backup_schedule} (Europe/Rome)`);
    console.log(`📁 Backup directory: ${config.backup_directory}`);
    console.log(`🗓️  Retention: ${config.retention_days} days`);
  }

  /**
   * Stop auto-backup scheduler
   */
  stop() {
    if (this.cronJob) {
      this.cronJob.stop();
      this.isRunning = false;
      console.log('⏹️  Auto-backup scheduler stopped');
    }
  }

  /**
   * Restart scheduler (reload config)
   */
  async restart() {
    console.log('🔄 Restarting auto-backup scheduler...');
    this.stop();
    await this.start();
  }

  /**
   * Get scheduler status
   */
  getStatus() {
    return {
      isRunning: this.isRunning,
      hasJob: !!this.cronJob
    };
  }
}

// Singleton instance
const autoBackupService = new AutoBackupService();

export default autoBackupService;
