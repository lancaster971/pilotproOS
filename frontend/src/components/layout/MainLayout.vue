<template>
  <div class="min-h-screen bg-background">
    <!-- Slim Premium Header -->
    <header class="premium-glass sticky top-0 z-50 h-10 border-b border-border/50">
      <div class="flex items-center justify-between h-full px-4">
        <div class="flex items-center gap-3">
          <button 
            @click="sidebarCollapsed = !sidebarCollapsed" 
            class="text-text-muted hover:text-primary transition-colors p-1"
          >
            <Menu class="h-4 w-4" />
          </button>
          <h1 class="text-sm font-semibold text-text">PilotPro Control Center</h1>
        </div>
        
        <div class="flex items-center gap-3">
          <!-- Compact Live indicator -->
          <div class="flex items-center gap-1 px-2 py-1 bg-primary/10 border border-primary/20 rounded-full">
            <div class="w-1.5 h-1.5 bg-primary rounded-full animate-pulse"></div>
            <span class="text-xs font-medium text-primary">LIVE</span>
          </div>
          
          <!-- Compact User menu -->
          <div class="relative">
            <button
              @click="showUserMenu = !showUserMenu"
              class="flex items-center gap-1.5 text-text-muted hover:text-text transition-colors p-1"
            >
              <User class="h-4 w-4" />
              <span class="text-xs">{{ authStore.user?.name || 'Admin' }}</span>
            </button>
            
            <!-- Compact dropdown -->
            <div
              v-if="showUserMenu"
              class="absolute right-0 mt-1 w-40 bg-surface border border-border rounded-lg shadow-lg py-1"
            >
              <div class="px-3 py-1.5 border-b border-border">
                <p class="text-xs font-medium text-text">{{ authStore.user?.name }}</p>
                <p class="text-xs text-text-muted">{{ authStore.user?.email }}</p>
              </div>
              <button
                @click="handleLogout"
                class="w-full px-3 py-1.5 text-left text-xs text-text-secondary hover:text-text hover:bg-surface-hover transition-colors flex items-center gap-2"
              >
                <LogOut class="h-3 w-3" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>

    <div class="flex">
      <!-- Collapsible PREMIUM Sidebar -->
      <aside 
        :class="sidebarCollapsed ? 'w-16' : 'w-52'"
        class="premium-glass border-r border-border min-h-screen flex-shrink-0 premium-scrollbar transition-all duration-300"
      >
        <div :class="sidebarCollapsed ? 'p-2' : 'p-4'">

          <!-- Navigation -->
          <nav class="space-y-1">
            <router-link
              v-for="(item, index) in navigationItems"
              :key="item.name"
              :to="item.path"
              :class="[
                'flex items-center rounded-lg premium-transition text-text-secondary hover:bg-surface-hover hover:text-text',
                sidebarCollapsed ? 'justify-center p-2' : 'gap-3 px-3 py-2',
                $route.path === item.path ? 'bg-primary text-white' : ''
              ]"
              :style="{ animationDelay: `${index * 50}ms` }"
              :title="sidebarCollapsed ? item.label : ''"
            >
              <component :is="item.icon" :class="sidebarCollapsed ? 'h-4 w-4' : 'h-4 w-4'" />
              <span v-if="!sidebarCollapsed" class="text-sm font-medium">{{ item.label }}</span>
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
    
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Menu, User, LogOut, LayoutDashboard, GitBranch, Play, BarChart3,
  Database, Shield, Bot, AlertTriangle, Clock, ChevronLeft
} from 'lucide-vue-next'
import { useAuthStore } from '../../stores/auth'
import { useUIStore } from '../../stores/ui'

// Stores
const authStore = useAuthStore()
const uiStore = useUIStore()
const router = useRouter()

// Local state
const showUserMenu = ref(false)
const sidebarCollapsed = ref(false)

// Navigation items - streamlined
const navigationItems = [
  { name: 'dashboard', path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { name: 'command-center', path: '/command-center', label: 'Command Center', icon: Menu },
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