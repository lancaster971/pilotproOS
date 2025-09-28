<template>
  <div class="pilotpro-chat-widget">
    <!-- Floating Button -->
    <transition name="fade">
      <button
        v-if="!isChatOpen"
        @click="openChat"
        class="chat-launcher"
      >
        <Icon icon="mdi:message-text" width="24" height="24" />
        <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
      </button>
    </transition>

    <!-- Beautiful Chat Widget -->
    <beautiful-chat
      :participants="participants"
      :on-message-was-sent="onMessageWasSent"
      :message-list="messageList"
      :new-messages-count="newMessagesCount"
      :is-open="isChatOpen"
      :close="closeChat"
      :open="openChat"
      :show-emoji="false"
      :show-file="false"
      :show-edition="false"
      :show-deletion="false"
      :show-typing-indicator="showTypingIndicator"
      :show-launcher="false"
      :show-close-button="true"
      :colors="colors"
      :always-scroll-to-bottom="true"
      :disable-user-list-toggle="true"
      :message-styling="true"
      placeholder="Type a message..."
      @onType="handleOnType"
      @edit="editMessage"
    >
      <template v-slot:header>
        <div class="custom-header">
          <div class="header-info">
            <div>
              <h4>System Assistant</h4>
              <p class="status">
                <span class="status-dot"></span>
                Active
              </p>
            </div>
          </div>
          <button @click="closeChat" class="close-button">
            <Icon icon="mdi:close" width="20" height="20" />
          </button>
        </div>
      </template>
    </beautiful-chat>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Icon } from '@iconify/vue'
import Chat from 'vue3-beautiful-chat'

// Chat state
const isChatOpen = ref(false)
const messageList = ref([])
const newMessagesCount = ref(0)
const showTypingIndicator = ref(false)
const sessionId = ref(generateSessionId())

// Participants
const participants = ref([
  {
    id: 'assistant',
    name: 'System Assistant',
    imageUrl: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"%3E%3Crect width="100" height="100" fill="%233b82f6"/%3E%3Ctext x="50" y="50" font-family="Arial, sans-serif" font-size="40" fill="white" text-anchor="middle" dominant-baseline="middle"%3ESA%3C/text%3E%3C/svg%3E'
  }
])

// Enterprise theme colors - consistent with app
const colors = {
  header: {
    bg: '#0f172a',
    text: '#f1f5f9'
  },
  launcher: {
    bg: '#3b82f6'
  },
  messageList: {
    bg: '#0f172a'
  },
  sentMessage: {
    bg: '#2563eb',
    text: '#ffffff'
  },
  receivedMessage: {
    bg: '#1e293b',
    text: '#cbd5e1'
  },
  userInput: {
    bg: '#1e293b',
    text: '#f1f5f9'
  }
}


// Computed
const unreadCount = computed(() => newMessagesCount.value)

// Methods
function generateSessionId() {
  return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

function openChat() {
  isChatOpen.value = true
  newMessagesCount.value = 0
}

function closeChat() {
  isChatOpen.value = false
}

async function onMessageWasSent(message) {
  // Add user message to list
  messageList.value.push({
    ...message,
    author: 'me',
    type: 'text',
    id: Math.random().toString(36)
  })

  // Show typing indicator
  showTypingIndicator.value = true

  try {
    // Call Intelligence Engine API
    const response = await fetch('http://localhost:8000/api/n8n/agent/customer-support', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message.data.text || message.data,
        session_id: sessionId.value
      })
    })

    const data = await response.json()

    // Add assistant response
    messageList.value.push({
      type: 'text',
      author: 'assistant',
      id: Math.random().toString(36),
      data: {
        text: data.response || data.message || 'No response received.'
      }
    })

    // Increment unread count if chat is closed
    if (!isChatOpen.value) {
      newMessagesCount.value++
    }

  } catch (error) {
    console.error('Error calling Intelligence Engine:', error)
    messageList.value.push({
      type: 'text',
      author: 'assistant',
      id: Math.random().toString(36),
      data: {
        text: 'Connection error. Please verify the Intelligence Engine is active.'
      }
    })
  } finally {
    showTypingIndicator.value = false
  }
}

function handleOnType() {
  // Could implement typing indicator to backend
  console.log('User is typing...')
}

function editMessage(message) {
  const idx = messageList.value.findIndex(m => m.id === message.id)
  if (idx > -1) {
    messageList.value[idx] = message
  }
}

// Welcome message on mount
onMounted(() => {
  setTimeout(() => {
    messageList.value.push({
      type: 'text',
      author: 'assistant',
      id: 'welcome',
      data: {
        text: 'Welcome to PilotPro. How can I assist you today?'
      }
    })

    if (!isChatOpen.value) {
      newMessagesCount.value = 1
    }
  }, 2000)
})
</script>

<style scoped>
.pilotpro-chat-widget {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
  font-family: 'DM Sans', sans-serif;
}

/* Floating launcher button */
.chat-launcher {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: #2563eb;
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: all 0.2s ease;
}

.chat-launcher:hover {
  background: #3b82f6;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

.chat-launcher .badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #dc2626;
  color: white;
  border-radius: 10px;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
}

/* Custom header */
.custom-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: #0f172a;
  border-bottom: 1px solid #334155;
  color: #f1f5f9;
}

.header-info {
  display: flex;
  align-items: center;
}

.custom-header h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 500;
  color: #f1f5f9;
}

.status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 2px 0 0 0;
  font-size: 11px;
  color: #94a3b8;
}

.status-dot {
  width: 6px;
  height: 6px;
  background: #06b6d4;
  border-radius: 50%;
}


.close-button {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.8;
  transition: all 0.2s;
}


.close-button:hover {
  opacity: 1;
}

/* Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* Override some default styles */
:deep(.sc-launcher) {
  display: none !important;
}

:deep(.sc-chat-window) {
  width: 480px !important;
  height: 650px !important;
  max-height: calc(100vh - 100px);
  border-radius: 12px !important;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3) !important;
  font-family: 'DM Sans', sans-serif !important;
}

:deep(.sc-header) {
  padding: 0 !important;
  border-radius: 12px 12px 0 0 !important;
  font-family: 'DM Sans', sans-serif !important;
}

:deep(.sc-message-list) {
  background: #0f172a !important;
  padding: 20px !important;
  overflow-y: auto !important;
}

:deep(.sc-message) {
  margin-bottom: 12px !important;
}

:deep(.sc-message--text) {
  word-wrap: break-word !important;
  word-break: break-word !important;
  white-space: pre-wrap !important;
  overflow-wrap: break-word !important;
  max-width: 100% !important;
  display: block !important;
}

:deep(.sc-message--content.sent) {
  background: #2563eb !important;
  color: white !important;
  border-radius: 12px 12px 4px 12px !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
  padding: 12px 16px !important;
  max-width: 85% !important;
  word-wrap: break-word !important;
  word-break: break-word !important;
  white-space: pre-wrap !important;
}

:deep(.sc-message--content.received) {
  background: #1e293b !important;
  color: #cbd5e1 !important;
  border: 1px solid #334155 !important;
  border-radius: 12px 12px 12px 4px !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
  padding: 12px 16px !important;
  max-width: 90% !important;
  word-wrap: break-word !important;
  word-break: break-word !important;
  white-space: pre-wrap !important;
}

:deep(.sc-user-input) {
  background: #1e293b !important;
  border-top: 1px solid #475569 !important;
}

:deep(.sc-user-input--text) {
  background: #0f172a !important;
  color: #f1f5f9 !important;
  border: 1px solid #334155 !important;
  border-radius: 8px !important;
  padding: 10px 15px !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 14px !important;
}

:deep(.sc-user-input--text::placeholder) {
  color: #94a3b8 !important;
}

:deep(.sc-user-input--button) {
  background: #2563eb !important;
  width: 36px !important;
  height: 36px !important;
  border-radius: 8px !important;
  transition: background 0.2s !important;
}

:deep(.sc-user-input--button:hover) {
  background: #3b82f6 !important;
}

:deep(.sc-user-input--button:hover) {
  transform: scale(1.1);
}

/* Responsive */
@media (max-width: 520px) {
  :deep(.sc-chat-window) {
    width: calc(100vw - 40px) !important;
    height: calc(100vh - 100px) !important;
  }
}

/* Force full text display - no truncation */
:deep(.sc-message--text-wrapper) {
  overflow: visible !important;
  text-overflow: unset !important;
  max-height: none !important;
  height: auto !important;
}

:deep(.sc-message--text-content) {
  overflow: visible !important;
  text-overflow: unset !important;
  display: block !important;
  height: auto !important;
  max-height: none !important;
  -webkit-line-clamp: unset !important;
  line-clamp: unset !important;
}

:deep(.sc-message p) {
  overflow: visible !important;
  text-overflow: unset !important;
  white-space: pre-wrap !important;
  word-break: break-word !important;
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
}

:deep(.sc-message--content-wrapper) {
  overflow: visible !important;
  max-height: none !important;
  height: auto !important;
}
</style>