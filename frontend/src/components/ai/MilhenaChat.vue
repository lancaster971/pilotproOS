<template>
  <div class="milhena-chat-widget">
    <!-- Chat minimized button -->
    <div 
      v-if="!isExpanded" 
      @click="toggleChat"
      class="milhena-chat-bubble group cursor-pointer"
    >
      <div class="flex items-center space-x-2">
        <div class="milhena-avatar">
          <Icon icon="lucide:bot" class="w-5 h-5 text-green-500" />
        </div>
        <div class="milhena-info">
          <span class="milhena-name">MILHENA</span>
          <div class="milhena-status">
            <div class="online-indicator"></div>
            <span>Manager Intelligente</span>
          </div>
        </div>
      </div>
      <Icon icon="lucide:message-circle" class="w-5 h-5 text-gray-400 group-hover:text-green-500 transition-colors" />
    </div>

    <!-- Chat expanded interface -->
    <div v-else class="milhena-chat-expanded">
      <!-- Header -->
      <div class="milhena-header">
        <div class="flex items-center space-x-3">
          <div class="milhena-avatar-large">
            <Icon icon="lucide:bot" class="w-6 h-6 text-green-500" />
          </div>
          <div>
            <h4 class="milhena-title">MILHENA</h4>
            <p class="milhena-subtitle">Manager Intelligente per i tuoi processi aziendali</p>
          </div>
        </div>
        
        <div class="milhena-controls">
          <div class="online-indicator-large"></div>
          <button @click="toggleChat" class="milhena-close">
            <Icon icon="lucide:x" class="w-5 h-5" />
          </button>
        </div>
      </div>

      <!-- Messages area -->
      <div class="milhena-messages" ref="messagesContainer">
        <div 
          v-for="message in messages" 
          :key="message.id" 
          :class="`milhena-message ${message.type}`"
        >
          <!-- Message header -->
          <div class="message-meta">
            <Icon 
              :icon="message.type === 'user' ? 'lucide:user' : 'lucide:bot'" 
              :class="message.type === 'user' ? 'text-blue-500' : 'text-green-500'"
              class="w-4 h-4" 
            />
            <span class="message-time">
              {{ formatTime(message.timestamp) }}
            </span>
          </div>

          <!-- Message content -->
          <div class="message-content">
            <p v-for="(line, index) in message.content.split('\n')" :key="index">
              {{ line }}
            </p>
          </div>

          <!-- Quick actions for AI responses -->
          <div v-if="message.type === 'assistant' && message.quickActions" class="quick-actions">
            <button
              v-for="action in message.quickActions"
              :key="action.label"
              @click="sendMessage(action.query)"
              class="quick-action-btn"
            >
              {{ action.label }}
            </button>
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="isLoading" class="milhena-loading">
          <div class="flex items-center space-x-2">
            <div class="milhena-avatar">
              <Icon icon="lucide:bot" class="w-4 h-4 text-green-500" />
            </div>
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span class="text-sm text-gray-500">MILHENA sta pensando...</span>
          </div>
        </div>
      </div>

      <!-- Input area -->
      <div class="milhena-input">
        <div class="input-container">
          <textarea
            v-model="inputMessage"
            @keydown.enter.prevent="handleEnterKey"
            placeholder="Chiedi a MILHENA sui tuoi processi aziendali..."
            :disabled="isLoading"
            class="milhena-textarea"
            rows="1"
          />
          <button 
            @click="sendMessage(inputMessage)"
            :disabled="!inputMessage.trim() || isLoading"
            class="milhena-send-btn"
          >
            <Icon icon="lucide:send" class="w-4 h-4" />
          </button>
        </div>
        
        <div class="milhena-examples">
          <button 
            v-for="example in quickExamples"
            :key="example"
            @click="sendMessage(example)"
            class="example-btn"
          >
            {{ example }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue';
import { Icon } from '@iconify/vue';
import { ofetch } from 'ofetch';
import { useToast } from 'vue-toastification';

// Composables
const toast = useToast();

// Reactive state
const isExpanded = ref(false);
const isLoading = ref(false);
const inputMessage = ref('');
const messages = ref([]);
const messagesContainer = ref(null);

// Quick examples for user guidance
const quickExamples = ref([
  'Mostra i processi attivi',
  'Come va il sistema?', 
  'Report di oggi'
]);

// Initialize with welcome message
onMounted(() => {
  messages.value = [{
    id: '1',
    type: 'assistant',
    content: '👋 Ciao! Sono MILHENA, il tuo Manager Intelligente per l\'automazione business.\n\nPuoi chiedermi qualsiasi cosa sui tuoi processi automatizzati. Sono qui per aiutarti!',
    timestamp: new Date(),
    quickActions: [
      { label: '📊 Stato Processi', query: 'Mostra lo stato dei miei processi' },
      { label: '📈 Analytics', query: 'Report delle performance' },
      { label: '⚠️ Problemi', query: 'Ci sono errori da controllare?' }
    ]
  }];
});

// API client using OFETCH (following project standards)
const milhenaApi = ofetch.create({
  baseURL: 'http://localhost:3002/api',
  timeout: 15000,
});

// Chat functions
async function toggleChat() {
  isExpanded.value = !isExpanded.value;
  if (isExpanded.value) {
    await nextTick();
    scrollToBottom();
  }
}

async function sendMessage(query) {
  if (!query?.trim()) return;
  
  // Add user message
  const userMessage = {
    id: `user-${Date.now()}`,
    type: 'user', 
    content: query,
    timestamp: new Date()
  };
  
  messages.value.push(userMessage);
  inputMessage.value = '';
  isLoading.value = true;
  
  await nextTick();
  scrollToBottom();

  try {
    // Call MILHENA API
    const response = await milhenaApi('/chat', {
      method: 'POST',
      body: {
        query,
        context: {
          userId: 'current-user',
          sessionId: 'chat-session',
          timestamp: new Date().toISOString()
        }
      }
    });

    // Add MILHENA response
    const assistantMessage = {
      id: `milhena-${Date.now()}`,
      type: 'assistant',
      content: response.response,
      timestamp: new Date(),
      intent: response.intent,
      quickActions: getQuickActionsForIntent(response.intent)
    };

    messages.value.push(assistantMessage);
    
  } catch (error) {
    console.error('MILHENA Error:', error);
    
    // Error handling with business-friendly message
    const errorMessage = {
      id: `error-${Date.now()}`,
      type: 'system',
      content: '🚨 Mi dispiace, ho avuto un problema tecnico. Il sistema di automazione business continua a funzionare normalmente. Riprova tra qualche istante.',
      timestamp: new Date()
    };
    
    messages.value.push(errorMessage);
    toast.error('MILHENA temporaneamente non disponibile');
  }
  
  isLoading.value = false;
  await nextTick();
  scrollToBottom();
}

function handleEnterKey(event) {
  if (!event.shiftKey) {
    sendMessage(inputMessage.value);
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

function formatTime(timestamp) {
  return new Date(timestamp).toLocaleTimeString('it-IT', {
    hour: '2-digit',
    minute: '2-digit'
  });
}

function getQuickActionsForIntent(intent) {
  const actions = {
    'process_status': [
      { label: '📊 Analytics', query: 'Mostra le metriche dettagliate' },
      { label: '⚠️ Problemi', query: 'Ci sono errori da controllare?' }
    ],
    'analytics': [
      { label: '📈 Trend', query: 'Mostra i trend settimanali' },
      { label: '🎯 KPI', query: 'Quali sono i KPI principali?' }
    ],
    'troubleshooting': [
      { label: '🔧 Soluzioni', query: 'Come posso risolvere questi problemi?' },
      { label: '📊 Stato', query: 'Mostra lo stato generale del sistema' }
    ],
    'management': [
      { label: '📋 Altri Processi', query: 'Mostra tutti i processi disponibili' },
      { label: '📊 Performance', query: 'Come stanno andando le performance?' }
    ]
  };
  
  return actions[intent] || [
    { label: '❓ Aiuto', query: 'Cosa puoi fare per me?' }
  ];
}
</script>

<style scoped>
/* MILHENA Chat Widget Styles */
.milhena-chat-widget {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
}

/* Minimized chat bubble */
.milhena-chat-bubble {
  @apply bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700;
  @apply p-4 hover:shadow-xl transition-all duration-300;
  @apply flex items-center space-x-3 max-w-xs;
}

.milhena-avatar {
  @apply w-10 h-10 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center;
}

.milhena-name {
  @apply font-semibold text-gray-900 dark:text-white text-sm;
}

.milhena-status {
  @apply flex items-center space-x-1 text-xs text-gray-500;
}

.online-indicator {
  @apply w-2 h-2 bg-green-500 rounded-full animate-pulse;
}

/* Expanded chat interface */
.milhena-chat-expanded {
  @apply bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700;
  @apply w-96 h-[500px] flex flex-col;
}

.milhena-header {
  @apply p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between;
  @apply bg-gradient-to-r from-green-50 to-blue-50 dark:from-gray-700 dark:to-gray-600 rounded-t-xl;
}

.milhena-avatar-large {
  @apply w-12 h-12 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center;
}

.milhena-title {
  @apply font-bold text-gray-900 dark:text-white;
}

.milhena-subtitle {
  @apply text-sm text-gray-600 dark:text-gray-300;
}

.milhena-controls {
  @apply flex items-center space-x-3;
}

.online-indicator-large {
  @apply w-3 h-3 bg-green-500 rounded-full animate-pulse;
}

.milhena-close {
  @apply p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded;
}

/* Messages area */
.milhena-messages {
  @apply flex-1 overflow-y-auto p-4 space-y-4;
}

.milhena-message {
  @apply space-y-2;
}

.milhena-message.user {
  @apply ml-8;
}

.milhena-message.assistant {
  @apply mr-8;
}

.milhena-message.system {
  @apply mx-4;
}

.message-meta {
  @apply flex items-center space-x-2 text-xs text-gray-500;
}

.message-content {
  @apply bg-gray-50 dark:bg-gray-700 rounded-lg p-3 text-sm;
}

.milhena-message.user .message-content {
  @apply bg-blue-500 text-white;
}

.milhena-message.assistant .message-content {
  @apply bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-700;
}

.milhena-message.system .message-content {
  @apply bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-700;
}

/* Quick actions */
.quick-actions {
  @apply flex flex-wrap gap-2 mt-3;
}

.quick-action-btn {
  @apply px-3 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300;
  @apply rounded-full text-xs hover:bg-green-200 dark:hover:bg-green-800 transition-colors;
}

/* Loading indicator */
.milhena-loading {
  @apply mr-8;
}

.typing-indicator {
  @apply flex space-x-1;
}

.typing-indicator span {
  @apply w-2 h-2 bg-green-500 rounded-full animate-pulse;
  animation-delay: calc(var(--i) * 0.2s);
}

.typing-indicator span:nth-child(1) { --i: 0; }
.typing-indicator span:nth-child(2) { --i: 1; }
.typing-indicator span:nth-child(3) { --i: 2; }

/* Input area */
.milhena-input {
  @apply p-4 border-t border-gray-200 dark:border-gray-700 space-y-3;
}

.input-container {
  @apply flex space-x-2;
}

.milhena-textarea {
  @apply flex-1 resize-none border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2;
  @apply focus:ring-2 focus:ring-green-500 focus:border-transparent;
  @apply bg-white dark:bg-gray-700 text-gray-900 dark:text-white;
  @apply placeholder-gray-500 text-sm;
}

.milhena-send-btn {
  @apply px-3 py-2 bg-green-500 hover:bg-green-600 disabled:bg-gray-300;
  @apply text-white rounded-lg transition-colors;
  @apply disabled:cursor-not-allowed;
}

/* Example buttons */
.milhena-examples {
  @apply flex flex-wrap gap-2;
}

.example-btn {
  @apply px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600;
  @apply rounded-full text-gray-600 dark:text-gray-300 transition-colors;
}

/* Animations */
@keyframes slideInUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.milhena-chat-expanded {
  animation: slideInUp 0.3s ease-out;
}

/* Mobile responsive */
@media (max-width: 640px) {
  .milhena-chat-expanded {
    @apply w-full h-full fixed inset-0 rounded-none;
  }
  
  .milhena-chat-bubble {
    @apply max-w-none;
  }
}
</style>