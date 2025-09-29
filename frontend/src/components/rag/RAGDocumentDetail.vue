<template>
  <Sidebar
    :visible="visible"
    @update:visible="$emit('update:visible', $event)"
    header="Document Details"
    position="right"
    :style="{ width: '50vw', minWidth: '600px' }"
    class="document-detail-sidebar"
  >
    <div v-if="document" class="document-detail-content">
      <!-- Document Header -->
      <div class="document-header">
        <div class="header-icon">
          <i :class="getDocumentIcon(document)" class="doc-icon"></i>
        </div>
        <div class="header-info">
          <h2 class="document-title">{{ document.title || 'Untitled Document' }}</h2>
          <div class="document-meta">
            <Badge
              :value="getStatusLabel(document.status)"
              :severity="getStatusSeverity(document.status)"
              class="status-badge"
            />
            <span class="separator">•</span>
            <span class="version">Version {{ document.version || 1 }}</span>
            <span class="separator">•</span>
            <span class="size">{{ formatFileSize(document.size) }}</span>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="action-buttons">
        <Button
          label="Edit"
          icon="pi pi-pencil"
          class="p-button-primary p-button-sm"
          @click="startEdit"
        />
        <Button
          label="Download"
          icon="pi pi-download"
          class="p-button-outlined p-button-sm"
          @click="downloadDocument"
        />
        <Button
          label="Delete"
          icon="pi pi-trash"
          class="p-button-outlined p-button-danger p-button-sm"
          @click="confirmDelete"
        />
      </div>

      <!-- Metadata Section -->
      <div class="metadata-section">
        <h3 class="section-title">Metadata</h3>
        <div class="metadata-grid">
          <div class="metadata-item">
            <label>Category:</label>
            <Chip
              :label="formatCategory(document.category)"
              :class="getCategoryClass(document.category)"
            />
          </div>
          <div class="metadata-item">
            <label>Author:</label>
            <span>{{ document.author || 'Unknown' }}</span>
          </div>
          <div class="metadata-item">
            <label>Source:</label>
            <span>{{ formatSource(document.source) }}</span>
          </div>
          <div class="metadata-item">
            <label>Created:</label>
            <span>{{ formatDate(document.created_at) }}</span>
          </div>
          <div class="metadata-item">
            <label>Updated:</label>
            <span>{{ formatDate(document.updated_at) }}</span>
          </div>
          <div class="metadata-item">
            <label>Language:</label>
            <span>{{ document.language || 'Auto-detected' }}</span>
          </div>
        </div>
      </div>

      <!-- Tags Section -->
      <div v-if="document.tags?.length > 0" class="tags-section">
        <h3 class="section-title">Tags</h3>
        <div class="tags-container">
          <Chip
            v-for="tag in document.tags"
            :key="tag"
            :label="tag"
            class="tag-chip"
          />
        </div>
      </div>

      <!-- Content Section -->
      <div class="content-section">
        <div class="section-header">
          <h3 class="section-title">Content</h3>
          <Button
            :label="showFullContent ? 'Show Preview' : 'Show Full'"
            :icon="showFullContent ? 'pi pi-compress' : 'pi pi-expand'"
            class="p-button-text p-button-sm"
            @click="toggleContent"
          />
        </div>

        <div class="content-display">
          <div
            v-if="!showFullContent"
            class="content-preview"
            :class="{ 'expandable': !showFullContent }"
          >
            {{ getContentPreview() }}
          </div>
          <div v-else class="content-full">
            <div class="content-text">{{ document.content || 'No content available' }}</div>
          </div>
        </div>
      </div>

      <!-- Similar Documents -->
      <div v-if="similarDocuments.length > 0" class="similar-section">
        <h3 class="section-title">Similar Documents</h3>
        <div class="similar-list">
          <div
            v-for="similar in similarDocuments"
            :key="similar.id"
            class="similar-item"
            @click="selectSimilar(similar)"
          >
            <div class="similar-info">
              <div class="similar-title">{{ similar.title }}</div>
              <div class="similar-meta">
                {{ formatCategory(similar.category) }} • {{ formatDate(similar.created_at) }}
              </div>
            </div>
            <div class="similarity-score">
              {{ (similar.similarity * 100).toFixed(1) }}%
            </div>
          </div>
        </div>
      </div>

      <!-- Version History -->
      <div v-if="versionHistory.length > 0" class="version-section">
        <h3 class="section-title">Version History</h3>
        <div class="version-list">
          <div
            v-for="version in versionHistory"
            :key="version.version"
            class="version-item"
            :class="{ 'current': version.version === document.version }"
          >
            <div class="version-info">
              <div class="version-number">v{{ version.version }}</div>
              <div class="version-meta">
                {{ version.author }} • {{ formatDate(version.created_at) }}
              </div>
              <div v-if="version.change_summary" class="version-changes">
                {{ version.change_summary }}
              </div>
            </div>
            <div class="version-actions">
              <Button
                v-if="version.version !== document.version"
                label="Restore"
                icon="pi pi-undo"
                class="p-button-text p-button-sm"
                @click="restoreVersion(version.version)"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Mode -->
    <div v-if="editMode" class="edit-overlay">
      <div class="edit-header">
        <h3>Edit Document</h3>
        <div class="edit-actions">
          <Button
            label="Cancel"
            icon="pi pi-times"
            class="p-button-outlined p-button-sm"
            @click="cancelEdit"
          />
          <Button
            label="Save"
            icon="pi pi-check"
            class="p-button-primary p-button-sm"
            @click="saveEdit"
            :loading="saving"
          />
        </div>
      </div>

      <div class="edit-form">
        <div class="form-group">
          <label>Title:</label>
          <InputText
            v-model="editData.title"
            placeholder="Document title"
            class="edit-input"
          />
        </div>

        <div class="form-group">
          <label>Category:</label>
          <Dropdown
            v-model="editData.category"
            :options="categoryOptions"
            option-label="label"
            option-value="value"
            placeholder="Select category"
            class="edit-input"
          />
        </div>

        <div class="form-group">
          <label>Tags (comma-separated):</label>
          <InputText
            v-model="editData.tagsText"
            placeholder="tag1, tag2, tag3"
            class="edit-input"
          />
        </div>

        <div class="form-group">
          <label>Content:</label>
          <Textarea
            v-model="editData.content"
            rows="15"
            placeholder="Document content"
            class="edit-textarea"
          />
        </div>
      </div>
    </div>

    <!-- Confirm Dialog -->
    <ConfirmDialog />
  </Sidebar>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'

import Sidebar from 'primevue/sidebar'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Chip from 'primevue/chip'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import ConfirmDialog from 'primevue/confirmdialog'

import { ragApi } from '@/api/rag'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  document: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'document-updated', 'document-deleted'])

const toast = useToast()
const confirm = useConfirm()

// Reactive state
const showFullContent = ref(false)
const editMode = ref(false)
const saving = ref(false)
const similarDocuments = ref([])
const versionHistory = ref([])

// Edit data
const editData = reactive({
  title: '',
  category: '',
  content: '',
  tagsText: ''
})

// Category options
const categoryOptions = [
  { label: 'Business Process', value: 'business_process' },
  { label: 'Documentation', value: 'documentation' },
  { label: 'Training Material', value: 'training' },
  { label: 'Policy', value: 'policy' },
  { label: 'General', value: 'general' }
]

// Watch document changes
watch(() => props.document, async (newDoc) => {
  if (newDoc) {
    await loadSimilarDocuments()
    await loadVersionHistory()
  }
})

// Watch visibility
watch(() => props.visible, (visible) => {
  if (!visible) {
    resetState()
  }
})

// Initialize
onMounted(() => {
  if (props.document) {
    loadSimilarDocuments()
    loadVersionHistory()
  }
})

// Reset component state
const resetState = () => {
  showFullContent.value = false
  editMode.value = false
  saving.value = false
  similarDocuments.value = []
  versionHistory.value = []
}

// Load similar documents
const loadSimilarDocuments = async () => {
  if (!props.document?.id) return

  try {
    const response = await ragApi.getSimilarDocuments(props.document.id, 5)
    similarDocuments.value = response.similar_documents || []
  } catch (error) {
    console.error('Error loading similar documents:', error)
  }
}

// Load version history
const loadVersionHistory = async () => {
  if (!props.document?.id) return

  try {
    const response = await ragApi.getDocumentHistory(props.document.id)
    versionHistory.value = response.versions || []
  } catch (error) {
    console.error('Error loading version history:', error)
    // Mock data for demonstration
    versionHistory.value = [
      {
        version: props.document.version || 1,
        author: props.document.author || 'Unknown',
        created_at: props.document.updated_at || new Date().toISOString(),
        change_summary: 'Current version'
      }
    ]
  }
}

// Toggle content display
const toggleContent = () => {
  showFullContent.value = !showFullContent.value
}

// Get content preview
const getContentPreview = () => {
  const content = props.document?.content || 'No content available'
  return content.length > 300 ? content.substring(0, 300) + '...' : content
}

// Start editing
const startEdit = () => {
  editData.title = props.document?.title || ''
  editData.category = props.document?.category || ''
  editData.content = props.document?.content || ''
  editData.tagsText = props.document?.tags?.join(', ') || ''
  editMode.value = true
}

// Cancel editing
const cancelEdit = () => {
  editMode.value = false
  Object.assign(editData, {
    title: '',
    category: '',
    content: '',
    tagsText: ''
  })
}

// Save edit
const saveEdit = async () => {
  saving.value = true

  try {
    const updateData = {
      content: editData.content,
      metadata: {
        title: editData.title,
        category: editData.category,
        tags: editData.tagsText.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0)
      }
    }

    await ragApi.updateDocument(props.document.id, updateData)

    toast.add({
      severity: 'success',
      summary: 'Document Updated',
      detail: 'Document has been updated successfully',
      life: 3000
    })

    editMode.value = false
    emit('document-updated')

  } catch (error) {
    console.error('Error updating document:', error)
    toast.add({
      severity: 'error',
      summary: 'Update Failed',
      detail: error.message || 'Failed to update document',
      life: 5000
    })
  } finally {
    saving.value = false
  }
}

// Download document
const downloadDocument = () => {
  // TODO: Implement download functionality
  toast.add({
    severity: 'info',
    summary: 'Download',
    detail: 'Document download feature coming soon',
    life: 3000
  })
}

// Confirm delete
const confirmDelete = () => {
  confirm.require({
    message: `Are you sure you want to delete "${props.document?.title}"?`,
    header: 'Delete Confirmation',
    icon: 'pi pi-exclamation-triangle',
    accept: deleteDocument,
    reject: () => {}
  })
}

// Delete document
const deleteDocument = async () => {
  try {
    await ragApi.deleteDocument(props.document.id)

    toast.add({
      severity: 'success',
      summary: 'Document Deleted',
      detail: 'Document has been deleted successfully',
      life: 3000
    })

    emit('document-deleted')

  } catch (error) {
    console.error('Error deleting document:', error)
    toast.add({
      severity: 'error',
      summary: 'Delete Failed',
      detail: error.message || 'Failed to delete document',
      life: 5000
    })
  }
}

// Select similar document
const selectSimilar = (similar) => {
  emit('update:visible', false)
  // TODO: Navigate to similar document
  console.log('Navigate to similar document:', similar.id)
}

// Restore version
const restoreVersion = async (version) => {
  confirm.require({
    message: `Are you sure you want to restore version ${version}?`,
    header: 'Restore Version',
    icon: 'pi pi-question-circle',
    accept: async () => {
      try {
        await ragApi.restoreDocumentVersion(props.document.id, version)

        toast.add({
          severity: 'success',
          summary: 'Version Restored',
          detail: `Document restored to version ${version}`,
          life: 3000
        })

        emit('document-updated')

      } catch (error) {
        console.error('Error restoring version:', error)
        toast.add({
          severity: 'error',
          summary: 'Restore Failed',
          detail: error.message || 'Failed to restore version',
          life: 5000
        })
      }
    },
    reject: () => {}
  })
}

// Utility functions
const formatCategory = (category) => {
  if (!category) return 'General'
  return category.charAt(0).toUpperCase() + category.slice(1).replace(/_/g, ' ')
}

const formatSource = (source) => {
  const sourceMap = {
    'upload': 'Manual Upload',
    'bulk_import': 'Bulk Import',
    'api': 'API Import',
    'system': 'System Generated'
  }
  return sourceMap[source] || 'Unknown'
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'Unknown'
  return new Date(dateStr).toLocaleString()
}

const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getDocumentIcon = (document) => {
  const source = document?.source || 'unknown'
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
.document-detail-sidebar {
  z-index: 1001;
}

.document-detail-content {
  padding: 0;
  height: 100%;
  overflow-y: auto;
}

.document-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header-icon {
  flex-shrink: 0;
}

.doc-icon {
  font-size: 3rem;
  color: rgba(255, 255, 255, 0.9);
}

.header-info {
  flex: 1;
}

.document-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: white;
}

.document-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: rgba(255, 255, 255, 0.8);
}

.separator {
  color: rgba(255, 255, 255, 0.5);
}

.action-buttons {
  display: flex;
  gap: 0.75rem;
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.metadata-section,
.tags-section,
.content-section,
.similar-section,
.version-section {
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.section-title {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.metadata-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.metadata-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.metadata-item label {
  font-weight: 600;
  color: #6c757d;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag-chip {
  background: #f8f9fa !important;
  color: #495057 !important;
}

.content-display {
  background: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
}

.content-preview {
  padding: 1.5rem;
  line-height: 1.6;
  color: #495057;
}

.content-full {
  max-height: 400px;
  overflow-y: auto;
}

.content-text {
  padding: 1.5rem;
  line-height: 1.6;
  color: #495057;
  white-space: pre-wrap;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.similar-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.similar-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.similar-item:hover {
  background: #e9ecef;
  transform: translateY(-1px);
}

.similar-title {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.similar-meta {
  font-size: 0.85rem;
  color: #6c757d;
}

.similarity-score {
  font-weight: 600;
  color: #28a745;
}

.version-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.version-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #dee2e6;
}

.version-item.current {
  border-left-color: #28a745;
  background: #e8f5e8;
}

.version-number {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.version-meta {
  font-size: 0.85rem;
  color: #6c757d;
  margin-bottom: 0.25rem;
}

.version-changes {
  font-size: 0.8rem;
  color: #495057;
  font-style: italic;
}

.edit-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: white;
  z-index: 10;
  display: flex;
  flex-direction: column;
}

.edit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.edit-header h3 {
  margin: 0;
  color: #2c3e50;
}

.edit-actions {
  display: flex;
  gap: 0.75rem;
}

.edit-form {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #495057;
}

.edit-input,
.edit-textarea {
  width: 100%;
}

.edit-textarea {
  resize: vertical;
  min-height: 300px;
  font-family: 'Courier New', monospace;
}

/* Category styles */
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

@media (max-width: 768px) {
  .metadata-grid {
    grid-template-columns: 1fr;
  }

  .edit-actions {
    flex-direction: column;
  }
}
</style>