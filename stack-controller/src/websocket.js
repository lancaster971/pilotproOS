/**
 * WebSocket Manager - Real-time updates
 * Broadcasts system status changes to connected clients
 */

class WebSocketManager {
  constructor(io, monitor) {
    this.io = io;
    this.monitor = monitor;
    this.updateInterval = null;
  }

  start() {
    this.io.on('connection', (socket) => {
      console.log('[CONNECTED] New dashboard connection:', socket.id);

      // Send initial status
      this.sendStatus(socket);

      // Handle disconnect
      socket.on('disconnect', () => {
        console.log('[DISCONNECTED] Dashboard disconnected:', socket.id);
      });

      // Handle manual refresh requests
      socket.on('refresh-status', () => {
        this.sendStatus(socket);
      });
    });

    // Start periodic updates (every 5 seconds)
    this.updateInterval = setInterval(() => {
      this.broadcastStatus();
    }, 5000);

    console.log('[READY] WebSocket manager started');
  }

  stop() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
    this.io.close();
    console.log('[STOPPED] WebSocket manager stopped');
  }

  sendStatus(socket) {
    const status = this.monitor.getCurrentStatus();
    socket.emit('status-update', this.formatStatus(status));
  }

  broadcastStatus() {
    const status = this.monitor.getCurrentStatus();
    this.io.emit('status-update', this.formatStatus(status));
  }

  broadcastEvent(event) {
    this.io.emit('new-event', {
      timestamp: event.timestamp,
      level: event.level,
      message: event.message,
      data: event.data
    });
  }

  formatStatus(status) {
    return {
      overall: this.translateHealth(status.overall),
      services: status.services.map(s => ({
        id: s.name,
        name: s.name,
        businessName: s.businessName,
        displayName: s.displayName,
        status: this.translateStatus(s.status),
        health: this.translateHealth(s.health),
        uptime: s.uptime,
        metrics: {
          cpu: s.metrics?.cpu || 0,
          memory: s.metrics?.memory || { percent: 0, used: 0, limit: 0 }
        },
        lastCheck: s.lastCheck
      })),
      timestamp: status.timestamp
    };
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
      'operational': 'All Systems Operational',
      'partial': 'Partial Service',
      'degraded': 'Service Degraded',
      'unknown': 'Checking...'
    };
    return translations[health] || health;
  }
}

module.exports = WebSocketManager;