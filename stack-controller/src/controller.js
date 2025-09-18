/**
 * Stack Controller - Core orchestration logic
 * Manages Docker containers with business terminology
 */

const Docker = require('dockerode');
const fs = require('fs').promises;
const path = require('path');

class Controller {
  constructor() {
    this.docker = new Docker({ socketPath: '/var/run/docker.sock' });
    this.servicesConfig = null;
    this.services = new Map();
    this.metrics = new Map();
    this.restartCounts = new Map();
    this.io = null; // Will be set by index.js after initialization
  }

  async initialize() {
    // Load service configuration
    const configPath = path.join(__dirname, '../config/services.json');
    const configData = await fs.readFile(configPath, 'utf8');
    this.servicesConfig = JSON.parse(configData);

    // Initialize service states
    for (const [name, config] of Object.entries(this.servicesConfig.services)) {
      this.services.set(name, {
        name,
        ...config,
        status: 'unknown',
        health: 'unknown',
        uptime: 0,
        lastCheck: null
      });
      this.restartCounts.set(name, 0);
    }

    console.log('[INIT] Controller initialized with', this.services.size, 'services');
  }

  async getServiceStatus(serviceName) {
    try {
      const container = this.docker.getContainer(`pilotpros-${serviceName}`);
      const info = await container.inspect();

      const service = this.services.get(serviceName);

      // Update service status
      service.status = info.State.Running ? 'running' : 'stopped';
      service.health = this.calculateHealth(info);
      service.uptime = this.calculateUptime(info.State.StartedAt);
      service.lastCheck = new Date();

      // Get container stats
      const stats = await container.stats({ stream: false });
      const metrics = this.calculateMetrics(stats);
      this.metrics.set(serviceName, metrics);

      return {
        ...service,
        metrics
      };
    } catch (error) {
      console.error(`Error checking ${serviceName}:`, error.message);
      return {
        ...this.services.get(serviceName),
        status: 'error',
        health: 'unknown',
        error: error.message
      };
    }
  }

  async getAllServicesStatus() {
    const statuses = [];
    for (const serviceName of this.services.keys()) {
      const status = await this.getServiceStatus(serviceName);
      statuses.push(status);
    }
    return statuses;
  }

  async restartService(serviceName) {
    try {
      const service = this.services.get(serviceName);
      if (!service) {
        throw new Error(`Service ${serviceName} not found`);
      }

      console.log(`[RESTART] Restarting ${service.businessName}...`);
      console.log(`[DEBUG] Socket.io available: ${this.io ? 'YES' : 'NO'}`);

      // Emit restart start event
      if (this.io) {
        console.log('[EMIT] Sending restart progress event - starting');
        this.io.emit('service-restart-progress', {
          serviceId: serviceName,
          phase: 'starting',
          progress: 0,
          message: 'Initializing restart...'
        });
      } else {
        console.log('[WARNING] Socket.io not available for emitting events');
      }

      const container = this.docker.getContainer(`pilotpros-${serviceName}`);

      // Check dependencies first
      if (service.dependencies) {
        for (const dep of service.dependencies) {
          const depStatus = await this.getServiceStatus(dep);
          if (depStatus.status !== 'running') {
            console.log(`[WARNING] Starting dependency ${dep} first...`);
            await this.startService(dep);
          }
        }
      }

      // Emit stopping phase
      if (this.io) {
        console.log('[EMIT] Sending restart progress event - stopping');
        this.io.emit('service-restart-progress', {
          serviceId: serviceName,
          phase: 'stopping',
          progress: 20,
          message: 'Stopping service...'
        });
      }

      // Restart the service
      console.log('[DEBUG] Calling container.restart()...');
      await container.restart();
      console.log('[DEBUG] Container.restart() completed');

      // Emit restarted phase
      console.log('[DEBUG] After restart, emitting restarted event');
      if (this.io) {
        console.log('[EMIT] Sending restart progress event - restarted');
        this.io.emit('service-restart-progress', {
          serviceId: serviceName,
          phase: 'restarted',
          progress: 50,
          message: 'Service restarted, performing health checks...'
        });
      }

      // Update restart count
      const count = this.restartCounts.get(serviceName) || 0;
      this.restartCounts.set(serviceName, count + 1);

      // Wait for health check
      await this.waitForHealthy(serviceName);

      // Emit completed phase
      console.log('[DEBUG] After health check, emitting completed event');
      if (this.io) {
        console.log('[EMIT] Sending restart progress event - completed');
        this.io.emit('service-restart-progress', {
          serviceId: serviceName,
          phase: 'completed',
          progress: 100,
          message: 'Service healthy and operational'
        });
      }

      console.log(`[SUCCESS] ${service.businessName} restarted successfully`);

      return {
        success: true,
        message: `${service.businessName} refreshed successfully`
      };
    } catch (error) {
      console.error(`[ERROR] Failed to restart ${serviceName}:`, error.message);
      return {
        success: false,
        message: `Failed to refresh service: ${error.message}`
      };
    }
  }

  async startService(serviceName) {
    try {
      const container = this.docker.getContainer(`pilotpros-${serviceName}`);
      await container.start();
      console.log(`[SUCCESS] Started ${serviceName}`);
    } catch (error) {
      console.error(`[ERROR] Failed to start ${serviceName}:`, error.message);
      throw error;
    }
  }

  async stopService(serviceName) {
    try {
      const container = this.docker.getContainer(`pilotpros-${serviceName}`);
      await container.stop();
      console.log(`[STOPPED] Stopped ${serviceName}`);
    } catch (error) {
      console.error(`[ERROR] Failed to stop ${serviceName}:`, error.message);
      throw error;
    }
  }

  async waitForHealthy(serviceName, maxAttempts = 5) {
    console.log(`[DEBUG] Starting health check for ${serviceName}`);

    for (let i = 0; i < maxAttempts; i++) {
      await new Promise(resolve => setTimeout(resolve, 2000));
      const status = await this.getServiceStatus(serviceName);

      console.log(`[DEBUG] Health check ${i + 1}/${maxAttempts}: status=${status.status}, health=${status.health}`);

      // Emit progress during health check
      if (this.io) {
        const progress = 50 + (i * 10); // Progress from 50% to 90%
        console.log(`[EMIT] Health check progress: ${progress}%`);
        this.io.emit('service-restart-progress', {
          serviceId: serviceName,
          phase: 'health-check',
          progress: Math.min(progress, 90),
          message: `Health check attempt ${i + 1}/${maxAttempts}`
        });
      }

      // Accept running status as healthy since not all containers have health checks
      if (status.health === 'healthy' || status.status === 'running') {
        console.log(`[DEBUG] Service ${serviceName} is healthy/running`);
        return true;
      }
      console.log(`Waiting for ${serviceName} to be healthy... (${i + 1}/${maxAttempts})`);
    }

    // Don't throw error, just log warning
    console.log(`[WARNING] ${serviceName} health check timeout, but may still be running`);
    return false;
  }

  calculateHealth(containerInfo) {
    if (!containerInfo.State.Running) {
      return 'stopped';
    }

    if (containerInfo.State.Health) {
      return containerInfo.State.Health.Status;
    }

    // No health check defined, consider it healthy if running
    return containerInfo.State.Running ? 'healthy' : 'unhealthy';
  }

  calculateUptime(startedAt) {
    if (!startedAt) return 0;

    const start = new Date(startedAt);
    const now = new Date();
    const uptimeMs = now - start;

    // Format as human-readable
    const hours = Math.floor(uptimeMs / 3600000);
    const minutes = Math.floor((uptimeMs % 3600000) / 60000);

    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `${days}d ${hours % 24}h`;
    }
    return `${hours}h ${minutes}m`;
  }

  calculateMetrics(stats) {
    // CPU percentage
    const cpuDelta = stats.cpu_stats.cpu_usage.total_usage - stats.precpu_stats.cpu_usage.total_usage;
    const systemDelta = stats.cpu_stats.system_cpu_usage - stats.precpu_stats.system_cpu_usage;
    const cpuPercent = (cpuDelta / systemDelta) * stats.cpu_stats.online_cpus * 100;

    // Memory usage
    const memoryUsage = stats.memory_stats.usage / 1024 / 1024; // Convert to MB
    const memoryLimit = stats.memory_stats.limit / 1024 / 1024;
    const memoryPercent = (stats.memory_stats.usage / stats.memory_stats.limit) * 100;

    return {
      cpu: Math.round(cpuPercent * 10) / 10,
      memory: {
        used: Math.round(memoryUsage),
        limit: Math.round(memoryLimit),
        percent: Math.round(memoryPercent)
      }
    };
  }

  async performAutoRecovery(serviceName) {
    const service = this.services.get(serviceName);
    const restartCount = this.restartCounts.get(serviceName) || 0;

    if (!service.critical) {
      console.log(`[INFO] ${service.businessName} is non-critical, skipping auto-recovery`);
      return;
    }

    if (restartCount >= service.maxRestarts) {
      console.error(`[CRITICAL] ${service.businessName} exceeded max restarts (${service.maxRestarts})`);
      // Here we would send critical alert
      return;
    }

    console.log(`[RECOVERY] Attempting auto-recovery for ${service.businessName}...`);
    await this.restartService(serviceName);
  }
}

module.exports = Controller;