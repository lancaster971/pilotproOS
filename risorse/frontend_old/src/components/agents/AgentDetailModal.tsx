/**
 * Agent Detail Modal
 * 
 * Modal per drill-down completo su execution AI agent
 * - Timeline step-by-step dell'agent
 * - Input/output di ogni nodo
 * - Business context dettagliato
 * - Raw execution data per debugging
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  X, Clock, CheckCircle, XCircle, Bot, Mail, ExternalLink,
  ChevronDown, ChevronRight, Code, Database, Activity,
  AlertTriangle, Info, Settings, Zap, Send, RefreshCw, FileText, Download
} from 'lucide-react';
import { tenantAPI } from '../../services/api';

// Tipi per execution details
interface AgentStep {
  nodeId: string;
  nodeName: string;
  type: 'input' | 'processing' | 'output' | 'error';
  startTime: string;
  duration: number;
  input: any;
  output: any;
  summary: string;
  details?: string;
  isVisible?: boolean; // Campo per filtro whitelist
}

interface AgentExecutionDetails {
  executionId: string;
  workflowId: string;
  workflowName: string;
  startedAt: string;
  duration: number;
  status: 'success' | 'error' | 'running';
  steps: AgentStep[];
  businessContext: {
    senderEmail?: string;
    orderId?: string;
    subject?: string;
    classification?: string;
    confidence?: number;
  };
  quickActions: {
    crmUrl?: string;
    replyAction?: string;
  };
  rawData?: any;
}

interface AgentDetailModalProps {
  workflowId: string;
  tenantId: string;
  isOpen: boolean;
  onClose: () => void;
}

const AgentDetailModal: React.FC<AgentDetailModalProps> = ({ 
  workflowId, 
  tenantId, 
  isOpen, 
  onClose 
}) => {
  const [activeTab, setActiveTab] = useState<'timeline' | 'context' | 'raw'>('timeline');
  const [expandedStep, setExpandedStep] = useState<string | null>(null);
  // Rimosso toggle - mostra sempre solo i nodi "show" per client view
  
  // React Query Client per invalidazione cache
  const queryClient = useQueryClient();

  // Utility per convertire dati JSON in descrizioni human-readable per EMAIL
  const humanizeStepData = (data: any, dataType: 'input' | 'output', nodeType?: string, nodeName?: string): string => {
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

    // Se è un array, prendi il primo elemento
    const processData = Array.isArray(data) ? data[0] : data;
    
    if (!processData || typeof processData !== 'object') {
      return String(processData) || 'Dato non strutturato';
    }

    const dataString = JSON.stringify(processData);
    const insights: string[] = [];
    
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
      processData.json?.output?.risposta_html, // Aggiunto per Milena node
      processData.json?.risposta_html,
      processData.json?.ai_response,
      processData.json?.response
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
      const preview = cleanResponse.substring(0, 150);
      insights.push(`Risposta AI: "${preview}${preview.length >= 150 ? '...' : ''}"`);
    }

    // PRIORITÀ 5: CLASSIFICAZIONE/CATEGORIA (se utile)
    if (processData.json?.output?.categoria && processData.json?.output?.confidence) {
      insights.push(`Classificazione: ${processData.json.output.categoria} (${processData.json.output.confidence} confidence)`);
    } else if (processData.json?.categoria && processData.json?.confidence) {
      insights.push(`Classificazione: ${processData.json.categoria} (${processData.json.confidence}% confidence)`);
    }

    // PRIORITÀ 6: ORDER ID (se specifico)
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
  };

  // SISTEMA CACHE ROBUSTO: Fetch workflow timeline con smart refresh
  const { data: timelineData, isLoading, error, refetch } = useQuery({
    queryKey: ['agent-workflow-timeline', tenantId, workflowId],
    queryFn: async () => {
      const response = await tenantAPI.agents.timeline(tenantId, workflowId);
      console.log('📡 API Response:', response);
      // response è già axios response, che ha response.data
      return response.data.data; // response.data è il body, response.data.data è il contenuto
    },
    enabled: isOpen, // Solo quando modal è aperto
    refetchInterval: 300000, // 🚀 POLLING INTENSIVO: Auto-refresh ogni 5 minuti per esecuzioni recenti
    staleTime: 0, // 🔥 SEMPRE FRESH: Nessuna cache stale per massima reattività
    refetchOnMount: true, // Sempre refresh quando modal si apre
    refetchOnWindowFocus: true, // 👁️ FOCUS REFRESH: Refresh quando torni al modal
  });

  // FORCE REFRESH: Mutation per forzare sync da n8n API
  const refreshMutation = useMutation({
    mutationFn: async () => {
      const response = await tenantAPI.agents.refresh(tenantId, workflowId);
      return response.data;
    },
    onSuccess: async () => {
      // Invalida cache e ricarica dati fresh
      queryClient.invalidateQueries({ queryKey: ['agent-workflow-timeline', tenantId, workflowId] });
      queryClient.invalidateQueries({ queryKey: ['workflow-cards'] }); // Invalida anche lista workflow
      queryClient.invalidateQueries({ queryKey: ['agents-workflows', tenantId] }); // 🔥 CRITICAL FIX: Invalida cache AgentsPage
      
      // 🚀 BRUTAL FORCE: Chiama timeline API direttamente con forceRefresh=true 
      try {
        console.log('🔥 FORCE REFRESH: Calling timeline API with forceRefresh=true');
        const freshResponse = await tenantAPI.agents.timeline(tenantId, workflowId, true);
        
        // Aggiorna la cache con i dati fresh
        queryClient.setQueryData(['agent-workflow-timeline', tenantId, workflowId], freshResponse);
        console.log('✅ Fresh timeline data loaded and cached');
      } catch (error) {
        console.error('❌ Failed to fetch fresh timeline:', error);
        // Fallback al normale refetch
        refetch();
      }
      
      console.log('✅ Workflow cache refreshed successfully - timeline loaded with forceRefresh=true');
    },
    onError: (error) => {
      console.error('❌ Failed to refresh workflow cache:', error);
    }
  });

  const handleForceRefresh = () => {
    console.log(`🔄 Force refreshing workflow ${workflowId} for tenant ${tenantId}`);
    console.log('🔧 Mutation status:', refreshMutation.status);
    refreshMutation.mutate();
  };

  // Ora timeline contiene l'intero oggetto response.data dal backend
  const timeline = timelineData;
  
  // Debug: vediamo cosa contiene timeline
  console.log('🔍 DEBUG timeline object:', timeline);
  console.log('🔍 DEBUG timeline keys:', timeline ? Object.keys(timeline) : 'null');
  console.log('🔍 DEBUG timeline.timeline:', timeline?.timeline);

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}min`;
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('it-IT', {
      dateStyle: 'short',
      timeStyle: 'medium'
    });
  };

  // Genera un report DETTAGLIATO e VERBOSO dal raw data
  const generateReadableReport = () => {
    if (!timeline) return '';
    
    let report = `╔${'═'.repeat(78)}╗\n`;
    report += `║${' '.repeat(20)}REPORT DETTAGLIATO ESECUZIONE WORKFLOW${' '.repeat(20)}║\n`;
    report += `║${' '.repeat(25)}PilotPro Control Center v2.4.1${' '.repeat(24)}║\n`;
    report += `╚${'═'.repeat(78)}╝\n\n`;
    
    // SEZIONE 1: INFORMAZIONI GENERALI
    report += `┌─ INFORMAZIONI GENERALI ${'─'.repeat(54)}┐\n\n`;
    
    report += `  Nome Workflow:     ${timeline.workflowName || 'Non specificato'}\n`;
    report += `  ID Workflow:       ${workflowId}\n`;
    report += `  Stato Workflow:    ${timeline.status === 'active' ? 'ATTIVO' : 'INATTIVO'}\n`;
    
    if (timeline.lastExecution) {
      report += `\n  ULTIMA ESECUZIONE:\n`;
      report += `  ├─ ID Esecuzione:  ${timeline.lastExecution.id}\n`;
      report += `  ├─ Data/Ora:       ${formatTimestamp(timeline.lastExecution.executedAt)}\n`;
      report += `  ├─ Durata Totale:  ${formatDuration(timeline.lastExecution.duration)}\n`;
      report += `  └─ Status:         ${timeline.lastExecution.status || 'Completato'}\n`;
    }
    
    report += `\n└${'─'.repeat(78)}┘\n\n`;
    
    // SEZIONE 2: CONTESTO BUSINESS DETTAGLIATO
    if (timeline.businessContext && Object.keys(timeline.businessContext).length > 0) {
      report += `┌─ ANALISI CONTESTO BUSINESS ${'─'.repeat(49)}┐\n\n`;
      
      report += `  Questo workflow ha processato una comunicazione business con i seguenti\n`;
      report += `  parametri identificati automaticamente dal sistema AI:\n\n`;
      
      if (timeline.businessContext.senderEmail) {
        report += `  MITTENTE EMAIL:\n`;
        report += `     Email: ${timeline.businessContext.senderEmail}\n`;
        report += `     Tipo: ${timeline.businessContext.senderEmail.includes('@') ? 'Email valida' : 'Formato non standard'}\n\n`;
      }
      
      if (timeline.businessContext.subject) {
        report += `  OGGETTO COMUNICAZIONE:\n`;
        report += `     "${timeline.businessContext.subject}"\n\n`;
      }
      
      if (timeline.businessContext.orderId) {
        report += `  RIFERIMENTO ORDINE:\n`;
        report += `     ID Ordine: ${timeline.businessContext.orderId}\n`;
        report += `     Formato: ${timeline.businessContext.orderId.length > 10 ? 'ID Esteso' : 'ID Standard'}\n\n`;
      }
      
      if (timeline.businessContext.classification) {
        report += `  CLASSIFICAZIONE AI:\n`;
        report += `     Categoria Identificata: ${timeline.businessContext.classification}\n`;
        if (timeline.businessContext.confidence) {
          report += `     Livello di Confidenza: ${timeline.businessContext.confidence}%\n`;
          const confidenceLevel = timeline.businessContext.confidence > 80 ? 'ALTA' : 
                                  timeline.businessContext.confidence > 60 ? 'MEDIA' : 'BASSA';
          report += `     Affidabilità: ${confidenceLevel}\n`;
        }
        report += `\n`;
      }
      
      // Analisi aggiuntive dal business context
      const contextKeys = Object.keys(timeline.businessContext);
      const additionalKeys = contextKeys.filter(key => 
        !['senderEmail', 'subject', 'orderId', 'classification', 'confidence'].includes(key)
      );
      
      if (additionalKeys.length > 0) {
        report += `  METRICHE AGGIUNTIVE:\n`;
        additionalKeys.forEach(key => {
          report += `     ${key}: ${timeline.businessContext[key]}\n`;
        });
        report += `\n`;
      }
      
      report += `└${'─'.repeat(78)}┘\n\n`;
    }
    
    // SEZIONE 3: TIMELINE DETTAGLIATA DELL'ESECUZIONE
    if (timeline.timeline && timeline.timeline.length > 0) {
      report += `┌─ TIMELINE DETTAGLIATA ESECUZIONE ${'─'.repeat(43)}┐\n\n`;
      
      report += `  Il workflow ha eseguito ${timeline.timeline.length} operazioni in sequenza.\n`;
      report += `  Di seguito il dettaglio completo di ogni passaggio:\n\n`;
      
      timeline.timeline.forEach((step: any, index: number) => {
        const stepNumber = index + 1;
        const isLastStep = index === timeline.timeline.length - 1;
        
        // Header dello step con formatting avanzato
        report += `  ${'═'.repeat(74)}\n`;
        report += `  STEP ${stepNumber}/${timeline.timeline.length}: ${step.nodeName.toUpperCase()}\n`;
        report += `  ${'═'.repeat(74)}\n\n`;
        
        // Informazioni tecniche dello step
        report += `  INFORMAZIONI TECNICHE:\n`;
        // Nascondi riferimenti a n8n sostituendoli con WFEngine
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
        
        if (step.customOrder) {
          report += `  ├─ Ordine Custom:    Show-${step.customOrder} (visibile nel client view)\n`;
        }
        
        if (step.summary) {
          report += `  └─ Sommario:         ${step.summary}\n`;
        }
        
        // DATI IN INPUT - ULTRA DETTAGLIATI
        report += `\n  DATI IN INPUT:\n`;
        if (step.inputData) {
          // Prima mostra il sommario human-readable
          const inputSummary = humanizeStepData(step.inputData, 'input', step.nodeType, step.nodeName);
          report += `  Sommario leggibile:\n`;
          const inputLines = inputSummary.split('\n');
          inputLines.forEach(line => {
            if (line.trim()) {
              report += `    ${line}\n`;
            }
          });
          
          // POI mostra i dati dettagliati in formato testuale leggibile
          report += `\n  Dettaglio completo dati in input:\n`;
          const inputDataObj = Array.isArray(step.inputData) ? step.inputData[0] : step.inputData;
          
          if (inputDataObj && typeof inputDataObj === 'object') {
            if (inputDataObj.json && typeof inputDataObj.json === 'object') {
              // Converti ogni campo JSON in testo leggibile
              Object.entries(inputDataObj.json).forEach(([key, value]) => {
                const humanKey = key.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2')
                  .toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
                
                if (value !== null && value !== undefined) {
                  if (typeof value === 'object') {
                    report += `    ${humanKey}: [Dati strutturati]\n`;
                    // Se è un oggetto, mostra i suoi campi principali
                    if (!Array.isArray(value)) {
                      Object.entries(value).slice(0, 3).forEach(([subKey, subValue]) => {
                        const humanSubKey = subKey.replace(/_/g, ' ').toLowerCase();
                        report += `      - ${humanSubKey}: ${String(subValue).substring(0, 100)}\n`;
                      });
                    }
                  } else if (typeof value === 'string' && value.length > 200) {
                    // Per testi lunghi, mostra solo un'anteprima
                    report += `    ${humanKey}: "${value.substring(0, 150)}..."\n`;
                  } else {
                    // Per valori semplici, mostra tutto
                    report += `    ${humanKey}: ${String(value)}\n`;
                  }
                }
              });
            } else {
              // Se non c'è wrapper json, mostra i campi diretti
              Object.entries(inputDataObj).slice(0, 10).forEach(([key, value]) => {
                const humanKey = key.replace(/_/g, ' ').toLowerCase();
                if (typeof value !== 'object') {
                  report += `    ${humanKey}: ${String(value).substring(0, 100)}\n`;
                }
              });
            }
          } else if (typeof inputDataObj === 'string') {
            report += `    ${inputDataObj}\n`;
          }
        } else {
          report += `     Nessun dato in input per questo step\n`;
        }
        
        // DATI IN OUTPUT - ULTRA DETTAGLIATI  
        report += `\n  DATI IN OUTPUT:\n`;
        if (step.outputData) {
          // Prima mostra il sommario human-readable
          const outputSummary = humanizeStepData(step.outputData, 'output', step.nodeType, step.nodeName);
          report += `  Sommario leggibile:\n`;
          const outputLines = outputSummary.split('\n');
          outputLines.forEach(line => {
            if (line.trim()) {
              report += `    ${line}\n`;
            }
          });
          
          // POI mostra i dati dettagliati in formato testuale leggibile
          report += `\n  Dettaglio completo dati in output:\n`;
          const outputDataObj = Array.isArray(step.outputData) ? step.outputData[0] : step.outputData;
          
          if (outputDataObj && typeof outputDataObj === 'object') {
            if (outputDataObj.json && typeof outputDataObj.json === 'object') {
              // Converti ogni campo JSON in testo leggibile
              const fieldsToShow = Object.entries(outputDataObj.json);
              
              // Prima mostra i campi più importanti
              const priorityFields = ['oggetto', 'mittente', 'messaggio_cliente', 'order_reference', 
                                    'customer_full_name', 'order_status', 'risposta_html', 'categoria',
                                    'confidence', 'order_id', 'tracking_number', 'subject', 'sender',
                                    'body', 'content', 'response', 'output'];
              
              // Campi prioritari
              priorityFields.forEach(field => {
                if (outputDataObj.json[field] !== undefined && outputDataObj.json[field] !== null) {
                  const humanField = field.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2')
                    .toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
                  const value = outputDataObj.json[field];
                  
                  if (typeof value === 'string') {
                    // Rimuovi HTML tags e mostra testo pulito
                    const cleanValue = value.replace(/<[^>]+>/g, ' ').replace(/&[a-zA-Z0-9]+;/g, ' ')
                      .replace(/\s+/g, ' ').trim();
                    if (cleanValue.length > 200) {
                      report += `    ${humanField}:\n      "${cleanValue.substring(0, 200)}..."\n\n`;
                    } else {
                      report += `    ${humanField}: ${cleanValue}\n`;
                    }
                  } else if (typeof value === 'object') {
                    report += `    ${humanField}: [Dati complessi - ${Object.keys(value).length} campi]\n`;
                  } else {
                    report += `    ${humanField}: ${String(value)}\n`;
                  }
                }
              });
              
              // Altri campi non prioritari
              fieldsToShow.forEach(([key, value]) => {
                if (!priorityFields.includes(key) && value !== null && value !== undefined) {
                  const humanKey = key.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2')
                    .toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
                  
                  if (typeof value === 'string' && value.length < 100) {
                    report += `    ${humanKey}: ${value}\n`;
                  } else if (typeof value === 'number' || typeof value === 'boolean') {
                    report += `    ${humanKey}: ${value}\n`;
                  }
                }
              });
            } else {
              // Se non c'è wrapper json, mostra i campi diretti
              Object.entries(outputDataObj).slice(0, 10).forEach(([key, value]) => {
                const humanKey = key.replace(/_/g, ' ').toLowerCase();
                if (typeof value !== 'object') {
                  report += `    ${humanKey}: ${String(value).substring(0, 100)}\n`;
                }
              });
            }
          } else if (typeof outputDataObj === 'string') {
            report += `    ${outputDataObj}\n`;
          }
        } else {
          report += `     Nessun dato in output per questo step\n`;
        }
        
        // Note aggiuntive per step specifici
        if (step.nodeName.toLowerCase().includes('ai') || step.nodeName.toLowerCase().includes('milena')) {
          report += `\n  NOTA: Questo è un nodo AI che ha processato la richiesta utilizzando\n`;
          report += `        intelligenza artificiale per generare una risposta contestuale.\n`;
        }
        
        if (step.nodeName.toLowerCase().includes('vector')) {
          report += `\n  NOTA: Questo nodo ha eseguito una ricerca vettoriale nel database\n`;
          report += `        per trovare informazioni rilevanti alla query.\n`;
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
    if (timeline.timeline && timeline.timeline.length > 0) {
      report += `┌─ ANALISI STATISTICA ESECUZIONE ${'─'.repeat(45)}┐\n\n`;
      
      const totalSteps = timeline.timeline.length;
      const successSteps = timeline.timeline.filter((s: any) => s.status === 'success').length;
      const errorSteps = timeline.timeline.filter((s: any) => s.status === 'error').length;
      const skippedSteps = timeline.timeline.filter((s: any) => s.status === 'not-executed').length;
      
      report += `  RIEPILOGO STEPS:\n`;
      report += `     Totale Steps:        ${totalSteps}\n`;
      report += `     Steps Completati:    ${successSteps} (${((successSteps/totalSteps)*100).toFixed(1)}%)\n`;
      report += `     Steps con Errori:    ${errorSteps} (${((errorSteps/totalSteps)*100).toFixed(1)}%)\n`;
      report += `     Steps Non Eseguiti:  ${skippedSteps} (${((skippedSteps/totalSteps)*100).toFixed(1)}%)\n`;
      
      // Calcola tempo totale e medio
      const timings = timeline.timeline
        .filter((s: any) => s.executionTime !== undefined)
        .map((s: any) => s.executionTime);
      
      if (timings.length > 0) {
        const totalTime = timings.reduce((a: number, b: number) => a + b, 0);
        const avgTime = totalTime / timings.length;
        const maxTime = Math.max(...timings);
        const minTime = Math.min(...timings);
        
        report += `\n  ANALISI TEMPI:\n`;
        report += `     Tempo Totale:        ${formatDuration(totalTime)}\n`;
        report += `     Tempo Medio/Step:    ${formatDuration(avgTime)}\n`;
        report += `     Step più Veloce:     ${formatDuration(minTime)}\n`;
        report += `     Step più Lento:      ${formatDuration(maxTime)}\n`;
        
        // Trova lo step più lento
        const slowestStep = timeline.timeline.find((s: any) => s.executionTime === maxTime);
        if (slowestStep) {
          report += `     └─ "${slowestStep.nodeName}" ha richiesto ${formatDuration(maxTime)}\n`;
        }
      }
      
      report += `\n└${'─'.repeat(78)}┘\n\n`;
    }
    
    // SEZIONE 5: RACCOMANDAZIONI E NOTE
    report += `┌─ RACCOMANDAZIONI E NOTE ${'─'.repeat(52)}┐\n\n`;
    
    // Analizza e fornisce raccomandazioni
    const hasErrors = timeline.timeline?.some((s: any) => s.status === 'error');
    const hasSkipped = timeline.timeline?.some((s: any) => s.status === 'not-executed');
    const avgTime = timeline.lastExecution ? timeline.lastExecution.duration / (timeline.timeline?.length || 1) : 0;
    
    if (hasErrors) {
      report += `  ATTENZIONE: Sono stati rilevati errori durante l'esecuzione.\n`;
      report += `     Si consiglia di verificare i log dettagliati per identificare\n`;
      report += `     e risolvere i problemi.\n\n`;
    }
    
    if (hasSkipped) {
      report += `  NOTA: Alcuni step non sono stati eseguiti.\n`;
      report += `     Questo potrebbe essere normale se il workflow include\n`;
      report += `     logica condizionale.\n\n`;
    }
    
    if (avgTime > 5000) {
      report += `  PERFORMANCE: Il tempo medio per step è elevato (${formatDuration(avgTime)}).\n`;
      report += `     Considerare l'ottimizzazione del workflow per migliorare\n`;
      report += `     le prestazioni.\n\n`;
    } else if (avgTime < 500) {
      report += `  ECCELLENTE: Il workflow sta eseguendo molto rapidamente!\n`;
      report += `     Tempo medio per step: ${formatDuration(avgTime)}\n\n`;
    }
    
    report += `└${'─'.repeat(78)}┘\n\n`;
    
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
  };

  // Scarica il report come file di testo
  const downloadReport = () => {
    const report = generateReadableReport();
    const blob = new Blob([report], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `workflow-report-${workflowId}-${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'error': return <XCircle className="w-4 h-4 text-red-400" />;
      case 'running': return <Settings className="w-4 h-4 text-yellow-400 animate-spin" />;
      case 'not-executed': return <Activity className="w-4 h-4 text-gray-500" />;
      default: return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStepColor = (status: string) => {
    switch (status) {
      case 'success': return 'border-green-400/30 bg-green-400/5';
      case 'error': return 'border-red-400/30 bg-red-400/5';
      case 'running': return 'border-yellow-400/30 bg-yellow-400/5';
      case 'not-executed': return 'border-gray-600/30 bg-gray-800/50';
      default: return 'border-gray-400/30 bg-gray-400/5';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-green-400/20 rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-800">
          <div className="flex items-center">
            <Bot className="w-6 h-6 text-green-400 mr-3" />
            <div>
              <h2 className="text-xl font-semibold text-white">
                {timeline ? timeline.workflowName : 'Loading...'}
              </h2>
              <p className="text-gray-400 text-sm">
                Workflow ID: {workflowId}
                {timeline?.lastExecution && (
                  <span className="ml-3">
                    • Last execution: {timeline?.lastExecution?.id || 'None'}
                  </span>
                )}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            {/* Force Refresh Button - MIGLIORATO */}
            <button
              onClick={handleForceRefresh}
              disabled={refreshMutation.isPending}
              className={`flex items-center px-4 py-2 rounded-lg font-medium transition-all ${
                refreshMutation.isPending 
                  ? 'bg-gray-700 text-gray-400 cursor-not-allowed' 
                  : 'bg-green-600 hover:bg-green-500 text-white shadow-lg hover:shadow-green-500/25'
              }`}
              title="Force refresh latest executions from workflow engine"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshMutation.isPending ? 'animate-spin' : ''}`} />
              {refreshMutation.isPending ? 'Refreshing...' : 'Force Refresh'}
            </button>
            
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex-1 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-400"></div>
            <span className="ml-3 text-green-400">Loading execution details...</span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="flex-1 flex items-center justify-center text-red-400">
            <AlertTriangle className="w-6 h-6 mr-2" />
            Failed to load execution details
          </div>
        )}

        {/* Content */}
        {timeline && (
          <>
            {/* Tabs */}
            <div className="flex border-b border-gray-800">
              <button
                onClick={() => setActiveTab('timeline')}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'timeline'
                    ? 'border-green-400 text-green-400'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                Timeline
              </button>
              <button
                onClick={() => setActiveTab('context')}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'context'
                    ? 'border-green-400 text-green-400'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                Business Context
              </button>
              <button
                onClick={() => setActiveTab('raw')}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'raw'
                    ? 'border-green-400 text-green-400'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                Raw Data
              </button>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {/* Timeline Tab */}
              {activeTab === 'timeline' && (
                <div>
                  <div className="mb-6 p-4 bg-black rounded-lg border border-gray-800">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-medium">Workflow Summary</span>
                      <div className="flex items-center">
                        {timeline?.status === 'active' ? (
                          <CheckCircle className="w-5 h-5 text-green-400 mr-2" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-400 mr-2" />
                        )}
                        <span className={timeline?.status === 'active' ? 'text-green-400' : 'text-red-400'}>
                          {timeline?.status?.toUpperCase() || 'UNKNOWN'}
                        </span>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">Last Execution:</span>
                        <span className="text-white ml-2">
                          {timeline?.lastExecution ? formatTimestamp(timeline.lastExecution.executedAt) : 'No executions'}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">Duration:</span>
                        <span className="text-white ml-2">
                          {timeline?.lastExecution ? formatDuration(timeline.lastExecution.duration) : 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Info header per timeline con freshness indicator */}
                  <div className="mb-4 flex items-center justify-between">
                    <div className="text-sm text-gray-400">
                      Showing workflow steps marked with "show" annotations
                    </div>
                    <div className="flex items-center text-xs text-gray-500">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
                      Auto-refresh: 5 min | Last check: {new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>

                  {(() => {
                    // Mostra sempre solo i nodi marcati con "show" (client view)
                    const stepsToShow = timeline?.timeline || [];
                    
                    if (stepsToShow.length === 0) {
                      return (
                        <div className="text-center py-8 text-gray-400">
                          <Info className="w-8 h-8 mx-auto mb-2" />
                          <p>No workflow steps available</p>
                          <p className="text-sm">
                            Steps will appear here when workflow executions contain nodes marked with "show-N" in their notes.
                          </p>
                        </div>
                      );
                    }
                    
                    return (
                      <div className="space-y-4">
                        {stepsToShow.map((step, index) => {
                          // Assicurati che step abbia tutti i campi necessari
                          const stepStatus = step.status || 'unknown';
                          const stepName = step.nodeName || 'Unknown Node';
                          const stepSummary = step.summary || '';
                          
                          return (
                        <div 
                          key={step.nodeId || index}
                          className={`border rounded-lg p-4 ${getStepColor(stepStatus)}`}
                        >
                          <div 
                            className="flex items-center justify-between cursor-pointer"
                            onClick={() => setExpandedStep(expandedStep === step.nodeId ? null : step.nodeId)}
                          >
                            <div className="flex items-center">
                              {getStepIcon(stepStatus)}
                              <div className="ml-3">
                                <div className="font-medium text-white">{stepName}</div>
                                <div className="text-sm text-gray-400">
                                  {stepStatus === 'not-executed' 
                                    ? 'Node not executed in this run' 
                                    : stepSummary}
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center">
                              <span className="text-xs text-gray-400 mr-3">
                                {stepStatus === 'not-executed' 
                                  ? 'Skipped' 
                                  : formatDuration(step.executionTime || 0)}
                              </span>
                              {expandedStep === step.nodeId ? (
                                <ChevronDown className="w-4 h-4 text-gray-400" />
                              ) : (
                                <ChevronRight className="w-4 h-4 text-gray-400" />
                              )}
                            </div>
                          </div>

                          {expandedStep === step.nodeId && (
                            <div className="mt-4 pt-4 border-t border-gray-700">
                              {step.details && (
                                <div className="mb-4">
                                  <div className="text-sm font-medium text-white mb-2">Details:</div>
                                  <div className="text-sm text-gray-300">{step.details}</div>
                                </div>
                              )}
                              
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                  <div className="text-sm font-medium text-white mb-2">Input:</div>
                                  <div className="bg-gray-900 p-3 rounded text-sm text-gray-300 whitespace-pre-line">
                                    {humanizeStepData(step.inputData, 'input', step.nodeType, step.nodeName)}
                                  </div>
                                  <details className="mt-2">
                                    <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                                      Mostra dati tecnici
                                    </summary>
                                    <pre className="bg-gray-800 p-2 rounded text-xs text-gray-400 overflow-x-auto mt-2">
                                      {JSON.stringify(step.inputData, null, 2)}
                                    </pre>
                                  </details>
                                </div>
                                <div>
                                  <div className="text-sm font-medium text-white mb-2">Output:</div>
                                  <div className="bg-gray-900 p-3 rounded text-sm text-gray-300 whitespace-pre-line">
                                    {humanizeStepData(step.outputData, 'output', step.nodeType, step.nodeName)}
                                  </div>
                                  <details className="mt-2">
                                    <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                                      Mostra dati tecnici
                                    </summary>
                                    <pre className="bg-gray-800 p-2 rounded text-xs text-gray-400 overflow-x-auto mt-2">
                                      {JSON.stringify(step.outputData, null, 2)}
                                    </pre>
                                  </details>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                      })}
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Business Context Tab */}
              {activeTab === 'context' && (
                <div className="space-y-6">
                  <div className="p-4 bg-black rounded-lg border border-gray-800">
                    <h3 className="text-lg font-medium text-white mb-4">Business Context</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {timeline.businessContext?.senderEmail && (
                        <div className="flex items-center">
                          <Mail className="w-4 h-4 text-blue-400 mr-2" />
                          <span className="text-gray-400">Sender:</span>
                          <span className="text-blue-400 ml-2">{timeline.businessContext.senderEmail}</span>
                        </div>
                      )}
                      
                      {timeline.businessContext?.orderId && (
                        <div className="flex items-center">
                          <Database className="w-4 h-4 text-green-400 mr-2" />
                          <span className="text-gray-400">Order ID:</span>
                          <span className="text-white ml-2">{timeline.businessContext.orderId}</span>
                        </div>
                      )}
                      
                      {timeline.businessContext?.subject && (
                        <div className="flex items-center">
                          <Info className="w-4 h-4 text-yellow-400 mr-2" />
                          <span className="text-gray-400">Subject:</span>
                          <span className="text-white ml-2">{timeline.businessContext.subject}</span>
                        </div>
                      )}
                      
                      {timeline.businessContext?.classification && (
                        <div className="flex items-center">
                          <Activity className="w-4 h-4 text-purple-400 mr-2" />
                          <span className="text-gray-400">Classification:</span>
                          <span className="text-purple-400 ml-2">
                            {timeline.businessContext.classification}
                            {timeline.businessContext.confidence && (
                              <span className="text-gray-400 ml-1">({timeline.businessContext.confidence}%)</span>
                            )}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Quick Actions */}
                  {timeline.businessContext?.senderEmail && (
                    <div className="p-4 bg-black rounded-lg border border-gray-800">
                      <h3 className="text-lg font-medium text-white mb-4">Quick Actions</h3>
                      <div className="flex space-x-4">
                        <button
                          onClick={() => window.open(`mailto:${timeline.businessContext.senderEmail}?subject=Re: ${timeline.businessContext.subject || ''}`, '_blank')}
                          className="flex items-center px-4 py-2 bg-blue-400 text-black rounded hover:bg-blue-300 transition-colors"
                        >
                          <Mail className="w-4 h-4 mr-2" />
                          Reply to Customer
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Raw Data Tab */}
              {activeTab === 'raw' && (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                      <Code className="w-5 h-5 text-gray-400 mr-2" />
                      <h3 className="text-lg font-medium text-white">Raw Timeline Data</h3>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          const report = generateReadableReport();
                          // Mostra il report nel pre tag invece del JSON
                          const preElement = document.getElementById('raw-data-content');
                          if (preElement) {
                            preElement.textContent = report;
                          }
                        }}
                        className="flex items-center px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
                      >
                        <FileText className="w-4 h-4 mr-1.5" />
                        Genera Report
                      </button>
                      <button
                        onClick={downloadReport}
                        className="flex items-center px-3 py-1.5 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm transition-colors"
                      >
                        <Download className="w-4 h-4 mr-1.5" />
                        Scarica Report
                      </button>
                      <button
                        onClick={() => {
                          // Ripristina JSON originale
                          const preElement = document.getElementById('raw-data-content');
                          if (preElement) {
                            // Sanitizza JSON rimuovendo riferimenti a n8n
                            const sanitizedJson = JSON.stringify(timeline, null, 2)
                              .replace(/n8n/gi, 'WFEngine')
                              .replace(/\.nodes\./g, '.engine.')
                              .replace(/\.base\./g, '.core.');
                            preElement.textContent = sanitizedJson;
                          }
                        }}
                        className="flex items-center px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
                      >
                        <Code className="w-4 h-4 mr-1.5" />
                        Mostra JSON
                      </button>
                    </div>
                  </div>
                  
                  <pre 
                    id="raw-data-content"
                    className="bg-black p-4 rounded-lg border border-gray-800 text-xs text-gray-300 overflow-auto max-h-96 font-mono whitespace-pre"
                  >
                    {JSON.stringify(timeline, null, 2)
                      .replace(/n8n/gi, 'WFEngine')
                      .replace(/\.nodes\./g, '.engine.')
                      .replace(/\.base\./g, '.core.')
                    }
                  </pre>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AgentDetailModal;