/**
 * Business Step Parser
 *
 * Port della logica humanizeStepData dal frontend_old
 * Trasforma dati tecnici n8n in descrizioni business-friendly
 */

// Temporarily disabled - path issue in Docker container
// import { UnifiedBusinessProcessor } from '../../../frontend/src/shared/business-parsers/unified-processor.js';
// import { cleanHtmlContent, truncateText } from '../../../frontend/src/shared/business-parsers/utils.js';

/**
 * Converte dati JSON complessi in descrizioni human-readable per business
 * @param {any} data - Dati del nodo (input o output)
 * @param {'input' | 'output'} dataType - Tipo di dati
 * @param {string} nodeType - Tipo tecnico del nodo
 * @param {string} nodeName - Nome del nodo
 * @returns {string} Descrizione business-friendly
 */
export function humanizeStepData(data, dataType, nodeType, nodeName) {
  // Sanitizza nodeType per rimuovere riferimenti a n8n
  const sanitizedType = nodeType?.replace(/n8n/gi, 'WFEngine').replace(/\.nodes\./g, '.engine.').replace(/\.base\./g, '.core.');

  // LOGICA SPECIALE PER TRIGGER NODES
  const isTriggerNode = sanitizedType?.includes('trigger') ||
                       sanitizedType?.includes('Trigger') ||
                       nodeName?.toLowerCase().includes('ricezione') ||
                       nodeName?.toLowerCase().includes('trigger');

  // Per nodi trigger, l'input è sempre "In attesa di dati"
  if (isTriggerNode && dataType === 'input') {
    return 'In attesa di nuove email dal server Microsoft Outlook';
  }

  if (!data) return 'Nessun dato disponibile';

  // Temporarily disabled - path issue in Docker container
  // try {
  //   const result = UnifiedBusinessProcessor.process(data, {
  //     source: 'backend',
  //     nodeType: sanitizedType
  //   });

  //   // Format the result for legacy compatibility
  //   if (result.details && result.details.length > 0) {
  //     return result.details.join('\n');
  //   }
  //   return result.summary;
  // } catch (err) {
  //   // Fallback to legacy parsing if unified processor fails
  //   console.log('Unified processor fallback, using legacy parser');
  // }

  // Se è un array, prendi il primo elemento
  const processData = Array.isArray(data) ? data[0] : data;
  
  if (!processData || typeof processData !== 'object') {
    return String(processData) || 'Dato non strutturato';
  }

  const dataString = JSON.stringify(processData);
  const insights = [];
  
  // Determina il tipo di nodo per personalizzare il parsing
  const nodeNameLower = nodeName?.toLowerCase() || '';
  const isEmailNode = nodeNameLower.includes('mail') || nodeNameLower.includes('ricezione');
  const isAINode = nodeNameLower.includes('milena') || nodeNameLower.includes('assistente') || nodeNameLower.includes('ai');
  const isOrderNode = nodeNameLower.includes('ordini') || nodeNameLower.includes('order');
  const isVectorNode = nodeNameLower.includes('qdrant') || nodeNameLower.includes('vector');
  const isParcelNode = nodeNameLower.includes('parcel');
  const isReplyNode = nodeNameLower.includes('rispondi') || nodeNameLower.includes('reply');
  const isExecuteNode = nodeNameLower.includes('execute') || nodeNameLower.includes('workflow');
  
  // PARSER SPECIFICI PER TIPO DI NODO
  
  // 1. NODO EMAIL (Ricezione Mail)
  if (isEmailNode && dataType === 'output') {
    insights.push('--- EMAIL RICEVUTA ---');
    
    // Oggetto
    if (processData.json?.oggetto || processData.json?.subject) {
      insights.push(`Oggetto: "${processData.json?.oggetto || processData.json?.subject}"`);
    }
    
    // Mittente
    const senderFields = [
      processData.json?.mittente,
      processData.json?.mittente_nome,
      processData.json?.sender?.emailAddress?.address,
      processData.sender?.emailAddress?.address
    ];
    const sender = senderFields.find(field => field);
    if (sender) {
      insights.push(`Da: ${sender}`);
    }
    
    // Contenuto
    const emailBodyFields = [
      processData.json?.messaggio_cliente,
      processData.json?.messaggio,
      processData.json?.body?.content,
      processData.json?.body,
      processData.json?.content
    ];
    const emailBody = emailBodyFields.find(field => 
      field && typeof field === 'string' && field.length > 20
    );
    if (emailBody) {
      const cleanContent = emailBody
        .replace(/<[^>]+>/g, ' ')
        .replace(/&[a-zA-Z0-9]+;/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
      const preview = cleanContent.substring(0, 150);
      insights.push(`Messaggio: "${preview}${preview.length >= 150 ? '...' : ''}"`);
    }
  }
  
  // 2. NODO AI ASSISTANT (Milena)
  else if (isAINode && dataType === 'output') {
    insights.push('--- RISPOSTA AI GENERATA ---');
    
    const aiResponseFields = [
      processData.json?.output?.risposta_html,
      processData.json?.risposta_html,
      processData.json?.ai_response,
      processData.json?.response,
      processData.json?.output
    ];
    
    const aiResponse = aiResponseFields.find(field => 
      field && typeof field === 'string' && field.length > 20
    );
    
    if (aiResponse) {
      const cleanResponse = aiResponse
        .replace(/<[^>]+>/g, ' ')
        .replace(/&[a-zA-Z0-9]+;/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
      const preview = cleanResponse.substring(0, 200);
      insights.push(`Risposta: "${preview}${preview.length >= 200 ? '...' : ''}"`);
    }
    
    // Categoria se presente
    if (processData.json?.categoria || processData.json?.classification) {
      insights.push(`Categoria: ${processData.json?.categoria || processData.json?.classification}`);
    }
  }
  
  // 3. NODO VECTOR STORE (Qdrant)
  else if (isVectorNode && dataType === 'output') {
    insights.push('--- RICERCA VETTORIALE ---');
    
    if (processData.json?.matches || processData.json?.results) {
      const matches = processData.json?.matches || processData.json?.results;
      const count = Array.isArray(matches) ? matches.length : 1;
      insights.push(`Documenti trovati: ${count}`);
    }
    
    if (processData.json?.score || processData.json?.similarity) {
      insights.push(`Similarità: ${processData.json?.score || processData.json?.similarity}`);
    }
    
    if (processData.json?.content || processData.json?.text) {
      const content = processData.json?.content || processData.json?.text;
      const preview = content.substring(0, 100);
      insights.push(`Contenuto: "${preview}${preview.length >= 100 ? '...' : ''}"`);
    }
  }
  
  // 4. NODO PARCEL APP
  else if (isParcelNode && dataType === 'output') {
    insights.push('--- TRACKING SPEDIZIONE ---');
    
    if (processData.json?.tracking_number) {
      insights.push(`Numero tracking: ${processData.json.tracking_number}`);
    }
    if (processData.json?.status) {
      insights.push(`Stato: ${processData.json.status}`);
    }
    if (processData.json?.location) {
      insights.push(`Posizione: ${processData.json.location}`);
    }
    if (processData.json?.estimated_delivery) {
      insights.push(`Consegna prevista: ${processData.json.estimated_delivery}`);
    }
  }
  
  // 5. NODO RISPOSTA EMAIL
  else if (isReplyNode && dataType === 'output') {
    insights.push('--- EMAIL INVIATA ---');
    
    if (processData.json?.to) {
      insights.push(`Destinatario: ${processData.json.to}`);
    }
    if (processData.json?.subject) {
      insights.push(`Oggetto: ${processData.json.subject}`);
    }
    if (processData.json?.sent || processData.json?.success) {
      insights.push(`Stato: Email inviata con successo`);
    }
  }
  
  // 6. NODO EXECUTE WORKFLOW
  else if (isExecuteNode && dataType === 'output') {
    insights.push('--- WORKFLOW ESEGUITO ---');
    
    if (processData.json?.workflowId) {
      insights.push(`Workflow ID: ${processData.json.workflowId}`);
    }
    if (processData.json?.executionId) {
      insights.push(`Execution ID: ${processData.json.executionId}`);
    }
    if (processData.json?.status) {
      insights.push(`Stato: ${processData.json.status}`);
    }
  }
  
  // Se non abbiamo insights specifici, prova i parser generici

  // PRIORITÀ 4: DATI ORDINE (per nodi tipo INFO ORDINI)
  if (processData.json?.order_reference || processData.json?.orderFound) {
    insights.push('--- DATI ORDINE RECUPERATI ---');
    
    if (processData.json?.order_reference) {
      insights.push(`Riferimento: ${processData.json.order_reference}`);
    }
    if (processData.json?.customer_full_name) {
      insights.push(`Cliente: ${processData.json.customer_full_name}`);
    }
    if (processData.json?.order_status) {
      insights.push(`Stato: ${processData.json.order_status}`);
    }
    if (processData.json?.order_total_paid) {
      insights.push(`Totale: ${processData.json.order_total_paid}`);
    }
    if (processData.json?.delivery_city) {
      insights.push(`Città consegna: ${processData.json.delivery_city}`);
    }
    if (processData.json?.order_shipping_number) {
      insights.push(`Tracking: ${processData.json.order_shipping_number}`);
    }
    if (processData.json?.chatbotResponse) {
      const cleanResponse = processData.json.chatbotResponse.replace(/[✅❌📦]/g, '').trim();
      insights.push(`Risposta: ${cleanResponse}`);
    }
  }

  // PRIORITÀ 5: RISPOSTA AI (se presente)
  const aiResponseFields = [
    processData.json?.output?.risposta_html,
    processData.json?.risposta_html,
    processData.json?.ai_response,
    processData.json?.response
  ];
  
  const aiResponse = aiResponseFields.find(field => 
    field && typeof field === 'string' && field.length > 20
  );
  
  if (aiResponse && insights.length === 0) {
    const cleanResponse = aiResponse
      .replace(/<[^>]+>/g, ' ')
      .replace(/&[a-zA-Z0-9]+;/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
    const preview = cleanResponse.substring(0, 150);
    insights.push(`Risposta AI: "${preview}${preview.length >= 150 ? '...' : ''}"`);
  }

  // PRIORITÀ 6: CLASSIFICAZIONE/CATEGORIA (se utile)
  if (processData.json?.output?.categoria && processData.json?.output?.confidence) {
    insights.push(`Classificazione: ${processData.json.output.categoria} (${processData.json.output.confidence} confidence)`);
  } else if (processData.json?.categoria && processData.json?.confidence) {
    insights.push(`Classificazione: ${processData.json.categoria} (${processData.json.confidence}% confidence)`);
  }

  // PRIORITÀ 7: ORDER ID (se specifico)
  if (processData.json?.output?.order_id && processData.json.output.order_id !== '000000') {
    insights.push(`Ordine: ${processData.json.output.order_id}`);
  } else if (processData.json?.order_id && processData.json.order_id !== '000000') {
    insights.push(`Ordine: ${processData.json.order_id}`);
  }

  // FALLBACK: Se non troviamo contenuti email, mostra dati generici
  if (insights.length === 0) {
    // Cerca almeno email e subject base
    const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
    const emails = dataString.match(emailRegex);
    if (emails && emails.length > 0) {
      insights.push(`Email rilevata: ${emails[0]}`);
    }
    
    // Mostra le chiavi principali come fallback
    const keys = Object.keys(processData.json || processData);
    if (keys.length > 0) {
      insights.push(`Campi disponibili: ${keys.slice(0, 4).join(', ')}${keys.length > 4 ? '...' : ''}`);
    } else {
      return 'Dati complessi - espandi per visualizzare dettagli completi';
    }
  }

  return insights.join('\n');
}

/**
 * Genera un report dettagliato in formato testo per export
 * @param {object} timelineData - Dati timeline completi
 * @param {string} workflowId - ID del workflow
 * @param {string} tenantId - ID del tenant
 * @returns {string} Report formattato
 */
export function generateDetailedReport(timelineData, workflowId, tenantId) {
  if (!timelineData) return '';
  
  let report = `╔${'═'.repeat(78)}╗\n`;
  report += `║${' '.repeat(20)}REPORT DETTAGLIATO ESECUZIONE WORKFLOW${' '.repeat(20)}║\n`;
  report += `║${' '.repeat(25)}PilotPro Control Center v2.4.1${' '.repeat(24)}║\n`;
  report += `╚${'═'.repeat(78)}╝\n\n`;
  
  // SEZIONE 1: INFORMAZIONI GENERALI
  report += `┌─ INFORMAZIONI GENERALI ${'─'.repeat(54)}┐\n\n`;
  
  report += `  Nome Workflow:     ${timelineData.processName || 'Non specificato'}\n`;
  report += `  ID Workflow:       ${workflowId}\n`;
  report += `  Stato Workflow:    ${timelineData.status === 'active' ? 'ATTIVO' : 'INATTIVO'}\n`;
  
  if (timelineData.lastExecution) {
    report += `\n  ULTIMA ESECUZIONE:\n`;
    report += `  ├─ ID Esecuzione:  ${timelineData.lastExecution.id}\n`;
    report += `  ├─ Data/Ora:       ${new Date(timelineData.lastExecution.executedAt).toLocaleString('it-IT')}\n`;
    report += `  ├─ Durata Totale:  ${formatDuration(timelineData.lastExecution.duration)}\n`;
    report += `  └─ Status:         ${timelineData.lastExecution.status || 'Completato'}\n`;
  }
  
  report += `\n└${'─'.repeat(78)}┘\n\n`;
  
  // SEZIONE 2: CONTESTO BUSINESS DETTAGLIATO
  if (timelineData.businessContext && Object.keys(timelineData.businessContext).length > 0) {
    report += `┌─ ANALISI CONTESTO BUSINESS ${'─'.repeat(49)}┐\n\n`;
    
    report += `  Questo workflow ha processato una comunicazione business con i seguenti\n`;
    report += `  parametri identificati automaticamente dal sistema AI:\n\n`;
    
    if (timelineData.businessContext.senderEmail) {
      report += `  MITTENTE EMAIL:\n`;
      report += `     Email: ${timelineData.businessContext.senderEmail}\n`;
      report += `     Tipo: ${timelineData.businessContext.senderEmail.includes('@') ? 'Email valida' : 'Formato non standard'}\n\n`;
    }
    
    if (timelineData.businessContext.subject) {
      report += `  OGGETTO COMUNICAZIONE:\n`;
      report += `     "${timelineData.businessContext.subject}"\n\n`;
    }
    
    if (timelineData.businessContext.orderId) {
      report += `  RIFERIMENTO ORDINE:\n`;
      report += `     ID Ordine: ${timelineData.businessContext.orderId}\n`;
      report += `     Formato: ${timelineData.businessContext.orderId.length > 10 ? 'ID Esteso' : 'ID Standard'}\n\n`;
    }
    
    if (timelineData.businessContext.classification) {
      report += `  CLASSIFICAZIONE AI:\n`;
      report += `     Categoria Identificata: ${timelineData.businessContext.classification}\n`;
      if (timelineData.businessContext.confidence) {
        report += `     Livello di Confidenza: ${timelineData.businessContext.confidence}%\n`;
        const confidenceLevel = timelineData.businessContext.confidence > 80 ? 'ALTA' : 
                                timelineData.businessContext.confidence > 60 ? 'MEDIA' : 'BASSA';
        report += `     Affidabilità: ${confidenceLevel}\n`;
      }
      report += `\n`;
    }
    
    report += `└${'─'.repeat(78)}┘\n\n`;
  }
  
  // SEZIONE 3: TIMELINE DETTAGLIATA DELL'ESECUZIONE
  if (timelineData.timeline && timelineData.timeline.length > 0) {
    report += `┌─ TIMELINE DETTAGLIATA ESECUZIONE ${'─'.repeat(43)}┐\n\n`;
    
    report += `  Il workflow ha eseguito ${timelineData.timeline.length} operazioni in sequenza.\n`;
    report += `  Di seguito il dettaglio completo di ogni passaggio:\n\n`;
    
    timelineData.timeline.forEach((step, index) => {
      const stepNumber = index + 1;
      const isLastStep = index === timelineData.timeline.length - 1;
      
      // Header dello step con formatting avanzato
      report += `  ${'═'.repeat(74)}\n`;
      report += `  STEP ${stepNumber}/${timelineData.timeline.length}: ${step.nodeName.toUpperCase()}\n`;
      report += `  ${'═'.repeat(74)}\n\n`;
      
      // Informazioni tecniche dello step
      report += `  INFORMAZIONI TECNICHE:\n`;
      const sanitizedNodeType = (step.nodeType || 'Tipo non specificato')
        .replace(/n8n/gi, 'WFEngine')
        .replace(/\.nodes\./g, '.engine.')
        .replace(/\.base\./g, '.core.');
      report += `  ├─ Tipo Nodo:        ${sanitizedNodeType}\n`;
      report += `  ├─ Status:           ${step.status === 'success' ? 'SUCCESSO' : 
                                           step.status === 'error' ? 'ERRORE' : 
                                           step.status === 'not-executed' ? 'NON ESEGUITO' : 
                                           (step.status || 'Sconosciuto').toUpperCase()}\n`;
      
      if (step.executionTime !== undefined) {
        report += `  ├─ Tempo Esecuzione: ${formatDuration(step.executionTime)}\n`;
        
        // Analisi performance
        if (step.executionTime > 5000) {
          report += `  │  Nota: Questo step ha richiesto più di 5 secondi\n`;
        } else if (step.executionTime < 100) {
          report += `  │  Nota: Esecuzione ultra-rapida\n`;
        }
      }
      
      if (step.summary) {
        report += `  └─ Sommario:         ${step.summary}\n`;
      }
      
      // DATI IN INPUT - ULTRA DETTAGLIATI
      report += `\n  DATI IN INPUT:\n`;
      if (step.inputData) {
        const inputSummary = humanizeStepData(step.inputData, 'input', step.nodeType, step.nodeName);
        report += `  Sommario leggibile:\n`;
        const inputLines = inputSummary.split('\n');
        inputLines.forEach(line => {
          if (line.trim()) {
            report += `    ${line}\n`;
          }
        });
      } else {
        report += `     Nessun dato in input per questo step\n`;
      }
      
      // DATI IN OUTPUT - ULTRA DETTAGLIATI  
      report += `\n  DATI IN OUTPUT:\n`;
      if (step.outputData) {
        const outputSummary = humanizeStepData(step.outputData, 'output', step.nodeType, step.nodeName);
        report += `  Sommario leggibile:\n`;
        const outputLines = outputSummary.split('\n');
        outputLines.forEach(line => {
          if (line.trim()) {
            report += `    ${line}\n`;
          }
        });
      } else {
        report += `     Nessun dato in output per questo step\n`;
      }
      
      if (!isLastStep) {
        report += `\n  --> Prosegue con lo step successivo...\n\n`;
      } else {
        report += `\n  [COMPLETATO] Fine dell'esecuzione\n\n`;
      }
    });
    
    report += `└${'─'.repeat(78)}┘\n\n`;
  }
  
  // SEZIONE 4: ANALISI STATISTICA
  if (timelineData.stats) {
    report += `┌─ ANALISI STATISTICA ESECUZIONE ${'─'.repeat(45)}┐\n\n`;
    
    const { totalSteps, successSteps, errorSteps, totalDuration } = timelineData.stats;
    
    report += `  RIEPILOGO STEPS:\n`;
    report += `     Totale Steps:        ${totalSteps}\n`;
    report += `     Steps Completati:    ${successSteps} (${totalSteps > 0 ? ((successSteps/totalSteps)*100).toFixed(1) : 0}%)\n`;
    report += `     Steps con Errori:    ${errorSteps} (${totalSteps > 0 ? ((errorSteps/totalSteps)*100).toFixed(1) : 0}%)\n`;
    
    if (totalDuration > 0) {
      const avgTime = totalDuration / totalSteps;
      report += `\n  ANALISI TEMPI:\n`;
      report += `     Tempo Totale:        ${formatDuration(totalDuration)}\n`;
      report += `     Tempo Medio/Step:    ${formatDuration(avgTime)}\n`;
    }
    
    report += `\n└${'─'.repeat(78)}┘\n\n`;
  }
  
  // FOOTER PROFESSIONALE
  report += `${'═'.repeat(80)}\n`;
  report += `FINE DEL REPORT\n\n`;
  report += `Report generato il: ${new Date().toLocaleString('it-IT', {
    weekday: 'long',
    year: 'numeric',
    month: 'long', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })}\n`;
  report += `Sistema: PilotPro Control Center v2.4.1\n`;
  report += `Tenant: ${tenantId}\n`;
  report += `${'═'.repeat(80)}\n`;
  
  return report;
}

/**
 * Formatta durata in millisecondi in formato human-readable
 * @param {number} ms - Millisecondi
 * @returns {string} Durata formattata
 */
function formatDuration(ms) {
  if (!ms || ms < 0) return '-';
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}min`;
}