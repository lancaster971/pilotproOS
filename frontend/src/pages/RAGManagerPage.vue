<template>
  <MainLayout>
    <div class="knowledge-base-premium">
      <!-- Premium Header -->
      <div class="kb-header">
        <div class="header-content">
          <div class="header-left">
            <Icon icon="mdi:book-open-variant" class="header-icon" />
            <div>
              <h1>Knowledge Base</h1>
              <p class="subtitle">Intelligent Document Management & Semantic Search</p>
            </div>
          </div>
          <div class="header-actions">
            <button @click="refreshStats" class="action-btn secondary" :disabled="loading">
              <Icon :icon="loading ? 'mdi:loading' : 'mdi:refresh'" :class="{'animate-spin': loading}" />
              Refresh
            </button>
            <button @click="showUploadModal = true" class="action-btn primary">
              <Icon icon="mdi:upload" />
              Upload Document
            </button>
          </div>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon documents">
            <Icon icon="mdi:file-document-multiple" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_documents }}</div>
            <div class="stat-label">Total Documents</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon storage">
            <Icon icon="mdi:database" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_size_mb.toFixed(1) }} MB</div>
            <div class="stat-label">Storage Used</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon categories">
            <Icon icon="mdi:tag-multiple" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.categories?.length || 0 }}</div>
            <div class="stat-label">Categories</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon update">
            <Icon icon="mdi:clock-outline" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatTime(stats.last_update) }}</div>
            <div class="stat-label">Last Update</div>
          </div>
        </div>
      </div>

      <!-- Main Content -->
      <div class="kb-content">
        <!-- Search Section -->
        <div class="search-section">
          <div class="search-header">
            <h2>Semantic Search</h2>
            <p>Find documents using natural language queries</p>
          </div>
          <div class="search-box">
            <Icon icon="mdi:magnify" class="search-icon" />
            <input
              v-model="searchQuery"
              @keyup.enter="performSearch"
              placeholder="Search documents by content, keywords, or questions..."
              class="search-input"
            />
            <button @click="performSearch" class="search-btn" :disabled="!searchQuery || searching">
              <Icon :icon="searching ? 'mdi:loading' : 'mdi:arrow-right'" :class="{'animate-spin': searching}" />
            </button>
          </div>

          <!-- Search Results -->
          <div v-if="searchResults.length > 0" class="search-results">
            <div class="results-header">
              <span>{{ searchResults.length }} results found</span>
              <button @click="clearSearch" class="clear-btn">
                <Icon icon="mdi:close" />
                Clear
              </button>
            </div>
            <div class="results-list">
              <div v-for="result in searchResults" :key="result.id" class="result-item">
                <div class="result-header">
                  <div class="result-title">
                    <Icon icon="mdi:file-document" class="doc-icon" />
                    {{ result.metadata?.filename || 'Untitled Document' }}
                  </div>
                  <div class="result-score">
                    <div class="score-bar" :style="{width: (result.score * 100) + '%'}"></div>
                    <span class="score-text">{{ (result.score * 100).toFixed(0) }}% match</span>
                  </div>
                </div>
                <div class="result-content">{{ result.content.substring(0, 200) }}...</div>
                <div class="result-meta">
                  <span v-if="result.metadata?.category" class="meta-tag">{{ result.metadata.category }}</span>
                  <span class="meta-date">{{ formatDate(result.metadata?.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else-if="searchPerformed && !searching" class="empty-state">
            <Icon icon="mdi:magnify-close" class="empty-icon" />
            <p>No documents found matching your query</p>
          </div>
        </div>

        <!-- Documents List -->
        <div class="documents-section">
          <div class="section-header">
            <h2>All Documents</h2>
            <div class="view-options">
              <button @click="viewMode = 'grid'" :class="['view-btn', {active: viewMode === 'grid'}]">
                <Icon icon="mdi:view-grid" />
              </button>
              <button @click="viewMode = 'list'" :class="['view-btn', {active: viewMode === 'list'}]">
                <Icon icon="mdi:view-list" />
              </button>
            </div>
          </div>

          <!-- Documents Grid/List -->
          <div v-if="documents.length > 0" :class="['documents-container', viewMode]">
            <div v-for="doc in documents" :key="doc.id" class="document-card">
              <div class="doc-icon-large">
                <Icon :icon="getDocIcon(doc.metadata?.filename)" />
              </div>
              <div class="doc-info">
                <div class="doc-title">{{ doc.metadata?.filename || 'Untitled' }}</div>
                <div class="doc-meta">
                  <span v-if="doc.metadata?.category" class="doc-category">{{ doc.metadata.category }}</span>
                  <span class="doc-size">{{ formatSize(doc.metadata?.size) }}</span>
                  <span class="doc-date">{{ formatDate(doc.metadata?.created_at) }}</span>
                </div>
              </div>
              <div class="doc-actions">
                <button @click="viewDocument(doc)" class="doc-action-btn" title="View">
                  <Icon icon="mdi:eye" />
                </button>
                <button @click="deleteDocument(doc.id)" class="doc-action-btn danger" title="Delete">
                  <Icon icon="mdi:delete" />
                </button>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else class="empty-state">
            <Icon icon="mdi:folder-open-outline" class="empty-icon" />
            <p>No documents in knowledge base</p>
            <button @click="showUploadModal = true" class="empty-action-btn">
              <Icon icon="mdi:upload" />
              Upload Your First Document
            </button>
          </div>
        </div>
      </div>

      <!-- Upload Modal -->
      <div v-if="showUploadModal" class="modal-overlay" @click.self="showUploadModal = false">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Upload Document</h3>
            <button @click="showUploadModal = false" class="modal-close">
              <Icon icon="mdi:close" />
            </button>
          </div>
          <div class="modal-body">
            <div class="upload-area" @dragover.prevent @drop.prevent="handleDrop">
              <Icon icon="mdi:cloud-upload" class="upload-icon" />
              <p>Drag & drop files here or click to browse</p>
              <input type="file" @change="handleFileSelect" accept=".pdf,.txt,.md,.doc,.docx" multiple hidden ref="fileInput" />
              <button @click="$refs.fileInput.click()" class="browse-btn">Browse Files</button>
            </div>
            <div v-if="uploadFiles.length > 0" class="upload-files-list">
              <div v-for="(file, idx) in uploadFiles" :key="idx" class="upload-file-item">
                <Icon icon="mdi:file" />
                <span>{{ file.name }}</span>
                <button @click="uploadFiles.splice(idx, 1)" class="remove-file-btn">
                  <Icon icon="mdi:close" />
                </button>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button @click="showUploadModal = false" class="modal-btn secondary">Cancel</button>
            <button @click="uploadDocuments" class="modal-btn primary" :disabled="uploadFiles.length === 0 || uploading">
              <Icon :icon="uploading ? 'mdi:loading' : 'mdi:upload'" :class="{'animate-spin': uploading}" />
              {{ uploading ? 'Uploading...' : 'Upload' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import MainLayout from '@/components/layout/MainLayout.vue'
import { apiClient } from '@/services/api-client'
import { useToast } from 'vue-toastification'

const toast = useToast()

// State
const stats = ref({
  total_documents: 0,
  total_size_mb: 0,
  categories: [],
  last_update: new Date().toISOString()
})
const documents = ref([])
const searchQuery = ref('')
const searchResults = ref([])
const searchPerformed = ref(false)
const loading = ref(false)
const searching = ref(false)
const uploading = ref(false)
const showUploadModal = ref(false)
const uploadFiles = ref([])
const viewMode = ref('grid')
const fileInput = ref(null)

// Load data on mount
onMounted(() => {
  refreshStats()
  loadDocuments()
})

// Refresh statistics
const refreshStats = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/api/rag/stats')
    stats.value = response
  } catch (error) {
    console.error('Error loading stats:', error)
    toast.error('Failed to load statistics')
  } finally {
    loading.value = false
  }
}

// Load all documents
const loadDocuments = async () => {
  try {
    const response = await apiClient.get('/api/rag/documents')
    documents.value = response.documents || []
  } catch (error) {
    console.error('Error loading documents:', error)
  }
}

// Perform semantic search
const performSearch = async () => {
  if (!searchQuery.value) return

  searching.value = true
  searchPerformed.value = true
  try {
    const response = await apiClient.post('/api/rag/search', {
      query: searchQuery.value,
      top_k: 10
    })
    searchResults.value = response.results || []
  } catch (error) {
    console.error('Search error:', error)
    toast.error('Search failed')
  } finally {
    searching.value = false
  }
}

// Clear search
const clearSearch = () => {
  searchQuery.value = ''
  searchResults.value = []
  searchPerformed.value = false
}

// File upload handlers
const handleFileSelect = (event: any) => {
  const files = Array.from(event.target.files)
  uploadFiles.value = [...uploadFiles.value, ...files]
}

const handleDrop = (event: any) => {
  const files = Array.from(event.dataTransfer.files)
  uploadFiles.value = [...uploadFiles.value, ...files]
}

const uploadDocuments = async () => {
  if (uploadFiles.value.length === 0) return

  uploading.value = true
  const formData = new FormData()
  uploadFiles.value.forEach(file => formData.append('files', file))

  try {
    // Call backend which proxies to intelligence engine
    await fetch('/api/rag/upload', {
      method: 'POST',
      body: formData
    })
    toast.success(`${uploadFiles.value.length} document(s) uploaded successfully`)
    uploadFiles.value = []
    showUploadModal.value = false
    refreshStats()
    loadDocuments()
  } catch (error) {
    console.error('Upload error:', error)
    toast.error('Upload failed')
  } finally {
    uploading.value = false
  }
}

// Delete document
const deleteDocument = async (id: string) => {
  if (!confirm('Are you sure you want to delete this document?')) return

  try {
    await apiClient.delete(`/api/rag/documents/${id}`)
    toast.success('Document deleted')
    refreshStats()
    loadDocuments()
  } catch (error) {
    toast.error('Failed to delete document')
  }
}

// View document
const viewDocument = (doc: any) => {
  // TODO: Implement document viewer
  console.log('View document:', doc)
}

// Utility functions
const formatTime = (timestamp: string) => {
  if (!timestamp) return 'Never'
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)

  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`
  return `${Math.floor(minutes / 1440)}d ago`
}

const formatDate = (timestamp: string) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

const formatSize = (bytes: number) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const getDocIcon = (filename: string) => {
  if (!filename) return 'mdi:file'
  const ext = filename.split('.').pop()?.toLowerCase()
  const icons = {
    pdf: 'mdi:file-pdf-box',
    doc: 'mdi:file-word-box',
    docx: 'mdi:file-word-box',
    txt: 'mdi:file-document-outline',
    md: 'mdi:language-markdown'
  }
  return icons[ext] || 'mdi:file'
}
</script>

<style>
.knowledge-base-premium {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

/* Header */
.kb-header {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
  color: white;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-icon {
  font-size: 3rem;
  opacity: 0.9;
}

.kb-header h1 {
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
}

.subtitle {
  opacity: 0.9;
  margin: 0.5rem 0 0 0;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  border: none;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.primary {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border: 1px solid rgba(96, 165, 250, 0.3);
}

.action-btn.secondary {
  background: rgba(255,255,255,0.2);
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(30, 30, 30, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  color: white;
}

.stat-icon.documents { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.stat-icon.storage { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
.stat-icon.categories { background: linear-gradient(135deg, #06b6d4, #0891b2); }
.stat-icon.update { background: linear-gradient(135deg, #f59e0b, #d97706); }

.stat-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #e2e8f0;
}

.stat-label {
  color: #9ca3af;
  font-size: 0.9rem;
}

/* Search Section */
.search-section {
  background: rgba(30, 30, 30, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.search-header h2 {
  margin: 0 0 0.5rem 0;
  color: #e2e8f0;
}

.search-header p {
  margin: 0;
  color: #9ca3af;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: rgba(30, 30, 30, 0.6);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 0.75rem 1rem;
  margin-top: 1.5rem;
  transition: border-color 0.2s;
}

.search-box:focus-within {
  border-color: #3b82f6;
}

.search-icon {
  font-size: 1.5rem;
  color: #9ca3af;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 1rem;
  outline: none;
  color: #e2e8f0;
}

.search-btn {
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  transition: background 0.2s;
}

.search-btn:hover:not(:disabled) {
  background: #2563eb;
}

.search-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Search Results */
.search-results {
  margin-top: 2rem;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
}

.clear-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.result-item {
  padding: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  background: rgba(30, 30, 30, 0.3);
  transition: all 0.2s;
}

.result-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.result-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #e2e8f0;
}

.doc-icon {
  color: #3b82f6;
}

.result-score {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.score-bar {
  height: 4px;
  background: #3b82f6;
  border-radius: 2px;
  width: 60px;
}

.score-text {
  font-size: 0.85rem;
  color: #9ca3af;
}

.result-content {
  color: #cbd5e0;
  line-height: 1.6;
  margin: 0.5rem 0;
}

.result-meta {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}

.meta-tag {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
}

.meta-date {
  color: #9ca3af;
  font-size: 0.85rem;
}

/* Documents Section */
.documents-section {
  background: rgba(30, 30, 30, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  margin: 0;
  color: #e2e8f0;
}

.view-options {
  display: flex;
  gap: 0.5rem;
}

.view-btn {
  background: rgba(30, 30, 30, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 0.5rem;
  cursor: pointer;
  color: #9ca3af;
  transition: all 0.2s;
}

.view-btn:hover,
.view-btn.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.documents-container.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.documents-container.list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.document-card {
  background: rgba(30, 30, 30, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.2s;
}

.document-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}

.doc-icon-large {
  font-size: 2.5rem;
  color: #3b82f6;
}

.doc-info {
  flex: 1;
}

.doc-title {
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 0.5rem;
}

.doc-meta {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  font-size: 0.85rem;
  color: #9ca3af;
}

.doc-category {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-weight: 500;
}

.doc-actions {
  display: flex;
  gap: 0.5rem;
}

.doc-action-btn {
  background: rgba(30, 30, 30, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 0.5rem;
  cursor: pointer;
  color: #9ca3af;
  transition: all 0.2s;
}

.doc-action-btn:hover {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.doc-action-btn.danger:hover {
  background: #f43f5e;
  border-color: #f43f5e;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 3rem;
  color: #9ca3af;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  cursor: pointer;
  margin-top: 1rem;
  transition: background 0.2s;
}

.empty-action-btn:hover {
  background: #2563eb;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #1a1a1a;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  width: 90%;
  max-width: 600px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h3 {
  margin: 0;
  color: #e2e8f0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #9ca3af;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.modal-close:hover {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.modal-body {
  padding: 1.5rem;
}

.upload-area {
  border: 2px dashed rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 3rem;
  text-align: center;
  transition: all 0.2s;
  color: #9ca3af;
}

.upload-area:hover {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
}

.upload-icon {
  font-size: 3rem;
  color: #9ca3af;
  margin-bottom: 1rem;
}

.browse-btn {
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  cursor: pointer;
  margin-top: 1rem;
  transition: background 0.2s;
}

.browse-btn:hover {
  background: #2563eb;
}

.upload-files-list {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.upload-file-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(30, 30, 30, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #e2e8f0;
}

.remove-file-btn {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: #9ca3af;
  padding: 0.25rem;
}

.remove-file-btn:hover {
  color: #f43f5e;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-btn {
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  border: none;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.modal-btn.primary {
  background: #3b82f6;
  color: white;
}

.modal-btn.secondary {
  background: rgba(30, 30, 30, 0.6);
  color: #e2e8f0;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.modal-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.modal-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
