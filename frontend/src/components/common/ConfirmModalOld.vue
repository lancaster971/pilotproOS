<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-2xl shadow-xl max-w-md w-full mx-4">
      <div class="p-6">
        <!-- Header -->
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-xl font-semibold text-text">{{ title }}</h3>
          <button 
            @click="$emit('close')"
            class="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X class="h-5 w-5" />
          </button>
        </div>

        <!-- Message -->
        <div class="mb-6">
          <p class="text-text-muted">{{ message }}</p>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3">
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            {{ cancelText }}
          </button>
          <button
            type="button"
            @click="$emit('confirm')"
            :disabled="isLoading"
            :class="[confirmClass, 'px-4 py-2 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2']"
          >
            <Loader2 v-if="isLoading" class="h-4 w-4 animate-spin" />
            {{ isLoading ? 'Elaborazione...' : confirmText }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { X, Loader2 } from 'lucide-vue-next'

defineProps({
  title: {
    type: String,
    default: 'Conferma'
  },
  message: {
    type: String,
    required: true
  },
  confirmText: {
    type: String,
    default: 'Conferma'
  },
  cancelText: {
    type: String,
    default: 'Annulla'
  },
  confirmClass: {
    type: String,
    default: 'bg-primary hover:bg-primary-hover'
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['close', 'confirm'])
</script>