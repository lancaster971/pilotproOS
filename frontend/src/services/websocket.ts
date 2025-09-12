import { io, type Socket } from 'socket.io-client';
import { useUIStore } from '../stores/ui';
import { API_BASE_URL } from '../utils/api-config';

class WebSocketService {
  private socket: Socket | null = null;
  private autoRefreshIntervals: Map<string, NodeJS.Timeout> = new Map();
  
  constructor() {
    this.connect();
  }

  connect() {
    // Connect to backend WebSocket server using dynamic configuration
    const wsUrl = import.meta.env.VITE_API_URL || API_BASE_URL;
    this.socket = io(wsUrl, {
      withCredentials: true,
      transports: ['websocket', 'polling']
    });

    this.socket.on('connect', () => {
      console.log('✅ WebSocket connected');
      const uiStore = useUIStore();
      uiStore.showToast('WebSocket', 'Connected to real-time updates', 'success');
      
      // Join tenant room if we have tenant ID
      const tenantId = localStorage.getItem('tenantId');
      if (tenantId) {
        this.socket?.emit('join-tenant', tenantId);
      }
    });

    this.socket.on('disconnect', () => {
      console.log('❌ WebSocket disconnected');
      const uiStore = useUIStore();
      uiStore.showToast('WebSocket', 'Disconnected from real-time updates', 'warning');
    });

    // Listen for real-time events
    this.setupEventListeners();
  }

  private setupEventListeners() {
    if (!this.socket) return;

    // Workflow updates
    this.socket.on('workflow:updated', (data) => {
      console.log('📊 Workflow updated:', data);
      // Trigger refresh of workflow data
      window.dispatchEvent(new CustomEvent('workflow:updated', { detail: data }));
    });

    // Execution events
    this.socket.on('execution:started', (data) => {
      console.log('▶️ Execution started:', data);
      window.dispatchEvent(new CustomEvent('execution:started', { detail: data }));
    });

    this.socket.on('execution:completed', (data) => {
      console.log('✅ Execution completed:', data);
      window.dispatchEvent(new CustomEvent('execution:completed', { detail: data }));
    });

    // Stats updates
    this.socket.on('stats:update', (data) => {
      console.log('📈 Stats update:', data);
      window.dispatchEvent(new CustomEvent('stats:update', { detail: data }));
    });

    // Alert notifications
    this.socket.on('alert:new', (data) => {
      console.log('🚨 New alert:', data);
      const uiStore = useUIStore();
      uiStore.showToast('Alert', data.message || 'New system alert', 'warning');
      window.dispatchEvent(new CustomEvent('alert:new', { detail: data }));
    });

    // Database updates
    this.socket.on('database:updated', (data) => {
      console.log('💾 Database updated:', data);
      window.dispatchEvent(new CustomEvent('database:updated', { detail: data }));
    });
  }

  // Subscribe to specific data stream
  subscribe(type: string, id: string) {
    if (this.socket) {
      this.socket.emit('subscribe', { type, id });
      console.log(`📡 Subscribed to ${type}-${id}`);
    }
  }

  // Unsubscribe from data stream
  unsubscribe(type: string, id: string) {
    if (this.socket) {
      this.socket.emit('unsubscribe', { type, id });
      console.log(`🔕 Unsubscribed from ${type}-${id}`);
    }
  }

  // Auto-refresh functionality
  startAutoRefresh(key: string, callback: () => void, intervalMs: number = 5000) {
    // Clear existing interval if any
    this.stopAutoRefresh(key);
    
    // Start new interval
    const interval = setInterval(callback, intervalMs);
    this.autoRefreshIntervals.set(key, interval);
    console.log(`🔄 Started auto-refresh for ${key} every ${intervalMs}ms`);
  }

  stopAutoRefresh(key: string) {
    const interval = this.autoRefreshIntervals.get(key);
    if (interval) {
      clearInterval(interval);
      this.autoRefreshIntervals.delete(key);
      console.log(`⏹️ Stopped auto-refresh for ${key}`);
    }
  }

  stopAllAutoRefresh() {
    this.autoRefreshIntervals.forEach((interval, key) => {
      clearInterval(interval);
      console.log(`⏹️ Stopped auto-refresh for ${key}`);
    });
    this.autoRefreshIntervals.clear();
  }

  disconnect() {
    this.stopAllAutoRefresh();
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  getSocket(): Socket | null {
    return this.socket;
  }
}

// Create singleton instance
const webSocketService = new WebSocketService();

export default webSocketService;