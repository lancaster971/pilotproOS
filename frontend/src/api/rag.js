/**
 * RAG (Retrieval-Augmented Generation) API Client
 * BATTLE-TESTED: Using OFETCH (same as rest of frontend)
 * Following TODO-MILHENA-EXPERT.md specifications exactly
 *
 * ARCHITECTURE FIX (2025-10-17):
 * Now routes through Backend Express proxy for proper auth/logging
 * Frontend → Backend (:3001/api/rag) → Intelligence Engine (:8000/api/rag)
 */

import { ofetch } from 'ofetch'

// Base configuration - USE BACKEND PROXY (not direct Intelligence Engine)
const RAG_API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001'

// Create ofetch instance with default configuration
const ragApiClient = ofetch.create({
  baseURL: `${RAG_API_BASE}/api/rag`,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000, // 30 seconds timeout for file uploads
  onRequest({ options }) {
    // CRITICAL FIX: Ensure Content-Type is always set (not automatically merged from defaults)
    // Add auth token if available
    const token = localStorage.getItem('auth_token') || localStorage.getItem('token')
    if (token) {
      options.headers = {
        'Content-Type': 'application/json',  // MUST explicitly include default headers
        ...options.headers,
        'Authorization': `Bearer ${token}`
      }
    } else {
      // Even without auth, ensure Content-Type is set
      options.headers = {
        'Content-Type': 'application/json',
        ...options.headers
      }
    }
  },
  onResponseError({ response }) {
    console.error('RAG API Error:', response)

    // Handle specific error cases
    if (response.status === 401) {
      // Unauthorized - redirect to login
      localStorage.removeItem('auth_token')
      localStorage.removeItem('token')
      window.location.href = '/login'
    } else if (response.status === 413) {
      // Payload too large
      throw new Error('File size too large. Please use files smaller than 50MB.')
    } else if (response.status === 422) {
      // Validation error
      const detail = response._data?.detail
      throw new Error(detail || 'Invalid request data')
    }
  }
})

/**
 * RAG API Methods
 */
export const ragApi = {
  /**
   * Upload multiple documents
   * @param {FormData} formData - Form data containing files and metadata
   * @param {Object} options - Additional options (onUploadProgress, etc.)
   * @returns {Promise<Object>} Upload response
   */
  async uploadDocuments(formData, options = {}) {
    return await ragApiClient('/documents', {
      method: 'POST',
      body: formData,
      timeout: 300000, // 5 minutes for large uploads
      ...options
    })
  },

  /**
   * List documents with filtering and pagination
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>} Documents list response
   */
  async listDocuments(params = {}) {
    return await ragApiClient('/documents', {
      method: 'GET',
      query: params
    })
  },

  /**
   * Update document content and metadata
   * @param {string} docId - Document ID
   * @param {Object} data - Update data
   * @returns {Promise<Object>} Update response
   */
  async updateDocument(docId, data) {
    const formData = new FormData()

    if (data.content) {
      formData.append('content', data.content)
    }

    if (data.metadata) {
      formData.append('metadata', JSON.stringify(data.metadata))
    }

    return await ragApiClient(`/documents/${docId}`, {
      method: 'PUT',
      body: formData
    })
  },

  /**
   * Delete document
   * @param {string} docId - Document ID
   * @param {boolean} softDelete - Whether to soft delete (default: false = hard delete)
   * @returns {Promise<Object>} Delete response
   */
  async deleteDocument(docId, softDelete = false) {
    // IMPORTANT: ofetch DELETE with query params causes issues - use params in URL if needed
    const url = `/documents/${docId}${softDelete ? '?soft_delete=true' : ''}`
    return await ragApiClient(url, {
      method: 'DELETE'
    })
  },

  /**
   * Perform semantic search
   * @param {Object} searchRequest - Search parameters
   * @returns {Promise<Object>} Search results
   */
  async searchDocuments(searchRequest) {
    return await ragApiClient('/search', {
      method: 'POST',
      body: searchRequest
    })
  },

  /**
   * Get RAG system statistics
   * @returns {Promise<Object>} System statistics
   */
  async getStatistics() {
    return await ragApiClient('/stats', { method: 'GET' })
  },

  /**
   * Bulk import documents from ZIP archive
   * @param {File} zipFile - ZIP file containing documents
   * @param {Object} options - Upload options
   * @returns {Promise<Object>} Import response
   */
  async bulkImport(zipFile, options = {}) {
    const formData = new FormData()
    formData.append('archive', zipFile)

    return await ragApiClient('/bulk-import', {
      method: 'POST',
      body: formData,
      timeout: 600000, // 10 minutes for large imports
      ...options
    })
  },

  /**
   * Force reindex all documents
   * @returns {Promise<Object>} Reindex response
   */
  async reindex() {
    return await ragApiClient('/reindex', { method: 'POST' })
  },

  /**
   * Get single document by ID
   * @param {string} docId - Document ID
   * @returns {Promise<Object>} Document data
   */
  async getDocument(docId) {
    return await ragApiClient(`/documents/${docId}`, { method: 'GET' })
  },

  /**
   * Export documents (placeholder for future implementation)
   * @param {Object} exportOptions - Export configuration
   * @returns {Promise<Blob>} Exported data
   */
  async exportDocuments(exportOptions = {}) {
    // TODO: Implement document export functionality
    return await ragApiClient('/export', {
      method: 'POST',
      body: exportOptions,
      responseType: 'blob'
    })
  },

  /**
   * Get document content preview
   * @param {string} docId - Document ID
   * @param {number} maxLength - Maximum content length
   * @returns {Promise<Object>} Document preview
   */
  async getDocumentPreview(docId, maxLength = 500) {
    return await ragApiClient(`/documents/${docId}/preview`, {
      method: 'GET',
      query: { max_length: maxLength }
    })
  },

  /**
   * Get document version history
   * @param {string} docId - Document ID
   * @returns {Promise<Object>} Version history
   */
  async getDocumentHistory(docId) {
    return await ragApiClient(`/documents/${docId}/history`, { method: 'GET' })
  },

  /**
   * Restore document version
   * @param {string} docId - Document ID
   * @param {number} version - Version number to restore
   * @returns {Promise<Object>} Restore response
   */
  async restoreDocumentVersion(docId, version) {
    return await ragApiClient(`/documents/${docId}/restore/${version}`, { method: 'POST' })
  },

  /**
   * Get similar documents
   * @param {string} docId - Document ID
   * @param {number} limit - Number of similar documents to return
   * @returns {Promise<Object>} Similar documents
   */
  async getSimilarDocuments(docId, limit = 5) {
    return await ragApiClient(`/documents/${docId}/similar`, {
      method: 'GET',
      query: { limit }
    })
  },

  /**
   * Get document categories
   * @returns {Promise<Array>} Available categories
   */
  async getCategories() {
    const stats = await this.getStatistics()
    return stats.categories || []
  },

  /**
   * Health check for RAG system
   * @returns {Promise<Object>} Health status
   */
  async healthCheck() {
    return await ragApiClient('/health', { method: 'GET' })
  },

  /**
   * Get embedding status for documents
   * @returns {Promise<Object>} Embedding status
   */
  async getEmbeddingStatus() {
    const stats = await this.getStatistics()
    return stats.embedding_status || {}
  },

  /**
   * Validate document format before upload
   * @param {File} file - File to validate
   * @returns {Object} Validation result
   */
  validateFile(file) {
    const validExtensions = ['.pdf', '.docx', '.txt', '.md', '.html']
    const maxSize = 50 * 1024 * 1024 // 50MB

    const extension = '.' + file.name.split('.').pop().toLowerCase()

    const result = {
      valid: true,
      errors: []
    }

    if (!validExtensions.includes(extension)) {
      result.valid = false
      result.errors.push(`Unsupported file type: ${extension}`)
    }

    if (file.size > maxSize) {
      result.valid = false
      result.errors.push('File size exceeds 50MB limit')
    }

    if (file.size === 0) {
      result.valid = false
      result.errors.push('File is empty')
    }

    return result
  },

  /**
   * Create WebSocket connection for real-time updates
   * NOTE: WebSocket connects DIRECTLY to Intelligence Engine (not through backend proxy)
   * Reason: Backend Express doesn't proxy WebSocket connections
   * @param {Function} onMessage - Message handler
   * @returns {WebSocket} WebSocket instance
   */
  createWebSocket(onMessage) {
    // WebSocket connects directly to Intelligence Engine (ws://localhost:8000)
    const intelligenceEngineUrl = import.meta.env.VITE_INTELLIGENCE_API_URL || 'http://localhost:8000'
    const wsUrl = `${intelligenceEngineUrl}/api/rag/ws`.replace('http', 'ws')
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('RAG WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        if (onMessage) onMessage(message)
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('RAG WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('RAG WebSocket disconnected')
    }

    return ws
  },

  /**
   * Format file size for display
   * @param {number} bytes - File size in bytes
   * @returns {string} Formatted file size
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  },

  /**
   * Get file type icon class
   * @param {string} filename - File name
   * @returns {string} Icon class
   */
  getFileIcon(filename) {
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
}

// Export default for convenience
export default ragApi