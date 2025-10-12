<template>
  <div class="pattern-visualization">
    <div class="viz-header">
      <h3>Pattern Usage Heatmap</h3>
      <div class="viz-subtitle">Usage distribution by category and hour (24h)</div>
    </div>

    <div v-if="isLoading" class="viz-loading">
      <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
      <p>Loading heatmap...</p>
    </div>

    <div v-else-if="error" class="viz-error">
      <i class="pi pi-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>

    <div v-else-if="!data || data.length === 0" class="viz-empty">
      <i class="pi pi-chart-bar" style="font-size: 2rem"></i>
      <p>No pattern data available</p>
    </div>

    <div v-else class="viz-container">
      <svg ref="svgElement" :viewBox="`0 0 ${width} ${height}`" preserveAspectRatio="xMidYMid meet"></svg>

      <!-- Tooltip -->
      <div v-if="tooltip.visible" class="heatmap-tooltip" :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }">
        <div class="tooltip-category">{{ tooltip.category }}</div>
        <div class="tooltip-row">
          <span class="tooltip-label">Hour:</span>
          <span class="tooltip-value">{{ tooltip.hour }}:00</span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">Usage:</span>
          <span class="tooltip-value">{{ tooltip.usage }} queries</span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">Accuracy:</span>
          <span class="tooltip-value">{{ tooltip.accuracy }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as d3 from 'd3'
import type { HeatmapDataPoint } from '../../types/learning'

const props = defineProps<{
  data: HeatmapDataPoint[]
  isLoading?: boolean
  error?: string | null
}>()

// SVG dimensions
const width = 1100
const height = 400
const margin = { top: 40, right: 120, bottom: 60, left: 120 }

// Refs
const svgElement = ref<SVGSVGElement | null>(null)
const tooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  category: '',
  hour: 0,
  usage: 0,
  accuracy: 0
})

// Extract unique categories and hours from data
const getCategories = (): string[] => {
  if (!props.data || props.data.length === 0) return []
  return [...new Set(props.data.map(d => d.category))]
}

const getHours = (): number[] => {
  return Array.from({ length: 24 }, (_, i) => i)
}

// Render D3.js heatmap
const renderHeatmap = () => {
  if (!svgElement.value || !props.data || props.data.length === 0) return

  // Clear existing SVG content
  d3.select(svgElement.value).selectAll('*').remove()

  const svg = d3.select(svgElement.value)
  const categories = getCategories()
  const hours = getHours()

  // Calculate scales
  const xScale = d3.scaleBand()
    .domain(hours.map(String))
    .range([margin.left, width - margin.right])
    .padding(0.05)

  const yScale = d3.scaleBand()
    .domain(categories)
    .range([margin.top, height - margin.bottom])
    .padding(0.05)

  // Color scale (blue to green based on usage)
  const maxUsage = d3.max(props.data, d => d.usage_count) || 1
  const colorScale = d3.scaleSequential()
    .domain([0, maxUsage])
    .interpolator(d3.interpolateRgb('#1e3a8a', '#10b981')) // Dark blue to green

  // Draw heatmap cells
  const cells = svg.selectAll('.cell')
    .data(props.data)
    .enter()
    .append('rect')
    .attr('class', 'cell')
    .attr('x', d => xScale(String(d.hour)) || 0)
    .attr('y', d => yScale(d.category) || 0)
    .attr('width', xScale.bandwidth())
    .attr('height', yScale.bandwidth())
    .attr('fill', d => d.usage_count === 0 ? '#0a0a0a' : colorScale(d.usage_count))
    .attr('stroke', '#2a2a2a')
    .attr('stroke-width', 1)
    .attr('rx', 4)
    .style('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      // Highlight cell
      d3.select(event.currentTarget)
        .attr('stroke', '#2563eb')
        .attr('stroke-width', 2)

      // Show tooltip
      const rect = event.currentTarget.getBoundingClientRect()
      const container = svgElement.value!.getBoundingClientRect()

      tooltip.value = {
        visible: true,
        x: rect.left - container.left + rect.width / 2,
        y: rect.top - container.top - 10,
        category: d.category,
        hour: d.hour,
        usage: d.usage_count,
        accuracy: Math.round(d.accuracy * 100)
      }
    })
    .on('mouseleave', (event) => {
      // Remove highlight
      d3.select(event.currentTarget)
        .attr('stroke', '#2a2a2a')
        .attr('stroke-width', 1)

      // Hide tooltip
      tooltip.value.visible = false
    })

  // Add X axis (hours)
  const xAxis = d3.axisBottom(xScale)
    .tickFormat(d => `${d}h`)

  svg.append('g')
    .attr('class', 'x-axis')
    .attr('transform', `translate(0, ${height - margin.bottom})`)
    .call(xAxis)
    .selectAll('text')
    .style('text-anchor', 'middle')
    .style('fill', '#888888')
    .style('font-size', '11px')

  // Add Y axis (categories)
  const yAxis = d3.axisLeft(yScale)
    .tickFormat(d => formatCategory(d as string))

  svg.append('g')
    .attr('class', 'y-axis')
    .attr('transform', `translate(${margin.left}, 0)`)
    .call(yAxis)
    .selectAll('text')
    .style('text-anchor', 'end')
    .style('fill', '#888888')
    .style('font-size', '11px')

  // Add X axis label
  svg.append('text')
    .attr('x', (width - margin.left - margin.right) / 2 + margin.left)
    .attr('y', height - 20)
    .style('text-anchor', 'middle')
    .style('fill', '#e5e5e5')
    .style('font-size', '13px')
    .style('font-weight', '600')
    .text('Hour of Day')

  // Add Y axis label
  svg.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('x', -(height - margin.top - margin.bottom) / 2 - margin.top)
    .attr('y', 30)
    .style('text-anchor', 'middle')
    .style('fill', '#e5e5e5')
    .style('font-size', '13px')
    .style('font-weight', '600')
    .text('Pattern Category')

  // Add legend
  const legendWidth = 200
  const legendHeight = 20
  const legendX = width - margin.right + 20
  const legendY = margin.top

  // Legend gradient
  const defs = svg.append('defs')
  const gradient = defs.append('linearGradient')
    .attr('id', 'legend-gradient')
    .attr('x1', '0%')
    .attr('x2', '100%')
    .attr('y1', '0%')
    .attr('y2', '0%')

  gradient.append('stop')
    .attr('offset', '0%')
    .attr('stop-color', '#1e3a8a')

  gradient.append('stop')
    .attr('offset', '100%')
    .attr('stop-color', '#10b981')

  // Legend rectangle
  svg.append('rect')
    .attr('x', legendX)
    .attr('y', legendY)
    .attr('width', legendWidth)
    .attr('height', legendHeight)
    .style('fill', 'url(#legend-gradient)')
    .attr('stroke', '#2a2a2a')
    .attr('stroke-width', 1)
    .attr('rx', 4)

  // Legend labels
  svg.append('text')
    .attr('x', legendX)
    .attr('y', legendY - 8)
    .style('fill', '#888888')
    .style('font-size', '11px')
    .text('0')

  svg.append('text')
    .attr('x', legendX + legendWidth)
    .attr('y', legendY - 8)
    .style('text-anchor', 'end')
    .style('fill', '#888888')
    .style('font-size', '11px')
    .text(`${maxUsage}`)

  svg.append('text')
    .attr('x', legendX + legendWidth / 2)
    .attr('y', legendY + legendHeight + 20)
    .style('text-anchor', 'middle')
    .style('fill', '#e5e5e5')
    .style('font-size', '12px')
    .style('font-weight', '600')
    .text('Usage Count')
}

// Format category name
const formatCategory = (category: string): string => {
  return category
    .replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// Watch data changes and re-render
watch(() => props.data, () => {
  renderHeatmap()
}, { deep: true })

onMounted(() => {
  renderHeatmap()
})

onBeforeUnmount(() => {
  tooltip.value.visible = false
})
</script>

<style scoped>
.pattern-visualization {
  background: #1a1a1a;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #2a2a2a;
  position: relative;
}

.viz-header {
  margin-bottom: 20px;
}

.viz-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 6px 0;
}

.viz-subtitle {
  font-size: 13px;
  color: #888888;
}

.viz-container {
  position: relative;
  width: 100%;
  overflow: visible;
}

.viz-container svg {
  width: 100%;
  height: auto;
  display: block;
}

.viz-loading,
.viz-error,
.viz-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #888888;
  padding: 80px 20px;
  min-height: 400px;
}

.viz-error {
  color: #ef4444;
}

.viz-error i {
  font-size: 2rem;
}

.viz-loading p,
.viz-error p,
.viz-empty p {
  margin: 0;
  font-size: 14px;
}

/* Heatmap tooltip */
.heatmap-tooltip {
  position: absolute;
  background: rgba(0, 0, 0, 0.95);
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  padding: 12px;
  pointer-events: none;
  z-index: 1000;
  transform: translateX(-50%) translateY(-100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  min-width: 180px;
}

.tooltip-category {
  font-weight: 600;
  color: #2563eb;
  font-size: 13px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #2a2a2a;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 4px 0;
  font-size: 12px;
}

.tooltip-label {
  color: #888888;
}

.tooltip-value {
  color: #e5e5e5;
  font-weight: 600;
}

/* D3.js axis styling */
.viz-container :deep(.x-axis path),
.viz-container :deep(.y-axis path) {
  stroke: #2a2a2a;
}

.viz-container :deep(.x-axis line),
.viz-container :deep(.y-axis line) {
  stroke: #2a2a2a;
}

/* Mobile responsive */
@media (max-width: 1024px) {
  .pattern-visualization {
    padding: 16px;
  }

  .viz-header h3 {
    font-size: 16px;
  }

  .viz-subtitle {
    font-size: 12px;
  }
}

@media (max-width: 768px) {
  .viz-container svg {
    min-height: 300px;
  }

  .heatmap-tooltip {
    font-size: 11px;
    padding: 10px;
    min-width: 150px;
  }
}
</style>
