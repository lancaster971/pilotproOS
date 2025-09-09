/**
 * Health Monitor
 * 
 * Sistema di monitoraggio health e metriche per applicazione multi-tenant
 */

import { DatabaseConnection } from '../database/connection.js';
import { getMultiTenantScheduler } from '../backend/multi-tenant-scheduler.js';
import os from 'os';
import process from 'process';

export interface HealthCheckResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  checks: {
    database: ComponentHealth;
    scheduler: ComponentHealth;
    memory: ComponentHealth;
    disk: ComponentHealth;
    api: ComponentHealth;
  };
  metrics: SystemMetrics;
  alerts: Alert[];
}

export interface ComponentHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  message: string;
  latency_ms?: number;
  details?: any;
}

export interface SystemMetrics {
  uptime_seconds: number;
  memory: {
    used_mb: number;
    total_mb: number;
    percentage: number;
  };
  cpu: {
    load_1m: number;
    load_5m: number;
    load_15m: number;
    cores: number;
  };
  process: {
    memory_rss_mb: number;
    memory_heap_mb: number;
    memory_external_mb: number;
    cpu_percentage: number;
  };
  database: {
    connections_active: number;
    connections_idle: number;
    connections_total: number;
    query_time_avg_ms: number;
  };
  scheduler: {
    is_running: boolean;
    tasks_scheduled: number;
    last_sync_time: string | null;
    sync_errors_24h: number;
  };
  tenants: {
    total: number;
    active: number;
    with_errors: number;
  };
}

export interface Alert {
  severity: 'warning' | 'critical';
  component: string;
  message: string;
  timestamp: string;
}

/**
 * Health Monitor Service
 */
export class HealthMonitor {
  private db: DatabaseConnection;
  private queryMetrics: { times: number[], errors: number } = { times: [], errors: 0 };
  private startTime: Date = new Date();

  constructor() {
    this.db = DatabaseConnection.getInstance();
  }

  /**
   * Esegui health check completo
   */
  async performHealthCheck(): Promise<HealthCheckResult> {
    const alerts: Alert[] = [];
    
    // Check database
    const dbHealth = await this.checkDatabase();
    if (dbHealth.status !== 'healthy') {
      alerts.push({
        severity: dbHealth.status === 'unhealthy' ? 'critical' : 'warning',
        component: 'database',
        message: dbHealth.message,
        timestamp: new Date().toISOString()
      });
    }

    // Check scheduler
    const schedulerHealth = await this.checkScheduler();
    if (schedulerHealth.status !== 'healthy') {
      alerts.push({
        severity: 'warning',
        component: 'scheduler',
        message: schedulerHealth.message,
        timestamp: new Date().toISOString()
      });
    }

    // Check memory
    const memoryHealth = this.checkMemory();
    if (memoryHealth.status !== 'healthy') {
      alerts.push({
        severity: memoryHealth.status === 'unhealthy' ? 'critical' : 'warning',
        component: 'memory',
        message: memoryHealth.message,
        timestamp: new Date().toISOString()
      });
    }

    // Check disk
    const diskHealth = await this.checkDisk();
    if (diskHealth.status !== 'healthy') {
      alerts.push({
        severity: diskHealth.status === 'unhealthy' ? 'critical' : 'warning',
        component: 'disk',
        message: diskHealth.message,
        timestamp: new Date().toISOString()
      });
    }

    // Check API
    const apiHealth = this.checkAPI();

    // Collect metrics
    const metrics = await this.collectMetrics();

    // Determine overall status
    const checks = {
      database: dbHealth,
      scheduler: schedulerHealth,
      memory: memoryHealth,
      disk: diskHealth,
      api: apiHealth
    };

    const unhealthyCount = Object.values(checks).filter(c => c.status === 'unhealthy').length;
    const degradedCount = Object.values(checks).filter(c => c.status === 'degraded').length;

    let overallStatus: 'healthy' | 'degraded' | 'unhealthy';
    if (unhealthyCount > 0) {
      overallStatus = 'unhealthy';
    } else if (degradedCount > 0) {
      overallStatus = 'degraded';
    } else {
      overallStatus = 'healthy';
    }

    return {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      checks,
      metrics,
      alerts
    };
  }

  /**
   * Check database health
   */
  private async checkDatabase(): Promise<ComponentHealth> {
    try {
      const start = Date.now();
      await this.db.query('SELECT 1');
      const latency = Date.now() - start;

      this.queryMetrics.times.push(latency);
      if (this.queryMetrics.times.length > 100) {
        this.queryMetrics.times.shift();
      }

      // Check connection pool stats (simplified for now)
      const totalConnections = 10; // Default pool size
      const idleConnections = 5; // Estimated
      const waitingCount = 0;

      if (latency > 1000) {
        return {
          status: 'degraded',
          message: `Database response slow (${latency}ms)`,
          latency_ms: latency,
          details: { totalConnections, idleConnections, waitingCount }
        };
      }

      if (waitingCount > 5) {
        return {
          status: 'degraded',
          message: `High database connection wait queue (${waitingCount} waiting)`,
          latency_ms: latency,
          details: { totalConnections, idleConnections, waitingCount }
        };
      }

      return {
        status: 'healthy',
        message: 'Database connection healthy',
        latency_ms: latency,
        details: { totalConnections, idleConnections, waitingCount }
      };

    } catch (error) {
      this.queryMetrics.errors++;
      return {
        status: 'unhealthy',
        message: `Database connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        details: { error: error instanceof Error ? error.message : error }
      };
    }
  }

  /**
   * Check scheduler health
   */
  private async checkScheduler(): Promise<ComponentHealth> {
    try {
      const scheduler = getMultiTenantScheduler();
      const stats = scheduler.getStats();
      const health = await scheduler.healthCheck();

      if (!stats.isRunning) {
        return {
          status: 'degraded',
          message: 'Scheduler not running',
          details: stats
        };
      }

      // Check last sync time
      if (stats.stats.lastSyncTime) {
        const lastSync = new Date(stats.stats.lastSyncTime);
        const hoursSinceSync = (Date.now() - lastSync.getTime()) / (1000 * 60 * 60);
        
        if (hoursSinceSync > 24) {
          return {
            status: 'degraded',
            message: `No sync in ${Math.floor(hoursSinceSync)} hours`,
            details: stats
          };
        }
      }

      // Check for errors
      const recentErrors = await this.db.getOne(`
        SELECT COUNT(*) as count 
        FROM tenant_sync_logs 
        WHERE status = 'error' 
        AND started_at > NOW() - INTERVAL '24 hours'
      `);

      if (parseInt(recentErrors.count) > 10) {
        return {
          status: 'degraded',
          message: `High error rate: ${recentErrors.count} errors in 24h`,
          details: { ...stats, errors_24h: recentErrors.count }
        };
      }

      return {
        status: 'healthy',
        message: 'Scheduler running normally',
        details: stats
      };

    } catch (error) {
      return {
        status: 'unhealthy',
        message: `Scheduler check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        details: { error: error instanceof Error ? error.message : error }
      };
    }
  }

  /**
   * Check memory health
   */
  private checkMemory(): ComponentHealth {
    const memUsage = process.memoryUsage();
    const totalMem = os.totalmem();
    const freeMem = os.freemem();
    const usedMem = totalMem - freeMem;
    const memPercentage = (usedMem / totalMem) * 100;

    // Check process memory
    const heapUsedMB = memUsage.heapUsed / 1024 / 1024;
    const rssMB = memUsage.rss / 1024 / 1024;

    if (memPercentage > 90 || heapUsedMB > 1024) {
      return {
        status: 'unhealthy',
        message: `Critical memory usage: ${memPercentage.toFixed(1)}% system, ${heapUsedMB.toFixed(0)}MB heap`,
        details: {
          system_percentage: memPercentage,
          heap_mb: heapUsedMB,
          rss_mb: rssMB
        }
      };
    }

    if (memPercentage > 75 || heapUsedMB > 512) {
      return {
        status: 'degraded',
        message: `High memory usage: ${memPercentage.toFixed(1)}% system, ${heapUsedMB.toFixed(0)}MB heap`,
        details: {
          system_percentage: memPercentage,
          heap_mb: heapUsedMB,
          rss_mb: rssMB
        }
      };
    }

    return {
      status: 'healthy',
      message: `Memory usage normal: ${memPercentage.toFixed(1)}%`,
      details: {
        system_percentage: memPercentage,
        heap_mb: heapUsedMB,
        rss_mb: rssMB
      }
    };
  }

  /**
   * Check disk health
   */
  private async checkDisk(): Promise<ComponentHealth> {
    try {
      // Check database size
      const dbSize = await this.db.getOne(`
        SELECT pg_database_size(current_database()) as size
      `);

      const dbSizeMB = parseInt(dbSize.size) / 1024 / 1024;

      if (dbSizeMB > 10000) { // > 10GB
        return {
          status: 'degraded',
          message: `Large database size: ${(dbSizeMB / 1024).toFixed(1)}GB`,
          details: { database_size_mb: dbSizeMB }
        };
      }

      return {
        status: 'healthy',
        message: `Database size: ${dbSizeMB.toFixed(0)}MB`,
        details: { database_size_mb: dbSizeMB }
      };

    } catch (error) {
      return {
        status: 'degraded',
        message: 'Unable to check disk usage',
        details: { error: error instanceof Error ? error.message : error }
      };
    }
  }

  /**
   * Check API health
   */
  private checkAPI(): ComponentHealth {
    const uptime = process.uptime();
    
    if (uptime < 60) {
      return {
        status: 'degraded',
        message: 'API recently restarted',
        details: { uptime_seconds: uptime }
      };
    }

    return {
      status: 'healthy',
      message: 'API running normally',
      details: { uptime_seconds: uptime }
    };
  }

  /**
   * Collect system metrics
   */
  private async collectMetrics(): Promise<SystemMetrics> {
    const memUsage = process.memoryUsage();
    const cpuUsage = process.cpuUsage();
    const loadAvg = os.loadavg();
    const totalMem = os.totalmem();
    const freeMem = os.freemem();

    // Database metrics (simplified for now)
    const avgQueryTime = this.queryMetrics.times.length > 0
      ? this.queryMetrics.times.reduce((a, b) => a + b, 0) / this.queryMetrics.times.length
      : 0;

    // Scheduler metrics
    const scheduler = getMultiTenantScheduler();
    const schedulerStats = scheduler.getStats();

    // Tenant metrics
    const totalTenants = await this.db.getOne('SELECT COUNT(*) as count FROM tenants');
    const activeTenants = await this.db.getOne('SELECT COUNT(*) as count FROM tenants WHERE sync_enabled = true');
    const tenantsWithErrors = await this.db.getOne(`
      SELECT COUNT(DISTINCT tenant_id) as count 
      FROM tenant_sync_logs 
      WHERE status = 'error' 
      AND started_at > NOW() - INTERVAL '24 hours'
    `);

    // Recent sync errors
    const syncErrors24h = await this.db.getOne(`
      SELECT COUNT(*) as count 
      FROM tenant_sync_logs 
      WHERE status = 'error' 
      AND started_at > NOW() - INTERVAL '24 hours'
    `);

    return {
      uptime_seconds: process.uptime(),
      memory: {
        used_mb: (totalMem - freeMem) / 1024 / 1024,
        total_mb: totalMem / 1024 / 1024,
        percentage: ((totalMem - freeMem) / totalMem) * 100
      },
      cpu: {
        load_1m: loadAvg[0],
        load_5m: loadAvg[1],
        load_15m: loadAvg[2],
        cores: os.cpus().length
      },
      process: {
        memory_rss_mb: memUsage.rss / 1024 / 1024,
        memory_heap_mb: memUsage.heapUsed / 1024 / 1024,
        memory_external_mb: memUsage.external / 1024 / 1024,
        cpu_percentage: (cpuUsage.user + cpuUsage.system) / 1000000 // Convert to percentage
      },
      database: {
        connections_active: 5, // Estimated
        connections_idle: 5, // Estimated
        connections_total: 10, // Default pool size
        query_time_avg_ms: avgQueryTime
      },
      scheduler: {
        is_running: schedulerStats.isRunning,
        tasks_scheduled: schedulerStats.scheduledTasks.length,
        last_sync_time: schedulerStats.stats.lastSyncTime ? schedulerStats.stats.lastSyncTime.toISOString() : null,
        sync_errors_24h: parseInt(syncErrors24h.count)
      },
      tenants: {
        total: parseInt(totalTenants.count),
        active: parseInt(activeTenants.count),
        with_errors: parseInt(tenantsWithErrors.count)
      }
    };
  }

  /**
   * Get prometheus metrics format
   */
  async getPrometheusMetrics(): Promise<string> {
    const metrics = await this.collectMetrics();
    const health = await this.performHealthCheck();

    const lines: string[] = [];

    // Health status
    lines.push(`# HELP n8n_mcp_health_status Overall health status (1=healthy, 0.5=degraded, 0=unhealthy)`);
    lines.push(`# TYPE n8n_mcp_health_status gauge`);
    lines.push(`n8n_mcp_health_status ${health.status === 'healthy' ? 1 : health.status === 'degraded' ? 0.5 : 0}`);

    // Component health
    lines.push(`# HELP n8n_mcp_component_health Component health status`);
    lines.push(`# TYPE n8n_mcp_component_health gauge`);
    for (const [component, status] of Object.entries(health.checks)) {
      const value = status.status === 'healthy' ? 1 : status.status === 'degraded' ? 0.5 : 0;
      lines.push(`n8n_mcp_component_health{component="${component}"} ${value}`);
    }

    // System metrics
    lines.push(`# HELP n8n_mcp_uptime_seconds Application uptime in seconds`);
    lines.push(`# TYPE n8n_mcp_uptime_seconds counter`);
    lines.push(`n8n_mcp_uptime_seconds ${metrics.uptime_seconds}`);

    // Memory metrics
    lines.push(`# HELP n8n_mcp_memory_usage_bytes Memory usage in bytes`);
    lines.push(`# TYPE n8n_mcp_memory_usage_bytes gauge`);
    lines.push(`n8n_mcp_memory_usage_bytes{type="rss"} ${metrics.process.memory_rss_mb * 1024 * 1024}`);
    lines.push(`n8n_mcp_memory_usage_bytes{type="heap"} ${metrics.process.memory_heap_mb * 1024 * 1024}`);

    // Database metrics
    lines.push(`# HELP n8n_mcp_db_connections Database connections`);
    lines.push(`# TYPE n8n_mcp_db_connections gauge`);
    lines.push(`n8n_mcp_db_connections{state="active"} ${metrics.database.connections_active}`);
    lines.push(`n8n_mcp_db_connections{state="idle"} ${metrics.database.connections_idle}`);
    lines.push(`n8n_mcp_db_query_time_ms Average query time in milliseconds`);
    lines.push(`# TYPE n8n_mcp_db_query_time_ms gauge`);
    lines.push(`n8n_mcp_db_query_time_ms ${metrics.database.query_time_avg_ms}`);

    // Scheduler metrics
    lines.push(`# HELP n8n_mcp_scheduler_running Scheduler running status`);
    lines.push(`# TYPE n8n_mcp_scheduler_running gauge`);
    lines.push(`n8n_mcp_scheduler_running ${metrics.scheduler.is_running ? 1 : 0}`);
    lines.push(`# HELP n8n_mcp_sync_errors_total Sync errors in last 24h`);
    lines.push(`# TYPE n8n_mcp_sync_errors_total counter`);
    lines.push(`n8n_mcp_sync_errors_total ${metrics.scheduler.sync_errors_24h}`);

    // Tenant metrics
    lines.push(`# HELP n8n_mcp_tenants_total Total number of tenants`);
    lines.push(`# TYPE n8n_mcp_tenants_total gauge`);
    lines.push(`n8n_mcp_tenants_total ${metrics.tenants.total}`);
    lines.push(`n8n_mcp_tenants_active ${metrics.tenants.active}`);
    lines.push(`n8n_mcp_tenants_with_errors ${metrics.tenants.with_errors}`);

    return lines.join('\n');
  }
}

// Singleton instance
let monitorInstance: HealthMonitor | null = null;

export function getHealthMonitor(): HealthMonitor {
  if (!monitorInstance) {
    monitorInstance = new HealthMonitor();
  }
  return monitorInstance;
}