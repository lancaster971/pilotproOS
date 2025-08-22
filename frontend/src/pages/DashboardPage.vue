<template>
  <div class="min-h-screen bg-black">
    <!-- Header -->
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
      <!-- Sidebar -->
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

      <!-- Main Content -->
      <main class="flex-1 p-6">
        <div class="space-y-6">
          <!-- Dashboard Content -->
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-3xl font-bold text-gradient">Dashboard - PilotProOS</h1>
              <p class="text-gray-400 mt-1">I tuoi dati business process automation</p>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span class="text-sm text-gray-400">Live</span>
            </div>
          </div>
          
          <!-- Stats Cards -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="control-card p-6 hover:shadow-2xl transition-all duration-300 border-gray-800 hover:border-green-500/30">
              <div class="flex items-center justify-between mb-4">
                <div class="h-12 w-12 rounded-lg bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center">
                  <GitBranch class="h-6 w-6 text-white" />
                </div>
                <div class="flex items-center gap-1">
                  <TrendingUp class="h-4 w-4 text-green-500" />
                  <span class="text-xs text-green-500">+5%</span>
                </div>
              </div>
              <div>
                <p class="text-2xl font-bold text-white">{{ workflowCount }}</p>
                <p class="text-sm text-gray-400">I Tuoi Workflows</p>
              </div>
            </div>
            
            <div class="control-card p-6 hover:shadow-2xl transition-all duration-300 border-gray-800 hover:border-green-500/30">
              <div class="flex items-center justify-between mb-4">
                <div class="h-12 w-12 rounded-lg bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center">
                  <Play class="h-6 w-6 text-white" />
                </div>
                <div class="flex items-center gap-1">
                  <TrendingUp class="h-4 w-4 text-green-500" />
                  <span class="text-xs text-green-500">+2%</span>
                </div>
              </div>
              <div>
                <p class="text-2xl font-bold text-white">{{ activeWorkflows }}</p>
                <p class="text-sm text-gray-400">Workflows Attivi</p>
              </div>
            </div>
            
            <div class="control-card p-6 hover:shadow-2xl transition-all duration-300 border-gray-800 hover:border-green-500/30">
              <div class="flex items-center justify-between mb-4">
                <div class="h-12 w-12 rounded-lg bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center">
                  <CheckCircle class="h-6 w-6 text-white" />
                </div>
                <div class="flex items-center gap-1">
                  <TrendingUp class="h-4 w-4 text-green-500" />
                  <span class="text-xs text-green-500">+0%</span>
                </div>
              </div>
              <div>
                <p class="text-2xl font-bold text-white">{{ executionsToday }}</p>
                <p class="text-sm text-gray-400">Esecuzioni (24h)</p>
              </div>
            </div>
            
            <div class="control-card p-6 hover:shadow-2xl transition-all duration-300 border-gray-800 hover:border-green-500/30">
              <div class="flex items-center justify-between mb-4">
                <div class="h-12 w-12 rounded-lg bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center">
                  <TrendingUp class="h-6 w-6 text-white" />
                </div>
              </div>
              <div>
                <p class="text-2xl font-bold text-white">{{ successRate }}%</p>
                <p class="text-sm text-gray-400">Success Rate</p>
              </div>
            </div>
          </div>
          
          <!-- Recent Activity -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="control-card p-6">
              <h3 class="text-lg font-semibold text-white mb-4">Recent Activity</h3>
              <div class="space-y-3">
                <div class="flex items-start gap-3 p-3 bg-gray-800/30 rounded-lg">
                  <div class="p-1.5 rounded-full bg-green-500/20">
                    <Play class="h-3 w-3 text-green-400" />
                  </div>
                  <div class="flex-1">
                    <p class="text-white text-sm">Workflow "TRY Backend" eseguito con successo</p>
                    <p class="text-xs text-gray-400">5 minutes ago</p>
                  </div>
                </div>
                <div class="flex items-start gap-3 p-3 bg-gray-800/30 rounded-lg">
                  <div class="p-1.5 rounded-full bg-purple-500/20">
                    <Database class="h-3 w-3 text-purple-400" />
                  </div>
                  <div class="flex-1">
                    <p class="text-white text-sm">Sincronizzazione database completata</p>
                    <p class="text-xs text-gray-400">30 minutes ago</p>
                  </div>
                </div>
                <div class="flex items-start gap-3 p-3 bg-gray-800/30 rounded-lg">
                  <div class="p-1.5 rounded-full bg-blue-500/20">
                    <GitBranch class="h-3 w-3 text-blue-400" />
                  </div>
                  <div class="flex-1">
                    <p class="text-white text-sm">Sistema PilotProOS inizializzato</p>
                    <p class="text-xs text-gray-400">1 hour ago</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="control-card p-6">
              <h3 class="text-lg font-semibold text-white mb-4">System Health</h3>
              <div class="space-y-4">
                <div class="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
                  <div class="flex items-center gap-3">
                    <div class="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                    <span class="text-white font-medium">Sistema Generale</span>
                  </div>
                  <span class="text-green-400 text-sm font-medium">Operativo</span>
                </div>

                <div class="space-y-2">
                  <div class="flex items-center justify-between p-2 rounded">
                    <div class="flex items-center gap-2">
                      <Database class="h-4 w-4 text-gray-400" />
                      <span class="text-white text-sm">PostgreSQL</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <div class="w-2 h-2 bg-green-500 rounded-full" />
                      <span class="text-xs text-green-400">Running</span>
                    </div>
                  </div>
                  
                  <div class="flex items-center justify-between p-2 rounded">
                    <div class="flex items-center gap-2">
                      <GitBranch class="h-4 w-4 text-gray-400" />
                      <span class="text-white text-sm">n8n Engine</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <div class="w-2 h-2 bg-green-500 rounded-full" />
                      <span class="text-xs text-green-400">Running</span>
                    </div>
                  </div>
                  
                  <div class="flex items-center justify-between p-2 rounded">
                    <div class="flex items-center gap-2">
                      <Server class="h-4 w-4 text-gray-400" />
                      <span class="text-white text-sm">Backend API</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <div class="w-2 h-2 bg-green-500 rounded-full" />
                      <span class="text-xs text-green-400">Running</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Menu, LogOut, LayoutDashboard, GitBranch, Play, BarChart3,
  Database, Shield, Bot, TrendingUp, CheckCircle, Server
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { businessAPI } from '../services/api'
import webSocketService from '../services/websocket'

// Stores
const authStore = useAuthStore()
const router = useRouter()

// Local state
const sidebarOpen = ref(true)
const workflowCount = ref(0)
const activeWorkflows = ref(0)
const executionsToday = ref(0)
const successRate = ref(0)

// Methods
const doLogout = () => {
  authStore.logout()
  router.push('/login')
}

const loadData = async () => {
  try {
    console.log('🔄 Loading ALL REAL data from PilotProOS backend...')
    
    // Load workflows data
    const processesResponse = await fetch('http://localhost:3001/api/business/processes')
    if (!processesResponse.ok) {
      throw new Error(`Processes API error: ${processesResponse.status}`)
    }
    const processesData = await processesResponse.json()
    console.log('✅ Processes data:', processesData)
    
    // Load analytics data 
    const analyticsResponse = await fetch('http://localhost:3001/api/business/analytics')
    if (!analyticsResponse.ok) {
      throw new Error(`Analytics API error: ${analyticsResponse.status}`)
    }
    const analyticsData = await analyticsResponse.json()
    console.log('✅ Analytics data:', analyticsData)
    
    // Load automation insights
    const insightsResponse = await fetch('http://localhost:3001/api/business/automation-insights')
    if (!insightsResponse.ok) {
      throw new Error(`Insights API error: ${insightsResponse.status}`)
    }
    const insightsData = await insightsResponse.json()
    console.log('✅ Insights data:', insightsData)
    
    // Use ALL REAL data from backend
    workflowCount.value = processesData.total || 0
    activeWorkflows.value = processesData.summary?.active || 0
    
    // Update with analytics data
    executionsToday.value = analyticsData.overview?.totalExecutions || 0
    successRate.value = analyticsData.overview?.successRate || 0
    
    console.log(`📊 Complete real stats: ${workflowCount.value} workflows, ${activeWorkflows.value} active, ${executionsToday.value} executions, ${successRate.value}% success`)
    
  } catch (error: any) {
    console.error('❌ Backend API calls failed:', error)
    workflowCount.value = 0
    activeWorkflows.value = 0
  }
}

// Lifecycle
onMounted(() => {
  loadData()
  
  // Start auto-refresh every 5 seconds
  webSocketService.startAutoRefresh('dashboard', loadData, 5000)
  
  // Listen for real-time events
  window.addEventListener('stats:update', loadData)
  window.addEventListener('workflow:updated', loadData)
})

onUnmounted(() => {
  // Stop auto-refresh when leaving the page
  webSocketService.stopAutoRefresh('dashboard')
  
  // Clean up event listeners
  window.removeEventListener('stats:update', loadData)
  window.removeEventListener('workflow:updated', loadData)
})
</script>