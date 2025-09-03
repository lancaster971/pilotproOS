<template>
  <div class="fixed top-4 right-4 z-[9999] space-y-2">
    <TransitionGroup name="toast" tag="div">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast-card max-w-sm relative"
        :class="getToastClass(toast.type)"
      >
        <!-- Close Button -->
        <button
          @click="remove(toast.id)"
          class="absolute top-2 right-2 p-1 rounded-full hover:bg-black/10 transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
        
        <!-- Icon -->
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 mt-0.5">
            <CheckCircle v-if="toast.type === 'success'" class="w-5 h-5" />
            <XCircle v-else-if="toast.type === 'error'" class="w-5 h-5" />
            <AlertTriangle v-else-if="toast.type === 'warning'" class="w-5 h-5" />
            <Info v-else class="w-5 h-5" />
          </div>
          
          <!-- Content -->
          <div class="flex-1 pr-6">
            <div class="text-sm font-medium mb-1">{{ toast.title }}</div>
            <div v-if="toast.message" class="text-xs opacity-90">{{ toast.message }}</div>
            
            <!-- Actions -->
            <div v-if="toast.actions && toast.actions.length > 0" class="mt-3 space-x-2">
              <button
                v-for="action in toast.actions"
                :key="action.label"
                @click="action.action"
                class="text-xs underline hover:no-underline"
              >
                {{ action.label }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-vue-next'
import { useToast } from '../composables/useToast'

const { toasts, remove } = useToast()

const getToastClass = (type: string) => {
  const baseClass = 'p-4 rounded-lg shadow-lg backdrop-blur-sm border text-white'
  
  switch (type) {
    case 'success':
      return `${baseClass} bg-green-500/90 border-green-400/50`
    case 'error':
      return `${baseClass} bg-red-500/90 border-red-400/50`
    case 'warning':
      return `${baseClass} bg-yellow-500/90 border-yellow-400/50`
    case 'info':
      return `${baseClass} bg-blue-500/90 border-blue-400/50`
    default:
      return `${baseClass} bg-gray-500/90 border-gray-400/50`
  }
}
</script>

<style scoped>
.toast-card {
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-move {
  transition: transform 0.3s ease;
}
</style>