/**
 * Business Repository - Timeline, Analytics & Business Intelligence
 * Replaces complex raw SQL queries with standardized Drizzle operations
 * Handles the critical Timeline Modal and Business Intelligence features
 */

import { db } from '../db/connection.js';
import { 
  executionEntity, 
  workflowEntity, 
  businessExecutionData, 
  businessAnalytics,
  users
} from '../db/schema.js';
import { eq, count, desc, sql, and, gte, lte, isNull, isNotNull } from 'drizzle-orm';

export class BusinessRepository {
  /**
   * Get Timeline Data for Modal
   * Replaces: Complex JOIN query in server.js /api/business/raw-data-for-modal
   * This is the CRITICAL query that powers the Timeline Modal feature
   */
  async getTimelineData(workflowId, executionId = null) {
    const selectFields = {
      // Execution core data
      executionId: executionEntity.id,
      workflowId: workflowEntity.id,
      workflowName: workflowEntity.name,
      startedAt: executionEntity.startedAt,
      stoppedAt: executionEntity.stoppedAt,
      status: executionEntity.status,
      finished: executionEntity.finished,
      mode: executionEntity.mode,
      
      // Essential data for Timeline processing
      executionData: executionEntity.executionData,
      workflowData: executionEntity.workflowData,
      customData: executionEntity.customData,
      metadata: executionEntity.metadata,
      
      // Workflow structure for Timeline rendering
      nodes: workflowEntity.nodes,
      connections: workflowEntity.connections,
      settings: workflowEntity.settings,
      
      // Performance metrics
      duration: sql`EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000`.mapWith(Number)
    };

    let query = db
      .select(selectFields)
      .from(executionEntity)
      .innerJoin(workflowEntity, eq(executionEntity.workflowId, workflowEntity.id))
      .where(eq(workflowEntity.id, workflowId));

    if (executionId) {
      // Specific execution requested
      query = query.where(
        and(
          eq(workflowEntity.id, workflowId),
          eq(executionEntity.id, executionId)
        )
      );
    } else {
      // Latest execution (default Timeline Modal behavior)
      query = query
        .orderBy(desc(executionEntity.startedAt))
        .limit(1);
    }

    const results = await query;
    return results[0] || null;
  }

  /**
   * Save Business Execution Data
   * Replaces: INSERT query in server.js extractBusinessData function
   * Critical for Business Intelligence data collection
   */
  async saveBusinessExecutionData(data) {
    const {
      executionId,
      workflowId,
      nodeId,
      nodeName,
      nodeType,
      businessCategory,
      businessData
    } = data;

    const results = await db
      .insert(businessExecutionData)
      .values({
        executionId: executionId.toString(),
        workflowId: workflowId.toString(),
        nodeId,
        nodeName,
        nodeType,
        businessCategory,
        businessData,
        executedAt: new Date(),
        isActive: true
      })
      .returning({ id: businessExecutionData.id });

    return results[0];
  }

  /**
   * Get Business Execution Data
   * Replaces: Raw SQL query in server.js getBusinessExecutionData function
   */
  async getBusinessExecutionData(workflowId, executionId = null, nodeType = null) {
    let query = db
      .select()
      .from(businessExecutionData)
      .where(eq(businessExecutionData.workflowId, workflowId.toString()));

    const conditions = [eq(businessExecutionData.workflowId, workflowId.toString())];
    
    if (executionId) {
      conditions.push(eq(businessExecutionData.executionId, executionId.toString()));
    }
    
    if (nodeType) {
      conditions.push(eq(businessExecutionData.nodeType, nodeType));
    }

    if (conditions.length > 1) {
      query = query.where(and(...conditions));
    }

    return await query
      .orderBy(desc(businessExecutionData.executedAt));
  }

  /**
   * Get Business Analytics
   * Replaces: Complex analytics queries scattered across multiple endpoints
   * Addresses DATA-001 technical debt (Business Analytics Storage)
   */
  async getBusinessAnalytics(workflowId) {
    const results = await db
      .select()
      .from(businessAnalytics)
      .where(eq(businessAnalytics.workflowId, workflowId.toString()))
      .limit(1);

    return results[0] || null;
  }

  /**
   * Update Business Analytics
   * Addresses DATA-001: Business Analytics Storage Implementation
   * This replaces the TODO in business-sanitizer.js:293
   */
  async updateBusinessAnalytics(workflowId, analyticsData) {
    const {
      executionCount = 0,
      successCount = 0,
      failureCount = 0,
      avgExecutionTime = 0,
      lastExecution = null
    } = analyticsData;

    // Check if analytics record exists
    const existing = await this.getBusinessAnalytics(workflowId);
    
    if (existing) {
      // Update existing record
      const results = await db
        .update(businessAnalytics)
        .set({
          executionCount,
          successCount,
          failureCount,
          avgExecutionTime,
          lastExecution,
          updatedAt: new Date()
        })
        .where(eq(businessAnalytics.workflowId, workflowId.toString()))
        .returning();
      
      return results[0];
    } else {
      // Create new record
      const results = await db
        .insert(businessAnalytics)
        .values({
          workflowId: workflowId.toString(),
          executionCount,
          successCount,
          failureCount,
          avgExecutionTime,
          lastExecution,
          createdAt: new Date(),
          updatedAt: new Date()
        })
        .returning();
      
      return results[0];
    }
  }

  /**
   * Calculate Business Analytics from Execution Data
   * Implements the missing analytics calculation for DATA-001
   */
  async calculateAndSaveBusinessAnalytics(workflowId, days = 30) {
    const cutoffDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    
    // Calculate analytics from execution data
    const analytics = await db
      .select({
        executionCount: count(),
        successCount: sql`COUNT(CASE WHEN ${executionEntity.finished} = true AND ${executionEntity.status} != 'error' THEN 1 END)`.mapWith(Number),
        failureCount: sql`COUNT(CASE WHEN ${executionEntity.finished} = false OR ${executionEntity.status} = 'error' THEN 1 END)`.mapWith(Number),
        avgExecutionTime: sql`AVG(EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000)`.mapWith(Number),
        lastExecution: sql`MAX(${executionEntity.startedAt})`.mapWith(Date)
      })
      .from(executionEntity)
      .where(
        and(
          eq(executionEntity.workflowId, workflowId),
          gte(executionEntity.startedAt, cutoffDate)
        )
      );

    const analyticsData = analytics[0];
    
    // Save to business_analytics table (resolves DATA-001)
    return await this.updateBusinessAnalytics(workflowId, analyticsData);
  }

  /**
   * Get Business Summary for Workflow
   * Replaces: generateBusinessSummary function in server.js
   */
  async getBusinessSummary(workflowId) {
    // Get workflow info with analytics
    const workflowInfo = await db
      .select({
        id: workflowEntity.id,
        name: workflowEntity.name,
        active: workflowEntity.active,
        createdAt: workflowEntity.createdAt,
        updatedAt: workflowEntity.updatedAt,
        nodes: workflowEntity.nodes,
        // Execution stats
        totalExecutions: sql`COUNT(${executionEntity.id})`.mapWith(Number),
        successfulExecutions: sql`COUNT(CASE WHEN ${executionEntity.finished} = true THEN 1 END)`.mapWith(Number),
        failedExecutions: sql`COUNT(CASE WHEN ${executionEntity.finished} = false THEN 1 END)`.mapWith(Number),
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
        workflowEntity.createdAt,
        workflowEntity.updatedAt,
        workflowEntity.nodes
      )
      .limit(1);

    const workflow = workflowInfo[0];
    if (!workflow) return null;

    // Calculate business metrics
    const successRate = workflow.totalExecutions > 0 
      ? (workflow.successfulExecutions / workflow.totalExecutions) * 100 
      : 0;

    // Determine business category based on workflow analysis
    const businessCategory = this.categorizeWorkflow(workflow);
    
    return {
      workflowId: workflow.id,
      name: workflow.name,
      active: workflow.active,
      businessCategory,
      performance: {
        totalExecutions: workflow.totalExecutions,
        successRate,
        avgDuration: workflow.avgDuration || 0,
        lastExecution: workflow.lastExecution
      },
      health: successRate >= 90 ? 'healthy' : successRate >= 70 ? 'warning' : 'critical',
      nodeCount: workflow.nodes ? workflow.nodes.length : 0
    };
  }

  /**
   * Categorize Workflow for Business Intelligence
   * Helper function for business classification
   */
  categorizeWorkflow(workflow) {
    if (!workflow.nodes || !Array.isArray(workflow.nodes)) {
      return 'general';
    }

    const nodeTypes = workflow.nodes.map(node => node.type);
    
    // Email-focused workflows
    if (nodeTypes.some(type => type.includes('email') || type.includes('mail'))) {
      return 'communication';
    }
    
    // Data processing workflows
    if (nodeTypes.some(type => 
      type.includes('spreadsheet') || 
      type.includes('csv') || 
      type.includes('json') || 
      type.includes('xml')
    )) {
      return 'data-processing';
    }
    
    // Integration workflows
    if (nodeTypes.some(type => 
      type.includes('webhook') || 
      type.includes('http') || 
      type.includes('api')
    )) {
      return 'integration';
    }
    
    // Automation workflows
    if (nodeTypes.some(type => 
      type.includes('schedule') || 
      type.includes('trigger') || 
      type.includes('cron')
    )) {
      return 'automation';
    }

    return 'general';
  }

  /**
   * Get Dashboard Business Overview
   * Replaces: Multiple dashboard queries in various endpoints
   */
  async getDashboardOverview() {
    // System statistics
    const systemStats = await db
      .select({
        totalWorkflows: sql`COUNT(DISTINCT ${workflowEntity.id})`.mapWith(Number),
        activeWorkflows: sql`COUNT(DISTINCT CASE WHEN ${workflowEntity.active} = true THEN ${workflowEntity.id} END)`.mapWith(Number),
        totalExecutions: sql`COUNT(${executionEntity.id})`.mapWith(Number),
        recentExecutions: sql`COUNT(CASE WHEN ${executionEntity.startedAt} >= NOW() - INTERVAL '24 hours' THEN 1 END)`.mapWith(Number),
        successfulExecutions: sql`COUNT(CASE WHEN ${executionEntity.finished} = true AND ${executionEntity.status} != 'error' THEN 1 END)`.mapWith(Number),
        avgExecutionTime: sql`AVG(EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000)`.mapWith(Number)
      })
      .from(workflowEntity)
      .leftJoin(executionEntity, eq(workflowEntity.id, executionEntity.workflowId));

    const stats = systemStats[0];
    const successRate = stats.totalExecutions > 0 
      ? (stats.successfulExecutions / stats.totalExecutions) * 100 
      : 0;

    return {
      workflows: {
        total: stats.totalWorkflows,
        active: stats.activeWorkflows,
        inactive: stats.totalWorkflows - stats.activeWorkflows
      },
      executions: {
        total: stats.totalExecutions,
        recent: stats.recentExecutions,
        successRate,
        avgDuration: stats.avgExecutionTime || 0
      },
      systemHealth: successRate >= 90 ? 'healthy' : successRate >= 70 ? 'warning' : 'critical'
    };
  }

  /**
   * Get Execution Performance Metrics
   * Addresses part of PERF-001 and PERF-002 technical debt
   * Note: Concurrent processing calculation still needs implementation
   */
  async getPerformanceMetrics(days = 7) {
    const cutoffDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    
    const metrics = await db
      .select({
        totalExecutions: count(),
        avgDuration: sql`AVG(EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000)`.mapWith(Number),
        minDuration: sql`MIN(EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000)`.mapWith(Number),
        maxDuration: sql`MAX(EXTRACT(EPOCH FROM (${executionEntity.stoppedAt} - ${executionEntity.startedAt})) * 1000)`.mapWith(Number),
        successRate: sql`
          ROUND(
            COUNT(CASE WHEN ${executionEntity.finished} = true THEN 1 END) * 100.0 / 
            NULLIF(COUNT(${executionEntity.id}), 0), 
            2
          )
        `.mapWith(Number),
        // TODO: Implement actual concurrent processing calculation (PERF-001)
        peakConcurrent: sql`0`.mapWith(Number), // Placeholder
        // TODO: Implement system load monitoring (PERF-002)
        systemLoad: sql`0`.mapWith(Number) // Placeholder
      })
      .from(executionEntity)
      .where(gte(executionEntity.startedAt, cutoffDate));

    return metrics[0] || {
      totalExecutions: 0,
      avgDuration: 0,
      minDuration: 0,
      maxDuration: 0,
      successRate: 0,
      peakConcurrent: 0, // PERF-001: TO BE IMPLEMENTED
      systemLoad: 0     // PERF-002: TO BE IMPLEMENTED
    };
  }

  /**
   * Search Business Execution Data
   * For Timeline filtering and business intelligence queries
   */
  async searchBusinessData(searchParams) {
    const {
      workflowId = null,
      nodeType = null,
      businessCategory = null,
      dateFrom = null,
      dateTo = null,
      limit = 100
    } = searchParams;

    let query = db
      .select({
        id: businessExecutionData.id,
        executionId: businessExecutionData.executionId,
        workflowId: businessExecutionData.workflowId,
        nodeId: businessExecutionData.nodeId,
        nodeName: businessExecutionData.nodeName,
        nodeType: businessExecutionData.nodeType,
        businessCategory: businessExecutionData.businessCategory,
        businessData: businessExecutionData.businessData,
        executedAt: businessExecutionData.executedAt,
        workflowName: workflowEntity.name
      })
      .from(businessExecutionData)
      .innerJoin(workflowEntity, eq(businessExecutionData.workflowId, workflowEntity.id));

    const conditions = [];
    
    if (workflowId) {
      conditions.push(eq(businessExecutionData.workflowId, workflowId.toString()));
    }
    
    if (nodeType) {
      conditions.push(eq(businessExecutionData.nodeType, nodeType));
    }
    
    if (businessCategory) {
      conditions.push(eq(businessExecutionData.businessCategory, businessCategory));
    }
    
    if (dateFrom) {
      conditions.push(gte(businessExecutionData.executedAt, dateFrom));
    }
    
    if (dateTo) {
      conditions.push(lte(businessExecutionData.executedAt, dateTo));
    }

    if (conditions.length > 0) {
      query = query.where(and(...conditions));
    }

    return await query
      .orderBy(desc(businessExecutionData.executedAt))
      .limit(limit);
  }
}