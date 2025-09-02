<template>
  <div class="premium-status-online premium-transition">
    <div class="premium-status-dot"></div>
    <span class="text-sm font-semibold text-primary premium-text-glow">
      <slot />
    </span>
  </div>
</template>

<script setup lang="ts">
// No props needed - slot content determines the text
</script>

<style scoped>
.premium-status-dot {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  animation: premiumPulseRing 2s infinite;
  box-shadow: 
    0 0 10px rgba(16, 185, 129, 0.8),
    0 0 20px rgba(16, 185, 129, 0.4),
    0 0 30px rgba(16, 185, 129, 0.2);
}

@keyframes premiumPulseRing {
  0% { 
    transform: scale(1);
    box-shadow: 
      0 0 10px rgba(16, 185, 129, 0.8),
      0 0 20px rgba(16, 185, 129, 0.4),
      0 0 30px rgba(16, 185, 129, 0.2);
  }
  50% { 
    transform: scale(1.4);
    box-shadow: 
      0 0 15px rgba(16, 185, 129, 1),
      0 0 30px rgba(16, 185, 129, 0.6),
      0 0 45px rgba(16, 185, 129, 0.3);
  }
  100% { 
    transform: scale(1);
    box-shadow: 
      0 0 10px rgba(16, 185, 129, 0.8),
      0 0 20px rgba(16, 185, 129, 0.4),
      0 0 30px rgba(16, 185, 129, 0.2);
  }
}
</style>