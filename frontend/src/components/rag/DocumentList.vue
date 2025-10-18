<template>
  <div class="document-list">
    <!-- Header -->
    <div class="list-header">
      <h3>Gestione Documenti</h3>
      <div class="header-actions">
        <span class="p-input-icon-left">
          <Icon icon="lucide:search" />
          <InputText
            v-model="filters.global.value"
            placeholder="Cerca documenti..."
            class="search-input"
          />
        </span>
        <Button
          @click="refresh"
          icon="pi pi-refresh"
          label="Aggiorna"
          :loading="loading"
          severity="info"
        />
      </div>
    </div>

    <!-- DataTable -->
    <DataTable
      id="rag-documents-table-vscode"
      ref="dataTableRef"
      v-model:filters="filters"
      v-model:selection="selectedDocuments"
      :value="documents"
      :paginator="true"
      :rows="10"
      :rowsPerPageOptions="[5, 10, 20, 50]"
      :loading="loading"
      :globalFilterFields="['metadata.filename', 'metadata.category', 'metadata.tags']"
      dataKey="id"
      filterDisplay="row"
      responsiveLayout="scroll"
      class="documents-table"
      :pt="{
        wrapper: { style: 'background: transparent; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px;' },
        header: { style: 'background: #1e1e1e; border-bottom: 1px solid rgba(255,255,255,0.1);' },
        tbody: { style: 'background: #1a1a1a;' },
        footer: { style: 'background: #1e1e1e; border-top: 1px solid rgba(255,255,255,0.1);' }
      }"
    >
      <!-- Selection Column -->
      <Column selectionMode="multiple" :exportable="false" style="width: 3rem" />

      <!-- Filename Column -->
      <Column field="metadata.filename" header="Nome File" :sortable="true" style="min-width: 200px">
        <template #body="{ data }">
          <div class="filename-cell">
            <Icon :icon="getFileIcon(data.metadata?.filename)" class="file-icon" />
            <span class="filename">{{ data.metadata?.filename || 'Senza nome' }}</span>
          </div>
        </template>
        <template #filter="{ filterModel, filterCallback }">
          <InputText
            v-model="filterModel.value"
            type="text"
            @input="filterCallback()"
            placeholder="Filtra per nome"
            class="p-column-filter"
          />
        </template>
      </Column>

      <!-- Category Column -->
      <Column field="metadata.category" header="Categoria" :sortable="true" style="min-width: 120px">
        <template #body="{ data }">
          <Tag
            v-if="data.metadata?.category"
            :value="data.metadata.category"
            severity="info"
          />
          <span v-else class="no-category">-</span>
        </template>
        <template #filter="{ filterModel, filterCallback }">
          <Dropdown
            v-model="filterModel.value"
            :options="categories"
            placeholder="Tutte"
            @change="filterCallback()"
            showClear
            class="p-column-filter"
          />
        </template>
      </Column>

      <!-- Size Column -->
      <Column field="metadata.size" header="Dimensione" :sortable="true" style="min-width: 100px">
        <template #body="{ data }">
          <span class="size-cell">{{ formatFileSize(data.metadata?.size || 0) }}</span>
        </template>
      </Column>

      <!-- Created Date Column -->
      <Column field="metadata.created_at" header="Data Creazione" :sortable="true" style="min-width: 150px">
        <template #body="{ data }">
          <span class="date-cell">{{ formatDate(data.metadata?.created_at) }}</span>
        </template>
      </Column>

      <!-- Chunks Column -->
      <Column field="chunks_count" header="Frammenti" :sortable="true" style="min-width: 100px">
        <template #body="{ data }">
          <div class="chunks-cell">
            <Icon icon="lucide:layers" class="chunks-icon" />
            <span>{{ data.chunks_count || 0 }}</span>
          </div>
        </template>
      </Column>

      <!-- Actions Column -->
      <Column :exportable="false" header="Azioni" style="min-width: 150px">
        <template #body="{ data }">
          <div class="action-buttons">
            <Button
              @click="viewDocument(data)"
              severity="info"
              text
              rounded
              v-tooltip="'Visualizza Contenuto'"
            >
              <Icon icon="lucide:eye" class="action-icon" />
            </Button>
            <Button
              @click="editDocument(data)"
              severity="warning"
              text
              rounded
              v-tooltip="'Modifica Metadata'"
            >
              <Icon icon="lucide:pencil" class="action-icon" />
            </Button>
            <Button
              @click="confirmDelete(data)"
              severity="danger"
              text
              rounded
              v-tooltip="'Elimina Documento'"
            >
              <Icon icon="lucide:trash-2" class="action-icon" />
            </Button>
          </div>
        </template>
      </Column>

      <!-- Empty Template -->
      <template #empty>
        <div class="empty-message">
          <Icon icon="lucide:file-x" class="empty-icon" />
          <p>Nessun documento trovato</p>
        </div>
      </template>

      <!-- Loading Template -->
      <template #loading>
        <div class="loading-message">
          <ProgressSpinner style="width: 50px; height: 50px" />
          <p>Caricamento documenti...</p>
        </div>
      </template>
    </DataTable>

    <!-- Bulk Actions -->
    <div v-if="selectedDocuments.length > 0" class="bulk-actions">
      <Card>
        <template #content>
          <div class="bulk-content">
            <span class="selection-count">
              <Icon icon="lucide:check-square" />
              {{ selectedDocuments.length }} documenti selezionati
            </span>
            <div class="bulk-buttons">
              <Button
                @click="exportSelected"
                icon="pi pi-download"
                label="Esporta"
                severity="info"
                outlined
              />
              <Button
                @click="deleteSelected"
                icon="pi pi-trash"
                label="Elimina Selezionati"
                severity="danger"
              />
            </div>
          </div>
        </template>
      </Card>
    </div>

    <!-- Edit Dialog -->
    <Dialog
      v-model:visible="editDialogVisible"
      modal
      header="Modifica Documento"
      :style="{ width: '500px' }"
      class="edit-dialog"
    >
      <div class="edit-form" v-if="editingDocument">
        <div class="form-field">
          <label>Nome File:</label>
          <InputText v-model="editingDocument.metadata.filename" disabled class="w-full" />
        </div>
        <div class="form-field">
          <label>Categoria:</label>
          <InputText v-model="editingDocument.metadata.category" placeholder="Inserisci categoria" class="w-full" />
        </div>
        <div class="form-field">
          <label>Tag (separati da virgola):</label>
          <Textarea
            v-model="editingDocument.metadata.tags"
            rows="3"
            placeholder="tag1, tag2, tag3"
            class="w-full"
          />
        </div>
      </div>

      <template #footer>
        <Button label="Annulla" @click="editDialogVisible = false" text />
        <Button label="Salva" @click="saveDocument" icon="pi pi-check" severity="success" />
      </template>
    </Dialog>

    <!-- View Document Dialog -->
    <Dialog
      v-model:visible="viewDialogVisible"
      modal
      header="Dettagli Documento"
      :style="{ width: '700px' }"
      class="view-dialog"
    >
      <div v-if="viewingDocument" class="view-content">
        <!-- Metadata -->
        <div class="metadata-section">
          <h4>Informazioni</h4>
          <div class="metadata-grid">
            <div class="metadata-item">
              <label>Nome File:</label>
              <span>{{ viewingDocument.metadata?.filename || 'N/A' }}</span>
            </div>
            <div class="metadata-item">
              <label>Categoria:</label>
              <Tag v-if="viewingDocument.metadata?.category" :value="viewingDocument.metadata.category" severity="info" />
              <span v-else>-</span>
            </div>
            <div class="metadata-item">
              <label>Dimensione:</label>
              <span>{{ formatFileSize(viewingDocument.metadata?.size || 0) }}</span>
            </div>
            <div class="metadata-item">
              <label>Data Creazione:</label>
              <span>{{ formatDate(viewingDocument.metadata?.created_at) }}</span>
            </div>
            <div class="metadata-item">
              <label>Frammenti:</label>
              <span>{{ viewingDocument.chunks_count || 0 }}</span>
            </div>
            <div class="metadata-item">
              <label>Tags:</label>
              <div class="tags-list">
                <Tag v-for="tag in viewingDocument.metadata?.tags || []" :key="tag" :value="tag" severity="secondary" />
                <span v-if="!viewingDocument.metadata?.tags?.length">-</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Content Preview -->
        <div v-if="viewingDocument.content" class="content-section">
          <h4>Anteprima Contenuto</h4>
          <div class="content-preview">
            {{ viewingDocument.content.substring(0, 1000) }}
            <span v-if="viewingDocument.content.length > 1000">...</span>
          </div>
        </div>
      </div>

      <template #footer>
        <Button label="Chiudi" @click="viewDialogVisible = false" text />
      </template>
    </Dialog>

    <!-- Confirm Delete Dialog -->
    <ConfirmDialog group="delete">
      <template #message="slotProps">
        <div class="confirm-delete-content">
          <Icon icon="lucide:alert-triangle" class="delete-warning-icon" />
          <span>{{ slotProps.message.message }}</span>
        </div>
      </template>
    </ConfirmDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Icon } from '@iconify/vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'
import Card from 'primevue/card'
import Dialog from 'primevue/dialog'
import Textarea from 'primevue/textarea'
import ConfirmDialog from 'primevue/confirmdialog'
import ProgressSpinner from 'primevue/progressspinner'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import { FilterMatchMode } from '@primevue/core/api'
import ragApi from '../../api/rag'
import { useForceVSCodeDropdown } from '../../composables/useForceVSCodeDropdown'

// Force VS Code theme on dropdowns (CSS alone cannot override PrimeVue runtime styles)
useForceVSCodeDropdown()

// Emits
const emit = defineEmits<{
  'document-updated': [document: any]
  'document-deleted': [id: string]
}>()

// Composables
const toast = useToast()
const confirm = useConfirm()

// Refs
const dataTableRef = ref()

// State
const documents = ref<any[]>([])
const selectedDocuments = ref<any[]>([])
const loading = ref(false)
const editDialogVisible = ref(false)
const editingDocument = ref<any>(null)
const viewDialogVisible = ref(false)
const viewingDocument = ref<any>(null)
// Predefined categories (same as DocumentUploader)
const predefinedCategories = [
  'generale',
  'business',
  'tecnico',
  'hr',
  'legale',
  'finanza',
  'marketing',
  'formazione'
]
const categories = ref<string[]>(predefinedCategories)

// Filters
const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS },
  'metadata.filename': { value: null, matchMode: FilterMatchMode.CONTAINS },
  'metadata.category': { value: null, matchMode: FilterMatchMode.EQUALS }
})

// Methods
const loadDocuments = async () => {
  loading.value = true
  try {
    const response = await ragApi.listDocuments()
    documents.value = response.documents || []
    // Categories are predefined, no need to extract

  } catch (error) {
    console.error('Error loading documents:', error)
    toast.add({
      severity: 'error',
      summary: 'Errore',
      detail: 'Impossibile caricare i documenti',
      life: 5000
    })
  } finally {
    loading.value = false
  }
}

const refresh = async () => {
  await loadDocuments()
  toast.add({
    severity: 'success',
    summary: 'Aggiornato',
    detail: 'Lista documenti aggiornata',
    life: 2000
  })
}

const viewDocument = async (document: any) => {
  try {
    // Fetch full document content from API
    const response = await fetch(`http://localhost:8000/api/rag/documents/${document.id}`)
    if (!response.ok) throw new Error('Failed to fetch document')

    const fullDoc = await response.json()
    viewingDocument.value = fullDoc
    viewDialogVisible.value = true
  } catch (error) {
    console.error('Error fetching document:', error)
    toast.add({
      severity: 'error',
      summary: 'Errore',
      detail: 'Impossibile caricare i dettagli del documento',
      life: 5000
    })
  }
}

const editDocument = (document: any) => {
  editingDocument.value = JSON.parse(JSON.stringify(document))

  // Convert tags array to comma-separated string
  if (Array.isArray(editingDocument.value.metadata?.tags)) {
    editingDocument.value.metadata.tags = editingDocument.value.metadata.tags.join(', ')
  }

  editDialogVisible.value = true
}

const saveDocument = async () => {
  if (!editingDocument.value) return

  try {
    // Convert tags string back to array
    const tags = editingDocument.value.metadata.tags
      ?.split(',')
      .map((t: string) => t.trim())
      .filter(Boolean) || []

    const updateData = {
      metadata: {
        category: editingDocument.value.metadata.category,
        tags
      }
    }

    await ragApi.updateDocument(editingDocument.value.id, updateData)

    toast.add({
      severity: 'success',
      summary: 'Salvato',
      detail: 'Documento aggiornato con successo',
      life: 3000
    })

    editDialogVisible.value = false
    await loadDocuments()
    emit('document-updated', editingDocument.value)

  } catch (error) {
    console.error('Error updating document:', error)
    toast.add({
      severity: 'error',
      summary: 'Errore',
      detail: 'Impossibile aggiornare il documento',
      life: 5000
    })
  }
}

const confirmDelete = (document: any) => {
  confirm.require({
    group: 'delete',
    message: `Sei sicuro di voler eliminare "${document.metadata?.filename}"? Questa azione non può essere annullata.`,
    header: 'Conferma Eliminazione',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    accept: async () => {
      await deleteDocument(document.id)
    }
  })
}

const deleteDocument = async (id: string) => {
  try {
    await ragApi.deleteDocument(id)

    toast.add({
      severity: 'success',
      summary: 'Eliminato',
      detail: 'Documento eliminato con successo',
      life: 3000
    })

    await loadDocuments()
    emit('document-deleted', id)

  } catch (error) {
    console.error('Error deleting document:', error)
    toast.add({
      severity: 'error',
      summary: 'Errore',
      detail: 'Impossibile eliminare il documento',
      life: 5000
    })
  }
}

const deleteSelected = () => {
  confirm.require({
    group: 'delete',
    message: `Sei sicuro di voler eliminare ${selectedDocuments.value.length} documenti? Questa azione non può essere annullata.`,
    header: 'Conferma Eliminazione Multipla',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    accept: async () => {
      for (const doc of selectedDocuments.value) {
        await deleteDocument(doc.id)
      }
      selectedDocuments.value = []
    }
  })
}

const exportSelected = () => {
  try {
    // Export selected documents as JSON
    const exportData = selectedDocuments.value.map(doc => ({
      id: doc.id,
      filename: doc.metadata?.filename,
      category: doc.metadata?.category,
      tags: doc.metadata?.tags,
      size: doc.metadata?.size,
      created_at: doc.metadata?.created_at,
      chunks_count: doc.chunks_count
    }))

    // Create blob and download
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `rag-documents-export-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    toast.add({
      severity: 'success',
      summary: 'Export Completato',
      detail: `${selectedDocuments.value.length} documenti esportati`,
      life: 3000
    })
  } catch (error) {
    console.error('Error exporting documents:', error)
    toast.add({
      severity: 'error',
      summary: 'Errore',
      detail: 'Impossibile esportare i documenti',
      life: 5000
    })
  }
}

const getFileIcon = (filename?: string) => {
  if (!filename) return 'lucide:file'
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

const formatDate = (dateString?: string) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Expose refresh method to parent
defineExpose({
  refresh
})

// Lifecycle
onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.document-list {
  width: 100%;
}

/* Header */
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.list-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-input {
  width: 250px;
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #ffffff !important;
}

/* DataTable */
.documents-table :deep(.p-datatable-header) {
  background: #1e1e1e;
  border: none;
}

.documents-table :deep(.p-datatable-thead > tr > th) {
  background: #1e1e1e;
  color: #a0a0a0;
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-weight: 600;
}

.documents-table :deep(.p-datatable-tbody > tr) {
  background: #1a1a1a;
  color: #e0e0e0;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.2s ease;
}

.documents-table :deep(.p-datatable-tbody > tr:hover) {
  background: rgba(255, 255, 255, 0.05);
}

.documents-table :deep(.p-datatable-tbody > tr.p-highlight) {
  background: rgba(16, 185, 129, 0.15);
}

.documents-table :deep(.p-paginator) {
  background: #1e1e1e;
  border: none;
  color: #a0a0a0;
}

.documents-table :deep(.p-column-filter) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

/* Cell Styles */
.filename-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.file-icon {
  color: #10b981;
  font-size: 1.25rem;
}

.filename {
  font-weight: 500;
  color: #ffffff;
}

.no-category {
  color: #6b7280;
}

.size-cell {
  font-family: monospace;
  color: #a0a0a0;
}

.date-cell {
  color: #a0a0a0;
  font-size: 0.9rem;
}

.chunks-cell {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  color: #10b981;
}

.chunks-icon {
  font-size: 1rem;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 0.25rem;
}

.action-icon {
  font-size: 1.1rem;
}

/* Empty & Loading States */
.empty-message,
.loading-message {
  text-align: center;
  padding: 3rem;
  color: #a0a0a0;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-message p,
.loading-message p {
  margin: 1rem 0 0 0;
}

/* Bulk Actions */
.bulk-actions {
  margin-top: 1.5rem;
  animation: slideIn 0.3s ease-out;
}

.bulk-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.selection-count {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #10b981;
  font-weight: 500;
}

.bulk-buttons {
  display: flex;
  gap: 0.75rem;
}

/* Edit Dialog */
.edit-dialog :deep(.p-dialog) {
  background: #1a1a1a;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.edit-dialog :deep(.p-dialog-header) {
  background: #1e1e1e;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.edit-dialog :deep(.p-dialog-content) {
  background: #1a1a1a;
}

.edit-dialog :deep(.p-dialog-footer) {
  background: #1e1e1e;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-field label {
  color: #a0a0a0;
  font-size: 0.9rem;
  font-weight: 500;
}

.form-field :deep(.p-inputtext),
.form-field :deep(.p-inputtextarea) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

/* Confirm Delete */
.confirm-delete-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.delete-warning-icon {
  font-size: 2rem;
  color: #ef4444;
}

/* Animations */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Utility */
.w-full {
  width: 100%;
}

/* Responsive */
@media (max-width: 768px) {
  .list-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    flex-direction: column;
  }

  .search-input {
    width: 100%;
  }

  .bulk-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .bulk-buttons {
    width: 100%;
  }

  .bulk-buttons button {
    flex: 1;
  }
}
</style>

<!-- GLOBAL VS CODE THEME OVERRIDE - NO SCOPED - ID SPECIFICITY -->
<style>
/* ⚡ PAGINATOR - Force VS Code gray (not blue!) */
#rag-documents-table-vscode .p-paginator {
  background: #1A1A1A !important;
  background-color: #1A1A1A !important;
  border-top: 1px solid #3C3C3C !important;
  color: #9E9E9E !important;
}

/* Paginator buttons - Gray background */
#rag-documents-table-vscode .p-paginator .p-paginator-page,
#rag-documents-table-vscode .p-paginator .p-paginator-first,
#rag-documents-table-vscode .p-paginator .p-paginator-prev,
#rag-documents-table-vscode .p-paginator .p-paginator-next,
#rag-documents-table-vscode .p-paginator .p-paginator-last {
  background: #2A2A2A !important;
  background-color: #2A2A2A !important;
  color: #9E9E9E !important;
  border: 1px solid #3C3C3C !important;
}

/* Paginator buttons hover - Lighter gray */
#rag-documents-table-vscode .p-paginator .p-paginator-page:not(.p-disabled):hover,
#rag-documents-table-vscode .p-paginator .p-paginator-first:not(.p-disabled):hover,
#rag-documents-table-vscode .p-paginator .p-paginator-prev:not(.p-disabled):hover,
#rag-documents-table-vscode .p-paginator .p-paginator-next:not(.p-disabled):hover,
#rag-documents-table-vscode .p-paginator .p-paginator-last:not(.p-disabled):hover {
  background: #3C3C3C !important;
  background-color: #3C3C3C !important;
  color: #E0E0E0 !important;
  border-color: #6B6B6B !important;
}

/* Active page - VS Code accent blue */
#rag-documents-table-vscode .p-paginator .p-paginator-page.p-highlight {
  background: #007ACC !important;
  background-color: #007ACC !important;
  color: #FFFFFF !important;
  border-color: #007ACC !important;
}

#rag-documents-table-vscode .p-paginator .p-paginator-page.p-highlight:hover {
  background: #005A9E !important;
  background-color: #005A9E !important;
}

/* Disabled buttons */
#rag-documents-table-vscode .p-paginator .p-paginator-page.p-disabled,
#rag-documents-table-vscode .p-paginator .p-paginator-first.p-disabled,
#rag-documents-table-vscode .p-paginator .p-paginator-prev.p-disabled,
#rag-documents-table-vscode .p-paginator .p-paginator-next.p-disabled,
#rag-documents-table-vscode .p-paginator .p-paginator-last.p-disabled {
  opacity: 0.4 !important;
  background: #1A1A1A !important;
}

/* Rows per page dropdown */
#rag-documents-table-vscode .p-paginator .p-dropdown {
  background: #2A2A2A !important;
  border: 1px solid #3C3C3C !important;
  color: #E0E0E0 !important;
}

#rag-documents-table-vscode .p-paginator .p-dropdown:hover {
  border-color: #007ACC !important;
}
</style>