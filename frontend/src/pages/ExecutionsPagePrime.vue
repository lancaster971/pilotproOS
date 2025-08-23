<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gradient">
            Executions - {{ authStore.tenantId }}
          </h1>
          <p class="text-gray-400 mt-1">
            Monitora le esecuzioni dei tuoi workflow con PrimeVue DataTable
          </p>
        </div>
        
        <div class="flex items-center gap-3">
          <!-- Auto Refresh Toggle -->
          <div class="flex items-center gap-2">
            <InputSwitch v-model="autoRefresh" />
            <label class="text-sm text-white">Auto refresh</label>
          </div>
          
          <Button 
            @click="refreshExecutions"
            :loading="isLoading"
            icon="pi pi-refresh"
            label="Refresh"
            severity="secondary"
            size="small"
          />
          
          <Button 
            icon="pi pi-download"
            label="Esporta"
            severity="secondary"
            size="small"
            @click="exportData"
          />
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div class="bg-gray-900 border border-gray-700 rounded-lg p-4 premium-glow">
          <div class="text-center">
            <p class="text-2xl font-bold text-white">{{ executionStats.total }}</p>
            <p class="text-xs text-gray-400">Totali</p>
          </div>
        </div>
        
        <div class="bg-gray-900 border border-gray-700 rounded-lg p-4 success-glow">
          <div class="text-center">
            <p class="text-2xl font-bold text-green-400">{{ executionStats.success }}</p>
            <p class="text-xs text-gray-400">Success</p>
          </div>
        </div>
        
        <div class="bg-gray-900 border border-gray-700 rounded-lg p-4 error-glow">
          <div class="text-center">
            <p class="text-2xl font-bold text-red-400">{{ executionStats.error }}</p>
            <p class="text-xs text-gray-400">Error</p>
          </div>
        </div>
        
        <div class="bg-gray-900 border border-gray-700 rounded-lg p-4 info-glow">
          <div class="text-center">
            <p class="text-2xl font-bold text-blue-400">{{ executionStats.running }}</p>
            <p class="text-xs text-gray-400">Running</p>
          </div>
        </div>
        
        <div class="bg-gray-900 border border-gray-700 rounded-lg p-4 warning-glow">
          <div class="text-center">
            <p class="text-2xl font-bold text-yellow-400">{{ executionStats.waiting }}</p>
            <p class="text-xs text-gray-400">Waiting</p>
          </div>
        </div>
      </div>

      <!-- DataTable with PrimeVue -->
      <div class="bg-gray-900 border border-gray-700 rounded-lg p-6 chart-container">
        <DataTable 
            :value="executions" 
            :loading="isLoading"
            :paginator="true"
            :rows="10"
            :rowsPerPageOptions="[10, 25, 50, 100]"
            :globalFilterFields="['workflow_name', 'status', 'mode']"
            v-model:filters="filters"
            filterDisplay="row"
            showGridlines
            stripedRows
            responsiveLayout="scroll"
            class="p-datatable-dark"
          >
            <!-- Global Filter -->
            <template #header>
              <div class="flex justify-between items-center">
                <span class="text-xl text-white">Process Runs</span>
                <IconField iconPosition="left">
                  <InputIcon><i class="pi pi-search" /></InputIcon>
                  <InputText 
                    v-model="filters['global'].value" 
                    placeholder="Global Search" 
                    class="bg-gray-800 border-gray-700 text-white placeholder-gray-500"
                  />
                </IconField>
              </div>
            </template>

            <!-- Status Column with Badge -->
            <Column field="status" header="Status" :sortable="true" style="min-width: 120px">
              <template #body="{ data }">
                <Tag 
                  :value="data.status" 
                  :severity="getStatusSeverity(data.status)"
                  :icon="getStatusIcon(data.status)"
                />
              </template>
              <template #filter="{ filterModel, filterCallback }">
                <Select
                  v-model="filterModel.value"
                  @change="filterCallback()"
                  :options="statusOptions"
                  placeholder="Select Status"
                  class="bg-gray-800 border-gray-700 text-white"
                />
              </template>
            </Column>

            <!-- Workflow Name Column -->
            <Column field="workflow_name" header="Workflow" :sortable="true" style="min-width: 200px">
              <template #body="{ data }">
                <div class="flex items-center gap-2">
                  <i class="pi pi-sitemap text-green-400"></i>
                  <span class="text-white font-medium">{{ data.workflow_name || 'Unknown' }}</span>
                </div>
              </template>
            </Column>

            <!-- Execution ID -->
            <Column field="id" header="ID" :sortable="true" style="min-width: 80px">
              <template #body="{ data }">
                <span class="text-gray-400 font-mono text-xs">#{{ data.id }}</span>
              </template>
            </Column>

            <!-- Mode -->
            <Column field="mode" header="Mode" :sortable="true" style="min-width: 100px">
              <template #body="{ data }">
                <Tag 
                  :value="data.mode || 'manual'" 
                  :severity="data.mode === 'trigger' ? 'info' : 'contrast'"
                  :icon="data.mode === 'trigger' ? 'pi pi-bolt' : 'pi pi-user'"
                />
              </template>
            </Column>

            <!-- Started At -->
            <Column field="startedAt" header="Started" :sortable="true" style="min-width: 180px">
              <template #body="{ data }">
                <div class="text-gray-300 text-sm">
                  <i class="pi pi-clock text-gray-500 mr-1"></i>
                  {{ formatDate(data.startedAt) }}
                </div>
              </template>
            </Column>

            <!-- Duration -->
            <Column field="executionTime" header="Duration" :sortable="true" style="min-width: 100px">
              <template #body="{ data }">
                <span class="text-gray-300 font-mono text-sm">
                  {{ formatDuration(data.executionTime) }}
                </span>
              </template>
            </Column>

            <!-- Actions -->
            <Column header="Actions" style="min-width: 100px">
              <template #body="{ data }">
                <div class="flex gap-2">
                  <Button 
                    icon="pi pi-eye" 
                    severity="info" 
                    text 
                    rounded 
                    size="small"
                    @click="viewExecution(data)"
                    title="View Details"
                  />
                  <Button 
                    icon="pi pi-replay" 
                    severity="success" 
                    text 
                    rounded 
                    size="small"
                    @click="retryExecution(data)"
                    title="Retry"
                    :disabled="data.status === 'running'"
                  />
                </div>
              </template>
            </Column>
          </DataTable>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { FilterMatchMode } from '@primevue/core/api'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Select from 'primevue/select'
import InputSwitch from 'primevue/inputswitch'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'

import MainLayout from '../components/layout/MainLayout.vue'
import { useAuthStore } from '../stores/auth'
import { useWorkflowsStore } from '../stores/workflows'
import { useUIStore } from '../stores/ui'
import webSocketService from '../services/websocket'
import type { Execution } from '../types'

// Stores
const authStore = useAuthStore()
const workflowsStore = useWorkflowsStore()
const uiStore = useUIStore()

// Local state
const isLoading = ref(false)
const autoRefresh = ref(false)
const executions = ref<Execution[]>([])

// PrimeVue Filters
const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS },
  status: { value: null, matchMode: FilterMatchMode.EQUALS },
  workflow_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
  mode: { value: null, matchMode: FilterMatchMode.EQUALS }
})

const statusOptions = ['success', 'error', 'running', 'waiting', 'canceled']

// Computed stats
const executionStats = computed(() => {
  const total = executions.value.length
  const success = executions.value.filter(e => e.status === 'success').length
  const error = executions.value.filter(e => e.status === 'error').length
  const running = executions.value.filter(e => e.status === 'running').length
  const waiting = executions.value.filter(e => e.status === 'waiting').length
  
  return { total, success, error, running, waiting }
})

// Methods
const refreshExecutions = async () => {
  isLoading.value = true
  console.log('🔄 Refreshing executions...')
  
  try {
    const response = await fetch('http://localhost:3001/api/business/process-runs?limit=1000')
    console.log('📡 Response status:', response.status)
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('📦 Raw data:', data)
    console.log('📊 Number of runs:', data.data?.length || 0)
    
    executions.value = (data.data || []).map((run: any) => ({
      id: run.run_id,
      workflow_id: run.process_id,
      workflow_name: run.process_name,
      status: mapBackendStatus(run.business_status),
      mode: run.trigger_mode || 'manual',
      startedAt: run.start_time,
      stoppedAt: run.end_time,
      executionTime: run.duration_ms,
      data: run.input_data,
      error: run.error_details
    }))
    
    console.log('✅ Executions loaded:', executions.value.length)
    console.log('📋 First execution:', executions.value[0])
    
    uiStore.showToast('Aggiornamento', `${executions.value.length} executions caricate`, 'success')
  } catch (error: any) {
    console.error('❌ Failed to load executions:', error)
    uiStore.showToast('Errore', 'Impossibile caricare executions', 'error')
  } finally {
    isLoading.value = false
  }
}

const mapBackendStatus = (status: string): string => {
  const statusMap: Record<string, string> = {
    'Completed Successfully': 'success',
    'Failed': 'error',
    'In Progress': 'running',
    'Waiting': 'waiting',
    'Canceled': 'canceled'
  }
  return statusMap[status] || status.toLowerCase()
}

const getStatusSeverity = (status: string) => {
  switch (status) {
    case 'success': return 'success'
    case 'error': return 'danger'
    case 'running': return 'info'
    case 'waiting': return 'warn'
    case 'canceled': return 'secondary'
    default: return 'secondary'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'success': return 'pi pi-check-circle'
    case 'error': return 'pi pi-times-circle'
    case 'running': return 'pi pi-spin pi-spinner'
    case 'waiting': return 'pi pi-clock'
    case 'canceled': return 'pi pi-ban'
    default: return 'pi pi-question-circle'
  }
}

const formatDate = (dateString?: string) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('it-IT')
}

const formatDuration = (ms?: number) => {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}min`
}

const viewExecution = (execution: Execution) => {
  console.log('View execution:', execution)
  // TODO: Open detail modal or navigate to detail page
}

const retryExecution = (execution: Execution) => {
  console.log('Retry execution:', execution)
  // TODO: Implement retry logic
}

const exportData = () => {
  // TODO: Implement export functionality
  console.log('Export data')
}

// Auto-refresh setup
watch(autoRefresh, (enabled) => {
  if (enabled) {
    webSocketService.startAutoRefresh('executions-prime', refreshExecutions, 5000)
  } else {
    webSocketService.stopAutoRefresh('executions-prime')
  }
})

// Lifecycle
onMounted(() => {
  refreshExecutions()
  workflowsStore.fetchWorkflows()
  
  if (autoRefresh.value) {
    webSocketService.startAutoRefresh('executions-prime', refreshExecutions, 5000)
  }
  
  // Listen for real-time execution events
  window.addEventListener('execution:started', refreshExecutions)
  window.addEventListener('execution:completed', refreshExecutions)
})

onUnmounted(() => {
  // Stop auto-refresh
  webSocketService.stopAutoRefresh('executions-prime')
  
  // Clean up event listeners
  window.removeEventListener('execution:started', refreshExecutions)
  window.removeEventListener('execution:completed', refreshExecutions)
})
</script>

<style scoped>
/* Additional dark theme overrides if needed */
</style>