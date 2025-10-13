<template>
  <MainLayout>
    <div class="learning-dashboard">
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
      <!-- KPI Bar (Horizontal Insights Style) -->
      <div class="professional-kpi-bar">
        <div class="kpi-card">
          <Icon icon="mdi:database" class="kpi-card-icon" />
          <div class="kpi-card-content">
            <div class="kpi-card-value">{{ store.metrics?.total_patterns || 0 }}</div>
            <div class="kpi-card-label">Total Patterns</div>
            <div class="kpi-card-detail">
              <span class="auto">{{ store.metrics?.auto_learned_count || 0 }} auto</span>
              <span class="separator">•</span>
              <span class="hardcoded">{{ store.metrics?.hardcoded_count || 0 }} hardcoded</span>
            </div>
          </div>
        </div>

        <div class="kpi-card highlight">
          <Icon icon="mdi:target" class="kpi-card-icon" />
          <div class="kpi-card-content">
            <div class="kpi-card-value">{{ formatPercentage(store.metrics?.accuracy_rate || 0) }}</div>
            <div class="kpi-card-label">Accuracy Rate</div>
            <div class="kpi-card-detail">
              {{ store.metrics?.total_usages || 0 }} queries
            </div>
          </div>
        </div>

        <div class="kpi-card">
          <Icon icon="mdi:lightning-bolt" class="kpi-card-icon" />
          <div class="kpi-card-content">
            <div class="kpi-card-value">{{ formatPercentage(store.costTrend?.fastPathCoverage / 100 || 0) }}</div>
            <div class="kpi-card-label">Fast-Path Coverage</div>
            <div class="kpi-card-detail">
              <span class="fast-path">{{ formatPercentage(store.costTrend?.llmCoverage / 100 || 0) }} LLM</span>
            </div>
          </div>
        </div>

        <div class="kpi-card success">
          <Icon icon="mdi:cash-multiple" class="kpi-card-icon" />
          <div class="kpi-card-content">
            <div class="kpi-card-value">${{ formatCurrency(store.costTrend?.monthly || 0) }}</div>
            <div class="kpi-card-label">Monthly Savings</div>
            <div class="kpi-card-detail">
              <span class="total">${{ formatCurrency(store.costTrend?.total || 0) }} total</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Grid 2x2: Componenti principali -->
      <div class="dashboard-grid">
        <PatternPerformanceTable
          :patterns="store.topPatterns"
          :isLoading="store.isLoading"
          :error="store.error"
        />

        <AccuracyTrendChart
          :data="store.accuracyTrend"
          :isLoading="store.isLoading"
          :error="store.error"
        />

        <FeedbackTimeline
          :events="store.recentFeedback"
          :isLoading="store.isLoading"
          :error="store.error"
        />

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

// Store & Toast
const store = useLearningStore()
const toast = useToast()

// Format percentage
const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`
}

// Format currency
const formatCurrency = (value: number): string => {
  return value.toFixed(2)
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
  width: 100%;
  background: #0a0a0a;
  min-height: 100vh;
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

/* Professional KPI Bar (Insights Style) */
.professional-kpi-bar {
  display: flex;
  gap: 0;
  background: rgba(10, 10, 15, 0.8);
  border: 1px solid rgba(31, 41, 55, 0.4);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
}

.kpi-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: rgba(15, 15, 20, 0.6);
  border: 1px solid rgba(31, 41, 55, 0.3);
  border-radius: 8px;
  margin-right: 16px;
  max-height: 100px;
}

.kpi-card:last-child {
  margin-right: 0;
}

.kpi-card.highlight {
  background: rgba(16, 185, 129, 0.05);
  border-color: rgba(16, 185, 129, 0.2);
}

.kpi-card.highlight .kpi-card-value {
  color: #10b981;
}

.kpi-card.success {
  background: rgba(34, 197, 94, 0.05);
  border-color: rgba(34, 197, 94, 0.2);
}

.kpi-card.success .kpi-card-value {
  color: #22c55e;
}

.kpi-card-icon {
  font-size: 24px;
  color: #64748b;
  opacity: 0.8;
  flex-shrink: 0;
}

.kpi-card.highlight .kpi-card-icon {
  color: #10b981;
}

.kpi-card.success .kpi-card-icon {
  color: #22c55e;
}

.kpi-card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kpi-card-value {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  line-height: 1;
  letter-spacing: -0.5px;
}

.kpi-card-label {
  font-size: 10px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 500;
}

.kpi-card-detail {
  font-size: 11px;
  color: #666666;
}

.kpi-card-detail .auto {
  color: #10b981;
}

.kpi-card-detail .hardcoded {
  color: #9ca3af;
}

.kpi-card-detail .fast-path {
  color: #f59e0b;
}

.kpi-card-detail .total {
  color: #22c55e;
}

.kpi-card-detail .separator {
  margin: 0 4px;
}

/* Dashboard Grid 2x2 */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .professional-kpi-bar {
    flex-wrap: wrap;
    gap: 12px;
  }

  .kpi-card {
    min-width: calc(50% - 6px);
    margin-right: 0;
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 992px) {
  .professional-kpi-bar {
    flex-direction: column;
  }

  .kpi-card {
    min-width: 100%;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .learning-dashboard {
    padding: 16px;
  }

  .professional-kpi-bar {
    padding: 16px;
  }

  .kpi-card {
    width: 100%;
    min-width: 100%;
  }

  .kpi-card-value {
    font-size: 22px;
  }
}
</style>
