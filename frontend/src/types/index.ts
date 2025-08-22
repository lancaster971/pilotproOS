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

export interface SecurityLog {
  id: string
  timestamp: string
  event: 'login' | 'logout' | 'failed_login' | 'api_access' | 'data_export' | 'config_change'
  user: string
  userRole: string
  ipAddress: string
  userAgent: string
  location: string
  deviceType: 'desktop' | 'mobile' | 'api' | 'unknown'
  status: 'success' | 'failed' | 'warning'
  details: string
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
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

export interface SchedulerStatus {
  isRunning: boolean
  nextSync?: string
  lastSync?: string
  activeJobs: number
  totalSyncRuns: number
}

export interface DatabaseTable {
  name: string
  records: number
  size: string
  lastModified: string
  growth: number
}

export interface AgentWorkflow {
  id: string
  name: string
  status: 'active' | 'inactive'
  lastActivity: string | null
  lastExecutionId: string | null
  lastExecutionStatus: string
  totalExecutions: number
  hasDetailedData: boolean
  updatedAt: string
  type: 'ai-agent'
  preview?: {
    senderEmail?: string
    subject?: string
    classification?: string
  }
}