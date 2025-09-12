<template>
  <div class="min-h-screen bg-black">
    <!-- Header Unico -->
    <header class="bg-black sticky top-0 z-50 h-16 border-b border-gray-900">
      <div class="flex items-center justify-between h-full px-6">
        <div class="flex items-center gap-4">
          <button @click="sidebarOpen = !sidebarOpen" class="text-gray-400 hover:text-white">
            <Menu class="h-6 w-6" />
          </button>
          <h1 class="text-xl font-bold text-white">PilotPro Control Center</h1>
        </div>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span class="text-sm text-gray-400">Live</span>
          </div>
          <button @click="doLogout" class="text-gray-400 hover:text-white">
            <LogOut class="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>

    <div class="flex">
      <!-- Sidebar Unica -->
      <aside v-show="sidebarOpen" class="w-64 bg-gray-900 border-r border-gray-800 min-h-screen">
        <div class="p-6">
          <nav class="space-y-2">
            <router-link
              to="/dashboard"
              class="flex items-center gap-3 px-4 py-2 rounded-lg transition-colors"
              :class="$route.path === '/dashboard' ? 'bg-green-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'"
            >
              <LayoutDashboard class="h-5 w-5" />
              Dashboard
            </router-link>
            
            <router-link
              to="/workflows"
              class="flex items-center gap-3 px-4 py-2 rounded-lg transition-colors"
              :class="$route.path === '/workflows' ? 'bg-green-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'"
            >
              <GitBranch class="h-5 w-5" />
              Workflows
            </router-link>
            
            <router-link
              to="/executions"
              class="flex items-center gap-3 px-4 py-2 rounded-lg transition-colors"
              :class="$route.path === '/executions' ? 'bg-green-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'"
            >
              <Play class="h-5 w-5" />
              Executions
            </router-link>
            
            <router-link
              to="/stats"
              class="flex items-center gap-3 px-4 py-2 rounded-lg transition-colors"
              :class="$route.path === '/stats' ? 'bg-green-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'"
            >
              <BarChart3 class="h-5 w-5" />
              Statistics
            </router-link>
            
            <router-link
              to="/database"
              class="flex items-center gap-3 px-4 py-2 rounded-lg transition-colors"
              :class="$route.path === '/database' ? 'bg-green-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'"
            >
              <Database class="h-5 w-5" />
              Database
            </router-link>
            
            <!-- Removed security route - functionality not needed -->
            
            <router-link
              to="/agents"
              class="flex items-center gap-3 px-4 py-2 rounded-lg transition-colors"
              :class="$route.path === '/agents' ? 'bg-green-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'"
            >
              <Bot class="h-5 w-5" />
              AI Agents
            </router-link>
          </nav>
        </div>
      </aside>

      <!-- Content Area -->
      <main class="flex-1">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Menu, LogOut, LayoutDashboard, GitBranch, Play, BarChart3,
  Database, Bot
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const sidebarOpen = ref(true)

const doLogout = async () => {
  try {
    await authStore.logout()
    await router.push('/login')
  } catch (error) {
    console.error('Logout error:', error)
    await router.push('/login')
  }
}
</script>