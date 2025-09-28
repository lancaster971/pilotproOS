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
            <Icon icon="mdi:robot" class="header-icon" />
            <div>
              <h3>PilotPro Assistant</h3>
              <p class="status-text">
                <span class="online-status">
                  ● Online
                </span>
              </p>
            </div>
          </div>
          <div class="header-actions">
            <button @click="clearChat" class="action-btn" title="Clear chat">
              <Icon icon="mdi:delete-outline" />
            </button>
            <button @click="toggleChat" class="close-btn">
              <Icon icon="mdi:close" />
            </button>
          </div>
        </div>

        <!-- Messages Area -->
        <div class="messages-area" ref="messagesContainer">
          <!-- Welcome message -->
          <div v-if="messages.length === 0" class="welcome-message">
            <p>Benvenuto in PilotPro Assistant</p>
            <p>Come posso aiutarti oggi?</p>
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
              <div class="message-text" v-html="formatMessage(msg.content)"></div>


              <!-- Timestamp -->
              <div class="message-time">
                {{ formatTime(msg.timestamp) }}
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


        <!-- Input Area -->
        <div class="input-area">
          <input
            v-model="inputMessage"
            @keyup.enter="sendMessage()"
            :disabled="isLoading"
            placeholder="Scrivi un messaggio..."
            class="message-input"
          />
          <button @click="sendMessage()" :disabled="!inputMessage.trim() || isLoading"
                  class="send-btn">
            <Icon v-if="isLoading" icon="mdi:loading" class="animate-spin" />
            <Icon v-else icon="mdi:send" />
          </button>
        </div>

      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
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

// Clear chat function
const clearChat = () => {
  messages.value = []
  sessionId.value = generateSessionId()
}

// Session management
const sessionId = ref(generateSessionId())

// Quick actions
const quickActions = [
  { label: 'Status sistema', text: 'Qual è lo stato del sistema?' },
  { label: 'Ultimi errori', text: 'Ci sono errori critici?' },
  { label: 'Performance', text: 'Come sono le performance oggi?' }
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


// Format time
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
}

// Format message (handle markdown)
const formatMessage = (content) => {
  if (!content) return ''

  // Remove markdown formatting
  let formatted = content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
    .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
    .replace(/\n\n/g, '<br><br>') // Paragraphs
    .replace(/\n/g, '<br>') // Line breaks

  return formatted
}

// Send quick message
const sendQuickMessage = (text) => {
  inputMessage.value = text
  sendMessage()
}


const messagesContainer = ref(null)

// Scroll to bottom
const scrollToBottom = () => {
  nextTick(() => {
    const container = messagesContainer.value
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  })
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
    // Call Intelligence Engine directly
    const response = await fetch('http://localhost:8000/api/n8n/agent/customer-support', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: messageText,
        session_id: sessionId.value
      })
    })

    const data = await response.json()

    // Add response
    messages.value.push({
      role: 'assistant',
      content: data.response || data.message || 'Nessuna risposta ricevuta',
      timestamp: new Date()
    })

  } catch (error) {
    console.error('Errore chiamata Intelligence Engine:', error)
    messages.value.push({
      role: 'assistant',
      content: 'Errore di connessione all\'Intelligence Engine. Verifica che sia attivo su porta 8000.',
      error: true,
      timestamp: new Date()
    })
  } finally {
    isLoading.value = false
    isTyping.value = false
    scrollToBottom()
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
  document.addEventListener('keydown', handleKeyboard)
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
  width: 450px;
  height: 600px;
  background: #1e293b;
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
  overflow-x: hidden;
  padding: 20px;
  background: #0f172a;
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  background: #1e293b;
  border: 1px solid #475569;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  color: #cbd5e1;
}

.quick-action-btn:hover {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border-color: transparent;
}

/* Messages */
.message {
  display: flex;
  width: 100%;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 12px;
  word-wrap: break-word;
  word-break: break-word;
  white-space: pre-wrap;
  overflow-wrap: break-word;
  min-width: 100px;
}

.message.user .message-bubble {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-bubble {
  background: #334155;
  color: #f1f5f9;
  border: 1px solid #475569;
  border-bottom-left-radius: 4px;
  max-width: 90%;
}

.message-text {
  font-size: 14px;
  line-height: 1.6;
  word-wrap: break-word;
  word-break: break-word;
  white-space: pre-wrap;
  overflow-wrap: break-word;
  display: block;
  width: 100%;
}

.message-time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 4px;
  text-align: right;
}

.message.assistant .message-time {
  color: #94a3b8;
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
  background: #1e293b;
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
  background: #1e293b;
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
  background: #1e293b;
}

.messages-area::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 3px;
}

.messages-area::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}
</style>