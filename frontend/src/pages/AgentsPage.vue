<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center">
          <Bot class="w-8 h-8 text-green-400 mr-3" />
          <div>
            <h1 class="text-2xl font-bold text-white">AI Agents</h1>
            <p class="text-gray-400">Real-time transparency on your AI agents activity</p>
          </div>
        </div>
        <div class="flex items-center space-x-4">
          <div class="flex items-center text-sm text-gray-400">
            <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
            Live Feed
          </div>
          <button
            @click="refreshAgents"
            :disabled="isLoading"
            class="btn-control-primary"
          >
            <RefreshCw :class="{ 'animate-spin': isLoading }" class="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      <!-- Stats Cards - Workflow-based -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div class="bg-gray-900 border border-green-400/20 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-400 text-sm">Active Agents</p>
              <p class="text-2xl font-bold text-white">{{ agentWorkflows.length }}</p>
            </div>
            <Bot class="w-8 h-8 text-green-400" />
          </div>
        </div>
        
        <div class="bg-gray-900 border border-green-400/20 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-400 text-sm">With Data</p>
              <p class="text-2xl font-bold text-green-400">
                {{ agentWorkflows.filter(w => w.hasDetailedData).length }}
              </p>
            </div>
            <CheckCircle class="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div class="bg-gray-900 border border-green-400/20 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-400 text-sm">Total Executions</p>
              <p class="text-2xl font-bold text-white">
                {{ agentWorkflows.reduce((sum, w) => sum + w.totalExecutions, 0) }}
              </p>
            </div>
            <Clock class="w-8 h-8 text-yellow-400" />
          </div>
        </div>

        <div class="bg-gray-900 border border-green-400/20 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-400 text-sm">Recently Active</p>
              <p class="text-2xl font-bold text-white">
                {{ agentWorkflows.filter(w => w.lastActivity && isRecentlyActive(w.lastActivity)).length }}
              </p>
            </div>
            <Bot class="w-8 h-8 text-blue-400" />
          </div>
        </div>
      </div>

      <!-- Workflow Cards -->
      <div class="bg-gray-900 border border-green-400/20 rounded-lg p-6">
        <h2 class="text-xl font-semibold text-white mb-6">AI Agent Workflows</h2>
        
        <div v-if="agentWorkflows.length === 0" class="text-center py-12">
          <Bot class="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p class="text-gray-400">No AI agent workflows found</p>
          <p class="text-gray-500 text-sm mt-2">Active AI workflows will appear here</p>
        </div>
        
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div 
            v-for="workflow in agentWorkflows"
            :key="workflow.id"
            @click="handleViewWorkflow(workflow.id)"
            class="bg-black border border-gray-800 rounded-lg p-5 hover:border-green-400/30 transition-all cursor-pointer"
          >
            <!-- Header -->
            <div class="flex items-start justify-between mb-4">
              <div class="flex-1">
                <div class="flex items-center mb-2">
                  <Bot class="w-5 h-5 text-green-400 mr-2" />
                  <span 
                    class="px-2 py-1 rounded-full text-xs font-semibold"
                    :class="getWorkflowColor(workflow.name)"
                  >
                    {{ workflow.name }}
                  </span>
                </div>
              </div>
              <div class="flex items-center">
                <div 
                  v-if="workflow.hasDetailedData"
                  class="w-2 h-2 bg-green-400 rounded-full animate-pulse" 
                  title="Has detailed execution data"
                />
                <div 
                  v-else
                  class="w-2 h-2 bg-gray-600 rounded-full" 
                  title="No execution data available"
                />
              </div>
            </div>

            <!-- Stats -->
            <div class="grid grid-cols-2 gap-4 mb-4">
              <div>
                <div class="text-gray-400 text-xs mb-1">Executions</div>
                <div class="text-white text-lg font-semibold">{{ workflow.totalExecutions }}</div>
              </div>
              <div>
                <div class="text-gray-400 text-xs mb-1">Status</div>
                <div class="flex items-center">
                  <CheckCircle v-if="workflow.lastExecutionStatus === 'success'" class="w-4 h-4 text-green-400 mr-1" />
                  <XCircle v-else-if="workflow.lastExecutionStatus === 'error'" class="w-4 h-4 text-red-400 mr-1" />
                  <Clock v-else class="w-4 h-4 text-gray-400 mr-1" />
                  <span class="text-white text-sm">{{ workflow.lastExecutionStatus || 'inactive' }}</span>
                </div>
              </div>
            </div>

            <!-- Business Context Preview -->
            <div v-if="workflow.preview" class="mb-4 p-3 bg-gray-800/50 rounded border-l-2 border-green-400/50">
              <div class="text-gray-400 text-xs mb-2">Latest Activity</div>
              <div v-if="workflow.preview.senderEmail" class="flex items-center mb-1">
                <Mail class="w-3 h-3 text-blue-400 mr-2" />
                <span class="text-blue-400 text-sm truncate">{{ workflow.preview.senderEmail }}</span>
              </div>
              <div v-if="workflow.preview.subject" class="text-gray-300 text-sm truncate mb-1">
                "{{ workflow.preview.subject }}"
              </div>
              <div v-if="workflow.preview.classification" class="text-green-400 text-xs">
                {{ workflow.preview.classification }}
              </div>
            </div>

            <!-- Last Activity -->
            <div class="flex items-center justify-between text-xs text-gray-400">
              <div>
                {{ workflow.lastActivity ? formatTimeAgo(workflow.lastActivity) : 'No recent activity' }}
              </div>
              <button class="text-green-400 hover:text-green-300 font-medium">
                View Timeline →
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Agent Detail Modal placeholder -->
      <AgentDetailModal
        v-if="selectedWorkflowId"
        :workflow-id="selectedWorkflowId"
        :tenant-id="authStore.tenantId"
        :show="showAgentModal"
        @close="closeAgentModal"
      />
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  Bot, RefreshCw, CheckCircle, XCircle, Clock, Mail
} from 'lucide-vue-next'
import MainLayout from '../components/layout/MainLayout.vue'
import AgentDetailModal from '../components/agents/AgentDetailModal.vue'
import { useAuthStore } from '../stores/auth'
import { useUIStore } from '../stores/ui'
import type { AgentWorkflow } from '../types'

// Stores
const authStore = useAuthStore()
const uiStore = useUIStore()

// Local state
const isLoading = ref(false)
const selectedWorkflowId = ref<string | null>(null)
const showAgentModal = ref(false)

const agentWorkflows = ref<AgentWorkflow[]>([
  {
    id: '1',
    name: 'Email Processing Agent',
    status: 'active',
    lastActivity: new Date().toISOString(),
    lastExecutionId: 'exec_001',
    lastExecutionStatus: 'success',
    totalExecutions: 245,
    hasDetailedData: true,
    updatedAt: new Date().toISOString(),
    type: 'ai-agent',
    preview: {
      senderEmail: 'customer@example.com',
      subject: 'Richiesta informazioni prodotto',
      classification: 'Customer Support'
    }
  },
  {
    id: '2',
    name: 'Customer Service Bot',
    status: 'active',
    lastActivity: new Date(Date.now() - 1800000).toISOString(),
    lastExecutionId: 'exec_002',
    lastExecutionStatus: 'success',
    totalExecutions: 156,
    hasDetailedData: true,
    updatedAt: new Date().toISOString(),
    type: 'ai-agent',
    preview: {
      senderEmail: 'support@company.com',
      subject: 'Ticket di supporto automatico',
      classification: 'Support Automation'
    }
  }
])

// Methods
const refreshAgents = async () => {
  isLoading.value = true
  
  try {
    // In real implementation, fetch from our agents API
    // For now, simulate refresh
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Update last activity timestamps
    agentWorkflows.value.forEach(workflow => {
      if (Math.random() > 0.7) { // 30% chance of new activity
        workflow.lastActivity = new Date().toISOString()
        workflow.totalExecutions += Math.floor(Math.random() * 3)
      }
    })
    
    uiStore.showToast('Aggiornamento', 'AI Agents aggiornati', 'success')
  } catch (error: any) {
    console.error('Failed to load agents:', error)
    uiStore.showToast('Errore', 'Impossibile caricare AI agents', 'error')
  } finally {
    isLoading.value = false
  }
}

const handleViewWorkflow = (workflowId: string) => {
  selectedWorkflowId.value = workflowId
  showAgentModal.value = true
}

const closeAgentModal = () => {
  showAgentModal.value = false
  selectedWorkflowId.value = null
}

const getWorkflowColor = (workflowName: string) => {
  if (workflowName.includes('Email')) return 'text-blue-400 bg-blue-400/10'
  if (workflowName.includes('Bot')) return 'text-purple-400 bg-purple-400/10'
  if (workflowName.includes('AI')) return 'text-green-400 bg-green-400/10'
  return 'text-gray-400 bg-gray-400/10'
}

const formatTimeAgo = (timestamp: string) => {
  const now = new Date()
  const time = new Date(timestamp)
  const diffMs = now.getTime() - time.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
  return `${Math.floor(diffMins / 1440)}d ago`
}

const isRecentlyActive = (timestamp: string) => {
  const now = new Date()
  const time = new Date(timestamp)
  const diffHours = (now.getTime() - time.getTime()) / (1000 * 60 * 60)
  return diffHours < 24
}

// Lifecycle
onMounted(() => {
  refreshAgents()
})
</script>