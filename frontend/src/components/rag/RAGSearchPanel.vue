<template>
  <div class="rag-search-panel">
    <!-- Search Form -->
    <div class="search-form">
      <div class="search-input-group">
        <div class="p-inputgroup">
          <InputText
            v-model="searchQuery"
            placeholder="Search documents with natural language..."
            @keyup.enter="performSearch"
            :disabled="searching"
            class="search-input"
          />
          <Button
            icon="pi pi-search"
            @click="performSearch"
            :loading="searching"
            class="p-button-primary"
          />
        </div>
      </div>

      <!-- Advanced Filters (Collapsible) -->
      <div class="filters-section">
        <Button
          :label="showFilters ? 'Hide Filters' : 'Show Filters'"
          :icon="showFilters ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"
          class="p-button-text"
          @click="showFilters = !showFilters"
        />

        <div v-if="showFilters" class="filters-content">
          <div class="filter-row">
            <div class="filter-group">
              <label class="filter-label">Category</label>
              <Dropdown
                v-model="filters.category"
                :options="availableCategories"
                option-label="label"
                option-value="value"
                placeholder="All Categories"
                class="filter-dropdown"
              />
            </div>

            <div class="filter-group">
              <label class="filter-label">User Level</label>
              <Dropdown
                v-model="filters.user_level"
                :options="userLevels"
                option-label="label"
                option-value="value"
                placeholder="Select Level"
                class="filter-dropdown"
              />
            </div>

            <div class="filter-group">
              <label class="filter-label">Results Count</label>
              <Dropdown
                v-model="filters.k"
                :options="resultCounts"
                option-label="label"
                option-value="value"
                placeholder="Number of Results"
                class="filter-dropdown"
              />
            </div>
          </div>

          <div class="filter-actions">
            <Button
              label="Clear Filters"
              icon="pi pi-times"
              class="p-button-outlined p-button-secondary"
              @click="clearFilters"
            />
            <Button
              label="Apply Filters"
              icon="pi pi-check"
              class="p-button-outlined"
              @click="performSearch"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Search Results -->
    <div v-if="searchResults.length > 0" class="search-results">
      <div class="results-header">
        <h3>
          <i class="pi pi-search mr-2"></i>
          Search Results ({{ searchResults.length }})
        </h3>
        <div class="query-info">
          <span>Query time: {{ lastQueryTime }}ms</span>
          <Chip v-if="lastQuery" :label="`&quot;${lastQuery}&quot;`" class="query-chip" />
        </div>
      </div>

      <div class="results-grid">
        <Card
          v-for="(result, index) in searchResults"
          :key="`result-${index}`"
          class="result-card"
          @click="selectDocument(result)"
        >
          <template #header>
            <div class="result-header">
              <div class="relevance-score">
                <div class="score-bar">
                  <div
                    class="score-fill"
                    :style="{ width: `${(result.score || 0.5) * 100}%` }"
                  ></div>
                </div>
                <span class="score-text">{{ ((result.score || 0.5) * 100).toFixed(1) }}%</span>
              </div>
              <Badge
                :value="result.metadata?.category || 'general'"
                :severity="getCategorySeverity(result.metadata?.category)"
                class="category-badge"
              />
            </div>
          </template>

          <template #title>
            <div class="result-title">
              <i :class="getDocumentIcon(result.metadata?.source)" class="mr-2"></i>
              {{ result.metadata?.title || 'Untitled Document' }}
            </div>
          </template>

          <template #subtitle>
            <div class="result-subtitle">
              <span class="source">{{ result.metadata?.source || 'Unknown' }}</span>
              <span class="separator">•</span>
              <span class="date">{{ formatDate(result.metadata?.created_at) }}</span>
            </div>
          </template>

          <template #content>
            <div class="result-content">
              <p class="content-preview">
                {{ truncateContent(result.page_content, 200) }}
              </p>

              <div class="result-metadata">
                <div class="metadata-tags" v-if="result.metadata?.tags?.length">
                  <Chip
                    v-for="tag in result.metadata.tags.slice(0, 3)"
                    :key="tag"
                    :label="tag"
                    class="tag-chip"
                  />
                  <span v-if="result.metadata.tags.length > 3" class="more-tags">
                    +{{ result.metadata.tags.length - 3 }} more
                  </span>
                </div>

                <div class="metadata-info">
                  <span v-if="result.metadata?.author" class="author">
                    <i class="pi pi-user mr-1"></i>{{ result.metadata.author }}
                  </span>
                  <span v-if="result.metadata?.version" class="version">
                    v{{ result.metadata.version }}
                  </span>
                </div>
              </div>
            </div>
          </template>

          <template #footer>
            <div class="result-actions">
              <Button
                label="View Details"
                icon="pi pi-eye"
                class="p-button-text p-button-sm"
                @click.stop="selectDocument(result)"
              />
              <Button
                label="Edit"
                icon="pi pi-pencil"
                class="p-button-text p-button-sm"
                @click.stop="editDocument(result)"
              />
              <Button
                label="Share"
                icon="pi pi-share-alt"
                class="p-button-text p-button-sm"
                @click.stop="shareDocument(result)"
              />
            </div>
          </template>
        </Card>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="hasSearched && !searching" class="empty-state">
      <div class="empty-icon">
        <i class="pi pi-search"></i>
      </div>
      <h3>No Results Found</h3>
      <p>Try adjusting your search query or filters</p>
      <Button
        label="Clear Search"
        icon="pi pi-times"
        class="p-button-outlined"
        @click="clearSearch"
      />
    </div>

    <!-- Initial State -->
    <div v-else-if="!hasSearched && !searching" class="initial-state">
      <div class="initial-icon">
        <i class="pi pi-search"></i>
      </div>
      <h3>Semantic Search</h3>
      <p>Search your knowledge base using natural language queries</p>
      <div class="search-examples">
        <h4>Example queries:</h4>
        <div class="example-chips">
          <Chip
            v-for="example in searchExamples"
            :key="example"
            :label="example"
            class="example-chip clickable"
            @click="searchQuery = example; performSearch()"
          />
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="searching" class="loading-state">
      <ProgressSpinner />
      <p>Searching knowledge base...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Dropdown from 'primevue/dropdown'
import Badge from 'primevue/badge'
import Chip from 'primevue/chip'
import ProgressSpinner from 'primevue/progressspinner'

import { ragApi } from '@/api/rag'

const emit = defineEmits(['document-selected'])
const toast = useToast()

// Reactive state
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const hasSearched = ref(false)
const showFilters = ref(false)
const lastQuery = ref('')
const lastQueryTime = ref(0)

// Filters
const filters = ref({
  category: null,
  user_level: 'BUSINESS',
  k: 5
})

// Options
const availableCategories = ref([
  { label: 'All Categories', value: null },
  { label: 'Business Process', value: 'business_process' },
  { label: 'Documentation', value: 'documentation' },
  { label: 'Training', value: 'training' },
  { label: 'Policy', value: 'policy' },
  { label: 'General', value: 'general' }
])

const userLevels = [
  { label: 'Business User', value: 'BUSINESS' },
  { label: 'Administrator', value: 'ADMIN' },
  { label: 'Developer', value: 'DEVELOPER' }
]

const resultCounts = [
  { label: '5 Results', value: 5 },
  { label: '10 Results', value: 10 },
  { label: '15 Results', value: 15 },
  { label: '20 Results', value: 20 }
]

const searchExamples = [
  'How to create a new business process?',
  'User management procedures',
  'System configuration guidelines',
  'Error handling best practices',
  'Integration documentation'
]

// Initialize
onMounted(() => {
  loadAvailableCategories()
})

// Load available categories from API
const loadAvailableCategories = async () => {
  try {
    const stats = await ragApi.getStatistics()
    const categories = stats.categories || []

    // Build categories list
    const categoryOptions = [
      { label: 'All Categories', value: null },
      ...categories.map(cat => ({
        label: cat.charAt(0).toUpperCase() + cat.slice(1).replace('_', ' '),
        value: cat
      }))
    ]

    availableCategories.value = categoryOptions
  } catch (error) {
    console.error('Error loading categories:', error)
  }
}

// Perform semantic search
const performSearch = async () => {
  if (!searchQuery.value.trim()) {
    toast.add({
      severity: 'warn',
      summary: 'Empty Query',
      detail: 'Please enter a search query',
      life: 3000
    })
    return
  }

  searching.value = true
  hasSearched.value = true
  lastQuery.value = searchQuery.value

  try {
    const searchRequest = {
      query: searchQuery.value,
      k: filters.value.k,
      user_level: filters.value.user_level,
      filters: {}
    }

    // Add category filter if selected
    if (filters.value.category) {
      searchRequest.filters.category = filters.value.category
    }

    const response = await ragApi.searchDocuments(searchRequest)

    searchResults.value = response.results || []
    lastQueryTime.value = response.query_time_ms || 0

    if (searchResults.value.length === 0) {
      toast.add({
        severity: 'info',
        summary: 'No Results',
        detail: 'No documents found matching your query',
        life: 3000
      })
    }
  } catch (error) {
    console.error('Search error:', error)
    toast.add({
      severity: 'error',
      summary: 'Search Failed',
      detail: 'Failed to search documents',
      life: 5000
    })
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

// Clear search
const clearSearch = () => {
  searchQuery.value = ''
  searchResults.value = []
  hasSearched.value = false
  lastQuery.value = ''
  lastQueryTime.value = 0
}

// Clear filters
const clearFilters = () => {
  filters.value = {
    category: null,
    user_level: 'BUSINESS',
    k: 5
  }
}

// Select document
const selectDocument = (document) => {
  emit('document-selected', document)
}

// Edit document (placeholder)
const editDocument = (document) => {
  // TODO: Implement edit functionality
  console.log('Edit document:', document.metadata?.id)
}

// Share document (placeholder)
const shareDocument = (document) => {
  // TODO: Implement share functionality
  console.log('Share document:', document.metadata?.id)
}

// Utility functions
const truncateContent = (content, maxLength) => {
  if (!content) return ''
  return content.length > maxLength
    ? content.substring(0, maxLength) + '...'
    : content
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'Unknown'
  return new Date(dateStr).toLocaleDateString()
}

const getDocumentIcon = (source) => {
  const iconMap = {
    'upload': 'pi pi-upload',
    'bulk_import': 'pi pi-download',
    'api': 'pi pi-cog',
    'system': 'pi pi-server'
  }
  return iconMap[source] || 'pi pi-file'
}

const getCategorySeverity = (category) => {
  const severityMap = {
    'business_process': 'success',
    'documentation': 'info',
    'training': 'warning',
    'policy': 'danger',
    'general': 'secondary'
  }
  return severityMap[category] || 'secondary'
}
</script>

<style scoped>
.rag-search-panel {
  padding: 1.5rem;
}

.search-form {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.search-input-group {
  margin-bottom: 1rem;
}

.search-input {
  font-size: 1.1rem;
  padding: 0.75rem 1rem;
}

.filters-section {
  border-top: 1px solid #e9ecef;
  padding-top: 1rem;
}

.filters-content {
  margin-top: 1rem;
  animation: slideDown 0.3s ease;
}

.filter-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
}

.filter-label {
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #495057;
}

.filter-dropdown {
  width: 100%;
}

.filter-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.search-results {
  margin-top: 2rem;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding: 1rem 0;
}

.results-header h3 {
  margin: 0;
  color: #2c3e50;
  display: flex;
  align-items: center;
}

.query-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.query-chip {
  background: #e3f2fd !important;
  color: #1976d2 !important;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 1.5rem;
}

.result-card {
  cursor: pointer;
  transition: all 0.3s;
  height: fit-content;
}

.result-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
}

.relevance-score {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.score-bar {
  width: 60px;
  height: 6px;
  background: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6b6b 0%, #feca57 50%, #48dbfb 100%);
  transition: width 0.3s;
}

.score-text {
  font-size: 0.8rem;
  font-weight: 600;
  color: #495057;
}

.result-title {
  display: flex;
  align-items: center;
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.result-subtitle {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin-bottom: 1rem;
}

.separator {
  margin: 0 0.5rem;
}

.content-preview {
  line-height: 1.6;
  color: #495057;
  margin-bottom: 1rem;
}

.result-metadata {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.metadata-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  align-items: center;
}

.tag-chip {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
}

.more-tags {
  font-size: 0.8rem;
  color: #7f8c8d;
  font-style: italic;
}

.metadata-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  color: #7f8c8d;
}

.result-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e9ecef;
}

.empty-state,
.initial-state {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.empty-icon,
.initial-icon {
  font-size: 4rem;
  color: #bdc3c7;
  margin-bottom: 1rem;
}

.search-examples {
  margin-top: 2rem;
  text-align: left;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.search-examples h4 {
  margin-bottom: 1rem;
  color: #2c3e50;
}

.example-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.example-chip.clickable {
  cursor: pointer;
  transition: all 0.2s;
}

.example-chip.clickable:hover {
  background: #3498db !important;
  color: white !important;
}

.loading-state {
  text-align: center;
  padding: 4rem 2rem;
}

.loading-state p {
  margin-top: 1rem;
  color: #7f8c8d;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>