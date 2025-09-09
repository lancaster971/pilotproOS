/**
 * Error Analytics Handler
 * 
 * Analizza pattern di errori, frequenze e fornisce insights
 * per migliorare l'affidabilità dei workflow.
 */

import { BaseAnalyticsHandler } from './base-handler.js';
import { ToolCallResult } from '../../types/index.js';
import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * Handler per analisi dettagliata degli errori
 */
export class ErrorAnalyticsHandler extends BaseAnalyticsHandler {
  /**
   * Esegue l'analisi degli errori nel sistema
   * 
   * @param args - Parametri opzionali: days, workflowId, limit
   * @returns Analisi dettagliata degli errori
   */
  async execute(args: Record<string, unknown>): Promise<ToolCallResult> {
    try {
      const days = (args.days as number) || 7;
      const workflowId = args.workflowId as string | undefined;
      const limit = (args.limit as number) || 100;

      // Ottieni esecuzioni con errori
      const executionParams: any = { limit };
      if (workflowId) {
        executionParams.workflowId = workflowId;
      }

      const executions = await this.apiService.listExecutions(executionParams);
      
      // Filtra esecuzioni recenti
      const recentExecutions = this.filterRecentExecutions(executions, days);
      
      // Filtra solo esecuzioni con errori
      const failedExecutions = recentExecutions.filter(e => 
        e.stoppedAt || (e.finished && e.data?.resultData?.error)
      );

      if (failedExecutions.length === 0) {
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                periodo: `Ultimi ${days} giorni`,
                messaggio: 'Nessun errore rilevato nel periodo analizzato',
                statistiche: {
                  totaleEsecuzioni: recentExecutions.length,
                  esecuzioniConSuccesso: recentExecutions.length,
                  tassoSuccesso: '100%'
                }
              }, null, 2)
            }
          ],
          isError: false
        };
      }

      // Analizza errori
      const errorAnalysis = this.performErrorAnalysis(failedExecutions, recentExecutions);
      
      // Analisi per workflow
      const workflowErrors = this.analyzeErrorsByWorkflow(failedExecutions);
      
      // Pattern temporali
      const temporalPatterns = this.analyzeTemporalPatterns(failedExecutions);
      
      // Analisi dei nodi problematici
      const nodeAnalysis = this.analyzeProblematicNodes(failedExecutions);
      
      // Correlazioni
      const correlations = this.findErrorCorrelations(failedExecutions);
      
      // Raccomandazioni
      const recommendations = this.generateRecommendations(errorAnalysis, nodeAnalysis);
      
      // Previsioni
      const predictions = this.generatePredictions(temporalPatterns, errorAnalysis);

      const response = {
        periodo: `Ultimi ${days} giorni`,
        dataAnalisi: new Date().toISOString(),
        filtro: workflowId ? `Workflow: ${workflowId}` : 'Tutti i workflow',
        
        // Riepilogo generale
        riepilogo: errorAnalysis.summary,
        
        // Categorizzazione errori
        categorieErrori: errorAnalysis.categories,
        
        // Top errori
        topErrori: errorAnalysis.topErrors,
        
        // Analisi per workflow
        errorWorkflow: workflowErrors,
        
        // Pattern temporali
        patternTemporali: temporalPatterns,
        
        // Nodi problematici
        nodiProblematici: nodeAnalysis,
        
        // Correlazioni
        correlazioni: correlations,
        
        // Raccomandazioni
        raccomandazioni: recommendations,
        
        // Previsioni
        previsioni: predictions
      };

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(response, null, 2),
          },
        ],
        isError: false,
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Filtra esecuzioni recenti
   */
  private filterRecentExecutions(executions: any[], days: number): any[] {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);
    
    return executions.filter(exec => {
      const execDate = new Date(exec.startedAt || exec.createdAt);
      return execDate >= cutoffDate;
    });
  }

  /**
   * Esegue analisi completa degli errori
   */
  private performErrorAnalysis(failedExecutions: any[], allExecutions: any[]): any {
    const totalExecutions = allExecutions.length;
    const totalErrors = failedExecutions.length;
    const errorRate = totalExecutions > 0 ? (totalErrors / totalExecutions) * 100 : 0;

    // Categorizza errori
    const categories: Record<string, { count: number; percentage: number; examples: string[] }> = {};
    const errorMessages: Record<string, number> = {};
    
    failedExecutions.forEach(exec => {
      const error = exec.data?.resultData?.error;
      if (error && error.message) {
        // Categorizza
        const category = this.categorizeError(error.message);
        if (!categories[category]) {
          categories[category] = { count: 0, percentage: 0, examples: [] };
        }
        categories[category].count++;
        if (categories[category].examples.length < 3 && !categories[category].examples.includes(error.message)) {
          categories[category].examples.push(error.message);
        }
        
        // Conta messaggi specifici
        const cleanMessage = this.cleanErrorMessage(error.message);
        errorMessages[cleanMessage] = (errorMessages[cleanMessage] || 0) + 1;
      }
    });

    // Calcola percentuali
    Object.keys(categories).forEach(cat => {
      categories[cat].percentage = Math.round((categories[cat].count / totalErrors) * 100);
    });

    // Top errori
    const topErrors = Object.entries(errorMessages)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([message, count]) => ({
        messaggio: message,
        occorrenze: count,
        percentuale: `${Math.round((count / totalErrors) * 100)}%`
      }));

    // Calcola trend
    const trend = this.calculateErrorTrend(failedExecutions, allExecutions);

    return {
      summary: {
        totaleEsecuzioni: totalExecutions,
        totaleErrori: totalErrors,
        tassoErrore: `${errorRate.toFixed(2)}%`,
        trend: trend,
        gravitàMedia: this.calculateAverageSeverity(failedExecutions)
      },
      categories,
      topErrors
    };
  }

  /**
   * Analizza errori per workflow
   */
  private analyzeErrorsByWorkflow(failedExecutions: any[]): any {
    const workflowErrors: Record<string, any> = {};
    
    failedExecutions.forEach(exec => {
      const workflowId = exec.workflowId;
      const workflowName = exec.workflowData?.name || 'Unknown';
      
      if (!workflowErrors[workflowId]) {
        workflowErrors[workflowId] = {
          nome: workflowName,
          errori: 0,
          tipiErrore: {},
          primoErrore: null,
          ultimoErrore: null,
          durataMediaErrore: []
        };
      }
      
      workflowErrors[workflowId].errori++;
      
      // Traccia tipo errore
      const error = exec.data?.resultData?.error;
      if (error) {
        const errorType = this.categorizeError(error.message || 'Unknown');
        workflowErrors[workflowId].tipiErrore[errorType] = 
          (workflowErrors[workflowId].tipiErrore[errorType] || 0) + 1;
      }
      
      // Traccia tempi
      const errorTime = new Date(exec.startedAt || exec.createdAt);
      if (!workflowErrors[workflowId].primoErrore || errorTime < new Date(workflowErrors[workflowId].primoErrore)) {
        workflowErrors[workflowId].primoErrore = errorTime.toISOString();
      }
      if (!workflowErrors[workflowId].ultimoErrore || errorTime > new Date(workflowErrors[workflowId].ultimoErrore)) {
        workflowErrors[workflowId].ultimoErrore = errorTime.toISOString();
      }
      
      // Durata se disponibile
      if (exec.executionTime) {
        workflowErrors[workflowId].durataMediaErrore.push(parseInt(exec.executionTime));
      }
    });

    // Calcola medie e ordina
    const sortedWorkflows = Object.entries(workflowErrors)
      .map(([id, data]) => {
        const avgDuration = data.durataMediaErrore.length > 0
          ? data.durataMediaErrore.reduce((a: number, b: number) => a + b, 0) / data.durataMediaErrore.length
          : 0;
        
        return {
          workflowId: id,
          ...data,
          durataMediaErrore: this.formatDuration(avgDuration),
          errorePrincipale: Object.entries(data.tipiErrore)
            .sort((a, b) => (b[1] as number) - (a[1] as number))[0]?.[0] || 'N/A'
        };
      })
      .sort((a, b) => b.errori - a.errori);

    return {
      totaleWorkflowConErrori: sortedWorkflows.length,
      top5WorkflowProblematici: sortedWorkflows.slice(0, 5),
      distribuzioneErrori: this.calculateErrorDistribution(sortedWorkflows)
    };
  }

  /**
   * Analizza pattern temporali degli errori
   */
  private analyzeTemporalPatterns(failedExecutions: any[]): any {
    // Distribuzione oraria
    const hourlyDistribution: Record<number, number> = {};
    for (let i = 0; i < 24; i++) {
      hourlyDistribution[i] = 0;
    }
    
    // Distribuzione giornaliera
    const dailyDistribution: Record<string, number> = {};
    const dayNames = ['Domenica', 'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato'];
    dayNames.forEach(day => dailyDistribution[day] = 0);
    
    // Serie temporale giornaliera
    const dailySeries: Record<string, number> = {};
    
    failedExecutions.forEach(exec => {
      const date = new Date(exec.startedAt || exec.createdAt);
      
      // Ora
      hourlyDistribution[date.getHours()]++;
      
      // Giorno settimana
      dailyDistribution[dayNames[date.getDay()]]++;
      
      // Data specifica
      const dateKey = date.toISOString().split('T')[0];
      dailySeries[dateKey] = (dailySeries[dateKey] || 0) + 1;
    });

    // Identifica picchi
    const maxHourly = Math.max(...Object.values(hourlyDistribution));
    const peakHours = Object.entries(hourlyDistribution)
      .filter(([_, count]) => count >= maxHourly * 0.8)
      .map(([hour, count]) => ({
        ora: `${hour}:00`,
        errori: count
      }));

    const maxDaily = Math.max(...Object.values(dailyDistribution));
    const peakDays = Object.entries(dailyDistribution)
      .filter(([_, count]) => count >= maxDaily * 0.8)
      .map(([day, count]) => ({
        giorno: day,
        errori: count
      }));

    // Calcola burst di errori
    const errorBursts = this.identifyErrorBursts(dailySeries);

    return {
      distribuzioneOraria: hourlyDistribution,
      distribuzioneSettimanale: dailyDistribution,
      picchiOrari: peakHours,
      picchiGiornalieri: peakDays,
      burstErrori: errorBursts,
      pattern: this.identifyPatterns(failedExecutions)
    };
  }

  /**
   * Analizza nodi problematici
   */
  private analyzeProblematicNodes(failedExecutions: any[]): any {
    const nodeErrors: Record<string, {
      count: number;
      errors: string[];
      workflows: Set<string>;
    }> = {};
    
    failedExecutions.forEach(exec => {
      const error = exec.data?.resultData?.error;
      if (error && error.node) {
        if (!nodeErrors[error.node]) {
          nodeErrors[error.node] = {
            count: 0,
            errors: [],
            workflows: new Set()
          };
        }
        
        nodeErrors[error.node].count++;
        nodeErrors[error.node].workflows.add(exec.workflowId);
        
        const errorMsg = this.cleanErrorMessage(error.message || 'Unknown error');
        if (!nodeErrors[error.node].errors.includes(errorMsg) && nodeErrors[error.node].errors.length < 3) {
          nodeErrors[error.node].errors.push(errorMsg);
        }
      }
    });

    // Ordina per frequenza errori
    const sortedNodes = Object.entries(nodeErrors)
      .map(([node, data]) => ({
        nodo: node,
        errori: data.count,
        workflowCoinvolti: data.workflows.size,
        messaggiErrore: data.errors,
        gravità: this.calculateNodeSeverity(data.count, data.workflows.size)
      }))
      .sort((a, b) => b.errori - a.errori);

    return {
      totaleNodiProblematici: sortedNodes.length,
      top10Nodi: sortedNodes.slice(0, 10),
      categorieNodi: this.categorizeProblematicNodes(sortedNodes)
    };
  }

  /**
   * Trova correlazioni tra errori
   */
  private findErrorCorrelations(failedExecutions: any[]): any {
    const correlations: any[] = [];
    
    // Correlazione errore-ora del giorno
    const hourlyErrors = this.correlateErrorsWithTime(failedExecutions);
    if (hourlyErrors.correlation) {
      correlations.push(hourlyErrors);
    }
    
    // Correlazione errore-durata esecuzione
    const durationErrors = this.correlateErrorsWithDuration(failedExecutions);
    if (durationErrors.correlation) {
      correlations.push(durationErrors);
    }
    
    // Correlazione errore-sequenza (errori che avvengono in sequenza)
    const sequentialErrors = this.findSequentialErrors(failedExecutions);
    if (sequentialErrors.length > 0) {
      correlations.push({
        tipo: 'Errori sequenziali',
        descrizione: 'Errori che tendono a verificarsi in sequenza',
        pattern: sequentialErrors
      });
    }

    return correlations.length > 0 ? correlations : { messaggio: 'Nessuna correlazione significativa trovata' };
  }

  /**
   * Genera raccomandazioni basate sull'analisi
   */
  private generateRecommendations(errorAnalysis: any, nodeAnalysis: any): string[] {
    const recommendations: string[] = [];
    
    // Raccomandazioni basate sul tasso di errore
    const errorRate = parseFloat(errorAnalysis.summary.tassoErrore);
    if (errorRate > 20) {
      recommendations.push('🚨 Alto tasso di errore: richiede intervento immediato');
    } else if (errorRate > 10) {
      recommendations.push('⚠️ Tasso di errore elevato: monitorare attentamente');
    }
    
    // Raccomandazioni per categoria errore
    Object.entries(errorAnalysis.categories).forEach(([category, data]: [string, any]) => {
      if (data.percentage > 30) {
        switch (category) {
          case 'Timeout':
            recommendations.push(`⏱️ ${category} frequenti (${data.percentage}%): aumenta timeout o ottimizza performance`);
            break;
          case 'Connessione':
            recommendations.push(`🔌 Problemi di ${category} (${data.percentage}%): verifica stabilità rete e endpoint`);
            break;
          case 'Autenticazione':
            recommendations.push(`🔐 Errori di ${category} (${data.percentage}%): verifica credenziali e permessi`);
            break;
          case 'Validazione':
            recommendations.push(`✅ Errori di ${category} (${data.percentage}%): controlla formato dati`);
            break;
          default:
            recommendations.push(`📍 ${category} frequente (${data.percentage}%): richiede analisi approfondita`);
        }
      }
    });
    
    // Raccomandazioni per nodi problematici
    if (nodeAnalysis.totaleNodiProblematici > 0) {
      const topNode = nodeAnalysis.top10Nodi[0];
      if (topNode && topNode.errori > 10) {
        recommendations.push(`🔧 Nodo "${topNode.nodo}" critico con ${topNode.errori} errori: richiede revisione`);
      }
    }
    
    // Raccomandazioni generali
    if (errorAnalysis.summary.trend === 'In aumento ⬆️') {
      recommendations.push('📈 Trend errori in aumento: investigare cause recenti');
    }
    
    if (recommendations.length === 0) {
      recommendations.push('✅ Sistema stabile con basso tasso di errore');
    }
    
    return recommendations;
  }

  /**
   * Genera previsioni basate sui pattern
   */
  private generatePredictions(temporalPatterns: any, errorAnalysis: any): any {
    const predictions: any = {
      prossime24Ore: [],
      prossimaSettimana: [],
      rischioElevato: []
    };
    
    // Previsione basata su pattern orari
    if (temporalPatterns.picchiOrari && temporalPatterns.picchiOrari.length > 0) {
      temporalPatterns.picchiOrari.forEach((peak: any) => {
        predictions.prossime24Ore.push(`Probabile picco errori alle ${peak.ora}`);
      });
    }
    
    // Previsione basata su pattern settimanali
    if (temporalPatterns.picchiGiornalieri && temporalPatterns.picchiGiornalieri.length > 0) {
      temporalPatterns.picchiGiornalieri.forEach((peak: any) => {
        predictions.prossimaSettimana.push(`Maggior rischio errori di ${peak.giorno}`);
      });
    }
    
    // Identifica situazioni ad alto rischio
    if (errorAnalysis.summary.trend === 'In aumento ⬆️') {
      predictions.rischioElevato.push('Trend in crescita: possibile aumento errori nei prossimi giorni');
    }
    
    if (temporalPatterns.burstErrori && temporalPatterns.burstErrori.length > 0) {
      predictions.rischioElevato.push('Rilevati burst di errori: monitorare per possibili picchi improvvisi');
    }
    
    return predictions;
  }

  // Metodi helper

  private cleanErrorMessage(message: string): string {
    // Rimuove dettagli specifici per raggruppare errori simili
    return message
      .replace(/\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/gi, '[ID]')
      .replace(/\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, '[IP]')
      .replace(/:[0-9]+/g, ':[PORT]')
      .replace(/\/[^\/\s]+\.[^\/\s]+/g, '/[FILE]')
      .substring(0, 100);
  }

  private calculateErrorTrend(failed: any[], all: any[]): string {
    if (failed.length < 2) return 'Stabile ➡️';
    
    // Dividi in due periodi
    const midPoint = Math.floor(all.length / 2);
    const firstHalf = all.slice(0, midPoint);
    const secondHalf = all.slice(midPoint);
    
    const firstErrors = firstHalf.filter(e => 
      failed.some(f => f.id === e.id)
    ).length;
    
    const secondErrors = secondHalf.filter(e => 
      failed.some(f => f.id === e.id)
    ).length;
    
    const firstRate = firstHalf.length > 0 ? firstErrors / firstHalf.length : 0;
    const secondRate = secondHalf.length > 0 ? secondErrors / secondHalf.length : 0;
    
    if (secondRate > firstRate * 1.2) return 'In aumento ⬆️';
    if (secondRate < firstRate * 0.8) return 'In diminuzione ⬇️';
    return 'Stabile ➡️';
  }

  private calculateAverageSeverity(failed: any[]): string {
    let totalSeverity = 0;
    
    failed.forEach(exec => {
      const error = exec.data?.resultData?.error;
      if (error) {
        const category = this.categorizeError(error.message || '');
        // Assegna gravità per categoria
        switch (category) {
          case 'Autenticazione':
          case 'Rate limit':
            totalSeverity += 3; // Alta
            break;
          case 'Timeout':
          case 'Connessione':
            totalSeverity += 2; // Media
            break;
          default:
            totalSeverity += 1; // Bassa
        }
      }
    });
    
    const avgSeverity = failed.length > 0 ? totalSeverity / failed.length : 0;
    
    if (avgSeverity >= 2.5) return 'Alta';
    if (avgSeverity >= 1.5) return 'Media';
    return 'Bassa';
  }

  private calculateErrorDistribution(workflows: any[]): any {
    const total = workflows.reduce((sum, w) => sum + w.errori, 0);
    
    return {
      top20PercWorkflows: Math.round((workflows.slice(0, Math.ceil(workflows.length * 0.2)).reduce((sum, w) => sum + w.errori, 0) / total) * 100),
      distribuzione: workflows.length <= 5 ? 'Concentrata' : 'Distribuita'
    };
  }

  private identifyErrorBursts(dailySeries: Record<string, number>): any[] {
    const bursts: any[] = [];
    const threshold = 5; // Più di 5 errori in un giorno è considerato burst
    
    Object.entries(dailySeries)
      .filter(([_, count]) => count >= threshold)
      .forEach(([date, count]) => {
        bursts.push({
          data: date,
          errori: count,
          gravità: count >= 10 ? 'Alta' : 'Media'
        });
      });
    
    return bursts.sort((a, b) => b.errori - a.errori).slice(0, 5);
  }

  private identifyPatterns(failed: any[]): string[] {
    const patterns: string[] = [];
    
    // Analizza intervalli
    const sorted = [...failed].sort((a, b) => 
      new Date(a.startedAt || a.createdAt).getTime() - 
      new Date(b.startedAt || b.createdAt).getTime()
    );
    
    if (sorted.length < 3) return ['Dati insufficienti per identificare pattern'];
    
    // Cerca cluster temporali
    let clusters = 0;
    let lastTime = new Date(sorted[0].startedAt || sorted[0].createdAt).getTime();
    
    for (let i = 1; i < sorted.length; i++) {
      const currentTime = new Date(sorted[i].startedAt || sorted[i].createdAt).getTime();
      const diff = currentTime - lastTime;
      
      if (diff < 60 * 60 * 1000) { // Meno di un'ora
        clusters++;
      }
      lastTime = currentTime;
    }
    
    if (clusters > sorted.length * 0.3) {
      patterns.push('Errori tendono a verificarsi in cluster');
    }
    
    // Cerca pattern ricorrenti
    const hours = sorted.map(e => new Date(e.startedAt || e.createdAt).getHours());
    const mostCommonHour = this.mode(hours);
    const hourFrequency = hours.filter(h => h === mostCommonHour).length / hours.length;
    
    if (hourFrequency > 0.3) {
      patterns.push(`Concentrazione errori alle ore ${mostCommonHour}:00`);
    }
    
    return patterns.length > 0 ? patterns : ['Nessun pattern evidente'];
  }

  private calculateNodeSeverity(errorCount: number, workflowCount: number): string {
    const score = errorCount * workflowCount;
    
    if (score >= 50) return 'Critica';
    if (score >= 20) return 'Alta';
    if (score >= 10) return 'Media';
    return 'Bassa';
  }

  private categorizeProblematicNodes(nodes: any[]): any {
    const categories: Record<string, string[]> = {
      critico: [],
      attenzione: [],
      monitorare: []
    };
    
    nodes.forEach(node => {
      if (node.gravità === 'Critica') {
        categories.critico.push(node.nodo);
      } else if (node.gravità === 'Alta') {
        categories.attenzione.push(node.nodo);
      } else {
        categories.monitorare.push(node.nodo);
      }
    });
    
    return categories;
  }

  private correlateErrorsWithTime(failed: any[]): any {
    const hourlyErrors: Record<number, number> = {};
    
    failed.forEach(exec => {
      const hour = new Date(exec.startedAt || exec.createdAt).getHours();
      hourlyErrors[hour] = (hourlyErrors[hour] || 0) + 1;
    });
    
    // Identifica correlazione
    const peakHours = Object.entries(hourlyErrors)
      .filter(([_, count]) => count > failed.length / 24 * 2)
      .map(([hour, _]) => parseInt(hour));
    
    if (peakHours.length > 0) {
      return {
        tipo: 'Errori-Orario',
        correlation: true,
        descrizione: `Errori concentrati nelle ore: ${peakHours.join(', ')}`,
        forza: 'Media'
      };
    }
    
    return { correlation: false };
  }

  private correlateErrorsWithDuration(failed: any[]): any {
    const longRunning = failed.filter(e => 
      e.executionTime && parseInt(e.executionTime) > 30000
    );
    
    if (longRunning.length > failed.length * 0.5) {
      return {
        tipo: 'Errori-Durata',
        correlation: true,
        descrizione: 'Errori correlati con esecuzioni lunghe (>30s)',
        percentuale: `${Math.round((longRunning.length / failed.length) * 100)}%`,
        forza: 'Alta'
      };
    }
    
    return { correlation: false };
  }

  private findSequentialErrors(failed: any[]): any[] {
    const sequential: any[] = [];
    
    // Raggruppa per workflow
    const byWorkflow: Record<string, any[]> = {};
    failed.forEach(exec => {
      if (!byWorkflow[exec.workflowId]) {
        byWorkflow[exec.workflowId] = [];
      }
      byWorkflow[exec.workflowId].push(exec);
    });
    
    // Cerca sequenze
    Object.entries(byWorkflow).forEach(([workflowId, execs]) => {
      if (execs.length < 3) return;
      
      const sorted = execs.sort((a, b) => 
        new Date(a.startedAt || a.createdAt).getTime() - 
        new Date(b.startedAt || b.createdAt).getTime()
      );
      
      let consecutiveCount = 1;
      for (let i = 1; i < sorted.length; i++) {
        const timeDiff = new Date(sorted[i].startedAt || sorted[i].createdAt).getTime() -
                        new Date(sorted[i-1].startedAt || sorted[i-1].createdAt).getTime();
        
        if (timeDiff < 60 * 60 * 1000) { // Entro un'ora
          consecutiveCount++;
        } else {
          if (consecutiveCount >= 3) {
            sequential.push({
              workflowId,
              erroriConsecutivi: consecutiveCount,
              periodo: `${this.formatDate(sorted[i - consecutiveCount].startedAt)} - ${this.formatDate(sorted[i - 1].startedAt)}`
            });
          }
          consecutiveCount = 1;
        }
      }
    });
    
    return sequential;
  }

  private mode(arr: number[]): number {
    const frequency: Record<number, number> = {};
    let maxFreq = 0;
    let mode = arr[0];
    
    arr.forEach(num => {
      frequency[num] = (frequency[num] || 0) + 1;
      if (frequency[num] > maxFreq) {
        maxFreq = frequency[num];
        mode = num;
      }
    });
    
    return mode;
  }
}

/**
 * Definizione del tool per error analytics
 */
export const errorAnalyticsTool: Tool = {
  name: 'get_error_analytics',
  description: 'Analizza pattern di errori, frequenze e fornisce insights per migliorare affidabilità',
  inputSchema: {
    type: 'object',
    properties: {
      days: {
        type: 'number',
        description: 'Numero di giorni da analizzare (default: 7)',
        minimum: 1,
        maximum: 90
      },
      workflowId: {
        type: 'string',
        description: 'ID workflow specifico da analizzare (opzionale)'
      },
      limit: {
        type: 'number',
        description: 'Limite esecuzioni da analizzare (default: 100)',
        minimum: 10,
        maximum: 1000
      }
    }
  }
};