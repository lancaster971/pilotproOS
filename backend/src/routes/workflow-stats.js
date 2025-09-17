import express from 'express';
import { db } from '../db/connection.js';
import { sql } from 'drizzle-orm';

const router = express.Router();

/**
 * Get complete statistics for a single workflow
 * Reads directly from n8n tables without modifications
 */
router.get('/workflow/:workflowId/full-stats', async (req, res) => {
  try {
    const { workflowId } = req.params;
    const { days = 30 } = req.query;
    
    // 1. Get workflow_statistics data (n8n's own tracking)
    const statsResult = await db.execute(sql`
      SELECT name, count, "latestEvent"
      FROM n8n.workflow_statistics
      WHERE "workflowId" = ${workflowId}
    `);
    
    // Parse n8n statistics
    const n8nStats = {};
    statsResult.forEach(row => {
      n8nStats[row.name] = {
        count: parseInt(row.count) || 0,
        lastEvent: row.latestEvent
      };
    });
    
    // 2. Get execution statistics (last N days)
    const executionStats = await db.execute(sql`
      SELECT
        COUNT(*) as total_executions,
        COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
        COUNT(CASE WHEN status = 'error' THEN 1 END) as failed,
        COUNT(CASE WHEN status = 'canceled' THEN 1 END) as canceled,
        COUNT(CASE WHEN status = 'running' THEN 1 END) as running,
        COUNT(CASE WHEN status = 'waiting' THEN 1 END) as waiting,
        AVG(CASE 
          WHEN "stoppedAt" IS NOT NULL AND "startedAt" IS NOT NULL 
          THEN EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt")) * 1000 
          ELSE NULL 
        END) as avg_duration_ms,
        MIN(CASE 
          WHEN "stoppedAt" IS NOT NULL AND "startedAt" IS NOT NULL 
          THEN EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt")) * 1000 
          ELSE NULL 
        END) as min_duration_ms,
        MAX(CASE 
          WHEN "stoppedAt" IS NOT NULL AND "startedAt" IS NOT NULL 
          THEN EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt")) * 1000 
          ELSE NULL 
        END) as max_duration_ms,
        MAX("startedAt") as last_execution
      FROM n8n.execution_entity
      WHERE "workflowId" = ${workflowId}
        AND "startedAt" >= NOW() - INTERVAL '${sql.raw(days)} days'
    `);
    
    // 3. Get daily trend (last 7 days)
    const dailyTrend = await db.execute(sql`
      SELECT 
        DATE("startedAt") as execution_date,
        COUNT(*) as executions,
        COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
        COUNT(CASE WHEN status = 'error' THEN 1 END) as failed,
        AVG(CASE 
          WHEN "stoppedAt" IS NOT NULL AND "startedAt" IS NOT NULL 
          THEN EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt")) * 1000 
          ELSE NULL 
        END) as avg_ms
      FROM n8n.execution_entity
      WHERE "workflowId" = ${workflowId}
        AND "startedAt" >= NOW() - INTERVAL '7 days'
      GROUP BY DATE("startedAt")
      ORDER BY execution_date DESC
    `);
    
    // 4. Get last 24h executions count
    const last24hResult = await db.execute(sql`
      SELECT COUNT(*) as count_24h
      FROM n8n.execution_entity
      WHERE "workflowId" = ${workflowId}
        AND "startedAt" >= NOW() - INTERVAL '24 hours'
    `);

    // 5. Get workflow info
    const workflowInfo = await db.execute(sql`
      SELECT name, active, "createdAt", "updatedAt"
      FROM n8n.workflow_entity
      WHERE id = ${workflowId}
    `);
    
    const stats = executionStats[0] || {};
    const info = workflowInfo[0] || {};
    const last24h = last24hResult[0] || {};

    // Calculate KPIs
    const totalExecutions = parseInt(stats.total_executions) || 0;
    const successful = parseInt(stats.successful) || 0;
    const failed = parseInt(stats.failed) || 0;
    const canceled = parseInt(stats.canceled) || 0;
    const successRate = totalExecutions > 0 ? (successful / totalExecutions * 100) : 0;
    const avgDurationMs = parseFloat(stats.avg_duration_ms) || 0;
    const executions24h = parseInt(last24h.count_24h) || 0;
    
    // Format response
    res.json({
      workflow: {
        id: workflowId,
        name: info.name,
        active: info.active,
        created: info.createdAt,
        updated: info.updatedAt
      },
      kpis: {
        // Main KPIs for Command Center
        totalExecutions,
        successfulExecutions: successful, // Aggiunto per il TimelineModal
        failedExecutions: failed,
        canceledExecutions: canceled, // Aggiunto per calcolo corretto nel TimelineModal
        successRate: totalExecutions > 0 ? Math.round(successRate * 10) / 10 : 0, // Aggiunto successRate
        failureRate: totalExecutions > 0 ? Math.round((failed / totalExecutions) * 100 * 10) / 10 : 0,
        timeSavedHours: Math.round((successful * 5) / 60), // 5 min saved per execution
        avgRunTime: avgDurationMs > 0 ? Math.round(avgDurationMs / 100) / 10 : 0, // in seconds
        minRunTime: parseFloat(stats.min_duration_ms) || 0, // Aggiunto per analytics
        maxRunTime: parseFloat(stats.max_duration_ms) || 0, // Aggiunto per analytics
        efficiencyScore: totalExecutions > 0 ? Math.min(100, Math.round(successRate * 1.2)) : 0, // Score basato su success rate
        reliabilityScore: Math.round(successRate), // Uguale a success rate
        last24hExecutions: executions24h, // Esecuzioni ultime 24 ore
        last7dExecutions: totalExecutions, // Già filtrato per periodo
        avgExecutionsPerDay: totalExecutions > 0 ? Math.round(totalExecutions / parseInt(days)) : 0,
        peakHour: null, // TODO: implementare se necessario
        totalDataProcessed: totalExecutions * 10, // Stima: 10 items per esecuzione
        automationImpact: successful * 5 // Minuti risparmiati
      },
      statistics: {
        // From workflow_statistics table
        n8n: n8nStats,
        // From execution_entity aggregation
        executions: {
          total: totalExecutions,
          successful,
          failed,
          running: parseInt(stats.running) || 0,
          waiting: parseInt(stats.waiting) || 0,
          successRate: Math.round(successRate * 10) / 10,
          lastExecution: stats.last_execution
        },
        performance: {
          avgDurationMs: Math.round(avgDurationMs * 10) / 10,
          minDurationMs: parseFloat(stats.min_duration_ms) || 0,
          maxDurationMs: parseFloat(stats.max_duration_ms) || 0,
          avgDurationSeconds: avgDurationMs > 0 ? Math.round(avgDurationMs / 100) / 10 : 0
        }
      },
      trends: {
        // Calcolo trend volume (confronto con periodo precedente)
        volumeTrend: totalExecutions > 0 ? 10 : 0, // TODO: calcolo reale confronto periodi
        successRateTrend: successRate > 80 ? 5 : -5, // TODO: calcolo reale confronto periodi
      },
      trend: dailyTrend.map(day => ({
        date: day.execution_date,
        executions: parseInt(day.executions),
        successful: parseInt(day.successful),
        failed: parseInt(day.failed),
        avgMs: parseFloat(day.avg_ms) || 0
      })),
      period: `${days} days`,
      _metadata: {
        source: 'n8n database direct',
        timestamp: new Date().toISOString()
      }
    });
    
  } catch (error) {
    console.error('❌ Error fetching workflow stats:', error);
    res.status(500).json({ 
      error: 'Failed to fetch workflow statistics',
      details: error.message 
    });
  }
});

export default router;