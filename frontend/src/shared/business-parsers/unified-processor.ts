/**
 * Unified Business Data Processor
 * Central routing and processing for all business data types
 */

import { BusinessParsingResult, ProcessingContext } from './types'
import { EmailParser } from './email-parser'
import { AIResponseParser } from './ai-parser'
import { detectDataType, cleanHtmlContent, truncateText } from './utils'

export class UnifiedBusinessProcessor {
  private static cache = new Map<string, BusinessParsingResult>()

  /**
   * Process any business data through appropriate parser
   */
  static process(data: any, context?: ProcessingContext): BusinessParsingResult {
    // Check cache if execution ID is provided
    if (context?.executionId) {
      const cacheKey = `${context.executionId}-${JSON.stringify(data).substring(0, 50)}`
      if (this.cache.has(cacheKey)) {
        return this.cache.get(cacheKey)!
      }
    }

    // Detect data type and route to appropriate parser
    const dataType = detectDataType(data)
    let result: BusinessParsingResult

    switch (dataType) {
      case 'email':
        result = EmailParser.parse(data)
        break

      case 'ai':
        result = AIResponseParser.parse(data)
        break

      case 'order':
        result = this.parseOrderData(data)
        break

      case 'vector':
        result = this.parseVectorData(data)
        break

      default:
        result = this.parseGenericData(data)
    }

    // Add context information if provided
    if (context) {
      result.metadata = {
        ...result.metadata,
        source: context.source,
        nodeType: context.nodeType,
        workflowId: context.workflowId
      }
    }

    // Cache the result
    if (context?.executionId) {
      const cacheKey = `${context.executionId}-${JSON.stringify(data).substring(0, 50)}`
      this.cache.set(cacheKey, result)

      // Limit cache size
      if (this.cache.size > 100) {
        const firstKey = this.cache.keys().next().value
        this.cache.delete(firstKey)
      }
    }

    return result
  }

  /**
   * Parse order data
   */
  private static parseOrderData(data: any): BusinessParsingResult {
    const jsonData = data.json || data
    const details: string[] = []
    let summary = 'Order processed'

    if (jsonData.orderId || jsonData.order_id) {
      const orderId = jsonData.orderId || jsonData.order_id
      summary = `Order #${orderId}`
      details.push(`Order ID: ${orderId}`)
    }

    if (jsonData.customer || jsonData.customerName) {
      details.push(`Customer: ${jsonData.customer || jsonData.customerName}`)
    }

    if (jsonData.items && Array.isArray(jsonData.items)) {
      details.push(`Items: ${jsonData.items.length} product(s)`)

      // Add first few items
      jsonData.items.slice(0, 3).forEach((item: any) => {
        if (item.name || item.product) {
          details.push(`  • ${item.name || item.product}`)
        }
      })
    }

    if (jsonData.total || jsonData.totalAmount) {
      const total = jsonData.total || jsonData.totalAmount
      details.push(`Total: €${total}`)
    }

    if (jsonData.status || jsonData.orderStatus) {
      details.push(`Status: ${jsonData.status || jsonData.orderStatus}`)
    }

    return {
      summary,
      details,
      type: 'order',
      confidence: 'high',
      metadata: jsonData,
      businessValue: 'Customer transaction'
    }
  }

  /**
   * Parse vector/search data
   */
  private static parseVectorData(data: any): BusinessParsingResult {
    const jsonData = data.json || data
    const details: string[] = []
    let summary = 'Search completed'

    if (jsonData.query || jsonData.search_query) {
      const query = jsonData.query || jsonData.search_query
      summary = `Search: "${truncateText(query, 50)}"`
      details.push(`Query: ${query}`)
    }

    if (jsonData.results || jsonData.vector_results) {
      const results = jsonData.results || jsonData.vector_results
      if (Array.isArray(results)) {
        details.push(`Found: ${results.length} result(s)`)

        // Add top results
        results.slice(0, 3).forEach((result: any, index: number) => {
          const content = result.content || result.text || result.document
          if (content) {
            details.push(`  ${index + 1}. ${truncateText(content, 100)}`)
          }
        })
      }
    }

    if (jsonData.similarity_score || jsonData.score) {
      details.push(`Match score: ${jsonData.similarity_score || jsonData.score}`)
    }

    return {
      summary,
      details,
      type: 'vector',
      confidence: 'medium',
      metadata: jsonData,
      businessValue: 'Information retrieval'
    }
  }

  /**
   * Parse generic/unknown data
   */
  private static parseGenericData(data: any): BusinessParsingResult {
    const jsonData = data.json || data
    const details: string[] = []
    let summary = 'Data processed'

    // Try to extract meaningful information
    const keys = Object.keys(jsonData).filter(key =>
      jsonData[key] !== null &&
      jsonData[key] !== undefined &&
      key !== 'json'
    )

    // Use first non-empty string value as summary
    for (const key of keys) {
      const value = jsonData[key]
      if (typeof value === 'string' && value.length > 0) {
        summary = truncateText(cleanHtmlContent(value), 100)
        break
      }
    }

    // Add key details
    keys.slice(0, 5).forEach(key => {
      const value = jsonData[key]
      if (value !== null && value !== undefined) {
        if (typeof value === 'string') {
          details.push(`${key}: ${truncateText(value, 100)}`)
        } else if (typeof value === 'number') {
          details.push(`${key}: ${value}`)
        } else if (typeof value === 'boolean') {
          details.push(`${key}: ${value ? 'Yes' : 'No'}`)
        } else if (Array.isArray(value)) {
          details.push(`${key}: ${value.length} items`)
        } else if (typeof value === 'object') {
          details.push(`${key}: [Complex data]`)
        }
      }
    })

    return {
      summary,
      details: details.length > 0 ? details : ['Data processing completed'],
      type: 'generic',
      confidence: 'low',
      metadata: jsonData,
      businessValue: 'Business operation'
    }
  }

  /**
   * Clear the cache
   */
  static clearCache(): void {
    this.cache.clear()
  }

  /**
   * Get cache statistics
   */
  static getCacheStats(): { size: number; maxSize: number } {
    return {
      size: this.cache.size,
      maxSize: 100
    }
  }
}