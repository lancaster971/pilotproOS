import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { router, businessProcedure } from '../trpc.js';

/**
 * Executions Router - Process Runs & Timeline Management
 * Migrates execution-related endpoints to tRPC
 */

export const executionsRouter = router({
  
  /**
   * Get process runs (executions)
   * Equivalent to: GET /api/business/process-runs
   */
  getProcessRuns: businessProcedure
    .input(z.object({
      limit: z.number().optional().default(50),
      offset: z.number().optional().default(0),
      workflowId: z.string().optional()
    }))
    .query(async ({ input, ctx }) => {
      const { limit, offset, workflowId } = input;
      
      console.log(`🏃 tRPC: Getting process runs (limit=${limit}, offset=${offset}, workflowId=${workflowId || 'all'})`);
      
      try {
        let whereClause = 'WHERE w."isArchived" = false';
        let queryParams = [limit, offset];
        
        if (workflowId) {
          whereClause += ' AND e."workflowId" = $3';
          queryParams.push(workflowId);
        }
        
        const executionsQuery = `
          SELECT 
            e.id as execution_id,
            e."workflowId" as workflow_id,
            w.name as workflow_name,
            e.status,
            e."startedAt" as started_at,
            e."stoppedAt" as stopped_at,
            e.mode,
            e."workflowData",
            EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) * 1000 as duration_ms
          FROM n8n.execution_entity e
          LEFT JOIN n8n.workflow_entity w ON e."workflowId" = w.id
          ${whereClause}
          ORDER BY e."startedAt" DESC
          LIMIT $1 OFFSET $2
        `;
        
        const result = await ctx.dbPool.query(executionsQuery, queryParams);
        
        // Also get total count
        const countQuery = `
          SELECT COUNT(*) as total
          FROM n8n.execution_entity e
          LEFT JOIN n8n.workflow_entity w ON e."workflowId" = w.id
          ${whereClause}
        `;
        const countParams = workflowId ? [workflowId] : [];
        const countResult = await ctx.dbPool.query(countQuery, countParams);
        
        const executions = result.rows.map(row => ({
          id: row.execution_id,
          workflowId: row.workflow_id,
          workflowName: row.workflow_name || 'Unknown Process',
          status: row.status,
          startedAt: row.started_at,
          stoppedAt: row.stopped_at,
          duration: Math.round(row.duration_ms || 0),
          mode: row.mode,
          hasWorkflowData: !!row.workflowData
        }));
        
        const total = parseInt(countResult.rows[0].total) || 0;
        
        console.log(`✅ tRPC: Found ${executions.length} executions (${total} total)`);
        
        return {
          success: true,
          executions,
          pagination: {
            total,
            limit,
            offset,
            hasMore: (offset + limit) < total
          }
        };
        
      } catch (error) {
        console.error('❌ tRPC executions getProcessRuns failed:', error);
        
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Errore durante recupero esecuzioni processi',
          cause: error.message
        });
      }
    }),

  /**
   * Get process timeline for specific process
   * Equivalent to: GET /api/business/process-timeline/:processId
   */
  getProcessTimeline: businessProcedure
    .input(z.object({
      processId: z.string().min(1, 'Process ID è richiesto')
    }))
    .query(async ({ input, ctx }) => {
      const { processId } = input;
      
      console.log(`📅 tRPC: Getting timeline for process ID=${processId}`);
      
      try {
        // Get workflow info
        const workflowResult = await ctx.dbPool.query(`
          SELECT id, name, active 
          FROM n8n.workflow_entity 
          WHERE id = $1 AND "isArchived" = false
        `, [processId]);
        
        if (workflowResult.rows.length === 0) {
          throw new TRPCError({
            code: 'NOT_FOUND',
            message: 'Business Process non trovato'
          });
        }
        
        const workflow = workflowResult.rows[0];
        
        // Get recent executions for timeline
        const timelineResult = await ctx.dbPool.query(`
          SELECT 
            e.id as execution_id,
            e.status,
            e."startedAt" as started_at,
            e."stoppedAt" as stopped_at,
            e.mode,
            EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) * 1000 as duration_ms
          FROM n8n.execution_entity e
          WHERE e."workflowId" = $1
          ORDER BY e."startedAt" DESC
          LIMIT 50
        `, [processId]);
        
        // Get business execution data if available
        const businessDataResult = await ctx.dbPool.query(`
          SELECT *
          FROM pilotpros.business_execution_data
          WHERE workflow_id = $1
          ORDER BY execution_date DESC
          LIMIT 10
        `, [processId]);
        
        const timeline = timelineResult.rows.map(row => ({
          executionId: row.execution_id,
          status: row.status,
          startedAt: row.started_at,
          stoppedAt: row.stopped_at,
          duration: Math.round(row.duration_ms || 0),
          mode: row.mode
        }));
        
        const businessData = businessDataResult.rows.map(row => ({
          executionId: row.execution_id,
          nodeType: row.node_type,
          businessContent: row.business_content,
          executionDate: row.execution_date
        }));
        
        console.log(`✅ tRPC: Timeline retrieved - ${timeline.length} executions, ${businessData.length} business records`);
        
        return {
          success: true,
          process: {
            id: workflow.id,
            name: workflow.name,
            active: workflow.active
          },
          timeline,
          businessData,
          stats: {
            totalExecutions: timeline.length,
            successfulExecutions: timeline.filter(t => t.status === 'success').length,
            averageDuration: timeline.length > 0 
              ? Math.round(timeline.reduce((sum, t) => sum + t.duration, 0) / timeline.length)
              : 0
          }
        };
        
      } catch (error) {
        console.error('❌ tRPC executions getProcessTimeline failed:', error);
        
        if (error instanceof TRPCError) throw error;
        
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Errore durante recupero timeline processo',
          cause: error.message
        });
      }
    }),

  /**
   * Get process timeline report
   * Equivalent to: GET /api/business/process-timeline/:processId/report
   */
  getTimelineReport: businessProcedure
    .input(z.object({
      processId: z.string().min(1, 'Process ID è richiesto'),
      days: z.number().optional().default(30)
    }))
    .query(async ({ input, ctx }) => {
      const { processId, days } = input;
      
      console.log(`📊 tRPC: Getting timeline report for process ID=${processId} (${days} days)`);
      
      try {
        // Get workflow info
        const workflowResult = await ctx.dbPool.query(`
          SELECT id, name 
          FROM n8n.workflow_entity 
          WHERE id = $1 AND "isArchived" = false
        `, [processId]);
        
        if (workflowResult.rows.length === 0) {
          throw new TRPCError({
            code: 'NOT_FOUND',
            message: 'Business Process non trovato'
          });
        }
        
        const workflow = workflowResult.rows[0];
        
        // Get execution statistics for the period
        const statsResult = await ctx.dbPool.query(`
          SELECT 
            COUNT(*) as total_executions,
            COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_executions,
            COUNT(CASE WHEN status = 'error' THEN 1 END) as failed_executions,
            AVG(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt")) * 1000) as avg_duration_ms,
            MIN("startedAt") as first_execution,
            MAX("startedAt") as last_execution
          FROM n8n.execution_entity
          WHERE "workflowId" = $1 
            AND "startedAt" >= NOW() - INTERVAL '${days} days'
        `, [processId]);
        
        // Get daily execution trend
        const trendResult = await ctx.dbPool.query(`
          SELECT 
            DATE("startedAt") as execution_date,
            COUNT(*) as execution_count,
            COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count,
            AVG(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt")) * 1000) as avg_duration_ms
          FROM n8n.execution_entity
          WHERE "workflowId" = $1 
            AND "startedAt" >= NOW() - INTERVAL '${days} days'
          GROUP BY DATE("startedAt")
          ORDER BY execution_date ASC
        `, [processId]);
        
        const stats = statsResult.rows[0];
        const successRate = stats.total_executions > 0 
          ? Math.round((stats.successful_executions / stats.total_executions) * 100)
          : 0;
        
        const report = {
          process: {
            id: workflow.id,
            name: workflow.name
          },
          period: {
            days,
            firstExecution: stats.first_execution,
            lastExecution: stats.last_execution
          },
          summary: {
            totalExecutions: parseInt(stats.total_executions) || 0,
            successfulExecutions: parseInt(stats.successful_executions) || 0,
            failedExecutions: parseInt(stats.failed_executions) || 0,
            successRate,
            averageDuration: Math.round(stats.avg_duration_ms || 0)
          },
          trend: trendResult.rows.map(row => ({
            date: row.execution_date,
            executions: parseInt(row.execution_count),
            successCount: parseInt(row.success_count),
            avgDuration: Math.round(row.avg_duration_ms || 0)
          }))
        };
        
        console.log(`✅ tRPC: Timeline report - ${report.summary.totalExecutions} executions, ${successRate}% success rate`);
        
        return {
          success: true,
          report
        };
        
      } catch (error) {
        console.error('❌ tRPC executions getTimelineReport failed:', error);
        
        if (error instanceof TRPCError) throw error;
        
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Errore durante generazione report timeline',
          cause: error.message
        });
      }
    }),

  /**
   * Get raw data for modal
   * Equivalent to: GET /api/business/raw-data-for-modal/:workflowId
   */
  getRawDataForModal: businessProcedure
    .input(z.object({
      workflowId: z.string().min(1, 'Workflow ID è richiesto')
    }))
    .query(async ({ input, ctx }) => {
      const { workflowId } = input;
      
      console.log(`🔍 tRPC: Getting raw data for modal - workflowId=${workflowId}`);
      
      try {
        // Get latest execution data
        const executionResult = await ctx.dbPool.query(`
          SELECT 
            id,
            status,
            "startedAt",
            "stoppedAt",
            "workflowData"
          FROM n8n.execution_entity
          WHERE "workflowId" = $1
          ORDER BY "startedAt" DESC
          LIMIT 1
        `, [workflowId]);
        
        // Get business execution data
        const businessResult = await ctx.dbPool.query(`
          SELECT *
          FROM pilotpros.business_execution_data
          WHERE workflow_id = $1
          ORDER BY execution_date DESC
          LIMIT 10
        `, [workflowId]);
        
        const latestExecution = executionResult.rows[0] || null;
        const businessData = businessResult.rows || [];
        
        console.log(`✅ tRPC: Raw data retrieved - ${businessData.length} business records`);
        
        return {
          success: true,
          latestExecution,
          businessData,
          workflowId
        };
        
      } catch (error) {
        console.error('❌ tRPC executions getRawDataForModal failed:', error);
        
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Errore durante recupero dati raw per modal',
          cause: error.message
        });
      }
    }),

});