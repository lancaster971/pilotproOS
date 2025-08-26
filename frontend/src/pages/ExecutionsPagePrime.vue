<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-lg font-bold text-gradient">
            Executions - {{ authStore.tenantId }}
          </h1>
          <p class="text-text-muted mt-1">
            Monitora le esecuzioni dei tuoi workflow con PrimeVue DataTable
          </p>
        </div>
        
        <div class="flex items-center gap-3">
          <!-- Auto Refresh Toggle -->
          <div class="flex items-center gap-2">
            <InputSwitch v-model="autoRefresh" />
            <label class="text-sm text-text">Auto refresh</label>
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

      <!-- Compact Statistics Table -->
      <div class="premium-glass rounded-lg overflow-hidden border border-border mb-4">
        <table class="w-full table-fixed">
          <thead>
            <tr class="bg-surface">
              <th class="text-xs font-semibold text-text-muted py-2 px-3 border-r border-border text-center w-1/5">Total</th>
              <th class="text-xs font-semibold text-text-muted py-2 px-3 border-r border-border text-center w-1/5">Success</th>
              <th class="text-xs font-semibold text-text-muted py-2 px-3 border-r border-border text-center w-1/5">Error</th>
              <th class="text-xs font-semibold text-text-muted py-2 px-3 border-r border-border text-center w-1/5">Running</th>
              <th class="text-xs font-semibold text-text-muted py-2 px-3 text-center w-1/5">Waiting</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-t border-border">
              <td class="text-center py-2 px-3 border-r border-border">
                <div class="text-lg font-bold text-text">{{ executionStats.total }}</div>
              </td>
              <td class="text-center py-2 px-3 border-r border-border">
                <div class="text-lg font-bold text-primary">{{ executionStats.success }}</div>
              </td>
              <td class="text-center py-2 px-3 border-r border-border">
                <div class="text-lg font-bold text-error">{{ executionStats.error }}</div>
              </td>
              <td class="text-center py-2 px-3 border-r border-border">
                <div class="text-lg font-bold text-primary">{{ executionStats.running }}</div>
              </td>
              <td class="text-center py-2 px-3">
                <div class="text-lg font-bold text-warning">{{ executionStats.waiting }}</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- DataTable with PrimeVue -->
      <div class="control-card p-6">
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
            <!-- Header with Search and Status Filter -->
            <template #header>
              <div class="flex justify-between items-center">
                <span class="text-lg font-bold text-text">Process Runs</span>
                <div class="flex items-center gap-3">
                  <!-- Status Filter -->
                  <Select
                    v-model="statusFilter"
                    @change="applyStatusFilter"
                    :options="statusOptions"
                    placeholder="All Status"
                    class="premium-input text-xs w-32"
                  />
                  <!-- Global Search -->
                  <IconField iconPosition="left">
                    <InputIcon><i class="pi pi-search" /></InputIcon>
                    <InputText 
                      v-model="filters['global'].value" 
                      placeholder="Global Search" 
                      class="premium-input text-sm"
                    />
                  </IconField>
                </div>
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
                <span class="text-text-muted font-mono text-xs">#{{ data.id }}</span>
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
                <div class="text-text-secondary text-sm">
                  <i class="pi pi-clock text-text-muted mr-1"></i>
                  {{ formatDate(data.startedAt) }}
                </div>
              </template>
            </Column>

            <!-- Duration -->
            <Column field="executionTime" header="Duration" :sortable="true" style="min-width: 100px">
              <template #body="{ data }">
                <span class="text-text-secondary font-mono text-sm">
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
const statusFilter = ref(null)

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

const applyStatusFilter = () => {
  if (statusFilter.value) {
    filters.value.status.value = statusFilter.value
  } else {
    filters.value.status.value = null
  }
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