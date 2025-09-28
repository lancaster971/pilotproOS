<template>
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
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Icon } from '@iconify/vue'
import { useToast } from 'vue-toastification'
import apiClient from '@/services/api-client'

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
    // Call Milhena API with session support
    const response = await apiClient.post('/api/milhena/query', {
      question: question,
      session_id: sessionId.value,
      context: contextData,
      user_id: 'frontend_user'
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

<style scoped>
.milhena-chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
}

/* Header */
.chat-header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 1.5rem;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-icon {
  font-size: 2.5rem;
  color: white;
}

.chat-header h1 {
  color: white;
  font-size: 1.5rem;
  margin: 0;
}

.subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.875rem;
  margin: 0;
}

.header-stats {
  display: flex;
  gap: 2rem;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  color: white;
  font-size: 1.25rem;
  font-weight: 600;
}

.stat-label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.75rem;
  text-transform: uppercase;
}

/* Chat Messages */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}

.welcome-message {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.wave-icon {
  font-size: 3rem;
  color: #667eea;
  animation: wave 1s ease-in-out;
}

@keyframes wave {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-20deg); }
  75% { transform: rotate(20deg); }
}

.welcome-message h2 {
  color: #333;
  margin: 1rem 0;
}

.welcome-message p {
  color: #666;
  margin-bottom: 1.5rem;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.quick-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.3s;
}

.quick-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

/* Messages */
.message {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  animation: messageIn 0.3s ease;
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.message.assistant .message-avatar {
  background: white;
  color: #667eea;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.message-content {
  flex: 1;
  background: white;
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.message-sender {
  font-weight: 600;
  color: #333;
}

.message-time {
  color: #999;
}

.message-latency {
  background: #10b981;
  color: white;
  padding: 0.125rem 0.375rem;
  border-radius: 9999px;
  font-size: 0.75rem;
}

.message-text {
  color: #333;
  line-height: 1.6;
}

.message-confidence {
  margin-top: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.confidence-bar {
  flex: 1;
  height: 4px;
  background: #e5e7eb;
  border-radius: 9999px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.5s ease;
}

.confidence-text {
  font-size: 0.75rem;
  color: #666;
}

/* Typing Indicator */
.typing-indicator {
  display: flex;
  gap: 0.25rem;
  padding: 0.5rem;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #999;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    opacity: 0.3;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-10px);
  }
}

/* Input Area */
.chat-input-container {
  background: white;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

.input-wrapper {
  display: flex;
  gap: 1rem;
  max-width: 900px;
  margin: 0 auto;
}

.chat-input {
  flex: 1;
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: all 0.3s;
}

.chat-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.send-button {
  padding: 0 1.5rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  font-size: 1.25rem;
}

.send-button:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.input-hint {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  max-width: 900px;
  margin: 0.5rem auto 0;
  font-size: 0.875rem;
  color: #666;
}

/* Scrollbar */
.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 9999px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

/* Feedback Buttons */
.feedback-buttons {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.feedback-btn {
  padding: 0.375rem 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 9999px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
}

.feedback-btn:hover {
  transform: scale(1.1);
}

.feedback-btn.positive:hover {
  background: #e8f5e9;
  border-color: #4caf50;
  color: #4caf50;
}

.feedback-btn.negative:hover {
  background: #ffebee;
  border-color: #f44336;
  color: #f44336;
}

.feedback-confirmed {
  margin-top: 0.75rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.feedback-confirmed.positive {
  background: #e8f5e9;
  color: #2e7d32;
}

.feedback-confirmed.negative {
  background: #fff3e0;
  color: #e65100;
}

/* Reformulation Helper */
.reformulation-helper {
  margin-top: 1rem;
  padding: 1rem;
  background: #fff3e0;
  border-radius: 0.5rem;
  border-left: 3px solid #ff9800;
}

.reformulation-helper p {
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  color: #666;
}

.suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.suggestion-btn {
  padding: 0.5rem 1rem;
  background: white;
  border: 1px solid #ff9800;
  border-radius: 9999px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.suggestion-btn:hover {
  background: #ff9800;
  color: white;
}

/* Confidence Styles */
.confidence-fill.high {
  background: linear-gradient(90deg, #4caf50, #66bb6a);
}

.confidence-fill.medium {
  background: linear-gradient(90deg, #ff9800, #ffa726);
}

.confidence-fill.low {
  background: linear-gradient(90deg, #f44336, #ef5350);
}

/* Learning Indicator */
.learning-icon {
  color: #9c27b0;
  font-size: 1.5rem;
}

.animate-pulse {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* Learning Stats Footer */
.learning-stats {
  display: flex;
  justify-content: space-around;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.95);
  border-top: 1px solid rgba(102, 126, 234, 0.2);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.learning-stats .stat-label {
  color: #666;
  font-size: 0.75rem;
  text-transform: uppercase;
}

.learning-stats .stat-value {
  font-weight: 600;
  color: #667eea;
  font-size: 1rem;
}

.reformulation-alert {
  color: #ff9800;
  font-weight: 500;
}
</style>