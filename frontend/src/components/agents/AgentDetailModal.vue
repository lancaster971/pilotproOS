<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="$emit('close')"
    >
      <div class="w-full max-w-6xl max-h-[90vh] bg-gray-900 border border-green-500/30 rounded-xl shadow-2xl overflow-hidden">
        
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-gray-800">
          <div class="flex items-center gap-4">
            <div class="p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              <Bot class="h-6 w-6 text-green-400" />
            </div>
            <div>
              <h2 class="text-2xl font-bold text-white">
                {{ timelineData?.workflowName || `Process ${workflowId}` }}
              </h2>
              <div class="flex items-center gap-3 mt-1">
                <span class="text-sm text-gray-400">ID: {{ workflowId }}</span>
                <span v-if="timelineData?.lastExecution" class="text-sm text-gray-400">
                  • Last execution: {{ timelineData.lastExecution.id }}
                </span>
                <span v-if="timelineData?.status" :class="[
                  'px-2 py-1 rounded text-xs font-medium',
                  timelineData.status === 'active' 
                    ? 'bg-green-500/10 border border-green-500/30 text-green-400'
                    : 'bg-yellow-500/10 border border-yellow-500/30 text-yellow-400'
                ]">
                  {{ timelineData.status.toUpperCase() }}
                </span>
              </div>
            </div>
          </div>
          
          <div class="flex items-center gap-2">
            <!-- Force Refresh Button -->
            <button
              @click="handleForceRefresh"
              :disabled="isRefreshing"
              class="flex items-center px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg font-medium transition-all"
              :class="{ 'opacity-50 cursor-not-allowed': isRefreshing }"
              title="Force refresh latest executions from workflow engine"
            >
              <RefreshCw :class="['w-4 h-4 mr-2', { 'animate-spin': isRefreshing }]" />
              {{ isRefreshing ? 'Refreshing...' : 'Force Refresh' }}
            </button>
            
            <button
              @click="$emit('close')"
              class="p-2 text-gray-400 hover:text-red-400 transition-colors"
            >
              <X class="h-5 w-5" />
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="flex items-center justify-center p-12">
          <div class="text-center">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-green-400"></div>
            <p class="mt-4 text-gray-400">Loading execution details...</p>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="p-6">
          <div class="flex items-center justify-center text-red-400">
            <XCircle class="w-6 h-6 mr-2" />
            <span>{{ error }}</span>
          </div>
          <div class="mt-4 text-center">
            <button @click="loadTimeline" class="btn-control-primary">Try Again</button>
          </div>
        </div>

        <!-- Content -->
        <div v-else>
          <!-- Tabs -->
          <div class="flex items-center gap-1 p-2 border-b border-gray-800 bg-gray-900/50">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all',
                activeTab === tab.id
                  ? 'bg-green-500 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              ]"
            >
              <component :is="tab.icon" class="h-4 w-4" />
              {{ tab.label }}
            </button>
          </div>

          <!-- Tab Content -->
          <div class="overflow-y-auto" style="max-height: calc(90vh - 200px);">
            
            <!-- Timeline Tab -->
            <div v-if="activeTab === 'timeline'" class="p-6">
              
              <!-- Workflow Summary -->
              <div v-if="timelineData" class="mb-6 p-4 bg-black/50 rounded-lg border border-gray-800">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-white font-medium">Workflow Summary</span>
                  <div class="flex items-center">
                    <CheckCircle v-if="timelineData.status === 'active'" class="w-5 h-5 text-green-400 mr-2" />
                    <XCircle v-else class="w-5 h-5 text-red-400 mr-2" />
                    <span :class="timelineData.status === 'active' ? 'text-green-400' : 'text-red-400'">
                      {{ timelineData.status?.toUpperCase() || 'UNKNOWN' }}
                    </span>
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span class="text-gray-400">Last Execution:</span>
                    <span class="text-white ml-2">
                      {{ timelineData.lastExecution ? formatTimestamp(timelineData.lastExecution.executedAt) : 'No executions' }}
                    </span>
                  </div>
                  <div>
                    <span class="text-gray-400">Duration:</span>
                    <span class="text-white ml-2">
                      {{ timelineData.lastExecution ? formatDuration(timelineData.lastExecution.duration) : 'N/A' }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Info header per timeline con freshness indicator -->
              <div class="mb-4 flex items-center justify-between">
                <div class="text-sm text-gray-400">
                  Showing workflow steps with intelligent data parsing
                </div>
                <div class="flex items-center text-xs text-gray-500">
                  <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
                  Auto-refresh: 5 min | Last check: {{ new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }) }}
                </div>
              </div>

              <!-- Timeline Steps with humanizeStepData -->
              <div v-if="timelineData?.timeline?.length > 0" class="space-y-4">
                <div
                  v-for="(step, index) in timelineData.timeline"
                  :key="step.nodeId || index"
                  :class="[
                    'border rounded-lg p-4',
                    getStepColor(step.status)
                  ]"
                >
                  <div 
                    class="flex items-center justify-between cursor-pointer"
                    @click="toggleExpanded(step.nodeId || index)"
                  >
                    <div class="flex items-center">
                      <component :is="getStepIcon(step.status)" class="w-4 h-4 mr-3" />
                      <div>
                        <div class="font-medium text-white">{{ step.nodeName || `Step ${index + 1}` }}</div>
                        <div class="text-sm text-gray-400">
                          {{ step.status === 'not-executed' 
                            ? 'Node not executed in this run' 
                            : step.summary || 'Execution step' }}
                        </div>
                      </div>
                    </div>
                    <div class="flex items-center">
                      <span class="text-xs text-gray-400 mr-3">
                        {{ step.status === 'not-executed' 
                          ? 'Skipped' 
                          : formatDuration(step.executionTime || 0) }}
                      </span>
                      <ChevronDown 
                        v-if="expandedStep === (step.nodeId || index)"
                        class="w-4 h-4 text-gray-400" 
                      />
                      <ChevronRight 
                        v-else
                        class="w-4 h-4 text-gray-400" 
                      />
                    </div>
                  </div>

                  <!-- Expanded Step Details with humanizeStepData -->
                  <div v-if="expandedStep === (step.nodeId || index)" class="mt-4 pt-4 border-t border-gray-700">
                    <div v-if="step.details" class="mb-4">
                      <div class="text-sm font-medium text-white mb-2">Details:</div>
                      <div class="text-sm text-gray-300">{{ step.details }}</div>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <!-- Input Data -->
                      <div>
                        <div class="text-sm font-medium text-white mb-2">Input:</div>
                        <div class="bg-gray-900 p-3 rounded text-sm text-gray-300 whitespace-pre-line">
                          {{ humanizeStepData(step.inputData, 'input', step.nodeType, step.nodeName) }}
                        </div>
                        <details class="mt-2">
                          <summary class="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                            Show technical data
                          </summary>
                          <pre class="bg-gray-800 p-2 rounded text-xs text-gray-400 overflow-x-auto mt-2">{{ 
                            step.inputData ? JSON.stringify(step.inputData, null, 2) : 'No input data' 
                          }}</pre>
                        </details>
                      </div>
                      
                      <!-- Output Data -->
                      <div>
                        <div class="text-sm font-medium text-white mb-2">Output:</div>
                        <div class="bg-gray-900 p-3 rounded text-sm text-gray-300 whitespace-pre-line">
                          {{ humanizeStepData(step.outputData, 'output', step.nodeType, step.nodeName) }}
                        </div>
                        <details class="mt-2">
                          <summary class="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                            Show technical data
                          </summary>
                          <pre class="bg-gray-800 p-2 rounded text-xs text-gray-400 overflow-x-auto mt-2">{{ 
                            step.outputData ? JSON.stringify(step.outputData, null, 2) : 'No output data' 
                          }}</pre>
                        </details>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- No Timeline Data -->
              <div v-else class="text-center py-8 text-gray-400">
                <Clock class="w-8 h-8 mx-auto mb-2" />
                <p>No workflow steps available</p>
                <p class="text-sm">
                  Steps will appear here when workflow executions contain process data.
                </p>
              </div>
            </div>

            <!-- Business Context Tab -->
            <div v-if="activeTab === 'context'" class="p-6 space-y-6">
              <div v-if="timelineData?.businessContext" class="p-4 bg-black/50 rounded-lg border border-gray-800">
                <h3 class="text-lg font-medium text-white mb-4">Business Context</h3>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div v-if="timelineData.businessContext.senderEmail" class="flex items-center">
                    <Mail class="w-4 h-4 text-blue-400 mr-2" />
                    <span class="text-gray-400">Sender:</span>
                    <span class="text-blue-400 ml-2">{{ timelineData.businessContext.senderEmail }}</span>
                  </div>
                  
                  <div v-if="timelineData.businessContext.orderId" class="flex items-center">
                    <Package class="w-4 h-4 text-green-400 mr-2" />
                    <span class="text-gray-400">Order ID:</span>
                    <span class="text-white ml-2">{{ timelineData.businessContext.orderId }}</span>
                  </div>
                  
                  <div v-if="timelineData.businessContext.subject" class="flex items-center">
                    <FileText class="w-4 h-4 text-yellow-400 mr-2" />
                    <span class="text-gray-400">Subject:</span>
                    <span class="text-white ml-2">{{ timelineData.businessContext.subject }}</span>
                  </div>
                  
                  <div v-if="timelineData.businessContext.classification" class="flex items-center">
                    <Tag class="w-4 h-4 text-purple-400 mr-2" />
                    <span class="text-gray-400">Classification:</span>
                    <span class="text-purple-400 ml-2">
                      {{ timelineData.businessContext.classification }}
                      <span v-if="timelineData.businessContext.confidence" class="text-gray-400 ml-1">
                        ({{ timelineData.businessContext.confidence }}%)
                      </span>
                    </span>
                  </div>
                </div>
              </div>

              <!-- Quick Actions -->
              <div v-if="timelineData?.businessContext?.senderEmail" class="p-4 bg-black/50 rounded-lg border border-gray-800">
                <h3 class="text-lg font-medium text-white mb-4">Quick Actions</h3>
                <div class="flex space-x-4">
                  <button
                    @click="replyToCustomer"
                    class="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
                  >
                    <Mail class="w-4 h-4 mr-2" />
                    Reply to Customer
                  </button>
                </div>
              </div>
            </div>

            <!-- Raw Data Tab -->
            <div v-if="activeTab === 'raw'" class="p-6">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center">
                  <Code class="w-5 h-5 text-gray-400 mr-2" />
                  <h3 class="text-lg font-medium text-white">Raw Timeline Data</h3>
                </div>
                <div class="flex gap-2">
                  <button
                    @click="generateReadableReport"
                    class="flex items-center px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
                  >
                    <FileText class="w-4 h-4 mr-1.5" />
                    Generate Report
                  </button>
                  <button
                    @click="downloadReport"
                    class="flex items-center px-3 py-1.5 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm transition-colors"
                  >
                    <Download class="w-4 h-4 mr-1.5" />
                    Download Report
                  </button>
                  <button
                    @click="showJsonData"
                    class="flex items-center px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
                  >
                    <Code class="w-4 h-4 mr-1.5" />
                    Show JSON
                  </button>
                </div>
              </div>
              
              <pre 
                id="raw-data-content"
                class="bg-black/50 p-4 rounded-lg border border-gray-800 text-xs text-gray-300 overflow-auto max-h-96 font-mono whitespace-pre"
              >{{ 
                timelineData ? 
                JSON.stringify(timelineData, null, 2).replace(/n8n/gi, 'WFEngine').replace(/\.nodes\./g, '.engine.').replace(/\.base\./g, '.core.') 
                : 'No data available' 
              }}</pre>
            </div>

          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { 
  X, Bot, RefreshCw, XCircle, Clock, CheckCircle, AlertTriangle, Settings,
  ChevronDown, ChevronRight, Mail, Package, FileText, Tag, Code, Download
} from 'lucide-vue-next'
import { useUIStore } from '../../stores/ui'

// Props
interface Props {
  workflowId: string
  tenantId: string
  show: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  close: []
}>()

// State
const uiStore = useUIStore()
const isLoading = ref(false)
const isRefreshing = ref(false)
const error = ref<string | null>(null)
const activeTab = ref('timeline')
const expandedStep = ref<string | null>(null)

// Timeline data
const timelineData = ref<any>(null)

// Tab configuration
const tabs = [
  { id: 'timeline', label: 'Timeline', icon: Clock },
  { id: 'context', label: 'Business Context', icon: FileText },
  { id: 'raw', label: 'Raw Data', icon: Code },
]

// Utility for converting dati JSON in descrizioni human-readable per EMAIL
const humanizeStepData = (data: any, dataType: 'input' | 'output', nodeType?: string, nodeName?: string): string => {
  // Sanitizza nodeType per rimuovere riferimenti a n8n
  const sanitizedType = nodeType?.replace(/n8n/gi, 'WFEngine').replace(/\.nodes\./g, '.engine.').replace(/\.base\./g, '.core.')
  
  // LOGICA SPECIALE PER TRIGGER NODES
  const isTriggerNode = sanitizedType?.includes('trigger') || 
                       sanitizedType?.includes('Trigger') ||
                       nodeName?.toLowerCase().includes('ricezione') ||
                       nodeName?.toLowerCase().includes('trigger')
  
  // Per nodi trigger, l'input è sempre "In attesa di dati"
  if (isTriggerNode && dataType === 'input') {
    return 'In attesa di nuove email dal server Microsoft Outlook'
  }
  
  if (!data) return 'Nessun dato disponibile'

  // Se è un array, prendi il primo elemento
  const processData = Array.isArray(data) ? data[0] : data
  
  if (!processData || typeof processData !== 'object') {
    return String(processData) || 'Dato non strutturato'
  }

  const dataString = JSON.stringify(processData)
  const insights: string[] = []
  
  // Determina il tipo di nodo per personalizzare il parsing
  const nodeNameLower = nodeName?.toLowerCase() || ''
  const isEmailNode = nodeNameLower.includes('mail') || nodeNameLower.includes('ricezione')
  const isAINode = nodeNameLower.includes('milena') || nodeNameLower.includes('assistente') || nodeNameLower.includes('ai')
  const isOrderNode = nodeNameLower.includes('ordini') || nodeNameLower.includes('order')
  const isVectorNode = nodeNameLower.includes('qdrant') || nodeNameLower.includes('vector')
  const isParcelNode = nodeNameLower.includes('parcel')
  const isReplyNode = nodeNameLower.includes('rispondi') || nodeNameLower.includes('reply')
  const isExecuteNode = nodeNameLower.includes('execute') || nodeNameLower.includes('workflow')
  
  // PARSER SPECIFICI PER TIPO DI NODO
  
  // 1. NODO EMAIL (Ricezione Mail)
  if (isEmailNode && dataType === 'output') {
    insights.push('--- EMAIL RICEVUTA ---')
    
    // Oggetto
    if (processData.json?.oggetto || processData.json?.subject) {
      insights.push(`Oggetto: "${processData.json?.oggetto || processData.json?.subject}"`)
    }
    
    // Mittente
    const senderFields = [
      processData.json?.mittente,
      processData.json?.mittente_nome,
      processData.json?.sender?.emailAddress?.address,
      processData.sender?.emailAddress?.address
    ]
    const sender = senderFields.find(field => field)
    if (sender) {
      insights.push(`Da: ${sender}`)
    }
    
    // Contenuto
    const emailBodyFields = [
      processData.json?.messaggio_cliente,
      processData.json?.messaggio,
      processData.json?.body?.content,
      processData.json?.body,
      processData.json?.content
    ]
    const emailBody = emailBodyFields.find(field => 
      field && typeof field === 'string' && field.length > 20
    )
    if (emailBody) {
      const cleanContent = emailBody
        .replace(/<[^>]+>/g, ' ')
        .replace(/&[a-zA-Z0-9]+;/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
      const preview = cleanContent.substring(0, 150)
      insights.push(`Messaggio: "${preview}${preview.length >= 150 ? '...' : ''}"`)
    }
  }
  
  // 2. NODO AI ASSISTANT (Milena)
  else if (isAINode && dataType === 'output') {
    insights.push('--- RISPOSTA AI GENERATA ---')
    
    const aiResponseFields = [
      processData.json?.output?.risposta_html,
      processData.json?.risposta_html,
      processData.json?.ai_response,
      processData.json?.response,
      processData.json?.output
    ]
    
    const aiResponse = aiResponseFields.find(field => 
      field && typeof field === 'string' && field.length > 20
    )
    
    if (aiResponse) {
      const cleanResponse = aiResponse
        .replace(/<[^>]+>/g, ' ')
        .replace(/&[a-zA-Z0-9]+;/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
      const preview = cleanResponse.substring(0, 200)
      insights.push(`Risposta: "${preview}${preview.length >= 200 ? '...' : ''}"`)
    }
    
    // Categoria se presente
    if (processData.json?.categoria || processData.json?.classification) {
      insights.push(`Categoria: ${processData.json?.categoria || processData.json?.classification}`)
    }
  }
  
  // 3. NODO VECTOR STORE (Qdrant)
  else if (isVectorNode && dataType === 'output') {
    insights.push('--- RICERCA VETTORIALE ---')
    
    if (processData.json?.matches || processData.json?.results) {
      const matches = processData.json?.matches || processData.json?.results
      const count = Array.isArray(matches) ? matches.length : 1
      insights.push(`Documenti trovati: ${count}`)
    }
    
    if (processData.json?.score || processData.json?.similarity) {
      insights.push(`Similarità: ${processData.json?.score || processData.json?.similarity}`)
    }
    
    if (processData.json?.content || processData.json?.text) {
      const content = processData.json?.content || processData.json?.text
      const preview = content.substring(0, 100)
      insights.push(`Contenuto: "${preview}${preview.length >= 100 ? '...' : ''}"`)
    }
  }
  
  // 4. NODO PARCEL APP
  else if (isParcelNode && dataType === 'output') {
    insights.push('--- TRACKING SPEDIZIONE ---')
    
    if (processData.json?.tracking_number) {
      insights.push(`Numero tracking: ${processData.json.tracking_number}`)
    }
    if (processData.json?.status) {
      insights.push(`Stato: ${processData.json.status}`)
    }
    if (processData.json?.location) {
      insights.push(`Posizione: ${processData.json.location}`)
    }
    if (processData.json?.estimated_delivery) {
      insights.push(`Consegna prevista: ${processData.json.estimated_delivery}`)
    }
  }
  
  // 5. NODO RISPOSTA EMAIL
  else if (isReplyNode && dataType === 'output') {
    insights.push('--- EMAIL INVIATA ---')
    
    if (processData.json?.to) {
      insights.push(`Destinatario: ${processData.json.to}`)
    }
    if (processData.json?.subject) {
      insights.push(`Oggetto: ${processData.json.subject}`)
    }
    if (processData.json?.sent || processData.json?.success) {
      insights.push(`Stato: Email inviata con successo`)
    }
  }
  
  // 6. NODO EXECUTE WORKFLOW
  else if (isExecuteNode && dataType === 'output') {
    insights.push('--- WORKFLOW ESEGUITO ---')
    
    if (processData.json?.workflowId) {
      insights.push(`Workflow ID: ${processData.json.workflowId}`)
    }
    if (processData.json?.executionId) {
      insights.push(`Execution ID: ${processData.json.executionId}`)
    }
    if (processData.json?.status) {
      insights.push(`Stato: ${processData.json.status}`)
    }
  }
  
  // Se non abbiamo insights specifici, prova i parser generici

  // PRIORITÀ 4: DATI ORDINE (per nodi tipo INFO ORDINI)
  if (processData.json?.order_reference || processData.json?.orderFound) {
    insights.push('--- DATI ORDINE RECUPERATI ---')
    
    if (processData.json?.order_reference) {
      insights.push(`Riferimento: ${processData.json.order_reference}`)
    }
    if (processData.json?.customer_full_name) {
      insights.push(`Cliente: ${processData.json.customer_full_name}`)
    }
    if (processData.json?.order_status) {
      insights.push(`Stato: ${processData.json.order_status}`)
    }
    if (processData.json?.order_total_paid) {
      insights.push(`Totale: ${processData.json.order_total_paid}`)
    }
    if (processData.json?.delivery_city) {
      insights.push(`Città consegna: ${processData.json.delivery_city}`)
    }
    if (processData.json?.order_shipping_number) {
      insights.push(`Tracking: ${processData.json.order_shipping_number}`)
    }
    if (processData.json?.chatbotResponse) {
      const cleanResponse = processData.json.chatbotResponse.replace(/[✅❌📦]/g, '').trim()
      insights.push(`Risposta: ${cleanResponse}`)
    }
  }

  // PRIORITÀ 5: RISPOSTA AI (se presente)
  const aiResponseFields = [
    processData.json?.output?.risposta_html,
    processData.json?.risposta_html,
    processData.json?.ai_response,
    processData.json?.response
  ]
  
  const aiResponse = aiResponseFields.find(field => 
    field && typeof field === 'string' && field.length > 20
  )
  
  if (aiResponse) {
    const cleanResponse = aiResponse
      .replace(/<[^>]+>/g, ' ')
      .replace(/&[a-zA-Z0-9]+;/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
    const preview = cleanResponse.substring(0, 150)
    insights.push(`Risposta AI: "${preview}${preview.length >= 150 ? '...' : ''}"`)
  }

  // PRIORITÀ 5: CLASSIFICAZIONE/CATEGORIA (se utile)
  if (processData.json?.output?.categoria && processData.json?.output?.confidence) {
    insights.push(`Classificazione: ${processData.json.output.categoria} (${processData.json.output.confidence} confidence)`)
  } else if (processData.json?.categoria && processData.json?.confidence) {
    insights.push(`Classificazione: ${processData.json.categoria} (${processData.json.confidence}% confidence)`)
  }

  // PRIORITÀ 6: ORDER ID (se specifico)
  if (processData.json?.output?.order_id && processData.json.output.order_id !== '000000') {
    insights.push(`Ordine: ${processData.json.output.order_id}`)
  } else if (processData.json?.order_id && processData.json.order_id !== '000000') {
    insights.push(`Ordine: ${processData.json.order_id}`)
  }

  // FALLBACK: Se non troviamo contenuti email, mostra dati generici
  if (insights.length === 0) {
    // Cerca almeno email e subject base
    const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g
    const emails = dataString.match(emailRegex)
    if (emails && emails.length > 0) {
      insights.push(`Email rilevata: ${emails[0]}`)
    }
    
    // Mostra le chiavi principali come fallback
    const keys = Object.keys(processData.json || processData)
    if (keys.length > 0) {
      insights.push(`Campi disponibili: ${keys.slice(0, 4).join(', ')}${keys.length > 4 ? '...' : ''}`)
    } else {
      return 'Dati complessi - espandi per visualizzare dettagli completi'
    }
  }

  return insights.join('\n')
}

// Load timeline data
const loadTimeline = async () => {
  isLoading.value = true
  error.value = null
  
  try {
    console.log('🔄 Loading agent timeline for workflow:', props.workflowId)
    
    // Call backend API for timeline data
    const response = await fetch(`http://localhost:3001/api/business/process-timeline/${props.workflowId}`)
    
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('✅ Agent timeline loaded:', data.data)
    
    timelineData.value = data.data
    
  } catch (err: any) {
    console.error('❌ Failed to load agent timeline:', err)
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

// Force refresh
const handleForceRefresh = async () => {
  isRefreshing.value = true
  
  try {
    console.log('🔥 FORCE REFRESH: Agent timeline for workflow', props.workflowId)
    
    // Try force refresh endpoint
    try {
      const refreshResponse = await fetch(`http://localhost:3001/api/business/process-refresh/${props.workflowId}`, {
        method: 'POST'
      })
      
      if (refreshResponse.ok) {
        console.log('✅ Force refresh succeeded')
        uiStore.showToast('Success', 'Timeline data refreshed successfully', 'success')
      }
    } catch (refreshError) {
      console.warn('⚠️ Force refresh endpoint not available:', refreshError)
    }
    
    // Reload timeline data
    await loadTimeline()
    
  } catch (error: any) {
    uiStore.showToast('Error', `Failed to refresh: ${error.message}`, 'error')
  } finally {
    isRefreshing.value = false
  }
}

// Utility functions
const formatDuration = (ms: number) => {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}min`
}

const formatTimestamp = (timestamp: string) => {
  return new Date(timestamp).toLocaleString('it-IT', {
    dateStyle: 'short',
    timeStyle: 'medium'
  })
}

const toggleExpanded = (stepId: string | number) => {
  expandedStep.value = expandedStep.value === stepId ? null : String(stepId)
}

const getStepIcon = (status: string) => {
  switch (status) {
    case 'success': return CheckCircle
    case 'error': return XCircle
    case 'running': return Settings
    case 'not-executed': return Clock
    default: return Clock
  }
}

const getStepColor = (status: string) => {
  switch (status) {
    case 'success': return 'border-green-400/30 bg-green-400/5'
    case 'error': return 'border-red-400/30 bg-red-400/5'
    case 'running': return 'border-yellow-400/30 bg-yellow-400/5'
    case 'not-executed': return 'border-gray-600/30 bg-gray-800/50'
    default: return 'border-gray-400/30 bg-gray-400/5'
  }
}

const replyToCustomer = () => {
  const senderEmail = timelineData.value?.businessContext?.senderEmail
  const subject = timelineData.value?.businessContext?.subject || ''
  
  if (senderEmail) {
    window.open(`mailto:${senderEmail}?subject=Re: ${subject}`, '_blank')
  }
}

const generateReadableReport = () => {
  if (!timelineData.value) return
  
  let report = `╔${'═'.repeat(78)}╗\n`
  report += `║${' '.repeat(20)}REPORT DETTAGLIATO ESECUZIONE WORKFLOW${' '.repeat(20)}║\n`
  report += `║${' '.repeat(25)}PilotPro Control Center v1.3.0${' '.repeat(24)}║\n`
  report += `╚${'═'.repeat(78)}╝\n\n`
  
  // SEZIONE 1: INFORMAZIONI GENERALI
  report += `┌─ INFORMAZIONI GENERALI ${'─'.repeat(54)}┐\n\n`
  
  report += `  Nome Workflow:     ${timelineData.value.workflowName || 'Non specificato'}\n`
  report += `  ID Workflow:       ${props.workflowId}\n`
  report += `  Stato Workflow:    ${timelineData.value.status === 'active' ? 'ATTIVO' : 'INATTIVO'}\n`
  
  if (timelineData.value.lastExecution) {
    report += `\n  ULTIMA ESECUZIONE:\n`
    report += `  ├─ ID Esecuzione:  ${timelineData.value.lastExecution.id}\n`
    report += `  ├─ Data/Ora:       ${formatTimestamp(timelineData.value.lastExecution.executedAt)}\n`
    report += `  ├─ Durata Totale:  ${formatDuration(timelineData.value.lastExecution.duration)}\n`
    report += `  └─ Status:         ${timelineData.value.lastExecution.status || 'Completato'}\n`
  }
  
  report += `\n└${'─'.repeat(78)}┘\n\n`
  
  // SEZIONE 2: CONTESTO BUSINESS DETTAGLIATO
  if (timelineData.value.businessContext && Object.keys(timelineData.value.businessContext).length > 0) {
    report += `┌─ ANALISI CONTESTO BUSINESS ${'─'.repeat(49)}┐\n\n`
    
    report += `  Questo workflow ha processato una comunicazione business con i seguenti\n`
    report += `  parametri identificati automaticamente dal sistema AI:\n\n`
    
    if (timelineData.value.businessContext.senderEmail) {
      report += `  MITTENTE EMAIL:\n`
      report += `     Email: ${timelineData.value.businessContext.senderEmail}\n`
      report += `     Tipo: ${timelineData.value.businessContext.senderEmail.includes('@') ? 'Email valida' : 'Formato non standard'}\n\n`
    }
    
    if (timelineData.value.businessContext.subject) {
      report += `  OGGETTO COMUNICAZIONE:\n`
      report += `     "${timelineData.value.businessContext.subject}"\n\n`
    }
    
    if (timelineData.value.businessContext.orderId) {
      report += `  RIFERIMENTO ORDINE:\n`
      report += `     ID Ordine: ${timelineData.value.businessContext.orderId}\n`
      report += `     Formato: ${timelineData.value.businessContext.orderId.length > 10 ? 'ID Esteso' : 'ID Standard'}\n\n`
    }
    
    if (timelineData.value.businessContext.classification) {
      report += `  CLASSIFICAZIONE AI:\n`
      report += `     Categoria Identificata: ${timelineData.value.businessContext.classification}\n`
      if (timelineData.value.businessContext.confidence) {
        report += `     Livello di Confidenza: ${timelineData.value.businessContext.confidence}%\n`
        const confidenceLevel = timelineData.value.businessContext.confidence > 80 ? 'ALTA' : 
                                timelineData.value.businessContext.confidence > 60 ? 'MEDIA' : 'BASSA'
        report += `     Affidabilità: ${confidenceLevel}\n`
      }
      report += `\n`
    }
    
    report += `└${'─'.repeat(78)}┘\n\n`
  }
  
  // Update the raw data content
  const preElement = document.getElementById('raw-data-content')
  if (preElement) {
    preElement.textContent = report
  }
}

const downloadReport = () => {
  generateReadableReport()
  
  if (!timelineData.value) return
  
  const report = generateReadableReport()
  const blob = new Blob([report], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `agent-report-${props.workflowId}-${new Date().toISOString().slice(0, 10)}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const showJsonData = () => {
  const preElement = document.getElementById('raw-data-content')
  if (preElement && timelineData.value) {
    const sanitizedJson = JSON.stringify(timelineData.value, null, 2)
      .replace(/n8n/gi, 'WFEngine')
      .replace(/\.nodes\./g, '.engine.')
      .replace(/\.base\./g, '.core.')
    preElement.textContent = sanitizedJson
  }
}

// Watchers
watch(() => props.show, (newShow) => {
  if (newShow) {
    console.log('📊 Agent modal opened for workflow:', props.workflowId)
    loadTimeline()
    activeTab.value = 'timeline'
  }
})

// Lifecycle
onMounted(() => {
  if (props.show) {
    loadTimeline()
  }
})
</script>

<style scoped>
.btn-control-primary {
  @apply flex items-center gap-2 px-4 py-2 bg-green-600 border border-green-500 text-white rounded-lg hover:bg-green-500 hover:border-green-400 transition-all text-sm;
}

/* Tab content max height */
.overflow-y-auto {
  scrollbar-width: thin;
  scrollbar-color: #4ade80 #1f2937;
}

.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #1f2937;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #4ade80;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #22c55e;
}
</style>