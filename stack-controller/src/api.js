/**
 * REST API for Stack Controller
 * All endpoints use business terminology
 */

class API {
  constructor(app, controller, monitor) {
    this.app = app;
    this.controller = controller;
    this.monitor = monitor;
    this.setupRoutes();
  }

  setupRoutes() {
    // System status
    this.app.get('/api/system/status', async (req, res) => {
      try {
        const status = this.monitor.getCurrentStatus();
        res.json(status);
      } catch (error) {
        res.status(500).json({
          error: 'Failed to retrieve system status',
          message: error.message
        });
      }
    });

    // Service list with current state
    this.app.get('/api/system/services', async (req, res) => {
      try {
        const services = await this.controller.getAllServicesStatus();
        res.json(services.map(s => ({
          id: s.name,
          name: s.businessName,
          displayName: s.displayName,
          status: this.translateStatus(s.status),
          health: this.translateHealth(s.health),
          performance: {
            cpu: s.metrics?.cpu || 0,
            memory: s.metrics?.memory || { percent: 0, used: 0, limit: 0 }
          },
          uptime: s.uptime
        })));
      } catch (error) {
        res.status(500).json({
          error: 'Failed to retrieve services',
          message: error.message
        });
      }
    });

    // Individual service details
    this.app.get('/api/system/service/:name', async (req, res) => {
      try {
        const service = await this.controller.getServiceStatus(req.params.name);
        if (!service) {
          return res.status(404).json({
            error: 'Service not found'
          });
        }

        res.json({
          id: service.name,
          name: service.businessName,
          displayName: service.displayName,
          status: this.translateStatus(service.status),
          health: this.translateHealth(service.health),
          performance: {
            cpu: service.metrics?.cpu || 0,
            memory: service.metrics?.memory || { percent: 0, used: 0, limit: 0 }
          },
          uptime: service.uptime,
          critical: service.critical,
          lastCheck: service.lastCheck
        });
      } catch (error) {
        res.status(500).json({
          error: 'Failed to retrieve service details',
          message: error.message
        });
      }
    });

    // Restart service
    this.app.post('/api/system/service/:name/refresh', async (req, res) => {
      try {
        const result = await this.controller.restartService(req.params.name);
        res.json(result);
      } catch (error) {
        res.status(500).json({
          error: 'Failed to refresh service',
          message: error.message
        });
      }
    });

    // Performance metrics
    this.app.get('/api/system/performance', async (req, res) => {
      try {
        const services = await this.controller.getAllServicesStatus();
        const overall = {
          totalCpu: 0,
          totalMemory: 0,
          services: {}
        };

        for (const service of services) {
          if (service.metrics) {
            overall.totalCpu += service.metrics.cpu;
            overall.totalMemory += service.metrics.memory.used;
            overall.services[service.businessName] = {
              cpu: service.metrics.cpu,
              memory: service.metrics.memory
            };
          }
        }

        res.json({
          timestamp: new Date().toISOString(),
          overall: {
            cpu: Math.round(overall.totalCpu * 10) / 10,
            memory: Math.round(overall.totalMemory)
          },
          services: overall.services
        });
      } catch (error) {
        res.status(500).json({
          error: 'Failed to retrieve performance metrics',
          message: error.message
        });
      }
    });

    // Recent events/logs
    this.app.get('/api/system/events', (req, res) => {
      const limit = parseInt(req.query.limit) || 20;
      const events = this.monitor.getRecentEvents(limit);

      res.json(events.map(e => ({
        timestamp: e.timestamp,
        level: this.translateEventLevel(e.level),
        message: e.message,
        details: e.data
      })));
    });

    // System overview for frontend widget
    this.app.get('/api/system/overview', async (req, res) => {
      try {
        const status = this.monitor.getCurrentStatus();
        const services = await this.controller.getAllServicesStatus();

        const overview = {
          health: this.translateOverallHealth(status.overall),
          serviceCount: {
            total: services.length,
            operational: services.filter(s => s.health === 'healthy').length,
            warning: services.filter(s => s.health === 'starting').length,
            error: services.filter(s => s.health === 'unhealthy' || s.status === 'stopped').length
          },
          lastCheck: new Date().toISOString()
        };

        res.json(overview);
      } catch (error) {
        res.status(500).json({
          error: 'Failed to retrieve system overview',
          message: error.message
        });
      }
    });
  }

  translateStatus(status) {
    const translations = {
      'running': 'Operational',
      'stopped': 'Stopped',
      'starting': 'Initializing',
      'error': 'Error',
      'unknown': 'Unknown'
    };
    return translations[status] || status;
  }

  translateHealth(health) {
    const translations = {
      'healthy': 'Healthy',
      'unhealthy': 'Needs Attention',
      'starting': 'Starting Up',
      'stopped': 'Inactive',
      'unknown': 'Checking...'
    };
    return translations[health] || health;
  }

  translateOverallHealth(health) {
    const translations = {
      'operational': 'All Systems Operational',
      'partial': 'Partial Service',
      'degraded': 'Service Degraded'
    };
    return translations[health] || health;
  }

  translateEventLevel(level) {
    const translations = {
      'success': 'Success',
      'error': 'Error',
      'warning': 'Warning',
      'critical': 'Critical',
      'info': 'Information',
      'system_check': 'Health Check'
    };
    return translations[level] || level;
  }
}

module.exports = API;