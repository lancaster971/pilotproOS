/**
 * Business Terminology Sanitization
 * 
 * Questo modulo gestisce la completa sanitizzazione di tutti i termini tecnici
 * traducendoli in linguaggio business comprensibile per il cliente finale.
 * 
 * PRINCIPIO FONDAMENTALE: Il cliente NON deve mai vedere terminologia tecnica.
 */

/**
 * Mappatura terminologia tecnica → business
 */
export const BUSINESS_TERMINOLOGY = {
  // Core concepts
  workflow: 'business_process',
  workflows: 'business_processes', 
  execution: 'process_run',
  executions: 'process_runs',
  node: 'process_step',
  nodes: 'process_steps',
  webhook: 'integration_endpoint',
  webhooks: 'integration_endpoints',
  trigger: 'process_starter',
  triggers: 'process_starters',
  credential: 'connection_setting',
  credentials: 'connection_settings',
  
  // Technical terms
  workflow_id: 'process_id',
  workflow_name: 'process_name',
  execution_id: 'run_id',
  node_id: 'step_id',
  node_type: 'step_type',
  node_name: 'step_name',
  
  // Status terms
  running: 'in_progress',
  success: 'completed_successfully',
  error: 'requires_attention',
  stopped: 'paused_by_user',
  waiting: 'waiting_for_input',
  
  // Database terms
  workflow_entity: 'business_processes',
  execution_entity: 'process_runs',
  credentials_entity: 'connection_settings'
};

/**
 * Mappatura status per frontend
 */
export const BUSINESS_STATUS_MAP = {
  // Execution statuses
  running: {
    label: 'In Progress',
    icon: '🔄',
    color: 'blue',
    description: 'Process is currently running'
  },
  success: {
    label: 'Completed Successfully', 
    icon: '✅',
    color: 'green',
    description: 'Process completed without issues'
  },
  error: {
    label: 'Requires Attention',
    icon: '⚠️', 
    color: 'red',
    description: 'Process encountered an issue that needs review'
  },
  stopped: {
    label: 'Paused by User',
    icon: '⏸️',
    color: 'yellow', 
    description: 'Process was manually stopped'
  },
  waiting: {
    label: 'Waiting for Input',
    icon: '⏳',
    color: 'orange',
    description: 'Process is waiting for external input or trigger'
  }
};

/**
 * Mappatura health status
 */
export const BUSINESS_HEALTH_MAP = {
  excellent: {
    label: 'Excellent Performance',
    icon: '🎯',
    color: 'green',
    range: '98-100%',
    description: 'Process is performing exceptionally well'
  },
  good: {
    label: 'Good Performance', 
    icon: '👍',
    color: 'blue',
    range: '85-97%',
    description: 'Process is performing well with minor optimization opportunities'
  },
  fair: {
    label: 'Fair Performance',
    icon: '📊', 
    color: 'yellow',
    range: '70-84%',
    description: 'Process is functional but has room for improvement'
  },
  poor: {
    label: 'Needs Attention',
    icon: '🔧',
    color: 'red', 
    range: '0-69%',
    description: 'Process requires immediate attention and optimization'
  }
};

/**
 * Categorizzazione tipi di processo business
 */
export const BUSINESS_PROCESS_CATEGORIES = {
  // Customer operations
  customer_onboarding: {
    label: 'Customer Onboarding',
    icon: '👥',
    description: 'Automated customer registration and setup processes'
  },
  customer_support: {
    label: 'Customer Support',
    icon: '🎧', 
    description: 'Automated support ticket handling and resolution'
  },
  
  // Sales & Marketing
  lead_generation: {
    label: 'Lead Generation',
    icon: '🎯',
    description: 'Automated lead capture and qualification processes'
  },
  sales_pipeline: {
    label: 'Sales Pipeline',
    icon: '💼',
    description: 'Automated sales process management'
  },
  
  // Operations
  order_processing: {
    label: 'Order Processing', 
    icon: '📦',
    description: 'Automated order fulfillment and tracking'
  },
  inventory_management: {
    label: 'Inventory Management',
    icon: '📊',
    description: 'Automated inventory tracking and restocking'
  },
  
  // Finance
  invoice_processing: {
    label: 'Invoice Processing',
    icon: '💰',
    description: 'Automated invoice generation and payment tracking'
  },
  expense_management: {
    label: 'Expense Management', 
    icon: '💳',
    description: 'Automated expense tracking and approval'
  },
  
  // HR & Admin
  employee_onboarding: {
    label: 'Employee Onboarding',
    icon: '🏢',
    description: 'Automated new employee setup and training'
  },
  document_management: {
    label: 'Document Management',
    icon: '📄',
    description: 'Automated document processing and filing'
  },
  
  // Generic/Custom
  data_integration: {
    label: 'Data Integration',
    icon: '🔗',
    description: 'Automated data synchronization between systems'
  },
  reporting: {
    label: 'Business Reporting',
    icon: '📈', 
    description: 'Automated report generation and distribution'
  },
  custom: {
    label: 'Custom Process',
    icon: '⚙️',
    description: 'Custom automated business process'
  }
};

/**
 * Sanitizza un oggetto rimuovendo terminologia tecnica
 * 
 * @param {Object} data - Dati da sanitizzare
 * @param {Object} options - Opzioni di sanitizzazione
 * @returns {Object} Dati sanitizzati
 */
export function sanitizeBusinessData(data, options = {}) {
  if (!data) return data;
  
  // Se è un array, sanitizza ogni elemento
  if (Array.isArray(data)) {
    return data.map(item => sanitizeBusinessData(item, options));
  }
  
  // Se non è un oggetto, ritorna così com'è
  if (typeof data !== 'object') {
    return data;
  }
  
  const sanitized = {};
  
  for (const [key, value] of Object.entries(data)) {
    // Sanitizza la chiave
    const sanitizedKey = BUSINESS_TERMINOLOGY[key] || key;
    
    // Sanitizza il valore se è un oggetto
    let sanitizedValue = value;
    if (typeof value === 'object' && value !== null) {
      sanitizedValue = sanitizeBusinessData(value, options);
    }
    
    // Applica sanitizzazione speciale per status
    if (key === 'status' && typeof value === 'string') {
      sanitizedValue = BUSINESS_STATUS_MAP[value]?.label || value;
    }
    
    sanitized[sanitizedKey] = sanitizedValue;
  }
  
  return sanitized;
}

/**
 * Converte status tecnico in business status completo
 * 
 * @param {string} technicalStatus - Status tecnico
 * @returns {Object} Status business con label, icon, color
 */
export function getBusinessStatus(technicalStatus) {
  return BUSINESS_STATUS_MAP[technicalStatus] || {
    label: 'Unknown Status',
    icon: '❓',
    color: 'gray',
    description: 'Status not recognized'
  };
}

/**
 * Determina health status basato su success rate
 * 
 * @param {number} successRate - Percentuale di successo (0-100)
 * @returns {Object} Health status business
 */
export function getBusinessHealthStatus(successRate) {
  if (successRate >= 98) return BUSINESS_HEALTH_MAP.excellent;
  if (successRate >= 85) return BUSINESS_HEALTH_MAP.good;
  if (successRate >= 70) return BUSINESS_HEALTH_MAP.fair;
  return BUSINESS_HEALTH_MAP.poor;
}

/**
 * Categorizza un processo business basato sul nome e nodi
 * 
 * @param {string} processName - Nome del processo
 * @param {Array} nodes - Array di nodi (opzionale)
 * @returns {Object} Categoria business
 */
export function categorizeBusinessProcess(processName, nodes = []) {
  const name = processName.toLowerCase();
  const nodeTypes = nodes.map(n => n.type?.toLowerCase() || '').join(' ');
  const fullText = `${name} ${nodeTypes}`;
  
  // Pattern matching per categorizzazione automatica
  if (fullText.includes('customer') || fullText.includes('client')) {
    if (fullText.includes('onboard') || fullText.includes('registr')) {
      return BUSINESS_PROCESS_CATEGORIES.customer_onboarding;
    }
    if (fullText.includes('support') || fullText.includes('ticket')) {
      return BUSINESS_PROCESS_CATEGORIES.customer_support;
    }
  }
  
  if (fullText.includes('lead') || fullText.includes('prospect')) {
    return BUSINESS_PROCESS_CATEGORIES.lead_generation;
  }
  
  if (fullText.includes('sale') || fullText.includes('crm')) {
    return BUSINESS_PROCESS_CATEGORIES.sales_pipeline;
  }
  
  if (fullText.includes('order') || fullText.includes('purchase')) {
    return BUSINESS_PROCESS_CATEGORIES.order_processing;
  }
  
  if (fullText.includes('invoice') || fullText.includes('billing')) {
    return BUSINESS_PROCESS_CATEGORIES.invoice_processing;
  }
  
  if (fullText.includes('employee') || fullText.includes('hr')) {
    return BUSINESS_PROCESS_CATEGORIES.employee_onboarding;
  }
  
  if (fullText.includes('report') || fullText.includes('analytics')) {
    return BUSINESS_PROCESS_CATEGORIES.reporting;
  }
  
  if (fullText.includes('data') || fullText.includes('sync')) {
    return BUSINESS_PROCESS_CATEGORIES.data_integration;
  }
  
  // Default
  return BUSINESS_PROCESS_CATEGORIES.custom;
}

/**
 * Genera descrizione business-friendly per errori tecnici
 * 
 * @param {string} technicalError - Messaggio di errore tecnico
 * @param {string} nodeName - Nome del nodo che ha generato l'errore
 * @returns {string} Descrizione business dell'errore
 */
export function sanitizeErrorMessage(technicalError, nodeName = null) {
  if (!technicalError) return null;
  
  const error = technicalError.toLowerCase();
  
  // Errori di connettività
  if (error.includes('timeout') || error.includes('network')) {
    return `Connection timeout occurred${nodeName ? ` in ${nodeName} step` : ''}. The external service may be temporarily unavailable.`;
  }
  
  // Errori di autenticazione
  if (error.includes('unauthorized') || error.includes('authentication') || error.includes('401')) {
    return `Authentication failed${nodeName ? ` in ${nodeName} step` : ''}. Please check connection credentials.`;
  }
  
  // Errori di permessi
  if (error.includes('forbidden') || error.includes('403')) {
    return `Access denied${nodeName ? ` in ${nodeName} step` : ''}. Insufficient permissions for this operation.`;
  }
  
  // Errori di validazione dati
  if (error.includes('validation') || error.includes('invalid')) {
    return `Data validation failed${nodeName ? ` in ${nodeName} step` : ''}. Please check input data format.`;
  }
  
  // Errori di rate limiting
  if (error.includes('rate limit') || error.includes('too many requests')) {
    return `Service rate limit exceeded${nodeName ? ` in ${nodeName} step` : ''}. The process will retry automatically.`;
  }
  
  // Errori generici
  return `Process encountered an issue${nodeName ? ` in ${nodeName} step` : ''}. Technical support has been notified.`;
}

/**
 * Converte durata in formato business-friendly
 * 
 * @param {number} durationMs - Durata in millisecondi
 * @returns {string} Durata formattata per business
 */
export function formatBusinessDuration(durationMs) {
  if (!durationMs || durationMs < 0) return 'Unknown';
  
  const seconds = Math.floor(durationMs / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) {
    const remainingMinutes = minutes % 60;
    return `${hours}h${remainingMinutes > 0 ? ` ${remainingMinutes}m` : ''}`;
  }
  
  if (minutes > 0) {
    const remainingSeconds = seconds % 60;
    return `${minutes}m${remainingSeconds > 0 ? ` ${remainingSeconds}s` : ''}`;
  }
  
  return `${seconds}s`;
}

/**
 * Genera insights business da metriche tecniche
 * 
 * @param {Object} metrics - Metriche tecniche
 * @returns {Array} Array di insights business
 */
export function generateBusinessInsights(metrics) {
  const insights = [];
  
  if (metrics.successRate >= 98) {
    insights.push({
      type: 'positive',
      icon: '🎯',
      message: 'Excellent process performance - your automation is running smoothly',
      priority: 'low'
    });
  } else if (metrics.successRate < 70) {
    insights.push({
      type: 'warning', 
      icon: '⚠️',
      message: 'Process performance needs attention - consider reviewing error patterns',
      priority: 'high'
    });
  }
  
  if (metrics.avgDurationMs && metrics.avgDurationMs < 30000) {
    insights.push({
      type: 'positive',
      icon: '⚡',
      message: 'Fast processing times - your processes are highly efficient',
      priority: 'low'
    });
  }
  
  if (metrics.totalExecutions > 1000) {
    insights.push({
      type: 'info',
      icon: '📈',
      message: 'High usage indicates this process is valuable to your business',
      priority: 'medium'
    });
  }
  
  return insights;
}