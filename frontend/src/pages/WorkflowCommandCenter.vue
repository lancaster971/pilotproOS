<template>
  <MainLayout>
    <div class="h-[calc(100vh-6rem)] overflow-auto">

      <!-- KPI Stats Row (Compact) -->
      <div class="grid grid-cols-5 gap-3 mb-3">
        <!-- Prod. executions -->
        <div class="premium-glass rounded-lg p-3">
          <div class="flex items-center justify-between text-xs mb-1">
            <span class="font-bold text-text">Prod. executions</span>
            <span class="text-text-muted">Last 7 days</span>
          </div>
          <div class="flex items-baseline justify-between">
            <div class="text-xl font-bold text-text">{{ totalExecutions.toLocaleString() }}</div>
            <div v-if="analyticsData?.trends" class="flex items-center">
              <span :class="getTrendClass(analyticsData.trends.executionsTrend)" class="text-xs">
                {{ getTrendIcon(analyticsData.trends.executionsTrend) }}{{ Math.abs(analyticsData.trends.executionsTrend) }}%
              </span>
            </div>
          </div>
        </div>

        <!-- Failed prod. executions -->
        <div class="premium-glass rounded-lg p-3">
          <div class="flex items-center justify-between text-xs mb-1">
            <span class="font-bold text-text">Failed prod. executions</span>
            <span class="text-text-muted">Last 7 days</span>
          </div>
          <div class="flex items-baseline justify-between">
            <div class="text-xl font-bold text-text">{{ failedExecutions }}</div>
            <div v-if="analyticsData?.trends" class="flex items-center">
              <span :class="getTrendClass(-analyticsData.trends.failedExecutionsTrend)" class="text-xs">
                {{ getTrendIcon(-analyticsData.trends.failedExecutionsTrend) }}{{ Math.abs(analyticsData.trends.failedExecutionsTrend) }}%
              </span>
            </div>
          </div>
        </div>

        <!-- Failure rate -->
        <div class="premium-glass rounded-lg p-3">
          <div class="flex items-center justify-between text-xs mb-1">
            <span class="font-bold text-text">Failure rate</span>
            <span class="text-text-muted">Last 7 days</span>
          </div>
          <div class="flex items-baseline justify-between">
            <div class="text-xl font-bold text-text">{{ failureRate }}%</div>
            <div v-if="analyticsData?.trends" class="flex items-center">
              <span :class="getTrendClass(-analyticsData.trends.failureRateTrend)" class="text-xs">
                {{ getTrendIcon(-analyticsData.trends.failureRateTrend) }}{{ formatTrendValue(analyticsData.trends.failureRateTrend) }}pp
              </span>
            </div>
          </div>
        </div>

        <!-- Time saved -->
        <div class="premium-glass rounded-lg p-3">
          <div class="flex items-center justify-between text-xs mb-1">
            <span class="font-bold text-text">Time saved</span>
            <span class="text-text-muted">Last 7 days</span>
          </div>
          <div class="flex items-baseline justify-between">
            <div class="text-xl font-bold text-text">{{ timeSaved }}h</div>
            <div v-if="analyticsData?.trends" class="flex items-center">
              <span :class="getTrendClass(analyticsData.trends.timeSavedTrend)" class="text-xs">
                {{ getTrendIcon(analyticsData.trends.timeSavedTrend) }}{{ formatTrendDuration(analyticsData.trends.timeSavedTrend) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Run time (avg.) -->
        <div class="premium-glass rounded-lg p-3">
          <div class="flex items-center justify-between text-xs mb-1">
            <span class="font-bold text-text">Run time (avg.)</span>
            <span class="text-text-muted">Last 7 days</span>
          </div>
          <div class="flex items-baseline justify-between">
            <div class="text-xl font-bold text-text">{{ avgRunTime }}m</div>
            <div v-if="analyticsData?.trends" class="flex items-center">
              <span :class="getTrendClass(-analyticsData.trends.avgDurationTrend)" class="text-xs">
                {{ getTrendIcon(-analyticsData.trends.avgDurationTrend) }}{{ formatTrendSeconds(analyticsData.trends.avgDurationTrend) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Layout: Collapsible Sidebar + Flow + Details -->
      <div class="flex gap-4 h-[calc(100%-4rem)]">
        
        <!-- Collapsible Left Sidebar: Workflow List -->
        <div 
          :class="sidebarCollapsed ? 'w-12' : 'w-48'"
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
                :key="workflow.id"
                @click="selectWorkflow(workflow)"
                class="p-2 rounded-md cursor-pointer transition-all text-xs"
                :class="selectedWorkflowId === workflow.id 
                  ? 'bg-primary/10 border border-primary/30' 
                  : 'bg-surface/50 hover:bg-surface border border-transparent hover:border-border'"
              >
                <div class="flex items-center gap-2 mb-1">
                  <div 
                    class="w-1.5 h-1.5 rounded-full"
                    :class="workflow.is_active ? 'bg-primary animate-pulse' : 'bg-text-muted'"
                  />
                  <span class="font-medium text-text truncate flex-1 max-w-32" :title="workflow.process_name">
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
                :key="workflow.id"
                @click="selectWorkflow(workflow)"
                class="w-8 h-8 rounded-md cursor-pointer transition-all flex items-center justify-center"
                :class="selectedWorkflowId === workflow.id 
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
          <!-- n8n-style Header with Tabs -->
          <div class="bg-surface/30 border-b border-border px-4 py-2 flex items-center justify-between">
            <div class="text-sm font-medium text-text truncate">
              {{ selectedWorkflowData?.process_name || 'Select a workflow to visualize' }}
            </div>
            
            <!-- Action Buttons like n8n -->
            <div class="flex items-center bg-surface border border-border rounded-lg p-1 gap-1">
              <button 
                @click="openDetailedModal"
                :disabled="!selectedWorkflowId"
                class="px-3 py-1.5 text-xs font-medium rounded transition-colors text-text-muted hover:text-text hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                <Eye class="w-3 h-3" />
                Details
              </button>
              <button 
                @click="openTimelineModal"
                :disabled="!selectedWorkflowId"
                class="px-3 py-1.5 text-xs font-medium rounded transition-colors text-text-muted hover:text-text hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                <Clock class="w-3 h-3" />
                Timeline
              </button>
              <button 
                @click="openExecutionsModal"
                :disabled="!selectedWorkflowId"
                class="px-3 py-1.5 text-xs font-medium rounded transition-colors text-text-muted hover:text-text hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                <GitBranch class="w-3 h-3" />
                Executions
              </button>
            </div>
            
            <div></div> <!-- Spacer for balance -->
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
              
              <!-- Custom n8n-style Controls -->
              <div class="absolute bottom-4 left-4 flex flex-col gap-2 z-50">
                <!-- Fit View Button -->
                <button 
                  @click="() => fitView({ duration: 800, padding: 0.15 })"
                  class="w-10 h-10 bg-gray-800 border border-gray-600 text-white rounded hover:bg-gray-700 transition-colors flex items-center justify-center shadow-lg"
                  title="Fit View"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M5 5h4v2H7v2H5V5zm10 0h4v4h-2V7h-2V5zM7 15v2h2v2H5v-4h2zm8 2v-2h2v4h-4v-2h2z"/>
                  </svg>
                </button>
                
                <!-- Zoom In Button -->
                <button 
                  @click="zoomIn"
                  class="w-10 h-10 bg-gray-800 border border-gray-600 text-white rounded hover:bg-gray-700 transition-colors flex items-center justify-center text-lg font-bold shadow-lg"
                  title="Zoom In"
                >
                  +
                </button>
                
                <!-- Zoom Out Button -->
                <button 
                  @click="zoomOut"
                  class="w-10 h-10 bg-gray-800 border border-gray-600 text-white rounded hover:bg-gray-700 transition-colors flex items-center justify-center text-lg font-bold shadow-lg"
                  title="Zoom Out"
                >
                  −
                </button>
                
                <!-- Layout Button -->
                <button 
                  @click="autoLayoutFlow"
                  :disabled="!selectedWorkflowId || flowElements.length === 0"
                  class="w-10 h-10 bg-gray-800 border border-gray-600 text-white rounded hover:bg-gray-700 transition-colors flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
                  title="Auto Layout"
                >
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M3 3v6h6V3H3zM5 5h2v2H5V5zM3 15v6h6v-6H3zM5 17h2v2H5v-2zM15 3v6h6V3h-6zM17 5h2v2h-2V5zM15 15v6h6v-6h-6zM17 17h2v2h-2v-2z"/>
                  </svg>
                </button>
              </div>
              
              <template #node-custom="{ data }">
                <!-- AI NODES: Premium Diamond/Hexagon Shape (Internal Labels) -->
                <div 
                  v-if="data.type === 'ai'"
                  class="premium-ai-node"
                  :class="[
                    data.status === 'success' ? 'premium-ai-active' : 'premium-ai-inactive'
                  ]"
                >
                  <!-- Main Input Handle (LEFT side) -->
                  <Handle 
                    v-for="(input, index) in (data.inputs || []).filter(i => i === 'main')"
                    :key="'main-input-' + index"
                    :id="'input-' + index" 
                    type="target" 
                    :position="Position.Left" 
                    :style="{ top: '50%', transform: 'translateY(-50%)' }"
                    class="premium-handle-ai-main"
                    :title="`Main Input: ${input}`"
                  />
                  
                  <!-- Main Output Handle (RIGHT side) -->
                  <Handle 
                    v-for="(output, index) in (data.outputs || []).filter(o => o === 'main')"
                    :key="'main-output-' + index"
                    :id="'output-' + index" 
                    type="source" 
                    :position="Position.Right" 
                    :style="{ top: '50%', transform: 'translateY(-50%)' }"
                    class="premium-handle-ai-main"
                    :title="`Main Output: ${output}`"
                  />
                  
                  <!-- AI Tool Handles (BOTTOM) - Multiple distributed handles -->
                  <Handle 
                    v-for="(nonMainConnection, index) in [...(data.inputs || []).filter(i => i !== 'main'), ...(data.outputs || []).filter(o => o !== 'main')]"
                    :key="'tool-' + index"
                    :id="'tool-' + index" 
                    :type="(data.inputs || []).includes(nonMainConnection) ? 'target' : 'source'" 
                    :position="Position.Bottom" 
                    :style="{ 
                      left: nonMainConnection.length > 1 ? 
                        `${20 + (index * (140 / Math.max([...(data.inputs || []).filter(i => i !== 'main'), ...(data.outputs || []).filter(o => o !== 'main')].length - 1, 1)))}px` : 
                        '50%',
                      transform: 'translateX(-50%)'
                    }"
                    class="premium-handle-ai-tool"
                    :title="`AI Tool: ${nonMainConnection}`"
                  />
                  
                  <!-- AI Icon with glow effect -->
                  <div class="premium-ai-icon">
                    <N8nIcon v-bind="getN8nIconProps(data.nodeType, data.label)" size="w-16 h-16" />
                    <div class="premium-ai-glow"></div>
                  </div>
                  
                  <!-- AI Content -->
                  <div class="premium-ai-content">
                    <div class="premium-ai-name">{{ data.label }}</div>
                    <div class="premium-ai-badge">AI AGENT</div>
                    <div v-if="data.outputs?.length > 1" class="premium-ai-connections">
                      {{ data.outputs.length }} outputs
                    </div>
                  </div>
                  
                  <!-- AI Status indicator -->
                  <div 
                    class="premium-ai-status"
                    :class="data.status === 'success' ? 'premium-status-ai-active' : 'premium-status-ai-inactive'"
                  />
                </div>

                <!-- TRIGGER NODES: n8n Style with External Label -->
                <div 
                  v-else-if="data.type === 'trigger'"
                  class="premium-node-wrapper"
                >
                  <div 
                    class="premium-trigger-node"
                    :class="[
                      data.status === 'success' ? 'premium-trigger-active' : 'premium-trigger-inactive'
                    ]"
                  >
                    <!-- Right-side handles -->
                    <Handle 
                      v-for="(output, index) in data.outputs || ['main']"
                      :key="'output-' + index"
                      :id="'output-' + index" 
                      type="source" 
                      :position="Position.Right" 
                      :style="{ 
                        top: data.outputs?.length > 1 ? `${15 + (index * 20)}px` : '50%',
                        transform: 'translateY(-50%)'
                      }"
                      class="premium-handle-trigger" 
                    />
                    
                    <!-- Center icon only -->
                    <div class="premium-trigger-icon">
                      <N8nIcon v-bind="getN8nIconProps(data.nodeType, data.label)" size="w-12 h-12" />
                    </div>
                  </div>
                  
                  <!-- External label below node -->
                  <div class="premium-external-label">
                    {{ data.label }}
                  </div>
                </div>

                <!-- TOOL NODES: n8n Style Circular with External Label -->
                <div 
                  v-else-if="data.type === 'tool'"
                  class="premium-node-wrapper"
                >
                  <div 
                    class="premium-tool-node"
                    :class="[
                      data.status === 'success' ? 'premium-tool-active' : 'premium-tool-inactive'
                    ]"
                  >
                    <!-- Tool handles: Input BOTTOM, Output TOP like n8n -->
                    <Handle 
                      v-for="(input, index) in data.inputs || ['main']"
                      :key="'input-' + index"
                      :id="'input-' + index" 
                      type="target" 
                      :position="Position.Bottom" 
                      :style="{ left: '50%', transform: 'translateX(-50%)' }"
                      class="premium-handle-tool-bottom" 
                    />
                    
                    <Handle 
                      v-for="(output, index) in data.outputs || ['main']"
                      :key="'output-' + index"
                      :id="'output-' + index" 
                      type="source" 
                      :position="Position.Top" 
                      :style="{ left: '50%', transform: 'translateX(-50%)' }"
                      class="premium-handle-tool-top" 
                    />
                    
                    <!-- Center icon only -->
                    <div class="premium-tool-icon">
                      <N8nIcon v-bind="getN8nIconProps(data.nodeType, data.label)" size="w-12 h-12" />
                    </div>
                  </div>
                  
                  <!-- External label below node -->
                  <div class="premium-external-label">
                    {{ data.label }}
                  </div>
                </div>

                <!-- STORAGE NODES: n8n Style Pill Shape -->
                <div 
                  v-else-if="data.type === 'storage'"
                  class="premium-storage-node"
                  :class="[
                    data.status === 'success' ? 'premium-storage-active' : 'premium-storage-inactive'
                  ]"
                >
                  <!-- Handles top and bottom like n8n -->
                  <Handle 
                    v-for="(input, index) in data.inputs || ['main']"
                    :key="'input-' + index"
                    :id="'input-' + index" 
                    type="target" 
                    :position="Position.Top" 
                    :style="{ left: '50%', transform: 'translateX(-50%)' }"
                    class="premium-handle-storage" 
                  />
                  
                  <Handle 
                    v-for="(output, index) in data.outputs || ['main']"
                    :key="'output-' + index"
                    :id="'output-' + index" 
                    type="source" 
                    :position="Position.Bottom" 
                    :style="{ left: '50%', transform: 'translateX(-50%)' }"
                    class="premium-handle-storage" 
                  />
                  
                  <!-- Horizontal layout: icon + text -->
                  <div class="premium-storage-icon">
                    <N8nIcon v-bind="getN8nIconProps(data.nodeType, data.label)" />
                  </div>
                  <div class="premium-storage-name">{{ data.label }}</div>
                </div>

                <!-- PROCESS NODES: n8n Style Square with External Label -->
                <div 
                  v-else
                  class="premium-node-wrapper"
                >
                  <div 
                    class="premium-process-node"
                    :class="[
                      data.status === 'success' ? 'premium-process-active' : 'premium-process-inactive'
                    ]"
                  >
                    <!-- Left-side input handles -->
                    <Handle 
                      v-for="(input, index) in data.inputs || ['main']"
                      :key="'input-' + index"
                      :id="'input-' + index" 
                      type="target" 
                      :position="Position.Left" 
                      :style="{ 
                        top: data.inputs?.length > 1 ? `${15 + (index * 20)}px` : '50%',
                        transform: 'translateY(-50%)'
                      }"
                      class="premium-handle-process" 
                    />
                    
                    <!-- Right-side output handles -->
                    <Handle 
                      v-for="(output, index) in data.outputs || ['main']"
                      :key="'output-' + index"
                      :id="'output-' + index" 
                      type="source" 
                      :position="Position.Right" 
                      :style="{ 
                        top: data.outputs?.length > 1 ? `${15 + (index * 20)}px` : '50%',
                        transform: 'translateY(-50%)'
                      }"
                      class="premium-handle-process" 
                    />
                    
                    <!-- Only icon inside the square node -->
                    <div class="premium-process-icon">
                      <N8nIcon v-bind="getN8nIconProps(data.nodeType, data.label)" size="w-12 h-12" />
                    </div>
                  </div>
                  
                  <!-- External label below node -->
                  <div class="premium-external-label">
                    {{ data.label }}
                  </div>
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

        <!-- Panel destro rimosso - ora fullscreen canvas -->
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

      <!-- Executions Modal -->
      <div 
        v-if="showExecutionsModal && selectedWorkflowForModal"
        class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
        @click.self="closeExecutionsModal"
      >
        <div class="bg-surface border border-border rounded-lg w-full max-w-4xl max-h-[80vh] overflow-hidden">
          <!-- Modal Header -->
          <div class="bg-surface/30 border-b border-border px-6 py-4 flex items-center justify-between">
            <div>
              <h2 class="text-lg font-bold text-text">Workflow Executions</h2>
              <p class="text-sm text-text-muted mt-1">{{ selectedWorkflowForModal.process_name }}</p>
            </div>
            <button 
              @click="closeExecutionsModal"
              class="text-text-muted hover:text-text p-2 rounded-lg hover:bg-surface-hover transition-colors"
            >
              ✕
            </button>
          </div>
          
          <!-- Modal Content -->
          <div class="p-6 overflow-y-auto max-h-[60vh]">
            <!-- Executions List Placeholder -->
            <div class="text-center py-8">
              <GitBranch class="w-16 h-16 text-text-muted mx-auto mb-4" />
              <h3 class="text-lg font-semibold text-text mb-2">Workflow Executions</h3>
              <p class="text-text-muted mb-4">
                Executions filtered for workflow: <span class="font-mono text-sm">{{ selectedWorkflowForModal.id }}</span>
              </p>
              <div class="bg-surface/50 border border-border rounded-lg p-4 text-left">
                <div class="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span class="text-text-muted">Total Executions:</span>
                    <span class="text-text font-bold ml-2">{{ selectedWorkflowForModal.executions_today }}</span>
                  </div>
                  <div>
                    <span class="text-text-muted">Status:</span>
                    <span :class="selectedWorkflowForModal.is_active ? 'text-green-500' : 'text-red-500'" class="ml-2 font-bold">
                      {{ selectedWorkflowForModal.is_active ? 'ACTIVE' : 'INACTIVE' }}
                    </span>
                  </div>
                </div>
              </div>
              <p class="text-xs text-text-muted mt-4">
                🚧 Detailed execution history will be implemented here
              </p>
            </div>
          </div>
          
          <!-- Modal Footer -->
          <div class="bg-surface/30 border-t border-border px-6 py-3 flex justify-end">
            <button 
              @click="closeExecutionsModal"
              class="px-4 py-2 bg-surface border border-border text-text rounded hover:bg-surface-hover transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { VueFlow, useVueFlow, Position, Handle } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { 
  RefreshCw, GitBranch, Eye, Clock, Play, Settings, Database, Mail, Bot, ChevronLeft,
  Code, Brain, Globe, FileText, Zap, Cpu, Workflow, MessageSquare, Link
} from 'lucide-vue-next'
import MainLayout from '../components/layout/MainLayout.vue'
import WorkflowDetailModal from '../components/workflows/WorkflowDetailModal.vue'
import AgentDetailModal from '../components/agents/AgentDetailModal.vue'
import N8nIcon from '../components/N8nIcon.vue'
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
const analyticsData = ref<any>(null)
const selectedWorkflowId = ref('')
const selectedWorkflowData = ref<any>(null)
const workflowDetails = ref<any>(null)

// Modal state
const showDetailModal = ref(false)
const showTimelineModal = ref(false)
const showExecutionsModal = ref(false)
const selectedWorkflowForModal = ref<any>(null)

// Action buttons state

// VueFlow
const flowElements = ref([])
const { fitView, zoomIn: vueFlowZoomIn, zoomOut: vueFlowZoomOut, setViewport, getViewport } = useVueFlow()

// Computed
const totalWorkflows = computed(() => realWorkflows.value.length)
const activeWorkflows = computed(() => realWorkflows.value.filter(w => w.is_active).length)
const flowNodes = computed(() => flowElements.value.filter(el => !el.source))
const flowEdges = computed(() => flowElements.value.filter(el => el.source))

// KPI Stats (REAL DATA FROM ANALYTICS API)
const totalExecutions = computed(() => {
  return analyticsData.value?.overview?.totalExecutions || 0
})
const failedExecutions = computed(() => {
  // REAL calculation from success rate
  const total = totalExecutions.value
  const successRate = analyticsData.value?.overview?.successRate || 100
  return Math.round(total * (1 - successRate / 100))
})
const failureRate = computed(() => {
  const successRate = analyticsData.value?.overview?.successRate || 100
  return (100 - successRate).toFixed(1)
})
const timeSaved = computed(() => {
  // REAL calculation from business impact
  return analyticsData.value?.businessImpact?.timeSavedHours || 0
})
const avgRunTime = computed(() => {
  // REAL average from backend API
  const avgSeconds = analyticsData.value?.overview?.avgDurationSeconds || 0
  return avgSeconds > 0 ? (avgSeconds / 60).toFixed(1) : '0.0'
})

// Methods - ALL USING REAL BACKEND DATA
const refreshAllData = async () => {
  isLoading.value = true
  
  try {
    console.log('🔄 Loading ALL REAL workflow data for Command Center...')
    
    // Get all workflows from backend with cache busting via URL param
    const [workflowsResponse, analyticsResponse] = await Promise.all([
      fetch(`http://localhost:3001/api/business/processes?_t=${Date.now()}&refresh=true`),
      fetch(`http://localhost:3001/api/business/analytics?_t=${Date.now()}`)
    ])
    
    if (!workflowsResponse.ok) {
      throw new Error(`Backend API error: ${workflowsResponse.status}`)
    }
    
    const workflowsData = await workflowsResponse.json()
    console.log('✅ REAL workflows loaded:', workflowsData.data?.length || 0)
    console.log('📋 Raw data preview:', workflowsData.data?.slice(0, 3))
    
    realWorkflows.value = workflowsData.data || []
    console.log('🔄 Set realWorkflows to:', realWorkflows.value.length, 'items')
    
    // Get analytics data for KPI calculations
    if (analyticsResponse.ok) {
      analyticsData.value = await analyticsResponse.json()
      console.log('✅ REAL analytics loaded:', {
        totalExecutions: analyticsData.value.overview?.totalExecutions,
        successRate: analyticsData.value.overview?.successRate,
        avgDuration: analyticsData.value.overview?.avgDurationSeconds
      })
    }
    
    // Auto-select Grab_Track_Simple workflow for node classification testing (contains "Scarica Pagina")
    if (!selectedWorkflowId.value && realWorkflows.value.length > 0) {
      const grabTrackWorkflow = realWorkflows.value.find(w => w.id === 'GZsYKMPDqUktd309')
      if (grabTrackWorkflow) {
        console.log('🎯 Auto-selecting Grab_Track_Simple workflow for node testing:', grabTrackWorkflow.process_name)
        await selectWorkflow(grabTrackWorkflow)
      } else {
        const tryWorkflow = realWorkflows.value.find(w => w.id === '1KpquD1jgzUsOKrx')
        if (tryWorkflow) {
          console.log('🎯 Auto-selecting TRY Backend workflow for testing node classification:', tryWorkflow.process_name)
          await selectWorkflow(tryWorkflow)
        } else {
          const firstActive = realWorkflows.value.find(w => w.is_active)
          if (firstActive) {
            await selectWorkflow(firstActive)
          }
        }
      }
    }
    
    uiStore.showToast('Success', `${realWorkflows.value.length} workflows loaded`, 'success')
    
  } catch (error: any) {
    console.error('❌ Failed to fetch workflows:', error)
    console.error('🔍 Error details:', error.stack)
    
    // Try alternative method or show detailed error
    const errorMsg = error.message?.includes('fetch') 
      ? 'Cannot connect to backend server. Is it running on port 3001?' 
      : `API Error: ${error.message}`
    
    uiStore.showToast('Connection Error', errorMsg, 'error')
    
    // Set empty array as fallback
    realWorkflows.value = []
  } finally {
    isLoading.value = false
  }
}

const selectWorkflow = async (workflow: any) => {
  selectedWorkflowId.value = workflow.id  // ✅ FIX: Use workflow.id not workflow.process_id
  selectedWorkflowData.value = workflow
  
  console.log('🎯 Selected workflow:', workflow.process_name, 'ID:', workflow.id)
  
  // Load detailed workflow structure from backend
  await loadWorkflowStructure(workflow)
}

const loadWorkflowStructure = async (workflow: any) => {
  try {
    console.log('🔍 Loading REAL structure for:', workflow.process_name)
    
    const response = await fetch(`http://localhost:3001/api/business/process-details/${workflow.id}`)  // ✅ FIX: Use workflow.id
    
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
  
  console.log('🔧 Creating flow from REAL data:', processSteps.length, 'steps', processFlow.length, 'connections')
  
  // Analyze connections to determine node handles
  const nodeConnections = new Map()
  
  processFlow.forEach((flow: any) => {
    // Track outputs for source nodes
    if (!nodeConnections.has(flow.from)) {
      nodeConnections.set(flow.from, { inputs: [], outputs: [] })
    }
    const sourceNode = nodeConnections.get(flow.from)
    if (!sourceNode.outputs.includes(flow.type)) {
      sourceNode.outputs.push(flow.type)
    }
    
    // Track inputs for target nodes
    if (!nodeConnections.has(flow.to)) {
      nodeConnections.set(flow.to, { inputs: [], outputs: [] })
    }
    const targetNode = nodeConnections.get(flow.to)
    if (!targetNode.inputs.includes(flow.type)) {
      targetNode.inputs.push(flow.type)
    }
  })
  
  // Create nodes with dynamic handles (exclude sticky notes)
  const nodes = processSteps.filter((step: any) => !step.nodeType.includes('stickyNote')).map((step: any) => {
    const connections = nodeConnections.get(step.stepName) || { inputs: ['main'], outputs: ['main'] }
    
    return {
      id: step.stepName,
      type: 'custom',
      position: { 
        x: step.position[0] || 0, 
        y: step.position[1] || 0
      },
      data: {
        label: step.stepName,
        status: workflowMetadata.is_active ? 'success' : 'inactive',
        type: getNodeTypeFromN8nType(step.nodeType, step.stepName),
        nodeType: step.nodeType, // Add nodeType for icon selection
        inputs: connections.inputs.length > 0 ? connections.inputs : ['main'],
        outputs: connections.outputs.length > 0 ? connections.outputs : ['main']
      }
    }
  })
  
  // Create edges with specific handles for STRAIGHT CONNECTIONS
  const edges = processFlow.map((flow: any, index: number) => {
    const isMainConnection = flow.type === 'main'
    const isAIConnection = flow.type.startsWith('ai_')
    
    // Source and target node types
    const sourceStep = processSteps.find(step => step.stepName === flow.from)
    const targetStep = processSteps.find(step => step.stepName === flow.to)
    
    const sourceNodeType = getNodeTypeFromN8nType(sourceStep?.nodeType || '', flow.from)
    const targetNodeType = getNodeTypeFromN8nType(targetStep?.nodeType || '', flow.to)
    
    // FIXED Handle Logic for separate straight connections
    let sourceHandle = 'output-0'
    let targetHandle = 'input-0'
    
    // Source handles based on connection type and node type
    if (sourceNodeType === 'storage') {
      // Storage nodes: Bottom output
      sourceHandle = 'output-0'
    } else if (sourceNodeType === 'tool') {
      // Tool nodes: Bottom output for all connections
      sourceHandle = 'output-0'
    } else if (sourceNodeType === 'ai') {
      // AI nodes: Right for main, Bottom distributed for AI tools
      if (isMainConnection) {
        sourceHandle = 'output-0'  // Right side
      } else {
        // Use distributed handles for AI tools - calculate index based on all AI connections
        const sourceConnections = nodeConnections.get(flow.from) || { inputs: [], outputs: [] }
        const allAIConnections = [...sourceConnections.inputs.filter(i => i !== 'main'), ...sourceConnections.outputs.filter(o => o !== 'main')]
        const connectionIndex = allAIConnections.findIndex(conn => conn === flow.type)
        sourceHandle = `tool-${Math.max(0, connectionIndex)}`   // Bottom side distributed
      }
    } else {
      // Process nodes: Right side
      sourceHandle = 'output-0'
    }
    
    // Target handles based on connection type and node type
    if (targetNodeType === 'storage') {
      // Storage nodes: Top input for all connections
      targetHandle = 'input-0'
    } else if (targetNodeType === 'tool') {
      // Tool nodes: Top input for all connections
      targetHandle = 'input-0'
    } else if (targetNodeType === 'ai') {
      // AI nodes: Left for main, Bottom distributed for AI tool connections
      if (isMainConnection) {
        targetHandle = 'input-0'  // Left side
      } else if (isAIConnection) {
        // Use distributed handles for AI tools - calculate index based on all AI connections
        const targetConnections = nodeConnections.get(flow.to) || { inputs: [], outputs: [] }
        const allAIConnections = [...targetConnections.inputs.filter(i => i !== 'main'), ...targetConnections.outputs.filter(o => o !== 'main')]
        const connectionIndex = allAIConnections.findIndex(conn => conn === flow.type) 
        targetHandle = `tool-${Math.max(0, connectionIndex)}`   // Bottom side distributed
      } else {
        targetHandle = 'input-0'  // Default left
      }
    } else {
      // Process nodes: Left side
      targetHandle = 'input-0'
    }
    
    console.log(`🔗 Edge ${flow.from}->${flow.to}: type=${flow.type}, source=${sourceNodeType}, target=${targetNodeType}, handles=${sourceHandle}->${targetHandle}`)
    
    return {
      id: `edge-${index}`,
      source: flow.from,
      target: flow.to,
      type: 'straight', // STRAIGHT connections instead of bezier curves
      animated: workflowMetadata.is_active && isMainConnection,
      style: { 
        stroke: isMainConnection ? '#10b981' : isAIConnection ? '#667eea' : '#3b82f6', 
        strokeWidth: isMainConnection ? 3 : 2,
        strokeDasharray: isMainConnection ? 'none' : '8 4',
        opacity: isMainConnection ? 1 : 0.8
      },
      sourceHandle,
      targetHandle,
      className: isMainConnection ? 'main-edge' : 'secondary-edge'
    }
  })
  
  console.log('✅ Created nodes with handles:', nodes.map(n => `${n.data.label}: inputs=${JSON.stringify(n.data.inputs)} outputs=${JSON.stringify(n.data.outputs)}`))
  console.log('🔗 Created edges:', edges.map(e => `${e.source}->${e.target} (${e.sourceHandle}->${e.targetHandle})`))
  
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
    id: selectedWorkflowData.value.id,
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

const openExecutionsModal = () => {
  if (selectedWorkflowData.value) {
    selectedWorkflowForModal.value = selectedWorkflowData.value
    showExecutionsModal.value = true
  }
}

const closeExecutionsModal = () => {
  showExecutionsModal.value = false
  selectedWorkflowForModal.value = null
}

// Helper functions
// Trend formatting and styling helpers
const getTrendClass = (trendValue: number) => {
  if (trendValue === null || trendValue === undefined) return 'text-gray-400 text-xs font-medium'
  if (trendValue > 0) return 'text-green-500 text-xs font-medium'
  if (trendValue < 0) return 'text-red-500 text-xs font-medium'
  return 'text-gray-400 text-xs font-medium'
}

const getTrendIcon = (trendValue: number) => {
  if (trendValue === null || trendValue === undefined) return '—'
  if (trendValue > 0) return '▲'
  if (trendValue < 0) return '▼'
  return '—'
}

const formatTrendValue = (value: number) => {
  if (value === null || value === undefined) return '—'
  return Math.abs(value).toFixed(1)
}

const formatTrendDuration = (trendPercent: number) => {
  if (trendPercent === 0) return '0m'
  // Convert percentage to estimated time change
  const timeChange = Math.abs(trendPercent) > 100 ? '30m' : `${Math.round(Math.abs(trendPercent) / 10)}m`
  return timeChange
}

const formatTrendSeconds = (trendPercent: number) => {
  if (trendPercent === 0) return '0s'
  // Convert percentage to estimated seconds change  
  const secondsChange = Math.abs(trendPercent) > 100 ? '0.06s' : `0.0${Math.round(Math.abs(trendPercent) / 10)}s`
  return secondsChange
}

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

const isScheduleTrigger = (nodeName: string) => {
  const name = nodeName.toLowerCase()
  return name.includes('trigger') || 
         name.includes('schedule') ||
         name.includes('webhook') ||
         name.includes('cron') ||
         name.includes('interval') ||
         name === 'schedule' ||
         name.startsWith('when ') ||
         name.includes('start workflow') ||
         name.includes('manual trigger')
}

const isToolNode = (nodeName: string) => {
  // Vector stores and AI processing nodes remain rectangular (exception)
  const rectangularExceptions = [
    'vector store', 'ai -', 'interpreta', 'analizza', 'elabora',
    'recupera', 'scarica', 'filtra', 'processa', 'gestisce'
  ]
  
  if (rectangularExceptions.some(exception => 
    nodeName.toLowerCase().includes(exception.toLowerCase())
  )) {
    return false
  }
  
  // Only very specific external tools/services should be circular
  const circularNodes = [
    'openai chat model', 'window buffer memory', 'pilotpro knowledge base',
    'schedule expert call', 'openai embeddings', 'cohere reranker',
    'vector store retriever', 'info ordini', 'date & time', 'parcelapp',
    'formatta risposta', 'embeddings openai3'
  ]
  
  if (circularNodes.some(name => nodeName.toLowerCase().includes(name.toLowerCase()))) {
    return true
  }
  
  // Only pure external API/service tools should be circular (more restrictive)
  const toolPatterns = [
    'chat model', 'embeddings', 'reranker', 'memory', 'retriever',
    'http request', 'webhook', 'gmail', 'outlook', 'sheets', 'drive',
    'slack', 'discord', 'telegram', 'twilio', 'stripe', 'paypal',
    'hubspot', 'salesforce', 'mailchimp', 'airtable', 'notion'
  ]
  
  return toolPatterns.some(pattern => 
    nodeName.toLowerCase().includes(pattern.toLowerCase())
  )
}

const getNodeTypeFromN8nType = (n8nType: string, nodeName: string) => {
  console.log(`🚨 CLASSIFYING: "${nodeName}" | Type: "${n8nType}"`)
  
  // 1. AI Agent LangChain → RETTANGOLO
  if (n8nType === '@n8n/n8n-nodes-langchain.agent') {
    console.log(`✅ AI AGENT: ${nodeName}`)
    return 'ai'
  }
  
  // 2. Vector Store → PILLOLA (storage CSS class)
  if (n8nType.includes('vectorstore') || n8nType.includes('vectorStore')) {
    console.log(`✅ VECTOR STORE (PILLOLA): ${nodeName}`)
    return 'storage'
  }
  
  // 3. Tools LangChain (direttamente collegati agli AI Agent) → CERCHIO
  if (n8nType.includes('@n8n/n8n-nodes-langchain.')) {
    // Escludi vector store (che sono pillole)
    if (!n8nType.includes('vectorstore') && !n8nType.includes('agent')) {
      console.log(`✅ LANGCHAIN TOOL (CERCHIO): ${nodeName}`)
      return 'tool'
    }
  }
  
  // 4. Trigger → QUADRATO con lato sx tondo smussato
  if (n8nType.includes('Trigger')) {
    console.log(`✅ TRIGGER: ${nodeName}`)
    return 'trigger'
  }
  
  // 5. Storage normale (Supabase, Database, etc.) → QUADRATO normale
  if (n8nType.includes('supabase') || n8nType.includes('database') || n8nType.includes('storage')) {
    console.log(`✅ STORAGE (QUADRATO): ${nodeName}`)
    return 'process'  // Quadrato normale
  }
  
  // 6. TUTTO IL RESTO → QUADRATO normale
  console.log(`✅ PROCESS (QUADRATO): ${nodeName}`)
  return 'process'
}

// Keep old function for fallback when n8n type not available
const getNodeType = (nodeName: string, businessCategory: string) => {
  console.log(`🔍 Node: "${nodeName}" | Category: "${businessCategory}"`)
  
  // Special case: AI Agent nodes are always 'ai'  
  if (nodeName.toLowerCase().includes('agent') || nodeName.toLowerCase().includes('assistente')) {
    console.log(`✅ ${nodeName} → AI (agent)`)
    return 'ai'
  }
  
  // Check if it's a trigger first (takes precedence)
  if (isScheduleTrigger(nodeName)) {
    console.log(`🔴 ${nodeName} → TRIGGER (should be rounded rectangle)`)
    return 'trigger'
  }
  
  // Check if it's a tool first (takes precedence over business category)
  if (isToolNode(nodeName)) {
    console.log(`🟣 ${nodeName} → TOOL (should be circular)`)
    return 'tool'
  }
  
  // Default to business category mapping
  const categoryType = getBusinessTypeFromCategory(businessCategory)
  console.log(`📦 ${nodeName} → ${categoryType} (from category)`)
  return categoryType
}

// Get n8n icon component props for a node type
const getN8nIconProps = (nodeType: string, nodeName: string = '') => {
  console.log('🔍 [DEBUG] getN8nIconProps called with:', { nodeType, nodeName })
  
  // Return object with nodeType and fallback icon
  const props = {
    nodeType: nodeType,
    fallback: 'Settings', // Default fallback
    size: 'w-5 h-5'
  }
  
  // Set specific fallbacks based on node type patterns
  if (nodeType?.includes('code')) props.fallback = 'Code'
  else if (nodeType?.includes('openAi') || nodeName.toLowerCase().includes('ai ')) props.fallback = 'Brain'
  else if (nodeType?.includes('httpRequest') || nodeName.toLowerCase().includes('scarica')) props.fallback = 'Globe'
  else if (nodeType?.includes('function')) props.fallback = 'Zap'
  else if (nodeType?.includes('webhook')) props.fallback = 'Link'
  else if (nodeType?.includes('email') || nodeType?.includes('outlook') || nodeType?.includes('gmail')) props.fallback = 'Mail'
  else if (nodeType?.includes('googleDrive') || nodeType?.includes('file')) props.fallback = 'FileText'
  else if (nodeType?.includes('scheduleTrigger') || nodeType?.includes('intervalTrigger') || nodeType?.includes('cronTrigger')) props.fallback = 'Clock'
  else if (nodeType?.includes('trigger')) props.fallback = 'Play'
  else if (nodeType?.includes('agent')) props.fallback = 'Bot'
  else if (nodeType?.includes('database') || nodeType?.includes('supabase') || nodeType?.includes('vectorStore')) props.fallback = 'Database'
  else if (nodeType?.includes('telegram')) props.fallback = 'MessageSquare'
  
  return props
}

const getNodeIcon = (nodeType: string, nodeName: string = '') => {
  // First check by nodeType for specific icons
  if (nodeType?.includes('code')) return Code
  if (nodeType?.includes('openAi') || nodeName.toLowerCase().includes('ai ')) return Brain
  if (nodeType?.includes('httpRequest') || nodeName.toLowerCase().includes('scarica')) return Globe
  if (nodeType?.includes('function')) return Zap
  if (nodeType?.includes('webhook')) return Link
  if (nodeType?.includes('email') || nodeType?.includes('outlook') || nodeType?.includes('gmail')) return Mail
  if (nodeType?.includes('googleDrive') || nodeType?.includes('file')) return FileText
  
  // Trigger icons - specific first, then generic
  if (nodeType?.includes('scheduleTrigger') || nodeType?.includes('intervalTrigger') || nodeType?.includes('cronTrigger')) return Clock
  if (nodeType?.includes('trigger')) return Play
  
  if (nodeType?.includes('agent')) return Bot
  if (nodeType?.includes('database') || nodeType?.includes('supabase') || nodeType?.includes('vectorStore')) return Database
  
  // Fallback to general type
  if (typeof nodeType === 'string') {
    if (nodeType === 'trigger') return Play
    if (nodeType === 'ai') return Bot
    if (nodeType === 'storage') return Database
    if (nodeType === 'tool') return Cpu
  }
  
  // Default
  return Settings
}

const getHandleType = (connectionType: string) => {
  if (connectionType.includes('ai_')) return 'ai'
  if (connectionType.includes('memory')) return 'memory'
  if (connectionType.includes('tool')) return 'tool'
  if (connectionType.includes('language')) return 'language'
  return 'main'
}

// Lifecycle
onMounted(async () => {
  console.log('🚀 WorkflowCommandCenter mounted, loading data...')
  await refreshAllData()
  console.log('📊 Final state:', { 
    workflows: realWorkflows.value.length, 
    totalExecutions: totalExecutions.value,
    activeWorkflows: activeWorkflows.value 
  })
})
</script>

<style scoped>
.workflow-flow {
  background: var(--color-background);
}

/* Clear default VueFlow styles */
:deep(.vue-flow__node-custom) {
  background: transparent !important;
  border: none !important;
}

/* ===== AGENT NODES (n8n Style Rectangular) ===== */
:deep(.premium-ai-node) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: 2px solid rgba(102, 126, 234, 0.4);
  border-radius: 8px;
  width: 180px;
  height: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 
    0 4px 16px rgba(102, 126, 234, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
  transform-style: preserve-3d;
}

:deep(.premium-ai-node:hover) {
  transform: translateY(-4px) rotateX(5deg);
  box-shadow: 
    0 16px 48px rgba(102, 126, 234, 0.4),
    0 0 24px rgba(118, 75, 162, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

:deep(.premium-ai-active) {
  animation: aiPulse 2s ease-in-out infinite;
}

:deep(.premium-ai-icon) {
  position: relative;
  color: white;
  margin-bottom: 8px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

:deep(.premium-ai-glow) {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.4) 0%, transparent 70%);
  border-radius: 50%;
  animation: aiGlow 3s ease-in-out infinite;
  z-index: -1;
}

:deep(.premium-ai-content) {
  text-align: center;
  color: white;
}

:deep(.premium-ai-name) {
  font-size: 11px;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  margin-bottom: 2px;
  line-height: 1.2;
}

:deep(.premium-ai-badge) {
  font-size: 8px;
  font-weight: 900;
  background: rgba(255, 255, 255, 0.2);
  padding: 1px 6px;
  border-radius: 10px;
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

:deep(.premium-ai-connections) {
  font-size: 8px;
  opacity: 0.8;
  margin-top: 2px;
}

/* ===== TOOL NODES (n8n Style Circular) ===== */
:deep(.premium-tool-node) {
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  width: 90px;
  height: 90px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

:deep(.premium-tool-node:hover) {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

:deep(.premium-tool-active) {
  animation: toolPulse 2s ease-in-out infinite;
}

:deep(.premium-tool-icon) {
  color: white;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
}

:deep(.premium-tool-content) {
  text-align: center;
  color: white;
}

:deep(.premium-tool-name) {
  font-size: 8px;
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  margin-bottom: 1px;
  line-height: 1.1;
}

:deep(.premium-tool-badge) {
  font-size: 6px;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  padding: 1px 3px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

/* ===== TRIGGER NODES (Exact n8n Style) ===== */
:deep(.premium-trigger-node) {
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 50px 12px 12px 50px; /* Left side fully rounded, right side square */
  width: 100px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

:deep(.premium-trigger-node:hover) {
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

:deep(.premium-trigger-active) {
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
  border-color: rgba(16, 185, 129, 0.4);
}

:deep(.premium-trigger-inactive) {
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
  border-color: rgba(255, 255, 255, 0.1);
}

:deep(.premium-trigger-icon) {
  color: white;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.5));
}

/* Lightning bolt indicator (top-left corner) */
:deep(.premium-trigger-node::before) {
  content: "⚡";
  position: absolute;
  top: -8px;
  left: -8px;
  font-size: 12px;
  width: 16px;
  height: 16px;
  background: #f59e0b;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

:deep(.premium-trigger-content) {
  text-align: left;
  flex: 1;
  overflow: hidden;
}

:deep(.premium-trigger-name) {
  font-size: 10px;
  font-weight: 500;
  color: #e0e0e0;
  margin-bottom: 0;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

:deep(.premium-trigger-badge) {
  font-size: 7px;
  font-weight: 800;
  background: rgba(214, 51, 132, 0.1);
  color: #d63384;
  padding: 1px 4px;
  border-radius: 6px;
  border: 1px solid rgba(214, 51, 132, 0.2);
}

/* ===== STORAGE NODES (Exact n8n Style - Pill Shape) ===== */
:deep(.premium-storage-node) {
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%) !important;
  border: 2px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 30px !important; /* Perfect pill shape - half of height */
  width: 180px !important;
  height: 60px !important;
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: flex-start !important;
  position: relative !important;
  cursor: pointer !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
  padding: 0 20px !important;
}

:deep(.premium-storage-node:hover) {
  transform: scale(1.02);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

:deep(.premium-storage-icon) {
  color: white;
  margin-right: 12px;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.5));
  flex-shrink: 0;
}

:deep(.premium-storage-name) {
  font-size: 12px;
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

:deep(.premium-storage-badge) {
  font-size: 7px;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  padding: 1px 4px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

/* ===== PREMIUM PROCESS NODES ===== */
:deep(.premium-process-node) {
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px; /* Square corners */
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(74, 85, 104, 0.2);
}

:deep(.premium-process-node:hover) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(74, 85, 104, 0.4);
}

:deep(.premium-process-active) {
  border-color: #10b981;
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
}

:deep(.premium-process-icon) {
  color: #e2e8f0; /* Light gray icon */
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
}

/* Process node names and connections are now handled by external labels */

/* ===== PREMIUM HANDLES (Enhanced Visibility) ===== */

/* Main flow handles (left/right) - INVISIBLE */
:deep(.premium-handle-ai-main) {
  width: 14px !important;
  height: 14px !important;
  background: transparent !important;
  border: none !important;
  border-radius: 50% !important;
  box-shadow: none !important;
  transition: all 0.3s ease !important;
  opacity: 0 !important;
  z-index: 10 !important;
}

:deep(.premium-handle-ai-main:hover) {
  opacity: 0 !important;
  transform: none !important;
  box-shadow: none !important;
}

/* AI Tool handles (bottom) - INVISIBLE */
:deep(.premium-handle-ai-tool) {
  width: 12px !important;
  height: 12px !important;
  background: transparent !important;
  border: none !important;
  border-radius: 50% !important;
  box-shadow: none !important;
  transition: all 0.3s ease !important;
  opacity: 0 !important;
  z-index: 10 !important;
}

:deep(.premium-handle-ai-tool:hover) {
  opacity: 0 !important;
  transform: none !important;
  box-shadow: none !important;
}

/* Handle type-specific colors */
:deep(.premium-handle-memory) {
  background: linear-gradient(45deg, #ff6b6b, #ee5a24) !important;
}

:deep(.premium-handle-tool) {
  background: linear-gradient(45deg, #2ecc71, #27ae60) !important;
}

:deep(.premium-handle-language) {
  background: linear-gradient(45deg, #f39c12, #e67e22) !important;
}

:deep(.premium-handle-ai) {
  background: linear-gradient(45deg, #9b59b6, #8e44ad) !important;
}

:deep(.premium-handle-main) {
  background: linear-gradient(45deg, #3498db, #2980b9) !important;
}

:deep(.premium-handle-trigger) {
  width: 6px !important;
  height: 6px !important;
  background: #ffffff !important;
  border: 1px solid rgba(200, 200, 200, 0.8) !important;
  border-radius: 50% !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  opacity: 1 !important;
}

:deep(.premium-handle-tool) {
  width: 12px !important;
  height: 12px !important;
  background: linear-gradient(45deg, #a855f7, #8b5cf6) !important;
  border: 2px solid white !important;
  border-radius: 50% !important;
  box-shadow: 0 2px 8px rgba(168, 85, 247, 0.5) !important;
  transition: all 0.3s ease !important;
}

:deep(.premium-handle-tool-top) {
  width: 14px !important;
  height: 14px !important;
  background: transparent !important;
  border: none !important;
  border-radius: 50% !important;
  box-shadow: none !important;
  transition: all 0.3s ease !important;
  opacity: 0 !important; /* Completely invisible */
  z-index: 15 !important;
  top: -7px !important;
}

:deep(.premium-handle-tool-top:hover) {
  opacity: 0 !important; /* Stay invisible even on hover */
  transform: translateX(-50%) !important;
  box-shadow: none !important;
}

:deep(.premium-handle-storage) {
  width: 10px !important;
  height: 10px !important;
  background: transparent !important;
  border: none !important;
  border-radius: 50% !important;
  box-shadow: none !important;
  opacity: 0 !important;
}

:deep(.premium-handle-process) {
  width: 10px !important;
  height: 10px !important;
  background: transparent !important;
  border: none !important;
  border-radius: 50% !important;
  box-shadow: none !important;
  opacity: 0 !important;
}

/* Trigger handles are now visible */

/* ===== ANIMATIONS ===== */
@keyframes aiPulse {
  0%, 100% { 
    box-shadow: 
      0 8px 32px rgba(102, 126, 234, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
  50% { 
    box-shadow: 
      0 8px 32px rgba(102, 126, 234, 0.5),
      0 0 32px rgba(118, 75, 162, 0.4),
      inset 0 1px 0 rgba(255, 255, 255, 0.3);
  }
}

@keyframes aiGlow {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.7; }
}

@keyframes triggerPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

@keyframes toolPulse {
  0%, 100% { 
    box-shadow: 0 4px 16px rgba(168, 85, 247, 0.2);
  }
  50% { 
    box-shadow: 
      0 6px 24px rgba(168, 85, 247, 0.4),
      0 0 16px rgba(139, 92, 246, 0.3);
  }
}

/* ===== EDGE STYLES (Curved like n8n) ===== */

/* Main flow edges (solid, thick, animated, curved) */
:deep(.main-edge) {
  z-index: 10;
}

:deep(.main-edge .vue-flow__edge-path) {
  stroke: #10b981 !important;
  stroke-width: 3px !important;
  opacity: 1 !important;
  stroke-linecap: round !important;
  stroke-linejoin: round !important;
}

/* Secondary/AI tool edges (dashed, thinner, curved) */
:deep(.secondary-edge) {
  z-index: 5;
}

:deep(.secondary-edge .vue-flow__edge-path) {
  stroke-dasharray: 8 4 !important;
  opacity: 0.8 !important;
  transition: all 0.3s ease !important;
  stroke-linecap: round !important;
  stroke-linejoin: round !important;
}

:deep(.secondary-edge:hover .vue-flow__edge-path) {
  opacity: 1 !important;
  stroke-width: 3px !important;
}

/* Smooth bezier curves for all edges (like n8n) */
:deep(.vue-flow__edge .vue-flow__edge-path) {
  stroke-linecap: round !important;
  stroke-linejoin: round !important;
}

/* Ensure bezier curves render properly */
:deep(.vue-flow__edge-default .vue-flow__edge-path) {
  stroke-linecap: round !important;
  stroke-linejoin: round !important;
}

/* ALL handles stay invisible - clean workflow design */
:deep(.premium-ai-node:hover .vue-flow__handle),
:deep(.premium-tool-node:hover .vue-flow__handle),
:deep(.premium-trigger-node:hover .vue-flow__handle),
:deep(.premium-storage-node:hover .vue-flow__handle),
:deep(.premium-process-node:hover .vue-flow__handle) {
  opacity: 0 !important;
}

/* ===== NODE WRAPPER & EXTERNAL LABELS (n8n Style) ===== */
:deep(.premium-node-wrapper) {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  position: relative;
  width: fit-content;
  height: fit-content;
}

:deep(.premium-external-label) {
  font-size: 10px;
  font-weight: 600;
  color: #374151;
  text-align: center;
  margin-top: 6px;
  padding: 2px 6px;
  max-width: 80px;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}
</style>