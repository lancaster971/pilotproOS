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
  if (!props.nodeType) {
    console.log('❌ [DEBUG] No nodeType provided to N8nIcon!')
    return
  }
  
  try {
    console.log('🎨 [DEBUG] Loading n8n icon for:', props.nodeType)
    // MEGA cache-buster per forzare reload di tutti i fallback
    const cacheBuster = Date.now() + Math.random()
    const url = `http://localhost:3001/api/n8n-icons/${encodeURIComponent(props.nodeType)}?v=${cacheBuster}`
    console.log('🌐 [DEBUG] Fetching URL:', url)
    
    const response = await fetch(url, {
      cache: 'no-cache'
    })
    
    console.log('📡 [DEBUG] Response status:', response.status, 'for:', props.nodeType)
    
    if (response.ok) {
      const svg = await response.text()
      // Verifica che sia effettivamente un SVG e non un errore JSON
      if (svg.includes('<svg')) {
        svgContent.value = svg
        console.log('✅ Loaded n8n icon for:', props.nodeType)
      } else {
        console.log('⚠️ Response not SVG, using fallback for:', props.nodeType, 'Response:', svg.substring(0, 100))
        svgContent.value = ''
      }
    } else {
      console.log('❌ N8n icon request failed:', response.status, 'for:', props.nodeType)
      svgContent.value = ''
    }
  } catch (error) {
    console.error('❌ Error loading n8n icon:', error)
    svgContent.value = ''
  }
}

onMounted(() => {
  console.log('🚀 [DEBUG] N8nIcon mounted with nodeType:', props.nodeType)
  loadIcon()
})

watch(() => props.nodeType, () => {
  loadIcon()
})
</script>

<style scoped>
.n8n-icon {
  /* Rimuovo sfondo bianco, lo gestirà il nodo stesso */
  display: flex;
  align-items: center;
  justify-content: center;
}

.n8n-icon :deep(svg) {
  width: 100%;
  height: 100%;
  display: block;
}

.n8n-icon-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>