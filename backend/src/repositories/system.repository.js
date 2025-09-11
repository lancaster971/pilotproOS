/**
 * System Repository - Health, Settings, Users & System Operations
 * Replaces raw SQL queries in system endpoints
 */

import { db } from '../db/connection.js';
import { 
  users, 
  systemSettings, 
  auditLogs, 
  userSessions,
  workflowEntity,
  executionEntity
} from '../db/schema.js';
import { eq, count, desc, sql, and, gte, lte, isNull, ne } from 'drizzle-orm';

export class SystemRepository {
  /**
   * Get System Health Status
   * Replaces: Health check queries in server.js endpoints
   */
  async getHealthStatus() {
    try {
      // Test database connectivity
      const dbTest = await db
        .select({ currentTime: sql`NOW()`.mapWith(Date) })
        .limit(1);
      
      const dbHealthy = dbTest.length > 0;
      
      // Check n8n schema accessibility
      const n8nTest = await db
        .select({ 
          workflowCount: sql`COUNT(*)`.mapWith(Number) 
        })
        .from(workflowEntity)
        .limit(1);
        
      const n8nHealthy = n8nTest.length > 0;
      
      // Get system statistics
      const systemStats = await this.getSystemStatistics();
      
      return {
        status: (dbHealthy && n8nHealthy) ? 'healthy' : 'unhealthy',
        database: {
          status: dbHealthy ? 'connected' : 'disconnected',
          timestamp: dbTest[0]?.currentTime || null
        },
        n8nSchema: {
          status: n8nHealthy ? 'accessible' : 'inaccessible',
          workflowCount: n8nTest[0]?.workflowCount || 0
        },
        ...systemStats
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        database: { status: 'error', error: error.message },
        n8nSchema: { status: 'error' }
      };
    }
  }

  /**
   * Get System Statistics
   * Replaces: Statistics queries scattered across system endpoints
   */
  async getSystemStatistics() {
    const [workflowStats, executionStats, userStats] = await Promise.all([
      // Workflow statistics
      db
        .select({
          totalWorkflows: count(),
          activeWorkflows: sql`COUNT(CASE WHEN ${workflowEntity.active} = true THEN 1 END)`.mapWith(Number),
          inactiveWorkflows: sql`COUNT(CASE WHEN ${workflowEntity.active} = false THEN 1 END)`.mapWith(Number)
        })
        .from(workflowEntity),
        
      // Execution statistics  
      db
        .select({
          totalExecutions: count(),
          recentExecutions: sql`COUNT(CASE WHEN ${executionEntity.startedAt} >= NOW() - INTERVAL '24 hours' THEN 1 END)`.mapWith(Number),
          runningExecutions: sql`COUNT(CASE WHEN ${executionEntity.finished} = false THEN 1 END)`.mapWith(Number)
        })
        .from(executionEntity),
        
      // User statistics
      db
        .select({
          totalUsers: count(),
          activeUsers: sql`COUNT(CASE WHEN ${users.isActive} = true THEN 1 END)`.mapWith(Number)
        })
        .from(users)
    ]);

    return {
      workflows: workflowStats[0],
      executions: executionStats[0], 
      users: userStats[0],
      timestamp: new Date()
    };
  }

  /**
   * User Management Operations
   * Replaces: User queries in authentication controllers
   */
  async getUserById(userId) {
    const results = await db
      .select({
        id: users.id,
        username: users.username,
        email: users.email,
        role: users.role,
        isActive: users.isActive,
        createdAt: users.createdAt,
        updatedAt: users.updatedAt,
        lastLogin: users.lastLogin,
        settings: users.settings
      })
      .from(users)
      .where(eq(users.id, userId))
      .limit(1);

    return results[0] || null;
  }

  async getUserByEmail(email) {
    const results = await db
      .select()
      .from(users)
      .where(eq(users.email, email))
      .limit(1);

    return results[0] || null;
  }

  async getUserByUsername(username) {
    const results = await db
      .select()
      .from(users)
      .where(eq(users.username, username))
      .limit(1);

    return results[0] || null;
  }

  async getAllUsers(includeInactive = false) {
    let query = db
      .select({
        id: users.id,
        username: users.username,
        email: users.email,
        role: users.role,
        isActive: users.isActive,
        createdAt: users.createdAt,
        updatedAt: users.updatedAt,
        lastLogin: users.lastLogin
      })
      .from(users);

    if (!includeInactive) {
      query = query.where(eq(users.isActive, true));
    }

    return await query.orderBy(desc(users.createdAt));
  }

  async createUser(userData) {
    const results = await db
      .insert(users)
      .values({
        username: userData.username,
        email: userData.email,
        password: userData.password, // Should be hashed before calling this method
        role: userData.role || 'user',
        isActive: userData.isActive !== false,
        settings: userData.settings || {},
        createdAt: new Date(),
        updatedAt: new Date()
      })
      .returning({
        id: users.id,
        username: users.username,
        email: users.email,
        role: users.role,
        isActive: users.isActive,
        createdAt: users.createdAt
      });

    return results[0];
  }

  async updateUser(userId, updateData) {
    const updateFields = {
      ...updateData,
      updatedAt: new Date()
    };

    const results = await db
      .update(users)
      .set(updateFields)
      .where(eq(users.id, userId))
      .returning({
        id: users.id,
        username: users.username,
        email: users.email,
        role: users.role,
        isActive: users.isActive,
        updatedAt: users.updatedAt
      });

    return results[0] || null;
  }

  async updateLastLogin(userId) {
    const results = await db
      .update(users)
      .set({ lastLogin: new Date() })
      .where(eq(users.id, userId))
      .returning({ lastLogin: users.lastLogin });

    return results[0] || null;
  }

  /**
   * System Settings Operations
   * Replaces: Settings queries scattered across the application
   */
  async getSetting(key) {
    const results = await db
      .select()
      .from(systemSettings)
      .where(eq(systemSettings.key, key))
      .limit(1);

    return results[0] || null;
  }

  async getPublicSettings() {
    return await db
      .select({
        key: systemSettings.key,
        value: systemSettings.value,
        description: systemSettings.description
      })
      .from(systemSettings)
      .where(eq(systemSettings.isPublic, true))
      .orderBy(systemSettings.key);
  }

  async getAllSettings() {
    return await db
      .select()
      .from(systemSettings)
      .orderBy(systemSettings.key);
  }

  async setSetting(key, value, description = null, isPublic = false) {
    // Check if setting exists
    const existing = await this.getSetting(key);
    
    if (existing) {
      // Update existing setting
      const results = await db
        .update(systemSettings)
        .set({
          value,
          description: description || existing.description,
          isPublic,
          updatedAt: new Date()
        })
        .where(eq(systemSettings.key, key))
        .returning();
        
      return results[0];
    } else {
      // Create new setting
      const results = await db
        .insert(systemSettings)
        .values({
          key,
          value,
          description,
          isPublic,
          createdAt: new Date(),
          updatedAt: new Date()
        })
        .returning();
        
      return results[0];
    }
  }

  /**
   * Audit Log Operations
   * Replaces: Audit logging scattered across controllers
   */
  async logUserAction(userId, action, entityType = null, entityId = null, details = null, request = null) {
    const auditData = {
      userId,
      action,
      entityType,
      entityId: entityId?.toString(),
      details,
      createdAt: new Date()
    };

    // Extract request information if provided
    if (request) {
      auditData.ipAddress = request.ip || request.connection?.remoteAddress;
      auditData.userAgent = request.get?.('User-Agent');
    }

    const results = await db
      .insert(auditLogs)
      .values(auditData)
      .returning({ id: auditLogs.id });

    return results[0];
  }

  async getAuditLogs(options = {}) {
    const {
      userId = null,
      action = null,
      entityType = null,
      dateFrom = null,
      dateTo = null,
      limit = 100,
      offset = 0
    } = options;

    let query = db
      .select({
        id: auditLogs.id,
        userId: auditLogs.userId,
        username: users.username,
        action: auditLogs.action,
        entityType: auditLogs.entityType,
        entityId: auditLogs.entityId,
        details: auditLogs.details,
        ipAddress: auditLogs.ipAddress,
        createdAt: auditLogs.createdAt
      })
      .from(auditLogs)
      .leftJoin(users, eq(auditLogs.userId, users.id));

    const conditions = [];
    
    if (userId) {
      conditions.push(eq(auditLogs.userId, userId));
    }
    
    if (action) {
      conditions.push(eq(auditLogs.action, action));
    }
    
    if (entityType) {
      conditions.push(eq(auditLogs.entityType, entityType));
    }
    
    if (dateFrom) {
      conditions.push(gte(auditLogs.createdAt, dateFrom));
    }
    
    if (dateTo) {
      conditions.push(lte(auditLogs.createdAt, dateTo));
    }

    if (conditions.length > 0) {
      query = query.where(and(...conditions));
    }

    return await query
      .orderBy(desc(auditLogs.createdAt))
      .limit(limit)
      .offset(offset);
  }

  /**
   * User Session Operations
   * Replaces: Session management in authentication
   */
  async createUserSession(userId, sessionToken, expiresAt, request = null) {
    const sessionData = {
      userId,
      sessionToken,
      expiresAt,
      isActive: true,
      createdAt: new Date()
    };

    if (request) {
      sessionData.ipAddress = request.ip;
      sessionData.userAgent = request.get?.('User-Agent');
    }

    const results = await db
      .insert(userSessions)
      .values(sessionData)
      .returning({ id: userSessions.id });

    return results[0];
  }

  async getActiveSession(sessionToken) {
    const results = await db
      .select({
        id: userSessions.id,
        userId: userSessions.userId,
        sessionToken: userSessions.sessionToken,
        expiresAt: userSessions.expiresAt,
        createdAt: userSessions.createdAt,
        // User info
        username: users.username,
        email: users.email,
        role: users.role,
        isActive: users.isActive
      })
      .from(userSessions)
      .innerJoin(users, eq(userSessions.userId, users.id))
      .where(
        and(
          eq(userSessions.sessionToken, sessionToken),
          eq(userSessions.isActive, true),
          gte(userSessions.expiresAt, new Date()),
          eq(users.isActive, true)
        )
      )
      .limit(1);

    return results[0] || null;
  }

  async deactivateSession(sessionToken) {
    const results = await db
      .update(userSessions)
      .set({ isActive: false })
      .where(eq(userSessions.sessionToken, sessionToken))
      .returning({ id: userSessions.id });

    return results[0] || null;
  }

  async cleanupExpiredSessions() {
    const deletedSessions = await db
      .delete(userSessions)
      .where(lte(userSessions.expiresAt, new Date()))
      .returning({ id: userSessions.id });

    return deletedSessions.length;
  }

  /**
   * Database Maintenance Operations
   * Replaces: Maintenance queries in various services
   */
  async getDatabaseSize() {
    const results = await db.execute(sql`
      SELECT 
        pg_database.datname as database_name,
        pg_size_pretty(pg_database_size(pg_database.datname)) as size,
        pg_database_size(pg_database.datname) as size_bytes
      FROM pg_database 
      WHERE datname = current_database()
    `);

    return results[0] || null;
  }

  async getTableSizes() {
    const results = await db.execute(sql`
      SELECT 
        schemaname,
        tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
        pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
        pg_relation_size(schemaname||'.'||tablename) as table_size_bytes
      FROM pg_tables 
      WHERE schemaname IN ('n8n', 'pilotpros')
      ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    `);

    return results;
  }

  /**
   * System Diagnostics
   * Replaces: Diagnostic queries in system monitoring
   */
  async getDiagnosticInfo() {
    const [healthStatus, dbSize, tableSizes, recentStats] = await Promise.all([
      this.getHealthStatus(),
      this.getDatabaseSize(), 
      this.getTableSizes(),
      this.getSystemStatistics()
    ]);

    return {
      health: healthStatus,
      database: {
        size: dbSize,
        tables: tableSizes.slice(0, 10) // Top 10 tables by size
      },
      statistics: recentStats,
      timestamp: new Date()
    };
  }
}