import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, businessProcedure } from '../trpc.js';
import { notifyAnalyticsUpdate, notifyInsightsUpdate, notifyHealthUpdate } from '../../websocket.js';

/**
 * Analytics Router - Business Analytics & Statistics
 * Migrates analytics, statistics, and insights endpoints to tRPC
 */

export const analyticsRouter = router({
  
  /**
   * Get business analytics overview
   * Equivalent to: GET /api/business/analytics
   */
  getOverview: businessProcedure
    .query(async ({ ctx }) => {
      console.log('📊 tRPC: Getting business analytics overview');
      
      try {
        const analyticsQuery = `
          SELECT 
            COUNT(DISTINCT w.id) as total_processes,
            COUNT(DISTINCT CASE WHEN w.active = true THEN w.id END) as active_processes,
            COUNT(e.id) as total_executions,
            COUNT(CASE WHEN e.status = 'success' THEN 1 END) as successful_executions,
            AVG(EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) * 1000) as avg_duration_ms
          FROM n8n.workflow_entity w
          LEFT JOIN n8n.execution_entity e ON w.id = e."workflowId"
          WHERE w."isArchived" = false
            AND (e."startedAt" IS NULL OR e."startedAt" >= NOW() - INTERVAL '7 days')
        `;
        
        const result = await ctx.dbPool.query(analyticsQuery);
        const data = result.rows[0];
        
        const successRate = data.total_executions > 0 
          ? (data.successful_executions / data.total_executions * 100) 
          : 0;
        
        const overview = {
          totalProcesses: parseInt(data.total_processes) || 0,
          activeProcesses: parseInt(data.active_processes) || 0,
          totalExecutions: parseInt(data.total_executions) || 0,
          successRate: Math.round(successRate * 10) / 10,
          avgDurationSeconds: Math.round((data.avg_duration_ms || 0) / 1000)
        };
        
        console.log(`✅ tRPC: Analytics overview - ${overview.totalProcesses} processes, ${overview.totalExecutions} executions`);
        
        const overviewResult = {
          success: true,
          overview,
          timestamp: new Date().toISOString()
        };
        
        // Notify WebSocket clients of analytics update
        notifyAnalyticsUpdate(overviewResult);
        
        return overviewResult;
        
      } catch (error) {
        console.error('❌ tRPC analytics getOverview failed:', error);
        
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Errore durante recupero analytics business',
          cause: error.message
        });
      }
    }),

  /**
   * Get business statistics
   * Equivalent to: GET /api/business/statistics
   */
  getStatistics: businessProcedure
    .query(async ({ ctx }) => {
      console.log('📈 tRPC: Getting business statistics');
      
      try {
        // Get workflow statistics
        const workflowStats = await ctx.dbPool.query(`
          SELECT 
            COUNT(*) as total_workflows,
            COUNT(CASE WHEN active = true THEN 1 END) as active_workflows,
            COUNT(CASE WHEN active = false THEN 1 END) as inactive_workflows
          FROM n8n.workflow_entity 
          WHERE "isArchived" = false
        `);

        // Get execution statistics for last 30 days
        const executionStats = await ctx.dbPool.query(`
          SELECT 
            COUNT(*) as total_executions,
            COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_executions,
            COUNT(CASE WHEN status = 'error' THEN 1 END) as failed_executions,
            AVG(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt")) * 1000) as avg_execution_time_ms
          FROM n8n.execution_entity 
          WHERE "startedAt" >= NOW() - INTERVAL '30 days'
        `);

        // Get daily execution trend (last 7 days)
        const executionTrend = await ctx.dbPool.query(`
          SELECT 
            DATE("startedAt") as execution_date,
            COUNT(*) as execution_count,
            COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count
          FROM n8n.execution_entity 
          WHERE "startedAt" >= NOW() - INTERVAL '7 days'
          GROUP BY DATE("startedAt")
          ORDER BY execution_date ASC
        `);

        const workflowData = workflowStats.rows[0];
        const executionData = executionStats.rows[0];
        
        const successRate = executionData.total_executions > 0 
          ? (executionData.successful_executions / executionData.total_executions * 100) 
          : 0;

        const statistics = {
          workflows: {
            total: parseInt(workflowData.total_workflows) || 0,
            active: parseInt(workflowData.active_workflows) || 0,
            inactive: parseInt(workflowData.inactive_workflows) || 0
          },
          executions: {
            total: parseInt(executionData.total_executions) || 0,
            successful: parseInt(executionData.successful_executions) || 0,
            failed: parseInt(executionData.failed_executions) || 0,
            successRate: Math.round(successRate * 10) / 10,
            avgExecutionTime: Math.round((executionData.avg_execution_time_ms || 0) / 1000)
          },
          trend: executionTrend.rows.map(row => ({
            date: row.execution_date,
            executions: parseInt(row.execution_count),
            successCount: parseInt(row.success_count)
          }))
        };
        
        console.log(`✅ tRPC: Statistics retrieved - ${statistics.workflows.total} workflows, ${statistics.executions.total} executions`);
        
        return {
          success: true,
          statistics,
          timestamp: new Date().toISOString()
        };
        
      } catch (error) {
        console.error('❌ tRPC analytics getStatistics failed:', error);
        
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Errore durante recupero statistiche business',
          cause: error.message
        });
      }
    }),

  /**
   * Get automation insights
   * Equivalent to: GET /api/business/automation-insights
   */
  getAutomationInsights: businessProcedure
    .query(async ({ ctx }) => {
      console.log('🤖 tRPC: Getting automation insights');
      
      try {
        // Get top performing workflows
        const topWorkflows = await ctx.dbPool.query(`
          SELECT 
            w.name as process_name,
            COUNT(e.id) as execution_count,
            COUNT(CASE WHEN e.status = 'success' THEN 1 END) as success_count,
            AVG(EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) * 1000) as avg_duration_ms
          FROM n8n.workflow_entity w
          LEFT JOIN n8n.execution_entity e ON w.id = e."workflowId"
          WHERE w."isArchived" = false 
            AND e."startedAt" >= NOW() - INTERVAL '30 days'
          GROUP BY w.id, w.name
          HAVING COUNT(e.id) > 0
          ORDER BY execution_count DESC
          LIMIT 10
        `);

        // Calculate time saved (estimated)
        const timeSavedQuery = await ctx.dbPool.query(`
          SELECT 
            COUNT(CASE WHEN e.status = 'success' THEN 1 END) as successful_executions
          FROM n8n.execution_entity e
          WHERE e."startedAt" >= NOW() - INTERVAL '30 days'
        `);

        const successfulExecutions = parseInt(timeSavedQuery.rows[0]?.successful_executions) || 0;
        const estimatedTimeSavedHours = Math.round(successfulExecutions * 0.5); // Estimate 30 minutes saved per execution

        const insights = {
          topPerformers: topWorkflows.rows.map(row => ({
            processName: row.process_name,
            executionCount: parseInt(row.execution_count),
            successCount: parseInt(row.success_count),
            successRate: row.execution_count > 0 
              ? Math.round((row.success_count / row.execution_count) * 100) 
              : 0,
            avgDuration: Math.round((row.avg_duration_ms || 0) / 1000)
          })),
          automation: {
            timeSavedHours: estimatedTimeSavedHours,
            processesAutomated: topWorkflows.rows.length,
            totalSuccessfulRuns: successfulExecutions
          }
        };
        
        console.log(`✅ tRPC: Automation insights - ${insights.topPerformers.length} top performers, ${estimatedTimeSavedHours}h saved`);
        
        const insightsResult = {
          success: true,
          insights,
          timestamp: new Date().toISOString()
        };
        
        // Notify WebSocket clients of insights update
        notifyInsightsUpdate(insightsResult);
        
        return insightsResult;
        
      } catch (error) {
        console.error('❌ tRPC analytics getAutomationInsights failed:', error);
        
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Errore durante recupero insights automazione',
          cause: error.message
        });
      }
    }),

  /**
   * Get integration health
   * Equivalent to: GET /api/business/integration-health
   */
  getIntegrationHealth: businessProcedure
    .query(async ({ ctx }) => {
      console.log('🔗 tRPC: Getting integration health');
      
      try {
        // Get connection statistics from workflows (simplified)
        const healthQuery = await ctx.dbPool.query(`
          SELECT 
            COUNT(DISTINCT w.id) as total_workflows,
            COUNT(DISTINCT CASE WHEN w.active = true THEN w.id END) as active_workflows,
            COUNT(DISTINCT e.id) as recent_executions,
            COUNT(CASE WHEN e.status = 'success' THEN 1 END) as successful_executions
          FROM n8n.workflow_entity w
          LEFT JOIN n8n.execution_entity e ON w.id = e."workflowId" 
            AND e."startedAt" >= NOW() - INTERVAL '24 hours'
          WHERE w."isArchived" = false
        `);

        const data = healthQuery.rows[0];
        const totalConnections = parseInt(data.total_workflows) || 0;
        const healthyConnections = parseInt(data.active_workflows) || 0;
        const recentExecutions = parseInt(data.recent_executions) || 0;
        const successfulExecutions = parseInt(data.successful_executions) || 0;
        
        const healthScore = totalConnections > 0 
          ? Math.round((healthyConnections / totalConnections) * 100)
          : 100;

        const health = {
          totalConnections,
          healthyConnections,
          activeConnections: healthyConnections,
          healthScore,
          recentActivity: {
            executions24h: recentExecutions,
            successfulExecutions24h: successfulExecutions,
            successRate24h: recentExecutions > 0 
              ? Math.round((successfulExecutions / recentExecutions) * 100)
              : 0
          }
        };
        
        console.log(`✅ tRPC: Integration health - ${healthScore}% health score, ${totalConnections} connections`);
        
        const healthResult = {
          success: true,
          health,
          timestamp: new Date().toISOString()
        };
        
        // Notify WebSocket clients of health update
        notifyHealthUpdate(healthResult);
        
        return healthResult;
        
      } catch (error) {
        console.error('❌ tRPC analytics getIntegrationHealth failed:', error);
        
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Errore durante recupero stato integrazioni',
          cause: error.message
        });
      }
    }),

});