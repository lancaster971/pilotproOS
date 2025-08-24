<template>
  <button
    :class="[
      'btn-premium',
      'premium-transition',
      sizeClass,
      variantClass,
      $attrs.disabled && 'opacity-50 cursor-not-allowed'
    ]"
    :disabled="$attrs.disabled"
    @click="$emit('click', $event)"
  >
    <slot name="icon" />
    <span v-if="$slots.default">
      <slot />
    </span>
    <slot name="trailing" />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning'
  size?: 'xs' | 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md'
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const sizeClass = computed(() => {
  switch (props.size) {
    case 'xs': return 'px-2 py-1 text-xs'
    case 'sm': return 'px-3 py-1.5 text-sm'
    case 'md': return 'px-4 py-2 text-sm'
    case 'lg': return 'px-6 py-3 text-base'
    default: return 'px-4 py-2 text-sm'
  }
})

const variantClass = computed(() => {
  switch (props.variant) {
    case 'secondary': return 'btn-premium-secondary'
    case 'success': return 'btn-premium-success'
    case 'danger': return 'btn-premium-danger'
    case 'warning': return 'btn-premium-warning'
    default: return 'btn-premium-primary'
  }
})
</script>

<style scoped>
.btn-premium-primary {
  background: linear-gradient(135deg, #10b981, #00d26a) !important;
  border-color: rgba(16, 185, 129, 0.6) !important;
}

.btn-premium-secondary {
  background: linear-gradient(135deg, #374151, #4b5563) !important;
  border-color: rgba(75, 85, 99, 0.6) !important;
}

.btn-premium-success {
  background: linear-gradient(135deg, #10b981, #059669) !important;
  border-color: rgba(16, 185, 129, 0.6) !important;
}

.btn-premium-danger {
  background: linear-gradient(135deg, #ef4444, #dc2626) !important;
  border-color: rgba(239, 68, 68, 0.6) !important;
}

.btn-premium-warning {
  background: linear-gradient(135deg, #f59e0b, #d97706) !important;
  border-color: rgba(245, 158, 11, 0.6) !important;
}
</style>