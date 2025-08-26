<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="$emit('close')"
    >
      <div class="w-full max-w-6xl max-h-[90vh] bg-gray-900 border border-green-500/30 rounded-xl shadow-2xl overflow-hidden">
        
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-gray-800">
          <div class="flex items-center gap-4">
            <div class="p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              <GitBranch class="h-6 w-6 text-green-400" />
            </div>
            <div>
              <h2 class="text-2xl font-bold text-white">{{ workflow.name }}</h2>
              <div class="flex items-center gap-3 mt-1">
                <span class="text-sm text-gray-400">ID: {{ workflow.id }}</span>
                <span :class="[
                  'px-2 py-1 rounded text-xs font-medium',
                  workflow.active 
                    ? 'bg-green-500/10 border border-green-500/30 text-green-400'
                    : 'bg-yellow-500/10 border border-yellow-500/30 text-yellow-400'
                ]">
                  {{ workflow.active ? 'Active' : 'Inactive' }}
                </span>
                <span v-if="workflow.has_webhook" class="px-2 py-1 bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded text-xs font-medium">
                  Webhook
                </span>
              </div>
            </div>
          </div>
          
          <div class="flex items-center gap-2">
            <button
              @click="copyToClipboard(workflow.id)"
              class="p-2 text-gray-400 hover:text-green-400 transition-colors"
              title="Copy ID"
            >
              <Copy class="h-4 w-4" />
            </button>
            <button
              @click="handleExport"
              class="p-2 text-gray-400 hover:text-green-400 transition-colors"
              title="Export JSON"
            >
              <Download class="h-4 w-4" />
            </button>
            <button
              @click="handleForceRefresh"
              :disabled="isLoading"
              class="p-2 text-gray-400 hover:text-green-400 disabled:text-gray-600 transition-colors"
              :title="isLoading ? 'Refreshing...' : 'Force Refresh from n8n'"
            >
              <RefreshCw :class="['h-4 w-4', { 'animate-spin': isLoading }]" />
            </button>
            <button
              @click="$emit('close')"
              class="p-2 text-gray-400 hover:text-red-400 transition-colors"
            >
              <X class="h-5 w-5" />
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="flex items-center justify-center p-12">
          <div class="text-center">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-green-400"></div>
            <p class="mt-4 text-gray-400">Caricamento dettagli workflow...</p>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-xl font-bold text-red-400">Errore nel caricamento</h2>
          </div>
          <p class="text-gray-400">Impossibile caricare i dettagli del workflow. Riprova più tardi.</p>
          <p class="text-sm text-gray-500 mt-2">{{ error.message || 'Errore sconosciuto' }}</p>
          <div class="mt-4 flex gap-2">
            <button @click="refreshData" class="btn-control-primary">Riprova</button>
            <button @click="$emit('close')" class="btn-control">Chiudi</button>
          </div>
        </div>

        <!-- Content -->
        <div v-else>
          <!-- Tabs -->
          <div class="flex items-center gap-1 p-2 border-b border-gray-800 bg-gray-900/50">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all',
                activeTab === tab.id
                  ? 'bg-green-500 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              ]"
            >
              <component :is="tab.icon" class="h-4 w-4" />
              {{ tab.label }}
            </button>
          </div>

          <!-- Tab Content -->
          <div class="overflow-y-auto" style="max-height: calc(90vh - 200px);">
            
            <!-- Overview Tab -->
            <div v-if="activeTab === 'overview'" class="p-6 space-y-6">
              
              <!-- Business Description (Sticky Notes) -->
              <div v-if="businessDescription" class="control-card p-6 border-blue-500/30">
                <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Info class="h-5 w-5 text-blue-400" />
                  Business Description
                </h3>
                <div class="space-y-3">
                  <div v-for="(note, index) in businessDescription" :key="index" 
                       class="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                    <FileText class="h-4 w-4 text-yellow-400 float-left mr-2 mt-1" />
                    <div class="text-gray-300 text-sm whitespace-pre-wrap">{{ note }}</div>
                  </div>
                </div>
              </div>

              <!-- Stats Cards -->
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="control-card p-4">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-sm text-gray-400">Total Nodes</span>
                    <Box class="h-4 w-4 text-gray-600" />
                  </div>
                  <p class="text-2xl font-bold text-white">{{ nodeAnalysis.totalNodes || workflow.node_count || 0 }}</p>
                </div>
                
                <div class="control-card p-4">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-sm text-gray-400">Total Executions</span>
                    <Play class="h-4 w-4 text-gray-600" />
                  </div>
                  <p class="text-2xl font-bold text-white">{{ executionStats.total || workflow.execution_count || 0 }}</p>
                </div>
                
                <div class="control-card p-4">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-sm text-gray-400">Success Rate</span>
                    <CheckCircle class="h-4 w-4 text-gray-600" />
                  </div>
                  <p class="text-2xl font-bold text-green-400">
                    {{ executionStats.total > 0 
                      ? `${((executionStats.successful / executionStats.total) * 100).toFixed(1)}%`
                      : 'N/A' }}
                  </p>
                </div>
                
                <div class="control-card p-4">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-sm text-gray-400">Avg Duration</span>
                    <Clock class="h-4 w-4 text-gray-600" />
                  </div>
                  <p class="text-2xl font-bold text-white">
                    {{ formatDuration(executionStats.averageDuration) }}
                  </p>
                </div>
              </div>

              <!-- Info Sections -->
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="control-card p-6">
                  <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Info class="h-5 w-5 text-green-400" />
                    Workflow Information
                  </h3>
                  <div class="space-y-3">
                    <div class="flex justify-between">
                      <span class="text-gray-400">Created</span>
                      <span class="text-white">{{ formatDate(workflow.created_at) }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-gray-400">Updated</span>
                      <span class="text-white">{{ formatDate(workflow.updated_at) }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-gray-400">Last Execution</span>
                      <span class="text-white">
                        {{ workflow.last_execution ? formatDate(workflow.last_execution) : 'Never' }}
                      </span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-gray-400">Webhook</span>
                      <span :class="workflow.has_webhook ? 'text-green-400' : 'text-gray-500'">
                        {{ workflow.has_webhook ? 'Enabled' : 'Disabled' }}
                      </span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-gray-400">Archived</span>
                      <span :class="workflow.is_archived ? 'text-yellow-400' : 'text-gray-500'">
                        {{ workflow.is_archived ? 'Yes' : 'No' }}
                      </span>
                    </div>
                  </div>
                </div>

                <div class="control-card p-6">
                  <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Activity class="h-5 w-5 text-blue-400" />
                    Quick Stats
                  </h3>
                  <div class="space-y-3">
                    <div class="flex justify-between">
                      <span class="text-gray-400">Successful Runs</span>
                      <span class="text-green-400 font-bold">{{ executionStats.successful }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-gray-400">Failed Runs</span>
                      <span class="text-red-400 font-bold">{{ executionStats.failed }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-gray-400">AI Agents</span>
                      <span class="text-purple-400 font-bold">{{ nodeAnalysis.aiAgents?.length || 0 }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-gray-400">Tools</span>
                      <span class="text-orange-400 font-bold">{{ nodeAnalysis.tools?.length || 0 }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-gray-400">Error Rate</span>
                      <span class="text-yellow-400">{{ performance.errorRate || 0 }}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Executions Tab -->
            <div v-if="activeTab === 'executions'" class="p-6 space-y-6">
              <div class="control-card p-6">
                <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Clock class="h-5 w-5 text-blue-400" />
                  Recent Executions
                </h3>
                <div class="space-y-3">
                  <div v-if="executionStats.recentExecutions?.length === 0" 
                       class="text-gray-500 text-center py-4">
                    No recent executions
                  </div>
                  <div v-else v-for="(exec, index) in (executionStats.recentExecutions || [])" 
                       :key="exec.id || index" 
                       class="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                    <div class="flex items-center gap-3">
                      <CheckCircle v-if="exec.status === 'success'" class="h-4 w-4 text-green-400" />
                      <XCircle v-else-if="exec.status === 'error'" class="h-4 w-4 text-red-400" />
                      <AlertTriangle v-else class="h-4 w-4 text-yellow-400" />
                      <div>
                        <p class="text-white text-sm">Execution #{{ exec.id }}</p>
                        <p class="text-xs text-gray-400">{{ formatDate(exec.started_at) }}</p>
                      </div>
                    </div>
                    <div class="text-right">
                      <p class="text-white text-sm">{{ formatDuration(exec.duration_ms || 0) }}</p>
                      <p :class="[
                        'text-xs',
                        exec.status === 'success' ? 'text-green-400' : 
                        exec.status === 'error' ? 'text-red-400' : 'text-yellow-400'
                      ]">
                        {{ exec.status }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Nodes Tab -->
            <div v-if="activeTab === 'nodes'" class="p-6 space-y-6">
              
              <!-- AI Agents Section -->
              <div v-if="nodeAnalysis.aiAgents?.length > 0" class="control-card p-6 border-purple-500/30">
                <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Brain class="h-5 w-5 text-purple-400" />
                  AI Agents ({{ nodeAnalysis.aiAgents.length }})
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div v-for="(agent, index) in nodeAnalysis.aiAgents" 
                       :key="index" 
                       class="p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                    <div class="flex items-start justify-between mb-2">
                      <h4 class="text-white font-medium">{{ agent.name }}</h4>
                      <Brain class="h-5 w-5 text-purple-400" />
                    </div>
                    <div class="space-y-1 text-sm">
                      <p class="text-gray-400">Type: <span class="text-purple-300">{{ agent.type }}</span></p>
                      <p v-if="agent.model !== 'unknown'" class="text-gray-400">
                        Model: <span class="text-purple-300">{{ agent.model }}</span>
                      </p>
                      <div v-if="agent.connectedTools?.length > 0" class="mt-2">
                        <p class="text-gray-400 mb-1">Connected Tools:</p>
                        <div class="flex flex-wrap gap-1">
                          <span v-for="(tool, idx) in agent.connectedTools" 
                                :key="idx"
                                class="px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs">
                            {{ tool }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Tools & Workflow Flow -->
              <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Triggers -->
                <div class="control-card p-6">
                  <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Zap class="h-5 w-5 text-yellow-400" />
                    Triggers
                  </h3>
                  <div v-if="nodeAnalysis.triggers?.length > 0" class="space-y-3">
                    <div v-for="(trigger, index) in nodeAnalysis.triggers" 
                         :key="index" 
                         class="flex items-center gap-3 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                      <Webhook class="h-5 w-5 text-yellow-400" />
                      <div class="flex-1">
                        <p class="text-white font-medium">{{ trigger.name }}</p>
                        <p class="text-xs text-gray-400">{{ trigger.type }}</p>
                      </div>
                    </div>
                  </div>
                  <p v-else class="text-gray-500 text-center py-4">No triggers</p>
                </div>

                <!-- Processing -->
                <div class="control-card p-6">
                  <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Layers class="h-5 w-5 text-blue-400" />
                    Processing
                  </h3>
                  <div class="space-y-3">
                    <template v-for="([category, count]) in Object.entries(nodeAnalysis.nodesByType || {})" 
                              :key="category">
                      <div v-if="category !== 'Triggers' && category !== 'Output/Response'"
                           class="flex items-center justify-between p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                        <div class="flex items-center gap-2">
                          <Package class="h-4 w-4 text-blue-400" />
                          <span class="text-white text-sm">{{ category }}</span>
                        </div>
                        <span class="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs font-bold">
                          {{ count }}
                        </span>
                      </div>
                    </template>
                  </div>
                </div>

                <!-- Outputs -->
                <div class="control-card p-6">
                  <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <ExternalLink class="h-5 w-5 text-green-400" />
                    Outputs
                  </h3>
                  <div v-if="nodeAnalysis.outputs?.length > 0" class="space-y-3">
                    <div v-for="(output, index) in nodeAnalysis.outputs" 
                         :key="index" 
                         class="flex items-center gap-3 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
                      <Send class="h-5 w-5 text-green-400" />
                      <div class="flex-1">
                        <p class="text-white font-medium">{{ output.name }}</p>
                        <p class="text-xs text-gray-400">{{ output.type }}</p>
                      </div>
                    </div>
                  </div>
                  <p v-else class="text-gray-500 text-center py-4">No outputs</p>
                </div>
              </div>
            </div>

            <!-- Performance Tab -->
            <div v-if="activeTab === 'performance'" class="p-6 space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="control-card p-6">
                  <div class="flex items-center justify-between mb-4">
                    <span class="text-sm text-gray-400">Min Execution Time</span>
                    <TrendingUp class="h-4 w-4 text-green-400" />
                  </div>
                  <p class="text-3xl font-bold text-white">
                    {{ formatDuration(performance.minExecutionTime || 0) }}
                  </p>
                </div>
                
                <div class="control-card p-6">
                  <div class="flex items-center justify-between mb-4">
                    <span class="text-sm text-gray-400">Average Time</span>
                    <Activity class="h-4 w-4 text-blue-400" />
                  </div>
                  <p class="text-3xl font-bold text-white">
                    {{ formatDuration(performance.avgExecutionTime || 0) }}
                  </p>
                </div>
                
                <div class="control-card p-6">
                  <div class="flex items-center justify-between mb-4">
                    <span class="text-sm text-gray-400">Max Execution Time</span>
                    <AlertTriangle class="h-4 w-4 text-red-400" />
                  </div>
                  <p class="text-3xl font-bold text-white">
                    {{ formatDuration(performance.maxExecutionTime || 0) }}
                  </p>
                </div>
              </div>

              <!-- Common Errors -->
              <div v-if="performance.commonErrors?.length > 0" class="control-card p-6">
                <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <XCircle class="h-5 w-5 text-red-400" />
                  Common Errors
                </h3>
                <div class="space-y-3">
                  <div v-for="(error, index) in performance.commonErrors" 
                       :key="index" 
                       class="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                    <div class="flex items-start justify-between">
                      <div class="flex-1">
                        <p class="text-red-400 font-medium">{{ error.message }}</p>
                        <p class="text-xs text-gray-400 mt-1">Occurred {{ error.count }} times</p>
                      </div>
                      <span class="text-xs text-gray-500">{{ error.lastOccurred }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Activity Tab -->
            <div v-if="activeTab === 'activity'" class="p-6">
              <div class="control-card p-6">
                <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Clock class="h-5 w-5 text-blue-400" />
                  Recent Activity Timeline
                </h3>
                <div class="space-y-4">
                  <div v-for="(exec, index) in (executionStats.recentExecutions || []).slice(0, 20)" 
                       :key="exec.id || index" 
                       class="flex items-start gap-4">
                    <div class="flex-shrink-0 mt-1">
                      <div v-if="exec.status === 'success'" 
                           class="w-8 h-8 bg-green-500/10 border border-green-500/30 rounded-full flex items-center justify-center">
                        <CheckCircle class="h-4 w-4 text-green-400" />
                      </div>
                      <div v-else-if="exec.status === 'error'" 
                           class="w-8 h-8 bg-red-500/10 border border-red-500/30 rounded-full flex items-center justify-center">
                        <XCircle class="h-4 w-4 text-red-400" />
                      </div>
                      <div v-else 
                           class="w-8 h-8 bg-yellow-500/10 border border-yellow-500/30 rounded-full flex items-center justify-center">
                        <Clock class="h-4 w-4 text-yellow-400" />
                      </div>
                    </div>
                    <div class="flex-1 pb-4 border-l-2 border-gray-800 pl-4 -ml-4">
                      <div class="flex items-center justify-between mb-1">
                        <p class="text-white font-medium">
                          Execution {{ exec.status === 'success' ? 'completed' : 
                                     exec.status === 'error' ? 'failed' : 'started' }}
                        </p>
                        <span class="text-xs text-gray-500">{{ formatDate(exec.started_at) }}</span>
                      </div>
                      <p class="text-sm text-gray-400">
                        Duration: {{ formatDuration(exec.duration_ms || 0) }}
                      </p>
                      <p v-if="exec.error_message" class="text-sm text-red-400 mt-1">
                        {{ exec.error_message }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { 
  X, GitBranch, CheckCircle, XCircle, Play, Copy, Download,
  RefreshCw, Info, FileText, Activity, Clock, Box, TrendingUp, AlertTriangle,
  Brain, Zap, Layers, ExternalLink, Package, Send, Webhook
} from 'lucide-vue-next'
import { useUIStore } from '../../stores/ui'
import type { Workflow } from '../../types'

// Props
interface Props {
  workflow: Workflow
  show: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  close: []
}>()

// State
const uiStore = useUIStore()
const isLoading = ref(false)
const error = ref<Error | null>(null)
const activeTab = ref('overview')

// Workflow detail data
const businessDescription = ref<string[]>([])
const nodeAnalysis = ref<any>({
  totalNodes: 0,
  nodesByType: {},
  triggers: [],
  outputs: [],
  aiAgents: [],
  tools: [],
  subWorkflows: [],
  connections: []
})
const executionStats = ref<any>({
  total: 0,
  successful: 0,
  failed: 0,
  averageDuration: 0,
  recentExecutions: []
})
const performance = ref<any>({
  minExecutionTime: 0,
  avgExecutionTime: 0,
  maxExecutionTime: 0,
  errorRate: 0,
  commonErrors: []
})

// Tab configuration
const tabs = [
  { id: 'overview', label: 'Overview', icon: Info },
  { id: 'executions', label: 'Executions', icon: Activity },
  { id: 'nodes', label: 'Nodes', icon: Layers },
  { id: 'performance', label: 'Performance', icon: TrendingUp },
  { id: 'activity', label: 'Activity', icon: Clock },
]

// Load workflow details
const loadWorkflowDetails = async () => {
  isLoading.value = true
  error.value = null
  
  try {
    console.log('🔄 Loading workflow details for:', props.workflow.id)
    
    // Get detailed workflow data from backend
    const response = await fetch(`http://localhost:3001/api/business/process-details/${props.workflow.id}`)
    
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('✅ Workflow details loaded:', data.data)
    
    // Extract business description from sticky notes
    if (data.data.businessDescription) {
      businessDescription.value = Array.isArray(data.data.businessDescription) 
        ? data.data.businessDescription 
        : [data.data.businessDescription]
    }
    
    // Set node analysis
    nodeAnalysis.value = {
      totalNodes: data.data.nodeCount || 0,
      nodesByType: data.data.nodesByType || {},
      triggers: data.data.triggers || [],
      outputs: data.data.outputs || [],
      aiAgents: data.data.aiAgents || [],
      tools: data.data.tools || [],
      subWorkflows: data.data.subWorkflows || [],
      connections: data.data.connections || []
    }
    
    // Set execution stats
    executionStats.value = {
      total: data.data.totalExecutions || props.workflow.execution_count || 0,
      successful: data.data.successfulExecutions || 0,
      failed: data.data.failedExecutions || 0,
      averageDuration: data.data.avgDuration || 0,
      recentExecutions: data.data.recentExecutions || []
    }
    
    // Set performance data
    performance.value = {
      minExecutionTime: data.data.minExecutionTime || 0,
      avgExecutionTime: data.data.avgExecutionTime || 0,
      maxExecutionTime: data.data.maxExecutionTime || 0,
      errorRate: data.data.errorRate || 0,
      commonErrors: data.data.commonErrors || []
    }
    
    // Also load business description from sticky notes directly
    await loadBusinessDescription()
    
  } catch (err: any) {
    console.error('❌ Failed to load workflow details:', err)
    error.value = err
  } finally {
    isLoading.value = false
  }
}

// Load business description from sticky notes
const loadBusinessDescription = async () => {
  try {
    // Get sticky notes content from n8n workflow
    const response = await fetch(`http://localhost:3001/api/business/sticky-notes/${props.workflow.id}`)
    
    if (response.ok) {
      const data = await response.json()
      if (data.data?.stickyNotes?.length > 0) {
        businessDescription.value = data.data.stickyNotes.map((note: any) => note.content).filter(Boolean)
        console.log('✅ Business description loaded from sticky notes:', businessDescription.value.length)
      }
    }
  } catch (err) {
    console.warn('⚠️ Could not load sticky notes:', err)
  }
}

// Utility functions
const formatDuration = (ms: number) => {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}min`
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit', 
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text)
  uiStore.showToast('Success', 'ID copiato negli appunti', 'success')
}

const handleExport = () => {
  const dataStr = JSON.stringify(props.workflow, null, 2)
  const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr)
  const exportFileDefaultName = `workflow-${props.workflow.name}-${Date.now()}.json`
  
  const linkElement = document.createElement('a')
  linkElement.setAttribute('href', dataUri)
  linkElement.setAttribute('download', exportFileDefaultName)
  linkElement.click()
  
  uiStore.showToast('Success', 'Workflow esportato', 'success')
}

const handleForceRefresh = async () => {
  console.log('🔄 Force refresh requested for workflow', props.workflow.id)
  await loadWorkflowDetails()
  uiStore.showToast('Success', 'Dati aggiornati dal backend', 'success')
}

const refreshData = () => {
  loadWorkflowDetails()
}

// Watchers
watch(() => props.show, (newShow) => {
  if (newShow) {
    console.log('📊 Modal opened for workflow:', props.workflow.name)
    loadWorkflowDetails()
    activeTab.value = 'overview'
  }
})

// Lifecycle
onMounted(() => {
  if (props.show) {
    loadWorkflowDetails()
  }
})
</script>

<style scoped>
.control-card {
  @apply bg-gray-800/50 border border-gray-700/50 rounded-lg backdrop-blur-sm;
}

.btn-control {
  @apply flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-600 text-white rounded-lg hover:bg-gray-700 hover:border-gray-500 transition-all text-sm;
}

.btn-control-primary {
  @apply flex items-center gap-2 px-4 py-2 bg-green-600 border border-green-500 text-white rounded-lg hover:bg-green-500 hover:border-green-400 transition-all text-sm;
}

/* Tab content max height */
.overflow-y-auto {
  scrollbar-width: thin;
  scrollbar-color: #4ade80 #1f2937;
}

.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #1f2937;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #4ade80;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #22c55e;
}
</style>