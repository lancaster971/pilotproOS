<template>
  <div class="min-h-screen bg-background">

    <div class="flex">
      <!-- Collapsible PREMIUM Sidebar -->
      <aside 
        :class="sidebarCollapsed ? 'w-16' : 'w-52'"
        class="premium-glass border-r border-border min-h-screen flex-shrink-0 premium-scrollbar transition-all duration-300"
      >
        <div :class="sidebarCollapsed ? 'p-3' : 'p-5'">
          <!-- Logo with Collapse Toggle -->
          <div class="flex items-center mb-6 pb-3 border-b border-border">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                 style="background: linear-gradient(135deg, #10b981, #00d26a); box-shadow: 0 0 8px rgba(16, 185, 129, 0.3);">
              <span class="text-white font-bold text-sm">P</span>
            </div>
            <div v-if="!sidebarCollapsed" class="ml-3 flex-1">
              <h1 class="text-text font-semibold text-sm">PilotPro OS</h1>
              <p class="text-text-muted text-xs">Enterprise Command Center</p>
            </div>
            <button 
              @click="sidebarCollapsed = !sidebarCollapsed"
              class="p-1 text-text-muted hover:text-text transition-colors ml-2"
            >
              <ChevronLeft :class="{ 'rotate-180': sidebarCollapsed }" class="w-4 h-4 transition-transform" />
            </button>
          </div>

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

          <!-- User Menu in Sidebar Footer -->
          <div class="mt-auto pt-4 border-t border-border">
            <div v-if="!sidebarCollapsed" class="relative">
              <button
                @click="showUserMenu = !showUserMenu"
                class="w-full flex items-center gap-2 p-2 text-text-muted hover:text-text transition-colors rounded-lg hover:bg-surface-hover"
              >
                <User class="h-4 w-4 flex-shrink-0" />
                <span class="text-sm truncate">{{ authStore.user?.name || 'User' }}</span>
              </button>
              
              <!-- User dropdown -->
              <div
                v-if="showUserMenu"
                class="absolute bottom-full mb-2 left-0 right-0 bg-surface border border-border rounded-lg shadow-lg py-2"
              >
                <div class="px-3 py-2 border-b border-border">
                  <p class="text-xs font-medium text-text truncate">{{ authStore.user?.name }}</p>
                  <p class="text-xs text-text-muted truncate">{{ authStore.user?.email }}</p>
                </div>
                <button
                  @click="handleLogout"
                  class="w-full px-3 py-2 text-left text-xs text-text-secondary hover:text-text hover:bg-surface-hover transition-colors flex items-center gap-2"
                >
                  <LogOut class="h-3 w-3" />
                  Logout
                </button>
              </div>
            </div>
            
            <!-- Collapsed user menu -->
            <div v-else class="relative">
              <button
                @click="showUserMenu = !showUserMenu"
                class="w-full flex items-center justify-center p-2 text-text-muted hover:text-text transition-colors rounded-lg hover:bg-surface-hover"
                :title="authStore.user?.name || 'User Menu'"
              >
                <User class="h-4 w-4" />
              </button>
              
              <!-- Collapsed dropdown -->
              <div
                v-if="showUserMenu"
                class="absolute bottom-full mb-2 left-full ml-2 w-48 bg-surface border border-border rounded-lg shadow-lg py-2"
              >
                <div class="px-3 py-2 border-b border-border">
                  <p class="text-xs font-medium text-text">{{ authStore.user?.name }}</p>
                  <p class="text-xs text-text-muted">{{ authStore.user?.email }}</p>
                </div>
                <button
                  @click="handleLogout"
                  class="w-full px-3 py-2 text-left text-xs text-text-secondary hover:text-text hover:bg-surface-hover transition-colors flex items-center gap-2"
                >
                  <LogOut class="h-3 w-3" />
                  Logout
                </button>
              </div>
            </div>
          </div>
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