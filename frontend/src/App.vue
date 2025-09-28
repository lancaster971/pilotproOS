<template>
  <div id="app" class="min-h-screen bg-background text-text">
    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
    <!-- Custom notification system -->
    <NotificationContainer />
    <!-- Milhena Floating Widget - Always available -->
    <MilhenaWidget v-if="isAuthenticated" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue'
import webSocketService from './services/websocket'
import NotificationContainer from './components/NotificationContainer.vue'
import MilhenaWidget from './components/MilhenaWidget.vue'
import { useAuthStore } from './stores/auth'

// Initialize Design System theme globally
import { initializeDesignSystem } from './design-system'
initializeDesignSystem()

// Check authentication for widget
const authStore = useAuthStore()
const isAuthenticated = computed(() => authStore.isAuthenticated)

// Initialize WebSocket connection when app mounts
onMounted(() => {
  console.log('🎨 Design System initialized globally')
  console.log('🚀 Initializing WebSocket connection...')
  // WebSocket service auto-connects on instantiation
})

// Clean up when app unmounts
onUnmounted(() => {
  webSocketService.disconnect()
})
</script>

<style>
/* Global styles are now handled by design-system and style.css */
/* No more hardcoded colors! */

/* Page Transitions - VELOCI */
.page-enter-active,
.page-leave-active {
  transition: all 0.15s ease-out;
}

.page-enter-from {
  opacity: 0;
  transform: translateX(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

/* Smooth loading states */
.loading-shimmer {
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
</style>