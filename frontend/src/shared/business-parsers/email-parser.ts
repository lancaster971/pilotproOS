/**
 * Unified Email Parser
 * Single source of truth for email parsing logic
 */

import { BusinessParsingResult, EmailData } from './types'
import { cleanHtmlContent, truncateText, calculateConfidence } from './utils'

export class EmailParser {
  /**
   * Parse email data from any source format
   */
  static parse(data: any): BusinessParsingResult {
    const emailData = this.extractEmailData(data)
    const confidence = calculateConfidence(emailData)

    const details: string[] = []
    let summary = 'Email received'

    if (emailData.subject) {
      summary = `Email: ${truncateText(emailData.subject, 100)}`
      details.push(`Subject: ${emailData.subject}`)
    }

    if (emailData.sender) {
      details.push(`From: ${emailData.sender}`)
    }

    if (emailData.recipient) {
      details.push(`To: ${emailData.recipient}`)
    }

    if (emailData.body) {
      const cleanBody = cleanHtmlContent(emailData.body)
      const preview = truncateText(cleanBody, 200)
      if (preview) {
        details.push(`Content: ${preview}`)
      }
    }

    if (emailData.attachments && emailData.attachments.length > 0) {
      details.push(`Attachments: ${emailData.attachments.length} file(s)`)
    }

    return {
      summary,
      details,
      type: 'email',
      confidence,
      metadata: emailData,
      businessValue: this.extractBusinessValue(emailData)
    }
  }

  /**
   * Extract email data from various formats
   */
  private static extractEmailData(data: any): EmailData {
    if (!data) return {}

    const result: EmailData = {}

    // Handle nested json structure
    const jsonData = data.json || data

    // Subject extraction - multiple field names
    result.subject = jsonData.subject ||
                    jsonData.oggetto ||
                    jsonData.email_subject ||
                    jsonData.Subject ||
                    jsonData.title

    // Sender extraction
    result.sender = jsonData.sender ||
                   jsonData.mittente ||
                   jsonData.from ||
                   jsonData.From ||
                   jsonData.email_from ||
                   jsonData.sender_email

    // Recipient extraction
    result.recipient = jsonData.recipient ||
                      jsonData.destinatario ||
                      jsonData.to ||
                      jsonData.To ||
                      jsonData.email_to

    // Body extraction - check multiple possible fields
    result.body = jsonData.body ||
                 jsonData.email_body ||
                 jsonData.corpo ||
                 jsonData.message ||
                 jsonData.content ||
                 jsonData.text ||
                 jsonData.html ||
                 jsonData.email_content

    // Attachments extraction
    if (jsonData.attachments || jsonData.allegati) {
      result.attachments = jsonData.attachments || jsonData.allegati
    }

    // Timestamp extraction
    result.timestamp = jsonData.timestamp ||
                      jsonData.date ||
                      jsonData.received_at ||
                      jsonData.sent_at

    return result
  }

  /**
   * Extract business value from email
   */
  private static extractBusinessValue(emailData: EmailData): string {
    const indicators = []

    // Check for customer communication
    if (emailData.subject) {
      const subject = emailData.subject.toLowerCase()
      if (subject.includes('order') || subject.includes('ordine')) {
        indicators.push('Order-related')
      }
      if (subject.includes('support') || subject.includes('help') || subject.includes('assistenza')) {
        indicators.push('Support request')
      }
      if (subject.includes('urgent') || subject.includes('urgente')) {
        indicators.push('High priority')
      }
      if (subject.includes('invoice') || subject.includes('fattura')) {
        indicators.push('Financial')
      }
    }

    // Check sender domain for importance
    if (emailData.sender) {
      const sender = emailData.sender.toLowerCase()
      if (sender.includes('.com') || sender.includes('.it')) {
        const domain = sender.split('@')[1]
        if (domain) {
          if (domain.includes('google') || domain.includes('microsoft') || domain.includes('amazon')) {
            indicators.push('Major vendor')
          }
        }
      }
    }

    return indicators.length > 0
      ? indicators.join(', ')
      : 'Standard communication'
  }

  /**
   * Generate business-friendly summary
   */
  static generateSummary(emailData: EmailData): string {
    if (emailData.subject) {
      return `Processed email: "${truncateText(emailData.subject, 80)}"`
    }
    if (emailData.sender) {
      return `Email received from ${emailData.sender}`
    }
    return 'Email communication processed'
  }
}