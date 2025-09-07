<template>
  <div class="milhena-chat-widget">
    <!-- Chat minimized button -->
    <div 
      v-if="!isExpanded" 
      @click="toggleChat"
      class="control-card p-4 cursor-pointer group hover:border-primary/30 transition-all duration-300"
    >
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
          <Bot class="w-5 h-5 text-primary" />
        </div>
        <div>
          <span class="font-semibold text-text text-sm">MILHENA</span>
          <div class="flex items-center space-x-1 text-xs text-text-muted">
            <div class="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
            <span>Manager Intelligente</span>
          </div>
        </div>
      </div>
      <MessageCircle class="w-5 h-5 text-text-muted group-hover:text-primary transition-colors" />
    </div>

    <!-- Chat expanded interface -->
    <div v-else class="control-card w-96 h-[500px] flex flex-col">
      <!-- Header -->
      <div class="p-4 border-b border-border/50 flex items-center justify-between bg-surface/50">
        <div class="flex items-center space-x-3">
          <div class="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
            <Bot class="w-6 h-6 text-primary" />
          </div>
          <div>
            <h4 class="font-bold text-text">MILHENA</h4>
            <p class="text-sm text-text-muted">Manager Intelligente per i tuoi processi aziendali</p>
          </div>
        </div>
        
        <div class="flex items-center space-x-3">
          <div class="w-3 h-3 bg-primary rounded-full animate-pulse"></div>
          <button @click="toggleChat" class="p-1 hover:bg-surface-hover rounded text-text-muted hover:text-text transition-colors">
            <X class="w-5 h-5" />
          </button>
        </div>
      </div>

      <!-- Messages area -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4" ref="messagesContainer">
        <div 
          v-for="message in messages" 
          :key="message.id" 
          :class="message.type === 'user' ? 'ml-8' : 'mr-8'"
          class="space-y-2"
        >
          <!-- Message header -->
          <div class="flex items-center space-x-2 text-xs text-text-muted">
            <component 
              :is="message.type === 'user' ? User : Bot"
              :class="message.type === 'user' ? 'text-secondary' : 'text-primary'"
              class="w-4 h-4" 
            />
            <span>
              {{ formatTime(message.timestamp) }}
            </span>
          </div>

          <!-- Message content -->
          <div :class="[
            'rounded-lg p-3 text-sm',
            message.type === 'user' 
              ? 'bg-secondary text-white ml-4' 
              : message.type === 'assistant'
                ? 'bg-surface border border-border mr-4 text-text'
                : 'bg-warning/10 border border-warning/20 text-text mx-4'
          ]">
            <p v-for="(line, index) in message.content.split('\n')" :key="index">
              {{ line }}
            </p>
          </div>

          <!-- Suggested queries as clickable text (like ChatGPT) -->
          <!-- Suggested queries as subtle clickable text (ChatGPT style) -->
          <div v-if="message.type === 'assistant' && message.quickActions" class="mt-3 mr-4 space-y-1">
            <button
              v-for="action in message.quickActions"
              :key="action.query"
              @click="sendMessage(action.query)"
              class="block text-sm text-text-muted hover:text-primary transition-colors cursor-pointer bg-transparent border-none p-0 text-left underline-offset-2 hover:underline"
            >
              {{ action.query }}
            </button>
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="isLoading" class="mr-8">
          <div class="flex items-center space-x-2">
            <Bot class="w-4 h-4 text-primary" />
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span class="text-sm text-text-muted">MILHENA sta pensando...</span>
          </div>
        </div>
      </div>

      <!-- Input area -->
      <div class="p-4 border-t border-border/50 space-y-3">
        <div class="flex space-x-2">
          <textarea
            v-model="inputMessage"
            @keydown.enter.prevent="handleEnterKey"
            placeholder="Chiedi a MILHENA sui tuoi processi aziendali..."
            :disabled="isLoading"
            class="flex-1 resize-none border border-border rounded-lg px-3 py-2 bg-surface text-text placeholder-text-muted focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
            rows="1"
          />
          <button 
            @click="sendMessage(inputMessage)"
            :disabled="!inputMessage.trim() || isLoading"
            class="px-3 py-2 bg-primary hover:bg-primary-hover disabled:opacity-50 text-white rounded-lg transition-colors disabled:cursor-not-allowed"
          >
            <Send class="w-4 h-4" />
          </button>
        </div>
        
        <!-- Subtle example suggestions (ChatGPT style) -->
        <div class="space-y-1">
          <button 
            v-for="example in quickExamples"
            :key="example"
            @click="sendMessage(example)"
            class="block text-xs text-text-muted hover:text-primary transition-colors cursor-pointer bg-transparent border-none p-0 text-left underline-offset-2 hover:underline"
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
import { Bot, User, MessageCircle, X, Send, BarChart3, AlertTriangle, Activity } from 'lucide-vue-next';
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
    content: 'Ciao! Sono MILHENA, il tuo Manager Intelligente per l\'automazione business.\n\nPuoi chiedermi qualsiasi cosa sui tuoi processi automatizzati. Sono qui per aiutarti!',
    timestamp: new Date(),
    quickActions: [
      { query: 'Mostra lo stato dei miei processi' },
      { query: 'Report delle performance' },
      { query: 'Ci sono errori da controllare?' }
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
      { query: 'Mostra le metriche dettagliate' },
      { query: 'Ci sono errori da controllare?' }
    ],
    'analytics': [
      { query: 'Mostra i trend settimanali' },
      { query: 'Quali sono i KPI principali?' }
    ],
    'troubleshooting': [
      { query: 'Come posso risolvere questi problemi?' },
      { query: 'Mostra lo stato generale del sistema' }
    ],
    'management': [
      { query: 'Mostra tutti i processi disponibili' },
      { query: 'Come stanno andando le performance?' }
    ]
  };
  
  return actions[intent] || [
    { query: 'Cosa puoi fare per me?' }
  ];
}
</script>

<style scoped>
/* MILHENA Chat Widget - PilotProOS Design System */
.milhena-chat-widget {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
}

/* Typing indicator animation */
.typing-indicator {
  @apply flex space-x-1;
}

.typing-indicator span {
  @apply w-2 h-2 bg-primary rounded-full animate-pulse;
  animation-delay: calc(var(--i) * 0.2s);
}

.typing-indicator span:nth-child(1) { --i: 0; }
.typing-indicator span:nth-child(2) { --i: 1; }
.typing-indicator span:nth-child(3) { --i: 2; }

/* Slide-in animation for expanded chat */
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

.control-card {
  animation: slideInUp 0.3s ease-out;
}

/* Mobile responsive */
@media (max-width: 640px) {
  .milhena-chat-widget .control-card {
    @apply w-full h-full fixed inset-0 rounded-none;
  }
}
</style>