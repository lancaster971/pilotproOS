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

    <!-- Advanced Chat Widget -->
    <div v-if="isChatOpen" class="chat-container">
      <vue-advanced-chat
        :current-user-id="currentUserId"
        :rooms="rooms"
        :messages="messages"
        :room-id="currentRoomId"
        :show-emoji="false"
        :show-files="false"
        :show-audio="false"
        :show-reaction-emojis="false"
        :text-messages="textMessages"
        :theme="'dark'"
        @send-message="onMessageWasSent"
        @typing-message="handleOnType"
      />
      <button @click="closeChat" class="close-button-overlay">
        <Icon icon="mdi:close" width="20" height="20" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Icon } from '@iconify/vue'

// Chat state
const isChatOpen = ref(false)
const sessionId = ref(generateSessionId())
const currentUserId = ref('user-1')
const currentRoomId = ref('room-1')

// Vue-advanced-chat data structure
const rooms = ref([
  {
    roomId: 'room-1',
    roomName: 'PilotPro Support',
    users: [
      {
        _id: 'user-1',
        username: 'You',
        avatar: ''
      },
      {
        _id: 'assistant-1',
        username: 'System Assistant',
        avatar: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"%3E%3Crect width="100" height="100" fill="%233b82f6"/%3E%3Ctext x="50" y="50" font-family="Arial, sans-serif" font-size="40" fill="white" text-anchor="middle" dominant-baseline="middle"%3ESA%3C/text%3E%3C/svg%3E'
      }
    ]
  }
])

const messages = ref([])

// Text messages configuration
const textMessages = ref({
  ROOMS_EMPTY: 'No conversations',
  ROOM_EMPTY: 'No messages yet',
  NEW_MESSAGES: 'New Messages',
  MESSAGE_DELETED: 'Message deleted',
  MESSAGE_EDITED: 'Message edited',
  MESSAGES_LOADED: 'Messages loaded',
  CONVERSATION_STARTED: 'Conversation started',
  TYPING: 'typing...',
  IS_TYPING: 'is typing...',
  CANCEL_SELECT_MESSAGE: 'Cancel',
  BUTTON_SEND: 'Send',
  MESSAGE_REPLY: 'Reply',
  MESSAGE_EDIT: 'Edit',
  MESSAGE_DELETE: 'Delete',
  SEND_MESSAGE_PLACEHOLDER: 'Type a message...'
})


// Computed
const unreadCount = computed(() => {
  // Count unread messages for current room
  return messages.value.filter(msg =>
    msg.roomId === currentRoomId.value &&
    msg.senderId !== currentUserId.value &&
    !msg.seen
  ).length
})

// Methods
function generateSessionId() {
  return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

function openChat() {
  isChatOpen.value = true
  // Mark messages as seen
  messages.value.forEach(msg => {
    if (msg.roomId === currentRoomId.value && msg.senderId !== currentUserId.value) {
      msg.seen = true
    }
  })
}

function closeChat() {
  isChatOpen.value = false
}

async function onMessageWasSent(message) {
  // Add user message
  const userMessage = {
    _id: Date.now().toString(),
    roomId: currentRoomId.value,
    content: message.content,
    senderId: currentUserId.value,
    username: 'You',
    timestamp: new Date().toISOString(),
    seen: true
  }

  messages.value.push(userMessage)

  try {
    // Call Intelligence Engine API
    const response = await fetch('http://localhost:8000/api/n8n/agent/customer-support', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message.content,
        session_id: sessionId.value
      })
    })

    const data = await response.json()

    // Add assistant response
    const assistantMessage = {
      _id: (Date.now() + 1).toString(),
      roomId: currentRoomId.value,
      content: data.response || data.message || 'No response received.',
      senderId: 'assistant-1',
      username: 'System Assistant',
      timestamp: new Date().toISOString(),
      seen: isChatOpen.value
    }

    messages.value.push(assistantMessage)

  } catch (error) {
    console.error('Error calling Intelligence Engine:', error)
    const errorMessage = {
      _id: (Date.now() + 2).toString(),
      roomId: currentRoomId.value,
      content: 'Connection error. Please verify the Intelligence Engine is active.',
      senderId: 'assistant-1',
      username: 'System Assistant',
      timestamp: new Date().toISOString(),
      seen: isChatOpen.value
    }

    messages.value.push(errorMessage)
  }
}

function handleOnType() {
  // Could implement typing indicator to backend
  console.log('User is typing...')
}

// Welcome message on mount
onMounted(() => {
  setTimeout(() => {
    const welcomeMessage = {
      _id: 'welcome',
      roomId: currentRoomId.value,
      content: 'Welcome to PilotPro. How can I assist you today?',
      senderId: 'assistant-1',
      username: 'System Assistant',
      timestamp: new Date().toISOString(),
      seen: false
    }

    messages.value.push(welcomeMessage)
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

/* Chat container */
.chat-container {
  position: relative;
  width: 480px;
  height: 650px;
  max-height: calc(100vh - 100px);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  background: #0f172a;
}

.close-button-overlay {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.5);
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  opacity: 0.8;
  transition: all 0.2s;
  z-index: 10;
}

.close-button-overlay:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.7);
}

/* Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* Advanced Chat styles override */
:deep(.vac-chat-container) {
  height: 100% !important;
  font-family: 'DM Sans', sans-serif !important;
}

:deep(.vac-room-header) {
  background: #0f172a !important;
  border-bottom: 1px solid #334155 !important;
  color: #f1f5f9 !important;
  padding: 14px 16px !important;
}

:deep(.vac-messages-container) {
  background: #0f172a !important;
  padding: 20px !important;
}

:deep(.vac-message-box) {
  margin-bottom: 12px !important;
}

:deep(.vac-message-box-me .vac-message-bubble) {
  background: #2563eb !important;
  color: white !important;
  border-radius: 12px 12px 4px 12px !important;
  padding: 12px 16px !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
}

:deep(.vac-message-box-other .vac-message-bubble) {
  background: #1e293b !important;
  color: #cbd5e1 !important;
  border: 1px solid #334155 !important;
  border-radius: 12px 12px 12px 4px !important;
  padding: 12px 16px !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
}

:deep(.vac-box-footer) {
  background: #1e293b !important;
  border-top: 1px solid #475569 !important;
}

:deep(.vac-textarea) {
  background: #0f172a !important;
  color: #f1f5f9 !important;
  border: 1px solid #334155 !important;
  border-radius: 8px !important;
  padding: 10px 15px !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 14px !important;
}

:deep(.vac-textarea::placeholder) {
  color: #94a3b8 !important;
}

:deep(.vac-icon-send) {
  background: #2563eb !important;
  border-radius: 8px !important;
  transition: background 0.2s !important;
}

:deep(.vac-icon-send:hover) {
  background: #3b82f6 !important;
}

/* Responsive */
@media (max-width: 520px) {
  .chat-container {
    width: calc(100vw - 40px) !important;
    height: calc(100vh - 100px) !important;
  }
}
</style>