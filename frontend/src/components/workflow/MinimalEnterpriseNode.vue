<template>
  <div class="node-wrapper">
    <!-- Shape with icon only -->
    <div
      :class="[
        'minimal-node',
        `shape-${nodeShape}`,
        `category-${nodeCategory}`,
        {
          'node-active': isActive,
          'node-error': hasError,
          'node-selected': selected
        }
      ]"
    >
      <!-- Status Dot -->
      <div class="status-dot" :class="`status-${status}`"></div>

      <!-- Icon only inside shape -->
      <Icon :icon="nodeIcon" class="node-icon" />
    </div>

    <!-- Text label OUTSIDE below shape -->
    <div class="node-label">
      <div class="node-title">{{ shortName }}</div>
      <div class="node-badge">{{ categoryBadge }}</div>
    </div>

    <!-- Handles attached to shape -->
    <Handle
      v-for="(handle, idx) in inputs"
      :key="`in-${idx}`"
      type="target"
      :position="Position.Left"
      :id="`input-${idx}`"
      class="minimal-handle handle-input"
    />

    <Handle
      v-for="(handle, idx) in outputs"
      :key="`out-${idx}`"
      type="source"
      :position="Position.Right"
      :id="`output-${idx}`"
      class="minimal-handle handle-output"
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

// Detection based on original n8n logic
const isToolNode = (nodeName: string, nodeType: string): boolean => {
  const name = nodeName.toLowerCase()
  const type = nodeType.toLowerCase()

  // External tools/services (were circles in n8n)
  const toolPatterns = [
    'openai', 'chat model', 'embeddings', 'http request', 'webhook',
    'gmail', 'slack', 'telegram', 'google', 'microsoft', 'api',
    'buffer memory', 'retriever', 'reranker', 'parcelapp'
  ]

  return toolPatterns.some(pattern => name.includes(pattern) || type.includes(pattern))
}

const isTriggerNode = (nodeName: string, nodeType: string): boolean => {
  const name = nodeName.toLowerCase()
  const type = nodeType.toLowerCase()

  return type.includes('trigger') || name.includes('trigger') ||
         type.includes('webhook') || name.includes('schedule')
}

const isStorageNode = (nodeName: string, nodeType: string): boolean => {
  const name = nodeName.toLowerCase()
  const type = nodeType.toLowerCase()

  return type === 'storage' || type.includes('database') ||
         type.includes('vectorstore') || type.includes('postgres') ||
         name.includes('vector store') || name.includes('qdrant')
}

const isAINode = (nodeName: string, nodeType: string): boolean => {
  const name = nodeName.toLowerCase()
  const type = nodeType.toLowerCase()

  return type === 'ai' || type.includes('agent') ||
         type.includes('langchain') || name.includes('ai -') ||
         name.includes('analizza') || name.includes('interpreta')
}

// Get node shape based on classification
const nodeShape = computed(() => {
  const name = props.data.label
  const type = props.data.type
  const nodeType = props.data.nodeType || ''

  // Priority order matters!
  if (isTriggerNode(name, nodeType)) return 'diamond'      // Was special in n8n
  if (isStorageNode(name, nodeType)) return 'cylinder'     // Database shape
  if (isAINode(name, nodeType)) return 'hexagon'          // AI gets hexagon
  if (isToolNode(name, nodeType)) return 'pill'           // Was circle -> now pill

  // Default processes/actions
  return 'rectangle' // Was square -> keep rectangle
})

// Simplified category for coloring
const nodeCategory = computed(() => {
  const shape = nodeShape.value

  if (shape === 'diamond') return 'trigger'
  if (shape === 'cylinder') return 'storage'
  if (shape === 'hexagon') return 'ai'
  if (shape === 'pill') return 'tool'

  return 'process'
})

// Icons based on shape/category
const nodeIcon = computed(() => {
  const iconMap: Record<string, string> = {
    'trigger': 'ph:lightning-fill',      // Diamond - trigger/start
    'ai': 'ph:brain-fill',               // Hexagon - AI/agents
    'storage': 'ph:database-fill',       // Cylinder - database
    'tool': 'ph:plug-fill',              // Pill - external tools
    'process': 'ph:gear-fill'            // Rectangle - processes
  }
  return iconMap[nodeCategory.value] || 'ph:square-fill'
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
.node-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.minimal-node {
  position: relative;
  width: 60px;
  height: 60px;
  background: rgba(30, 41, 59, 0.95);
  border: 2px solid rgba(100, 116, 139, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  backdrop-filter: blur(8px);
}

/* SHAPE DEFINITIONS - Clean geometric shapes */
.shape-diamond {
  transform: rotate(45deg);
  border-radius: 8px;
}

.shape-diamond .node-icon {
  transform: rotate(-45deg);
}

.shape-cylinder {
  border-radius: 50%;
  border-top-width: 3px;
  border-bottom-width: 3px;
}

.shape-hexagon {
  clip-path: polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%);
}

.shape-pill {
  border-radius: 30px;
  width: 80px;
}

.shape-rectangle {
  border-radius: 8px;
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

/* Icon centered in shape */
.node-icon {
  width: 24px;
  height: 24px;
  color: white;
}

/* Label outside shape */
.node-label {
  text-align: center;
  max-width: 100px;
  pointer-events: none;
}

.node-title {
  font-size: 12px;
  font-weight: 500;
  color: #f1f5f9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2;
  margin-bottom: 2px;
}

.node-badge {
  font-size: 9px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Handles */
.minimal-handle {
  position: absolute;
  width: 8px !important;
  height: 8px !important;
  background: #475569 !important;
  border: 1px solid #1e293b !important;
  border-radius: 50%;
  top: 50%;
  transform: translateY(-50%);
}

.handle-input {
  left: -4px;
}

.handle-output {
  right: -4px;
}

.minimal-handle:hover {
  background: #3b82f6 !important;
  transform: translateY(-50%) scale(1.3);
}

/* Category-specific colors with shapes */
.category-trigger {
  --node-color: #8b5cf6;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(30, 41, 59, 0.95));
}

.category-ai {
  --node-color: #ec4899;
  border: 2px solid #ec4899;
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.1), rgba(30, 41, 59, 0.95));
}

.category-storage {
  --node-color: #06b6d4;
  border-color: #06b6d4;
  background: linear-gradient(180deg, rgba(6, 182, 212, 0.1), rgba(30, 41, 59, 0.95));
}

.category-tool {
  --node-color: #f59e0b;
  border: 1px solid #f59e0b;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(30, 41, 59, 0.95));
}

.category-process {
  --node-color: #6b7280;
  border-left: 3px solid #6b7280;
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