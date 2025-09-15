<template>
  <div
    :class="[
      'premium-node',
      `node-category-${nodeCategory}`,
      {
        'node-active': isActive,
        'node-error': hasError,
        'node-selected': selected
      }
    ]"
  >
    <!-- Top Status Bar -->
    <div class="node-status-bar" :style="{ background: statusBarColor }">
      <div class="status-indicator">
        <div :class="['status-pulse', `pulse-${status}`]"></div>
      </div>
      <span class="status-text">{{ statusText }}</span>
    </div>

    <!-- Main Card Body -->
    <div class="node-body">
      <!-- Large Icon Section -->
      <div class="node-icon-section" :style="{ background: iconGradient }">
        <Icon
          :icon="nodeIcon"
          class="node-main-icon"
        />
      </div>

      <!-- Content Section -->
      <div class="node-content-section">
        <h3 class="node-name">{{ businessName }}</h3>
        <p class="node-type">{{ categoryLabel }}</p>

        <!-- Metrics if available -->
        <div v-if="showMetrics" class="node-metrics">
          <div class="metric">
            <span class="metric-value">{{ executionCount || 0 }}</span>
            <span class="metric-label">Runs</span>
          </div>
          <div class="metric">
            <span class="metric-value">{{ successRate || '100' }}%</span>
            <span class="metric-label">Success</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Action Bar -->
    <div class="node-action-bar">
      <div class="connection-info">
        <Icon icon="lucide:log-in" class="connection-icon" />
        <span>{{ inputs.length }}</span>
      </div>
      <div class="node-category-badge">
        {{ categoryBadge }}
      </div>
      <div class="connection-info">
        <span>{{ outputs.length }}</span>
        <Icon icon="lucide:log-out" class="connection-icon" />
      </div>
    </div>

    <!-- Connection Handles -->
    <Handle
      v-for="(handle, idx) in inputs"
      :key="`in-${idx}`"
      type="target"
      :position="Position.Left"
      :id="`input-${idx}`"
      class="premium-handle handle-input"
      :style="{ top: `${30 + (idx * 20)}px` }"
    />

    <Handle
      v-for="(handle, idx) in outputs"
      :key="`out-${idx}`"
      type="source"
      :position="Position.Right"
      :id="`output-${idx}`"
      class="premium-handle handle-output"
      :style="{ top: `${30 + (idx * 20)}px` }"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import { Icon } from '@iconify/vue'

interface Props {
  data: {
    label: string
    type: string
    nodeType?: string
    status?: 'active' | 'pending' | 'error' | 'success' | 'idle'
    executionCount?: number
    successRate?: number
    inputs?: string[]
    outputs?: string[]
  }
  selected?: boolean
}

const props = defineProps<Props>()

// Category detection with clear mapping
const nodeCategory = computed(() => {
  const type = props.data.type
  const nodeType = props.data.nodeType || ''

  // Priority categorization
  if (type === 'ai' || nodeType.includes('agent') || nodeType.includes('openai')) return 'ai'
  if (type === 'storage' || nodeType.includes('database') || nodeType.includes('vectorStore')) return 'storage'
  if (type === 'trigger' || nodeType.includes('trigger') || nodeType.includes('webhook')) return 'trigger'
  if (nodeType.includes('if') || nodeType.includes('switch') || nodeType.includes('merge')) return 'logic'
  if (nodeType.includes('http') || nodeType.includes('email') || nodeType.includes('slack')) return 'communication'
  if (nodeType.includes('code') || nodeType.includes('function')) return 'transform'

  return 'process' // default
})

// Premium icon selection
const nodeIcon = computed(() => {
  const iconMap: Record<string, string> = {
    'trigger': 'carbon:launch',
    'ai': 'carbon:machine-learning-model',
    'storage': 'carbon:data-base',
    'logic': 'carbon:flow-data',
    'communication': 'carbon:send-alt',
    'transform': 'carbon:code',
    'process': 'carbon:task'
  }
  return iconMap[nodeCategory.value] || 'carbon:circle-dash'
})

// Business-friendly names
const businessName = computed(() => {
  const name = props.data.label

  // Smart name transformation
  const replacements: Record<string, string> = {
    'Webhook': 'API Receiver',
    'Schedule Trigger': 'Scheduled Task',
    'Manual Trigger': 'Manual Start',
    'OpenAI': 'AI Assistant',
    'Agent': 'AI Agent',
    'Postgres': 'Database',
    'Vector Store': 'Knowledge Base',
    'If': 'Condition Check',
    'Switch': 'Route Decision',
    'Merge': 'Data Merger',
    'HTTP Request': 'Web Service',
    'Code': 'Custom Logic',
    'Function': 'Data Transform'
  }

  for (const [key, value] of Object.entries(replacements)) {
    if (name.includes(key)) return value
  }

  return name
})

// Category labels
const categoryLabel = computed(() => {
  const labels: Record<string, string> = {
    'trigger': 'Process Initiator',
    'ai': 'Artificial Intelligence',
    'storage': 'Data Management',
    'logic': 'Business Logic',
    'communication': 'External Communication',
    'transform': 'Data Processing',
    'process': 'Business Operation'
  }
  return labels[nodeCategory.value] || 'Operation'
})

// Category badge
const categoryBadge = computed(() => {
  const badges: Record<string, string> = {
    'trigger': 'START',
    'ai': 'AI',
    'storage': 'DATA',
    'logic': 'LOGIC',
    'communication': 'COMM',
    'transform': 'TRANSFORM',
    'process': 'PROCESS'
  }
  return badges[nodeCategory.value] || 'NODE'
})

// Dynamic gradient backgrounds
const iconGradient = computed(() => {
  const gradients: Record<string, string> = {
    'trigger': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'ai': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'storage': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    'logic': 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    'communication': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    'transform': 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
    'process': 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)'
  }
  return gradients[nodeCategory.value] || gradients['process']
})

// Status bar color
const statusBarColor = computed(() => {
  if (props.data.status === 'active') return 'linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%)'
  if (props.data.status === 'success') return 'linear-gradient(90deg, #11998e 0%, #38ef7d 100%)'
  if (props.data.status === 'error') return 'linear-gradient(90deg, #eb3349 0%, #f45c43 100%)'
  if (props.data.status === 'pending') return 'linear-gradient(90deg, #f2994a 0%, #f2c94c 100%)'
  return 'linear-gradient(90deg, #bdc3c7 0%, #2c3e50 100%)'
})

// Status text
const statusText = computed(() => {
  const statusMap: Record<string, string> = {
    'active': 'RUNNING',
    'success': 'COMPLETED',
    'error': 'FAILED',
    'pending': 'WAITING',
    'idle': 'IDLE'
  }
  return statusMap[props.data.status || 'idle'] || 'READY'
})

// Props
const inputs = computed(() => props.data.inputs || ['input'])
const outputs = computed(() => props.data.outputs || ['output'])
const isActive = computed(() => props.data.status === 'active')
const hasError = computed(() => props.data.status === 'error')
const status = computed(() => props.data.status || 'idle')
const showMetrics = computed(() => nodeCategory.value !== 'trigger')
const executionCount = computed(() => props.data.executionCount)
const successRate = computed(() => props.data.successRate)
</script>

<style scoped>
.premium-node {
  min-width: 280px;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  border-radius: 16px;
  overflow: visible;
  box-shadow:
    0 10px 40px rgba(0, 0, 0, 0.3),
    0 2px 10px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.premium-node:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.4),
    0 5px 20px rgba(0, 0, 0, 0.3);
}

/* Status Bar */
.node-status-bar {
  height: 28px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  border-radius: 16px 16px 0 0;
  position: relative;
}

.status-indicator {
  width: 8px;
  height: 8px;
  margin-right: 8px;
}

.status-pulse {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: white;
  animation: pulse 2s infinite;
}

.pulse-active {
  animation: pulse 1s infinite;
  background: #00ff88;
}

.pulse-error {
  animation: pulse 0.5s infinite;
  background: #ff4444;
}

@keyframes pulse {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.1);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.status-text {
  font-size: 10px;
  font-weight: 600;
  color: white;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Body */
.node-body {
  padding: 20px;
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

/* Icon Section */
.node-icon-section {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.node-main-icon {
  width: 32px;
  height: 32px;
  color: white;
}

/* Content */
.node-content-section {
  flex: 1;
  min-width: 0;
}

.node-name {
  font-size: 16px;
  font-weight: 600;
  color: white;
  margin: 0 0 4px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-type {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 12px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Metrics */
.node-metrics {
  display: flex;
  gap: 20px;
}

.metric {
  display: flex;
  flex-direction: column;
}

.metric-value {
  font-size: 18px;
  font-weight: 700;
  color: white;
  line-height: 1;
}

.metric-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.6);
  text-transform: uppercase;
  margin-top: 2px;
}

/* Action Bar */
.node-action-bar {
  height: 32px;
  background: rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  border-radius: 0 0 16px 16px;
}

.connection-info {
  display: flex;
  align-items: center;
  gap: 4px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 11px;
}

.connection-icon {
  width: 14px;
  height: 14px;
}

.node-category-badge {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 9px;
  font-weight: 600;
  color: white;
  letter-spacing: 1px;
}

/* Handles */
.premium-handle {
  width: 12px !important;
  height: 12px !important;
  background: white !important;
  border: 2px solid #2a5298 !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.2s;
}

.handle-input {
  left: -6px;
}

.handle-output {
  right: -6px;
}

.premium-handle:hover {
  transform: scale(1.5);
  background: #00d2ff !important;
  box-shadow: 0 0 12px rgba(0, 210, 255, 0.6);
}

/* States */
.node-active {
  animation: activeGlow 2s infinite;
}

@keyframes activeGlow {
  0%, 100% {
    box-shadow:
      0 10px 40px rgba(0, 0, 0, 0.3),
      0 0 20px rgba(0, 210, 255, 0.4);
  }
  50% {
    box-shadow:
      0 10px 40px rgba(0, 0, 0, 0.3),
      0 0 40px rgba(0, 210, 255, 0.6);
  }
}

.node-error {
  border-color: #ff4444;
  animation: errorShake 0.5s;
}

@keyframes errorShake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

.node-selected {
  border: 2px solid #00d2ff;
  box-shadow:
    0 10px 40px rgba(0, 0, 0, 0.3),
    0 0 30px rgba(0, 210, 255, 0.5);
}

/* Category-specific styling */
.node-category-trigger .node-body {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
}

.node-category-ai .node-body {
  background: linear-gradient(135deg, rgba(240, 147, 251, 0.1) 0%, rgba(245, 87, 108, 0.1) 100%);
}

.node-category-storage .node-body {
  background: linear-gradient(135deg, rgba(79, 172, 254, 0.1) 0%, rgba(0, 242, 254, 0.1) 100%);
}
</style>