<template>
  <Teleport to="body">
    <!-- Chat Button -->
    <button v-if="!isOpen" @click="isOpen = true" class="chat-btn">
      <Icon icon="mdi:message-text" />
    </button>

    <!-- Chat Window -->
    <div v-if="isOpen" class="chat-window">
      <!-- Header -->
      <div class="chat-header">
        <span>Milhena Assistant</span>
        <button @click="isOpen = false" class="close-btn">
          <Icon icon="mdi:close" />
        </button>
      </div>

      <!-- Messages -->
      <div class="messages" ref="messagesContainer">
        <div v-if="messages.length === 0" class="welcome">
          <p>Ciao! Chiedi informazioni su workflow, errori, statistiche.</p>
        </div>

        <div v-for="(msg, i) in messages" :key="i" :class="['msg', msg.role]">
          <div class="msg-content">
            <div class="msg-text" v-html="formatMessage(msg.content)"></div>
            <div class="msg-meta">
              <span class="time">{{ formatTime(msg.timestamp) }}</span>
            </div>
            <!-- Feedback buttons (only for assistant messages) -->
            <div v-if="msg.role === 'assistant'" class="feedback-buttons">
              <button
                @click="sendFeedback(i, 'positive')"
                :class="['feedback-btn', { active: msg.feedback === 'positive' }]"
                :disabled="msg.feedback !== null && msg.feedback !== undefined"
                title="Risposta utile"
              >
                <Icon icon="mdi:thumb-up-outline" />
              </button>
              <button
                @click="sendFeedback(i, 'negative')"
                :class="['feedback-btn', { active: msg.feedback === 'negative' }]"
                :disabled="msg.feedback !== null && msg.feedback !== undefined"
                title="Risposta non utile"
              >
                <Icon icon="mdi:thumb-down-outline" />
              </button>
            </div>
          </div>
        </div>

        <div v-if="isLoading" class="msg assistant">
          <div class="msg-content loading">
            <div class="typing">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="input-bar">
        <input
          v-model="input"
          @keydown.enter="send"
          placeholder="Chiedi qualcosa..."
          :disabled="isLoading"
        />
        <button @click="send" :disabled="!input.trim() || isLoading">
          <Icon icon="mdi:send" />
        </button>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { Icon } from '@iconify/vue'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  feedback?: 'positive' | 'negative' | null
}

const isOpen = ref(false)
const messages = ref<Message[]>([])
const input = ref('')
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement>()
const sessionId = ref(`session_${Date.now()}_${Math.random().toString(36).substring(7)}`)

const send = async () => {
  if (!input.value.trim() || isLoading.value) return

  const userMessage = input.value.trim()
  input.value = ''

  messages.value.push({
    role: 'user',
    content: userMessage,
    timestamp: new Date()
  })

  scrollToBottom()
  isLoading.value = true

  try {
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: userMessage,
        session_id: sessionId.value
      })
    })

    const data = await response.json()

    messages.value.push({
      role: 'assistant',
      content: data.response,
      timestamp: new Date()
    })

    scrollToBottom()
  } catch (error) {
    console.error('Error:', error)
    messages.value.push({
      role: 'assistant',
      content: 'Errore di connessione. Riprova.',
      timestamp: new Date()
    })
  } finally {
    isLoading.value = false
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const formatMessage = (text: string) => {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

const formatTime = (date: Date) => {
  return date.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
}

const sendFeedback = async (messageIndex: number, feedback: 'positive' | 'negative') => {
  const message = messages.value[messageIndex]
  if (!message || message.feedback !== null && message.feedback !== undefined) return

  // Find the corresponding user message (the one before the assistant message)
  const userMessage = messageIndex > 0 ? messages.value[messageIndex - 1] : null
  if (!userMessage || userMessage.role !== 'user') {
    console.error('Cannot find corresponding user message for feedback')
    return
  }

  try {
    const response = await fetch('http://localhost:3001/api/milhena/feedback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionId.value,
        query: userMessage.content,
        response: message.content,
        feedback_type: feedback,
        intent: 'GENERAL'
      })
    })

    if (response.ok) {
      // Update message feedback state
      message.feedback = feedback
      console.log(`Feedback ${feedback} sent successfully`)
    } else {
      console.error('Failed to send feedback:', await response.text())
    }
  } catch (error) {
    console.error('Error sending feedback:', error)
  }
}
</script>

<style scoped>
/* Chat Button */
.chat-btn {
  position: fixed !important;
  bottom: 24px !important;
  right: 24px !important;
  width: 56px !important;
  height: 56px !important;
  background: #2563eb !important;
  color: #fff !important;
  border: none !important;
  border-radius: 50% !important;
  cursor: pointer !important;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  font-size: 24px !important;
  transition: all 0.2s !important;
  z-index: 999999 !important;
}

.chat-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.5);
}

/* Chat Window */
.chat-window {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 380px;
  height: 600px;
  background: #1a1a1a !important;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.9);
  display: flex;
  flex-direction: column;
  z-index: 99999 !important;
  animation: slideUp 0.3s ease;
  overflow: hidden;
  border: 1px solid #2a2a2a !important;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-header {
  padding: 16px 20px;
  background: #0a0a0a !important;
  color: #ffffff !important;
  border-bottom: 1px solid #2a2a2a;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

.close-btn {
  background: transparent;
  border: none;
  color: #ffffff !important;
  cursor: pointer;
  font-size: 20px;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s;
}

.close-btn:hover {
  opacity: 0.8;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #1a1a1a !important;
}

.welcome {
  text-align: center;
  padding: 40px 20px;
  color: #888 !important;
  font-size: 14px;
  line-height: 1.6;
}

.welcome p {
  color: #888 !important;
  margin: 0;
}

.msg {
  display: flex;
  animation: fadeIn 0.2s ease;
}

.msg.user {
  justify-content: flex-end;
}

.msg-content {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.5;
}

.msg.user .msg-content {
  background: #2563eb !important;
  color: #ffffff !important;
  border-bottom-right-radius: 3px;
}

.msg.assistant .msg-content {
  background: #2a2a2a !important;
  color: #e5e5e5 !important;
  border-bottom-left-radius: 3px;
}

.msg-text {
  margin-bottom: 4px;
}

.msg-text :deep(strong) {
  font-weight: 600;
}

.msg-meta {
  font-size: 10px;
  opacity: 0.6;
  margin-top: 2px;
}

.msg.user .msg-meta {
  text-align: right;
}

.feedback-buttons {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.feedback-btn {
  background: transparent;
  border: 1px solid #3a3a3a;
  color: #888;
  padding: 4px 8px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.feedback-btn:hover:not(:disabled) {
  border-color: #2563eb;
  color: #2563eb;
  background: rgba(37, 99, 235, 0.1);
}

.feedback-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.feedback-btn.active {
  border-color: #2563eb;
  color: #2563eb;
  background: rgba(37, 99, 235, 0.15);
}

.loading {
  padding: 12px;
}

.typing {
  display: flex;
  gap: 3px;
}

.typing span {
  width: 5px;
  height: 5px;
  background: #999;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; }
  30% { opacity: 1; }
}

.input-bar {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid #2a2a2a;
  background: #0a0a0a !important;
}

.input-bar input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  font-size: 13px;
  outline: none;
  background: #1a1a1a !important;
  color: #e5e5e5 !important;
}

.input-bar input::placeholder {
  color: #666 !important;
}

.input-bar input:focus {
  border-color: #2563eb;
}

.input-bar button {
  padding: 10px 14px;
  background: #2563eb !important;
  color: #ffffff !important;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.input-bar button:hover:not(:disabled) {
  background: #1d4ed8 !important;
}

.input-bar button:disabled {
  background: #9ca3af !important;
  cursor: not-allowed;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.messages::-webkit-scrollbar {
  width: 5px;
}

.messages::-webkit-scrollbar-track {
  background: transparent;
}

.messages::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

@media (max-width: 480px) {
  .chat-window {
    width: calc(100vw - 24px);
    height: calc(100vh - 48px);
    right: 12px;
    bottom: 12px;
  }
}
</style>
