/**
 * Frontend Sanitization Utilities
 * REGOLA FERREA: Backup sanitizzazione per garantire che nessun "n8n" raggiunga il cliente
 * 
 * NOTA: Questo è il Layer 2 di sicurezza. Il Layer 1 è nel backend.
 * Uso principale: UI labels, export files, error messages client-side
 */

/**
 * Mappa delle sostituzioni per privacy cliente
 */
const FRONTEND_SANITIZATION_MAP = {
  // UI Labels e messaggi
  'n8n': 'WFEngine',
  'N8N': 'WFEngine',
  
  // Node types per display
  'n8n-nodes-base': 'WFEngine.core',
  'n8n-nodes-': 'WFEngine.',
  '@n8n/': '@WFEngine/',
  
  // Error messages user-facing
  'n8n API': 'Workflow Engine API',
  'n8n server': 'Workflow Engine server',
  'n8n instance': 'Workflow Engine instance',
  'n8n workflow': 'automation workflow',
  'n8n execution': 'workflow execution',
  'Failed to connect to n8n': 'Workflow engine unavailable',
  'n8n is not responding': 'Workflow engine is not responding',
  
  // Export filenames
  'n8n_export': 'workflow_export',
  'n8n_report': 'automation_report',
  'n8n_data': 'workflow_data',
  
  // URLs e paths in frontend
  '/n8n/': '/wfengine/',
  'n8n.io': 'workflowengine.local',
};

/**
 * Sanitizza una stringa rimuovendo riferimenti n8n
 */
export function sanitizeString(str: string): string {
  if (typeof str !== 'string') {
    return str;
  }
  
  let sanitized = str;
  
  // Applica tutte le sostituzioni
  for (const [search, replace] of Object.entries(FRONTEND_SANITIZATION_MAP)) {
    const regex = new RegExp(search.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
    sanitized = sanitized.replace(regex, replace);
  }
  
  return sanitized;
}

/**
 * Sanitizza ricorsivamente un oggetto
 */
export function sanitizeObject(obj: any): any {
  if (obj === null || obj === undefined) {
    return obj;
  }
  
  if (typeof obj === 'string') {
    return sanitizeString(obj);
  }
  
  if (Array.isArray(obj)) {
    return obj.map(item => sanitizeObject(item));
  }
  
  if (typeof obj === 'object') {
    const sanitized: any = {};
    for (const [key, value] of Object.entries(obj)) {
      const sanitizedKey = sanitizeString(key);
      sanitized[sanitizedKey] = sanitizeObject(value);
    }
    return sanitized;
  }
  
  return obj;
}

/**
 * Sanitizza response da API (backup per sicurezza)
 */
export function sanitizeApiResponse(response: any): any {
  return sanitizeObject(response);
}

/**
 * Sanitizza testi per UI components
 */
export const uiSanitization = {
  /**
   * Sanitizza titoli e labels
   */
  sanitizeLabel: (label: string): string => {
    return sanitizeString(label);
  },
  
  /**
   * Sanitizza descrizioni e tooltips
   */
  sanitizeDescription: (description: string): string => {
    return sanitizeString(description);
  },
  
  /**
   * Sanitizza breadcrumbs
   */
  sanitizeBreadcrumb: (breadcrumb: string): string => {
    return sanitizeString(breadcrumb);
  },
  
  /**
   * Sanitizza titoli di modal
   */
  sanitizeModalTitle: (title: string): string => {
    return sanitizeString(title);
  },
  
  /**
   * Sanitizza placeholder text
   */
  sanitizePlaceholder: (placeholder: string): string => {
    return sanitizeString(placeholder);
  }
};

/**
 * Sanitizza messaggi di errore per l'utente
 */
export const errorSanitization = {
  /**
   * Sanitizza messaggi di errore da API
   */
  sanitizeErrorMessage: (error: string): string => {
    return sanitizeString(error);
  },
  
  /**
   * Sanitizza error stack traces (per development)
   */
  sanitizeStackTrace: (stack: string): string => {
    return sanitizeString(stack);
  },
  
  /**
   * Sanitizza toast notifications
   */
  sanitizeToastMessage: (message: string): string => {
    return sanitizeString(message);
  }
};

/**
 * Sanitizza file exports (CSV, PDF, JSON)
 */
export const exportSanitization = {
  /**
   * Sanitizza nome file per download
   */
  sanitizeFilename: (filename: string): string => {
    return sanitizeString(filename);
  },
  
  /**
   * Sanitizza contenuto CSV
   */
  sanitizeCsvContent: (csvData: any[]): any[] => {
    return csvData.map(row => sanitizeObject(row));
  },
  
  /**
   * Sanitizza dati JSON per export
   */
  sanitizeJsonExport: (data: any): any => {
    return sanitizeObject(data);
  },
  
  /**
   * Sanitizza testo per PDF reports
   */
  sanitizePdfContent: (content: string): string => {
    return sanitizeString(content);
  }
};

/**
 * Sanitizza dati per componenti specifici
 */
export const componentSanitization = {
  /**
   * Sanitizza dati per WorkflowCard
   */
  sanitizeWorkflowData: (workflow: any): any => {
    return sanitizeObject(workflow);
  },
  
  /**
   * Sanitizza dati per ExecutionCard
   */
  sanitizeExecutionData: (execution: any): any => {
    return sanitizeObject(execution);
  },
  
  /**
   * Sanitizza dati per AI Agent timeline
   */
  sanitizeAgentTimeline: (timeline: any[]): any[] => {
    return timeline.map(step => sanitizeObject(step));
  },
  
  /**
   * Sanitizza dati per Security dashboard
   */
  sanitizeSecurityData: (securityData: any): any => {
    return sanitizeObject(securityData);
  }
};

/**
 * Verifica se un oggetto contiene ancora riferimenti n8n
 */
export function containsN8nReferences(obj: any): boolean {
  const serialized = JSON.stringify(obj).toLowerCase();
  return serialized.includes('n8n');
}

/**
 * Hook React per sanitizzazione automatica di dati
 */
export function useSanitizedData<T>(data: T): T {
  if (!data) return data;
  return sanitizeObject(data) as T;
}

/**
 * Wrapper per console.log che sanitizza output in development
 */
export function safelog(message: string, ...args: any[]): void {
  if (process.env.NODE_ENV === 'development') {
    const sanitizedMessage = sanitizeString(message);
    const sanitizedArgs = args.map(arg => 
      typeof arg === 'string' ? sanitizeString(arg) : sanitizeObject(arg)
    );
    console.log(sanitizedMessage, ...sanitizedArgs);
  }
}

/**
 * Utility per test anti-n8n nel frontend
 */
export const debugUtils = {
  /**
   * Scansiona tutti i elementi DOM per riferimenti n8n
   */
  scanDOMForN8nReferences: (): string[] => {
    const foundReferences: string[] = [];
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      null
    );
    
    let node;
    while (node = walker.nextNode()) {
      const text = node.textContent?.toLowerCase() || '';
      if (text.includes('n8n')) {
        foundReferences.push(node.textContent || '');
      }
    }
    
    return foundReferences;
  },
  
  /**
   * Verifica localStorage per riferimenti n8n
   */
  scanLocalStorageForN8nReferences: (): string[] => {
    const foundReferences: string[] = [];
    
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key) {
        const value = localStorage.getItem(key);
        if (key.toLowerCase().includes('n8n') || value?.toLowerCase().includes('n8n')) {
          foundReferences.push(`${key}: ${value}`);
        }
      }
    }
    
    return foundReferences;
  },
  
  /**
   * Report completo di compliance frontend
   */
  generateComplianceReport: (): { clean: boolean; issues: string[] } => {
    const domIssues = debugUtils.scanDOMForN8nReferences();
    const storageIssues = debugUtils.scanLocalStorageForN8nReferences();
    const allIssues = [...domIssues, ...storageIssues];
    
    return {
      clean: allIssues.length === 0,
      issues: allIssues
    };
  }
};

export default {
  sanitizeString,
  sanitizeObject,
  sanitizeApiResponse,
  uiSanitization,
  errorSanitization,
  exportSanitization,
  componentSanitization,
  containsN8nReferences,
  useSanitizedData,
  safelog,
  debugUtils
};