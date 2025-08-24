<template>
  <div class="premium-chart-container">
    <Chart :type="type" :data="enhancedData" :options="premiumOptions" :class="containerClass" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Chart from 'primevue/chart'

interface Props {
  type: 'line' | 'bar' | 'doughnut' | 'radar'
  data: any
  height?: string
  containerClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  height: 'h-80',
  containerClass: ''
})

// Enhanced data with premium styling
const enhancedData = computed(() => {
  if (!props.data) return props.data
  
  const enhanced = { ...props.data }
  
  // Enhance datasets with premium styling
  if (enhanced.datasets) {
    enhanced.datasets = enhanced.datasets.map((dataset: any, index: number) => ({
      ...dataset,
      // Premium line styling
      borderWidth: 4,
      pointRadius: 8,
      pointHoverRadius: 12,
      pointBorderWidth: 3,
      tension: 0.2,
      borderCapStyle: 'round',
      borderJoinStyle: 'round',
      
      // Premium colors based on data type
      borderColor: index === 0 ? '#00d26a' : '#f87171',
      backgroundColor: index === 0 ? 'rgba(0, 210, 106, 0.15)' : 'rgba(248, 113, 113, 0.08)',
      pointBackgroundColor: index === 0 ? '#00d26a' : '#dc2626',
      pointBorderColor: index === 0 ? '#10b981' : '#f87171',
      
      // Dashed line for errors
      borderDash: index === 1 ? [8, 4] : undefined
    }))
  }
  
  return enhanced
})

// Premium chart options
const premiumOptions = computed(() => ({
  maintainAspectRatio: false,
  responsive: true,
  interaction: {
    intersect: false,
    mode: 'index'
  },
  plugins: {
    legend: {
      position: 'top',
      align: 'end',
      labels: { 
        color: '#e5e7eb',
        padding: 24,
        font: {
          size: 13,
          weight: '600'
        },
        usePointStyle: true,
        pointStyle: 'circle',
        boxWidth: 12,
        boxHeight: 12
      }
    },
    tooltip: {
      backgroundColor: 'rgba(17, 24, 39, 0.95)',
      titleColor: '#fff',
      bodyColor: '#d1d5db',
      borderColor: '#10b981',
      borderWidth: 2,
      cornerRadius: 12,
      displayColors: true,
      padding: 16,
      titleFont: {
        size: 14,
        weight: '600'
      },
      bodyFont: {
        size: 13,
        weight: '500'
      },
      callbacks: {
        title: function(context: any) {
          return `📅 ${context[0].label}`
        },
        label: function(context: any) {
          return `${context.dataset.label}: ${context.parsed.y} esecuzioni`
        }
      }
    }
  },
  scales: {
    x: {
      ticks: { 
        color: '#e5e7eb',
        font: { size: 12, weight: '500' },
        padding: 10,
        maxRotation: 0
      },
      grid: { 
        color: 'rgba(16, 185, 129, 0.12)',
        lineWidth: 1,
        drawOnChartArea: true,
        borderDash: [2, 2]
      },
      border: {
        color: '#10b981',
        width: 2
      }
    },
    y: {
      ticks: { 
        color: '#e5e7eb',
        font: { size: 12, weight: '500' },
        padding: 15,
        callback: function(value: any) {
          return value + ' exec'
        }
      },
      grid: { 
        color: 'rgba(16, 185, 129, 0.08)',
        lineWidth: 1,
        drawBorder: false,
        borderDash: [1, 3]
      },
      border: {
        color: '#10b981',
        width: 2
      },
      beginAtZero: true
    }
  },
  elements: {
    point: {
      hoverBackgroundColor: '#00d26a',
      hoverBorderColor: '#fff',
      hoverBorderWidth: 4
    },
    line: {
      borderJoinStyle: 'round',
      borderCapStyle: 'round'
    }
  },
  animation: {
    duration: 1200,
    easing: 'easeInOutCubic'
  }
}))
</script>

<style scoped>
.premium-chart-container {
  position: relative;
}

.premium-chart-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.6), transparent);
  border-radius: 1px;
}
</style>