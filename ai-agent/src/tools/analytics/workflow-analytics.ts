/**
 * Workflow Analytics Handler
 * 
 * Fornisce analisi dettagliata di un singolo workflow includendo
 * complexity score, reliability score, efficiency score e metriche avanzate.
 */

import { BaseAnalyticsHandler } from './base-handler.js';
import { ToolCallResult } from '../../types/index.js';
import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { McpError, ErrorCode } from '../../errors/index.js';

/**
 * Handler per ottenere analytics dettagliati di un workflow
 */
export class WorkflowAnalyticsHandler extends BaseAnalyticsHandler {
  /**
   * Esegue l'analisi completa di un workflow specifico
   * 
   * @param args - Deve contenere workflowId e opzionalmente days per il periodo
   * @returns Analytics dettagliati del workflow
   */
  async execute(args: Record<string, unknown>): Promise<ToolCallResult> {
    try {
      // Valida parametri richiesti
      const workflowId = args.workflowId as string;
      if (!workflowId) {
        throw new McpError(
          ErrorCode.InvalidParams,
          'Il parametro workflowId è richiesto'
        );
      }

      const days = (args.days as number) || 30; // Default ultimi 30 giorni

      // Ottieni dati workflow ed esecuzioni
      const [workflow, executions] = await Promise.all([
        this.apiService.getWorkflow(workflowId),
        this.apiService.listExecutions({ workflowId, limit: 100 })
      ]);

      // Filtra esecuzioni per periodo
      const recentExecutions = this.filterRecentExecutions(executions, days);

      // Calcola metriche base
      const baseMetrics = this.calculateBaseMetrics(workflow, recentExecutions);
      
      // Calcola scores
      const scores = this.calculateScores(workflow, recentExecutions);
      
      // Analisi nodi
      const nodeAnalysis = this.analyzeNodes(workflow, recentExecutions);
      
      // Pattern di esecuzione
      const executionPatterns = this.analyzeExecutionPatterns(recentExecutions);
      
      // Analisi errori
      const errorAnalysis = this.analyzeErrors(recentExecutions);
      
      // Trend temporali
      const trends = this.calculateTrends(recentExecutions);
      
      // Raccomandazioni
      const recommendations = this.generateRecommendations(scores, errorAnalysis, nodeAnalysis);

      // Costruisci response completa
      const analytics = {
        workflow: {
          id: workflow.id,
          nome: workflow.name,
          descrizione: workflow.description || 'Nessuna descrizione',
          stato: workflow.active ? 'Attivo' : 'Inattivo',
          tags: workflow.tags || [],
          ultimaModifica: this.formatDate(workflow.updatedAt),
          creatoIl: this.formatDate(workflow.createdAt)
        },
        
        periodo: `Ultimi ${days} giorni`,
        dataAnalisi: new Date().toISOString(),
        
        // Metriche principali
        metriche: baseMetrics,
        
        // Scores calcolati
        scores: {
          complessità: {
            valore: scores.complexity,
            descrizione: this.getComplexityDescription(scores.complexity)
          },
          affidabilità: {
            valore: scores.reliability,
            descrizione: this.getReliabilityDescription(scores.reliability)
          },
          efficienza: {
            valore: scores.efficiency,
            descrizione: this.getEfficiencyDescription(scores.efficiency)
          },
          salute: {
            valore: scores.health,
            descrizione: this.getHealthDescription(scores.health)
          }
        },
        
        // Analisi dettagliate
        analisiNodi: nodeAnalysis,
        patternEsecuzione: executionPatterns,
        analisiErrori: errorAnalysis,
        trend: trends,
        
        // Raccomandazioni
        raccomandazioni: recommendations
      };

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(analytics, null, 2),
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
   * Calcola metriche base del workflow
   */
  private calculateBaseMetrics(workflow: any, executions: any[]): any {
    const successCount = executions.filter(e => e.finished && !e.stoppedAt).length;
    const failureCount = executions.filter(e => e.stoppedAt || (e.finished && e.data?.resultData?.error)).length;
    const runningCount = executions.filter(e => !e.finished).length;
    
    const durations = executions
      .filter(e => e.finished && e.executionTime)
      .map(e => parseInt(e.executionTime));
    
    const avgDuration = durations.length > 0
      ? durations.reduce((a, b) => a + b, 0) / durations.length
      : 0;
    
    const minDuration = durations.length > 0 ? Math.min(...durations) : 0;
    const maxDuration = durations.length > 0 ? Math.max(...durations) : 0;
    
    // Calcola deviazione standard
    const stdDev = this.calculateStandardDeviation(durations);

    return {
      esecuzioniTotali: executions.length,
      successi: successCount,
      fallimenti: failureCount,
      inCorso: runningCount,
      tassoSuccesso: executions.length > 0 
        ? `${Math.round((successCount / executions.length) * 100)}%`
        : 'N/A',
      durataMedia: this.formatDuration(avgDuration),
      durataMinima: this.formatDuration(minDuration),
      durataMassima: this.formatDuration(maxDuration),
      deviazioneStandard: this.formatDuration(stdDev),
      numeroNodi: workflow.nodes?.length || 0,
      numeroConnessioni: workflow.connections ? Object.keys(workflow.connections).length : 0
    };
  }

  /**
   * Calcola tutti gli scores del workflow
   */
  private calculateScores(workflow: any, executions: any[]): any {
    const nodeCount = workflow.nodes?.length || 0;
    const connectionCount = workflow.connections ? Object.keys(workflow.connections).length : 0;
    const uniqueNodeTypes = workflow.nodes 
      ? new Set(workflow.nodes.map((n: any) => n.type)).size 
      : 0;
    
    const successCount = executions.filter(e => e.finished && !e.stoppedAt).length;
    
    const durations = executions
      .filter(e => e.finished && e.executionTime)
      .map(e => parseInt(e.executionTime));
    
    const avgDuration = durations.length > 0
      ? durations.reduce((a, b) => a + b, 0) / durations.length
      : 0;

    const complexity = this.calculateComplexityScore(nodeCount, connectionCount, uniqueNodeTypes);
    const reliability = this.calculateReliabilityScore(successCount, executions.length);
    const efficiency = this.calculateEfficiencyScore(avgDuration);
    
    // Health score è una media ponderata degli altri scores
    const health = Math.round((reliability * 0.5 + efficiency * 0.3 + (100 - complexity) * 0.2));

    return {
      complexity,
      reliability,
      efficiency,
      health
    };
  }

  /**
   * Analizza i nodi del workflow
   */
  private analyzeNodes(workflow: any, executions: any[]): any {
    if (!workflow.nodes || workflow.nodes.length === 0) {
      return { messaggio: 'Nessun nodo presente nel workflow' };
    }

    // Conta tipi di nodi
    const nodeTypes: Record<string, number> = {};
    const nodesByCategory: Record<string, string[]> = {
      trigger: [],
      action: [],
      logic: [],
      data: []
    };

    workflow.nodes.forEach((node: any) => {
      nodeTypes[node.type] = (nodeTypes[node.type] || 0) + 1;
      
      // Categorizza nodi
      const category = this.categorizeNode(node.type);
      nodesByCategory[category].push(node.name);
    });

    // Analizza nodi critici (quelli con più connessioni)
    const criticalNodes = this.identifyCriticalNodes(workflow);

    // Identifica nodi che causano errori (se disponibile dai dati di esecuzione)
    const errorProneNodes = this.identifyErrorProneNodes(executions);

    return {
      totaleNodi: workflow.nodes.length,
      tipiNodi: nodeTypes,
      categorieNodi: {
        trigger: nodesByCategory.trigger,
        azioni: nodesByCategory.action,
        logica: nodesByCategory.logic,
        dati: nodesByCategory.data
      },
      nodiCritici: criticalNodes,
      nodiProblematici: errorProneNodes,
      complessitàConnessioni: this.analyzeConnectionComplexity(workflow)
    };
  }

  /**
   * Analizza pattern di esecuzione
   */
  private analyzeExecutionPatterns(executions: any[]): any {
    if (executions.length === 0) {
      return { messaggio: 'Nessuna esecuzione disponibile per l\'analisi' };
    }

    // Distribuzione per giorno della settimana
    const dayDistribution: Record<string, number> = {
      'Lunedì': 0, 'Martedì': 0, 'Mercoledì': 0, 'Giovedì': 0,
      'Venerdì': 0, 'Sabato': 0, 'Domenica': 0
    };
    
    const dayNames = ['Domenica', 'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato'];
    
    // Distribuzione oraria
    const hourlyDistribution: Record<number, number> = {};
    for (let i = 0; i < 24; i++) {
      hourlyDistribution[i] = 0;
    }

    executions.forEach(exec => {
      const date = new Date(exec.startedAt || exec.createdAt);
      const dayName = dayNames[date.getDay()];
      const hour = date.getHours();
      
      dayDistribution[dayName]++;
      hourlyDistribution[hour]++;
    });

    // Trova picchi
    const maxHourly = Math.max(...Object.values(hourlyDistribution));
    const peakHours = Object.entries(hourlyDistribution)
      .filter(([_, count]) => count === maxHourly)
      .map(([hour, _]) => parseInt(hour));

    const maxDaily = Math.max(...Object.values(dayDistribution));
    const peakDays = Object.entries(dayDistribution)
      .filter(([_, count]) => count === maxDaily)
      .map(([day, _]) => day);

    // Calcola frequenza media
    const totalDays = this.calculateDaySpan(executions);
    const avgExecutionsPerDay = totalDays > 0 ? (executions.length / totalDays).toFixed(2) : 0;

    return {
      distribuzioneGiornaliera: dayDistribution,
      distribuzioneOraria: hourlyDistribution,
      giorniPicco: peakDays,
      orePicco: peakHours,
      frequenzaMedia: `${avgExecutionsPerDay} esecuzioni/giorno`,
      patternRicorrenti: this.identifyRecurringPatterns(executions)
    };
  }

  /**
   * Analizza gli errori
   */
  private analyzeErrors(executions: any[]): any {
    const failedExecutions = executions.filter(e => 
      e.stoppedAt || (e.finished && e.data?.resultData?.error)
    );

    if (failedExecutions.length === 0) {
      return {
        totaleErrori: 0,
        tassoErrore: '0%',
        messaggio: 'Nessun errore rilevato nel periodo analizzato'
      };
    }

    // Categorizza errori
    const errorTypes: Record<string, number> = {};
    const errorNodes: Record<string, number> = {};
    const errorMessages: string[] = [];

    failedExecutions.forEach(exec => {
      const error = exec.data?.resultData?.error;
      if (error) {
        const errorType = this.categorizeError(error.message || 'Errore sconosciuto');
        errorTypes[errorType] = (errorTypes[errorType] || 0) + 1;
        
        if (error.node) {
          errorNodes[error.node] = (errorNodes[error.node] || 0) + 1;
        }
        
        if (error.message && !errorMessages.includes(error.message)) {
          errorMessages.push(error.message);
        }
      }
    });

    // Calcola trend errori
    const errorTrend = this.calculateErrorTrend(failedExecutions);

    return {
      totaleErrori: failedExecutions.length,
      tassoErrore: `${Math.round((failedExecutions.length / executions.length) * 100)}%`,
      tipiErrore: errorTypes,
      nodiConErrori: errorNodes,
      messaggiErrore: errorMessages.slice(0, 5), // Top 5 messaggi
      trendErrori: errorTrend,
      raccomandazioni: this.generateErrorRecommendations(errorTypes)
    };
  }

  /**
   * Calcola trend temporali
   */
  private calculateTrends(executions: any[]): any {
    if (executions.length < 2) {
      return { messaggio: 'Dati insufficienti per calcolare trend' };
    }

    // Ordina per data
    const sortedExecs = [...executions].sort((a, b) => 
      new Date(a.startedAt || a.createdAt).getTime() - 
      new Date(b.startedAt || b.createdAt).getTime()
    );

    // Dividi in periodi per confronto
    const midPoint = Math.floor(sortedExecs.length / 2);
    const firstHalf = sortedExecs.slice(0, midPoint);
    const secondHalf = sortedExecs.slice(midPoint);

    // Calcola metriche per ogni periodo
    const firstHalfStats = this.calculatePeriodStats(firstHalf);
    const secondHalfStats = this.calculatePeriodStats(secondHalf);

    // Calcola variazioni
    const successRateChange = secondHalfStats.successRate - firstHalfStats.successRate;
    const avgDurationChange = secondHalfStats.avgDuration - firstHalfStats.avgDuration;
    const volumeChange = secondHalf.length - firstHalf.length;

    return {
      primoperiodo: firstHalfStats,
      secondoPeriodo: secondHalfStats,
      variazioni: {
        tassoSuccesso: `${successRateChange > 0 ? '+' : ''}${successRateChange.toFixed(1)}%`,
        durataMedia: `${avgDurationChange > 0 ? '+' : ''}${this.formatDuration(avgDurationChange)}`,
        volume: `${volumeChange > 0 ? '+' : ''}${volumeChange} esecuzioni`,
        trend: this.determineTrend(successRateChange, avgDurationChange, volumeChange)
      }
    };
  }

  /**
   * Genera raccomandazioni basate sull'analisi
   */
  private generateRecommendations(scores: any, errorAnalysis: any, nodeAnalysis: any): string[] {
    const recommendations: string[] = [];

    // Raccomandazioni basate sugli scores
    if (scores.complexity > 70) {
      recommendations.push('⚠️ Workflow molto complesso: considera di suddividerlo in workflow più piccoli');
    }
    
    if (scores.reliability < 70) {
      recommendations.push('🔧 Bassa affidabilità: analizza e risolvi gli errori frequenti');
    }
    
    if (scores.efficiency < 50) {
      recommendations.push('🐌 Bassa efficienza: ottimizza i nodi lenti o riduci le operazioni');
    }

    // Raccomandazioni basate sugli errori
    if (errorAnalysis.totaleErrori > 0) {
      const mainErrorType = Object.entries(errorAnalysis.tipiErrore || {})
        .sort((a, b) => (b[1] as number) - (a[1] as number))[0];
      
      if (mainErrorType) {
        recommendations.push(`🚨 Errore principale "${mainErrorType[0]}": verifica configurazione e connessioni`);
      }
    }

    // Raccomandazioni basate sui nodi
    if (nodeAnalysis.nodiProblematici && nodeAnalysis.nodiProblematici.length > 0) {
      recommendations.push(`📍 Nodi problematici identificati: ${nodeAnalysis.nodiProblematici.join(', ')}`);
    }

    if (nodeAnalysis.totaleNodi > 20) {
      recommendations.push('📊 Numero elevato di nodi: valuta se semplificare il flusso');
    }

    // Se tutto va bene
    if (recommendations.length === 0) {
      recommendations.push('✅ Workflow in buona salute, continua a monitorare le performance');
    }

    return recommendations;
  }

  // Metodi helper

  private calculateStandardDeviation(values: number[]): number {
    if (values.length === 0) return 0;
    
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const squaredDiffs = values.map(value => Math.pow(value - mean, 2));
    const avgSquaredDiff = squaredDiffs.reduce((a, b) => a + b, 0) / values.length;
    
    return Math.sqrt(avgSquaredDiff);
  }

  private categorizeNode(nodeType: string): string {
    const type = nodeType.toLowerCase();
    
    if (type.includes('trigger') || type.includes('webhook') || type.includes('cron')) {
      return 'trigger';
    }
    if (type.includes('http') || type.includes('api') || type.includes('request')) {
      return 'action';
    }
    if (type.includes('if') || type.includes('switch') || type.includes('loop')) {
      return 'logic';
    }
    
    return 'data';
  }

  private identifyCriticalNodes(workflow: any): string[] {
    if (!workflow.connections) return [];
    
    const connectionCount: Record<string, number> = {};
    
    Object.values(workflow.connections).forEach((connections: any) => {
      Object.keys(connections).forEach(nodeName => {
        connectionCount[nodeName] = (connectionCount[nodeName] || 0) + 1;
      });
    });
    
    // Nodi con più di 3 connessioni sono considerati critici
    return Object.entries(connectionCount)
      .filter(([_, count]) => count > 3)
      .map(([name, _]) => name);
  }

  private identifyErrorProneNodes(executions: any[]): string[] {
    const errorNodes: Record<string, number> = {};
    
    executions
      .filter(e => e.data?.resultData?.error?.node)
      .forEach(exec => {
        const nodeName = exec.data.resultData.error.node;
        errorNodes[nodeName] = (errorNodes[nodeName] || 0) + 1;
      });
    
    // Ritorna nodi con più di 2 errori
    return Object.entries(errorNodes)
      .filter(([_, count]) => count > 2)
      .map(([name, _]) => name);
  }

  private analyzeConnectionComplexity(workflow: any): string {
    if (!workflow.connections) return 'Semplice';
    
    const connectionCount = Object.keys(workflow.connections).length;
    const nodeCount = workflow.nodes?.length || 0;
    
    if (nodeCount === 0) return 'N/A';
    
    const ratio = connectionCount / nodeCount;
    
    if (ratio < 1) return 'Semplice';
    if (ratio < 1.5) return 'Moderata';
    if (ratio < 2) return 'Complessa';
    return 'Molto complessa';
  }

  private calculateDaySpan(executions: any[]): number {
    if (executions.length === 0) return 0;
    
    const dates = executions.map(e => new Date(e.startedAt || e.createdAt).getTime());
    const minDate = Math.min(...dates);
    const maxDate = Math.max(...dates);
    
    return Math.ceil((maxDate - minDate) / (1000 * 60 * 60 * 24)) || 1;
  }

  private identifyRecurringPatterns(executions: any[]): string[] {
    const patterns: string[] = [];
    
    // Analizza intervalli tra esecuzioni
    const sortedExecs = [...executions].sort((a, b) => 
      new Date(a.startedAt || a.createdAt).getTime() - 
      new Date(b.startedAt || b.createdAt).getTime()
    );
    
    if (sortedExecs.length < 2) return patterns;
    
    const intervals: number[] = [];
    for (let i = 1; i < sortedExecs.length; i++) {
      const interval = new Date(sortedExecs[i].startedAt || sortedExecs[i].createdAt).getTime() -
                      new Date(sortedExecs[i-1].startedAt || sortedExecs[i-1].createdAt).getTime();
      intervals.push(interval);
    }
    
    // Cerca pattern comuni
    const hourlyInterval = 60 * 60 * 1000;
    const dailyInterval = 24 * hourlyInterval;
    
    const hourlyCount = intervals.filter(i => Math.abs(i - hourlyInterval) < 5 * 60 * 1000).length;
    const dailyCount = intervals.filter(i => Math.abs(i - dailyInterval) < hourlyInterval).length;
    
    if (hourlyCount > intervals.length * 0.3) {
      patterns.push('Esecuzione oraria');
    }
    if (dailyCount > intervals.length * 0.3) {
      patterns.push('Esecuzione giornaliera');
    }
    
    return patterns.length > 0 ? patterns : ['Nessun pattern ricorrente identificato'];
  }

  private calculateErrorTrend(failedExecutions: any[]): string {
    if (failedExecutions.length < 2) return 'Stabile';
    
    // Ordina per data
    const sorted = [...failedExecutions].sort((a, b) => 
      new Date(a.startedAt || a.createdAt).getTime() - 
      new Date(b.startedAt || b.createdAt).getTime()
    );
    
    // Confronta prima e seconda metà
    const midPoint = Math.floor(sorted.length / 2);
    const firstHalf = sorted.slice(0, midPoint).length;
    const secondHalf = sorted.slice(midPoint).length;
    
    if (secondHalf > firstHalf * 1.2) return 'In aumento ⬆️';
    if (secondHalf < firstHalf * 0.8) return 'In diminuzione ⬇️';
    return 'Stabile ➡️';
  }

  private generateErrorRecommendations(errorTypes: Record<string, number>): string[] {
    const recommendations: string[] = [];
    
    Object.entries(errorTypes).forEach(([type, count]) => {
      if (count > 3) {
        switch (type) {
          case 'Timeout':
            recommendations.push('Aumenta i timeout o ottimizza le operazioni lente');
            break;
          case 'Connessione':
            recommendations.push('Verifica la connettività di rete e gli endpoint');
            break;
          case 'Autenticazione':
            recommendations.push('Controlla le credenziali e i permessi');
            break;
          case 'Validazione':
            recommendations.push('Verifica i dati di input e le validazioni');
            break;
        }
      }
    });
    
    return recommendations;
  }

  private calculatePeriodStats(executions: any[]): any {
    const successCount = executions.filter(e => e.finished && !e.stoppedAt).length;
    const durations = executions
      .filter(e => e.finished && e.executionTime)
      .map(e => parseInt(e.executionTime));
    
    const avgDuration = durations.length > 0
      ? durations.reduce((a, b) => a + b, 0) / durations.length
      : 0;
    
    return {
      esecuzioni: executions.length,
      successi: successCount,
      successRate: executions.length > 0 ? (successCount / executions.length) * 100 : 0,
      avgDuration: Math.round(avgDuration)
    };
  }

  private determineTrend(successChange: number, durationChange: number, volumeChange: number): string {
    if (successChange > 5 && durationChange < 0) return 'Miglioramento ⬆️';
    if (successChange < -5 || durationChange > 1000) return 'Peggioramento ⬇️';
    if (volumeChange > 10) return 'Crescita volume 📈';
    if (volumeChange < -10) return 'Calo volume 📉';
    return 'Stabile ➡️';
  }

  private getComplexityDescription(score: number): string {
    if (score < 30) return 'Molto semplice';
    if (score < 50) return 'Semplice';
    if (score < 70) return 'Moderatamente complesso';
    if (score < 85) return 'Complesso';
    return 'Molto complesso';
  }

  private getReliabilityDescription(score: number): string {
    if (score >= 95) return 'Eccellente';
    if (score >= 85) return 'Molto buona';
    if (score >= 70) return 'Buona';
    if (score >= 50) return 'Sufficiente';
    return 'Scarsa';
  }

  private getEfficiencyDescription(score: number): string {
    if (score >= 90) return 'Molto efficiente';
    if (score >= 70) return 'Efficiente';
    if (score >= 50) return 'Moderata';
    if (score >= 30) return 'Lenta';
    return 'Molto lenta';
  }

  private getHealthDescription(score: number): string {
    if (score >= 85) return 'Ottima salute';
    if (score >= 70) return 'Buona salute';
    if (score >= 50) return 'Salute discreta';
    if (score >= 30) return 'Necessita attenzione';
    return 'Critico';
  }
}

/**
 * Definizione del tool per workflow analytics
 */
export const workflowAnalyticsTool: Tool = {
  name: 'get_workflow_analytics',
  description: 'Ottiene analytics dettagliati di un workflow specifico con scores e metriche avanzate',
  inputSchema: {
    type: 'object',
    properties: {
      workflowId: {
        type: 'string',
        description: 'ID del workflow da analizzare'
      },
      days: {
        type: 'number',
        description: 'Numero di giorni da analizzare (default: 30)',
        minimum: 1,
        maximum: 365
      }
    },
    required: ['workflowId']
  }
};