// Types - same structure as n8n frontend types

export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'user' | 'viewer'
  tenantId: string
  createdAt: string
  preferences?: Record<string, any>
}

export interface Workflow {
  id: string
  name: string
  active: boolean
  is_archived: boolean
  created_at: string
  updated_at: string
  node_count: number
  execution_count: number
  has_webhook: boolean
  last_execution: string | null
  tags: string[]
  settings: Record<string, any>
}

export interface WorkflowStats {
  total: number
  active: number
  inactive: number
  archived: number
}

export interface Execution {
  id: string
  workflow_id: string
  workflow_name: string
  status: 'success' | 'error' | 'running' | 'waiting' | null
  mode: string
  started_at: string
  stopped_at?: string
  duration_ms?: number
  error_message?: string
  data?: Record<string, any>
}

export interface ExecutionStats {
  total: number
  success: number
  error: number
  running: number
  waiting: number
  successRate: number
  avgDuration: number
}

export interface DashboardData {
  tenant: {
    id: string
    name: string
  }
  stats: {
    workflows: {
      total: number
      active: number
      inactive: number
    }
    executions: {
      total: number
      last24h: number
      successRate: number
      avgDuration: number
    }
  }
  activity: {
    recent: any[]
    hourly: any[]
  }
}

export interface Alert {
  id: string
  type: 'error' | 'warning' | 'info' | 'success'
  severity: 'critical' | 'high' | 'medium' | 'low'
  title: string
  message: string
  source: string
  timestamp: string
  isRead: boolean
  isActive: boolean
  category: 'system' | 'workflow' | 'database' | 'security' | 'performance'
}

// Removed SecurityLog and SchedulerStatus interfaces - functionality not needed

export interface DatabaseTable {
  name: string
  records: number
  size: string
  lastModified: string
  growth: number
}

// Removed AgentWorkflow interface - agents functionality integrated into workflows