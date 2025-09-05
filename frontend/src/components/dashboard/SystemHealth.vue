<template>
  <div class="control-card p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-white">System Health</h3>
      <button 
        @click="refreshHealth"
        class="text-gray-400 hover:text-white transition-colors"
      >
        <Icon icon="lucide:refresh-cw" :class="{ 'animate-spin': isLoading }" class="h-4 w-4" />
      </button>
    </div>

    <div class="space-y-4">
      <!-- Overall Status -->
      <div class="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg">
        <div class="flex items-center gap-3">
          <div 
            class="w-3 h-3 rounded-full"
            :class="overallStatus === 'healthy' ? 'bg-green-500 animate-pulse' : 'bg-red-500'"
          />
          <span class="text-white font-medium">Sistema Generale</span>
        </div>
        <span 
          :class="overallStatus === 'healthy' ? 'text-green-400' : 'text-red-400'"
          class="text-sm font-medium"
        >
          {{ overallStatus === 'healthy' ? 'Operativo' : 'Problemi' }}
        </span>
      </div>

      <!-- Service Status -->
      <div class="space-y-2">
        <div
          v-for="service in services"
          :key="service.name"
          class="flex items-center justify-between p-2 rounded"
        >
          <div class="flex items-center gap-2">
            <Icon :icon="service.icon" class="h-4 w-4 text-gray-400" />
            <span class="text-white text-sm">{{ service.name }}</span>
          </div>
          <div class="flex items-center gap-2">
            <div 
              class="w-2 h-2 rounded-full"
              :class="service.status === 'running' ? 'bg-green-500' : 'bg-red-500'"
            />
            <span 
              class="text-xs"
              :class="service.status === 'running' ? 'text-green-400' : 'text-red-400'"
            >
              {{ service.status === 'running' ? 'Running' : 'Down' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Performance Metrics -->
      <div class="pt-4 border-t border-gray-800">
        <h4 class="text-sm font-medium text-gray-300 mb-3">Performance</h4>
        <div class="space-y-2">
          <div class="flex justify-between items-center text-sm">
            <span class="text-gray-400">CPU Usage</span>
            <div class="flex items-center gap-2">
              <div class="w-16 bg-gray-800 rounded-full h-1">
                <div 
                  class="bg-green-500 h-1 rounded-full transition-all duration-500"
                  :style="{ width: `${cpuUsage}%` }"
                />
              </div>
              <span class="text-white font-mono text-xs w-8">{{ cpuUsage }}%</span>
            </div>
          </div>
          
          <div class="flex justify-between items-center text-sm">
            <span class="text-gray-400">Memory Usage</span>
            <div class="flex items-center gap-2">
              <div class="w-16 bg-gray-800 rounded-full h-1">
                <div 
                  class="bg-blue-500 h-1 rounded-full transition-all duration-500"
                  :style="{ width: `${memoryUsage}%` }"
                />
              </div>
              <span class="text-white font-mono text-xs w-8">{{ memoryUsage }}%</span>
            </div>
          </div>
          
          <div class="flex justify-between items-center text-sm">
            <span class="text-gray-400">API Response</span>
            <span class="text-green-400 font-mono text-xs">{{ apiResponse }}ms</span>
          </div>
        </div>
      </div>

      <!-- Uptime -->
      <div class="pt-4 border-t border-gray-800">
        <div class="flex justify-between items-center">
          <span class="text-gray-400 text-sm">System Uptime</span>
          <span class="text-white font-medium text-sm">{{ formatUptime(uptime) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Icon } from '@iconify/vue'
import { businessAPI } from '../../services/api'

// Local state
const isLoading = ref(false)
const overallStatus = ref<'healthy' | 'degraded' | 'down'>('healthy')
const cpuUsage = ref(45)
const memoryUsage = ref(62)
const apiResponse = ref(89)
const uptime = ref(15 * 24 * 3600) // 15 days in seconds

const services = ref([
  { name: 'PostgreSQL', icon: 'lucide:database', status: 'running' },
  { name: 'n8n Engine', icon: 'lucide:git-branch', status: 'running' },
  { name: 'Backend API', icon: 'lucide:server', status: 'running' },
  { name: 'Scheduler', icon: 'lucide:activity', status: 'running' },
])

// Methods
const refreshHealth = async () => {
  isLoading.value = true
  
  try {
    const response = await businessAPI.getHealth()
    const healthData = response.data
    
    // Update overall status based on backend health
    overallStatus.value = healthData.status === 'healthy' ? 'healthy' : 'degraded'
    
    // Update service status based on backend response
    if (healthData.services) {
      services.value.forEach(service => {
        switch (service.name) {
          case 'PostgreSQL':
            service.status = healthData.services.database === 'connected' ? 'running' : 'down'
            break
          case 'Backend API':
            service.status = healthData.services.apiServer === 'running' ? 'running' : 'down'
            break
          case 'n8n Engine':
            service.status = healthData.services.processEngine === 'reachable' ? 'running' : 'down'
            break
        }
      })
    }
    
    // Simulate some realistic metrics
    cpuUsage.value = Math.round(Math.random() * 30 + 30) // 30-60%
    memoryUsage.value = Math.round(Math.random() * 40 + 40) // 40-80%
    apiResponse.value = Math.round(Math.random() * 100 + 50) // 50-150ms
    
  } catch (error) {
    console.error('Failed to refresh health:', error)
    overallStatus.value = 'degraded'
  } finally {
    isLoading.value = false
  }
}

const formatUptime = (seconds: number) => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (days > 0) return `${days}d ${hours}h`
  if (hours > 0) return `${hours}h ${minutes}m`
  return `${minutes}m`
}

// Auto-refresh health data every 30 seconds
let healthInterval: NodeJS.Timeout

onMounted(() => {
  refreshHealth()
  healthInterval = setInterval(refreshHealth, 30000)
})

onUnmounted(() => {
  if (healthInterval) {
    clearInterval(healthInterval)
  }
})
</script>