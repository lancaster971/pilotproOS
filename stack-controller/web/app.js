/**
 * Stack Controller Dashboard - Client Application
 * Real-time monitoring with business terminology
 */

const { createApp } = window.Vue;

createApp({
  data() {
    return {
      // Overall system status
      overallStatus: 'Checking...',
      overallStatusClass: 'operational',
      lastUpdate: 'Never',
      
      // Services list
      services: [],
      
      // Recent events/activity
      recentEvents: [],
      maxEvents: 20,
      
      // WebSocket connection
      socket: null,
      connected: false,
      reconnectAttempts: 0,
      maxReconnectAttempts: 10,
      
      // Loading states
      isRefreshingAll: false,
      exportInProgress: false
    };
  },

  mounted() {
    this.connectWebSocket();
    this.loadInitialData();
    this.startClockUpdate();
  },

  beforeUnmount() {
    if (this.socket) {
      this.socket.disconnect();
    }
    if (this.clockInterval) {
      clearInterval(this.clockInterval);
    }
  },

  methods: {
    // WebSocket connection management
    connectWebSocket() {
      console.log('Connecting to monitoring service...');
      
      this.socket = io('/', {
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        reconnectionAttempts: this.maxReconnectAttempts
      });

      this.socket.on('connect', () => {
        console.log('Connected to monitoring service');
        this.connected = true;
        this.reconnectAttempts = 0;
        this.addEvent('Success', 'Connected to monitoring service');
      });

      this.socket.on('disconnect', () => {
        console.log('Disconnected from monitoring service');
        this.connected = false;
        this.addEvent('Warning', 'Connection lost, attempting to reconnect...');
      });

      this.socket.on('status-update', (data) => {
        this.handleStatusUpdate(data);
      });

      this.socket.on('new-event', (event) => {
        this.addEventFromServer(event);
      });

      // Listen for restart progress events
      this.socket.on('service-restart-progress', (data) => {
        this.handleRestartProgress(data);
      });

      this.socket.on('connect_error', (error) => {
        this.reconnectAttempts++;
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          this.addEvent('Error', 'Unable to connect to monitoring service');
        }
      });
    },

    // Load initial data from API
    async loadInitialData() {
      try {
        const response = await fetch('/api/system/status');
        if (response.ok) {
          const data = await response.json();
          this.handleStatusUpdate(data);
        }
      } catch (error) {
        console.error('Failed to load initial data:', error);
        this.addEvent('Error', 'Failed to load system status');
      }

      // Load recent events
      try {
        const eventsResponse = await fetch('/api/system/events?limit=10');
        if (eventsResponse.ok) {
          const events = await eventsResponse.json();
          events.forEach(e => this.addEventFromServer(e));
        }
      } catch (error) {
        console.error('Failed to load events:', error);
      }
    },

    // Handle restart progress events from server
    handleRestartProgress(data) {
      const service = this.services.find(s => s.id === data.serviceId);
      if (!service) return;

      // Update service restart state based on real backend events
      if (data.phase === 'starting') {
        service.isRefreshing = true;
        service.restartProgress = data.progress;
        service.restartPhase = data.message;
      } else if (data.phase === 'stopping') {
        service.restartProgress = data.progress;
        service.restartPhase = data.message;
      } else if (data.phase === 'restarted') {
        service.restartProgress = data.progress;
        service.restartPhase = data.message;
      } else if (data.phase === 'health-check') {
        service.restartProgress = data.progress;
        service.restartPhase = data.message;
      } else if (data.phase === 'completed') {
        service.restartProgress = 100;
        service.restartPhase = 'Restart completed!';

        // Clear after showing completion
        setTimeout(() => {
          service.isRefreshing = false;
          service.restartProgress = 0;
          service.restartPhase = '';
          this.services = [...this.services];

          // Request fresh status
          this.loadInitialData();
        }, 2000);
      } else if (data.phase === 'error') {
        service.restartProgress = 0;
        service.restartPhase = 'Restart failed!';

        setTimeout(() => {
          service.isRefreshing = false;
          service.restartProgress = 0;
          service.restartPhase = '';
          this.services = [...this.services];
        }, 3000);
      }

      // Force Vue to update
      this.services = [...this.services];
    },

    // Handle status updates from server
    handleStatusUpdate(data) {
      this.overallStatus = data.overall || 'Unknown';
      this.updateOverallStatusClass(data.overall);
      this.lastUpdate = this.formatTime(data.timestamp || new Date().toISOString());

      // Update services (preserve refresh state)
      if (data.services) {
        const currentServices = this.services;
        this.services = data.services.map(service => {
          // Find existing service to preserve refresh state
          const existing = currentServices.find(s => s.id === (service.id || service.name));

          return {
            id: service.id || service.name,
            name: service.businessName || service.name,
            displayName: service.displayName || service.name,
            status: service.status || 'Unknown',
            health: service.health || 'Unknown',
            isRefreshing: existing?.isRefreshing || false,
            restartProgress: existing?.restartProgress || 0,
            restartPhase: existing?.restartPhase || '',
            cpu: Math.round(service.metrics?.cpu || 0),
            memory: {
              percent: Math.round(service.metrics?.memory?.percent || 0),
              used: service.metrics?.memory?.used || 0,
              limit: service.metrics?.memory?.limit || 0
            },
            uptime: service.uptime || '0m',
            lastCheck: service.lastCheck
          };
        });
      }
    },

    // Update overall status styling
    updateOverallStatusClass(status) {
      const statusMap = {
        'All Systems Operational': 'operational',
        'Healthy': 'operational',
        'Partial Service': 'partial',
        'Service Degraded': 'degraded',
        'Needs Attention': 'degraded'
      };
      this.overallStatusClass = statusMap[status] || 'degraded';
    },

    // Get service card styling
    getServiceClass(service) {
      if (service.status === 'Operational' || service.status === 'running') return 'healthy';
      if (service.status === 'Initializing' || service.health === 'Starting Up') return 'warning';
      if (service.status === 'Stopped' || service.status === 'Error' || service.status === 'stopped') return 'error';
      return '';
    },

    // Get status dot class
    getStatusDotClass(service) {
      // Check if service is restarting first
      if (service.isRefreshing) {
        return 'warning';
      }
      if (service.status === 'Operational' || service.status === 'running') {
        return 'active';
      }
      if (service.status === 'Stopped' || service.status === 'stopped' || service.status === 'Error') {
        return 'stopped';
      }
      if (service.status === 'Initializing' || service.status === 'starting') {
        return 'warning';
      }
      return 'warning';
    },

    // Get status text class
    getStatusTextClass(service) {
      // Check if service is restarting first
      if (service.isRefreshing) {
        return 'warning';
      }
      if (service.status === 'Operational' || service.status === 'running') {
        return 'active';
      }
      if (service.status === 'Stopped' || service.status === 'stopped' || service.status === 'Error') {
        return 'stopped';
      }
      if (service.status === 'Initializing' || service.status === 'starting') {
        return 'warning';
      }
      return 'warning';
    },

    // Refresh individual service with inline progress
    async refreshService(serviceId) {
      const service = this.services.find(s => s.id === serviceId);
      if (!service) return;

      console.log('Starting restart for', service.name);

      // Initialize restart state
      service.isRefreshing = true;
      service.restartProgress = 0;
      service.restartPhase = 'Initializing...';

      // Force Vue to update
      this.services = [...this.services];

      try {
        // Send restart request - progress will be tracked via WebSocket events
        const response = await fetch(`/api/system/service/${serviceId}/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
          throw new Error('Restart request failed');
        }

        // Progress updates will come via WebSocket events (handleRestartProgress)
        // No need for local animation - real backend events drive the UI

      } catch (error) {
        console.error('Service refresh failed:', error);

        service.restartProgress = 0;
        service.restartPhase = 'Restart failed!';
        this.services = [...this.services];
        this.addEvent('Error', `Failed to restart ${service.name}`);

        await this.delay(2000);

        service.isRefreshing = false;
        service.restartProgress = 0;
        service.restartPhase = '';
        this.services = [...this.services];
      }
    },

    // Utility delay function
    delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    },

    // Refresh all services
    async refreshAll() {
      if (this.isRefreshingAll) return;

      this.isRefreshingAll = true;
      this.addEvent('Success', 'Refreshing all services...');

      try {
        for (const service of this.services) {
          await this.refreshService(service.id);
          // Small delay between services
          await new Promise(resolve => setTimeout(resolve, 500));
        }
        this.addEvent('Success', 'All services refreshed');
      } catch (error) {
        this.addEvent('Error', 'Failed to refresh some services');
      } finally {
        this.isRefreshingAll = false;
      }
    },

    // Export performance metrics
    async exportMetrics() {
      if (this.exportInProgress) return;

      this.exportInProgress = true;
      this.addEvent('Success', 'Generating performance report...');

      try {
        const response = await fetch('/api/system/performance');
        if (response.ok) {
          const metrics = await response.json();
          
          // Create CSV content
          const csv = this.generateCSV(metrics);
          
          // Download file
          const blob = new Blob([csv], { type: 'text/csv' });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `performance_report_${new Date().toISOString().split('T')[0]}.csv`;
          a.click();
          window.URL.revokeObjectURL(url);
          
          this.addEvent('Success', 'Performance report exported');
        }
      } catch (error) {
        console.error('Export failed:', error);
        this.addEvent('Error', 'Failed to export performance report');
      } finally {
        this.exportInProgress = false;
      }
    },

    // Generate CSV from metrics
    generateCSV(metrics) {
      let csv = 'Service,CPU %,Memory MB,Memory %,Timestamp\n';
      
      for (const [serviceName, data] of Object.entries(metrics.services)) {
        csv += `"${serviceName}",${data.cpu},${data.memory.used},${data.memory.percent},"${metrics.timestamp}"\n`;
      }
      
      csv += `\n"Total CPU",${metrics.overall.cpu},,"${metrics.timestamp}"\n`;
      csv += `"Total Memory MB",${metrics.overall.memory},,"${metrics.timestamp}"\n`;
      
      return csv;
    },

    // View system logs
    viewLogs() {
      this.addEvent('Success', 'Opening system logs...');
      // Could open in new tab or modal
      window.open('/api/system/events?limit=100', '_blank');
    },

    // Add event to activity log
    addEvent(level, message) {
      const event = {
        timestamp: new Date().toISOString(),
        level,
        message
      };
      
      this.recentEvents.unshift(event);
      
      // Keep only recent events
      if (this.recentEvents.length > this.maxEvents) {
        this.recentEvents = this.recentEvents.slice(0, this.maxEvents);
      }
    },

    // Add event from server
    addEventFromServer(event) {
      this.recentEvents.unshift(event);
      
      if (this.recentEvents.length > this.maxEvents) {
        this.recentEvents = this.recentEvents.slice(0, this.maxEvents);
      }
    },

    // Format timestamp to time only
    formatTime(timestamp) {
      if (!timestamp) return 'Never';
      const date = new Date(timestamp);
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
      });
    },

    // Format uptime string
    formatUptime(seconds) {
      if (!seconds || seconds === 0) return '0m';
      
      const days = Math.floor(seconds / 86400);
      const hours = Math.floor((seconds % 86400) / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      
      if (days > 0) {
        return `${days}d ${hours}h`;
      } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
      } else {
        return `${minutes}m`;
      }
    },

    // Update clock
    startClockUpdate() {
      this.clockInterval = setInterval(() => {
        // Update "last update" time if we have a timestamp
        if (this.lastUpdate && this.lastUpdate !== 'Never') {
          // Just trigger reactivity
          this.lastUpdate = this.formatTime(new Date().toISOString());
        }
      }, 1000);
    }
  }
}).mount('#app');