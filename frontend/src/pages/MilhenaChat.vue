<template>
  <MainLayout>
    <div class="chat-widget">
      <!-- Chat Messages -->
      <div class="messages" ref="messagesContainer">
        <div v-if="messages.length === 0" class="welcome">
          <h2>Milhena Assistant</h2>
          <p>Chiedi informazioni su workflow, errori, statistiche</p>
        </div>

        <div v-for="(msg, i) in messages" :key="i" :class="['msg', msg.role]">
          <div class="msg-content">
            <div class="msg-text" v-html="formatMessage(msg.content)"></div>
            <div class="msg-meta">
              <span class="time">{{ formatTime(msg.timestamp) }}</span>
              <span v-if="msg.latency" class="latency">{{ msg.latency }}ms</span>
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
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import MainLayout from '../layouts/MainLayout.vue'
import axios from 'axios'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  latency?: number
}

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
    const startTime = Date.now()
    const response = await axios.post('http://localhost:8000/api/chat', {
      message: userMessage,
      session_id: sessionId.value
    })

    const latency = Date.now() - startTime

    messages.value.push({
      role: 'assistant',
      content: response.data.response,
      timestamp: new Date(),
      latency
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

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.chat-widget {
  max-width: 900px;
  margin: 0 auto;
  height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.welcome h2 {
  font-size: 24px;
  font-weight: 600;
  color: #111;
  margin-bottom: 8px;
}

.welcome p {
  font-size: 14px;
}

.msg {
  display: flex;
  gap: 12px;
  animation: fadeIn 0.3s ease;
}

.msg.user {
  justify-content: flex-end;
}

.msg-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
}

.msg.user .msg-content {
  background: #2563eb;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.msg.assistant .msg-content {
  background: #f3f4f6;
  color: #111;
  border-bottom-left-radius: 4px;
}

.msg-text {
  margin-bottom: 4px;
}

.msg-text :deep(strong) {
  font-weight: 600;
}

.msg-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  opacity: 0.6;
  margin-top: 4px;
}

.msg.user .msg-meta {
  justify-content: flex-end;
}

.loading {
  padding: 16px;
}

.typing {
  display: flex;
  gap: 4px;
}

.typing span {
  width: 6px;
  height: 6px;
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
  padding: 16px;
  border-top: 1px solid #e5e7eb;
}

.input-bar input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.input-bar input:focus {
  border-color: #2563eb;
}

.input-bar button {
  padding: 12px 20px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
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
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Scrollbar */
.messages::-webkit-scrollbar {
  width: 6px;
}

.messages::-webkit-scrollbar-track {
  background: transparent;
}

.messages::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

.messages::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>
