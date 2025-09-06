// 🚀 Basic Fetch API Client - Unified HTTP client for PilotProOS
// Replaces Axios (15.2KB) + mixed fetch calls with native fetch (0KB)
// Lightweight, fast, and reliable

import type { DashboardData, Workflow, Execution } from '../types'

// Helper function for basic fetch API calls
const baseFetch = async (endpoint: string, options: RequestInit & { params?: any } = {}) => {
  let url = `http://localhost:3001${endpoint}`
  
  // Handle query parameters
  if (options.params) {
    const searchParams = new URLSearchParams()
    Object.keys(options.params).forEach(key => {
      if (options.params[key] !== undefined) {
        searchParams.append(key, String(options.params[key]))
      }
    })
    if (searchParams.toString()) {
      url += `?${searchParams.toString()}`
    }
  }
  
  // Remove params from options before passing to fetch
  const { params, ...fetchOptions } = options
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...fetchOptions.headers
    },
    ...fetchOptions
  })
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }
  
  return response.json()
}

// Auth API - Clean implementation with basic fetch
export const authAPI = {
  login: (email: string, password: string) =>
    baseFetch('/auth/login', { 
      method: 'POST', 
      body: JSON.stringify({ email, password })
    }),
  
  logout: () => baseFetch('/auth/logout', { method: 'POST' }),
  
  getProfile: () => baseFetch('/auth/profile'),
}

// Business API - Converted to basic fetch (OFETCH replacement)
export const businessAPI = {
  // Insights data
  getInsights: (): Promise<DashboardData> =>
    baseFetch('/api/business/dashboard'),
  
  // Business processes (workflows with business terminology)  
  getProcesses: (params?: any) =>
    baseFetch('/api/business/processes', { params }),
  
  // Process executions (executions with business terminology)
  getProcessExecutions: (params?: any) =>
    baseFetch('/api/business/executions', { params }),
  
  // Process executions for specific workflow
  getProcessExecutionsForWorkflow: (workflowId: string) =>
    baseFetch(`/api/business/process-executions/${workflowId}`),
  
  // Process runs (executions)
  getProcessRuns: (params?: any) =>
    baseFetch('/api/business/process-runs', { params }),
  
  // Analytics data for Dashboard and Insights
  getAnalytics: (params?: any) =>
    baseFetch('/api/business/analytics', { params }),
    
  // Automation insights  
  getAutomationInsights: () =>
    baseFetch('/api/business/automation-insights'),
    
  // Statistics
  getStatistics: () =>
    baseFetch('/api/business/statistics'),
    
  // Integration health
  getIntegrationHealth: () =>
    baseFetch('/api/business/integration-health'),
  
  // Workflow operations - NEW unified endpoints
  executeWorkflow: (workflowId: string) =>
    baseFetch(`/api/business/execute-workflow/${workflowId}`, {
      method: 'POST'
    }),
  
  stopWorkflow: (workflowId: string) =>
    baseFetch(`/api/business/stop-workflow/${workflowId}`, {
      method: 'POST'
    }),
  
  toggleWorkflow: (workflowId: string) =>
    baseFetch(`/api/business/toggle-workflow/${workflowId}`, {
      method: 'POST'
    }),
  
  // Get workflow details for modal
  getWorkflowDetails: (workflowId: string) =>
    baseFetch(`/api/business/raw-data-for-modal/${workflowId}`),
  
  // Force refresh process
  refreshProcess: (workflowId: string) =>
    baseFetch(`/api/business/process-refresh/${workflowId}`, {
      method: 'POST'
    }),
  
  // Get process details
  getProcessDetails: (workflowId: string) =>
    baseFetch(`/api/business/process-details/${workflowId}`),
  
  // System health
  getHealth: () => baseFetch('/health'),
  
  // Compatibility info
  getCompatibility: () => baseFetch('/api/system/compatibility'),
}

// Tenant API - Same interface as Axios version
export const tenantAPI = {
  dashboard: (tenantId: string) => 
    baseFetch(`/api/tenant/${tenantId}/dashboard`),
  
  workflows: (tenantId: string) => 
    baseFetch(`/api/tenant/${tenantId}/workflows`),
  
  executions: (tenantId: string, params?: any) => 
    baseFetch(`/api/tenant/${tenantId}/executions`, { params }),
  
  stats: (tenantId: string) => 
    baseFetch(`/api/tenant/${tenantId}/stats`),
}

// Security API - Same interface as Axios version
export const securityAPI = {
  getLogs: (params?: any) => baseFetch('/api/security/logs', { params }),
  getMetrics: () => baseFetch('/api/security/metrics'),
  getApiKeys: () => baseFetch('/api/security/api-keys'),
}

// Database API - Same interface as Axios version
export const databaseAPI = {
  getStats: () => baseFetch('/api/database/stats'),
  getTables: () => baseFetch('/api/database/tables'),
  getActivity: () => baseFetch('/api/database/activity'),
}

// Scheduler API - Same interface as Axios version
export const schedulerAPI = {
  getStatus: () => baseFetch('/api/scheduler/status'),
  start: () => baseFetch('/api/scheduler/start', { method: 'POST' }),
  stop: () => baseFetch('/api/scheduler/stop', { method: 'POST' }),
  getLogs: () => baseFetch('/api/scheduler/logs'),
}

// AI Agents API - Same interface as Axios version
export const agentsAPI = {
  getWorkflows: (tenantId: string) => 
    baseFetch(`/api/tenant/${tenantId}/agents/workflows`),
  
  getTimeline: (tenantId: string, workflowId: string) => 
    baseFetch(`/api/tenant/${tenantId}/agents/workflow/${workflowId}/timeline`),
  
  refresh: (tenantId: string, workflowId: string) => 
    baseFetch(`/api/tenant/${tenantId}/agents/workflow/${workflowId}/refresh`, {
      method: 'POST'
    }),
}

// Alerts API - Same interface as Axios version
export const alertsAPI = {
  getAlerts: (params?: any) => baseFetch('/api/alerts', { params }),
  markAsRead: (alertId: string) => baseFetch(`/api/alerts/${alertId}/read`, { 
    method: 'PUT' 
  }),
  getMetrics: () => baseFetch('/api/alerts/metrics'),
}

// Export a simple fetch-style function for easy migration from raw fetch calls
export const $fetch = baseFetch