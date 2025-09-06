import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { tenantAPI, businessAPI } from '../services/api-client'

// 🔒 Tipi TypeScript per Enterprise Data Layer

export interface Workflow {
  id: string
  name: string
  active: boolean
  tags: string[]
  createdAt: string
  updatedAt: string
  lastExecution?: Execution
  nodeCount: number
  description?: string
  aiAgents?: AIAgent[]
  tenantId: string
}

export interface Execution {
  id: string
  workflowId: string
  status: 'success' | 'error' | 'running' | 'waiting'
  startedAt: string
  finishedAt?: string
  duration?: number
  data?: any
  tenantId: string
}

export interface AIAgent {
  id: string
  name: string
  type: string
  model?: string
  temperature?: number
  workflowId: string
}

export interface Metric {
  type: 'performance' | 'business' | 'system'
  name: string
  value: number
  unit: string
  timestamp: string
  tenantId: string
}

export interface DashboardStats {
  totalWorkflows: number
  activeWorkflows: number
  totalExecutions: number
  successRate: number
  avgExecutionTime: number
  lastUpdated: string
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'error'
  components: {
    database: boolean
    scheduler: boolean
    api: boolean
    memory: number
    cpu: number
  }
  lastChecked: string
}

// 📊 Cache TTL Configuration
const CACHE_TTL = {
  workflows: 60 * 1000,        // 60 secondi per workflows
  executions: 30 * 1000,       // 30 secondi per executions 
  dashboard: 30 * 1000,        // 30 secondi per dashboard stats
  metrics: 60 * 1000,          // 60 secondi per metrics
  timeline: 300 * 1000,        // 5 minuti per timeline (più stabile)
  systemHealth: 15 * 1000,     // 15 secondi per system health
} as const

// 🏗️ Enterprise DataStore State Interface
interface DataStoreState {
  // 📊 Normalized Data Layer - Single Source of Truth
  workflows: Record<string, Workflow>
  executions: Record<string, Execution>
  metrics: Record<string, Metric>
  aiAgents: Record<string, AIAgent>
  dashboardStats: DashboardStats | null
  systemHealth: SystemHealth | null

  // 🔄 Cache Management
  lastSync: Record<string, number>
  syncInProgress: Set<string>
  
  // ⚡ Smart Sync Service Integration
  backgroundSyncEnabled: boolean
  syncInterval: number

  // 🎯 Current Tenant Context
  currentTenantId: string

  // 🛡️ Error Handling & Loading States
  isLoading: boolean
  errors: Record<string, string>

  // 📡 Actions
  setCurrentTenant: (tenantId: string) => void
  syncWorkflows: (force?: boolean) => Promise<void>
  syncExecutions: (force?: boolean) => Promise<void>
  syncDashboard: (force?: boolean) => Promise<void>
  syncMetrics: (force?: boolean) => Promise<void>
  syncSystemHealth: (force?: boolean) => Promise<void>
  syncAll: (force?: boolean) => Promise<void>
  
  // 🔄 Smart Cache Methods
  isDataStale: (dataType: keyof typeof CACHE_TTL) => boolean
  invalidateCache: (dataType?: keyof typeof CACHE_TTL) => void
  clearError: (key: string) => void
  
  // 🎯 Getters Ottimizzati
  getWorkflowsByTenant: (tenantId?: string) => Workflow[]
  getExecutionsByWorkflow: (workflowId: string) => Execution[]
  getAIAgentsByWorkflow: (workflowId: string) => AIAgent[]
  getActiveWorkflows: () => Workflow[]
  getRecentExecutions: (limit?: number) => Execution[]
}

// 🚀 Enterprise DataStore Implementation
export const useDataStore = create<DataStoreState>()(
  subscribeWithSelector((set, get) => ({
    // 📊 Initial State
    workflows: {},
    executions: {},
    metrics: {},
    aiAgents: {},
    dashboardStats: null,
    systemHealth: null,
    
    lastSync: {},
    syncInProgress: new Set(),
    backgroundSyncEnabled: true,
    syncInterval: 60000, // 60 secondi default
    
    currentTenantId: 'client_simulation_a', // Default tenant
    isLoading: false,
    errors: {},

    // 🎯 Actions Implementation
    setCurrentTenant: (tenantId: string) => {
      set({ currentTenantId: tenantId })
      // Invalida cache quando cambia tenant
      get().invalidateCache()
    },

    // 🔄 Smart Cache Checker
    isDataStale: (dataType: keyof typeof CACHE_TTL) => {
      const lastSync = get().lastSync[dataType] || 0
      const ttl = CACHE_TTL[dataType]
      return Date.now() - lastSync > ttl
    },

    // 🧹 Cache Invalidation
    invalidateCache: (dataType?: keyof typeof CACHE_TTL) => {
      if (dataType) {
        set(state => ({
          lastSync: { ...state.lastSync, [dataType]: 0 }
        }))
      } else {
        set({ lastSync: {} })
      }
    },

    // 🛡️ Error Management
    clearError: (key: string) => {
      set(state => {
        const { [key]: removed, ...rest } = state.errors
        return { errors: rest }
      })
    },

    // 📈 Workflows Sync
    syncWorkflows: async (force = false) => {
      const state = get()
      const cacheKey = 'workflows'
      
      if (!force && !state.isDataStale(cacheKey)) {
        console.log(`📋 Workflows cache still fresh, skipping sync`)
        return
      }

      if (state.syncInProgress.has(cacheKey)) {
        console.log(`📋 Workflows sync already in progress`)
        return
      }

      try {
        set(state => ({
          syncInProgress: new Set(state.syncInProgress).add(cacheKey),
          isLoading: true
        }))
        
        state.clearError(cacheKey)
        
        console.log(`📋 Syncing workflows for tenant: ${state.currentTenantId}`)
        const response = await tenantAPI.workflows(state.currentTenantId)
        const workflows = response.data.workflows || []
        
        // Normalizza i workflows nel store
        const normalizedWorkflows: Record<string, Workflow> = {}
        workflows.forEach((workflow: any) => {
          normalizedWorkflows[workflow.id] = {
            id: workflow.id,
            name: workflow.name,
            active: workflow.active,
            tags: workflow.tags || [],
            createdAt: workflow.createdAt,
            updatedAt: workflow.updatedAt,
            nodeCount: workflow.nodeCount || 0,
            description: workflow.description,
            tenantId: state.currentTenantId,
            lastExecution: workflow.lastExecution
          }
        })

        set(state => ({
          workflows: { ...state.workflows, ...normalizedWorkflows },
          lastSync: { ...state.lastSync, [cacheKey]: Date.now() },
          syncInProgress: new Set([...state.syncInProgress].filter(k => k !== cacheKey)),
          isLoading: false
        }))

        console.log(`✅ Synced ${workflows.length} workflows`)
        
      } catch (error: any) {
        console.error(`❌ Workflows sync failed:`, error)
        set(state => ({
          errors: { ...state.errors, [cacheKey]: error.message },
          syncInProgress: new Set([...state.syncInProgress].filter(k => k !== cacheKey)),
          isLoading: false
        }))
      }
    },

    // ⚡ Executions Sync
    syncExecutions: async (force = false) => {
      const state = get()
      const cacheKey = 'executions'
      
      if (!force && !state.isDataStale(cacheKey)) {
        console.log(`⚡ Executions cache still fresh, skipping sync`)
        return
      }

      if (state.syncInProgress.has(cacheKey)) return

      try {
        set(state => ({
          syncInProgress: new Set(state.syncInProgress).add(cacheKey)
        }))
        
        state.clearError(cacheKey)
        
        console.log(`⚡ Syncing executions for tenant: ${state.currentTenantId}`)
        const response = await tenantAPI.executions(state.currentTenantId, { limit: 100 })
        const executions = response.data.executions || []
        
        const normalizedExecutions: Record<string, Execution> = {}
        executions.forEach((execution: any) => {
          normalizedExecutions[execution.id] = {
            id: execution.id,
            workflowId: execution.workflowId,
            status: execution.status,
            startedAt: execution.startedAt,
            finishedAt: execution.finishedAt,
            duration: execution.duration,
            data: execution.data,
            tenantId: state.currentTenantId
          }
        })

        set(state => ({
          executions: { ...state.executions, ...normalizedExecutions },
          lastSync: { ...state.lastSync, [cacheKey]: Date.now() },
          syncInProgress: new Set([...state.syncInProgress].filter(k => k !== cacheKey))
        }))

        console.log(`✅ Synced ${executions.length} executions`)
        
      } catch (error: any) {
        console.error(`❌ Executions sync failed:`, error)
        set(state => ({
          errors: { ...state.errors, [cacheKey]: error.message },
          syncInProgress: new Set([...state.syncInProgress].filter(k => k !== cacheKey))
        }))
      }
    },

    // 📊 Dashboard Sync
    syncDashboard: async (force = false) => {
      const state = get()
      const cacheKey = 'dashboard'
      
      if (!force && !state.isDataStale(cacheKey)) {
        console.log(`📊 Dashboard cache still fresh, skipping sync`)
        return
      }

      if (state.syncInProgress.has(cacheKey)) return

      try {
        set(state => ({
          syncInProgress: new Set(state.syncInProgress).add(cacheKey)
        }))
        
        state.clearError(cacheKey)
        
        console.log(`📊 Syncing dashboard for tenant: ${state.currentTenantId}`)
        const response = await tenantAPI.dashboard(state.currentTenantId)
        const stats = response.data
        
        const dashboardStats: DashboardStats = {
          totalWorkflows: stats.totalWorkflows || 0,
          activeWorkflows: stats.activeWorkflows || 0,
          totalExecutions: stats.totalExecutions || 0,
          successRate: stats.successRate || 0,
          avgExecutionTime: stats.avgExecutionTime || 0,
          lastUpdated: new Date().toISOString()
        }

        set(state => ({
          dashboardStats,
          lastSync: { ...state.lastSync, [cacheKey]: Date.now() },
          syncInProgress: new Set([...state.syncInProgress].filter(k => k !== cacheKey))
        }))

        console.log(`✅ Synced dashboard stats`)
        
      } catch (error: any) {
        console.error(`❌ Dashboard sync failed:`, error)
        set(state => ({
          errors: { ...state.errors, [cacheKey]: error.message },
          syncInProgress: new Set([...state.syncInProgress].filter(k => k !== cacheKey))
        }))
      }
    },

    // 🛡️ System Health Sync
    syncSystemHealth: async (force = false) => {
      const state = get()
      const cacheKey = 'systemHealth'
      
      if (!force && !state.isDataStale(cacheKey)) return
      if (state.syncInProgress.has(cacheKey)) return

      try {
        set(state => ({
          syncInProgress: new Set(state.syncInProgress).add(cacheKey)
        }))
        
        state.clearError(cacheKey)
        
        const response = await monitoringAPI.health()
        const health = response.data
        
        const systemHealth: SystemHealth = {
          status: health.status,
          components: health.components || {},
          lastChecked: new Date().toISOString()
        }

        set(state => ({
          systemHealth,
          lastSync: { ...state.lastSync, [cacheKey]: Date.now() },
          syncInProgress: new Set([...state.syncInProgress].filter(k => k !== cacheKey))
        }))
        
      } catch (error: any) {
        console.error(`❌ System health sync failed:`, error)
        set(state => ({
          errors: { ...state.errors, [cacheKey]: error.message },
          syncInProgress: new Set([...state.syncInProgress].filter(k => k !== cacheKey))
        }))
      }
    },

    // 📈 Metrics Sync (placeholder)
    syncMetrics: async (force = false) => {
      const state = get()
      const cacheKey = 'metrics'
      
      if (!force && !state.isDataStale(cacheKey)) return
      if (state.syncInProgress.has(cacheKey)) return

      try {
        set(state => ({
          syncInProgress: new Set(state.syncInProgress).add(cacheKey)
        }))
        
        // TODO: Implementare metrics API quando sarà disponibile
        console.log(`📈 Metrics sync not implemented yet`)
        
        set(state => ({
          lastSync: { ...state.lastSync, [cacheKey]: Date.now() },
          syncInProgress: new Set([...state.syncInProgress].filter(k => k !== cacheKey))
        }))
        
      } catch (error: any) {
        console.error(`❌ Metrics sync failed:`, error)
        set(state => ({
          errors: { ...state.errors, [cacheKey]: error.message },
          syncInProgress: new Set([...state.syncInProgress].filter(k => k !== cacheKey))
        }))
      }
    },

    // 🚀 Sync All Data
    syncAll: async (force = false) => {
      const state = get()
      console.log(`🔄 Starting full sync${force ? ' (forced)' : ''} for tenant: ${state.currentTenantId}`)
      
      // Sync in parallel per massima performance
      await Promise.allSettled([
        state.syncWorkflows(force),
        state.syncExecutions(force),
        state.syncDashboard(force),
        state.syncSystemHealth(force),
        state.syncMetrics(force)
      ])
      
      console.log(`✅ Full sync completed`)
    },

    // 🎯 Optimized Getters
    getWorkflowsByTenant: (tenantId?: string) => {
      const state = get()
      const targetTenant = tenantId || state.currentTenantId
      return Object.values(state.workflows).filter(w => w.tenantId === targetTenant)
    },

    getExecutionsByWorkflow: (workflowId: string) => {
      const state = get()
      return Object.values(state.executions)
        .filter(e => e.workflowId === workflowId)
        .sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime())
    },

    getAIAgentsByWorkflow: (workflowId: string) => {
      const state = get()
      return Object.values(state.aiAgents).filter(a => a.workflowId === workflowId)
    },

    getActiveWorkflows: () => {
      const state = get()
      return state.getWorkflowsByTenant().filter(w => w.active)
    },

    getRecentExecutions: (limit = 10) => {
      const state = get()
      return Object.values(state.executions)
        .filter(e => e.tenantId === state.currentTenantId)
        .sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime())
        .slice(0, limit)
    }
  }))
)

// 🔄 Smart Background Sync Service
let backgroundSyncTimer: NodeJS.Timeout | null = null

export const startBackgroundSync = () => {
  const store = useDataStore.getState()
  
  if (backgroundSyncTimer) {
    clearInterval(backgroundSyncTimer)
  }
  
  console.log(`🔄 Starting background sync every ${store.syncInterval}ms`)
  
  backgroundSyncTimer = setInterval(() => {
    const currentState = useDataStore.getState()
    if (currentState.backgroundSyncEnabled) {
      console.log(`🔄 Background sync triggered`)
      currentState.syncAll(false) // Non-forced sync, rispetta cache TTL
    }
  }, store.syncInterval)
  
  // Initial sync
  store.syncAll(true)
}

export const stopBackgroundSync = () => {
  if (backgroundSyncTimer) {
    clearInterval(backgroundSyncTimer)
    backgroundSyncTimer = null
    console.log(`⏹️ Background sync stopped`)
  }
}

// 🎯 Store Selectors per Performance
export const selectWorkflows = (state: DataStoreState) => state.getWorkflowsByTenant()
export const selectDashboardStats = (state: DataStoreState) => state.dashboardStats
export const selectSystemHealth = (state: DataStoreState) => state.systemHealth
export const selectRecentExecutions = (state: DataStoreState) => state.getRecentExecutions()
export const selectIsLoading = (state: DataStoreState) => state.isLoading
export const selectErrors = (state: DataStoreState) => state.errors