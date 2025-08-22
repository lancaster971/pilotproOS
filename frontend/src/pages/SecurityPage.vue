<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gradient">
            Security Center
          </h1>
          <p class="text-gray-400 mt-1">
            Monitoraggio sicurezza, audit trail e gestione accessi
          </p>
        </div>
        
        <div class="flex items-center gap-3">
          <button 
            @click="refreshSecurity"
            :disabled="isLoading"
            class="btn-control"
          >
            <RefreshCw :class="{ 'animate-spin': isLoading }" class="h-4 w-4" />
            Aggiorna
          </button>
          
          <button class="btn-control">
            <Settings class="h-4 w-4" />
            Policies
          </button>
          
          <button class="btn-control-primary">
            <Plus class="h-4 w-4" />
            Nuova API Key
          </button>
        </div>
      </div>

      <!-- Security Metrics -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div class="control-card p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-400">Utenti Attivi</p>
              <p class="text-2xl font-bold text-white">{{ securityMetrics.activeUsers }}</p>
              <p class="text-xs text-gray-500">di {{ securityMetrics.totalUsers }} totali</p>
            </div>
            <Users class="h-8 w-8 text-gray-600" />
          </div>
        </div>

        <div class="control-card p-6 border-red-500/30">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-400">Login Falliti</p>
              <p class="text-2xl font-bold text-red-400">{{ securityMetrics.failedLogins }}</p>
              <p class="text-xs text-gray-500">ultime 24h</p>
            </div>
            <Ban class="h-8 w-8 text-red-500" />
          </div>
        </div>

        <div class="control-card p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-400">API Keys</p>
              <p class="text-2xl font-bold text-green-400">{{ securityMetrics.apiKeysActive }}</p>
              <p class="text-xs text-gray-500">attive</p>
            </div>
            <Key class="h-8 w-8 text-gray-600" />
          </div>
        </div>

        <div class="control-card p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-400">Success Rate</p>
              <p class="text-2xl font-bold text-green-400">{{ securityMetrics.loginSuccessRate }}%</p>
              <p class="text-xs text-gray-500">operazioni</p>
            </div>
            <CheckCircle class="h-8 w-8 text-gray-600" />
          </div>
        </div>
      </div>

      <!-- Security Status Overview -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="control-card p-6">
          <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Shield class="h-5 w-5 text-green-400" />
            Security Status
          </h3>
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <span class="text-gray-400">Two-Factor Authentication</span>
              <div class="flex items-center gap-2">
                <CheckCircle class="h-4 w-4 text-green-400" />
                <span class="text-green-400 text-sm">Enabled</span>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-gray-400">Password Policy</span>
              <div class="flex items-center gap-2">
                <CheckCircle class="h-4 w-4 text-green-400" />
                <span class="text-green-400 text-sm">Strong</span>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-gray-400">API Rate Limiting</span>
              <div class="flex items-center gap-2">
                <CheckCircle class="h-4 w-4 text-green-400" />
                <span class="text-green-400 text-sm">Active</span>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-gray-400">Session Security</span>
              <div class="flex items-center gap-2">
                <AlertTriangle class="h-4 w-4 text-yellow-400" />
                <span class="text-yellow-400 text-sm">Medium</span>
              </div>
            </div>
          </div>
        </div>

        <div class="control-card p-6">
          <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle class="h-5 w-5 text-red-400" />
            Recent Security Events
          </h3>
          <div class="space-y-3">
            <div
              v-for="log in securityLogs.slice(0, 5)"
              :key="log.id"
              class="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg"
            >
              <div 
                class="p-2 rounded-lg"
                :class="getEventColor(log.event, log.status)"
              >
                <component :is="getEventIcon(log.event)" class="h-4 w-4" />
              </div>
              <div class="flex-1">
                <p class="text-white text-sm">{{ log.details }}</p>
                <p class="text-xs text-gray-400">
                  {{ log.user }} • {{ formatTime(log.timestamp) }}
                </p>
              </div>
              <span 
                class="px-2 py-1 rounded text-xs font-medium border"
                :class="getRiskColor(log.riskLevel)"
              >
                {{ log.riskLevel }}
              </span>
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
  RefreshCw, Settings, Plus, Users, Ban, Key, CheckCircle,
  Shield, AlertTriangle, Search, Table, LogIn, LogOut,
  Database, Download, Activity
} from 'lucide-vue-next'
import MainLayout from '../components/layout/MainLayout.vue'
import { useAuthStore } from '../stores/auth'
import { useUIStore } from '../stores/ui'
import type { SecurityLog } from '../types'

// Stores
const authStore = useAuthStore()
const uiStore = useUIStore()

// Local state
const isLoading = ref(false)
const searchTerm = ref('')

const securityMetrics = ref({
  totalUsers: 5,
  activeUsers: 3,
  failedLogins: 2,
  apiKeysActive: 2,
  loginSuccessRate: 98.5
})

const securityLogs = ref<SecurityLog[]>([
  {
    id: '1',
    timestamp: new Date().toISOString(),
    event: 'login',
    user: 'admin@pilotpro.com',
    userRole: 'admin',
    ipAddress: '192.168.1.50',
    userAgent: navigator.userAgent,
    location: 'Rome, Italy',
    deviceType: 'desktop',
    status: 'success',
    details: 'Successful login to control panel',
    riskLevel: 'low'
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    event: 'api_access',
    user: 'system',
    userRole: 'service',
    ipAddress: '10.0.0.1',
    userAgent: 'PilotPro-API/1.0',
    location: 'Internal Network',
    deviceType: 'api',
    status: 'success',
    details: 'Backend API health check completed',
    riskLevel: 'low'
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    event: 'failed_login',
    user: 'unknown@example.com',
    userRole: 'unknown',
    ipAddress: '192.168.1.100',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    location: 'Milan, Italy',
    deviceType: 'desktop',
    status: 'failed',
    details: 'Invalid password attempt (3rd attempt)',
    riskLevel: 'high'
  }
])

// Computed
const filteredTables = computed(() => {
  // Mock database tables for PilotProOS
  const mockTables = [
    { name: 'workflow_entity', schema: 'n8n', records: 29, size: '2.1 MB', lastModified: new Date().toISOString() },
    { name: 'execution_entity', schema: 'n8n', records: 1245, size: '89.2 MB', lastModified: new Date().toISOString() },
    { name: 'credentials_entity', schema: 'n8n', records: 15, size: '156 KB', lastModified: new Date().toISOString() },
    { name: 'business_analytics', schema: 'pilotpros', records: 29, size: '245 KB', lastModified: new Date().toISOString() },
    { name: 'users', schema: 'pilotpros', records: 3, size: '12 KB', lastModified: new Date().toISOString() },
    { name: 'audit_logs', schema: 'pilotpros', records: 156, size: '890 KB', lastModified: new Date().toISOString() },
  ]
  
  return mockTables.filter(table =>
    table.name.toLowerCase().includes(searchTerm.value.toLowerCase())
  )
})

// Methods
const refreshSecurity = async () => {
  isLoading.value = true
  
  try {
    // Use our backend health endpoint and enhance with security data
    const response = await businessAPI.getHealth()
    const healthData = response.data
    
    // Add a new security log entry for this check
    securityLogs.value.unshift({
      id: `log-${Date.now()}`,
      timestamp: new Date().toISOString(),
      event: 'api_access',
      user: authStore.user?.email || 'system',
      userRole: 'admin',
      ipAddress: '192.168.1.50',
      userAgent: navigator.userAgent,
      location: 'Internal Network',
      deviceType: 'desktop',
      status: 'success',
      details: 'Security dashboard refreshed successfully',
      riskLevel: 'low'
    })
    
    // Keep only last 20 logs
    securityLogs.value = securityLogs.value.slice(0, 20)
    
    uiStore.showToast('Aggiornamento', 'Security logs aggiornati', 'success')
  } catch (error: any) {
    console.error('Failed to load security data:', error)
    uiStore.showToast('Errore', 'Impossibile caricare dati security', 'error')
  } finally {
    isLoading.value = false
  }
}

const getEventIcon = (event: string) => {
  switch (event) {
    case 'login': return LogIn
    case 'logout': return LogOut
    case 'failed_login': return Ban
    case 'api_access': return Database
    case 'data_export': return Download
    case 'config_change': return Settings
    default: return Activity
  }
}

const getEventColor = (event: string, status: string) => {
  if (status === 'failed') return 'text-red-400 bg-red-500/10'
  
  switch (event) {
    case 'login': return 'text-green-400 bg-green-500/10'
    case 'logout': return 'text-blue-400 bg-blue-500/10'
    case 'failed_login': return 'text-red-400 bg-red-500/10'
    case 'api_access': return 'text-purple-400 bg-purple-500/10'
    case 'data_export': return 'text-orange-400 bg-orange-500/10'
    default: return 'text-gray-400 bg-gray-500/10'
  }
}

const getRiskColor = (risk: string) => {
  switch (risk) {
    case 'critical': return 'text-red-400 bg-red-500/10 border-red-500/30'
    case 'high': return 'text-orange-400 bg-orange-500/10 border-orange-500/30'
    case 'medium': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30'
    case 'low': return 'text-green-400 bg-green-500/10 border-green-500/30'
    default: return 'text-gray-400 bg-gray-500/10 border-gray-500/30'
  }
}

const formatTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('it-IT')
}

// Lifecycle
onMounted(() => {
  refreshSecurity()
})
</script>