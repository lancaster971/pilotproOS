<template>
  <div class="rag-document-list">
    <!-- Controls Header -->
    <div class="controls-header">
      <div class="search-controls">
        <div class="p-inputgroup">
          <InputText
            v-model="searchTerm"
            placeholder="Search documents by name or content..."
            @input="debouncedSearch"
            class="search-input"
          />
          <Button
            icon="pi pi-search"
            class="p-button-outlined"
            @click="loadDocuments"
          />
        </div>
      </div>

      <div class="filter-controls">
        <Dropdown
          v-model="filters.category"
          :options="categoryOptions"
          option-label="label"
          option-value="value"
          placeholder="Filter by Category"
          class="category-filter"
          @change="loadDocuments"
        />

        <Dropdown
          v-model="filters.sort_by"
          :options="sortOptions"
          option-label="label"
          option-value="value"
          placeholder="Sort by"
          class="sort-filter"
          @change="loadDocuments"
        />

        <Dropdown
          v-model="filters.sort_order"
          :options="orderOptions"
          option-label="label"
          option-value="value"
          class="order-filter"
          @change="loadDocuments"
        />
      </div>

      <div class="action-controls">
        <Button
          label="Refresh"
          icon="pi pi-refresh"
          class="p-button-outlined"
          @click="refreshList"
          :loading="loading"
        />
      </div>
    </div>

    <!-- Data Table -->
    <DataTable
      :value="documents"
      :loading="loading"
      :paginator="true"
      :rows="filters.page_size"
      :total-records="totalCount"
      :lazy="true"
      @page="onPageChange"
      data-key="id"
      selection-mode="single"
      v-model:selection="selectedDocument"
      @row-select="onRowSelect"
      class="document-table"
      responsive-layout="scroll"
    >
      <!-- Status Column -->
      <Column field="status" header="Status" :sortable="false" style="width: 100px">
        <template #body="{ data }">
          <Badge
            :value="getStatusLabel(data.status)"
            :severity="getStatusSeverity(data.status)"
            class="status-badge"
          />
        </template>
      </Column>

      <!-- Document Title -->
      <Column field="title" header="Document" :sortable="true" style="min-width: 300px">
        <template #body="{ data }">
          <div class="document-title">
            <i :class="getDocumentIcon(data)" class="doc-icon mr-2"></i>
            <div class="title-content">
              <div class="title-text">{{ data.title || 'Untitled Document' }}</div>
              <div class="title-meta">
                <span class="source">{{ data.source || 'Unknown' }}</span>
                <span class="separator">•</span>
                <span class="size">{{ formatFileSize(data.size) }}</span>
              </div>
            </div>
          </div>
        </template>
      </Column>

      <!-- Category -->
      <Column field="category" header="Category" :sortable="true" style="width: 150px">
        <template #body="{ data }">
          <Chip
            :label="formatCategory(data.category)"
            :class="getCategoryClass(data.category)"
            class="category-chip"
          />
        </template>
      </Column>

      <!-- Tags -->
      <Column field="tags" header="Tags" :sortable="false" style="min-width: 200px">
        <template #body="{ data }">
          <div class="tags-container" v-if="data.tags && data.tags.length > 0">
            <Chip
              v-for="tag in data.tags.slice(0, 2)"
              :key="tag"
              :label="tag"
              class="tag-chip"
            />
            <span v-if="data.tags.length > 2" class="more-tags">
              +{{ data.tags.length - 2 }}
            </span>
          </div>
          <span v-else class="no-tags">No tags</span>
        </template>
      </Column>

      <!-- Author -->
      <Column field="author" header="Author" :sortable="true" style="width: 150px">
        <template #body="{ data }">
          <div class="author-info">
            <i class="pi pi-user mr-1"></i>
            {{ data.author || 'Unknown' }}
          </div>
        </template>
      </Column>

      <!-- Created Date -->
      <Column field="created_at" header="Created" :sortable="true" style="width: 120px">
        <template #body="{ data }">
          <div class="date-info">
            {{ formatDate(data.created_at) }}
          </div>
        </template>
      </Column>

      <!-- Updated Date -->
      <Column field="updated_at" header="Updated" :sortable="true" style="width: 120px">
        <template #body="{ data }">
          <div class="date-info">
            {{ formatDate(data.updated_at) }}
          </div>
        </template>
      </Column>

      <!-- Version -->
      <Column field="version" header="Version" :sortable="true" style="width: 100px">
        <template #body="{ data }">
          <Badge
            :value="`v${data.version || 1}`"
            severity="info"
            class="version-badge"
          />
        </template>
      </Column>

      <!-- Actions -->
      <Column header="Actions" :sortable="false" style="width: 180px">
        <template #body="{ data }">
          <div class="action-buttons">
            <Button
              icon="pi pi-eye"
              class="p-button-rounded p-button-text p-button-sm"
              v-tooltip="'View'"
              @click="viewDocument(data)"
            />
            <Button
              icon="pi pi-pencil"
              class="p-button-rounded p-button-text p-button-sm"
              v-tooltip="'Edit'"
              @click="editDocument(data)"
            />
            <Button
              icon="pi pi-download"
              class="p-button-rounded p-button-text p-button-sm"
              v-tooltip="'Download'"
              @click="downloadDocument(data)"
            />
            <Button
              icon="pi pi-trash"
              class="p-button-rounded p-button-text p-button-sm p-button-danger"
              v-tooltip="'Delete'"
              @click="confirmDelete(data)"
            />
          </div>
        </template>
      </Column>

      <!-- Empty State -->
      <template #empty>
        <div class="empty-table-state">
          <div class="empty-icon">
            <i class="pi pi-file"></i>
          </div>
          <h3>No Documents Found</h3>
          <p v-if="searchTerm">No documents match your search criteria</p>
          <p v-else>Your knowledge base is empty</p>
          <Button
            label="Upload Documents"
            icon="pi pi-upload"
            class="p-button-primary"
            @click="$emit('upload-requested')"
          />
        </div>
      </template>
    </DataTable>

    <!-- Delete Confirmation Dialog -->
    <ConfirmDialog />

    <!-- Document Preview Dialog -->
    <Dialog
      v-model:visible="showPreviewDialog"
      :header="previewDocument?.title || 'Document Preview'"
      :style="{ width: '80vw', height: '80vh' }"
      :modal="true"
      :draggable="false"
      class="preview-dialog"
    >
      <div v-if="previewDocument" class="preview-content">
        <div class="preview-metadata">
          <div class="metadata-grid">
            <div class="metadata-item">
              <label>Category:</label>
              <Chip :label="formatCategory(previewDocument.category)" />
            </div>
            <div class="metadata-item">
              <label>Author:</label>
              <span>{{ previewDocument.author }}</span>
            </div>
            <div class="metadata-item">
              <label>Created:</label>
              <span>{{ formatDate(previewDocument.created_at) }}</span>
            </div>
            <div class="metadata-item">
              <label>Version:</label>
              <Badge :value="`v${previewDocument.version}`" severity="info" />
            </div>
          </div>
          <div v-if="previewDocument.tags?.length" class="tags-section">
            <label>Tags:</label>
            <div class="tags-list">
              <Chip
                v-for="tag in previewDocument.tags"
                :key="tag"
                :label="tag"
                class="tag-chip"
              />
            </div>
          </div>
        </div>

        <div class="preview-divider"></div>

        <div class="preview-text">
          <h4>Content Preview:</h4>
          <div class="content-text">
            {{ previewDocument.content || 'No content available' }}
          </div>
        </div>
      </div>

      <template #footer>
        <div class="preview-actions">
          <Button
            label="Edit Document"
            icon="pi pi-pencil"
            class="p-button-primary"
            @click="editPreviewDocument"
          />
          <Button
            label="Close"
            icon="pi pi-times"
            class="p-button-outlined"
            @click="showPreviewDialog = false"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useToast } from 'vue-toastification'
import { useConfirm } from 'primevue/useconfirm'
import { debounce } from 'lodash-es'

import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Badge from 'primevue/badge'
import Chip from 'primevue/chip'
import Dialog from 'primevue/dialog'
import ConfirmDialog from 'primevue/confirmdialog'

import { ragApi } from '@/api/rag'

const emit = defineEmits(['document-selected', 'document-updated', 'document-deleted', 'upload-requested'])

const toast = useToast()
const confirm = useConfirm()

// Reactive state
const documents = ref([])
const loading = ref(false)
const searchTerm = ref('')
const selectedDocument = ref(null)
const totalCount = ref(0)
const showPreviewDialog = ref(false)
const previewDocument = ref(null)

// Filters
const filters = ref({
  category: null,
  sort_by: 'created_at',
  sort_order: 'desc',
  page: 1,
  page_size: 20
})

// Options
const categoryOptions = ref([
  { label: 'All Categories', value: null }
])

const sortOptions = [
  { label: 'Created Date', value: 'created_at' },
  { label: 'Updated Date', value: 'updated_at' },
  { label: 'Title', value: 'title' },
  { label: 'Author', value: 'author' },
  { label: 'Size', value: 'size' }
]

const orderOptions = [
  { label: 'Newest First', value: 'desc' },
  { label: 'Oldest First', value: 'asc' }
]

// Debounced search
const debouncedSearch = debounce(() => {
  filters.value.page = 1
  loadDocuments()
}, 500)

// Initialize
onMounted(async () => {
  await loadCategories()
  await loadDocuments()
})

// Load available categories
const loadCategories = async () => {
  try {
    const stats = await ragApi.getStatistics()
    const categories = stats.categories || []

    categoryOptions.value = [
      { label: 'All Categories', value: null },
      ...categories.map(cat => ({
        label: formatCategory(cat),
        value: cat
      }))
    ]
  } catch (error) {
    console.error('Error loading categories:', error)
  }
}

// Load documents
const loadDocuments = async () => {
  loading.value = true

  try {
    const params = {
      page: filters.value.page,
      page_size: filters.value.page_size,
      sort_by: filters.value.sort_by,
      sort_order: filters.value.sort_order
    }

    if (filters.value.category) {
      params.category = filters.value.category
    }

    if (searchTerm.value.trim()) {
      params.search = searchTerm.value.trim()
    }

    const response = await ragApi.listDocuments(params)

    documents.value = response.documents || []
    totalCount.value = response.total_count || 0
  } catch (error) {
    console.error('Error loading documents:', error)
    toast.error('Failed to load documents')
    documents.value = []
    totalCount.value = 0
  } finally {
    loading.value = false
  }
}

// Refresh list
const refreshList = async () => {
  filters.value.page = 1
  await loadDocuments()
}

// Handle page change
const onPageChange = (event) => {
  filters.value.page = event.page + 1
  loadDocuments()
}

// Handle row selection
const onRowSelect = (event) => {
  emit('document-selected', event.data)
}

// View document
const viewDocument = (document) => {
  previewDocument.value = document
  showPreviewDialog.value = true
}

// Edit document
const editDocument = (document) => {
  emit('document-selected', document)
}

// Edit preview document
const editPreviewDocument = () => {
  showPreviewDialog.value = false
  emit('document-selected', previewDocument.value)
}

// Download document
const downloadDocument = (document) => {
  // TODO: Implement document download
  toast.info('Document download feature coming soon')
}

// Confirm delete
const confirmDelete = (document) => {
  confirm.require({
    message: `Are you sure you want to delete "${document.title}"?`,
    header: 'Delete Confirmation',
    icon: 'pi pi-exclamation-triangle',
    accept: () => deleteDocument(document),
    reject: () => {}
  })
}

// Delete document
const deleteDocument = async (document) => {
  try {
    await ragApi.deleteDocument(document.id)

    toast.success('Document deleted successfully')

    emit('document-deleted', document)
    await loadDocuments()
  } catch (error) {
    console.error('Error deleting document:', error)
    toast.error('Failed to delete document')
  }
}

// Utility functions
const formatCategory = (category) => {
  if (!category) return 'General'
  return category.charAt(0).toUpperCase() + category.slice(1).replace(/_/g, ' ')
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'Unknown'
  return new Date(dateStr).toLocaleDateString()
}

const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getDocumentIcon = (document) => {
  const source = document.source || 'unknown'
  const iconMap = {
    'upload': 'pi pi-upload',
    'bulk_import': 'pi pi-download',
    'api': 'pi pi-cog',
    'system': 'pi pi-server'
  }
  return iconMap[source] || 'pi pi-file'
}

const getStatusLabel = (status) => {
  const statusMap = {
    'active': 'Active',
    'archived': 'Archived',
    'processing': 'Processing',
    'error': 'Error'
  }
  return statusMap[status] || 'Unknown'
}

const getStatusSeverity = (status) => {
  const severityMap = {
    'active': 'success',
    'archived': 'secondary',
    'processing': 'warning',
    'error': 'danger'
  }
  return severityMap[status] || 'secondary'
}

const getCategoryClass = (category) => {
  const classMap = {
    'business_process': 'category-business',
    'documentation': 'category-docs',
    'training': 'category-training',
    'policy': 'category-policy',
    'general': 'category-general'
  }
  return classMap[category] || 'category-general'
}
</script>

<style scoped>
.rag-document-list {
  padding: 1.5rem;
}

.controls-header {
  display: grid;
  grid-template-columns: 2fr 1fr auto;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.search-input {
  min-width: 300px;
}

.filter-controls {
  display: flex;
  gap: 0.5rem;
}

.category-filter,
.sort-filter,
.order-filter {
  min-width: 120px;
}

.document-table {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.document-title {
  display: flex;
  align-items: center;
}

.doc-icon {
  color: #3498db;
  font-size: 1.2rem;
}

.title-content {
  flex: 1;
}

.title-text {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.title-meta {
  font-size: 0.8rem;
  color: #7f8c8d;
}

.separator {
  margin: 0 0.5rem;
}

.status-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
}

.category-chip {
  font-size: 0.75rem;
}

.category-business {
  background: #e8f5e8 !important;
  color: #2e7d32 !important;
}

.category-docs {
  background: #e3f2fd !important;
  color: #1976d2 !important;
}

.category-training {
  background: #fff3e0 !important;
  color: #f57c00 !important;
}

.category-policy {
  background: #fce4ec !important;
  color: #c2185b !important;
}

.category-general {
  background: #f5f5f5 !important;
  color: #616161 !important;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  align-items: center;
}

.tag-chip {
  font-size: 0.7rem;
  padding: 0.25rem 0.5rem;
  background: #f8f9fa;
  color: #495057;
}

.more-tags {
  font-size: 0.8rem;
  color: #7f8c8d;
  font-style: italic;
}

.no-tags {
  color: #bdc3c7;
  font-style: italic;
}

.author-info {
  display: flex;
  align-items: center;
  color: #495057;
}

.date-info {
  font-size: 0.9rem;
  color: #495057;
}

.version-badge {
  font-size: 0.75rem;
}

.action-buttons {
  display: flex;
  gap: 0.25rem;
}

.empty-table-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-icon {
  font-size: 4rem;
  color: #bdc3c7;
  margin-bottom: 1rem;
}

.empty-table-state h3 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.empty-table-state p {
  color: #7f8c8d;
  margin-bottom: 2rem;
}

.preview-dialog {
  max-width: none !important;
}

.preview-content {
  height: calc(80vh - 160px);
  overflow-y: auto;
}

.preview-metadata {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.metadata-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.metadata-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.metadata-item label {
  font-weight: 600;
  color: #495057;
  min-width: 80px;
}

.tags-section {
  border-top: 1px solid #dee2e6;
  padding-top: 1rem;
}

.tags-section label {
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.5rem;
  display: block;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.preview-divider {
  height: 1px;
  background: #dee2e6;
  margin: 1rem 0;
}

.preview-text h4 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.content-text {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  line-height: 1.6;
  color: #495057;
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  max-height: 400px;
  overflow-y: auto;
}

.preview-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .controls-header {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .filter-controls {
    flex-direction: column;
  }

  .filter-controls > * {
    width: 100%;
  }
}
</style>