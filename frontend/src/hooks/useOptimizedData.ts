// 🚀 Optimized Data Hooks - Enterprise Frontend Architecture
// Sostituisce 19+ useQuery frammentate con hook intelligenti e performance ottimizzate

import { useEffect, useMemo } from 'react'
import { useDataStore } from '../store/dataStore'
import { useSmartSync } from '../services/smartSyncService'
import { aiAgentsAPI } from '../services/api'

// 🎯 Interfacce per hook return types
interface UseWorkflowsReturn {
  workflows: any[]
  activeWorkflows: any[]
  isLoading: boolean
  error: string | null
  refresh: () => void
  lastUpdated: number
}

interface UseDashboardReturn {
  stats: any
  systemHealth: any
  recentExecutions: any[]
  recentActivity: any[]
  isLoading: boolean
  error: string | null
  refresh: () => void
  lastUpdated: number
}

interface UseTimelineReturn {
  timeline: any[]
  businessContext: any
  isLoading: boolean
  error: string | null
  refresh: () => void
  forceRefresh: () => void
}

interface UseExecutionsReturn {
  executions: any[]
  workflowExecutions: (workflowId: string) => any[]
  isLoading: boolean
  error: string | null
  refresh: () => void
  lastUpdated: number
}

// 📋 useWorkflows - Hook centralizzato per workflows
export const useWorkflows = (tenantId?: string): UseWorkflowsReturn => {
  const store = useDataStore()
  
  // Auto-sync on mount e quando cambia tenant
  useEffect(() => {
    if (tenantId && tenantId !== store.currentTenantId) {
      store.setCurrentTenant(tenantId)
    }
    
    // Trigger initial sync se dati non presenti
    const workflows = store.getWorkflowsByTenant()
    if (workflows.length === 0 || store.isDataStale('workflows')) {
      store.syncWorkflows(false)
    }
  }, [tenantId, store.currentTenantId])

  const workflows = useMemo(() => store.getWorkflowsByTenant(), [store.workflows, store.currentTenantId])
  const activeWorkflows = useMemo(() => store.getActiveWorkflows(), [store.workflows, store.currentTenantId])
  
  return {
    workflows,
    activeWorkflows,
    isLoading: store.isLoading,
    error: store.errors.workflows || null,
    refresh: () => store.syncWorkflows(true),
    lastUpdated: store.lastSync.workflows || 0
  }
}

// 📊 useDashboard - Hook centralizzato per dashboard
export const useDashboard = (tenantId?: string): UseDashboardReturn => {
  const store = useDataStore()
  
  useEffect(() => {
    if (tenantId && tenantId !== store.currentTenantId) {
      store.setCurrentTenant(tenantId)
    }
    
    // Sync dashboard se stale
    if (!store.dashboardStats || store.isDataStale('dashboard')) {
      store.syncDashboard(false)
    }
    
    // Sync system health se stale
    if (!store.systemHealth || store.isDataStale('systemHealth')) {
      store.syncSystemHealth(false)
    }
    
    // Sync recent executions se stale
    if (store.isDataStale('executions')) {
      store.syncExecutions(false)
    }
  }, [tenantId, store.currentTenantId])

  const recentExecutions = useMemo(() => store.getRecentExecutions(5), [store.executions, store.currentTenantId])
  
  // Simula recent activity dal executions
  const recentActivity = useMemo(() => {
    return recentExecutions.map(execution => ({
      id: execution.id,
      type: 'execution',
      action: execution.status === 'success' ? 'Execution completed' : 'Execution failed',
      workflowName: store.workflows[execution.workflowId]?.name || 'Unknown Workflow',
      timestamp: execution.startedAt,
      status: execution.status
    }))
  }, [recentExecutions, store.workflows])
  
  return {
    stats: store.dashboardStats,
    systemHealth: store.systemHealth,
    recentExecutions,
    recentActivity,
    isLoading: store.isLoading,
    error: store.errors.dashboard || store.errors.systemHealth || null,
    refresh: () => {
      store.syncDashboard(true)
      store.syncSystemHealth(true)
      store.syncExecutions(true)
    },
    lastUpdated: Math.min(store.lastSync.dashboard || 0, store.lastSync.systemHealth || 0)
  }
}

// ⚡ useExecutions - Hook centralizzato per executions
export const useExecutions = (tenantId?: string): UseExecutionsReturn => {
  const store = useDataStore()
  
  useEffect(() => {
    if (tenantId && tenantId !== store.currentTenantId) {
      store.setCurrentTenant(tenantId)
    }
    
    // Sync executions se stale
    if (store.isDataStale('executions')) {
      store.syncExecutions(false)
    }
  }, [tenantId, store.currentTenantId])

  const executions = useMemo(() => {
    return Object.values(store.executions)
      .filter(e => e.tenantId === store.currentTenantId)
      .sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime())
  }, [store.executions, store.currentTenantId])

  const workflowExecutions = useMemo(() => {
    return (workflowId: string) => store.getExecutionsByWorkflow(workflowId)
  }, [store.executions])
  
  return {
    executions,
    workflowExecutions,
    isLoading: store.isLoading,
    error: store.errors.executions || null,
    refresh: () => store.syncExecutions(true),
    lastUpdated: store.lastSync.executions || 0
  }
}

// 🤖 useAgentTimeline - Hook per AI Agent Timeline (specifico)
export const useAgentTimeline = (workflowId: string, tenantId?: string): UseTimelineReturn => {
  const store = useDataStore()
  const { syncForModal } = useSmartSync()
  
  useEffect(() => {
    if (tenantId && tenantId !== store.currentTenantId) {
      store.setCurrentTenant(tenantId)
    }
    
    // Trigger modal-specific sync
    if (workflowId) {
      syncForModal('agent', workflowId)
    }
  }, [workflowId, tenantId, store.currentTenantId])

  // TODO: Implementa timeline cache nel dataStore
  // Per ora usa API diretta ma con cache management
  const [timeline, setTimeline] = React.useState<any[]>([])
  const [businessContext, setBusinessContext] = React.useState<any>(null)
  const [isLoading, setIsLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  const fetchTimeline = async (force = false) => {
    if (!workflowId) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await aiAgentsAPI.getWorkflowTimeline(store.currentTenantId, workflowId, force)
      const data = response.data
      
      setTimeline(data.timeline || [])
      setBusinessContext(data.businessContext || null)
      
    } catch (err: any) {
      console.error('Timeline fetch failed:', err)
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchTimeline(false)
  }, [workflowId, store.currentTenantId])
  
  return {
    timeline,
    businessContext,
    isLoading,
    error,
    refresh: () => fetchTimeline(false),
    forceRefresh: () => fetchTimeline(true)
  }
}

// 📊 useStats - Hook centralizzato per statistics
export const useStats = (tenantId?: string) => {
  const store = useDataStore()
  
  useEffect(() => {
    if (tenantId && tenantId !== store.currentTenantId) {
      store.setCurrentTenant(tenantId)
    }
    
    // Sync tutti i dati needed per stats
    if (store.isDataStale('dashboard')) {
      store.syncDashboard(false)
    }
    
    if (store.isDataStale('workflows')) {
      store.syncWorkflows(false)
    }
    
    if (store.isDataStale('executions')) {
      store.syncExecutions(false)
    }
  }, [tenantId, store.currentTenantId])

  // Calcola statistiche avanzate dai dati normalizzati
  const stats = useMemo(() => {
    const workflows = store.getWorkflowsByTenant()
    const executions = Object.values(store.executions)
      .filter(e => e.tenantId === store.currentTenantId)
    
    const today = new Date()
    const last24h = new Date(today.getTime() - 24 * 60 * 60 * 1000)
    const last7d = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
    
    const executions24h = executions.filter(e => new Date(e.startedAt) > last24h)
    const executions7d = executions.filter(e => new Date(e.startedAt) > last7d)
    
    return {
      // Base stats
      totalWorkflows: workflows.length,
      activeWorkflows: workflows.filter(w => w.active).length,
      totalExecutions: executions.length,
      
      // Rates
      successRate: executions.length > 0 
        ? executions.filter(e => e.status === 'success').length / executions.length * 100 
        : 0,
      
      // Performance
      avgExecutionTime: executions.length > 0
        ? executions.reduce((sum, e) => sum + (e.duration || 0), 0) / executions.length
        : 0,
      
      // Trend data
      executions24h: executions24h.length,
      executions7d: executions7d.length,
      
      // Top workflows
      topWorkflows: workflows
        .map(w => ({
          ...w,
          executionCount: executions.filter(e => e.workflowId === w.id).length
        }))
        .sort((a, b) => b.executionCount - a.executionCount)
        .slice(0, 10)
    }
  }, [store.workflows, store.executions, store.currentTenantId])
  
  return {
    stats,
    isLoading: store.isLoading,
    error: store.errors.dashboard || store.errors.workflows || store.errors.executions || null,
    refresh: () => {
      store.syncDashboard(true)
      store.syncWorkflows(true)
      store.syncExecutions(true)
    },
    lastUpdated: Math.min(
      store.lastSync.dashboard || 0, 
      store.lastSync.workflows || 0, 
      store.lastSync.executions || 0
    )
  }
}

// 🔄 useAutoRefresh - Hook per auto-refresh intelligente
export const useAutoRefresh = (
  refreshFn: () => void, 
  intervalMs: number = 60000, 
  dependencies: any[] = []
) => {
  const { onWindowFocus } = useSmartSync()
  
  useEffect(() => {
    // Auto refresh interval
    const interval = setInterval(refreshFn, intervalMs)
    
    // Refresh on window focus
    const handleFocus = () => {
      onWindowFocus()
      refreshFn()
    }
    
    window.addEventListener('focus', handleFocus)
    
    return () => {
      clearInterval(interval)
      window.removeEventListener('focus', handleFocus)
    }
  }, dependencies)
}

// 🛡️ useSafeData - Hook con error boundaries per safety
export const useSafeData = <T>(
  dataFetcher: () => T,
  fallback: T,
  errorHandler?: (error: Error) => void
): T => {
  try {
    return dataFetcher() || fallback
  } catch (error) {
    console.error('Data fetching error:', error)
    if (errorHandler) {
      errorHandler(error as Error)
    }
    return fallback
  }
}

// React import fix
import React from 'react'