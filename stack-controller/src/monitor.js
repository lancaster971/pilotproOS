/**
 * Monitor Service - Health monitoring and alerting
 * Uses business terminology for all external communications
 */

const cron = require('node-cron');

class Monitor {
  constructor(controller) {
    this.controller = controller;
    this.monitoringActive = false;
    this.cronJob = null;
    this.lastStatus = new Map();
    this.events = [];
    this.maxEvents = 100;
  }

  async startMonitoring() {
    if (this.monitoringActive) {
      console.log('[WARNING] Monitoring already active');
      return;
    }

    this.monitoringActive = true;
    console.log('[MONITOR] Starting system monitoring...');

    // Initial check
    await this.performHealthCheck();

    // Schedule regular checks (every 30 seconds)
    this.cronJob = cron.schedule('*/30 * * * * *', async () => {
      await this.performHealthCheck();
    });

    console.log('[READY] System monitoring active');
  }

  async stopMonitoring() {
    if (this.cronJob) {
      this.cronJob.stop();
      this.cronJob = null;
    }
    this.monitoringActive = false;
    console.log('[STOPPED] System monitoring stopped');
  }

  async performHealthCheck() {
    try {
      const services = await this.controller.getAllServicesStatus();

      for (const service of services) {
        await this.checkService(service);
      }

      // Calculate overall system health
      const overallHealth = this.calculateOverallHealth(services);
      this.logEvent('system_check', 'System health check completed', { health: overallHealth });

    } catch (error) {
      console.error('[ERROR] Health check failed:', error);
      this.logEvent('error', 'System health check failed', { error: error.message });
    }
  }

  async checkService(service) {
    const lastStatus = this.lastStatus.get(service.name);
    this.lastStatus.set(service.name, service);

    // Check if status changed
    if (lastStatus && lastStatus.status !== service.status) {
      this.handleStatusChange(service, lastStatus);
    }

    // Check if service needs recovery
    if (service.health === 'unhealthy' && service.critical) {
      this.logEvent('warning', `${service.businessName} requires attention`, {
        service: service.name,
        health: service.health
      });

      // Trigger auto-recovery
      await this.controller.performAutoRecovery(service.name);
    }

    // Check resource usage
    if (service.metrics) {
      this.checkResourceUsage(service);
    }
  }

  handleStatusChange(service, previousStatus) {
    const message = `${service.businessName} status changed from ${previousStatus.status} to ${service.status}`;

    if (service.status === 'running') {
      this.logEvent('success', message, { service: service.name });
    } else if (service.status === 'stopped') {
      this.logEvent('error', message, { service: service.name });
    } else {
      this.logEvent('warning', message, { service: service.name });
    }
  }

  checkResourceUsage(service) {
    const config = this.controller.servicesConfig.alerts.thresholds;

    if (service.metrics.cpu > config.cpuCritical) {
      this.logEvent('critical', `${service.businessName} CPU usage critical: ${service.metrics.cpu}%`, {
        service: service.name,
        cpu: service.metrics.cpu
      });
    } else if (service.metrics.cpu > config.cpuWarning) {
      this.logEvent('warning', `${service.businessName} CPU usage high: ${service.metrics.cpu}%`, {
        service: service.name,
        cpu: service.metrics.cpu
      });
    }

    if (service.metrics.memory.percent > config.memoryCritical) {
      this.logEvent('critical', `${service.businessName} memory usage critical: ${service.metrics.memory.percent}%`, {
        service: service.name,
        memory: service.metrics.memory
      });
    } else if (service.metrics.memory.percent > config.memoryWarning) {
      this.logEvent('warning', `${service.businessName} memory usage high: ${service.metrics.memory.percent}%`, {
        service: service.name,
        memory: service.metrics.memory
      });
    }
  }

  calculateOverallHealth(services) {
    const healthCounts = {
      healthy: 0,
      unhealthy: 0,
      warning: 0,
      unknown: 0
    };

    for (const service of services) {
      if (service.health === 'healthy' && service.status === 'running') {
        healthCounts.healthy++;
      } else if (service.health === 'unhealthy' || service.status === 'stopped') {
        healthCounts.unhealthy++;
      } else if (service.health === 'starting') {
        healthCounts.warning++;
      } else {
        healthCounts.unknown++;
      }
    }

    // Determine overall health
    if (healthCounts.unhealthy > 0) {
      return 'degraded';
    } else if (healthCounts.warning > 0 || healthCounts.unknown > 0) {
      return 'partial';
    } else {
      return 'operational';
    }
  }

  logEvent(level, message, data = {}) {
    const event = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data
    };

    this.events.push(event);

    // Keep only recent events
    if (this.events.length > this.maxEvents) {
      this.events = this.events.slice(-this.maxEvents);
    }

    // Log to console with appropriate formatting
    const prefix = {
      success: '[SUCCESS]',
      error: '[ERROR]',
      warning: '[WARNING]',
      critical: '[CRITICAL]',
      info: '[INFO]',
      system_check: '[CHECK]'
    }[level] || '[LOG]';

    console.log(`${prefix} ${message}`);
  }

  getRecentEvents(limit = 20) {
    return this.events.slice(-limit).reverse();
  }

  getCurrentStatus() {
    const services = Array.from(this.lastStatus.values());
    const overallHealth = this.calculateOverallHealth(services);

    return {
      overall: overallHealth,
      services: services.map(s => ({
        name: s.name,
        displayName: s.displayName,
        businessName: s.businessName,
        status: s.status,
        health: s.health,
        uptime: s.uptime,
        metrics: s.metrics || {},
        lastCheck: s.lastCheck
      })),
      timestamp: new Date().toISOString()
    };
  }
}

module.exports = Monitor;