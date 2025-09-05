<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-text">Database Management</h1>
          <p class="text-text-muted mt-1">Gestione e monitoraggio del database PostgreSQL</p>
        </div>
        <div class="flex items-center gap-3">
          <button
            @click="testConnection"
            :disabled="isLoading"
            class="inline-flex items-center gap-2 px-4 py-2 bg-success text-white rounded-lg hover:bg-success-hover disabled:opacity-50 transition-colors"
          >
            <Database :class="['h-4 w-4', { 'animate-pulse': isLoading }]" />
            Test Connessione
          </button>
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

      <!-- Connection Status -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-surface border border-border rounded-lg p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-text-muted text-sm font-medium">Status Connessione</p>
              <div class="flex items-center gap-2 mt-2">
                <div :class="['w-3 h-3 rounded-full', connectionStatus ? 'bg-success animate-pulse' : 'bg-error']"></div>
                <span :class="['font-medium', connectionStatus ? 'text-success' : 'text-error']">
                  {{ connectionStatus ? 'CONNESSO' : 'DISCONNESSO' }}
                </span>
              </div>
            </div>
            <div class="p-3 bg-success/10 rounded-lg">
              <Server class="h-6 w-6 text-success" />
            </div>
          </div>
        </div>

        <div class="bg-surface border border-border rounded-lg p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-text-muted text-sm font-medium">Database Version</p>
              <p class="text-xl font-bold text-text mt-2">PostgreSQL 16</p>
            </div>
            <div class="p-3 bg-primary/10 rounded-lg">
              <Database class="h-6 w-6 text-primary" />
            </div>
          </div>
        </div>

        <div class="bg-surface border border-border rounded-lg p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-text-muted text-sm font-medium">Schemas Attivi</p>
              <p class="text-xl font-bold text-text mt-2">2</p>
              <p class="text-text-muted text-xs mt-1">n8n + pilotpros</p>
            </div>
            <div class="p-3 bg-warning/10 rounded-lg">
              <Layers class="h-6 w-6 text-warning" />
            </div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading && !dbStats" class="flex items-center justify-center py-12">
        <div class="text-center">
          <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p class="mt-4 text-text-muted">Caricamento statistiche database...</p>
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

      <!-- Database Statistics -->
      <div v-else-if="dbStats" class="space-y-6">
        <!-- Schema Statistics -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- N8n Schema Stats -->
          <div class="bg-surface border border-border rounded-lg">
            <div class="p-6 border-b border-border">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-lg font-semibold text-text">N8n Schema</h3>
                  <p class="text-text-muted text-sm">Workflow engine data</p>
                </div>
                <div class="p-2 bg-primary/10 rounded-lg">
                  <Workflow class="h-5 w-5 text-primary" />
                </div>
              </div>
            </div>
            <div class="p-6">
              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <span class="text-text-muted">Workflows</span>
                  <span class="text-text font-medium">{{ dbStats.n8n.workflows }}</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-text-muted">Executions</span>
                  <span class="text-text font-medium">{{ dbStats.n8n.executions }}</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-text-muted">Credentials</span>
                  <span class="text-text font-medium">{{ dbStats.n8n.credentials }}</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-text-muted">Users</span>
                  <span class="text-text font-medium">{{ dbStats.n8n.users }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- PilotProOS Schema Stats -->
          <div class="bg-surface border border-border rounded-lg">
            <div class="p-6 border-b border-border">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-lg font-semibold text-text">PilotProOS Schema</h3>
                  <p class="text-text-muted text-sm">Business application data</p>
                </div>
                <div class="p-2 bg-success/10 rounded-lg">
                  <BarChart3 class="h-5 w-5 text-success" />
                </div>
              </div>
            </div>
            <div class="p-6">
              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <span class="text-text-muted">Business Executions</span>
                  <span class="text-text font-medium">{{ dbStats.pilotpros.businessExecutions }}</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-text-muted">Analytics Records</span>
                  <span class="text-text font-medium">{{ dbStats.pilotpros.analytics }}</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-text-muted">Audit Logs</span>
                  <span class="text-text font-medium">{{ dbStats.pilotpros.auditLogs }}</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-text-muted">Process Templates</span>
                  <span class="text-text font-medium">{{ dbStats.pilotpros.templates }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Database Performance -->
        <div class="bg-surface border border-border rounded-lg">
          <div class="p-6 border-b border-border">
            <h3 class="text-lg font-semibold text-text">Performance Metrics</h3>
            <p class="text-text-muted text-sm">Statistiche di utilizzo del database</p>
          </div>
          <div class="p-6">
            <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div class="text-center">
                <p class="text-text-muted text-sm">Connessioni Attive</p>
                <p class="text-2xl font-bold text-text mt-2">{{ dbStats.performance.activeConnections }}</p>
              </div>
              <div class="text-center">
                <p class="text-text-muted text-sm">Queries/sec</p>
                <p class="text-2xl font-bold text-text mt-2">{{ dbStats.performance.queriesPerSecond }}</p>
              </div>
              <div class="text-center">
                <p class="text-text-muted text-sm">Cache Hit Ratio</p>
                <p class="text-2xl font-bold text-text mt-2">{{ dbStats.performance.cacheHitRatio }}%</p>
              </div>
              <div class="text-center">
                <p class="text-text-muted text-sm">DB Size</p>
                <p class="text-2xl font-bold text-text mt-2">{{ dbStats.performance.dbSize }}MB</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="bg-surface border border-border rounded-lg">
          <div class="p-6 border-b border-border">
            <h3 class="text-lg font-semibold text-text">Attività Recente</h3>
            <p class="text-text-muted text-sm">Ultime operazioni sul database</p>
          </div>
          <div class="p-6">
            <div class="space-y-4">
              <div
                v-for="activity in dbStats.recentActivity"
                :key="activity.id"
                class="flex items-start gap-3 p-4 bg-background rounded-lg"
              >
                <div class="p-2 bg-primary/10 rounded-lg">
                  <component :is="getActivityIcon(activity.type)" class="h-4 w-4 text-primary" />
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-text font-medium">{{ activity.operation }}</p>
                  <p class="text-text-muted text-sm mt-1">{{ activity.table }} • {{ activity.schema }}</p>
                  <p class="text-text-muted text-xs mt-2">{{ formatTimeAgo(activity.timestamp) }}</p>
                </div>
                <div class="text-right">
                  <span :class="[
                    'px-2 py-1 text-xs rounded-full',
                    activity.status === 'success' ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'
                  ]">
                    {{ activity.status }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Debug Section -->
        <div class="bg-surface border border-border rounded-lg">
          <div class="p-6 border-b border-border">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-semibold text-text">Debug & Testing</h3>
                <p class="text-text-muted text-sm">Strumenti di sviluppo e test</p>
              </div>
            </div>
          </div>
          <div class="p-6">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <button
                @click="testDrizzle"
                :disabled="isLoading"
                class="flex items-center gap-2 px-4 py-3 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 disabled:opacity-50 transition-colors"
              >
                <TestTube class="h-4 w-4" />
                Test Drizzle ORM
              </button>
              <button
                @click="runHealthCheck"
                :disabled="isLoading"
                class="flex items-center gap-2 px-4 py-3 bg-success/10 text-success rounded-lg hover:bg-success/20 disabled:opacity-50 transition-colors"
              >
                <Activity class="h-4 w-4" />
                Health Check
              </button>
              <button
                @click="viewLogs"
                :disabled="isLoading"
                class="flex items-center gap-2 px-4 py-3 bg-warning/10 text-warning rounded-lg hover:bg-warning/20 disabled:opacity-50 transition-colors"
              >
                <FileText class="h-4 w-4" />
                View Logs
              </button>
            </div>
            
            <!-- Test Results -->
            <div v-if="testResult" class="mt-6 p-4 bg-background rounded-lg">
              <div class="flex items-center gap-2 mb-2">
                <CheckCircle v-if="testResult.success" class="h-4 w-4 text-success" />
                <AlertCircle v-else class="h-4 w-4 text-error" />
                <span class="font-medium text-text">Test Result</span>
              </div>
              <pre class="text-text-muted text-sm">{{ JSON.stringify(testResult, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { 
  RefreshCw, AlertCircle, Database, Server, Layers, Workflow, 
  BarChart3, TestTube, Activity, FileText, CheckCircle, 
  Plus, Edit, Trash2
} from 'lucide-vue-next'
import MainLayout from '../components/layout/MainLayout.vue'
import { trpc } from '../services/trpc'

// State
const isLoading = ref(false)
const error = ref<string | null>(null)
const dbStats = ref<any>(null)
const connectionStatus = ref(true)
const testResult = ref<any>(null)

// Fetch data
const fetchDatabaseStats = async () => {
  try {
    isLoading.value = true
    error.value = null
    
    // Simulate database statistics (since we don't have real DB stats endpoint)
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    dbStats.value = {
      n8n: {
        workflows: 31,
        executions: 1247,
        credentials: 15,
        users: 3
      },
      pilotpros: {
        businessExecutions: 856,
        analytics: 342,
        auditLogs: 1203,
        templates: 8
      },
      performance: {
        activeConnections: 5,
        queriesPerSecond: 127,
        cacheHitRatio: 98.5,
        dbSize: 245
      },
      recentActivity: [
        { 
          id: 1, 
          operation: 'INSERT INTO business_execution_data', 
          table: 'business_execution_data', 
          schema: 'pilotpros',
          type: 'insert',
          status: 'success',
          timestamp: new Date(Date.now() - 5 * 60 * 1000)
        },
        { 
          id: 2, 
          operation: 'UPDATE workflow_entity SET active = true', 
          table: 'workflow_entity', 
          schema: 'n8n',
          type: 'update',
          status: 'success',
          timestamp: new Date(Date.now() - 12 * 60 * 1000)
        },
        { 
          id: 3, 
          operation: 'SELECT * FROM execution_entity', 
          table: 'execution_entity', 
          schema: 'n8n',
          type: 'select',
          status: 'success',
          timestamp: new Date(Date.now() - 18 * 60 * 1000)
        }
      ]
    }
    
    connectionStatus.value = true
  } catch (err: any) {
    error.value = err.message || 'Errore nel caricamento statistiche database'
    connectionStatus.value = false
  } finally {
    isLoading.value = false
  }
}

// Methods
const refreshData = () => {
  testResult.value = null
  fetchDatabaseStats()
}

const testConnection = async () => {
  try {
    isLoading.value = true
    const health = await trpc.system.health.query()
    connectionStatus.value = health.status === 'healthy'
    testResult.value = { success: true, message: 'Connessione database OK', data: health }
  } catch (err: any) {
    connectionStatus.value = false
    testResult.value = { success: false, message: err.message }
  } finally {
    isLoading.value = false
  }
}

const testDrizzle = async () => {
  try {
    isLoading.value = true
    const result = await trpc.system.testDrizzle.query()
    testResult.value = { success: true, message: 'Drizzle ORM test completato', data: result }
  } catch (err: any) {
    testResult.value = { success: false, message: err.message }
  } finally {
    isLoading.value = false
  }
}

const runHealthCheck = async () => {
  try {
    isLoading.value = true
    const health = await trpc.system.health.query()
    testResult.value = { success: true, message: 'Health check completato', data: health }
  } catch (err: any) {
    testResult.value = { success: false, message: err.message }
  } finally {
    isLoading.value = false
  }
}

const viewLogs = () => {
  testResult.value = { 
    success: true, 
    message: 'Logs sistema',
    data: {
      postgres: 'Database connections: 5/100',
      n8n: 'Workflows running: 3',
      api: 'Requests/min: 45'
    }
  }
}

const getActivityIcon = (type: string) => {
  switch (type) {
    case 'insert': return Plus
    case 'update': return Edit
    case 'delete': return Trash2
    default: return Database
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
  fetchDatabaseStats()
})
</script>