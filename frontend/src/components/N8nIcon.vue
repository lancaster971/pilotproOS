<template>
  <div class="node-icon" :class="className">
    <img v-if="iconSrc" :src="iconSrc" :alt="nodeType" />
    <div v-else class="placeholder-icon" :title="`Missing SVG: ${nodeType}`">
      <span class="placeholder-text">{{ placeholderText }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// IMPORT DIRETTI - icone da n8n
import cronIcon from '../assets/nodeIcons/svg/cron.svg'
import triggerScheduleIcon from '../assets/nodeIcons/svg/scheduleIcon.svg'
import supabaseIcon from '../assets/nodeIcons/svg/supabase.svg'
import postgresElephantIcon from '../assets/nodeIcons/svg/postgresql.svg'
import telegramIcon from '../assets/nodeIcons/svg/telegram.svg'
import webhookIcon from '../assets/nodeIcons/svg/webhook.svg'
import codeIcon from '../assets/nodeIcons/svg/code.svg'
import httpRequestIcon from '../assets/nodeIcons/svg/httprequest.svg'
import gmailIcon from '../assets/nodeIcons/svg/gmail.svg'
import googleSheetsIcon from '../assets/nodeIcons/svg/googleSheets.svg'
import googleDriveIcon from '../assets/nodeIcons/svg/googleDrive.svg'
import openAiIcon from '../assets/nodeIcons/svg/openAi-light.svg'
import mcpIcon from '../assets/nodeIcons/svg/mcp.svg'
import ifIcon from '../assets/nodeIcons/svg/if.svg'
import mergeIcon from '../assets/nodeIcons/svg/merge.svg'
import outlookIcon from '../assets/nodeIcons/svg/outlook.svg'
import serpApiIcon from '../assets/nodeIcons/svg/serpApi.svg'
import dateTimeIcon from '../assets/nodeIcons/svg/dateTime.svg'
import memoryIcon from '../assets/nodeIcons/svg/memory.svg'
import chatTriggerIcon from '../assets/nodeIcons/svg/chatTrigger.svg'
import convertToFileIcon from '../assets/nodeIcons/svg/convertToFile.svg'
import qdrantIcon from '../assets/nodeIcons/svg/qdrant.svg'
import toolSubworkflowIcon from '../assets/nodeIcons/svg/toolSubworkflow.svg'
import outputParserIcon from '../assets/nodeIcons/svg/outputParser.svg'
import loopIcon from '../assets/nodeIcons/svg/loop.svg'
import noOpIcon from '../assets/nodeIcons/svg/noOp.svg'
import whatsappIcon from '../assets/nodeIcons/svg/whatsapp.svg'
import langchainChainIcon from '../assets/nodeIcons/svg/langchainChain.svg'
import agentIcon from '../assets/nodeIcons/svg/agent.svg'

// MAPPING DIRETTO - icone complete da n8n
const iconMap: Record<string, string> = {
  // Base nodes
  'n8n-nodes-base.cron': cronIcon,
  'n8n-nodes-base.scheduleTrigger': triggerScheduleIcon,
  'n8n-nodes-base.supabase': supabaseIcon,
  'n8n-nodes-base.postgres': postgresElephantIcon,
  'n8n-nodes-base.telegram': telegramIcon,
  'n8n-nodes-base.telegramTrigger': telegramIcon,
  'n8n-nodes-base.webhook': webhookIcon,
  'n8n-nodes-base.code': codeIcon,
  'n8n-nodes-base.function': codeIcon,
  'n8n-nodes-base.httpRequest': httpRequestIcon,
  'n8n-nodes-base.gmail': gmailIcon,
  'n8n-nodes-base.googleSheets': googleSheetsIcon,
  'n8n-nodes-base.googleDrive': googleDriveIcon,
  'n8n-nodes-base.openAi': openAiIcon,
  'n8n-nodes-base.if': ifIcon,
  'n8n-nodes-base.merge': mergeIcon,
  'n8n-nodes-base.microsoftOutlook': outlookIcon,
  'n8n-nodes-base.microsoftOutlookTrigger': outlookIcon,
  'n8n-nodes-base.dateTime': dateTimeIcon,
  'n8n-nodes-base.switch': ifIcon,
  'n8n-nodes-base.splitInBatches': loopIcon,
  'n8n-nodes-base.noOp': noOpIcon,
  'n8n-nodes-base.whatsApp': whatsappIcon,
  'n8n-nodes-base.whatsAppTrigger': whatsappIcon,
  'n8n-nodes-base.extractFromFile': convertToFileIcon,
  
  // Parser nodes
  'n8n-nodes-base.xml': codeIcon,
  'n8n-nodes-base.json': codeIcon,
  'n8n-nodes-base.html': codeIcon,
  'n8n-nodes-base.csv': codeIcon,
  'n8n-nodes-base.yaml': codeIcon,
  'n8n-nodes-base.markdown': codeIcon,
  
  // LangChain nodes
  '@n8n/n8n-nodes-langchain.agent': agentIcon,
  '@n8n/n8n-nodes-langchain.toolSerpApi': serpApiIcon,
  '@n8n/n8n-nodes-langchain.toolDateTime': dateTimeIcon,
  '@n8n/n8n-nodes-langchain.memoryPostgresChat': postgresElephantIcon,
  '@n8n/n8n-nodes-langchain.memoryPostgresChatMemory': postgresElephantIcon,
  '@n8n/n8n-nodes-langchain.memoryBufferWindow': memoryIcon,
  '@n8n/n8n-nodes-langchain.lmChatOpenAi': openAiIcon,
  '@n8n/n8n-nodes-langchain.embeddingsOpenAi': openAiIcon,
  '@n8n/n8n-nodes-langchain.openAi': openAiIcon,
  '@n8n/n8n-nodes-langchain.chatTrigger': chatTriggerIcon,
  '@n8n/n8n-nodes-langchain.vectorStoreQdrant': qdrantIcon,
  '@n8n/n8n-nodes-langchain.toolVectorStore': qdrantIcon,
  '@n8n/n8n-nodes-langchain.retrieverVectorStore': qdrantIcon,
  '@n8n/n8n-nodes-langchain.toolWorkflow': toolSubworkflowIcon,
  '@n8n/n8n-nodes-langchain.outputParserStructured': outputParserIcon,
  '@n8n/n8n-nodes-langchain.chainLlm': langchainChainIcon,
  '@n8n/n8n-nodes-langchain.chainSummarization': langchainChainIcon,
  '@n8n/n8n-nodes-langchain.toolMcp': mcpIcon,
}

interface Props {
  nodeType?: string
  size?: string
}

const props = withDefaults(defineProps<Props>(), {
  nodeType: '',
  size: 'w-8 h-8'
})

const className = computed(() => props.size)

const iconSrc = computed(() => {
  if (!props.nodeType) return null
  return iconMap[props.nodeType] || null
})

const placeholderText = computed(() => {
  if (!props.nodeType) return '?'
  
  let text = props.nodeType
    .replace('n8n-nodes-base.', '')
    .replace('@n8n/n8n-nodes-langchain.', '')
    .toUpperCase()
  
  return text.length > 6 ? text.substring(0, 6) : text
})
</script>

<style scoped>
.node-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.node-icon img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.placeholder-icon {
  width: 100%;
  height: 100%;
  background: #374151;
  border: 2px dashed #6B7280;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-text {
  color: #9CA3AF;
  font-size: 8px;
  font-weight: bold;
  text-align: center;
  word-break: break-all;
}
</style>