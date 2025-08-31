<template>
  <DetailModal
    :show="show"
    :title="modalTitle"
    :subtitle="modalSubtitle"
    :header-icon="Bot"
    :tabs="tabs"
    default-tab="timeline"
    :is-loading="isLoading"
    :error="error"
    :data="timelineData"
    :show-refresh="true"
    @close="$emit('close')"
    @refresh="handleForceRefresh"
    @retry="loadTimeline"
  >
    <!-- Header Actions Slot -->
    <template #headerActions="{ isLoading, refresh }">
      <button
        @click="downloadReport"
        class="p-2 text-text-muted hover:text-green-400 transition-colors"
        title="Download Report"
      >
        <Download class="h-4 w-4" />
      </button>
    </template>

    <!-- Timeline Tab -->
    <template #timeline="{ data }">
      <div class="p-6">
        
        <!-- Workflow Summary -->
        <div v-if="data" class="mb-6 p-4 bg-black/50 rounded-lg border border-gray-800">
          <div class="flex items-center justify-between mb-2">
            <span class="text-white font-medium">Process Summary</span>
            <div class="flex items-center">
              <CheckCircle v-if="data.status === 'active'" class="w-5 h-5 text-green-400 mr-2" />
              <XCircle v-else class="w-5 h-5 text-red-400 mr-2" />
              <span :class="data.status === 'active' ? 'text-green-400' : 'text-red-400'">
                {{ data.status?.toUpperCase() || 'UNKNOWN' }}
              </span>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-gray-400">Last Execution:</span>
              <span class="text-white ml-2">
                {{ data.lastExecution ? formatTimestamp(data.lastExecution.executedAt) : 'No executions' }}
              </span>
            </div>
            <div>
              <span class="text-gray-400">Duration:</span>
              <span class="text-white ml-2">
                {{ data.lastExecution ? formatDuration(data.lastExecution.duration) : 'N/A' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Info header -->
        <div class="mb-4 flex items-center justify-between">
          <div class="text-sm text-gray-400">
            Showing process steps with intelligent business data parsing
          </div>
          <div class="flex items-center text-xs text-gray-500">
            <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
            Last updated: {{ new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }) }}
          </div>
        </div>

        <!-- Timeline Steps -->
        <div v-if="data?.businessNodes?.length > 0" class="space-y-4">
          <div
            v-for="(step, index) in data.businessNodes"
            :key="step.nodeId || index"
            :class="[
              'border rounded-lg p-4 transition-all cursor-pointer',
              getStepColor(step.status),
              expandedStep === (step.nodeId || index) ? 'shadow-lg' : ''
            ]"
            @click="toggleExpanded(step.nodeId || index)"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center">
                <component :is="getStepIcon(step.status)" class="w-4 h-4 mr-3" />
                <div>
                  <div class="font-medium text-white">{{ step.name || `Step ${index + 1}` }}</div>
                  <div class="text-sm text-gray-400">
                    {{ step.status === 'not-executed' 
                      ? 'Node not executed in this run' 
                      : (step.data?.suggestedSummary || step.data?.summary || getBusinessSummary(step)) }}
                  </div>
                </div>
              </div>
              <div class="flex items-center">
                <span class="text-xs text-gray-400 mr-3">
                  {{ step.status === 'not-executed' 
                    ? 'Skipped' 
                    : formatDuration(step.executionTime || 0) }}
                </span>
                <ChevronDown 
                  v-if="expandedStep === (step.nodeId || index)"
                  class="w-4 h-4 text-gray-400" 
                />
                <ChevronRight 
                  v-else
                  class="w-4 h-4 text-gray-400" 
                />
              </div>
            </div>

            <!-- Expanded Step Details -->
            <div v-if="expandedStep === (step.nodeId || index)" class="mt-4 pt-4 border-t border-gray-700">
              
              <!-- Complete Data Overview -->
              <div v-if="step.data" class="mb-4 p-3 bg-green-400/5 rounded-lg border border-green-400/20">
                <div class="text-sm font-medium text-green-400 mb-2">Execution Data Available:</div>
                <div class="text-sm text-gray-300 mb-3">{{ step.data.suggestedSummary || 'Step completed successfully' }}</div>
                
                <!-- Data Availability Metrics -->
                <div class="grid grid-cols-2 gap-4 text-xs">
                  <div class="text-gray-400">
                    <span class="text-blue-400">Total Data Size:</span> {{ step.data.totalDataSize || 0 }} bytes
                  </div>
                  <div class="text-gray-400">
                    <span class="text-blue-400">Available Fields:</span> {{ step.data.totalAvailableFields || 0 }}
                  </div>
                  <div class="text-gray-400">
                    <span class="text-green-400">Input Data:</span> {{ step.data.hasInputData ? '✅' : '❌' }}
                  </div>
                  <div class="text-gray-400">
                    <span class="text-green-400">Output Data:</span> {{ step.data.hasOutputData ? '✅' : '❌' }}
                  </div>
                  <div class="text-gray-400">
                    <span class="text-purple-400">Node Category:</span> {{ step.data.nodeCategory || 'unknown' }}
                  </div>
                  <div class="text-gray-400">
                    <span class="text-gray-500">Executed:</span> {{ formatTimestamp(step.data.executedAt) }}
                  </div>
                </div>
                
                <!-- Available Field Lists -->
                <div v-if="step.data.availableInputFields || step.data.availableOutputFields" class="mt-3 pt-2 border-t border-gray-700">
                  <div v-if="step.data.availableInputFields" class="mb-2">
                    <span class="text-xs text-blue-400">Input Fields:</span>
                    <span class="text-xs text-gray-400 ml-2">{{ step.data.availableInputFields.join(', ') }}</span>
                  </div>
                  <div v-if="step.data.availableOutputFields">
                    <span class="text-xs text-green-400">Output Fields:</span>
                    <span class="text-xs text-gray-400 ml-2">{{ step.data.availableOutputFields.join(', ') }}</span>
                  </div>
                </div>
              </div>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <!-- Input Data - Complete -->
                <div>
                  <div class="text-sm font-medium text-white mb-2">Input Data ({{ step.data?.inputDataSize || 0 }} bytes):</div>
                  <div class="bg-gray-900 p-3 rounded text-sm text-gray-300 whitespace-pre-line">
                    {{ step.data?.inputJson ? 'Click "Show all input data" below to see complete input JSON' : 'No input data available' }}
                  </div>
                  <details class="mt-2">
                    <summary class="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                      Show all input data ({{ step.data?.availableInputFields?.length || 0 }} fields)
                    </summary>
                    <pre class="bg-gray-800 p-2 rounded text-xs text-gray-400 overflow-x-auto mt-2 max-h-96">{{ 
                      step.data?.inputJson ? JSON.stringify(step.data.inputJson, null, 2) : 'No input data' 
                    }}</pre>
                  </details>
                </div>
                
                <!-- Output Data - Complete -->
                <div>
                  <div class="text-sm font-medium text-white mb-2">Output Data ({{ step.data?.outputDataSize || 0 }} bytes):</div>
                  <div class="bg-gray-900 p-3 rounded text-sm text-gray-300 whitespace-pre-line">
                    {{ step.data?.outputJson ? 'Click "Show all output data" below to see complete output JSON' : 'No output data available' }}
                  </div>
                  <details class="mt-2">
                    <summary class="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                      Show all output data ({{ step.data?.availableOutputFields?.length || 0 }} fields)
                    </summary>
                    <pre class="bg-gray-800 p-2 rounded text-xs text-gray-400 overflow-x-auto mt-2 max-h-96">{{ 
                      step.data?.outputJson ? JSON.stringify(step.data.outputJson, null, 2) : 'No output data' 
                    }}</pre>
                  </details>
                </div>
              </div>
              
              <!-- RAW DATA Section - Complete Raw n8n Data -->
              <div v-if="step.data?.rawInputData || step.data?.rawOutputData" class="mt-4 pt-4 border-t border-gray-700">
                <div class="text-sm font-medium text-white mb-2">Complete Raw n8n Execution Data:</div>
                <details>
                  <summary class="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                    Show complete raw n8n data structure (unfiltered)
                  </summary>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                    <div v-if="step.data.rawInputData">
                      <div class="text-xs text-blue-400 mb-1">Raw Input Data:</div>
                      <pre class="bg-gray-800 p-2 rounded text-xs text-gray-400 overflow-x-auto max-h-64">{{ 
                        JSON.stringify(step.data.rawInputData, null, 2) 
                      }}</pre>
                    </div>
                    <div v-if="step.data.rawOutputData">
                      <div class="text-xs text-green-400 mb-1">Raw Output Data:</div>
                      <pre class="bg-gray-800 p-2 rounded text-xs text-gray-400 overflow-x-auto max-h-64">{{ 
                        JSON.stringify(step.data.rawOutputData, null, 2) 
                      }}</pre>
                    </div>
                  </div>
                </details>
              </div>
            </div>
          </div>
        </div>

        <!-- No Timeline Data -->
        <div v-else class="text-center py-8 text-gray-400">
          <Clock class="w-8 h-8 mx-auto mb-2" />
          <p>No process steps available</p>
          <p class="text-sm">
            Steps will appear here when process executions contain step data.
          </p>
        </div>
      </div>
    </template>

    <!-- Business Context Tab -->
    <template #context="{ data }">
      <div class="p-6 space-y-6">
        <div v-if="data?.execution?.businessContext" class="p-4 bg-black/50 rounded-lg border border-gray-800">
          <h3 class="text-lg font-medium text-white mb-4">Business Context</h3>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-if="data.execution.businessContext.customerEmail" class="flex items-center">
              <Mail class="w-4 h-4 text-blue-400 mr-2" />
              <span class="text-gray-400">Customer:</span>
              <span class="text-blue-400 ml-2">{{ data.execution.businessContext.customerEmail }}</span>
            </div>
            
            <div v-if="data.execution.businessContext.orderId" class="flex items-center">
              <Package class="w-4 h-4 text-green-400 mr-2" />
              <span class="text-gray-400">Order ID:</span>
              <span class="text-white ml-2">{{ data.execution.businessContext.orderId }}</span>
            </div>
            
            <div v-if="data.execution.businessContext.classification" class="flex items-center">
              <Tag class="w-4 h-4 text-purple-400 mr-2" />
              <span class="text-gray-400">Classification:</span>
              <span class="text-purple-400 ml-2">{{ data.execution.businessContext.classification }}</span>
            </div>
            
            <div v-if="data.execution.businessContext.aiResponseGenerated" class="flex items-center">
              <Bot class="w-4 h-4 text-green-400 mr-2" />
              <span class="text-gray-400">AI Response:</span>
              <span class="text-green-400 ml-2">Generated</span>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div v-if="data?.execution?.businessContext?.customerEmail" class="p-4 bg-black/50 rounded-lg border border-gray-800">
          <h3 class="text-lg font-medium text-white mb-4">Quick Actions</h3>
          <div class="flex space-x-4">
            <button
              @click="replyToCustomer(data.execution.businessContext)"
              class="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
            >
              <Mail class="w-4 h-4 mr-2" />
              Reply to Customer
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- Raw Data Tab -->
    <template #raw="{ data }">
      <div class="p-6">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center">
            <Code class="w-5 h-5 text-gray-400 mr-2" />
            <h3 class="text-lg font-medium text-white">Raw Timeline Data</h3>
          </div>
          <div class="flex gap-2">
            <button
              @click="generateBusinessReport"
              class="flex items-center px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
            >
              <FileText class="w-4 h-4 mr-1.5" />
              Generate Report
            </button>
            <button
              @click="showJsonData"
              class="flex items-center px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
            >
              <Code class="w-4 h-4 mr-1.5" />
              Show JSON
            </button>
          </div>
        </div>
        
        <pre 
          id="raw-data-content"
          class="bg-black/50 p-4 rounded-lg border border-gray-800 text-xs text-gray-300 overflow-auto max-h-96 font-mono whitespace-pre premium-scrollbar"
        >{{ 
          data ? 
          JSON.stringify(data, null, 2)
            .replace(/n8n/gi, 'WFEngine')
            .replace(/\.nodes\./g, '.engine.')
            .replace(/\.base\./g, '.core.')
          : 'No data available' 
        }}</pre>
      </div>
    </template>
  </DetailModal>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { 
  Bot, CheckCircle, XCircle, Clock, Settings, ChevronDown, ChevronRight,
  Mail, Package, FileText, Tag, Code, Download
} from 'lucide-vue-next'
import DetailModal from './DetailModal.vue'
import { useModal } from '../../composables/useModal'
import { useBusinessParser } from '../../composables/useBusinessParser'

interface Props {
  workflowId: string
  executionId?: string
  tenantId?: string
  show: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
}>()

// Composables
const { isLoading, error, setLoading, setError, showToast } = useModal()
const { parseBusinessData, formatBusinessData } = useBusinessParser()

// State
const timelineData = ref<any>(null)
const expandedStep = ref<string | null>(null)

// Modal configuration
const modalTitle = computed(() => {
  return timelineData.value?.workflow?.name || `Business Process ${props.workflowId}`
})

const modalSubtitle = computed(() => {
  if (!timelineData.value) return ''
  const workflow = timelineData.value.workflow
  const execution = timelineData.value.execution
  const status = workflow?.active ? 'ACTIVE' : 'INACTIVE'
  return `ID: ${props.workflowId} • Status: ${status}${execution ? ` • Last: ${execution.id}` : ''}`
})

const tabs = [
  { id: 'timeline', label: 'Timeline', icon: Clock },
  { id: 'context', label: 'Business Context', icon: FileText },
  { id: 'raw', label: 'Raw Data', icon: Code },
]

// Timeline logic
const loadTimeline = async () => {
  setLoading(true)
  setError(null)
  
  try {
    console.log('🔄 Loading raw data for modal:', props.workflowId, props.executionId ? `(execution: ${props.executionId})` : '(latest)')
    
    let url = `http://localhost:3001/api/business/raw-data-for-modal/${props.workflowId}`
    if (props.executionId) {
      url += `?executionId=${props.executionId}`
    }
    
    const response = await fetch(url)
    
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('✅ Process timeline loaded:', data.data)
    
    timelineData.value = data.data
    
  } catch (err: any) {
    console.error('❌ Failed to load process timeline:', err)
    setError(err.message)
  } finally {
    setLoading(false)
  }
}

const handleForceRefresh = async () => {
  try {
    console.log('🔥 Force refresh: Process timeline for', props.workflowId)
    
    // Try force refresh endpoint first
    try {
      const refreshResponse = await fetch(`http://localhost:3001/api/business/process-refresh/${props.workflowId}`, {
        method: 'POST'
      })
      
      if (refreshResponse.ok) {
        console.log('✅ Force refresh succeeded')
        showToast('success', 'Timeline data refreshed successfully')
      }
    } catch (refreshError) {
      console.warn('⚠️ Force refresh endpoint not available:', refreshError)
    }
    
    // Reload timeline data
    await loadTimeline()
    
  } catch (error: any) {
    showToast('error', 'Failed to refresh', error.message)
  }
}

// Step visualization helpers
const getStepIcon = (status: string) => {
  switch (status) {
    case 'success': return CheckCircle
    case 'error': return XCircle
    case 'running': return Settings
    case 'not-executed': return Clock
    default: return Clock
  }
}

const getStepColor = (status: string) => {
  switch (status) {
    case 'success': return 'border-green-400/30 bg-green-400/5 hover:bg-green-400/10'
    case 'error': return 'border-red-400/30 bg-red-400/5 hover:bg-red-400/10'
    case 'running': return 'border-yellow-400/30 bg-yellow-400/5 hover:bg-yellow-400/10'
    case 'not-executed': return 'border-gray-600/30 bg-gray-800/50 hover:bg-gray-700/50'
    default: return 'border-gray-400/30 bg-gray-400/5 hover:bg-gray-400/10'
  }
}

const getBusinessSummary = (step: any): string => {
  const parsedData = parseBusinessData(
    step.outputData || step.inputData,
    step.outputData ? 'output' : 'input',
    step.nodeType,
    step.nodeName
  )
  return parsedData.summary
}

const getBusinessData = (step: any, dataType: 'input' | 'output'): string => {
  const data = dataType === 'input' ? step.inputData : step.outputData
  const parsedData = parseBusinessData(data, dataType, step.nodeType, step.nodeName)
  return formatBusinessData(parsedData)
}

const toggleExpanded = (stepId: string | number) => {
  expandedStep.value = expandedStep.value === stepId ? null : String(stepId)
}

// Utility functions
const formatDuration = (ms: number) => {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}min`
}

const formatTimestamp = (timestamp: string | number) => {
  // Handle both string ISO dates and Unix timestamps
  const date = typeof timestamp === 'number' ? new Date(timestamp) : new Date(timestamp)
  return date.toLocaleString('it-IT', {
    dateStyle: 'short',
    timeStyle: 'medium'
  })
}

// Actions
const replyToCustomer = (context: any) => {
  const customerEmail = context.customerEmail
  const subject = context.subject || ''
  
  if (customerEmail) {
    window.open(`mailto:${customerEmail}?subject=Re: ${subject}`, '_blank')
  }
}

const downloadReport = () => {
  if (!timelineData.value) return
  
  const reportContent = generateBusinessReport()
  const blob = new Blob([reportContent], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `business-process-report-${props.workflowId}-${new Date().toISOString().slice(0, 10)}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const generateBusinessReport = (): string => {
  if (!timelineData.value) return ''
  
  let report = `╔${'═'.repeat(78)}╗\n`
  report += `║${' '.repeat(15)}BUSINESS PROCESS EXECUTION REPORT${' '.repeat(16)}║\n`
  report += `║${' '.repeat(25)}PilotPro Control Center${' '.repeat(29)}║\n`
  report += `╚${'═'.repeat(78)}╝\n\n`
  
  // Process Information
  report += `┌─ PROCESS INFORMATION ${'─'.repeat(56)}┐\n\n`
  report += `  Process Name:      ${timelineData.value.workflowName || 'Not specified'}\n`
  report += `  Process ID:        ${props.workflowId}\n`
  report += `  Status:            ${timelineData.value.status === 'active' ? 'ACTIVE' : 'INACTIVE'}\n`
  
  if (timelineData.value.lastExecution) {
    report += `\n  LAST EXECUTION:\n`
    report += `  ├─ Execution ID:   ${timelineData.value.lastExecution.id}\n`
    report += `  ├─ Date/Time:      ${formatTimestamp(timelineData.value.lastExecution.executedAt)}\n`
    report += `  ├─ Total Duration: ${formatDuration(timelineData.value.lastExecution.duration)}\n`
    report += `  └─ Status:         ${timelineData.value.lastExecution.status || 'Completed'}\n`
  }
  
  report += `\n└${'─'.repeat(78)}┘\n\n`
  
  // Business Context
  if (timelineData.value.execution?.businessContext && Object.keys(timelineData.value.execution.businessContext).length > 0) {
    report += `┌─ BUSINESS CONTEXT ANALYSIS ${'─'.repeat(50)}┐\n\n`
    
    const context = timelineData.value.execution.businessContext
    if (context.customerEmail) {
      report += `  CUSTOMER INFORMATION:\n`
      report += `     Email: ${context.customerEmail}\n\n`
    }
    
    if (context.subject) {
      report += `  COMMUNICATION SUBJECT:\n`
      report += `     "${context.subject}"\n\n`
    }
    
    if (context.orderId) {
      report += `  ORDER REFERENCE:\n`
      report += `     Order ID: ${context.orderId}\n\n`
    }
    
    if (context.classification) {
      report += `  AI CLASSIFICATION:\n`
      report += `     Category: ${context.classification}\n`
      if (context.confidence) {
        report += `     Confidence: ${context.confidence}%\n`
      }
      report += `\n`
    }
    
    report += `└${'─'.repeat(78)}┘\n\n`
  }
  
  return report
}

const showJsonData = () => {
  const preElement = document.getElementById('raw-data-content')
  if (preElement && timelineData.value) {
    const sanitizedJson = JSON.stringify(timelineData.value, null, 2)
      .replace(/n8n/gi, 'WFEngine')
      .replace(/\.nodes\./g, '.engine.')
      .replace(/\.base\./g, '.core.')
    preElement.textContent = sanitizedJson
  }
}

// Lifecycle
watch(() => props.show, (newShow) => {
  if (newShow) {
    console.log('📊 Timeline modal opened for process:', props.workflowId)
    loadTimeline()
  }
})

onMounted(() => {
  if (props.show) {
    loadTimeline()
  }
})
</script>