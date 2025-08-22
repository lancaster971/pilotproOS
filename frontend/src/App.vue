<template>
  <div id="app" class="dark min-h-screen bg-black text-white">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import webSocketService from './services/websocket'

// Initialize WebSocket connection when app mounts
onMounted(() => {
  console.log('🚀 Initializing WebSocket connection...')
  // WebSocket service auto-connects on instantiation
})

// Clean up when app unmounts
onUnmounted(() => {
  webSocketService.disconnect()
})
</script>

<style>
* {
  font-weight: 300 !important;
  font-family: 'DM Sans', sans-serif;
}

.control-card {
  background-color: rgb(17 24 39);
  border: 1px solid rgb(31 41 55);
  border-radius: 0.5rem;
}

.btn-control {
  background-color: rgb(31 41 55);
  border: 1px solid rgb(55 65 81);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-control-primary {
  background-color: rgb(22 163 74);
  border: 1px solid rgb(34 197 94);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.text-gradient {
  background: linear-gradient(45deg, #10b981, #059669);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>