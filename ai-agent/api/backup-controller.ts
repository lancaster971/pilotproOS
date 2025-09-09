/**
 * Backup Controller
 * 
 * API endpoints per gestione backup database
 */

import express, { Request, Response } from 'express';
import { getDatabaseBackupService } from '../backup/database-backup.js';
import { getAuthService } from '../auth/jwt-auth.js';

const router = express.Router();
const backupService = getDatabaseBackupService();
const authService = getAuthService();

/**
 * @swagger
 * /api/backup/status:
 *   get:
 *     summary: Stato servizio backup
 *     description: Ottieni lo stato del servizio di backup automatico
 *     tags: [Backup]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Backup service status
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 isRunning:
 *                   type: boolean
 *                 config:
 *                   type: object
 *                 nextRun:
 *                   type: string
 *                   format: date-time
 */
router.get('/backup/status',
  authService.authenticateToken(),
  authService.requirePermission('system:read'),
  async (req: Request, res: Response) => {
    try {
      const status = backupService.getStatus();
      res.json(status);
    } catch (error) {
      res.status(500).json({
        error: 'Failed to get backup status',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }
);

/**
 * @swagger
 * /api/backup/list:
 *   get:
 *     summary: Lista backup disponibili
 *     description: Ottieni lista di tutti i backup disponibili
 *     tags: [Backup]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: List of available backups
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 backups:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       filename:
 *                         type: string
 *                       size:
 *                         type: number
 *                       created:
 *                         type: string
 *                         format: date-time
 *                       age_days:
 *                         type: number
 *                 total:
 *                   type: number
 */
router.get('/backup/list',
  authService.authenticateToken(),
  authService.requirePermission('backup:read'),
  async (req: Request, res: Response) => {
    try {
      const backups = await backupService.listBackups();
      res.json({
        backups,
        total: backups.length
      });
    } catch (error) {
      res.status(500).json({
        error: 'Failed to list backups',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }
);

/**
 * @swagger
 * /api/backup/create:
 *   post:
 *     summary: Crea backup manuale
 *     description: Esegui un backup manuale del database
 *     tags: [Backup]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               label:
 *                 type: string
 *                 description: Label opzionale per il backup
 *     responses:
 *       200:
 *         description: Backup created successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                 filename:
 *                   type: string
 *                 size:
 *                   type: number
 *                 duration_ms:
 *                   type: number
 */
router.post('/backup/create',
  authService.authenticateToken(),
  authService.requirePermission('backup:write'),
  async (req: Request, res: Response) => {
    try {
      const { label } = req.body;
      
      console.log(`📦 Creating manual backup${label ? ` with label: ${label}` : ''}...`);
      const result = await backupService.performBackup(label);
      
      if (result.success) {
        res.json(result);
      } else {
        res.status(500).json(result);
      }
    } catch (error) {
      res.status(500).json({
        error: 'Failed to create backup',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }
);

/**
 * @swagger
 * /api/backup/restore:
 *   post:
 *     summary: Ripristina backup
 *     description: Ripristina il database da un backup
 *     tags: [Backup]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - filename
 *             properties:
 *               filename:
 *                 type: string
 *                 description: Nome del file di backup da ripristinare
 *     responses:
 *       200:
 *         description: Backup restored successfully
 *       500:
 *         description: Restore failed
 */
router.post('/backup/restore',
  authService.authenticateToken(),
  authService.requirePermission('backup:restore'),
  async (req: Request, res: Response) => {
    try {
      const { filename } = req.body;
      
      if (!filename) {
        return res.status(400).json({
          error: 'Bad Request',
          message: 'Filename is required'
        });
      }
      
      console.log(`🔄 Restoring backup: ${filename}...`);
      const result = await backupService.restoreBackup(filename);
      
      if (result.success) {
        res.json({
          message: 'Backup restored successfully',
          ...result
        });
      } else {
        res.status(500).json(result);
      }
    } catch (error) {
      res.status(500).json({
        error: 'Failed to restore backup',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }
);

/**
 * @swagger
 * /api/backup/clean:
 *   post:
 *     summary: Pulisci backup vecchi
 *     description: Elimina backup più vecchi del periodo di retention
 *     tags: [Backup]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Old backups cleaned
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 deleted:
 *                   type: number
 */
router.post('/backup/clean',
  authService.authenticateToken(),
  authService.requirePermission('backup:delete'),
  async (req: Request, res: Response) => {
    try {
      const deletedCount = await backupService.cleanOldBackups();
      res.json({
        message: `Cleaned ${deletedCount} old backup(s)`,
        deleted: deletedCount
      });
    } catch (error) {
      res.status(500).json({
        error: 'Failed to clean backups',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }
);

/**
 * @swagger
 * /api/backup/start:
 *   post:
 *     summary: Avvia servizio backup
 *     description: Avvia il servizio di backup automatico
 *     tags: [Backup]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Backup service started
 */
router.post('/backup/start',
  authService.authenticateToken(),
  authService.requirePermission('backup:control'),
  async (req: Request, res: Response) => {
    try {
      await backupService.start();
      res.json({
        message: 'Backup service started',
        status: backupService.getStatus()
      });
    } catch (error) {
      res.status(500).json({
        error: 'Failed to start backup service',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }
);

/**
 * @swagger
 * /api/backup/stop:
 *   post:
 *     summary: Ferma servizio backup
 *     description: Ferma il servizio di backup automatico
 *     tags: [Backup]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Backup service stopped
 */
router.post('/backup/stop',
  authService.authenticateToken(),
  authService.requirePermission('backup:control'),
  async (req: Request, res: Response) => {
    try {
      backupService.stop();
      res.json({
        message: 'Backup service stopped',
        status: backupService.getStatus()
      });
    } catch (error) {
      res.status(500).json({
        error: 'Failed to stop backup service',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }
);

export default router;