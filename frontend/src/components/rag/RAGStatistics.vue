<template>
  <div class="rag-statistics">
    <!-- Header -->
    <div class="statistics-header">
      <h3>Statistiche Base di Conoscenza</h3>
      <p class="subtitle">Panoramica completa del sistema RAG</p>
    </div>

    <!-- Stats Cards Grid -->
    <div class="stats-grid">
      <!-- Total Documents -->
      <Card class="stat-card primary">
        <template #content>
          <div class="stat-content">
            <div class="stat-icon">
              <Icon icon="lucide:file-text" />
            </div>
            <div class="stat-details">
              <span class="stat-value">{{ stats?.total_documents || 0 }}</span>
              <span class="stat-label">Documenti Totali</span>
            </div>
          </div>
        </template>
      </Card>

      <!-- Total Chunks -->
      <Card class="stat-card success">
        <template #content>
          <div class="stat-content">
            <div class="stat-icon">
              <Icon icon="lucide:layers" />
            </div>
            <div class="stat-details">
              <span class="stat-value">{{ stats?.total_chunks || 0 }}</span>
              <span class="stat-label">Frammenti Indicizzati</span>
            </div>
          </div>
        </template>
      </Card>

      <!-- Storage Used -->
      <Card class="stat-card warning">
        <template #content>
          <div class="stat-content">
            <div class="stat-icon">
              <Icon icon="lucide:database" />
            </div>
            <div class="stat-details">
              <span class="stat-value">{{ formatSize(stats?.total_size_bytes) }}</span>
              <span class="stat-label">Spazio Utilizzato</span>
            </div>
          </div>
        </template>
      </Card>

      <!-- Categories -->
      <Card class="stat-card info">
        <template #content>
          <div class="stat-content">
            <div class="stat-icon">
              <Icon icon="lucide:tags" />
            </div>
            <div class="stat-details">
              <span class="stat-value">{{ stats?.categories?.length || 0 }}</span>
              <span class="stat-label">Categorie</span>
            </div>
          </div>
        </template>
      </Card>

      <!-- Avg Document Size -->
      <Card class="stat-card secondary">
        <template #content>
          <div class="stat-content">
            <div class="stat-icon">
              <Icon icon="lucide:file-bar-chart" />
            </div>
            <div class="stat-details">
              <span class="stat-value">{{ formatSize(avgDocumentSize) }}</span>
              <span class="stat-label">Dimensione Media</span>
            </div>
          </div>
        </template>
      </Card>

      <!-- Last Update -->
      <Card class="stat-card accent">
        <template #content>
          <div class="stat-content">
            <div class="stat-icon">
              <Icon icon="lucide:clock" />
            </div>
            <div class="stat-details">
              <span class="stat-value">{{ formatLastUpdate(stats?.last_update) }}</span>
              <span class="stat-label">Ultimo Aggiornamento</span>
            </div>
          </div>
        </template>
      </Card>
    </div>

    <!-- Charts Section -->
    <div class="charts-grid">
      <!-- Documents by Category Chart -->
      <Card class="chart-card">
        <template #title>
          <div class="chart-title">
            <Icon icon="lucide:pie-chart" />
            Distribuzione per Categoria
          </div>
        </template>
        <template #content>
          <Chart
            type="doughnut"
            :data="categoryChartData"
            :options="categoryChartOptions"
            class="category-chart"
          />
        </template>
      </Card>

      <!-- Documents Timeline Chart -->
      <Card class="chart-card">
        <template #title>
          <div class="chart-title">
            <Icon icon="lucide:trending-up" />
            Documenti nel Tempo
          </div>
        </template>
        <template #content>
          <Chart
            type="line"
            :data="timelineChartData"
            :options="timelineChartOptions"
            class="timeline-chart"
          />
        </template>
      </Card>
    </div>

    <!-- Detailed Stats Table -->
    <Card class="details-card">
      <template #title>
        <div class="details-title">
          <Icon icon="lucide:list" />
          Dettagli per Categoria
        </div>
      </template>
      <template #content>
        <DataTable
          :value="categoryDetails"
          responsiveLayout="scroll"
          class="category-table"
        >
          <Column field="category" header="Categoria" :sortable="true">
            <template #body="{ data }">
              <Tag :value="data.category || 'Senza categoria'" severity="info" />
            </template>
          </Column>
          <Column field="count" header="Documenti" :sortable="true">
            <template #body="{ data }">
              <span class="count-badge">{{ data.count }}</span>
            </template>
          </Column>
          <Column field="size" header="Dimensione" :sortable="true">
            <template #body="{ data }">
              <span>{{ formatSize(data.size) }}</span>
            </template>
          </Column>
          <Column field="chunks" header="Frammenti" :sortable="true">
            <template #body="{ data }">
              <span>{{ data.chunks }}</span>
            </template>
          </Column>
          <Column field="avgSize" header="Media Dimensione" :sortable="true">
            <template #body="{ data }">
              <span>{{ formatSize(data.avgSize) }}</span>
            </template>
          </Column>
          <Column field="percentage" header="Percentuale" :sortable="true">
            <template #body="{ data }">
              <div class="percentage-cell">
                <ProgressBar :value="data.percentage" :showValue="false" class="percentage-bar" />
                <span class="percentage-text">{{ data.percentage.toFixed(1) }}%</span>
              </div>
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>

    <!-- System Info -->
    <Card class="system-info-card">
      <template #title>
        <div class="system-title">
          <Icon icon="lucide:info" />
          Informazioni Sistema
        </div>
      </template>
      <template #content>
        <div class="system-info-grid">
          <div class="info-item">
            <span class="info-label">Modello Embeddings:</span>
            <span class="info-value">text-embedding-3-large</span>
          </div>
          <div class="info-item">
            <span class="info-label">Dimensione Embeddings:</span>
            <span class="info-value">3072</span>
          </div>
          <div class="info-item">
            <span class="info-label">Dimensione Chunk:</span>
            <span class="info-value">600 caratteri</span>
          </div>
          <div class="info-item">
            <span class="info-label">Overlap Chunk:</span>
            <span class="info-value">250 caratteri</span>
          </div>
          <div class="info-item">
            <span class="info-label">Database Vettoriale:</span>
            <span class="info-value">ChromaDB</span>
          </div>
          <div class="info-item">
            <span class="info-label">Versione Sistema:</span>
            <span class="info-value">v3.1.1</span>
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Icon } from '@iconify/vue'
import Card from 'primevue/card'
import Chart from 'primevue/chart'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import ProgressBar from 'primevue/progressbar'

// Props
const props = defineProps<{
  stats: any
}>()

// State
const categoryDetails = ref<any[]>([])

// Computed
const avgDocumentSize = computed(() => {
  if (!props.stats || props.stats.total_documents === 0) return 0
  return props.stats.total_size_bytes / props.stats.total_documents
})

const categoryChartData = computed(() => {
  if (!props.stats?.documents_by_category) {
    return { labels: [], datasets: [] }
  }

  const categories = Object.keys(props.stats.documents_by_category)
  const values = Object.values(props.stats.documents_by_category) as number[]

  return {
    labels: categories.length > 0 ? categories : ['Senza categoria'],
    datasets: [{
      data: values.length > 0 ? values : [props.stats.total_documents || 0],
      backgroundColor: [
        '#10b981',
        '#3b82f6',
        '#f59e0b',
        '#ef4444',
        '#8b5cf6',
        '#06b6d4',
        '#ec4899',
        '#14b8a6'
      ],
      borderColor: '#1a1a1a',
      borderWidth: 2
    }]
  }
})

const categoryChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        color: '#a0a0a0',
        padding: 15,
        font: {
          size: 12
        }
      }
    },
    tooltip: {
      backgroundColor: '#1e1e1e',
      titleColor: '#ffffff',
      bodyColor: '#a0a0a0',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      borderWidth: 1
    }
  }
}))

const timelineChartData = computed(() => {
  // Mock data per il grafico timeline (in futuro da backend)
  const last7Days = Array.from({ length: 7 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - (6 - i))
    return date.toLocaleDateString('it-IT', { day: '2-digit', month: 'short' })
  })

  return {
    labels: last7Days,
    datasets: [{
      label: 'Documenti aggiunti',
      data: [2, 5, 3, 8, 4, 6, props.stats?.total_documents || 0],
      fill: true,
      borderColor: '#10b981',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      tension: 0.4,
      pointBackgroundColor: '#10b981',
      pointBorderColor: '#1a1a1a',
      pointBorderWidth: 2
    }]
  }
})

const timelineChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      backgroundColor: '#1e1e1e',
      titleColor: '#ffffff',
      bodyColor: '#a0a0a0',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      borderWidth: 1
    }
  },
  scales: {
    x: {
      grid: {
        color: 'rgba(255, 255, 255, 0.05)'
      },
      ticks: {
        color: '#a0a0a0'
      }
    },
    y: {
      grid: {
        color: 'rgba(255, 255, 255, 0.05)'
      },
      ticks: {
        color: '#a0a0a0',
        precision: 0
      }
    }
  }
}))

// Methods
const formatSize = (bytes?: number) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatLastUpdate = (timestamp?: string) => {
  if (!timestamp) return 'Mai'
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)

  if (minutes < 1) return 'Adesso'
  if (minutes < 60) return `${minutes} min fa`
  if (minutes < 1440) return `${Math.floor(minutes / 60)} ore fa`
  return `${Math.floor(minutes / 1440)} giorni fa`
}

const updateCategoryDetails = () => {
  if (!props.stats?.documents_by_category) {
    categoryDetails.value = []
    return
  }

  const total = props.stats.total_documents || 0
  const categories = Object.entries(props.stats.documents_by_category)

  categoryDetails.value = categories.map(([category, count]) => {
    const docCount = count as number
    const percentage = total > 0 ? (docCount / total) * 100 : 0

    // Mock additional data (in futuro da backend)
    const avgSize = props.stats.total_size_bytes ? props.stats.total_size_bytes / total : 0

    return {
      category: category || 'Senza categoria',
      count: docCount,
      size: avgSize * docCount,
      chunks: Math.round((props.stats.total_chunks || 0) * (docCount / total)),
      avgSize,
      percentage
    }
  })
}

// Watchers
watch(() => props.stats, () => {
  updateCategoryDetails()
}, { deep: true })

// Lifecycle
onMounted(() => {
  updateCategoryDetails()
})
</script>

<style scoped>
.rag-statistics {
  width: 100%;
}

/* Header */
.statistics-header {
  margin-bottom: 2rem;
}

.statistics-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 0.5rem 0;
}

.subtitle {
  color: #a0a0a0;
  font-size: 0.9rem;
  margin: 0;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.25rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.stat-card.primary { border-left: 4px solid #10b981; }
.stat-card.success { border-left: 4px solid #3b82f6; }
.stat-card.warning { border-left: 4px solid #f59e0b; }
.stat-card.info { border-left: 4px solid #06b6d4; }
.stat-card.secondary { border-left: 4px solid #8b5cf6; }
.stat-card.accent { border-left: 4px solid #ec4899; }

.stat-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 12px;
  font-size: 1.5rem;
  color: #10b981;
}

.stat-card.success .stat-icon {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.stat-card.warning .stat-icon {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.stat-card.info .stat-icon {
  background: rgba(6, 182, 212, 0.1);
  color: #06b6d4;
}

.stat-card.secondary .stat-icon {
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.stat-card.accent .stat-icon {
  background: rgba(236, 72, 153, 0.1);
  color: #ec4899;
}

.stat-details {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #ffffff;
  line-height: 1;
}

.stat-label {
  font-size: 0.85rem;
  color: #a0a0a0;
  margin-top: 0.25rem;
}

/* Charts Grid */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.chart-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.chart-card :deep(.p-card-title) {
  background: #1e1e1e;
  margin: -1rem -1rem 0;
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #ffffff;
  font-size: 1rem;
  font-weight: 600;
}

.category-chart,
.timeline-chart {
  height: 300px;
}

/* Details Card */
.details-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 2rem;
}

.details-card :deep(.p-card-title) {
  background: #1e1e1e;
  margin: -1rem -1rem 0;
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.details-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #ffffff;
  font-size: 1rem;
  font-weight: 600;
}

.category-table :deep(.p-datatable-thead > tr > th) {
  background: #1e1e1e;
  color: #a0a0a0;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.category-table :deep(.p-datatable-tbody > tr) {
  background: #1a1a1a;
  color: #e0e0e0;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.category-table :deep(.p-datatable-tbody > tr:hover) {
  background: rgba(255, 255, 255, 0.05);
}

.count-badge {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-weight: 500;
}

.percentage-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.percentage-bar {
  width: 60px;
}

.percentage-bar :deep(.p-progressbar) {
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
}

.percentage-bar :deep(.p-progressbar-value) {
  background: linear-gradient(90deg, #10b981 0%, #0d9668 100%);
}

.percentage-text {
  font-size: 0.85rem;
  color: #a0a0a0;
}

/* System Info Card */
.system-info-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.system-info-card :deep(.p-card-title) {
  background: #1e1e1e;
  margin: -1rem -1rem 0;
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.system-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #ffffff;
  font-size: 1rem;
  font-weight: 600;
}

.system-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 6px;
}

.info-label {
  color: #a0a0a0;
  font-size: 0.9rem;
}

.info-value {
  color: #10b981;
  font-weight: 500;
  font-family: monospace;
}

/* Responsive */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .system-info-grid {
    grid-template-columns: 1fr;
  }

  .percentage-cell {
    flex-direction: column;
    align-items: flex-start;
  }

  .percentage-bar {
    width: 100%;
  }
}
</style>