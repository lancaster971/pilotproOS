<template>
  <div class="pattern-performance-table">
    <div class="table-header">
      <h3>Pattern Performance</h3>
      <div class="table-subtitle">Top patterns by usage</div>
    </div>

    <div v-if="isLoading" class="table-loading">
      <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
      <p>Loading patterns...</p>
    </div>

    <div v-else-if="error" class="table-error">
      <i class="pi pi-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>

    <DataTable
      v-else
      :value="patterns"
      :rows="10"
      :paginator="patterns.length > 10"
      :rowsPerPageOptions="[10, 20, 50]"
      paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
      :globalFilterFields="['query', 'classification']"
      v-model:filters="filters"
      filterDisplay="row"
      :sortField="sortField"
      :sortOrder="sortOrder"
      @sort="onSort"
      tableStyle="min-width: 50rem"
      class="custom-table"
      :rowHover="true"
      :expandedRows="expandedRows"
      v-model:expandedRows="expandedRows"
      dataKey="id"
    >
      <!-- Expand column -->
      <Column :expander="true" headerStyle="width: 3rem" />

      <!-- Query column -->
      <Column field="query" header="Query" :sortable="true" style="min-width: 200px">
        <template #body="slotProps">
          <div class="query-cell">
            <span class="query-text">{{ slotProps.data.query }}</span>
            <span v-if="slotProps.data.source === 'auto_learned'" class="badge badge-auto">Auto</span>
            <span v-else class="badge badge-hardcoded">Hardcoded</span>
          </div>
        </template>
        <template #filter="{ filterModel, filterCallback }">
          <input
            type="text"
            v-model="filterModel.value"
            @input="filterCallback()"
            class="filter-input"
            placeholder="Search query..."
          />
        </template>
      </Column>

      <!-- Category column -->
      <Column field="classification" header="Category" :sortable="true" style="min-width: 150px">
        <template #body="slotProps">
          <span class="category-badge">{{ formatCategory(slotProps.data.classification) }}</span>
        </template>
        <template #filter="{ filterModel, filterCallback }">
          <input
            type="text"
            v-model="filterModel.value"
            @input="filterCallback()"
            class="filter-input"
            placeholder="Search category..."
          />
        </template>
      </Column>

      <!-- Times Used column -->
      <Column field="times_used" header="Times Used" :sortable="true" style="min-width: 120px">
        <template #body="slotProps">
          <span class="usage-count">{{ slotProps.data.times_used }}</span>
        </template>
      </Column>

      <!-- Accuracy column -->
      <Column field="accuracy" header="Accuracy" :sortable="true" style="min-width: 120px">
        <template #body="slotProps">
          <div class="accuracy-cell">
            <div class="accuracy-bar">
              <div
                class="accuracy-fill"
                :style="{ width: `${getAccuracy(slotProps.data) * 100}%`, backgroundColor: getAccuracyColor(getAccuracy(slotProps.data)) }"
              ></div>
            </div>
            <span class="accuracy-text">{{ (getAccuracy(slotProps.data) * 100).toFixed(0) }}%</span>
          </div>
        </template>
      </Column>

      <!-- Confidence column -->
      <Column field="confidence" header="Confidence" :sortable="true" style="min-width: 120px">
        <template #body="slotProps">
          <span class="confidence-value">{{ (slotProps.data.confidence * 100).toFixed(0) }}%</span>
        </template>
      </Column>

      <!-- Row expansion template -->
      <template #expansion="slotProps">
        <div class="expanded-details">
          <div class="detail-row">
            <span class="detail-label">Normalized Query:</span>
            <span class="detail-value">{{ slotProps.data.normalized_query }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Times Correct:</span>
            <span class="detail-value">{{ slotProps.data.times_correct }} / {{ slotProps.data.times_used }}</span>
          </div>
          <div class="detail-row" v-if="slotProps.data.last_used_at">
            <span class="detail-label">Last Used:</span>
            <span class="detail-value">{{ formatDate(slotProps.data.last_used_at) }}</span>
          </div>
          <div class="detail-row" v-if="slotProps.data.created_at">
            <span class="detail-label">Created:</span>
            <span class="detail-value">{{ formatDate(slotProps.data.created_at) }}</span>
          </div>
        </div>
      </template>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import type { PatternData } from '../../types/learning'

// FilterMatchMode implementation (PrimeVue constant)
const FilterMatchMode = {
  CONTAINS: 'contains',
  STARTS_WITH: 'startsWith',
  ENDS_WITH: 'endsWith',
  EQUALS: 'equals',
  NOT_EQUALS: 'notEquals',
  IN: 'in',
  LESS_THAN: 'lt',
  LESS_THAN_OR_EQUAL_TO: 'lte',
  GREATER_THAN: 'gt',
  GREATER_THAN_OR_EQUAL_TO: 'gte',
  BETWEEN: 'between',
  DATE_IS: 'dateIs',
  DATE_IS_NOT: 'dateIsNot',
  DATE_BEFORE: 'dateBefore',
  DATE_AFTER: 'dateAfter'
} as const

const props = defineProps<{
  patterns: PatternData[]
  isLoading?: boolean
  error?: string | null
}>()

// Table state
const filters = ref({
  query: { value: null, matchMode: FilterMatchMode.CONTAINS },
  classification: { value: null, matchMode: FilterMatchMode.CONTAINS }
})

const sortField = ref('times_used')
const sortOrder = ref(-1) // Descending by default
const expandedRows = ref<PatternData[]>([])

// Calculate accuracy
const getAccuracy = (pattern: PatternData): number => {
  if (pattern.times_used === 0) return 0
  return pattern.times_correct / pattern.times_used
}

// Get color for accuracy bar
const getAccuracyColor = (accuracy: number): string => {
  if (accuracy >= 0.9) return '#10b981' // Green
  if (accuracy >= 0.7) return '#f59e0b' // Orange
  return '#ef4444' // Red
}

// Format category name
const formatCategory = (category: string): string => {
  return category
    .replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// Format date
const formatDate = (timestamp: string): string => {
  const date = new Date(timestamp)
  return date.toLocaleString('it-IT', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Handle sort
const onSort = (event: any) => {
  sortField.value = event.sortField
  sortOrder.value = event.sortOrder
}
</script>

<style scoped>
.pattern-performance-table {
  background: #1a1a1a;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #2a2a2a;
}

.table-header {
  margin-bottom: 20px;
}

.table-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 6px 0;
}

.table-subtitle {
  font-size: 13px;
  color: #888888;
}

.table-loading,
.table-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #888888;
  padding: 60px 20px;
}

.table-error {
  color: #ef4444;
}

.table-error i {
  font-size: 2rem;
}

.table-loading p,
.table-error p {
  margin: 0;
  font-size: 14px;
}

/* Custom PrimeVue DataTable styling */
.custom-table {
  font-size: 13px;
}

.custom-table :deep(.p-datatable-header) {
  background: transparent;
  border: none;
  padding: 0 0 12px 0;
}

.custom-table :deep(.p-datatable-thead > tr > th) {
  background: #0a0a0a;
  color: #e5e5e5;
  border: none;
  padding: 12px;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.custom-table :deep(.p-datatable-tbody > tr) {
  background: #1a1a1a;
  color: #e5e5e5;
  border-bottom: 1px solid #2a2a2a;
}

.custom-table :deep(.p-datatable-tbody > tr:hover) {
  background: #222222;
}

.custom-table :deep(.p-datatable-tbody > tr > td) {
  padding: 12px;
  border: none;
}

.custom-table :deep(.p-paginator) {
  background: transparent;
  color: #e5e5e5;
  border: none;
  padding: 16px 0 0 0;
}

.custom-table :deep(.p-paginator .p-paginator-pages .p-paginator-page) {
  color: #888888;
  min-width: 2rem;
  height: 2rem;
  border-radius: 6px;
}

.custom-table :deep(.p-paginator .p-paginator-pages .p-paginator-page.p-highlight) {
  background: #2563eb;
  color: #ffffff;
}

.custom-table :deep(.p-paginator .p-paginator-pages .p-paginator-page:hover) {
  background: #2a2a2a;
}

/* Filter input */
.filter-input {
  width: 100%;
  padding: 6px 10px;
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  border-radius: 6px;
  color: #e5e5e5;
  font-size: 12px;
  outline: none;
}

.filter-input::placeholder {
  color: #666666;
}

.filter-input:focus {
  border-color: #2563eb;
}

/* Query cell */
.query-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.query-text {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge-auto {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.badge-hardcoded {
  background: rgba(107, 114, 128, 0.15);
  color: #9ca3af;
  border: 1px solid rgba(107, 114, 128, 0.3);
}

/* Category badge */
.category-badge {
  display: inline-block;
  padding: 4px 10px;
  background: #2a2a2a;
  border-radius: 6px;
  font-size: 12px;
  color: #2563eb;
}

/* Usage count */
.usage-count {
  font-weight: 600;
  color: #e5e5e5;
}

/* Accuracy cell */
.accuracy-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.accuracy-bar {
  flex: 1;
  height: 6px;
  background: #2a2a2a;
  border-radius: 3px;
  overflow: hidden;
}

.accuracy-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.accuracy-text {
  font-weight: 600;
  font-size: 12px;
  min-width: 40px;
  text-align: right;
}

/* Confidence value */
.confidence-value {
  font-weight: 600;
  color: #888888;
}

/* Expanded details */
.expanded-details {
  background: #0a0a0a;
  padding: 16px 20px;
  border-radius: 8px;
  margin: 8px;
}

.detail-row {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid #2a2a2a;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-weight: 600;
  color: #888888;
  min-width: 160px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  color: #e5e5e5;
  font-size: 13px;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .pattern-performance-table {
    padding: 16px;
  }

  .table-header h3 {
    font-size: 16px;
  }

  .custom-table {
    font-size: 12px;
  }

  .custom-table :deep(.p-datatable-thead > tr > th) {
    font-size: 11px;
    padding: 8px;
  }

  .custom-table :deep(.p-datatable-tbody > tr > td) {
    padding: 8px;
  }

  .detail-label {
    min-width: 120px;
  }
}
</style>
