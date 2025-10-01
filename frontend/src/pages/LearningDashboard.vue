<template>
  <MainLayout>
    <div class="learning-dashboard">
      <!-- Header -->
      <div class="dashboard-header">
        <div class="header-content">
          <div class="header-left">
            <Icon icon="mdi:brain" class="header-icon" />
            <div>
              <h1>Milhena Learning Analytics</h1>
              <p class="subtitle">Continuous Improvement Dashboard - Self-Learning AI</p>
            </div>
          </div>
          <div class="header-actions">
            <button @click="refreshData" class="refresh-btn" :disabled="isLoading">
              <Icon :icon="isLoading ? 'mdi:loading' : 'mdi:refresh'" :class="{'animate-spin': isLoading}" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading && !performanceData" class="loading-container">
        <Icon icon="mdi:loading" class="animate-spin loading-icon" />
        <p>Loading learning analytics...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-container">
        <Icon icon="mdi:alert-circle" class="error-icon" />
        <p>{{ error }}</p>
        <button @click="refreshData" class="retry-btn">Retry</button>
      </div>

      <!-- Dashboard Content -->
      <div v-else-if="performanceData" class="dashboard-content">
        <!-- Metrics Cards -->
        <div class="metrics-grid">
          <div class="metric-card">
            <div class="metric-icon accuracy">
              <Icon icon="mdi:target" />
            </div>
            <div class="metric-content">
              <span class="metric-value">{{ formatPercentage(performanceData.metrics.accuracy_rate) }}</span>
              <span class="metric-label">Accuracy Rate</span>
              <span class="metric-trend" :class="getTrendClass(performanceData.improvement_trend)">
                <Icon :icon="getTrendIcon(performanceData.improvement_trend)" />
                {{ performanceData.improvement_trend }}
              </span>
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-icon queries">
              <Icon icon="mdi:message-text" />
            </div>
            <div class="metric-content">
              <span class="metric-value">{{ performanceData.metrics.total_queries }}</span>
              <span class="metric-label">Total Queries</span>
              <span class="metric-info">All-time interactions</span>
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-icon patterns">
              <Icon icon="mdi:lightbulb" />
            </div>
            <div class="metric-content">
              <span class="metric-value">{{ performanceData.high_confidence_patterns }}</span>
              <span class="metric-label">High-Confidence Patterns</span>
              <span class="metric-info">{{ performanceData.pattern_count }} total patterns</span>
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-icon recent">
              <Icon icon="mdi:chart-timeline-variant" />
            </div>
            <div class="metric-content">
              <span class="metric-value">{{ formatPercentage(performanceData.recent_accuracy) }}</span>
              <span class="metric-label">Recent Accuracy</span>
              <span class="metric-info">Last 7 days</span>
            </div>
          </div>
        </div>

        <!-- Improvement Curve Chart -->
        <div class="chart-card">
          <div class="card-header">
            <h3>
              <Icon icon="mdi:chart-line" />
              Accuracy Improvement Over Time
            </h3>
          </div>
          <div class="chart-container">
            <canvas ref="improvementChart"></canvas>
          </div>
        </div>

        <!-- Two-Column Layout -->
        <div class="two-column-layout">
          <!-- Learned Patterns -->
          <div class="patterns-card">
            <div class="card-header">
              <h3>
                <Icon icon="mdi:brain-freeze-outline" />
                Learned Patterns
              </h3>
              <span class="badge">{{ performanceData.learned_patterns.length }}</span>
            </div>
            <div class="patterns-list">
              <div v-if="performanceData.learned_patterns.length === 0" class="empty-state">
                <Icon icon="mdi:brain-freeze" />
                <p>No high-confidence patterns yet</p>
              </div>
              <div v-else v-for="pattern in performanceData.learned_patterns" :key="pattern.pattern"
                   class="pattern-item">
                <div class="pattern-header">
                  <span class="pattern-text">"{{ pattern.pattern }}"</span>
                  <span class="confidence-badge" :class="getConfidenceClass(pattern.confidence)">
                    {{ formatPercentage(pattern.confidence) }}
                  </span>
                </div>
                <div class="pattern-details">
                  <span class="detail-item">
                    <Icon icon="mdi:tag" />
                    {{ pattern.correct_intent }}
                  </span>
                  <span class="detail-item">
                    <Icon icon="mdi:counter" />
                    {{ pattern.occurrences }}x
                  </span>
                  <span class="detail-item">
                    <Icon icon="mdi:percent" />
                    {{ formatPercentage(pattern.success_rate) }} success
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Recent Feedback -->
          <div class="feedback-card">
            <div class="card-header">
              <h3>
                <Icon icon="mdi:comment-multiple" />
                Recent Feedback
              </h3>
              <span class="badge">{{ performanceData.recent_feedback.length }}</span>
            </div>
            <div class="feedback-list">
              <div v-if="performanceData.recent_feedback.length === 0" class="empty-state">
                <Icon icon="mdi:comment-off" />
                <p>No feedback received yet</p>
              </div>
              <div v-else v-for="(feedback, index) in performanceData.recent_feedback.slice().reverse()"
                   :key="index" class="feedback-item">
                <div class="feedback-header">
                  <span class="feedback-type" :class="feedback.feedback_type">
                    <Icon :icon="getFeedbackIcon(feedback.feedback_type)" />
                    {{ feedback.feedback_type }}
                  </span>
                  <span class="feedback-time">{{ formatTimestamp(feedback.timestamp) }}</span>
                </div>
                <div class="feedback-content">
                  <p class="feedback-query">{{ feedback.query }}</p>
                  <div class="feedback-meta">
                    <span class="intent-tag">{{ feedback.intent }}</span>
                    <span class="session-id">{{ feedback.session_id.substring(0, 8) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Top Corrections -->
        <div class="corrections-card">
          <div class="card-header">
            <h3>
              <Icon icon="mdi:file-document-edit" />
              Top Intent Corrections
            </h3>
            <span class="badge">{{ performanceData.top_corrections.length }}</span>
          </div>
          <div class="corrections-list">
            <div v-if="performanceData.top_corrections.length === 0" class="empty-state">
              <Icon icon="mdi:check-circle" />
              <p>No corrections needed - all intents accurate!</p>
            </div>
            <div v-else v-for="correction in performanceData.top_corrections" :key="correction.incorrect"
                 class="correction-item">
              <div class="correction-flow">
                <span class="incorrect-intent">{{ correction.incorrect }}</span>
                <Icon icon="mdi:arrow-right" class="arrow-icon" />
                <span class="correct-intent">{{ correction.correct }}</span>
              </div>
              <span class="correction-count">{{ correction.count }} times</span>
            </div>
          </div>
        </div>

        <!-- Feedback Distribution -->
        <div class="distribution-card">
          <div class="card-header">
            <h3>
              <Icon icon="mdi:chart-donut" />
              Feedback Distribution
            </h3>
          </div>
          <div class="distribution-content">
            <div class="distribution-chart">
              <div class="distribution-item positive">
                <div class="bar" :style="{width: getFeedbackPercentage('positive') + '%'}"></div>
                <span class="label">
                  <Icon icon="mdi:thumb-up" />
                  Positive: {{ performanceData.metrics.positive_feedback }}
                </span>
              </div>
              <div class="distribution-item negative">
                <div class="bar" :style="{width: getFeedbackPercentage('negative') + '%'}"></div>
                <span class="label">
                  <Icon icon="mdi:thumb-down" />
                  Negative: {{ performanceData.metrics.negative_feedback }}
                </span>
              </div>
              <div class="distribution-item corrections">
                <div class="bar" :style="{width: getFeedbackPercentage('corrections') + '%'}"></div>
                <span class="label">
                  <Icon icon="mdi:pencil" />
                  Corrections: {{ performanceData.metrics.corrections }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import MainLayout from '@/layouts/MainLayout.vue'
import axios from 'axios'
import Chart from 'chart.js/auto'

// State
const isLoading = ref(false)
const error = ref<string | null>(null)
const performanceData = ref<any>(null)
const improvementChart = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

// Methods
const refreshData = async () => {
  isLoading.value = true
  error.value = null

  try {
    const response = await axios.get('/api/milhena/performance')

    if (response.data.success) {
      performanceData.value = response.data

      // Render chart after data is loaded
      await new Promise(resolve => setTimeout(resolve, 100))
      renderImprovementChart()
    } else {
      error.value = 'Failed to load performance data'
    }
  } catch (err: any) {
    console.error('Performance data error:', err)
    error.value = err.response?.data?.message || 'Failed to connect to learning system'
  } finally {
    isLoading.value = false
  }
}

const renderImprovementChart = () => {
  if (!improvementChart.value || !performanceData.value) return

  const curve = performanceData.value.metrics.improvement_curve || []

  if (curve.length === 0) {
    return
  }

  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy()
  }

  const ctx = improvementChart.value.getContext('2d')
  if (!ctx) return

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: curve.map((point: any, index: number) => `Q${index + 1}`),
      datasets: [{
        label: 'Accuracy Rate',
        data: curve.map((point: any) => (point.accuracy * 100).toFixed(2)),
        borderColor: '#00d4ff',
        backgroundColor: 'rgba(0, 212, 255, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointBackgroundColor: '#00d4ff',
        pointBorderColor: '#fff',
        pointBorderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#00d4ff',
          bodyColor: '#fff',
          borderColor: '#00d4ff',
          borderWidth: 1,
          padding: 12,
          displayColors: false,
          callbacks: {
            label: (context) => `Accuracy: ${context.parsed.y}%`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: (value) => `${value}%`,
            color: '#8b949e'
          },
          grid: {
            color: 'rgba(139, 148, 158, 0.1)'
          }
        },
        x: {
          ticks: {
            color: '#8b949e'
          },
          grid: {
            color: 'rgba(139, 148, 158, 0.1)'
          }
        }
      }
    }
  })
}

// Helper Functions
const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`
}

const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)

  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`
  return `${Math.floor(minutes / 1440)}d ago`
}

const getTrendClass = (trend: string): string => {
  if (trend === 'improving') return 'trend-up'
  if (trend === 'declining') return 'trend-down'
  return 'trend-stable'
}

const getTrendIcon = (trend: string): string => {
  if (trend === 'improving') return 'mdi:trending-up'
  if (trend === 'declining') return 'mdi:trending-down'
  return 'mdi:trending-neutral'
}

const getConfidenceClass = (confidence: number): string => {
  if (confidence > 0.8) return 'high'
  if (confidence > 0.6) return 'medium'
  return 'low'
}

const getFeedbackIcon = (type: string): string => {
  if (type === 'positive') return 'mdi:thumb-up'
  if (type === 'negative') return 'mdi:thumb-down'
  return 'mdi:pencil'
}

const getFeedbackPercentage = (type: string): number => {
  if (!performanceData.value) return 0

  const total = performanceData.value.metrics.total_queries
  if (total === 0) return 0

  const count = performanceData.value.metrics[`${type === 'corrections' ? 'corrections' : type + '_feedback'}`]
  return (count / total) * 100
}

// Lifecycle
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.learning-dashboard {
  padding: 2rem;
  background: var(--color-background);
  min-height: 100vh;
}

.dashboard-header {
  background: var(--color-surface);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-icon {
  font-size: 3rem;
  color: var(--color-primary);
}

h1 {
  margin: 0;
  font-size: 1.75rem;
  color: var(--color-text);
}

.subtitle {
  margin: 0.25rem 0 0;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: var(--color-primary-dark);
  transform: translateY(-2px);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  gap: 1rem;
}

.loading-icon,
.error-icon {
  font-size: 4rem;
  color: var(--color-primary);
}

.error-icon {
  color: var(--color-error);
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.75rem 2rem;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.metric-card {
  background: var(--color-surface);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  gap: 1rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.metric-card:hover {
  transform: translateY(-4px);
}

.metric-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  color: white;
}

.metric-icon.accuracy { background: linear-gradient(135deg, #00d4ff, #0099cc); }
.metric-icon.queries { background: linear-gradient(135deg, #a259ff, #7722cc); }
.metric-icon.patterns { background: linear-gradient(135deg, #ff6b35, #cc5522); }
.metric-icon.recent { background: linear-gradient(135deg, #00ff88, #00cc66); }

.metric-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.metric-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text);
}

.metric-label {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  margin-top: 0.25rem;
}

.metric-trend,
.metric-info {
  font-size: 0.8rem;
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.trend-up { color: #00ff88; }
.trend-down { color: #ff3366; }
.trend-stable { color: #ffcc00; }

.chart-card,
.patterns-card,
.feedback-card,
.corrections-card,
.distribution-card {
  background: var(--color-surface);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.card-header h3 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  font-size: 1.25rem;
  color: var(--color-text);
}

.badge {
  background: var(--color-primary);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.chart-container {
  height: 300px;
}

.two-column-layout {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
}

.patterns-list,
.feedback-list {
  max-height: 500px;
  overflow-y: auto;
}

.pattern-item,
.feedback-item {
  padding: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.pattern-item:last-child,
.feedback-item:last-child {
  border-bottom: none;
}

.pattern-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.pattern-text {
  font-weight: 600;
  color: var(--color-text);
  font-style: italic;
}

.confidence-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.confidence-badge.high {
  background: rgba(0, 255, 136, 0.2);
  color: #00ff88;
}

.confidence-badge.medium {
  background: rgba(255, 204, 0, 0.2);
  color: #ffcc00;
}

.confidence-badge.low {
  background: rgba(255, 51, 102, 0.2);
  color: #ff3366;
}

.pattern-details {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.feedback-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.feedback-type {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: capitalize;
}

.feedback-type.positive {
  background: rgba(0, 255, 136, 0.2);
  color: #00ff88;
}

.feedback-type.negative {
  background: rgba(255, 51, 102, 0.2);
  color: #ff3366;
}

.feedback-type.correction {
  background: rgba(162, 89, 255, 0.2);
  color: #a259ff;
}

.feedback-time {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.feedback-query {
  margin: 0 0 0.5rem;
  color: var(--color-text);
  font-size: 0.95rem;
}

.feedback-meta {
  display: flex;
  gap: 0.5rem;
}

.intent-tag,
.session-id {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  background: var(--color-background);
  color: var(--color-text-secondary);
}

.corrections-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.correction-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: var(--color-background);
  border-radius: 8px;
}

.correction-flow {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.incorrect-intent {
  padding: 0.5rem 1rem;
  background: rgba(255, 51, 102, 0.2);
  color: #ff3366;
  border-radius: 6px;
  font-weight: 600;
}

.correct-intent {
  padding: 0.5rem 1rem;
  background: rgba(0, 255, 136, 0.2);
  color: #00ff88;
  border-radius: 6px;
  font-weight: 600;
}

.arrow-icon {
  color: var(--color-text-secondary);
}

.correction-count {
  font-weight: 600;
  color: var(--color-text-secondary);
}

.distribution-content {
  padding: 1rem 0;
}

.distribution-chart {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.distribution-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.distribution-item .label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.95rem;
}

.distribution-item.positive .label { color: #00ff88; }
.distribution-item.negative .label { color: #ff3366; }
.distribution-item.corrections .label { color: #a259ff; }

.distribution-item .bar {
  height: 30px;
  border-radius: 6px;
  transition: width 0.5s ease;
}

.distribution-item.positive .bar { background: linear-gradient(90deg, #00ff88, #00cc66); }
.distribution-item.negative .bar { background: linear-gradient(90deg, #ff3366, #cc2244); }
.distribution-item.corrections .bar { background: linear-gradient(90deg, #a259ff, #7722cc); }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  color: var(--color-text-secondary);
}

.empty-state svg {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
