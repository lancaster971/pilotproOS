<template>
  <div class="control-card p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-white">Recent Activity</h3>
      <button 
        @click="refreshActivity"
        class="text-gray-400 hover:text-white transition-colors"
      >
        <RefreshCw :class="{ 'animate-spin': isLoading }" class="h-4 w-4" />
      </button>
    </div>
    
    <div class="space-y-3">
      <div v-if="isLoading" class="text-center py-4">
        <Loader2 class="h-6 w-6 animate-spin text-green-400 mx-auto" />
        <p class="text-gray-500 text-sm mt-2">Caricamento attività...</p>
      </div>
      
      <div v-else-if="activities.length === 0" class="text-center py-8 text-gray-500">
        <Activity class="h-12 w-12 mx-auto mb-4 text-gray-600" />
        <p>Nessuna attività recente</p>
      </div>
      
      <div
        v-for="activity in activities"
        :key="activity.id"
        class="flex items-start gap-3 p-3 bg-gray-800/30 rounded-lg hover:bg-gray-800/50 transition-colors"
      >
        <div 
          class="p-1.5 rounded-full"
          :class="getActivityColor(activity.type)"
        >
          <component :is="getActivityIcon(activity.type)" class="h-3 w-3" />
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-white text-sm">{{ activity.message }}</p>
          <p class="text-xs text-gray-400">{{ formatRelativeTime(activity.timestamp) }}</p>
        </div>
        <span 
          class="px-2 py-1 rounded text-xs font-medium"
          :class="getActivityBadge(activity.type)"
        >
          {{ activity.type }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { 
  RefreshCw, Loader2, Activity, CheckCircle, XCircle, 
  Play, GitBranch, Database
} from 'lucide-vue-next'

// Types
interface ActivityItem {
  id: string
  type: 'workflow_executed' | 'workflow_created' | 'execution_failed' | 'sync_completed'
  message: string
  timestamp: number
  workflowId?: string
  workflowName?: string
}

// Local state
const isLoading = ref(false)
const activities = ref<ActivityItem[]>([])

// Methods
const refreshActivity = async () => {
  isLoading.value = true
  
  try {
    // Mock data for demo
    activities.value = [
      {
        id: '1',
        type: 'workflow_executed',
        message: 'Workflow "TRY Backend" eseguito con successo',
        timestamp: Date.now() - 300000,
        workflowId: '1',
        workflowName: 'TRY Backend'
      },
      {
        id: '2',
        type: 'sync_completed',
        message: 'Sincronizzazione database completata',
        timestamp: Date.now() - 1800000,
      },
      {
        id: '3',
        type: 'workflow_created',
        message: 'Sistema PilotProOS inizializzato',
        timestamp: Date.now() - 3600000,
      }
    ]
  } catch (error) {
    console.error('Failed to load recent activity:', error)
  } finally {
    isLoading.value = false
  }
}

const getActivityIcon = (type: string) => {
  switch (type) {
    case 'workflow_executed': return Play
    case 'workflow_created': return GitBranch
    case 'execution_failed': return XCircle
    case 'sync_completed': return Database
    default: return Activity
  }
}

const getActivityColor = (type: string) => {
  switch (type) {
    case 'workflow_executed': return 'bg-green-500/20'
    case 'workflow_created': return 'bg-blue-500/20'
    case 'execution_failed': return 'bg-red-500/20'
    case 'sync_completed': return 'bg-purple-500/20'
    default: return 'bg-gray-500/20'
  }
}

const getActivityBadge = (type: string) => {
  switch (type) {
    case 'workflow_executed': return 'bg-green-500/20 text-green-400'
    case 'workflow_created': return 'bg-blue-500/20 text-blue-400'
    case 'execution_failed': return 'bg-red-500/20 text-red-400'
    case 'sync_completed': return 'bg-purple-500/20 text-purple-400'
    default: return 'bg-gray-500/20 text-gray-400'
  }
}

const formatRelativeTime = (timestamp: number) => {
  const now = Date.now()
  const diffMins = Math.floor((now - timestamp) / 60000)
  
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
  return `${Math.floor(diffMins / 1440)}d ago`
}

// Lifecycle
onMounted(() => {
  refreshActivity()
})
</script>