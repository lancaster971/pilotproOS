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
      <!-- Premium Enterprise Sidebar -->
      <aside
        :class="sidebarCollapsed ? 'w-16' : 'w-64'"
        class="flex-shrink-0 fixed left-0 top-10 h-screen bg-gray-900 z-40"
        style="height: calc(100vh - 2.5rem);"
      >
        <!-- Glass morphism backdrop -->
        <div class="sidebar-backdrop-main"></div>

        <!-- Content -->
        <div class="sidebar-content-main">
          <!-- Navigation -->
          <nav class="sidebar-nav-main">
            <router-link
              v-for="(item, index) in navigationItems"
              :key="item.name"
              :to="item.path"
              class="nav-item-main"
              :class="{ 'nav-item-active-main': $route.path === item.path }"
              :style="{ '--delay': `${index * 50}ms` }"
              :title="sidebarCollapsed ? item.label : ''"
            >
              <!-- Active indicator -->
              <div v-if="$route.path === item.path" class="active-indicator-main"></div>

              <!-- Icon wrapper -->
              <div class="nav-icon-wrapper-main">
                <div class="nav-icon-bg-main"></div>
                <component :is="item.icon" class="nav-icon-main" />
              </div>

              <!-- Content -->
              <div v-if="!sidebarCollapsed" class="nav-content-main">
                <div class="nav-label-main">{{ item.label }}</div>
                <div v-if="item.description" class="nav-description-main">{{ item.description }}</div>
              </div>

              <!-- Badge -->
              <div v-if="!sidebarCollapsed && item.badge"
                   class="nav-badge-main"
                   :class="`badge-${item.badge.type}-main`">
                <span class="badge-text-main">{{ item.badge.text }}</span>
                <div v-if="item.badge.type === 'new'" class="badge-pulse-main"></div>
              </div>
            </router-link>
          </nav>

          <!-- Footer -->
          <div class="sidebar-footer-main">
            <div class="status-container-main">
              <div v-if="!sidebarCollapsed" class="status-indicator-main">
                <div class="status-dot-main"></div>
                <span class="status-text-main">Stack Running</span>
              </div>
              <div v-else class="flex justify-center">
                <div class="status-dot-main"></div>
              </div>
            </div>
          </div>
        </div>

      </aside>

      <!-- Center Toggle Button - Just White Arrow -->
      <div
        @click="sidebarCollapsed = !sidebarCollapsed"
        :style="{
          position: 'fixed',
          left: sidebarCollapsed ? '60px' : '252px',
          top: '50%',
          transform: 'translateY(-50%)',
          zIndex: 100,
          transition: 'left 0.3s cubic-bezier(0.25, 0.1, 0.25, 1)',
          cursor: 'pointer'
        }"
        class="hover:scale-110 transition-transform"
        :title="sidebarCollapsed ? 'Espandi sidebar' : 'Comprimi sidebar'"
      >
        <ChevronLeft v-if="!sidebarCollapsed" class="w-6 h-6 text-white drop-shadow-lg" />
        <ChevronRight v-else class="w-6 h-6 text-white drop-shadow-lg" />
      </div>

      <!-- Main content area -->
      <main
        class="flex-1"
        :style="{
          marginLeft: sidebarCollapsed ? '64px' : '256px',
          transition: 'margin-left 0.4s cubic-bezier(0.25, 0.1, 0.25, 1)',
          willChange: 'margin-left'
        }"
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
  Database, Bot, AlertTriangle, ChevronLeft, ChevronRight, Settings, Zap, Terminal, Cpu, Brain, Workflow
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
const sidebarCollapsed = ref(false) // Show sidebar by default
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
  {
    name: 'insights',
    path: '/insights',
    label: 'Insights',
    description: 'Business intelligence & analytics',
    icon: LayoutDashboard,
    roles: ['admin', 'viewer']
  },
  {
    name: 'command-center',
    path: '/command-center',
    label: 'AI Automation',
    description: 'Workflow automation & AI agents',
    icon: Workflow,
    roles: ['admin', 'viewer']
  },
  {
    name: 'executions',
    path: '/executions',
    label: 'Executions',
    description: 'Process execution history & logs',
    icon: Play,
    roles: ['admin', 'viewer']
  },
  {
    name: 'settings',
    path: '/settings',
    label: 'Impostazioni',
    description: 'System configuration & user management',
    icon: Settings,
    roles: ['admin']
  }
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
/* Premium Sidebar Styles - Enterprise Design */

/* Container principale */
.sidebar-container-main {
  flex-shrink: 0;
  transition: width 0.4s cubic-bezier(0.25, 0.1, 0.25, 1);
  will-change: width;
  height: calc(100vh - 2.5rem);
  position: relative;
  isolation: isolate;
  transform: translateZ(0); /* Force GPU acceleration */
}

.sidebar-expanded {
  width: 16rem; /* w-64 */
}

.sidebar-collapsed {
  width: 4rem; /* w-16 */
}

/* Backdrop con glass morphism premium */
.sidebar-backdrop-main {
  @apply absolute inset-0;
  background: linear-gradient(
    180deg,
    rgba(15, 15, 15, 0.95) 0%,
    rgba(15, 15, 15, 0.98) 50%,
    rgba(10, 10, 10, 0.99) 100%
  );
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-right: 1px solid rgba(31, 41, 55, 0.3);
  box-shadow:
    4px 0 24px rgba(0, 0, 0, 0.4),
    inset -1px 0 0 rgba(255, 255, 255, 0.05);
}

/* Content */
.sidebar-content-main {
  @apply relative z-10 flex flex-col h-full overflow-y-auto;
}

/* Header con logo */
.sidebar-header-main {
  @apply p-6 pb-4;
  border-bottom: 1px solid rgba(31, 41, 55, 0.2);
  background: linear-gradient(180deg, rgba(31, 41, 55, 0.1) 0%, transparent 100%);
  animation: fadeInDown 0.4s cubic-bezier(0.25, 0.1, 0.25, 1);
  transform: translateZ(0);
}

.sidebar-logo-main {
  @apply flex items-center gap-3;
  animation: fadeInScale 0.5s cubic-bezier(0.25, 0.1, 0.25, 1);
  transform: translateZ(0);
}

/* Logo icon con pulse effect */
.logo-icon-main {
  @apply relative w-10 h-10 flex items-center justify-center;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  border-radius: 12px;
  box-shadow:
    0 4px 12px rgba(59, 130, 246, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.logo-pulse-main {
  @apply absolute inset-0;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  border-radius: 12px;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  opacity: 0.4;
}

.logo-svg-main {
  @apply w-6 h-6 text-white relative z-10;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
}

/* Logo text */
.logo-title-main {
  @apply text-white text-base font-semibold tracking-tight;
  background: linear-gradient(90deg, #ffffff 0%, #e5e7eb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-subtitle-main {
  @apply text-xs font-medium;
  color: rgba(148, 163, 184, 0.8);
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

/* Navigation */
.sidebar-nav-main {
  @apply flex-1 px-3 pt-6 py-4 space-y-1;
}

/* Nav items */
.nav-item-main {
  @apply relative flex items-center px-3 py-2.5 rounded-xl;
  background: transparent;
  animation: slideInLeft var(--delay) cubic-bezier(0.25, 0.1, 0.25, 1) backwards;
  border: 1px solid transparent;
  transition:
    background-color 0.2s cubic-bezier(0.25, 0.1, 0.25, 1),
    transform 0.2s cubic-bezier(0.25, 0.1, 0.25, 1),
    border-color 0.2s cubic-bezier(0.25, 0.1, 0.25, 1);
  will-change: transform, background-color;
  transform: translateZ(0); /* GPU acceleration */
}

.nav-item-main:hover {
  background: rgba(31, 41, 55, 0.2);
  transform: translateX(3px) translateZ(0);
  border-color: rgba(59, 130, 246, 0.1);
}

.nav-item-active-main {
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%) !important;
  border: 1px solid rgba(59, 130, 246, 0.2) !important;
  box-shadow:
    0 0 20px rgba(59, 130, 246, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

/* Active indicator semplice */
.active-indicator-main {
  @apply absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-full;
  background: #3b82f6;
}

/* Icon wrapper */
.nav-icon-wrapper-main {
  @apply relative flex items-center justify-center w-9 h-9 rounded-lg;
}

.nav-icon-bg-main {
  @apply absolute inset-0 rounded-lg opacity-0;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
  transition: opacity 0.25s cubic-bezier(0.25, 0.1, 0.25, 1);
  will-change: opacity;
}

.nav-item-main:hover .nav-icon-bg-main,
.nav-item-active-main .nav-icon-bg-main {
  opacity: 1;
}

.nav-icon-main {
  @apply w-5 h-5 relative z-10;
  color: rgba(148, 163, 184, 0.8);
  transition:
    color 0.2s cubic-bezier(0.25, 0.1, 0.25, 1),
    transform 0.2s cubic-bezier(0.25, 0.1, 0.25, 1);
  will-change: transform, color;
  transform: translateZ(0);
}

.nav-item-main:hover .nav-icon-main {
  color: #93bbfc;
  transform: scale(1.1);
}

.nav-item-active-main .nav-icon-main {
  color: #3b82f6;
  filter: drop-shadow(0 0 4px rgba(59, 130, 246, 0.4));
}

/* Content area */
.nav-content-main {
  @apply flex-1 ml-3;
}

.nav-label-main {
  @apply text-sm font-medium;
  color: rgba(229, 231, 235, 0.9);
  transition: color 0.2s cubic-bezier(0.25, 0.1, 0.25, 1);
  will-change: color;
}

.nav-item-main:hover .nav-label-main {
  color: #ffffff;
}

.nav-item-active-main .nav-label-main {
  color: #ffffff;
  font-weight: 600;
}

.nav-description-main {
  @apply text-xs mt-0.5;
  color: rgba(148, 163, 184, 0.6);
}

/* Badges */
.nav-badge-main {
  @apply relative px-2 py-0.5 rounded-full text-xs font-semibold;
  animation: fadeIn 0.3s ease;
}

.badge-new-main {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.1) 100%);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #10b981;
}

.badge-pulse-main {
  @apply absolute inset-0 rounded-full;
  background: rgba(16, 185, 129, 0.4);
  animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
}

/* Footer */
.sidebar-footer-main {
  @apply p-4 mt-auto;
  border-top: 1px solid rgba(31, 41, 55, 0.2);
  background: linear-gradient(180deg, transparent 0%, rgba(10, 10, 10, 0.5) 100%);
}

.status-container-main {
  @apply flex items-center justify-between;
}

.status-indicator-main {
  @apply flex items-center gap-2;
}

.status-dot-main {
  @apply w-2 h-2 rounded-full;
  background: linear-gradient(135deg, #10b981 0%, #06b6d4 100%);
  box-shadow:
    0 0 8px rgba(16, 185, 129, 0.6),
    0 0 16px rgba(16, 185, 129, 0.3);
  animation: pulse 2s ease-in-out infinite;
}

.status-text-main {
  @apply text-xs font-medium;
  color: rgba(148, 163, 184, 0.8);
  letter-spacing: 0.5px;
}

/* Animations */
@keyframes fadeInDown {
  0% { opacity: 0; transform: translateY(-10px); }
  100% { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInScale {
  0% { opacity: 0; transform: scale(0.95); }
  100% { opacity: 1; transform: scale(1); }
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.05); }
}

@keyframes glow {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes ping {
  75%, 100% { transform: scale(2); opacity: 0; }
}

@keyframes fadeIn {
  0% { opacity: 0; }
  100% { opacity: 1; }
}

@keyframes slideInLeft {
  0% {
    opacity: 0;
    transform: translateX(-15px) translateZ(0);
  }
  100% {
    opacity: 1;
    transform: translateX(0) translateZ(0);
  }
}

/* Scrollbar */
.sidebar-content-main::-webkit-scrollbar {
  width: 4px;
}

.sidebar-content-main::-webkit-scrollbar-track {
  background: rgba(31, 41, 55, 0.2);
  border-radius: 2px;
}

.sidebar-content-main::-webkit-scrollbar-thumb {
  background: rgba(107, 114, 128, 0.3);
  border-radius: 2px;
}

.sidebar-content-main::-webkit-scrollbar-thumb:hover {
  background: rgba(107, 114, 128, 0.5);
}

</style>