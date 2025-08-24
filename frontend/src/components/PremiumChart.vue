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

// Ultra-premium data styling
const enhancedData = computed(() => {
  if (!props.data) return props.data
  
  const enhanced = { ...props.data }
  
  // Create premium gradients for datasets
  if (enhanced.datasets) {
    enhanced.datasets = enhanced.datasets.map((dataset: any, index: number) => {
      if (index === 0) {
        // Success line - Ultra premium emerald
        return {
          ...dataset,
          borderColor: '#00ff88', // Neon emerald
          backgroundColor: createGradient('success'),
          borderWidth: 5,
          pointRadius: 10,
          pointHoverRadius: 16,
          pointBorderWidth: 4,
          pointBackgroundColor: '#00ff88',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#00d26a',
          pointHoverBorderColor: '#00ff88',
          tension: 0.3,
          fill: true,
          borderCapStyle: 'round',
          borderJoinStyle: 'round',
          shadowColor: 'rgba(0, 255, 136, 0.6)',
          shadowBlur: 15,
          shadowOffsetY: 4
        }
      } else {
        // Error line - Premium red with dash
        return {
          ...dataset,
          borderColor: '#ff6b6b',
          backgroundColor: createGradient('error'),
          borderWidth: 4,
          pointRadius: 8,
          pointHoverRadius: 14,
          pointBorderWidth: 3,
          pointBackgroundColor: '#ff6b6b',
          pointBorderColor: '#fff',
          tension: 0.3,
          fill: true,
          borderDash: [12, 6],
          borderCapStyle: 'round'
        }
      }
    })
  }
  
  return enhanced
})

// Create premium gradients
function createGradient(type: 'success' | 'error') {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  
  if (!ctx) return type === 'success' ? 'rgba(0, 210, 106, 0.1)' : 'rgba(255, 107, 107, 0.1)'
  
  const gradient = ctx.createLinearGradient(0, 0, 0, 400)
  
  if (type === 'success') {
    gradient.addColorStop(0, 'rgba(0, 255, 136, 0.3)')
    gradient.addColorStop(0.5, 'rgba(0, 210, 106, 0.15)')
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.05)')
  } else {
    gradient.addColorStop(0, 'rgba(255, 107, 107, 0.2)')
    gradient.addColorStop(0.5, 'rgba(239, 68, 68, 0.1)')
    gradient.addColorStop(1, 'rgba(220, 38, 38, 0.05)')
  }
  
  return gradient
}

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
        color: '#f3f4f6',
        font: { size: 13, weight: '600' },
        padding: 12,
        maxRotation: 0
      },
      grid: { 
        color: 'rgba(0, 255, 136, 0.15)',
        lineWidth: 2,
        drawOnChartArea: true,
        borderDash: [1, 8]
      },
      border: {
        display: false
      }
    },
    y: {
      ticks: { 
        color: '#f3f4f6',
        font: { size: 13, weight: '600' },
        padding: 18,
        callback: function(value: any) {
          return '⚡ ' + value
        }
      },
      grid: { 
        color: 'rgba(0, 255, 136, 0.1)',
        lineWidth: 1,
        drawBorder: false,
        borderDash: [2, 6]
      },
      border: {
        display: false
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
  background: rgba(17, 24, 39, 0.8);
  backdrop-filter: blur(12px);
  border-radius: 12px;
  padding: 1rem;
  border: 1px solid rgba(0, 255, 136, 0.2);
  box-shadow: 
    0 0 30px rgba(0, 255, 136, 0.1),
    0 8px 25px rgba(0, 0, 0, 0.1);
}

.premium-chart-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(0, 255, 136, 0.8), 
    rgba(0, 210, 106, 0.6),
    rgba(0, 255, 136, 0.8), 
    transparent
  );
  border-radius: 12px 12px 0 0;
  animation: chartGlow 4s ease-in-out infinite;
}

.premium-chart-container::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 255, 136, 0.4), transparent);
  border-radius: 0 0 12px 12px;
}

@keyframes chartGlow {
  0%, 100% { 
    opacity: 0.6;
    filter: blur(0px);
  }
  50% { 
    opacity: 1;
    filter: blur(1px);
  }
}

/* Chart.js canvas styling */
:deep(canvas) {
  border-radius: 8px;
  filter: drop-shadow(0 4px 20px rgba(0, 255, 136, 0.1));
}
</style>