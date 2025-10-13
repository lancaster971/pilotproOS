<template>
  <MainLayout>
    <div class="learning-dashboard">
    <!-- Header Section -->
    <div class="dashboard-header">
      <div class="header-left">
        <h1>Learning System Dashboard</h1>
        <p class="header-subtitle">Auto-Learning Performance & Analytics</p>
      </div>

      <div class="header-right">
        <button
          @click="handleReloadPatterns"
          :disabled="store.isLoading"
          class="reload-btn"
          title="Reload patterns from database"
        >
          <Icon :icon="store.isLoading ? 'mdi:loading' : 'mdi:refresh'" :class="{ spin: store.isLoading }" />
          <span>Reload Patterns</span>
        </button>

        <div v-if="store.lastUpdated" class="last-updated">
          <Icon icon="mdi:clock-outline" />
          <span>{{ formatLastUpdated(store.lastUpdated) }}</span>
        </div>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="store.error" class="error-alert">
      <Icon icon="mdi:alert-circle" />
      <span>{{ store.error }}</span>
      <button @click="handleRetry" class="retry-btn">
        <Icon icon="mdi:refresh" />
        Retry
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="store.isLoading && !store.metrics" class="loading-state">
      <i class="pi pi-spin pi-spinner" style="font-size: 3rem"></i>
      <p>Loading learning metrics...</p>
    </div>

    <!-- Dashboard Content -->
    <div v-else class="dashboard-content">
      <!-- Section 1: Metrics Cards -->
      <div class="metrics-cards">
        <div class="metric-card">
          <div class="metric-icon total">
            <Icon icon="mdi:database" />
          </div>
          <div class="metric-info">
            <div class="metric-label">Total Patterns</div>
            <div class="metric-value">{{ store.metrics?.total_patterns || 0 }}</div>
            <div class="metric-detail">
              <span class="auto">{{ store.metrics?.auto_learned_count || 0 }} auto</span>
              <span class="separator">•</span>
              <span class="hardcoded">{{ store.metrics?.hardcoded_count || 0 }} hardcoded</span>
            </div>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon accuracy">
            <Icon icon="mdi:target" />
          </div>
          <div class="metric-info">
            <div class="metric-label">Accuracy Rate</div>
            <div class="metric-value">{{ formatPercentage(store.metrics?.accuracy_rate || 0) }}</div>
            <div class="metric-detail">
              {{ store.metrics?.total_usages || 0 }} total queries
            </div>
          </div>
        </div>

        <CostMetricsCard
          :costData="store.costTrend"
          :isLoading="store.isLoading"
          :error="store.error"
          class="cost-card"
        />
      </div>

      <!-- Section 2: Accuracy Trend Chart -->
      <div class="chart-section">
        <AccuracyTrendChart
          :data="store.accuracyTrend"
          :isLoading="store.isLoading"
          :error="store.error"
        />
      </div>

      <!-- Section 3: Split Section (Table + Timeline) -->
      <div class="split-section">
        <div class="split-left">
          <PatternPerformanceTable
            :patterns="store.topPatterns"
            :isLoading="store.isLoading"
            :error="store.error"
          />
        </div>

        <div class="split-right">
          <FeedbackTimeline
            :events="store.recentFeedback"
            :isLoading="store.isLoading"
            :error="store.error"
          />
        </div>
      </div>

      <!-- Section 4: Pattern Visualization Heatmap -->
      <div class="heatmap-section">
        <PatternVisualization
          :data="store.heatmapData"
          :isLoading="store.isLoading"
          :error="store.error"
        />
      </div>
    </div>
  </div>
  </MainLayout>
</template>

<script setup lang="ts">
import MainLayout from '../components/layout/MainLayout.vue'
import { onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import { useLearningStore } from '../stores/learning-store'
import { useToast } from 'vue-toastification'

// Components
import AccuracyTrendChart from '../components/learning/AccuracyTrendChart.vue'
import PatternPerformanceTable from '../components/learning/PatternPerformanceTable.vue'
import FeedbackTimeline from '../components/learning/FeedbackTimeline.vue'
import PatternVisualization from '../components/learning/PatternVisualization.vue'
import CostMetricsCard from '../components/learning/CostMetricsCard.vue'

// Store & Toast
const store = useLearningStore()
const toast = useToast()

// Format percentage
const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`
}

// Format last updated time
const formatLastUpdated = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMinutes = Math.floor(diffMs / 60000)

  if (diffMinutes < 1) return 'Just now'
  if (diffMinutes === 1) return '1 minute ago'
  if (diffMinutes < 60) return `${diffMinutes} minutes ago`

  return date.toLocaleTimeString('it-IT', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Handle pattern reload
const handleReloadPatterns = async () => {
  try {
    const result = await store.reloadPatterns()

    toast.success(`Patterns reloaded successfully! (${result.patterns_loaded} patterns in ${result.reload_time_ms}ms)`, {
      timeout: 3000
    })
  } catch (err: any) {
    toast.error(`Failed to reload patterns: ${err.message || 'Unknown error'}`, {
      timeout: 5000
    })
  }
}

// Handle retry
const handleRetry = async () => {
  try {
    await store.fetchMetrics(true)
    toast.success('Metrics loaded successfully', { timeout: 2000 })
  } catch (err: any) {
    toast.error(`Failed to load metrics: ${err.message || 'Unknown error'}`, {
      timeout: 5000
    })
  }
}

// Fetch metrics on mount
onMounted(async () => {
  try {
    await store.fetchMetrics()
  } catch (err: any) {
    console.error('Failed to fetch metrics on mount:', err)
  }
})
</script>

<style scoped>
.learning-dashboard {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
  background: #0a0a0a;
  min-height: 100vh;
}

/* Dashboard Header */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  flex-wrap: wrap;
  gap: 20px;
}

.header-left h1 {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 6px 0;
}

.header-subtitle {
  font-size: 14px;
  color: #888888;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.reload-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.reload-btn:hover:not(:disabled) {
  background: #1d4ed8;
  transform: translateY(-1px);
}

.reload-btn:disabled {
  background: #4b5563;
  cursor: not-allowed;
  opacity: 0.7;
}

.reload-btn .spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.last-updated {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666666;
  padding: 8px 12px;
  background: #1a1a1a;
  border-radius: 6px;
  border: 1px solid #2a2a2a;
}

/* Error Alert */
.error-alert {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #ef4444;
  margin-bottom: 24px;
  font-size: 14px;
}

.error-alert .iconify {
  font-size: 20px;
}

.retry-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  padding: 6px 12px;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.4);
  border-radius: 6px;
  color: #ef4444;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: rgba(239, 68, 68, 0.3);
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 100px 20px;
  color: #888888;
}

.loading-state p {
  margin: 0;
  font-size: 16px;
}

/* Dashboard Content */
.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Metrics Cards */
.metrics-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.metric-card {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #1a1a1a;
  border-radius: 12px;
  border: 1px solid #2a2a2a;
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.metric-icon.total {
  background: rgba(37, 99, 235, 0.15);
  color: #2563eb;
}

.metric-icon.accuracy {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.metric-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metric-label {
  font-size: 12px;
  color: #888888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  line-height: 1;
}

.metric-detail {
  font-size: 12px;
  color: #666666;
}

.metric-detail .auto {
  color: #10b981;
}

.metric-detail .hardcoded {
  color: #9ca3af;
}

.metric-detail .separator {
  margin: 0 6px;
}

.cost-card {
  grid-column: span 1;
}

/* Chart Section */
.chart-section {
  width: 100%;
}

/* Split Section */
.split-section {
  display: grid;
  grid-template-columns: 60% 40%;
  gap: 20px;
}

.split-left,
.split-right {
  min-height: 200px;
}

/* Heatmap Section */
.heatmap-section {
  width: 100%;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .metrics-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .cost-card {
    grid-column: span 2;
  }

  .split-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .learning-dashboard {
    padding: 16px;
  }

  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-left h1 {
    font-size: 24px;
  }

  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .metrics-cards {
    grid-template-columns: 1fr;
  }

  .cost-card {
    grid-column: span 1;
  }

  .metric-card {
    padding: 16px;
  }

  .metric-icon {
    width: 48px;
    height: 48px;
    font-size: 20px;
  }

  .metric-value {
    font-size: 24px;
  }
}

@media (max-width: 480px) {
  .reload-btn span {
    display: none;
  }

  .last-updated span {
    display: none;
  }
}
</style>
