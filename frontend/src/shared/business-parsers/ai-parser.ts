/**
 * Unified AI Response Parser
 * Single source of truth for AI response parsing logic
 */

import { BusinessParsingResult, AIResponseData } from './types'
import { cleanHtmlContent, truncateText, calculateConfidence } from './utils'

export class AIResponseParser {
  /**
   * Parse AI response data from any source format
   */
  static parse(data: any): BusinessParsingResult {
    const aiData = this.extractAIData(data)
    const confidence = calculateConfidence(aiData)

    const details: string[] = []
    let summary = 'AI processing completed'

    // Extract and clean the response
    if (aiData.response) {
      const cleanResponse = cleanHtmlContent(aiData.response)
      summary = `AI: ${truncateText(cleanResponse, 100)}`
      details.push(`Response: ${truncateText(cleanResponse, 300)}`)
    }

    // Add prompt if available
    if (aiData.prompt) {
      details.push(`Prompt: ${truncateText(aiData.prompt, 150)}`)
    }

    // Add model info if available
    if (aiData.model) {
      details.push(`Model: ${aiData.model}`)
    }

    // Add token count if available
    if (aiData.tokens) {
      details.push(`Tokens used: ${aiData.tokens}`)
    }

    return {
      summary,
      details,
      type: 'ai',
      confidence,
      metadata: aiData,
      businessValue: this.extractBusinessValue(aiData)
    }
  }

  /**
   * Extract AI data from various formats
   */
  private static extractAIData(data: any): AIResponseData {
    if (!data) return {}

    const result: AIResponseData = {}

    // Handle nested json structure
    const jsonData = data.json || data

    // Response extraction - check multiple possible fields
    result.response = jsonData.ai_response ||
                     jsonData.risposta_html ||
                     jsonData.output?.risposta_html ||
                     jsonData.chatResponse ||
                     jsonData.gpt_response ||
                     jsonData.response ||
                     jsonData.answer ||
                     jsonData.output?.text ||
                     jsonData.completion ||
                     jsonData.generated_text ||
                     jsonData.ai_output

    // Prompt extraction
    result.prompt = jsonData.prompt ||
                   jsonData.question ||
                   jsonData.query ||
                   jsonData.input ||
                   jsonData.user_message ||
                   jsonData.domanda

    // Model extraction
    result.model = jsonData.model ||
                  jsonData.model_name ||
                  jsonData.ai_model ||
                  jsonData.llm_model ||
                  this.detectModelFromResponse(result.response)

    // Token count extraction
    if (jsonData.tokens || jsonData.token_count || jsonData.usage?.total_tokens) {
      result.tokens = jsonData.tokens ||
                     jsonData.token_count ||
                     jsonData.usage?.total_tokens
    }

    // Timestamp extraction
    result.timestamp = jsonData.timestamp ||
                      jsonData.created_at ||
                      jsonData.generated_at

    return result
  }

  /**
   * Detect AI model from response patterns
   */
  private static detectModelFromResponse(response: string | undefined): string {
    if (!response) return 'Unknown AI Model'

    const responseText = response.toLowerCase()

    if (responseText.includes('gpt-4') || responseText.includes('openai')) {
      return 'GPT-4'
    }
    if (responseText.includes('gpt-3')) {
      return 'GPT-3.5'
    }
    if (responseText.includes('claude')) {
      return 'Claude'
    }
    if (responseText.includes('gemini')) {
      return 'Gemini'
    }
    if (responseText.includes('llama')) {
      return 'LLaMA'
    }

    return 'AI Assistant'
  }

  /**
   * Extract business value from AI interaction
   */
  private static extractBusinessValue(aiData: AIResponseData): string {
    const indicators = []

    // Analyze response content for business indicators
    if (aiData.response) {
      const response = aiData.response.toLowerCase()

      if (response.includes('customer') || response.includes('cliente')) {
        indicators.push('Customer-focused')
      }
      if (response.includes('analysis') || response.includes('analisi')) {
        indicators.push('Data analysis')
      }
      if (response.includes('recommendation') || response.includes('suggest') || response.includes('consiglio')) {
        indicators.push('Strategic advice')
      }
      if (response.includes('report') || response.includes('summary') || response.includes('rapporto')) {
        indicators.push('Report generation')
      }
      if (response.includes('translation') || response.includes('traduzione')) {
        indicators.push('Translation service')
      }
    }

    // Check prompt for task type
    if (aiData.prompt) {
      const prompt = aiData.prompt.toLowerCase()

      if (prompt.includes('write') || prompt.includes('scrivi')) {
        indicators.push('Content creation')
      }
      if (prompt.includes('analyze') || prompt.includes('analizza')) {
        indicators.push('Analysis task')
      }
      if (prompt.includes('help') || prompt.includes('aiuto')) {
        indicators.push('Support task')
      }
    }

    // Token usage indicator
    if (aiData.tokens) {
      if (aiData.tokens > 1000) {
        indicators.push('Complex processing')
      } else if (aiData.tokens < 100) {
        indicators.push('Quick response')
      }
    }

    return indicators.length > 0
      ? indicators.join(', ')
      : 'AI processing task'
  }

  /**
   * Generate business-friendly summary
   */
  static generateSummary(aiData: AIResponseData): string {
    if (aiData.response) {
      const clean = cleanHtmlContent(aiData.response)
      return `AI generated: ${truncateText(clean, 80)}`
    }
    if (aiData.prompt) {
      return `AI processed: "${truncateText(aiData.prompt, 60)}"`
    }
    if (aiData.model) {
      return `${aiData.model} completed processing`
    }
    return 'AI task completed successfully'
  }

  /**
   * Check if response contains structured data
   */
  static hasStructuredData(aiData: AIResponseData): boolean {
    if (!aiData.response) return false

    const response = aiData.response

    // Check for JSON structure
    if (response.includes('{') && response.includes('}')) {
      try {
        JSON.parse(response)
        return true
      } catch {
        // Not valid JSON
      }
    }

    // Check for list/table structure
    if (response.includes('|') || response.includes('•') || response.includes('1.')) {
      return true
    }

    return false
  }
}