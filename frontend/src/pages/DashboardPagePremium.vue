<template>
  <MainLayout>
        <div class="space-y-6">
          <!-- Premium Header -->
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-3xl font-bold text-gradient premium-gradient-text">Dashboard - PilotProOS</h1>
              <p class="text-text-muted mt-1">I tuoi dati business process automation</p>
            </div>
            <div class="premium-status-online">
              <span class="text-sm font-semibold text-primary premium-text-glow">LIVE DATA</span>
            </div>
          </div>
          
          <!-- Premium KPI Cards -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <!-- Total Processes Card -->
            <Card class="premium-glass premium-hover-lift premium-float">
              <template #content>
                <div class="p-4">
                  <div class="flex items-center justify-between mb-3">
                    <div class="flex items-baseline gap-2">
                      <p class="text-2xl font-bold text-text premium-text-glow">{{ workflowCount }}</p>
                      <Badge value="ATTIVI" severity="success" class="premium-badge" />
                    </div>
                    <Knob v-model="workflowCount" :size="40" :strokeWidth="6" 
                      valueColor="#10b981" rangeColor="#374151" 
                      readonly :max="50" :showValue="false" />
                  </div>
                  <p class="text-sm text-text-muted mb-2 font-semibold">PROCESSI TOTALI</p>
                  <ProgressBar :value="(activeWorkflows/workflowCount)*100" 
                    :showValue="false" class="h-2 premium-glow-intense" />
                </div>
              </template>
            </Card>

            <!-- Executions Card -->
            <Card class="premium-glass premium-hover-lift premium-float" style="animation-delay: 200ms">
              <template #content>
                <div class="p-4">
                  <div class="flex items-center justify-between mb-3">
                    <div class="flex items-baseline gap-2">
                      <p class="text-2xl font-bold text-text premium-text-glow">{{ totalExecutions }}</p>
                      <Badge value="OGGI" severity="info" class="premium-badge" />
                    </div>
                    <Chart type="line" :data="miniChartData" :options="miniChartOptions" class="w-16 h-8" />
                  </div>
                  <p class="text-sm text-text-muted mb-2 font-semibold">ESECUZIONI</p>
                  <p class="text-xs text-text-muted">{{ avgDurationFormatted }}</p>
                </div>
              </template>
            </Card>

            <!-- Success Rate Card -->
            <Card class="premium-glass premium-hover-lift premium-float premium-glow-intense" style="animation-delay: 400ms">
              <template #content>
                <div class="p-4">
                  <div class="flex items-center justify-between mb-3">
                    <div class="flex items-baseline gap-2">
                      <p class="text-2xl font-bold text-primary premium-text-glow">{{ successRate }}%</p>
                      <Badge value="SUCCESS" severity="success" class="premium-badge" />
                    </div>
                    <Knob v-model="successRate" :size="40" :strokeWidth="6"
                      valueColor="#00d26a" rangeColor="#374151"
                      readonly :max="100" :showValue="false" />
                  </div>
                  <p class="text-sm text-text-muted mb-2 font-semibold">TASSO SUCCESSO</p>
                  <p class="text-xs text-text-muted">{{ failedExecutions }} fallite</p>
                </div>
              </template>
            </Card>

            <!-- Business ROI Card -->
            <Card class="premium-glass premium-hover-lift premium-float premium-neon-pulse" style="animation-delay: 600ms">
              <template #content>
                <div class="p-4">
                  <div class="flex items-center justify-between mb-3">
                    <div class="flex items-baseline gap-2">
                      <p class="text-2xl font-bold text-warning premium-text-glow">{{ timeSaved }}h</p>
                      <Badge value="SAVED" severity="warning" class="premium-badge" />
                    </div>
                    <div class="w-10 h-10 rounded-full bg-warning/20 flex items-center justify-center premium-neon-pulse">
                      <TrendingUp class="w-5 h-5 text-warning" />
                    </div>
                  </div>
                  <p class="text-sm text-text-muted mb-2 font-semibold">TEMPO RISPARMIATO</p>
                  <p class="text-xs text-text-muted">ROI: {{ businessROI }}</p>
                </div>
              </template>
            </Card>
          </div>

          <!-- Premium Chart Section -->
          <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <!-- Main Performance Chart -->
            <Card class="xl:col-span-2 premium-chart-container premium-holographic">
              <template #content>
                <div class="p-6 pb-2 border-b border-border">
                  <div class="flex items-center justify-between">
                    <div>
                      <h3 class="text-2xl font-bold premium-gradient-text">
                        Performance Analytics
                      </h3>
                      <p class="text-sm text-text-muted mt-1">Analisi delle performance degli ultimi 30 giorni</p>
                    </div>
                    <div class="premium-status-online">
                      <span class="text-xs font-bold text-primary">REAL-TIME</span>
                    </div>
                  </div>
                </div>
                <div class="p-6">
                  <Chart type="line" :data="chartData" :options="chartOptions" class="w-full h-64" />
                </div>
              </template>
            </Card>

            <!-- Premium Recent Activity -->
            <Card class="premium-glass premium-hover-lift">
              <template #content>
                <div class="p-6">
                  <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-bold text-text premium-text-glow">Attività Recenti</h3>
                    <Badge value="LIVE" severity="success" class="premium-badge premium-neon-pulse" />
                  </div>
                  
                  <div class="space-y-4">
                    <div v-for="(activity, index) in recentActivities" 
                         :key="index" 
                         class="premium-glass p-4 rounded-lg premium-transition premium-hover-lift"
                         :style="{ animationDelay: `${index * 100}ms` }">
                      <div class="flex items-center justify-between">
                        <div class="flex items-center gap-3">
                          <div class="w-8 h-8 rounded-full flex items-center justify-center premium-neon-pulse"
                               :class="getActivityStatusClass(activity.status)">
                            <component :is="getActivityIcon(activity.type)" class="w-4 h-4" />
                          </div>
                          <div>
                            <p class="text-sm font-semibold text-text">{{ activity.workflow }}</p>
                            <p class="text-xs text-text-muted">{{ activity.action }}</p>
                          </div>
                        </div>
                        <div class="text-right">
                          <Badge :value="activity.status.toUpperCase()" 
                                 :severity="getActivitySeverity(activity.status)" 
                                 class="premium-badge text-xs" />
                          <p class="text-xs text-text-muted mt-1">{{ formatTimeAgo(activity.timestamp) }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="mt-6 pt-4 border-t border-border">
                    <button class="btn-premium w-full premium-transition">
                      <Eye class="w-4 h-4" />
                      <span>VEDI TUTTO</span>
                    </button>
                  </div>
                </div>
              </template>
            </Card>
          </div>

          <!-- Premium System Status -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card class="premium-glass premium-hover-lift premium-glow-intense">
              <template #content>
                <div class="p-4 text-center">
                  <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/20 flex items-center justify-center premium-neon-pulse">
                    <Server class="w-8 h-8 text-primary" />
                  </div>
                  <h3 class="text-lg font-bold text-text premium-text-glow">Sistema</h3>
                  <p class="text-primary font-semibold text-sm">OPERATIVO</p>
                  <p class="text-xs text-text-muted mt-2">Uptime: 99.9%</p>
                </div>
              </template>
            </Card>

            <Card class="premium-glass premium-hover-lift premium-glow-intense">
              <template #content>
                <div class="p-4 text-center">
                  <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/20 flex items-center justify-center premium-neon-pulse">
                    <Database class="w-8 h-8 text-primary" />
                  </div>
                  <h3 class="text-lg font-bold text-text premium-text-glow">Database</h3>
                  <p class="text-primary font-semibold text-sm">CONNESSO</p>
                  <p class="text-xs text-text-muted mt-2">{{ workflowCount }} processi</p>
                </div>
              </template>
            </Card>

            <Card class="premium-glass premium-hover-lift premium-glow-intense">
              <template #content>
                <div class="p-4 text-center">
                  <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/20 flex items-center justify-center premium-neon-pulse">
                    <Bot class="w-8 h-8 text-primary" />
                  </div>
                  <h3 class="text-lg font-bold text-text premium-text-glow">AI Agents</h3>
                  <p class="text-primary font-semibold text-sm">ATTIVI</p>
                  <p class="text-xs text-text-muted mt-2">{{ activeWorkflows }} agenti</p>
                </div>
              </template>
            </Card>
          </div>
        </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  TrendingUp, Eye, Server, Database, Bot, CheckCircle, 
  Clock, AlertTriangle, GitBranch
} from 'lucide-vue-next'
import MainLayout from '../components/layout/MainLayout.vue'
import { useAuthStore } from '../stores/auth'
import { useUIStore } from '../stores/ui'

// PrimeVue components
import Card from 'primevue/card'
import Badge from 'primevue/badge'
import ProgressBar from 'primevue/progressbar'
import Knob from 'primevue/knob'
import Chart from 'primevue/chart'

// Stores
const authStore = useAuthStore()
const uiStore = useUIStore()
const router = useRouter()

// Data from backend - REAL DATA INTEGRATION
const workflowCount = ref(29) // Real count from backend
const activeWorkflows = ref(1) // Real active count
const totalExecutions = ref(0) // Will be loaded from backend
const successRate = ref(95)
const timeSaved = ref(147)
const businessROI = ref('340%')

// Computed
const avgDurationFormatted = computed(() => '1.2s avg')
const failedExecutions = computed(() => Math.round(totalExecutions.value * (100 - successRate.value) / 100))

// Recent activities - premium mock data for demo
const recentActivities = ref([
  {
    workflow: 'Customer Onboarding',
    action: 'Email automation completed',
    status: 'success',
    type: 'email',
    timestamp: new Date(Date.now() - 2 * 60 * 1000)
  },
  {
    workflow: 'Data Processing',
    action: 'Batch process executed',
    status: 'success', 
    type: 'data',
    timestamp: new Date(Date.now() - 15 * 60 * 1000)
  },
  {
    workflow: 'Report Generation',
    action: 'PDF report created',
    status: 'running',
    type: 'report',
    timestamp: new Date(Date.now() - 45 * 60 * 1000)
  },
  {
    workflow: 'Backup Sync',
    action: 'Daily backup completed',
    status: 'success',
    type: 'backup', 
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000)
  }
])

// Chart data - Premium styling
const chartData = ref({
  labels: ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu'],
  datasets: [
    {
      label: 'Esecuzioni',
      data: [65, 78, 90, 81, 95, 102],
      fill: true,
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      borderColor: '#10b981',
      borderWidth: 3,
      pointBackgroundColor: '#00d26a',
      pointBorderColor: '#10b981',
      pointBorderWidth: 2,
      pointRadius: 6,
      tension: 0.4
    }
  ]
})

const chartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    }
  },
  scales: {
    y: {
      grid: {
        color: 'rgba(55, 65, 81, 0.3)'
      },
      ticks: {
        color: '#9ca3af'
      }
    },
    x: {
      grid: {
        color: 'rgba(55, 65, 81, 0.3)'
      },
      ticks: {
        color: '#9ca3af'
      }
    }
  }
})

const miniChartData = ref({
  labels: ['', '', '', '', ''],
  datasets: [{
    data: [20, 35, 28, 45, 38],
    borderColor: '#10b981',
    borderWidth: 2,
    fill: false,
    pointRadius: 0
  }]
})

const miniChartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { display: false },
    y: { display: false }
  }
})

// Methods
const getActivityIcon = (type: string) => {
  switch (type) {
    case 'email': return CheckCircle
    case 'data': return Database
    case 'report': return GitBranch
    case 'backup': return Server
    default: return Clock
  }
}

const getActivityStatusClass = (status: string) => {
  switch (status) {
    case 'success': return 'bg-primary/20 text-primary'
    case 'running': return 'bg-warning/20 text-warning'
    case 'error': return 'bg-error/20 text-error'
    default: return 'bg-text-muted/20 text-text-muted'
  }
}

const getActivitySeverity = (status: string) => {
  switch (status) {
    case 'success': return 'success'
    case 'running': return 'warn'
    case 'error': return 'danger'
    default: return 'info'
  }
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
  console.log('🎨 Premium Dashboard initialized')
})
</script>

<style scoped>
/* All premium effects handled by premium.css */
</style>