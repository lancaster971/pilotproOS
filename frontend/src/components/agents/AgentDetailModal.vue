<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="$emit('close')"
    >
      <div class="control-card w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-border">
          <div class="flex items-center">
            <Bot class="w-6 h-6 text-primary mr-3" />
            <div>
              <h2 class="text-xl font-semibold text-text">
                {{ timelineData?.workflowName || `Workflow ${workflowId}` }}
              </h2>
              <p class="text-text-muted text-sm">
                Workflow ID: {{ workflowId }}
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
              {{ isRefreshing ? 'Refreshing...' : 'Force Refresh' }}
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
            <Loader2 class="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
            <p class="text-text-muted">Loading real execution timeline from backend...</p>
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

        <!-- No Data State -->
        <div v-else-if="!timelineData" class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <Clock class="w-16 h-16 text-text-muted mx-auto mb-4" />
            <h3 class="text-text text-lg font-medium mb-2">No Timeline Data Available</h3>
            <p class="text-text-muted mb-4">
              Backend timeline API endpoint not yet implemented for workflow {{ workflowId }}
            </p>
            <p class="text-text-muted text-sm mb-6">
              Real execution data will appear here when the backend timeline API is ready.
            </p>
            <button @click="forceRefresh" class="btn-control-primary">
              <RefreshCw class="w-4 h-4 mr-2" />
              Try Load from Backend
            </button>
          </div>
        </div>

        <!-- Content with Real Data -->
        <div v-else class="flex-1 flex flex-col">
          <!-- Tabs -->
          <div class="flex border-b border-border">
            <button
              @click="activeTab = 'timeline'"
              class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
              :class="activeTab === 'timeline'
                ? 'border-primary text-primary'
                : 'border-transparent text-text-muted hover:text-text'"
            >
              Timeline
            </button>
            <button
              @click="activeTab = 'context'"
              class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
              :class="activeTab === 'context'
                ? 'border-primary text-primary'
                : 'border-transparent text-text-muted hover:text-text'"
            >
              Business Context
            </button>
            <button
              @click="activeTab = 'raw'"
              class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
              :class="activeTab === 'raw'
                ? 'border-primary text-primary'
                : 'border-transparent text-text-muted hover:text-text'"
            >
              Raw Data
            </button>
          </div>

          <!-- Tab Content -->
          <div class="flex-1 overflow-y-auto p-6">
            <!-- Timeline Tab -->
            <div v-if="activeTab === 'timeline'">
              <div class="mb-6 p-4 bg-surface rounded-lg border border-border">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-text font-medium">Real Workflow Data</span>
                  <div class="flex items-center">
                    <CheckCircle class="w-5 h-5 text-primary mr-2" />
                    <span class="text-primary">Loaded from Backend</span>
                  </div>
                </div>
                <p class="text-text-muted text-sm">
                  Workflow: {{ timelineData.workflowName }}
                  • ID: {{ workflowId }}
                  • Status: {{ timelineData.status }}
                </p>
              </div>

              <!-- Real Timeline Steps -->
              <div v-if="timelineData.timeline && timelineData.timeline.length > 0" class="space-y-4">
                <div
                  v-for="(step, index) in timelineData.timeline"
                  :key="step.nodeId || index"
                  class="border rounded-lg p-4 border-primary/30 bg-primary/5"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center">
                      <CheckCircle class="w-4 h-4 mr-3 text-primary" />
                      <div>
                        <div class="font-medium text-text">{{ step.nodeName || `Step ${index + 1}` }}</div>
                        <div class="text-sm text-text-muted">{{ step.summary || 'Real execution step' }}</div>
                      </div>
                    </div>
                    <div class="flex items-center">
                      <span class="text-xs text-text-muted mr-3">
                        {{ formatDuration(step.executionTime || 0) }}
                      </span>
                    </div>
                  </div>

                  <!-- Real Step Data -->
                  <div class="mt-4 pt-4 border-t border-border">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 class="text-sm font-medium text-text-secondary mb-2">Real Input Data</h4>
                        <div class="bg-surface-hover rounded p-3 text-xs">
                          <pre class="text-text-secondary whitespace-pre-wrap">{{ 
                            step.inputData ? JSON.stringify(step.inputData, null, 2) : 'No input data from backend' 
                          }}</pre>
                        </div>
                      </div>
                      <div>
                        <h4 class="text-sm font-medium text-text-secondary mb-2">Real Output Data</h4>
                        <div class="bg-surface-hover rounded p-3 text-xs">
                          <pre class="text-text-secondary whitespace-pre-wrap">{{ 
                            step.outputData ? JSON.stringify(step.outputData, null, 2) : 'No output data from backend' 
                          }}</pre>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- No Timeline Data -->
              <div v-else class="text-center py-12">
                <Clock class="w-16 h-16 text-warning mx-auto mb-4" />
                <h3 class="text-text text-lg font-medium mb-2">No Real Timeline Data</h3>
                <p class="text-text-muted mb-4">
                  Backend API `/api/tenant/{{ tenantId }}/agents/workflow/{{ workflowId }}/timeline` returned no execution data
                </p>
                <div class="control-card p-4 mb-4 text-left">
                  <h4 class="text-warning font-medium mb-2">Backend API Status:</h4>
                  <p class="text-text-secondary text-sm">Endpoint not implemented yet or no executions for this workflow</p>
                  <p class="text-text-muted text-xs mt-2">Real execution data will appear here when available from backend</p>
                </div>
                <button @click="forceRefresh" class="btn-control-primary">
                  <RefreshCw class="w-4 h-4 mr-2" />
                  Retry Backend API
                </button>
              </div>
            </div>

            <!-- Business Context Tab -->
            <div v-if="activeTab === 'context'" class="space-y-6">
              <div class="p-4 bg-surface rounded-lg border border-border">
                <h3 class="text-lg font-medium text-text mb-4">Real Business Context</h3>
                
                <div v-if="timelineData?.businessContext" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div v-if="timelineData.businessContext.senderEmail" class="flex items-center">
                    <Mail class="w-4 h-4 text-info mr-2" />
                    <span class="text-text-muted">Sender:</span>
                    <span class="text-info ml-2">{{ timelineData.businessContext.senderEmail }}</span>
                  </div>
                  
                  <div v-if="timelineData.businessContext.subject" class="flex items-center">
                    <FileText class="w-4 h-4 text-primary mr-2" />
                    <span class="text-text-muted">Subject:</span>
                    <span class="text-text ml-2">{{ timelineData.businessContext.subject }}</span>
                  </div>
                  
                  <div v-if="timelineData.businessContext.classification" class="flex items-center">
                    <Tag class="w-4 h-4 text-warning mr-2" />
                    <span class="text-text-muted">Classification:</span>
                    <span class="text-warning ml-2">{{ timelineData.businessContext.classification }}</span>
                  </div>
                </div>
                
                <div v-else class="text-center py-8">
                  <FileText class="w-12 h-12 text-text-muted mx-auto mb-4" />
                  <p class="text-text-muted">No business context available from backend</p>
                  <p class="text-text-muted text-sm">Real business context will appear when execution data is available</p>
                </div>
              </div>
            </div>

            <!-- Raw Data Tab -->
            <div v-if="activeTab === 'raw'" class="space-y-4">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-medium text-text flex items-center gap-2">
                  <Code class="w-5 h-5 text-text-muted" />
                  Real Backend Data
                </h3>
                <div class="flex gap-2">
                  <button
                    @click="downloadRawData"
                    class="btn-control-primary text-sm"
                  >
                    <Download class="w-4 h-4" />
                    Download Real Data
                  </button>
                </div>
              </div>
              
              <div v-if="timelineData">
                <pre 
                  class="bg-surface-hover p-4 rounded-lg border border-border text-xs text-text-secondary overflow-auto max-h-96 font-mono whitespace-pre"
                >{{ JSON.stringify(timelineData, null, 2) }}</pre>
              </div>
              
              <div v-else class="control-card p-4">
                <p class="text-warning font-medium">No Real Data Available</p>
                <p class="text-text-secondary text-sm mt-2">Backend API call to get timeline data failed or returned empty</p>
                <p class="text-text-muted text-xs mt-2">URL attempted: /api/tenant/{{ tenantId }}/agents/workflow/{{ workflowId }}/timeline</p>
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
import { 
  X, Bot, RefreshCw, Loader2, XCircle, Clock, CheckCircle,
  Mail, FileText, Tag, Code, Download
} from 'lucide-vue-next'
import { useUIStore } from '../../stores/ui'

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
const activeTab = ref<'timeline' | 'context' | 'raw'>('timeline')

// Timeline data - ONLY REAL DATA FROM BACKEND
const timelineData = ref<any>(null)

// Methods - ONLY REAL BACKEND CALLS
const loadTimeline = async () => {
  isLoading.value = true
  error.value = null
  timelineData.value = null
  
  try {
    console.log('🔄 Loading REAL timeline data for workflow:', props.workflowId)
    
    // Use REAL backend endpoint that exists and works
    const endpoint = `/api/business/process-details/${props.workflowId}`
    
    console.log(`🔍 Loading from REAL backend endpoint: ${endpoint}`)
    const response = await fetch(`http://localhost:3001${endpoint}`)
    
    if (!response.ok) {
      throw new Error(`Backend API returned ${response.status}: ${response.statusText}`)
    }
    
    const realData = await response.json()
    console.log('✅ REAL data from backend:', realData)
    
    // Transform REAL backend data to timeline format
    timelineData.value = {
      workflowName: realData.data.processName,
      status: realData.data.isActive ? 'active' : 'inactive',
      lastExecution: {
        id: realData.data.latestActivity?.lastRun || 'no_executions',
        executedAt: realData.data.timeline?.lastModified || new Date().toISOString(),
        duration: realData.data.performance?.averageDurationMs || 0,
        status: realData.data.latestActivity?.lastRunStatus || 'unknown'
      },
      businessContext: {
        processId: realData.data.processId,
        category: realData.data.category?.label,
        healthStatus: realData.data.performance?.healthStatus?.label,
        businessImpact: realData.data.businessImpact?.score
      },
      timeline: realData.data.processSteps?.map((step, index) => ({
        nodeId: step.stepId,
        nodeName: step.stepName,
        nodeType: step.stepType?.type,
        status: 'success', // Default since no execution data yet
        executionTime: 0,
        customOrder: index + 1,
        summary: step.description,
        inputData: step.configuration,
        outputData: null
      })) || []
    }
    
    console.log('✅ Real timeline data transformed:', timelineData.value.timeline.length, 'steps')
    
  } catch (err: any) {
    error.value = `Backend API Error: ${err.message}`
    console.error('❌ Failed to load real timeline:', err)
  } finally {
    isLoading.value = false
  }
}

const forceRefresh = async () => {
  isRefreshing.value = true
  
  try {
    console.log('🔥 FORCE REFRESH: Attempting real backend API calls')
    
    // Try force refresh endpoint first
    try {
      const refreshResponse = await fetch(`http://localhost:3001/api/tenant/${props.tenantId}/agents/workflow/${props.workflowId}/refresh`, {
        method: 'POST'
      })
      
      if (refreshResponse.ok) {
        console.log('✅ Force refresh API succeeded')
        await loadTimeline()
        uiStore.showToast('Success', 'Real data refreshed from backend', 'success')
        return
      }
    } catch (refreshError) {
      console.warn('⚠️ Force refresh API not available:', refreshError)
    }
    
    // Fallback to regular load
    await loadTimeline()
    
  } catch (error: any) {
    uiStore.showToast('Errore', `Backend API Error: ${error.message}`, 'error')
  } finally {
    isRefreshing.value = false
  }
}

const downloadRawData = () => {
  if (!timelineData.value) {
    uiStore.showToast('Errore', 'No real data to download', 'error')
    return
  }
  
  const jsonData = JSON.stringify(timelineData.value, null, 2)
  const blob = new Blob([jsonData], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `real-workflow-data-${props.workflowId}-${new Date().toISOString().slice(0, 10)}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const formatDuration = (ms?: number) => {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}min`
}

// Watchers
watch(() => props.show, (newShow) => {
  if (newShow) {
    console.log(`🎯 Modal opened for workflow ${props.workflowId} - loading REAL data only`)
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
/* All styles now handled by Design System! */
</style>