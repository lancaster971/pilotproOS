<template>
  <div 
    :class="[
      'premium-glass',
      'premium-hover-lift',
      'premium-transition',
      animationClass,
      glowClass,
      customClass
    ]"
    :style="animationDelay"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  animation?: 'float' | 'pulse' | 'glow' | 'none'
  glow?: 'normal' | 'intense' | 'neon' | 'none'
  delay?: number
  customClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  animation: 'float',
  glow: 'normal',
  delay: 0,
  customClass: ''
})

const animationClass = computed(() => {
  switch (props.animation) {
    case 'float': return 'premium-float'
    case 'pulse': return 'premium-neon-pulse'
    case 'glow': return 'premium-glow-intense'
    default: return ''
  }
})

const glowClass = computed(() => {
  switch (props.glow) {
    case 'intense': return 'premium-glow-intense'
    case 'neon': return 'premium-neon-pulse'
    default: return ''
  }
})

const animationDelay = computed(() => ({
  animationDelay: `${props.delay}ms`
}))
</script>

<style scoped>
/* Premium card effects are in premium.css */
</style>