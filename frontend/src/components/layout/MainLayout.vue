<template>
  <div class="min-h-screen bg-black">
    <!-- Header - same pattern as n8n editor header -->
    <header class="bg-black sticky top-0 z-50 h-16 border-b border-gray-900">
      <div class="flex items-center justify-between h-full px-6">
        <div class="flex items-center gap-4">
          <button 
            @click="uiStore.toggleSidebar()" 
            class="text-gray-400 hover:text-white transition-colors"
          >
            <Menu class="h-6 w-6" />
          </button>
          <h1 class="text-xl font-bold text-white">PilotPro Control Center</h1>
        </div>
        
        <div class="flex items-center gap-4">
          <!-- Live indicator -->
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span class="text-sm text-gray-400">Live</span>
          </div>
          
          <!-- User menu -->
          <div class="relative">
            <button
              @click="showUserMenu = !showUserMenu"
              class="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <User class="h-5 w-5" />
              <span class="text-sm">{{ authStore.user?.name || 'User' }}</span>
            </button>
            
            <!-- User dropdown -->
            <div
              v-if="showUserMenu"
              class="absolute right-0 mt-2 w-48 bg-gray-900 border border-gray-700 rounded-lg shadow-lg py-2"
            >
              <div class="px-4 py-2 border-b border-gray-700">
                <p class="text-sm font-medium text-white">{{ authStore.user?.name }}</p>
                <p class="text-xs text-gray-400">{{ authStore.user?.email }}</p>
              </div>
              <button
                @click="handleLogout"
                class="w-full px-4 py-2 text-left text-sm text-gray-300 hover:text-white hover:bg-gray-800 transition-colors flex items-center gap-2"
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
      <!-- Simple Fixed Sidebar -->
      <aside class="w-60 bg-gray-900 border-r border-gray-700 min-h-screen flex-shrink-0">
        <div class="p-6">
          <!-- Logo -->
          <div class="flex items-center gap-3 mb-8 pb-4 border-b border-gray-800">
            <div class="w-8 h-8 bg-gradient-to-br from-green-400 to-green-600 rounded-lg flex items-center justify-center">
              <span class="text-white font-bold text-sm">P</span>
            </div>
            <div>
              <h1 class="text-white font-semibold text-sm">PilotPro</h1>
              <p class="text-gray-400 text-xs">Control Center</p>
            </div>
          </div>

          <!-- Navigation -->
          <nav class="space-y-2">
            <router-link
              v-for="item in navigationItems"
              :key="item.name"
              :to="item.path"
              class="flex items-center gap-3 px-4 py-2 rounded-lg transition-colors text-gray-300 hover:bg-gray-800 hover:text-white"
              :class="[$route.path === item.path ? 'bg-green-600 text-white' : '']"
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

// Stores
const authStore = useAuthStore()
const uiStore = useUIStore()
const router = useRouter()

// Local state
const showUserMenu = ref(false)

// Navigation items
const navigationItems = [
  { name: 'dashboard', path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { name: 'workflows', path: '/workflows', label: 'Workflows', icon: GitBranch },
  { name: 'workflow-visual', path: '/workflows/visual', label: 'Visual Flow', icon: GitBranch },
  { name: 'executions', path: '/executions', label: 'Executions', icon: Play },
  { name: 'stats', path: '/stats', label: 'Statistics', icon: BarChart3 },
  { name: 'database', path: '/database', label: 'Database', icon: Database },
  { name: 'security', path: '/security', label: 'Security', icon: Shield },
  { name: 'agents', path: '/agents', label: 'AI Agents', icon: Bot },
  { name: 'alerts', path: '/alerts', label: 'Alerts', icon: AlertTriangle },
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
/* Component-specific styles for layout */
.router-link-active {
  @apply bg-green-600 text-white;
}
</style>