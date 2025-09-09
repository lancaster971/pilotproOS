/**
 * Database Backup Service
 * 
 * Servizio per backup automatico del database PostgreSQL
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs/promises';
import path from 'path';
import cron from 'node-cron';
import { DatabaseConnection } from '../database/connection.js';

const execAsync = promisify(exec);

export interface BackupConfig {
  enabled: boolean;
  schedule: string; // Cron expression
  retentionDays: number;
  backupPath: string;
  compress: boolean;
  includeData: boolean;
  includeSchema: boolean;
}

export interface BackupResult {
  success: boolean;
  filename?: string;
  size?: number;
  duration_ms?: number;
  error?: string;
  timestamp: string;
}

/**
 * Database Backup Service
 */
export class DatabaseBackupService {
  private config: BackupConfig;
  private scheduledTask: cron.ScheduledTask | null = null;
  private db: DatabaseConnection;
  private isRunning: boolean = false;

  constructor(config?: Partial<BackupConfig>) {
    this.config = {
      enabled: process.env.BACKUP_ENABLED === 'true',
      schedule: process.env.BACKUP_SCHEDULE || '0 2 * * *', // Default: 2 AM daily
      retentionDays: parseInt(process.env.BACKUP_RETENTION_DAYS || '7'),
      backupPath: process.env.BACKUP_PATH || './backups',
      compress: process.env.BACKUP_COMPRESS !== 'false',
      includeData: process.env.BACKUP_INCLUDE_DATA !== 'false',
      includeSchema: process.env.BACKUP_INCLUDE_SCHEMA !== 'false',
      ...config
    };
    
    this.db = DatabaseConnection.getInstance();
  }

  /**
   * Start backup scheduler
   */
  async start(): Promise<void> {
    if (!this.config.enabled) {
      console.log('📦 Database backup service disabled');
      return;
    }

    // Ensure backup directory exists
    await this.ensureBackupDirectory();

    // Schedule backup task
    this.scheduledTask = cron.schedule(this.config.schedule, async () => {
      console.log('🔄 Starting scheduled database backup...');
      const result = await this.performBackup();
      
      if (result.success) {
        console.log(`✅ Backup completed: ${result.filename} (${this.formatBytes(result.size || 0)})`);
        
        // Clean old backups
        await this.cleanOldBackups();
      } else {
        console.error(`❌ Backup failed: ${result.error}`);
      }
    });

    console.log(`📦 Database backup service started (schedule: ${this.config.schedule})`);
    this.isRunning = true;
  }

  /**
   * Stop backup scheduler
   */
  stop(): void {
    if (this.scheduledTask) {
      this.scheduledTask.stop();
      this.scheduledTask = null;
      this.isRunning = false;
      console.log('📦 Database backup service stopped');
    }
  }

  /**
   * Perform manual backup
   */
  async performBackup(label?: string): Promise<BackupResult> {
    const startTime = Date.now();
    
    try {
      // Get database connection info
      const dbConfig = this.db.getConfig();
      
      // Generate backup filename
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const labelPart = label ? `-${label}` : '';
      const extension = this.config.compress ? '.sql.gz' : '.sql';
      const filename = `backup-${timestamp}${labelPart}${extension}`;
      const filepath = path.join(this.config.backupPath, filename);

      // Build pg_dump command
      let pgDumpCmd = `pg_dump`;
      
      // Connection parameters
      pgDumpCmd += ` -h ${dbConfig.host}`;
      pgDumpCmd += ` -p ${dbConfig.port}`;
      pgDumpCmd += ` -U ${dbConfig.user}`;
      pgDumpCmd += ` -d ${dbConfig.database}`;
      
      // Backup options
      if (!this.config.includeData) {
        pgDumpCmd += ' --schema-only';
      }
      if (!this.config.includeSchema) {
        pgDumpCmd += ' --data-only';
      }
      
      // Add verbose and clean options
      pgDumpCmd += ' --verbose --clean --if-exists';
      
      // Compression
      if (this.config.compress) {
        pgDumpCmd += ` | gzip > "${filepath}"`;
      } else {
        pgDumpCmd += ` > "${filepath}"`;
      }

      // Set PGPASSWORD environment variable
      const env = {
        ...process.env,
        PGPASSWORD: dbConfig.password || ''
      };

      // Execute backup
      await execAsync(pgDumpCmd, { env });

      // Get file size
      const stats = await fs.stat(filepath);
      
      // Log backup to database
      await this.logBackup({
        filename,
        filepath,
        size: stats.size,
        duration_ms: Date.now() - startTime,
        success: true
      });

      return {
        success: true,
        filename,
        size: stats.size,
        duration_ms: Date.now() - startTime,
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      // Log failed backup
      await this.logBackup({
        filename: 'failed',
        filepath: '',
        size: 0,
        duration_ms: Date.now() - startTime,
        success: false,
        error: errorMessage
      });

      return {
        success: false,
        error: errorMessage,
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Restore from backup
   */
  async restoreBackup(filename: string): Promise<BackupResult> {
    const startTime = Date.now();
    
    try {
      const filepath = path.join(this.config.backupPath, filename);
      
      // Check if file exists
      await fs.access(filepath);
      
      // Get database connection info
      const dbConfig = this.db.getConfig();
      
      // Build psql restore command
      let restoreCmd = '';
      
      if (filename.endsWith('.gz')) {
        restoreCmd = `gunzip -c "${filepath}" | `;
      } else {
        restoreCmd = `cat "${filepath}" | `;
      }
      
      restoreCmd += `psql`;
      restoreCmd += ` -h ${dbConfig.host}`;
      restoreCmd += ` -p ${dbConfig.port}`;
      restoreCmd += ` -U ${dbConfig.user}`;
      restoreCmd += ` -d ${dbConfig.database}`;
      
      // Set PGPASSWORD environment variable
      const env = {
        ...process.env,
        PGPASSWORD: dbConfig.password || ''
      };

      // Execute restore
      await execAsync(restoreCmd, { env });

      return {
        success: true,
        filename,
        duration_ms: Date.now() - startTime,
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * List available backups
   */
  async listBackups(): Promise<Array<{
    filename: string;
    size: number;
    created: Date;
    age_days: number;
  }>> {
    try {
      const files = await fs.readdir(this.config.backupPath);
      const backups = [];
      
      for (const file of files) {
        if (file.startsWith('backup-') && (file.endsWith('.sql') || file.endsWith('.sql.gz'))) {
          const filepath = path.join(this.config.backupPath, file);
          const stats = await fs.stat(filepath);
          const ageDays = Math.floor((Date.now() - stats.mtime.getTime()) / (1000 * 60 * 60 * 24));
          
          backups.push({
            filename: file,
            size: stats.size,
            created: stats.mtime,
            age_days: ageDays
          });
        }
      }
      
      // Sort by creation date (newest first)
      backups.sort((a, b) => b.created.getTime() - a.created.getTime());
      
      return backups;
    } catch (error) {
      console.error('Error listing backups:', error);
      return [];
    }
  }

  /**
   * Clean old backups
   */
  async cleanOldBackups(): Promise<number> {
    try {
      const backups = await this.listBackups();
      let deletedCount = 0;
      
      for (const backup of backups) {
        if (backup.age_days > this.config.retentionDays) {
          const filepath = path.join(this.config.backupPath, backup.filename);
          await fs.unlink(filepath);
          console.log(`🗑️ Deleted old backup: ${backup.filename} (${backup.age_days} days old)`);
          deletedCount++;
        }
      }
      
      if (deletedCount > 0) {
        console.log(`🧹 Cleaned ${deletedCount} old backup(s)`);
      }
      
      return deletedCount;
    } catch (error) {
      console.error('Error cleaning old backups:', error);
      return 0;
    }
  }

  /**
   * Ensure backup directory exists
   */
  private async ensureBackupDirectory(): Promise<void> {
    try {
      await fs.access(this.config.backupPath);
    } catch {
      await fs.mkdir(this.config.backupPath, { recursive: true });
      console.log(`📁 Created backup directory: ${this.config.backupPath}`);
    }
  }

  /**
   * Log backup to database
   */
  private async logBackup(data: {
    filename: string;
    filepath: string;
    size: number;
    duration_ms: number;
    success: boolean;
    error?: string;
  }): Promise<void> {
    try {
      // Create backup_logs table if not exists
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS backup_logs (
          id SERIAL PRIMARY KEY,
          filename VARCHAR(255) NOT NULL,
          filepath TEXT,
          size_bytes BIGINT,
          duration_ms INTEGER,
          success BOOLEAN NOT NULL,
          error_message TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
      
      // Insert log
      await this.db.query(`
        INSERT INTO backup_logs (filename, filepath, size_bytes, duration_ms, success, error_message)
        VALUES ($1, $2, $3, $4, $5, $6)
      `, [data.filename, data.filepath, data.size, data.duration_ms, data.success, data.error || null]);
      
    } catch (error) {
      console.error('Failed to log backup:', error);
    }
  }

  /**
   * Format bytes to human readable
   */
  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Get backup status
   */
  getStatus(): {
    isRunning: boolean;
    config: BackupConfig;
    nextRun?: Date;
  } {
    const status: any = {
      isRunning: this.isRunning,
      config: this.config
    };
    
    if (this.scheduledTask) {
      // Calculate next run based on cron expression
      const cronExpression = cron.validate(this.config.schedule);
      if (cronExpression) {
        // This is simplified - in production you'd use a cron parser
        status.nextRun = new Date(Date.now() + 24 * 60 * 60 * 1000); // Next day
      }
    }
    
    return status;
  }
}

// Singleton instance
let backupInstance: DatabaseBackupService | null = null;

export function getDatabaseBackupService(config?: Partial<BackupConfig>): DatabaseBackupService {
  if (!backupInstance) {
    backupInstance = new DatabaseBackupService(config);
  }
  return backupInstance;
}