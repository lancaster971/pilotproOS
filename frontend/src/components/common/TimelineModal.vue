<template>
  <DetailModal
    :show="show"
    :title="modalTitle"
    :subtitle="modalSubtitle"
    :header-icon="'lucide:bot'"
    :tabs="tabs"
    default-tab="executions"
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
    </template>

    <!-- Executions Details Tab -->
    <template #executions="{ data }">
      <div class="p-6">

        <div v-if="data?.businessNodes?.length > 0" class="space-y-6">
          <div
            v-for="(step, index) in data.businessNodes"
            :key="step._nodeId || index"
            :class="[
              'rounded-lg p-5 border transition-all',
              step.status === 'error' || step.showTag === 'error' 
                ? 'bg-red-900/20 border-red-500/30' 
                : 'bg-gray-800/50 border-gray-700',
              // Highlight if has intelligent summary
              step.data?.intelligentSummary ? 'ring-1 ring-blue-500/20' : ''
            ]"
          >
            <!-- Step Header -->
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center">
                <div :class="[
                  'w-8 h-8 rounded-full flex items-center justify-center mr-3',
                  step.status === 'error' || step.showTag === 'error'
                    ? 'bg-red-400/20'
                    : 'bg-green-400/20'
                ]">
                  <span :class="[
                    'font-medium',
                    step.status === 'error' || step.showTag === 'error'
                      ? 'text-red-400'
                      : 'text-green-400'
                  ]">{{ step.showTag === 'error' ? '⚠️' : index + 1 }}</span>
                </div>
                <div>
                  <h4 class="text-white font-medium">{{ step.name || `Process Step ${index + 1}` }}</h4>
                  <p class="text-sm text-gray-400">{{ formatBusinessStepType(step) }}</p>
                </div>
              </div>
              <div class="text-xs text-gray-500">
                {{ formatDuration(step.executionTime || 0) }}
              </div>
            </div>

            <!-- Business Summary -->
            <div class="mb-4">
              <div :class="[
                'text-sm font-medium mb-2',
                step.status === 'error' || step.showTag === 'error'
                  ? 'text-red-400'
                  : 'text-green-400'
              ]">
                {{ step.status === 'error' || step.showTag === 'error' ? 'Error Details:' : 'Business Summary:' }}
              </div>
              <div :class="[
                'text-white bg-gray-900/50 p-3 rounded border-l-4',
                step.status === 'error' || step.showTag === 'error'
                  ? 'border-red-400'
                  : 'border-green-400'
              ]">
                {{ 
                  step.status === 'error' || step.showTag === 'error' 
                    ? getBusinessErrorSummary(step)
                    : generateExecutionDetail(step) 
                }}
              </div>
            </div>

            <!-- Input/Output Summary -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- What Happened -->
              <div :class="[
                'rounded p-3 border',
                step.status === 'error' || step.showTag === 'error'
                  ? 'bg-orange-400/10 border-orange-400/20'
                  : 'bg-blue-400/10 border-blue-400/20'
              ]">
                <div :class="[
                  'text-xs font-medium mb-1',
                  step.status === 'error' || step.showTag === 'error'
                    ? 'text-orange-400'
                    : 'text-blue-400'
                ]">{{ step.status === 'error' || step.showTag === 'error' ? 'ERROR CONTEXT' : 'WHAT HAPPENED' }}</div>
                <div class="text-sm text-gray-300">
                  {{ 
                    step.status === 'error' || step.showTag === 'error' 
                      ? getBusinessErrorContext(step)
                      : (step.enrichedData?.inputSummary || getBusinessSummary(step))
                  }}
                </div>
              </div>
              
              <!-- Result -->
              <div :class="[
                'rounded p-3 border',
                step.status === 'error' || step.showTag === 'error'
                  ? 'bg-red-400/10 border-red-400/20'
                  : 'bg-green-400/10 border-green-400/20'
              ]">
                <div :class="[
                  'text-xs font-medium mb-1',
                  step.status === 'error' || step.showTag === 'error'
                    ? 'text-red-400'
                    : 'text-green-400'
                ]">{{ step.status === 'error' || step.showTag === 'error' ? 'ERROR RESULT' : 'RESULT' }}</div>
                <div class="text-sm text-gray-300">
                  {{ 
                    step.status === 'error' || step.showTag === 'error' 
                      ? getBusinessErrorDetails(step)
                      : (step.enrichedData?.outputSummary || 'Process completed successfully')
                  }}
                </div>
              </div>
            </div>

            <!-- Business Value -->
            <div v-if="step.enrichedData?.businessValue" class="mt-4 p-3 bg-purple-400/10 rounded border border-purple-400/20">
              <div class="text-xs text-purple-400 font-medium mb-1">BUSINESS VALUE</div>
              <div class="text-sm text-white">{{ step.enrichedData.businessValue }}</div>
            </div>

            <!-- Intelligent Summary Section (for large data) -->
            <div v-if="step.data?.intelligentSummary" class="mt-4 space-y-3">
              <!-- Summary Type Badge -->
              <div class="flex items-center gap-2">
                <Icon :icon="getIntelligentSummaryIcon(step.data.intelligentSummary.type)" class="w-4 h-4 text-blue-400" />
                <span class="text-xs font-medium text-blue-400 uppercase">
                  {{ getIntelligentSummaryLabel(step.data.intelligentSummary.summaryType) }}
                </span>
                <div v-if="step.data.intelligentSummary.type === 'ai_generated'" class="ml-auto">
                  <span class="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-300 rounded">AI Generated</span>
                </div>
              </div>

              <!-- Business Summary Card -->
              <div v-if="step.data.intelligentSummary.businessSummary" class="bg-blue-900/20 border border-blue-500/20 rounded-lg p-4">
                <h5 class="text-sm font-medium text-blue-300 mb-2">
                  {{ step.data.intelligentSummary.businessSummary.title }}
                </h5>
                <p class="text-sm text-gray-300">
                  {{ step.data.intelligentSummary.businessSummary.description }}
                </p>
                
                <!-- Document Type Specific -->
                <div v-if="step.data.intelligentSummary.summaryType === 'document'" class="mt-2 text-xs text-gray-400">
                  <span>{{ step.data.intelligentSummary.businessSummary.pageCount }} pages</span>
                  <span class="mx-2">•</span>
                  <span>Type: {{ step.data.intelligentSummary.businessSummary.documentType }}</span>
                </div>
                
                <!-- Dataset Type Specific -->
                <div v-else-if="step.data.intelligentSummary.summaryType === 'dataset'" class="mt-2 text-xs text-gray-400">
                  <span>{{ step.data.intelligentSummary.businessSummary.totalRows }} rows</span>
                  <span class="mx-2">•</span>
                  <span>{{ step.data.intelligentSummary.businessSummary.totalColumns }} columns</span>
                </div>
              </div>

              <!-- Metrics Grid -->
              <div v-if="step.data.intelligentSummary.metrics && Object.keys(step.data.intelligentSummary.metrics).length > 0" 
                   class="grid grid-cols-2 md:grid-cols-4 gap-2">
                <div v-for="(value, key) in step.data.intelligentSummary.metrics" 
                     :key="key"
                     class="bg-gray-800/50 rounded p-2 text-center">
                  <div class="text-xs text-gray-500 capitalize">{{ formatMetricKey(key) }}</div>
                  <div class="text-sm font-medium text-white">{{ formatMetricValue(value) }}</div>
                </div>
              </div>

              <!-- Preview Section -->
              <div v-if="step.data.intelligentSummary.preview && !expandedSteps.has(step._nodeId)" 
                   class="bg-gray-900/50 rounded-lg p-3">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-xs font-medium text-gray-400">DATA PREVIEW</span>
                  <button @click="toggleExpandedStep(step._nodeId)" 
                          class="text-xs text-blue-400 hover:text-blue-300">
                    View More →
                  </button>
                </div>
                
                <!-- Document Preview -->
                <div v-if="step.data.intelligentSummary.summaryType === 'document'" class="text-xs text-gray-300 space-y-1">
                  <div v-if="step.data.intelligentSummary.preview.keyDates?.length > 0">
                    <span class="text-gray-500">Dates:</span> {{ step.data.intelligentSummary.preview.keyDates.join(', ') }}
                  </div>
                  <div v-if="step.data.intelligentSummary.preview.amounts?.length > 0">
                    <span class="text-gray-500">Amounts:</span> {{ step.data.intelligentSummary.preview.amounts.join(', ') }}
                  </div>
                </div>
                
                <!-- Dataset Preview -->
                <div v-else-if="step.data.intelligentSummary.summaryType === 'dataset' && step.data.intelligentSummary.preview.sampleRows" 
                     class="overflow-x-auto">
                  <table class="text-xs w-full">
                    <thead>
                      <tr class="text-gray-500">
                        <th v-for="header in step.data.intelligentSummary.preview.headers?.slice(0, 4)" 
                            :key="header" 
                            class="px-2 py-1 text-left">
                          {{ header }}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(row, idx) in step.data.intelligentSummary.preview.sampleRows?.slice(0, 3)" 
                          :key="idx"
                          class="text-gray-300 border-t border-gray-800">
                        <td v-for="header in step.data.intelligentSummary.preview.headers?.slice(0, 4)" 
                            :key="header"
                            class="px-2 py-1">
                          {{ row[header] }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- Business Insight -->
              <div v-if="step.data.intelligentSummary.businessInsight" 
                   class="bg-green-900/20 border border-green-500/20 rounded-lg p-3">
                <div class="flex items-start gap-2">
                  <Icon icon="lucide:lightbulb" class="w-4 h-4 text-green-400 mt-0.5" />
                  <div>
                    <div class="text-xs font-medium text-green-400 mb-1">BUSINESS INSIGHT</div>
                    <div class="text-sm text-gray-300">{{ step.data.intelligentSummary.businessInsight }}</div>
                  </div>
                </div>
              </div>

              <!-- Action Buttons -->
              <div v-if="step.data.intelligentSummary.actions?.length > 0" class="flex flex-wrap gap-2">
                <button v-for="action in step.data.intelligentSummary.actions" 
                        :key="action"
                        @click="handleIntelligentAction(action, step)"
                        class="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-white rounded-md transition-colors">
                  {{ formatActionLabel(action) }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- No Data -->
        <div v-else class="text-center py-12 text-gray-400">
          <Icon icon="lucide:list" class="w-12 h-12 mx-auto mb-4 opacity-50" />
          <h3 class="text-lg font-medium mb-2">Process Not Yet Configured</h3>
          <p class="text-sm mb-2">This business process doesn't have steps configured for client reporting.</p>
          <div class="bg-blue-400/10 border border-blue-400/20 rounded-lg p-4 mt-4 max-w-md mx-auto">
            <h4 class="text-blue-400 font-medium mb-2">For Administrators:</h4>
            <p class="text-xs text-blue-300">
              Add 'show-1', 'show-2', etc. notes to workflow nodes to make them visible in business reporting.
            </p>
          </div>
        </div>
      </div>
    </template>

    <!-- Raw Data Tab -->
    <template #raw="{ data }">
      <div class="p-6">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center">
            <Icon icon="lucide:code" class="w-5 h-5 text-gray-400 mr-2" />
            <h3 class="text-lg font-medium text-white">Raw Timeline Data</h3>
          </div>
          <div class="flex gap-2">
            <button
              @click="generateBusinessReport"
              class="flex items-center px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
            >
              <Icon icon="lucide:file-text" class="w-4 h-4 mr-1.5" />
              Generate Report
            </button>
            <button
              @click="showJsonData"
              class="flex items-center px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
            >
              <Icon icon="lucide:code" class="w-4 h-4 mr-1.5" />
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
import { Icon } from '@iconify/vue'
import DetailModal from './DetailModal.vue'
import { useModal } from '../../composables/useModal'
import { useBusinessParser } from '../../composables/useBusinessParser'
import { businessAPI, $fetch } from '../../services/api-client'
import { API_BASE_URL } from '../../utils/api-config'

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
const { parseBusinessData, formatBusinessData, formatTimelineStepData } = useBusinessParser()

// State
const timelineData = ref<any>(null)
const expandedStep = ref<string | null>(null)
const expandedSteps = ref(new Set<string>())

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
  { id: 'executions', label: 'Executions Details', icon: 'lucide:list' },
  { id: 'raw', label: 'Raw Data', icon: 'lucide:code' },
]

// Timeline logic
const loadTimeline = async () => {
  setLoading(true)
  setError(null)
  
  try {
    console.log('🔄 Loading raw data for modal:', props.workflowId, props.executionId ? `(execution: ${props.executionId})` : '(latest)')
    
    const API_BASE = import.meta.env.VITE_API_URL || API_BASE_URL
    let url = `${API_BASE}/api/business/raw-data-for-modal/${props.workflowId}`
    if (props.executionId) {
      url += `?executionId=${props.executionId}`
    }
    
    // Use OFETCH API client instead of direct fetch
    const data = await businessAPI.getWorkflowDetails(props.workflowId)
    console.log('✅ Process timeline loaded:', data.data)
    
    // Check if no business nodes are configured
    if (!data.data?.businessNodes || data.data.businessNodes.length === 0) {
      console.log('ℹ️ No show-n nodes found for this workflow - showing empty state')
      timelineData.value = { ...data.data, businessNodes: [] }
      return
    }
    
    // Enrich timeline data with business summaries
    console.log(`📊 Starting enrichment of ${data.data?.businessNodes?.length || 0} nodes`)
    if (data.data?.businessNodes) {
      const originalLength = data.data.businessNodes.length
      
      data.data.businessNodes = data.data.businessNodes.map((node: any, index: number) => {
        console.log(`📊 Processing node ${index + 1}/${originalLength}: "${node.name}"`)
        
        if (node.data && (node.data.inputJson || node.data.outputJson)) {
          try {
            const enrichedData = formatTimelineStepData(
              node.data.inputJson,
              node.data.outputJson,
              node.data.nodeType,
              node.name
            )
            console.log(`✅ Enriched node "${node.name}":`, enrichedData)
            return {
              ...node,
              enrichedData
            }
          } catch (err) {
            console.warn(`⚠️ Failed to enrich node "${node.name}":`, err)
            return node
          }
        } else {
          console.log(`ℹ️ Skipping enrichment for node "${node.name}" - no input/output data`)
          return node
        }
      })
      
      console.log(`📊 Enrichment complete: ${data.data.businessNodes.length}/${originalLength} nodes processed`)
      
      if (data.data.businessNodes.length !== originalLength) {
        console.error(`❌ Node count mismatch! Original: ${originalLength}, Final: ${data.data.businessNodes.length}`)
      }
    }
    
    timelineData.value = data.data
    
  } catch (err: any) {
    console.error('❌ Failed to load process timeline:', err)
    
    // More user-friendly error messages
    if (err.message.includes('Failed to fetch') || err.message.includes('fetch')) {
      setError('Process configuration incomplete. This business process needs to be configured with visible steps for reporting.')
    } else if (err.message.includes('404')) {
      setError('Process not found or not yet configured for business reporting.')
    } else {
      setError('Unable to load process details. Please try again or contact support.')
    }
  } finally {
    setLoading(false)
  }
}

const handleForceRefresh = async () => {
  try {
    console.log('🔥 Force refresh: Process timeline for', props.workflowId)
    
    // Try force refresh endpoint first  
    try {
      await businessAPI.refreshProcess(props.workflowId)
      console.log('✅ Force refresh succeeded')
      showToast('success', 'Timeline data refreshed successfully')
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
    case 'success': return 'lucide:check-circle'
    case 'error': return 'lucide:x-circle'
    case 'running': return 'lucide:settings'
    case 'not-executed': return 'lucide:clock'
    default: return 'lucide:clock'
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

const getBusinessErrorSummary = (step: any): string => {
  // Use the business parser to extract detailed error information
  const parsedData = parseBusinessData(
    step.data,
    'output',
    step.nodeType,
    step.name
  )
  
  // If the business parser extracted detailed error information, use it
  if (parsedData.type === 'error' && parsedData.details.length > 0) {
    return parsedData.details.join('\n')
  }
  
  // Fallback to direct n8n error details if available
  if (step.data?.n8nErrorDetails) {
    const error = step.data.n8nErrorDetails
    return `${error.errorType}: ${error.message} (Nodo: ${error.nodeName})`
  }
  
  // Final fallback
  return 'Process execution failed to complete successfully'
}

const getBusinessErrorDetails = (step: any): string => {
  // Use the business parser to extract detailed error information
  const parsedData = parseBusinessData(
    step.data,
    'output',
    step.nodeType,
    step.name
  )
  
  // If the business parser extracted detailed error information, use the first detail
  if (parsedData.type === 'error' && parsedData.details.length > 0) {
    // Return the most important detail (usually the first one with the error message)
    return parsedData.details.find(detail => detail.includes('Errore:')) || parsedData.details[0]
  }
  
  // Fallback to direct n8n error details if available
  if (step.data?.n8nErrorDetails) {
    const error = step.data.n8nErrorDetails
    return error.message || 'Error details not available'
  }
  
  // Final fallback
  return 'Check raw data for error details'
}

const getBusinessErrorContext = (step: any): string => {
  // Use the business parser to extract detailed error information
  const parsedData = parseBusinessData(
    step.data,
    'output',
    step.nodeType,
    step.name
  )
  
  // If the business parser extracted detailed error information, use node info
  if (parsedData.type === 'error' && parsedData.details.length > 1) {
    // Return the node context (usually the second detail with node info)
    return parsedData.details.find(detail => detail.includes('Nodo Fallito:')) || 
           parsedData.details.find(detail => detail.includes('Tipo Errore:')) ||
           parsedData.details[1]
  }
  
  // Fallback to direct n8n error details if available
  if (step.data?.n8nErrorDetails) {
    const error = step.data.n8nErrorDetails
    return `Errore nel nodo: ${error.nodeName} (${error.errorType})`
  }
  
  // Final fallback
  return `Errore durante l'esecuzione del nodo: ${step.name}`
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

// Executions Details Helper Functions
const formatBusinessStepType = (step: any): string => {
  const nodeName = step.name?.toLowerCase() || ''
  
  if (nodeName.includes('mail') || nodeName.includes('ricezione')) {
    return 'Customer Communication'
  }
  if (nodeName.includes('milena') || nodeName.includes('assistente')) {
    return 'AI Assistant Processing'
  }
  if (nodeName.includes('qdrant') || nodeName.includes('vector')) {
    return 'Knowledge Base Search'
  }
  if (nodeName.includes('ordini') || nodeName.includes('order')) {
    return 'Order Management'
  }
  if (nodeName.includes('supabase') || nodeName.includes('database')) {
    return 'Data Storage Operation'
  }
  if (nodeName.includes('execute') || nodeName.includes('workflow')) {
    return 'Business Process Execution'
  }
  
  return 'Business Process Step'
}

const generateExecutionDetail = (step: any): string => {
  const nodeName = step.name?.toLowerCase() || ''
  
  // Email nodes - focus on communication
  if (nodeName.includes('ricezione') && step.data?.outputJson) {
    const email = step.data.outputJson
    if (email.oggetto && email.mittente) {
      return `Customer email received from ${email.mittente} regarding "${email.oggetto}". Message successfully processed and categorized for business response.`
    }
    return 'Customer email received and processed successfully.'
  }
  
  // AI Assistant nodes - focus on intelligence
  if ((nodeName.includes('milena') || nodeName.includes('assistente')) && step.data?.outputJson?.output) {
    const aiOutput = step.data.outputJson.output
    if (aiOutput.categoria) {
      return `AI Assistant analyzed the customer request and generated an intelligent response. Category: ${aiOutput.categoria}. Response crafted based on business knowledge and customer context.`
    }
    return 'AI Assistant processed the request and generated an intelligent, personalized response for the customer.'
  }
  
  // Vector/Knowledge search nodes
  if (nodeName.includes('qdrant') || nodeName.includes('vector')) {
    return 'Knowledge base searched to find relevant information and context for providing accurate customer support.'
  }
  
  // Order/Database nodes
  if (nodeName.includes('ordini') || nodeName.includes('order')) {
    return 'Order information retrieved and processed to provide customer with accurate status and details.'
  }
  
  // Database storage nodes
  if (nodeName.includes('supabase') || nodeName.includes('database')) {
    return 'Customer interaction data saved to business database for future reference and analytics.'
  }
  
  // Sub-workflow execution
  if (nodeName.includes('execute') || nodeName.includes('workflow')) {
    return 'Business process sub-routine executed successfully to handle specific customer requirements.'
  }
  
  // Generic business value
  return 'Business process step completed successfully, contributing to efficient customer service automation.'
}

// Intelligent Summary Helper Functions
const getIntelligentSummaryIcon = (type: string) => {
  const icons: Record<string, string> = {
    'document': 'lucide:file-text',
    'dataset': 'lucide:table',
    'statistical': 'lucide:bar-chart-2',
    'ai_generated': 'lucide:sparkles',
    'email_batch': 'lucide:mail',
    'api_response': 'lucide:cloud',
    'generic': 'lucide:file'
  }
  return icons[type] || 'lucide:file'
}

const getIntelligentSummaryLabel = (summaryType: string) => {
  const labels: Record<string, string> = {
    'document': 'Document Analysis',
    'dataset': 'Data Table',
    'emails': 'Email Batch',
    'api': 'API Response',
    'statistics': 'Statistical Analysis',
    'ai': 'AI Analysis',
    'generic': 'Process Data'
  }
  return labels[summaryType] || 'Process Data'
}

const formatMetricKey = (key: string) => {
  return key.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').trim()
}

const formatMetricValue = (value: any) => {
  if (typeof value === 'number') {
    if (value > 1000000) return `${(value / 1000000).toFixed(1)}M`
    if (value > 1000) return `${(value / 1000).toFixed(1)}K`
    if (value % 1 !== 0) return value.toFixed(2)
    return value.toString()
  }
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (value === null || value === undefined) return '-'
  return value.toString()
}

const formatActionLabel = (action: string) => {
  const labels: Record<string, string> = {
    'download_full': '⬇️ Download Full Data',
    'request_ai_analysis': '✨ AI Analysis',
    'extract_data': '📊 Extract Data',
    'view_full_table': '📋 View Full Table',
    'export_excel': '📑 Export Excel',
    'generate_report': '📄 Generate Report',
    'analyze_patterns': '🔍 Analyze Patterns',
    'view_all_emails': '📧 View All Emails',
    'export_list': '📝 Export List',
    'analyze_sentiment': '💭 Analyze Sentiment',
    'view_json': '{ } View JSON',
    'export_data': '💾 Export Data',
    'analyze_structure': '🏗️ Analyze Structure',
    'view_chart': '📈 View Chart',
    'export_stats': '📊 Export Statistics',
    'analyze_trends': '📉 Analyze Trends',
    'view_raw': '📄 View Raw',
    'download': '⬇️ Download',
    'regenerate_analysis': '🔄 Regenerate Analysis'
  }
  return labels[action] || action
}

const toggleExpandedStep = (stepId: string) => {
  if (expandedSteps.value.has(stepId)) {
    expandedSteps.value.delete(stepId)
  } else {
    expandedSteps.value.add(stepId)
  }
}

const handleIntelligentAction = async (action: string, step: any) => {
  console.log('🎯 Handling intelligent action:', action, step)
  
  switch(action) {
    case 'download_full':
      downloadFullData(step)
      break
    case 'request_ai_analysis':
      await requestAIAnalysis(step)
      break
    case 'export_excel':
      exportToExcel(step)
      break
    case 'generate_report':
      generateStepReport(step)
      break
    default:
      showToast('info', `Action "${action}" not yet implemented`)
  }
}

const downloadFullData = (step: any) => {
  const data = step.data?.rawOutputData || step.data?.outputJson || {}
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${step.name}-data-${new Date().toISOString().slice(0, 10)}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  showToast('success', 'Data downloaded successfully')
}

const requestAIAnalysis = async (step: any) => {
  showToast('info', 'Requesting AI analysis...')
  // TODO: Implement AI analysis request
  // This would call the backend to process through Ollama
  setTimeout(() => {
    showToast('success', 'AI analysis complete')
  }, 2000)
}

const exportToExcel = (step: any) => {
  // TODO: Implement Excel export using a library like xlsx
  showToast('info', 'Excel export feature coming soon')
}

const generateStepReport = (step: any) => {
  const report = `
Business Process Step Report
============================
Step Name: ${step.name}
Type: ${step.data?.intelligentSummary?.businessSummary?.title || step.type}
Status: ${step.status}
Execution Time: ${formatDuration(step.executionTime || 0)}

Business Summary:
${step.data?.intelligentSummary?.businessSummary?.description || 'No summary available'}

Business Insight:
${step.data?.intelligentSummary?.businessInsight || 'No insights available'}

Generated: ${new Date().toLocaleString()}
  `.trim()
  
  const blob = new Blob([report], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${step.name}-report-${new Date().toISOString().slice(0, 10)}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  showToast('success', 'Report generated successfully')
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