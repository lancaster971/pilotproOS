<template>
  <Dialog 
    :visible="true" 
    @update:visible="$emit('close')"
    modal 
    :closable="false"
    :dismissableMask="true"
    class="premium-modal"
    :style="{ width: '24rem' }"
    :ptOptions="{ mergeProps: false }"
    :pt="{
      mask: { 
        style: 'animation: modalFadeIn 0.12s ease-out !important;'
      },
      root: { 
        style: 'animation: modalSlideIn 0.18s cubic-bezier(0.34, 1.56, 0.64, 1) !important;'
      }
    }"
  >
    <template #header>
      <div class="flex items-center justify-between w-full">
        <h3 class="text-lg font-semibold text-text">{{ title }}</h3>
        <Button
          @click="$emit('close')"
          severity="secondary"
          text
          rounded
          size="small"
        >
          <X class="h-4 w-4" />
        </Button>
      </div>
    </template>

    <!-- Message -->
    <div class="mb-4">
      <p class="text-text-muted">{{ message }}</p>
    </div>
    
    <template #footer>
      <div class="flex justify-end gap-3">
        <Button
          @click="$emit('close')"
          severity="secondary"
          size="small"
        >
          {{ cancelText }}
        </Button>
        <Button
          @click="$emit('confirm')"
          :disabled="isLoading"
          :severity="confirmSeverity"
          size="small"
          :loading="isLoading"
        >
          {{ isLoading ? 'Elaborazione...' : confirmText }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed } from 'vue'
import { X, Loader2 } from 'lucide-vue-next'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'

const props = defineProps({
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

const confirmSeverity = computed(() => {
  if (props.confirmClass.includes('red')) return 'danger'
  if (props.confirmClass.includes('green')) return 'success'
  if (props.confirmClass.includes('blue')) return 'info'
  return 'primary'
})

defineEmits(['close', 'confirm'])
</script>