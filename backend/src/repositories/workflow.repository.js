/**
 * Workflow Repository - Standardized Data Access Layer
 * Replaces raw SQL queries with type-safe Drizzle ORM operations
 */

import { db } from '../db/connection.js';
import { workflowEntity, executionEntity, businessAnalytics } from '../db/schema.js';
import { eq, count, desc, sql, and, gte, lte, isNull, isNotNull } from 'drizzle-orm';

export class WorkflowRepository {
  /**
   * Get all workflows with execution analytics
   * Replaces: Raw SQL with complex JOIN and GROUP BY
   */
  async getAllWithAnalytics() {
    return await db
      .select({
        id: workflowEntity.id,
        name: workflowEntity.name,
        active: workflowEntity.active,
        createdAt: workflowEntity.createdAt,
        updatedAt: workflowEntity.updatedAt,
        versionId: workflowEntity.versionId,
        nodes: workflowEntity.nodes,
        connections: workflowEntity.connections,
        settings: workflowEntity.settings,
        // Aggregated execution data
        executionCount: sql`COUNT(${executionEntity.id})`.mapWith(Number),
        successCount: sql`COUNT(CASE WHEN ${executionEntity.finished} = true THEN 1 END)`.mapWith(Number),
        failureCount: sql`COUNT(CASE WHEN ${executionEntity.finished} = false THEN 1 END)`.mapWith(Number),
        lastExecution: sql`MAX(${executionEntity.startedAt})`.mapWith(Date),
        // Performance metrics
        avgDuration: sql`AVG(EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000)`.mapWith(Number)
      })
      .from(workflowEntity)
      .leftJoin(executionEntity, eq(workflowEntity.id, executionEntity.workflowId))
      .groupBy(
        workflowEntity.id,
        workflowEntity.name,
        workflowEntity.active,
        workflowEntity.createdAt,
        workflowEntity.updatedAt,
        workflowEntity.versionId,
        workflowEntity.nodes,
        workflowEntity.connections,
        workflowEntity.settings
      )
      .orderBy(desc(workflowEntity.updatedAt));
  }

  /**
   * Get active workflows only with basic analytics
   * Replaces: Multiple raw SQL queries in server.js endpoints
   */
  async getActiveWithAnalytics() {
    return await db
      .select({
        id: workflowEntity.id,
        name: workflowEntity.name,
        active: workflowEntity.active,
        createdAt: workflowEntity.createdAt,
        updatedAt: workflowEntity.updatedAt,
        executionCount: sql`COUNT(${executionEntity.id})`.mapWith(Number),
        lastExecution: sql`MAX(${executionEntity.startedAt})`.mapWith(Date)
      })
      .from(workflowEntity)
      .leftJoin(executionEntity, eq(workflowEntity.id, executionEntity.workflowId))
      .where(eq(workflowEntity.active, true))
      .groupBy(
        workflowEntity.id,
        workflowEntity.name,
        workflowEntity.active,
        workflowEntity.createdAt,
        workflowEntity.updatedAt
      )
      .orderBy(desc(workflowEntity.updatedAt));
  }

  /**
   * Get workflow by ID with full details
   * Replaces: Simple SELECT queries in server.js
   */
  async getById(workflowId) {
    const results = await db
      .select()
      .from(workflowEntity)
      .where(eq(workflowEntity.id, workflowId))
      .limit(1);
    
    return results[0] || null;
  }

  /**
   * Get workflow by ID with execution analytics
   * Replaces: Complex JOIN queries in multiple endpoints
   */
  async getByIdWithAnalytics(workflowId) {
    const results = await db
      .select({
        // Workflow data
        id: workflowEntity.id,
        name: workflowEntity.name,
        active: workflowEntity.active,
        nodes: workflowEntity.nodes,
        connections: workflowEntity.connections,
        settings: workflowEntity.settings,
        staticData: workflowEntity.staticData,
        createdAt: workflowEntity.createdAt,
        updatedAt: workflowEntity.updatedAt,
        versionId: workflowEntity.versionId,
        // Execution analytics
        executionCount: sql`COUNT(${executionEntity.id})`.mapWith(Number),
        successCount: sql`COUNT(CASE WHEN ${executionEntity.finished} = true THEN 1 END)`.mapWith(Number),
        failureCount: sql`COUNT(CASE WHEN ${executionEntity.finished} = false THEN 1 END)`.mapWith(Number),
        lastExecution: sql`MAX(${executionEntity.startedAt})`.mapWith(Date),
        avgDuration: sql`AVG(EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000)`.mapWith(Number)
      })
      .from(workflowEntity)
      .leftJoin(executionEntity, eq(workflowEntity.id, executionEntity.workflowId))
      .where(eq(workflowEntity.id, workflowId))
      .groupBy(
        workflowEntity.id,
        workflowEntity.name,
        workflowEntity.active,
        workflowEntity.nodes,
        workflowEntity.connections,
        workflowEntity.settings,
        workflowEntity.staticData,
        workflowEntity.createdAt,
        workflowEntity.updatedAt,
        workflowEntity.versionId
      )
      .limit(1);

    return results[0] || null;
  }

  /**
   * Update workflow active status
   * Replaces: Raw UPDATE queries in server.js
   */
  async updateActiveStatus(workflowId, active) {
    const results = await db
      .update(workflowEntity)
      .set({ 
        active, 
        updatedAt: new Date() 
      })
      .where(eq(workflowEntity.id, workflowId))
      .returning({
        id: workflowEntity.id,
        name: workflowEntity.name,
        active: workflowEntity.active
      });

    return results[0] || null;
  }

  /**
   * Get workflows created in date range
   * Replaces: Raw SQL with date filtering
   */
  async getByDateRange(startDate, endDate) {
    return await db
      .select()
      .from(workflowEntity)
      .where(
        and(
          gte(workflowEntity.createdAt, startDate),
          lte(workflowEntity.createdAt, endDate)
        )
      )
      .orderBy(desc(workflowEntity.createdAt));
  }

  /**
   * Get workflow statistics for dashboard
   * Replaces: Complex analytics queries in system endpoints
   */
  async getStatistics() {
    const stats = await db
      .select({
        totalWorkflows: count(),
        activeWorkflows: sql`COUNT(CASE WHEN ${workflowEntity.active} = true THEN 1 END)`.mapWith(Number),
        inactiveWorkflows: sql`COUNT(CASE WHEN ${workflowEntity.active} = false THEN 1 END)`.mapWith(Number),
        archivedWorkflows: sql`COUNT(CASE WHEN ${workflowEntity.isArchived} = true THEN 1 END)`.mapWith(Number)
      })
      .from(workflowEntity);

    return stats[0];
  }

  /**
   * Search workflows by name
   * Replaces: Raw SQL with LIKE queries
   */
  async searchByName(searchTerm) {
    return await db
      .select({
        id: workflowEntity.id,
        name: workflowEntity.name,
        active: workflowEntity.active,
        createdAt: workflowEntity.createdAt,
        updatedAt: workflowEntity.updatedAt
      })
      .from(workflowEntity)
      .where(sql`${workflowEntity.name} ILIKE ${`%${searchTerm}%`}`)
      .orderBy(desc(workflowEntity.updatedAt))
      .limit(50);
  }

  /**
   * Get workflows with recent executions
   * Replaces: Complex temporal queries in server.js
   */
  async getWithRecentExecutions(hours = 24) {
    const cutoffDate = new Date(Date.now() - hours * 60 * 60 * 1000);
    
    return await db
      .select({
        id: workflowEntity.id,
        name: workflowEntity.name,
        active: workflowEntity.active,
        recentExecutions: sql`COUNT(${executionEntity.id})`.mapWith(Number),
        lastExecution: sql`MAX(${executionEntity.startedAt})`.mapWith(Date)
      })
      .from(workflowEntity)
      .leftJoin(
        executionEntity, 
        and(
          eq(workflowEntity.id, executionEntity.workflowId),
          gte(executionEntity.startedAt, cutoffDate)
        )
      )
      .groupBy(
        workflowEntity.id,
        workflowEntity.name,
        workflowEntity.active
      )
      .having(sql`COUNT(${executionEntity.id}) > 0`)
      .orderBy(desc(sql`MAX(${executionEntity.startedAt})`));
  }

  /**
   * Get workflow health status
   * Replaces: Business logic calculations scattered in multiple files
   */
  async getHealthStatus(workflowId, days = 7) {
    const cutoffDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    
    const results = await db
      .select({
        workflowId: workflowEntity.id,
        workflowName: workflowEntity.name,
        active: workflowEntity.active,
        totalExecutions: sql`COUNT(${executionEntity.id})`.mapWith(Number),
        successfulExecutions: sql`COUNT(CASE WHEN ${executionEntity.finished} = true THEN 1 END)`.mapWith(Number),
        failedExecutions: sql`COUNT(CASE WHEN ${executionEntity.finished} = false THEN 1 END)`.mapWith(Number),
        avgDuration: sql`AVG(EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000)`.mapWith(Number),
        lastExecution: sql`MAX(${executionEntity.startedAt})`.mapWith(Date)
      })
      .from(workflowEntity)
      .leftJoin(
        executionEntity,
        and(
          eq(workflowEntity.id, executionEntity.workflowId),
          gte(executionEntity.startedAt, cutoffDate)
        )
      )
      .where(eq(workflowEntity.id, workflowId))
      .groupBy(
        workflowEntity.id,
        workflowEntity.name,
        workflowEntity.active
      )
      .limit(1);

    const stats = results[0];
    if (!stats) return null;

    // Calculate health metrics
    const successRate = stats.totalExecutions > 0 
      ? (stats.successfulExecutions / stats.totalExecutions) * 100 
      : 0;

    let healthStatus;
    if (successRate >= 95) healthStatus = 'Excellent';
    else if (successRate >= 80) healthStatus = 'Good';
    else if (successRate >= 60) healthStatus = 'Needs Attention';
    else healthStatus = 'Critical';

    return {
      ...stats,
      successRate,
      healthStatus,
      isActive: Boolean(stats.active)
    };
  }
}