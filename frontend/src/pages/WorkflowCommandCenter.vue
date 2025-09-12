<template>
  <MainLayout>
    <div class="h-[calc(100vh-4rem)] overflow-auto">

      <!-- KPI Stats Row (Compact) -->
      <div class="grid grid-cols-5 gap-3 mb-3">
        <!-- Prod. executions -->
        <div class="premium-glass rounded-lg p-3">
          <div class="flex items-center justify-between text-xs mb-1">
            <span class="font-bold text-text">Prod. executions</span>
            <span class="text-text-muted">Last 7 days</span>
          </div>
          <div class="flex items-baseline justify-between">
            <div class="text-lg font-bold text-text">{{ totalExecutions.toLocaleString() }}</div>
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
            <div class="text-lg font-bold text-text">{{ failedExecutions }}</div>
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
            <div class="text-lg font-bold text-text">{{ failureRate }}%</div>
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
            <div class="text-lg font-bold text-text">{{ timeSaved }}h</div>
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
            <div class="text-lg font-bold text-text">{{ avgRunTime }}</div>
            <div v-if="analyticsData?.trends" class="flex items-center">
              <span :class="getTrendClass(-analyticsData.trends.avgDurationTrend)" class="text-xs">
                {{ getTrendIcon(-analyticsData.trends.avgDurationTrend) }}{{ formatTrendSeconds(analyticsData.trends.avgDurationTrend) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Layout: Collapsible Sidebar + Flow + Details -->
      <div class="flex gap-4 h-[calc(100%-6rem)]">
        
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
              <Icon icon="lucide:chevron-left" :class="{ 'rotate-180': sidebarCollapsed }" class="w-4 h-4 transition-transform" />
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
                <Icon icon="lucide:eye" class="w-3 h-3" />
                Details
              </button>
              <button 
                @click="openTimelineModal"
                :disabled="!selectedWorkflowId"
                class="px-3 py-1.5 text-xs font-medium rounded transition-colors text-text-muted hover:text-text hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                <Icon icon="lucide:clock" class="w-3 h-3" />
                Timeline
              </button>
              <button 
                @click="openExecutionsModal"
                :disabled="!selectedWorkflowId"
                class="px-3 py-1.5 text-xs font-medium rounded transition-colors text-text-muted hover:text-text hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                <Icon icon="lucide:git-branch" class="w-3 h-3" />
                Executions
              </button>
            </div>
            
            <!-- Workflow Toggle Switch -->
            <div class="flex items-center gap-3">
              <span class="text-xs text-text-muted">
                {{ selectedWorkflowData?.is_active ? 'Active' : 'Inactive' }}
              </span>
              <button
                v-if="canExecute"
                @click="() => { console.log('🔘 Toggle button clicked!', { selectedWorkflowId: selectedWorkflowId.value, disabled: !selectedWorkflowId.value }); toggleWorkflowStatus() }"
                :disabled="!selectedWorkflowId"
                :class="[
                  'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed',
                  selectedWorkflowData?.is_active ? 'bg-primary' : 'bg-gray-600'
                ]"
              >
                <span
                  :class="[
                    'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                    selectedWorkflowData?.is_active ? 'translate-x-6' : 'translate-x-1'
                  ]"
                />
              </button>
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
              :connection-line-type="'default'"
              class="workflow-flow h-full"
            >
              <Background pattern-color="#10b981" :size="1" variant="dots" />
              
              <!-- Execute/Stop Button: Central bottom position like n8n (Only for admin/editor) -->
              <div v-if="canExecute" class="absolute bottom-32 left-1/2 transform -translate-x-1/2 z-50">
                <button 
                  v-if="!isExecuting"
                  @click="executeWorkflow"
                  :disabled="!selectedWorkflowId"
                  :class="[
                    'px-4 py-2 bg-gray-800 border border-gray-600 text-white rounded transition-colors shadow-lg flex items-center gap-2',
                    'hover:bg-gray-700',
                    !selectedWorkflowId ? 'opacity-50 cursor-not-allowed' : ''
                  ]"
                  title="Execute Workflow"
                >
                  <Icon icon="lucide:play" class="w-4 h-4" />
                  Execute Now
                </button>
                
                <button 
                  v-else
                  @click="stopWorkflow"
                  class="px-4 py-2 bg-red-700 border border-red-600 text-white rounded transition-colors shadow-lg flex items-center gap-2 hover:bg-red-600"
                  title="Stop Workflow"
                >
                  <Icon icon="lucide:square" class="w-4 h-4" />
                  Stop
                </button>
              </div>

              <!-- n8n-style Controls: Bottom Left HORIZONTAL -->
              <div class="absolute bottom-32 left-4 flex flex-row gap-2 z-50">
                <!-- Fit View Button -->
                <button 
                  @click="() => fitView({ duration: 600, padding: 0.15 })"
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
              </div>
              
              <!-- n8n-style Logs Section - ALWAYS VISIBLE -->
              <div class="absolute bottom-4 left-16 right-4 z-50">
                <!-- Logs Button (Always Visible) -->
                <button 
                  @click="showLogs = !showLogs"
                  class="bg-gray-800 border border-gray-600 text-white px-4 py-2 rounded-t-lg shadow-lg hover:bg-gray-700 transition-colors flex items-center gap-2"
                >
                  <span class="text-sm font-medium">Logs</span>
                  <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <svg class="w-4 h-4 text-gray-400 transition-transform" :class="{ 'rotate-180': showLogs }" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"/>
                  </svg>
                </button>
                
                <!-- Logs Panel (Expandable) -->
                <div 
                  v-if="showLogs"
                  class="bg-gray-800 border border-gray-600 border-t-0 rounded-b-lg shadow-lg"
                  style="max-height: 200px;"
                >
                  <!-- Logs Content -->
                  <div class="p-4 overflow-y-auto" style="max-height: 180px;">
                    <div v-if="executionLogs.length === 0" class="text-center py-6">
                      <p class="text-gray-400 text-sm">Nothing to display yet. Execute the workflow to see execution logs.</p>
                    </div>
                    <div v-else class="space-y-2">
                      <div 
                        v-for="(log, index) in executionLogs" 
                        :key="index"
                        class="flex items-start gap-3 text-sm"
                      >
                        <span class="text-gray-500 shrink-0 font-mono">{{ log.timestamp }}</span>
                        <span :class="getLogLevelClass(log.level)" class="shrink-0 min-w-[60px]">{{ log.level }}</span>
                        <span class="text-gray-200">{{ log.message }}</span>
                      </div>
                    </div>
                  </div>
                </div>
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
                    :class="`premium-handle-ai-main ${isHandleConnected(data.id, 'input-' + index) ? 'handle-connected' : 'handle-disconnected'}`"
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
                    :class="[
                      'premium-handle-ai-main',
                      isHandleConnected(data.id, 'output-' + index) ? 'handle-connected' : 'handle-disconnected'
                    ]"
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
                    :class="[
                      'premium-handle-ai-tool',
                      isHandleConnected(data.id, 'tool-' + index) ? 'handle-connected' : 'handle-disconnected'
                    ]"
                    :title="`AI Tool: ${nonMainConnection}`"
                  />
                  
                  <!-- AI Icon centered -->
                  <div class="premium-ai-icon">
                    <N8nIcon v-bind="getN8nIconProps(data.nodeType, data.label)" size="w-16 h-16" />
                  </div>
                  
                  <!-- AI Content -->
                  <div class="premium-ai-content">
                    <div class="premium-ai-name">{{ data.label }}</div>
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
                      :class="[
                        'premium-handle-trigger',
                        isHandleConnected(data.id, 'output-' + index) ? 'handle-connected' : 'handle-disconnected'
                      ]"
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
                      :class="[
                        'premium-handle-tool-bottom',
                        isHandleConnected(data.id, 'input-' + index) ? 'handle-connected' : 'handle-disconnected'
                      ]"
                    />
                    
                    <Handle 
                      v-for="(output, index) in data.outputs || ['main']"
                      :key="'output-' + index"
                      :id="'output-' + index" 
                      type="source" 
                      :position="Position.Top" 
                      :style="{ left: '50%', transform: 'translateX(-50%)' }"
                      :class="[
                        'premium-handle-tool-top',
                        isHandleConnected(data.id, 'output-' + index) ? 'handle-connected' : 'handle-disconnected'
                      ]"
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
                  
                  <!-- Main input from top (for agent connections) -->
                  <Handle 
                    v-for="(input, index) in (data.inputs || ['main']).filter(i => i === 'main')"
                    :key="'input-' + index"
                    :id="'input-' + index" 
                    type="target" 
                    :position="Position.Top" 
                    :style="{ left: '50%', transform: 'translateX(-50%)' }"
                    :class="[
                      'premium-handle-storage',
                      isHandleConnected(data.id, 'input-' + index) ? 'handle-connected' : 'handle-disconnected'
                    ]"
                  />
                  
                  <!-- Tool input from bottom (for embeddings connections) -->
                  <Handle 
                    v-for="(input, index) in (data.inputs || []).filter(i => i !== 'main')"
                    :key="'tool-input-' + index"
                    :id="'tool-' + index" 
                    type="target" 
                    :position="Position.Bottom" 
                    :style="{ left: '50%', transform: 'translateX(-50%)' }"
                    :class="[
                      'premium-handle-storage',
                      isHandleConnected(data.id, 'tool-' + index) ? 'handle-connected' : 'handle-disconnected'
                    ]"
                  />
                  
                  <!-- Vector stores have no output handles - they are storage endpoints -->
                  
                  <!-- Horizontal layout: icon LEFT + text RIGHT -->
                  <div style="display: flex; align-items: center; width: 100%; height: 100%; padding: 0 8px;">
                    <div style="width: 32px; height: 32px; margin-right: 10px; flex-shrink: 0;">
                      <N8nIcon v-bind="getN8nIconProps(data.nodeType, data.label)" size="w-8 h-8" />
                    </div>
                    <div style="color: #ffffff !important; font-size: 13px !important; font-weight: 600 !important; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8) !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; flex: 1;">{{ data.label }}</div>
                  </div>
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
                      :class="`premium-handle-process handle-disconnected`"
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
                      :class="`premium-handle-process handle-disconnected`"
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

      <TimelineModal
        v-if="selectedWorkflowId && showTimelineModal"
        :workflow-id="selectedWorkflowId"
        :tenant-id="tenantId"
        :show="showTimelineModal"
        @close="closeTimelineModal"
      />

      <!-- Executions Modal - Using DetailModal with Real API -->
      <DetailModal
        v-if="selectedWorkflowForModal"
        :show="showExecutionsModal"
        :title="`Process Executions: ${selectedWorkflowForModal.process_name}`"
        :subtitle="`ID: ${selectedWorkflowForModal.id}`"
        :header-icon="'lucide:play'"
        :tabs="executionTabs"
        default-tab="executions"
        :is-loading="executionData?.loading || false"
        :error="executionsError"
        :data="executionData"
        @close="closeExecutionsModal"
        @refresh="loadExecutionData"
        @retry="loadExecutionData"
      >
        <template #executions="{ data }">
          <div class="p-4">
            <div class="space-y-3">
              <h3 class="text-base font-semibold text-text">Recent Executions (Page {{ currentPage }}/{{ totalPages }})</h3>
              
              <!-- Recent Executions Info -->
              <div v-if="data?.executions?.length > 0" class="mb-2 text-xs text-text-muted">
                Showing the {{ data.executions.length }} most recent executions
              </div>
              
              <!-- Compact Executions Table -->
              <div v-if="paginatedExecutions.length > 0" class="border border-border rounded-lg overflow-hidden">
                <table class="w-full text-sm">
                  <thead class="bg-surface-hover border-b border-border">
                    <tr>
                      <th class="text-left px-3 py-2 text-text-muted font-medium">Status</th>
                      <th class="text-left px-3 py-2 text-text-muted font-medium">ID</th>
                      <th class="text-left px-3 py-2 text-text-muted font-medium">Started</th>
                      <th class="text-left px-3 py-2 text-text-muted font-medium">Duration</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr 
                      v-for="(exec, index) in paginatedExecutions" 
                      :key="exec.id || index"
                      class="border-b border-border/50 hover:bg-surface-hover/30"
                    >
                      <td class="px-3 py-2">
                        <div class="flex items-center gap-2">
                          <Icon v-if="exec.finished && !exec.error" icon="lucide:check-circle" class="h-4 w-4 text-green-400" />
                          <Icon v-else-if="exec.error" icon="lucide:x-circle" class="h-4 w-4 text-red-400" />
                          <Icon v-else icon="lucide:clock" class="h-4 w-4 text-yellow-400" />
                          <span :class="[
                            'text-xs font-medium',
                            exec.finished && !exec.error ? 'text-green-400' : 
                            exec.error ? 'text-red-400' : 'text-yellow-400'
                          ]">
                            {{ exec.finished && !exec.error ? 'Success' : 
                                exec.error ? 'Failed' : 'Running' }}
                          </span>
                        </div>
                      </td>
                      <td class="px-3 py-2 text-text-muted font-mono text-xs">
                        #{{ exec.id }}
                      </td>
                      <td class="px-3 py-2 text-text-muted text-xs">
                        {{ formatDate(exec.startedAt) }}
                      </td>
                      <td class="px-3 py-2 text-text-muted text-xs">
                        {{ formatDuration(exec.execution_time || 0) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              <!-- Pagination Controls -->
              <div v-if="data?.executions?.length > itemsPerPage" class="mt-4 flex items-center justify-between pt-4 border-t border-border">
                <div class="text-sm text-text-muted">
                  Showing {{ (currentPage - 1) * itemsPerPage + 1 }} - {{ Math.min(currentPage * itemsPerPage, data.executions.length) }} of {{ data.executions.length }}
                </div>
                <div class="flex items-center gap-2">
                  <button 
                    @click="currentPage = Math.max(1, currentPage - 1)"
                    :disabled="currentPage === 1"
                    class="px-3 py-1 text-xs bg-surface border border-border rounded hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  
                  <!-- Page Numbers -->
                  <div class="flex items-center gap-1">
                    <button
                      v-for="page in Math.min(5, totalPages)"
                      :key="page"
                      @click="currentPage = page"
                      class="w-8 h-8 text-xs rounded transition-colors"
                      :class="currentPage === page ? 'bg-primary text-white' : 'bg-surface border border-border hover:bg-surface-hover'"
                    >
                      {{ page }}
                    </button>
                    <span v-if="totalPages > 5" class="text-text-muted px-2">...</span>
                    <button
                      v-if="totalPages > 5"
                      @click="currentPage = totalPages"
                      class="w-8 h-8 text-xs rounded transition-colors"
                      :class="currentPage === totalPages ? 'bg-primary text-white' : 'bg-surface border border-border hover:bg-surface-hover'"
                    >
                      {{ totalPages }}
                    </button>
                  </div>
                  
                  <button 
                    @click="currentPage = Math.min(totalPages, currentPage + 1)"
                    :disabled="currentPage === totalPages"
                    class="px-3 py-1 text-xs bg-surface border border-border rounded hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
              
              <div v-else-if="!data?.executions?.length" class="text-center py-8">
                <Icon icon="lucide:play" class="w-12 h-12 text-text-muted mx-auto mb-4" />
                <p class="text-text-muted">No executions found for this process</p>
              </div>
            </div>
          </div>
        </template>

        <template #stats="{ data }">
          <div class="p-6">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div class="control-card p-4">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm text-text-muted">Total Executions</span>
                  <Icon icon="lucide:play" class="h-4 w-4 text-gray-600" />
                </div>
                <p class="text-lg font-bold text-text">{{ data?.totalExecutions || 0 }}</p>
              </div>
              
              <div class="control-card p-4">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm text-text-muted">Success Rate</span>
                  <Icon icon="lucide:check-circle" class="h-4 w-4 text-gray-600" />
                </div>
                <p class="text-lg font-bold text-green-400">
                  {{ data?.successRate ? `${data.successRate.toFixed(1)}%` : 'N/A' }}
                </p>
              </div>
              
              <div class="control-card p-4">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm text-text-muted">Avg Duration</span>
                  <Icon icon="lucide:clock" class="h-4 w-4 text-gray-600" />
                </div>
                <p class="text-lg font-bold text-text">
                  {{ formatDuration(data?.avgDuration || 0) }}
                </p>
              </div>
            </div>
          </div>
        </template>
      </DetailModal>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { VueFlow, useVueFlow, Position, Handle } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { Icon } from '@iconify/vue'
import MainLayout from '../components/layout/MainLayout.vue'
import WorkflowDetailModal from '../components/workflows/WorkflowDetailModal.vue'
import TimelineModal from '../components/common/TimelineModal.vue'
import DetailModal from '../components/common/DetailModal.vue'
import N8nIcon from '../components/N8nIcon.vue'
import { useUIStore } from '../stores/ui'
import { useAuthStore } from '../stores/auth'
import { useToast } from 'vue-toastification'
import { businessAPI, $fetch } from '../services/api-client'

// VueFlow styles
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

// Stores
const uiStore = useUIStore()
const authStore = useAuthStore()

// Computed property for role-based permissions
const isViewer = computed(() => authStore.user?.role === 'viewer')
const canExecute = computed(() => !isViewer.value)
const { success, error } = useToast()

// State
const isLoading = ref(false)
const tenantId = 'client_simulation_a'
const sidebarCollapsed = ref(false)
const showLogs = ref(false)
const executionLogs = ref([
  {
    timestamp: '23:32:15',
    level: 'INFO',
    message: 'Workflow execution started'
  },
  {
    timestamp: '23:32:16', 
    level: 'DEBUG',
    message: 'Processing node: Schedule Trigger'
  },
  {
    timestamp: '23:32:17',
    level: 'SUCCESS',
    message: 'AI Agent completed successfully'
  }
])

// Workflow data - ONLY REAL DATA
const realWorkflows = ref<any[]>([])
const analyticsData = ref<any>(null)
const workflowStats = ref<any>(null) // Statistiche specifiche del workflow selezionato
const selectedWorkflowId = ref('')
const selectedWorkflowData = ref<any>(null)
const workflowDetails = ref<any>(null)

// Abort controller to cancel previous requests
let currentWorkflowController: AbortController | null = null

// Modal state
const showDetailModal = ref(false)
const showTimelineModal = ref(false)
const showExecutionsModal = ref(false)
const selectedWorkflowForModal = ref<any>(null)

// Executions modal data - REAL API DATA
const executionsError = ref<string | null>(null)
const executionData = ref<any>(null)
const executionTabs = [
  { id: 'executions', label: 'Executions', icon: 'lucide:play' },
  { id: 'stats', label: 'Statistics', icon: 'lucide:trending-up' }
]

// Pagination for executions
const currentPage = ref(1)
const itemsPerPage = 20
const totalPages = computed(() => {
  if (!executionData.value?.executions) return 1
  return Math.ceil(executionData.value.executions.length / itemsPerPage)
})
const paginatedExecutions = computed(() => {
  if (!executionData.value?.executions) return []
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return executionData.value.executions.slice(start, end)
})

// Action buttons state

// VueFlow
const flowElements = ref([])
const { fitView, zoomIn: vueFlowZoomIn, zoomOut: vueFlowZoomOut, setViewport, getViewport } = useVueFlow()

// Computed
const totalWorkflows = computed(() => realWorkflows.value.length)
const activeWorkflows = computed(() => realWorkflows.value.filter(w => w.is_active).length)
const flowNodes = computed(() => flowElements.value.filter(el => !el.source))
const flowEdges = computed(() => {
  return flowElements.value.filter(el => el.source)
})

// Helper function to check if a handle is connected  
const isHandleConnected = (nodeId: string, handleId: string) => {
  return false // Always return false - hiding all handles as requested
}

// KPI Stats (REAL DATA FROM ANALYTICS API)
const totalExecutions = computed(() => {
  // Se abbiamo statistiche specifiche del workflow, usiamole
  if (workflowStats.value?.kpis?.totalExecutions !== undefined) {
    return workflowStats.value.kpis.totalExecutions
  }
  // Altrimenti usa i dati globali
  return analyticsData.value?.overview?.totalExecutions || 0
})
const failedExecutions = computed(() => {
  // Se abbiamo statistiche specifiche del workflow, usiamole
  if (workflowStats.value?.kpis?.failedExecutions !== undefined) {
    return workflowStats.value.kpis.failedExecutions
  }
  // Altrimenti calcola dai dati globali
  const total = totalExecutions.value
  const successRate = analyticsData.value?.overview?.successRate || 100
  return Math.round(total * (1 - successRate / 100))
})
const failureRate = computed(() => {
  // Se abbiamo statistiche specifiche del workflow, usiamole
  if (workflowStats.value?.kpis?.failureRate !== undefined) {
    return workflowStats.value.kpis.failureRate
  }
  // Altrimenti calcola dai dati globali
  const successRate = analyticsData.value?.overview?.successRate || 100
  return (100 - successRate).toFixed(1)
})
const timeSaved = computed(() => {
  // Se abbiamo statistiche specifiche del workflow, usiamole
  if (workflowStats.value?.kpis?.timeSavedHours !== undefined) {
    return workflowStats.value.kpis.timeSavedHours
  }
  // Altrimenti usa i dati globali
  return analyticsData.value?.businessImpact?.timeSavedHours || 0
})
const avgRunTime = computed(() => {
  // Se abbiamo statistiche specifiche del workflow, usiamole
  if (workflowStats.value?.kpis?.avgRunTime !== undefined) {
    const seconds = workflowStats.value.kpis.avgRunTime
    // Se meno di 1 secondo, mostra in secondi con 2 decimali
    if (seconds < 1) {
      return seconds.toFixed(2) + 's'
    }
    // Se meno di 60 secondi, mostra in secondi con 1 decimale
    if (seconds < 60) {
      return seconds.toFixed(1) + 's'
    }
    // Altrimenti mostra in minuti
    return (seconds / 60).toFixed(1) + 'm'
  }
  // Altrimenti calcola dai dati globali
  const avgSeconds = analyticsData.value?.overview?.avgDurationSeconds || 0
  return avgSeconds > 0 ? (avgSeconds / 60).toFixed(1) : '0.0'
})

// Methods - ALL USING REAL BACKEND DATA
const refreshAllData = async () => {
  isLoading.value = true
  
  // Salva l'ID selezionato prima del refresh
  const previousSelectedId = selectedWorkflowId.value
  
  try {
    console.log('🔄 Loading ALL REAL workflow data for Command Center...')
    
    // Get all workflows from backend with cache busting via URL param - OFETCH Migration
    const [workflowsData, analyticsResponse] = await Promise.all([
      businessAPI.getProcesses({ _t: Date.now(), refresh: true }),
      businessAPI.getAnalytics({ _t: Date.now() })
    ])
    console.log('✅ REAL workflows loaded:', workflowsData.data?.length || 0)
    console.log('📋 Raw data preview:', workflowsData.data?.slice(0, 3))
    
    realWorkflows.value = workflowsData.data || []
    console.log('🔄 Set realWorkflows to:', realWorkflows.value.length, 'items')
    
    // Get analytics data for KPI calculations - OFETCH handles response automatically
    analyticsData.value = analyticsResponse
    console.log('✅ REAL analytics loaded:', {
      totalExecutions: analyticsData.value.overview?.totalExecutions,
      successRate: analyticsData.value.overview?.successRate,
      avgDuration: analyticsData.value.overview?.avgDurationSeconds
    })
    
    // Manual selection only - NO AUTO-SELECTION of first workflow
    // This was causing the bug where clicking any workflow showed the same content
    console.log('✅ Workflows loaded, manual selection required')
    
    // Rimosso toast fastidioso - non serve notificare ogni caricamento
    
  } catch (error: any) {
    console.error('❌ Failed to fetch workflows:', error)
    console.error('🔍 Error details:', error.stack)
    
    // Try alternative method or show detailed error
    const errorMsg = error.message?.includes('fetch') 
      ? 'Cannot connect to backend server. Is it running on port 3001?' 
      : `API Error: ${error.message}`
    
    error('Errore di Connessione', errorMsg)
    
    // Set empty array as fallback
    realWorkflows.value = []
  } finally {
    isLoading.value = false
    
    // Dopo il refresh, riseleziona il workflow precedente o il primo disponibile
    if (realWorkflows.value.length > 0) {
      if (previousSelectedId) {
        // Prova a riselezionare il workflow precedente
        const previousWorkflow = realWorkflows.value.find(w => w.id === previousSelectedId)
        if (previousWorkflow) {
          console.log('🔄 Re-selecting previous workflow:', previousWorkflow.process_name)
          await selectWorkflow(previousWorkflow)
        } else {
          // Se non esiste più, seleziona il primo
          console.log('🎯 Previous workflow not found, selecting first:', realWorkflows.value[0].process_name)
          await selectWorkflow(realWorkflows.value[0])
        }
      } else {
        // Se non c'era selezione, seleziona il primo
        console.log('🎯 Auto-selecting first workflow after refresh:', realWorkflows.value[0].process_name)
        await selectWorkflow(realWorkflows.value[0])
      }
    }
  }
}

const selectWorkflow = async (workflow: any) => {
  console.log('🔘 [FORCE TEST] CLICK DETECTED - selectWorkflow called with:', {
    workflowName: workflow.process_name,
    workflowId: workflow.id,
    currentSelectedId: selectedWorkflowId.value
  })
  
  // Set selected workflow
  selectedWorkflowId.value = workflow.id
  selectedWorkflowData.value = workflow
  
  console.log('✅ Workflow selected:', workflow.name, 'ID:', workflow.id)
  
  // Load workflow statistics and structure in parallel
  await Promise.all([
    loadWorkflowStatistics(workflow.id),
    loadWorkflowStructure(workflow)
  ])
}

// Carica le statistiche specifiche del workflow
const loadWorkflowStatistics = async (workflowId: string) => {
  try {
    console.log('📊 Loading statistics for workflow:', workflowId)
    const response = await $fetch(`/api/business/workflow/${workflowId}/full-stats`, {
      params: { days: 30 }
    })
    
    workflowStats.value = response
    console.log('✅ Workflow stats loaded:', {
      totalExecutions: response.kpis?.totalExecutions,
      failureRate: response.kpis?.failureRate,
      avgRunTime: response.kpis?.avgRunTime
    })
  } catch (error) {
    console.error('❌ Error loading workflow statistics:', error)
    // In caso di errore, reset stats per usare i dati globali
    workflowStats.value = null
  }
}

const loadWorkflowStructure = async (workflow: any) => {
  try {
    // Cancel previous request if it exists
    if (currentWorkflowController) {
      console.log('🚫 Cancelling previous workflow request')
      currentWorkflowController.abort()
    }
    
    // Create new abort controller for this request
    currentWorkflowController = new AbortController()
    
    console.log('🔍 Loading REAL structure for:', workflow.process_name, 'with ID:', workflow.id)
    
    console.log('📡 Fetching details with OFETCH for workflow:', workflow.id)
    
    // Use OFETCH API client instead of direct fetch
    const data = await businessAPI.getProcessDetails(workflow.id)
    workflowDetails.value = data.data
    
    console.log('✅ REAL workflow structure loaded for', workflow.process_name, ':', data.data.nodeCount, 'nodes')
    
    // Create VueFlow from REAL data
    createFlowFromRealData(data.data, workflow)
    
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.log('🚫 Request cancelled for', workflow.process_name)
      return
    }
    
    console.error('❌ Failed to load workflow structure for', workflow.process_name, ':', error)
    console.error('🔄 Falling back to enhanced flow')
    createEnhancedFlow(workflow)
  }
  
  // Auto-fit is handled immediately by createFlowFromRealData/createEnhancedFlow
  console.log('✅ Workflow structure loading completed')
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
        type: (() => {
          const nodeType = getNodeTypeFromN8nType(step.nodeType, step.stepName)
          // DEBUG COMPLETED: Qdrant text now visible!
          return nodeType
        })(),
        nodeType: (() => {
          const nodeType = step.nodeType || 'unknown-node'
          return nodeType
        })(),
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
        // Use distributed handles for AI tools - always from bottom
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
      // Storage nodes: Agent connections to top, embeddings connections to bottom
      if (sourceNodeType === 'ai' && !isMainConnection) {
        // AI tool connections go to top (agent input)
        targetHandle = 'input-0'  // Top for agent connections
      } else if (sourceNodeType === 'tool' || flow.from.toLowerCase().includes('embedding')) {
        // Embeddings and tool nodes go to bottom
        targetHandle = 'tool-0'  // Bottom for embeddings connections
      } else {
        // Main connections and others go to top
        targetHandle = 'input-0'  // Top for main connections
      }
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
      type: 'default', // Bezier curves like n8n
      animated: workflowMetadata.is_active && isMainConnection,
      style: { 
        stroke: isMainConnection ? '#10b981' : isAIConnection ? '#667eea' : '#3b82f6', 
        strokeWidth: 1,
        strokeDasharray: isMainConnection ? 'none' : '8 4',
        opacity: isMainConnection ? 1 : 0.8
      },
      sourceHandle,
      targetHandle,
      className: isMainConnection ? 'main-edge' : 'secondary-edge'
    }
  })
  
  console.log('✅ Created nodes with handles:', nodes.map(n => `ID:${n.id} Label:${n.data.label} inputs=${JSON.stringify(n.data.inputs)} outputs=${JSON.stringify(n.data.outputs)}`))
  console.log('🔗 Created edges:', edges.map(e => `${e.source}->${e.target} (${e.sourceHandle}->${e.targetHandle})`))
  console.log('🔢 Nodes count:', nodes.length, 'Edges count:', edges.length)
  
  flowElements.value = [...nodes, ...edges]
  console.log('🎯 FlowElements final:', flowElements.value.length, 'elements')
  
  // Force proper fit - reset viewport then fit
  nextTick(() => {
    // Force reset viewport and zoom
    setViewport({ x: 0, y: 0, zoom: 0.5 })
    
    setTimeout(() => {
      fitView({ 
        duration: 0,  // Instant fit
        padding: 0.2   // More padding to ensure visibility
      })
      console.log('🎯 Forced fit applied with viewport reset')
    }, 50)
  })
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
      type: 'default',
      animated: workflow.is_active,
      style: { stroke: '#10b981', strokeWidth: 1 },
      sourceHandle: 'right',
      targetHandle: 'left'
    })
  }
  
  flowElements.value = [...nodes, ...edges]
  
  // Force proper fit for enhanced flow  
  nextTick(() => {
    // Force reset viewport and zoom
    setViewport({ x: 0, y: 0, zoom: 0.5 })
    
    setTimeout(() => {
      fitView({ 
        duration: 0,  // Instant fit
        padding: 0.2   // More padding to ensure visibility
      })
      console.log('🎯 Forced fit applied for enhanced flow')
    }, 50)
  })
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

const openExecutionsModal = async () => {
  if (selectedWorkflowData.value) {
    selectedWorkflowForModal.value = selectedWorkflowData.value
    
    // Carica i dati PRIMA di mostrare il modal per evitare ritardi
    // Mostra subito uno stato di loading nel modal
    executionData.value = {
      executions: [],
      totalExecutions: 0,
      successRate: 0,
      avgDuration: 0,
      loading: true
    }
    
    showExecutionsModal.value = true
    
    // Carica i dati immediatamente senza await per non bloccare l'UI
    loadExecutionData()
  }
}

const closeExecutionsModal = () => {
  showExecutionsModal.value = false
  selectedWorkflowForModal.value = null
  executionData.value = null
  executionsError.value = null
}

// Execute workflow manually
const isExecuting = ref(false)
const currentExecutionId = ref<string | null>(null)
const executeWorkflow = async () => {
  if (!selectedWorkflowData.value || !selectedWorkflowId.value) {
    error('Nessun Workflow', 'Seleziona un workflow da eseguire')
    return
  }
  
  if (isExecuting.value) return // Prevent double clicks
  
  const workflowName = selectedWorkflowData.value.process_name || 'Unknown'
  isExecuting.value = true
  
  try {
    console.log(`🚀 Executing workflow ${selectedWorkflowId.value}...`)
    
    // API call to execute workflow - OFETCH Migration
    const result = await businessAPI.executeWorkflow(selectedWorkflowId.value)
    console.log('✅ Workflow execution result:', result)
    
    if (result.success && result.data.executionStarted) {
      // Store execution ID for stop functionality
      currentExecutionId.value = result.data.executionId
      
      success(
        'Esecuzione Avviata',
        `Il workflow "${workflowName}" è stato avviato. Controllo stato...`
      )
      
      // Start polling execution status
      let pollCount = 0
      const maxPolls = 30 // Max 30 secondi
      
      const pollInterval = setInterval(async () => {
        pollCount++
        
        try {
          const statusResult = await businessAPI.getExecutionStatus(result.data.executionId)
          
          if (statusResult.success && statusResult.data.isFinished) {
            clearInterval(pollInterval)
            isExecuting.value = false
            currentExecutionId.value = null
            
            if (statusResult.data.status === 'success') {
              success(
                'Esecuzione Completata',
                `Il workflow "${workflowName}" è stato eseguito con successo in ${Math.round(statusResult.data.duration / 1000)}s`
              )
            } else if (statusResult.data.status === 'error' && statusResult.data.errorInfo) {
              // Mostra errori specifici di n8n
              const errorDetails = statusResult.data.errorInfo.errors.map(e => 
                `${e.nodeName}: ${e.error.message}`
              ).join('\n')
              
              error(
                'Esecuzione Fallita',
                `Il workflow "${workflowName}" ha riscontrato errori:\n${errorDetails}`
              )
            } else {
              error(
                'Esecuzione Interrotta',
                `Il workflow "${workflowName}" è stato interrotto`
              )
            }
            
            // Ricarica dati
            fetchRealWorkflows()
            if (selectedWorkflowId.value) {
              loadWorkflowStatistics(selectedWorkflowId.value)
            }
          }
          
          // Stop polling after max time
          if (pollCount >= maxPolls) {
            clearInterval(pollInterval)
            isExecuting.value = false
            currentExecutionId.value = null
            
            success(
              'Esecuzione in Corso',
              `Il workflow "${workflowName}" è ancora in esecuzione dopo 30s`
            )
          }
        } catch (err) {
          console.error('Error polling execution status:', err)
        }
      }, 1000) // Poll ogni secondo
    } else {
      // Execution failed
      isExecuting.value = false
      currentExecutionId.value = null
      
      error(
        'Esecuzione Fallita',
        result.data?.n8nApiResult?.error || `Impossibile eseguire il workflow "${workflowName}"`
      )
    }
    
  } catch (error: any) {
    console.error('❌ Failed to execute workflow:', error)
    
    // Reset state on error
    isExecuting.value = false
    currentExecutionId.value = null
    
    error(
      'Errore di Esecuzione',
      `Impossibile eseguire il workflow "${workflowName}". ${error.message}`
    )
  }
}

// Stop workflow execution
const stopWorkflow = async () => {
  if (!selectedWorkflowId.value || !currentExecutionId.value) {
    error('Errore Stop', 'Nessuna esecuzione da fermare')
    return
  }
  
  const workflowName = selectedWorkflowData.value?.process_name || 'Unknown'
  
  try {
    console.log(`🛑 Stopping workflow ${selectedWorkflowId.value}, execution ${currentExecutionId.value}...`)
    
    // API call to stop workflow - OFETCH Migration
    const result = await businessAPI.stopWorkflow(selectedWorkflowId.value)
    console.log('✅ Workflow stop result:', result)
    
    if (result.success) {
      success(
        'Esecuzione Fermata',
        `Il workflow "${workflowName}" è stato fermato con successo`
      )
    } else {
      error(
        'Errore Stop',
        result.data?.n8nApiResult?.error || `Impossibile fermare il workflow "${workflowName}"`
      )
    }
    
  } catch (error: any) {
    console.error('❌ Failed to stop workflow:', error)
    
    error(
      'Errore di Stop',
      `Impossibile fermare il workflow "${workflowName}". ${error.message}`
    )
  } finally {
    // Reset execution state
    isExecuting.value = false
    currentExecutionId.value = null
  }
}

// Toggle workflow active status
const toggleWorkflowStatus = async () => {
  console.log('🚀 toggleWorkflowStatus called!')
  console.log('📊 selectedWorkflowData:', selectedWorkflowData.value)
  console.log('📊 selectedWorkflowId:', selectedWorkflowId.value)
  
  if (!selectedWorkflowData.value || !selectedWorkflowId.value) {
    console.log('❌ No workflow selected for toggle - EARLY RETURN')
    return
  }
  
  console.log('📊 Current workflow data:', selectedWorkflowData.value)
  
  const currentStatus = selectedWorkflowData.value.is_active || false
  const newStatus = !currentStatus
  
  console.log(`🔄 Will toggle workflow ${selectedWorkflowId.value} from ${currentStatus} to ${newStatus}`)
  
  try {    
    // Optimistic update
    console.log('🔄 Doing optimistic update...')
    selectedWorkflowData.value.is_active = newStatus
    
    // Update in workflows list  
    const workflowIndex = realWorkflows.value.findIndex(w => w.id === selectedWorkflowId.value)
    if (workflowIndex !== -1) {
      realWorkflows.value[workflowIndex].is_active = newStatus
      console.log('✅ Updated workflow in list')
    }
    
    // API call to backend - OFETCH Migration - passa il nuovo stato
    const result = await businessAPI.toggleWorkflow(selectedWorkflowId.value, newStatus)
    console.log('✅ Workflow status updated:', result)
    
    // Show appropriate success message
    if (result.success) {
      // Se c'è un errore con n8n ma il database è stato aggiornato
      if (result.data?.n8nApiResult?.error) {
        success(
          `Workflow ${newStatus ? 'Attivato' : 'Disattivato'}`,
          `${result.data.workflowName} è stato ${newStatus ? 'attivato' : 'disattivato'} localmente`
        )
      } else {
        success(
          `Workflow ${newStatus ? 'Attivato' : 'Disattivato'}`,
          `${result.data.workflowName} è stato ${newStatus ? 'attivato' : 'disattivato'} con successo`
        )
      }
    } else {
      error(
        'Errore Attivazione',
        'Impossibile aggiornare lo stato del workflow'
      )
    }
    
  } catch (error: any) {
    console.error('❌ Failed to toggle workflow:', error)
    
    // Revert optimistic update
    selectedWorkflowData.value.is_active = currentStatus
    const workflowIndex = realWorkflows.value.findIndex(w => w.id === selectedWorkflowId.value)
    if (workflowIndex !== -1) {
      realWorkflows.value[workflowIndex].is_active = currentStatus
    }
    
    error(
      'Errore di Attivazione',
      `Impossibile ${newStatus ? 'attivare' : 'disattivare'} il workflow. ${error.message}`
    )
  }
}

// Load real execution data from API
const loadExecutionData = async () => {
  if (!selectedWorkflowForModal.value?.id) return
  
  executionsError.value = null
  currentPage.value = 1 // Reset to first page
  
  const startTime = performance.now()
  
  try {
    console.log('🔄 Loading executions for workflow:', selectedWorkflowForModal.value.id)
    
    // API call - VELOCE: solo 50 esecuzioni più recenti
    const data = await businessAPI.getProcessExecutionsForWorkflow(
      selectedWorkflowForModal.value.id
    )
    
    const loadTime = performance.now() - startTime
    console.log(`✅ Executions loaded in ${loadTime.toFixed(0)}ms:`, data.data)
    
    // Store all data (pagination will handle display)
    executionData.value = {
      ...data.data,
      loading: false
    }
    
  } catch (err: any) {
    console.error('❌ Failed to load executions:', err)
    executionsError.value = err.message
    executionData.value = {
      executions: [],
      totalExecutions: 0,
      successRate: 0,
      avgDuration: 0,
      loading: false
    }
  }
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
  // REGOLA INDEROGABILE: TUTTO QUADRATO tranne specifiche eccezioni
  
  // 1. AI Agent LangChain → RETTANGOLO AI
  if (n8nType === '@n8n/n8n-nodes-langchain.agent') {
    return 'ai'
  }
  
  // 2. Vector Store → PILLOLA (storage CSS class) 
  if (n8nType.includes('vectorstore') || n8nType.includes('vectorStore')) {
    return 'storage'
  }
  
  // 3. OpenAI CHAT/EMBEDDINGS → CERCHIO (AI processing)
  if (n8nType.includes('@n8n/n8n-nodes-langchain.lmChat') ||
      n8nType.includes('@n8n/n8n-nodes-langchain.embeddings')) {
    return 'tool'  // OpenAI Chat/Embeddings sono TONDI!
  }
  
  // 4. OpenAI AUDIO/IMAGE TOOLS → QUADRATO (media processing)
  if (n8nType.includes('@n8n/n8n-nodes-langchain.openAi')) {
    return 'agent'  // OpenAI audio/image tools sono QUADRATI!
  }
  
  // 5. ALTRI TOOLS → CERCHIO (LangChain + base tools)
  if (n8nType.includes('@n8n/n8n-nodes-langchain.tool') || 
      n8nType.includes('@n8n/n8n-nodes-langchain.memory') ||
      n8nType.includes('@n8n/n8n-nodes-langchain.output') ||
      n8nType.includes('@n8n/n8n-nodes-langchain.reranker') ||
      n8nType.includes('@n8n/n8n-nodes-langchain.retriever') ||
      n8nType === 'n8n-nodes-base.dateTimeTool') {
    return 'tool'  // TUTTI gli altri tool sono tondi!
  }
  
  // 6. Trigger → QUADRATO con lato sx tondo smussato  
  if (n8nType.toLowerCase().includes('trigger')) {
    return 'trigger'
  }
  
  // 5. TUTTO IL RESTO → QUADRATO (incluso OpenAI, HTTP Request, Code, Function, etc.)
  return 'process'
}

// Keep old function for fallback when n8n type not available
const getNodeType = (nodeName: string, businessCategory: string) => {
  // Special case: AI Agent nodes are always 'ai'  
  if (nodeName.toLowerCase().includes('agent') || nodeName.toLowerCase().includes('assistente')) {
    return 'ai'
  }
  
  // Check if it's a trigger first (takes precedence)
  if (isScheduleTrigger(nodeName)) {
    return 'trigger'
  }
  
  // REGOLA INDEROGABILE: TUTTO QUADRATO - non più controllo isToolNode()
  // Tutti i nodi normali diventano quadrati
  return 'process'
}

// Get n8n icon component props for a node type
const getN8nIconProps = (nodeType: string, nodeName: string = '') => {
  // Handle undefined/empty nodeType
  if (!nodeType || nodeType === 'undefined' || nodeType === 'null') {
    return {
      nodeType: '',
      fallback: 'Settings',
      size: 'w-5 h-5'
    }
  }
  
  // OVERRIDE BASATO SUL NOME DEL NODO (priorità massima)
  if (nodeName.toUpperCase().includes('UPSERT') && nodeName.toUpperCase().includes('SUPABASE')) {
    return {
      nodeType: 'UPSERT_SUPABASE_OVERRIDE', // Key speciale per PostgreSQL
      fallback: 'Database',
      size: 'w-5 h-5'
    }
  }
  
  if (nodeName.toUpperCase().includes('CALCULATOR')) {
    return {
      nodeType: 'CALCULATOR_TOOL_OVERRIDE', // Key speciale per calculator
      fallback: 'Calculator',
      size: 'w-5 h-5'
    }
  }
  
  if (nodeName.toUpperCase().includes('MCP') && !nodeName.toUpperCase().includes('SUPABASE')) {
    return {
      nodeType: 'MCP_CLIENT_OVERRIDE', // Key speciale per MCP
      fallback: 'Zap',
      size: 'w-5 h-5'
    }
  }
  
  // FORCE FIX for SET nodes
  if (nodeType === 'n8n-nodes-base.set') {
    return {
      nodeType: 'n8n-nodes-base.set',
      fallback: 'Edit', // Matita come n8n originale
      size: 'w-5 h-5'
    }
  }
  
  // Return object with nodeType and fallback icon
  const props = {
    nodeType: nodeType,
    fallback: 'Settings', // Default fallback
    size: 'w-5 h-5'
  }
  
  // Set specific fallbacks based on node type patterns
  if (nodeType?.includes('code')) props.fallback = 'Code'
  else if (nodeType?.includes('httpRequest') || nodeName.toLowerCase().includes('scarica')) props.fallback = 'Globe'
  else if (nodeType?.includes('function')) props.fallback = 'Zap'
  else if (nodeType?.includes('webhook')) props.fallback = 'Link'
  else if (nodeType?.includes('email') || nodeType?.includes('outlook') || nodeType?.includes('gmail')) props.fallback = 'Mail'
  else if (nodeType?.includes('googleDrive') || nodeType?.includes('file')) props.fallback = 'FileText'
  else if (nodeType?.includes('scheduleTrigger') || nodeType?.includes('intervalTrigger') || nodeType?.includes('cronTrigger')) props.fallback = 'Clock'
  else if (nodeType?.includes('executeWorkflowTrigger')) props.fallback = 'GitBranch'  // Force a different fallback
  else if (nodeType?.includes('manualTrigger')) props.fallback = 'PlayCircle'  // FORCE PlayCircle for manual trigger
  else if (nodeType?.includes('trigger')) props.fallback = 'Play'
  else if (nodeType?.includes('agent')) props.fallback = 'Bot'
  else if (nodeType?.includes('database') || nodeType?.includes('supabase') || nodeType?.includes('vectorStore')) props.fallback = 'Database'
  else if (nodeType?.includes('telegram')) props.fallback = 'MessageSquare'
  
  return props
}

const getNodeIcon = (nodeType: string, nodeName: string = '') => {
  // First check by nodeType for specific icons
  if (nodeType?.includes('code')) return Code
  if (nodeType?.includes('httpRequest') || nodeName.toLowerCase().includes('scarica')) return 'lucide:globe'
  if (nodeType?.includes('function')) return 'lucide:zap'
  if (nodeType?.includes('webhook')) return 'lucide:link'
  if (nodeType?.includes('email') || nodeType?.includes('outlook') || nodeType?.includes('gmail')) return 'lucide:mail'
  if (nodeType?.includes('googleDrive') || nodeType?.includes('file')) return 'lucide:file-text'
  
  // Trigger icons - specific first, then generic
  if (nodeType?.includes('scheduleTrigger') || nodeType?.includes('intervalTrigger') || nodeType?.includes('cronTrigger')) return 'lucide:clock'
  if (nodeType?.includes('trigger')) return 'lucide:play'
  
  if (nodeType?.includes('agent')) return 'lucide:bot'
  if (nodeType?.includes('database') || nodeType?.includes('supabase') || nodeType?.includes('vectorStore')) return 'lucide:database'
  
  // Fallback to general type
  if (typeof nodeType === 'string') {
    if (nodeType === 'trigger') return 'lucide:play'
    if (nodeType === 'ai') return 'lucide:bot'
    if (nodeType === 'storage') return 'lucide:database'
    if (nodeType === 'tool') return 'lucide:cpu'
  }
  
  // Default
  return 'lucide:settings'
}

const getHandleType = (connectionType: string) => {
  if (connectionType.includes('ai_')) return 'ai'
  if (connectionType.includes('memory')) return 'memory'
  if (connectionType.includes('tool')) return 'tool'
  if (connectionType.includes('language')) return 'language'
  return 'main'
}

const getLogLevelClass = (level: string) => {
  switch (level) {
    case 'SUCCESS': return 'text-green-400 font-semibold'
    case 'INFO': return 'text-blue-400 font-semibold'
    case 'DEBUG': return 'text-gray-400 font-semibold'
    case 'WARN': return 'text-yellow-400 font-semibold'
    case 'ERROR': return 'text-red-400 font-semibold'
    default: return 'text-gray-400 font-semibold'
  }
}

// Debug watchers
watch(selectedWorkflowData, (newData, oldData) => {
  console.log('🔍 [DEBUG] selectedWorkflowData changed:', {
    newData: newData?.process_name,
    oldData: oldData?.process_name,
    newId: newData?.id,
    oldId: oldData?.id,
    stackTrace: new Error().stack?.split('\n')[2]?.trim()
  })
})

// Lifecycle
onMounted(async () => {
  console.log('🚀 WorkflowCommandCenter mounted, loading data...')
  try {
    await refreshAllData()
    console.log('📊 Final state:', { 
      workflows: realWorkflows.value.length, 
      totalExecutions: totalExecutions.value,
      activeWorkflows: activeWorkflows.value 
    })
    
    // Seleziona automaticamente il primo workflow se presente
    if (realWorkflows.value.length > 0 && !selectedWorkflowId.value) {
      console.log('🎯 Auto-selecting first workflow:', realWorkflows.value[0].process_name)
      await selectWorkflow(realWorkflows.value[0])
    }
  } catch (error) {
    console.error('❌ ERROR in onMounted:', error)
    console.error('❌ Error stack:', error.stack)
    // Forza un reload alternativo
    try {
      console.log('🔄 Trying alternative data load...')
      const workflowsData = await businessAPI.getProcesses({ _t: Date.now() })
      console.log('🔧 Alternative data:', workflowsData)
      realWorkflows.value = workflowsData.data || []
      console.log('🔧 Alternative workflows set:', realWorkflows.value.length)
      
      // Seleziona automaticamente il primo workflow anche nel fallback
      if (realWorkflows.value.length > 0 && !selectedWorkflowId.value) {
        console.log('🎯 Auto-selecting first workflow (fallback):', realWorkflows.value[0].process_name)
        await selectWorkflow(realWorkflows.value[0])
      }
    } catch (altError) {
      console.error('❌ Alternative load also failed:', altError)
    }
  }
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
  background: #1f2937;
  border: 0.5px solid #10b981;
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
  transform-style: preserve-3d;
}

:deep(.premium-ai-node:hover) {
  transform: translateY(-4px) rotateX(5deg);
  box-shadow: 
    0 16px 48px rgba(74, 85, 104, 0.4),
    0 0 24px rgba(45, 55, 72, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

:deep(.premium-ai-active) {
  animation: aiPulse 2s ease-in-out infinite;
}

:deep(.premium-ai-icon) {
  position: relative;
  color: white;
  margin-bottom: 0px;
  display: flex;
  align-items: center;
  justify-content: center;
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
  background: #1f2937;
  border: 0.5px solid #10b981;
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
  background: #1f2937;
  border: 0.5px solid #10b981;
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
  background: #1f2937;
  border-color: rgba(16, 185, 129, 0.4);
}

:deep(.premium-trigger-inactive) {
  background: #1f2937;
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
  background: #1f2937 !important;
  border: 0.5px solid #10b981 !important;
  border-radius: 50px !important; /* Perfect pill shape - half of height */
  width: 280px !important;
  height: 100px !important;
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
  font-size: 14px;
  font-weight: 600;
  color: #ffffff !important; /* BIANCO VISIBILE */
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8) !important; /* OMBRA FORTE */
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
  background: #1f2937;
  border: 0.5px solid #10b981;
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

/* Main flow handles (left/right) - VISIBLE */
:deep(.premium-handle-ai-main) {
  width: 8px !important;
  height: 8px !important;
  background: #ffffff !important;
  border: 1px solid rgba(200, 200, 200, 0.8) !important;
  border-radius: 50% !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  transition: all 0.3s ease !important;
  opacity: 1 !important;
  z-index: 10 !important;
}

:deep(.premium-handle-ai-main:hover) {
  opacity: 1 !important;
  transform: scale(1.2) !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

/* AI Tool handles (bottom) - VISIBLE */
:deep(.premium-handle-ai-tool) {
  width: 8px !important;
  height: 8px !important;
  background: #a855f7 !important;
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  border-radius: 50% !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  transition: all 0.3s ease !important;
  opacity: 1 !important;
  z-index: 10 !important;
}

:deep(.premium-handle-ai-tool:hover) {
  opacity: 1 !important;
  transform: scale(1.2) !important;
  box-shadow: 0 2px 4px rgba(168, 85, 247, 0.4) !important;
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
  width: 8px !important;
  height: 8px !important;
  background: #ffffff !important;
  border: 1px solid rgba(200, 200, 200, 0.8) !important;
  border-radius: 50% !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  transition: all 0.3s ease !important;
  opacity: 1 !important;
  z-index: 15 !important;
  top: -7px !important;
}

:deep(.premium-handle-tool-top:hover) {
  opacity: 1 !important;
  transform: translateX(-50%) scale(1.2) !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

:deep(.premium-handle-tool-bottom) {
  width: 8px !important;
  height: 8px !important;
  background: #ffffff !important;
  border: 1px solid rgba(200, 200, 200, 0.8) !important;
  border-radius: 50% !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  transition: all 0.3s ease !important;
  opacity: 1 !important;
  z-index: 15 !important;
}

:deep(.premium-handle-tool-bottom:hover) {
  opacity: 1 !important;
  transform: translateX(-50%) scale(1.2) !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

:deep(.premium-handle-storage) {
  width: 8px !important;
  height: 8px !important;
  background: #3b82f6 !important;
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  border-radius: 50% !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  transition: all 0.3s ease !important;
  opacity: 1 !important;
}

:deep(.premium-handle-storage:hover) {
  opacity: 1 !important;
  transform: scale(1.2) !important;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.4) !important;
}

:deep(.premium-handle-process) {
  width: 8px !important;
  height: 8px !important;
  background: #ffffff !important;
  border: 1px solid rgba(200, 200, 200, 0.8) !important;
  border-radius: 50% !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  transition: all 0.3s ease !important;
  opacity: 1 !important;
}

:deep(.premium-handle-process:hover) {
  opacity: 1 !important;
  transform: scale(1.2) !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

/* Handle visibility: show only connected handles */
:deep(.handle-connected) {
  opacity: 1 !important;
}

:deep(.handle-disconnected) {
  opacity: 0 !important;
}

/* All handles with connection point indicators */

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
  stroke-width: 1px !important;
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
  stroke-width: 1px !important;
  opacity: 0.8 !important;
  transition: all 0.3s ease !important;
  stroke-linecap: round !important;
  stroke-linejoin: round !important;
}

:deep(.secondary-edge:hover .vue-flow__edge-path) {
  opacity: 1 !important;
  stroke-width: 1px !important;
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
  font-size: 11px;
  font-weight: 500;
  color: #ffffff;
  text-align: center;
  margin-top: 6px;
  padding: 4px 8px;
  max-width: 140px;
  line-height: 1.3;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
  background: none;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
}
</style>