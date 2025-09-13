<template>
  <div class="node-icon" :class="[className, shapeClasses]" :title="`Shape: ${nodeShape}, Type: ${nodeType}`">
    <Icon
      v-if="iconName"
      :icon="iconName"
      :width="48"
      :height="48"
      class="icon-styled"
      :style="{ color: categoryColor }"
    />
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

// CATEGORY-BASED ICON SYSTEM - Categorie semantiche con colori
interface NodeMapping {
  icon: string
  category: string
  shape?: 'diamond' | 'rectangle' | 'diamond-flat' | 'circle'
}

const iconifyMap: Record<string, NodeMapping> = {
  // SCHEDULE TRIGGERS - Trigger temporali (🔵 Blu elettrico)
  'n8n-nodes-base.cron': { icon: 'mdi:timer-outline', category: 'schedule_triggers', shape: 'diamond' },
  'n8n-nodes-base.scheduleTrigger': { icon: 'mdi:calendar-clock', category: 'schedule_triggers', shape: 'diamond' },

  // WEBHOOK TRIGGERS - Trigger HTTP esterni (🔴 Rosso intenso)
  'n8n-nodes-base.webhook': { icon: 'mdi:webhook', category: 'webhook_triggers', shape: 'diamond' },
  'n8n-nodes-base.formTrigger': { icon: 'mdi:form-select', category: 'webhook_triggers', shape: 'diamond' },

  // EMAIL TRIGGERS - Trigger email (🟡 Giallo ambra)
  'n8n-nodes-base.gmailTrigger': { icon: 'simple-icons:gmail', category: 'email_triggers', shape: 'diamond' },
  'n8n-nodes-base.microsoftOutlookTrigger': { icon: 'simple-icons:microsoftoutlook', category: 'email_triggers', shape: 'diamond' },
  'n8n-nodes-base.emailReadImap': { icon: 'mdi:email-receive-outline', category: 'email_triggers', shape: 'diamond' },

  // SOCIAL TRIGGERS - Trigger social/messaging (🟢 Verde vivace)
  'n8n-nodes-base.telegramTrigger': { icon: 'simple-icons:telegram', category: 'social_triggers', shape: 'diamond' },
  'n8n-nodes-base.whatsAppTrigger': { icon: 'simple-icons:whatsapp', category: 'social_triggers', shape: 'diamond' },

  // WORKFLOW TRIGGERS - Trigger interni workflow (🟣 Viola)
  'n8n-nodes-base.manualTrigger': { icon: 'mdi:play-circle', category: 'workflow_triggers', shape: 'diamond' },
  'n8n-nodes-base.executeWorkflowTrigger': { icon: 'mdi:play-circle', category: 'workflow_triggers', shape: 'diamond' },

  // AI TRIGGERS - Trigger AI/Chat (🟪 Rosa magenta)
  '@n8n/n8n-nodes-langchain.chatTrigger': { icon: 'mdi:chat-outline', category: 'ai_triggers', shape: 'diamond' },

  // MARKETING TRIGGERS - Trigger marketing (🟠 Arancione)
  'n8n-nodes-base.activeCampaignTrigger': { icon: 'mdi:email-newsletter', category: 'marketing_triggers', shape: 'diamond' },

  // DATA_PROCESSING - Elaborano dati (🟢 Verde)
  'n8n-nodes-base.set': { icon: 'mdi:pencil-circle', category: 'data_processing' },
  'n8n-nodes-base.filter': { icon: 'mdi:filter-outline', category: 'data_processing' },
  'n8n-nodes-base.sort': { icon: 'mdi:sort-variant', category: 'data_processing' },
  'n8n-nodes-base.limit': { icon: 'mdi:numeric', category: 'data_processing' },
  'n8n-nodes-base.splitInBatches': { icon: 'mdi:format-list-bulleted', category: 'data_processing' },
  'n8n-nodes-base.splitOut': { icon: 'mdi:call-split', category: 'data_processing' },

  // COMMUNICATION - Comunicazioni esterne (🟡 Giallo)
  'n8n-nodes-base.telegram': { icon: 'simple-icons:telegram', category: 'communication', shape: 'circle' },
  'n8n-nodes-base.whatsApp': { icon: 'simple-icons:whatsapp', category: 'communication', shape: 'circle' },
  'n8n-nodes-base.slack': { icon: 'simple-icons:slack', category: 'communication', shape: 'circle' },
  'n8n-nodes-base.gmail': { icon: 'simple-icons:gmail', category: 'communication', shape: 'circle' },
  'n8n-nodes-base.microsoftOutlook': { icon: 'simple-icons:microsoftoutlook', category: 'communication', shape: 'circle' },
  'n8n-nodes-base.emailSend': { icon: 'mdi:email-send-outline', category: 'communication', shape: 'circle' },

  // DATABASES - Database e storage (🟠 Arancione)
  'n8n-nodes-base.postgres': { icon: 'simple-icons:postgresql', category: 'databases' },
  'n8n-nodes-base.supabase': { icon: 'simple-icons:supabase', category: 'databases' },
  'n8n-nodes-base.googleSheets': { icon: 'simple-icons:googlesheets', category: 'databases' },

  // FILE_OPERATIONS - Operazioni file (🟣 Viola intenso)
  'n8n-nodes-base.googleDrive': { icon: 'simple-icons:googledrive', category: 'file_operations' },
  'n8n-nodes-base.extractFromFile': { icon: 'mdi:file-document-outline', category: 'file_operations' },

  // HTTP_API - Richieste web/API (🔴 Rosso)
  'n8n-nodes-base.httpRequest': { icon: 'mdi:web', category: 'http_api' },
  'n8n-nodes-base.httpRequestTool': { icon: 'mdi:api', category: 'http_api' },
  'n8n-nodes-base.respondToWebhook': { icon: 'mdi:webhook', category: 'http_api' },

  // CODE - Sviluppo e scripting (🟪 Magenta)
  'n8n-nodes-base.code': { icon: 'mdi:code-braces', category: 'code' },
  'n8n-nodes-base.function': { icon: 'mdi:function', category: 'code' },

  // WORKFLOW_CONTROL - Controllo flusso (🔵 Indaco)
  'n8n-nodes-base.if': { icon: 'mdi:help-rhombus-outline', category: 'workflow_control', shape: 'diamond-flat' },
  'n8n-nodes-base.switch': { icon: 'mdi:electric-switch', category: 'workflow_control', shape: 'diamond-flat' },
  'n8n-nodes-base.merge': { icon: 'mdi:merge', category: 'workflow_control', shape: 'diamond-flat' },
  'n8n-nodes-base.wait': { icon: 'mdi:timer-sand', category: 'workflow_control', shape: 'circle' },
  'n8n-nodes-base.executeWorkflow': { icon: 'mdi:play-circle-outline', category: 'workflow_control', shape: 'circle' },

  // LOGGING_MONITORING - Log e monitoraggio (⚪ Grigio neutro)
  'n8n-nodes-base.debug': { icon: 'mdi:bug-outline', category: 'logging_monitoring' },

  // UTILITIES - Utilità e supporto (⚪ Grigio)
  'n8n-nodes-base.noOp': { icon: 'mdi:minus-circle-outline', category: 'utilities' },
  'n8n-nodes-base.stickyNote': { icon: 'mdi:note-text-outline', category: 'utilities' },

  // PARSERS - Parsing documenti (🟤 Marrone)
  'n8n-nodes-base.html': { icon: 'mdi:language-html5', category: 'parsers' },
  'n8n-nodes-base.markdown': { icon: 'simple-icons:markdown', category: 'parsers' },
  'n8n-nodes-base.dateTimeTool': { icon: 'mdi:calendar-clock', category: 'parsers' },

  // CALENDAR_SCHEDULING - Calendari e appuntamenti (🟢 Verde smeraldo)
  'n8n-nodes-base.googleCalendar': { icon: 'simple-icons:googlecalendar', category: 'calendar_scheduling' },

  // AI_ML - Intelligenza artificiale (🟣 Viola)
  'n8n-nodes-base.openAi': { icon: 'simple-icons:openai', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.agent': { icon: 'mdi:robot-outline', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.lmChatOpenAi': { icon: 'simple-icons:openai', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.embeddingsOpenAi': { icon: 'simple-icons:openai', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.openAi': { icon: 'simple-icons:openai', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.lmChatGoogleGemini': { icon: 'simple-icons:google', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.chainLlm': { icon: 'mdi:brain', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.chainSummarization': { icon: 'mdi:format-list-text', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.textClassifier': { icon: 'mdi:text-box-check-outline', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.textSplitterTokenSplitter': { icon: 'mdi:format-text-wrapping-clip', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.memoryBufferWindow': { icon: 'mdi:memory', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.memoryPostgresChat': { icon: 'simple-icons:postgresql', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.vectorStoreQdrant': { icon: 'mdi:database-search', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.vectorStorePinecone': { icon: 'mdi:pine-tree', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.vectorStoreSupabase': { icon: 'simple-icons:supabase', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.retrieverVectorStore': { icon: 'mdi:database-arrow-down', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.rerankerCohere': { icon: 'mdi:sort-ascending', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.outputParserStructured': { icon: 'mdi:code-braces', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.documentDefaultDataLoader': { icon: 'mdi:file-upload-outline', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.chatTrigger': { icon: 'mdi:chat-outline', category: 'triggers' }, // È un trigger

  // AI TOOLS - Strumenti AI (🟣 Viola)
  '@n8n/n8n-nodes-langchain.toolSerpApi': { icon: 'mdi:google', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.toolCalculator': { icon: 'mdi:calculator', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.toolVectorStore': { icon: 'mdi:database-search-outline', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.toolWorkflow': { icon: 'mdi:workflow', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.toolHttpRequest': { icon: 'mdi:web', category: 'http_api', shape: 'rectangle' }, // È HTTP
  '@n8n/n8n-nodes-langchain.toolConvertToFile': { icon: 'mdi:file-document-outline', category: 'ai_ml', shape: 'rectangle' },
  '@n8n/n8n-nodes-langchain.mcpClientTool': { icon: 'mdi:connection', category: 'ai_ml', shape: 'rectangle' },

  // PARSERS aggiuntivi - Parsing documenti (🟤 Marrone)
  'n8n-nodes-base.xml': { icon: 'mdi:code-tags', category: 'parsers' },
  'n8n-nodes-base.json': { icon: 'mdi:code-json', category: 'parsers' },
  'n8n-nodes-base.csv': { icon: 'mdi:file-delimited-outline', category: 'parsers' },
  'n8n-nodes-base.yaml': { icon: 'mdi:file-code-outline', category: 'parsers' },

  // CODE aggiuntivi - Sviluppo e scripting (🟪 Magenta)
  'n8n-nodes-base.javascript': { icon: 'vscode-icons:file-type-js-official', category: 'code' },
  'n8n-nodes-base.typescript': { icon: 'vscode-icons:file-type-typescript-official', category: 'code' },
  'n8n-nodes-base.python': { icon: 'vscode-icons:file-type-python', category: 'code' },

  // UTILITIES aggiuntive - Utilità e supporto (⚪ Grigio)
  'n8n-nodes-base.start': { icon: 'mdi:play-circle', category: 'utilities' },
  'n8n-nodes-base.itemLists': { icon: 'mdi:format-list-bulleted', category: 'utilities' },
  'n8n-nodes-base.database': { icon: 'vscode-icons:file-type-sql', category: 'utilities' }
}

// ADVANCED PROFESSIONAL COLOR PALETTE - Sistema categorizzazione esteso
const categoryColors: Record<string, string> = {
  // Core Categories
  triggers: '#4F709C',           // Blu scuro - Attivano workflow
  data_processing: '#5F8A5F',    // Verde foresta - Elaborano dati
  communication: '#B8860B',      // Oro opaco - Comunicazioni
  ai_ml: '#6B46C1',             // Viola profondo - Intelligenza artificiale
  databases: '#C2793D',         // Bronzo - Database e storage
  http_api: '#B91C1C',          // Rosso scuro - Richieste web/API
  code: '#A855F7',              // Magenta - Sviluppo e scripting
  utilities: '#64748B',         // Grigio ardesia - Utilità e supporto
  parsers: '#8B5A2B',           // Marrone cioccolato - Parsing documenti
  cloud_services: '#0284C7',    // Azzurro - Servizi cloud

  // Advanced Categories
  media_processing: '#DC2626',   // Rosso vivace - Audio, video, immagini
  file_operations: '#7C3AED',    // Viola intenso - Operazioni file
  calendar_scheduling: '#059669', // Verde smeraldo - Calendari e appuntamenti
  business_intelligence: '#D97706', // Ambra - Analytics e report
  order_management: '#1D4ED8',   // Blu reale - Gestione ordini
  notification_systems: '#DC2626', // Rosso alert - Sistemi notifica
  authentication: '#374151',     // Grigio scuro - Autenticazione
  workflow_control: '#6366F1',   // Indaco - Controllo flusso
  logging_monitoring: '#6B7280', // Grigio neutro - Log e monitoraggio
  document_processing: '#92400E', // Marrone scuro - Elaborazione documenti

  // N8N TRIGGER CATEGORIES - Classificazione nativa trigger
  schedule_triggers: '#2563EB',   // Blu elettrico - Trigger temporali
  webhook_triggers: '#DC2626',    // Rosso intenso - Trigger HTTP esterni
  email_triggers: '#F59E0B',      // Giallo ambra - Trigger email
  social_triggers: '#10B981',     // Verde vivace - Trigger social/messaging
  workflow_triggers: '#8B5CF6',   // Viola - Trigger interni workflow
  ai_triggers: '#EC4899',         // Rosa magenta - Trigger AI/Chat
  marketing_triggers: '#F97316'   // Arancione - Trigger marketing
}

// Computed properties
const nodeMapping = computed(() => {
  return iconifyMap[props.nodeType] || null
})

const iconName = computed(() => {
  return nodeMapping.value?.icon || null
})

const categoryColor = computed(() => {
  const category = nodeMapping.value?.category || 'utilities'
  return categoryColors[category] || categoryColors.utilities
})

const nodeShape = computed(() => {
  return nodeMapping.value?.shape || 'rectangle'
})

const shapeClasses = computed(() => {
  return `shape-${nodeShape.value}`
})

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
  position: relative;
  transition: all 0.2s ease;
  /* Dimensioni base - sovrascritte dalle forme specifiche */
  width: 48px;
  height: 48px;
}

/* N8N GEOMETRIC SHAPES - Forme specifiche per categorie */

/* Default: Rectangle (Actions) - Rettangolo più largo */
.shape-rectangle {
  width: 56px !important;
  height: 40px !important;
  border-radius: 8px;
}

/* Diamond (Triggers) - Forma a diamante per trigger */
.shape-diamond {
  width: 48px !important;
  height: 48px !important;
  transform: rotate(45deg);
  border-radius: 6px;
}

.shape-diamond .icon-styled,
.shape-diamond .placeholder-icon {
  transform: rotate(-45deg);
}

/* Diamond Flat (Logic/Control) - Rombo schiacciato per controlli */
.shape-diamond-flat {
  width: 48px !important;
  height: 48px !important;
  transform: rotate(45deg) scaleY(0.6);
  border-radius: 4px;
}

.shape-diamond-flat .icon-styled,
.shape-diamond-flat .placeholder-icon {
  transform: rotate(-45deg) scaleY(1.67);
}

/* Circle (Outputs) - Cerchio per endpoint */
.shape-circle {
  width: 48px !important;
  height: 48px !important;
  border-radius: 50%;
}

/* PROFESSIONAL CATEGORY COLORING - Icone con palette sofisticata */
.icon-styled {
  opacity: 0.8;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.08));
}

.node-icon:hover .icon-styled {
  opacity: 0.95;
  transform: scale(1.03);
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.12));
}

/* Placeholder per nodi senza mapping */
.placeholder-icon {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #374151;
  border: 2px dashed #6B7280;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.placeholder-icon:hover {
  background: #4B5563;
  border-color: #9CA3AF;
}

.placeholder-text {
  font-size: 10px;
  font-weight: bold;
  color: #9CA3AF;
  transition: color 0.2s ease;
}

.placeholder-icon:hover .placeholder-text {
  color: #D1D5DB;
}
</style>