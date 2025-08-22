<template>
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
        
        <router-link
          to="/security"
          class="flex items-center gap-3 px-4 py-2 rounded-lg transition-colors"
          :class="$route.path === '/security' ? 'bg-green-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'"
        >
          <Shield class="h-5 w-5" />
          Security
        </router-link>
        
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
</template>

<script setup lang="ts">
import { 
  LayoutDashboard, GitBranch, Play, BarChart3,
  Database, Shield, Bot
} from 'lucide-vue-next'

interface Props {
  sidebarOpen: boolean
}

defineProps<Props>()
</script>