// PilotProOS API Service - Business Process Operating System
// Simplified API service adapted from PilotProMT enterprise codebase
import axios from 'axios';

// API instance configured for PilotProOS backend
const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production' 
    ? '/api' 
    : 'http://localhost:3001/api',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor per JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('pilotpros_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor per error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('pilotpros_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// BUSINESS API ENDPOINTS (Anonimized)
// ============================================================================

export const businessAPI = {
  // Business Processes (ex-workflows anonimized)
  getBusinessProcesses: async () => {
    const response = await api.get('/business/processes');
    return response.data;
  },
  
  getBusinessProcess: async (processId: string) => {
    const response = await api.get(`/business/processes/${processId}`);
    return response.data;
  },
  
  triggerBusinessProcess: async (processId: string, data: any) => {
    const response = await api.post(`/business/processes/${processId}/trigger`, data);
    return response.data;
  },
  
  // Process Runs (ex-executions anonimized)
  getProcessRuns: async (filters: any = {}) => {
    const response = await api.get('/business/process-runs', { params: filters });
    return response.data;
  },
  
  getProcessRun: async (runId: string) => {
    const response = await api.get(`/business/process-runs/${runId}`);
    return response.data;
  },
  
  // Business Analytics
  getBusinessAnalytics: async () => {
    const response = await api.get('/business/analytics');
    return response.data;
  },
  
  getPerformanceReport: async (timeframe: string = '7d') => {
    const response = await api.get('/business/reports/performance', { 
      params: { timeframe } 
    });
    return response.data;
  },
  
  getBusinessInsights: async () => {
    const response = await api.get('/business/insights');
    return response.data;
  }
};

// ============================================================================
// AI AGENT API
// ============================================================================

export const aiAgentAPI = {
  // Chat with AI Assistant
  sendChatMessage: async (query: string, context: any = {}) => {
    const response = await api.post('/ai-agent/chat', {
      query,
      context: {
        ...context,
        timestamp: new Date().toISOString(),
        sessionId: context.sessionId || generateSessionId()
      }
    });
    return response.data;
  },
  
  // Get chat history
  getChatHistory: async (sessionId: string) => {
    const response = await api.get(`/ai-agent/history/${sessionId}`);
    return response.data;
  },
  
  // AI Agent health check
  getAgentStatus: async () => {
    const response = await api.get('/ai-agent/status');
    return response.data;
  }
};

// ============================================================================
// SYSTEM API
// ============================================================================

export const systemAPI = {
  // System health
  getSystemHealth: async () => {
    const response = await api.get('/health');
    return response.data;
  },
  
  // System status
  getSystemStatus: async () => {
    const response = await api.get('/system/status');
    return response.data;
  },
  
  // System metrics
  getSystemMetrics: async () => {
    const response = await api.get('/system/metrics');
    return response.data;
  }
};

// ============================================================================
// AUTHENTICATION API (Simplified)
// ============================================================================

export const authAPI = {
  // Login
  login: async (credentials: { email: string; password: string }) => {
    const response = await api.post('/auth/login', credentials);
    
    if (response.data.token) {
      localStorage.setItem('pilotpros_token', response.data.token);
      localStorage.setItem('pilotpros_user', JSON.stringify(response.data.user));
    }
    
    return response.data;
  },
  
  // Logout
  logout: async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      localStorage.removeItem('pilotpros_token');
      localStorage.removeItem('pilotpros_user');
    }
  },
  
  // Get current user profile
  getProfile: async () => {
    const response = await api.get('/auth/profile');
    return response.data;
  },
  
  // Refresh token
  refreshToken: async () => {
    const response = await api.post('/auth/refresh');
    if (response.data.token) {
      localStorage.setItem('pilotpros_token', response.data.token);
    }
    return response.data;
  }
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// Generate unique session ID for AI chat
function generateSessionId(): string {
  return `pilotpros_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Format business data for display
export const formatters = {
  // Format duration for business display
  formatDuration: (milliseconds: number): string => {
    if (milliseconds < 1000) return `${milliseconds}ms`;
    const seconds = Math.round(milliseconds / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.round(seconds / 60);
    return `${minutes}m`;
  },
  
  // Format success rate
  formatSuccessRate: (rate: number): string => {
    return `${rate.toFixed(1)}%`;
  },
  
  // Format business status
  formatBusinessStatus: (status: string): string => {
    const statusMap = {
      'completed': 'Completato',
      'running': 'In Esecuzione',
      'failed': 'Richiede Attenzione',
      'paused': 'In Pausa'
    };
    return statusMap[status] || status;
  },
  
  // Format date for business display
  formatBusinessDate: (date: string | Date): string => {
    return new Date(date).toLocaleString('it-IT', {
      year: 'numeric',
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
};

// Error handling utility
export const handleAPIError = (error: any) => {
  console.error('API Error:', error);
  
  if (error.response) {
    // Server responded with error status
    return {
      message: error.response.data?.error || 'Server error',
      status: error.response.status,
      details: error.response.data?.details
    };
  } else if (error.request) {
    // Request was made but no response
    return {
      message: 'Sistema non raggiungibile. Verifica la connessione.',
      status: 0,
      details: 'Network error'
    };
  } else {
    // Something else happened
    return {
      message: 'Errore di sistema inatteso',
      status: -1,
      details: error.message
    };
  }
};

// Default export per compatibility
export default {
  businessAPI,
  aiAgentAPI,
  systemAPI,
  authAPI,
  formatters,
  handleAPIError
};