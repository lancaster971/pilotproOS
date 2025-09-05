<template>
  <div class="node-icon" :class="className">
    <Icon v-if="iconName" :icon="iconName" :width="48" :height="48" class="icon-styled" />
    <div v-else class="placeholder-icon" :title="`Iconify mapping needed: ${nodeType}`">
      <span class="placeholder-text">{{ placeholderText }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Icon } from '@iconify/vue'

interface Props {
  nodeType: string
  className?: string
}

const props = defineProps<Props>()

// ICONIFY MAPPING - Sostituisce 29 import SVG manuali con infinite icone
const iconifyMap: Record<string, string> = {
  // Base nodes - Iconify professional icons
  'n8n-nodes-base.cron': 'mdi:timer-outline',
  'n8n-nodes-base.scheduleTrigger': 'mdi:calendar-clock',
  'n8n-nodes-base.supabase': 'simple-icons:supabase',
  'n8n-nodes-base.postgres': 'simple-icons:postgresql',
  'n8n-nodes-base.telegram': 'simple-icons:telegram',
  'n8n-nodes-base.telegramTrigger': 'simple-icons:telegram',
  'n8n-nodes-base.webhook': 'mdi:webhook',
  'n8n-nodes-base.code': 'mdi:code-braces',
  'n8n-nodes-base.function': 'mdi:function',
  'n8n-nodes-base.httpRequest': 'mdi:web',
  'n8n-nodes-base.gmail': 'simple-icons:gmail',
  'n8n-nodes-base.googleSheets': 'simple-icons:googlesheets',
  'n8n-nodes-base.googleDrive': 'simple-icons:googledrive', 
  'n8n-nodes-base.openAi': 'simple-icons:openai',
  'n8n-nodes-base.if': 'mdi:help-rhombus-outline',
  'n8n-nodes-base.merge': 'mdi:merge',
  'n8n-nodes-base.microsoftOutlook': 'simple-icons:microsoftoutlook',
  'n8n-nodes-base.microsoftOutlookTrigger': 'simple-icons:microsoftoutlook',
  'n8n-nodes-base.dateTime': 'mdi:calendar-clock',
  'n8n-nodes-base.switch': 'mdi:electric-switch',
  'n8n-nodes-base.splitInBatches': 'mdi:format-list-bulleted',
  'n8n-nodes-base.noOp': 'mdi:minus-circle-outline',
  'n8n-nodes-base.whatsApp': 'simple-icons:whatsapp',
  'n8n-nodes-base.whatsAppTrigger': 'simple-icons:whatsapp',
  'n8n-nodes-base.extractFromFile': 'mdi:file-document-outline',
  
  // Parser nodes - Iconify code icons
  'n8n-nodes-base.xml': 'mdi:code-tags',
  'n8n-nodes-base.json': 'mdi:code-json', 
  'n8n-nodes-base.html': 'mdi:language-html5',
  'n8n-nodes-base.csv': 'mdi:file-delimited-outline',
  'n8n-nodes-base.yaml': 'mdi:file-code-outline',
  'n8n-nodes-base.markdown': 'simple-icons:markdown',
  
  // LangChain nodes - AI & Tool icons
  '@n8n/n8n-nodes-langchain.agent': 'mdi:robot-outline',
  '@n8n/n8n-nodes-langchain.toolSerpApi': 'mdi:google',
  '@n8n/n8n-nodes-langchain.toolDateTime': 'mdi:calendar-clock',
  '@n8n/n8n-nodes-langchain.memoryPostgresChat': 'simple-icons:postgresql',
  '@n8n/n8n-nodes-langchain.memoryPostgresChatMemory': 'simple-icons:postgresql',
  '@n8n/n8n-nodes-langchain.memoryBufferWindow': 'mdi:memory',
  '@n8n/n8n-nodes-langchain.lmChatOpenAi': 'simple-icons:openai',
  '@n8n/n8n-nodes-langchain.embeddingsOpenAi': 'simple-icons:openai',
  '@n8n/n8n-nodes-langchain.toolMcp': 'mdi:toy-brick-outline',
  '@n8n/n8n-nodes-langchain.vectorStoreQdrant': 'mdi:database-search',
  '@n8n/n8n-nodes-langchain.toolSubworkflow': 'mdi:workflow',
  '@n8n/n8n-nodes-langchain.outputParserStructured': 'mdi:code-braces',
  '@n8n/n8n-nodes-langchain.chatTrigger': 'mdi:chat-outline',
  '@n8n/n8n-nodes-langchain.toolHttpRequest': 'mdi:web',
  '@n8n/n8n-nodes-langchain.toolConvertToFile': 'mdi:file-document-outline',
  '@n8n/n8n-nodes-langchain.chainSummarization': 'mdi:format-list-text',
  
  // Additional common mappings
  'n8n-nodes-base.start': 'mdi:play-circle-outline',
  'n8n-nodes-base.set': 'mdi:pencil-outline',
  'n8n-nodes-base.filter': 'mdi:filter-outline',
  'n8n-nodes-base.sort': 'mdi:sort-variant',
  'n8n-nodes-base.limit': 'mdi:numeric',
  'n8n-nodes-base.itemLists': 'mdi:format-list-bulleted-square'
}

// Computed icon name
const iconName = computed(() => {
  return iconifyMap[props.nodeType] || null
})

// Placeholder text for unmapped node types
const placeholderText = computed(() => {
  const parts = props.nodeType.split('.')
  return parts[parts.length - 1].substring(0, 3).toUpperCase()
})
</script>

<style scoped>
.node-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 8px;
}

/* Elegant gray color for icons - matches UI design */
.icon-styled {
  color: #9CA3AF !important; /* Gray-400 - elegant medium gray */
  opacity: 0.9;
  transition: all 0.2s ease;
}

.node-icon:hover .icon-styled {
  color: #D1D5DB !important; /* Gray-300 - lighter on hover */
  opacity: 1;
}

.placeholder-icon {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #374151; /* Dark gray background to match UI */
  border: 2px dashed #6B7280;
  border-radius: 8px;
}

.placeholder-text {
  font-size: 10px;
  font-weight: bold;
  color: #9CA3AF; /* Same gray as icons */
}
</style>