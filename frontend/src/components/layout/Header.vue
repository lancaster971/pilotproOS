<template>
  <header class="bg-black sticky top-0 z-50 h-16 border-b border-gray-900">
    <div class="flex items-center justify-between h-full px-6">
      <div class="flex items-center gap-4">
        <button @click="$emit('toggle-sidebar')" class="text-gray-400 hover:text-white">
          <Menu class="h-6 w-6" />
        </button>
        <h1 class="text-xl font-bold text-white">PilotPro Control Center</h1>
      </div>
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span class="text-sm text-gray-400">Live</span>
        </div>
        <button @click="$emit('logout')" class="text-gray-400 hover:text-white">
          <LogOut class="h-5 w-5" />
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { Menu, LogOut } from 'lucide-vue-next'

defineEmits<{
  'toggle-sidebar': []
  'logout': []
}>()
</script>