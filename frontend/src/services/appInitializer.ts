// 🚀 App Initializer - Enterprise Frontend Architecture Bootstrap
// Inizializza il sistema di data management e smart sync

import { useDataStore } from '../store/dataStore'
import { smartSyncService } from './smartSyncService'
import { useAuthStore } from '../store/authStore'

export class AppInitializer {
  private static initialized = false

  static async initialize() {
    if (this.initialized) {
      console.log('🔄 App already initialized, skipping...')
      return
    }

    console.log('🚀 Initializing Enterprise Frontend Architecture...')

    try {
      // 1. Inizializza autenticazione se presente
      await this.initializeAuth()

      // 2. Configura data store con tenant corrente
      this.initializeDataStore()

      // 3. Avvia smart sync service
      this.initializeSmartSync()

      // 4. Setup error handlers globali
      this.setupGlobalErrorHandlers()

      // 5. Setup performance monitoring
      this.setupPerformanceMonitoring()

      this.initialized = true
      console.log('✅ Enterprise Frontend Architecture initialized successfully')
      
    } catch (error) {
      console.error('❌ App initialization failed:', error)
      throw error
    }
  }

  private static async initializeAuth() {
    console.log('🔐 Initializing authentication...')
    
    const authStore = useAuthStore.getState()
    
    // Check auth se token presente
    if (authStore.token) {
      try {
        await authStore.checkAuth()
        console.log('✅ Authentication verified')
      } catch (error) {
        console.warn('⚠️ Auth verification failed, user needs to login')
      }
    }
  }

  private static initializeDataStore() {
    console.log('📊 Initializing data store...')
    
    const dataStore = useDataStore.getState()
    const authStore = useAuthStore.getState()
    
    // Set tenant da user autenticato se disponibile
    if (authStore.user?.tenantId) {
      dataStore.setCurrentTenant(authStore.user.tenantId)
      console.log(`🏢 Tenant set to: ${authStore.user.tenantId}`)
    }
    
    // Subscribe a cambiamenti di user per aggiornare tenant
    useAuthStore.subscribe(
      (state) => {
        const user = state.user
        if (user?.tenantId) {
          dataStore.setCurrentTenant(user.tenantId)
          console.log(`🏢 Tenant updated to: ${user.tenantId}`)
        }
      }
    )
  }

  private static initializeSmartSync() {
    console.log('🔄 Initializing smart sync service...')
    
    // SmartSyncService si auto-inizializza nel constructor
    // Qui possiamo configurare parametri specifici
    
    const authStore = useAuthStore.getState()
    if (authStore.isAuthenticated) {
      // Avvia sync solo se autenticato
      smartSyncService.startBackgroundSync()
      console.log('✅ Smart sync service started')
    } else {
      console.log('⏸️ Smart sync paused - user not authenticated')
    }
    
    // Listen per auth changes
    useAuthStore.subscribe(
      (state) => {
        if (state.isAuthenticated) {
          smartSyncService.startBackgroundSync()
          console.log('🔄 Smart sync started - user authenticated')
        } else {
          smartSyncService.stopBackgroundSync()
          console.log('⏸️ Smart sync stopped - user logged out')
        }
      }
    )
  }

  private static setupGlobalErrorHandlers() {
    console.log('🛡️ Setting up global error handlers...')
    
    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      console.error('🚨 Unhandled promise rejection:', event.reason)
      
      // Log to dataStore errors se è un errore di sync
      if (event.reason?.message?.includes('sync')) {
        const dataStore = useDataStore.getState()
        dataStore.errors.global = event.reason.message
      }
      
      // Prevent browser default behavior
      event.preventDefault()
    })

    // Global JavaScript errors
    window.addEventListener('error', (event) => {
      console.error('🚨 Global JavaScript error:', event.error)
    })

    console.log('✅ Global error handlers configured')
  }

  private static setupPerformanceMonitoring() {
    console.log('📈 Setting up performance monitoring...')
    
    // Performance observer per monitorare loading times
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        entries.forEach((entry) => {
          if (entry.entryType === 'navigation') {
            console.log(`📊 Page load time: ${entry.duration.toFixed(2)}ms`)
          }
          
          if (entry.entryType === 'measure') {
            console.log(`📊 Custom measure '${entry.name}': ${entry.duration.toFixed(2)}ms`)
          }
        })
      })
      
      try {
        observer.observe({ type: 'navigation', buffered: true })
        observer.observe({ type: 'measure', buffered: true })
      } catch (error) {
        console.warn('Performance observer setup failed:', error)
      }
    }

    // Memory usage monitoring (in development)
    if (import.meta.env.DEV) {
      setInterval(() => {
        if ('memory' in performance) {
          const memory = (performance as any).memory
          const used = (memory.usedJSHeapSize / 1024 / 1024).toFixed(2)
          const total = (memory.totalJSHeapSize / 1024 / 1024).toFixed(2)
          console.log(`🧠 Memory usage: ${used}MB / ${total}MB`)
        }
      }, 60000) // Log ogni minuto
    }

    console.log('✅ Performance monitoring configured')
  }

  // 🧹 Cleanup per app unmount
  static cleanup() {
    console.log('🧹 Cleaning up app initializer...')
    
    smartSyncService.cleanup()
    this.initialized = false
    
    console.log('✅ App cleanup completed')
  }

  // 🔍 Health check
  static healthCheck() {
    const authStore = useAuthStore.getState()
    const dataStore = useDataStore.getState()
    
    return {
      initialized: this.initialized,
      authenticated: authStore.isAuthenticated,
      tenant: dataStore.currentTenantId,
      smartSyncHealthy: smartSyncService.isHealthy(),
      errors: Object.keys(dataStore.errors).length,
      lastSync: dataStore.lastSync,
      timestamp: new Date().toISOString()
    }
  }
}

// 🎯 React hook per inizializzazione
export const useAppInitializer = () => {
  const [initialized, setInitialized] = React.useState(false)
  const [error, setError] = React.useState<Error | null>(null)

  React.useEffect(() => {
    let mounted = true

    AppInitializer.initialize()
      .then(() => {
        if (mounted) {
          setInitialized(true)
        }
      })
      .catch((error) => {
        if (mounted) {
          setError(error)
        }
      })

    return () => {
      mounted = false
    }
  }, [])

  return { initialized, error, healthCheck: AppInitializer.healthCheck }
}

// React import
import React from 'react'

export default AppInitializer