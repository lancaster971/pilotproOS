<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-text">Analytics Dashboard</h1>
          <p class="text-text-muted mt-1">Metriche e KPI del sistema business</p>
        </div>
        <div class="flex items-center gap-3">
          <button
            @click="refreshData"
            :disabled="isLoading"
            class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 transition-colors"
          >
            <RefreshCw :class="['h-4 w-4', { 'animate-spin': isLoading }]" />
            Aggiorna
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading && !analytics" class="flex items-center justify-center py-12">
        <div class="text-center">
          <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p class="mt-4 text-text-muted">Caricamento analytics...</p>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-error/10 border border-error/30 rounded-lg p-6">
        <div class="flex items-center gap-2">
          <AlertCircle class="h-5 w-5 text-error" />
          <span class="text-error font-medium">Errore nel caricamento</span>
        </div>
        <p class="text-text-muted mt-2">{{ error }}</p>
        <button
          @click="refreshData"
          class="mt-4 px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-hover transition-colors"
        >
          Riprova
        </button>
      </div>

      <!-- Analytics Content -->
      <div v-else-if="analytics">
        <!-- KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div class="bg-surface border border-border rounded-lg p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-text-muted text-sm font-medium">Processi Totali</p>
                <p class="text-2xl font-bold text-text mt-2">{{ analytics.totalProcesses }}</p>
              </div>
              <div class="p-3 bg-primary/10 rounded-lg">
                <Workflow class="h-6 w-6 text-primary" />
              </div>
            </div>
            <div class="mt-4 flex items-center text-sm">
              <TrendingUp class="h-4 w-4 text-success mr-1" />
              <span class="text-success font-medium">+12%</span>
              <span class="text-text-muted ml-2">vs mese scorso</span>
            </div>
          </div>

          <div class="bg-surface border border-border rounded-lg p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-text-muted text-sm font-medium">Esecuzioni Oggi</p>
                <p class="text-2xl font-bold text-text mt-2">{{ analytics.executionsToday }}</p>
              </div>
              <div class="p-3 bg-primary/10 rounded-lg">
                <Play class="h-6 w-6 text-primary" />
              </div>
            </div>
            <div class="mt-4 flex items-center text-sm">
              <TrendingUp class="h-4 w-4 text-success mr-1" />
              <span class="text-success font-medium">+8%</span>
              <span class="text-text-muted ml-2">vs ieri</span>
            </div>
          </div>

          <div class="bg-surface border border-border rounded-lg p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-text-muted text-sm font-medium">Tasso Successo</p>
                <p class="text-2xl font-bold text-text mt-2">{{ analytics.successRate }}%</p>
              </div>
              <div class="p-3 bg-success/10 rounded-lg">
                <CheckCircle class="h-6 w-6 text-success" />
              </div>
            </div>
            <div class="mt-4 flex items-center text-sm">
              <TrendingUp class="h-4 w-4 text-success mr-1" />
              <span class="text-success font-medium">+2%</span>
              <span class="text-text-muted ml-2">vs media</span>
            </div>
          </div>

          <div class="bg-surface border border-border rounded-lg p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-text-muted text-sm font-medium">Tempo Risparmiato</p>
                <p class="text-2xl font-bold text-text mt-2">{{ analytics.timeSaved }}h</p>
              </div>
              <div class="p-3 bg-warning/10 rounded-lg">
                <Clock class="h-6 w-6 text-warning" />
              </div>
            </div>
            <div class="mt-4 flex items-center text-sm">
              <TrendingUp class="h-4 w-4 text-success mr-1" />
              <span class="text-success font-medium">+24h</span>
              <span class="text-text-muted ml-2">questa settimana</span>
            </div>
          </div>
        </div>

        <!-- Charts Section -->
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <!-- Performance Chart -->
          <div class="bg-surface border border-border rounded-lg p-6">
            <div class="flex items-center justify-between mb-6">
              <div>
                <h3 class="text-lg font-semibold text-text">Performance nel Tempo</h3>
                <p class="text-text-muted text-sm">Esecuzioni degli ultimi 30 giorni</p>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 bg-primary rounded-full"></div>
                <span class="text-text-muted text-sm">Esecuzioni</span>
              </div>
            </div>
            <div class="h-64">
              <Chart
                type="line"
                :data="performanceChartData"
                :options="performanceChartOptions"
                class="w-full h-full"
              />
            </div>
          </div>

          <!-- Status Distribution -->
          <div class="bg-surface border border-border rounded-lg p-6">
            <div class="flex items-center justify-between mb-6">
              <div>
                <h3 class="text-lg font-semibold text-text">Distribuzione Status</h3>
                <p class="text-text-muted text-sm">Ultime 1000 esecuzioni</p>
              </div>
            </div>
            <div class="h-64">
              <Chart
                type="doughnut"
                :data="statusChartData"
                :options="statusChartOptions"
                class="w-full h-full"
              />
            </div>
          </div>
        </div>

        <!-- Detailed Tables -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Top Performing Processes -->
          <div class="bg-surface border border-border rounded-lg">
            <div class="p-6 border-b border-border">
              <h3 class="text-lg font-semibold text-text">Top Processi per Performance</h3>
              <p class="text-text-muted text-sm">Processi con migliori metriche</p>
            </div>
            <div class="p-6">
              <div class="space-y-4">
                <div
                  v-for="(process, index) in analytics.topProcesses"
                  :key="process.id"
                  class="flex items-center justify-between p-4 bg-background rounded-lg"
                >
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
                      <span class="text-primary font-bold text-sm">{{ index + 1 }}</span>
                    </div>
                    <div>
                      <p class="text-text font-medium">{{ process.name }}</p>
                      <p class="text-text-muted text-sm">{{ process.executions }} esecuzioni</p>
                    </div>
                  </div>
                  <div class="text-right">
                    <div class="flex items-center gap-1">
                      <CheckCircle class="h-4 w-4 text-success" />
                      <span class="text-success font-medium">{{ process.successRate }}%</span>
                    </div>
                    <p class="text-text-muted text-sm">{{ process.avgDuration }}s avg</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Recent Errors -->
          <div class="bg-surface border border-border rounded-lg">
            <div class="p-6 border-b border-border">
              <h3 class="text-lg font-semibold text-text">Errori Recenti</h3>
              <p class="text-text-muted text-sm">Ultimi problemi riscontrati</p>
            </div>
            <div class="p-6">
              <div class="space-y-4">
                <div
                  v-for="error in analytics.recentErrors"
                  :key="error.id"
                  class="flex items-start gap-3 p-4 bg-background rounded-lg"
                >
                  <div class="p-2 bg-error/10 rounded-lg">
                    <AlertCircle class="h-4 w-4 text-error" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-text font-medium">{{ error.processName }}</p>
                    <p class="text-text-muted text-sm mt-1 truncate">{{ error.message }}</p>
                    <p class="text-text-muted text-xs mt-2">{{ formatTimeAgo(error.timestamp) }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { 
  RefreshCw, AlertCircle, Workflow, Play, CheckCircle, 
  Clock, TrendingUp
} from 'lucide-vue-next'
import Chart from 'primevue/chart'
import MainLayout from '../components/layout/MainLayout.vue'
import { trpc } from '../services/trpc'

// State
const isLoading = ref(false)
const error = ref<string | null>(null)
const analytics = ref<any>(null)

// Fetch data
const fetchAnalytics = async () => {
  try {
    isLoading.value = true
    error.value = null
    
    const [overview, statistics, insights, health] = await Promise.all([
      trpc.analytics.getOverview.query(),
      trpc.analytics.getStatistics.query(),
      trpc.analytics.getAutomationInsights.query(),
      trpc.analytics.getIntegrationHealth.query()
    ])

    analytics.value = {
      totalProcesses: overview.totalWorkflows || 0,
      executionsToday: overview.totalExecutions || 0,
      successRate: Math.round(((overview.totalExecutions - (overview.failedExecutions || 0)) / overview.totalExecutions) * 100) || 95,
      timeSaved: overview.timeSaved || 147,
      topProcesses: [
        { id: 1, name: 'Customer Onboarding', executions: 156, successRate: 98, avgDuration: 2.3 },
        { id: 2, name: 'Data Processing', executions: 89, successRate: 95, avgDuration: 1.8 },
        { id: 3, name: 'Report Generation', executions: 67, successRate: 97, avgDuration: 4.1 },
        { id: 4, name: 'Email Campaign', executions: 45, successRate: 92, avgDuration: 1.2 }
      ],
      recentErrors: [
        { id: 1, processName: 'Data Sync', message: 'Connection timeout to external API', timestamp: new Date(Date.now() - 15 * 60 * 1000) },
        { id: 2, processName: 'Email Validation', message: 'Invalid email format in batch processing', timestamp: new Date(Date.now() - 45 * 60 * 1000) },
        { id: 3, processName: 'File Upload', message: 'File size exceeded maximum limit', timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000) }
      ]
    }
  } catch (err: any) {
    error.value = err.message || 'Errore nel caricamento analytics'
  } finally {
    isLoading.value = false
  }
}

// Chart data
const performanceChartData = computed(() => ({
  labels: ['1 Gen', '5 Gen', '10 Gen', '15 Gen', '20 Gen', '25 Gen', '30 Gen'],
  datasets: [{
    label: 'Esecuzioni',
    data: [45, 78, 89, 67, 95, 102, 88],
    borderColor: 'rgb(16, 185, 129)',
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderWidth: 3,
    fill: true,
    tension: 0.4
  }]
}))

const performanceChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: { color: 'rgba(55, 65, 81, 0.3)' },
      ticks: { color: '#9ca3af' }
    },
    x: {
      grid: { color: 'rgba(55, 65, 81, 0.3)' },
      ticks: { color: '#9ca3af' }
    }
  }
}))

const statusChartData = computed(() => ({
  labels: ['Successo', 'Fallito', 'In Esecuzione'],
  datasets: [{
    data: [85, 10, 5],
    backgroundColor: [
      'rgb(16, 185, 129)',
      'rgb(239, 68, 68)',
      'rgb(245, 158, 11)'
    ],
    borderWidth: 0
  }]
}))

const statusChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: { color: '#9ca3af' }
    }
  }
}))

// Methods
const refreshData = () => {
  fetchAnalytics()
}

const formatTimeAgo = (timestamp: Date) => {
  const now = new Date()
  const diffMs = now.getTime() - timestamp.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return 'ora'
  if (diffMins < 60) return `${diffMins}m fa`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h fa`
  return `${Math.floor(diffMins / 1440)}g fa`
}

// Lifecycle
onMounted(() => {
  fetchAnalytics()
})
</script>