<template>
  <div class="pattern-management">
    <div class="header-row">
      <div class="table-header">
        <h3>Pattern Management (Admin)</h3>
        <div class="table-subtitle">Review and approve auto-learned patterns</div>
      </div>

      <!-- Status filter tabs (same row as title) -->
      <div class="status-tabs">
        <button
          v-for="tab in statusTabs"
          :key="tab.value"
          :class="['status-tab', { active: selectedStatus === tab.value }]"
          @click="() => { selectedStatus = tab.value; console.log('🎯 Tab clicked:', tab.value) }"
        >
          <span class="tab-label">{{ tab.label }}</span>
          <span class="tab-count">{{ getStatusCount(tab.value) }}</span>
        </button>
      </div>
    </div>

    <!-- DataTable -->
    <DataTable
      :value="filteredPatterns"
      :key="selectedStatus"
      :rows="10"
      :paginator="filteredPatterns.length > 10"
      :rowsPerPageOptions="[10, 20, 50]"
      paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
      :globalFilterFields="['pattern', 'category']"
      v-model:filters="filters"
      filterDisplay="row"
      :sortField="sortField"
      :sortOrder="sortOrder"
      @sort="onSort"
      tableStyle="min-width: 50rem"
      class="custom-table"
      :rowHover="true"
      dataKey="id"
    >
      <!-- Pattern column -->
      <Column field="pattern" header="Pattern" :sortable="true" style="min-width: 200px">
        <template #body="slotProps">
          <div class="pattern-cell">
            <span class="pattern-text">{{ slotProps.data.pattern }}</span>
          </div>
        </template>
        <template #filter="{ filterModel, filterCallback }">
          <input
            type="text"
            v-model="filterModel.value"
            @input="filterCallback()"
            class="filter-input"
            placeholder="Search pattern..."
          />
        </template>
      </Column>

      <!-- Category column -->
      <Column field="category" header="Category" :sortable="true" style="min-width: 150px">
        <template #body="slotProps">
          <span class="category-badge">{{ formatCategory(slotProps.data.category) }}</span>
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

      <!-- Confidence column -->
      <Column field="confidence" header="Confidence" :sortable="true" style="min-width: 120px">
        <template #body="slotProps">
          <span class="confidence-value">{{ (slotProps.data.confidence * 100).toFixed(0) }}%</span>
        </template>
      </Column>

      <!-- Times Used column -->
      <Column field="times_used" header="Times Used" :sortable="true" style="min-width: 120px">
        <template #body="slotProps">
          <span class="usage-count">{{ slotProps.data.times_used || 0 }}</span>
        </template>
      </Column>

      <!-- Status column -->
      <Column field="status" header="Status" :sortable="true" style="min-width: 120px">
        <template #body="slotProps">
          <span :class="['status-badge', `status-${slotProps.data.status}`]">
            {{ formatStatus(slotProps.data.status) }}
          </span>
        </template>
      </Column>

      <!-- Actions column -->
      <Column header="Actions" style="min-width: 180px">
        <template #body="slotProps">
          <div class="action-buttons">
            <!-- Approve button (only for pending/disabled) -->
            <button
              v-if="slotProps.data.status === 'pending' || slotProps.data.status === 'disabled'"
              class="action-btn btn-approve"
              @click="handleApprove(slotProps.data.id)"
            >
              ✓ Approve
            </button>

            <!-- Disable button (only for approved) -->
            <button
              v-if="slotProps.data.status === 'approved'"
              class="action-btn btn-disable"
              @click="handleDisable(slotProps.data.id)"
            >
              ⊗ Disable
            </button>

            <!-- Delete button (always visible) -->
            <button
              class="action-btn btn-delete"
              @click="handleDelete(slotProps.data.id)"
            >
              🗑 Delete
            </button>
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Confirmation Dialog -->
    <Dialog
      v-model:visible="showConfirmDialog"
      :header="confirmDialogTitle"
      :modal="true"
      class="confirm-dialog"
      :style="{ width: '450px' }"
    >
      <div class="confirm-content">
        <Icon icon="mdi:alert-circle" class="confirm-icon" />
        <p>{{ confirmDialogMessage }}</p>
      </div>
      <template #footer>
        <button class="dialog-btn btn-cancel" @click="showConfirmDialog = false">Cancel</button>
        <button class="dialog-btn btn-confirm" @click="executeAction">Confirm</button>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import { Icon } from '@iconify/vue'
import { useLearningStore } from '../../stores/learning-store'
import { useToast } from 'primevue/usetoast'

// FilterMatchMode implementation
const FilterMatchMode = {
  CONTAINS: 'contains'
} as const

const props = defineProps<{
  patterns: any[]
  isLoading?: boolean
  error?: string | null
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

// Debug logging
console.log('🔧 PatternManagement mounted', {
  patternsCount: props.patterns?.length || 0,
  patterns: props.patterns,
  isLoading: props.isLoading,
  error: props.error
})

const learningStore = useLearningStore()
const toast = useToast()

// Status tabs
const statusTabs = [
  { label: 'All', value: 'all' },
  { label: 'Pending', value: 'pending' },
  { label: 'Approved', value: 'approved' },
  { label: 'Disabled', value: 'disabled' }
]

// Table state
const selectedStatus = ref('approved') // Default to approved patterns (existing patterns after migration)
const filters = ref({
  pattern: { value: null, matchMode: FilterMatchMode.CONTAINS },
  category: { value: null, matchMode: FilterMatchMode.CONTAINS }
})

const sortField = ref('created_at')
const sortOrder = ref(-1) // Descending by default

// Confirmation dialog
const showConfirmDialog = ref(false)
const confirmDialogTitle = ref('')
const confirmDialogMessage = ref('')
const pendingAction = ref<{ type: 'approve' | 'disable' | 'delete', patternId: number } | null>(null)

// Filtered patterns by status
const filteredPatterns = computed(() => {
  const result = selectedStatus.value === 'all'
    ? props.patterns
    : props.patterns.filter(p => p.status === selectedStatus.value)

  console.log('🔍 filteredPatterns computed', {
    selectedStatus: selectedStatus.value,
    totalPatterns: props.patterns.length,
    filteredCount: result.length,
    firstPattern: result[0],
    statuses: result.map(p => p.status)
  })

  return result
})

// Count patterns by status
const getStatusCount = (status: string): number => {
  if (status === 'all') return props.patterns.length
  return props.patterns.filter(p => p.status === status).length
}

// Format category name
const formatCategory = (category: string): string => {
  return category
    .replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// Format status
const formatStatus = (status: string): string => {
  return status.charAt(0).toUpperCase() + status.slice(1)
}

// Handle approve action
const handleApprove = (patternId: number) => {
  confirmDialogTitle.value = 'Approve Pattern'
  confirmDialogMessage.value = 'Are you sure you want to approve this pattern? It will be used in fast-path matching.'
  pendingAction.value = { type: 'approve', patternId }
  showConfirmDialog.value = true
}

// Handle disable action
const handleDisable = (patternId: number) => {
  confirmDialogTitle.value = 'Disable Pattern'
  confirmDialogMessage.value = 'Are you sure you want to disable this pattern? It will no longer be used in fast-path matching.'
  pendingAction.value = { type: 'disable', patternId }
  showConfirmDialog.value = true
}

// Handle delete action
const handleDelete = (patternId: number) => {
  confirmDialogTitle.value = 'Delete Pattern'
  confirmDialogMessage.value = 'Are you sure you want to permanently delete this pattern? This action cannot be undone.'
  pendingAction.value = { type: 'delete', patternId }
  showConfirmDialog.value = true
}

// Execute confirmed action
const executeAction = async () => {
  if (!pendingAction.value) return

  const { type, patternId } = pendingAction.value
  showConfirmDialog.value = false

  try {
    if (type === 'approve') {
      await learningStore.approvePattern(patternId)
      toast.add({
        severity: 'success',
        summary: 'Pattern Approved',
        detail: 'Pattern has been approved and will be used in fast-path matching',
        life: 3000
      })
    } else if (type === 'disable') {
      await learningStore.disablePattern(patternId)
      toast.add({
        severity: 'success',
        summary: 'Pattern Disabled',
        detail: 'Pattern has been disabled and will no longer be used',
        life: 3000
      })
    } else if (type === 'delete') {
      await learningStore.deletePattern(patternId)
      toast.add({
        severity: 'success',
        summary: 'Pattern Deleted',
        detail: 'Pattern has been permanently deleted',
        life: 3000
      })
    }

    // Refresh patterns
    emit('refresh')

  } catch (error: any) {
    toast.add({
      severity: 'error',
      summary: 'Action Failed',
      detail: error.message || 'Failed to execute action',
      life: 5000
    })
  } finally {
    pendingAction.value = null
  }
}

// Handle sort
const onSort = (event: any) => {
  sortField.value = event.sortField
  sortOrder.value = event.sortOrder
}

// Watch patterns changes
watch(() => props.patterns, (newPatterns) => {
  console.log('🔄 PatternManagement patterns updated')
  console.log('  Count:', newPatterns?.length || 0)
  console.log('  First pattern:', newPatterns?.[0])
  console.log('  First pattern.status:', newPatterns?.[0]?.status)
  console.log('  All statuses:', newPatterns?.map(p => p.status))
}, { deep: true, immediate: true })

// Watch selectedStatus changes
watch(selectedStatus, (newStatus) => {
  console.log('🎯 selectedStatus changed to:', newStatus)
  console.log('  filteredPatterns will be:', filteredPatterns.value.length, 'items')
})
</script>

<style scoped>
.pattern-management {
  background: #1a1a1a;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #2a2a2a;
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

/* Header row: title + tabs side by side */
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 20px;
  flex-wrap: wrap;
}

.table-header {
  flex-shrink: 0;
}

.table-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 4px 0;
}

.table-subtitle {
  font-size: 11px;
  color: #888888;
}

/* Status tabs (right side of header) */
.status-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.status-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  color: #888888;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.status-tab:hover {
  background: #222222;
  border-color: #2563eb;
  color: #e5e5e5;
}

.status-tab.active {
  background: #2563eb;
  border-color: #2563eb;
  color: #ffffff;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3);
  transform: translateY(-1px);
}

.tab-label {
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tab-count {
  background: rgba(255, 255, 255, 0.2);
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  min-width: 24px;
  text-align: center;
}

.status-tab.active .tab-count {
  background: rgba(255, 255, 255, 0.3);
}

/* Custom PrimeVue DataTable styling */
.custom-table {
  font-size: 13px;
  flex: 1;
  overflow-y: auto;
  min-height: 0;
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

/* Pattern cell */
.pattern-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pattern-text {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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

/* Confidence & usage */
.confidence-value,
.usage-count {
  font-weight: 600;
  color: #e5e5e5;
}

/* Status badges */
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-badge.status-pending {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.status-badge.status-approved {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-badge.status-disabled {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

/* Action buttons */
.action-buttons {
  display: flex;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 6px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.btn-approve {
  background: rgba(16, 185, 129, 0.25);
  color: #34d399;
  border: 2px solid #10b981;
  font-weight: 700;
}

.btn-approve:hover {
  background: rgba(16, 185, 129, 0.4);
  border-color: #34d399;
  color: #ffffff;
}

.btn-disable {
  background: rgba(245, 158, 11, 0.25);
  color: #fbbf24;
  border: 2px solid #f59e0b;
  font-weight: 700;
}

.btn-disable:hover {
  background: rgba(245, 158, 11, 0.4);
  border-color: #fbbf24;
  color: #ffffff;
}

.btn-delete {
  background: rgba(239, 68, 68, 0.25);
  color: #f87171;
  border: 2px solid #ef4444;
  font-weight: 700;
}

.btn-delete:hover {
  background: rgba(239, 68, 68, 0.4);
  border-color: #f87171;
  color: #ffffff;
}

/* Confirmation dialog */
.confirm-dialog :deep(.p-dialog) {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  border-radius: 12px;
}

.confirm-dialog :deep(.p-dialog-header) {
  background: #1a1a1a;
  color: #ffffff;
  border-bottom: 1px solid #2a2a2a;
  padding: 20px;
}

.confirm-dialog :deep(.p-dialog-content) {
  background: #1a1a1a;
  color: #e5e5e5;
  padding: 20px;
}

.confirm-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  text-align: center;
}

.confirm-icon {
  font-size: 48px;
  color: #f59e0b;
}

.confirm-content p {
  margin: 0;
  font-size: 14px;
  color: #888888;
}

.dialog-btn {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel {
  background: #2a2a2a;
  color: #e5e5e5;
  border: 1px solid #2a2a2a;
}

.btn-cancel:hover {
  background: #3a3a3a;
}

.btn-confirm {
  background: #2563eb;
  color: #ffffff;
  border: 1px solid #2563eb;
}

.btn-confirm:hover {
  background: #1d4ed8;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .pattern-management {
    padding: 12px;
  }

  .status-tabs {
    gap: 6px;
  }

  .status-tab {
    padding: 6px 12px;
    font-size: 11px;
  }

  .action-btn {
    width: 28px;
    height: 28px;
    font-size: 14px;
  }
}
</style>
