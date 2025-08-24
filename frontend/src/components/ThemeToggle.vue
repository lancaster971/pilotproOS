<template>
  <div class="fixed top-4 right-4 z-50">
    <div class="flex items-center gap-2 bg-surface border border-border rounded-lg p-2 shadow-lg">
      <Palette class="w-4 h-4 text-primary" />
      <select 
        v-model="currentTheme"
        @change="handleThemeChange"
        class="bg-surface border border-border text-text text-xs rounded px-2 py-1"
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