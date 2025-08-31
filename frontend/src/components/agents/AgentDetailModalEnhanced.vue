<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="$emit('close')"
    >
      <div class="control-card w-full max-w-7xl max-h-[95vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-border">
          <div class="flex items-center">
            <Database class="w-6 h-6 text-primary mr-3" />
            <div>
              <h2 class="text-xl font-semibold text-text">
                {{ timelineData?.processName || selectedWorkflowData?.process_name || `Process ${workflowId}` }}
              </h2>
              <p class="text-text-muted text-sm">
                ID: {{ workflowId }}
                <span v-if="timelineData?.lastExecution" class="ml-3">
                  • Last execution: {{ timelineData.lastExecution.id }}
                </span>
              </p>
            </div>
          </div>
          <div class="flex items-center space-x-3">
            <!-- Force Refresh Button -->
            <button
              @click="forceRefresh"
              :disabled="isRefreshing"
              class="btn-control-primary"
              :class="isRefreshing && 'opacity-50 cursor-not-allowed'"
            >
              <RefreshCw :class="{ 'animate-spin': isRefreshing }" class="w-4 h-4 mr-2" />
              {{ isRefreshing ? 'Refreshing...' : 'Refresh' }}
            </button>
            
            <button
              @click="$emit('close')"
              class="p-2 text-text-muted hover:text-text hover:bg-surface-hover rounded"
            >
              <X class="w-5 h-5" />
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <div class="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p class="text-text-muted">Loading process timeline from backend...</p>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <XCircle class="h-12 w-12 text-error mx-auto mb-4" />
            <p class="text-error">{{ error }}</p>
            <button @click="loadTimeline" class="mt-4 btn-control-primary">
              Try Again
            </button>
          </div>
        </div>

        <!-- Content with Tabs -->
        <div v-else class="flex-1 flex flex-col">
          <!-- Tab Navigation -->
          <div class="flex border-b border-border bg-surface/30">
            <button
              @click="activeTab = 'timeline'"
              class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
              :class="activeTab === 'timeline'
                ? 'border-primary text-primary bg-primary/5'
                : 'border-transparent text-text-muted hover:text-text'"
            >
              <Clock class="w-4 h-4 inline mr-2" />
              Process Timeline
            </button>
            <button
              @click="activeTab = 'flow'"
              class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
              :class="activeTab === 'flow'
                ? 'border-primary text-primary bg-primary/5'
                : 'border-transparent text-text-muted hover:text-text'"
            >
              <GitBranch class="w-4 h-4 inline mr-2" />
              Flow Visualization
            </button>
            <button
              @click="activeTab = 'context'"
              class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
              :class="activeTab === 'context'
                ? 'border-primary text-primary bg-primary/5'
                : 'border-transparent text-text-muted hover:text-text'"
            >
              <Database class="w-4 h-4 inline mr-2" />
              Business Context
            </button>
            <button
              @click="activeTab = 'raw'"
              class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
              :class="activeTab === 'raw'
                ? 'border-primary text-primary bg-primary/5'
                : 'border-transparent text-text-muted hover:text-text'"
            >
              <Code class="w-4 h-4 inline mr-2" />
              Raw Data
            </button>
          </div>

          <!-- Tab Content -->
          <div class="flex-1 overflow-y-auto p-6">
            <!-- Timeline Tab -->
            <div v-if="activeTab === 'timeline'">
              <div v-if="timelineData" class="space-y-4">
                <div class="mb-6 p-4 bg-surface rounded-lg border border-border">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-text font-medium">Process Execution Data</span>
                    <div class="flex items-center">
                      <CheckCircle class="w-5 h-5 text-primary mr-2" />
                      <span class="text-primary">Loaded from Backend</span>
                    </div>
                  </div>
                  <p class="text-text-muted text-sm">
                    Process: {{ timelineData.processName }}
                    • ID: {{ workflowId }}
                    • Status: {{ timelineData.status }}
                  </p>
                </div>

                <!-- Enhanced Interactive Timeline Steps -->
                <div v-if="timelineData.timeline && timelineData.timeline.length > 0" class="space-y-4">
                  <div
                    v-for="(step, index) in timelineData.timeline"
                    :key="step.nodeId || index"
                    class="border rounded-lg transition-all duration-200"
                    :class="getStepBorderClass(step.status)"
                  >
                    <!-- Step Header - Clickable -->
                    <div 
                      class="p-4 cursor-pointer hover:bg-surface/30 transition-colors"
                      @click="expandedStep = expandedStep === step.nodeId ? null : step.nodeId"
                    >
                      <div class="flex items-center justify-between">
                        <div class="flex items-center">
                          <component 
                            :is="getStepStatusIcon(step.status)" 
                            class="w-4 h-4 mr-3"
                            :class="getStepStatusColor(step.status)"
                          />
                          <div>
                            <div class="font-medium text-text">{{ step.nodeName || `Step ${index + 1}` }}</div>
                            <div class="text-sm text-text-muted">{{ step.summary || 'Process execution step' }}</div>
                          </div>
                        </div>
                        <div class="flex items-center gap-3">
                          <span class="text-xs text-text-muted">
                            {{ formatDuration(step.executionTime || 0) }}
                          </span>
                          <component
                            :is="expandedStep === step.nodeId ? ChevronDown : ChevronRight"
                            class="w-4 h-4 text-text-muted"
                          />
                        </div>
                      </div>
                    </div>

                    <!-- Expanded Details -->
                    <div v-if="expandedStep === step.nodeId" class="border-t border-border px-4 pb-4">
                      <div class="pt-4 space-y-4">
                        <!-- Step Details -->
                        <div v-if="step.details" class="mb-4">
                          <div class="text-sm font-medium text-text mb-2">Details:</div>
                          <div class="text-sm text-text-secondary">{{ step.details }}</div>
                        </div>
                        
                        <!-- Input/Output Data -->
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <!-- Input Data -->
                          <div>
                            <div class="text-sm font-medium text-text mb-2">Input Data:</div>
                            <div class="control-card p-3 text-sm text-text-secondary whitespace-pre-line">
                              {{ humanizeStepData(step.inputData, 'input', step.nodeType, step.nodeName) }}
                            </div>
                            <!-- Raw Input Toggle -->
                            <details class="mt-2">
                              <summary class="text-xs text-text-muted cursor-pointer hover:text-text">
                                Show technical data
                              </summary>
                              <pre class="control-card p-2 text-xs text-text-muted overflow-x-auto mt-2 font-mono">{{ JSON.stringify(step.inputData, null, 2) }}</pre>
                            </details>
                          </div>
                          
                          <!-- Output Data -->
                          <div>
                            <div class="text-sm font-medium text-text mb-2">Output Data:</div>
                            <div class="control-card p-3 text-sm text-text-secondary whitespace-pre-line">
                              {{ humanizeStepData(step.outputData, 'output', step.nodeType, step.nodeName) }}
                            </div>
                            <!-- Raw Output Toggle -->
                            <details class="mt-2">
                              <summary class="text-xs text-text-muted cursor-pointer hover:text-text">
                                Show technical data
                              </summary>
                              <pre class="control-card p-2 text-xs text-text-muted overflow-x-auto mt-2 font-mono">{{ JSON.stringify(step.outputData, null, 2) }}</pre>
                            </details>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- No Timeline Data -->
                <div v-else class="text-center py-12">
                  <Clock class="w-16 h-16 text-warning mx-auto mb-4" />
                  <h3 class="text-text text-lg font-medium mb-2">No Timeline Data</h3>
                  <p class="text-text-muted mb-4">
                    Backend timeline endpoint not implemented for this process
                  </p>
                  <button @click="forceRefresh" class="btn-control-primary">
                    <RefreshCw class="w-4 h-4 mr-2" />
                    Try Backend API
                  </button>
                </div>
              </div>
            </div>

            <!-- Flow Visualization Tab -->
            <div v-if="activeTab === 'flow'" class="space-y-4">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-text">Process Flow</h3>
                <div class="flex gap-2">
                  <button @click="autoLayoutTimelineFlow" class="btn-control text-xs">
                    <GitBranch class="w-3 h-3" />
                    Layout
                  </button>
                  <button @click="fitTimelineView" class="btn-control text-xs">
                    <Eye class="w-3 h-3" />
                    Fit
                  </button>
                </div>
              </div>
              
              <!-- VueFlow in Timeline Modal -->
              <div class="premium-glass rounded-lg overflow-hidden" style="height: 55vh;">
                <VueFlow
                  v-model="timelineFlowElements"
                  :default-viewport="{ zoom: 0.9 }"
                  :fit-view-on-init="true"
                  ref="timelineVueFlow"
                >
                  <Background
                    pattern-color="#10b981"
                    :size="1"
                    variant="dots"
                    class="!bg-background"
                  />
                  
                  <Controls class="!bg-surface !border-border" />
                  
                  <template #node-custom="{ data }">
                    <div 
                      class="premium-glass px-3 py-2 min-w-28 premium-transition premium-hover-lift rounded-md"
                      :class="getNodeStatusClass(data.status)"
                    >
                      <div class="flex items-center gap-1.5">
                        <component :is="getNodeIcon(data.type)" class="w-3 h-3 text-primary flex-shrink-0" />
                        <span class="font-medium text-text text-xs truncate">{{ data.label }}</span>
                        <div 
                          class="w-1.5 h-1.5 rounded-full flex-shrink-0 ml-auto"
                          :class="data.status === 'success' ? 'bg-primary' : 'bg-text-muted'"
                        />
                      </div>
                    </div>
                  </template>
                </VueFlow>
              </div>
            </div>

            <!-- Business Context Tab -->
            <div v-if="activeTab === 'context'" class="space-y-6">
              <div class="p-4 bg-surface rounded-lg border border-border">
                <h3 class="text-lg font-medium text-text mb-4">Business Process Context</h3>
                
                <div v-if="selectedWorkflowData" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div class="flex items-center">
                    <Database class="w-4 h-4 text-primary mr-2" />
                    <span class="text-text-muted">Process Name:</span>
                    <span class="text-text ml-2">{{ selectedWorkflowData.process_name }}</span>
                  </div>
                  
                  <div class="flex items-center">
                    <CheckCircle class="w-4 h-4 text-primary mr-2" />
                    <span class="text-text-muted">Status:</span>
                    <span :class="selectedWorkflowData.is_active ? 'text-primary' : 'text-text-muted'" class="ml-2">
                      {{ selectedWorkflowData.is_active ? 'Active' : 'Inactive' }}
                    </span>
                  </div>
                  
                  <div class="flex items-center">
                    <Clock class="w-4 h-4 text-warning mr-2" />
                    <span class="text-text-muted">Executions Today:</span>
                    <span class="text-warning ml-2">{{ selectedWorkflowData.executions_today }}</span>
                  </div>
                </div>
                
                <div v-else class="text-center py-8">
                  <Database class="w-12 h-12 text-text-muted mx-auto mb-4" />
                  <p class="text-text-muted">No business context loaded</p>
                </div>
              </div>
            </div>

            <!-- Raw Data Tab -->
            <div v-if="activeTab === 'raw'" class="space-y-4">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-medium text-text flex items-center gap-2">
                  <Code class="w-5 h-5 text-text-muted" />
                  Backend Process Data
                </h3>
                <button
                  @click="downloadTimelineData"
                  class="btn-control-primary text-sm"
                >
                  <Download class="w-4 h-4" />
                  Download
                </button>
              </div>
              
              <div v-if="timelineData || selectedWorkflowData">
                <pre 
                  class="bg-surface-hover p-4 rounded-lg border border-border text-xs text-text-secondary overflow-auto max-h-96 font-mono whitespace-pre"
                >{{ JSON.stringify(timelineData || selectedWorkflowData, null, 2) }}</pre>
              </div>
              
              <div v-else class="control-card p-4">
                <p class="text-warning font-medium">No Data Available</p>
                <p class="text-text-secondary text-sm mt-2">Backend API returned no data for this process</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { 
  X, Database, RefreshCw, XCircle, Clock, CheckCircle,
  Code, Download, GitBranch, Play, Settings, Eye, TrendingUp,
  ChevronDown, ChevronRight, AlertTriangle, Info
} from 'lucide-vue-next'
import { useUIStore } from '../../stores/ui'

// VueFlow styles
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

// Props
interface Props {
  workflowId: string
  tenantId: string
  show: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  close: []
}>()

// Stores
const uiStore = useUIStore()

// Local state
const isLoading = ref(false)
const isRefreshing = ref(false)
const error = ref<string | null>(null)
const activeTab = ref<'timeline' | 'flow' | 'context' | 'raw'>('timeline')
const expandedStep = ref<string | null>(null)

// Data
const timelineData = ref<any>(null)
const selectedWorkflowData = ref<any>(null)
const timelineFlowElements = ref([])

// VueFlow for timeline
const { fitView: timelineFitView } = useVueFlow()
const timelineFlowNodes = computed(() => timelineFlowElements.value.filter(el => !el.source))
const timelineFlowEdges = computed(() => timelineFlowElements.value.filter(el => el.source))

// Methods
const loadTimeline = async () => {
  isLoading.value = true
  error.value = null
  timelineData.value = null
  
  try {
    console.log('🔄 Loading ENHANCED timeline for:', props.workflowId)
    
    // Get workflow metadata first
    const workflowResponse = await fetch(`http://localhost:3001/api/business/processes`)
    if (workflowResponse.ok) {
      const workflowsData = await workflowResponse.json()
      selectedWorkflowData.value = workflowsData.data.find(w => w.process_id === props.workflowId)
    }
    
    // Get timeline execution data from NEW enhanced endpoint
    const timelineResponse = await fetch(`http://localhost:3001/api/business/process-timeline/${props.workflowId}`)
    
    if (timelineResponse.ok) {
      const timelineResult = await timelineResponse.json()
      console.log('✅ ENHANCED timeline loaded:', timelineResult)
      
      if (timelineResult.success) {
        timelineData.value = timelineResult.data
        
        // Create flow visualization from timeline steps
        createTimelineFlowFromSteps(timelineResult.data.timeline || [])
        
        console.log('✅ Enhanced timeline loaded:', timelineData.value.timeline?.length || 0, 'steps')
      } else {
        throw new Error(timelineResult.message || 'Failed to load timeline')
      }
    } else {
      throw new Error(`Timeline API returned ${timelineResponse.status}`)
    }
    
  } catch (err: any) {
    error.value = `Backend API Error: ${err.message}`
    console.error('❌ Failed to load timeline:', err)
  } finally {
    isLoading.value = false
  }
}

const createTimelineFlow = (processDetails: any) => {
  const processSteps = processDetails.processSteps || []
  const processFlow = processDetails.processFlow || []
  
  // Create nodes
  const nodes = processSteps.map((step: any) => ({
    id: step.stepName,
    type: 'custom',
    position: { 
      x: step.position[0] || 0, 
      y: step.position[1] || 0
    },
    data: {
      label: step.stepName,
      status: selectedWorkflowData.value?.is_active ? 'success' : 'inactive',
      type: getBusinessTypeFromCategory(step.businessCategory),
      businessCategory: step.businessCategory
    }
  }))
  
  // Create edges
  const edges = processFlow.map((flow: any, index: number) => ({
    id: `timeline-edge-${index}`,
    source: flow.from,
    target: flow.to,
    type: 'smoothstep',
    animated: selectedWorkflowData.value?.is_active,
    style: { 
      stroke: '#10b981', 
      strokeWidth: 2
    }
  }))
  
  timelineFlowElements.value = [...nodes, ...edges]
}

const createTimelineFlowFromSteps = (timelineSteps: any[]) => {
  if (!timelineSteps || timelineSteps.length === 0) {
    timelineFlowElements.value = []
    return
  }
  
  // Create nodes from timeline steps
  const nodes = timelineSteps.map((step: any, index: number) => ({
    id: step.nodeId,
    type: 'custom',
    position: { 
      x: (index % 3) * 200, 
      y: Math.floor(index / 3) * 120
    },
    data: {
      label: step.nodeName,
      status: step.status,
      type: getBusinessTypeFromNodeType(step.nodeType),
      executionTime: step.executionTime,
      summary: step.summary
    }
  }))
  
  // Create edges connecting steps in sequence
  const edges = timelineSteps.slice(0, -1).map((step: any, index: number) => ({
    id: `timeline-edge-${index}`,
    source: step.nodeId,
    target: timelineSteps[index + 1].nodeId,
    type: 'smoothstep',
    animated: timelineData.value?.status === 'active',
    style: { 
      stroke: step.status === 'success' ? '#10b981' : '#ef4444', 
      strokeWidth: 2
    }
  }))
  
  timelineFlowElements.value = [...nodes, ...edges]
}

const forceRefresh = async () => {
  isRefreshing.value = true
  await loadTimeline()
  isRefreshing.value = false
}

const autoLayoutTimelineFlow = () => {
  // Auto layout for timeline flow
  const nodes = timelineFlowNodes.value
  nodes.forEach((node, index) => {
    const elementIndex = timelineFlowElements.value.findIndex(el => el.id === node.id)
    if (elementIndex !== -1) {
      timelineFlowElements.value[elementIndex].position = {
        x: (index % 3) * 200,
        y: Math.floor(index / 3) * 100
      }
    }
  })
  
  setTimeout(() => timelineFitView({ duration: 600 }), 100)
}

const fitTimelineView = () => {
  timelineFitView({ duration: 600 })
}

const downloadTimelineData = () => {
  const dataToDownload = timelineData.value || selectedWorkflowData.value
  if (!dataToDownload) {
    uiStore.showToast('Error', 'No data to download', 'error')
    return
  }
  
  const jsonData = JSON.stringify(dataToDownload, null, 2)
  const blob = new Blob([jsonData], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `process-data-${props.workflowId}-${new Date().toISOString().slice(0, 10)}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

// Helper functions
const getBusinessTypeFromCategory = (businessCategory: string) => {
  switch (businessCategory) {
    case 'Event Handler': return 'trigger'
    case 'AI Intelligence': return 'ai'
    case 'Integration': return 'api'
    case 'Communication': return 'email'
    case 'Data Management': return 'storage'
    case 'Business Logic': return 'logic'
    case 'Document Processing': return 'file'
    default: return 'process'
  }
}

const getBusinessTypeFromNodeType = (nodeType: string) => {
  const type = nodeType?.toLowerCase() || ''
  
  if (type.includes('trigger') || type.includes('webhook')) return 'trigger'
  if (type.includes('ai') || type.includes('agent') || type.includes('openai') || type.includes('langchain')) return 'ai'
  if (type.includes('http') || type.includes('api')) return 'api'
  if (type.includes('mail') || type.includes('email')) return 'email'
  if (type.includes('vector') || type.includes('database') || type.includes('storage')) return 'storage'
  if (type.includes('code') || type.includes('javascript') || type.includes('function')) return 'logic'
  if (type.includes('file') || type.includes('document')) return 'file'
  
  return 'process'
}

const getNodeIcon = (type: string) => {
  switch (type) {
    case 'trigger': return Play
    case 'ai': return Database
    case 'api': return GitBranch
    case 'email': return Database
    case 'storage': return Database
    case 'logic': return Settings
    case 'file': return Database
    case 'validation': return CheckCircle
    default: return Clock
  }
}

const getNodeStatusClass = (status: string) => {
  switch (status) {
    case 'success': return 'border-primary/50 bg-primary/5'
    case 'running': return 'border-warning/50 bg-warning/5'
    case 'error': return 'border-error/50 bg-error/5'
    default: return 'border-border'
  }
}

const formatDuration = (ms?: number) => {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}min`
}

// Helper functions for enhanced timeline
const getStepStatusIcon = (status: string) => {
  switch (status) {
    case 'success': return CheckCircle
    case 'error': return XCircle
    case 'running': return Settings
    case 'not-executed': return AlertTriangle
    default: return Clock
  }
}

const getStepStatusColor = (status: string) => {
  switch (status) {
    case 'success': return 'text-primary'
    case 'error': return 'text-error'
    case 'running': return 'text-warning animate-spin'
    case 'not-executed': return 'text-text-muted'
    default: return 'text-text-muted'
  }
}

const getStepBorderClass = (status: string) => {
  switch (status) {
    case 'success': return 'border-primary/30 bg-primary/5'
    case 'error': return 'border-error/30 bg-error/5'
    case 'running': return 'border-warning/30 bg-warning/5'
    case 'not-executed': return 'border-text-muted/30 bg-surface/20'
    default: return 'border-border bg-surface/10'
  }
}

// Port della logica humanizeStepData dal frontend_old
const humanizeStepData = (data: any, dataType: 'input' | 'output', nodeType?: string, nodeName?: string) => {
  if (!data) return 'Nessun dato disponibile'
  
  // Se è un array, prendi il primo elemento
  const processData = Array.isArray(data) ? data[0] : data
  
  if (!processData || typeof processData !== 'object') {
    return String(processData) || 'Dato non strutturato'
  }

  const insights: string[] = []
  const nodeNameLower = nodeName?.toLowerCase() || ''
  
  // Trigger nodes special handling
  if (nodeType?.includes('trigger') && dataType === 'input') {
    return 'In attesa di nuovi dati dal sistema'
  }
  
  // Email nodes
  if (nodeNameLower.includes('mail') || nodeNameLower.includes('ricezione')) {
    if (dataType === 'output') {
      insights.push('--- EMAIL RICEVUTA ---')
      
      if (processData.json?.oggetto || processData.json?.subject) {
        insights.push(`Oggetto: "${processData.json?.oggetto || processData.json?.subject}"`)
      }
      
      if (processData.json?.mittente || processData.json?.sender?.emailAddress?.address) {
        const sender = processData.json?.mittente || processData.json?.sender?.emailAddress?.address
        insights.push(`Da: ${sender}`)
      }
      
      if (processData.json?.messaggio_cliente || processData.json?.body?.content) {
        const content = processData.json?.messaggio_cliente || processData.json?.body?.content
        const preview = content?.substring(0, 100) || ''
        insights.push(`Messaggio: "${preview}${preview.length >= 100 ? '...' : ''}"`)
      }
    }
  }
  
  // AI nodes
  else if (nodeNameLower.includes('ai') || nodeNameLower.includes('milena') || nodeNameLower.includes('assistant')) {
    if (dataType === 'output') {
      insights.push('--- RISPOSTA AI GENERATA ---')
      
      if (processData.json?.output?.risposta_html || processData.json?.risposta_html) {
        const response = processData.json?.output?.risposta_html || processData.json?.risposta_html
        const cleanResponse = response?.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
        const preview = cleanResponse?.substring(0, 150) || ''
        insights.push(`Risposta: "${preview}${preview.length >= 150 ? '...' : ''}"`)
      }
      
      if (processData.json?.categoria) {
        insights.push(`Categoria: ${processData.json.categoria}`)
      }
    }
  }
  
  // Fallback for other node types
  if (insights.length === 0) {
    if (processData.json) {
      const keys = Object.keys(processData.json)
      if (keys.length > 0) {
        insights.push(`Campi disponibili: ${keys.slice(0, 4).join(', ')}${keys.length > 4 ? '...' : ''}`)
      }
    } else {
      insights.push('Dati complessi - espandi per dettagli tecnici')
    }
  }
  
  return insights.join('\n')
}

// Watchers
watch(() => props.show, (newShow) => {
  if (newShow) {
    console.log(`🎯 Enhanced modal opened for process ${props.workflowId}`)
    loadTimeline()
    activeTab.value = 'timeline'
  }
})

// Lifecycle
onMounted(() => {
  if (props.show) {
    loadTimeline()
  }
})
</script>

<style scoped>
/* Modal VueFlow styling */
:deep(.vue-flow__node-custom) {
  background: transparent !important;
  border: none !important;
}

:deep(.vue-flow__controls) {
  button {
    background: var(--color-surface) !important;
    border: 1px solid var(--color-border) !important;
    color: var(--color-text) !important;
    font-size: 11px !important;
  }
}
</style>