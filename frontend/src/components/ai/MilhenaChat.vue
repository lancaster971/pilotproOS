<template>
  <div class="milhena-chat-container">
    <!-- AI Chat Interface - To Be Implemented -->
    <div class="chat-placeholder">
      <div class="placeholder-content">
        <div class="placeholder-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-16 h-16 text-gray-400">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
          </svg>
        </div>
        
        <h3 class="text-xl font-semibold text-gray-700 mb-2">
          Chat AI - In Sviluppo
        </h3>
        
        <p class="text-gray-500 text-center mb-4">
          L'interfaccia chat AI sarà implementata in futuro per fornire assistenza intelligente sui processi di automazione.
        </p>
        
        <div class="features-preview">
          <div class="feature-item">
            <span class="feature-icon">🤖</span>
            <span class="feature-text">Assistente AI per automazione</span>
          </div>
          
          <div class="feature-item">
            <span class="feature-icon">📊</span>
            <span class="feature-text">Analisi processi business</span>
          </div>
          
          <div class="feature-item">
            <span class="feature-icon">🔍</span>
            <span class="feature-text">Ricerca workflow intelligente</span>
          </div>
        </div>
        
        <div class="implementation-note">
          <p class="text-sm text-gray-400">
            Implementazione prevista: Q1 2025
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Empty script - no AI agent implementation
console.log('AI Chat placeholder - implementation pending');
</script>

<style scoped>
.milhena-chat-container {
  @apply w-full h-full flex items-center justify-center p-8;
}

.chat-placeholder {
  @apply max-w-md w-full;
}

.placeholder-content {
  @apply bg-white rounded-lg shadow-lg p-8 text-center;
}

.placeholder-icon {
  @apply flex justify-center mb-4;
}

.features-preview {
  @apply space-y-3 mb-6;
}

.feature-item {
  @apply flex items-center justify-center space-x-3 text-gray-600;
}

.feature-icon {
  @apply text-2xl;
}

.feature-text {
  @apply text-sm font-medium;
}

.implementation-note {
  @apply pt-4 border-t border-gray-200;
}
</style>