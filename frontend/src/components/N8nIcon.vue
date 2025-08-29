<template>
  <div 
    v-if="iconSrc" 
    class="node-icon" 
    :class="className"
  >
    <img :src="iconSrc" alt="Node Icon" />
  </div>
  <div v-else class="node-icon-fallback" :class="className">
    <component :is="fallbackIcon" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { 
  Settings, Database, Mail, Bot, Globe, Code, Zap, 
  Brain, FileText, Link, Clock, Play, MessageSquare, Edit
} from 'lucide-vue-next'
import { iconMap } from '../config/icon-map.js'

interface Props {
  nodeType?: string
  fallback?: string
  size?: string
}

const props = withDefaults(defineProps<Props>(), {
  nodeType: '',
  fallback: 'Settings',
  size: 'w-8 h-8'
})

const className = computed(() => props.size)

const iconSrc = computed(() => {
  if (!props.nodeType || props.nodeType === 'undefined' || props.nodeType === 'null') {
    return null
  }
  
  // Try to get icon from map
  const iconValue = iconMap[props.nodeType]
  
  // If it's an imported SVG file (contains .svg or blob:), return it for <img>
  if (iconValue && (typeof iconValue === 'string' && (iconValue.includes('.svg') || iconValue.startsWith('blob:') || iconValue.startsWith('/_assets/')))) {
    return iconValue
  }
  
  // If it's a Lucide icon name, return null (will use fallback)
  return null
})

const lucideIcon = computed(() => {
  const iconValue = iconMap[props.nodeType]
  
  // If it's a Lucide icon name (string without .svg), return it
  if (iconValue && typeof iconValue === 'string' && !iconValue.includes('.svg') && !iconValue.startsWith('blob:') && !iconValue.startsWith('/_assets/')) {
    return iconValue
  }
  
  // Otherwise use the fallback prop
  return props.fallback
})

const fallbackIcon = computed(() => {
  const iconComponentMap = {
    Settings, Database, Mail, Bot, Globe, Code, Zap,
    Brain, FileText, Link, Clock, Play, MessageSquare, Edit
  }
  return iconComponentMap[lucideIcon.value as keyof typeof iconComponentMap] || Settings
})
</script>

<style scoped>
.n8n-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  padding: 8px;
  box-sizing: border-box;
}

.node-icon img {
  width: auto;
  height: auto;
  max-width: 100%;
  max-height: 100%;
  display: block;
}

.n8n-icon-fallback {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  width: 100%;
  height: 100%;
  padding: 0;
}

.node-icon-fallback svg,
.n8n-icon-fallback svg {
  margin-top: 1px !important;
  margin-left: 1px !important;
  width: 48px !important;
  height: 48px !important;
  stroke: #FF6B35 !important;
  stroke-width: 2 !important;
  fill: none !important;
}

.node-icon-fallback :deep(svg),
.n8n-icon-fallback :deep(svg) {
  margin-top: 1px !important;
  margin-left: 1px !important;
  width: 48px !important;
  height: 48px !important;
  stroke: #FF6B35 !important;
  stroke-width: 2 !important;
  fill: none !important;
}
</style>