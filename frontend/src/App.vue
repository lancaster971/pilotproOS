<template>
  <div id="app" class="min-h-screen bg-background text-text">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import webSocketService from './services/websocket'

// Initialize Design System theme globally
import { initializeDesignSystem } from './design-system'
initializeDesignSystem()

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
</style>