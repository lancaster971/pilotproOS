<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="handleClickOutside"
    >
      <div class="control-card w-full max-w-md premium-modal">
        <div class="p-6">
          <!-- Header -->
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-semibold text-text">{{ title }}</h3>
            <button
              @click="$emit('close')"
              class="text-text-muted hover:text-text transition-colors"
            >
              <Icon icon="lucide:x" class="h-5 w-5" />
            </button>
          </div>

          <!-- Loading State -->
          <div v-if="isLoading" class="flex items-center justify-center py-8">
            <div class="text-center">
              <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-400"></div>
              <p class="mt-2 text-text-muted">{{ loadingText }}</p>
            </div>
          </div>

          <!-- Error State -->
          <div v-else-if="error" class="mb-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <div class="flex items-center gap-2">
              <Icon icon="lucide:alert-circle" class="h-4 w-4 text-red-400" />
              <span class="text-red-400 text-sm">{{ error }}</span>
            </div>
          </div>

          <!-- Content Slot -->
          <div v-else>
            <slot name="content" :close="$emit.bind(null, 'close')"></slot>
          </div>

          <!-- Footer Actions -->
          <div v-if="!isLoading" class="flex items-center justify-end gap-3 pt-6 mt-6 border-t border-border">
            <button
              type="button"
              @click="$emit('close')"
              class="btn-control"
            >
              {{ cancelText }}
            </button>
            <button
              v-if="showSubmit"
              type="button"
              @click="$emit('submit')"
              :disabled="isLoading || !canSubmit"
              class="btn-control-primary"
              :class="{ 'opacity-50 cursor-not-allowed': isLoading || !canSubmit }"
            >
              <Icon v-if="!isLoading" :icon="submitIcon" class="h-4 w-4" />
              <Icon v-else icon="lucide:loader-2" class="h-4 w-4 animate-spin" />
              {{ submitText }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
import { useModal } from '../../composables/useModal'

interface Props {
  show: boolean
  title: string
  loadingText?: string
  cancelText?: string
  submitText?: string
  showSubmit?: boolean
  canSubmit?: boolean
  submitIcon?: any
  isLoading?: boolean
  error?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  loadingText: 'Caricamento...',
  cancelText: 'Annulla',
  submitText: 'Conferma',
  showSubmit: true,
  canSubmit: true,
  submitIcon: 'lucide:check',
  isLoading: false,
  error: null
})

const emit = defineEmits<{
  close: []
  submit: []
}>()

const { handleClickOutside } = useModal(false, {
  closeOnClickOutside: true,
  closeOnEscape: true
})

const modalClickOutside = () => {
  handleClickOutside()
  emit('close')
}
</script>

<style scoped>
.premium-modal {
  animation: modalAppear 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes modalAppear {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
</style>