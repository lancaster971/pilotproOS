<template>
  <div class="rag-manager">
    <!-- Header -->
    <div class="rag-header">
      <div class="header-content">
        <h2 class="rag-title">
          <i class="pi pi-database mr-2"></i>
          Knowledge Base Manager
        </h2>
        <p class="rag-description">
          Manage your document knowledge base with advanced semantic search capabilities
        </p>
      </div>
      <div class="header-actions">
        <Button
          label="Upload Documents"
          icon="pi pi-upload"
          class="p-button-primary mr-2"
          @click="showUploadDialog = true"
        />
        <Button
          label="Bulk Import"
          icon="pi pi-download"
          class="p-button-outlined mr-2"
          @click="showBulkImportDialog = true"
        />
        <Button
          label="Reindex"
          icon="pi pi-refresh"
          class="p-button-outlined"
          @click="reindexKnowledgeBase"
          :loading="reindexing"
        />
      </div>
    </div>

    <!-- Statistics Cards -->
    <div class="stats-grid" v-if="statistics">
      <Card class="stat-card">
        <template #header>
          <div class="stat-icon-primary">
            <i class="pi pi-file"></i>
          </div>
        </template>
        <template #title>{{ statistics.total_documents }}</template>
        <template #subtitle>Total Documents</template>
      </Card>

      <Card class="stat-card">
        <template #header>
          <div class="stat-icon-success">
            <i class="pi pi-database"></i>
          </div>
        </template>
        <template #title>{{ statistics.total_size_mb.toFixed(1) }} MB</template>
        <template #subtitle>Storage Used</template>
      </Card>

      <Card class="stat-card">
        <template #header>
          <div class="stat-icon-info">
            <i class="pi pi-tags"></i>
          </div>
        </template>
        <template #title>{{ statistics.categories.length }}</template>
        <template #subtitle>Categories</template>
      </Card>

      <Card class="stat-card">
        <template #header>
          <div class="stat-icon-warning">
            <i class="pi pi-clock"></i>
          </div>
        </template>
        <template #title>{{ formatLastUpdate(statistics.last_update) }}</template>
        <template #subtitle>Last Update</template>
      </Card>
    </div>

    <!-- Main Content Tabs -->
    <TabView>
      <TabPanel header="Search Documents">
        <RAGSearchPanel
          @document-selected="selectedDocument = $event"
        />
      </TabPanel>

      <TabPanel header="Manage Documents">
        <RAGDocumentList
          @document-selected="selectedDocument = $event"
          @document-updated="refreshStats"
          @document-deleted="refreshStats"
        />
      </TabPanel>

      <TabPanel header="Analytics">
        <RAGAnalytics :statistics="statistics" />
      </TabPanel>
    </TabView>

    <!-- Upload Dialog -->
    <RAGUploadDialog
      v-model:visible="showUploadDialog"
      @upload-complete="handleUploadComplete"
    />

    <!-- Bulk Import Dialog -->
    <RAGBulkImportDialog
      v-model:visible="showBulkImportDialog"
      @import-complete="handleImportComplete"
    />

    <!-- Document Detail Sidebar -->
    <RAGDocumentDetail
      v-model:visible="showDocumentDetail"
      :document="selectedDocument"
      @document-updated="handleDocumentUpdate"
      @document-deleted="handleDocumentDelete"
    />

    <!-- WebSocket Status -->
    <div class="websocket-status" :class="{ 'connected': wsConnected }">
      <i :class="wsConnected ? 'pi pi-circle-on' : 'pi pi-circle-off'"></i>
      {{ wsConnected ? 'Real-time Connected' : 'Disconnected' }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useToast } from 'vue-toastification'
import Button from 'primevue/button'
import Card from 'primevue/card'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'

import RAGSearchPanel from './RAGSearchPanel.vue'
import RAGDocumentList from './RAGDocumentList.vue'
import RAGAnalytics from './RAGAnalytics.vue'
import RAGUploadDialog from './RAGUploadDialog.vue'
import RAGBulkImportDialog from './RAGBulkImportDialog.vue'
import RAGDocumentDetail from './RAGDocumentDetail.vue'

import { ragApi } from '@/api/rag'

const toast = useToast()

// Reactive state
const statistics = ref(null)
const selectedDocument = ref(null)
const showUploadDialog = ref(false)
const showBulkImportDialog = ref(false)
const showDocumentDetail = ref(false)
const reindexing = ref(false)
const wsConnected = ref(false)

// WebSocket connection
let websocket = null

// Watch selectedDocument to show detail
watch(selectedDocument, (newDoc) => {
  if (newDoc) {
    showDocumentDetail.value = true
  }
})

// Initialize
onMounted(async () => {
  await loadStatistics()
  connectWebSocket()
})

onUnmounted(() => {
  if (websocket) {
    websocket.close()
  }
})

// Load RAG statistics
const loadStatistics = async () => {
  try {
    const response = await ragApi.getStatistics()
    statistics.value = response
  } catch (error) {
    console.error('Error loading RAG statistics:', error)
    toast.error('Failed to load knowledge base statistics')
  }
}

// Connect WebSocket for real-time updates
const connectWebSocket = () => {
  const wsUrl = `ws://localhost:8000/api/rag/ws`
  websocket = new WebSocket(wsUrl)

  websocket.onopen = () => {
    wsConnected.value = true
    console.log('RAG WebSocket connected')
  }

  websocket.onmessage = (event) => {
    const message = JSON.parse(event.data)
    handleWebSocketMessage(message)
  }

  websocket.onclose = () => {
    wsConnected.value = false
    console.log('RAG WebSocket disconnected')

    // Reconnect after 5 seconds
    setTimeout(connectWebSocket, 5000)
  }

  websocket.onerror = (error) => {
    console.error('RAG WebSocket error:', error)
    wsConnected.value = false
  }
}

// Handle WebSocket messages
const handleWebSocketMessage = (message) => {
  switch (message.type) {
    case 'document_uploaded':
      toast.success(`File "${message.filename}" has been processed`)
      refreshStats()
      break

    case 'document_updated':
      toast.info('Document has been modified')
      refreshStats()
      break

    case 'document_deleted':
      toast.warning('Document has been removed')
      refreshStats()
      break

    case 'bulk_import_progress':
      toast.info(`Processing ${message.current_file} (${message.processed}/${message.total})`)
      break

    case 'reindex_started':
      toast.info('Knowledge base is being reindexed')
      break
  }
}

// Reindex knowledge base
const reindexKnowledgeBase = async () => {
  reindexing.value = true

  try {
    await ragApi.reindex()
    toast.success('Knowledge base reindexing has been initiated')
  } catch (error) {
    console.error('Error starting reindex:', error)
    toast.error('Failed to start knowledge base reindexing')
  } finally {
    reindexing.value = false
  }
}

// Handle upload complete
const handleUploadComplete = (result) => {
  showUploadDialog.value = false
  toast.success(result.message || 'Documents uploaded successfully')
  refreshStats()
}

// Handle import complete
const handleImportComplete = (result) => {
  showBulkImportDialog.value = false
  toast.success(`Processed ${result.processed_files} files in ${result.processing_time_seconds.toFixed(1)}s`)
  refreshStats()
}

// Handle document update
const handleDocumentUpdate = () => {
  showDocumentDetail.value = false
  selectedDocument.value = null
  refreshStats()
}

// Handle document delete
const handleDocumentDelete = () => {
  showDocumentDetail.value = false
  selectedDocument.value = null
  refreshStats()
}

// Refresh statistics
const refreshStats = async () => {
  await loadStatistics()
}

// Format last update date
const formatLastUpdate = (dateStr) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 60) {
    return `${diffMins}m ago`
  } else if (diffMins < 1440) {
    return `${Math.floor(diffMins / 60)}h ago`
  } else {
    return `${Math.floor(diffMins / 1440)}d ago`
  }
}
</script>

