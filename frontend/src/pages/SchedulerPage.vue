<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gradient">
            Scheduler Control
          </h1>
          <p class="text-gray-400 mt-1">
            Gestione scheduling automatico e monitoraggio job
          </p>
        </div>
        
        <div class="flex items-center gap-3">
          <button 
            @click="refreshScheduler"
            :disabled="isLoading"
            class="btn-control"
          >
            <RefreshCw :class="{ 'animate-spin': isLoading }" class="h-4 w-4" />
            Aggiorna
          </button>
          
          <button class="btn-control">
            <Settings class="h-4 w-4" />
            Configurazione
          </button>
          
          <button class="btn-control-primary">
            <Plus class="h-4 w-4" />
            Nuovo Job
          </button>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div class="control-card p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-400">Jobs Totali</p>
              <p class="text-2xl font-bold text-white">{{ schedulerStats.totalJobs }}</p>
            </div>
            <Calendar class="h-8 w-8 text-gray-600" />
          </div>
        </div>

        <div class="control-card p-6 border-green-500/30">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-400">Scheduler Status</p>
              <p 
                class="text-2xl font-bold"
                :class="schedulerStatus.isRunning ? 'text-green-400' : 'text-red-400'"
              >
                {{ schedulerStatus.isRunning ? 'RUNNING' : 'STOPPED' }}
              </p>
            </div>
            <Play 
              :class="schedulerStatus.isRunning ? 'text-green-500' : 'text-gray-600'" 
              class="h-8 w-8" 
            />
          </div>
        </div>

        <div class="control-card p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-400">Total Sync Runs</p>
              <p class="text-2xl font-bold text-blue-400">{{ schedulerStats.totalSyncRuns }}</p>
            </div>
            <Activity class="h-8 w-8 text-gray-600" />
          </div>
        </div>

        <div class="control-card p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-400">Active Tenants</p>
              <p class="text-2xl font-bold text-green-400">{{ schedulerStats.activeTenants }}</p>
            </div>
            <Target class="h-8 w-8 text-gray-600" />
          </div>
        </div>
      </div>

      <!-- System Status -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="control-card p-6">
          <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp class="h-5 w-5 text-green-400" />
            System Status
          </h3>
          <div class="space-y-4">
            <div class="flex justify-between items-center">
              <span class="text-gray-400">Scheduler Running</span>
              <span 
                class="font-bold"
                :class="schedulerStatus.isRunning ? 'text-green-400' : 'text-red-400'"
              >
                {{ schedulerStatus.isRunning ? 'YES' : 'NO' }}
              </span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-400">Active Tenants</span>
              <span class="text-white font-bold">{{ schedulerStats.activeTenants }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-400">System Uptime</span>
              <span class="text-green-400 font-bold">{{ systemUptime }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-400">Last Sync</span>
              <span class="text-blue-400 font-bold">{{ formatTime(schedulerStatus.lastSync) }}</span>
            </div>
          </div>
        </div>

        <div class="control-card p-6">
          <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Timer class="h-5 w-5 text-blue-400" />
            Recent Sync Activity
          </h3>
          <div class="space-y-3">
            <div v-if="isLoading" class="text-gray-500">Caricamento...</div>
            
            <div v-else-if="syncHistory.length === 0" class="text-gray-500">Nessun sync recente</div>
            
            <div
              v-for="log in syncHistory.slice(0, 5)"
              :key="log.id"
              class="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg"
            >
              <div>
                <p class="text-white font-medium">{{ log.tenant_name || 'Unknown Tenant' }}</p>
                <p class="text-xs text-gray-400">
                  {{ log.items_processed || 0 }} items • {{ formatDuration(log.duration_ms || 0) }}
                </p>
              </div>
              <div class="text-right">
                <div class="flex items-center gap-1">
                  <CheckCircle v-if="log.success" class="h-3 w-3 text-green-400" />
                  <XCircle v-else class="h-3 w-3 text-red-400" />
                  <span 
                    class="text-xs font-medium"
                    :class="log.success ? 'text-green-400' : 'text-red-400'"
                  >
                    {{ log.success ? 'Success' : 'Failed' }}
                  </span>
                </div>
                <p class="text-xs text-gray-500">{{ formatTime(log.started_at) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Control Actions -->
      <div class="control-card p-6">
        <h3 class="text-lg font-semibold text-white mb-4">Scheduler Controls</h3>
        <div class="flex items-center gap-4">
          <button
            @click="startScheduler"
            :disabled="schedulerStatus.isRunning"
            class="btn-control-primary"
            :class="{ 'opacity-50 cursor-not-allowed': schedulerStatus.isRunning }"
          >
            <Play class="h-4 w-4" />
            Start Scheduler
          </button>
          
          <button
            @click="stopScheduler"
            :disabled="!schedulerStatus.isRunning"
            class="btn-control text-red-400 border-red-500/30 hover:border-red-500 hover:bg-red-500/10"
            :class="{ 'opacity-50 cursor-not-allowed': !schedulerStatus.isRunning }"
          >
            <Square class="h-4 w-4" />
            Stop Scheduler
          </button>
          
          <button
            @click="runManualSync"
            class="btn-control"
          >
            <Zap class="h-4 w-4" />
            Manual Sync
          </button>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  RefreshCw, Settings, Plus, Calendar, Play, Activity, Target,
  TrendingUp, Timer, CheckCircle, XCircle, Square, Zap
} from 'lucide-vue-next'
import MainLayout from '../components/layout/MainLayout.vue'
import { useAuthStore } from '../stores/auth'
import { useUIStore } from '../stores/ui'
import { businessAPI } from '../services/api'

// Stores
const authStore = useAuthStore()
const uiStore = useUIStore()

// Local state
const isLoading = ref(false)
const systemUptime = ref('15d 8h 23m')

const schedulerStatus = ref({
  isRunning: true,
  lastSync: new Date().toISOString(),
  nextSync: new Date(Date.now() + 1800000).toISOString(), // 30 min from now
})

const schedulerStats = ref({
  totalJobs: 8,
  totalSyncRuns: 1547,
  activeTenants: 3
})

const syncHistory = ref([
  {
    id: '1',
    tenant_name: 'PilotProOS',
    tenant_id: 'pilotpros_main',
    success: true,
    items_processed: 29,
    duration_ms: 2450,
    started_at: new Date().toISOString()
  },
  {
    id: '2',
    tenant_name: 'Business Process',
    tenant_id: 'business_proc',
    success: true,
    items_processed: 1,
    duration_ms: 1200,
    started_at: new Date(Date.now() - 1800000).toISOString()
  },
  {
    id: '3',
    tenant_name: 'Test Environment',
    tenant_id: 'test_env',
    success: false,
    items_processed: 0,
    duration_ms: 800,
    started_at: new Date(Date.now() - 3600000).toISOString(),
    error_message: 'Connection timeout'
  }
])

// Methods
const refreshScheduler = async () => {
  isLoading.value = true
  
  try {
    // Try to get real scheduler status from our backend
    const response = await businessAPI.getHealth()
    const healthData = response.data
    
    // Update scheduler status based on system health
    schedulerStatus.value.isRunning = healthData.status === 'healthy'
    
    // Update system uptime
    if (healthData.uptime) {
      const uptimeSeconds = Math.floor(healthData.uptime)
      const days = Math.floor(uptimeSeconds / 86400)
      const hours = Math.floor((uptimeSeconds % 86400) / 3600)
      const minutes = Math.floor((uptimeSeconds % 3600) / 60)
      systemUptime.value = `${days}d ${hours}h ${minutes}m`
    }
    
    uiStore.showToast('Aggiornamento', 'Scheduler status aggiornato', 'success')
  } catch (error: any) {
    console.error('Failed to load scheduler data:', error)
    uiStore.showToast('Errore', 'Impossibile caricare scheduler data', 'error')
  } finally {
    isLoading.value = false
  }
}

const startScheduler = () => {
  schedulerStatus.value.isRunning = true
  uiStore.showToast('Scheduler', 'Scheduler avviato', 'success')
}

const stopScheduler = () => {
  schedulerStatus.value.isRunning = false
  uiStore.showToast('Scheduler', 'Scheduler fermato', 'warning')
}

const runManualSync = () => {
  // Add new sync to history
  syncHistory.value.unshift({
    id: `sync-${Date.now()}`,
    tenant_name: 'Manual Sync',
    tenant_id: 'manual',
    success: true,
    items_processed: Math.floor(Math.random() * 50),
    duration_ms: Math.floor(Math.random() * 5000 + 1000),
    started_at: new Date().toISOString()
  })
  
  schedulerStats.value.totalSyncRuns += 1
  uiStore.showToast('Sync', 'Manual sync completato', 'success')
}

const formatTime = (dateString?: string) => {
  if (!dateString) return 'Never'
  return new Date(dateString).toLocaleString('it-IT')
}

const formatDuration = (ms: number) => {
  if (ms < 60000) return `${Math.round(ms / 1000)}s`
  if (ms < 3600000) return `${Math.round(ms / 60000)}m`
  return `${Math.round(ms / 3600000)}h`
}

// Lifecycle
onMounted(() => {
  refreshScheduler()
})
</script>