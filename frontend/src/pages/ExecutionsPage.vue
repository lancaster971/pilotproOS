<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gradient">
            ⚡ CODICE AGGIORNATO ADESSO! - {{ authStore.tenantId }}
          </h1>
          <p class="text-gray-400 mt-1">
            Monitora le esecuzioni dei tuoi workflow
          </p>
        </div>
        
        <div class="flex items-center gap-3">
          <!-- Auto Refresh Toggle -->
          <div class="flex items-center gap-2">
            <input
              v-model="autoRefresh"
              type="checkbox"
              id="auto-refresh"
              class="w-4 h-4 text-green-500 bg-gray-900 border-gray-600 rounded focus:ring-green-500"
            />
            <label for="auto-refresh" class="text-sm text-white">
              Auto refresh
            </label>
          </div>
          
          <button 
            @click="refreshExecutions"
            :disabled="isLoading"
            class="btn-control"
          >
            <RefreshCw :class="{ 'animate-spin': isLoading }" class="h-4 w-4" />
            Refresh
          </button>
          
          <button class="btn-control">
            <Download class="h-4 w-4" />
            Esporta
          </button>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div class="control-card p-4">
          <div class="text-center">
            <p class="text-2xl font-bold text-white">{{ executionStats.total }}</p>
            <p class="text-xs text-gray-400">Totali</p>
          </div>
        </div>
        
        <div class="control-card p-4">
          <div class="text-center">
            <p class="text-2xl font-bold text-green-400">{{ executionStats.success }}</p>
            <p class="text-xs text-gray-400">Success</p>
          </div>
        </div>
        
        <div class="control-card p-4">
          <div class="text-center">
            <p class="text-2xl font-bold text-red-400">{{ executionStats.error }}</p>
            <p class="text-xs text-gray-400">Error</p>
          </div>
        </div>
        
        <div class="control-card p-4">
          <div class="text-center">
            <p class="text-2xl font-bold text-blue-400">{{ executionStats.running }}</p>
            <p class="text-xs text-gray-400">Running</p>
          </div>
        </div>
        
        <div class="control-card p-4">
          <div class="text-center">
            <p class="text-2xl font-bold text-yellow-400">{{ executionStats.waiting }}</p>
            <p class="text-xs text-gray-400">Waiting</p>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="control-card p-4">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div class="relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              v-model="searchTerm"
              type="text"
              placeholder="Cerca executions..."
              class="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
            />
          </div>

          <select
            v-model="statusFilter"
            class="px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
          >
            <option value="all">Any Status ({{ executionStats.total }})</option>
            <option value="success">Success ({{ executionStats.success }})</option>
            <option value="error">Error ({{ executionStats.error }})</option>
            <option value="running">Running ({{ executionStats.running }})</option>
            <option value="waiting">Waiting ({{ executionStats.waiting }})</option>
          </select>

          <select
            v-model="workflowFilter"
            class="px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
          >
            <option value="all">All Workflows</option>
            <option
              v-for="workflow in workflowsStore.workflows"
              :key="workflow.id"
              :value="workflow.id"
            >
              {{ workflow.name }}
            </option>
          </select>
        </div>
      </div>

      <!-- Executions Table -->
      <div class="control-card overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-800">
                <th class="text-left p-4 text-sm font-medium text-gray-400">
                  <input type="checkbox" class="w-4 h-4 bg-gray-900 border-gray-600 rounded" />
                </th>
                <th class="text-left p-4 text-sm font-medium text-gray-400">Workflow</th>
                <th class="text-left p-4 text-sm font-medium text-gray-400">Status</th>
                <th class="text-left p-4 text-sm font-medium text-gray-400">Started</th>
                <th class="text-left p-4 text-sm font-medium text-gray-400">Run Time</th>
                <th class="text-left p-4 text-sm font-medium text-gray-400">Exec. ID</th>
                <th class="text-left p-4 text-sm font-medium text-gray-400"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredExecutions.length === 0">
                <td colspan="7" class="p-8 text-center text-gray-500">
                  <Play class="h-8 w-8 mx-auto mb-2 text-gray-600" />
                  Nessuna execution trovata
                </td>
              </tr>
              
              <tr
                v-for="execution in filteredExecutions"
                :key="execution.id"
                class="border-b border-gray-800/50 hover:bg-gray-900/30 transition-colors"
              >
                <td class="p-4">
                  <input type="checkbox" class="w-4 h-4 bg-gray-900 border-gray-600 rounded" />
                </td>
                
                <td class="p-4">
                  <div class="font-medium text-white max-w-xs">
                    <span 
                      @click="openExecutionDetails(execution)"
                      class="truncate block cursor-pointer hover:text-green-400 transition-colors" 
                      :title="execution.workflow_name"
                    >
                      {{ execution.workflow_name }}
                    </span>
                  </div>
                </td>
                
                <td class="p-4">
                  <span 
                    class="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium border"
                    :class="getStatusClass(execution.status)"
                  >
                    <div class="w-1.5 h-1.5 rounded-full" :class="getStatusDot(execution.status)" />
                    {{ getStatusLabel(execution.status) }}
                  </span>
                </td>
                
                <td class="p-4 text-sm text-gray-300">
                  {{ formatTime(execution.started_at) }}
                </td>
                
                <td class="p-4 text-sm text-gray-300 font-mono">
                  {{ formatDuration(execution.duration_ms) }}
                </td>
                
                <td class="p-4 text-sm text-gray-300 font-mono">
                  {{ execution.id }}
                </td>
                
                <td class="p-4">
                  <button class="p-1 text-gray-400 hover:text-white transition-colors">
                    <MoreHorizontal class="h-4 w-4" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="filteredExecutions.length > 0" class="flex items-center justify-between">
        <p class="text-sm text-gray-400">
          Visualizzando {{ filteredExecutions.length }} di {{ executions.length }} executions
        </p>
        <div class="flex items-center gap-2">
          <button class="btn-control text-xs px-3 py-1" disabled>
            Precedente
          </button>
          <button class="btn-control text-xs px-3 py-1" disabled>
            Successiva
          </button>
        </div>
      </div>
    </div>

    <!-- Timeline Modal for Execution Details -->
    <TimelineModal
      :show="showTimelineModal"
      :workflow-id="selectedExecutionWorkflowId"
      :tenant-id="authStore.tenantId"
      @close="closeTimelineModal"
    />
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  RefreshCw, Download, Search, Play, CheckCircle, XCircle,
  Clock, Pause, MoreHorizontal
} from 'lucide-vue-next'
import MainLayout from '../components/layout/MainLayout.vue'
import TimelineModal from '../components/common/TimelineModal.vue'
import { useAuthStore } from '../stores/auth'
import { useWorkflowsStore } from '../stores/workflows'
import { useUIStore } from '../stores/ui'
import { businessAPI } from '../services/api-client'
import webSocketService from '../services/websocket'
import type { Execution } from '../types'

// Stores
const authStore = useAuthStore()
const workflowsStore = useWorkflowsStore()
const uiStore = useUIStore()

// Local state
const isLoading = ref(false)
const autoRefresh = ref(true)
const searchTerm = ref('')
const statusFilter = ref<'all' | 'success' | 'error' | 'running' | 'waiting'>('all')
const workflowFilter = ref('all')
const executions = ref<Execution[]>([])

// Modal state
const showTimelineModal = ref(false)
const selectedExecutionWorkflowId = ref<string>('')

// Auto-refresh interval
let refreshInterval: NodeJS.Timeout

// Computed
const executionStats = computed(() => ({
  total: executions.value.length,
  success: executions.value.filter(e => e.status === 'success').length,
  error: executions.value.filter(e => e.status === 'error').length,
  running: executions.value.filter(e => e.status === 'running').length,
  waiting: executions.value.filter(e => e.status === 'waiting').length,
}))

const filteredExecutions = computed(() => {
  console.log('🔍 Filtering executions. Total:', executions.value.length)
  const filtered = executions.value.filter((execution) => {
    // Search filter (fix: id is a number, not string)
    const matchesSearch = execution.workflow_name?.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
                         String(execution.id).includes(searchTerm.value)
    
    // Status filter
    const matchesStatus = statusFilter.value === 'all' || execution.status === statusFilter.value
    
    // Workflow filter
    const matchesWorkflow = workflowFilter.value === 'all' || execution.workflow_id === workflowFilter.value
    
    return matchesSearch && matchesStatus && matchesWorkflow
  })
  console.log('✅ Filtered executions:', filtered.length)
  return filtered
})

// Methods
const refreshExecutions = async () => {
  alert('🚀 REFRESH EXECUTIONS CALLED!')
  console.log('🚀 STARTING refreshExecutions...')
  isLoading.value = true
  
  try {
    console.log('🌐 Making API call to /process-runs...')
    
    // Use OFETCH API client instead of direct fetch
    const testData = await businessAPI.getProcessRuns()
    console.log('✅ OFETCH data loaded, length:', testData.data?.length)
    
    // Now try with businessAPI
    const response = await businessAPI.get('/process-runs')
    console.log('📡 BusinessAPI response status:', response.status)
    const data = response.data
    console.log('📊 BusinessAPI data:', data)
    
    if (!data.data || !Array.isArray(data.data)) {
      throw new Error('Invalid API response format')
    }
    
    // Create a simple test execution first
    executions.value = [{
      id: 999,
      workflow_id: 'test-id',
      workflow_name: 'TEST EXECUTION - Click me!',
      status: 'success',
      mode: 'webhook',
      started_at: new Date().toISOString(),
      stopped_at: new Date().toISOString(),
      duration_ms: 1000,
      business_status: 'Completed Successfully',
      issue_description: null
    }]
    
    console.log('✅ SET TEST EXECUTION:', executions.value)
    
    if (executions.value.length > 0) {
      uiStore.showToast('SUCCESS', `${executions.value.length} test executions loaded`, 'success')
    }
    
  } catch (error: any) {
    console.error('❌ ERROR in refreshExecutions:', error)
    uiStore.showToast('Errore', error.message || 'Impossibile caricare le executions', 'error')
    
    // Fallback to empty array on error
    executions.value = []
  } finally {
    console.log('🏁 FINISHED refreshExecutions. Executions count:', executions.value.length)
    isLoading.value = false
  }
}

// Helper to map backend status to frontend status
const mapBackendStatus = (businessStatus: string): string => {
  switch (businessStatus) {
    case 'Completed Successfully':
      return 'success'
    case 'Requires Attention':
      return 'error'
    case 'In Progress':
      return 'running'
    default:
      return 'waiting'
  }
}

// Status helpers - same pattern as n8n
const getStatusClass = (status: string | null) => {
  switch (status) {
    case 'success':
      return 'text-green-400 bg-green-500/10 border-green-500/30'
    case 'error':
      return 'text-red-400 bg-red-500/10 border-red-500/30'
    case 'running':
      return 'text-blue-400 bg-blue-500/10 border-blue-500/30'
    case 'waiting':
      return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30'
    default:
      return 'text-gray-400 bg-gray-500/10 border-gray-500/30'
  }
}

const getStatusDot = (status: string | null) => {
  switch (status) {
    case 'success': return 'bg-green-500'
    case 'error': return 'bg-red-500'
    case 'running': return 'bg-blue-500'
    case 'waiting': return 'bg-yellow-500'
    default: return 'bg-gray-500'
  }
}

const getStatusLabel = (status: string | null) => {
  switch (status) {
    case 'success': return 'Success'
    case 'error': return 'Error'
    case 'running': return 'Running'
    case 'waiting': return 'Waiting'
    default: return 'Unknown'
  }
}

const formatTime = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const executionDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  
  const timeStr = date.toLocaleTimeString('it-IT', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  })
  
  if (executionDate.getTime() === today.getTime()) {
    return timeStr
  }
  
  return `${date.toLocaleDateString('it-IT', { 
    month: 'short', 
    day: '2-digit' 
  })}, ${timeStr}`
}

const formatDuration = (ms?: number) => {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${Math.round(ms / 1000 * 10) / 10}s`
  return `${Math.round(ms / 60000 * 10) / 10}min`
}

// Auto-refresh setup
watch(autoRefresh, (enabled) => {
  if (enabled) {
    webSocketService.startAutoRefresh('executions', refreshExecutions, 5000)
  } else {
    webSocketService.stopAutoRefresh('executions')
  }
})

// Modal functions
const openExecutionDetails = (execution: any) => {
  console.log('🔥 CLICK DETECTED! Execution:', execution)
  console.log('🎯 Opening execution details for:', execution.workflow_name, 'ID:', execution.workflow_id)
  selectedExecutionWorkflowId.value = execution.workflow_id
  showTimelineModal.value = true
}

const closeTimelineModal = () => {
  showTimelineModal.value = false
  selectedExecutionWorkflowId.value = ''
}

// Lifecycle
onMounted(() => {
  refreshExecutions()
  workflowsStore.fetchWorkflows() // For workflow filter
  
  if (autoRefresh.value) {
    webSocketService.startAutoRefresh('executions', refreshExecutions, 5000)
  }
  
  // Listen for real-time execution events
  window.addEventListener('execution:started', refreshExecutions)
  window.addEventListener('execution:completed', refreshExecutions)
})

onUnmounted(() => {
  // Stop auto-refresh
  webSocketService.stopAutoRefresh('executions')
  
  // Clean up event listeners
  window.removeEventListener('execution:started', refreshExecutions)
  window.removeEventListener('execution:completed', refreshExecutions)
})
</script>