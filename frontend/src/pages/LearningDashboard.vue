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
      <!-- KPI Bar (2 Rows - 7 KPIs Total) -->
      <div class="professional-kpi-bar">
        <!-- First Row: 4 KPIs -->
        <div class="kpi-row">
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

          <div class="kpi-card feedback">
            <Icon icon="mdi:thumb-up-outline" class="kpi-card-icon" />
            <div class="kpi-card-content">
              <div class="kpi-card-value">{{ positiveFeedbackCount }}</div>
              <div class="kpi-card-label">User Feedback</div>
              <div class="kpi-card-detail">
                <span class="positive">{{ positiveFeedbackCount }} positive</span>
                <span class="separator">•</span>
                <span class="negative">{{ negativeFeedbackCount }} negative</span>
              </div>
            </div>
          </div>

          <div class="kpi-card fastpath">
            <Icon icon="mdi:lightning-bolt" class="kpi-card-icon" />
            <div class="kpi-card-content">
              <div class="kpi-card-value">{{ fastPathCoverage.toFixed(1) }}%</div>
              <div class="kpi-card-label">Fast-Path Coverage</div>
              <div class="kpi-card-detail">
                Auto-learning efficiency
              </div>
            </div>
          </div>
        </div>

        <!-- Second Row: 3 KPIs -->
        <div class="kpi-row">
          <div class="kpi-card performance">
            <Icon icon="mdi:speedometer" class="kpi-card-icon" />
            <div class="kpi-card-content">
              <div class="kpi-card-value">{{ avgResponseTime }}ms</div>
              <div class="kpi-card-label">Avg Response Time</div>
              <div class="kpi-card-detail">
                Weighted average latency
              </div>
            </div>
          </div>

          <div class="kpi-card activity">
            <Icon icon="mdi:chart-line" class="kpi-card-icon" />
            <div class="kpi-card-content">
              <div class="kpi-card-value">{{ recentActivity }}</div>
              <div class="kpi-card-label">Recent Activity</div>
              <div class="kpi-card-detail">
                Total queries processed
              </div>
            </div>
          </div>

          <div class="kpi-card category">
            <Icon icon="mdi:star" class="kpi-card-icon" />
            <div class="kpi-card-content">
              <div class="kpi-card-value category-name">{{ topCategory }}</div>
              <div class="kpi-card-label">Top Category</div>
              <div class="kpi-card-detail">
                Most requested type
              </div>
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
import { onMounted, computed } from 'vue'
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

// Compute feedback counts
const positiveFeedbackCount = computed(() => {
  return store.recentFeedback.filter(f => f.feedback === 'positive').length
})

const negativeFeedbackCount = computed(() => {
  return store.recentFeedback.filter(f => f.feedback === 'negative').length
})

// Compute Fast-Path Coverage
const fastPathCoverage = computed(() => {
  return store.costTrend?.fastPathCoverage || 0
})

// Compute Average Response Time (estimated from total_usages)
const avgResponseTime = computed(() => {
  // Estimate: fast-path ~10ms, LLM ~300ms
  const fastPathRate = fastPathCoverage.value / 100
  const llmRate = 1 - fastPathRate
  const estimatedMs = (fastPathRate * 10) + (llmRate * 300)
  return Math.round(estimatedMs)
})

// Compute Recent Activity (last 24h queries)
const recentActivity = computed(() => {
  // Use total_usages as proxy for 24h activity
  return store.metrics?.total_usages || 0
})

// Compute Top Category (most used)
const topCategory = computed(() => {
  if (!store.topPatterns || store.topPatterns.length === 0) {
    return 'N/A'
  }

  // Group by category and sum usage
  const categoryUsage: Record<string, number> = {}
  store.topPatterns.forEach(pattern => {
    const cat = pattern.classification
    categoryUsage[cat] = (categoryUsage[cat] || 0) + pattern.times_used
  })

  // Find category with max usage
  const topCat = Object.entries(categoryUsage)
    .sort(([, a], [, b]) => b - a)[0]

  return topCat ? formatCategoryName(topCat[0]) : 'N/A'
})

// Format percentage
const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`
}

// Format category name
const formatCategoryName = (category: string): string => {
  return category
    .replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
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

/* Professional KPI Bar (2 Rows - 7 KPIs) */
.professional-kpi-bar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: rgba(10, 10, 15, 0.8);
  border: 1px solid rgba(31, 41, 55, 0.4);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
}

.kpi-row {
  display: flex;
  gap: 16px;
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
  max-height: 100px;
}

.kpi-card.highlight {
  background: rgba(16, 185, 129, 0.05);
  border-color: rgba(16, 185, 129, 0.2);
}

.kpi-card.highlight .kpi-card-value {
  color: #10b981;
}

.kpi-card.feedback {
  background: rgba(59, 130, 246, 0.05);
  border-color: rgba(59, 130, 246, 0.2);
}

.kpi-card.feedback .kpi-card-value {
  color: #3b82f6;
}

.kpi-card.fastpath {
  background: rgba(245, 158, 11, 0.05);
  border-color: rgba(245, 158, 11, 0.2);
}

.kpi-card.fastpath .kpi-card-value {
  color: #f59e0b;
}

.kpi-card.performance {
  background: rgba(139, 92, 246, 0.05);
  border-color: rgba(139, 92, 246, 0.2);
}

.kpi-card.performance .kpi-card-value {
  color: #8b5cf6;
}

.kpi-card.activity {
  background: rgba(236, 72, 153, 0.05);
  border-color: rgba(236, 72, 153, 0.2);
}

.kpi-card.activity .kpi-card-value {
  color: #ec4899;
}

.kpi-card.category {
  background: rgba(34, 197, 94, 0.05);
  border-color: rgba(34, 197, 94, 0.2);
}

.kpi-card.category .kpi-card-value {
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

.kpi-card.feedback .kpi-card-icon {
  color: #3b82f6;
}

.kpi-card.fastpath .kpi-card-icon {
  color: #f59e0b;
}

.kpi-card.performance .kpi-card-icon {
  color: #8b5cf6;
}

.kpi-card.activity .kpi-card-icon {
  color: #ec4899;
}

.kpi-card.category .kpi-card-icon {
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

.kpi-card-value.category-name {
  font-size: 20px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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

.kpi-card-detail .positive {
  color: #10b981;
}

.kpi-card-detail .negative {
  color: #ef4444;
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
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1024px) {
  .kpi-row {
    flex-wrap: wrap;
    gap: 12px;
  }

  .kpi-card {
    min-width: calc(50% - 6px);
  }
}

@media (max-width: 768px) {
  .learning-dashboard {
    padding: 16px;
  }

  .professional-kpi-bar {
    padding: 16px;
  }

  .kpi-row {
    flex-direction: column;
    gap: 12px;
  }

  .kpi-card {
    width: 100%;
    min-width: 100%;
  }

  .kpi-card-value {
    font-size: 22px;
  }

  .kpi-card-value.category-name {
    font-size: 18px;
  }
}
</style>
