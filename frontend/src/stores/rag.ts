import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import ragApi from '../api/rag'

export interface RAGDocument {
  id: string
  metadata: {
    filename: string
    category?: string
    tags?: string[]
    size?: number
    created_at?: string
    updated_at?: string
  }
  content?: string
  chunks_count?: number
}

export interface RAGStatistics {
  total_documents: number
  total_chunks: number
  total_size_bytes: number
  documents_by_category?: Record<string, number>
  categories?: string[]
  last_update?: string
  embedding_status?: {
    completed: number
    pending: number
    failed: number
  }
}

export interface SearchResult {
  id: string
  content: string
  score: number
  metadata: {
    filename?: string
    category?: string
    tags?: string[]
    created_at?: string
  }
}

export const useRAGStore = defineStore('rag', () => {
  // State
  const documents = ref<RAGDocument[]>([])
  const statistics = ref<RAGStatistics | null>(null)
  const searchResults = ref<SearchResult[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const selectedDocument = ref<RAGDocument | null>(null)

  // Computed
  const totalDocuments = computed(() => statistics.value?.total_documents || 0)
  const totalChunks = computed(() => statistics.value?.total_chunks || 0)
  const categories = computed(() => statistics.value?.categories || [])
  const hasDocuments = computed(() => documents.value.length > 0)

  // Actions
  const fetchStatistics = async () => {
    isLoading.value = true
    error.value = null

    try {
      const stats = await ragApi.getStatistics()
      statistics.value = stats
      return stats
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Errore nel caricamento statistiche'
      console.error('Error fetching RAG statistics:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const fetchDocuments = async (params?: any) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await ragApi.listDocuments(params)
      documents.value = response.documents || []
      return documents.value
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Errore nel caricamento documenti'
      console.error('Error fetching documents:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const uploadDocuments = async (files: File[], metadata?: any) => {
    isLoading.value = true
    error.value = null

    try {
      const formData = new FormData()

      // Aggiungi tutti i file
      files.forEach(file => {
        formData.append('files', file)
      })

      // Aggiungi metadata se presente
      if (metadata) {
        formData.append('metadata', JSON.stringify(metadata))
      }

      const response = await ragApi.uploadDocuments(formData)

      // Aggiorna statistiche dopo upload
      await fetchStatistics()

      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Errore durante upload'
      console.error('Error uploading documents:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const searchDocuments = async (query: string, options?: any) => {
    isLoading.value = true
    error.value = null

    try {
      const searchRequest = {
        query,
        top_k: options?.limit || 10,
        threshold: options?.threshold || 0.7,
        category: options?.category
      }

      const response = await ragApi.searchDocuments(searchRequest)
      searchResults.value = response.results || []
      return searchResults.value
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Errore nella ricerca'
      console.error('Error searching documents:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const updateDocument = async (docId: string, updateData: any) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await ragApi.updateDocument(docId, updateData)

      // Aggiorna documento nella lista locale
      const index = documents.value.findIndex(doc => doc.id === docId)
      if (index !== -1) {
        documents.value[index] = { ...documents.value[index], ...response }
      }

      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Errore aggiornamento documento'
      console.error('Error updating document:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const deleteDocument = async (docId: string) => {
    isLoading.value = true
    error.value = null

    try {
      await ragApi.deleteDocument(docId)

      // Rimuovi documento dalla lista locale
      documents.value = documents.value.filter(doc => doc.id !== docId)

      // Aggiorna statistiche
      await fetchStatistics()

      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Errore eliminazione documento'
      console.error('Error deleting document:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const bulkImport = async (zipFile: File) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await ragApi.bulkImport(zipFile)

      // Aggiorna documenti e statistiche
      await Promise.all([
        fetchDocuments(),
        fetchStatistics()
      ])

      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Errore import bulk'
      console.error('Error bulk importing:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const reindex = async () => {
    isLoading.value = true
    error.value = null

    try {
      const response = await ragApi.reindex()

      // Aggiorna statistiche dopo reindex
      await fetchStatistics()

      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Errore reindexing'
      console.error('Error reindexing:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const clearSearchResults = () => {
    searchResults.value = []
  }

  const selectDocument = (doc: RAGDocument | null) => {
    selectedDocument.value = doc
  }

  const reset = () => {
    documents.value = []
    statistics.value = null
    searchResults.value = []
    selectedDocument.value = null
    error.value = null
  }

  return {
    // State
    documents,
    statistics,
    searchResults,
    isLoading,
    error,
    selectedDocument,

    // Computed
    totalDocuments,
    totalChunks,
    categories,
    hasDocuments,

    // Actions
    fetchStatistics,
    fetchDocuments,
    uploadDocuments,
    searchDocuments,
    updateDocument,
    deleteDocument,
    bulkImport,
    reindex,
    clearSearchResults,
    selectDocument,
    reset
  }
})