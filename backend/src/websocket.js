import { Server } from 'socket.io';

let io = null;

function initializeWebSocket(server) {
  // Get CORS origins from environment variables or defaults
  const corsOrigins = process.env.CORS_ORIGINS 
    ? process.env.CORS_ORIGINS.split(',')
    : [
        process.env.FRONTEND_URL || 'http://localhost:3000',
        'http://localhost:5173',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5173'
      ];
  
  io = new Server(server, {
    cors: {
      origin: corsOrigins,
      methods: ["GET", "POST"],
      credentials: true
    }
  });

  io.on('connection', (socket) => {
    console.log('🔌 New WebSocket client connected:', socket.id);

    // Join room based on tenant
    socket.on('join-tenant', (tenantId) => {
      socket.join(`tenant-${tenantId}`);
      console.log(`Client ${socket.id} joined tenant room: tenant-${tenantId}`);
    });

    // Subscribe to specific data streams
    socket.on('subscribe', (data) => {
      const { type, id } = data;
      socket.join(`${type}-${id}`);
      console.log(`Client ${socket.id} subscribed to ${type}-${id}`);
    });

    // Unsubscribe from data streams
    socket.on('unsubscribe', (data) => {
      const { type, id } = data;
      socket.leave(`${type}-${id}`);
      console.log(`Client ${socket.id} unsubscribed from ${type}-${id}`);
    });

    socket.on('disconnect', () => {
      console.log('❌ Client disconnected:', socket.id);
    });
  });

  return io;
}

// Emit events to specific rooms
function emitToTenant(tenantId, event, data) {
  if (io) {
    io.to(`tenant-${tenantId}`).emit(event, data);
  }
}

function emitToWorkflow(workflowId, event, data) {
  if (io) {
    io.to(`workflow-${workflowId}`).emit(event, data);
  }
}

function emitToAll(event, data) {
  if (io) {
    io.emit(event, data);
  }
}

// Real-time event emitters for different data types
function notifyWorkflowUpdate(workflowId, data) {
  emitToWorkflow(workflowId, 'workflow:updated', data);
}

function notifyExecutionStart(workflowId, executionData) {
  emitToWorkflow(workflowId, 'execution:started', executionData);
  emitToAll('stats:update', { type: 'execution_started' });
}

function notifyExecutionComplete(workflowId, executionData) {
  emitToWorkflow(workflowId, 'execution:completed', executionData);
  emitToAll('stats:update', { type: 'execution_completed', data: executionData });
}

function notifyAlert(alertData) {
  emitToAll('alert:new', alertData);
}

function notifyDatabaseUpdate(tableInfo) {
  emitToAll('database:updated', tableInfo);
}

export {
  initializeWebSocket,
  emitToTenant,
  emitToWorkflow,
  emitToAll,
  notifyWorkflowUpdate,
  notifyExecutionStart,
  notifyExecutionComplete,
  notifyAlert,
  notifyDatabaseUpdate
};