<template>
  <DetailModal
    :show="show"
    :title="modalTitle"
    :subtitle="modalSubtitle"
    :header-icon="Bot"
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
              'rounded-lg p-5 border',
              step.status === 'error' || step.showTag === 'error' 
                ? 'bg-red-900/20 border-red-500/30' 
                : 'bg-gray-800/50 border-gray-700'
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
          </div>
        </div>

        <!-- No Data -->
        <div v-else class="text-center py-12 text-gray-400">
          <List class="w-12 h-12 mx-auto mb-4 opacity-50" />
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
  Mail, Package, FileText, Tag, Code, Download, List
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
const { parseBusinessData, formatBusinessData, formatTimelineStepData } = useBusinessParser()

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
  { id: 'executions', label: 'Executions Details', icon: List },
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