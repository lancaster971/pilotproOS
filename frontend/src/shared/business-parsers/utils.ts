/**
 * Shared Utility Functions
 * Common utilities used across all parsers
 */

/**
 * Clean HTML content - Single implementation for all components
 */
export function cleanHtmlContent(content: string): string {
  if (!content) return ''

  return content
    .replace(/<[^>]+>/g, ' ')           // Remove HTML tags
    .replace(/&[a-zA-Z0-9]+;/g, ' ')    // Remove HTML entities
    .replace(/\s+/g, ' ')                // Normalize whitespace
    .replace(/\n{3,}/g, '\n\n')          // Limit consecutive newlines
    .trim()
}

/**
 * Truncate text intelligently at word boundaries
 */
export function truncateText(text: string, maxLength: number = 150): string {
  if (!text || text.length <= maxLength) return text

  const truncated = text.substring(0, maxLength)
  const lastSpace = truncated.lastIndexOf(' ')

  return lastSpace > 0
    ? truncated.substring(0, lastSpace) + '...'
    : truncated + '...'
}

/**
 * Extract first meaningful line from text
 */
export function extractFirstLine(text: string): string {
  if (!text) return ''

  const lines = text.split('\n').filter(line => line.trim().length > 0)
  return lines[0] || ''
}

/**
 * Detect data type from content structure
 */
export function detectDataType(data: any): 'email' | 'ai' | 'order' | 'vector' | 'generic' {
  if (!data) return 'generic'

  // Email detection
  if (data.subject || data.oggetto || data.sender || data.mittente || data.email_body) {
    return 'email'
  }

  // AI response detection
  if (data.ai_response || data.risposta_html || data.output?.risposta_html ||
      data.chatResponse || data.gpt_response) {
    return 'ai'
  }

  // Order detection
  if (data.orderId || data.order_id || data.items || data.orderDetails) {
    return 'order'
  }

  // Vector search detection
  if (data.vector_results || data.similarity_search || data.embeddings) {
    return 'vector'
  }

  return 'generic'
}

/**
 * Format date consistently across the application
 */
export function formatBusinessDate(date: string | Date): string {
  if (!date) return ''

  const d = new Date(date)
  if (isNaN(d.getTime())) return ''

  return new Intl.DateTimeFormat('it-IT', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(d)
}

/**
 * Calculate confidence based on data completeness
 */
export function calculateConfidence(data: any): 'high' | 'medium' | 'low' {
  if (!data) return 'low'

  const fields = Object.keys(data).filter(key => data[key] !== null && data[key] !== undefined)
  const fieldCount = fields.length

  if (fieldCount > 5) return 'high'
  if (fieldCount > 2) return 'medium'
  return 'low'
}