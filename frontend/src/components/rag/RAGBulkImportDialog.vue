<template>
  <Dialog
    :visible="visible"
    @update:visible="$emit('update:visible', $event)"
    header="Bulk Import from ZIP Archive"
    :style="{ width: '60vw', maxWidth: '700px' }"
    :modal="true"
    class="bulk-import-dialog"
  >
    <div class="import-content">
      <!-- ZIP Upload Area -->
      <div
        class="zip-upload-zone"
        :class="{ 'drag-over': isDragOver, 'has-file': selectedFile }"
        @drop="handleDrop"
        @dragover.prevent="isDragOver = true"
        @dragleave.prevent="isDragOver = false"
        @click="openFileDialog"
      >
        <div v-if="!selectedFile" class="upload-empty">
          <div class="upload-icon">
            <i class="pi pi-file-zip"></i>
          </div>
          <h3>Select ZIP Archive</h3>
          <p>Drag & drop or click to browse</p>
          <Button
            label="Browse Files"
            icon="pi pi-folder-open"
            class="p-button-outlined"
            @click.stop="openFileDialog"
          />
        </div>

        <div v-else class="selected-file">
          <div class="file-info">
            <i class="pi pi-file-zip file-icon"></i>
            <div class="file-details">
              <div class="file-name">{{ selectedFile.name }}</div>
              <div class="file-size">{{ formatFileSize(selectedFile.size) }}</div>
            </div>
          </div>
          <Button
            icon="pi pi-times"
            class="p-button-rounded p-button-text p-button-danger"
            @click="removeFile"
          />
        </div>
      </div>

      <!-- Import Progress -->
      <div v-if="importing" class="import-progress">
        <div class="progress-header">
          <h4>Importing Documents...</h4>
          <span class="progress-stats">
            {{ importStatus.processed }}/{{ importStatus.total }}
          </span>
        </div>

        <ProgressBar :value="progressPercentage" class="import-progress-bar" />

        <div v-if="importStatus.current_file" class="current-file">
          Processing: {{ importStatus.current_file }}
        </div>

        <div class="import-details">
          <div class="detail-item">
            <span class="label">Processed:</span>
            <span class="value success">{{ importStatus.processed_files }}</span>
          </div>
          <div class="detail-item">
            <span class="label">Failed:</span>
            <span class="value error">{{ importStatus.failed_files }}</span>
          </div>
          <div class="detail-item">
            <span class="label">Processing Time:</span>
            <span class="value">{{ formatTime(importStatus.processing_time_seconds) }}</span>
          </div>
        </div>

        <!-- Error List -->
        <div v-if="importStatus.errors?.length > 0" class="import-errors">
          <h5><i class="pi pi-exclamation-triangle mr-1"></i>Import Errors</h5>
          <div class="error-list">
            <div
              v-for="(error, index) in importStatus.errors.slice(0, 5)"
              :key="index"
              class="error-item"
            >
              {{ error }}
            </div>
            <div v-if="importStatus.errors.length > 5" class="more-errors">
              +{{ importStatus.errors.length - 5 }} more errors
            </div>
          </div>
        </div>
      </div>

      <!-- Import Results -->
      <div v-if="importComplete && !importing" class="import-results">
        <div class="results-header">
          <div class="success-icon">
            <i class="pi pi-check-circle"></i>
          </div>
          <h3>Import Complete!</h3>
        </div>

        <div class="results-summary">
          <div class="summary-grid">
            <div class="summary-item success">
              <div class="summary-value">{{ finalResults.processed_files }}</div>
              <div class="summary-label">Processed</div>
            </div>
            <div class="summary-item error">
              <div class="summary-value">{{ finalResults.failed_files }}</div>
              <div class="summary-label">Failed</div>
            </div>
            <div class="summary-item info">
              <div class="summary-value">{{ formatTime(finalResults.processing_time_seconds) }}</div>
              <div class="summary-label">Duration</div>
            </div>
          </div>
        </div>

        <div v-if="finalResults.errors?.length > 0" class="final-errors">
          <Accordion>
            <AccordionTab :header="`View Errors (${finalResults.errors.length})`">
              <div class="error-details">
                <div
                  v-for="(error, index) in finalResults.errors"
                  :key="index"
                  class="error-detail"
                >
                  {{ error }}
                </div>
              </div>
            </AccordionTab>
          </Accordion>
        </div>
      </div>

      <!-- Instructions -->
      <div v-if="!selectedFile && !importing && !importComplete" class="import-instructions">
        <h4>How to prepare your ZIP archive:</h4>
        <ul class="instructions-list">
          <li>Include only supported file types: PDF, DOCX, TXT, MD, HTML</li>
          <li>Organize files in folders by category (optional)</li>
          <li>Maximum archive size: 500MB</li>
          <li>Individual file size limit: 50MB each</li>
          <li>Avoid duplicate file names</li>
        </ul>

        <div class="supported-formats">
          <strong>Supported formats:</strong>
          <div class="format-chips">
            <Chip label="PDF" class="format-chip" />
            <Chip label="DOCX" class="format-chip" />
            <Chip label="TXT" class="format-chip" />
            <Chip label="MD" class="format-chip" />
            <Chip label="HTML" class="format-chip" />
          </div>
        </div>
      </div>
    </div>

    <!-- Dialog Footer -->
    <template #footer>
      <div class="dialog-actions">
        <Button
          label="Cancel"
          icon="pi pi-times"
          class="p-button-outlined"
          @click="closeDialog"
          :disabled="importing"
        />
        <Button
          v-if="importComplete"
          label="Done"
          icon="pi pi-check"
          class="p-button-primary"
          @click="closeDialog"
        />
        <Button
          v-else-if="!importing"
          label="Start Import"
          icon="pi pi-download"
          class="p-button-primary"
          @click="startImport"
          :disabled="!selectedFile"
        />
        <Button
          v-else
          label="Importing..."
          icon="pi pi-spinner pi-spin"
          class="p-button-primary"
          disabled
        />
      </div>
    </template>

    <!-- Hidden File Input -->
    <input
      ref="fileInput"
      type="file"
      accept=".zip"
      @change="handleFileSelect"
      style="display: none"
    />
  </Dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import ProgressBar from 'primevue/progressbar'
import Chip from 'primevue/chip'
import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'

import { ragApi } from '@/api/rag'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'import-complete'])

const toast = useToast()

// Reactive state
const selectedFile = ref(null)
const isDragOver = ref(false)
const importing = ref(false)
const importComplete = ref(false)
const fileInput = ref(null)

// Import status tracking
const importStatus = reactive({
  total: 0,
  processed: 0,
  processed_files: 0,
  failed_files: 0,
  processing_time_seconds: 0,
  current_file: '',
  errors: []
})

const finalResults = reactive({
  processed_files: 0,
  failed_files: 0,
  processing_time_seconds: 0,
  errors: []
})

// WebSocket for real-time progress
let websocket = null

// Computed
const progressPercentage = computed(() => {
  if (importStatus.total === 0) return 0
  return Math.round((importStatus.processed / importStatus.total) * 100)
})

// Watch dialog visibility
watch(() => props.visible, (newVal) => {
  if (newVal) {
    connectWebSocket()
  } else {
    resetDialog()
    if (websocket) {
      websocket.close()
      websocket = null
    }
  }
})

// Reset dialog state
const resetDialog = () => {
  selectedFile.value = null
  isDragOver.value = false
  importing.value = false
  importComplete.value = false

  // Reset status
  Object.assign(importStatus, {
    total: 0,
    processed: 0,
    processed_files: 0,
    failed_files: 0,
    processing_time_seconds: 0,
    current_file: '',
    errors: []
  })

  Object.assign(finalResults, {
    processed_files: 0,
    failed_files: 0,
    processing_time_seconds: 0,
    errors: []
  })
}

// Connect to WebSocket for progress updates
const connectWebSocket = () => {
  try {
    websocket = ragApi.createWebSocket((message) => {
      if (message.type === 'bulk_import_progress') {
        importStatus.processed = message.processed || 0
        importStatus.total = message.total || 0
        importStatus.current_file = message.current_file || ''
      }
    })
  } catch (error) {
    console.error('Failed to connect WebSocket:', error)
  }
}

// Open file dialog
const openFileDialog = () => {
  fileInput.value?.click()
}

// Handle file selection
const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    if (validateZipFile(file)) {
      selectedFile.value = file
    }
  }
  // Reset input
  event.target.value = ''
}

// Handle drag and drop
const handleDrop = (event) => {
  event.preventDefault()
  isDragOver.value = false

  const file = event.dataTransfer.files[0]
  if (file && validateZipFile(file)) {
    selectedFile.value = file
  }
}

// Validate ZIP file
const validateZipFile = (file) => {
  if (!file.name.toLowerCase().endsWith('.zip')) {
    toast.add({
      severity: 'warn',
      summary: 'Invalid File',
      detail: 'Please select a ZIP archive file',
      life: 3000
    })
    return false
  }

  const maxSize = 500 * 1024 * 1024 // 500MB
  if (file.size > maxSize) {
    toast.add({
      severity: 'warn',
      summary: 'File Too Large',
      detail: 'ZIP archive must be smaller than 500MB',
      life: 3000
    })
    return false
  }

  if (file.size === 0) {
    toast.add({
      severity: 'warn',
      summary: 'Empty File',
      detail: 'Selected ZIP file is empty',
      life: 3000
    })
    return false
  }

  return true
}

// Remove selected file
const removeFile = () => {
  selectedFile.value = null
}

// Start import process
const startImport = async () => {
  if (!selectedFile.value) return

  importing.value = true
  importComplete.value = false

  try {
    const result = await ragApi.bulkImport(selectedFile.value, {
      onUploadProgress: (progressEvent) => {
        // Upload progress is separate from processing progress
        console.log('Upload progress:', Math.round((progressEvent.loaded * 100) / progressEvent.total))
      }
    })

    // Store final results
    Object.assign(finalResults, {
      processed_files: result.processed_files || 0,
      failed_files: result.failed_files || 0,
      processing_time_seconds: result.processing_time_seconds || 0,
      errors: result.errors || []
    })

    // Update status for display
    Object.assign(importStatus, {
      processed_files: result.processed_files || 0,
      failed_files: result.failed_files || 0,
      processing_time_seconds: result.processing_time_seconds || 0,
      errors: result.errors || []
    })

    importComplete.value = true

    toast.add({
      severity: result.failed_files > 0 ? 'warn' : 'success',
      summary: 'Import Complete',
      detail: `Processed ${result.processed_files} files, ${result.failed_files} failed`,
      life: 5000
    })

    emit('import-complete', result)

  } catch (error) {
    console.error('Import error:', error)

    importComplete.value = true
    finalResults.errors = [error.message || 'Import failed with unknown error']

    toast.add({
      severity: 'error',
      summary: 'Import Failed',
      detail: error.message || 'Failed to import documents',
      life: 5000
    })
  } finally {
    importing.value = false
  }
}

// Close dialog
const closeDialog = () => {
  emit('update:visible', false)
}

// Utility functions
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (seconds) => {
  if (!seconds || seconds < 1) return '< 1s'
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}
</script>

<style scoped>
.bulk-import-dialog {
  max-width: none !important;
}

.import-content {
  min-height: 300px;
}

.zip-upload-zone {
  border: 3px dashed #dee2e6;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #f8f9fa;
  margin-bottom: 2rem;
}

.zip-upload-zone.drag-over {
  border-color: #007bff;
  background: #e3f2fd;
}

.zip-upload-zone.has-file {
  cursor: default;
  background: white;
  border-color: #28a745;
}

.upload-empty .upload-icon {
  font-size: 4rem;
  color: #6c757d;
  margin-bottom: 1rem;
}

.upload-empty h3 {
  color: #495057;
  margin-bottom: 0.5rem;
}

.upload-empty p {
  color: #6c757d;
  margin-bottom: 1.5rem;
}

.selected-file {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #e8f5e8;
  padding: 1.5rem;
  border-radius: 8px;
  border: 2px solid #28a745;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-icon {
  font-size: 2rem;
  color: #28a745;
}

.file-name {
  font-weight: 600;
  color: #155724;
  margin-bottom: 0.25rem;
}

.file-size {
  color: #6c757d;
  font-size: 0.9rem;
}

.import-progress {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.progress-header h4 {
  color: #495057;
  margin: 0;
}

.progress-stats {
  font-weight: 600;
  color: #007bff;
  font-size: 1.1rem;
}

.import-progress-bar {
  margin-bottom: 1rem;
}

.current-file {
  font-size: 0.9rem;
  color: #6c757d;
  margin-bottom: 1rem;
  font-style: italic;
}

.import-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  border-left: 4px solid #dee2e6;
}

.detail-item .label {
  font-weight: 600;
  color: #495057;
}

.detail-item .value {
  font-weight: 600;
}

.detail-item .value.success {
  color: #28a745;
}

.detail-item .value.error {
  color: #dc3545;
}

.import-errors {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
}

.import-errors h5 {
  color: #721c24;
  margin: 0 0 1rem 0;
}

.error-list {
  max-height: 150px;
  overflow-y: auto;
}

.error-item {
  background: white;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
  color: #721c24;
  border-left: 3px solid #dc3545;
}

.more-errors {
  font-style: italic;
  color: #6c757d;
  text-align: center;
  padding: 0.5rem;
}

.import-results {
  text-align: center;
  padding: 2rem;
}

.results-header {
  margin-bottom: 2rem;
}

.success-icon {
  font-size: 4rem;
  color: #28a745;
  margin-bottom: 1rem;
}

.results-header h3 {
  color: #155724;
  margin: 0;
}

.results-summary {
  margin-bottom: 2rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  max-width: 500px;
  margin: 0 auto;
}

.summary-item {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  border-left: 4px solid;
}

.summary-item.success {
  border-left-color: #28a745;
}

.summary-item.error {
  border-left-color: #dc3545;
}

.summary-item.info {
  border-left-color: #17a2b8;
}

.summary-value {
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.summary-label {
  color: #6c757d;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.85rem;
  letter-spacing: 1px;
}

.final-errors {
  max-width: 600px;
  margin: 0 auto;
}

.error-details {
  max-height: 200px;
  overflow-y: auto;
}

.error-detail {
  background: #f8f9fa;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  border-radius: 6px;
  border-left: 3px solid #dc3545;
  font-size: 0.9rem;
  color: #495057;
}

.import-instructions {
  background: #e3f2fd;
  border: 1px solid #bbdefb;
  border-radius: 12px;
  padding: 2rem;
  margin-top: 2rem;
}

.import-instructions h4 {
  color: #1976d2;
  margin-bottom: 1rem;
}

.instructions-list {
  color: #0d47a1;
  margin-bottom: 1.5rem;
  padding-left: 1.5rem;
}

.instructions-list li {
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

.supported-formats strong {
  color: #1976d2;
  display: block;
  margin-bottom: 0.75rem;
}

.format-chips {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.format-chip {
  background: #1976d2 !important;
  color: white !important;
  font-size: 0.75rem;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

@media (max-width: 768px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .import-details {
    grid-template-columns: 1fr;
  }
}
</style>