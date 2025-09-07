<template>
  <div class="fixed bottom-4 right-4 z-50">
    <!-- Simple chat toggle -->
    <button 
      v-if="!isOpen"
      @click="isOpen = true"
      class="w-12 h-12 bg-primary rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all"
    >
      <Bot class="w-6 h-6 text-white" />
    </button>

    <!-- Simple chat window -->
    <div v-else class="control-card w-96 h-[600px] flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between p-3 border-b border-border/50">
        <div class="flex items-center space-x-2">
          <Bot class="w-5 h-5 text-primary" />
          <span class="font-medium text-text">MILHENA</span>
        </div>
        <button @click="isOpen = false" class="text-text-muted hover:text-text">
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Messages -->
      <div class="flex-1 overflow-y-auto p-3 space-y-3">
        <div v-for="msg in messages" :key="msg.id">
          <div :class="[
            'p-3 rounded-lg text-sm max-w-[85%]',
            msg.isUser ? 'bg-primary text-white ml-auto' : 'bg-surface text-text'
          ]">
            {{ msg.text }}
          </div>
        </div>
        
        <div v-if="thinking" class="flex items-center space-x-2 text-text-muted">
          <Bot class="w-4 h-4" />
          <span class="text-sm">Pensando...</span>
        </div>
      </div>

      <!-- Input -->
      <div class="p-3 border-t border-border/50">
        <div class="flex space-x-2">
          <input
            v-model="input"
            @keydown.enter="send"
            placeholder="Scrivi a MILHENA..."
            class="flex-1 px-3 py-2 border border-border rounded bg-surface text-text placeholder-text-muted text-sm"
          />
          <button @click="send" class="px-3 py-2 bg-primary text-white rounded hover:bg-primary-hover">
            <Send class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Bot, X, Send } from 'lucide-vue-next';
import { ofetch } from 'ofetch';
import { useToast } from 'vue-toastification';

const toast = useToast();
const isOpen = ref(false);
const input = ref('');
const thinking = ref(false);
const messages = ref([]);

const api = ofetch.create({ baseURL: 'http://localhost:3002/api' });

onMounted(() => {
  messages.value = [{
    id: '1',
    text: 'Ciao! Sono MILHENA, il tuo Manager Intelligente. Chiedimi qualsiasi cosa sui tuoi processi aziendali.',
    isUser: false
  }];
});

async function send() {
  if (!input.value.trim()) return;
  
  messages.value.push({
    id: Date.now(),
    text: input.value,
    isUser: true
  });
  
  const query = input.value;
  input.value = '';
  thinking.value = true;

  try {
    const response = await api('/chat', {
      method: 'POST',
      body: { query }
    });

    messages.value.push({
      id: Date.now() + 1,
      text: response.response || 'Risposta ricevuta.',
      isUser: false
    });
  } catch (error) {
    console.error('Error:', error);
    messages.value.push({
      id: Date.now() + 1,
      text: 'Mi dispiace, ho avuto un problema. Riprova tra qualche istante.',
      isUser: false
    });
    toast.error('MILHENA non disponibile');
  }
  
  thinking.value = false;
}
</script>