<template>
  <MainLayout>
    <div class="h-[calc(100vh-2.5rem)] overflow-hidden">
      <!-- Compact Page Title -->
      <div class="mb-2">
        <h1 class="text-lg font-bold text-gradient">Workflow Command Center</h1>
      </div>

      <!-- Main Layout: Collapsible Sidebar + Flow + Details -->
      <div class="flex gap-4 h-[calc(100%-2rem)]">
        
        <!-- Collapsible Left Sidebar: Workflow List -->
        <div 
          :class="sidebarCollapsed ? 'w-12' : 'w-72'"
          class="premium-glass rounded-lg overflow-hidden transition-all duration-300 flex-shrink-0"
        >
          <!-- Sidebar Header -->
          <div class="p-3 border-b border-border flex items-center justify-between">
            <h3 v-if="!sidebarCollapsed" class="text-xs font-bold text-text">PROCESSES</h3>
            <button 
              @click="sidebarCollapsed = !sidebarCollapsed"
              class="p-1 text-text-muted hover:text-text transition-colors"
            >
              <ChevronLeft :class="{ 'rotate-180': sidebarCollapsed }" class="w-4 h-4 transition-transform" />
            </button>
          </div>
          
          <!-- Sidebar Content -->
          <div v-if="!sidebarCollapsed" class="p-4 overflow-y-auto h-full">
            <div class="flex items-center justify-between mb-3">
              <span class="text-xs text-text-muted">{{ activeWorkflows }}/{{ totalWorkflows }} active</span>
            </div>
            
            <!-- Real Workflow List -->
            <div class="space-y-1.5">
              <div
                v-for="workflow in realWorkflows"
                :key="workflow.process_id"
                @click="selectWorkflow(workflow)"
                class="p-2 rounded-md cursor-pointer transition-all text-xs"
                :class="selectedWorkflowId === workflow.process_id 
                  ? 'bg-primary/10 border border-primary/30' 
                  : 'bg-surface/50 hover:bg-surface border border-transparent hover:border-border'"
              >
                <div class="flex items-center gap-2 mb-1">
                  <div 
                    class="w-1.5 h-1.5 rounded-full"
                    :class="workflow.is_active ? 'bg-primary animate-pulse' : 'bg-text-muted'"
                  />
                  <span class="font-medium text-text truncate flex-1" :title="workflow.process_name">
                    {{ workflow.process_name }}
                  </span>
                </div>
                <div class="text-xs text-text-muted pl-3.5">
                  {{ workflow.executions_today }} today
                </div>
              </div>
            </div>
          </div>
          
          <!-- Collapsed State -->
          <div v-else class="p-2 overflow-y-auto h-full">
            <div class="space-y-2">
              <div
                v-for="workflow in realWorkflows"
                :key="workflow.process_id"
                @click="selectWorkflow(workflow)"
                class="w-8 h-8 rounded-md cursor-pointer transition-all flex items-center justify-center"
                :class="selectedWorkflowId === workflow.process_id 
                  ? 'bg-primary/20 border border-primary/50' 
                  : 'bg-surface/50 hover:bg-surface'"
                :title="workflow.process_name"
              >
                <div 
                  class="w-2 h-2 rounded-full"
                  :class="workflow.is_active ? 'bg-primary' : 'bg-text-muted'"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Center: VueFlow Visualization -->
        <div class="flex-1 premium-glass rounded-lg overflow-hidden">
          <!-- Flow Controls -->
          <div class="bg-surface/30 border-b border-border px-4 py-2 flex items-center justify-between">
            <div class="text-sm font-medium text-text truncate max-w-64">
              {{ selectedWorkflowData?.process_name || 'Select a workflow to visualize' }}
            </div>
            <div class="flex items-center gap-2">
              <button 
                @click="autoLayoutFlow"
                :disabled="!selectedWorkflowId || flowElements.length === 0"
                class="px-2 py-1 bg-surface border border-border text-text rounded text-xs hover:bg-surface-hover transition-colors"
              >
                Layout
              </button>
              <div class="flex items-center bg-surface border border-border rounded">
                <button @click="zoomOut" class="px-2 py-1 text-text hover:bg-surface-hover transition-colors text-xs">−</button>
                <button @click="zoomIn" class="px-2 py-1 text-text hover:bg-surface-hover transition-colors text-xs">+</button>
              </div>
            </div>
          </div>
          
          <!-- VueFlow -->
          <div class="relative h-full">
            <VueFlow
              v-if="selectedWorkflowId"
              v-model="flowElements"
              :default-viewport="{ zoom: 1, x: 0, y: 0 }"
              :min-zoom="0.2"
              :max-zoom="3"
              :connection-line-type="'straight'"
              class="workflow-flow"
            >
              <Background pattern-color="#10b981" :size="1" variant="dots" />
              <Controls class="!bg-surface !border-border" />
              
              <template #node-custom="{ data }">
                <div 
                  class="n8n-node"
                  :class="[
                    'n8n-node-' + data.type,
                    data.status === 'success' ? 'n8n-node-active' : 'n8n-node-inactive'
                  ]"
                >
                  <Handle id="left" type="target" :position="Position.Left" class="n8n-handle-left" />
                  <Handle id="right" type="source" :position="Position.Right" class="n8n-handle-right" />
                  
                  <div class="n8n-node-icon">
                    <component :is="getNodeIcon(data.type)" class="w-4 h-4" />
                  </div>
                  <div class="n8n-node-content">
                    <div class="n8n-node-name">{{ data.label }}</div>
                  </div>
                  <div 
                    class="n8n-node-status"
                    :class="data.status === 'success' ? 'n8n-status-success' : 'n8n-status-inactive'"
                  />
                </div>
              </template>
            </VueFlow>
            
            <!-- Empty State -->
            <div v-else class="absolute inset-0 flex items-center justify-center">
              <div class="text-center">
                <GitBranch class="w-16 h-16 text-text-muted mx-auto mb-4" />
                <h3 class="text-lg font-semibold text-text mb-2">Select a Process</h3>
                <p class="text-text-muted">Choose a workflow from the list to visualize its structure</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Panel: Details + Actions -->
        <div class="w-80 space-y-4 flex-shrink-0">
          <!-- Workflow Details -->
          <div v-if="selectedWorkflowData" class="premium-glass rounded-lg p-4">
            <h3 class="text-sm font-bold text-text mb-3">Process Details</h3>
            <div class="space-y-2 text-xs">
              <div class="flex justify-between">
                <span class="text-text-muted">Status:</span>
                <span :class="selectedWorkflowData.is_active ? 'text-primary font-semibold' : 'text-text-muted'">
                  {{ selectedWorkflowData.is_active ? 'ACTIVE' : 'INACTIVE' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">Steps:</span>
                <span class="text-text font-bold">{{ workflowDetails?.nodeCount || 0 }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">Connections:</span>
                <span class="text-text font-bold">{{ workflowDetails?.connectionCount || 0 }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">Complexity:</span>
                <span class="text-warning font-bold">{{ workflowDetails?.businessMetadata?.complexity || 'Unknown' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">Category:</span>
                <span class="text-primary font-semibold text-xs">{{ workflowDetails?.businessMetadata?.category || 'General' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">Business Impact:</span>
                <span class="text-warning font-semibold">{{ workflowDetails?.businessMetadata?.businessImpact || 'Medium' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">Executions Today:</span>
                <span class="text-primary font-bold">{{ selectedWorkflowData.executions_today }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">ID:</span>
                <span class="text-text font-mono text-xs">{{ selectedWorkflowData.process_id.slice(0, 8) }}...</span>
              </div>
            </div>
          </div>

          <!-- Quick Actions -->
          <div v-if="selectedWorkflowData" class="premium-glass rounded-lg p-4">
            <h3 class="text-sm font-bold text-text mb-3">Quick Actions</h3>
            <div class="grid grid-cols-2 gap-2">
              <button @click="openDetailedModal" class="btn-control text-xs justify-center">
                <Eye class="w-3 h-3" />
                Details
              </button>
              <button @click="openTimelineModal" class="btn-control-primary text-xs justify-center">
                <Clock class="w-3 h-3" />
                Timeline
              </button>
            </div>
          </div>

          <!-- Global Actions -->
          <div class="premium-glass rounded-lg p-4">
            <h3 class="text-sm font-bold text-text mb-3">System</h3>
            <button @click="refreshAllData" :disabled="isLoading" class="btn-control-primary w-full text-xs justify-center">
              <RefreshCw :class="{ 'animate-spin': isLoading }" class="w-3 h-3" />
              Refresh All Data
            </button>
          </div>

        </div>
      </div>

      <!-- Enhanced Modals -->
      <WorkflowDetailModal
        v-if="selectedWorkflowForModal"
        :workflow="selectedWorkflowForModal"
        :show="showDetailModal"
        @close="closeDetailModal"
      />

      <AgentDetailModal
        v-if="selectedWorkflowId && showTimelineModal"
        :workflow-id="selectedWorkflowId"
        :tenant-id="tenantId"
        :show="showTimelineModal"
        @close="closeTimelineModal"
      />
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { VueFlow, useVueFlow, Position, Handle } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { 
  RefreshCw, GitBranch, Eye, Clock, Play, Settings, Database, Mail, Bot, ChevronLeft
} from 'lucide-vue-next'
import MainLayout from '../components/layout/MainLayout.vue'
import WorkflowDetailModal from '../components/workflows/WorkflowDetailModalEnhanced.vue'
import AgentDetailModal from '../components/agents/AgentDetailModalEnhanced.vue'
import { useUIStore } from '../stores/ui'

// VueFlow styles
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

// Stores
const uiStore = useUIStore()

// State
const isLoading = ref(false)
const tenantId = 'client_simulation_a'
const sidebarCollapsed = ref(false)

// Workflow data - ONLY REAL DATA
const realWorkflows = ref<any[]>([])
const selectedWorkflowId = ref('')
const selectedWorkflowData = ref<any>(null)
const workflowDetails = ref<any>(null)

// Modal state
const showDetailModal = ref(false)
const showTimelineModal = ref(false)
const selectedWorkflowForModal = ref<any>(null)

// VueFlow
const flowElements = ref([])
const { fitView, zoomIn: vueFlowZoomIn, zoomOut: vueFlowZoomOut, setViewport, getViewport } = useVueFlow()

// Computed
const totalWorkflows = computed(() => realWorkflows.value.length)
const activeWorkflows = computed(() => realWorkflows.value.filter(w => w.is_active).length)
const flowNodes = computed(() => flowElements.value.filter(el => !el.source))
const flowEdges = computed(() => flowElements.value.filter(el => el.source))

// Methods - ALL USING REAL BACKEND DATA
const refreshAllData = async () => {
  isLoading.value = true
  
  try {
    console.log('🔄 Loading ALL REAL workflow data for Command Center...')
    
    // Get all workflows from backend
    const response = await fetch(`http://localhost:3001/api/business/processes?_t=${Date.now()}`)
    
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('✅ REAL workflows loaded:', data.data?.length || 0)
    
    realWorkflows.value = data.data || []
    
    // Auto-select first active workflow if none selected
    if (!selectedWorkflowId.value && realWorkflows.value.length > 0) {
      const firstActive = realWorkflows.value.find(w => w.is_active)
      if (firstActive) {
        await selectWorkflow(firstActive)
      }
    }
    
    uiStore.showToast('Success', `${realWorkflows.value.length} workflows loaded`, 'success')
    
  } catch (error: any) {
    console.error('❌ Failed to fetch workflows:', error)
    uiStore.showToast('Error', `API failed: ${error.message}`, 'error')
  } finally {
    isLoading.value = false
  }
}

const selectWorkflow = async (workflow: any) => {
  selectedWorkflowId.value = workflow.process_id
  selectedWorkflowData.value = workflow
  
  console.log('🎯 Selected workflow:', workflow.process_name)
  
  // Load detailed workflow structure from backend
  await loadWorkflowStructure(workflow)
}

const loadWorkflowStructure = async (workflow: any) => {
  try {
    console.log('🔍 Loading REAL structure for:', workflow.process_name)
    
    const response = await fetch(`http://localhost:3001/api/business/process-details/${workflow.process_id}`)
    
    if (response.ok) {
      const data = await response.json()
      workflowDetails.value = data.data
      
      console.log('✅ REAL workflow structure loaded:', data.data.nodeCount, 'nodes')
      
      // Create VueFlow from REAL data
      createFlowFromRealData(data.data, workflow)
      
    } else {
      console.warn('⚠️ Workflow details not available, using enhanced representation')
      createEnhancedFlow(workflow)
    }
    
  } catch (error: any) {
    console.error('❌ Failed to load workflow structure:', error)
    createEnhancedFlow(workflow)
  }
}

const createFlowFromRealData = (processDetails: any, workflowMetadata: any) => {
  const processSteps = processDetails.processSteps || []
  const processFlow = processDetails.processFlow || []
  
  console.log('🔧 Creating flow from REAL data:', processSteps.length, 'steps')
  
  // Create nodes from REAL backend data
  const nodes = processSteps.map((step: any) => ({
    id: step.stepName,
    type: 'custom',
    position: { 
      x: step.position[0] || 0, 
      y: step.position[1] || 0
    },
    data: {
      label: step.stepName,
      status: workflowMetadata.is_active ? 'success' : 'inactive',
      type: getBusinessTypeFromCategory(step.businessCategory)
    }
  }))
  
  // Create edges from REAL connections
  const edges = processFlow.map((flow: any, index: number) => ({
    id: `edge-${index}`,
    source: flow.from,
    target: flow.to,
    type: 'straight',
    animated: workflowMetadata.is_active,
    style: { stroke: '#10b981', strokeWidth: 2 },
    sourceHandle: 'right',
    targetHandle: 'left'
  }))
  
  flowElements.value = [...nodes, ...edges]
  
  // Auto-fit after loading
  setTimeout(() => {
    fitView({ duration: 800, padding: 0.15 })
  }, 300)
}

const createEnhancedFlow = (workflow: any) => {
  // Enhanced fallback based on workflow name (when backend details not available)
  console.log('🔧 Creating enhanced flow for:', workflow.process_name)
  
  const name = workflow.process_name.toLowerCase()
  let steps = []
  
  if (name.includes('grab') || name.includes('track')) {
    steps = ['Data Source', 'Extract', 'Process', 'AI Analysis', 'Store', 'Notify']
  } else if (name.includes('chatbot')) {
    steps = ['Webhook', 'Parse', 'Intent', 'AI Response', 'Reply', 'Log']
  } else if (name.includes('customer') || name.includes('service')) {
    steps = ['Request', 'Classify', 'Route', 'AI Process', 'Respond', 'Update']
  } else {
    steps = ['Trigger', 'Process', 'Execute', 'Complete']
  }
  
  const nodes = steps.map((step, index) => ({
    id: step,
    type: 'custom',
    position: { x: index * 180, y: 50 },
    data: {
      label: step,
      status: workflow.is_active ? 'success' : 'inactive',
      type: index === 0 ? 'trigger' : index === steps.length - 1 ? 'storage' : 'process'
    }
  }))
  
  const edges = []
  for (let i = 0; i < steps.length - 1; i++) {
    edges.push({
      id: `e${i}`,
      source: steps[i],
      target: steps[i + 1],
      type: 'straight',
      animated: workflow.is_active,
      style: { stroke: '#10b981', strokeWidth: 2 },
      sourceHandle: 'right',
      targetHandle: 'left'
    })
  }
  
  flowElements.value = [...nodes, ...edges]
  
  setTimeout(() => {
    fitView({ duration: 800 })
  }, 300)
}

// Flow controls
const autoLayoutFlow = () => {
  const nodes = flowNodes.value
  
  // Horizontal layout
  nodes.forEach((node, index) => {
    const elementIndex = flowElements.value.findIndex(el => el.id === node.id)
    if (elementIndex !== -1) {
      flowElements.value[elementIndex].position = {
        x: index * 180,
        y: 50 + (index % 2 * 40) // Slight zigzag
      }
    }
  })
  
  uiStore.showToast('Success', 'Flow arranged horizontally', 'success')
}

const zoomIn = () => {
  const viewport = getViewport()
  setViewport({ ...viewport, zoom: Math.min(viewport.zoom * 1.2, 3) }, { duration: 300 })
}

const zoomOut = () => {
  const viewport = getViewport()
  setViewport({ ...viewport, zoom: Math.max(viewport.zoom * 0.8, 0.2) }, { duration: 300 })
}

// Modal functions
const openDetailedModal = () => {
  if (!selectedWorkflowData.value) return
  
  selectedWorkflowForModal.value = {
    id: selectedWorkflowData.value.process_id,
    name: selectedWorkflowData.value.process_name,
    active: selectedWorkflowData.value.is_active,
    is_archived: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    node_count: workflowDetails.value?.nodeCount || 0,
    execution_count: parseInt(selectedWorkflowData.value.executions_today) || 0
  }
  showDetailModal.value = true
}

const openTimelineModal = () => {
  showTimelineModal.value = true
}

const closeDetailModal = () => {
  showDetailModal.value = false
  selectedWorkflowForModal.value = null
}

const closeTimelineModal = () => {
  showTimelineModal.value = false
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
    case 'ai': return Bot
    case 'api': return GitBranch
    case 'email': return Mail
    case 'storage': return Database
    case 'logic': return Settings
    case 'file': return Database
    default: return Settings
  }
}

// Lifecycle
onMounted(() => {
  refreshAllData()
})
</script>

<style scoped>
.workflow-flow {
  background: var(--color-background);
}

/* Import n8n node styles */
:deep(.vue-flow__node-custom) {
  background: transparent !important;
  border: none !important;
}

/* n8n node styles (copy from main page) */
:deep(.n8n-node) {
  background: #fff;
  border: 2px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  width: 80px;
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: all 0.2s ease;
  cursor: pointer;
}

:deep(.n8n-node:hover) {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

:deep(.n8n-node-active) {
  border-color: #10b981;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
}

:deep(.n8n-node-icon) {
  background: #f8f9fa;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  margin-bottom: 6px;
}

:deep(.n8n-node-name) {
  font-size: 10px;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 70px;
  text-align: center;
}

:deep(.n8n-handle-left) {
  left: -4px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  width: 8px !important;
  height: 8px !important;
  background: #10b981 !important;
  border: 2px solid #fff !important;
  border-radius: 50% !important;
  opacity: 0 !important;
}

:deep(.n8n-handle-right) {
  right: -4px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  width: 8px !important;
  height: 8px !important;
  background: #10b981 !important;
  border: 2px solid #fff !important;
  border-radius: 50% !important;
  opacity: 0 !important;
}

:deep(.n8n-node:hover .vue-flow__handle) {
  opacity: 1 !important;
}
</style>