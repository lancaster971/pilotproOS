/**
 * Execution Repository - Standardized Data Access Layer
 * Replaces raw SQL queries with type-safe Drizzle ORM operations
 */

import { db } from '../db/connection.js';
import { executionEntity, workflowEntity, businessExecutionData } from '../db/schema.js';
import { eq, count, desc, sql, and, gte, lte, isNull, isNotNull, inArray, or } from 'drizzle-orm';

export class ExecutionRepository {
  /**
   * Get executions for a specific workflow
   * Replaces: Complex pagination queries in server.js
   */
  async getByWorkflowId(workflowId, options = {}) {
    const { limit = 50, offset = 0, status = null, dateFrom = null, dateTo = null } = options;
    
    let query = db
      .select({
        id: executionEntity.id,
        workflowId: executionEntity.workflowId,
        finished: executionEntity.finished,
        mode: executionEntity.mode,
        status: executionEntity.status,
        startedAt: executionEntity.startedAt,
        stoppedAt: executionEntity.stoppedAt,
        retryOf: executionEntity.retryOf,
        retrySuccessId: executionEntity.retrySuccessId,
        waitTill: executionEntity.waitTill,
        // Calculate duration
        duration: sql`EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000`.mapWith(Number),
        // Workflow info
        workflowName: workflowEntity.name
      })
      .from(executionEntity)
      .innerJoin(workflowEntity, eq(executionEntity.workflowId, workflowEntity.id))
      .where(eq(executionEntity.workflowId, workflowId));

    // Apply filters
    const conditions = [eq(executionEntity.workflowId, workflowId)];
    
    if (status) {
      conditions.push(eq(executionEntity.status, status));
    }
    
    if (dateFrom) {
      conditions.push(gte(executionEntity.startedAt, dateFrom));
    }
    
    if (dateTo) {
      conditions.push(lte(executionEntity.startedAt, dateTo));
    }

    if (conditions.length > 1) {
      query = query.where(and(...conditions));
    }

    return await query
      .orderBy(desc(executionEntity.startedAt))
      .limit(limit)
      .offset(offset);
  }

  /**
   * Get execution by ID with full details
   * Replaces: Raw SQL queries for execution details in server.js
   */
  async getById(executionId, includeWorkflowData = true) {
    const selectFields = {
      id: executionEntity.id,
      workflowId: executionEntity.workflowId,
      finished: executionEntity.finished,
      mode: executionEntity.mode,
      status: executionEntity.status,
      startedAt: executionEntity.startedAt,
      stoppedAt: executionEntity.stoppedAt,
      retryOf: executionEntity.retryOf,
      retrySuccessId: executionEntity.retrySuccessId,
      waitTill: executionEntity.waitTill,
      customData: executionEntity.customData,
      metadata: executionEntity.metadata,
      deletedAt: executionEntity.deletedAt,
      duration: sql`EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000`.mapWith(Number),
      // Workflow info
      workflowName: workflowEntity.name,
      workflowActive: workflowEntity.active
    };

    if (includeWorkflowData) {
      selectFields.workflowData = executionEntity.workflowData;
      selectFields.executionData = executionEntity.executionData;
      selectFields.workflowNodes = workflowEntity.nodes;
      selectFields.workflowConnections = workflowEntity.connections;
    }

    const results = await db
      .select(selectFields)
      .from(executionEntity)
      .innerJoin(workflowEntity, eq(executionEntity.workflowId, workflowEntity.id))
      .where(eq(executionEntity.id, executionId))
      .limit(1);

    return results[0] || null;
  }

  /**
   * Get latest execution for a workflow
   * Replaces: Raw SQL in timeline modal and server endpoints
   */
  async getLatestByWorkflowId(workflowId, includeData = false) {
    const selectFields = {
      id: executionEntity.id,
      workflowId: executionEntity.workflowId,
      finished: executionEntity.finished,
      mode: executionEntity.mode,
      status: executionEntity.status,
      startedAt: executionEntity.startedAt,
      stoppedAt: executionEntity.stoppedAt,
      duration: sql`EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000`.mapWith(Number),
      workflowName: workflowEntity.name
    };

    if (includeData) {
      selectFields.executionData = executionEntity.executionData;
      selectFields.workflowData = executionEntity.workflowData;
      selectFields.workflowNodes = workflowEntity.nodes;
    }

    const results = await db
      .select(selectFields)
      .from(executionEntity)
      .innerJoin(workflowEntity, eq(executionEntity.workflowId, workflowEntity.id))
      .where(eq(executionEntity.workflowId, workflowId))
      .orderBy(desc(executionEntity.startedAt))
      .limit(1);

    return results[0] || null;
  }

  /**
   * Get execution statistics by workflow
   * Replaces: Complex GROUP BY queries in multiple files
   */
  async getStatsByWorkflowId(workflowId, days = 30) {
    const cutoffDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    
    const results = await db
      .select({
        workflowId: executionEntity.workflowId,
        totalExecutions: count(),
        successfulExecutions: sql`COUNT(CASE WHEN ${executionEntity.finished} = true AND ${executionEntity.status} != 'error' THEN 1 END)`.mapWith(Number),
        failedExecutions: sql`COUNT(CASE WHEN ${executionEntity.finished} = false OR ${executionEntity.status} = 'error' THEN 1 END)`.mapWith(Number),
        runningExecutions: sql`COUNT(CASE WHEN ${executionEntity.finished} = false AND ${executionEntity.status} != 'error' THEN 1 END)`.mapWith(Number),
        avgDuration: sql`AVG(EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000)`.mapWith(Number),
        minDuration: sql`MIN(EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000)`.mapWith(Number),
        maxDuration: sql`MAX(EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000)`.mapWith(Number),
        firstExecution: sql`MIN(${executionEntity.startedAt})`.mapWith(Date),
        lastExecution: sql`MAX(${executionEntity.startedAt})`.mapWith(Date),
        // Calculate peak concurrent executions
        peakConcurrent: sql`(
          SELECT COUNT(*)
          FROM ${executionEntity} e2
          WHERE e2."workflowId" = ${executionEntity.workflowId}
          AND e2."startedAt" >= ${cutoffDate}
          AND EXISTS (
            SELECT 1 FROM ${executionEntity} e3
            WHERE e3.id != e2.id
            AND e3."workflowId" = e2."workflowId"
            AND e3."startedAt" <= e2."stoppedAt"
            AND e3."stoppedAt" >= e2."startedAt"
          )
        )`.mapWith(Number)
      })
      .from(executionEntity)
      .where(
        and(
          eq(executionEntity.workflowId, workflowId),
          gte(executionEntity.startedAt, cutoffDate)
        )
      )
      .groupBy(executionEntity.workflowId)
      .limit(1);

    const stats = results[0];
    if (!stats) {
      return {
        workflowId,
        totalExecutions: 0,
        successfulExecutions: 0,
        failedExecutions: 0,
        runningExecutions: 0,
        avgDuration: 0,
        minDuration: 0,
        maxDuration: 0,
        firstExecution: null,
        lastExecution: null,
        peakConcurrent: 0,
        successRate: 0
      };
    }

    // Calculate success rate
    const successRate = stats.totalExecutions > 0 
      ? (stats.successfulExecutions / stats.totalExecutions) * 100 
      : 0;

    return {
      ...stats,
      successRate
    };
  }

  /**
   * Get recent executions across all workflows
   * Replaces: Dashboard queries in server endpoints
   */
  async getRecent(limit = 20, includeWorkflowInfo = true) {
    const selectFields = {
      id: executionEntity.id,
      workflowId: executionEntity.workflowId,
      finished: executionEntity.finished,
      mode: executionEntity.mode,
      status: executionEntity.status,
      startedAt: executionEntity.startedAt,
      stoppedAt: executionEntity.stoppedAt,
      duration: sql`EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000`.mapWith(Number)
    };

    if (includeWorkflowInfo) {
      selectFields.workflowName = workflowEntity.name;
      selectFields.workflowActive = workflowEntity.active;
    }

    const query = includeWorkflowInfo
      ? db
          .select(selectFields)
          .from(executionEntity)
          .innerJoin(workflowEntity, eq(executionEntity.workflowId, workflowEntity.id))
      : db
          .select(selectFields)
          .from(executionEntity);

    return await query
      .orderBy(desc(executionEntity.startedAt))
      .limit(limit);
  }

  /**
   * Get executions by status
   * Replaces: Status filtering queries
   */
  async getByStatus(status, limit = 50) {
    return await db
      .select({
        id: executionEntity.id,
        workflowId: executionEntity.workflowId,
        finished: executionEntity.finished,
        mode: executionEntity.mode,
        status: executionEntity.status,
        startedAt: executionEntity.startedAt,
        stoppedAt: executionEntity.stoppedAt,
        workflowName: workflowEntity.name,
        duration: sql`EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000`.mapWith(Number)
      })
      .from(executionEntity)
      .innerJoin(workflowEntity, eq(executionEntity.workflowId, workflowEntity.id))
      .where(eq(executionEntity.status, status))
      .orderBy(desc(executionEntity.startedAt))
      .limit(limit);
  }

  /**
   * Get running executions
   * Replaces: Monitoring queries for active processes
   */
  async getRunning() {
    return await db
      .select({
        id: executionEntity.id,
        workflowId: executionEntity.workflowId,
        mode: executionEntity.mode,
        startedAt: executionEntity.startedAt,
        waitTill: executionEntity.waitTill,
        workflowName: workflowEntity.name,
        workflowActive: workflowEntity.active,
        runningDuration: sql`EXTRACT(EPOCH FROM (NOW() - ${executionEntity.startedAt})) * 1000`.mapWith(Number)
      })
      .from(executionEntity)
      .innerJoin(workflowEntity, eq(executionEntity.workflowId, workflowEntity.id))
      .where(
        and(
          eq(executionEntity.finished, false),
          isNull(executionEntity.stoppedAt)
        )
      )
      .orderBy(executionEntity.startedAt);
  }

  /**
   * Get execution count by date range
   * Replaces: Analytics queries for charts and dashboards
   */
  async getCountByDateRange(startDate, endDate, groupBy = 'day') {
    const truncFunction = groupBy === 'hour' ? 'hour' : 'day';
    
    return await db
      .select({
        date: sql`DATE_TRUNC('${sql.raw(truncFunction)}', ${executionEntity.startedAt})`.mapWith(Date),
        totalExecutions: count(),
        successfulExecutions: sql`COUNT(CASE WHEN ${executionEntity.finished} = true AND ${executionEntity.status} != 'error' THEN 1 END)`.mapWith(Number),
        failedExecutions: sql`COUNT(CASE WHEN ${executionEntity.finished} = false OR ${executionEntity.status} = 'error' THEN 1 END)`.mapWith(Number)
      })
      .from(executionEntity)
      .where(
        and(
          gte(executionEntity.startedAt, startDate),
          lte(executionEntity.startedAt, endDate)
        )
      )
      .groupBy(sql`DATE_TRUNC('${sql.raw(truncFunction)}', ${executionEntity.startedAt})`)
      .orderBy(sql`DATE_TRUNC('${sql.raw(truncFunction)}', ${executionEntity.startedAt})`);
  }

  /**
   * Get system-wide execution statistics
   * Replaces: Dashboard analytics queries
   */
  async getSystemStats(days = 30) {
    const cutoffDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    
    const results = await db
      .select({
        totalExecutions: count(),
        successfulExecutions: sql`COUNT(CASE WHEN ${executionEntity.finished} = true AND ${executionEntity.status} != 'error' THEN 1 END)`.mapWith(Number),
        failedExecutions: sql`COUNT(CASE WHEN ${executionEntity.finished} = false OR ${executionEntity.status} = 'error' THEN 1 END)`.mapWith(Number),
        runningExecutions: sql`COUNT(CASE WHEN ${executionEntity.finished} = false AND ${executionEntity.status} != 'error' THEN 1 END)`.mapWith(Number),
        avgDuration: sql`AVG(EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000)`.mapWith(Number),
        uniqueWorkflows: sql`COUNT(DISTINCT ${executionEntity.workflowId})`.mapWith(Number),
        firstExecution: sql`MIN(${executionEntity.startedAt})`.mapWith(Date),
        lastExecution: sql`MAX(${executionEntity.startedAt})`.mapWith(Date)
      })
      .from(executionEntity)
      .where(gte(executionEntity.startedAt, cutoffDate));

    const stats = results[0];
    const successRate = stats.totalExecutions > 0 
      ? (stats.successfulExecutions / stats.totalExecutions) * 100 
      : 0;

    return {
      ...stats,
      successRate
    };
  }

  /**
   * Get failed executions for monitoring
   * Replaces: Error monitoring queries
   */
  async getFailedExecutions(limit = 50, workflowId = null) {
    let query = db
      .select({
        id: executionEntity.id,
        workflowId: executionEntity.workflowId,
        mode: executionEntity.mode,
        status: executionEntity.status,
        startedAt: executionEntity.startedAt,
        stoppedAt: executionEntity.stoppedAt,
        retryOf: executionEntity.retryOf,
        workflowName: workflowEntity.name,
        duration: sql`EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000`.mapWith(Number)
      })
      .from(executionEntity)
      .innerJoin(workflowEntity, eq(executionEntity.workflowId, workflowEntity.id));

    if (workflowId) {
      query = query.where(
        and(
          eq(executionEntity.workflowId, workflowId),
          or(
            eq(executionEntity.status, 'error'),
            and(eq(executionEntity.finished, false), isNotNull(executionEntity.stoppedAt))
          )
        )
      );
    } else {
      query = query.where(
        or(
          eq(executionEntity.status, 'error'),
          and(eq(executionEntity.finished, false), isNotNull(executionEntity.stoppedAt))
        )
      );
    }

    return await query
      .orderBy(desc(executionEntity.startedAt))
      .limit(limit);
  }

  /**
   * Delete old executions (cleanup)
   * Replaces: Maintenance queries
   */
  async deleteOlderThan(days) {
    const cutoffDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    
    const deletedRows = await db
      .delete(executionEntity)
      .where(lte(executionEntity.startedAt, cutoffDate))
      .returning({ id: executionEntity.id });

    return deletedRows.length;
  }
}