<template>
  <div class="cost-metrics-card">
    <div class="card-header">
      <h3>Cost Savings</h3>
      <div class="card-subtitle">Fast-path vs LLM performance</div>
    </div>

    <div v-if="isLoading" class="card-loading">
      <i class="pi pi-spin pi-spinner" style="font-size: 1.5rem"></i>
    </div>

    <div v-else-if="error" class="card-error">
      <i class="pi pi-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>

    <div v-else-if="!costData" class="card-empty">
      <i class="pi pi-chart-pie"></i>
      <p>No cost data</p>
    </div>

    <div v-else class="card-content">
      <!-- Savings metrics -->
      <div class="metrics-grid">
        <div class="metric-item">
          <div class="metric-label">Monthly</div>
          <div class="metric-value">${{ formatCurrency(costData.monthly) }}</div>
        </div>

        <div class="metric-item">
          <div class="metric-label">Total</div>
          <div class="metric-value highlight">${{ formatCurrency(costData.total) }}</div>
        </div>
      </div>

      <!-- Doughnut chart -->
      <div class="chart-container">
        <canvas ref="chartCanvas"></canvas>
      </div>

      <!-- Coverage stats -->
      <div class="coverage-stats">
        <div class="stat-row">
          <div class="stat-indicator fast-path"></div>
          <span class="stat-label">Fast-path</span>
          <span class="stat-value">{{ costData.fastPathCoverage.toFixed(1) }}%</span>
        </div>
        <div class="stat-row">
          <div class="stat-indicator llm"></div>
          <span class="stat-label">LLM</span>
          <span class="stat-value">{{ costData.llmCoverage.toFixed(1) }}%</span>
        </div>
      </div>

      <!-- ROI message -->
      <div class="roi-message">
        <i class="pi pi-bolt"></i>
        <span>{{ getRoiMessage() }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  type ChartConfiguration
} from 'chart.js'

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{
  costData: {
    monthly: number
    total: number
    fastPathCoverage: number
    llmCoverage: number
  } | null
  isLoading?: boolean
  error?: string | null
}>()

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chartInstance: ChartJS | null = null

// Format currency
const formatCurrency = (value: number): string => {
  return value.toFixed(2)
}

// Get ROI message
const getRoiMessage = (): string => {
  if (!props.costData) return ''

  const coverage = props.costData.fastPathCoverage
  if (coverage >= 60) return 'Excellent optimization!'
  if (coverage >= 40) return 'Good progress!'
  if (coverage >= 20) return 'Room for improvement'
  return 'Learning in progress'
}

// Render doughnut chart
const renderChart = () => {
  if (!chartCanvas.value || !props.costData) return

  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  const config: ChartConfiguration = {
    type: 'doughnut',
    data: {
      labels: ['Fast-path', 'LLM'],
      datasets: [
        {
          data: [props.costData.fastPathCoverage, props.costData.llmCoverage],
          backgroundColor: ['#10b981', '#2563eb'],
          borderColor: ['#10b981', '#2563eb'],
          borderWidth: 2,
          hoverOffset: 8
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%', // Doughnut thickness
      plugins: {
        legend: {
          display: false // Hide legend (we show custom stats)
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.9)',
          titleColor: '#ffffff',
          bodyColor: '#e5e5e5',
          borderColor: '#2a2a2a',
          borderWidth: 1,
          padding: 12,
          displayColors: true,
          callbacks: {
            label: (context) => {
              const label = context.label || ''
              const value = context.parsed || 0
              return `${label}: ${value.toFixed(1)}%`
            }
          }
        }
      }
    }
  }

  chartInstance = new ChartJS(chartCanvas.value, config)
}

// Watch data changes and re-render
watch(() => props.costData, () => {
  renderChart()
}, { deep: true })

onMounted(() => {
  renderChart()
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})
</script>

<style scoped>
.cost-metrics-card {
  background: #1a1a1a;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #2a2a2a;
  display: flex;
  flex-direction: column;
  min-height: 400px;
}

.card-header {
  margin-bottom: 20px;
}

.card-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 6px 0;
}

.card-subtitle {
  font-size: 13px;
  color: #888888;
}

.card-loading,
.card-error,
.card-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #888888;
}

.card-error {
  color: #ef4444;
}

.card-error i {
  font-size: 1.5rem;
}

.card-loading p,
.card-error p,
.card-empty p {
  margin: 0;
  font-size: 13px;
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Metrics grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.metric-item {
  background: #0a0a0a;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #2a2a2a;
  text-align: center;
}

.metric-label {
  font-size: 12px;
  color: #888888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: #10b981;
  font-variant-numeric: tabular-nums;
}

.metric-value.highlight {
  color: #2563eb;
  font-size: 28px;
}

/* Chart container */
.chart-container {
  flex: 1;
  position: relative;
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-container canvas {
  max-width: 220px;
  max-height: 220px;
}

/* Coverage stats */
.coverage-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: #0a0a0a;
  border-radius: 8px;
  border: 1px solid #2a2a2a;
}

.stat-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stat-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.stat-indicator.fast-path {
  background: #10b981;
}

.stat-indicator.llm {
  background: #2563eb;
}

.stat-label {
  flex: 1;
  font-size: 13px;
  color: #e5e5e5;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #e5e5e5;
  min-width: 50px;
  text-align: right;
}

/* ROI message */
.roi-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: rgba(37, 99, 235, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(37, 99, 235, 0.3);
  color: #2563eb;
  font-size: 13px;
  font-weight: 600;
}

.roi-message i {
  font-size: 16px;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .cost-metrics-card {
    padding: 16px;
    min-height: 350px;
  }

  .card-header h3 {
    font-size: 16px;
  }

  .card-subtitle {
    font-size: 12px;
  }

  .metrics-grid {
    gap: 12px;
  }

  .metric-item {
    padding: 12px;
  }

  .metric-value {
    font-size: 20px;
  }

  .metric-value.highlight {
    font-size: 24px;
  }

  .chart-container canvas {
    max-width: 180px;
    max-height: 180px;
  }

  .coverage-stats {
    padding: 12px;
  }

  .roi-message {
    font-size: 12px;
    padding: 10px;
  }
}
</style>
