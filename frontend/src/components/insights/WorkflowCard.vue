<template>
  <Card class="workflow-card">
    <!-- Status Badge Animato -->
    <div style="position: absolute; top: -8px; right: -8px; z-index: 10;">
      <Badge
        :value="statusLabel"
        :severity="statusSeverity"
        :class="workflow.active ? 'animate-pulse' : ''"
      />
    </div>

    <!-- Background Gradient Effect -->
    <div style="position: absolute; inset: 0; opacity: 0.05;"
         :style="{
           background: workflow.critical
             ? 'linear-gradient(135deg, rgb(239, 68, 68), rgb(249, 115, 22))'
             : workflow.active
               ? 'linear-gradient(135deg, rgb(34, 197, 94), rgb(16, 185, 129))'
               : 'linear-gradient(135deg, rgb(107, 114, 128), rgb(75, 85, 99))'
         }">
    </div>

    <template #content>
      <div style="position: relative; z-index: 10; padding: 1rem;">
        <!-- Header con Icona e Nome -->
        <div style="display: flex; align-items: flex-start; gap: 0.75rem; margin-bottom: 1rem;">
          <div class="workflow-icon"
               :class="{ 'workflow-icon-active': workflow.active }"
               :style="workflow.active ? {
                 background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.3), rgba(16, 185, 129, 0.1))',
                 boxShadow: '0 10px 15px -3px rgba(16, 185, 129, 0.2)'
               } : {
                 background: 'rgba(31, 41, 55, 0.5)'
               }">
            <Icon :icon="getWorkflowIcon()" class="text-2xl"
                  :class="workflow.active ? 'text-primary' : 'text-text-muted'" />
          </div>
          <div style="flex: 1; min-width: 0;">
            <h3 style="font-weight: bold; color: white; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.875rem;" :title="workflow.name">
              {{ workflow.name }}
            </h3>
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.25rem;">
              <span style="font-size: 0.75rem; color: #9ca3af;">{{ workflow.id.slice(0, 8) }}...</span>
              <div v-if="workflow.lastExecution" style="display: flex; align-items: center; gap: 0.25rem;">
                <div :style="{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: isRecentExecution() ? '#10b981' : '#9ca3af'
                }"></div>
                <span style="font-size: 0.75rem; color: #9ca3af;">{{ formatLastExecution() }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- KPI Grid - Metriche Chiave -->
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; margin-bottom: 0.75rem;">
          <!-- Success Rate -->
          <div style="text-align: center; padding: 0.5rem; background: rgba(31, 41, 55, 0.3); border-radius: 0.5rem;">
            <div style="font-size: 1.125rem; font-weight: bold;"
                 :style="{ color: getSuccessRateColor() }">
              {{ workflow.successRate || 0 }}%
            </div>
            <div style="font-size: 0.75rem; color: #9ca3af;">Success</div>
          </div>

          <!-- 24h Executions -->
          <div style="text-align: center; padding: 0.5rem; background: rgba(31, 41, 55, 0.3); border-radius: 0.5rem;">
            <div style="font-size: 1.125rem; font-weight: bold; color: white;">
              {{ workflow.last24hExecutions || 0 }}
            </div>
            <div style="font-size: 0.75rem; color: #9ca3af;">24h Runs</div>
          </div>

          <!-- Average Time -->
          <div style="text-align: center; padding: 0.5rem; background: rgba(31, 41, 55, 0.3); border-radius: 0.5rem;">
            <div style="font-size: 1.125rem; font-weight: bold; color: white;">
              {{ formatDuration(workflow.avgRunTime) }}
            </div>
            <div style="font-size: 0.75rem; color: #9ca3af;">Avg Time</div>
          </div>

          <!-- Efficiency Score -->
          <div style="text-align: center; padding: 0.5rem; background: rgba(31, 41, 55, 0.3); border-radius: 0.5rem;">
            <div style="font-size: 1.125rem; font-weight: bold;"
                 :style="{ color: getEfficiencyColor() }">
              {{ workflow.efficiencyScore || 0 }}
            </div>
            <div style="font-size: 0.75rem; color: #9ca3af;">Efficiency</div>
          </div>
        </div>

        <!-- Capabilities Pills -->
        <div v-if="workflow.capabilities?.length > 0" style="display: flex; flex-wrap: wrap; gap: 0.25rem; margin-bottom: 0.75rem;">
          <span v-for="(capability, index) in workflow.capabilities.slice(0, 2)"
                :key="index"
                style="font-size: 0.75rem; padding: 0.25rem 0.5rem; background: rgba(16, 185, 129, 0.1); color: #10b981; border-radius: 9999px;">
            {{ truncateCapability(capability) }}
          </span>
          <span v-if="workflow.capabilities.length > 2"
                style="font-size: 0.75rem; padding: 0.25rem 0.5rem; background: rgba(31, 41, 55, 0.3); color: #9ca3af; border-radius: 9999px;">
            +{{ workflow.capabilities.length - 2 }}
          </span>
        </div>

        <!-- Action Buttons -->
        <div style="display: flex; gap: 0.5rem;">
          <Button
            icon="pi pi-chart-line"
            label="Dashboard"
            @click="openDashboard"
            style="flex: 1;"
            size="small"
            severity="secondary"
            outlined
          />
          <Button
            v-if="workflow.active"
            icon="pi pi-play"
            @click="executeWorkflow"
            size="small"
            severity="success"
            :title="'Execute Now'"
          />
          <Button
            v-else
            icon="pi pi-power-off"
            @click="activateWorkflow"
            size="small"
            severity="warning"
            :title="'Activate'"
          />
        </div>
      </div>
    </template>
  </Card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Chart from 'primevue/chart'
import Skeleton from 'primevue/skeleton'
import { Icon } from '@iconify/vue'
import { useToast } from 'primevue/usetoast'

const router = useRouter()
const toast = useToast()

const props = defineProps({
  workflow: {
    type: Object,
    required: true
  }
})

// Computed properties
const statusLabel = computed(() => {
  if (props.workflow.critical) return 'CRITICAL'
  if (props.workflow.active) return 'ACTIVE'
  return 'INACTIVE'
})

const statusSeverity = computed(() => {
  if (props.workflow.critical) return 'danger'
  if (props.workflow.active) return 'success'
  return 'secondary'
})

const hasTrendData = computed(() => {
  return props.workflow.trend && props.workflow.trend.length > 0
})

const miniChartData = computed(() => ({
  labels: ['', '', '', '', '', '', ''],
  datasets: [{
    data: props.workflow.trend || [0, 0, 0, 0, 0, 0, 0],
    borderColor: props.workflow.successRate >= 80 ? '#10b981' : '#f59e0b',
    borderWidth: 2,
    fill: false,
    tension: 0.4,
    pointRadius: 0
  }]
}))

const miniChartOptions = ref({
  maintainAspectRatio: false,
  responsive: true,
  plugins: {
    legend: { display: false },
    tooltip: { enabled: false }
  },
  scales: {
    x: { display: false },
    y: { display: false }
  }
})

// Helper functions
const getWorkflowIcon = () => {
  // Icon based on workflow type/capabilities
  if (props.workflow.capabilities?.some(c => c.toLowerCase().includes('ai'))) {
    return 'lucide:brain'
  }
  if (props.workflow.capabilities?.some(c => c.toLowerCase().includes('email'))) {
    return 'lucide:mail'
  }
  if (props.workflow.capabilities?.some(c => c.toLowerCase().includes('database'))) {
    return 'lucide:database'
  }
  if (props.workflow.active) {
    return 'lucide:activity'
  }
  return 'lucide:workflow'
}

const getSuccessRateColor = () => {
  const rate = props.workflow.successRate
  if (rate >= 95) return '#10b981'
  if (rate >= 80) return '#fbbf24'
  return '#ef4444'
}

const getEfficiencyColor = () => {
  const score = props.workflow.efficiencyScore
  if (score >= 80) return '#10b981'
  if (score >= 60) return '#fbbf24'
  return '#fb923c'
}

const formatDuration = (ms: number) => {
  if (!ms) return '0ms'
  if (ms < 1000) return `${Math.round(ms)}ms`
  if (ms < 60000) return `${Math.round(ms / 1000)}s`
  return `${Math.round(ms / 60000)}m`
}

const formatLastExecution = () => {
  if (!props.workflow.lastExecution) return 'Never'
  const date = new Date(props.workflow.lastExecution)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}

const isRecentExecution = () => {
  if (!props.workflow.lastExecution) return false
  const date = new Date(props.workflow.lastExecution)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  return diff < 3600000 // Less than 1 hour
}

const truncateCapability = (capability: string) => {
  const words = capability.split(' ')
  if (words.length <= 3) return capability
  return words.slice(0, 3).join(' ') + '...'
}

// Actions
const openDashboard = () => {
  // Use window.location to avoid Vue Router issues during development
  window.location.href = `/dashboard/workflow/${props.workflow.id}`
}

const executeWorkflow = async () => {
  toast.add({
    severity: 'info',
    summary: 'Executing Workflow',
    detail: `Starting ${props.workflow.name}...`,
    life: 3000
  })
  // TODO: Call API to execute workflow
}

const activateWorkflow = async () => {
  toast.add({
    severity: 'warning',
    summary: 'Activating Workflow',
    detail: `Activating ${props.workflow.name}...`,
    life: 3000
  })
  // TODO: Call API to activate workflow
}
</script>

<style scoped>
.workflow-card {
  transition: all 0.3s ease;
}

.workflow-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>