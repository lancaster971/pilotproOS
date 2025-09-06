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
            <GitBranch class="w-6 h-6 text-primary mr-3" />
            <div>
              <h2 class="text-lg font-semibold text-text">
                {{ workflow.name }}
              </h2>
              <p class="text-text-muted text-sm">
                Process ID: {{ workflow.id }} • 
                <span :class="workflow.active ? 'text-primary' : 'text-text-muted'">
                  {{ workflow.active ? 'ACTIVE' : 'INACTIVE' }}
                </span>
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <button
              @click="refreshWorkflowData"
              :disabled="isRefreshing"
              class="btn-control"
            >
              <RefreshCw :class="{ 'animate-spin': isRefreshing }" class="w-4 h-4" />
              Refresh
            </button>
            <button
              @click="$emit('close')"
              class="p-2 text-text-muted hover:text-text hover:bg-surface-hover rounded transition-colors"
            >
              <X class="w-5 h-5" />
            </button>
          </div>
        </div>

        <!-- Content with Tabs -->
        <div class="flex-1 flex flex-col">
          <!-- Tab Navigation -->
          <div class="flex border-b border-border bg-surface/30">
            <button
              @click="activeTab = 'overview'"
              class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
              :class="activeTab === 'overview'
                ? 'border-primary text-primary bg-primary/5'
                : 'border-transparent text-text-muted hover:text-text hover:bg-surface/50'"
            >
              <BarChart3 class="w-4 h-4 inline mr-2" />
              Overview
            </button>
            <button
              @click="activeTab = 'flow'"
              class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
              :class="activeTab === 'flow'
                ? 'border-primary text-primary bg-primary/5'
                : 'border-transparent text-text-muted hover:text-text hover:bg-surface/50'"
            >
              <GitBranch class="w-4 h-4 inline mr-2" />
              Flow Visualization
            </button>
            <button
              @click="activeTab = 'executions'"
              class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
              :class="activeTab === 'executions'
                ? 'border-primary text-primary bg-primary/5'
                : 'border-transparent text-text-muted hover:text-text hover:bg-surface/50'"
            >
              <Play class="w-4 h-4 inline mr-2" />
              Recent Executions
            </button>
            <button
              @click="activeTab = 'settings'"
              class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
              :class="activeTab === 'settings'
                ? 'border-primary text-primary bg-primary/5'
                : 'border-transparent text-text-muted hover:text-text hover:bg-surface/50'"
            >
              <Settings class="w-4 h-4 inline mr-2" />
              Settings
            </button>
          </div>

          <!-- Tab Content -->
          <div class="flex-1 overflow-y-auto p-6">
            <!-- Overview Tab -->
            <div v-if="activeTab === 'overview'" class="space-y-6">
              <!-- Workflow Summary -->
              <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- Basic Info -->
                <div class="control-card p-4">
                  <h3 class="text-base font-semibold text-text mb-3 flex items-center gap-2">
                    <Database class="w-4 h-4 text-primary" />
                    Process Information
                  </h3>
                  <div class="space-y-2 text-sm">
                    <div class="flex justify-between">
                      <span class="text-text-muted">Created:</span>
                      <span class="text-text">{{ formatDate(workflow.created_at) }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-text-muted">Updated:</span>
                      <span class="text-text">{{ formatDate(workflow.updated_at) }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-text-muted">Status:</span>
                      <span :class="workflow.active ? 'text-primary' : 'text-text-muted'">
                        {{ workflow.active ? 'Active' : 'Inactive' }}
                      </span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-text-muted">Archived:</span>
                      <span class="text-text">{{ workflow.is_archived ? 'Yes' : 'No' }}</span>
                    </div>
                  </div>
                </div>

                <!-- Statistics -->
                <div class="control-card p-4">
                  <h3 class="text-base font-semibold text-text mb-3 flex items-center gap-2">
                    <BarChart3 class="w-4 h-4 text-primary" />
                    Statistics
                  </h3>
                  <div class="space-y-2 text-sm">
                    <div class="flex justify-between">
                      <span class="text-text-muted">Total Nodes:</span>
                      <span class="text-sm font-semibold text-text">{{ workflowDetails?.nodeCount || workflow.node_count || 0 }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-text-muted">Connections:</span>
                      <span class="text-sm font-semibold text-text">{{ workflowDetails?.connectionCount || 0 }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-text-muted">Executions:</span>
                      <span class="text-sm font-semibold text-text">{{ workflow.execution_count || 0 }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-text-muted">Complexity:</span>
                      <span class="text-sm font-semibold text-primary">{{ workflowDetails?.businessMetadata?.complexity || 'Unknown' }}</span>
                    </div>
                  </div>
                </div>

                <!-- Business Impact -->
                <div class="control-card p-4">
                  <h3 class="text-base font-semibold text-text mb-3 flex items-center gap-2">
                    <TrendingUp class="w-4 h-4 text-primary" />
                    Business Impact
                  </h3>
                  <div class="space-y-2 text-sm">
                    <div class="flex justify-between">
                      <span class="text-text-muted">Category:</span>
                      <span class="text-sm font-semibold text-primary">{{ workflowDetails?.businessMetadata?.category || 'General' }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-text-muted">Impact:</span>
                      <span class="text-sm font-semibold text-warning">{{ workflowDetails?.businessMetadata?.businessImpact || 'Medium' }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-text-muted">Last Modified:</span>
                      <span class="text-text">{{ formatRelativeTime(workflowDetails?.businessMetadata?.lastModified || workflow.updated_at) }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Actions -->
              <div class="flex items-center gap-4">
                <button
                  @click="toggleWorkflowStatus"
                  :disabled="workflow.is_archived"
                  class="btn-control-primary"
                  :class="{ 'opacity-50 cursor-not-allowed': workflow.is_archived }"
                >
                  <Play v-if="!workflow.active" class="h-4 w-4" />
                  <Pause v-else class="h-4 w-4" />
                  {{ workflow.active ? 'Deactivate' : 'Activate' }}
                </button>
                
                <button class="btn-control">
                  <Edit class="h-4 w-4" />
                  Edit in n8n
                </button>
                
                <button class="btn-control">
                  <Copy class="h-4 w-4" />
                  Duplicate
                </button>
                
                <button 
                  v-if="!workflow.is_archived"
                  class="btn-control text-error border-error/30 hover:border-error hover:bg-error/10"
                >
                  <Archive class="h-4 w-4" />
                  Archive
                </button>
              </div>
            </div>

            <!-- Flow Visualization Tab -->
            <div v-if="activeTab === 'flow'" class="space-y-4">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-text">Process Flow Visualization</h3>
                <div class="flex gap-2">
                  <button @click="autoLayoutModalFlow" class="btn-control text-xs">
                    <GitBranch class="w-3 h-3" />
                    Auto Layout
                  </button>
                  <button @click="fitModalView" class="btn-control text-xs">
                    <Eye class="w-3 h-3" />
                    Fit View
                  </button>
                </div>
              </div>
              
              <!-- Mini VueFlow in Modal -->
              <div class="premium-glass rounded-lg overflow-hidden" style="height: 60vh;">
                <VueFlow
                  v-model="modalFlowElements"
                  :default-viewport="{ zoom: 0.8 }"
                  :min-zoom="0.2"
                  :max-zoom="3"
                  :fit-view-on-init="true"
                  ref="modalVueFlow"
                >
                  <Background
                    pattern-color="#10b981"
                    :size="1"
                    variant="dots"
                    class="!bg-background"
                  />
                  
                  <Controls class="!bg-surface !border-border" />
                  
                  <!-- Same node template as main VueFlow -->
                  <template #node-custom="{ data }">
                    <div 
                      class="n8n-node n8n-node-modal"
                      :class="[
                        'n8n-node-' + data.type,
                        data.status === 'success' ? 'n8n-node-active' : 'n8n-node-inactive'
                      ]"
                    >
                      <div class="n8n-node-icon">
                        <component :is="getNodeIcon(data.type)" class="w-3.5 h-3.5" />
                      </div>
                      <div class="n8n-node-content">
                        <div class="n8n-node-name">{{ data.label }}</div>
                      </div>
                      <div 
                        class="n8n-node-status"
                        :class="data.status === 'success' ? 'n8n-status-success' : 'n8n-status-inactive'"
                      ></div>
                    </div>
                  </template>
                </VueFlow>
              </div>
              
              <!-- Flow Statistics -->
              <div class="grid grid-cols-4 gap-4">
                <div class="control-card p-3 text-center">
                  <div class="text-base font-bold text-primary">{{ modalFlowNodes.length }}</div>
                  <div class="text-xs text-text-muted">Process Steps</div>
                </div>
                <div class="control-card p-3 text-center">
                  <div class="text-base font-bold text-text">{{ modalFlowEdges.length }}</div>
                  <div class="text-xs text-text-muted">Connections</div>
                </div>
                <div class="control-card p-3 text-center">
                  <div class="text-base font-bold text-warning">{{ workflowDetails?.businessMetadata?.complexity || 'Unknown' }}</div>
                  <div class="text-xs text-text-muted">Complexity</div>
                </div>
                <div class="control-card p-3 text-center">
                  <div class="text-base font-bold text-primary">{{ workflowDetails?.businessMetadata?.businessImpact || 'Medium' }}</div>
                  <div class="text-xs text-text-muted">Business Impact</div>
                </div>
              </div>
            </div>

            <!-- Executions Tab -->
            <div v-if="activeTab === 'executions'" class="space-y-4">
              <h3 class="text-lg font-semibold text-text">Recent Executions</h3>
              
              <!-- Real execution data would go here -->
              <div class="control-card p-4">
                <div class="text-center py-8">
                  <Clock class="w-12 h-12 text-text-muted mx-auto mb-4" />
                  <h4 class="text-text font-medium mb-2">Execution History</h4>
                  <p class="text-text-muted text-sm">Real execution data from backend would be displayed here</p>
                  <p class="text-text-muted text-xs mt-2">Endpoint: /api/business/process-executions/{{ workflow.id }}</p>
                </div>
              </div>
            </div>

            <!-- Settings Tab -->
            <div v-if="activeTab === 'settings'" class="space-y-4">
              <h3 class="text-lg font-semibold text-text">Process Configuration</h3>
              
              <div class="control-card p-4">
                <div class="text-center py-8">
                  <Settings class="w-12 h-12 text-text-muted mx-auto mb-4" />
                  <h4 class="text-base font-medium text-text mb-2">Configuration Panel</h4>
                  <p class="text-text-muted text-sm">Process settings and configuration options</p>
                  <div class="mt-4">
                    <button class="btn-control-primary">
                      <Settings class="w-4 h-4" />
                      Open in n8n Editor
                    </button>
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
import { ref, computed, watch, onMounted } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { 
  X, GitBranch, CheckCircle, XCircle, Play, Pause, Edit, 
  Copy, Archive, RefreshCw, BarChart3, Settings, TrendingUp,
  Database, Clock, Eye
} from 'lucide-vue-next'
import { useWorkflowsStore } from '../../stores/workflows'
import { useUIStore } from '../../stores/ui'
import { businessAPI } from '../../services/api-client'
import type { Workflow } from '../../types'

// VueFlow styles
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

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

// Stores
const workflowsStore = useWorkflowsStore()
const uiStore = useUIStore()

// Local state
const activeTab = ref<'overview' | 'flow' | 'executions' | 'settings'>('overview')
const isRefreshing = ref(false)
const workflowDetails = ref<any>(null)

// VueFlow for modal
const modalFlowElements = ref([])
const modalVueFlow = ref()
const { fitView: modalFitView } = useVueFlow()

const modalFlowNodes = computed(() => modalFlowElements.value.filter(el => !el.source))
const modalFlowEdges = computed(() => modalFlowElements.value.filter(el => el.source))

// Methods
const refreshWorkflowData = async () => {
  isRefreshing.value = true
  
  try {
    // Fetch detailed workflow data from backend using OFETCH
    const data = await businessAPI.getProcessDetails(props.workflow.id)
    
    if (data) {
      workflowDetails.value = data.data
      
      // Create flow for modal visualization
      createModalFlow(data.data)
      
      uiStore.showToast('Success', 'Workflow data refreshed', 'success')
    } else {
      throw new Error('Failed to fetch workflow details')
    }
  } catch (error: any) {
    uiStore.showToast('Error', 'Failed to refresh workflow data', 'error')
  } finally {
    isRefreshing.value = false
  }
}

const createModalFlow = (details: any) => {
  const processSteps = details.processSteps || []
  const processFlow = details.processFlow || []
  
  // Create nodes for modal flow
  const nodes = processSteps.map((step: any) => ({
    id: step.stepName,
    type: 'custom',
    position: { 
      x: step.position[0] || 0, 
      y: step.position[1] || 0
    },
    data: {
      label: step.stepName,
      status: props.workflow.active ? 'success' : 'inactive',
      type: getBusinessTypeFromCategory(step.businessCategory),
      businessCategory: step.businessCategory
    }
  }))
  
  // Create edges
  const edges = processFlow.map((flow: any, index: number) => ({
    id: `modal-edge-${index}`,
    source: flow.from,
    target: flow.to,
    type: 'smoothstep',
    animated: props.workflow.active,
    style: { 
      stroke: '#10b981', 
      strokeWidth: 2
    }
  }))
  
  modalFlowElements.value = [...nodes, ...edges]
}

const autoLayoutModalFlow = () => {
  // Simple auto layout for modal
  const nodes = modalFlowNodes.value
  nodes.forEach((node, index) => {
    const elementIndex = modalFlowElements.value.findIndex(el => el.id === node.id)
    if (elementIndex !== -1) {
      modalFlowElements.value[elementIndex].position = {
        x: (index % 3) * 200,
        y: Math.floor(index / 3) * 120
      }
    }
  })
  
  setTimeout(() => {
    modalFitView({ duration: 600 })
  }, 100)
}

const fitModalView = () => {
  modalFitView({ duration: 600 })
}

const toggleWorkflowStatus = async () => {
  try {
    await workflowsStore.toggleWorkflow(props.workflow)
    uiStore.showToast(
      'Workflow',
      `${props.workflow.active ? 'Deactivated' : 'Activated'}: ${props.workflow.name}`,
      'success'
    )
  } catch (error: any) {
    uiStore.showToast('Error', 'Failed to toggle workflow status', 'error')
  }
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

const getNodeIcon = (type: string) => {
  switch (type) {
    case 'trigger': return Play
    case 'ai': return Database // Using Database as Bot alternative
    case 'api': return GitBranch
    case 'email': return Copy // Using Copy as Mail alternative
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

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('it-IT', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatRelativeTime = (dateString: string) => {
  const now = new Date()
  const time = new Date(dateString)
  const diffHours = (now.getTime() - time.getTime()) / (1000 * 60 * 60)
  
  if (diffHours < 1) return 'Just now'
  if (diffHours < 24) return `${Math.floor(diffHours)}h ago`
  if (diffHours < 24 * 7) return `${Math.floor(diffHours / 24)}d ago`
  return formatDate(dateString)
}

// Watch for modal open/close
watch(() => props.show, (newShow) => {
  if (newShow) {
    activeTab.value = 'overview'
    refreshWorkflowData()
  }
})

onMounted(() => {
  if (props.show) {
    refreshWorkflowData()
  }
})
</script>

<style scoped>
/* Modal-specific VueFlow styling */
:deep(.vue-flow__node-custom) {
  background: transparent !important;
  border: none !important;
}

:deep(.vue-flow__controls) {
  button {
    background: var(--color-surface) !important;
    border: 1px solid var(--color-border) !important;
    color: var(--color-text) !important;
    font-size: 12px !important;
  }
}

/* Square nodes in modal context */
:deep(.n8n-node-modal) {
  width: 70px;
  height: 70px;
  transform: scale(1); /* Normal size in modal */
}

:deep(.n8n-node-modal .n8n-node-icon) {
  width: 28px;
  height: 28px;
  margin-bottom: 4px;
}

:deep(.n8n-node-modal .n8n-node-name) {
  font-size: 9px;
  max-width: 65px;
  line-height: 1.1;
}
</style>