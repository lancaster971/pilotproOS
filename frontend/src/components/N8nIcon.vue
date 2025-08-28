<template>
  <div 
    v-if="svgContent" 
    class="n8n-icon" 
    :class="className"
    v-html="svgContent"
  ></div>
  <div v-else class="n8n-icon-fallback" :class="className">
    <component :is="fallbackIcon" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { 
  Settings, Database, Mail, Bot, Globe, Code, Zap, 
  Brain, FileText, Link, Clock, Play, MessageSquare
} from 'lucide-vue-next'

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

const svgContent = ref<string>('')

const className = computed(() => props.size)

const fallbackIcon = computed(() => {
  const iconMap = {
    Settings, Database, Mail, Bot, Globe, Code, Zap,
    Brain, FileText, Link, Clock, Play, MessageSquare
  }
  return iconMap[props.fallback as keyof typeof iconMap] || Settings
})

const loadIcon = async () => {
  if (!props.nodeType || props.nodeType === 'undefined' || props.nodeType === 'null') {
    svgContent.value = ''
    return
  }
  
  try {
    const url = `http://localhost:3001/api/n8n-icons/${encodeURIComponent(props.nodeType)}`
    console.log(`🎨 N8nIcon loading: ${props.nodeType} -> ${url}`)
    
    const response = await fetch(url, {
      cache: 'no-cache'
    })
    
    if (response.ok) {
      const svg = await response.text()
      
      if (svg.includes('<svg')) {
        console.log(`✅ N8nIcon loaded: ${props.nodeType}`, svg.substring(0, 100) + '...')
        svgContent.value = svg
      } else {
        console.warn(`⚠️ N8nIcon invalid SVG: ${props.nodeType}`, svg)
        svgContent.value = ''
      }
    } else {
      console.error(`❌ N8nIcon fetch failed: ${props.nodeType}, status: ${response.status}`)
      svgContent.value = ''
    }
  } catch (error) {
    console.error(`❌ N8nIcon error: ${props.nodeType}`, error)
    svgContent.value = ''
  }
}

onMounted(() => {
  loadIcon()
})

watch(() => props.nodeType, () => {
  loadIcon()
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

.n8n-icon :deep(svg) {
  width: 28px !important;
  height: 28px !important;
  min-width: 28px;
  min-height: 28px;
  max-width: 28px;
  max-height: 28px;
  display: block;
}

.n8n-icon-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  padding: 8px;
  box-sizing: border-box;
}

.n8n-icon-fallback :deep(svg) {
  width: 28px !important;
  height: 28px !important;
  min-width: 28px;
  min-height: 28px;
  max-width: 28px;
  max-height: 28px;
}
</style>