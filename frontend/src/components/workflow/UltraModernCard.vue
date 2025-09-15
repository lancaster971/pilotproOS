<template>
  <div class="ultra-card-wrapper">
    <!-- Main Card Container -->
    <div
      :class="[
        'ultra-card',
        `card-${nodeCategory}`,
        {
          'card-ai-wide': isAIAgent,
          'card-tool-narrow': isLangchainTool,
          'card-running': isActive,
          'card-error': hasError,
          'card-selected': selected
        }
      ]"
    >
      <!-- Top Ribbon with Category -->
      <div class="card-ribbon" :style="{ background: ribbonGradient }">
        <span class="ribbon-text">{{ categoryText }}</span>
      </div>

      <!-- Main Card Content -->
      <div class="card-content">
        <!-- Large Central Icon -->
        <div class="icon-container" :style="{ background: iconBackground }">
          <Icon :icon="nodeIcon" class="main-icon" />
          <div class="icon-pulse"></div>
        </div>

        <!-- Title Only -->
        <div class="text-content">
          <h3 class="card-title">{{ businessTitle }}</h3>
        </div>

      </div>

      <!-- Bottom Tech Strip -->
      <div class="tech-strip">
        <div class="tech-dots">
          <span v-for="i in 3" :key="i" class="tech-dot"></span>
        </div>
        <span class="tech-type">{{ techTypeLabel }}</span>
        <div class="tech-badge" v-if="techBadge">
          <span>{{ techBadge }}</span>
        </div>
      </div>
    </div>

    <!-- Modern Handle Placement -->
    <template v-if="isAIAgent">
      <!-- AI Agent: Lateral for main flow, bottom for tools -->
      <Handle
        type="target"
        :position="Position.Left"
        id="left"
        class="ultra-handle handle-main"
      />
      <Handle
        type="source"
        :position="Position.Right"
        id="right"
        class="ultra-handle handle-main"
      />
      <!-- Bottom handles for tool connections -->
      <Handle
        v-for="i in 4"
        :key="`tool-out-${i}`"
        type="source"
        :position="Position.Bottom"
        :id="`tool-${i - 1}`"
        class="ultra-handle handle-tool"
        :style="{ left: `${20 + (i - 1) * 20}%` }"
      />
    </template>

    <template v-else-if="isLangchainTool">
      <!-- Tools: Connect FROM top (coming from agent) -->
      <Handle
        type="target"
        :position="Position.Top"
        id="top"
        class="ultra-handle handle-tool-input"
      />
      <Handle
        type="source"
        :position="Position.Bottom"
        id="bottom"
        class="ultra-handle handle-tool-output"
      />
    </template>

    <template v-else-if="nodeCategory === 'storage'">
      <!-- Storage: Vertical flow -->
      <Handle
        type="target"
        :position="Position.Top"
        id="top"
        class="ultra-handle handle-data"
      />
      <Handle
        type="source"
        :position="Position.Bottom"
        id="bottom"
        class="ultra-handle handle-data"
      />
    </template>

    <template v-else-if="nodeCategory === 'trigger'">
      <!-- Trigger: Only output -->
      <Handle
        type="source"
        :position="Position.Right"
        id="right"
        class="ultra-handle handle-trigger"
      />
    </template>

    <template v-else>
      <!-- Default: Standard flow -->
      <Handle
        type="target"
        :position="Position.Left"
        id="left"
        class="ultra-handle handle-standard"
      />
      <Handle
        type="source"
        :position="Position.Right"
        id="right"
        class="ultra-handle handle-standard"
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
    avgTime?: string
    inputs?: string[]
    outputs?: string[]
  }
  selected?: boolean
}

const props = defineProps<Props>()

// Detect Langchain tools for narrower cards (separate nodes connected to agents)
const isLangchainTool = computed(() => {
  const nodeType = props.data.nodeType || ''
  const type = props.data.type || ''
  const label = props.data.label.toLowerCase()

  // Check type returned by getNodeTypeFromN8nType
  // These are SEPARATE tool nodes that connect TO the agent
  // Based on REAL node names from database
  return type === 'tool' ||  // This is what getNodeTypeFromN8nType returns for tools!
         nodeType.includes('toolWorkflow') ||
         nodeType.includes('dateTimeTool') ||
         nodeType.includes('vectorStoreQdrant') ||
         nodeType.includes('embeddingsOpenAi') ||
         nodeType.includes('lmChatOpenAi') ||
         nodeType.includes('outputParser') ||
         // Real node names from Milena workflow
         label === 'info ordini' ||
         label === 'date & time' ||
         label === 'parcelapp' ||
         label === 'formatta risposta' ||
         label.includes('retriever') ||
         label.includes('memory') ||
         label.includes('buffer')
})

// Detect AI/Langchain agents for wider cards
const isAIAgent = computed(() => {
  const nodeType = props.data.nodeType || ''
  const type = props.data.type || ''
  const label = props.data.label.toLowerCase()

  // Check both type (from getNodeTypeFromN8nType) and nodeType (original)
  // Based on REAL node names from database
  // ONLY true AI agents should be wide
  const result = type === 'ai' && nodeType.includes('langchain.agent')

  if (result) {
    console.log('🤖 AI Agent detected:', label, 'type:', type, 'nodeType:', nodeType)
  }

  return result
})

// Smart categorization
const nodeCategory = computed(() => {
  const type = props.data.type
  const nodeType = props.data.nodeType || ''
  const label = props.data.label.toLowerCase()

  if (type === 'trigger' || nodeType.includes('trigger')) return 'trigger'
  if (type === 'ai' || nodeType.includes('agent') || nodeType.includes('openai')) return 'ai'
  if (type === 'storage' || nodeType.includes('database') || nodeType.includes('vector')) return 'storage'
  if (nodeType.includes('if') || nodeType.includes('switch')) return 'logic'
  if (nodeType.includes('http') || nodeType.includes('webhook')) return 'integration'
  if (nodeType.includes('code') || nodeType.includes('function')) return 'transform'
  if (label.includes('email') || label.includes('slack')) return 'communication'

  return 'process'
})

// Category icons - unique set
const categoryIcon = computed(() => {
  const icons: Record<string, string> = {
    'trigger': 'carbon:flash',
    'ai': 'carbon:watson-machine-learning',
    'storage': 'carbon:db2-database',
    'logic': 'carbon:decision-tree',
    'integration': 'carbon:api',
    'transform': 'carbon:transform',
    'communication': 'carbon:email',
    'process': 'carbon:flow'
  }
  return icons[nodeCategory.value] || 'carbon:circle-solid'
})

// Main node icons - different from category
const nodeIcon = computed(() => {
  const name = props.data.label.toLowerCase()
  const type = props.data.nodeType || ''

  // Brand icons - Use official logos
  if (type.includes('postgres') || name.includes('postgres')) return 'simple-icons:postgresql'
  if (type.includes('mysql') || name.includes('mysql')) return 'simple-icons:mysql'
  if (type.includes('mongodb') || name.includes('mongo')) return 'simple-icons:mongodb'
  if (type.includes('redis') || name.includes('redis')) return 'simple-icons:redis'
  if (type.includes('supabase') || name.includes('supabase')) return 'simple-icons:supabase'

  // Microsoft/Office services - Check first!
  if (type === 'n8n-nodes-base.microsoftOutlook' ||
      type === 'n8n-nodes-base.microsoftOutlookTrigger' ||
      type.includes('microsoftOutlook') ||
      type.includes('outlook') ||
      name.includes('outlook') ||
      name.includes('mail') && (name.includes('ordini') || name.includes('email'))) return 'vscode-icons:file-type-outlook'
  if (type.includes('telegram') || name.includes('telegram')) return 'simple-icons:telegram'
  if (type.includes('slack') || name.includes('slack')) return 'simple-icons:slack'
  if (type.includes('gmail') || name.includes('gmail')) return 'simple-icons:gmail'
  if (type.includes('discord') || name.includes('discord')) return 'simple-icons:discord'
  if (type.includes('whatsapp') || name.includes('whatsapp')) return 'simple-icons:whatsapp'

  // AI Services - Check AI Agents first with better icons
  if (type.includes('langchain.agent') ||
      (type === 'ai' && nodeType.includes('agent')) ||
      name.includes('agent') || name.includes('assistente') ||
      name.includes('milena')) {
    return 'fluent:brain-circuit-20-regular' // Modern AI brain circuit icon
  }
  if (type.includes('openai') || name.includes('openai') || name.includes('gpt')) return 'simple-icons:openai'
  if (type.includes('anthropic') || name.includes('claude')) return 'simple-icons:anthropic'
  if (type.includes('langchain')) return 'carbon:flow-data' // Better for LangChain

  // Cloud & APIs
  if (type.includes('google') || name.includes('google')) return 'simple-icons:google'
  if (type.includes('aws') || name.includes('aws')) return 'simple-icons:amazonaws'
  if (type.includes('azure') || name.includes('azure')) return 'simple-icons:microsoftazure'
  if (type.includes('github') || name.includes('github')) return 'simple-icons:github'
  if (type.includes('gitlab') || name.includes('gitlab')) return 'simple-icons:gitlab'

  // Dev tools
  if (type.includes('docker') || name.includes('docker')) return 'simple-icons:docker'
  if (type.includes('kubernetes') || name.includes('kubernetes')) return 'simple-icons:kubernetes'
  if (type.includes('git') || name.includes('git')) return 'simple-icons:git'

  // Social Media
  if (type.includes('twitter') || name.includes('twitter')) return 'simple-icons:x'
  if (type.includes('facebook') || name.includes('facebook')) return 'simple-icons:facebook'
  if (type.includes('instagram') || name.includes('instagram')) return 'simple-icons:instagram'
  if (type.includes('linkedin') || name.includes('linkedin')) return 'simple-icons:linkedin'

  // Other services
  if (type.includes('stripe') || name.includes('stripe')) return 'simple-icons:stripe'
  if (type.includes('paypal') || name.includes('paypal')) return 'simple-icons:paypal'
  if (type.includes('shopify') || name.includes('shopify')) return 'simple-icons:shopify'
  if (type.includes('wordpress') || name.includes('wordpress')) return 'simple-icons:wordpress'

  // File formats
  if (type.includes('excel') || name.includes('excel')) return 'vscode-icons:file-type-excel'
  if (type.includes('csv') || name.includes('csv')) return 'vscode-icons:file-type-csv'
  if (type.includes('json') || name.includes('json')) return 'vscode-icons:file-type-json'
  if (type.includes('xml') || name.includes('xml')) return 'vscode-icons:file-type-xml'
  if (type.includes('pdf') || name.includes('pdf')) return 'vscode-icons:file-type-pdf'

  // N8n specific nodes
  if (type.includes('n8n-nodes-base.spreadsheetFile')) return 'vscode-icons:file-type-excel'
  if (type.includes('n8n-nodes-base.googleSheets')) return 'simple-icons:googlesheets'
  if (type.includes('n8n-nodes-base.googleDrive')) return 'simple-icons:googledrive'
  if (type.includes('n8n-nodes-base.notion')) return 'simple-icons:notion'
  if (type.includes('n8n-nodes-base.airtable')) return 'simple-icons:airtable'
  if (type.includes('n8n-nodes-base.trello')) return 'simple-icons:trello'
  if (type.includes('n8n-nodes-base.jira')) return 'simple-icons:jira'
  if (type.includes('n8n-nodes-base.asana')) return 'simple-icons:asana'
  if (type.includes('n8n-nodes-base.monday')) return 'simple-icons:mondaydotcom'
  if (type.includes('n8n-nodes-base.clickup')) return 'simple-icons:clickup'
  if (type.includes('n8n-nodes-base.hubspot')) return 'simple-icons:hubspot'
  if (type.includes('n8n-nodes-base.salesforce')) return 'simple-icons:salesforce'
  if (type.includes('n8n-nodes-base.zendesk')) return 'simple-icons:zendesk'
  if (type.includes('n8n-nodes-base.twilio')) return 'simple-icons:twilio'
  if (type.includes('n8n-nodes-base.sendgrid')) return 'simple-icons:sendgrid'
  if (type.includes('n8n-nodes-base.mailchimp')) return 'simple-icons:mailchimp'
  if (type.includes('n8n-nodes-base.calendly')) return 'simple-icons:calendly'
  if (type.includes('n8n-nodes-base.zoom')) return 'simple-icons:zoom'
  if (type.includes('n8n-nodes-base.teams')) return 'simple-icons:microsoftteams'
  if (type.includes('n8n-nodes-base.dropbox')) return 'simple-icons:dropbox'
  if (type.includes('n8n-nodes-base.box')) return 'simple-icons:box'
  if (type.includes('n8n-nodes-base.onedrive')) return 'simple-icons:microsoftonedrive'

  // Generic node types with nice icons
  if (type.includes('webhook')) return 'carbon:webhook'
  if (type.includes('schedule') || type.includes('cron')) return 'carbon:alarm'
  if (type.includes('httpRequest')) return 'carbon:http'
  if (type.includes('n8n-nodes-base.code')) return 'carbon:code'
  if (type.includes('n8n-nodes-base.function')) return 'carbon:function'
  if (type.includes('n8n-nodes-base.if')) return 'carbon:decision-tree'
  if (type.includes('n8n-nodes-base.switch')) return 'carbon:flow-switch'
  if (type.includes('n8n-nodes-base.merge')) return 'carbon:join-inner'
  if (type.includes('n8n-nodes-base.wait')) return 'carbon:hourglass'
  if (type.includes('n8n-nodes-base.set')) return 'carbon:settings-adjust'
  if (type.includes('n8n-nodes-base.splitInBatches')) return 'carbon:batch-job'
  if (type.includes('email')) return 'carbon:email'

  // Fallback to category icon
  return categoryIcon.value
})

// Business-friendly titles
const businessTitle = computed(() => {
  const name = props.data.label

  const mapping: Record<string, string> = {
    'Webhook': 'Data Receiver',
    'Schedule Trigger': 'Scheduled Process',
    'Manual Trigger': 'Manual Start',
    'OpenAI': 'AI Processing',
    'Chat Model': 'AI Conversation',
    'Agent': 'Smart Assistant',
    'Postgres': 'Database Operations',
    'Vector Store': 'Knowledge Store',
    'HTTP Request': 'API Call',
    'If': 'Decision Logic',
    'Switch': 'Multi-Path Router',
    'Code': 'Custom Processing',
    'Function': 'Data Transform'
  }

  for (const [key, value] of Object.entries(mapping)) {
    if (name.includes(key)) return value
  }

  return name
})

// Descriptions
const nodeDescription = computed(() => {
  const descriptions: Record<string, string> = {
    'trigger': 'Initiates business process',
    'ai': 'Intelligent processing',
    'storage': 'Data persistence layer',
    'logic': 'Business rule evaluation',
    'integration': 'External system bridge',
    'transform': 'Data manipulation',
    'communication': 'Message handling',
    'process': 'Business operation'
  }
  return descriptions[nodeCategory.value] || 'Processing node'
})

// Category text
const categoryText = computed(() => {
  const texts: Record<string, string> = {
    'trigger': 'PROCESS START',
    'ai': 'INTELLIGENCE',
    'storage': 'DATA LAYER',
    'logic': 'DECISION',
    'integration': 'INTEGRATION',
    'transform': 'TRANSFORM',
    'communication': 'MESSAGING',
    'process': 'OPERATION'
  }
  return texts[nodeCategory.value] || 'PROCESS'
})

// Tech type badge
const techType = computed(() => {
  const types: Record<string, string> = {
    'trigger': 'ASYNC',
    'ai': 'ML/AI',
    'storage': 'CRUD',
    'logic': 'CONDITIONAL',
    'integration': 'REST/API',
    'transform': 'COMPUTE',
    'communication': 'SMTP/WEBHOOK',
    'process': 'SYNC'
  }
  return types[nodeCategory.value] || 'PROCESS'
})

// Modern gradients
const ribbonGradient = computed(() => {
  const gradients: Record<string, string> = {
    'trigger': 'linear-gradient(135deg, #2f855a, #276749)',
    'ai': 'linear-gradient(135deg, #553c9a, #434190)',
    'storage': 'linear-gradient(135deg, #2b6cb0, #2c5282)',
    'logic': 'linear-gradient(135deg, #4a5568, #2d3748)',
    'integration': 'linear-gradient(135deg, #742a2a, #63171b)',
    'transform': 'linear-gradient(135deg, #234e52, #1a4044)',
    'communication': 'linear-gradient(135deg, #744210, #5f370e)',
    'process': 'linear-gradient(135deg, #2d3748, #1a202c)'
  }
  return gradients[nodeCategory.value] || gradients['process']
})

const iconBackground = computed(() => {
  const color = {
    'trigger': '#276749',
    'ai': '#434190',
    'storage': '#2c5282',
    'logic': '#2d3748',
    'integration': '#63171b',
    'transform': '#1a4044',
    'communication': '#5f370e',
    'process': '#1a202c'
  }[nodeCategory.value] || '#1a202c'

  return `radial-gradient(circle, ${color}22, ${color}11)`
})

// Computed properties
const inputs = computed(() => props.data.inputs || ['input'])
const outputs = computed(() => props.data.outputs || ['output'])
const isActive = computed(() => props.data.status === 'active')
const hasError = computed(() => props.data.status === 'error')
const status = computed(() => props.data.status || 'idle')
const showMetrics = computed(() => nodeCategory.value !== 'trigger')
const executionCount = computed(() => props.data.executionCount)
const successRate = computed(() => props.data.successRate)
const avgTime = computed(() => props.data.avgTime)

// Tech type label with execution mode
const techTypeLabel = computed(() => {
  const nodeType = props.data.nodeType || ''
  const label = props.data.label.toLowerCase()
  const type = props.data.type || ''

  // Check if it's async (webhooks, triggers, wait nodes, cron)
  if (nodeType.includes('trigger') || nodeType.includes('webhook') ||
      nodeType.includes('wait') || nodeType.includes('cron') ||
      nodeType.includes('schedule') || type === 'trigger') {
    return 'ASYNC'
  }

  // Check if it's a code node
  if (nodeType.includes('n8n-nodes-base.code') ||
      nodeType.includes('n8n-nodes-base.function') ||
      nodeType.includes('javascript') || nodeType.includes('python') ||
      label.includes('code') || label.includes('function')) {
    return 'CODE'
  }

  // Check if it's an AI node
  if (nodeType.includes('langchain') || nodeType.includes('openai') ||
      nodeType.includes('ai') || type === 'ai' || type === 'tool') {
    return 'AI'
  }

  // Check if it's a database node
  if (nodeType.includes('postgres') || nodeType.includes('mysql') ||
      nodeType.includes('mongo') || nodeType.includes('redis') ||
      nodeType.includes('supabase') || type === 'storage') {
    return 'DB'
  }

  // Check if it's an HTTP/API node
  if (nodeType.includes('httpRequest') || nodeType.includes('webhook') ||
      nodeType.includes('api') || label.includes('http')) {
    return 'API'
  }

  // Check for IF/Switch nodes (conditional logic)
  if (nodeType.includes('n8n-nodes-base.if') ||
      nodeType.includes('switch') || label.includes('if')) {
    return 'LOGIC'
  }

  // Default is SYNC
  return 'SYNC'
})

// Tech badge for additional info
const techBadge = computed(() => {
  const nodeType = props.data.nodeType || ''
  const label = props.data.label.toLowerCase()

  // Code nodes show custom code indicator
  if (nodeType.includes('n8n-nodes-base.code')) {
    return '</>'
  }
  if (nodeType.includes('n8n-nodes-base.function')) {
    return 'f(x)'
  }
  if (nodeType.includes('javascript')) {
    return 'JS'
  }
  if (nodeType.includes('python')) {
    return 'PY'
  }

  // AI specific badges
  if (nodeType.includes('langchain.agent')) {
    return 'AI'
  }
  if (nodeType.includes('openai') || nodeType.includes('gpt')) {
    return 'GPT'
  }
  if (nodeType.includes('embeddings')) {
    return '↗️'
  }

  // Database specific
  if (nodeType.includes('postgres')) {
    return 'PG'
  }
  if (nodeType.includes('mysql')) {
    return 'SQL'
  }
  if (nodeType.includes('qdrant') || nodeType.includes('vectorStore')) {
    return 'VEC'
  }

  // Communication badges
  if (nodeType.includes('telegram')) {
    return 'TG'
  }
  if (nodeType.includes('gmail') || nodeType.includes('email')) {
    return '✉️'
  }
  if (nodeType.includes('slack')) {
    return 'SK'
  }

  // Conditional logic
  if (nodeType.includes('n8n-nodes-base.if')) {
    return 'IF'
  }
  if (nodeType.includes('switch')) {
    return '⇄'
  }
  if (nodeType.includes('merge')) {
    return '⊕'
  }

  // Time-based
  if (nodeType.includes('cron')) {
    return '⏰'
  }
  if (nodeType.includes('wait')) {
    return '⏸'
  }

  return null
})
</script>

<style scoped>
.ultra-card-wrapper {
  position: relative;
}

.ultra-card {
  width: 280px;
  min-height: 160px;
  background: linear-gradient(135deg, #2a2f3e, #1f2430);
  border-radius: 20px;
  overflow: hidden;
  box-shadow:
    0 20px 40px rgba(0, 0, 0, 0.4),
    0 0 1px rgba(255, 255, 255, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

/* Wider cards for AI/Langchain agents - same height, more width */
.card-ai-wide {
  width: 380px; /* 100px wider than standard */
  background: linear-gradient(135deg, #242938, #1a1f2e),
              linear-gradient(135deg, rgba(236, 72, 153, 0.05), transparent);
  border: 2px solid rgba(236, 72, 153, 0.2);
}

/* Narrower cards for Langchain tools - same height, less width */
.card-tool-narrow {
  width: 200px; /* 80px narrower than standard */
  background: linear-gradient(135deg, #242938, #1a1f2e),
              linear-gradient(135deg, rgba(59, 130, 246, 0.05), transparent);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.card-tool-narrow .card-content {
  padding: 12px;
}

.card-tool-narrow .card-title {
  font-size: 13px;
}

.card-tool-narrow .metrics-row {
  display: none; /* Hide metrics for tools to save space */
}

.ultra-card:hover {
  transform: translateY(-4px);
  box-shadow:
    0 30px 60px rgba(0, 0, 0, 0.5),
    0 0 1px rgba(255, 255, 255, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* Ribbon */
.card-ribbon {
  height: 32px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  position: relative;
  overflow: hidden;
}

.card-ribbon::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
}

.ribbon-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  margin-right: 8px;
}

.ribbon-icon-svg {
  width: 14px;
  height: 14px;
  color: white;
}

.ribbon-text {
  flex: 1;
  font-size: 10px;
  font-weight: 700;
  color: white;
  letter-spacing: 1px;
  opacity: 0.95;
}

.ribbon-status {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-light {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #475569;
  position: relative;
}

.status-light::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  background: inherit;
  opacity: 0.3;
  animation: pulse-ring 2s infinite;
}

.light-active {
  background: #3b82f6;
  box-shadow: 0 0 10px #3b82f6;
  animation: pulse-light 1s infinite;
}

.light-success {
  background: #10b981;
  box-shadow: 0 0 10px #10b981;
}

.light-error {
  background: #ef4444;
  box-shadow: 0 0 10px #ef4444;
  animation: pulse-light 0.5s infinite;
}

@keyframes pulse-light {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes pulse-ring {
  0% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.5); opacity: 0; }
  100% { transform: scale(1); opacity: 0; }
}

/* Content */
.card-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px 12px 0 0;
}

.icon-container {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  align-self: center;
  backdrop-filter: blur(10px);
}

.icon-pulse {
  position: absolute;
  inset: 0;
  border-radius: 16px;
  background: inherit;
  opacity: 0.3;
  animation: icon-pulse 3s infinite;
}

@keyframes icon-pulse {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.1); opacity: 0; }
}

.main-icon {
  width: 36px;
  height: 36px;
  color: white !important;
  fill: white !important;
  z-index: 1;
  position: relative;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}

/* Force all SVG icons to be white */
.main-icon :deep(svg) {
  fill: white !important;
  color: white !important;
}

.main-icon :deep(path) {
  fill: white !important;
}

.text-content {
  text-align: center;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #f1f5f9;
  margin: 0 0 4px 0;
  line-height: 1.2;
}

.card-subtitle {
  font-size: 11px;
  color: #64748b;
  margin: 0;
  line-height: 1.3;
}

/* Metrics Row */
.metrics-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.metric-icon {
  width: 14px;
  height: 14px;
  color: #64748b;
}

.metric-icon.success {
  color: #10b981;
}

.metric-value {
  font-size: 13px;
  font-weight: 600;
  color: #f1f5f9;
}

.metric-label {
  font-size: 10px;
  color: #475569;
  margin-left: 2px;
}

.metric-divider {
  width: 1px;
  height: 16px;
  background: rgba(255, 255, 255, 0.1);
}

/* Tech Strip */
.tech-strip {
  height: 24px;
  background: rgba(10, 10, 15, 0.7);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  border-radius: 0 0 12px 12px;
  backdrop-filter: blur(4px);
}

.tech-dots {
  display: flex;
  gap: 3px;
}

.tech-dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #4a5568;
  opacity: 0.6;
}

.tech-type {
  font-size: 9px;
  font-weight: 600;
  color: #718096;
  letter-spacing: 0.5px;
  opacity: 0.8;
}

.tech-badge {
  display: flex;
  align-items: center;
}

.tech-badge span {
  font-size: 8px;
  font-weight: 700;
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
  padding: 2px 5px;
  border-radius: 3px;
  letter-spacing: 0.3px;
  font-family: 'Monaco', 'Courier New', monospace;
}

.tech-connections {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #64748b;
}

.tech-icon {
  width: 12px;
  height: 12px;
}

/* Handles */
.ultra-handle {
  position: absolute;
  width: 10px !important;
  height: 10px !important;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
  border: 2px solid #1a1f2e !important;
  border-radius: 50%;
  transition: all 0.2s;
}

.handle-main {
  top: 50%;
  transform: translateY(-50%);
}

.handle-main:first-of-type {
  left: -5px;
}

.handle-main:last-of-type {
  right: -5px;
}

.handle-tool {
  bottom: -5px;
}

.handle-data {
  left: 50%;
  transform: translateX(-50%);
}

.handle-data:first-of-type {
  top: -5px;
}

.handle-data:last-of-type {
  bottom: -5px;
}

.handle-trigger {
  right: -5px;
  top: 50%;
  transform: translateY(-50%);
  background: linear-gradient(135deg, #10b981, #3b82f6) !important;
}

.handle-standard {
  top: 50%;
  transform: translateY(-50%);
}

.handle-standard:first-of-type {
  left: -5px;
}

.handle-standard:last-of-type {
  right: -5px;
}

/* Special styles for tool connections */
.handle-tool-input {
  top: -5px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #3b82f6, #06b6d4) !important;
}

.handle-tool-output {
  bottom: -5px;
  left: 50%;
  transform: translateX(-50%);
}

.ultra-handle:hover {
  transform: scale(1.5) translateY(-50%);
  box-shadow: 0 0 12px currentColor;
  background: linear-gradient(135deg, #8b5cf6, #ec4899) !important;
}

.handle-data:hover,
.handle-tool-input:hover,
.handle-tool-output:hover {
  transform: scale(1.5) translateX(-50%);
}

/* States */
.card-running {
  animation: running-pulse 2s infinite;
}

@keyframes running-pulse {
  0%, 100% {
    box-shadow:
      0 20px 40px rgba(0, 0, 0, 0.4),
      0 0 30px rgba(59, 130, 246, 0.3);
  }
  50% {
    box-shadow:
      0 20px 40px rgba(0, 0, 0, 0.4),
      0 0 40px rgba(59, 130, 246, 0.5);
  }
}

.card-error {
  border-color: #ef4444;
  animation: error-shake 0.5s;
}

@keyframes error-shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

.card-selected {
  border: 2px solid #8b5cf6;
  box-shadow:
    0 20px 40px rgba(0, 0, 0, 0.4),
    0 0 40px rgba(139, 92, 246, 0.4);
}

/* Trigger - Same rectangular shape as others with distinctive color */
.card-trigger {
  background: linear-gradient(135deg, #2f3444, #242938),
              linear-gradient(135deg, rgba(16, 185, 129, 0.08), transparent);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.card-ai {
  background: linear-gradient(135deg, #242938, #1a1f2e),
              linear-gradient(135deg, rgba(238, 9, 121, 0.03), transparent);
}

.card-storage {
  background: linear-gradient(135deg, #242938, #1a1f2e),
              linear-gradient(135deg, rgba(0, 201, 255, 0.03), transparent);
}
</style>