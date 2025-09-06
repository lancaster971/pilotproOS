<template>
  <AppLayout>
    <div class="p-6">
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
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { TrendingUp, CheckCircle, Server, GitBranch, Play, Database } from 'lucide-vue-next'
import AppLayout from '../layouts/AppLayout.vue'
import { businessAPI } from '../services/api-client'
import webSocketService from '../services/websocket'

// Local state
const workflowCount = ref(0)
const activeWorkflows = ref(0)
const executionsToday = ref(0)
const successRate = ref(0)

const loadData = async () => {
  try {
    console.log('🔄 Loading REAL data from PilotProOS backend...')
    
    // Use OFETCH API client for processes
    const processesData = await businessAPI.getProcesses()
    workflowCount.value = processesData.total || processesData.data?.length || 0
    activeWorkflows.value = processesData.summary?.active || 0
    
    // Use OFETCH API client for analytics
    const analyticsData = await businessAPI.getAnalytics()
    console.log('✅ Analytics data loaded:', analyticsData)
    executionsToday.value = analyticsData.overview?.totalExecutions || 0
    successRate.value = analyticsData.overview?.successRate || 0
    
    console.log(`📊 Dashboard loaded: ${workflowCount.value} workflows, ${activeWorkflows.value} active`)
    
  } catch (error: any) {
    console.error('❌ Backend connection failed:', error.message)
  }
}

onMounted(() => {
  loadData()
  webSocketService.startAutoRefresh('dashboard', loadData, 5000)
  window.addEventListener('stats:update', loadData)
  window.addEventListener('workflow:updated', loadData)
})

onUnmounted(() => {
  webSocketService.stopAutoRefresh('dashboard')
  window.removeEventListener('stats:update', loadData)
  window.removeEventListener('workflow:updated', loadData)
})
</script>