<template>
  <div class="ai-assistant">
    <div class="chat-header">
      <div class="header-content">
        <Icon icon="mdi:robot-happy-outline" class="assistant-icon" />
        <h3>PilotPro Assistant</h3>
        <Badge v-if="isConnected" variant="success">Online</Badge>
        <Badge v-else variant="secondary">Offline</Badge>
      </div>
      <button @click="toggleChat" class="btn-minimize">
        <Icon :icon="isMinimized ? 'mdi:chevron-up' : 'mdi:chevron-down'" />
      </button>
    </div>

    <div v-if="!isMinimized" class="chat-body">
      <div class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0" class="welcome-message">
          <Icon icon="mdi:hand-wave" class="wave-icon" />
          <p>Ciao! Sono il tuo assistente PilotPro.</p>
          <p class="text-muted">Come posso aiutarti oggi?</p>
        </div>

        <div v-for="(message, index) in messages" :key="index"
             :class="['message', message.type]">
          <div class="message-avatar">
            <Icon v-if="message.type === 'user'" icon="mdi:account" />
            <Icon v-else icon="mdi:robot" />
          </div>
          <div class="message-content">
            <div class="message-text">{{ message.text }}</div>
            <div v-if="message.confidence" class="message-meta">
              <small>Confidenza: {{ Math.round(message.confidence * 100) }}%</small>
            </div>
            <div v-if="message.suggestions && message.suggestions.length > 0"
                 class="suggestions">
              <p class="suggestions-title">Suggerimenti:</p>
              <button v-for="(suggestion, idx) in message.suggestions"
                      :key="idx"
                      @click="askQuestion(suggestion)"
                      class="btn-suggestion">
                {{ suggestion }}
              </button>
            </div>
          </div>
          <div class="message-time">
            {{ formatTime(message.timestamp) }}
          </div>
        </div>

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

      <div class="chat-input">
        <form @submit.prevent="sendMessage">
          <div class="input-group">
            <input
              v-model="inputMessage"
              type="text"
              placeholder="Scrivi la tua domanda..."
              :disabled="isTyping"
              class="form-control"
              @keyup.enter="sendMessage"
            />
            <button
              type="submit"
              :disabled="!inputMessage.trim() || isTyping"
              class="btn btn-primary">
              <Icon icon="mdi:send" />
            </button>
          </div>
        </form>

        <div class="quick-actions">
          <button @click="askQuestion('Quali sono le performance del sistema?')"
                  class="btn-quick">
            <Icon icon="mdi:speedometer" /> Performance
          </button>
          <button @click="askQuestion('Mostra i processi più utilizzati')"
                  class="btn-quick">
            <Icon icon="mdi:chart-line" /> Top Processi
          </button>
          <button @click="askQuestion('Suggerimenti per ottimizzare?')"
                  class="btn-quick">
            <Icon icon="mdi:lightbulb" /> Ottimizzazioni
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { Icon } from '@iconify/vue'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/composables/use-toast'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/services/api-client'

const authStore = useAuthStore()
const { toast } = useToast()

// State
const messages = ref([])
const inputMessage = ref('')
const isTyping = ref(false)
const isMinimized = ref(false)
const isConnected = ref(false)
const messagesContainer = ref(null)

// Check connection on mount
onMounted(async () => {
  await checkConnection()
})

// Check if Agent Engine is available
const checkConnection = async () => {
  try {
    const response = await apiClient.get('/api/agent-engine/health')
    isConnected.value = response.data.status === 'healthy'
  } catch (error) {
    isConnected.value = false
  }
}

// Toggle chat minimize/maximize
const toggleChat = () => {
  isMinimized.value = !isMinimized.value
}

// Format timestamp
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('it-IT', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Scroll to bottom of messages
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Send message to assistant
const sendMessage = async () => {
  const question = inputMessage.value.trim()
  if (!question || isTyping.value) return

  // Add user message
  messages.value.push({
    type: 'user',
    text: question,
    timestamp: new Date()
  })

  // Clear input
  inputMessage.value = ''
  isTyping.value = true

  await scrollToBottom()

  try {
    // Send to backend
    const response = await apiClient.post('/api/agent-engine/assistant', {
      question,
      context: {
        page: window.location.pathname,
        user: authStore.user?.email
      }
    })

    // Add assistant response
    messages.value.push({
      type: 'assistant',
      text: response.data.answer || 'Non ho capito la domanda.',
      confidence: response.data.confidence,
      suggestions: response.data.suggestions,
      timestamp: new Date()
    })

    if (!response.data.success && response.data.timeout) {
      toast({
        title: 'Elaborazione in corso',
        description: 'La risposta richiede più tempo del previsto. Riprova tra qualche secondo.',
        variant: 'warning'
      })
    }

  } catch (error) {
    console.error('Assistant error:', error)

    // Add error message
    messages.value.push({
      type: 'assistant',
      text: 'Mi dispiace, ho avuto un problema nel rispondere. Riprova più tardi.',
      timestamp: new Date()
    })

    toast({
      title: 'Errore',
      description: 'Impossibile contattare l\'assistente',
      variant: 'destructive'
    })
  } finally {
    isTyping.value = false
    await scrollToBottom()
  }
}

// Ask a predefined question
const askQuestion = (question) => {
  inputMessage.value = question
  sendMessage()
}
</script>

<style scoped>
.ai-assistant {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 400px;
  max-width: calc(100vw - 40px);
  background: var(--card);
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: var(--primary);
  color: white;
  border-radius: 12px 12px 0 0;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.assistant-icon {
  font-size: 24px;
}

.chat-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.btn-minimize {
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-minimize:hover {
  opacity: 0.8;
}

.chat-body {
  display: flex;
  flex-direction: column;
  height: 500px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-message {
  text-align: center;
  padding: 32px;
  color: var(--muted-foreground);
}

.wave-icon {
  font-size: 48px;
  margin-bottom: 16px;
  animation: wave 0.6s ease-in-out;
}

@keyframes wave {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-10deg); }
  75% { transform: rotate(10deg); }
}

.message {
  display: flex;
  gap: 12px;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 18px;
}

.message.user .message-avatar {
  background: var(--primary);
  color: white;
}

.message.assistant .message-avatar {
  background: var(--secondary);
  color: var(--secondary-foreground);
}

.message-content {
  max-width: 75%;
  padding: 12px;
  border-radius: 12px;
  background: var(--muted);
}

.message.user .message-content {
  background: var(--primary);
  color: white;
}

.message-text {
  line-height: 1.5;
  word-wrap: break-word;
}

.message-meta {
  margin-top: 4px;
  opacity: 0.7;
}

.message-time {
  font-size: 11px;
  color: var(--muted-foreground);
  align-self: flex-end;
  margin: 0 4px;
}

.suggestions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.suggestions-title {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
  opacity: 0.8;
}

.btn-suggestion {
  display: block;
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  margin-bottom: 4px;
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
}

.btn-suggestion:hover {
  background: var(--accent);
  transform: translateX(4px);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--muted-foreground);
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
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

.chat-input {
  padding: 16px;
  border-top: 1px solid var(--border);
  background: var(--background);
  border-radius: 0 0 12px 12px;
}

.input-group {
  display: flex;
  gap: 8px;
}

.form-control {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--card);
  color: var(--foreground);
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-control:focus {
  outline: none;
  border-color: var(--primary);
}

.form-control:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn {
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  font-weight: 500;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: scale(1.05);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.quick-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.btn-quick {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--card);
  color: var(--foreground);
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-quick:hover {
  background: var(--accent);
  border-color: var(--primary);
  transform: translateY(-2px);
}

/* Dark mode adjustments */
.dark .ai-assistant {
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
}

.dark .message-content {
  background: var(--muted);
}

.dark .message.user .message-content {
  background: var(--primary);
}

/* Mobile responsiveness */
@media (max-width: 600px) {
  .ai-assistant {
    width: calc(100vw - 40px);
    bottom: 10px;
    right: 10px;
    left: 10px;
  }

  .chat-body {
    height: 400px;
  }

  .quick-actions {
    flex-direction: column;
  }

  .btn-quick {
    width: 100%;
    justify-content: center;
  }
}
</style>