<template>
  <div class="business-node-container">
    <!-- Main Card -->
    <div
      :class="[
        'business-card',
        `type-${nodeCategory}`,
        {
          'is-running': isActive,
          'has-error': hasError,
          'is-selected': selected
        }
      ]"
    >
      <!-- Category Header Strip -->
      <div class="category-header" :style="{ background: categoryGradient }">
        <span class="category-text">{{ categoryLabel }}</span>
        <div class="status-indicator" :class="`status-${status}`"></div>
      </div>

      <!-- Main Content Area -->
      <div class="card-body">
        <!-- Left Icon Section -->
        <div class="icon-section">
          <div class="icon-container" :style="{ background: categoryColor + '20' }">
            <Icon :icon="nodeIcon" class="main-icon" :style="{ color: categoryColor }" />
          </div>
        </div>

        <!-- Right Content Section -->
        <div class="content-section">
          <h4 class="node-name">{{ displayName }}</h4>
          <p class="node-description">{{ nodeDescription }}</p>

          <!-- Mini Stats Bar -->
          <div v-if="showStats" class="stats-bar">
            <div class="stat-item">
              <Icon icon="ph:play-circle" class="stat-icon" />
              <span>{{ executionCount || 0 }}</span>
            </div>
            <div class="stat-item">
              <Icon icon="ph:check-circle" class="stat-icon success" />
              <span>{{ successRate || 100 }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Connection Points Indicators -->
      <div class="connection-indicators">
        <div class="conn-in" v-if="hasInputs">
          <Icon icon="ph:arrow-right" class="conn-icon" />
        </div>
        <div class="conn-out" v-if="hasOutputs">
          <Icon icon="ph:arrow-right" class="conn-icon" />
        </div>
      </div>
    </div>

    <!-- Handles with proper positioning -->
    <template v-if="nodeCategory === 'ai'">
      <!-- AI nodes: complex handle setup -->
      <Handle
        type="target"
        :position="Position.Left"
        id="input-0"
        class="business-handle"
        :style="{ top: '50%' }"
      />
      <Handle
        v-for="idx in 3"
        :key="`tool-in-${idx}`"
        type="target"
        :position="Position.Bottom"
        :id="`tool-${idx - 1}`"
        class="business-handle"
        :style="{ left: `${20 + (idx - 1) * 30}%`, bottom: '-6px' }"
      />
      <Handle
        type="source"
        :position="Position.Right"
        id="output-0"
        class="business-handle"
        :style="{ top: '50%' }"
      />
    </template>

    <template v-else-if="nodeCategory === 'storage'">
      <!-- Storage: top and bottom -->
      <Handle
        type="target"
        :position="Position.Top"
        id="input-0"
        class="business-handle"
        :style="{ left: '50%', top: '-6px' }"
      />
      <Handle
        type="source"
        :position="Position.Bottom"
        id="output-0"
        class="business-handle"
        :style="{ left: '50%', bottom: '-6px' }"
      />
    </template>

    <template v-else>
      <!-- Default: left and right -->
      <Handle
        type="target"
        :position="Position.Left"
        id="input-0"
        class="business-handle"
        :style="{ top: '50%', left: '-6px' }"
      />
      <Handle
        type="source"
        :position="Position.Right"
        id="output-0"
        class="business-handle"
        :style="{ top: '50%', right: '-6px' }"
      />
    </template>
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

// Category detection
const nodeCategory = computed(() => {
  const type = props.data.type
  const nodeType = props.data.nodeType || ''
  const label = props.data.label.toLowerCase()

  // Clear categorization
  if (type === 'trigger' || nodeType.includes('trigger')) return 'trigger'
  if (type === 'ai' || nodeType.includes('agent') || nodeType.includes('openai')) return 'ai'
  if (type === 'storage' || nodeType.includes('database') || nodeType.includes('vector')) return 'storage'
  if (nodeType.includes('if') || nodeType.includes('switch')) return 'logic'
  if (nodeType.includes('http') || nodeType.includes('webhook')) return 'integration'
  if (nodeType.includes('code') || nodeType.includes('function')) return 'transform'

  // Check by label patterns
  if (label.includes('email') || label.includes('slack')) return 'communication'

  return 'process'
})

// Modern business icons
const nodeIcon = computed(() => {
  const iconMap: Record<string, string> = {
    'trigger': 'fluent:rocket-24-filled',
    'ai': 'fluent:brain-circuit-24-filled',
    'storage': 'fluent:database-24-filled',
    'logic': 'fluent:branch-24-filled',
    'integration': 'fluent:plug-connected-24-filled',
    'transform': 'fluent:code-24-filled',
    'communication': 'fluent:mail-24-filled',
    'process': 'fluent:settings-24-filled'
  }
  return iconMap[nodeCategory.value] || 'fluent:circle-24-filled'
})

// Business-friendly display names
const displayName = computed(() => {
  const name = props.data.label

  // Transform technical names to business terms
  const nameMap: Record<string, string> = {
    'Webhook': 'Data Receiver',
    'Schedule Trigger': 'Automated Schedule',
    'Manual Trigger': 'Manual Start',
    'OpenAI': 'AI Assistant',
    'Chat Model': 'AI Conversation',
    'Agent': 'Smart Agent',
    'Postgres': 'Database',
    'Vector Store': 'Knowledge Base',
    'HTTP Request': 'Web Service',
    'If': 'Decision Point',
    'Switch': 'Multi-Route',
    'Code': 'Custom Logic',
    'Function': 'Processing'
  }

  for (const [key, value] of Object.entries(nameMap)) {
    if (name.includes(key)) return value
  }

  return name
})

// Node descriptions
const nodeDescription = computed(() => {
  const descMap: Record<string, string> = {
    'trigger': 'Initiates the process',
    'ai': 'AI-powered processing',
    'storage': 'Data persistence layer',
    'logic': 'Business rule evaluation',
    'integration': 'External system connection',
    'transform': 'Data transformation',
    'communication': 'Message delivery',
    'process': 'Business operation'
  }
  return descMap[nodeCategory.value] || 'Processing step'
})

// Category labels
const categoryLabel = computed(() => {
  const labels: Record<string, string> = {
    'trigger': 'START POINT',
    'ai': 'ARTIFICIAL INTELLIGENCE',
    'storage': 'DATA STORAGE',
    'logic': 'BUSINESS LOGIC',
    'integration': 'INTEGRATION',
    'transform': 'TRANSFORMATION',
    'communication': 'COMMUNICATION',
    'process': 'PROCESSING'
  }
  return labels[nodeCategory.value] || 'OPERATION'
})

// Modern color scheme
const categoryColor = computed(() => {
  const colors: Record<string, string> = {
    'trigger': '#8b5cf6',     // Purple
    'ai': '#ec4899',          // Pink
    'storage': '#0ea5e9',     // Sky
    'logic': '#10b981',       // Emerald
    'integration': '#f59e0b', // Amber
    'transform': '#3b82f6',   // Blue
    'communication': '#ef4444', // Red
    'process': '#6b7280'      // Gray
  }
  return colors[nodeCategory.value] || '#6b7280'
})

// Gradient backgrounds
const categoryGradient = computed(() => {
  const color = categoryColor.value
  return `linear-gradient(135deg, ${color}, ${color}dd)`
})

// Computed properties
const isActive = computed(() => props.data.status === 'active')
const hasError = computed(() => props.data.status === 'error')
const status = computed(() => props.data.status || 'idle')
const hasInputs = computed(() => (props.data.inputs?.length || 0) > 0)
const hasOutputs = computed(() => (props.data.outputs?.length || 0) > 0)
const showStats = computed(() => nodeCategory.value !== 'trigger')
const executionCount = computed(() => props.data.executionCount)
const successRate = computed(() => props.data.successRate)
</script>

<style scoped>
.business-node-container {
  position: relative;
}

.business-card {
  width: 240px;
  min-height: 100px;
  background: linear-gradient(145deg, #1e293b, #0f172a);
  border: 1px solid #334155;
  border-radius: 12px;
  overflow: hidden;
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  transition: all 0.2s ease;
}

.business-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 10px 15px -3px rgba(0, 0, 0, 0.2),
    0 4px 6px -2px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* Category Header */
.category-header {
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.category-text {
  font-size: 9px;
  font-weight: 700;
  color: white;
  letter-spacing: 0.5px;
  opacity: 0.9;
}

.status-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #64748b;
}

.status-active {
  background: #3b82f6;
  animation: pulse 2s infinite;
}

.status-success {
  background: #10b981;
}

.status-error {
  background: #ef4444;
  animation: pulse 0.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Card Body */
.card-body {
  padding: 12px;
  display: flex;
  gap: 12px;
}

/* Icon Section */
.icon-section {
  flex-shrink: 0;
}

.icon-container {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.main-icon {
  width: 24px;
  height: 24px;
}

/* Content Section */
.content-section {
  flex: 1;
  min-width: 0;
}

.node-name {
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
  margin: 0 0 4px 0;
  line-height: 1.2;
}

.node-description {
  font-size: 11px;
  color: #64748b;
  margin: 0 0 8px 0;
  line-height: 1.3;
}

/* Stats Bar */
.stats-bar {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #94a3b8;
}

.stat-icon {
  width: 14px;
  height: 14px;
  opacity: 0.7;
}

.stat-icon.success {
  color: #10b981;
}

/* Connection Indicators */
.connection-indicators {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 100%;
  display: flex;
  justify-content: space-between;
  pointer-events: none;
}

.conn-in,
.conn-out {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.3;
}

.conn-in {
  margin-left: -10px;
}

.conn-out {
  margin-right: -10px;
  transform: rotate(180deg);
}

.conn-icon {
  width: 16px;
  height: 16px;
  color: #64748b;
}

/* Handles */
.business-handle {
  position: absolute;
  width: 10px !important;
  height: 10px !important;
  background: #475569 !important;
  border: 2px solid #1e293b !important;
  border-radius: 50%;
  z-index: 10;
}

.business-handle:hover {
  background: #3b82f6 !important;
  transform: scale(1.4);
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.5);
}

/* States */
.is-running {
  border-color: #3b82f6;
  animation: running-glow 2s infinite;
}

@keyframes running-glow {
  0%, 100% {
    box-shadow:
      0 4px 6px -1px rgba(0, 0, 0, 0.1),
      0 0 20px rgba(59, 130, 246, 0.2);
  }
  50% {
    box-shadow:
      0 4px 6px -1px rgba(0, 0, 0, 0.1),
      0 0 30px rgba(59, 130, 246, 0.4);
  }
}

.has-error {
  border-color: #ef4444;
  background: linear-gradient(145deg, #1e293b, #0f172a),
              linear-gradient(145deg, rgba(239, 68, 68, 0.05), rgba(239, 68, 68, 0.02));
}

.is-selected {
  border: 2px solid #3b82f6;
  box-shadow:
    0 10px 15px -3px rgba(0, 0, 0, 0.2),
    0 0 25px rgba(59, 130, 246, 0.3);
}

/* Type-specific styling */
.type-trigger .card-body {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.05), transparent);
}

.type-ai .card-body {
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.05), transparent);
}

.type-storage .card-body {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.05), transparent);
}
</style>