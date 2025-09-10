export interface ParsedBusinessData {
  summary: string
  details: string[]
  type: 'email' | 'ai' | 'order' | 'vector' | 'parcel' | 'reply' | 'workflow' | 'generic' | 'document' | 'dataset' | 'statistical' | 'error'
  confidence: 'high' | 'medium' | 'low'
}

export interface IntelligentSummary {
  type: 'document' | 'dataset' | 'statistical' | 'ai_generated' | 'email_batch' | 'api_response' | 'generic' | 'direct' | 'pre-processed'
  summaryType: 'document' | 'dataset' | 'emails' | 'api' | 'statistics' | 'ai' | 'generic' | 'direct'
  businessSummary?: {
    title: string
    description: string
    [key: string]: any
  }
  metrics?: Record<string, any>
  preview?: any
  businessInsight?: string
  statistics?: any
  dataQuality?: any
  visualization?: any
  recommendations?: string[]
  actions?: string[]
  fullDataAvailable?: boolean
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
    
    // Handle execution error nodes with complete n8n error details
    if (sanitizedType === 'execution_error' || nodeNameLower.includes('execution error')) {
      let errorSummary = 'Errore di Esecuzione';
      let errorDetails = ['Il workflow ha riscontrato un errore durante l\'esecuzione'];
      
      // Extract comprehensive n8n error details if available
      if (data && typeof data === 'object') {
        if (data.n8nErrorDetails || data.errorType) {
          const errorType = data.errorType || 'Unknown Error';
          const nodeName = data.failedNode || 'Unknown Node';
          const message = data.specificErrorMessage || 'Error details not available';
          const stackTrace = data.stackTrace;
          const httpCode = data.httpCode;
          const timestamp = data.errorTimestamp;
          
          errorSummary = `${errorType}: ${nodeName}`;
          
          errorDetails = [
            `Errore: ${message}`,
            `Nodo Fallito: ${nodeName}`,
            `Tipo Errore: ${errorType}`
          ];
          
          // Add HTTP code if available
          if (httpCode) {
            errorDetails.push(`Codice HTTP: ${httpCode}`);
          }
          
          // Add timestamp if available
          if (timestamp) {
            const date = new Date(timestamp);
            errorDetails.push(`Timestamp: ${date.toLocaleString('it-IT')}`);
          }
          
          // Add stack trace info (truncated for UI)
          if (stackTrace && stackTrace.includes('at ')) {
            const firstLine = stackTrace.split('\n')[0];
            errorDetails.push(`Stack: ${firstLine}`);
          }
          
          // Add resolution hints based on error type
          if (errorType === 'NodeApiError') {
            errorDetails.push('Suggerimento: Verificare connessioni API e credenziali');
          } else if (message.toLowerCase().includes('connection')) {
            errorDetails.push('Suggerimento: Controllare connettività di rete');
          } else if (message.toLowerCase().includes('auth')) {
            errorDetails.push('Suggerimento: Verificare le credenziali di autenticazione');
          }
        }
      }
      
      return {
        summary: errorSummary,
        details: errorDetails,
        type: 'error',
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

  const formatTimelineStepData = (
    inputData: any, 
    outputData: any, 
    nodeType?: string, 
    nodeName?: string
  ): { inputSummary: string; outputSummary: string; businessValue: string } => {
    
    const parsedInput = parseBusinessData(inputData, 'input', nodeType, nodeName)
    const parsedOutput = parseBusinessData(outputData, 'output', nodeType, nodeName)
    
    // Create detailed summaries for timeline display with full business content
    let inputSummary = parsedInput.details.length > 0 
      ? parsedInput.details.join(' • ')
      : parsedInput.summary
    
    let outputSummary = parsedOutput.details.length > 0 
      ? parsedOutput.details.join(' • ')
      : parsedOutput.summary
    
    // Extract real business content based on node type from raw data
    const nodeNameLower = nodeName?.toLowerCase() || ''
    
    // EMAIL NODES - Extract email content
    if (nodeNameLower.includes('mail') || nodeNameLower.includes('ricezione') || parsedOutput.type === 'email') {
      const emailContent = outputData?.body?.content || 
                          outputData?.json?.body?.content || 
                          outputData?.main?.json?.body?.content ||
                          inputData?.body?.content || 
                          inputData?.json?.body?.content ||
                          inputData?.main?.json?.body?.content
                          
      if (emailContent && typeof emailContent === 'string') {
        // Improved HTML cleaning for human readability
        let cleanContent = emailContent
          // Remove HTML tags completely
          .replace(/<script[^>]*>.*?<\/script>/gi, '')
          .replace(/<style[^>]*>.*?<\/style>/gi, '')
          .replace(/<[^>]+>/g, ' ')
          // Decode HTML entities
          .replace(/&nbsp;/g, ' ')
          .replace(/&amp;/g, '&')
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&quot;/g, '"')
          .replace(/&#039;/g, "'")
          .replace(/&[a-zA-Z0-9]+;/g, ' ')
          // Clean whitespace
          .replace(/\r\n/g, ' ')
          .replace(/\n/g, ' ')
          .replace(/\t/g, ' ')
          .replace(/\s+/g, ' ')
          .trim()
        
        if (cleanContent.length > 20) {
          // Extract meaningful content, not HTML metadata
          // Skip if it's just HTML boilerplate
          if (!cleanContent.toLowerCase().includes('content-type') && 
              !cleanContent.toLowerCase().includes('charset') &&
              !cleanContent.toLowerCase().includes('viewport')) {
            const preview = cleanContent.length > 150 ? cleanContent.substring(0, 150) + '...' : cleanContent
            outputSummary = `Email received: "${preview}"`
          } else {
            // Try to extract email metadata instead
            const subject = outputData?.oggetto || outputData?.json?.oggetto || inputData?.oggetto || inputData?.json?.oggetto
            const sender = outputData?.mittente || outputData?.json?.mittente || inputData?.mittente || inputData?.json?.mittente
            if (subject && sender) {
              outputSummary = `Email from ${sender} - Subject: "${subject}"`
            } else if (subject) {
              outputSummary = `Email received - Subject: "${subject}"`
            } else {
              outputSummary = `Customer email received and processed`
            }
          }
        }
      }
      
      // Email response nodes - get the sent email content
      if (nodeNameLower.includes('rispond')) {
        const responseContent = outputData?.body?.content || outputData?.json?.body?.content
        if (responseContent && typeof responseContent === 'string') {
          const cleanResponse = responseContent.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim()
          const preview = cleanResponse.length > 200 ? cleanResponse.substring(0, 200) + '...' : cleanResponse
          outputSummary = `Email sent: "${preview}"`
        }
      }
    }
    
    // AI AGENT NODES - Extract AI response
    else if (nodeNameLower.includes('milena') || nodeNameLower.includes('assistente') || nodeType === 'ai_agent') {
      const aiResponse = outputData?.output?.risposta_html || 
                        outputData?.json?.output?.risposta_html ||
                        outputData?.response || 
                        outputData?.json?.response ||
                        outputData?.main?.json?.output?.risposta_html
                        
      if (aiResponse && typeof aiResponse === 'string') {
        const cleanResponse = aiResponse.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim()
        const preview = cleanResponse.length > 200 ? cleanResponse.substring(0, 200) + '...' : cleanResponse
        outputSummary = `AI Response: "${preview}"`
      }
    }
    
    // VECTOR SEARCH NODES - Extract search results
    else if (nodeNameLower.includes('qdrant') || nodeNameLower.includes('vector') || nodeType === 'vector_search') {
      const searchResults = outputData?.ai_tool?.json?.response || 
                           outputData?.json?.response ||
                           outputData?.response ||
                           outputData?.main?.ai_tool?.json?.response
                           
      if (searchResults && Array.isArray(searchResults)) {
        const resultCount = searchResults.length
        const firstResult = searchResults[0]
        if (firstResult && typeof firstResult.text === 'string') {
          try {
            const parsedResult = JSON.parse(firstResult.text)
            const content = parsedResult.pageContent || parsedResult.content
            if (content) {
              const preview = content.length > 150 ? content.substring(0, 150) + '...' : content
              outputSummary = `Found ${resultCount} documents: "${preview}"`
            }
          } catch (e) {
            outputSummary = `Found ${resultCount} search results`
          }
        } else {
          outputSummary = `Found ${resultCount} search results`
        }
      }
    }
    
    // ORDER/PARCEL LOOKUP NODES - Extract order info
    else if (nodeNameLower.includes('ordini') || nodeNameLower.includes('parcel') || nodeType === 'order_lookup' || nodeType === 'parcel_tracking') {
      const orderData = outputData?.json || outputData?.main?.json || outputData
      
      if (orderData) {
        const details = []
        if (orderData.order_reference) details.push(`Order: ${orderData.order_reference}`)
        if (orderData.customer_full_name) details.push(`Customer: ${orderData.customer_full_name}`)
        if (orderData.order_status) details.push(`Status: ${orderData.order_status}`)
        if (orderData.tracking_number) details.push(`Tracking: ${orderData.tracking_number}`)
        if (orderData.delivery_status) details.push(`Delivery: ${orderData.delivery_status}`)
        
        if (details.length > 0) {
          outputSummary = details.join(' • ')
        }
      }
    }
    
    // SUB-WORKFLOW NODES - Extract workflow execution info
    else if (nodeNameLower.includes('execute') || nodeNameLower.includes('workflow') || nodeType === 'sub_workflow') {
      const workflowResult = outputData?.json || outputData?.main?.json || outputData
      
      if (workflowResult) {
        const details = []
        if (workflowResult.workflow_name) details.push(`Workflow: ${workflowResult.workflow_name}`)
        if (workflowResult.execution_status) details.push(`Status: ${workflowResult.execution_status}`)
        if (workflowResult.duration) details.push(`Duration: ${workflowResult.duration}ms`)
        if (workflowResult.nodes_executed) details.push(`Nodes: ${workflowResult.nodes_executed}`)
        
        if (details.length > 0) {
          outputSummary = details.join(' • ')
        } else {
          outputSummary = `Sub-workflow executed successfully`
        }
      }
    }
    
    // Limit summary lengths for UI display
    if (inputSummary.length > 150) {
      inputSummary = inputSummary.substring(0, 150) + '...'
    }
    if (outputSummary.length > 250) {
      outputSummary = outputSummary.substring(0, 250) + '...'
    }
    
    // Generate business value based on node type and data
    const businessValue = generateBusinessValue(parsedInput, parsedOutput, nodeType, nodeName)
    
    return {
      inputSummary,
      outputSummary,
      businessValue
    }
  }

  const generateBusinessValue = (
    parsedInput: ParsedBusinessData,
    parsedOutput: ParsedBusinessData,
    nodeType?: string,
    nodeName?: string
  ): string => {
    
    const nodeNameLower = nodeName?.toLowerCase() || ''
    
    // AI nodes
    if (nodeNameLower.includes('milena') || nodeNameLower.includes('assistente') || parsedOutput.type === 'ai') {
      return 'Risposta intelligente generata per il cliente'
    }
    
    // Email nodes
    if (nodeNameLower.includes('mail') || nodeNameLower.includes('ricezione') || parsedOutput.type === 'email') {
      if (nodeNameLower.includes('ricezione')) {
        return 'Email cliente acquisita nel sistema'
      } else {
        return 'Comunicazione inviata al cliente'
      }
    }
    
    // Database/Storage nodes
    if (nodeNameLower.includes('supabase') || nodeNameLower.includes('database') || parsedOutput.type === 'order') {
      return 'Dati salvati nel sistema aziendale'
    }
    
    // Processing nodes
    if (nodeNameLower.includes('extractor') || nodeNameLower.includes('parser')) {
      return 'Informazioni estratte e processate'
    }
    
    // HTTP/API nodes
    if (nodeType?.includes('http') || nodeNameLower.includes('api')) {
      return 'Integrazione esterna completata'
    }
    
    // Generic value
    return 'Operazione completata con successo'
  }

  const parseIntelligentSummary = (summary: IntelligentSummary): ParsedBusinessData => {
    // Convert intelligent summary to parsed business data format
    const details: string[] = []
    
    // Add business summary as primary detail
    if (summary.businessSummary) {
      details.push(summary.businessSummary.description)
      
      // Add specific details based on summary type
      if (summary.summaryType === 'document' && summary.businessSummary.pageCount) {
        details.push(`Pages: ${summary.businessSummary.pageCount}`)
      }
      if (summary.summaryType === 'dataset') {
        if (summary.businessSummary.totalRows) {
          details.push(`Rows: ${summary.businessSummary.totalRows}`)
        }
        if (summary.businessSummary.totalColumns) {
          details.push(`Columns: ${summary.businessSummary.totalColumns}`)
        }
      }
    }
    
    // Add key metrics
    if (summary.metrics) {
      Object.entries(summary.metrics).slice(0, 3).forEach(([key, value]) => {
        details.push(`${key}: ${value}`)
      })
    }
    
    // Add business insight
    if (summary.businessInsight) {
      details.push(`Insight: ${summary.businessInsight}`)
    }
    
    // Map summary type to ParsedBusinessData type
    let dataType: ParsedBusinessData['type'] = 'generic'
    switch (summary.summaryType) {
      case 'document':
        dataType = 'document'
        break
      case 'dataset':
        dataType = 'dataset'
        break
      case 'emails':
        dataType = 'email'
        break
      case 'statistics':
        dataType = 'statistical'
        break
      case 'ai':
        dataType = 'ai'
        break
    }
    
    return {
      summary: summary.businessSummary?.title || 'Process Data',
      details,
      type: dataType,
      confidence: summary.type === 'ai_generated' ? 'medium' : 'high'
    }
  }

  const formatIntelligentData = (summary: IntelligentSummary): string => {
    const parsed = parseIntelligentSummary(summary)
    return formatBusinessData(parsed)
  }

  return {
    parseBusinessData,
    formatBusinessData,
    formatTimelineStepData,
    sanitizeNodeType,
    parseIntelligentSummary,
    formatIntelligentData
  }
}