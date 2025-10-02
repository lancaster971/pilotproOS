<template>
  <MainLayout>
  <div class="milhena-chat-container">
    <!-- Header -->
    <div class="chat-header">
      <div class="header-content">
        <div class="header-left">
          <Icon icon="mdi:robot-happy" class="header-icon" />
          <div>
            <h1>Milhena Assistant</h1>
            <p class="subtitle">v3.0 Learning Edition - Self-Improving AI</p>
          </div>
        </div>
        <div class="header-stats">
          <div class="stat">
            <span class="stat-value">{{ responseTime }}ms</span>
            <span class="stat-label">Latency</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ accuracy }}%</span>
            <span class="stat-label">Accuracy</span>
          </div>
          <div class="stat" v-if="isLearning">
            <Icon icon="mdi:brain" class="learning-icon animate-pulse" />
            <span class="stat-label">Learning...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat Messages -->
    <div class="chat-messages" ref="messagesContainer">
      <!-- Welcome Message -->
      <div v-if="messages.length === 0" class="welcome-message">
        <Icon icon="mdi:hand-wave" class="wave-icon" />
        <h2>Ciao! Sono Milhena</h2>
        <p>Il tuo assistente AI per PilotProOS. Posso aiutarti con:</p>
        <div class="quick-actions">
          <button @click="sendQuickMessage('Mostrami i workflow attivi')" class="quick-btn">
            <Icon icon="mdi:workflow" />
            Workflow Attivi
          </button>
          <button @click="sendQuickMessage('Analizza le performance di oggi')" class="quick-btn">
            <Icon icon="mdi:chart-line" />
            Performance Oggi
          </button>
          <button @click="sendQuickMessage('Quali sono gli ultimi errori?')" class="quick-btn">
            <Icon icon="mdi:alert-circle" />
            Ultimi Errori
          </button>
          <button @click="sendQuickMessage('Come funzioni?')" class="quick-btn">
            <Icon icon="mdi:help-circle" />
            Come Funzioni
          </button>
        </div>
      </div>

      <!-- Messages List -->
      <div v-for="(message, index) in messages" :key="index"
           :class="['message', message.role]">
        <div class="message-avatar">
          <Icon v-if="message.role === 'user'" icon="mdi:account" />
          <Icon v-else icon="mdi:robot" />
        </div>
        <div class="message-content">
          <div class="message-header">
            <span class="message-sender">{{ message.role === 'user' ? 'Tu' : 'Milhena' }}</span>
            <span class="message-time">{{ formatTime(message.timestamp) }}</span>
            <span v-if="message.latency" class="message-latency">{{ message.latency }}ms</span>
          </div>
          <div class="message-text" v-html="formatMessage(message.content)"></div>

          <!-- Confidence Indicator -->
          <div v-if="message.confidence" class="message-confidence">
            <div class="confidence-bar">
              <div class="confidence-fill"
                   :style="{width: (message.confidence * 100) + '%'}"
                   :class="{
                     'high': message.confidence > 0.8,
                     'medium': message.confidence > 0.6 && message.confidence <= 0.8,
                     'low': message.confidence <= 0.6
                   }">
              </div>
            </div>
            <span class="confidence-text">Confidence: {{ (message.confidence * 100).toFixed(0) }}%</span>
          </div>

          <!-- Feedback Buttons for Assistant Messages -->
          <div v-if="message.role === 'assistant' && !message.feedback" class="feedback-buttons">
            <button @click="sendFeedback(index, 'positive')"
                    class="feedback-btn positive"
                    title="Risposta utile">
              <Icon icon="mdi:thumb-up-outline" />
            </button>
            <button @click="sendFeedback(index, 'negative')"
                    class="feedback-btn negative"
                    title="Risposta non utile">
              <Icon icon="mdi:thumb-down-outline" />
            </button>
          </div>

          <!-- Feedback Confirmation -->
          <div v-if="message.feedback" class="feedback-confirmed">
            <span v-if="message.feedback === 'positive'" class="positive">
              <Icon icon="mdi:check-circle" /> Grazie per il feedback!
            </span>
            <span v-else class="negative">
              <Icon icon="mdi:alert-circle" /> Grazie, sto imparando...
            </span>
          </div>

          <!-- Reformulation Helper -->
          <div v-if="message.feedback === 'negative' && !message.reformulated" class="reformulation-helper">
            <p>Puoi riformulare la domanda per aiutarmi a capire meglio?</p>
            <div class="suggestions">
              <button v-for="suggestion in getReformulationSuggestions(message)"
                      :key="suggestion"
                      @click="sendQuickMessage(suggestion)"
                      class="suggestion-btn">
                {{ suggestion }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Typing Indicator -->
      <div v-if="isTyping" class="message assistant typing">
        <div class="message-avatar">
          <Icon icon="mdi:robot" />
        </div>
        <div class="message-content">
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="chat-input-container">
      <div class="input-wrapper">
        <input
          v-model="inputMessage"
          @keyup.enter="sendMessage"
          :disabled="isLoading"
          placeholder="Chiedi qualsiasi cosa su processi, workflow, performance..."
          class="chat-input"
        />
        <button
          @click="sendMessage"
          :disabled="!inputMessage.trim() || isLoading"
          class="send-button"
        >
          <Icon v-if="isLoading" icon="mdi:loading" class="animate-spin" />
          <Icon v-else icon="mdi:send" />
        </button>
      </div>
      <div class="input-hint">
        <Icon icon="mdi:information" />
        <span v-if="isReformulating" class="reformulation-alert">
          🔄 Sto imparando dalla tua correzione...
        </span>
        <span v-else>Milhena impara dai tuoi feedback per migliorare continuamente.</span>
      </div>
    </div>

    <!-- Learning Stats Footer -->
    <div class="learning-stats">
      <div class="stat-item">
        <span class="stat-label">Oggi:</span>
        <span class="stat-value">{{ todayStats.queries }} queries</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Patterns appresi:</span>
        <span class="stat-value">{{ todayStats.patterns }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Miglioramento:</span>
        <span class="stat-value">+{{ todayStats.improvement }}%</span>
      </div>
      <div class="stat-item" v-if="todayStats.cache_hit_rate">
        <span class="stat-label">Cache Hit:</span>
        <span class="stat-value">{{ todayStats.cache_hit_rate }}%</span>
      </div>
    </div>
  </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Icon } from '@iconify/vue'
import { useToast } from 'vue-toastification'
import { apiClient } from '@/services/api-client'
import MainLayout from '@/components/layout/MainLayout.vue'

const toast = useToast()

// State
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const isTyping = ref(false)
const isLearning = ref(false)
const isReformulating = ref(false)
const responseTime = ref(0)
const accuracy = ref(92) // Will be updated from API
const messagesContainer = ref(null)
const sessionId = ref(generateSessionId())
const todayStats = ref({
  queries: 0,
  patterns: 0,
  improvement: 0,
  cache_hit_rate: 0
})

// Generate session ID
function generateSessionId() {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

// Format time
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('it-IT', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Format message with markdown support
const formatMessage = (text) => {
  // Convert markdown bold
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  // Convert markdown italic
  text = text.replace(/\*(.*?)\*/g, '<em>$1</em>')
  // Convert line breaks
  text = text.replace(/\n/g, '<br>')
  // Convert bullet points
  text = text.replace(/• /g, '🔸 ')

  return text
}

// Scroll to bottom
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// Send quick message
const sendQuickMessage = (text) => {
  inputMessage.value = text
  sendMessage()
}

// Send feedback
const sendFeedback = async (messageIndex, feedbackType) => {
  const message = messages.value[messageIndex]
  if (!message || message.feedback) return

  // Mark message with feedback
  message.feedback = feedbackType

  // If negative, prepare for reformulation detection
  if (feedbackType === 'negative') {
    isReformulating.value = true
    setTimeout(() => {
      isReformulating.value = false
    }, 30000) // 30 seconds window for reformulation
  }

  // Show learning indicator
  isLearning.value = true
  setTimeout(() => {
    isLearning.value = false
  }, 3000)

  try {
    // Send feedback to API
    await apiClient.post('/api/milhena/feedback', {
      session_id: sessionId.value,
      message_id: message.id || messageIndex,
      query: messages.value[messageIndex - 1]?.content || '',
      response: message.content,
      feedback_type: feedbackType,
      confidence: message.confidence,
      timestamp: message.timestamp
    })

    toast.success(feedbackType === 'positive' ?
                  'Grazie per il feedback positivo!' :
                  'Grazie, userò questo feedback per migliorare')
  } catch (error) {
    console.error('Feedback error:', error)
  }
}

// Get reformulation suggestions
const getReformulationSuggestions = (message) => {
  const suggestions = []

  // Generate contextual suggestions based on the query
  if (message.intent === 'ERRORS' || message.content.includes('error')) {
    suggestions.push('Mostra solo gli errori critici di oggi')
    suggestions.push('Quali processi hanno avuto problemi nelle ultime 24 ore?')
  } else if (message.intent === 'METRICS' || message.content.includes('metric')) {
    suggestions.push('Quante fatture sono state elaborate oggi?')
    suggestions.push('Dammi le statistiche complete del sistema')
  } else {
    suggestions.push('Mostra lo stato generale del sistema')
    suggestions.push('Ci sono problemi urgenti da risolvere?')
  }

  return suggestions
}

// Send message
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userMessage = {
    role: 'user',
    content: inputMessage.value,
    timestamp: new Date(),
    isReformulation: isReformulating.value
  }

  messages.value.push(userMessage)
  const question = inputMessage.value
  inputMessage.value = ''

  // Check if this is a reformulation
  let contextData = {
    conversation_history: messages.value.slice(-10), // Last 10 messages
    is_reformulation: isReformulating.value
  }

  if (isReformulating.value) {
    // Find the last negative feedback message
    const lastNegativeIndex = messages.value.findLastIndex(m => m.feedback === 'negative')
    if (lastNegativeIndex >= 0) {
      contextData.original_query = messages.value[lastNegativeIndex - 1]?.content || ''
      contextData.failed_response = messages.value[lastNegativeIndex]?.content || ''
    }
    isReformulating.value = false
  }

  isLoading.value = true
  isTyping.value = true
  scrollToBottom()

  const startTime = Date.now()

  try {
    // Call Milhena API via backend proxy
    const response = await apiClient.post('/api/milhena/chat', {
      message: question,
      session_id: sessionId.value,
      context: contextData
    })

    const latency = Date.now() - startTime
    responseTime.value = latency

    // Update accuracy if provided
    if (response.data.system_accuracy) {
      accuracy.value = Math.round(response.data.system_accuracy * 100)
    }

    // Add assistant response with all metadata
    messages.value.push({
      role: 'assistant',
      content: response.data.response || response.data.message,
      timestamp: new Date(),
      confidence: response.data.confidence,
      intent: response.data.intent,
      latency: latency,
      cached: response.data.cached || false,
      learned: response.data.learned || false
    })

    // Update stats if learned something
    if (response.data.learned) {
      todayStats.value.patterns++
    }

  } catch (error) {
    console.error('Chat error:', error)

    // Fallback message
    messages.value.push({
      role: 'assistant',
      content: error.response?.data?.message ||
               'Mi dispiace, c\'è stato un problema. Riprova tra poco.',
      timestamp: new Date(),
      latency: Date.now() - startTime
    })

    toast.error('Errore nella comunicazione con Milhena')
  } finally {
    isLoading.value = false
    isTyping.value = false
    scrollToBottom()
    todayStats.value.queries++
  }
}

// Load learning stats
const loadLearningStats = async () => {
  try {
    const response = await apiClient.get('/api/milhena/learning/stats/today')
    todayStats.value = response.data

    // Update accuracy from stats
    if (response.data.accuracy) {
      accuracy.value = Math.round(response.data.accuracy * 100)
    }
  } catch (error) {
    console.error('Failed to load learning stats:', error)
  }
}

// Welcome message on mount
onMounted(() => {
  // Load learning stats
  loadLearningStats()

  // Refresh stats every 60 seconds
  const statsInterval = setInterval(loadLearningStats, 60000)

  // Optional: Add initial greeting
  setTimeout(() => {
    messages.value.push({
      role: 'assistant',
      content: 'Ciao! Sono Milhena v3.0 Learning Edition. Imparo dai tuoi feedback per migliorare continuamente. Come posso aiutarti oggi?',
      timestamp: new Date(),
      confidence: 1.0
    })
  }, 500)

  // Cleanup on unmount
  onBeforeUnmount(() => {
    clearInterval(statsInterval)
  })
})
</script>

