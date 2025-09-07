<template>
  <div class="fixed bottom-4 right-4 z-50">
    <!-- Chat toggle button -->
    <button 
      v-if="!isExpanded"
      @click="isExpanded = true"
      class="w-12 h-12 bg-primary rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all"
    >
      <Bot class="w-6 h-6 text-white" />
    </button>

    <!-- Advanced chat component -->
    <vue-advanced-chat
      v-else
      height="400px"
      width="320px"
      :current-user-id="currentUserId"
      :rooms="chatRooms"
      :messages="chatMessages"
      :show-audio="false"
      :show-files="false"
      :show-emoji="false"
      :show-reaction-emojis="false"
      :show-new-messages-divider="false"
      :show-footer="false"
      :text-messages="textMessages"
      @send-message="handleSendMessage"
      @toggle-rooms-list="isExpanded = false"
      class="milhena-advanced-chat"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { Bot } from 'lucide-vue-next';
import VueAdvancedChat from 'vue-advanced-chat';
import { ofetch } from 'ofetch';
import { useToast } from 'vue-toastification';

// Composables
const toast = useToast();

// State
const isExpanded = ref(false);
const isLoading = ref(false);
const messages = ref([]);

// Advanced chat configuration
const currentUserId = ref('user-1');
const chatRooms = ref([{
  roomId: 'milhena-room',
  roomName: 'MILHENA',
  users: [
    { _id: 'user-1', username: 'Tu' },
    { _id: 'milhena', username: 'MILHENA' }
  ]
}]);

// Text customization for Italian
const textMessages = ref({
  ROOMS_EMPTY: 'Nessuna conversazione',
  ROOM_EMPTY: 'Inizia una conversazione con MILHENA',
  NEW_MESSAGES: 'Nuovi messaggi',
  MESSAGE_DELETED: 'Messaggio eliminato',
  MESSAGES_EMPTY: 'Nessun messaggio',
  CONVERSATION_STARTED: 'Conversazione iniziata',
  TYPE_MESSAGE: 'Scrivi a MILHENA...',
  SEARCH: 'Cerca',
  IS_ONLINE: 'è online',
  LAST_SEEN: 'Ultimo accesso',
  IS_TYPING: 'sta scrivendo...'
});

// Convert messages for vue-advanced-chat format
const chatMessages = computed(() => {
  return messages.value.map(msg => ({
    _id: msg.id,
    senderId: msg.type === 'user' ? 'user-1' : 'milhena',
    username: msg.type === 'user' ? 'Tu' : 'MILHENA',
    content: msg.content,
    timestamp: msg.timestamp,
    date: msg.timestamp,
    system: msg.type === 'system'
  }));
});

// API client
const milhenaApi = ofetch.create({
  baseURL: 'http://localhost:3002/api',
  timeout: 15000,
});

// Initialize welcome message
onMounted(() => {
  messages.value = [{
    id: '1',
    type: 'assistant',
    content: 'Ciao! Sono MILHENA, il tuo Manager Intelligente.\n\nChiedimi qualsiasi cosa sui tuoi processi aziendali.',
    timestamp: new Date()
  }];
});

// Handle message sending
async function handleSendMessage(message) {
  if (!message.content?.trim()) return;
  
  // Add user message
  const userMessage = {
    id: `user-${Date.now()}`,
    type: 'user',
    content: message.content,
    timestamp: new Date()
  };
  
  messages.value.push(userMessage);
  isLoading.value = true;

  try {
    // Call MILHENA API
    const response = await milhenaApi('/chat', {
      method: 'POST',
      body: {
        query: message.content,
        context: {
          userId: currentUserId.value,
          sessionId: 'chat-session'
        }
      }
    });

    // Add MILHENA response
    const assistantMessage = {
      id: `milhena-${Date.now()}`,
      type: 'assistant',
      content: response.response || 'Risposta ricevuta.',
      timestamp: new Date()
    };

    messages.value.push(assistantMessage);
    
  } catch (error) {
    console.error('MILHENA Error:', error);
    
    // Error message
    const errorMessage = {
      id: `error-${Date.now()}`,
      type: 'assistant',
      content: 'Mi dispiace, ho avuto un problema tecnico. Riprova tra qualche istante.',
      timestamp: new Date()
    };
    
    messages.value.push(errorMessage);
    toast.error('MILHENA temporaneamente non disponibile');
  }
  
  isLoading.value = false;
}
</script>

<style scoped>
/* Override vue-advanced-chat styles to match PilotProOS theme */
:deep(.vac-wrapper) {
  @apply border border-border rounded-lg shadow-xl;
  background: rgb(var(--color-background));
}

:deep(.vac-room-header) {
  @apply bg-surface border-b border-border/50;
}

:deep(.vac-room-name) {
  @apply text-text font-medium;
}

:deep(.vac-container-center) {
  @apply bg-background;
}

:deep(.vac-message-wrapper) {
  @apply text-text;
}

:deep(.vac-message-box) {
  @apply bg-surface;
}

:deep(.vac-message-current) {
  @apply bg-primary;
}

:deep(.vac-room-footer) {
  @apply bg-surface border-t border-border/50;
}

:deep(.vac-textarea) {
  @apply bg-surface text-text border-border;
}

:deep(.vac-icon-send) {
  @apply text-primary;
}
</style>