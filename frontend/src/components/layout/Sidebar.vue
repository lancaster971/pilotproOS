<template>
  <aside v-show="sidebarOpen" class="sidebar-container w-64 min-h-screen relative">
    <!-- Background with glass effect -->
    <div class="sidebar-background absolute inset-0"></div>
    
    <!-- Content -->
    <div class="sidebar-content relative z-10">
      <!-- Header -->
      <div class="sidebar-header">
        <div class="sidebar-logo flex items-center">
          <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center mr-3" 
               style="background: linear-gradient(135deg, var(--color-primary), var(--color-primary-hover));">
            <span class="text-white text-sm font-bold">P</span>
          </div>
          <div>
            <h2 class="text-text text-sm font-semibold">PilotPro OS</h2>
            <p class="text-text-secondary text-xs">Command Center</p>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="sidebar-nav space-y-1">
        <router-link
          v-for="(item, index) in navigationItems"
          :key="item.path"
          :to="item.path"
          class="sidebar-nav-item group"
          :class="{ 'active': $route.path === item.path }"
          :style="{ animationDelay: `${index * 0.1}s` }"
        >
          <!-- Active indicator -->
          <div v-if="$route.path === item.path" class="sidebar-active-indicator"></div>
          
          <!-- Icon -->
          <div class="sidebar-nav-icon">
            <component :is="item.icon" class="w-5 h-5" />
          </div>
          
          <!-- Content -->
          <div class="flex-1 ml-3">
            <div class="sidebar-nav-label">{{ item.label }}</div>
            <div v-if="item.description" class="sidebar-nav-description">{{ item.description }}</div>
          </div>
          
          <!-- Badge -->
          <div v-if="item.badge" 
               class="sidebar-nav-badge"
               :class="{
                 'badge-new': item.badge.type === 'new',
                 'badge-ai': item.badge.type === 'ai',
                 'badge-default': item.badge.type === 'default'
               }">
            {{ item.badge.text }}
          </div>
        </router-link>
      </nav>

      <!-- Footer -->
      <div class="sidebar-footer mt-auto">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <div class="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
            <span class="text-xs text-text-muted">Sistema Online</span>
          </div>
          <button class="sidebar-toggle-btn">
            <ChevronLeft class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { 
  LayoutDashboard, GitBranch, Play, BarChart3,
  Database, ChevronLeft, Workflow
} from 'lucide-vue-next'

interface Props {
  sidebarOpen: boolean
}

interface NavigationItem {
  path: string
  label: string
  description?: string
  icon: any
  badge?: {
    text: string
    type: 'new' | 'ai' | 'default'
  }
}

defineProps<Props>()

// Navigation items con descrizioni e badge come nel vecchio progetto
const navigationItems = computed<NavigationItem[]>(() => [
  {
    path: '/insights',
    label: 'Insights',
    description: 'Panoramica generale',
    icon: LayoutDashboard,
    badge: { text: 'Live', type: 'new' }
  },
  {
    path: '/command-center', 
    label: 'Processi',
    description: 'Automazioni business',
    icon: Workflow
  },
  {
    path: '/executions',
    label: 'Esecuzioni', 
    description: 'Cronologia processi',
    icon: Play
  },
  {
    path: '/stats',
    label: 'Analytics',
    description: 'Metriche e KPI',
    icon: BarChart3
  },
  {
    path: '/database',
    label: 'Database',
    description: 'Gestione dati',
    icon: Database
  },
  // Removed security and scheduler routes - functionality not needed for business system
])
</script>