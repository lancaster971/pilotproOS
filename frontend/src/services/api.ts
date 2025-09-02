import axios from 'axios'
import type { DashboardData, Workflow, Execution } from '../types'

// API Client configuration - same pattern as n8n
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:3001',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
})

// Request interceptor for auth token - same as n8n approach
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('pilotpro_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling - same as n8n
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('pilotpro_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (email: string, password: string) =>
    apiClient.post('/auth/login', { email, password }),
  
  logout: () => apiClient.post('/auth/logout'),
  
  getProfile: () => apiClient.get('/auth/profile'),
}

// Business API - using our PilotProOS endpoints with business terminology
export const businessAPI = {
  // Insights data
  getInsights: (): Promise<{ data: DashboardData }> =>
    apiClient.get('/api/business/dashboard'),
  
  // Business processes (workflows with business terminology)
  getProcesses: () => apiClient.get('/api/business/processes'),
  
  // Process executions (executions with business terminology)
  getProcessExecutions: (params?: any) => 
    apiClient.get('/api/business/executions', { params }),
  
  // Analytics and stats
  getAnalytics: () => apiClient.get('/api/business/analytics'),
  
  // System health
  getHealth: () => apiClient.get('/health'),
  
  // Compatibility info
  getCompatibility: () => apiClient.get('/api/system/compatibility'),
}

// Tenant API - for multi-tenant operations (future use)
export const tenantAPI = {
  dashboard: (tenantId: string) => 
    apiClient.get(`/api/tenant/${tenantId}/dashboard`),
  
  workflows: (tenantId: string) => 
    apiClient.get(`/api/tenant/${tenantId}/workflows`),
  
  executions: (tenantId: string, params?: any) => 
    apiClient.get(`/api/tenant/${tenantId}/executions`, { params }),
  
  stats: (tenantId: string) => 
    apiClient.get(`/api/tenant/${tenantId}/stats`),
}

// Security API
export const securityAPI = {
  getLogs: (params?: any) => apiClient.get('/api/security/logs', { params }),
  getMetrics: () => apiClient.get('/api/security/metrics'),
  getApiKeys: () => apiClient.get('/api/security/api-keys'),
}

// Database API
export const databaseAPI = {
  getStats: () => apiClient.get('/api/database/stats'),
  getTables: () => apiClient.get('/api/database/tables'),
  getActivity: () => apiClient.get('/api/database/activity'),
}

// Scheduler API
export const schedulerAPI = {
  getStatus: () => apiClient.get('/api/scheduler/status'),
  start: () => apiClient.post('/api/scheduler/start'),
  stop: () => apiClient.post('/api/scheduler/stop'),
  getLogs: () => apiClient.get('/api/scheduler/logs'),
}

// AI Agents API - for agent transparency
export const agentsAPI = {
  getWorkflows: (tenantId: string) => 
    apiClient.get(`/api/tenant/${tenantId}/agents/workflows`),
  
  getTimeline: (tenantId: string, workflowId: string) => 
    apiClient.get(`/api/tenant/${tenantId}/agents/workflow/${workflowId}/timeline`),
  
  refresh: (tenantId: string, workflowId: string) => 
    apiClient.post(`/api/tenant/${tenantId}/agents/workflow/${workflowId}/refresh`),
}

// Alerts API
export const alertsAPI = {
  getAlerts: (params?: any) => apiClient.get('/api/alerts', { params }),
  markAsRead: (alertId: string) => apiClient.put(`/api/alerts/${alertId}/read`),
  getMetrics: () => apiClient.get('/api/alerts/metrics'),
}

export { apiClient }