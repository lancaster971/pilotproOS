<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gradient">
            Workflow Visualization
          </h1>
          <p class="text-gray-400 mt-1">
            Visual representation of your business processes
          </p>
        </div>
        
        <div class="flex items-center gap-3">
          <select 
            v-model="selectedWorkflowId" 
            @change="loadWorkflow"
            class="bg-gray-800 border border-gray-700 text-white px-4 py-2 rounded-lg"
          >
            <option value="">Select a workflow</option>
            <option v-for="wf in workflows" :key="wf.id" :value="wf.id">
              {{ wf.name }}
            </option>
          </select>
          
          <button 
            @click="autoLayout"
            class="btn-control"
          >
            <Shuffle class="h-4 w-4" />
            Auto Layout
          </button>
          
          <button 
            @click="fitView"
            class="btn-control"
          >
            <Maximize2 class="h-4 w-4" />
            Fit View
          </button>
          
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

      <!-- Vue Flow Container -->
      <div class="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden" style="height: 70vh;">
        <VueFlow
          v-if="nodes.length > 0"
          v-model:nodes="nodes"
          v-model:edges="edges"
          :node-types="nodeTypes"
          :default-viewport="{ x: 0, y: 0, zoom: 1 }"
          :min-zoom="0.5"
          :max-zoom="2"
          class="bg-black"
          @nodes-change="onNodesChange"
          @edges-change="onEdgesChange"
          @node-click="onNodeClick"
        >
          <Background 
            :variant="BackgroundVariant.Dots" 
            :gap="20"
            :size="1"
            pattern-color="#374151"
          />
          
          <Controls 
            :show-zoom="true"
            :show-fit-view="true"
            :show-interactive="true"
            class="!bg-gray-800 !border-gray-700"
          />
          
          <MiniMap 
            class="!bg-gray-900 !border-gray-700"
            node-color="#10b981"
            mask-color="rgb(17, 24, 39, 0.9)"
          />
          
          <!-- Custom Node Template -->
          <template #node-custom="{ data }">
            <div 
              class="px-4 py-3 bg-gray-800 border-2 rounded-lg shadow-lg transition-all hover:shadow-xl"
              :class="getNodeBorderColor(data.type)"
            >
              <div class="flex items-center gap-2 mb-2">
                <component :is="getNodeIcon(data.type)" class="h-4 w-4" :class="getNodeIconColor(data.type)" />
                <span class="text-white font-medium">{{ data.label }}</span>
              </div>
              <div class="text-xs text-gray-400">
                {{ data.type }}
              </div>
              <div v-if="data.status" class="mt-2 flex items-center gap-1">
                <div 
                  class="w-2 h-2 rounded-full"
                  :class="data.status === 'success' ? 'bg-green-400' : 'bg-gray-600'"
                />
                <span class="text-xs text-gray-400">{{ data.status }}</span>
              </div>
            </div>
          </template>
        </VueFlow>
        
        <!-- Empty State -->
        <div v-else class="h-full flex items-center justify-center">
          <div class="text-center">
            <GitBranch class="h-16 w-16 text-gray-600 mx-auto mb-4" />
            <p class="text-gray-400 text-lg">Select a workflow to visualize</p>
            <p class="text-gray-500 text-sm mt-2">Choose from the dropdown above</p>
          </div>
        </div>
      </div>

      <!-- Node Details Panel -->
      <div v-if="selectedNode" class="bg-gray-900 border border-gray-700 rounded-lg p-6">
        <h3 class="text-lg font-semibold text-white mb-4">Node Details</h3>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <p class="text-gray-400 text-sm">Name</p>
            <p class="text-white">{{ selectedNode.data.label }}</p>
          </div>
          <div>
            <p class="text-gray-400 text-sm">Type</p>
            <p class="text-white">{{ selectedNode.data.type }}</p>
          </div>
          <div>
            <p class="text-gray-400 text-sm">Position</p>
            <p class="text-white">X: {{ Math.round(selectedNode.position.x) }}, Y: {{ Math.round(selectedNode.position.y) }}</p>
          </div>
          <div>
            <p class="text-gray-400 text-sm">Status</p>
            <p class="text-white">{{ selectedNode.data.status || 'Not executed' }}</p>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background, BackgroundVariant } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { 
  RefreshCw, GitBranch, Maximize2, Shuffle,
  Database, Mail, Globe, Bot, Zap, Filter, Code, Send
} from 'lucide-vue-next'
import MainLayout from '../components/layout/MainLayout.vue'
import { useUIStore } from '../stores/ui'

// Types
interface WorkflowNode {
  id: string
  type: string
  position: { x: number; y: number }
  data: {
    label: string
    type: string
    status?: string
  }
}

interface WorkflowEdge {
  id: string
  source: string
  target: string
  type?: string
  animated?: boolean
  style?: any
}

// Stores
const uiStore = useUIStore()

// Vue Flow
const { fitView: fitViewMethod, zoomTo } = useVueFlow()

// Local state
const isLoading = ref(false)
const workflows = ref<any[]>([])
const selectedWorkflowId = ref('')
const nodes = ref<WorkflowNode[]>([])
const edges = ref<WorkflowEdge[]>([])
const selectedNode = ref<WorkflowNode | null>(null)

// Node types for custom rendering
const nodeTypes = {
  custom: 'custom'
}

// Methods
const refreshWorkflows = async () => {
  isLoading.value = true
  
  try {
    const response = await fetch('http://localhost:3001/api/business/processes')
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }
    
    const data = await response.json()
    workflows.value = data.data || []
    
    uiStore.showToast('Success', `Loaded ${workflows.value.length} workflows`, 'success')
  } catch (error: any) {
    console.error('Failed to load workflows:', error)
    uiStore.showToast('Error', 'Failed to load workflows', 'error')
  } finally {
    isLoading.value = false
  }
}

const loadWorkflow = () => {
  if (!selectedWorkflowId.value) {
    nodes.value = []
    edges.value = []
    return
  }
  
  // Generate sample workflow visualization
  // In real implementation, this would parse actual workflow data
  const workflow = workflows.value.find(w => w.id === selectedWorkflowId.value)
  
  if (!workflow) return
  
  // Create sample nodes based on workflow type
  const sampleNodes: WorkflowNode[] = [
    {
      id: '1',
      type: 'custom',
      position: { x: 100, y: 100 },
      data: {
        label: 'Webhook Trigger',
        type: 'trigger',
        status: 'success'
      }
    },
    {
      id: '2',
      type: 'custom',
      position: { x: 300, y: 100 },
      data: {
        label: 'Data Validation',
        type: 'filter',
        status: 'success'
      }
    },
    {
      id: '3',
      type: 'custom',
      position: { x: 500, y: 100 },
      data: {
        label: 'AI Processing',
        type: 'ai-agent',
        status: 'success'
      }
    },
    {
      id: '4',
      type: 'custom',
      position: { x: 700, y: 100 },
      data: {
        label: 'Database Save',
        type: 'database',
        status: 'success'
      }
    },
    {
      id: '5',
      type: 'custom',
      position: { x: 500, y: 250 },
      data: {
        label: 'Send Email',
        type: 'email',
        status: 'pending'
      }
    }
  ]
  
  const sampleEdges: WorkflowEdge[] = [
    {
      id: 'e1-2',
      source: '1',
      target: '2',
      animated: true,
      style: { stroke: '#10b981' }
    },
    {
      id: 'e2-3',
      source: '2',
      target: '3',
      animated: true,
      style: { stroke: '#10b981' }
    },
    {
      id: 'e3-4',
      source: '3',
      target: '4',
      animated: true,
      style: { stroke: '#10b981' }
    },
    {
      id: 'e3-5',
      source: '3',
      target: '5',
      animated: false,
      style: { stroke: '#6b7280' }
    }
  ]
  
  nodes.value = sampleNodes
  edges.value = sampleEdges
  
  // Fit view after loading
  setTimeout(() => {
    fitViewMethod()
  }, 100)
}

const autoLayout = () => {
  // Simple auto-layout algorithm
  const nodeWidth = 200
  const nodeHeight = 100
  const horizontalSpacing = 250
  const verticalSpacing = 150
  
  nodes.value.forEach((node, index) => {
    const row = Math.floor(index / 3)
    const col = index % 3
    
    node.position = {
      x: col * horizontalSpacing + 100,
      y: row * verticalSpacing + 100
    }
  })
  
  setTimeout(() => {
    fitViewMethod()
  }, 100)
}

const fitView = () => {
  fitViewMethod()
}

const onNodesChange = (changes: any) => {
  console.log('Nodes changed:', changes)
}

const onEdgesChange = (changes: any) => {
  console.log('Edges changed:', changes)
}

const onNodeClick = (event: any) => {
  selectedNode.value = event.node
}

// Helper methods for node styling
const getNodeBorderColor = (type: string) => {
  switch (type) {
    case 'trigger': return 'border-green-400'
    case 'ai-agent': return 'border-purple-400'
    case 'database': return 'border-blue-400'
    case 'email': return 'border-yellow-400'
    case 'filter': return 'border-orange-400'
    default: return 'border-gray-600'
  }
}

const getNodeIcon = (type: string) => {
  switch (type) {
    case 'trigger': return Zap
    case 'ai-agent': return Bot
    case 'database': return Database
    case 'email': return Mail
    case 'filter': return Filter
    case 'api': return Globe
    case 'code': return Code
    default: return Send
  }
}

const getNodeIconColor = (type: string) => {
  switch (type) {
    case 'trigger': return 'text-green-400'
    case 'ai-agent': return 'text-purple-400'
    case 'database': return 'text-blue-400'
    case 'email': return 'text-yellow-400'
    case 'filter': return 'text-orange-400'
    default: return 'text-gray-400'
  }
}

// Lifecycle
onMounted(() => {
  refreshWorkflows()
})
</script>

<style>
/* Vue Flow base styles */
.vue-flow {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.vue-flow__container {
  position: absolute;
  width: 100%;
  height: 100%;
}

.vue-flow__pane {
  position: absolute;
  width: 100%;
  height: 100%;
  cursor: grab;
}

.vue-flow__pane.dragging {
  cursor: grabbing;
}

.vue-flow__viewport {
  position: relative;
  transform-origin: 0 0;
}

.vue-flow__edges {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

.vue-flow__edge {
  pointer-events: visibleStroke;
}

.vue-flow__nodes {
  position: absolute;
  top: 0;
  left: 0;
}

.vue-flow__node {
  position: absolute;
  user-select: none;
  pointer-events: all;
}

.vue-flow__handle {
  position: absolute;
  width: 10px;
  height: 10px;
  background: #10b981;
  border: 2px solid #047857;
  border-radius: 50%;
  cursor: crosshair;
}

.vue-flow__handle-top {
  top: -5px;
  left: 50%;
  transform: translateX(-50%);
}

.vue-flow__handle-right {
  right: -5px;
  top: 50%;
  transform: translateY(-50%);
}

.vue-flow__handle-bottom {
  bottom: -5px;
  left: 50%;
  transform: translateX(-50%);
}

.vue-flow__handle-left {
  left: -5px;
  top: 50%;
  transform: translateY(-50%);
}

/* Controls styles */
.vue-flow__controls {
  position: absolute;
  bottom: 20px;
  left: 20px;
  z-index: 5;
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: rgb(31 41 55);
  border: 1px solid rgb(55 65 81);
  border-radius: 8px;
  padding: 4px;
}

.vue-flow__controls-button {
  background: rgb(31 41 55);
  border: 1px solid rgb(55 65 81);
  color: white;
  padding: 8px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
}

.vue-flow__controls-button:hover {
  background: rgb(55 65 81);
}

/* Minimap styles */
.vue-flow__minimap {
  position: absolute;
  bottom: 20px;
  right: 20px;
  z-index: 5;
  width: 200px;
  height: 150px;
  background: rgb(17 24 39);
  border: 1px solid rgb(55 65 81);
  border-radius: 8px;
}

/* Background styles */
.vue-flow__background {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
}

.vue-flow__background-pattern {
  stroke: #374151;
  stroke-width: 1;
}

/* Dark theme overrides */
.vue-flow {
  background-color: #000000 !important;
}

.vue-flow__edge-path {
  stroke-width: 2;
}
</style>