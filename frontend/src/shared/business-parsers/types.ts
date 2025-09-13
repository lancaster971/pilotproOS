/**
 * Shared Business Data Types
 * Unified types for all business data parsing across frontend and backend
 */

export interface BusinessParsingResult {
  summary: string
  details: string[]
  type: 'email' | 'ai' | 'order' | 'vector' | 'generic'
  confidence: 'high' | 'medium' | 'low'
  metadata?: Record<string, any>
  timestamp?: string
  businessValue?: string
}

export interface ProcessingContext {
  source: 'frontend' | 'backend'
  nodeType?: string
  executionId?: string
  workflowId?: string
}

export interface CompressedSummary {
  original_size: number
  compressed_size: number
  summary: string
  key_points: string[]
  compression_ratio: number
  data_type: string
}

export interface EmailData {
  subject?: string
  sender?: string
  recipient?: string
  body?: string
  attachments?: any[]
  timestamp?: string
}

export interface AIResponseData {
  prompt?: string
  response?: string
  model?: string
  tokens?: number
  timestamp?: string
}

export interface OrderData {
  orderId?: string
  customer?: string
  items?: any[]
  total?: number
  status?: string
  timestamp?: string
}