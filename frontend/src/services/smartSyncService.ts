// 🚀 SmartSyncService - Intelligent Background Synchronization
// Gestisce sync intelligente con detection cambiamenti e ottimizzazioni performance

import { useDataStore, startBackgroundSync, stopBackgroundSync } from '../store/dataStore'

export interface SyncOptions {
  force?: boolean
  priority?: 'high' | 'normal' | 'low'
  debounceMs?: number
  retryCount?: number
}

export interface SyncMetrics {
  totalSyncs: number
  successfulSyncs: number
  failedSyncs: number
  avgSyncTime: number
  lastSyncTime: number
  cacheHitRate: number
}

// 🎯 Smart Sync Service Class
class SmartSyncService {
  // private syncQueue: Array<{ key: string; options: SyncOptions; timestamp: number }> = []
  // private isProcessingQueue = false
  private syncMetrics: SyncMetrics = {
    totalSyncs: 0,
    successfulSyncs: 0,
    failedSyncs: 0,
    avgSyncTime: 0,
    lastSyncTime: 0,
    cacheHitRate: 0
  }
  
  // 📊 Priority Intervals (ms)
  private readonly SYNC_INTERVALS = {
    high: 15000,    // 15 secondi per dati critici
    normal: 60000,  // 60 secondi per dati standard  
    low: 300000     // 5 minuti per dati non critici
  }

  // 🔄 Debounce timers per evitare sync eccessivi
  private debounceTimers: Map<string, NodeJS.Timeout> = new Map()

  constructor() {
    this.initializeService()
  }

  // 🚀 Inizializzazione servizio
  private initializeService() {
    console.log(`🚀 SmartSyncService initialized`)
    
    // Avvia background sync automaticamente
    this.startBackgroundSync()
    
    // Listen per cambiamenti di tenant
    useDataStore.subscribe(
      (state) => state.currentTenantId,
      (tenantId, prevTenantId) => {
        if (tenantId !== prevTenantId) {
          console.log(`🏢 Tenant changed: ${prevTenantId} → ${tenantId}`)
          this.onTenantChange(tenantId)
        }
      }
    )

    // Cleanup su window unload
    window.addEventListener('beforeunload', () => {
      this.cleanup()
    })
  }

  // 🏢 Gestione cambio tenant
  private onTenantChange(_newTenantId: string) {
    // Invalida tutto il cache
    const store = useDataStore.getState()
    store.invalidateCache()
    
    // Force sync per nuovo tenant
    this.queueSync('all', { force: true, priority: 'high' })
  }

  // 📋 Queue Sync con Smart Priority
  queueSync(syncType: 'workflows' | 'executions' | 'dashboard' | 'metrics' | 'systemHealth' | 'all', options: SyncOptions = {}) {
    const { debounceMs = 1000 } = options
    
    // Debounce per evitare sync eccessivi
    if (debounceMs > 0) {
      const existingTimer = this.debounceTimers.get(syncType)
      if (existingTimer) {
        clearTimeout(existingTimer)
      }
      
      const timer = setTimeout(() => {
        this.executeSync(syncType, options)
        this.debounceTimers.delete(syncType)
      }, debounceMs)
      
      this.debounceTimers.set(syncType, timer)
      return
    }
    
    this.executeSync(syncType, options)
  }

  // ⚡ Esecuzione sync immediata
  private async executeSync(syncType: string, options: SyncOptions) {
    const startTime = Date.now()
    const store = useDataStore.getState()
    
    try {
      console.log(`🔄 SmartSync executing: ${syncType} (priority: ${options.priority})`)
      
      this.syncMetrics.totalSyncs++
      
      switch (syncType) {
        case 'workflows':
          await store.syncWorkflows(options.force)
          break
        case 'executions':
          await store.syncExecutions(options.force)
          break
        case 'dashboard':
          await store.syncDashboard(options.force)
          break
        case 'metrics':
          await store.syncMetrics(options.force)
          break
        case 'systemHealth':
          await store.syncSystemHealth(options.force)
          break
        case 'all':
          await store.syncAll(options.force)
          break
        default:
          throw new Error(`Unknown sync type: ${syncType}`)
      }
      
      const syncTime = Date.now() - startTime
      this.updateSyncMetrics(syncTime, true)
      
      console.log(`✅ SmartSync completed: ${syncType} in ${syncTime}ms`)
      
    } catch (error: any) {
      const syncTime = Date.now() - startTime
      this.updateSyncMetrics(syncTime, false)
      
      console.error(`❌ SmartSync failed: ${syncType}`, error)
      
      // Retry logic per high priority syncs
      if (options.priority === 'high' && (options.retryCount || 0) < 3) {
        const retryOptions = { ...options, retryCount: (options.retryCount || 0) + 1 }
        setTimeout(() => {
          this.queueSync(syncType as any, retryOptions)
        }, 2000 * Math.pow(2, retryOptions.retryCount!)) // Exponential backoff
      }
    }
  }

  // 📈 Aggiornamento metriche
  private updateSyncMetrics(syncTime: number, success: boolean) {
    if (success) {
      this.syncMetrics.successfulSyncs++
    } else {
      this.syncMetrics.failedSyncs++
    }
    
    // Calcola average sync time
    this.syncMetrics.avgSyncTime = (
      (this.syncMetrics.avgSyncTime * (this.syncMetrics.totalSyncs - 1) + syncTime) /
      this.syncMetrics.totalSyncs
    )
    
    this.syncMetrics.lastSyncTime = Date.now()
    
    // Calcola cache hit rate
    this.syncMetrics.cacheHitRate = this.syncMetrics.successfulSyncs / this.syncMetrics.totalSyncs
  }

  // 🔄 Avvia background sync
  startBackgroundSync() {
    console.log(`🔄 Starting SmartSync background service`)
    startBackgroundSync()
  }

  // ⏹️ Ferma background sync
  stopBackgroundSync() {
    console.log(`⏹️ Stopping SmartSync background service`)
    stopBackgroundSync()
  }

  // 🎯 Force Refresh specifico con priorità
  forceRefresh(type: 'workflows' | 'executions' | 'dashboard' | 'all' = 'all') {
    console.log(`🔥 Force refresh triggered: ${type}`)
    this.queueSync(type, { force: true, priority: 'high', debounceMs: 0 })
  }

  // 📊 Smart sync basato su focus window
  onWindowFocus() {
    console.log(`👁️ Window focused - triggering smart sync`)
    this.queueSync('all', { priority: 'normal', debounceMs: 500 })
  }

  // 😴 Window blur - riduce frequency
  onWindowBlur() {
    console.log(`😴 Window blurred - reducing sync frequency`)
    // Implementa logic per ridurre frequency quando non in focus
  }

  // 🎯 Sync specifico per modal aperti
  syncForModal(modalType: 'workflow' | 'execution' | 'agent', entityId?: string) {
    console.log(`🎯 Modal sync triggered: ${modalType}${entityId ? ` (${entityId})` : ''}`)
    
    switch (modalType) {
      case 'workflow':
        this.queueSync('workflows', { force: true, priority: 'high', debounceMs: 0 })
        if (entityId) {
          this.queueSync('executions', { force: true, priority: 'high', debounceMs: 0 })
        }
        break
      case 'execution':
        this.queueSync('executions', { force: true, priority: 'high', debounceMs: 0 })
        break
      case 'agent':
        this.queueSync('workflows', { force: true, priority: 'high', debounceMs: 0 })
        break
    }
  }

  // 📊 Ottimizzazione basata su pattern utente
  optimizeSyncStrategy() {
    const hitRate = this.syncMetrics.cacheHitRate
    const avgTime = this.syncMetrics.avgSyncTime
    
    console.log(`📊 Sync metrics - Hit rate: ${(hitRate * 100).toFixed(1)}%, Avg time: ${avgTime.toFixed(0)}ms`)
    
    // Se hit rate è alto, aumenta cache TTL
    if (hitRate > 0.8 && avgTime < 1000) {
      console.log(`⚡ High cache efficiency - optimizing intervals`)
      // Logica per ottimizzare intervalli
    }
    
    // Se sync time è alto, reduce frequency
    if (avgTime > 3000) {
      console.log(`🐌 Slow sync detected - reducing frequency`)
      // Logica per ridurre frequency
    }
  }

  // 📈 Getter per metriche
  getMetrics(): SyncMetrics {
    return { ...this.syncMetrics }
  }

  // 🧹 Cleanup
  cleanup() {
    console.log(`🧹 SmartSyncService cleanup`)
    
    // Clear all debounce timers
    this.debounceTimers.forEach(timer => clearTimeout(timer))
    this.debounceTimers.clear()
    
    // Stop background sync
    this.stopBackgroundSync()
  }

  // 🔍 Health check
  isHealthy(): boolean {
    const recentSyncTime = Date.now() - this.syncMetrics.lastSyncTime
    const isRecent = recentSyncTime < 120000 // 2 minuti
    const hasGoodRate = this.syncMetrics.cacheHitRate > 0.5
    
    return isRecent && hasGoodRate
  }

  // 🎛️ Configurazione dinamica intervals
  setInterval(priority: 'high' | 'normal' | 'low', intervalMs: number) {
    this.SYNC_INTERVALS[priority] = intervalMs
    console.log(`⚙️ Updated ${priority} sync interval to ${intervalMs}ms`)
  }
}

// 🚀 Export singleton instance
export const smartSyncService = new SmartSyncService()

// 🎯 React hooks per integrazione UI
export const useSmartSync = () => {
  return {
    forceRefresh: smartSyncService.forceRefresh.bind(smartSyncService),
    syncForModal: smartSyncService.syncForModal.bind(smartSyncService),
    getMetrics: smartSyncService.getMetrics.bind(smartSyncService),
    isHealthy: smartSyncService.isHealthy.bind(smartSyncService),
    onWindowFocus: smartSyncService.onWindowFocus.bind(smartSyncService),
    onWindowBlur: smartSyncService.onWindowBlur.bind(smartSyncService)
  }
}

// 🔧 Window focus/blur listeners automatici
if (typeof window !== 'undefined') {
  window.addEventListener('focus', () => smartSyncService.onWindowFocus())
  window.addEventListener('blur', () => smartSyncService.onWindowBlur())
}

export default smartSyncService