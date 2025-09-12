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
          <!-- Compact User menu -->
          <div class="relative">
            <button
              @click="showUserMenu = !showUserMenu"
              class="flex items-center gap-1.5 text-text-muted hover:text-text transition-colors p-1"
            >
              <User class="h-4 w-4" />
              <span class="text-xs">{{ authStore.user?.email?.split('@')[0] || 'User' }}</span>
            </button>
            
            <!-- Compact dropdown -->
            <div
              v-if="showUserMenu"
              class="absolute right-0 mt-1 w-40 bg-surface border border-border rounded-lg shadow-lg py-1"
            >
              <div class="px-3 py-1.5 border-b border-border">
                <p class="text-xs font-medium text-text">{{ authStore.user?.email?.split('@')[0] }}</p>
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
        class="premium-glass border-r border-border flex-shrink-0 premium-scrollbar transition-all duration-300 fixed left-0 z-40 overflow-y-auto"
        style="top: 2.5rem; height: calc(100vh - 2.5rem);"
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
      <main 
        :class="sidebarCollapsed ? 'ml-16' : 'ml-52'"
        class="flex-1 transition-all duration-300"
      >
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
    
    <!-- Toast Container -->
    
    <!-- AI Chat removed - future implementation -->
    
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Menu, User, LogOut, LayoutDashboard, GitBranch, Play, BarChart3,
  Database, Bot, AlertTriangle, ChevronLeft, Settings
} from 'lucide-vue-next'
import { useAuthStore } from '../../stores/auth'
import { useUIStore } from '../../stores/ui'
// MilhenaChat import removed - AI agent discontinued

// Stores
const authStore = useAuthStore()
const uiStore = useUIStore()
const router = useRouter()

// Local state
const showUserMenu = ref(false)
const sidebarCollapsed = ref(true) // Start collapsed by default
const isMobile = ref(false)

// Check if mobile
const checkMobile = () => {
  isMobile.value = window.innerWidth < 1024
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

// Navigation items with role-based filtering (simplified to 2 roles)
const allNavigationItems = [
  { name: 'insights', path: '/insights', label: 'Insights', icon: LayoutDashboard, roles: ['admin', 'viewer'] },
  { name: 'command-center', path: '/command-center', label: 'Command Center', icon: Menu, roles: ['admin', 'viewer'] },
  { name: 'executions', path: '/executions', label: 'Executions', icon: Play, roles: ['admin', 'viewer'] },
  { name: 'settings', path: '/settings', label: 'Settings', icon: Settings, roles: ['admin'] }
]

// Filter navigation based on user role
const navigationItems = computed(() => {
  const userRole = authStore.user?.role || 'viewer'
  return allNavigationItems.filter(item => item.roles.includes(userRole))
})

// Methods
const handleLogout = async () => {
  try {
    await authStore.logout()
    uiStore.showToast('Logout', 'Disconnesso con successo', 'success')
    await router.push('/login')
    showUserMenu.value = false
  } catch (error) {
    console.error('Logout error:', error)
    // Force logout anyway
    await router.push('/login') 
    showUserMenu.value = false
  }
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