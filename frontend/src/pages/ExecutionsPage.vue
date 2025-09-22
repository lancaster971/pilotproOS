<template>
  <MainLayout>
    <div class="executions-container">
      <!-- Professional Header Bar -->
      <div class="header-bar">
        <div>
          <h1 class="page-title">Process Runs</h1>
          <p class="page-subtitle">Monitor and analyze your business process executions</p>
        </div>
        
        <div class="header-actions">
          <!-- Auto Refresh Toggle -->
          <div class="auto-refresh-toggle">
            <input
              v-model="autoRefresh"
              type="checkbox"
              id="auto-refresh"
              class="checkbox-input"
            />
            <label for="auto-refresh" class="checkbox-label">
              <Icon icon="mdi:refresh-auto" class="inline-icon" />
              Auto refresh
            </label>
          </div>

          <button
            @click="refreshExecutions"
            :disabled="isLoading"
            class="action-button"
          >
            <Icon icon="mdi:refresh" :class="{ 'animate-spin': isLoading }" class="button-icon" />
            Refresh
          </button>

          <button class="action-button primary">
            <Icon icon="mdi:download" class="button-icon" />
            Export
          </button>
        </div>
      </div>

      <!-- Professional KPI Bar -->
      <div class="professional-kpi-bar">
        <div class="kpi-card">
          <Icon icon="mdi:sigma" class="kpi-card-icon" />
          <div class="kpi-card-content">
            <div class="kpi-card-value">{{ executionStats.total }}</div>
            <div class="kpi-card-label">TOTAL RUNS</div>
          </div>
        </div>

        <div class="kpi-card highlight-success">
          <Icon icon="mdi:check-circle" class="kpi-card-icon" />
          <div class="kpi-card-content">
            <div class="kpi-card-value">{{ executionStats.success }}</div>
            <div class="kpi-card-label">SUCCESS</div>
          </div>
        </div>

        <div class="kpi-card highlight-error">
          <Icon icon="mdi:alert-circle" class="kpi-card-icon" />
          <div class="kpi-card-content">
            <div class="kpi-card-value">{{ executionStats.error }}</div>
            <div class="kpi-card-label">ERRORS</div>
          </div>
        </div>

        <div class="kpi-card">
          <Icon icon="mdi:cancel" class="kpi-card-icon" />
          <div class="kpi-card-content">
            <div class="kpi-card-value">{{ executionStats.canceled }}</div>
            <div class="kpi-card-label">CANCELED</div>
          </div>
        </div>

        <div class="kpi-card">
          <Icon icon="mdi:play-circle" class="kpi-card-icon" />
          <div class="kpi-card-content">
            <div class="kpi-card-value">{{ executionStats.running }}</div>
            <div class="kpi-card-label">RUNNING</div>
          </div>
        </div>

        <div class="kpi-card">
          <Icon icon="mdi:clock-outline" class="kpi-card-icon" />
          <div class="kpi-card-content">
            <div class="kpi-card-value">{{ executionStats.waiting }}</div>
            <div class="kpi-card-label">WAITING</div>
          </div>
        </div>
      </div>

      <!-- Filters - Excel Style -->
      <div class="control-card p-4">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <!-- Search Input -->
          <div class="relative">
            <Icon icon="mdi:magnify" class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              v-model="searchTerm"
              type="text"
              placeholder="Cerca executions..."
              class="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-white text-sm focus:border-green-500 focus:outline-none"
            />
          </div>

          <!-- Status Filter -->
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

          <!-- Workflow Filter -->
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
                <th class="border-r border-gray-700 px-2 py-1 text-xs font-bold text-gray-300 text-left">
                  <input type="checkbox" class="w-3 h-3 bg-gray-700 border-gray-600 rounded" />
                </th>
                <th class="border-r border-gray-700 px-2 py-1 text-xs font-bold text-gray-300 text-left">PROCESS NAME</th>
                <th class="border-r border-gray-700 px-2 py-1 text-xs font-bold text-gray-300 text-left">STATUS</th>
                <th class="border-r border-gray-700 px-2 py-1 text-xs font-bold text-gray-300 text-left">STARTED</th>
                <th class="border-r border-gray-700 px-2 py-1 text-xs font-bold text-gray-300 text-left">RUN TIME</th>
                <th class="border-r border-gray-700 px-2 py-1 text-xs font-bold text-gray-300 text-left">EXEC. ID</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredExecutions.length === 0">
                <td colspan="6" class="px-2 py-8 text-center text-gray-500 bg-gray-900">
                  <Icon icon="mdi:play-circle-outline" class="h-8 w-8 mx-auto mb-2 text-gray-600" />
                  No process runs found
                </td>
              </tr>

              <tr
                v-for="(execution, index) in filteredExecutions"
                :key="execution.id"
                class="border-b border-gray-700 hover:bg-gray-800"
                :class="{ 'bg-gray-900': index % 2 === 0, 'bg-gray-850': index % 2 === 1 }"
              >
                <td class="border-r border-gray-700 px-2 py-1">
                  <input type="checkbox" class="w-3 h-3 bg-gray-700 border-gray-600 rounded" />
                </td>

                <td class="border-r border-gray-700 px-2 py-1">
                  <div class="text-xs text-gray-100 max-w-xs">
                    <span
                      @click="openExecutionDetails(execution)"
                      class="truncate block cursor-pointer hover:text-green-400 transition-colors"
                      :title="execution.workflow_name || execution.processName"
                    >
                      {{ execution.workflow_name || execution.processName }}
                    </span>
                  </div>
                </td>

                <td class="border-r border-gray-700 px-2 py-1">
                  <!-- Success Status -->
                  <span
                    v-if="execution.status === 'success'"
                    class="text-xs text-green-300 font-bold"
                  >
                    SUCCESS
                  </span>
                  <!-- Error Status -->
                  <span
                    v-else-if="execution.status === 'error'"
                    class="text-xs text-red-300 font-bold"
                  >
                    ERROR
                  </span>
                  <!-- Canceled Status -->
                  <span
                    v-else-if="execution.status === 'canceled'"
                    class="text-xs text-yellow-300 font-bold"
                  >
                    CANCELED
                  </span>
                  <!-- Running Status -->
                  <span
                    v-else-if="execution.status === 'running'"
                    class="text-xs text-blue-300 font-bold"
                  >
                    RUNNING
                  </span>
                  <!-- Waiting Status -->
                  <span
                    v-else-if="execution.status === 'waiting'"
                    class="text-xs text-orange-300 font-bold"
                  >
                    WAITING
                  </span>
                  <!-- Unknown Status (fallback) -->
                  <span
                    v-else
                    class="text-xs text-white font-bold"
                  >
                    {{ (execution.status || 'UNKNOWN').toUpperCase() }}
                  </span>
                </td>

                <td class="border-r border-gray-700 px-2 py-1 text-xs text-gray-300">
                  {{ formatTime(execution.started_at) }}
                </td>

                <td class="border-r border-gray-700 px-2 py-1 text-xs text-gray-300">
                  {{ formatDuration(execution.duration_ms) }}
                </td>

                <td class="border-gray-700 px-2 py-1 text-xs text-gray-400">
                  #{{ execution.id || execution.processRunId }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="filteredExecutions.length > 0" class="pagination">
        <p class="text-sm text-gray-400">
          Showing {{ filteredExecutions.length }} of {{ executions.length }} process runs
        </p>
        <div class="flex items-center gap-2">
          <button class="action-button" disabled>
            <Icon icon="mdi:chevron-left" class="button-icon" />
            Previous
          </button>
          <button class="action-button" disabled>
            Next
            <Icon icon="mdi:chevron-right" class="button-icon" />
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
import { Icon } from '@iconify/vue'
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
const statusFilter = ref<'all' | 'success' | 'error' | 'canceled' | 'running' | 'waiting'>('all')
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
    canceled: executions.value.filter(e => e.status === 'canceled').length,
    running: executions.value.filter(e => e.status === 'running').length,
    waiting: executions.value.filter(e => e.status === 'waiting').length,
  }
  console.log('📈 Execution Stats:', stats)
  return stats
})

const uniqueWorkflows = computed(() => {
  const workflows = new Map()
  executions.value.forEach(exec => {
    const id = exec.workflow_id || exec.processId
    const name = exec.workflow_name || exec.processName
    if (id && name) {
      workflows.set(id, name)
    }
  })
  return Array.from(workflows.entries()).map(([id, name]) => ({
    id,
    name
  }))
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

// Helper to normalize status
const normalizeStatus = (originalStatus: string | null, label?: string): string => {
  if (!originalStatus) return 'success'

  const status = originalStatus.toLowerCase()
  if (status.includes('success')) return 'success'
  if (status.includes('error') || status.includes('fail')) return 'error'
  if (status.includes('cancel')) return 'canceled'
  if (status.includes('running') || status.includes('progress')) return 'running'
  if (status.includes('waiting') || status.includes('pending')) return 'waiting'

  // Check business label as fallback
  if (label) {
    const businessLabel = label.toLowerCase()
    if (businessLabel.includes('completed')) return 'success'
    if (businessLabel.includes('attention')) return 'error'
    if (businessLabel.includes('progress')) return 'running'
  }

  return 'success' // Default to success
}

// Helper to map execution data
const mapExecution = (execution: any) => {
  const statusKey = normalizeStatus(execution.originalStatus, execution.processRunStatus?.label) || 'success'
  return {
    ...execution,
    id: execution.processRunId || execution.id,
    workflow_id: execution.processId || execution.workflow_id,
    workflow_name: execution.processName || execution.workflow_name,
    status: statusKey,
    started_at: execution.processRunStartTime || execution.started_at,
    stopped_at: execution.processRunEndTime || execution.stopped_at,
    duration_ms: execution.processDuration || execution.duration_ms || 0,
    originalStatus: execution.originalStatus,
    processRunStatus: execution.processRunStatus
  }
}

// Methods
const refreshExecutions = async () => {
  console.log('🚀 Starting refresh executions...')
  isLoading.value = true

  try {
    // Use the correct API method that ExecutionsPagePrime uses
    const data = await businessAPI.getProcessExecutions()
    console.log('🔥 RAW API DATA:', data)

    if (data.processRuns && Array.isArray(data.processRuns)) {
      console.log('📦 First execution raw:', data.processRuns[0])
      executions.value = data.processRuns.map(mapExecution)
      console.log('✅ Mapped executions:', executions.value)

      if (executions.value.length > 0) {
        uiStore.showToast('Process Runs', `${executions.value.length} process runs loaded`, 'success')
      }
    } else {
      console.log('⚠️ No processRuns in data')
      executions.value = []
    }
  } catch (error: any) {
    console.error('❌ ERROR loading executions:', error.message)
    uiStore.showToast('Error', error.message || 'Unable to load process runs', 'error')
    executions.value = []
  } finally {
    isLoading.value = false
  }
}


// Status helpers - same pattern as n8n
const getStatusClass = (status: string | null) => {
  switch (status) {
    case 'success':
      return 'text-green-400 bg-green-500/10 border-green-500/30'
    case 'error':
      return 'text-red-400 bg-red-500/10 border-red-500/30'
    case 'canceled':
      return 'text-gray-400 bg-gray-500/10 border-gray-500/30'
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
    case 'canceled': return 'bg-gray-500'
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
    case 'canceled': return 'Canceled'
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

<style scoped>
/* Professional Design matching InsightsPage */
.executions-container {
  width: 100%;
  padding: 20px;
  background: #0a0a0a;
  min-height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  max-height: calc(100vh - 40px);
}

/* Header Styling */
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(31, 41, 55, 0.5);
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #e5e7eb;
  margin: 0;
}

.page-subtitle {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.auto-refresh-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
}

.checkbox-input {
  width: 16px;
  height: 16px;
  background: rgba(31, 41, 55, 0.5);
  border: 1px solid rgba(107, 114, 128, 0.3);
  border-radius: 4px;
  cursor: pointer;
}

.checkbox-label {
  font-size: 12px;
  color: #9ca3af;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.inline-icon {
  font-size: 14px;
  color: #6b7280;
}

/* Action Buttons */
.action-button {
  padding: 8px 16px;
  background: rgba(31, 41, 55, 0.5);
  border: 1px solid rgba(107, 114, 128, 0.3);
  border-radius: 6px;
  color: #e5e7eb;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.action-button:hover:not(:disabled) {
  background: rgba(31, 41, 55, 0.8);
  border-color: rgba(16, 185, 129, 0.3);
  transform: translateY(-1px);
}

.action-button.primary {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
  color: #93bbfc;
}

.action-button.primary:hover {
  background: rgba(59, 130, 246, 0.2);
}

.action-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.button-icon {
  font-size: 16px;
}

/* Professional KPI Bar */
.professional-kpi-bar {
  display: flex;
  gap: 0;
  background: rgba(10, 10, 15, 0.8);
  border: 1px solid rgba(31, 41, 55, 0.4);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
}

.kpi-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: rgba(15, 15, 20, 0.6);
  border: 1px solid rgba(31, 41, 55, 0.3);
  border-radius: 8px;
  margin-right: 16px;
  position: relative;
}

.kpi-card:last-child {
  margin-right: 0;
}

.kpi-card.highlight-success {
  background: rgba(16, 185, 129, 0.05);
  border-color: rgba(16, 185, 129, 0.2);
}

.kpi-card.highlight-success .kpi-card-value {
  color: #10b981;
}

.kpi-card.highlight-success .kpi-card-icon {
  color: #10b981;
}

.kpi-card.highlight-error {
  background: rgba(239, 68, 68, 0.05);
  border-color: rgba(239, 68, 68, 0.2);
}

.kpi-card.highlight-error .kpi-card-value {
  color: #ef4444;
}

.kpi-card.highlight-error .kpi-card-icon {
  color: #ef4444;
}

.kpi-card-icon {
  font-size: 24px;
  color: #64748b;
  opacity: 0.8;
}

.kpi-card-content {
  flex: 1;
}

.kpi-card-value {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  line-height: 1;
  margin-bottom: 4px;
  letter-spacing: -0.5px;
}

.kpi-card-label {
  font-size: 10px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 500;
}

/* Section Containers */
.section-container {
  background: rgba(10, 10, 15, 0.9);
  border: 1px solid rgba(31, 41, 55, 0.5);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.6);
}

/* Filter Inputs */
.search-input {
  width: 100%;
  padding: 10px 40px 10px 16px;
  background: rgba(31, 41, 55, 0.3);
  border: 1px solid rgba(107, 114, 128, 0.3);
  border-radius: 6px;
  color: #e5e7eb;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: rgba(16, 185, 129, 0.5);
  background: rgba(31, 41, 55, 0.5);
}

/* Table Styling */
table {
  width: 100%;
  border-collapse: collapse;
}

th {
  text-align: left;
  padding: 12px;
  font-size: 12px;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(31, 41, 55, 0.3);
}

td {
  padding: 12px;
  font-size: 13px;
  color: #e5e7eb;
  border-bottom: 1px solid rgba(31, 41, 55, 0.2);
}

tr:hover {
  background: rgba(31, 41, 55, 0.1);
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #9ca3af;
}

.empty-icon {
  font-size: 48px;
  color: #6b7280;
  margin-bottom: 16px;
}

.empty-state p {
  font-size: 14px;
  margin-bottom: 0;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
}

/* Responsive */
@media (max-width: 1400px) {
  .professional-kpi-bar {
    padding: 20px 16px;
  }

  .kpi-card {
    padding: 12px 14px;
    margin-right: 12px;
  }

  .kpi-card-value {
    font-size: 24px;
  }
}

@media (max-width: 1200px) {
  .professional-kpi-bar {
    flex-wrap: wrap;
    gap: 12px;
  }

  .kpi-card {
    min-width: calc(50% - 6px);
    margin-right: 0;
  }
}

@media (max-width: 768px) {
  .professional-kpi-bar {
    padding: 16px;
  }

  .kpi-card {
    width: 100%;
    min-width: 100%;
  }

  .kpi-card-value {
    font-size: 22px;
  }
}

/* Excel Table Zebra Stripes */
.bg-gray-850 {
  background-color: #111317;
}

/* Animations */
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>