<template>
  <div class="fixed top-4 right-4 z-50">
    <div class="flex items-center gap-2 premium-glass p-3 rounded-lg enterprise-shadow premium-hover-lift">
      <Palette class="w-4 h-4 text-primary premium-neon-pulse" />
      <span class="text-xs font-semibold text-primary premium-text-glow">THEME:</span>
      <select 
        v-model="currentTheme"
        @change="handleThemeChange"
        class="premium-input text-xs rounded px-2 py-1 font-semibold"
      >
        <option value="default">Default Dark</option>
        <option value="emerald">Emerald Bright</option>
        <option value="premium">Premium Glow</option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { switchTheme, getCurrentTheme, type ThemeName } from '../design-system'
import { Palette } from 'lucide-vue-next'

const currentTheme = ref<ThemeName>('default')

function handleThemeChange() {
  switchTheme(currentTheme.value)
}

onMounted(() => {
  currentTheme.value = getCurrentTheme()
})
</script>

<style scoped>
select {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-text);
}

select option {
  background: var(--color-surface);
  color: var(--color-text);
}
</style>