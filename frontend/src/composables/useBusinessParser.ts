export interface ParsedBusinessData {
  summary: string
  details: string[]
  type: 'email' | 'ai' | 'order' | 'vector' | 'parcel' | 'reply' | 'workflow' | 'generic'
  confidence: 'high' | 'medium' | 'low'
}

export function useBusinessParser() {
  
  const sanitizeNodeType = (nodeType?: string): string => {
    if (!nodeType) return ''
    return nodeType
      .replace(/n8n/gi, 'WFEngine')
      .replace(/\.nodes\./g, '.engine.')
      .replace(/\.base\./g, '.core.')
  }

  const extractEmailData = (data: any): ParsedBusinessData | null => {
    if (!data?.json) return null

    const insights: string[] = []
    
    // Oggetto email
    const subject = data.json.oggetto || data.json.subject
    if (subject) {
      insights.push(`Oggetto: "${subject}"`)
    }
    
    // Mittente
    const senderFields = [
      data.json.mittente,
      data.json.mittente_nome,
      data.json.sender?.emailAddress?.address,
      data.sender?.emailAddress?.address
    ]
    const sender = senderFields.find(field => field)
    if (sender) {
      insights.push(`Da: ${sender}`)
    }
    
    // Contenuto email
    const emailBodyFields = [
      data.json.messaggio_cliente,
      data.json.messaggio,
      data.json.body?.content,
      data.json.body,
      data.json.content
    ]
    const emailBody = emailBodyFields.find(field => 
      field && typeof field === 'string' && field.length > 20
    )
    
    if (emailBody) {
      const cleanContent = emailBody
        .replace(/<[^>]+>/g, ' ')
        .replace(/&[a-zA-Z0-9]+;/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
      const preview = cleanContent.substring(0, 150)
      insights.push(`Messaggio: "${preview}${preview.length >= 150 ? '...' : ''}"`)
    }

    return insights.length > 0 ? {
      summary: 'Email ricevuta',
      details: insights,
      type: 'email',
      confidence: 'high'
    } : null
  }

  const extractAIData = (data: any): ParsedBusinessData | null => {
    if (!data?.json) return null

    const insights: string[] = []
    
    // Risposta AI
    const aiResponseFields = [
      data.json.output?.risposta_html,
      data.json.risposta_html,
      data.json.ai_response,
      data.json.response,
      data.json.output
    ]
    
    const aiResponse = aiResponseFields.find(field => 
      field && typeof field === 'string' && field.length > 20
    )
    
    if (aiResponse) {
      const cleanResponse = aiResponse
        .replace(/<[^>]+>/g, ' ')
        .replace(/&[a-zA-Z0-9]+;/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
      const preview = cleanResponse.substring(0, 200)
      insights.push(`Risposta: "${preview}${preview.length >= 200 ? '...' : ''}"`)
    }
    
    // Categoria/Classificazione
    if (data.json.categoria || data.json.classification) {
      insights.push(`Categoria: ${data.json.categoria || data.json.classification}`)
    }

    return insights.length > 0 ? {
      summary: 'Risposta AI generata',
      details: insights,
      type: 'ai',
      confidence: 'high'
    } : null
  }

  const extractOrderData = (data: any): ParsedBusinessData | null => {
    if (!data?.json) return null

    const insights: string[] = []
    
    if (data.json.order_reference) {
      insights.push(`Riferimento: ${data.json.order_reference}`)
    }
    if (data.json.customer_full_name) {
      insights.push(`Cliente: ${data.json.customer_full_name}`)
    }
    if (data.json.order_status) {
      insights.push(`Stato: ${data.json.order_status}`)
    }
    if (data.json.order_total_paid) {
      insights.push(`Totale: ${data.json.order_total_paid}`)
    }
    if (data.json.delivery_city) {
      insights.push(`Città consegna: ${data.json.delivery_city}`)
    }
    if (data.json.order_shipping_number) {
      insights.push(`Tracking: ${data.json.order_shipping_number}`)
    }

    return insights.length > 0 ? {
      summary: 'Dati ordine recuperati',
      details: insights,
      type: 'order',
      confidence: 'high'
    } : null
  }

  const extractVectorData = (data: any): ParsedBusinessData | null => {
    if (!data?.json) return null

    const insights: string[] = []
    
    if (data.json.matches || data.json.results) {
      const matches = data.json.matches || data.json.results
      const count = Array.isArray(matches) ? matches.length : 1
      insights.push(`Documenti trovati: ${count}`)
    }
    
    if (data.json.score || data.json.similarity) {
      insights.push(`Similarità: ${data.json.score || data.json.similarity}`)
    }
    
    if (data.json.content || data.json.text) {
      const content = data.json.content || data.json.text
      const preview = content.substring(0, 100)
      insights.push(`Contenuto: "${preview}${preview.length >= 100 ? '...' : ''}"`)
    }

    return insights.length > 0 ? {
      summary: 'Ricerca vettoriale completata',
      details: insights,
      type: 'vector',
      confidence: 'medium'
    } : null
  }

  const extractGenericData = (data: any): ParsedBusinessData => {
    const dataString = JSON.stringify(data)
    const insights: string[] = []
    
    // Cerca email
    const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g
    const emails = dataString.match(emailRegex)
    if (emails && emails.length > 0) {
      insights.push(`Email rilevata: ${emails[0]}`)
    }
    
    // Mostra chiavi principali
    const processData = Array.isArray(data) ? data[0] : data
    if (processData && typeof processData === 'object') {
      const keys = Object.keys(processData.json || processData)
      if (keys.length > 0) {
        insights.push(`Campi disponibili: ${keys.slice(0, 4).join(', ')}${keys.length > 4 ? '...' : ''}`)
      }
    }

    return {
      summary: 'Dati di processo',
      details: insights.length > 0 ? insights : ['Dati complessi disponibili'],
      type: 'generic',
      confidence: 'low'
    }
  }

  const parseBusinessData = (
    data: any, 
    dataType: 'input' | 'output', 
    nodeType?: string, 
    nodeName?: string
  ): ParsedBusinessData => {
    
    const sanitizedType = sanitizeNodeType(nodeType)
    const nodeNameLower = nodeName?.toLowerCase() || ''
    
    // Check for trigger nodes
    const isTriggerNode = sanitizedType?.includes('trigger') || 
                         sanitizedType?.includes('Trigger') ||
                         nodeNameLower.includes('ricezione') ||
                         nodeNameLower.includes('trigger')
    
    if (isTriggerNode && dataType === 'input') {
      return {
        summary: 'In attesa di eventi',
        details: ['In attesa di nuove email dal server Microsoft Outlook'],
        type: 'email',
        confidence: 'high'
      }
    }
    
    if (!data) {
      return {
        summary: 'Nessun dato',
        details: ['Nessun dato disponibile per questo step'],
        type: 'generic',
        confidence: 'high'
      }
    }

    // Process data
    const processData = Array.isArray(data) ? data[0] : data
    
    if (!processData || typeof processData !== 'object') {
      return {
        summary: 'Dato semplice',
        details: [String(processData) || 'Dato non strutturato'],
        type: 'generic',
        confidence: 'medium'
      }
    }

    // Try specific parsers based on node type/name
    const isEmailNode = nodeNameLower.includes('mail') || nodeNameLower.includes('ricezione')
    const isAINode = nodeNameLower.includes('milena') || nodeNameLower.includes('assistente') || nodeNameLower.includes('ai')
    const isOrderNode = nodeNameLower.includes('ordini') || nodeNameLower.includes('order')
    const isVectorNode = nodeNameLower.includes('qdrant') || nodeNameLower.includes('vector')

    if (isEmailNode && dataType === 'output') {
      const emailData = extractEmailData(processData)
      if (emailData) return emailData
    }
    
    if (isAINode && dataType === 'output') {
      const aiData = extractAIData(processData)
      if (aiData) return aiData
    }
    
    if (isOrderNode) {
      const orderData = extractOrderData(processData)
      if (orderData) return orderData
    }
    
    if (isVectorNode && dataType === 'output') {
      const vectorData = extractVectorData(processData)
      if (vectorData) return vectorData
    }

    // Fallback to generic parsing
    return extractGenericData(processData)
  }

  const formatBusinessData = (parsedData: ParsedBusinessData): string => {
    const header = `--- ${parsedData.summary.toUpperCase()} ---`
    const details = parsedData.details.join('\n')
    return `${header}\n${details}`
  }

  return {
    parseBusinessData,
    formatBusinessData,
    sanitizeNodeType
  }
}