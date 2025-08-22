<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gradient">
            Alerts & Monitoring
          </h1>
          <p class="text-gray-400 mt-1">
            Monitoraggio real-time e gestione alert del sistema
          </p>
        </div>
        
        <div class="flex items-center gap-3">
          <button
            @click="toggleMonitoring"
            class="btn-control"
            :class="{ 'bg-green-500/20 border-green-500/30 text-green-400': isMonitoringEnabled }"
          >
            <Bell v-if="isMonitoringEnabled" class="h-4 w-4" />
            <BellOff v-else class="h-4 w-4" />
            {{ isMonitoringEnabled ? 'Monitoring ON' : 'Monitoring OFF' }}
          </button>
          
          <button 
            @click="refreshAlerts"
            :disabled="isLoading"
            class="btn-control"
          >
            <RefreshCw :class="{ 'animate-spin': isLoading }" class="h-4 w-4" />
            Aggiorna
          </button>
          
          <button class="btn-control">
            <Download class="h-4 w-4" />
            Esporta Log
          </button>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div class="control-card p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-400">Alert Totali</p>
              <p class="text-2xl font-bold text-white">{{ alertStats.total }}</p>
            </div>
            <Bell class="h-8 w-8 text-gray-600" />
          </div>
        </div>

        <div class="control-card p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-400">Non Letti</p>
              <p class="text-2xl font-bold text-blue-400">{{ alertStats.unread }}</p>
            </div>
            <Eye class="h-8 w-8 text-gray-600" />
          </div>
        </div>

        <div class="control-card p-6 border-red-500/30">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-400">Critical</p>
              <p class="text-2xl font-bold text-red-400">{{ alertStats.critical }}</p>
            </div>
            <AlertTriangle class="h-8 w-8 text-red-500" />
          </div>
        </div>

        <div class="control-card p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-400">Attivi</p>
              <p class="text-2xl font-bold text-green-400">{{ alertStats.active }}</p>
            </div>
            <Activity class="h-8 w-8 text-gray-600" />
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="control-card p-4">
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div class="relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              v-model="searchTerm"
              type="text"
              placeholder="Cerca alerts..."
              class="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
            />
          </div>

          <select
            v-model="severityFilter"
            class="px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
          >
            <option value="all">Tutte le severity</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            v-model="categoryFilter"
            class="px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
          >
            <option value="all">Tutte le categorie</option>
            <option value="system">System</option>
            <option value="workflow">Workflow</option>
            <option value="database">Database</option>
            <option value="security">Security</option>
            <option value="performance">Performance</option>
          </select>

          <div class="flex items-center gap-3">
            <input
              v-model="showOnlyUnread"
              type="checkbox"
              id="unread-only"
              class="w-4 h-4 text-green-500 bg-gray-800 border-gray-600 rounded focus:ring-green-500"
            />
            <label for="unread-only" class="text-sm text-white">
              Solo non letti
            </label>
          </div>
        </div>
      </div>

      <!-- Alerts List -->
      <div class="control-card p-6">
        <div class="space-y-4">
          <div v-if="isLoading" class="text-center py-8 text-gray-500">
            <Bell class="h-12 w-12 mx-auto mb-4 text-gray-600 animate-pulse" />
            <p>Caricamento alerts...</p>
          </div>
          
          <div v-else-if="filteredAlerts.length === 0" class="text-center py-8 text-gray-500">
            <Bell class="h-12 w-12 mx-auto mb-4 text-gray-600" />
            <p>Nessun alert trovato con i filtri selezionati</p>
          </div>
          
          <div
            v-for="alert in filteredAlerts"
            :key="alert.id"
            class="p-4 rounded-lg border transition-all cursor-pointer hover:shadow-md"
            :class="getAlertClass(alert)"
            @click="markAsRead(alert)"
          >
            <div class="flex items-start gap-4">
              <div class="flex-shrink-0 mt-1">
                <component :is="getAlertIcon(alert.type)" class="h-5 w-5" :class="getAlertIconColor(alert.type)" />
              </div>
              
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-3">
                    <h3 class="text-white font-medium">{{ alert.title }}</h3>
                    <span 
                      class="px-2 py-1 rounded text-xs font-medium border"
                      :class="getSeverityColor(alert.severity)"
                    >
                      {{ alert.severity.toUpperCase() }}
                    </span>
                    <span v-if="alert.count && alert.count > 1" class="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">
                      x{{ alert.count }}
                    </span>
                  </div>
                  <span class="text-xs text-gray-500">
                    {{ formatTimeAgo(alert.timestamp) }}
                  </span>
                </div>
                
                <p class="text-gray-300 text-sm mb-2">
                  {{ alert.message }}
                </p>
                
                <div class="flex items-center justify-between text-xs">
                  <div class="flex items-center gap-3">
                    <span class="text-gray-500">Sorgente: {{ alert.source }}</span>
                    <span class="text-blue-400 capitalize">{{ alert.category }}</span>
                  </div>
                  
                  <div v-if="!alert.isRead" class="flex items-center gap-2">
                    <button class="text-blue-400 hover:text-blue-300">
                      Segna come letto
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  RefreshCw, Download, Bell, BellOff, Eye, AlertTriangle, Activity,
  Search, CheckCircle, XCircle, Info
} from 'lucide-vue-next'
import MainLayout from '../components/layout/MainLayout.vue'
import { useAuthStore } from '../stores/auth'
import { useUIStore } from '../stores/ui'
import type { Alert } from '../types'

// Stores
const authStore = useAuthStore()
const uiStore = useUIStore()

// Local state
const isLoading = ref(false)
const isMonitoringEnabled = ref(true)
const searchTerm = ref('')
const severityFilter = ref<'all' | 'critical' | 'high' | 'medium' | 'low'>('all')
const categoryFilter = ref<'all' | 'system' | 'workflow' | 'database' | 'security' | 'performance'>('all')
const showOnlyUnread = ref(false)

const alertStats = ref({
  total: 15,
  unread: 3,
  critical: 1,
  active: 8
})

const alerts = ref<Alert[]>([
  {
    id: '1',
    type: 'warning',
    severity: 'high',
    title: 'High Memory Usage Detected',
    message: 'System memory usage has exceeded 80% for the past 15 minutes',
    source: 'monitoring.memory',
    timestamp: new Date().toISOString(),
    isRead: false,
    isActive: true,
    category: 'system'
  },
  {
    id: '2',
    type: 'success',
    severity: 'low',
    title: 'Backup Completed Successfully',
    message: 'Daily automated backup completed without errors',
    source: 'backup.scheduler',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    isRead: false,
    isActive: false,
    category: 'system'
  },
  {
    id: '3',
    type: 'error',
    severity: 'critical',
    title: 'Database Connection Lost',
    message: 'Temporary connection loss to PostgreSQL database, auto-reconnect successful',
    source: 'database.connection',
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    isRead: true,
    isActive: false,
    category: 'database'
  }
])

// Computed
const filteredAlerts = computed(() => {
  return alerts.value.filter(alert => {
    const matchesSeverity = severityFilter.value === 'all' || alert.severity === severityFilter.value
    const matchesCategory = categoryFilter.value === 'all' || alert.category === categoryFilter.value
    const matchesSearch = alert.title.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
                         alert.message.toLowerCase().includes(searchTerm.value.toLowerCase())
    const matchesReadStatus = !showOnlyUnread.value || !alert.isRead
    
    return matchesSeverity && matchesCategory && matchesSearch && matchesReadStatus
  })
})

// Methods
const refreshAlerts = async () => {
  isLoading.value = true
  
  try {
    // Simulate alert refresh
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Add a new system check alert
    alerts.value.unshift({
      id: `alert-${Date.now()}`,
      type: 'info',
      severity: 'low',
      title: 'System Health Check',
      message: 'Routine system health check completed successfully',
      source: 'monitoring.health',
      timestamp: new Date().toISOString(),
      isRead: false,
      isActive: false,
      category: 'system'
    })
    
    alertStats.value.total = alerts.value.length
    alertStats.value.unread = alerts.value.filter(a => !a.isRead).length
    
    uiStore.showToast('Aggiornamento', 'Alerts aggiornati', 'success')
  } catch (error: any) {
    uiStore.showToast('Errore', 'Impossibile caricare alerts', 'error')
  } finally {
    isLoading.value = false
  }
}

const toggleMonitoring = () => {
  isMonitoringEnabled.value = !isMonitoringEnabled.value
  uiStore.showToast(
    'Monitoring', 
    isMonitoringEnabled.value ? 'Monitoring attivato' : 'Monitoring disattivato', 
    'success'
  )
}

const markAsRead = (alert: Alert) => {
  if (!alert.isRead) {
    alert.isRead = true
    alertStats.value.unread = Math.max(0, alertStats.value.unread - 1)
  }
}

const getAlertClass = (alert: Alert) => {
  const base = !alert.isRead ? 'bg-gray-800/50 border-gray-700' : 'bg-gray-900/30 border-gray-800'
  
  switch (alert.severity) {
    case 'critical': return `${base} border-red-500/30`
    case 'high': return `${base} border-orange-500/30`
    case 'medium': return `${base} border-yellow-500/30`
    case 'low': return `${base} border-green-500/30`
    default: return base
  }
}

const getAlertIcon = (type: string) => {
  switch (type) {
    case 'error': return XCircle
    case 'warning': return AlertTriangle
    case 'info': return Info
    case 'success': return CheckCircle
    default: return Info
  }
}

const getAlertIconColor = (type: string) => {
  switch (type) {
    case 'error': return 'text-red-400'
    case 'warning': return 'text-yellow-400'
    case 'info': return 'text-blue-400'
    case 'success': return 'text-green-400'
    default: return 'text-gray-400'
  }
}

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical': return 'text-red-400 bg-red-500/10 border-red-500/30'
    case 'high': return 'text-orange-400 bg-orange-500/10 border-orange-500/30'
    case 'medium': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30'
    case 'low': return 'text-green-400 bg-green-500/10 border-green-500/30'
    default: return 'text-gray-400 bg-gray-500/10 border-gray-500/30'
  }
}

const formatTimeAgo = (timestamp: string) => {
  const now = new Date()
  const time = new Date(timestamp)
  const diffMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60))
  
  if (diffMinutes < 1) return 'Ora'
  if (diffMinutes < 60) return `${diffMinutes}m fa`
  if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h fa`
  return `${Math.floor(diffMinutes / 1440)}g fa`
}

// Lifecycle
onMounted(() => {
  refreshAlerts()
})
</script>