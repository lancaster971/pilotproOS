<template>
  <div class="accuracy-trend-chart">
    <div class="chart-header">
      <h3>Accuracy Trend</h3>
      <div class="chart-subtitle">Last 7 days performance</div>
    </div>

    <div v-if="isLoading" class="chart-loading">
      <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
      <p>Loading chart data...</p>
    </div>

    <div v-else-if="error" class="chart-error">
      <i class="pi pi-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>

    <div v-else-if="!data || data.length === 0" class="chart-empty">
      <i class="pi pi-chart-line" style="font-size: 2rem"></i>
      <p>No accuracy data available yet</p>
    </div>

    <div v-else class="chart-container">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  type ChartConfiguration
} from 'chart.js'
import type { AccuracyDataPoint } from '../../types/learning'

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

const props = defineProps<{
  data: AccuracyDataPoint[]
  isLoading?: boolean
  error?: string | null
}>()

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chartInstance: ChartJS | null = null

// Format timestamp to readable date
const formatDate = (timestamp: string): string => {
  const date = new Date(timestamp)
  return date.toLocaleDateString('it-IT', {
    month: 'short',
    day: 'numeric'
  })
}

// Create or update chart
const renderChart = () => {
  if (!chartCanvas.value) return

  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  if (!props.data || props.data.length === 0) {
    return
  }

  // Prepare data for Chart.js
  const labels = props.data.map(d => formatDate(d.timestamp))
  const accuracyData = props.data.map(d => (d.accuracy * 100).toFixed(1)) // Convert to percentage

  const config: ChartConfiguration = {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Accuracy %',
          data: accuracyData,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.1)',
          borderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#2563eb',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          fill: true,
          tension: 0.3 // Smooth curve
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false // Hide legend for cleaner look
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#ffffff',
          bodyColor: '#e5e5e5',
          borderColor: '#2a2a2a',
          borderWidth: 1,
          padding: 12,
          displayColors: false,
          callbacks: {
            title: (context) => {
              return labels[context[0].dataIndex]
            },
            label: (context) => {
              const point = props.data[context.dataIndex]
              return [
                `Accuracy: ${context.parsed.y}%`,
                `Correct: ${point.correct_queries}/${point.total_queries}`
              ]
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          },
          ticks: {
            color: '#888888',
            font: {
              size: 11
            }
          }
        },
        y: {
          min: 0,
          max: 100,
          grid: {
            color: 'rgba(255, 255, 255, 0.05)',
            drawBorder: false
          },
          ticks: {
            color: '#888888',
            font: {
              size: 11
            },
            callback: (value) => `${value}%`
          }
        }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      }
    }
  }

  chartInstance = new ChartJS(chartCanvas.value, config)
}

// Watch data changes and re-render
watch(() => props.data, () => {
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
.accuracy-trend-chart {
  background: #1a1a1a;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #2a2a2a;
  min-height: 350px;
  display: flex;
  flex-direction: column;
}

.chart-header {
  margin-bottom: 20px;
}

.chart-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 6px 0;
}

.chart-subtitle {
  font-size: 13px;
  color: #888888;
}

.chart-container {
  flex: 1;
  min-height: 300px;
  position: relative;
}

.chart-loading,
.chart-error,
.chart-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #888888;
  min-height: 200px;
}

.chart-error {
  color: #ef4444;
}

.chart-error i {
  font-size: 2rem;
}

.chart-loading p,
.chart-error p,
.chart-empty p {
  margin: 0;
  font-size: 14px;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .accuracy-trend-chart {
    padding: 16px;
    min-height: 280px;
  }

  .chart-header h3 {
    font-size: 16px;
  }

  .chart-subtitle {
    font-size: 12px;
  }

  .chart-container {
    min-height: 220px;
  }
}
</style>
