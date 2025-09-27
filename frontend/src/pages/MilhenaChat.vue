<template>
  <div class="milhena-chat-container">
    <!-- Header -->
    <div class="chat-header">
      <div class="header-content">
        <div class="header-left">
          <Icon icon="mdi:robot-happy" class="header-icon" />
          <div>
            <h1>Milhena Assistant</h1>
            <p class="subtitle">v4.0 - Powered by Groq (60ms response)</p>
          </div>
        </div>
        <div class="header-stats">
          <div class="stat">
            <span class="stat-value">{{ responseTime }}ms</span>
            <span class="stat-label">Latency</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ messages.length }}</span>
            <span class="stat-label">Messages</span>
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
          <div v-if="message.confidence" class="message-confidence">
            <div class="confidence-bar">
              <div class="confidence-fill" :style="{width: (message.confidence * 100) + '%'}"></div>
            </div>
            <span class="confidence-text">Confidence: {{ (message.confidence * 100).toFixed(0) }}%</span>
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
        <span>Milhena usa Groq con zero allucinazioni. Non inventa mai dati.</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Icon } from '@iconify/vue'
import { useToast } from 'vue-toastification'
import apiClient from '@/services/api-client'

const toast = useToast()

// State
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const isTyping = ref(false)
const responseTime = ref(0)
const messagesContainer = ref(null)

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

// Send message
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userMessage = {
    role: 'user',
    content: inputMessage.value,
    timestamp: new Date()
  }

  messages.value.push(userMessage)
  const question = inputMessage.value
  inputMessage.value = ''

  isLoading.value = true
  isTyping.value = true
  scrollToBottom()

  const startTime = Date.now()

  try {
    // Call Milhena API
    const response = await apiClient.post('/api/milhena/query', {
      question: question,
      context: {
        conversation_history: messages.value.slice(-10) // Last 10 messages
      },
      user_id: 'frontend_user'
    })

    const latency = Date.now() - startTime
    responseTime.value = latency

    // Add assistant response
    messages.value.push({
      role: 'assistant',
      content: response.data.response || response.data.message,
      timestamp: new Date(),
      confidence: response.data.confidence,
      latency: latency
    })

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
  }
}

// Welcome message on mount
onMounted(() => {
  // Optional: Add initial greeting
  setTimeout(() => {
    messages.value.push({
      role: 'assistant',
      content: 'Ciao! Sono Milhena v4.0, il tuo assistente AI per PilotProOS. Come posso aiutarti oggi?',
      timestamp: new Date(),
      confidence: 1.0
    })
  }, 500)
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
</style>