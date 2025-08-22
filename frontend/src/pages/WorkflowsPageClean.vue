<template>
  <AppLayout>
    <div class="p-6">
      <div class="space-y-6">
        <!-- Workflows Header -->
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-gradient">Business Processes</h1>
            <p class="text-gray-400 mt-1">Gestisci i tuoi processi aziendali automatizzati</p>
          </div>
          <div class="flex items-center gap-3">
            <button @click="refreshWorkflows" class="btn-control" :disabled="isLoading">
              <RefreshCw class="h-4 w-4" :class="{'animate-spin': isLoading}" />
              Aggiorna
            </button>
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span class="text-sm text-gray-400">{{ workflowsFromBackend.length }} processi caricati</span>
            </div>
          </div>
        </div>

        <!-- Workflows Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div 
            v-for="workflow in workflowsFromBackend" 
            :key="workflow.id"
            class="control-card p-6 hover:shadow-2xl transition-all duration-300 cursor-pointer group"
            @click="viewWorkflowDetails(workflow)"
          >
            <div class="flex items-start justify-between mb-4">
              <div class="flex items-center gap-3">
                <div class="h-10 w-10 rounded-lg bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center">
                  <GitBranch class="h-5 w-5 text-white" />
                </div>
                <div class="flex-1">
                  <h3 class="font-semibold text-white group-hover:text-green-400 transition-colors truncate">
                    {{ workflow.name }}
                  </h3>
                  <p class="text-xs text-gray-500 mt-1">
                    ID: {{ workflow.id.substring(0, 8) }}...
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-1">
                <div :class="workflow.active ? 'w-2 h-2 bg-green-500 rounded-full animate-pulse' : 'w-2 h-2 bg-gray-500 rounded-full'" />
                <span :class="workflow.active ? 'text-green-400 text-xs' : 'text-gray-500 text-xs'">
                  {{ workflow.active ? 'Attivo' : 'Inattivo' }}
                </span>
              </div>
            </div>
            
            <div class="space-y-3">
              <div class="flex items-center justify-between text-sm">
                <span class="text-gray-400">Ultima modifica:</span>
                <span class="text-gray-300">{{ formatDate(workflow.updatedAt) }}</span>
              </div>
              
              <div class="flex items-center justify-between text-sm">
                <span class="text-gray-400">Versione:</span>
                <span class="text-gray-300">{{ workflow.versionId || 'Draft' }}</span>
              </div>
              
              <div class="flex items-center justify-between text-sm">
                <span class="text-gray-400">Nodi:</span>
                <span class="text-gray-300">{{ workflow.nodes?.length || 0 }}</span>
              </div>
            </div>
            
            <div class="mt-4 pt-4 border-t border-gray-800 flex items-center justify-between">
              <button 
                @click.stop="toggleWorkflow(workflow)"
                :class="workflow.active ? 'text-yellow-400 hover:text-yellow-300' : 'text-green-400 hover:text-green-300'"
                class="text-sm font-medium transition-colors"
              >
                {{ workflow.active ? 'Disattiva' : 'Attiva' }}
              </button>
              
              <div class="flex items-center gap-2">
                <button @click.stop="viewWorkflowDetails(workflow)" class="text-gray-400 hover:text-white transition-colors">
                  <Eye class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="workflowsFromBackend.length === 0 && !isLoading" class="text-center py-12">
          <GitBranch class="h-16 w-16 text-gray-600 mx-auto mb-4" />
          <h3 class="text-xl font-semibold text-gray-400 mb-2">Nessun processo trovato</h3>
          <p class="text-gray-500">I processi aziendali appariranno qui una volta caricati dal database.</p>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="text-center py-12">
          <RefreshCw class="h-16 w-16 text-green-500 mx-auto mb-4 animate-spin" />
          <h3 class="text-xl font-semibold text-gray-400 mb-2">Caricamento processi...</h3>
          <p class="text-gray-500">Connessione al database PostgreSQL in corso...</p>
        </div>
      </div>
    </div>

    <!-- Workflow Detail Modal -->
    <WorkflowDetailModal
      v-if="selectedWorkflowForDetails"
      :workflow="selectedWorkflowForDetails"
      :isOpen="showDetailsModal"
      @close="closeDetailsModal"
    />
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RefreshCw, GitBranch, Eye } from 'lucide-vue-next'
import AppLayout from '../layouts/AppLayout.vue'
import WorkflowDetailModal from '../components/workflows/WorkflowDetailModal.vue'

// Local state
const isLoading = ref(false)
const workflowsFromBackend = ref<any[]>([])
const selectedWorkflowForDetails = ref<any>(null)
const showDetailsModal = ref(false)

// Methods
const loadWorkflows = async () => {
  isLoading.value = true
  try {
    console.log('🔄 Loading workflows from backend...')
    const response = await fetch('http://localhost:3001/api/business/processes')
    
    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }
    
    const data = await response.json()
    workflowsFromBackend.value = data.processes || []
    console.log(`✅ Loaded ${workflowsFromBackend.value.length} workflows`)
    
  } catch (error: any) {
    console.error('❌ Failed to load workflows:', error.message)
  } finally {
    isLoading.value = false
  }
}

const refreshWorkflows = () => {
  loadWorkflows()
}

const toggleWorkflow = (workflow: any) => {
  // TODO: Implement workflow toggle
  console.log('Toggle workflow:', workflow.id)
}

const viewWorkflowDetails = (workflow: any) => {
  selectedWorkflowForDetails.value = workflow
  showDetailsModal.value = true
}

const closeDetailsModal = () => {
  showDetailsModal.value = false
  selectedWorkflowForDetails.value = null
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

onMounted(() => {
  loadWorkflows()
})
</script>