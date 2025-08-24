<template>
  <div class="min-h-screen bg-background">
    <!-- Header - PREMIUM with glassmorphism -->
    <header class="premium-glass sticky top-0 z-50 h-16 border-b border-border backdrop-blur-25">
      <div class="flex items-center justify-between h-full px-6">
        <div class="flex items-center gap-4">
          <button 
            @click="uiStore.toggleSidebar()" 
            class="text-text-muted hover:text-text transition-colors"
          >
            <Menu class="h-6 w-6" />
          </button>
          <h1 class="text-xl font-bold text-text">PilotPro Control Center</h1>
        </div>
        
        <div class="flex items-center gap-4">
          <!-- Premium Live indicator -->
          <div class="premium-status-online">
            <span class="text-sm font-semibold text-primary premium-text-glow">SISTEMA LIVE</span>
          </div>
          
          <!-- User menu -->
          <div class="relative">
            <button
              @click="showUserMenu = !showUserMenu"
              class="flex items-center gap-2 text-text-muted hover:text-text transition-colors"
            >
              <User class="h-5 w-5" />
              <span class="text-sm">{{ authStore.user?.name || 'User' }}</span>
            </button>
            
            <!-- User dropdown -->
            <div
              v-if="showUserMenu"
              class="absolute right-0 mt-2 w-48 bg-surface border border-border rounded-lg shadow-lg py-2"
            >
              <div class="px-4 py-2 border-b border-border">
                <p class="text-sm font-medium text-text">{{ authStore.user?.name }}</p>
                <p class="text-xs text-text-muted">{{ authStore.user?.email }}</p>
              </div>
              <button
                @click="handleLogout"
                class="w-full px-4 py-2 text-left text-sm text-text-secondary hover:text-text hover:bg-surface-hover transition-colors flex items-center gap-2"
              >
                <LogOut class="h-4 w-4" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>

    <div class="flex">
      <!-- PREMIUM Sidebar with glassmorphism -->
      <aside class="w-60 premium-glass border-r border-border min-h-screen flex-shrink-0 premium-scrollbar">
        <div class="p-6">
          <!-- Logo -->
          <div class="flex items-center gap-3 mb-8 pb-4 border-b border-border">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                 style="background: linear-gradient(135deg, #10b981, #00d26a); box-shadow: 0 0 8px rgba(16, 185, 129, 0.3);">
              <span class="text-white font-bold text-sm">P</span>
            </div>
            <div>
              <h1 class="text-text font-semibold text-sm">PilotPro OS</h1>
              <p class="text-text-muted text-xs">Enterprise Command Center</p>
            </div>
          </div>

          <!-- Navigation -->
          <nav class="space-y-2">
            <router-link
              v-for="(item, index) in navigationItems"
              :key="item.name"
              :to="item.path"
              class="flex items-center gap-3 px-4 py-2 rounded-lg premium-transition text-text-secondary hover:bg-surface-hover hover:text-text premium-hover-lift"
              :class="[$route.path === item.path ? 'premium-glass premium-glow-intense text-white' : '']"
              :style="{ animationDelay: `${index * 100}ms` }"
            >
              <component :is="item.icon" class="h-5 w-5" />
              <span class="text-sm">{{ item.label }}</span>
            </router-link>
          </nav>
        </div>
      </aside>

      <!-- Main content area -->
      <main class="flex-1">
        <div class="p-6">
          <slot />
        </div>
      </main>
    </div>

    <!-- Mobile sidebar overlay -->
    <div
      v-if="uiStore.sidebarOpen && isMobile"
      @click="uiStore.toggleSidebar()"
      class="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
    ></div>
    
    <!-- Theme Toggle - Available on all pages -->
    <ThemeToggle />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Menu, User, LogOut, LayoutDashboard, GitBranch, Play, BarChart3,
  Database, Shield, Bot, AlertTriangle, Clock
} from 'lucide-vue-next'
import { useAuthStore } from '../../stores/auth'
import { useUIStore } from '../../stores/ui'
import ThemeToggle from '../ThemeToggle.vue'

// Stores
const authStore = useAuthStore()
const uiStore = useUIStore()
const router = useRouter()

// Local state
const showUserMenu = ref(false)

// Navigation items - streamlined
const navigationItems = [
  { name: 'dashboard', path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { name: 'workflows', path: '/workflows', label: 'Workflows', icon: GitBranch },
  { name: 'workflow-visual', path: '/workflows/visual', label: 'Visual Flow', icon: GitBranch },
  { name: 'executions', path: '/executions', label: 'Executions', icon: Play },
  { name: 'security', path: '/security', label: 'Security', icon: Shield },
  { name: 'agents', path: '/agents', label: 'AI Agents', icon: Bot },
  { name: 'scheduler', path: '/scheduler', label: 'Scheduler', icon: Clock },
]

// Methods
const handleLogout = () => {
  authStore.logout()
  uiStore.showToast('Logout', 'Disconnesso con successo', 'success')
  router.push('/login')
  showUserMenu.value = false
}

// Close user menu when clicking outside
onMounted(() => {
  const handleClickOutside = (event: Event) => {
    const target = event.target as HTMLElement
    if (!target.closest('.relative')) {
      showUserMenu.value = false
    }
  }
  
  document.addEventListener('click', handleClickOutside)
  
  // Cleanup
  return () => {
    document.removeEventListener('click', handleClickOutside)
  }
})
</script>

<style scoped>
/* Active route styling using design system */
.router-link-active {
  background: var(--color-primary);
  color: white;
}
</style>