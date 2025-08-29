// Hybrid Icon Mapping - SVG + Lucide Fallback System
// Maps nodeType to either local SVG or Lucide icon name

// Import SVG files directly
import codeIcon from '../assets/nodeIcons/svg/code.svg'
import httprequestIcon from '../assets/nodeIcons/svg/httprequest.svg'
import supabaseIcon from '../assets/nodeIcons/svg/supabase.svg'
import telegramIcon from '../assets/nodeIcons/svg/telegram.svg'
import outlookIcon from '../assets/nodeIcons/svg/outlook.svg'
import googleDriveIcon from '../assets/nodeIcons/svg/googleDrive.svg'
import googleCalendarIcon from '../assets/nodeIcons/svg/googleCalendar.svg'
import mergeIcon from '../assets/nodeIcons/svg/merge.svg'
import openAiIcon from '../assets/nodeIcons/svg/openAi.svg'
import extractFromFileIcon from '../assets/nodeIcons/svg/extractFromFile.svg'
import splitOutIcon from '../assets/nodeIcons/svg/splitOut.svg'
import webhookIcon from '../assets/nodeIcons/svg/webhook.svg'

export const iconMap = {
  // ✅ NODES WITH SVG - Direct Vite imports
  'n8n-nodes-base.code': codeIcon,
  'n8n-nodes-base.httpRequest': httprequestIcon,
  'n8n-nodes-base.supabase': supabaseIcon,
  'n8n-nodes-base.telegram': telegramIcon,
  'n8n-nodes-base.microsoftOutlook': outlookIcon,
  'n8n-nodes-base.microsoftOutlookTrigger': outlookIcon,
  'n8n-nodes-base.googleDrive': googleDriveIcon,
  'n8n-nodes-base.googleCalendar': googleCalendarIcon,
  'n8n-nodes-base.merge': mergeIcon,
  'n8n-nodes-base.openAi': openAiIcon,
  'n8n-nodes-base.extractFromFile': extractFromFileIcon,
  'n8n-nodes-base.splitOut': splitOutIcon,
  'n8n-nodes-base.webhook': webhookIcon,

  // ❌ NODES WITHOUT SVG - Use Lucide fallback (from CSV analysis)
  'n8n-nodes-base.set': 'Edit', // Matita per Set
  'n8n-nodes-base.function': 'Zap', // Fulmine per Function
  'n8n-nodes-base.if': 'Settings', // Ingranaggio per If  
  'n8n-nodes-base.switch': 'Settings', // Ingranaggio per Switch
  'n8n-nodes-base.manualTrigger': 'Play', // Play per Manual Trigger
  'n8n-nodes-base.scheduleTrigger': 'Clock', // Orologio per Schedule
  'n8n-nodes-base.cron': 'Clock', // Orologio per Cron
  'n8n-nodes-base.executeWorkflow': 'Settings', // Ingranaggio per Execute
  'n8n-nodes-base.executeWorkflowTrigger': 'Settings', // Ingranaggio per Execute Trigger
  'n8n-nodes-base.dateTimeTool': 'Settings', // Ingranaggio per DateTime
  'n8n-nodes-base.formTrigger': 'Settings', // Ingranaggio per Form
  'n8n-nodes-base.emailReadImap': 'Mail', // Mail per Email
  'n8n-nodes-base.respondToWebhook': 'Settings', // Ingranaggio per Respond
  'n8n-nodes-base.telegramTrigger': 'MessageSquare', // Messaggio per Telegram Trigger
  'n8n-nodes-base.whatsAppTrigger': 'Settings', // Ingranaggio per WhatsApp

  // 🤖 LANGCHAIN NODES - All use Lucide (no SVG available)
  '@n8n/n8n-nodes-langchain.agent': 'Bot', // Robot per AI Agent
  '@n8n/n8n-nodes-langchain.lmChatOpenAi': 'Brain', // Cervello per Chat Model
  '@n8n/n8n-nodes-langchain.embeddingsOpenAi': 'Brain', // Cervello per Embeddings  
  '@n8n/n8n-nodes-langchain.vectorStoreQdrant': 'Database', // Database per Vector Store
  '@n8n/n8n-nodes-langchain.vectorStorePinecone': 'Database', // Database per Vector Store
  '@n8n/n8n-nodes-langchain.toolVectorStore': 'Settings', // Ingranaggio per Tool
  '@n8n/n8n-nodes-langchain.toolWorkflow': 'Settings', // Ingranaggio per Tool
  '@n8n/n8n-nodes-langchain.toolSerpApi': 'Settings', // Ingranaggio per Tool
  '@n8n/n8n-nodes-langchain.memoryPostgresChat': 'Settings', // Ingranaggio per Memory
  '@n8n/n8n-nodes-langchain.memoryBufferWindow': 'Settings', // Ingranaggio per Memory
  '@n8n/n8n-nodes-langchain.outputParserStructured': 'Settings', // Ingranaggio per Parser
  '@n8n/n8n-nodes-langchain.chatTrigger': 'Settings', // Ingranaggio per Chat Trigger
  '@n8n/n8n-nodes-langchain.openAi': 'Brain', // Cervello per OpenAI
  '@n8n/n8n-nodes-langchain.rerankerCohere': 'Settings', // Ingranaggio per Reranker
  '@n8n/n8n-nodes-langchain.retrieverVectorStore': 'Settings' // Ingranaggio per Retriever
}

// Function to get icon path by nodeType
export const getIconPath = (nodeType) => {
  return iconMap[nodeType] || null
}

// Function to check if icon exists for nodeType
export const hasIcon = (nodeType) => {
  return nodeType in iconMap
}