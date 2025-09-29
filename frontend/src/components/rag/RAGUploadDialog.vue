<template>
  <Dialog
    :visible="visible"
    @update:visible="$emit('update:visible', $event)"
    header="Upload Documents"
    :style="{ width: '70vw', maxWidth: '800px' }"
    :modal="true"
    class="upload-dialog"
  >
    <div class="upload-content">
      <!-- Drag & Drop Area -->
      <div
        class="upload-zone"
        :class="{ 'drag-over': isDragOver, 'has-files': selectedFiles.length > 0 }"
        @drop="handleDrop"
        @dragover.prevent="isDragOver = true"
        @dragleave.prevent="isDragOver = false"
        @click="openFileDialog"
      >
        <div v-if="selectedFiles.length === 0" class="upload-empty">
          <div class="upload-icon">
            <i class="pi pi-cloud-upload"></i>
          </div>
          <h3>Drag & Drop Documents</h3>
          <p>or click to browse files</p>
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

        <div v-else class="upload-files">
          <div class="files-header">
            <h4>Selected Files ({{ selectedFiles.length }})</h4>
            <Button
              label="Add More"
              icon="pi pi-plus"
              class="p-button-text"
              @click="openFileDialog"
            />
          </div>

          <div class="files-list">
            <div
              v-for="(file, index) in selectedFiles"
              :key="`file-${index}`"
              class="file-item"
            >
              <div class="file-info">
                <i :class="getFileIcon(file.name)" class="file-icon"></i>
                <div class="file-details">
                  <div class="file-name">{{ file.name }}</div>
                  <div class="file-meta">
                    {{ formatFileSize(file.size) }} • {{ getFileType(file.name) }}
                  </div>
                </div>
              </div>

              <div class="file-actions">
                <Button
                  icon="pi pi-times"
                  class="p-button-rounded p-button-text p-button-sm"
                  @click="removeFile(index)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Upload Options -->
      <div v-if="selectedFiles.length > 0" class="upload-options">
        <Accordion :activeIndex="0">
          <AccordionTab header="Upload Settings">
            <div class="settings-grid">
              <div class="setting-group">
                <label class="setting-label">Category</label>
                <Dropdown
                  v-model="uploadSettings.category"
                  :options="categoryOptions"
                  option-label="label"
                  option-value="value"
                  placeholder="Select category"
                  class="setting-input"
                />
              </div>

              <div class="setting-group">
                <label class="setting-label">Tags (comma-separated)</label>
                <InputText
                  v-model="uploadSettings.tags"
                  placeholder="e.g. policy, training, important"
                  class="setting-input"
                />
              </div>

              <div class="setting-group">
                <label class="setting-label">Options</label>
                <div class="checkbox-group">
                  <div class="checkbox-item">
                    <Checkbox
                      v-model="uploadSettings.auto_category"
                      :binary="true"
                      input-id="auto-category"
                    />
                    <label for="auto-category">Auto-detect category</label>
                  </div>
                  <div class="checkbox-item">
                    <Checkbox
                      v-model="uploadSettings.extract_metadata"
                      :binary="true"
                      input-id="extract-metadata"
                    />
                    <label for="extract-metadata">Extract metadata</label>
                  </div>
                </div>
              </div>
            </div>
          </AccordionTab>
        </Accordion>
      </div>

      <!-- Upload Progress -->
      <div v-if="uploading" class="upload-progress">
        <div class="progress-header">
          <h4>Uploading Documents...</h4>
          <span class="progress-stats">
            {{ uploadProgress.completed }}/{{ uploadProgress.total }}
          </span>
        </div>

        <ProgressBar
          :value="uploadProgress.percentage"
          class="upload-progress-bar"
        />

        <div v-if="uploadProgress.currentFile" class="current-file">
          Processing: {{ uploadProgress.currentFile }}
        </div>

        <div class="upload-results">
          <div v-if="uploadProgress.successful.length > 0" class="success-files">
            <h5><i class="pi pi-check-circle mr-1"></i>Successfully Uploaded</h5>
            <ul>
              <li v-for="file in uploadProgress.successful" :key="file">
                {{ file }}
              </li>
            </ul>
          </div>

          <div v-if="uploadProgress.failed.length > 0" class="failed-files">
            <h5><i class="pi pi-times-circle mr-1"></i>Failed Uploads</h5>
            <ul>
              <li v-for="error in uploadProgress.failed" :key="error.file">
                {{ error.file }}: {{ error.error }}
              </li>
            </ul>
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
          :disabled="uploading"
        />
        <Button
          v-if="!uploading"
          label="Upload Documents"
          icon="pi pi-upload"
          class="p-button-primary"
          @click="uploadDocuments"
          :disabled="selectedFiles.length === 0"
        />
        <Button
          v-else
          label="Uploading..."
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
      multiple
      accept=".pdf,.docx,.txt,.md,.html"
      @change="handleFileSelect"
      style="display: none"
    />
  </Dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useToast } from 'vue-toastification'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Chip from 'primevue/chip'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Checkbox from 'primevue/checkbox'
import ProgressBar from 'primevue/progressbar'
import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'

import { ragApi } from '@/api/rag'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'upload-complete'])

const toast = useToast()

// Reactive state
const selectedFiles = ref([])
const isDragOver = ref(false)
const uploading = ref(false)
const fileInput = ref(null)

// Upload settings
const uploadSettings = reactive({
  category: null,
  tags: '',
  auto_category: true,
  extract_metadata: true
})

// Upload progress
const uploadProgress = reactive({
  total: 0,
  completed: 0,
  percentage: 0,
  currentFile: '',
  successful: [],
  failed: []
})

// Category options
const categoryOptions = [
  { label: 'Auto-detect', value: null },
  { label: 'Business Process', value: 'business_process' },
  { label: 'Documentation', value: 'documentation' },
  { label: 'Training Material', value: 'training' },
  { label: 'Policy', value: 'policy' },
  { label: 'General', value: 'general' }
]

// Watch dialog visibility
watch(() => props.visible, (newVal) => {
  if (!newVal) {
    resetDialog()
  }
})

// Reset dialog state
const resetDialog = () => {
  selectedFiles.value = []
  isDragOver.value = false
  uploading.value = false

  // Reset upload settings
  uploadSettings.category = null
  uploadSettings.tags = ''
  uploadSettings.auto_category = true
  uploadSettings.extract_metadata = true

  // Reset progress
  Object.assign(uploadProgress, {
    total: 0,
    completed: 0,
    percentage: 0,
    currentFile: '',
    successful: [],
    failed: []
  })
}

// Open file dialog
const openFileDialog = () => {
  fileInput.value?.click()
}

// Handle file selection from dialog
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  addFiles(files)

  // Reset input
  event.target.value = ''
}

// Handle drag and drop
const handleDrop = (event) => {
  event.preventDefault()
  isDragOver.value = false

  const files = Array.from(event.dataTransfer.files)
  addFiles(files)
}

// Add files to selection
const addFiles = (files) => {
  const validFiles = files.filter(file => {
    const validExtensions = ['.pdf', '.docx', '.txt', '.md', '.html']
    const hasValidExtension = validExtensions.some(ext =>
      file.name.toLowerCase().endsWith(ext)
    )

    if (!hasValidExtension) {
      toast.warning(`${file.name} - Unsupported file format`)
      return false
    }

    if (file.size > 50 * 1024 * 1024) { // 50MB limit
      toast.warning(`${file.name} - File size exceeds 50MB limit`)
      return false
    }

    return true
  })

  // Check for duplicates
  const uniqueFiles = validFiles.filter(file => {
    return !selectedFiles.value.some(existingFile =>
      existingFile.name === file.name && existingFile.size === file.size
    )
  })

  selectedFiles.value.push(...uniqueFiles)

  if (uniqueFiles.length > 0) {
    toast.success(`Added ${uniqueFiles.length} file(s) for upload`)
  }
}

// Remove file from selection
const removeFile = (index) => {
  selectedFiles.value.splice(index, 1)
}

// Upload documents
const uploadDocuments = async () => {
  if (selectedFiles.value.length === 0) return

  uploading.value = true

  // Reset progress
  uploadProgress.total = selectedFiles.value.length
  uploadProgress.completed = 0
  uploadProgress.percentage = 0
  uploadProgress.successful = []
  uploadProgress.failed = []

  try {
    // Prepare form data
    const formData = new FormData()

    // Add files
    selectedFiles.value.forEach(file => {
      formData.append('files', file)
    })

    // Add settings
    if (uploadSettings.category) {
      formData.append('category', uploadSettings.category)
    }

    if (uploadSettings.tags.trim()) {
      const tagsArray = uploadSettings.tags
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0)
      formData.append('tags', JSON.stringify(tagsArray))
    }

    formData.append('auto_category', uploadSettings.auto_category.toString())
    formData.append('extract_metadata', uploadSettings.extract_metadata.toString())

    // Upload with progress tracking
    const result = await ragApi.uploadDocuments(formData, {
      onUploadProgress: (progressEvent) => {
        uploadProgress.percentage = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        )
      }
    })

    // Handle results
    if (result.success) {
      uploadProgress.completed = uploadProgress.total
      uploadProgress.percentage = 100

      toast.success(result.message || 'Documents uploaded successfully')

      emit('upload-complete', result)

      // Close dialog after short delay
      setTimeout(() => {
        closeDialog()
      }, 2000)
    } else {
      throw new Error(result.message || 'Upload failed')
    }

  } catch (error) {
    console.error('Upload error:', error)

    uploadProgress.failed.push({
      file: 'Upload process',
      error: error.message || 'Unknown error occurred'
    })

    toast.error(error.message || 'Failed to upload documents')
  } finally {
    uploading.value = false
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

const getFileType = (filename) => {
  const extension = filename.split('.').pop()?.toUpperCase()
  return extension || 'Unknown'
}

const getFileIcon = (filename) => {
  const extension = filename.split('.').pop()?.toLowerCase()
  const iconMap = {
    'pdf': 'pi pi-file-pdf',
    'docx': 'pi pi-file-word',
    'txt': 'pi pi-file',
    'md': 'pi pi-file-edit',
    'html': 'pi pi-code'
  }
  return iconMap[extension] || 'pi pi-file'
}
</script>

