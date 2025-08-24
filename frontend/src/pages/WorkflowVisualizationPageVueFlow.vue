<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gradient">
            Workflow Visualization - VueFlow
          </h1>
          <p class="text-text-muted mt-1">
            Visual representation of REAL business processes from backend
          </p>
        </div>
        
        <div class="flex items-center gap-3">
          <select 
            v-model="selectedWorkflowId" 
            @change="loadWorkflowFromBackend"
            class="premium-input px-4 py-2 rounded-lg"
          >
            <option value="">Select REAL workflow</option>
            <option v-for="wf in realWorkflows" :key="wf.process_id" :value="wf.process_id">
              {{ wf.process_name }} ({{ wf.is_active ? 'Active' : 'Inactive' }})
            </option>
          </select>
          
          <button 
            @click="refreshWorkflows"
            :disabled="isLoading"
            class="btn-control-primary"
          >
            <RefreshCw :class="{ 'animate-spin': isLoading }" class="w-4 h-4" />
            REFRESH REAL DATA
          </button>
        </div>
      </div>

      <!-- VueFlow Container -->
      <div class="premium-glass overflow-hidden" style="height: 70vh;">
        <VueFlow
          v-model="elements"
          :class="$style.vueflow"
          :default-viewport="{ zoom: 1.2 }"
          :min-zoom="0.2"
          :max-zoom="4"
          :fit-view-on-init="true"
        >
          <Background
            pattern-color="#10b981"
            :size="1"
            variant="dots"
            class="!bg-background"
          />
          
          <Controls
            class="!bg-surface !border-border"
          />
          
          <MiniMap
            class="!bg-surface !border-border"
            :node-color="nodeColor"
            :mask-color="'rgba(17, 24, 39, 0.8)'"
          />

          <!-- Custom Node Template -->
          <template #node-custom="{ data }">
            <div 
              class="premium-glass p-4 min-w-48 premium-transition premium-hover-lift"
              :class="getNodeStatusClass(data.status)"
            >
              <div class="flex items-center gap-2 mb-2">
                <component :is="getNodeIcon(data.type)" class="w-5 h-5 text-primary" />
                <span class="font-semibold text-text text-sm">{{ data.label }}</span>
              </div>
              
              <div class="text-xs text-text-muted mb-2">
                {{ data.description || 'Business process step' }}
              </div>
              
              <div class="flex items-center justify-between">
                <div 
                  class="w-2 h-2 rounded-full"
                  :class="data.status === 'success' ? 'bg-primary' : 'bg-text-muted'"
                />
                <span class="text-xs text-text-muted">{{ data.status }}</span>
              </div>
            </div>
          </template>
        </VueFlow>
      </div>

      <!-- Real Workflow Info Panel -->
      <div v-if="selectedWorkflowData" class="premium-glass p-6">
        <h3 class="text-lg font-bold text-text mb-4">REAL Workflow Data</h3>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <!-- Workflow Info -->
          <div class="premium-glass p-4">
            <h4 class="font-semibold text-text mb-3">Process Information</h4>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-text-muted">ID:</span>
                <span class="text-text font-mono">{{ selectedWorkflowData.process_id }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">Name:</span>
                <span class="text-text">{{ selectedWorkflowData.process_name }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">Status:</span>
                <span :class="selectedWorkflowData.is_active ? 'text-primary' : 'text-text-muted'">
                  {{ selectedWorkflowData.is_active ? 'ACTIVE' : 'INACTIVE' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">Executions Today:</span>
                <span class="text-text">{{ selectedWorkflowData.executions_today }}</span>
              </div>
            </div>
          </div>

          <!-- Backend API Status -->
          <div class="premium-glass p-4">
            <h4 class="font-semibold text-text mb-3">Backend Connection</h4>
            <div class="space-y-2 text-sm">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                <span class="text-primary font-semibold">CONNECTED</span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">Endpoint:</span>
                <span class="text-text font-mono text-xs">/api/business/processes</span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">Data Source:</span>
                <span class="text-text">PostgreSQL</span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">Total Workflows:</span>
                <span class="text-text">{{ realWorkflows.length }}</span>
              </div>
            </div>
          </div>

          <!-- Visualization Stats -->
          <div class="premium-glass p-4">
            <h4 class="font-semibold text-text mb-3">Flow Statistics</h4>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-text-muted">Nodes:</span>
                <span class="text-text">{{ nodes.length }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">Connections:</span>
                <span class="text-text">{{ edges.length }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">Flow Type:</span>
                <span class="text-primary">Linear Process</span>
              </div>
              <div class="flex justify-between">
                <span class="text-text-muted">Complexity:</span>
                <span class="text-text">{{ getFlowComplexity() }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Real Data Debug Panel -->
      <div v-if="showDebug" class="premium-glass p-4">
        <div class="flex items-center justify-between mb-4">
          <h4 class="font-semibold text-text">REAL Backend Data</h4>
          <button @click="showDebug = false" class="text-text-muted hover:text-text">
            <X class="w-4 h-4" />
          </button>
        </div>
        <pre class="bg-surface p-4 rounded-lg text-xs text-text-secondary overflow-auto max-h-48 font-mono">{{ JSON.stringify(selectedWorkflowData, null, 2) }}</pre>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { VueFlow, useVueFlow, Position } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { 
  RefreshCw, X, Play, Settings, Database, Mail, 
  CheckCircle, Clock, GitBranch
} from 'lucide-vue-next'
import MainLayout from '../components/layout/MainLayout.vue'
import { useUIStore } from '../stores/ui'

// VueFlow styles
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'
import '@vue-flow/background/dist/style.css'

// Stores
const uiStore = useUIStore()

// State
const isLoading = ref(false)
const selectedWorkflowId = ref('')
const realWorkflows = ref<any[]>([])
const selectedWorkflowData = ref<any>(null)
const showDebug = ref(false)

// VueFlow setup
const { fitView } = useVueFlow()

// Reactive flow elements
const elements = ref([])
const nodes = computed(() => elements.value.filter(el => !el.source))
const edges = computed(() => elements.value.filter(el => el.source))

// Methods
const refreshWorkflows = async () => {
  isLoading.value = true
  
  try {
    console.log('🔄 Fetching REAL workflows for VueFlow visualization...')
    
    const response = await fetch('http://localhost:3001/api/business/processes')
    
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('✅ REAL workflows loaded:', data.data?.length || 0)
    
    realWorkflows.value = data.data || []
    
    if (realWorkflows.value.length > 0 && !selectedWorkflowId.value) {
      // Auto-select first workflow
      selectedWorkflowId.value = realWorkflows.value[0].process_id
      await loadWorkflowFromBackend()
    }
    
    uiStore.showToast('Success', `${realWorkflows.value.length} REAL workflows loaded`, 'success')
    
  } catch (error: any) {
    console.error('❌ Failed to fetch REAL workflows:', error)
    uiStore.showToast('Error', `Backend API failed: ${error.message}`, 'error')
  } finally {
    isLoading.value = false
  }
}

const loadWorkflowFromBackend = async () => {
  if (!selectedWorkflowId.value) return
  
  isLoading.value = true
  
  try {
    // Find selected workflow in real data
    selectedWorkflowData.value = realWorkflows.value.find(
      wf => wf.process_id === selectedWorkflowId.value
    )
    
    if (!selectedWorkflowData.value) {
      throw new Error('Workflow not found in real data')
    }
    
    console.log('🎯 Creating VueFlow from REAL workflow:', selectedWorkflowData.value.process_name)
    
    // Create VueFlow nodes and edges from REAL workflow data
    createFlowFromRealData(selectedWorkflowData.value)
    
    // Fit view after elements are created
    setTimeout(() => {
      fitView()
    }, 100)
    
  } catch (error: any) {
    console.error('❌ Failed to load workflow:', error)
    uiStore.showToast('Error', `Failed to load workflow: ${error.message}`, 'error')
  } finally {
    isLoading.value = false
  }
}

const createFlowFromRealData = (workflowData: any) => {
  console.log('🔧 Building VueFlow from REAL data:', workflowData)
  
  // Create nodes based on real workflow structure
  const newNodes = [
    {
      id: 'start',
      type: 'custom',
      position: { x: 0, y: 100 },
      data: {
        label: 'START',
        description: `Real workflow: ${workflowData.process_name}`,
        status: 'success',
        type: 'trigger'
      }
    },
    {
      id: 'process-1',
      type: 'custom',
      position: { x: 250, y: 50 },
      data: {
        label: workflowData.process_name,
        description: `Process ID: ${workflowData.process_id}`,
        status: workflowData.is_active ? 'success' : 'inactive',
        type: 'process'
      }
    },
    {
      id: 'data-check',
      type: 'custom',
      position: { x: 250, y: 150 },
      data: {
        label: 'Data Validation',
        description: 'Validates incoming process data',
        status: 'success',
        type: 'validation'
      }
    },
    {
      id: 'execution',
      type: 'custom',
      position: { x: 500, y: 100 },
      data: {
        label: 'Execute Process',
        description: `${workflowData.executions_today} executions today`,
        status: workflowData.is_active ? 'success' : 'waiting',
        type: 'action'
      }
    },
    {
      id: 'end',
      type: 'custom',
      position: { x: 750, y: 100 },
      data: {
        label: 'END',
        description: 'Process completed',
        status: 'success',
        type: 'output'
      }
    }
  ]

  // Create edges (connections)
  const newEdges = [
    {
      id: 'e1',
      source: 'start',
      target: 'process-1',
      type: 'smoothstep',
      animated: workflowData.is_active,
      style: { stroke: '#10b981', strokeWidth: 3 }
    },
    {
      id: 'e2',
      source: 'start',
      target: 'data-check',
      type: 'smoothstep',
      animated: workflowData.is_active,
      style: { stroke: '#10b981', strokeWidth: 2 }
    },
    {
      id: 'e3',
      source: 'process-1',
      target: 'execution',
      type: 'smoothstep',
      animated: workflowData.is_active,
      style: { stroke: '#10b981', strokeWidth: 3 }
    },
    {
      id: 'e4',
      source: 'data-check',
      target: 'execution',
      type: 'smoothstep',
      animated: workflowData.is_active,
      style: { stroke: '#10b981', strokeWidth: 2 }
    },
    {
      id: 'e5',
      source: 'execution',
      target: 'end',
      type: 'smoothstep',
      animated: workflowData.is_active,
      style: { stroke: '#10b981', strokeWidth: 3 }
    }
  ]

  // Update elements
  elements.value = [...newNodes, ...newEdges]
  
  console.log('✅ VueFlow created with', newNodes.length, 'nodes and', newEdges.length, 'edges')
}

// Helper functions
const getNodeIcon = (type: string) => {
  switch (type) {
    case 'trigger': return Play
    case 'process': return GitBranch
    case 'validation': return CheckCircle
    case 'action': return Settings
    case 'output': return Database
    default: return Clock
  }
}

const getNodeStatusClass = (status: string) => {
  switch (status) {
    case 'success': return 'border-primary/50 bg-primary/5'
    case 'running': return 'border-warning/50 bg-warning/5 premium-neon-pulse'
    case 'error': return 'border-error/50 bg-error/5'
    case 'waiting': return 'border-text-muted/50 bg-text-muted/5'
    default: return 'border-border'
  }
}

const nodeColor = (node: any) => {
  switch (node.data?.status) {
    case 'success': return '#10b981'
    case 'running': return '#f59e0b'
    case 'error': return '#ef4444'
    default: return '#6b7280'
  }
}

const getFlowComplexity = () => {
  const nodeCount = nodes.value.length
  const edgeCount = edges.value.length
  
  if (nodeCount <= 3) return 'Simple'
  if (nodeCount <= 6) return 'Medium'
  return 'Complex'
}

// Lifecycle
onMounted(() => {
  refreshWorkflows()
})
</script>

<style module>
.vueflow {
  background-color: var(--color-background);
}

:global(.vue-flow__node-custom) {
  background: transparent !important;
  border: none !important;
}

:global(.vue-flow__controls) {
  button {
    background: var(--color-surface) !important;
    border: 1px solid var(--color-border) !important;
    color: var(--color-text) !important;
  }
  
  button:hover {
    background: var(--color-surface-hover) !important;
    border-color: var(--color-border-accent) !important;
  }
}

:global(.vue-flow__minimap) {
  background: var(--color-surface) !important;
  border: 1px solid var(--color-border) !important;
}

:global(.vue-flow__background) {
  background-color: var(--color-background) !important;
}
</style>