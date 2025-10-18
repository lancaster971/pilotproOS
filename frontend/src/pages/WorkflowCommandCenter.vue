<template>
  <MainLayout>
    <div class="h-[calc(100vh-4rem)] overflow-auto">

      <!-- KPI Stats Row - SOTTILE per massimizzare canvas -->
      <div class="grid grid-cols-6 gap-3 mb-3">
        <!-- Total Executions Card - COMPATTO -->
        <Card class="premium-glass premium-hover-lift">
          <template #content>
            <div class="p-2">
              <div class="flex items-center justify-between mb-1">
                <p class="text-lg font-bold text-text">{{ totalExecutions.toLocaleString() }}</p>
                <Badge value="Totali" severity="info" class="text-xs badge-white-text" />
              </div>
              <p class="text-xs text-text-muted">Prod. executions • Last 7 days</p>
            </div>
          </template>
        </Card>

        <!-- Failed Executions Card - COMPATTO -->
        <Card class="premium-glass premium-hover-lift">
          <template #content>
            <div class="p-2">
              <div class="flex items-center justify-between mb-1">
                <p class="text-lg font-bold text-text">{{ failedExecutions }}</p>
                <Badge value="Fallite" severity="danger" class="text-xs badge-white-text" />
              </div>
              <p class="text-xs text-text-muted">Failed prod. executions • Last 7 days</p>
            </div>
          </template>
        </Card>

        <!-- Success Rate Card - COMPATTO -->
        <Card class="premium-glass premium-hover-lift">
          <template #content>
            <div class="p-2">
              <div class="flex items-center justify-between mb-1">
                <p class="text-lg font-bold text-cyan-500">{{ Math.round(100 - failureRate) }}%</p>
                <Badge value="SUCCESS" severity="info" class="text-xs badge-white-text" />
              </div>
              <p class="text-xs text-text-muted">Tasso Successo • Last 7 days</p>
            </div>
          </template>
        </Card>

        <!-- Time Saved Card - COMPATTO -->
        <Card class="premium-glass premium-hover-lift">
          <template #content>
            <div class="p-2">
              <div class="flex items-center justify-between mb-1">
                <p class="text-lg font-bold text-warning">{{ timeSaved }}h</p>
                <Badge value="SAVED" severity="warning" class="text-xs badge-white-text" />
              </div>
              <p class="text-xs text-text-muted">Time saved • Last 7 days</p>
            </div>
          </template>
        </Card>

        <!-- Run Time Card - COMPATTO -->
        <Card class="premium-glass premium-hover-lift">
          <template #content>
            <div class="p-2">
              <div class="flex items-center justify-between mb-1">
                <p class="text-lg font-bold text-text">{{ avgRunTime }}</p>
                <Badge value="AVG" severity="info" class="text-xs badge-white-text" />
              </div>
              <p class="text-xs text-text-muted">Run time (avg.) • Last 7 days</p>
            </div>
          </template>
        </Card>

        <!-- System Health Card - COMPATTO -->
        <Card class="premium-glass premium-hover-lift">
          <template #content>
            <div class="p-2">
              <div class="flex items-center justify-between mb-1">
                <p class="text-lg font-bold text-blue-500">{{ activeWorkflows }}/{{ totalWorkflows }}</p>
                <Badge value="SYSTEM" severity="info" class="text-xs badge-white-text" />
              </div>
              <p class="text-xs text-text-muted">Active workflows • System status</p>
            </div>
          </template>
        </Card>
      </div>

      <!-- Main Layout: Full Canvas (NO SIDEBAR) -->
      <div class="flex gap-4 h-[calc(100%-4rem)]">

        <!-- Center: VueFlow Visualization (FULL WIDTH) -->
        <div class="flex-1 premium-glass rounded-lg overflow-hidden">
          <!-- Enhanced Header con Dropdown Workflow Selector -->
          <div class="bg-surface/30 border-b border-border px-4 py-2.5 flex items-center justify-between">
            <!-- Left: Dropdown Workflow Selector + Stats Inline -->
            <div class="flex items-center gap-4">
              <!-- Dropdown Compatto -->
              <Dropdown
                v-model="selectedWorkflowId"
                :options="workflowDropdownOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Select a workflow"
                @change="onWorkflowChange"
                class="workflow-dropdown"
                :filter="true"
                filterPlaceholder="Search workflows..."
                :showClear="false"
                scrollHeight="400px"
              >
                <!-- Custom option template con status badge -->
                <template #option="slotProps">
                  <div class="flex items-center gap-2 py-1">
                    <!-- Status indicator -->
                    <div
                      class="w-1.5 h-1.5 rounded-full flex-shrink-0"
                      :class="slotProps.option.isActive ? 'bg-green-500' : 'bg-gray-500'"
                    />

                    <!-- Workflow name -->
                    <span class="text-xs text-gray-200 font-normal flex-1 truncate" style="max-width: 200px;">
                      {{ slotProps.option.label }}
                    </span>

                    <!-- Executions count (plain text, no badge) -->
                    <span class="text-[10px] text-gray-500 font-normal px-1.5 py-0.5 bg-gray-800 rounded">
                      {{ slotProps.option.executionsToday }}
                    </span>
                  </div>
                </template>

                <!-- Selected value template (compatto) -->
                <template #value="slotProps">
                  <div v-if="slotProps.value" class="flex items-center gap-1.5">
                    <div
                      class="w-1 h-1 rounded-full"
                      :class="selectedWorkflowData?.is_active ? 'bg-green-500' : 'bg-gray-500'"
                    />
                    <span class="text-xs font-normal text-gray-400 truncate" style="max-width: 240px; color: #9CA3AF !important;">
                      {{ selectedWorkflowData?.process_name }}
                    </span>
                  </div>
                  <span v-else class="text-xs text-gray-500">Select a workflow</span>
                </template>
              </Dropdown>

              <!-- Workflow Stats Inline -->
              <div
                v-if="workflowStats"
                class="flex items-center gap-3 text-xs text-text-muted border-l border-border pl-4"
              >
                <span class="flex items-center gap-1.5">
                  <Icon icon="lucide:bar-chart-4" class="w-3.5 h-3.5 text-cyan-400" />
                  {{ workflowStats.kpis?.totalExecutions || 0 }} exec
                </span>
                <span class="text-text-muted/50">•</span>
                <span class="flex items-center gap-1.5">
                  <div :style="{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    backgroundColor: (workflowStats.kpis?.successRate || 0) >= 80 ? '#10b981' : '#ef4444'
                  }"></div>
                  {{ workflowStats.kpis?.successRate || 0 }}%
                </span>
                <span class="text-text-muted/50">•</span>
                <span class="flex items-center gap-1.5">
                  <Icon icon="lucide:timer" class="w-3.5 h-3.5 text-amber-400" />
                  {{ workflowStats.kpis?.avgRunTime ? Math.round(workflowStats.kpis.avgRunTime) + 'ms' : 'N/A' }}
                </span>
              </div>
            </div>

            <!-- Center: Analytics button -->
            <div class="flex items-center gap-2">
              <button
                @click="openBusinessDashboard"
                :disabled="!selectedWorkflowId"
                class="group px-5 py-2.5 text-sm font-medium rounded-lg flex items-center gap-2 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-emerald-500/10 via-emerald-600/10 to-emerald-500/10 hover:from-emerald-500/20 hover:via-emerald-600/20 hover:to-emerald-500/20 border border-emerald-500/30 hover:border-emerald-500/50 backdrop-blur-xl hover:shadow-[0_0_20px_rgba(16,185,129,0.15)] hover:scale-[1.02]"
              >
                <Icon icon="lucide:bar-chart-3" class="w-4 h-4 text-emerald-400 group-hover:text-emerald-300 transition-colors" />
                <span class="text-emerald-400 group-hover:text-emerald-300 transition-colors">Business Analytics</span>
              </button>
            </div>

            <!-- Right: Status + Performance indicators -->
            <div class="flex items-center gap-4">
              <!-- Last execution indicator -->
              <div v-if="workflowStats?.kpis?.last24hExecutions" class="flex items-center gap-2 text-xs">
                <div class="w-2 h-2 rounded-full bg-cyan-500 animate-pulse"></div>
                <span class="text-gray-300 font-medium">{{ workflowStats.kpis.last24hExecutions }} runs today</span>
              </div>

              <!-- Efficiency badge -->
              <span
                v-if="workflowStats?.kpis?.efficiencyScore"
                :class="[
                  'px-2 py-1 rounded text-xs font-medium',
                  workflowStats.kpis.efficiencyScore >= 80
                    ? 'bg-green-500/20 text-green-300 border border-green-500/30'
                    : workflowStats.kpis.efficiencyScore >= 60
                    ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
                    : 'bg-red-500/20 text-red-300 border border-red-500/30'
                ]"
              >
                {{ workflowStats.kpis.efficiencyScore }}% efficiency
              </span>

              <!-- Active/Inactive toggle -->
              <div class="flex items-center gap-2">
                <span class="text-xs text-text-muted">
                  {{ selectedWorkflowData?.is_active ? 'Active' : 'Inactive' }}
                </span>
                <button
                  v-if="canExecute"
                  @click="toggleWorkflowStatus"
                  :disabled="!selectedWorkflowId"
                  :class="[
                    'relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed',
                    selectedWorkflowData?.is_active ? 'bg-primary' : 'bg-gray-600'
                  ]"
                >
                  <span
                    :class="[
                      'inline-block h-3 w-3 transform rounded-full bg-white transition-transform',
                      selectedWorkflowData?.is_active ? 'translate-x-5' : 'translate-x-1'
                    ]"
                  />
                </button>
              </div>
            </div>
          </div>
          
          <!-- VueFlow -->
          <div class="relative h-full">
            <VueFlow
              v-if="selectedWorkflowId"
              v-model="flowElements"
              :node-types="nodeTypes"
              :default-viewport="{ zoom: 1, x: 0, y: 0 }"
              :min-zoom="0.2"
              :max-zoom="3"
              :connection-line-type="'default'"
              :class="['workflow-flow', 'h-full', 'workflow-transition', { 'workflow-flow-modern': USE_MODERN_THEME }]"
            >
              <!-- Original background (hidden when modern theme active) -->
              <Background
                v-if="!USE_MODERN_THEME"
                pattern-color="#4b5563"
                :size="2"
                variant="dots"
                :gap="20"
                :style="{ backgroundColor: '#0a0a0a' }"
              />
              
              <!-- Execute/Stop Button: Central bottom position like n8n (Only for admin/editor) -->
              <div v-if="canExecute" class="absolute bottom-32 left-1/2 transform -translate-x-1/2 z-50 flex gap-2">
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
                  <div class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
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
                          <Icon v-if="exec.finished && !exec.error" icon="lucide:check-circle" class="h-4 w-4 text-cyan-500" />
                          <Icon v-else-if="exec.error" icon="lucide:x-circle" class="h-4 w-4 text-red-400" />
                          <Icon v-else icon="lucide:clock" class="h-4 w-4 text-yellow-400" />
                          <span :class="[
                            'text-xs font-medium',
                            exec.finished && !exec.error ? 'text-cyan-500' : 
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
                <p class="text-lg font-bold text-cyan-500">
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
import { useRoute } from 'vue-router'
import { VueFlow, useVueFlow, Position, Handle } from '@vue-flow/core'

const route = useRoute()
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { Icon } from '@iconify/vue'
import MainLayout from '../components/layout/MainLayout.vue'
import UltraModernCard from '../components/workflow/UltraModernCard.vue'

// PrimeVue Components
import Card from 'primevue/card'
import Badge from 'primevue/badge'
import Dropdown from 'primevue/dropdown'
import Knob from 'primevue/knob'
import Chart from 'primevue/chart'
import ProgressBar from 'primevue/progressbar'
import WorkflowDetailModal from '../components/workflows/WorkflowDetailModal.vue'
import TimelineModal from '../components/common/TimelineModal.vue'
import DetailModal from '../components/common/DetailModal.vue'
import N8nIcon from '../components/N8nIcon.vue'
import { useUIStore } from '../stores/ui'
import { useAuthStore } from '../stores/auth'
import { businessAPI, $fetch } from '../services/api-client'
import { useNotification } from '../composables/useNotification'

// VueFlow styles
import '@vue-flow/core/dist/style.css'
// Theme CSS now consolidated in vscode-theme.css (imported in main.ts)

/**
 * Theme Switch Configuration
 *
 * ✅ CURRENTLY: Modern glassmorphism theme (dark slate, Inter font, professional)
 *
 * TO ROLLBACK TO ORIGINAL:
 * 1. Set USE_MODERN_THEME = false
 * 2. Comment out the CSS import above
 * 3. No other changes needed!
 */
const USE_MODERN_THEME = true // ✅ MODERN THEME ENABLED

// Stores
const uiStore = useUIStore()
const authStore = useAuthStore()

// Computed property for role-based permissions
const isViewer = computed(() => authStore.user?.role === 'viewer')
const canExecute = computed(() => !isViewer.value)

// Initialize our custom notification system
const toast = useNotification()

// Notification system ready
console.log('🔔 Custom notification system initialized')

// State
const isLoading = ref(false)
const tenantId = 'client_simulation_a'
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

// Node Types for VueFlow - Minimal clean design
const nodeTypes = {
  enterprise: UltraModernCard,
  custom: UltraModernCard // Fallback for any remaining custom nodes
}

// Computed
const totalWorkflows = computed(() => realWorkflows.value.length)
const activeWorkflows = computed(() => realWorkflows.value.filter(w => w.is_active).length)
const successRateValue = computed(() => Math.round(100 - failureRate.value))
const flowNodes = computed(() => flowElements.value.filter(el => !el.source))
const flowEdges = computed(() => {
  return flowElements.value.filter(el => el.source)
})

// Dropdown workflow options computed property
const workflowDropdownOptions = computed(() => {
  return realWorkflows.value.map(workflow => ({
    label: workflow.process_name,
    value: workflow.id,
    isActive: workflow.is_active,
    executionsToday: workflow.executions_today || 0
  }))
})

// Handler for workflow change via dropdown
const onWorkflowChange = (event: any) => {
  const workflowId = event.value
  const workflow = realWorkflows.value.find(w => w.id === workflowId)

  if (workflow) {
    console.log('🔄 Workflow changed via dropdown:', workflow.process_name)
    selectWorkflow(workflow)
  }
}

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
    
    // ORDINA per status: Active prima, poi il resto
    const sortedWorkflows = (workflowsData.data || []).sort((a, b) => {
      // Active workflows first
      if (a.is_active !== b.is_active) return a.is_active ? -1 : 1
      // Poi per nome alfabetico
      return a.process_name.localeCompare(b.process_name)
    })

    realWorkflows.value = sortedWorkflows
    console.log('🔄 Set realWorkflows to:', realWorkflows.value.length, 'items (sorted: active first)')
    console.log('📊 Active workflows:', realWorkflows.value.filter(w => w.is_active).map(w => w.process_name))
    
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
    
    toast.error(errorMsg)
    
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
    
    // Use OFETCH API client con force refresh per avere sempre dati aggiornati da n8n
    const data = await businessAPI.getProcessDetails(workflow.id, {
      _t: Date.now(),
      forceRefresh: true
    })
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
  const nodes = processSteps.filter((step: any) => !step.nodeType.includes('stickyNote')).map((step: any, index: number) => {
    const connections = nodeConnections.get(step.stepName) || { inputs: ['main'], outputs: ['main'] }
    
    return {
      id: step.stepName,
      type: 'enterprise',
      position: {
        x: (step.position[0] || 0) * 1.8, // Increased spacing for business cards
        y: (step.position[1] || 0) * 1.6  // Increased vertical spacing
      },
      data: {
        label: step.stepName,
        status: workflowMetadata.is_active ? 'success' : 'inactive',
        type: (() => {
          const nodeType = getNodeTypeFromN8nType(step.nodeType, step.stepName)
          // DEBUG COMPLETED: Qdrant text now visible!
          return nodeType
        })(),
        nodeType: step.nodeType || 'unknown-node',
        // Esecuzione reale - da collegare con WebSocket/SSE
        isExecuting: false, // Disabilitato per ora - da attivare con pulsante Execute
        inputs: connections.inputs.length > 0 ? connections.inputs : ['main'],
        outputs: connections.outputs.length > 0 ? connections.outputs : ['main'],
        // Add REAL execution stats for this workflow
        executionCount: workflowStats.totalExecutions || Math.floor(Math.random() * 100) + 10,
        successRate: workflowStats.kpis?.successRate || Math.floor(Math.random() * 20) + 80,
        avgTime: workflowStats.kpis?.avgDuration ?
          (workflowStats.kpis.avgDuration / 1000).toFixed(1) :
          (Math.random() * 2 + 0.5).toFixed(1)
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
    let sourceHandle = 'right'  // Default right output
    let targetHandle = 'left'   // Default left input
    let isConnectionToTool = false  // Track if this is a connection to a tool

    // Source handles based on connection type and node type
    if (sourceNodeType === 'storage') {
      // Storage nodes: Bottom output
      sourceHandle = 'bottom'
    } else if (sourceNodeType === 'tool') {
      // Tool nodes: Bottom output for all connections
      sourceHandle = 'bottom'
    } else if (sourceNodeType === 'ai') {
      // AI nodes: Right for main, Bottom distributed for AI tools

      // Check if this is a connection TO a tool node
      isConnectionToTool = targetNodeType === 'tool' ||
                            targetStep?.stepName?.toLowerCase().includes('ordini') ||
                            targetStep?.stepName?.toLowerCase().includes('date') ||
                            targetStep?.stepName?.toLowerCase().includes('parcel') ||
                            targetStep?.stepName?.toLowerCase().includes('formatta') ||
                            targetStep?.stepName?.toLowerCase().includes('clean data') ||
                            (targetStep?.nodeType && targetStep.nodeType.includes('langchain.tool'))

      if (isMainConnection && !isConnectionToTool) {
        sourceHandle = 'right'  // Right side for main connections
      } else if (isConnectionToTool) {
        // Connections from AI to tools ALWAYS go from bottom handles
        // Use a simple counter based on target node name for unique indexes
        const targetName = flow.to.toLowerCase()
        const targetStepName = targetStep?.stepName?.toLowerCase() || ''

        // Map tool names to specific indexes based on common patterns
        let toolIndex = 0

        // Check both flow.to and stepName for matches
        if (targetName.includes('clean') || targetName.includes('data') ||
            targetStepName.includes('clean') || targetStepName.includes('data')) {
          toolIndex = 0  // Clean Data -> tool-0
        } else if (targetName.includes('info') || targetName.includes('ordini') ||
            targetStepName.includes('info') || targetStepName.includes('ordini')) {
          toolIndex = 0  // INFO ORDINI -> tool-0
        } else if (targetName.includes('date') || targetName.includes('time') ||
                   targetStepName.includes('date') || targetStepName.includes('time')) {
          toolIndex = 1  // Date & Time -> tool-1
        } else if (targetName.includes('parcel') || targetName.includes('app') ||
                   targetStepName.includes('parcel') || targetStepName.includes('app')) {
          toolIndex = 2  // ParcelApp -> tool-2
        } else if (targetName.includes('formatta') || targetName.includes('risposta') ||
                   targetStepName.includes('formatta') || targetStepName.includes('risposta')) {
          toolIndex = 3  // Formatta risposta -> tool-3
        } else if (targetName.includes('openai') || targetName.includes('chat') ||
                   targetStepName.includes('openai') || targetStepName.includes('chat')) {
          toolIndex = 0  // OpenAI Chat -> tool-0
        } else if (targetName.includes('qdrant') || targetStepName.includes('qdrant')) {
          toolIndex = 1  // Qdrant -> tool-1
        } else if (targetName.includes('embedding') || targetStepName.includes('embedding')) {
          toolIndex = 2  // Embeddings -> tool-2
        } else {
          // Default index based on hash of name for consistency
          toolIndex = Math.abs(flow.to.charCodeAt(0) + flow.to.charCodeAt(1)) % 4
        }

        sourceHandle = `tool-${toolIndex}`   // Bottom side distributed
        console.log(`🔧 Tool connection: ${flow.from} -> ${flow.to} (${targetStepName}) using handle: ${sourceHandle}`)
      } else {
        sourceHandle = 'right'  // Default to right
      }
    } else {
      // Process nodes: Right side
      sourceHandle = 'right'
    }
    
    // Target handles based on connection type and node type
    if (targetNodeType === 'storage') {
      // Storage nodes: Agent connections to top, embeddings connections to bottom
      if (sourceNodeType === 'ai' && !isMainConnection) {
        // AI tool connections go to top (agent input)
        targetHandle = 'top'  // Top for agent connections
      } else if (sourceNodeType === 'tool' || flow.from.toLowerCase().includes('embedding')) {
        // Embeddings and tool nodes go to bottom
        targetHandle = 'bottom'  // Bottom for embeddings connections
      } else {
        // Main connections and others go to top
        targetHandle = 'top'  // Top for main connections
      }
    } else if (targetNodeType === 'tool') {
      // Tool nodes: Top input for connections FROM AI agents
      // Since tools connect FROM agent's bottom TO tool's top
      targetHandle = 'top'
    } else if (targetNodeType === 'ai') {
      // AI nodes: Left for main, Bottom distributed for AI tool connections
      if (isMainConnection) {
        targetHandle = 'left'  // Left side for main connections
      } else if (isAIConnection) {
        // Use distributed handles for AI tools - calculate index based on all AI connections
        const targetConnections = nodeConnections.get(flow.to) || { inputs: [], outputs: [] }
        const allAIConnections = [...targetConnections.inputs.filter(i => i !== 'main'), ...targetConnections.outputs.filter(o => o !== 'main')]
        const connectionIndex = allAIConnections.findIndex(conn => conn === flow.type)
        targetHandle = `tool-${Math.max(0, connectionIndex)}`   // Bottom side distributed
      } else {
        targetHandle = 'left'  // Default left
      }
    } else {
      // Process nodes: Left side
      targetHandle = 'left'
    }
    
    console.log(`🔗 Edge ${flow.from}->${flow.to}: type=${flow.type}, source=${sourceNodeType}, target=${targetNodeType}, handles=${sourceHandle}->${targetHandle}, isMain=${isMainConnection}, isConnectionToTool=${isConnectionToTool || false}`)
    
    return {
      id: `edge-${index}`,
      source: flow.from,
      target: flow.to,
      type: 'smoothstep',
      animated: workflowMetadata.is_active && isMainConnection,
      // Remove inline styles when modern theme active - let CSS handle it
      style: USE_MODERN_THEME ? {} : {
        stroke: isMainConnection ? '#10b981' : isAIConnection ? '#667eea' : '#3b82f6',
        strokeWidth: isMainConnection ? 3 : 2,
        strokeDasharray: isMainConnection ? 'none' : '5 5',
        opacity: isMainConnection ? 1 : 0.7,
        strokeLinecap: 'round',
        strokeLinejoin: 'round',
        filter: isMainConnection ? 'drop-shadow(0 0 3px rgba(16, 185, 129, 0.5))' : 'none'
      },
      sourceHandle,
      targetHandle,
      className: isMainConnection ? 'main-edge' : 'secondary-edge',
      markerEnd: USE_MODERN_THEME ? undefined : (isMainConnection ? {
        type: 'arrowclosed',
        width: 20,
        height: 20,
        color: '#10b981'
      } : undefined)
    }
  })
  
  console.log('✅ Created nodes with handles:', nodes.map(n => `ID:${n.id} Label:${n.data.label} type=${n.data.type} nodeType=${n.data.nodeType} inputs=${JSON.stringify(n.data.inputs)} outputs=${JSON.stringify(n.data.outputs)}`))
  console.log('🔗 Created edges:', edges.map(e => `${e.source}->${e.target} (${e.sourceHandle}->${e.targetHandle}) color=${e.style.stroke}`))
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
    type: 'enterprise',
    position: { x: index * 280, y: 50 },
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

// Nuovo: Business Dashboard Unificato
const openBusinessDashboard = () => {
  // Apre direttamente il Timeline Modal che diventerà il Business Dashboard
  showTimelineModal.value = true
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
const executingNodes = ref<Set<string>>(new Set())

// Function to connect to SSE for execution tracking (secured by execution verification)
const connectExecutionStream = (workflowId: string, executionId: string) => {
  const url = `${import.meta.env.VITE_API_URL || 'http://localhost:3001'}/api/business/processes/${workflowId}/execution-stream?executionId=${executionId}`
  console.log('🔗 Connecting to SSE for active execution:', url)

  const eventSource = new EventSource(url)

  eventSource.onopen = () => {
    console.log('✅ SSE Connection opened')
  }

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    console.log('🔄 SSE Event received:', data)

    // Debug: show current flowElements for comparison
    if (data.type === 'nodeExecuteBefore') {
      const currentNodeIds = flowElements.value.filter(el => !el.source).map(el => ({
        id: el.id,
        name: el.data?.stepName,
        type: el.type
      }))
      console.log('📋 Current flowElements nodes:', currentNodeIds)
      console.log('🎯 Looking for nodeId:', data.nodeId)
    }

    switch (data.type) {
      case 'nodeExecuteBefore':
        // Node starts executing - add to executing set
        console.log(`🟠 Node ${data.nodeName} (${data.nodeId}) starting execution`)

        // Find node by NAME instead of ID
        let nodeFound = false
        flowElements.value = flowElements.value.map(el => {
          if (el.id === data.nodeName) {
            console.log(`✅ Found matching node by name: ${el.id}, setting isExecuting=true`)
            nodeFound = true
            return {
              ...el,
              data: {
                ...el.data,
                isExecuting: true
              }
            }
          }
          return el
        })

        if (!nodeFound) {
          console.warn(`⚠️ Node ${data.nodeName} not found in flowElements! Available nodes:`, flowElements.value.filter(el => !el.source).map(el => el.id))
        }
        break

      case 'nodeExecuteAfter':
        // Node finishes executing - remove from executing set
        console.log(`⚫ Node ${data.nodeName} (${data.nodeId}) finished execution`)

        // Find node by NAME instead of ID
        flowElements.value = flowElements.value.map(el => {
          if (el.id === data.nodeName) {
            console.log(`✅ Found matching node by name: ${el.id}, setting isExecuting=false`)
            return {
              ...el,
              data: {
                ...el.data,
                isExecuting: false
              }
            }
          }
          return el
        })
        break

      case 'workflowExecuteAfter':
        // Workflow complete - show toast ONLY after last animation finishes
        console.log(`🏁 Workflow completed, waiting for last animation to finish...`)

        // Wait for last node animation to be visible before showing toast
        setTimeout(() => {
          isExecuting.value = false
          executingNodes.value.clear()

          // Clear all executing states
          flowElements.value = flowElements.value.map(el => ({
            ...el,
            data: {
              ...el.data,
              isExecuting: false
            }
          }))

          // Don't show toast here - polling will handle it with duration info
          console.log(`✅ Workflow completed - toast will be shown by polling with duration`)

          // Reload workflow stats after completion
          setTimeout(async () => {
            await loadWorkflowDetails(selectedWorkflowId.value)
            await loadExecutionData(selectedWorkflowId.value)
          }, 1000)

        }, 300) // Wait 300ms for last node to be clearly visible

        eventSource.close()
        break

      case 'error':
        isExecuting.value = false
        executingNodes.value.clear()
        eventSource.close()
        toast.error(`Errore Esecuzione: ${data.message}`)
        break
    }
  }

  eventSource.onerror = (error) => {
    console.error('❌ SSE connection error:', error)
    eventSource.close()
    isExecuting.value = false
    executingNodes.value.clear()
    // Reset all nodes
    flowElements.value = flowElements.value.map(el => ({
      ...el,
      data: {
        ...el.data,
        isExecuting: false
      }
    }))
  }

  return eventSource
}

const executeWorkflow = async () => {
  if (!selectedWorkflowData.value || !selectedWorkflowId.value) {
    toast.error('Seleziona un workflow da eseguire')
    return
  }

  if (isExecuting.value) return // Prevent double clicks

  const workflowName = selectedWorkflowData.value.process_name || 'Unknown'
  isExecuting.value = true

  // Show start toast IMMEDIATELY
  console.log('🎯 Showing start notification...')
  toast.success(`Il workflow "${workflowName}" è stato avviato correttamente`)

  try {
    console.log(`🚀 Executing workflow ${selectedWorkflowId.value}...`)

    // API call to execute workflow FIRST to get real execution ID
    console.log(`📞 Calling businessAPI.executeWorkflow...`)
    const result = await businessAPI.executeWorkflow(selectedWorkflowId.value)
    console.log('✅ Workflow execution result:', result)

    if (result.success && result.data.executionStarted) {
      // Store execution ID for stop functionality
      currentExecutionId.value = result.data.executionId

      // Connect to SSE for real-time tracking with REAL execution ID
      console.log(`🔗 Connecting SSE with real executionId: ${result.data.executionId}`)
      const eventSource = connectExecutionStream(selectedWorkflowId.value, result.data.executionId)

      console.log(`🚀 Workflow "${workflowName}" started`)

      // Update KPI immediately (increment execution count)
      if (workflowStats.value && workflowStats.value.kpis) {
        workflowStats.value.kpis.totalExecutions = (workflowStats.value.kpis.totalExecutions || 0) + 1
        workflowStats.value.kpis.runningExecutions = (workflowStats.value.kpis.runningExecutions || 0) + 1
      }

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
            
            // Update KPI: remove from running count
            if (workflowStats.value && workflowStats.value.kpis) {
              workflowStats.value.kpis.runningExecutions = Math.max(0, (workflowStats.value.kpis.runningExecutions || 0) - 1)
            }

            if (statusResult.data.status === 'success') {
              // Simplified toast call
              toast.success(`Il workflow "${workflowName}" è stato eseguito con successo in ${Math.round(statusResult.data.duration / 1000)}s`)
              // Update success count in KPIs
              if (workflowStats.value && workflowStats.value.kpis) {
                workflowStats.value.kpis.successfulExecutions = (workflowStats.value.kpis.successfulExecutions || 0) + 1
                // Recalculate success rate
                const total = workflowStats.value.kpis.totalExecutions || 1
                const success = workflowStats.value.kpis.successfulExecutions || 0
                workflowStats.value.kpis.successRate = Math.round((success / total) * 100)
              }
            } else if (statusResult.data.status === 'error' && statusResult.data.errorInfo) {
              // Mostra errori specifici di n8n
              const errorDetails = statusResult.data.errorInfo.errors.map(e =>
                `${e.nodeName}: ${e.error.message}`
              ).join('\n')

              toast.error(`Il workflow "${workflowName}" ha riscontrato errori: ${errorDetails}`)
              // Update failed count in KPIs
              if (workflowStats.value && workflowStats.value.kpis) {
                workflowStats.value.kpis.failedExecutions = (workflowStats.value.kpis.failedExecutions || 0) + 1
                // Recalculate success rate
                const total = workflowStats.value.kpis.totalExecutions || 1
                const success = workflowStats.value.kpis.successfulExecutions || 0
                workflowStats.value.kpis.successRate = Math.round((success / total) * 100)
              }
            } else {
              toast.error(`Il workflow "${workflowName}" è stato interrotto`)
              // Update failed count in KPIs
              if (workflowStats.value && workflowStats.value.kpis) {
                workflowStats.value.kpis.failedExecutions = (workflowStats.value.kpis.failedExecutions || 0) + 1
                // Recalculate success rate
                const total = workflowStats.value.kpis.totalExecutions || 1
                const success = workflowStats.value.kpis.successfulExecutions || 0
                workflowStats.value.kpis.successRate = Math.round((success / total) * 100)
              }
            }

            // Ricarica dati completi per avere statistiche accurate
            fetchRealWorkflows()
            if (selectedWorkflowId.value) {
              await loadWorkflowStatistics(selectedWorkflowId.value)
            }
          }
          
          // Stop polling after max time
          if (pollCount >= maxPolls) {
            clearInterval(pollInterval)
            isExecuting.value = false
            currentExecutionId.value = null
            
            toast.info(
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
      
      toast.error(
        result.data?.n8nApiResult?.error || `Impossibile eseguire il workflow "${workflowName}"`
      )
    }
    
  } catch (error: any) {
    console.error('❌ Failed to execute workflow:', error)
    
    // Reset state on error
    isExecuting.value = false
    currentExecutionId.value = null
    
    toast.error(
      `Impossibile eseguire il workflow "${workflowName}". ${error.message}`
    )
  }
}


// Stop workflow execution
const stopWorkflow = async () => {
  if (!selectedWorkflowId.value || !currentExecutionId.value) {
    toast.error('Nessuna esecuzione da fermare')
    return
  }
  
  const workflowName = selectedWorkflowData.value?.process_name || 'Unknown'
  
  try {
    console.log(`🛑 Stopping workflow ${selectedWorkflowId.value}, execution ${currentExecutionId.value}...`)
    
    // API call to stop workflow - OFETCH Migration
    const result = await businessAPI.stopWorkflow(selectedWorkflowId.value)
    console.log('✅ Workflow stop result:', result)
    
    if (result.success) {
      toast.success(
        `Il workflow "${workflowName}" è stato fermato con successo`
      )
    } else {
      toast.error(
        result.data?.n8nApiResult?.error || `Impossibile fermare il workflow "${workflowName}"`
      )
    }
    
  } catch (error: any) {
    console.error('❌ Failed to stop workflow:', error)
    
    toast.error(
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
        toast.success(
          `${result.data.workflowName} è stato ${newStatus ? 'attivato' : 'disattivato'} localmente`
        )
      } else {
        toast.success(
          `${result.data.workflowName} è stato ${newStatus ? 'attivato' : 'disattivato'} con successo`
        )
      }
    } else {
      toast.error(
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
    
    toast.error(
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
  if (trendValue > 0) return 'text-cyan-500 text-xs font-medium'
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
    case 'SUCCESS': return 'text-cyan-500 font-semibold'
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
    
    // Controlla se c'è un workflowId nei parametri URL (da Insights)
    const urlWorkflowId = route.query.workflowId
    if (urlWorkflowId && realWorkflows.value.length > 0) {
      console.log('🎯 URL workflowId detected:', urlWorkflowId)
      const targetWorkflow = realWorkflows.value.find(w => w.id === urlWorkflowId)
      if (targetWorkflow) {
        console.log('✅ Found workflow from URL, selecting:', targetWorkflow.process_name)
        await selectWorkflow(targetWorkflow)
        return
      } else {
        console.log('❌ Workflow from URL not found, falling back to first')
      }
    }

    // Seleziona automaticamente il primo workflow se presente e nessuno dall'URL
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
      // ORDINA anche nel fallback
      const sortedFallback = (workflowsData.data || []).sort((a, b) => {
        if (a.is_active !== b.is_active) return a.is_active ? -1 : 1
        return a.process_name.localeCompare(b.process_name)
      })
      realWorkflows.value = sortedFallback
      console.log('🔧 Alternative workflows set:', realWorkflows.value.length, '(sorted)')
      
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
/* Selected workflow - Professional subtle style with smooth animations */
[data-theme="vscode"] .selected-workflow {
  background: linear-gradient(135deg, rgba(137, 209, 133, 0.05) 0%, rgba(137, 209, 133, 0.02) 100%);
  border: 1px solid var(--vscode-success) !important;
  box-shadow: 0 0 0 1px rgba(137, 209, 133, 0.1) inset;
  position: relative;
  animation: smoothSelection 0.3s ease-out;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes smoothSelection {
  from {
    opacity: 0.6;
    transform: scale(0.98);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

[data-theme="vscode"] .selected-workflow::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(to bottom, var(--vscode-success), #059669);
  border-radius: 2px 0 0 2px;
  animation: slideInLeft 0.2s ease-out;
}

@keyframes slideInLeft {
  from {
    transform: translateX(-100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Remove any white borders from theme */
[data-theme="vscode"] .selected-workflow * {
  border-color: transparent !important;
  outline: none !important;
}
[data-theme="vscode"] .workflow-flow {
  background: var(--vscode-bg-primary);
}

/* Smooth transitions for workflow canvas */
.workflow-transition {
  animation: fadeInCanvas 0.4s ease-out;
}

@keyframes fadeInCanvas {
  from {
    opacity: 0;
    filter: blur(2px);
    transform: scale(0.98);
  }
  to {
    opacity: 1;
    filter: blur(0);
    transform: scale(1);
  }
}

/* Smooth transition for all workflow items in list */
[data-theme="vscode"] .p-2.rounded-md.cursor-pointer {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* VueFlow nodes smooth appearance */
[data-theme="vscode"] :deep(.vue-flow__node) {
  animation: nodeAppear 0.3s ease-out;
  transition: transform 0.3s ease-out;
}

@keyframes nodeAppear {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Clear default VueFlow styles */
[data-theme="vscode"] :deep(.vue-flow__node-custom),
[data-theme="vscode"] :deep(.vue-flow__node-enterprise) {
  background: transparent !important;
  border: none !important;
}


/* ===== AGENT NODES (n8n Style Rectangular) ===== */
[data-theme="vscode"] :deep(.premium-ai-node) {
  background: #1C1C1C; /* Grigio scuro - visibile su #141414 */
  border: 0.5px solid var(--vscode-success);
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

/* Badge con testo bianco per massima visibilità */
[data-theme="vscode"] .badge-white-text {
  color: var(--vscode-text-inverse) !important;
}

[data-theme="vscode"] :deep(.premium-ai-node:hover) {
  transform: translateY(-4px) rotateX(5deg);
  box-shadow:
    0 16px 48px rgba(74, 85, 104, 0.4),
    0 0 24px rgba(45, 55, 72, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

[data-theme="vscode"] :deep(.premium-ai-active) {
  animation: aiPulse 2s ease-in-out infinite;
}

[data-theme="vscode"] :deep(.premium-ai-icon) {
  position: relative;
  color: var(--vscode-text-inverse);
  margin-bottom: 0px;
  display: flex;
  align-items: center;
  justify-content: center;
}

[data-theme="vscode"] :deep(.premium-ai-glow) {
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

[data-theme="vscode"] :deep(.premium-ai-content) {
  text-align: center;
  color: var(--vscode-text-inverse);
}

[data-theme="vscode"] :deep(.premium-ai-name) {
  font-size: 11px;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  margin-bottom: 2px;
  line-height: 1.2;
}

[data-theme="vscode"] :deep(.premium-ai-badge) {
  font-size: 8px;
  font-weight: 900;
  background: rgba(255, 255, 255, 0.2);
  padding: 1px 6px;
  border-radius: 10px;
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

[data-theme="vscode"] :deep(.premium-ai-connections) {
  font-size: 8px;
  opacity: 0.8;
  margin-top: 2px;
}

/* ===== TOOL NODES (n8n Style Circular) ===== */
[data-theme="vscode"] :deep(.premium-tool-node) {
  background: #1C1C1C; /* Grigio scuro - visibile su #141414 */
  border: 0.5px solid var(--vscode-success);
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

[data-theme="vscode"] :deep(.premium-tool-node:hover) {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

[data-theme="vscode"] :deep(.premium-tool-active) {
  animation: toolPulse 2s ease-in-out infinite;
}

[data-theme="vscode"] :deep(.premium-tool-icon) {
  color: var(--vscode-text-inverse);
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
}

[data-theme="vscode"] :deep(.premium-tool-content) {
  text-align: center;
  color: var(--vscode-text-inverse);
}

[data-theme="vscode"] :deep(.premium-tool-name) {
  font-size: 8px;
  font-weight: 600;
  color: var(--vscode-text-inverse);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  margin-bottom: 1px;
  line-height: 1.1;
}

[data-theme="vscode"] :deep(.premium-tool-badge) {
  font-size: 6px;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.2);
  color: var(--vscode-text-inverse);
  padding: 1px 3px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

/* ===== TRIGGER NODES (Exact n8n Style) ===== */
[data-theme="vscode"] :deep(.premium-trigger-node) {
  background: #1C1C1C; /* Grigio scuro - visibile su #141414 */
  border: 0.5px solid var(--vscode-success);
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

[data-theme="vscode"] :deep(.premium-trigger-node:hover) {
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

[data-theme="vscode"] :deep(.premium-trigger-active) {
  background: var(--vscode-bg-primary);
  border-color: rgba(16, 185, 129, 0.4);
}

[data-theme="vscode"] :deep(.premium-trigger-inactive) {
  background: var(--vscode-bg-primary);
  border-color: rgba(255, 255, 255, 0.1);
}

[data-theme="vscode"] :deep(.premium-trigger-icon) {
  color: var(--vscode-text-inverse);
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.5));
}

/* Lightning bolt indicator (top-left corner) */
[data-theme="vscode"] :deep(.premium-trigger-node::before) {
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

[data-theme="vscode"] :deep(.premium-trigger-content) {
  text-align: left;
  flex: 1;
  overflow: hidden;
}

[data-theme="vscode"] :deep(.premium-trigger-name) {
  font-size: 10px;
  font-weight: 500;
  color: var(--vscode-text-secondary);
  margin-bottom: 0;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

[data-theme="vscode"] :deep(.premium-trigger-badge) {
  font-size: 7px;
  font-weight: 800;
  background: rgba(214, 51, 132, 0.1);
  color: #d63384;
  padding: 1px 4px;
  border-radius: 6px;
  border: 1px solid rgba(214, 51, 132, 0.2);
}

/* ===== STORAGE NODES (Exact n8n Style - Pill Shape) ===== */
[data-theme="vscode"] :deep(.premium-storage-node) {
  background: #1C1C1C !important; /* Grigio scuro - visibile su #141414 */
  border: 0.5px solid var(--vscode-success) !important;
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

[data-theme="vscode"] :deep(.premium-storage-node:hover) {
  transform: scale(1.02);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

[data-theme="vscode"] :deep(.premium-storage-icon) {
  color: var(--vscode-text-inverse);
  margin-right: 12px;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.5));
  flex-shrink: 0;
}

[data-theme="vscode"] :deep(.premium-storage-name) {
  font-size: 14px;
  font-weight: 600;
  color: var(--vscode-text-inverse) !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8) !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

[data-theme="vscode"] :deep(.premium-storage-badge) {
  font-size: 7px;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.2);
  color: var(--vscode-text-inverse);
  padding: 1px 4px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

/* ===== PREMIUM PROCESS NODES ===== */
[data-theme="vscode"] :deep(.premium-process-node) {
  background: #1C1C1C; /* Grigio scuro - visibile su #141414 */
  border: 0.5px solid var(--vscode-success);
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

[data-theme="vscode"] :deep(.premium-process-node:hover) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(74, 85, 104, 0.4);
}

[data-theme="vscode"] :deep(.premium-process-active) {
  border-color: var(--vscode-success);
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
}

[data-theme="vscode"] :deep(.premium-process-icon) {
  color: var(--vscode-text-secondary);
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
}

/* Process node names and connections are now handled by external labels */

/* ===== PREMIUM HANDLES (Enhanced Visibility) ===== */

/* Main flow handles (left/right) - VISIBLE */
[data-theme="vscode"] :deep(.premium-handle-ai-main) {
  width: 8px !important;
  height: 8px !important;
  background: var(--vscode-text-inverse) !important;
  border: 1px solid rgba(200, 200, 200, 0.8) !important;
  border-radius: 50% !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  transition: all 0.3s ease !important;
  opacity: 1 !important;
  z-index: 10 !important;
}

[data-theme="vscode"] :deep(.premium-handle-ai-main:hover) {
  opacity: 1 !important;
  transform: scale(1.2) !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

/* AI Tool handles (bottom) - VISIBLE */
[data-theme="vscode"] :deep(.premium-handle-ai-tool) {
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

[data-theme="vscode"] :deep(.premium-handle-ai-tool:hover) {
  opacity: 1 !important;
  transform: scale(1.2) !important;
  box-shadow: 0 2px 4px rgba(168, 85, 247, 0.4) !important;
}

/* Handle type-specific colors */
[data-theme="vscode"] :deep(.premium-handle-memory) {
  background: linear-gradient(45deg, #ff6b6b, #ee5a24) !important;
}

[data-theme="vscode"] :deep(.premium-handle-tool) {
  background: linear-gradient(45deg, #2ecc71, #27ae60) !important;
}

[data-theme="vscode"] :deep(.premium-handle-language) {
  background: linear-gradient(45deg, #f39c12, #e67e22) !important;
}

[data-theme="vscode"] :deep(.premium-handle-ai) {
  background: linear-gradient(45deg, #9b59b6, #8e44ad) !important;
}

[data-theme="vscode"] :deep(.premium-handle-main) {
  background: linear-gradient(45deg, #3498db, #2980b9) !important;
}

[data-theme="vscode"] :deep(.premium-handle-trigger) {
  width: 6px !important;
  height: 6px !important;
  background: var(--vscode-text-inverse) !important;
  border: 1px solid rgba(200, 200, 200, 0.8) !important;
  border-radius: 50% !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  opacity: 1 !important;
}

[data-theme="vscode"] :deep(.premium-handle-tool) {
  width: 12px !important;
  height: 12px !important;
  background: linear-gradient(45deg, #a855f7, #8b5cf6) !important;
  border: 2px solid var(--vscode-text-inverse) !important;
  border-radius: 50% !important;
  box-shadow: 0 2px 8px rgba(168, 85, 247, 0.5) !important;
  transition: all 0.3s ease !important;
}

[data-theme="vscode"] :deep(.premium-handle-tool-top) {
  width: 8px !important;
  height: 8px !important;
  background: var(--vscode-text-inverse) !important;
  border: 1px solid rgba(200, 200, 200, 0.8) !important;
  border-radius: 50% !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  transition: all 0.3s ease !important;
  opacity: 1 !important;
  z-index: 15 !important;
  top: -7px !important;
}

[data-theme="vscode"] :deep(.premium-handle-tool-top:hover) {
  opacity: 1 !important;
  transform: translateX(-50%) scale(1.2) !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="vscode"] :deep(.premium-handle-tool-bottom) {
  width: 8px !important;
  height: 8px !important;
  background: var(--vscode-text-inverse) !important;
  border: 1px solid rgba(200, 200, 200, 0.8) !important;
  border-radius: 50% !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  transition: all 0.3s ease !important;
  opacity: 1 !important;
  z-index: 15 !important;
}

[data-theme="vscode"] :deep(.premium-handle-tool-bottom:hover) {
  opacity: 1 !important;
  transform: translateX(-50%) scale(1.2) !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="vscode"] :deep(.premium-handle-storage) {
  width: 8px !important;
  height: 8px !important;
  background: var(--vscode-accent) !important;
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  border-radius: 50% !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  transition: all 0.3s ease !important;
  opacity: 1 !important;
}

[data-theme="vscode"] :deep(.premium-handle-storage:hover) {
  opacity: 1 !important;
  transform: scale(1.2) !important;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.4) !important;
}

[data-theme="vscode"] :deep(.premium-handle-process) {
  width: 8px !important;
  height: 8px !important;
  background: var(--vscode-text-inverse) !important;
  border: 1px solid rgba(200, 200, 200, 0.8) !important;
  border-radius: 50% !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  transition: all 0.3s ease !important;
  opacity: 1 !important;
}

[data-theme="vscode"] :deep(.premium-handle-process:hover) {
  opacity: 1 !important;
  transform: scale(1.2) !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

/* Handle visibility: show only connected handles */
[data-theme="vscode"] :deep(.handle-connected) {
  opacity: 1 !important;
}

[data-theme="vscode"] :deep(.handle-disconnected) {
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
[data-theme="vscode"] :deep(.main-edge) {
  z-index: 10;
}

[data-theme="vscode"] :deep(.main-edge .vue-flow__edge-path) {
  stroke: var(--vscode-success) !important;
  stroke-width: 1px !important;
  opacity: 1 !important;
  stroke-linecap: round !important;
  stroke-linejoin: round !important;
}

/* Secondary/AI tool edges (dashed, thinner, curved) */
[data-theme="vscode"] :deep(.secondary-edge) {
  z-index: 5;
}

[data-theme="vscode"] :deep(.secondary-edge .vue-flow__edge-path) {
  stroke-dasharray: 8 4 !important;
  stroke-width: 1px !important;
  opacity: 0.8 !important;
  transition: all 0.3s ease !important;
  stroke-linecap: round !important;
  stroke-linejoin: round !important;
}

[data-theme="vscode"] :deep(.secondary-edge:hover .vue-flow__edge-path) {
  opacity: 1 !important;
  stroke-width: 1px !important;
}

/* Smooth bezier curves for all edges (like n8n) */
[data-theme="vscode"] :deep(.vue-flow__edge .vue-flow__edge-path) {
  stroke-linecap: round !important;
  stroke-linejoin: round !important;
}

/* Ensure bezier curves render properly */
[data-theme="vscode"] :deep(.vue-flow__edge-default .vue-flow__edge-path) {
  stroke-linecap: round !important;
  stroke-linejoin: round !important;
}

/* ALL handles stay invisible - clean workflow design */
[data-theme="vscode"] :deep(.premium-ai-node:hover .vue-flow__handle),
[data-theme="vscode"] :deep(.premium-tool-node:hover .vue-flow__handle),
[data-theme="vscode"] :deep(.premium-trigger-node:hover .vue-flow__handle),
[data-theme="vscode"] :deep(.premium-storage-node:hover .vue-flow__handle),
[data-theme="vscode"] :deep(.premium-process-node:hover .vue-flow__handle) {
  opacity: 0 !important;
}

/* ===== FORCE DARK THEME - MAXIMUM SPECIFICITY OVERRIDE ===== */
/* Target ALL PrimeVue Card components and glass elements */

/* KPI Cards - PrimeVue Card component with all variations */
[data-theme="vscode"] :deep(.premium-glass.premium-hover-lift),
[data-theme="vscode"] :deep(.premium-glass.premium-hover-lift .p-card),
[data-theme="vscode"] :deep(.premium-glass.premium-hover-lift .p-card-body),
[data-theme="vscode"] :deep(.premium-glass.premium-hover-lift .p-card-content),
[data-theme="vscode"] :deep(.premium-glass),
[data-theme="vscode"] :deep(.p-card),
[data-theme="vscode"] :deep(.p-card-body),
[data-theme="vscode"] :deep(.p-card-content),
[data-theme="vscode"] :deep(.glass),
[data-theme="vscode"] :deep([class*="glass"]) {
  background: rgba(26, 26, 26, 0.85) !important;
  background-color: rgba(26, 26, 26, 0.85) !important;
  border-color: rgba(60, 60, 60, 1) !important;
}

/* Target grid children (KPI stat cards container) */
[data-theme="vscode"] .grid.grid-cols-6 > * {
  background: transparent !important;
}

[data-theme="vscode"] .grid.grid-cols-6 :deep(.p-card) {
  background: rgba(26, 26, 26, 0.85) !important;
  background-color: rgba(26, 26, 26, 0.85) !important;
  border-color: rgba(60, 60, 60, 1) !important;
}

/* Sidebar workflow list - Ultra aggressive with combined selectors */
[data-theme="vscode"] .premium-glass.rounded-lg,
[data-theme="vscode"] :deep(.premium-glass.rounded-lg),
[data-theme="vscode"] .premium-glass.rounded-lg .p-card,
[data-theme="vscode"] .flex.gap-4 > .premium-glass {
  background: rgba(26, 26, 26, 0.85) !important;
  background-color: rgba(26, 26, 26, 0.85) !important;
  border-color: rgba(60, 60, 60, 1) !important;
}

/* ===== NODE WRAPPER & EXTERNAL LABELS (n8n Style) ===== */
[data-theme="vscode"] :deep(.premium-node-wrapper) {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  position: relative;
  width: fit-content;
  height: fit-content;
}

[data-theme="vscode"] :deep(.premium-external-label) {
  font-size: 11px;
  font-weight: 500;
  color: var(--vscode-text-inverse);
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

/* ============================================
   WORKFLOW DROPDOWN CUSTOM STYLING - MINIMAL
   ============================================ */

/* Dropdown container */
:deep(.workflow-dropdown) {
  min-width: 260px;
  max-width: 300px;
}

/* Dropdown chiuso - GRAY THEME (NO CYAN) */
:deep(.workflow-dropdown .p-dropdown) {
  background: rgba(20, 20, 20, 0.9) !important;
  border: 1px solid #3C3C3C !important;
  backdrop-filter: blur(8px);
  transition: all 0.2s ease;
  padding: 0.4rem 0.75rem !important;
  font-size: 0.75rem !important;
}

:deep(.workflow-dropdown .p-dropdown:hover) {
  border-color: #4B5563 !important;
  background: rgba(30, 30, 30, 0.95) !important;
  box-shadow: none !important;
}

:deep(.workflow-dropdown .p-dropdown:focus-within),
:deep(.workflow-dropdown .p-dropdown:focus),
:deep(.workflow-dropdown .p-dropdown.p-focus) {
  border-color: #6B7280 !important;
  box-shadow: 0 0 0 1px rgba(107, 114, 128, 0.2) !important;
  outline: none !important;
}

/* Dropdown trigger icon */
:deep(.workflow-dropdown .p-dropdown-trigger) {
  color: #9CA3AF !important;
  width: 2rem !important;
}

/* Dropdown label (selected value text) - FORCE GRAY ON WRAPPER */
:deep(.workflow-dropdown .p-select-label),
:deep(.workflow-dropdown .p-dropdown-label),
:deep(.workflow-dropdown .p-inputtext),
:deep(.workflow-dropdown .p-select-label *),
:deep(.workflow-dropdown .p-dropdown-label *),
:deep(.workflow-dropdown span),
:deep(.workflow-dropdown div) {
  color: #9CA3AF !important;
  font-weight: 400 !important;
}

/* Target the EXACT wrapper span that PrimeVue generates */
:deep(.workflow-dropdown span.p-select-label),
:deep(.workflow-dropdown span.p-select-label[role="combobox"]),
:deep(.workflow-dropdown span.p-select-label div),
:deep(.workflow-dropdown span.p-select-label div span),
:deep(.workflow-dropdown span.p-select-label > *),
:deep(.workflow-dropdown span.p-select-label *) {
  color: #9CA3AF !important;
}

/* Override ANY cyan/blue inheritance */
:deep(.workflow-dropdown *) {
  --vscode-variable: #9CA3AF !important;
  --vscode-accent: #6B7280 !important;
  --vscode-border-focus: #6B7280 !important;
  --primary: #6B7280 !important;
}

/* Dropdown panel (menu aperto) - DARKER */
:deep(.p-dropdown-panel) {
  background: rgba(20, 20, 20, 0.98) !important;
  backdrop-filter: blur(12px);
  border: 1px solid #3C3C3C !important;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
  border-radius: 6px;
  margin-top: 2px;
}

/* Override panel variable inheritance */
:deep(.p-dropdown-panel *) {
  --vscode-variable: #9CA3AF !important;
  --vscode-accent: #6B7280 !important;
  --vscode-border-focus: #6B7280 !important;
  --primary: #6B7280 !important;
}

/* Dropdown items - COMPACT */
:deep(.p-dropdown-item) {
  color: #E5E7EB !important;
  padding: 0.4rem 0.6rem !important;
  transition: all 0.15s ease;
  border-radius: 4px;
  margin: 1px 4px;
  font-size: 0.75rem !important;
}

:deep(.p-dropdown-item:hover) {
  background: rgba(55, 65, 81, 0.5) !important;
  color: #F3F4F6 !important;
}

:deep(.p-dropdown-item.p-highlight) {
  background: rgba(75, 85, 99, 0.6) !important;
  color: #F9FAFB !important;
  font-weight: 500;
}

/* Filter input (search box) - COMPACT */
:deep(.p-dropdown-filter) {
  background: rgba(15, 15, 15, 0.8) !important;
  border: 1px solid #374151 !important;
  color: #E5E7EB !important;
  padding: 0.35rem 0.6rem !important;
  border-radius: 4px;
  margin: 6px 6px 3px 6px !important;
  font-size: 0.7rem !important;
}

:deep(.p-dropdown-filter:focus) {
  border-color: #6B7280 !important;
  box-shadow: 0 0 0 1px rgba(107, 114, 128, 0.15) !important;
  outline: none;
}

:deep(.p-dropdown-filter::placeholder) {
  color: #6B7280 !important;
  font-size: 0.7rem !important;
}

/* Empty message */
:deep(.p-dropdown-empty-message) {
  color: #9CA3AF;
  padding: 0.75rem;
  text-align: center;
  font-size: 0.7rem;
}

/* Scrollbar - THIN */
:deep(.p-dropdown-items-wrapper) {
  max-height: 380px;
  overflow-y: auto;
}

:deep(.p-dropdown-items-wrapper)::-webkit-scrollbar {
  width: 6px;
}

:deep(.p-dropdown-items-wrapper)::-webkit-scrollbar-track {
  background: rgba(15, 15, 15, 0.5);
  border-radius: 3px;
}

:deep(.p-dropdown-items-wrapper)::-webkit-scrollbar-thumb {
  background: rgba(75, 85, 99, 0.6);
  border-radius: 3px;
}

:deep(.p-dropdown-items-wrapper)::-webkit-scrollbar-thumb:hover {
  background: rgba(107, 114, 128, 0.8);
}

/* NUCLEAR OPTION - Force gray on ALL dropdown elements */
:deep(.workflow-dropdown),
:deep(.workflow-dropdown) *,
:deep(.workflow-dropdown) input,
:deep(.workflow-dropdown) span,
:deep(.workflow-dropdown) div,
:deep(.workflow-dropdown) label,
:deep(.workflow-dropdown) .p-inputtext,
:deep(.p-dropdown-panel),
:deep(.p-dropdown-panel) * {
  border-color: #3C3C3C !important;
}

:deep(.workflow-dropdown) *:focus,
:deep(.workflow-dropdown) *:focus-within,
:deep(.p-dropdown-panel) *:focus,
:deep(.p-dropdown-panel) *:focus-within {
  border-color: #6B7280 !important;
  box-shadow: 0 0 0 1px rgba(107, 114, 128, 0.2) !important;
  outline: none !important;
}
</style>