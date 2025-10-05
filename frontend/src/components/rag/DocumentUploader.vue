<template>
  <div class="document-uploader">
    <!-- Header sezione -->
    <div class="uploader-header">
      <h3>Carica Documenti</h3>
      <p class="subtitle">Supporta PDF, DOCX, TXT, MD, HTML - Max 50MB per file</p>
    </div>

    <!-- FileUpload component di PrimeVue -->
    <FileUpload
      ref="fileUploadRef"
      name="files"
      :multiple="true"
      :accept="acceptedFormats"
      :maxFileSize="maxFileSize"
      :customUpload="true"
      @upload="customUploader"
      @select="onFileSelect"
      @remove="onFileRemove"
      @clear="onClear"
      :showUploadButton="false"
      :showCancelButton="false"
      class="file-uploader"
    >
      <template #header>
        <div class="upload-header-actions">
          <Button
            @click="uploadFiles"
            icon="pi pi-upload"
            label="Carica Tutti"
            :disabled="!selectedFiles.length || isUploading"
            severity="success"
          />
          <Button
            @click="clearFiles"
            icon="pi pi-times"
            label="Rimuovi Tutti"
            :disabled="!selectedFiles.length || isUploading"
            severity="secondary"
          />
        </div>
      </template>

      <template #empty>
        <div class="upload-empty-state">
          <Icon icon="lucide:upload-cloud" class="upload-icon" />
          <p>Trascina qui i documenti o clicca per selezionare</p>
        </div>
      </template>

      <template #content="{ files, uploadedFiles, removeFileCallback }">
        <div v-if="files.length > 0" class="files-list">
          <div v-for="(file, index) in files" :key="file.name + file.type + file.size" class="file-item">
            <div class="file-info">
              <Icon :icon="getFileIcon(file.name)" class="file-icon" />
              <div class="file-details">
                <span class="file-name">{{ file.name }}</span>
                <span class="file-size">{{ formatFileSize(file.size) }}</span>
              </div>
            </div>

            <div class="file-metadata">
              <InputText
                v-model="fileMetadata[file.name].category"
                placeholder="Categoria (opzionale)"
                class="metadata-input"
                :disabled="isUploading"
              />
              <InputText
                v-model="fileMetadata[file.name].tags"
                placeholder="Tag (separati da virgola)"
                class="metadata-input"
                :disabled="isUploading"
              />
            </div>

            <div class="file-actions">
              <ProgressBar
                v-if="uploadProgress[file.name]"
                :value="uploadProgress[file.name]"
                :showValue="true"
                class="upload-progress"
              />
              <Button
                v-else
                @click="removeFileCallback(index)"
                icon="pi pi-trash"
                severity="danger"
                text
                rounded
                :disabled="isUploading"
              />
            </div>
          </div>
        </div>
      </template>
    </FileUpload>

    <!-- Upload Summary -->
    <div v-if="uploadSummary.total > 0" class="upload-summary">
      <Card>
        <template #content>
          <div class="summary-content">
            <div class="summary-item success" v-if="uploadSummary.success > 0">
              <Icon icon="lucide:check-circle" />
              <span>{{ uploadSummary.success }} caricati con successo</span>
            </div>
            <div class="summary-item error" v-if="uploadSummary.failed > 0">
              <Icon icon="lucide:x-circle" />
              <span>{{ uploadSummary.failed }} falliti</span>
            </div>
            <Button
              v-if="uploadSummary.success > 0"
              @click="resetUploader"
              label="Carica altri documenti"
              icon="pi pi-plus"
              severity="info"
              class="reset-button"
            />
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { Icon } from '@iconify/vue'
import FileUpload from 'primevue/fileupload'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import ProgressBar from 'primevue/progressbar'
import Card from 'primevue/card'
import { useToast } from 'primevue/usetoast'
import ragApi from '../../api/rag'

// Emits
const emit = defineEmits<{
  'upload-success': [files: any[]]
  'upload-error': [error: any]
}>()

// Composables
const toast = useToast()

// Refs
const fileUploadRef = ref<any>(null)

// State
const selectedFiles = ref<File[]>([])
const fileMetadata = reactive<Record<string, any>>({})
const uploadProgress = reactive<Record<string, number>>({})
const isUploading = ref(false)
const uploadSummary = reactive({
  total: 0,
  success: 0,
  failed: 0
})

// Constants
const acceptedFormats = '.pdf,.docx,.doc,.txt,.md,.html'
const maxFileSize = 50 * 1024 * 1024 // 50MB

// Computed
const canUpload = computed(() => selectedFiles.value.length > 0 && !isUploading.value)

// Methods
const onFileSelect = (event: any) => {
  const files = event.files as File[]

  files.forEach(file => {
    // Valida il file
    const validation = ragApi.validateFile(file)
    if (!validation.valid) {
      toast.add({
        severity: 'error',
        summary: 'File non valido',
        detail: `${file.name}: ${validation.errors.join(', ')}`,
        life: 5000
      })
      return
    }

    // Aggiungi metadata di default per ogni file
    if (!fileMetadata[file.name]) {
      fileMetadata[file.name] = {
        category: '',
        tags: ''
      }
    }

    selectedFiles.value.push(file)
  })
}

const onFileRemove = (event: any) => {
  const file = event.file
  const index = selectedFiles.value.findIndex(f => f.name === file.name)
  if (index > -1) {
    selectedFiles.value.splice(index, 1)
    delete fileMetadata[file.name]
    delete uploadProgress[file.name]
  }
}

const onClear = () => {
  selectedFiles.value = []
  Object.keys(fileMetadata).forEach(key => delete fileMetadata[key])
  Object.keys(uploadProgress).forEach(key => delete uploadProgress[key])
}

const clearFiles = () => {
  fileUploadRef.value?.clear()
  onClear()
}

const uploadFiles = async () => {
  if (!canUpload.value) return

  isUploading.value = true
  uploadSummary.total = selectedFiles.value.length
  uploadSummary.success = 0
  uploadSummary.failed = 0

  const formData = new FormData()

  // Aggiungi tutti i file al FormData
  selectedFiles.value.forEach(file => {
    formData.append('files', file)

    // Aggiungi metadata se presente
    const meta = fileMetadata[file.name]
    if (meta.category || meta.tags) {
      const metadata = {
        filename: file.name,
        category: meta.category,
        tags: meta.tags.split(',').map((t: string) => t.trim()).filter(Boolean)
      }
      formData.append('metadata', JSON.stringify(metadata))
    }
  })

  try {
    // Upload con progress tracking
    const response = await fetch('/api/rag/upload', {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`)
    }

    const result = await response.json()

    // Aggiorna summary
    uploadSummary.success = result.successful_uploads || selectedFiles.value.length
    uploadSummary.failed = result.failed_uploads || 0

    toast.add({
      severity: 'success',
      summary: 'Upload Completato',
      detail: `${uploadSummary.success} documenti caricati con successo`,
      life: 3000
    })

    emit('upload-success', result)

    // Reset dopo successo
    setTimeout(() => {
      clearFiles()
    }, 1500)

  } catch (error) {
    console.error('Upload error:', error)
    uploadSummary.failed = selectedFiles.value.length

    toast.add({
      severity: 'error',
      summary: 'Errore Upload',
      detail: error instanceof Error ? error.message : 'Errore durante il caricamento',
      life: 5000
    })

    emit('upload-error', error)
  } finally {
    isUploading.value = false
  }
}

const customUploader = async (event: any) => {
  // Non usiamo l'upload automatico, gestiamo manualmente
  await uploadFiles()
}

const resetUploader = () => {
  uploadSummary.total = 0
  uploadSummary.success = 0
  uploadSummary.failed = 0
  clearFiles()
}

const getFileIcon = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  const icons: Record<string, string> = {
    pdf: 'lucide:file-text',
    docx: 'lucide:file-type',
    doc: 'lucide:file-type',
    txt: 'lucide:file',
    md: 'lucide:file-code',
    html: 'lucide:code'
  }
  return icons[ext || ''] || 'lucide:file'
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>

<style scoped>
.document-uploader {
  width: 100%;
}

/* Header */
.uploader-header {
  margin-bottom: 1.5rem;
}

.uploader-header h3 {
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

/* FileUpload customization */
.file-uploader :deep(.p-fileupload) {
  background: #1a1a1a;
  border: 2px dashed rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.file-uploader :deep(.p-fileupload-buttonbar) {
  background: transparent;
  border: none;
  padding: 1rem;
}

.file-uploader :deep(.p-fileupload-content) {
  background: transparent;
  border: none;
  padding: 0 1rem 1rem;
}

/* Upload header actions */
.upload-header-actions {
  display: flex;
  gap: 0.75rem;
}

/* Empty state */
.upload-empty-state {
  padding: 3rem 2rem;
  text-align: center;
  color: #a0a0a0;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.upload-empty-state p {
  margin: 0;
  font-size: 1rem;
}

/* Files list */
.files-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.file-item {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.3s ease;
}

.file-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(16, 185, 129, 0.3);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 200px;
}

.file-icon {
  font-size: 1.5rem;
  color: #10b981;
}

.file-details {
  display: flex;
  flex-direction: column;
}

.file-name {
  font-weight: 500;
  color: #ffffff;
  font-size: 0.95rem;
  word-break: break-word;
}

.file-size {
  font-size: 0.85rem;
  color: #a0a0a0;
}

/* File metadata */
.file-metadata {
  flex: 1;
  display: flex;
  gap: 0.75rem;
}

.metadata-input {
  flex: 1;
}

.metadata-input :deep(.p-inputtext) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #ffffff;
  font-size: 0.9rem;
  padding: 0.5rem 0.75rem;
}

.metadata-input :deep(.p-inputtext:focus) {
  border-color: #10b981;
  box-shadow: 0 0 0 0.2rem rgba(16, 185, 129, 0.25);
}

/* File actions */
.file-actions {
  min-width: 100px;
  display: flex;
  justify-content: flex-end;
}

.upload-progress {
  width: 100px;
}

.upload-progress :deep(.p-progressbar) {
  height: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
}

.upload-progress :deep(.p-progressbar-value) {
  background: linear-gradient(90deg, #10b981 0%, #0d9668 100%);
}

/* Upload summary */
.upload-summary {
  margin-top: 1.5rem;
}

.summary-content {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
}

.summary-item.success {
  color: #10b981;
}

.summary-item.error {
  color: #ef4444;
}

.reset-button {
  margin-left: auto;
}

/* Responsive */
@media (max-width: 768px) {
  .file-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .file-info {
    width: 100%;
  }

  .file-metadata {
    width: 100%;
    flex-direction: column;
  }

  .file-actions {
    width: 100%;
    justify-content: center;
    margin-top: 0.5rem;
  }

  .upload-progress {
    width: 100%;
  }
}

/* Dark theme overrides */
.file-uploader :deep(.p-button) {
  transition: all 0.3s ease;
}

.file-uploader :deep(.p-button:hover) {
  transform: translateY(-2px);
}

.file-uploader :deep(.p-fileupload-content:has(.files-list)) {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}
</style>