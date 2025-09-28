<template>
  <div class="milhena-widget-container">
    <!-- Floating Button -->
    <transition name="bounce">
      <button
        v-if="!isOpen"
        @click="toggleChat"
        class="floating-button"
        :class="{ 'has-notification': hasNewMessage }"
      >
        <Icon icon="mdi:robot-happy" class="button-icon" />
        <span v-if="hasNewMessage" class="notification-badge">{{ unreadCount }}</span>
      </button>
    </transition>

    <!-- Chat Window -->
    <transition name="slide-up">
      <div v-if="isOpen" class="chat-window">
        <!-- Header -->
        <div class="chat-header">
          <div class="header-left">
            <Icon icon="mdi:robot-happy" class="header-icon" />
            <div>
              <h3>Milhena AI</h3>
              <p class="status-text">
                <span v-if="isLearning" class="learning-status">
                  🧠 Learning...
                </span>
                <span v-else class="online-status">
                  ● Online - {{ accuracy }}% accuracy
                </span>
              </p>
            </div>
          </div>
          <button @click="toggleChat" class="close-btn">
            <Icon icon="mdi:close" />
          </button>
        </div>

        <!-- Messages Area -->
        <div class="messages-area" ref="messagesContainer">
          <!-- Welcome message -->
          <div v-if="messages.length === 0" class="welcome-message">
            <p>👋 Ciao! Sono Milhena v3.0</p>
            <p>Come posso aiutarti con i tuoi processi?</p>
            <div class="quick-actions">
              <button
                v-for="action in quickActions"
                :key="action.text"
                @click="sendQuickMessage(action.text)"
                class="quick-action-btn"
              >
                {{ action.label }}
              </button>
            </div>
          </div>

          <!-- Messages -->
          <div v-for="(msg, index) in messages" :key="index"
               :class="['message', msg.role]">
            <div class="message-bubble">
              <div class="message-text">{{ msg.content }}</div>

              <!-- Confidence indicator -->
              <div v-if="msg.confidence && msg.role === 'assistant'" class="confidence-indicator">
                <div class="confidence-bar">
                  <div class="confidence-fill"
                       :style="{width: (msg.confidence * 100) + '%'}"
                       :class="getConfidenceClass(msg.confidence)">
                  </div>
                </div>
                <span class="confidence-text">{{ Math.round(msg.confidence * 100) }}%</span>
              </div>

              <!-- Feedback buttons -->
              <div v-if="msg.role === 'assistant' && !msg.feedback" class="feedback-buttons">
                <button @click="sendFeedback(index, 'positive')"
                        class="feedback-btn" title="Utile">
                  <Icon icon="mdi:thumb-up-outline" />
                </button>
                <button @click="sendFeedback(index, 'negative')"
                        class="feedback-btn" title="Non utile">
                  <Icon icon="mdi:thumb-down-outline" />
                </button>
              </div>

              <!-- Feedback confirmation -->
              <div v-if="msg.feedback" class="feedback-status">
                <Icon :icon="msg.feedback === 'positive' ? 'mdi:check' : 'mdi:lightbulb'" />
                {{ msg.feedback === 'positive' ? 'Grazie!' : 'Sto imparando...' }}
              </div>
            </div>

            <!-- Reformulation suggestion -->
            <div v-if="msg.feedback === 'negative' && !msg.reformulated"
                 class="reformulation-hint">
              <p>Prova a riformulare per aiutarmi:</p>
              <div class="suggestions">
                <button v-for="sugg in getReformulationSuggestions()"
                        :key="sugg"
                        @click="sendMessage(sugg)"
                        class="suggestion-chip">
                  {{ sugg }}
                </button>
              </div>
            </div>
          </div>

          <!-- Typing indicator -->
          <div v-if="isTyping" class="message assistant">
            <div class="message-bubble">
              <div class="typing-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Learning Stats Bar -->
        <div v-if="showStats" class="learning-stats-bar">
          <div class="stat-item">
            <span class="stat-value">{{ todayStats.queries }}</span>
            <span class="stat-label">queries</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ todayStats.patterns }}</span>
            <span class="stat-label">learned</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">+{{ todayStats.improvement }}%</span>
            <span class="stat-label">better</span>
          </div>
        </div>

        <!-- Input Area -->
        <div class="input-area">
          <input
            v-model="inputMessage"
            @keyup.enter="sendMessage"
            :disabled="isLoading"
            placeholder="Chiedi qualsiasi cosa..."
            class="message-input"
          />
          <button @click="sendMessage" :disabled="!inputMessage.trim() || isLoading"
                  class="send-btn">
            <Icon v-if="isLoading" icon="mdi:loading" class="animate-spin" />
            <Icon v-else icon="mdi:send" />
          </button>
        </div>

        <!-- Reformulation indicator -->
        <div v-if="isReformulating" class="reformulation-indicator">
          🔄 Sto imparando dalla tua correzione...
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Icon } from '@iconify/vue'
import { useToast } from 'vue-toastification'
// Try importing as a named export and create a wrapper
import { apiClient } from '@/services/api-client'

const toast = useToast()

// Widget state
const isOpen = ref(false)
const hasNewMessage = ref(false)
const unreadCount = ref(0)

// Chat state
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const isTyping = ref(false)
const isLearning = ref(false)
const isReformulating = ref(false)
const showStats = ref(false)

// Learning metrics
const accuracy = ref(92)
const todayStats = ref({
  queries: 0,
  patterns: 0,
  improvement: 0
})

// Session management
const sessionId = ref(generateSessionId())

// Quick actions
const quickActions = [
  { label: '📊 Status sistema', text: 'Qual è lo stato del sistema?' },
  { label: '🔴 Ultimi errori', text: 'Ci sono errori critici?' },
  { label: '📈 Performance', text: 'Come sono le performance oggi?' }
]

// Generate session ID
function generateSessionId() {
  return 'widget_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

// Toggle chat
const toggleChat = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    hasNewMessage.value = false
    unreadCount.value = 0
    nextTick(() => scrollToBottom())
  }
}

// Get confidence class
const getConfidenceClass = (confidence) => {
  if (confidence > 0.8) return 'high'
  if (confidence > 0.6) return 'medium'
  return 'low'
}

// Get reformulation suggestions
const getReformulationSuggestions = () => {
  return [
    'Mostra più dettagli',
    'Spiega in modo diverso',
    'Dammi esempi specifici'
  ]
}

// Send quick message
const sendQuickMessage = (text) => {
  inputMessage.value = text
  sendMessage()
}

// Send message
const sendMessage = async (text) => {
  const messageText = text || inputMessage.value
  if (!messageText.trim() || isLoading.value) return

  // Add user message
  messages.value.push({
    role: 'user',
    content: messageText,
    timestamp: new Date()
  })

  inputMessage.value = ''
  isLoading.value = true
  isTyping.value = true
  scrollToBottom()

  try {
    // Call Milhena API
    const response = await apiClient.post('/api/milhena/query', {
      question: messageText,
      session_id: sessionId.value,
      context: {
        is_reformulation: isReformulating.value,
        widget: true
      }
    })

    // Add response
    messages.value.push({
      role: 'assistant',
      content: response.data.response || response.data.message,
      confidence: response.data.confidence,
      timestamp: new Date()
    })

    // Update stats
    if (response.data.system_accuracy) {
      accuracy.value = Math.round(response.data.system_accuracy * 100)
    }

    // Check if learned something
    if (response.data.learned) {
      showLearningAnimation()
    }

    isReformulating.value = false

  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: 'Mi dispiace, c\'è stato un problema. Riprova tra poco.',
      timestamp: new Date()
    })
  } finally {
    isLoading.value = false
    isTyping.value = false
    scrollToBottom()
    todayStats.value.queries++
  }
}

// Send feedback
const sendFeedback = async (messageIndex, type) => {
  const message = messages.value[messageIndex]
  if (!message || message.feedback) return

  message.feedback = type

  if (type === 'negative') {
    isReformulating.value = true
    setTimeout(() => {
      isReformulating.value = false
    }, 30000)
  }

  // Show learning animation
  isLearning.value = true
  setTimeout(() => {
    isLearning.value = false
  }, 3000)

  try {
    await apiClient.post('/api/milhena/feedback', {
      session_id: sessionId.value,
      message_id: messageIndex,
      feedback_type: type,
      query: messages.value[messageIndex - 1]?.content || '',
      response: message.content,
      confidence: message.confidence
    })

    if (type === 'negative') {
      toast.info('Grazie! Usa una formulazione diversa per aiutarmi a imparare')
    }
  } catch (error) {
    console.error('Feedback error:', error)
  }
}

// Show learning animation
const showLearningAnimation = () => {
  isLearning.value = true
  todayStats.value.patterns++
  setTimeout(() => {
    isLearning.value = false
  }, 2000)
}

// Scroll to bottom
const scrollToBottom = () => {
  nextTick(() => {
    const container = messagesContainer.value
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  })
}

const messagesContainer = ref(null)

// Load stats on mount
const loadStats = async () => {
  try {
    const response = await apiClient.get('/api/milhena/learning/stats/today')
    todayStats.value = response.data
    if (response.data.accuracy) {
      accuracy.value = Math.round(response.data.accuracy * 100)
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

// Keyboard shortcut
const handleKeyboard = (e) => {
  // Ctrl/Cmd + Shift + M to toggle
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'M') {
    toggleChat()
  }
}

onMounted(() => {
  loadStats()
  document.addEventListener('keydown', handleKeyboard)

  // Show welcome animation after 3 seconds
  setTimeout(() => {
    hasNewMessage.value = true
    unreadCount.value = 1
  }, 3000)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeyboard)
})
</script>

<style scoped>
.milhena-widget-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Floating Button */
.floating-button {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: all 0.3s ease;
}

.floating-button:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 30px rgba(102, 126, 234, 0.6);
}

.floating-button.has-notification {
  animation: pulse 2s infinite;
}

.button-icon {
  font-size: 28px;
}

.notification-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background: #ff4757;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  border: 2px solid white;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7);
  }
  70% {
    box-shadow: 0 0 0 15px rgba(102, 126, 234, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(102, 126, 234, 0);
  }
}

/* Chat Window */
.chat-window {
  position: fixed;
  bottom: 90px;
  right: 20px;
  width: 380px;
  height: 600px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Responsive */
@media (max-width: 420px) {
  .chat-window {
    width: calc(100vw - 40px);
    height: calc(100vh - 110px);
    right: 20px;
  }
}

/* Header */
.chat-header {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  font-size: 24px;
}

.chat-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.status-text {
  font-size: 12px;
  margin: 0;
  opacity: 0.9;
}

.online-status {
  display: flex;
  align-items: center;
  gap: 4px;
}

.learning-status {
  animation: pulse-text 1.5s infinite;
}

@keyframes pulse-text {
  0%, 100% { opacity: 0.9; }
  50% { opacity: 0.5; }
}

.close-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.8;
  transition: opacity 0.2s;
}

.close-btn:hover {
  opacity: 1;
}

/* Messages Area */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f8f9fa;
}

.welcome-message {
  text-align: center;
  padding: 20px;
  color: #666;
}

.welcome-message p {
  margin: 8px 0;
}

.quick-actions {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-action-btn {
  padding: 8px 12px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-action-btn:hover {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-color: transparent;
}

/* Messages */
.message {
  margin-bottom: 12px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 18px;
  word-wrap: break-word;
}

.message.user .message-bubble {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-bubble {
  background: white;
  color: #333;
  border: 1px solid #e0e0e0;
  border-bottom-left-radius: 4px;
}

.message-text {
  font-size: 14px;
  line-height: 1.4;
}

/* Confidence Indicator */
.confidence-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.confidence-bar {
  flex: 1;
  height: 3px;
  background: #e0e0e0;
  border-radius: 3px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  transition: width 0.3s;
}

.confidence-fill.high {
  background: #4caf50;
}

.confidence-fill.medium {
  background: #ff9800;
}

.confidence-fill.low {
  background: #f44336;
}

.confidence-text {
  font-size: 11px;
  color: #999;
}

/* Feedback */
.feedback-buttons {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.feedback-btn {
  padding: 4px 8px;
  background: #f0f0f0;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all 0.2s;
}

.feedback-btn:hover {
  background: #e0e0e0;
  transform: scale(1.1);
}

.feedback-status {
  font-size: 12px;
  color: #666;
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.reformulation-hint {
  margin-top: 8px;
  padding: 8px;
  background: #fff3e0;
  border-radius: 8px;
  font-size: 12px;
}

.suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

.suggestion-chip {
  padding: 4px 8px;
  background: white;
  border: 1px solid #ff9800;
  border-radius: 12px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.suggestion-chip:hover {
  background: #ff9800;
  color: white;
}

/* Typing indicator */
.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dots span {
  width: 8px;
  height: 8px;
  background: #999;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    opacity: 0.3;
  }
  30% {
    opacity: 1;
  }
}

/* Learning Stats Bar */
.learning-stats-bar {
  padding: 8px 16px;
  background: #f0f3f7;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-around;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.stat-value {
  font-weight: 600;
  color: #667eea;
}

.stat-label {
  color: #999;
}

/* Input Area */
.input-area {
  padding: 12px;
  background: white;
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 8px;
}

.message-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.message-input:focus {
  border-color: #667eea;
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.1);
}

.send-btn:disabled {
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

/* Reformulation Indicator */
.reformulation-indicator {
  padding: 8px;
  background: #fff3e0;
  color: #ff9800;
  font-size: 12px;
  text-align: center;
  border-top: 1px solid #ffe0b2;
}

/* Animations */
.bounce-enter-active {
  animation: bounce-in 0.5s;
}

.bounce-leave-active {
  animation: bounce-in 0.5s reverse;
}

@keyframes bounce-in {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(100%);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

/* Scrollbar */
.messages-area::-webkit-scrollbar {
  width: 6px;
}

.messages-area::-webkit-scrollbar-track {
  background: #f0f0f0;
}

.messages-area::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

.messages-area::-webkit-scrollbar-thumb:hover {
  background: #999;
}
</style>