<template>
  <div class="theme-switcher">
    <div class="flex items-center gap-3 p-4 bg-surface border border-border rounded-lg">
      <div class="flex items-center gap-2">
        <Icon icon="lucide:palette" class="w-4 h-4 text-primary" />
        <span class="text-sm font-medium text-text">Theme:</span>
      </div>
      
      <div class="flex gap-1">
        <button
          v-for="(theme, key) in availableThemes"
          :key="key"
          :class="[
            'px-3 py-1.5 text-xs rounded-md transition-all duration-200',
            currentTheme === key 
              ? 'bg-primary text-white shadow-success-glow' 
              : 'bg-surface-hover text-text-secondary hover:bg-border hover:text-text'
          ]"
          @click="switchToTheme(key as ThemeName)"
        >
          {{ theme.name }}
        </button>
      </div>
    </div>
    
    <!-- Theme Preview Cards -->
    <div class="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="control-card p-4">
        <h3 class="text-text font-semibold mb-2">Surface Example</h3>
        <p class="text-text-secondary text-sm mb-3">This card uses the design system variables.</p>
        <div class="btn-control-primary">
          <Icon icon="lucide:check" class="w-4 h-4" />
          <span>Primary Action</span>
        </div>
      </div>
      
      <div class="control-card p-4">
        <h3 class="text-text font-semibold mb-2">Status Examples</h3>
        <div class="space-y-2">
          <div class="status-success px-2 py-1 rounded text-xs border">Success</div>
          <div class="status-error px-2 py-1 rounded text-xs border">Error</div>
          <div class="status-warning px-2 py-1 rounded text-xs border">Warning</div>
          <div class="status-running px-2 py-1 rounded text-xs border">Running</div>
        </div>
      </div>
      
      <div class="control-card p-4">
        <h3 class="text-text font-semibold mb-2">Interactive Elements</h3>
        <div class="space-y-2">
          <div class="btn-control">
            <Icon icon="lucide:settings" class="w-4 h-4" />
            <span>Normal Button</span>
          </div>
          <div class="text-gradient text-lg font-semibold">
            Gradient Text
          </div>
        </div>
      </div>
    </div>
    
    <!-- Live Theme Info -->
    <div class="mt-4 p-3 bg-surface border border-border rounded-lg">
      <div class="flex items-center gap-2 mb-2">
        <div class="live-dot"></div>
        <span class="text-xs font-semibold text-success">LIVE THEME DATA</span>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
        <div>
          <div class="text-text-muted">Primary:</div>
          <div class="text-text font-mono">{{ liveColors.primary }}</div>
        </div>
        <div>
          <div class="text-text-muted">Background:</div>
          <div class="text-text font-mono">{{ liveColors.background }}</div>
        </div>
        <div>
          <div class="text-text-muted">Surface:</div>
          <div class="text-text font-mono">{{ liveColors.surface }}</div>
        </div>
        <div>
          <div class="text-text-muted">Border:</div>
          <div class="text-text font-mono">{{ liveColors.border }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { switchTheme, getCurrentTheme, getCSSVariable, themes, type ThemeName } from '../design-system'
import { Icon } from '@iconify/vue'

const currentTheme = ref<ThemeName>('default')
const availableThemes = themes

// Live CSS variable values
const liveColors = reactive({
  primary: '',
  background: '',
  surface: '',
  border: ''
})

// Switch theme with instant update
function switchToTheme(themeName: ThemeName) {
  switchTheme(themeName)
  currentTheme.value = themeName
  updateLiveColors()
}

// Update live color values from CSS variables
function updateLiveColors() {
  liveColors.primary = getCSSVariable('color-primary')
  liveColors.background = getCSSVariable('color-background')
  liveColors.surface = getCSSVariable('color-surface')
  liveColors.border = getCSSVariable('color-border')
}

// Listen for theme changes
function onThemeChange(event: CustomEvent) {
  currentTheme.value = event.detail.theme
  updateLiveColors()
}

onMounted(() => {
  currentTheme.value = getCurrentTheme()
  updateLiveColors()
  window.addEventListener('theme-changed', onThemeChange as EventListener)
})

onUnmounted(() => {
  window.removeEventListener('theme-changed', onThemeChange as EventListener)
})
</script>

<style scoped>
.live-dot {
  width: 6px;
  height: 6px;
  background: var(--success);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.2); }
}
</style>