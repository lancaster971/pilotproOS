<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Stats Cards -->
      <div class="grid grid-cols-2 md:grid-cols-6 gap-4">
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
            <p class="text-2xl font-bold text-white">{{ executionStats.canceled }}</p>
            <p class="text-xs text-gray-400">Canceled</p>
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
            <option value="canceled">Canceled ({{ executionStats.canceled }})</option>
            <option value="running">Running ({{ executionStats.running }})</option>
            <option value="waiting">Waiting ({{ executionStats.waiting }})</option>
          </select>

          <select
            v-model="workflowFilter"
            class="px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
          >
            <option value="all">All Workflows</option>
            <option
              v-for="workflow in uniqueWorkflows"
              :key="workflow.id"
              :value="workflow.id"
            >
              {{ workflow.name }}
            </option>
          </select>
        </div>
      </div>

      <!-- Executions Table - Excel Dark Style -->
      <div class="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full border-collapse">
            <thead>
              <tr class="bg-gray-800 border-b-2 border-gray-600">
                <th class="border-r border-gray-700 px-2 py-1 text-xs font-bold text-gray-300 text-left">Workflow</th>
                <th class="border-r border-gray-700 px-2 py-1 text-xs font-bold text-gray-300 text-left">Status</th>
                <th class="border-r border-gray-700 px-2 py-1 text-xs font-bold text-gray-300 text-left">Started</th>
                <th class="border-r border-gray-700 px-2 py-1 text-xs font-bold text-gray-300 text-left">Run Time</th>
                <th class="border-r border-gray-700 px-2 py-1 text-xs font-bold text-gray-300 text-left">Exec. ID</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredExecutions.length === 0">
                <td colspan="5" class="px-2 py-8 text-center text-gray-500 bg-gray-900">
                  <Play class="h-8 w-8 mx-auto mb-2 text-gray-600" />
                  Nessuna execution trovata
                </td>
              </tr>

              <tr
                v-for="(execution, index) in filteredExecutions"
                :key="execution.id"
                class="border-b border-gray-700 hover:bg-gray-800"
                :class="{ 'bg-gray-900': index % 2 === 0, 'bg-gray-850': index % 2 === 1 }"
              >
                <td class="border-r border-gray-700 px-2 py-1">
                  <div class="text-xs text-gray-100 max-w-xs">
                    <span class="truncate block" :title="execution.process_name">
                      {{ execution.processName }}
                    </span>
                  </div>
                </td>
                
                <td class="border-r border-gray-700 px-2 py-1">
                  <!-- Success Status -->
                  <span
                    v-if="execution.originalStatus === 'success'"
                    class="text-xs text-green-300 font-bold"
                  >
                    SUCCESS
                  </span>
                  <!-- Error Status -->
                  <span
                    v-else-if="execution.originalStatus === 'error'"
                    class="text-xs text-red-300 font-bold"
                  >
                    ERROR
                  </span>
                  <!-- Canceled Status -->
                  <span
                    v-else-if="execution.originalStatus === 'canceled'"
                    class="text-xs text-yellow-300 font-bold"
                  >
                    CANCELED
                  </span>
                  <!-- Unknown Status (fallback) -->
                  <span
                    v-else
                    class="text-xs text-white font-bold"
                  >
                    {{ (execution.originalStatus || 'UNKNOWN').toUpperCase() }}
                  </span>
                </td>
                
                <td class="border-r border-gray-700 px-2 py-1 text-xs text-gray-300">
                  {{ formatTime(execution.processRunStarted) }}
                </td>
                
                <td class="border-r border-gray-700 px-2 py-1 text-xs text-gray-300">
                  {{ formatDuration(execution.processRunDuration * 1000) }}
                </td>
                
                <td class="border-gray-700 px-2 py-1 text-xs text-gray-400">
                  #{{ execution.processRunId }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="executions.length > 0" class="flex items-center justify-between">
        <p class="text-sm text-gray-400">
          Pagina {{ currentPage }} di {{ totalPages }} -
          Visualizzando {{ filteredExecutions.length }} di {{ allFilteredExecutions.length }} risultati
        </p>
        <div class="flex items-center gap-2">
          <button
            @click="currentPage = Math.max(1, currentPage - 1)"
            :disabled="currentPage === 1"
            class="btn-control text-xs px-3 py-1"
            :class="currentPage === 1 ? 'opacity-50 cursor-not-allowed' : ''"
          >
            ← Precedente
          </button>
          <span class="text-white text-sm px-2">
            {{ currentPage }} / {{ totalPages }}
          </span>
          <button
            @click="currentPage = Math.min(totalPages, currentPage + 1)"
            :disabled="currentPage === totalPages"
            class="btn-control text-xs px-3 py-1"
            :class="currentPage === totalPages ? 'opacity-50 cursor-not-allowed' : ''"
          >
            Successiva →
          </button>
        </div>
      </div>
    </div>

  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { RefreshCw, Search, Play } from 'lucide-vue-next'
import MainLayout from '../components/layout/MainLayout.vue'
import { businessAPI } from '../services/api-client'

// Local state
const isLoading = ref(false)
const autoRefresh = ref(true)
const searchTerm = ref('')
const statusFilter = ref<'all' | 'success' | 'error' | 'running' | 'waiting'>('all')
const workflowFilter = ref('all')
const executions = ref<any[]>([])

// Pagination state
const currentPage = ref(1)
const itemsPerPage = ref(20)

// Reset to page 1 when filters change
watch([searchTerm, statusFilter, workflowFilter], () => {
  currentPage.value = 1
})

// Computed
const uniqueWorkflows = computed(() => {
  const workflows = new Map()
  executions.value.forEach(exec => {
    if (exec.processId && exec.processName) {
      workflows.set(exec.processId, exec.processName)
    }
  })
  return Array.from(workflows.entries()).map(([id, name]) => ({
    id,
    name
  })).sort((a, b) => a.name.localeCompare(b.name))
})

const executionStats = computed(() => {
  const stats = {
    total: executions.value.length,
    success: executions.value.filter(e => e.statusKey === 'success').length,
    error: executions.value.filter(e => e.statusKey === 'error').length,
    canceled: executions.value.filter(e => e.statusKey === 'canceled').length,
    running: executions.value.filter(e => e.statusKey === 'running').length,
    waiting: executions.value.filter(e => e.statusKey === 'waiting').length,
  }
  console.log('📈 Execution Stats:', stats)
  console.log('📈 All statusKeys:', executions.value.map(e => e.statusKey))
  return stats
})

const allFilteredExecutions = computed(() => {
  return executions.value.filter((execution) => {
    // Search filter
    const matchesSearch = execution.processName?.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
                         String(execution.processRunId).includes(searchTerm.value)

    // Status filter
    const matchesStatus = statusFilter.value === 'all' || execution.statusKey === statusFilter.value

    // Workflow filter
    const matchesWorkflow = workflowFilter.value === 'all' || execution.processId === workflowFilter.value

    return matchesSearch && matchesStatus && matchesWorkflow
  })
})

const filteredExecutions = computed(() => {
  // Apply pagination
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return allFilteredExecutions.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(allFilteredExecutions.value.length / itemsPerPage.value)
})

const normalizeStatus = (status?: string | null, label?: string | null) => {
  // Use n8n exact status values
  const raw = (status || '').toLowerCase().trim()

  // Map n8n statuses directly
  switch (raw) {
    case 'success':
      return 'success'
    case 'error':
      return 'error'
    case 'canceled':
      return 'canceled'
    case 'running':
      return 'running'
    case 'waiting':
      return 'waiting'
    default:
      // If empty status, default to success
      if (!raw) {
        console.log('⚠️ Empty status detected, defaulting to success')
        return 'success'
      }
      // Log unexpected status
      console.log('📊 Unexpected status:', status, '→ keeping as is')
      return raw
  }
}

const mapExecution = (execution: any) => {
  const statusKey = normalizeStatus(execution.originalStatus, execution.processRunStatus?.label) || 'success'
  console.log('📋 Mapping execution:', execution.processName)
  console.log('   Original Status:', execution.originalStatus)
  console.log('   Process Run Status:', execution.processRunStatus)
  console.log('   → Mapped to:', statusKey)

  return {
    ...execution,
    originalStatus: execution.originalStatus, // ENSURE originalStatus is preserved!
    statusKey,
    // Ensure we always have a status label
    processRunStatus: {
      ...execution.processRunStatus,
      label: execution.processRunStatus?.label || getStatusLabel(statusKey)
    }
  }
}

// Methods
const refreshExecutions = async () => {
  isLoading.value = true

  try {
    const data = await businessAPI.getProcessExecutions()
    console.log('🔥 RAW API DATA:', data)

    if (data.processRuns && Array.isArray(data.processRuns)) {
      console.log('📦 First execution raw:', data.processRuns[0])
      executions.value = data.processRuns.map(mapExecution)
      console.log('✅ Mapped executions:', executions.value)
    } else {
      console.log('⚠️ No processRuns in data')
      executions.value = []
    }

  } catch (error: any) {
    console.error('❌ ERROR loading executions:', error.message)
    executions.value = []
  } finally {
    isLoading.value = false
  }
}

// Status helpers
const getStatusClass = (status: string) => {
  switch (status) {
    case 'success':
      return 'text-green-400 bg-green-500/10 border-green-500/30'
    case 'error':
      return 'text-red-400 bg-red-500/10 border-red-500/30'
    case 'running':
      return 'text-blue-400 bg-blue-500/10 border-blue-500/30'
    case 'waiting':
      return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30'
    case 'canceled':
    case 'unknown':
      return 'text-gray-400 bg-gray-500/10 border-gray-500/30'
    default:
      return 'text-green-400 bg-green-500/10 border-green-500/30' // Default to success style
  }
}

const getStatusDot = (status: string) => {
  switch (status) {
    case 'success': return 'bg-green-500'
    case 'error': return 'bg-red-500'
    case 'running': return 'bg-blue-500'
    case 'waiting': return 'bg-yellow-500'
    case 'canceled':
    case 'unknown': return 'bg-gray-500'
    default: return 'bg-green-500' // Default to success color
  }
}

const getStatusLabel = (status: string | null | undefined) => {
  if (!status) return 'Success' // Default if no status

  switch (status) {
    case 'success': return 'Success'
    case 'error': return 'Error'
    case 'running': return 'Running'
    case 'waiting': return 'Waiting'
    case 'unknown': return 'Unknown'
    default: return 'Success' // Default to Success
  }
}

const getExecutionStatusLabel = (execution: any) => {
  // Try to get label from processRunStatus object first
  if (execution.processRunStatus && typeof execution.processRunStatus === 'object') {
    if (execution.processRunStatus.label) {
      return execution.processRunStatus.label
    }
  }

  // Fallback to originalStatus
  if (execution.originalStatus === 'canceled') {
    return 'Unknown Status'
  }

  // Default
  return 'Completed Successfully'
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

const formatDuration = (ms?: string | number) => {
  if (!ms) return '-'
  const duration = typeof ms === 'string' ? parseFloat(ms) : ms
  if (duration < 1000) return `${duration}ms`
  if (duration < 60000) return `${Math.round(duration / 1000 * 10) / 10}s`
  return `${Math.round(duration / 60000 * 10) / 10}min`
}


// Lifecycle
onMounted(() => {
  refreshExecutions()
})
</script>
