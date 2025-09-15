<template>
  <div
    :class="[
      'enterprise-node',
      nodeShapeClass,
      `node-type-${nodeType}`,
      { 'node-active': isActive, 'node-error': hasError }
    ]"
    :style="nodeStyle"
  >
    <!-- Glass overlay effect -->
    <div class="node-glass-overlay"></div>

    <!-- Icon Container -->
    <div class="node-icon-wrapper">
      <component
        :is="nodeIcon"
        class="node-icon"
        :style="{ color: iconColor }"
      />
    </div>

    <!-- Node Content -->
    <div class="node-content">
      <h4 class="node-title">{{ businessTitle }}</h4>
      <p class="node-subtitle">{{ nodeSubtitle }}</p>
    </div>

    <!-- Status Indicator -->
    <div v-if="status" class="node-status">
      <div :class="['status-dot', `status-${status}`]"></div>
    </div>

    <!-- Handles for connections -->
    <Handle
      v-for="handle in handles.inputs"
      :key="`input-${handle.id}`"
      type="target"
      :position="Position.Left"
      :id="handle.id"
      :style="handleStyle"
      class="enterprise-handle handle-input"
    />

    <Handle
      v-for="handle in handles.outputs"
      :key="`output-${handle.id}`"
      type="source"
      :position="Position.Right"
      :id="handle.id"
      :style="handleStyle"
      class="enterprise-handle handle-output"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import {
  Zap, Database, Cpu, Send, HardDrive,
  GitBranch, Cloud, Bot, Globe, Clock,
  Filter, Layers, Package, Server, Shield
} from 'lucide-vue-next'

interface Props {
  data: {
    label: string
    type: string
    status?: 'active' | 'pending' | 'error' | 'success'
    category?: string
    hasError?: boolean
    inputs?: string[]
    outputs?: string[]
  }
  selected?: boolean
}

const props = defineProps<Props>()

// Business terminology mapping
const businessTerms: Record<string, string> = {
  // Node types
  'webhook': 'API Endpoint',
  'schedule': 'Time Automation',
  'manual': 'Manual Process',
  'http': 'Web Service',
  'postgres': 'Data Store',
  'function': 'Business Logic',
  'if': 'Decision Point',
  'merge': 'Data Consolidation',
  'split': 'Data Distribution',
  'openai': 'AI Processing',
  'email': 'Communication',
  'slack': 'Team Notification',

  // Categories
  'trigger': 'Process Initiator',
  'action': 'Business Operation',
  'logic': 'Process Logic',
  'storage': 'Data Management',
  'output': 'Result Delivery'
}

// Get business-friendly title
const businessTitle = computed(() => {
  const label = props.data.label.toLowerCase()
  for (const [key, value] of Object.entries(businessTerms)) {
    if (label.includes(key)) return value
  }
  return props.data.label
})

// Node subtitle based on category
const nodeSubtitle = computed(() => {
  const category = props.data.category || detectCategory(props.data.type)
  return businessTerms[category] || category
})

// Detect category from node type
const detectCategory = (type: string): string => {
  if (type.includes('trigger') || type.includes('webhook') || type.includes('schedule')) {
    return 'trigger'
  }
  if (type.includes('database') || type.includes('postgres') || type.includes('mongodb')) {
    return 'storage'
  }
  if (type.includes('if') || type.includes('switch') || type.includes('merge')) {
    return 'logic'
  }
  if (type.includes('email') || type.includes('slack') || type.includes('http')) {
    return 'output'
  }
  return 'action'
}

// Node type for styling
const nodeType = computed(() => detectCategory(props.data.type))

// Shape class based on node type
const nodeShapeClass = computed(() => {
  const shapeMap: Record<string, string> = {
    'trigger': 'shape-rounded-rect',
    'storage': 'shape-cylinder',
    'logic': 'shape-hexagon',
    'output': 'shape-chevron',
    'action': 'shape-pill',
    'ai': 'shape-octagon'
  }

  if (props.data.type.includes('openai') || props.data.type.includes('gpt')) {
    return shapeMap['ai']
  }

  return shapeMap[nodeType.value] || 'shape-rounded-rect'
})

// Icon selection based on node type
const nodeIcon = computed(() => {
  const iconMap: Record<string, any> = {
    'webhook': Globe,
    'schedule': Clock,
    'database': Database,
    'postgres': Database,
    'openai': Bot,
    'if': GitBranch,
    'merge': Layers,
    'split': Filter,
    'http': Cloud,
    'email': Send,
    'function': Cpu,
    'default': Package
  }

  const type = props.data.type.toLowerCase()
  for (const [key, icon] of Object.entries(iconMap)) {
    if (type.includes(key)) return icon
  }
  return iconMap['default']
})

// Dynamic colors based on node type
const iconColor = computed(() => {
  const colorMap: Record<string, string> = {
    'trigger': '#3b82f6',
    'storage': '#64748b',
    'logic': '#8b5cf6',
    'output': '#f59e0b',
    'action': '#06b6d4',
    'ai': '#ec4899'
  }
  return colorMap[nodeType.value] || '#3b82f6'
})

// Node styling
const nodeStyle = computed(() => ({
  '--node-color': iconColor.value,
  minWidth: '200px',
  minHeight: '80px'
}))

// Handle styling
const handleStyle = {
  width: '8px',
  height: '8px',
  background: '#3b82f6',
  border: '2px solid #1e293b'
}

// Process handles
const handles = computed(() => ({
  inputs: (props.data.inputs || ['input']).map(id => ({ id })),
  outputs: (props.data.outputs || ['output']).map(id => ({ id }))
}))

const isActive = computed(() => props.data.status === 'active')
const hasError = computed(() => props.data.hasError || props.data.status === 'error')
const status = computed(() => props.data.status)
</script>

<style scoped>
.enterprise-node {
  position: relative;
  padding: 16px 20px;
  background: linear-gradient(135deg, #1e293b, #334155);
  border: 1px solid rgba(148, 163, 184, 0.3);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: visible;
}

.node-glass-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg,
    rgba(59, 130, 246, 0.05),
    rgba(139, 92, 246, 0.05)
  );
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  pointer-events: none;
}

/* Professional Shapes */
.shape-rounded-rect {
  border-radius: 12px;
}

.shape-pill {
  border-radius: 50px;
}

.shape-hexagon {
  clip-path: polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%);
}

.shape-octagon {
  clip-path: polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%);
}

.shape-chevron {
  clip-path: polygon(0% 20%, 75% 20%, 100% 50%, 75% 80%, 0% 80%, 15% 50%);
}

.shape-cylinder {
  border-radius: 50px/20px;
  border-top: 3px solid rgba(148, 163, 184, 0.3);
  border-bottom: 3px solid rgba(148, 163, 184, 0.3);
}

/* Icon Styling */
.node-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  backdrop-filter: blur(4px);
}

.node-icon {
  width: 20px;
  height: 20px;
}

/* Content Styling */
.node-content {
  position: relative;
  z-index: 2;
}

.node-title {
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
  margin: 0 0 4px 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.node-subtitle {
  font-size: 11px;
  color: #94a3b8;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Status Indicator */
.node-status {
  position: absolute;
  top: 8px;
  right: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-active { background: #06b6d4; }
.status-pending { background: #f59e0b; }
.status-error { background: #f43f5e; }
.status-success { background: #06b6d4; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Handle Styling */
.enterprise-handle {
  position: absolute;
  width: 10px !important;
  height: 10px !important;
  background: #3b82f6 !important;
  border: 2px solid #1e293b !important;
  border-radius: 50%;
  transition: all 0.2s;
}

.handle-input {
  left: -5px;
}

.handle-output {
  right: -5px;
}

.enterprise-handle:hover {
  transform: scale(1.3);
  background: #60a5fa !important;
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.6);
}

/* Hover Effects */
.enterprise-node:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(59, 130, 246, 0.25);
  border-color: var(--node-color);
}

.enterprise-node:hover .node-glass-overlay {
  background: linear-gradient(135deg,
    rgba(59, 130, 246, 0.1),
    rgba(139, 92, 246, 0.1)
  );
}

/* Active State */
.node-active {
  border-color: #3b82f6;
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
}

/* Error State */
.node-error {
  border-color: #f43f5e;
  animation: error-pulse 1s infinite;
}

@keyframes error-pulse {
  0%, 100% { box-shadow: 0 0 20px rgba(244, 63, 94, 0.3); }
  50% { box-shadow: 0 0 30px rgba(244, 63, 94, 0.6); }
}
</style>