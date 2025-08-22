<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="$emit('close')"
    >
      <div class="bg-gray-900 border border-green-400/20 rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-gray-800">
          <div class="flex items-center">
            <Bot class="w-6 h-6 text-green-400 mr-3" />
            <div>
              <h2 class="text-xl font-semibold text-white">
                {{ timelineData?.workflowName || `Workflow ${workflowId}` }}
              </h2>
              <p class="text-gray-400 text-sm">
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
              class="flex items-center px-4 py-2 rounded-lg font-medium transition-all"
              :class="isRefreshing 
                ? 'bg-gray-700 text-gray-400 cursor-not-allowed' 
                : 'bg-green-600 hover:bg-green-500 text-white shadow-lg hover:shadow-green-500/25'"
            >
              <RefreshCw :class="{ 'animate-spin': isRefreshing }" class="w-4 h-4 mr-2" />
              {{ isRefreshing ? 'Refreshing...' : 'Force Refresh' }}
            </button>
            
            <button
              @click="$emit('close')"
              class="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded"
            >
              <X class="w-5 h-5" />
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <Loader2 class="h-12 w-12 animate-spin text-green-400 mx-auto mb-4" />
            <p class="text-gray-400">Loading real execution timeline from backend...</p>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <XCircle class="h-12 w-12 text-red-400 mx-auto mb-4" />
            <p class="text-red-400">{{ error }}</p>
            <button @click="loadTimeline" class="mt-4 btn-control-primary">
              Try Again
            </button>
          </div>
        </div>

        <!-- No Data State -->
        <div v-else-if="!timelineData" class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <Clock class="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h3 class="text-white text-lg font-medium mb-2">No Timeline Data Available</h3>
            <p class="text-gray-400 mb-4">
              Backend timeline API endpoint not yet implemented for workflow {{ workflowId }}
            </p>
            <p class="text-gray-500 text-sm mb-6">
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
          <div class="flex border-b border-gray-800">
            <button
              @click="activeTab = 'timeline'"
              class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
              :class="activeTab === 'timeline'
                ? 'border-green-400 text-green-400'
                : 'border-transparent text-gray-400 hover:text-white'"
            >
              Timeline
            </button>
            <button
              @click="activeTab = 'context'"
              class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
              :class="activeTab === 'context'
                ? 'border-green-400 text-green-400'
                : 'border-transparent text-gray-400 hover:text-white'"
            >
              Business Context
            </button>
            <button
              @click="activeTab = 'raw'"
              class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
              :class="activeTab === 'raw'
                ? 'border-green-400 text-green-400'
                : 'border-transparent text-gray-400 hover:text-white'"
            >
              Raw Data
            </button>
          </div>

          <!-- Tab Content -->
          <div class="flex-1 overflow-y-auto p-6">
            <!-- Timeline Tab -->
            <div v-if="activeTab === 'timeline'">
              <div class="mb-6 p-4 bg-black rounded-lg border border-gray-800">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-white font-medium">Real Workflow Data</span>
                  <div class="flex items-center">
                    <CheckCircle class="w-5 h-5 text-green-400 mr-2" />
                    <span class="text-green-400">Loaded from Backend</span>
                  </div>
                </div>
                <p class="text-gray-400 text-sm">
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
                  class="border rounded-lg p-4 border-green-400/30 bg-green-400/5"
                >
                  <div class="flex items-center justify-between">
                    <div class="flex items-center">
                      <CheckCircle class="w-4 h-4 mr-3 text-green-400" />
                      <div>
                        <div class="font-medium text-white">{{ step.nodeName || `Step ${index + 1}` }}</div>
                        <div class="text-sm text-gray-400">{{ step.summary || 'Real execution step' }}</div>
                      </div>
                    </div>
                    <div class="flex items-center">
                      <span class="text-xs text-gray-400 mr-3">
                        {{ formatDuration(step.executionTime || 0) }}
                      </span>
                    </div>
                  </div>

                  <!-- Real Step Data -->
                  <div class="mt-4 pt-4 border-t border-gray-700">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 class="text-sm font-medium text-gray-300 mb-2">Real Input Data</h4>
                        <div class="bg-gray-800 rounded p-3 text-xs">
                          <pre class="text-gray-300 whitespace-pre-wrap">{{ 
                            step.inputData ? JSON.stringify(step.inputData, null, 2) : 'No input data from backend' 
                          }}</pre>
                        </div>
                      </div>
                      <div>
                        <h4 class="text-sm font-medium text-gray-300 mb-2">Real Output Data</h4>
                        <div class="bg-gray-800 rounded p-3 text-xs">
                          <pre class="text-gray-300 whitespace-pre-wrap">{{ 
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
                <Clock class="w-16 h-16 text-yellow-600 mx-auto mb-4" />
                <h3 class="text-white text-lg font-medium mb-2">No Real Timeline Data</h3>
                <p class="text-gray-400 mb-4">
                  Backend API `/api/tenant/{{ tenantId }}/agents/workflow/{{ workflowId }}/timeline` returned no execution data
                </p>
                <div class="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-4 text-left">
                  <h4 class="text-yellow-400 font-medium mb-2">Backend API Status:</h4>
                  <p class="text-gray-300 text-sm">Endpoint not implemented yet or no executions for this workflow</p>
                  <p class="text-gray-400 text-xs mt-2">Real execution data will appear here when available from backend</p>
                </div>
                <button @click="forceRefresh" class="btn-control-primary">
                  <RefreshCw class="w-4 h-4 mr-2" />
                  Retry Backend API
                </button>
              </div>
            </div>

            <!-- Business Context Tab -->
            <div v-if="activeTab === 'context'" class="space-y-6">
              <div class="p-4 bg-black rounded-lg border border-gray-800">
                <h3 class="text-lg font-medium text-white mb-4">Real Business Context</h3>
                
                <div v-if="timelineData?.businessContext" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div v-if="timelineData.businessContext.senderEmail" class="flex items-center">
                    <Mail class="w-4 h-4 text-blue-400 mr-2" />
                    <span class="text-gray-400">Sender:</span>
                    <span class="text-blue-400 ml-2">{{ timelineData.businessContext.senderEmail }}</span>
                  </div>
                  
                  <div v-if="timelineData.businessContext.subject" class="flex items-center">
                    <FileText class="w-4 h-4 text-green-400 mr-2" />
                    <span class="text-gray-400">Subject:</span>
                    <span class="text-white ml-2">{{ timelineData.businessContext.subject }}</span>
                  </div>
                  
                  <div v-if="timelineData.businessContext.classification" class="flex items-center">
                    <Tag class="w-4 h-4 text-yellow-400 mr-2" />
                    <span class="text-gray-400">Classification:</span>
                    <span class="text-yellow-400 ml-2">{{ timelineData.businessContext.classification }}</span>
                  </div>
                </div>
                
                <div v-else class="text-center py-8">
                  <FileText class="w-12 h-12 text-gray-600 mx-auto mb-4" />
                  <p class="text-gray-400">No business context available from backend</p>
                  <p class="text-gray-500 text-sm">Real business context will appear when execution data is available</p>
                </div>
              </div>
            </div>

            <!-- Raw Data Tab -->
            <div v-if="activeTab === 'raw'" class="space-y-4">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-medium text-white flex items-center gap-2">
                  <Code class="w-5 h-5 text-gray-400" />
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
                  class="bg-black p-4 rounded-lg border border-gray-800 text-xs text-gray-300 overflow-auto max-h-96 font-mono whitespace-pre"
                >{{ JSON.stringify(timelineData, null, 2) }}</pre>
              </div>
              
              <div v-else class="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                <p class="text-yellow-400 font-medium">No Real Data Available</p>
                <p class="text-gray-300 text-sm mt-2">Backend API call to get timeline data failed or returned empty</p>
                <p class="text-gray-400 text-xs mt-2">URL attempted: /api/tenant/{{ tenantId }}/agents/workflow/{{ workflowId }}/timeline</p>
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
    
    // Try multiple backend endpoints for real data
    const endpoints = [
      `/api/tenant/${props.tenantId}/agents/workflow/${props.workflowId}/timeline`,
      `/api/business/process-details/${props.workflowId}`,
      `/api/business/processes/${props.workflowId}/executions`
    ]
    
    for (const endpoint of endpoints) {
      try {
        console.log(`🔍 Trying backend endpoint: ${endpoint}`)
        const response = await fetch(`http://localhost:3001${endpoint}`)
        
        if (response.ok) {
          const realData = await response.json()
          console.log('✅ REAL data from backend:', realData)
          
          // Transform backend data to timeline format
          timelineData.value = {
            workflowName: realData.workflowName || realData.name || `Workflow ${props.workflowId}`,
            status: realData.active ? 'active' : 'inactive',
            lastExecution: realData.lastExecution || {
              id: `exec_${props.workflowId}_latest`,
              executedAt: new Date().toISOString(),
              duration: 0
            },
            businessContext: realData.businessContext || null,
            timeline: realData.timeline || realData.steps || []
          }
          
          console.log('✅ Timeline data loaded from backend')
          return
        } else {
          console.warn(`⚠️ Endpoint ${endpoint} returned ${response.status}`)
        }
      } catch (endpointError) {
        console.warn(`⚠️ Endpoint ${endpoint} failed:`, endpointError)
      }
    }
    
    // If all endpoints fail
    throw new Error(`No backend endpoint available for workflow ${props.workflowId} timeline data`)
    
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
/* Clean modal styles for real data display */
.btn-control {
  background-color: rgb(31 41 55);
  border: 1px solid rgb(55 65 81);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-control-primary {
  background-color: rgb(22 163 74);
  border: 1px solid rgb(34 197 94);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
</style>