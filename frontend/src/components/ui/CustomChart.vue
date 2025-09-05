<template>
  <div :class="['relative', containerClass]">
    <canvas :id="chartId" :class="canvasClass"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  RadialLinearScale
} from 'chart.js'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  RadialLinearScale
)

interface Props {
  type: 'line' | 'bar' | 'doughnut' | 'pie' | 'radar'
  data: any
  options?: any
  containerClass?: string
  canvasClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  containerClass: 'w-full h-full',
  canvasClass: 'w-full h-full',
  options: () => ({})
})

const chartId = ref(`chart-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`)
let chartInstance: ChartJS | null = null

const createChart = async () => {
  if (chartInstance) {
    chartInstance.destroy()
  }

  await nextTick()
  
  const canvas = document.getElementById(chartId.value) as HTMLCanvasElement
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  chartInstance = new ChartJS(ctx, {
    type: props.type,
    data: props.data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      ...props.options
    }
  })
}

const updateChart = () => {
  if (chartInstance) {
    chartInstance.data = props.data
    chartInstance.options = { 
      responsive: true, 
      maintainAspectRatio: false,
      ...props.options 
    }
    chartInstance.update()
  }
}

watch(() => props.data, updateChart, { deep: true })
watch(() => props.options, updateChart, { deep: true })

onMounted(() => {
  createChart()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>