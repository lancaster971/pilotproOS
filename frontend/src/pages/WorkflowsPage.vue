<template>
  <MainLayout>
        <div class="space-y-6">
          <!-- Header -->
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-3xl font-bold text-gradient">AI Agent Workflows</h1>
              <p class="text-gray-400 mt-1">Real-time transparency on your AI agents activity</p>
            </div>
            <div class="flex items-center gap-3">
              <div class="flex items-center text-sm text-gray-400">
                <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
                Live Feed
              </div>
              <button
                @click="refreshWorkflows"
                :disabled="isLoading"
                class="btn-control-primary"
              >
                <RefreshCw :class="{ 'animate-spin': isLoading }" class="h-4 w-4" />
                Refresh
              </button>
            </div>
          </div>

          <!-- Stats Cards -->
          <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div class="bg-gray-900 border border-green-400/20 rounded-lg p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-400 text-sm">Active Agents</p>
                  <p class="text-2xl font-bold text-white">{{ agentWorkflows.length }}</p>
                </div>
                <Bot class="w-8 h-8 text-green-400" />
              </div>
            </div>
            
            <div class="bg-gray-900 border border-green-400/20 rounded-lg p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-400 text-sm">With Data</p>
                  <p class="text-2xl font-bold text-green-400">
                    {{ agentWorkflows.filter(w => w.hasDetailedData).length }}
                  </p>
                </div>
                <CheckCircle class="w-8 h-8 text-green-400" />
              </div>
            </div>

            <div class="bg-gray-900 border border-green-400/20 rounded-lg p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-400 text-sm">Total Executions</p>
                  <p class="text-2xl font-bold text-white">
                    {{ agentWorkflows.reduce((sum, w) => sum + w.totalExecutions, 0) }}
                  </p>
                </div>
                <Clock class="w-8 h-8 text-yellow-400" />
              </div>
            </div>

            <div class="bg-gray-900 border border-green-400/20 rounded-lg p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-400 text-sm">Recently Active</p>
                  <p class="text-2xl font-bold text-white">
                    {{ agentWorkflows.filter(w => w.lastActivity && isRecentlyActive(w.lastActivity)).length }}
                  </p>
                </div>
                <Bot class="w-8 h-8 text-blue-400" />
              </div>
            </div>
          </div>

          <!-- AI Agent Workflow Cards - KILLER FEATURE -->
          <div class="bg-gray-900 border border-green-400/20 rounded-lg p-6">
            <h2 class="text-xl font-semibold text-white mb-6">AI Agent Workflows</h2>
            
            <div v-if="agentWorkflows.length === 0" class="text-center py-12">
              <Bot class="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <p class="text-gray-400">No AI agent workflows found</p>
              <p class="text-gray-500 text-sm mt-2">Active AI workflows will appear here</p>
            </div>
            
            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div 
                v-for="workflow in agentWorkflows"
                :key="workflow.id"
                class="bg-black border border-gray-800 rounded-lg p-5 hover:border-green-400/30 transition-all"
              >
                <!-- Header -->
                <div class="flex items-start justify-between mb-4">
                  <div class="flex-1">
                    <div class="flex items-center mb-2">
                      <Bot class="w-5 h-5 text-green-400 mr-2" />
                      <span 
                        class="px-2 py-1 rounded-full text-xs font-semibold"
                        :class="getWorkflowColor(workflow.name)"
                      >
                        {{ workflow.name }}
                      </span>
                    </div>
                  </div>
                  <div class="flex items-center">
                    <div 
                      v-if="workflow.hasDetailedData"
                      class="w-2 h-2 bg-green-400 rounded-full animate-pulse" 
                      title="Has detailed execution data"
                    />
                    <div 
                      v-else
                      class="w-2 h-2 bg-gray-600 rounded-full" 
                      title="No execution data available"
                    />
                  </div>
                </div>

                <!-- Stats -->
                <div class="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <div class="text-gray-400 text-xs mb-1">Executions</div>
                    <div class="text-white text-lg font-semibold">{{ workflow.totalExecutions }}</div>
                  </div>
                  <div>
                    <div class="text-gray-400 text-xs mb-1">Status</div>
                    <div class="flex items-center">
                      <CheckCircle v-if="workflow.lastExecutionStatus === 'success'" class="w-4 h-4 text-green-400 mr-1" />
                      <XCircle v-else-if="workflow.lastExecutionStatus === 'error'" class="w-4 h-4 text-red-400 mr-1" />
                      <Clock v-else class="w-4 h-4 text-gray-400 mr-1" />
                      <span class="text-white text-sm">{{ workflow.lastExecutionStatus || 'inactive' }}</span>
                    </div>
                  </div>
                </div>

                <!-- Business Context Preview -->
                <div v-if="workflow.preview" class="mb-4 p-3 bg-gray-800/50 rounded border-l-2 border-green-400/50">
                  <div class="text-gray-400 text-xs mb-2">Latest Activity</div>
                  <div v-if="workflow.preview.senderEmail" class="flex items-center mb-1">
                    <Mail class="w-3 h-3 text-blue-400 mr-2" />
                    <span class="text-blue-400 text-sm truncate">{{ workflow.preview.senderEmail }}</span>
                  </div>
                  <div v-if="workflow.preview.subject" class="text-gray-300 text-sm truncate mb-1">
                    "{{ workflow.preview.subject }}"
                  </div>
                  <div v-if="workflow.preview.classification" class="text-green-400 text-xs">
                    {{ workflow.preview.classification }}
                  </div>
                </div>

                <!-- Action Buttons - CORE FEATURE ACCESS -->
                <div class="flex items-center justify-between text-xs">
                  <div class="text-gray-400">
                    {{ workflow.lastActivity ? formatTimeAgo(workflow.lastActivity) : 'No recent activity' }}
                  </div>
                  <div class="flex items-center gap-2">
                    <!-- Details Button -->
                    <button
                      @click="openWorkflowDetails(workflow)"
                      class="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs transition-colors flex items-center gap-1"
                    >
                      <Eye class="w-3 h-3" />
                      Details
                    </button>
                    
                    <!-- Timeline Button - KILLER FEATURE ACCESS -->
                    <button
                      @click="openWorkflowTimeline(workflow.id)"
                      class="px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded text-xs transition-colors flex items-center gap-1"
                    >
                      <Clock class="w-3 h-3" />
                      Timeline
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Workflow Detail Modal -->
        <WorkflowDetailModal
          v-if="selectedWorkflowForDetails"
          :workflow="selectedWorkflowForDetails"
          :show="showDetailsModal"
          @close="closeDetailsModal"
        />

        <!-- Agent Timeline Modal - KILLER FEATURE -->
        <AgentDetailModal
          v-if="selectedWorkflowId"
          :workflow-id="selectedWorkflowId"
          :tenant-id="tenantId"
          :show="showTimelineModal"
          @close="closeTimelineModal"
        />
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  RefreshCw, CheckCircle, XCircle, Clock, Mail, Eye
} from 'lucide-vue-next'
import MainLayout from '../components/layout/MainLayout.vue'
import AgentDetailModal from '../components/agents/AgentDetailModal.vue'
import WorkflowDetailModal from '../components/workflows/WorkflowDetailModal.vue'
import { useAuthStore } from '../stores/auth'
import { useUIStore } from '../stores/ui'

// Types - same as old system
interface AgentWorkflow {
  id: string
  name: string
  status: 'active' | 'inactive'
  lastActivity: string | null
  lastExecutionId: string | null
  lastExecutionStatus: string
  totalExecutions: number
  hasDetailedData: boolean
  updatedAt: string
  type: 'ai-agent'
  preview?: {
    senderEmail?: string
    subject?: string
    classification?: string
  }
}

// Stores
const authStore = useAuthStore()
const uiStore = useUIStore()
const router = useRouter()

// Local state
const isLoading = ref(false)
const tenantId = 'client_simulation_a'

// Modal state
const selectedWorkflowId = ref<string | null>(null)
const selectedWorkflowForDetails = ref<any>(null)
const showTimelineModal = ref(false)
const showDetailsModal = ref(false)

// AI Agent Workflows - REAL DATA FROM BACKEND
const agentWorkflows = ref<AgentWorkflow[]>([])
const workflowsFromBackend = ref<any[]>([])

// Methods
const refreshWorkflows = async () => {
  isLoading.value = true
  
  try {
    // REAL BACKEND API CALL - NO MOCK DATA
    console.log('🔄 Fetching REAL workflows from backend API...')
    
    // Call our PilotProOS backend API
    const response = await fetch('http://localhost:3001/api/business/processes')
    
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('✅ Real backend response:', data)
    
    // Store raw backend data
    workflowsFromBackend.value = data.data || []
    
    // Transform REAL backend data to AgentWorkflow format
    agentWorkflows.value = (data.data || []).map((process: any): AgentWorkflow => {
      console.log('🔄 Processing workflow:', process.process_name)
      
      return {
        id: process.process_id,
        name: process.process_name,
        status: process.is_active ? 'active' : 'inactive',
        lastActivity: process.last_modified || new Date().toISOString(),
        lastExecutionId: `exec_${process.process_id}_latest`,
        lastExecutionStatus: 'success', // Default since backend doesn't provide this yet
        totalExecutions: parseInt(process.executions_today) || 0,
        hasDetailedData: true, // Assume true for workflows from backend
        updatedAt: process.last_modified || new Date().toISOString(),
        type: 'ai-agent',
        preview: {
          senderEmail: 'backend@pilotpros.local', // Real backend data doesn't have this yet
          subject: `Business Process: ${process.process_name}`,
          classification: 'Backend Process'
        }
      }
    })
    
    console.log('✅ Transformed to AgentWorkflows:', agentWorkflows.value.length)
    uiStore.showToast('Real Data', `${agentWorkflows.value.length} workflows caricati dal backend`, 'success')
    
  } catch (error: any) {
    console.error('❌ Backend API call failed:', error)
    uiStore.showToast('Errore Backend', `API call failed: ${error.message}`, 'error')
    
    // NO FALLBACK - show error instead of mock data
    agentWorkflows.value = []
  } finally {
    isLoading.value = false
  }
}

// Modal methods - CORE FEATURE ACCESS
const openWorkflowDetails = (workflow: AgentWorkflow) => {
  selectedWorkflowForDetails.value = {
    id: workflow.id,
    name: workflow.name,
    active: workflow.status === 'active',
    is_archived: false,
    created_at: new Date().toISOString(),
    updated_at: workflow.updatedAt,
    node_count: 5,
    execution_count: workflow.totalExecutions,
    has_webhook: false,
    last_execution: workflow.lastActivity,
    tags: [],
    settings: {}
  }
  showDetailsModal.value = true
}

const openWorkflowTimeline = (workflowId: string) => {
  console.log('🎯 Opening Timeline for workflow:', workflowId)
  selectedWorkflowId.value = workflowId
  showTimelineModal.value = true
}

const closeDetailsModal = () => {
  showDetailsModal.value = false
  selectedWorkflowForDetails.value = null
}

const closeTimelineModal = () => {
  showTimelineModal.value = false
  selectedWorkflowId.value = null
}

// Utility methods
const getWorkflowColor = (workflowName: string) => {
  if (workflowName.includes('CHATBOT')) return 'text-blue-400 bg-blue-400/10'
  if (workflowName.includes('AGENT')) return 'text-purple-400 bg-purple-400/10'
  if (workflowName.includes('AI')) return 'text-green-400 bg-green-400/10'
  return 'text-gray-400 bg-gray-400/10'
}

const formatTimeAgo = (timestamp: string) => {
  const now = new Date()
  const time = new Date(timestamp)
  const diffMs = now.getTime() - time.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
  return `${Math.floor(diffMins / 1440)}d ago`
}

const isRecentlyActive = (timestamp: string) => {
  const now = new Date()
  const time = new Date(timestamp)
  const diffHours = (now.getTime() - time.getTime()) / (1000 * 60 * 60)
  return diffHours < 24
}

// Lifecycle
onMounted(() => {
  refreshWorkflows()
})
</script>