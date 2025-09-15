<template>
  <div
    :class="[
      'minimal-node',
      `node-${nodeCategory}`,
      {
        'node-active': isActive,
        'node-error': hasError,
        'node-selected': selected
      }
    ]"
  >
    <!-- Compact Status Dot -->
    <div class="status-dot" :class="`status-${status}`"></div>

    <!-- Icon Badge -->
    <div class="icon-badge" :style="{ background: categoryColor }">
      <Icon :icon="nodeIcon" class="node-icon" />
    </div>

    <!-- Minimal Content -->
    <div class="node-content">
      <div class="node-title">{{ shortName }}</div>
      <div class="node-badge">{{ categoryBadge }}</div>
    </div>

    <!-- Handles - Simplified -->
    <Handle
      v-for="(handle, idx) in inputs"
      :key="`in-${idx}`"
      type="target"
      :position="Position.Left"
      :id="`input-${idx}`"
      class="minimal-handle"
      :style="{ top: `${50}%` }"
    />

    <Handle
      v-for="(handle, idx) in outputs"
      :key="`out-${idx}`"
      type="source"
      :position="Position.Right"
      :id="`output-${idx}`"
      class="minimal-handle"
      :style="{ top: `${50}%` }"
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
    inputs?: string[]
    outputs?: string[]
  }
  selected?: boolean
}

const props = defineProps<Props>()

// Simplified category detection
const nodeCategory = computed(() => {
  const type = props.data.type
  const nodeType = props.data.nodeType || ''

  if (type === 'ai' || nodeType.includes('agent') || nodeType.includes('openai')) return 'ai'
  if (type === 'storage' || nodeType.includes('database') || nodeType.includes('vectorStore')) return 'storage'
  if (type === 'trigger' || nodeType.includes('trigger') || nodeType.includes('webhook')) return 'trigger'
  if (nodeType.includes('if') || nodeType.includes('switch')) return 'logic'
  if (nodeType.includes('http') || nodeType.includes('email')) return 'output'
  if (nodeType.includes('code') || nodeType.includes('function')) return 'transform'

  return 'process'
})

// Minimal icons
const nodeIcon = computed(() => {
  const iconMap: Record<string, string> = {
    'trigger': 'ph:play-fill',
    'ai': 'ph:robot-fill',
    'storage': 'ph:database-fill',
    'logic': 'ph:git-branch-fill',
    'output': 'ph:arrow-square-out-fill',
    'transform': 'ph:code-simple-fill',
    'process': 'ph:circle-fill'
  }
  return iconMap[nodeCategory.value] || 'ph:circle-fill'
})

// Short names for compact display
const shortName = computed(() => {
  const name = props.data.label

  // Common abbreviations
  const abbreviations: Record<string, string> = {
    'Webhook': 'Webhook',
    'Schedule Trigger': 'Schedule',
    'Manual Trigger': 'Manual',
    'OpenAI': 'AI',
    'Agent': 'Agent',
    'Postgres': 'DB',
    'Vector Store': 'Vector',
    'If': 'If',
    'Switch': 'Switch',
    'Merge': 'Merge',
    'HTTP Request': 'HTTP',
    'Code': 'Code',
    'Function': 'Func',
    'Email': 'Email',
    'Slack': 'Slack'
  }

  for (const [key, value] of Object.entries(abbreviations)) {
    if (name.includes(key)) return value
  }

  // Truncate long names
  return name.length > 15 ? name.substring(0, 12) + '...' : name
})

// Ultra-compact badges
const categoryBadge = computed(() => {
  const badges: Record<string, string> = {
    'trigger': 'IN',
    'ai': 'AI',
    'storage': 'DB',
    'logic': 'IF',
    'output': 'OUT',
    'transform': 'FN',
    'process': '•'
  }
  return badges[nodeCategory.value] || '•'
})

// Simplified colors
const categoryColor = computed(() => {
  const colors: Record<string, string> = {
    'trigger': '#8b5cf6',  // Purple
    'ai': '#ec4899',       // Pink
    'storage': '#06b6d4',  // Cyan
    'logic': '#10b981',    // Green
    'output': '#f59e0b',   // Amber
    'transform': '#3b82f6', // Blue
    'process': '#6b7280'   // Gray
  }
  return colors[nodeCategory.value] || '#6b7280'
})

// Simplified props
const inputs = computed(() => props.data.inputs || ['input'])
const outputs = computed(() => props.data.outputs || ['output'])
const isActive = computed(() => props.data.status === 'active')
const hasError = computed(() => props.data.status === 'error')
const status = computed(() => props.data.status || 'idle')
</script>

<style scoped>
.minimal-node {
  position: relative;
  width: 160px;
  height: 56px;
  background: rgba(30, 41, 59, 0.95);
  border: 1px solid rgba(100, 116, 139, 0.5);
  border-radius: 8px;
  display: flex;
  align-items: center;
  padding: 0 10px;
  gap: 10px;
  transition: all 0.2s ease;
  backdrop-filter: blur(8px);
}

.minimal-node:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  border-color: var(--node-color);
}

/* Status Dot */
.status-dot {
  position: absolute;
  top: 6px;
  right: 6px;
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

.status-pending {
  background: #f59e0b;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Icon Badge */
.icon-badge {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  opacity: 0.9;
}

.node-icon {
  width: 18px;
  height: 18px;
  color: white;
}

/* Content */
.node-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.node-title {
  font-size: 13px;
  font-weight: 500;
  color: #f1f5f9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2;
}

.node-badge {
  font-size: 9px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Handles */
.minimal-handle {
  width: 8px !important;
  height: 8px !important;
  background: #475569 !important;
  border: 1px solid #1e293b !important;
  border-radius: 50%;
}

.minimal-handle:hover {
  background: #3b82f6 !important;
  transform: scale(1.3);
}

/* Category-specific accent colors */
.node-trigger {
  --node-color: #8b5cf6;
}

.node-ai {
  --node-color: #ec4899;
  border-left: 2px solid #ec4899;
}

.node-storage {
  --node-color: #06b6d4;
  border-left: 2px solid #06b6d4;
}

.node-logic {
  --node-color: #10b981;
  border-left: 2px solid #10b981;
}

.node-output {
  --node-color: #f59e0b;
  border-left: 2px solid #f59e0b;
}

.node-transform {
  --node-color: #3b82f6;
  border-left: 2px solid #3b82f6;
}

.node-process {
  --node-color: #6b7280;
}

/* States */
.node-active {
  border-color: #3b82f6;
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.3);
}

.node-error {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

.node-selected {
  border-color: #3b82f6;
  border-width: 2px;
  box-shadow: 0 0 16px rgba(59, 130, 246, 0.4);
}
</style>