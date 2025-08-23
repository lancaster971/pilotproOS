<template>
  <header class="header-container sticky top-0 z-50 h-16 border-b border-border backdrop-blur-lg">
    <!-- Background with glass effect -->
    <div class="header-background absolute inset-0"></div>
    
    <!-- Content -->
    <div class="relative z-10 flex items-center justify-between h-full px-6">
      <!-- Left section -->
      <div class="flex items-center gap-4">
        <button 
          @click="$emit('toggle-sidebar')" 
          class="header-toggle-btn p-2 rounded-lg transition-all duration-200 hover:bg-surface-200/50"
        >
          <Menu class="h-5 w-5 text-foreground-muted hover:text-foreground" />
        </button>
        
        <!-- Breadcrumb/Title -->
        <div class="flex items-center gap-2">
          <h1 class="text-lg font-semibold text-foreground">{{ pageTitle }}</h1>
          <div v-if="subtitle" class="flex items-center gap-2">
            <ChevronRight class="h-4 w-4 text-foreground-muted" />
            <span class="text-sm text-foreground-muted">{{ subtitle }}</span>
          </div>
        </div>
      </div>

      <!-- Center section - Search (optional) -->
      <div class="flex-1 max-w-md mx-8 hidden lg:block">
        <div class="relative">
          <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-foreground-muted" />
          <input
            type="text"
            placeholder="Cerca processi, esecuzioni..."
            class="w-full pl-10 pr-4 py-2 bg-surface-100/50 border border-border rounded-lg text-sm text-foreground placeholder-foreground-muted focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
          />
        </div>
      </div>

      <!-- Right section -->
      <div class="flex items-center gap-4">
        <!-- System status -->
        <div class="hidden md:flex items-center gap-3 px-3 py-1 bg-surface-100/30 border border-border rounded-full">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 bg-primary-500 rounded-full animate-pulse"></div>
            <span class="text-xs text-foreground-muted font-medium">Sistema Online</span>
          </div>
          <div class="w-px h-4 bg-border"></div>
          <span class="text-xs text-foreground-muted">{{ currentTime }}</span>
        </div>

        <!-- Notifications -->
        <button class="header-action-btn relative p-2 rounded-lg">
          <Bell class="h-5 w-5" />
          <div class="absolute -top-1 -right-1 w-3 h-3 bg-primary-500 rounded-full flex items-center justify-center">
            <span class="text-xs text-white font-bold">3</span>
          </div>
        </button>

        <!-- Settings -->
        <button class="header-action-btn p-2 rounded-lg">
          <Settings class="h-5 w-5" />
        </button>

        <!-- User menu -->
        <div class="flex items-center gap-3 pl-3 border-l border-border">
          <div class="hidden sm:block text-right">
            <p class="text-sm font-medium text-foreground">Admin</p>
            <p class="text-xs text-foreground-muted">Amministratore</p>
          </div>
          
          <button 
            @click="$emit('logout')" 
            class="header-action-btn p-2 rounded-lg text-error-500 hover:bg-error-500/10 hover:text-error-400"
            title="Logout"
          >
            <LogOut class="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { 
  Menu, LogOut, ChevronRight, Search, Bell, Settings
} from 'lucide-vue-next'

defineEmits<{
  'toggle-sidebar': []
  'logout': []
}>()

const route = useRoute()

// Page title basato sulla route corrente
const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/dashboard': 'Dashboard',
    '/workflows': 'Processi Business', 
    '/executions': 'Esecuzioni',
    '/stats': 'Analytics',
    '/database': 'Database',
    '/security': 'Sicurezza',
    '/agents': 'AI Agents',
    '/scheduler': 'Scheduler'
  }
  return titles[route.path] || 'PilotPro OS'
})

// Subtitle opzionale
const subtitle = computed(() => {
  const subtitles: Record<string, string> = {
    '/workflows': 'Automazioni',
    '/executions': 'Cronologia',
    '/stats': 'Metriche KPI',
    '/agents': 'Assistenti IA'
  }
  return subtitles[route.path]
})

// Current time display
const currentTime = ref('')

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('it-IT', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

onMounted(() => {
  updateTime()
  const interval = setInterval(updateTime, 1000)
  onUnmounted(() => clearInterval(interval))
})
</script>

<style scoped>
.header-container {
  background: transparent;
  backdrop-filter: blur(10px);
}

.header-background {
  background: linear-gradient(90deg, 
    rgba(17, 24, 39, 0.95) 0%, 
    rgba(31, 41, 55, 0.90) 50%, 
    rgba(17, 24, 39, 0.95) 100%
  );
  backdrop-filter: blur(20px);
}

.header-action-btn {
  @apply text-foreground-muted hover:text-foreground hover:bg-surface-200/30 transition-all duration-200;
}

.header-toggle-btn:hover {
  @apply bg-primary-500/10 border-primary-500/20;
}
</style>