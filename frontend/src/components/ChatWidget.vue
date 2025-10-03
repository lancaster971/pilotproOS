<template>
  <div>
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
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { Icon } from '@iconify/vue'
import axios from 'axios'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
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
    const response = await axios.post('http://localhost:8000/api/chat', {
      message: userMessage,
      session_id: sessionId.value
    })

    messages.value.push({
      role: 'assistant',
      content: response.data.response,
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
</script>

<style scoped>
/* Chat Button */
.chat-btn {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  transition: all 0.2s;
  z-index: 1000;
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
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  animation: slideUp 0.3s ease;
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
  background: #2563eb;
  color: #fff;
  border-radius: 12px 12px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.close-btn {
  background: transparent;
  border: none;
  color: #fff;
  cursor: pointer;
  font-size: 20px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
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
}

.welcome {
  text-align: center;
  padding: 40px 20px;
  color: #666;
  font-size: 14px;
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
  background: #2563eb;
  color: #fff;
  border-bottom-right-radius: 3px;
}

.msg.assistant .msg-content {
  background: #f3f4f6;
  color: #111;
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
  border-top: 1px solid #e5e7eb;
}

.input-bar input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 13px;
  outline: none;
}

.input-bar input:focus {
  border-color: #2563eb;
}

.input-bar button {
  padding: 10px 14px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.input-bar button:hover:not(:disabled) {
  background: #1d4ed8;
}

.input-bar button:disabled {
  background: #9ca3af;
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
