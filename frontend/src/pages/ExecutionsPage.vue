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
            <p class="text-2xl font-bold text-white">{{ executionStats.success }}</p>
            <p class="text-xs text-gray-400">Success</p>
          </div>
        </div>
        
        <div class="control-card p-4">
          <div class="text-center">
            <p class="text-2xl font-bold text-white">{{ executionStats.error }}</p>
            <p class="text-xs text-gray-400">Error</p>
          </div>
        </div>
        
        <div class="control-card p-4">
          <div class="text-center">
            <p class="text-2xl font-bold text-white">{{ executionStats.running }}</p>
            <p class="text-xs text-gray-400">Running</p>
          </div>
        </div>
        
        <div class="control-card p-4">
          <div class="text-center">
            <p class="text-2xl font-bold text-white">{{ executionStats.waiting }}</p>
            <p class="text-xs text-gray-400">Waiting</p>
          </div>
        </div>
      </div>

      <!-- Modern Filters with Premium Design -->
      <div class="control-card p-4">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <!-- Search Input -->
          <div class="relative group">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted transition-colors group-focus-within:text-primary" />
            <input
              v-model="searchTerm"
              type="text"
              placeholder="Cerca executions..."
              class="w-full pl-10 pr-4 py-2.5 bg-surface border border-border rounded-lg text-text text-sm 
                     focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20
                     transition-all duration-200 placeholder:text-text-muted"
            />
          </div>

          <!-- Status Filter Dropdown -->
          <div class="relative">
            <button
              @click="showStatusDropdown = !showStatusDropdown"
              class="w-full px-4 py-2.5 bg-surface border border-border rounded-lg text-text text-sm 
                     hover:border-primary/50 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20
                     transition-all duration-200 flex items-center justify-between group"
            >
              <span class="flex items-center gap-2">
                <div v-if="statusFilter !== 'all'" 
                     class="w-2 h-2 rounded-full"
                     :class="statusFilter === 'success' ? 'bg-green-400' : 
                             statusFilter === 'error' ? 'bg-red-400' :
                             statusFilter === 'running' ? 'bg-blue-400' : 'bg-yellow-400'"
                />
                {{ statusFilter === 'all' ? `Any Status (${executionStats.total})` :
                    statusFilter === 'success' ? `Success (${executionStats.success})` :
                    statusFilter === 'error' ? `Error (${executionStats.error})` :
                    statusFilter === 'running' ? `Running (${executionStats.running})` :
                    `Waiting (${executionStats.waiting})` }}
              </span>
              <ChevronDown class="h-4 w-4 text-text-muted transition-transform duration-200" 
                          :class="showStatusDropdown ? 'rotate-180' : ''" />
            </button>
            
            <!-- Status Dropdown Menu -->
            <transition
              enter-active-class="transition ease-out duration-200"
              enter-from-class="transform opacity-0 scale-95"
              enter-to-class="transform opacity-100 scale-100"
              leave-active-class="transition ease-in duration-150"
              leave-from-class="transform opacity-100 scale-100"
              leave-to-class="transform opacity-0 scale-95"
            >
              <div v-if="showStatusDropdown" 
                   class="absolute z-10 mt-2 w-full bg-surface border border-border rounded-lg shadow-xl overflow-hidden">
                <button
                  v-for="status in ['all', 'success', 'error', 'running', 'waiting']"
                  :key="status"
                  @click="statusFilter = status; showStatusDropdown = false"
                  class="w-full px-4 py-2.5 text-left text-sm hover:bg-surface-hover transition-colors 
                         flex items-center justify-between group"
                  :class="statusFilter === status ? 'bg-primary/10 text-primary' : 'text-text'"
                >
                  <span class="flex items-center gap-2">
                    <div class="w-2 h-2 rounded-full"
                         :class="status === 'success' ? 'bg-green-400' : 
                                 status === 'error' ? 'bg-red-400' :
                                 status === 'running' ? 'bg-blue-400' : 
                                 status === 'waiting' ? 'bg-yellow-400' : 'bg-transparent'"
                    />
                    {{ status === 'all' ? 'Any Status' :
                        status === 'success' ? 'Success' :
                        status === 'error' ? 'Error' :
                        status === 'running' ? 'Running' : 'Waiting' }}
                  </span>
                  <span class="text-text-muted text-xs">
                    {{ status === 'all' ? executionStats.total :
                        status === 'success' ? executionStats.success :
                        status === 'error' ? executionStats.error :
                        status === 'running' ? executionStats.running : executionStats.waiting }}
                  </span>
                </button>
              </div>
            </transition>
          </div>

          <!-- Workflow Filter Dropdown -->
          <div class="relative">
            <button
              @click="showWorkflowDropdown = !showWorkflowDropdown"
              class="w-full px-4 py-2.5 bg-surface border border-border rounded-lg text-text text-sm 
                     hover:border-primary/50 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20
                     transition-all duration-200 flex items-center justify-between group"
            >
              <span class="truncate">
                {{ workflowFilter === 'all' ? 'All Workflows' : 
                    workflowsStore.workflows.find(w => w.id === workflowFilter)?.name || 'Select Workflow' }}
              </span>
              <ChevronDown class="h-4 w-4 text-text-muted transition-transform duration-200 flex-shrink-0" 
                          :class="showWorkflowDropdown ? 'rotate-180' : ''" />
            </button>
            
            <!-- Workflow Dropdown Menu -->
            <transition
              enter-active-class="transition ease-out duration-200"
              enter-from-class="transform opacity-0 scale-95"
              enter-to-class="transform opacity-100 scale-100"
              leave-active-class="transition ease-in duration-150"
              leave-from-class="transform opacity-100 scale-100"
              leave-to-class="transform opacity-0 scale-95"
            >
              <div v-if="showWorkflowDropdown" 
                   class="absolute z-10 mt-2 w-full bg-surface border border-border rounded-lg shadow-xl overflow-hidden max-h-64 overflow-y-auto">
                <button
                  @click="workflowFilter = 'all'; showWorkflowDropdown = false"
                  class="w-full px-4 py-2.5 text-left text-sm hover:bg-surface-hover transition-colors"
                  :class="workflowFilter === 'all' ? 'bg-primary/10 text-primary' : 'text-text'"
                >
                  All Workflows
                </button>
                <button
                  v-for="workflow in workflowsStore.workflows"
                  :key="workflow.id"
                  @click="workflowFilter = workflow.id; showWorkflowDropdown = false"
                  class="w-full px-4 py-2.5 text-left text-sm hover:bg-surface-hover transition-colors flex items-center gap-2"
                  :class="workflowFilter === workflow.id ? 'bg-primary/10 text-primary' : 'text-text'"
                >
                  <div class="w-2 h-2 rounded-full" 
                       :class="workflow.active ? 'bg-green-400' : 'bg-gray-400'" />
                  <span class="truncate">{{ workflow.name }}</span>
                </button>
              </div>
            </transition>
          </div>
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
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredExecutions.length === 0">
                <td colspan="6" class="p-8 text-center text-gray-500">
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
                    :class="getStatusClass(execution.status || 'unknown')"
                  >
                    <div class="w-1.5 h-1.5 rounded-full" :class="getStatusDot(execution.status || 'unknown')" />
                    {{ getStatusLabel(execution.status || 'unknown') }}
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
  Clock, Pause, MoreHorizontal, ChevronDown
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

// Dropdown state
const showStatusDropdown = ref(false)
const showWorkflowDropdown = ref(false)

// Modal state
const showTimelineModal = ref(false)
const selectedExecutionWorkflowId = ref<string>('')

// Auto-refresh interval
let refreshInterval: NodeJS.Timeout

// Computed
const executionStats = computed(() => {
  const stats = {
    total: executions.value.length,
    success: executions.value.filter(e => e.status === 'success').length,
    error: executions.value.filter(e => e.status === 'error').length,
    running: executions.value.filter(e => e.status === 'running').length,
    waiting: executions.value.filter(e => e.status === 'waiting').length,
  }
  console.log('📈 Execution Stats:', stats)
  console.log('📈 All statuses:', executions.value.map(e => e.status))
  return stats
})

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

    // Map backend data to frontend format with proper status mapping
    executions.value = data.data.map((item: any, index: number) => {
      const businessStatus = item.business_status || ''
      const mappedStatus = mapBackendStatus(businessStatus)
      console.log(`📊 [${index}] Status mapping: "${businessStatus}" → "${mappedStatus}"`)
      console.log(`   Raw item:`, item)
      return {
        id: item.id,
        workflow_id: item.workflow_id,
        workflow_name: item.workflow_name,
        status: mappedStatus,
        mode: item.mode || 'unknown',
        started_at: item.started_at,
        stopped_at: item.stopped_at,
        duration_ms: item.duration_ms || 0,
        business_status: item.business_status,
        issue_description: item.issue_description
      }
    })

    console.log('✅ Executions loaded:', executions.value.length)

    if (executions.value.length > 0) {
      uiStore.showToast('Process Runs', `${executions.value.length} process runs loaded`, 'success')
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
  console.log('🔍 Mapping business status:', businessStatus)

  if (!businessStatus || businessStatus === '') {
    return 'success' // Default to success if no status
  }

  switch (businessStatus) {
    case 'Completed Successfully':
      return 'success'
    case 'Requires Attention':
      return 'error'
    case 'In Progress':
      return 'running'
    case 'Unknown':
      return 'unknown'
    default:
      return 'success' // Default to success instead of waiting
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
    case 'unknown':
      return 'text-gray-400 bg-gray-500/10 border-gray-500/30'
    default:
      return 'text-green-400 bg-green-500/10 border-green-500/30' // Default to success color
  }
}

const getStatusDot = (status: string | null) => {
  switch (status) {
    case 'success': return 'bg-green-500'
    case 'error': return 'bg-red-500'
    case 'running': return 'bg-blue-500'
    case 'waiting': return 'bg-yellow-500'
    case 'unknown': return 'bg-gray-500'
    default: return 'bg-green-500' // Default to success color
  }
}

const getStatusLabel = (status: string | null) => {
  switch (status) {
    case 'success': return 'Success'
    case 'error': return 'Error'
    case 'running': return 'Running'
    case 'waiting': return 'Waiting'
    case 'unknown': return 'Unknown'
    default: return 'Success' // Default to Success
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