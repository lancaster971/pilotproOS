<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="$emit('close')"
    >
      <div class="bg-gray-900 border border-green-400/20 rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-gray-800">
          <div class="flex items-center">
            <GitBranch class="w-6 h-6 text-green-400 mr-3" />
            <div>
              <h2 class="text-xl font-semibold text-white">
                {{ workflow.name }}
              </h2>
              <p class="text-gray-400 text-sm">
                Workflow ID: {{ workflow.id }}
              </p>
            </div>
          </div>
          <button
            @click="$emit('close')"
            class="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded transition-colors"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-6">
          <div class="space-y-6">
            <!-- Overview -->
            <div class="bg-black rounded-lg border border-gray-800 p-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-white font-medium">Workflow Summary</span>
                <div class="flex items-center">
                  <CheckCircle v-if="workflow.active" class="w-5 h-5 text-green-400 mr-2" />
                  <XCircle v-else class="w-5 h-5 text-red-400 mr-2" />
                  <span :class="workflow.active ? 'text-green-400' : 'text-red-400'">
                    {{ workflow.active ? 'Active' : 'Inactive' }}
                  </span>
                </div>
              </div>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span class="text-gray-400">Nodes</span>
                  <p class="text-white font-medium">{{ workflow.node_count }}</p>
                </div>
                <div>
                  <span class="text-gray-400">Executions</span>
                  <p class="text-white font-medium">{{ workflow.execution_count }}</p>
                </div>
                <div>
                  <span class="text-gray-400">Created</span>
                  <p class="text-white font-medium">{{ formatDate(workflow.created_at) }}</p>
                </div>
                <div>
                  <span class="text-gray-400">Updated</span>
                  <p class="text-white font-medium">{{ formatDate(workflow.updated_at) }}</p>
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-4">
              <button
                @click="toggleWorkflowStatus"
                :disabled="workflow.is_archived"
                class="btn-control-primary"
                :class="{ 'opacity-50 cursor-not-allowed': workflow.is_archived }"
              >
                <Play v-if="!workflow.active" class="h-4 w-4" />
                <Pause v-else class="h-4 w-4" />
                {{ workflow.active ? 'Disattiva' : 'Attiva' }}
              </button>
              
              <button class="btn-control">
                <Edit class="h-4 w-4" />
                Modifica
              </button>
              
              <button class="btn-control">
                <Copy class="h-4 w-4" />
                Duplica
              </button>
              
              <button 
                v-if="!workflow.is_archived"
                class="btn-control text-red-400 border-red-500/30 hover:border-red-500 hover:bg-red-500/10"
              >
                <Archive class="h-4 w-4" />
                Archivia
              </button>
            </div>

            <!-- Workflow Canvas Preview -->
            <div class="control-card p-6">
              <h3 class="text-lg font-semibold text-white mb-4">Workflow Structure</h3>
              <div class="bg-gray-800 rounded-lg p-4 h-64 flex items-center justify-center">
                <div class="text-center">
                  <GitBranch class="h-12 w-12 mx-auto mb-2 text-gray-600" />
                  <p class="text-gray-400">Workflow canvas preview</p>
                  <p class="text-xs text-gray-500">{{ workflow.node_count }} nodes connected</p>
                </div>
              </div>
            </div>

            <!-- Recent Executions -->
            <div class="control-card p-6">
              <h3 class="text-lg font-semibold text-white mb-4">Recent Executions</h3>
              <div class="space-y-2">
                <div v-for="i in 3" :key="i" class="flex items-center justify-between p-3 bg-gray-800/50 rounded">
                  <div class="flex items-center gap-2">
                    <CheckCircle class="h-4 w-4 text-green-400" />
                    <span class="text-white text-sm">Execution #{{ 1000 + i }}</span>
                  </div>
                  <div class="text-right">
                    <p class="text-xs text-gray-400">{{ formatRelativeTime(Date.now() - i * 3600000) }}</p>
                    <p class="text-xs text-gray-500">Duration: {{ Math.round(Math.random() * 5000) }}ms</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { 
  X, GitBranch, CheckCircle, XCircle, Play, Pause, Edit, 
  Copy, Archive
} from 'lucide-vue-next'
import { useWorkflowsStore } from '../../stores/workflows'
import { useUIStore } from '../../stores/ui'
import type { Workflow } from '../../types'

// Props
interface Props {
  workflow: Workflow
  show: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  close: []
}>()

// Stores
const workflowsStore = useWorkflowsStore()
const uiStore = useUIStore()

// Methods
const toggleWorkflowStatus = async () => {
  try {
    await workflowsStore.toggleWorkflow(props.workflow)
    uiStore.showToast(
      'Workflow',
      `${props.workflow.active ? 'Disattivato' : 'Attivato'}: ${props.workflow.name}`,
      'success'
    )
  } catch (error: any) {
    uiStore.showToast('Errore', 'Impossibile modificare workflow', 'error')
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('it-IT')
}

const formatRelativeTime = (timestamp: number) => {
  const now = Date.now()
  const diffMins = Math.floor((now - timestamp) / 60000)
  
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
  return `${Math.floor(diffMins / 1440)}d ago`
}
</script>