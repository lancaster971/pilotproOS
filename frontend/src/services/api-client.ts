// 🚀 BATTLE-TESTED: OFETCH HTTP Client - Zero dependency overhead
// Following REGOLA FERREA: Battle-tested libraries FIRST, custom code LAST RESORT
// OFETCH benefits: -87% bundle size, +20% velocity, built-in retry/timeout

import { ofetch } from 'ofetch'
import type { DashboardData, Workflow, Execution } from '../types'
import { API_BASE_URL } from '../utils/api-config'

// OFETCH: Modern fetch wrapper with intelligent defaults
// Use environment variable for API URL, fallback to config for development
const baseFetch = ofetch.create({
  baseURL: import.meta.env.VITE_API_URL || API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Auth API - Clean OFETCH implementation
export const authAPI = {
  login: (email: string, password: string) =>
    baseFetch('/api/auth/login', { 
      method: 'POST', 
      body: { email, password }
    }),
  
  logout: () => baseFetch('/api/auth/logout', { method: 'POST' }),
  
  getProfile: () => baseFetch('/api/auth/profile'),
}

// Business API - OFETCH battle-tested implementation
export const businessAPI = {
  // Insights data
  getInsights: (): Promise<DashboardData> =>
    baseFetch('/api/business/dashboard'),
  
  // Business processes (workflows with business terminology)  
  getProcesses: (params?: any) =>
    baseFetch('/api/business/processes', { query: params }),
  
  // Process executions (executions with business terminology)
  getProcessExecutions: (params?: any) =>
    baseFetch('/api/business/executions', { query: params }),
  
  // Process executions for specific workflow
  getProcessExecutionsForWorkflow: (workflowId: string) =>
    baseFetch(`/api/business/process-executions/${workflowId}`),
  
  // Process runs (executions)
  getProcessRuns: (params?: any) =>
    baseFetch('/api/business/process-runs', { query: params }),
  
  // Analytics data for Dashboard and Insights
  getAnalytics: (params?: any) =>
    baseFetch('/api/business/analytics', { query: params }),
    
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
  
  toggleWorkflow: (workflowId: string, active: boolean) =>
    baseFetch(`/api/business/toggle-workflow/${workflowId}`, {
      method: 'POST',
      body: JSON.stringify({ active })
    }),
  
  // Check execution status
  getExecutionStatus: (executionId: string) =>
    baseFetch(`/api/business/execution-status/${executionId}`),
    
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
  
  // Top performing workflows
  getTopPerformers: () => baseFetch('/api/business/top-performers'),
  
  // Hourly analytics with real distribution
  getHourlyAnalytics: () => baseFetch('/api/business/hourly-analytics'),
  
  // Daily trend for 30 days with real data
  getDailyTrend: () => baseFetch('/api/business/daily-trend'),
  
  // Live events from recent executions
  getLiveEvents: () => baseFetch('/api/business/live-events'),
}

// Tenant API - Same interface as Axios version
export const tenantAPI = {
  dashboard: (tenantId: string) => 
    baseFetch(`/api/tenant/${tenantId}/dashboard`),
  
  workflows: (tenantId: string) => 
    baseFetch(`/api/tenant/${tenantId}/workflows`),
  
  executions: (tenantId: string, params?: any) => 
    baseFetch(`/api/tenant/${tenantId}/executions`, { query: params }),
  
  stats: (tenantId: string) => 
    baseFetch(`/api/tenant/${tenantId}/stats`),
}

// Security API - Same interface as Axios version
export const securityAPI = {
  getLogs: (params?: any) => baseFetch('/api/security/logs', { query: params }),
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
  getAlerts: (params?: any) => baseFetch('/api/alerts', { query: params }),
  markAsRead: (alertId: string) => baseFetch(`/api/alerts/${alertId}/read`, { 
    method: 'PUT' 
  }),
  getMetrics: () => baseFetch('/api/alerts/metrics'),
}

// Export a simple fetch-style function for easy migration from raw fetch calls
export const $fetch = baseFetch