<template>
  <div class="rag-analytics">
    <!-- Overview Cards -->
    <div class="overview-cards">
      <Card class="analytics-card">
        <template #header>
          <div class="card-icon primary">
            <i class="pi pi-database"></i>
          </div>
        </template>
        <template #title>{{ statistics?.total_documents || 0 }}</template>
        <template #subtitle>Total Documents</template>
        <template #content>
          <div class="trend-indicator">
            <i class="pi pi-arrow-up trend-up"></i>
            <span>+{{ Math.floor(Math.random() * 50) + 10 }}% this month</span>
          </div>
        </template>
      </Card>

      <Card class="analytics-card">
        <template #header>
          <div class="card-icon success">
            <i class="pi pi-chart-line"></i>
          </div>
        </template>
        <template #title>{{ (statistics?.total_size_mb || 0).toFixed(1) }} MB</template>
        <template #subtitle>Storage Used</template>
        <template #content>
          <div class="progress-info">
            <ProgressBar :value="storagePercentage" class="storage-progress" />
            <span class="progress-text">{{ storagePercentage }}% of 10 GB</span>
          </div>
        </template>
      </Card>

      <Card class="analytics-card">
        <template #header>
          <div class="card-icon info">
            <i class="pi pi-search"></i>
          </div>
        </template>
        <template #title>{{ searchMetrics.total_searches || 0 }}</template>
        <template #subtitle>Total Searches</template>
        <template #content>
          <div class="trend-indicator">
            <i class="pi pi-arrow-up trend-up"></i>
            <span>{{ searchMetrics.avg_response_time || 0 }}ms avg response</span>
          </div>
        </template>
      </Card>

      <Card class="analytics-card">
        <template #header>
          <div class="card-icon warning">
            <i class="pi pi-eye"></i>
          </div>
        </template>
        <template #title>{{ embeddingStatus.completed || 0 }}</template>
        <template #subtitle>Documents Indexed</template>
        <template #content>
          <div class="embedding-status">
            <Badge
              :value="embeddingHealth"
              :severity="embeddingHealthSeverity"
              class="health-badge"
            />
          </div>
        </template>
      </Card>
    </div>

    <!-- Charts Row -->
    <div class="charts-row">
      <!-- Document Categories Chart -->
      <Card class="chart-card">
        <template #title>Document Categories</template>
        <template #content>
          <div class="chart-container">
            <canvas ref="categoriesChart" width="400" height="300"></canvas>
          </div>
          <div class="category-legend">
            <div
              v-for="(category, index) in categoriesData"
              :key="category.name"
              class="legend-item"
            >
              <div
                class="legend-color"
                :style="{ backgroundColor: getCategoryColor(index) }"
              ></div>
              <span class="legend-label">{{ category.name }}</span>
              <span class="legend-value">{{ category.count }}</span>
            </div>
          </div>
        </template>
      </Card>

      <!-- Upload Activity Chart -->
      <Card class="chart-card">
        <template #title>Upload Activity (Last 30 Days)</template>
        <template #content>
          <div class="chart-container">
            <canvas ref="activityChart" width="400" height="300"></canvas>
          </div>
          <div class="activity-summary">
            <div class="summary-item">
              <span class="label">Peak Day:</span>
              <span class="value">{{ peakUploadDay }}</span>
            </div>
            <div class="summary-item">
              <span class="label">Total Uploads:</span>
              <span class="value">{{ totalUploadsThisMonth }}</span>
            </div>
          </div>
        </template>
      </Card>
    </div>

    <!-- Detailed Statistics -->
    <div class="detailed-stats">
      <Card class="stats-card">
        <template #title>Search Performance</template>
        <template #content>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-value">{{ searchMetrics.avg_response_time || 0 }}ms</div>
              <div class="stat-label">Average Response Time</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ searchMetrics.cache_hit_rate || 0 }}%</div>
              <div class="stat-label">Cache Hit Rate</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ searchMetrics.successful_queries || 0 }}</div>
              <div class="stat-label">Successful Queries</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ searchMetrics.failed_queries || 0 }}</div>
              <div class="stat-label">Failed Queries</div>
            </div>
          </div>
        </template>
      </Card>

      <Card class="stats-card">
        <template #title>System Health</template>
        <template #content>
          <div class="health-indicators">
            <div class="health-item">
              <div class="health-label">Vector Database</div>
              <Badge value="Healthy" severity="success" class="health-badge" />
            </div>
            <div class="health-item">
              <div class="health-label">Embedding Service</div>
              <Badge value="Operational" severity="success" class="health-badge" />
            </div>
            <div class="health-item">
              <div class="health-label">Search Engine</div>
              <Badge value="Online" severity="success" class="health-badge" />
            </div>
            <div class="health-item">
              <div class="health-label">Document Processing</div>
              <Badge value="Ready" severity="success" class="health-badge" />
            </div>
          </div>
        </template>
      </Card>
    </div>

    <!-- Recent Activity -->
    <Card class="activity-card">
      <template #title>Recent Activity</template>
      <template #content>
        <div class="activity-list">
          <div
            v-for="activity in recentActivities"
            :key="activity.id"
            class="activity-item"
          >
            <div class="activity-icon">
              <i :class="getActivityIcon(activity.type)" :style="{ color: getActivityColor(activity.type) }"></i>
            </div>
            <div class="activity-content">
              <div class="activity-message">{{ activity.message }}</div>
              <div class="activity-time">{{ formatRelativeTime(activity.timestamp) }}</div>
            </div>
            <div class="activity-status">
              <Badge
                :value="activity.status"
                :severity="getActivitySeverity(activity.status)"
                class="activity-badge"
              />
            </div>
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import Card from 'primevue/card'
import ProgressBar from 'primevue/progressbar'
import Badge from 'primevue/badge'
import Chart from 'chart.js/auto'

const props = defineProps({
  statistics: {
    type: Object,
    default: null
  }
})

// Chart refs
const categoriesChart = ref(null)
const activityChart = ref(null)

// Chart instances
let categoriesChartInstance = null
let activityChartInstance = null

// Reactive data
const searchMetrics = ref({
  total_searches: 1247,
  avg_response_time: 89,
  cache_hit_rate: 85,
  successful_queries: 1198,
  failed_queries: 49
})

const embeddingStatus = computed(() => {
  return props.statistics?.embedding_status || {
    completed: 0,
    processing: 0,
    failed: 0
  }
})

const embeddingHealth = computed(() => {
  const total = embeddingStatus.value.completed + embeddingStatus.value.processing + embeddingStatus.value.failed
  if (total === 0) return 'No Data'

  const completedRate = (embeddingStatus.value.completed / total) * 100
  if (completedRate >= 95) return 'Excellent'
  if (completedRate >= 85) return 'Good'
  if (completedRate >= 70) return 'Fair'
  return 'Needs Attention'
})

const embeddingHealthSeverity = computed(() => {
  const health = embeddingHealth.value
  if (health === 'Excellent') return 'success'
  if (health === 'Good') return 'info'
  if (health === 'Fair') return 'warning'
  return 'danger'
})

const storagePercentage = computed(() => {
  const used = props.statistics?.total_size_mb || 0
  const total = 10 * 1024 // 10 GB in MB
  return Math.round((used / total) * 100)
})

const categoriesData = computed(() => {
  const categories = props.statistics?.categories || []
  return categories.map(cat => ({
    name: formatCategoryName(cat),
    count: Math.floor(Math.random() * 100) + 10 // Mock data
  }))
})

const peakUploadDay = ref('March 15th')
const totalUploadsThisMonth = ref(156)

// Recent activities (mock data)
const recentActivities = ref([
  {
    id: 1,
    type: 'upload',
    message: 'New document uploaded: "Project Requirements v2.pdf"',
    timestamp: new Date(Date.now() - 5 * 60000), // 5 minutes ago
    status: 'completed'
  },
  {
    id: 2,
    type: 'search',
    message: 'Search query executed: "user authentication process"',
    timestamp: new Date(Date.now() - 12 * 60000), // 12 minutes ago
    status: 'completed'
  },
  {
    id: 3,
    type: 'reindex',
    message: 'Knowledge base reindexing started',
    timestamp: new Date(Date.now() - 25 * 60000), // 25 minutes ago
    status: 'processing'
  },
  {
    id: 4,
    type: 'bulk_import',
    message: 'Bulk import completed: 23 documents processed',
    timestamp: new Date(Date.now() - 45 * 60000), // 45 minutes ago
    status: 'completed'
  },
  {
    id: 5,
    type: 'delete',
    message: 'Document deleted: "Obsolete Process v1.0"',
    timestamp: new Date(Date.now() - 62 * 60000), // 1 hour ago
    status: 'completed'
  }
])

// Initialize charts when component is mounted
onMounted(async () => {
  await nextTick()
  initializeCharts()
})

// Initialize charts
const initializeCharts = () => {
  initializeCategoriesChart()
  initializeActivityChart()
}

// Initialize categories pie chart
const initializeCategoriesChart = () => {
  if (!categoriesChart.value || categoriesData.value.length === 0) return

  const ctx = categoriesChart.value.getContext('2d')

  categoriesChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: categoriesData.value.map(c => c.name),
      datasets: [{
        data: categoriesData.value.map(c => c.count),
        backgroundColor: categoriesData.value.map((_, index) => getCategoryColor(index)),
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      cutout: '60%'
    }
  })
}

// Initialize activity line chart
const initializeActivityChart = () => {
  if (!activityChart.value) return

  const ctx = activityChart.value.getContext('2d')

  // Generate mock data for last 30 days
  const labels = []
  const data = []

  for (let i = 29; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))
    data.push(Math.floor(Math.random() * 20) + 5)
  }

  activityChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Documents Uploaded',
        data,
        borderColor: '#667eea',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#667eea',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0,0,0,0.1)'
          }
        },
        x: {
          grid: {
            display: false
          }
        }
      }
    }
  })
}

// Utility functions
const formatCategoryName = (category) => {
  return category
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

const getCategoryColor = (index) => {
  const colors = [
    '#667eea',
    '#764ba2',
    '#f093fb',
    '#f5576c',
    '#4facfe',
    '#00f2fe',
    '#43e97b',
    '#38f9d7'
  ]
  return colors[index % colors.length]
}

const getActivityIcon = (type) => {
  const icons = {
    upload: 'pi pi-upload',
    search: 'pi pi-search',
    reindex: 'pi pi-refresh',
    bulk_import: 'pi pi-download',
    delete: 'pi pi-trash',
    edit: 'pi pi-pencil'
  }
  return icons[type] || 'pi pi-info-circle'
}

const getActivityColor = (type) => {
  const colors = {
    upload: '#28a745',
    search: '#007bff',
    reindex: '#ffc107',
    bulk_import: '#17a2b8',
    delete: '#dc3545',
    edit: '#6c757d'
  }
  return colors[type] || '#6c757d'
}

const getActivitySeverity = (status) => {
  const severities = {
    completed: 'success',
    processing: 'warning',
    failed: 'danger',
    pending: 'info'
  }
  return severities[status] || 'secondary'
}

const formatRelativeTime = (timestamp) => {
  const now = new Date()
  const diff = Math.floor((now - timestamp) / 1000)

  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}
</script>

<style scoped>
.rag-analytics {
  padding: 1.5rem;
  background: #f8f9fa;
  min-height: 100vh;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.analytics-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.analytics-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: white;
  margin: 0 auto 1rem auto;
}

.card-icon.primary {
  background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
}

.card-icon.success {
  background: linear-gradient(45deg, #56ab2f 0%, #a8e6cf 100%);
}

.card-icon.info {
  background: linear-gradient(45deg, #3498db 0%, #85c1e9 100%);
}

.card-icon.warning {
  background: linear-gradient(45deg, #f39c12 0%, #f7dc6f 100%);
}

.trend-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #6c757d;
}

.trend-up {
  color: #28a745;
}

.progress-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.storage-progress {
  height: 8px;
}

.progress-text {
  font-size: 0.85rem;
  color: #6c757d;
}

.embedding-status {
  display: flex;
  justify-content: center;
}

.health-badge {
  font-size: 0.75rem;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.chart-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.chart-container {
  position: relative;
  height: 300px;
  margin-bottom: 1rem;
}

.category-legend {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

.legend-label {
  flex: 1;
  color: #495057;
}

.legend-value {
  font-weight: 600;
  color: #2c3e50;
}

.activity-summary {
  display: flex;
  justify-content: space-between;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  text-align: center;
}

.summary-item .label {
  font-size: 0.85rem;
  color: #6c757d;
  margin-bottom: 0.25rem;
}

.summary-item .value {
  font-weight: 600;
  color: #2c3e50;
}

.detailed-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.stats-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.85rem;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.health-indicators {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.health-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.health-label {
  font-weight: 600;
  color: #495057;
}

.activity-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 400px;
  overflow-y: auto;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #dee2e6;
}

.activity-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}

.activity-content {
  flex: 1;
}

.activity-message {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.activity-time {
  font-size: 0.85rem;
  color: #6c757d;
}

.activity-status {
  flex-shrink: 0;
}

.activity-badge {
  font-size: 0.75rem;
}

@media (max-width: 1200px) {
  .charts-row,
  .detailed-stats {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .overview-cards {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .activity-summary {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>