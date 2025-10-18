<template>
  <div class="semantic-search">
    <!-- Search Header -->
    <div class="search-header">
      <h3>Ricerca Intelligente</h3>
      <p class="subtitle">Cerca documenti utilizzando query in linguaggio naturale</p>
    </div>

    <!-- Search Input -->
    <div class="search-input-container">
      <span class="p-input-icon-left search-box">
        <Icon icon="lucide:search" class="search-icon" />
        <InputText
          v-model="searchQuery"
          placeholder="Fai una domanda o cerca informazioni..."
          class="search-input"
          @keyup.enter="performSearch"
          :disabled="isSearching"
        />
      </span>
      <Button
        @click="performSearch"
        icon="pi pi-search"
        label="Cerca"
        :loading="isSearching"
        :disabled="!searchQuery.trim()"
        severity="success"
        class="search-button"
      />
    </div>

    <!-- Search Filters -->
    <div class="search-filters">
      <div class="filter-group">
        <label>Numero risultati:</label>
        <Dropdown
          v-model="searchOptions.limit"
          :options="limitOptions"
          optionLabel="label"
          optionValue="value"
          class="filter-dropdown"
        />
      </div>
      <div class="filter-group">
        <label>Categoria:</label>
        <Dropdown
          v-model="searchOptions.category"
          :options="categoryOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Tutte le categorie"
          showClear
          class="filter-dropdown"
        />
      </div>
      <div class="filter-group">
        <label>Soglia rilevanza:</label>
        <Slider
          v-model="searchOptions.threshold"
          :min="0"
          :max="100"
          class="threshold-slider"
        />
        <span class="threshold-value">{{ searchOptions.threshold }}%</span>
      </div>
    </div>

    <!-- Search Results -->
    <div v-if="searchResults.length > 0" class="search-results">
      <div class="results-header">
        <h4>
          <Icon icon="lucide:file-search" />
          {{ searchResults.length }} risultati trovati
        </h4>
        <Button
          @click="clearResults"
          icon="pi pi-times"
          label="Cancella"
          text
          severity="secondary"
          size="small"
        />
      </div>

      <div class="results-list">
        <Card
          v-for="(result, index) in searchResults"
          :key="index"
          class="result-card"
        >
          <template #header>
            <div class="result-header">
              <div class="result-title">
                <Icon :icon="getFileIcon(result.metadata?.filename)" class="result-icon" />
                <span>{{ result.metadata?.filename || 'Documento senza nome' }}</span>
              </div>
              <div class="result-score">
                <ProgressBar
                  :value="Math.round((result.relevance_score || 0) * 100)"
                  :showValue="false"
                  class="score-bar"
                />
                <span class="score-text">{{ Math.round((result.relevance_score || 0) * 100) }}%</span>
              </div>
            </div>
          </template>

          <template #content>
            <div class="result-content">
              <p class="result-text">{{ highlightQuery(result.content) }}</p>
              <div class="result-metadata">
                <Tag
                  v-if="result.metadata?.category"
                  :value="result.metadata.category"
                  severity="info"
                  class="metadata-tag"
                />
                <Tag
                  v-for="tag in result.metadata?.tags"
                  :key="tag"
                  :value="tag"
                  severity="secondary"
                  class="metadata-tag"
                />
                <span class="result-date">
                  <Icon icon="lucide:calendar" />
                  {{ formatDate(result.metadata?.created_at) }}
                </span>
              </div>
            </div>
          </template>

          <template #footer>
            <div class="result-actions">
              <Button
                @click="viewDocument(result)"
                icon="pi pi-eye"
                label="Visualizza"
                text
                severity="info"
              />
              <Button
                @click="copyContent(result.content)"
                icon="pi pi-copy"
                label="Copia"
                text
                severity="secondary"
              />
            </div>
          </template>
        </Card>
      </div>

      <!-- Pagination -->
      <Paginator
        id="rag-semantic-search-paginator-vscode"
        v-if="totalResults > searchOptions.limit"
        v-model:first="currentPage"
        :rows="searchOptions.limit"
        :totalRecords="totalResults"
        @page="onPageChange"
        class="results-paginator"
      />
    </div>

    <!-- Empty State -->
    <div v-else-if="hasSearched && !isSearching" class="empty-state">
      <Icon icon="lucide:search-x" class="empty-icon" />
      <h4>Nessun risultato trovato</h4>
      <p>Prova a modificare la query o i filtri di ricerca</p>
    </div>

    <!-- Initial State -->
    <div v-else-if="!hasSearched" class="initial-state">
      <Icon icon="lucide:sparkles" class="initial-icon" />
      <h4>Inizia la ricerca</h4>
      <p>Inserisci una domanda o parole chiave per cercare nella base di conoscenza</p>
      <div class="example-queries">
        <h5>Esempi di ricerca:</h5>
        <Chip
          v-for="example in exampleQueries"
          :key="example"
          :label="example"
          @click="selectExample(example)"
          class="example-chip"
        />
      </div>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="isSearching" class="loading-skeleton">
      <Card v-for="i in 3" :key="i" class="skeleton-card">
        <template #content>
          <Skeleton width="100%" height="20px" class="mb-2" />
          <Skeleton width="80%" height="20px" class="mb-2" />
          <Skeleton width="90%" height="60px" />
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Slider from 'primevue/slider'
import Card from 'primevue/card'
import Tag from 'primevue/tag'
import ProgressBar from 'primevue/progressbar'
import Paginator from 'primevue/paginator'
import Chip from 'primevue/chip'
import Skeleton from 'primevue/skeleton'
import { useToast } from 'primevue/usetoast'
import ragApi from '../../api/rag'

// Emits
const emit = defineEmits(['view-document'])

// Composables
const toast = useToast()

// State
const searchQuery = ref('')
const searchResults = ref<any[]>([])
const isSearching = ref(false)
const hasSearched = ref(false)
const currentPage = ref(0)
const totalResults = ref(0)

// Search options
const searchOptions = reactive({
  limit: 10,
  category: null,
  threshold: 70
})

// Options
const limitOptions = [
  { label: '5 risultati', value: 5 },
  { label: '10 risultati', value: 10 },
  { label: '20 risultati', value: 20 },
  { label: '50 risultati', value: 50 }
]

const categoryOptions = ref<any[]>([])

const exampleQueries = [
  'Come configurare il sistema',
  'Procedure di sicurezza',
  'Analisi dei dati',
  'Best practices'
]

// Methods
const performSearch = async () => {
  const query = searchQuery.value.trim()
  if (!query) {
    toast.add({
      severity: 'warn',
      summary: 'Query vuota',
      detail: 'Inserisci una query di ricerca',
      life: 3000
    })
    return
  }

  isSearching.value = true
  hasSearched.value = true

  try {
    const searchRequest: any = {
      query,
      top_k: searchOptions.limit
    }

    // Add optional parameters only if they have values
    if (searchOptions.threshold && searchOptions.threshold > 0) {
      searchRequest.threshold = searchOptions.threshold / 100
    }

    if (searchOptions.category) {
      searchRequest.category = searchOptions.category
    }

    const response = await ragApi.searchDocuments(searchRequest)

    searchResults.value = response.results || []
    totalResults.value = response.total || searchResults.value.length

    if (searchResults.value.length === 0) {
      toast.add({
        severity: 'info',
        summary: 'Nessun risultato',
        detail: 'Prova con una query diversa',
        life: 3000
      })
    }
  } catch (error) {
    console.error('Search error:', error)
    toast.add({
      severity: 'error',
      summary: 'Errore di ricerca',
      detail: 'Si è verificato un errore durante la ricerca',
      life: 5000
    })
  } finally {
    isSearching.value = false
  }
}

const selectExample = async (example: string) => {
  searchQuery.value = example
  await performSearch()
}

const clearResults = () => {
  searchResults.value = []
  hasSearched.value = false
  currentPage.value = 0
  totalResults.value = 0
}

const onPageChange = (event: any) => {
  // Ricarica risultati per la nuova pagina SOLO se c'è una query
  if (searchQuery.value.trim()) {
    performSearch()
  }
}

const viewDocument = async (result: any) => {
  try {
    // Fetch full document from API using backend proxy
    const docId = result.doc_id || result.metadata?.doc_id
    if (!docId) {
      throw new Error('Document ID not found')
    }

    const response = await ragApi.getDocument(docId)

    // Open view dialog (emit event to parent or use local dialog)
    emit('view-document', response.document)

    toast.add({
      severity: 'success',
      summary: 'Documento Caricato',
      detail: `${response.document?.metadata?.filename || 'Documento'} caricato`,
      life: 2000
    })
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

const copyContent = (content: string) => {
  navigator.clipboard.writeText(content)
  toast.add({
    severity: 'success',
    summary: 'Copiato',
    detail: 'Contenuto copiato negli appunti',
    life: 2000
  })
}

const highlightQuery = (content: string) => {
  // Limita il contenuto a 300 caratteri
  let excerpt = content.substring(0, 300)
  if (content.length > 300) {
    excerpt += '...'
  }
  return excerpt
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

const formatDate = (dateString?: string) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('it-IT', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

// Load categories on mount
onMounted(async () => {
  try {
    const categories = await ragApi.getCategories()
    categoryOptions.value = categories.map((cat: string) => ({
      label: cat,
      value: cat
    }))
  } catch (error) {
    console.error('Error loading categories:', error)
  }
})
</script>

<style scoped>
.semantic-search {
  width: 100%;
}

/* Header */
.search-header {
  margin-bottom: 1.5rem;
}

.search-header h3 {
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

/* Search Input */
.search-input-container {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.search-box {
  flex: 1;
  position: relative;
}

.search-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #a0a0a0;
  font-size: 1.25rem;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding-left: 3rem !important;
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #ffffff !important;
  font-size: 1rem;
}

.search-input:focus {
  border-color: #10b981 !important;
  box-shadow: 0 0 0 0.2rem rgba(16, 185, 129, 0.25) !important;
}

.search-button {
  min-width: 120px;
}

/* Search Filters */
.search-filters {
  display: flex;
  gap: 2rem;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.filter-group label {
  color: #a0a0a0;
  font-size: 0.9rem;
  white-space: nowrap;
}

.filter-dropdown {
  min-width: 150px;
}

.filter-dropdown :deep(.p-dropdown) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.threshold-slider {
  width: 100px;
}

.threshold-value {
  color: #10b981;
  font-weight: 500;
  min-width: 40px;
}

/* Search Results */
.search-results {
  margin-top: 2rem;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.results-header h4 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  color: #ffffff;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.result-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.result-card:hover {
  border-color: rgba(16, 185, 129, 0.3);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #ffffff;
  font-weight: 500;
}

.result-icon {
  color: #10b981;
  font-size: 1.25rem;
}

.result-score {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.score-bar {
  width: 60px;
}

.score-bar :deep(.p-progressbar) {
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
}

.score-bar :deep(.p-progressbar-value) {
  background: linear-gradient(90deg, #10b981 0%, #0d9668 100%);
}

.score-text {
  color: #10b981;
  font-size: 0.9rem;
  font-weight: 500;
}

.result-content {
  padding: 0.5rem 0;
}

.result-text {
  color: #e0e0e0;
  line-height: 1.6;
  margin: 0 0 1rem 0;
}

.result-metadata {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.metadata-tag {
  font-size: 0.85rem;
}

.result-date {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  color: #a0a0a0;
  font-size: 0.85rem;
  margin-left: auto;
}

.result-actions {
  display: flex;
  gap: 0.5rem;
}

/* Empty & Initial States */
.empty-state,
.initial-state {
  text-align: center;
  padding: 3rem 2rem;
  color: #a0a0a0;
}

.empty-icon,
.initial-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.initial-icon {
  color: #10b981;
  opacity: 0.7;
}

.empty-state h4,
.initial-state h4 {
  color: #ffffff;
  margin: 0 0 0.5rem 0;
}

.empty-state p,
.initial-state p {
  margin: 0 0 1.5rem 0;
}

.example-queries {
  margin-top: 2rem;
}

.example-queries h5 {
  color: #ffffff;
  margin: 0 0 1rem 0;
  font-size: 0.95rem;
}

.example-chip {
  margin: 0.25rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.example-chip:hover {
  transform: translateY(-2px);
}

/* Loading Skeleton */
.loading-skeleton {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.skeleton-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.skeleton-card :deep(.p-skeleton) {
  background: rgba(255, 255, 255, 0.1);
}

/* Paginator */
.results-paginator {
  margin-top: 2rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

/* Responsive */
@media (max-width: 768px) {
  .search-input-container {
    flex-direction: column;
  }

  .search-filters {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-group {
    width: 100%;
    justify-content: space-between;
  }

  .result-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .result-score {
    width: 100%;
  }

  .result-metadata {
    flex-direction: column;
    align-items: flex-start;
  }

  .result-date {
    margin-left: 0;
  }
}

/* Utility */
.mb-2 {
  margin-bottom: 0.5rem;
}
</style>

<!-- GLOBAL VS CODE THEME OVERRIDE - NO SCOPED - ID SPECIFICITY -->
<style>
/* ⚡ PAGINATOR - Force VS Code gray (not blue!) */
#rag-semantic-search-paginator-vscode {
  background: #1A1A1A !important;
  background-color: #1A1A1A !important;
  border: 1px solid #3C3C3C !important;
  color: #9E9E9E !important;
}

/* Paginator buttons - Gray background */
#rag-semantic-search-paginator-vscode .p-paginator-page,
#rag-semantic-search-paginator-vscode .p-paginator-first,
#rag-semantic-search-paginator-vscode .p-paginator-prev,
#rag-semantic-search-paginator-vscode .p-paginator-next,
#rag-semantic-search-paginator-vscode .p-paginator-last {
  background: #2A2A2A !important;
  background-color: #2A2A2A !important;
  color: #9E9E9E !important;
  border: 1px solid #3C3C3C !important;
}

/* Paginator buttons hover - Lighter gray */
#rag-semantic-search-paginator-vscode .p-paginator-page:not(.p-disabled):hover,
#rag-semantic-search-paginator-vscode .p-paginator-first:not(.p-disabled):hover,
#rag-semantic-search-paginator-vscode .p-paginator-prev:not(.p-disabled):hover,
#rag-semantic-search-paginator-vscode .p-paginator-next:not(.p-disabled):hover,
#rag-semantic-search-paginator-vscode .p-paginator-last:not(.p-disabled):hover {
  background: #3C3C3C !important;
  background-color: #3C3C3C !important;
  color: #E0E0E0 !important;
  border-color: #6B6B6B !important;
}

/* Active page - VS Code accent blue */
#rag-semantic-search-paginator-vscode .p-paginator-page.p-highlight {
  background: #007ACC !important;
  background-color: #007ACC !important;
  color: #FFFFFF !important;
  border-color: #007ACC !important;
}

#rag-semantic-search-paginator-vscode .p-paginator-page.p-highlight:hover {
  background: #005A9E !important;
  background-color: #005A9E !important;
}

/* Disabled buttons */
#rag-semantic-search-paginator-vscode .p-paginator-page.p-disabled,
#rag-semantic-search-paginator-vscode .p-paginator-first.p-disabled,
#rag-semantic-search-paginator-vscode .p-paginator-prev.p-disabled,
#rag-semantic-search-paginator-vscode .p-paginator-next.p-disabled,
#rag-semantic-search-paginator-vscode .p-paginator-last.p-disabled {
  opacity: 0.4 !important;
  background: #1A1A1A !important;
}

/* Current page display */
#rag-semantic-search-paginator-vscode .p-paginator-current {
  color: #9E9E9E !important;
}

/* ⚡ DROPDOWNS - Force VS Code theme (not blue!) */
/* Filter Dropdowns in search-filters section */
.semantic-search .p-dropdown {
  background: #2A2A2A !important;
  border: 1px solid #3C3C3C !important;
  color: #E0E0E0 !important;
}

.semantic-search .p-dropdown:hover {
  border-color: #6B6B6B !important;
}

.semantic-search .p-dropdown:focus,
.semantic-search .p-dropdown.p-focus {
  border-color: #007ACC !important;
  box-shadow: 0 0 0 1px #007ACC !important;
}

/* Dropdown label (selected value) */
.semantic-search .p-dropdown .p-dropdown-label {
  color: #E0E0E0 !important;
  background: transparent !important;
}

.semantic-search .p-dropdown .p-dropdown-label.p-placeholder {
  color: #9E9E9E !important;
}

/* Dropdown trigger button */
.semantic-search .p-dropdown .p-dropdown-trigger {
  background: transparent !important;
  color: #9E9E9E !important;
}

/* Dropdown panel (options list) */
.semantic-search .p-dropdown-panel {
  background: #2A2A2A !important;
  border: 1px solid #3C3C3C !important;
  color: #E0E0E0 !important;
}

/* Dropdown items */
.semantic-search .p-dropdown-panel .p-dropdown-items .p-dropdown-item {
  background: transparent !important;
  color: #E0E0E0 !important;
}

.semantic-search .p-dropdown-panel .p-dropdown-items .p-dropdown-item:hover {
  background: #3C3C3C !important;
  color: #FFFFFF !important;
}

.semantic-search .p-dropdown-panel .p-dropdown-items .p-dropdown-item.p-highlight {
  background: #007ACC !important;
  color: #FFFFFF !important;
}

.semantic-search .p-dropdown-panel .p-dropdown-items .p-dropdown-item.p-focus {
  background: #3C3C3C !important;
}
</style>