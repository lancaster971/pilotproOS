/**
 * RAG (Retrieval-Augmented Generation) API Client
 * Following TODO-MILHENA-EXPERT.md specifications exactly
 */

import axios from 'axios'

// Base configuration
const RAG_API_BASE = process.env.VUE_APP_INTELLIGENCE_API_URL || 'http://localhost:8000'

// Create axios instance with default configuration
const ragApiClient = axios.create({
  baseURL: `${RAG_API_BASE}/api/rag`,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000 // 30 seconds timeout for file uploads
})

// Request interceptor for authentication
ragApiClient.interceptors.request.use((config) => {
  // Add auth token if available
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
ragApiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('RAG API Error:', error)

    // Handle specific error cases
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    } else if (error.response?.status === 413) {
      // Payload too large
      throw new Error('File size too large. Please use files smaller than 50MB.')
    } else if (error.response?.status === 422) {
      // Validation error
      const detail = error.response.data?.detail
      throw new Error(detail || 'Invalid request data')
    }

    throw error.response?.data || error
  }
)

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
    const config = {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 300000, // 5 minutes for large uploads
      ...options
    }

    return await ragApiClient.post('/documents', formData, config)
  },

  /**
   * List documents with filtering and pagination
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>} Documents list response
   */
  async listDocuments(params = {}) {
    const queryParams = new URLSearchParams()

    // Add all parameters
    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined) {
        queryParams.append(key, params[key])
      }
    })

    return await ragApiClient.get(`/documents?${queryParams.toString()}`)
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

    const config = {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }

    return await ragApiClient.put(`/documents/${docId}`, formData, config)
  },

  /**
   * Delete document
   * @param {string} docId - Document ID
   * @param {boolean} softDelete - Whether to soft delete (default: true)
   * @returns {Promise<Object>} Delete response
   */
  async deleteDocument(docId, softDelete = true) {
    const params = new URLSearchParams({ soft_delete: softDelete.toString() })
    return await ragApiClient.delete(`/documents/${docId}?${params.toString()}`)
  },

  /**
   * Perform semantic search
   * @param {Object} searchRequest - Search parameters
   * @returns {Promise<Object>} Search results
   */
  async searchDocuments(searchRequest) {
    return await ragApiClient.post('/search', searchRequest)
  },

  /**
   * Get RAG system statistics
   * @returns {Promise<Object>} System statistics
   */
  async getStatistics() {
    return await ragApiClient.get('/stats')
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

    const config = {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 600000, // 10 minutes for large imports
      ...options
    }

    return await ragApiClient.post('/bulk-import', formData, config)
  },

  /**
   * Force reindex all documents
   * @returns {Promise<Object>} Reindex response
   */
  async reindex() {
    return await ragApiClient.post('/reindex')
  },

  /**
   * Get single document by ID
   * @param {string} docId - Document ID
   * @returns {Promise<Object>} Document data
   */
  async getDocument(docId) {
    return await ragApiClient.get(`/documents/${docId}`)
  },

  /**
   * Export documents (placeholder for future implementation)
   * @param {Object} exportOptions - Export configuration
   * @returns {Promise<Blob>} Exported data
   */
  async exportDocuments(exportOptions = {}) {
    // TODO: Implement document export functionality
    const response = await ragApiClient.post('/export', exportOptions, {
      responseType: 'blob'
    })
    return response
  },

  /**
   * Get document content preview
   * @param {string} docId - Document ID
   * @param {number} maxLength - Maximum content length
   * @returns {Promise<Object>} Document preview
   */
  async getDocumentPreview(docId, maxLength = 500) {
    const params = new URLSearchParams({ max_length: maxLength.toString() })
    return await ragApiClient.get(`/documents/${docId}/preview?${params.toString()}`)
  },

  /**
   * Get document version history
   * @param {string} docId - Document ID
   * @returns {Promise<Object>} Version history
   */
  async getDocumentHistory(docId) {
    return await ragApiClient.get(`/documents/${docId}/history`)
  },

  /**
   * Restore document version
   * @param {string} docId - Document ID
   * @param {number} version - Version number to restore
   * @returns {Promise<Object>} Restore response
   */
  async restoreDocumentVersion(docId, version) {
    return await ragApiClient.post(`/documents/${docId}/restore/${version}`)
  },

  /**
   * Get similar documents
   * @param {string} docId - Document ID
   * @param {number} limit - Number of similar documents to return
   * @returns {Promise<Object>} Similar documents
   */
  async getSimilarDocuments(docId, limit = 5) {
    const params = new URLSearchParams({ limit: limit.toString() })
    return await ragApiClient.get(`/documents/${docId}/similar?${params.toString()}`)
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
    return await ragApiClient.get('/health')
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
   * @param {Function} onMessage - Message handler
   * @returns {WebSocket} WebSocket instance
   */
  createWebSocket(onMessage) {
    const wsUrl = `${RAG_API_BASE}/api/rag/ws`.replace('http', 'ws')
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