/**
 * Middleware di sanitizzazione globale per nascondere riferimenti n8n dal cliente
 * REGOLA FERREA: Il cliente NON deve mai sapere che sotto c'è n8n
 */

import { Request, Response, NextFunction } from 'express';

/**
 * Mappatura termini da sostituire per privacy cliente
 */
const SANITIZATION_MAP = {
  // Node types - CRITICO per nascondere implementazione
  'n8n-nodes-base': 'WFEngine.core',
  'n8n-nodes-': 'WFEngine.',
  '@n8n/': '@WFEngine/',
  
  // Nomi prodotto
  'n8n': 'WFEngine',
  'N8N': 'WFEngine',
  
  // Error messages comuni
  'n8n API': 'Workflow Engine API',
  'n8n server': 'Workflow Engine server',
  'n8n instance': 'Workflow Engine instance',
  'n8n workflow': 'automation workflow',
  'n8n execution': 'workflow execution',
  
  // URL e paths
  '/n8n/': '/wfengine/',
  'n8n.io': 'workflowengine.local',
  
  // Variabili e configurazioni
  'N8N_': 'WFENGINE_',
  'n8n_': 'wfengine_',
};

/**
 * Sanitizza ricorsivamente un oggetto sostituendo tutti i riferimenti n8n
 */
function sanitizeObject(obj: any): any {
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
      // Sanitizza sia la chiave che il valore
      const sanitizedKey = sanitizeString(key);
      sanitized[sanitizedKey] = sanitizeObject(value);
    }
    return sanitized;
  }
  
  return obj;
}

/**
 * Sanitizza una stringa sostituendo tutti i riferimenti n8n
 */
function sanitizeString(str: string): string {
  if (typeof str !== 'string') {
    return str;
  }
  
  let sanitized = str;
  
  // Applica tutte le sostituzioni dalla mappa
  for (const [search, replace] of Object.entries(SANITIZATION_MAP)) {
    // Case insensitive replacement per maggiore copertura
    const regex = new RegExp(search.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
    sanitized = sanitized.replace(regex, replace);
  }
  
  return sanitized;
}

/**
 * Middleware Express per sanitizzazione automatica delle response
 */
export function sanitizationMiddleware(req: Request, res: Response, next: NextFunction) {
  // Salva il metodo originale json
  const originalJson = res.json.bind(res);
  
  // Override del metodo json per sanitizzare automaticamente
  res.json = function(body: any) {
    try {
      // Sanitizza il body della response
      const sanitizedBody = sanitizeObject(body);
      
      // Log per debugging (solo in development)
      if (process.env.NODE_ENV === 'development') {
        const hasN8nReferences = JSON.stringify(body).toLowerCase().includes('n8n');
        if (hasN8nReferences) {
          console.log('🔒 Sanitization applied to response:', req.path);
        }
      }
      
      return originalJson(sanitizedBody);
    } catch (error) {
      console.error('❌ Sanitization error:', error);
      // In caso di errore, passa il body originale per non bloccare l'API
      return originalJson(body);
    }
  };
  
  next();
}

/**
 * Utility per sanitizzazione manuale quando necessaria
 */
export const sanitizationUtils = {
  sanitizeObject,
  sanitizeString,
  
  // Sanitizza specificamente i nodeTypes per workflow
  sanitizeNodeTypes: (nodeTypes: string[]): string[] => {
    return nodeTypes.map(nodeType => sanitizeString(nodeType));
  },
  
  // Sanitizza i nomi dei workflow
  sanitizeWorkflowName: (name: string): string => {
    return sanitizeString(name);
  },
  
  // Sanitizza i messaggi di errore
  sanitizeErrorMessage: (message: string): string => {
    return sanitizeString(message);
  },
  
  // Sanitizza raw data JSON dal database
  sanitizeRawData: (rawData: any): any => {
    return sanitizeObject(rawData);
  }
};

/**
 * Verifica se un oggetto contiene ancora riferimenti n8n
 * Utile per testing e debugging
 */
export function containsN8nReferences(obj: any): boolean {
  const serialized = JSON.stringify(obj).toLowerCase();
  return serialized.includes('n8n');
}

/**
 * Lista di warning per sviluppatori quando trovano riferimenti n8n
 */
export function validateNoN8nReferences(obj: any, context: string = 'unknown'): void {
  if (containsN8nReferences(obj)) {
    console.warn(`⚠️ N8N reference found in ${context}. Cliente NON deve vedere questo!`);
    console.warn('🔒 Applicare sanitizzazione prima di inviare al frontend');
  }
}