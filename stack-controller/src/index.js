/**
 * PilotProOS Stack Controller
 * System Health Monitoring and Management Service
 */

const express = require('express');
const cors = require('cors');
const { Server } = require('socket.io');
const http = require('http');
const path = require('path');
const Controller = require('./controller');
const Monitor = require('./monitor');
const API = require('./api');
const WebSocketManager = require('./websocket');
const { authMiddleware, loginHandler, logoutHandler, rateLimit } = require('./auth-middleware');

// Initialize Express app
const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: ["http://localhost:3000", "http://localhost:3005"],
    methods: ["GET", "POST"]
  }
});

// Middleware
app.use(cors());
app.use(express.json());

// Rate limiting for all routes
app.use(rateLimit(900000, 100)); // 100 requests per 15 minutes

// Auth endpoints (before auth middleware)
app.post('/api/auth/login', loginHandler);
app.post('/api/auth/logout', logoutHandler);

// Apply authentication middleware
app.use(authMiddleware);

// Static files (after auth)
app.use(express.static(path.join(__dirname, '../web')));

// Initialize components
const controller = new Controller();
controller.io = io; // Pass socket.io to controller for restart events
const monitor = new Monitor(controller);
const wsManager = new WebSocketManager(io, monitor);
const api = new API(app, controller, monitor);

// Health endpoint for self-monitoring
app.get('/health', (req, res) => {
  res.json({
    status: 'operational',
    service: 'System Controller',
    timestamp: new Date().toISOString()
  });
});

// Start monitoring
async function start() {
  try {
    console.log('[STARTUP] PilotProOS System Controller Starting...');

    // Initialize controller
    await controller.initialize();

    // Start monitoring
    await monitor.startMonitoring();

    // Start WebSocket manager
    wsManager.start();

    // Start server
    const PORT = process.env.CONTROLLER_PORT || 3005;
    server.listen(PORT, () => {
      console.log(`[READY] System Controller running on port ${PORT}`);
      console.log(`[INFO] Dashboard available at http://localhost:${PORT}`);
    });

  } catch (error) {
    console.error('[FATAL] Failed to start System Controller:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('[SHUTDOWN] Shutting down System Controller...');
  await monitor.stopMonitoring();
  server.close(() => {
    console.log('[INFO] System Controller stopped');
    process.exit(0);
  });
});

// Start the controller
start();