/**
 * Base Handler per Analytics
 * 
 * Classe base per tutti gli handler degli strumenti di analytics.
 * Fornisce gestione errori e utilità comuni per l'analisi dei dati.
 */

import { ToolCallResult } from '../../types/index.js';
import { McpError, ErrorCode } from '../../errors/index.js';
import { getEnvConfig } from '../../config/environment.js';
import { createApiService, N8nApiService } from '../../api/n8n-client.js';

/**
 * Classe base astratta per gli handler degli analytics
 */
export abstract class BaseAnalyticsHandler {
  private _apiService: N8nApiService | null = null;
  
  protected get apiService(): N8nApiService {
    if (!this._apiService) {
      const envConfig = getEnvConfig();
      this._apiService = createApiService(envConfig);
    }
    return this._apiService;
  }

  /**
   * Metodo astratto che deve essere implementato dalle sottoclassi
   * 
   * @param args - Argomenti passati al tool
   * @returns Risultato dell'esecuzione del tool
   */
  abstract execute(args: Record<string, unknown>): Promise<ToolCallResult>;

  /**
   * Gestisce gli errori e li converte in formato ToolCallResult
   * 
   * @param error - Errore da gestire
   * @returns Risultato con errore formattato
   */
  protected handleError(error: unknown): ToolCallResult {
    console.error('Errore nell\'handler analytics:', error);

    if (error instanceof McpError) {
      return {
        content: [
          {
            type: 'text',
            text: `Errore: ${error.message}`,
          },
        ],
        isError: true,
      };
    }

    if (error instanceof Error) {
      return {
        content: [
          {
            type: 'text',
            text: `Errore: ${error.message}`,
          },
        ],
        isError: true,
      };
    }

    return {
      content: [
        {
          type: 'text',
          text: 'Si è verificato un errore sconosciuto',
        },
      ],
      isError: true,
    };
  }

  /**
   * Calcola il complexity score di un workflow
   * 
   * @param nodeCount - Numero di nodi
   * @param connectionCount - Numero di connessioni
   * @param uniqueNodeTypes - Numero di tipi di nodi unici
   * @returns Complexity score calcolato
   */
  protected calculateComplexityScore(
    nodeCount: number, 
    connectionCount: number, 
    uniqueNodeTypes: number
  ): number {
    // Formula: base sui nodi + bonus per connessioni + bonus per diversità
    const baseScore = nodeCount * 10;
    const connectionBonus = connectionCount * 5;
    const diversityBonus = uniqueNodeTypes * 15;
    
    return Math.min(100, (baseScore + connectionBonus + diversityBonus) / 3);
  }

  /**
   * Calcola il reliability score basato sul success rate
   * 
   * @param successCount - Numero di esecuzioni con successo
   * @param totalCount - Numero totale di esecuzioni
   * @returns Reliability score come percentuale
   */
  protected calculateReliabilityScore(successCount: number, totalCount: number): number {
    if (totalCount === 0) return 0;
    return Math.round((successCount / totalCount) * 100);
  }

  /**
   * Calcola l'efficiency score basato sui tempi di esecuzione
   * 
   * @param avgDuration - Durata media in ms
   * @param targetDuration - Durata target ottimale in ms (default 5000ms)
   * @returns Efficiency score da 0 a 100
   */
  protected calculateEfficiencyScore(avgDuration: number, targetDuration: number = 5000): number {
    if (avgDuration === 0) return 100;
    
    // Score massimo se sotto il target, diminuisce progressivamente oltre
    if (avgDuration <= targetDuration) {
      return 100;
    }
    
    // Diminuisce di 10 punti ogni raddoppio del tempo target
    const ratio = avgDuration / targetDuration;
    const score = Math.max(0, 100 - (Math.log2(ratio) * 20));
    
    return Math.round(score);
  }

  /**
   * Formatta una data in formato leggibile
   * 
   * @param date - Data da formattare
   * @returns Stringa con data formattata
   */
  protected formatDate(date: Date | string): string {
    const d = typeof date === 'string' ? new Date(date) : date;
    return d.toLocaleString('it-IT', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  /**
   * Formatta una durata in ms in formato leggibile
   * 
   * @param durationMs - Durata in millisecondi
   * @returns Stringa con durata formattata
   */
  protected formatDuration(durationMs: number): string {
    if (durationMs < 1000) {
      return `${durationMs}ms`;
    } else if (durationMs < 60000) {
      return `${(durationMs / 1000).toFixed(1)}s`;
    } else if (durationMs < 3600000) {
      return `${Math.floor(durationMs / 60000)}m ${Math.floor((durationMs % 60000) / 1000)}s`;
    } else {
      return `${Math.floor(durationMs / 3600000)}h ${Math.floor((durationMs % 3600000) / 60000)}m`;
    }
  }

  /**
   * Categorizza un errore in base al messaggio
   * 
   * @param errorMessage - Messaggio di errore da categorizzare
   * @returns Categoria dell'errore
   */
  protected categorizeError(errorMessage: string): string {
    const lowerMessage = errorMessage.toLowerCase();
    
    if (lowerMessage.includes('timeout')) return 'Timeout';
    if (lowerMessage.includes('connection') || lowerMessage.includes('network')) return 'Connessione';
    if (lowerMessage.includes('auth') || lowerMessage.includes('permission')) return 'Autenticazione';
    if (lowerMessage.includes('not found') || lowerMessage.includes('404')) return 'Risorsa non trovata';
    if (lowerMessage.includes('rate limit')) return 'Rate limit';
    if (lowerMessage.includes('validation') || lowerMessage.includes('invalid')) return 'Validazione';
    
    return 'Altro';
  }
}