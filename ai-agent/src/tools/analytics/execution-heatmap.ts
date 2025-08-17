/**
 * Execution Heatmap Handler
 * 
 * Genera una mappa calore delle esecuzioni per identificare
 * pattern di utilizzo e picchi di attività.
 */

import { BaseAnalyticsHandler } from './base-handler.js';
import { ToolCallResult } from '../../types/index.js';
import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * Handler per generare heatmap delle esecuzioni
 */
export class ExecutionHeatmapHandler extends BaseAnalyticsHandler {
  /**
   * Genera la heatmap delle esecuzioni
   * 
   * @param args - Parametri: days, workflowId (opzionale)
   * @returns Heatmap con distribuzione temporale delle esecuzioni
   */
  async execute(args: Record<string, unknown>): Promise<ToolCallResult> {
    try {
      const days = (args.days as number) || 7;
      const workflowId = args.workflowId as string | undefined;

      // Ottieni esecuzioni
      const executionParams: any = { limit: 500 }; // Più esecuzioni per heatmap accurata
      if (workflowId) {
        executionParams.workflowId = workflowId;
      }

      const executions = await this.apiService.listExecutions(executionParams);
      
      // Filtra esecuzioni recenti
      const recentExecutions = this.filterRecentExecutions(executions, days);

      if (recentExecutions.length === 0) {
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                periodo: `Ultimi ${days} giorni`,
                messaggio: 'Nessuna esecuzione trovata nel periodo specificato'
              }, null, 2)
            }
          ],
          isError: false
        };
      }

      // Genera heatmap principale
      const mainHeatmap = this.generateMainHeatmap(recentExecutions);
      
      // Statistiche per ora del giorno
      const hourlyStats = this.calculateHourlyStatistics(recentExecutions);
      
      // Statistiche per giorno della settimana
      const weekdayStats = this.calculateWeekdayStatistics(recentExecutions);
      
      // Matrice ora x giorno
      const hourDayMatrix = this.generateHourDayMatrix(recentExecutions);
      
      // Pattern identificati
      const patterns = this.identifyActivityPatterns(mainHeatmap, hourlyStats, weekdayStats);
      
      // Previsioni basate su pattern
      const predictions = this.generateActivityPredictions(patterns, hourlyStats, weekdayStats);
      
      // Analisi carico di lavoro
      const workloadAnalysis = this.analyzeWorkload(recentExecutions);
      
      // Raccomandazioni per ottimizzazione
      const optimizations = this.generateOptimizationRecommendations(patterns, workloadAnalysis);

      const response = {
        periodo: `Ultimi ${days} giorni`,
        dataGenerazione: new Date().toISOString(),
        filtro: workflowId ? `Workflow: ${workflowId}` : 'Tutti i workflow',
        totaleEsecuzioni: recentExecutions.length,
        
        // Heatmap principale (intensità attività)
        heatmap: mainHeatmap,
        
        // Statistiche orarie
        statisticheOrarie: hourlyStats,
        
        // Statistiche per giorno settimana
        statisticheGiornaliere: weekdayStats,
        
        // Matrice bidimensionale ora x giorno
        matriceOraGiorno: hourDayMatrix,
        
        // Pattern identificati
        patternAttività: patterns,
        
        // Previsioni
        previsioni: predictions,
        
        // Analisi carico
        analisiCarico: workloadAnalysis,
        
        // Ottimizzazioni suggerite
        ottimizzazioni: optimizations,
        
        // Visualizzazione ASCII della heatmap
        visualizzazione: this.generateASCIIHeatmap(hourDayMatrix)
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
   * Genera la heatmap principale
   */
  private generateMainHeatmap(executions: any[]): any {
    // Crea struttura per ogni ora di ogni giorno
    const heatmapData: Record<string, Record<number, {
      count: number;
      success: number;
      failed: number;
      avgDuration: number;
      durations: number[];
    }>> = {};

    executions.forEach(exec => {
      const date = new Date(exec.startedAt || exec.createdAt);
      const dateKey = date.toISOString().split('T')[0];
      const hour = date.getHours();
      
      if (!heatmapData[dateKey]) {
        heatmapData[dateKey] = {};
      }
      
      if (!heatmapData[dateKey][hour]) {
        heatmapData[dateKey][hour] = {
          count: 0,
          success: 0,
          failed: 0,
          avgDuration: 0,
          durations: []
        };
      }
      
      heatmapData[dateKey][hour].count++;
      
      if (exec.finished && !exec.stoppedAt) {
        heatmapData[dateKey][hour].success++;
      } else if (exec.stoppedAt || (exec.finished && exec.data?.resultData?.error)) {
        heatmapData[dateKey][hour].failed++;
      }
      
      if (exec.executionTime) {
        heatmapData[dateKey][hour].durations.push(parseInt(exec.executionTime));
      }
    });

    // Calcola medie
    Object.values(heatmapData).forEach(dayData => {
      Object.values(dayData).forEach(hourData => {
        if (hourData.durations.length > 0) {
          hourData.avgDuration = hourData.durations.reduce((a, b) => a + b, 0) / hourData.durations.length;
        }
      });
    });

    // Trova valori min/max per normalizzazione
    let maxCount = 0;
    let minCount = Infinity;
    
    Object.values(heatmapData).forEach(dayData => {
      Object.values(dayData).forEach(hourData => {
        maxCount = Math.max(maxCount, hourData.count);
        minCount = Math.min(minCount, hourData.count);
      });
    });

    // Aggiungi intensità normalizzata
    const processedData: any = {};
    Object.entries(heatmapData).forEach(([date, dayData]) => {
      processedData[date] = {};
      Object.entries(dayData).forEach(([hour, hourData]) => {
        const intensity = maxCount > 0 ? (hourData.count / maxCount) : 0;
        processedData[date][hour] = {
          ...hourData,
          avgDuration: Math.round(hourData.avgDuration),
          intensità: Math.round(intensity * 100),
          livello: this.getIntensityLevel(intensity)
        };
      });
    });

    return {
      dati: processedData,
      statistiche: {
        massimoEsecuzioniOra: maxCount,
        minimoEsecuzioniOra: minCount === Infinity ? 0 : minCount,
        mediaEsecuzioniOra: this.calculateAverageExecutionsPerHour(executions)
      }
    };
  }

  /**
   * Calcola statistiche orarie
   */
  private calculateHourlyStatistics(executions: any[]): any {
    const hourlyData: Record<number, {
      count: number;
      success: number;
      failed: number;
      avgDuration: number[];
    }> = {};

    // Inizializza tutte le ore
    for (let h = 0; h < 24; h++) {
      hourlyData[h] = { count: 0, success: 0, failed: 0, avgDuration: [] };
    }

    executions.forEach(exec => {
      const hour = new Date(exec.startedAt || exec.createdAt).getHours();
      hourlyData[hour].count++;
      
      if (exec.finished && !exec.stoppedAt) {
        hourlyData[hour].success++;
      } else if (exec.stoppedAt || (exec.finished && exec.data?.resultData?.error)) {
        hourlyData[hour].failed++;
      }
      
      if (exec.executionTime) {
        hourlyData[hour].avgDuration.push(parseInt(exec.executionTime));
      }
    });

    // Calcola statistiche finali
    const stats: any = {};
    Object.entries(hourlyData).forEach(([hour, data]) => {
      const avgDuration = data.avgDuration.length > 0
        ? data.avgDuration.reduce((a, b) => a + b, 0) / data.avgDuration.length
        : 0;
      
      stats[`${hour}:00`] = {
        esecuzioni: data.count,
        successi: data.success,
        fallimenti: data.failed,
        tassoSuccesso: data.count > 0 ? `${Math.round((data.success / data.count) * 100)}%` : 'N/A',
        durataMedia: this.formatDuration(avgDuration),
        intensità: this.calculateIntensityLevel(data.count, executions.length)
      };
    });

    // Identifica ore di picco
    const sorted = Object.entries(hourlyData).sort((a, b) => b[1].count - a[1].count);
    const peakHours = sorted.slice(0, 3).map(([hour, data]) => ({
      ora: `${hour}:00`,
      esecuzioni: data.count,
      percentuale: `${Math.round((data.count / executions.length) * 100)}%`
    }));

    return {
      dettaglio: stats,
      orePicco: peakHours,
      oreInattive: Object.entries(hourlyData)
        .filter(([_, data]) => data.count === 0)
        .map(([hour, _]) => `${hour}:00`)
    };
  }

  /**
   * Calcola statistiche per giorno della settimana
   */
  private calculateWeekdayStatistics(executions: any[]): any {
    const dayNames = ['Domenica', 'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato'];
    const weekdayData: Record<string, {
      count: number;
      success: number;
      failed: number;
      avgDuration: number[];
    }> = {};

    // Inizializza tutti i giorni
    dayNames.forEach(day => {
      weekdayData[day] = { count: 0, success: 0, failed: 0, avgDuration: [] };
    });

    executions.forEach(exec => {
      const dayName = dayNames[new Date(exec.startedAt || exec.createdAt).getDay()];
      weekdayData[dayName].count++;
      
      if (exec.finished && !exec.stoppedAt) {
        weekdayData[dayName].success++;
      } else if (exec.stoppedAt || (exec.finished && exec.data?.resultData?.error)) {
        weekdayData[dayName].failed++;
      }
      
      if (exec.executionTime) {
        weekdayData[dayName].avgDuration.push(parseInt(exec.executionTime));
      }
    });

    // Calcola statistiche finali
    const stats: any = {};
    Object.entries(weekdayData).forEach(([day, data]) => {
      const avgDuration = data.avgDuration.length > 0
        ? data.avgDuration.reduce((a, b) => a + b, 0) / data.avgDuration.length
        : 0;
      
      stats[day] = {
        esecuzioni: data.count,
        successi: data.success,
        fallimenti: data.failed,
        tassoSuccesso: data.count > 0 ? `${Math.round((data.success / data.count) * 100)}%` : 'N/A',
        durataMedia: this.formatDuration(avgDuration),
        percentualeTotale: `${Math.round((data.count / executions.length) * 100)}%`
      };
    });

    // Identifica giorni più attivi
    const sorted = Object.entries(weekdayData).sort((a, b) => b[1].count - a[1].count);
    const mostActiveDays = sorted.slice(0, 3).map(([day, data]) => ({
      giorno: day,
      esecuzioni: data.count,
      percentuale: `${Math.round((data.count / executions.length) * 100)}%`
    }));

    return {
      dettaglio: stats,
      giorniPiùAttivi: mostActiveDays,
      weekend: {
        esecuzioni: weekdayData['Sabato'].count + weekdayData['Domenica'].count,
        percentuale: `${Math.round(((weekdayData['Sabato'].count + weekdayData['Domenica'].count) / executions.length) * 100)}%`
      }
    };
  }

  /**
   * Genera matrice ora x giorno
   */
  private generateHourDayMatrix(executions: any[]): any {
    const dayNames = ['Dom', 'Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab'];
    const matrix: Record<string, Record<string, number>> = {};
    
    // Inizializza matrice
    dayNames.forEach(day => {
      matrix[day] = {};
      for (let h = 0; h < 24; h++) {
        matrix[day][h.toString()] = 0;
      }
    });

    // Popola matrice
    executions.forEach(exec => {
      const date = new Date(exec.startedAt || exec.createdAt);
      const dayName = dayNames[date.getDay()];
      const hour = date.getHours();
      matrix[dayName][hour.toString()]++;
    });

    // Trova valori max per ogni giorno e ora
    const maxByDay: Record<string, number> = {};
    const maxByHour: Record<string, number> = {};
    
    dayNames.forEach(day => {
      maxByDay[day] = Math.max(...Object.values(matrix[day]));
    });
    
    for (let h = 0; h < 24; h++) {
      maxByHour[h.toString()] = Math.max(...dayNames.map(d => matrix[d][h.toString()]));
    }

    return {
      matrice: matrix,
      maxPerGiorno: maxByDay,
      maxPerOra: maxByHour,
      hotspots: this.identifyHotspots(matrix)
    };
  }

  /**
   * Identifica pattern di attività
   */
  private identifyActivityPatterns(heatmap: any, hourlyStats: any, weekdayStats: any): any {
    const patterns: any = {
      tipoAttività: '',
      picchiRegolari: [],
      periodiInattivi: [],
      distribuzioneCarico: '',
      consistenza: ''
    };

    // Determina tipo di attività
    const activeHours = Object.values(hourlyStats.dettaglio).filter((h: any) => h.esecuzioni > 0).length;
    if (activeHours < 8) {
      patterns.tipoAttività = 'Concentrata';
    } else if (activeHours < 16) {
      patterns.tipoAttività = 'Orario lavorativo';
    } else {
      patterns.tipoAttività = '24/7';
    }

    // Identifica picchi regolari
    const peakThreshold = this.calculateAverageExecutionsPerHour(heatmap.dati) * 2;
    Object.entries(hourlyStats.dettaglio).forEach(([hour, data]: [string, any]) => {
      if (data.esecuzioni > peakThreshold) {
        patterns.picchiRegolari.push({
          ora: hour,
          intensità: 'Alta',
          esecuzioni: data.esecuzioni
        });
      }
    });

    // Periodi inattivi
    patterns.periodiInattivi = hourlyStats.oreInattive;

    // Distribuzione carico
    const weekendActivity = weekdayStats.weekend.esecuzioni;
    const totalActivity = Object.values(weekdayStats.dettaglio).reduce((sum: number, d: any) => sum + d.esecuzioni, 0);
    const weekendRatio = weekendActivity / totalActivity;
    
    if (weekendRatio < 0.1) {
      patterns.distribuzioneCarico = 'Solo giorni lavorativi';
    } else if (weekendRatio < 0.25) {
      patterns.distribuzioneCarico = 'Principalmente giorni lavorativi';
    } else {
      patterns.distribuzioneCarico = 'Uniforme';
    }

    // Consistenza
    const stdDev = this.calculateActivityStdDev(Object.values(hourlyStats.dettaglio).map((h: any) => h.esecuzioni));
    const mean = totalActivity / 24;
    const cv = mean > 0 ? stdDev / mean : 0;
    
    if (cv < 0.5) {
      patterns.consistenza = 'Molto consistente';
    } else if (cv < 1) {
      patterns.consistenza = 'Moderatamente consistente';
    } else {
      patterns.consistenza = 'Altamente variabile';
    }

    return patterns;
  }

  /**
   * Genera previsioni di attività
   */
  private generateActivityPredictions(patterns: any, hourlyStats: any, weekdayStats: any): any {
    const predictions: any = {
      prossimeOre: [],
      prossimiGiorni: [],
      picchiPrevisti: [],
      caricoStimato: {}
    };

    // Previsioni basate su pattern orari
    const currentHour = new Date().getHours();
    const nextHours = [currentHour, (currentHour + 1) % 24, (currentHour + 2) % 24];
    
    nextHours.forEach(hour => {
      const hourKey = `${hour}:00`;
      const data = hourlyStats.dettaglio[hourKey];
      if (data && data.esecuzioni > 0) {
        predictions.prossimeOre.push({
          ora: hourKey,
          esecuzioniPreviste: data.esecuzioni,
          probabilità: data.intensità
        });
      }
    });

    // Previsioni per i prossimi giorni
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dayNames = ['Domenica', 'Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato'];
    
    for (let i = 0; i < 3; i++) {
      const futureDate = new Date(tomorrow);
      futureDate.setDate(futureDate.getDate() + i);
      const dayName = dayNames[futureDate.getDay()];
      const dayData = weekdayStats.dettaglio[dayName];
      
      if (dayData) {
        predictions.prossimiGiorni.push({
          giorno: dayName,
          data: futureDate.toISOString().split('T')[0],
          esecuzioniPreviste: dayData.esecuzioni,
          confidenza: this.calculateConfidence(dayData.esecuzioni, Object.values(weekdayStats.dettaglio))
        });
      }
    }

    // Picchi previsti
    patterns.picchiRegolari.forEach((peak: any) => {
      predictions.picchiPrevisti.push({
        quando: peak.ora,
        intensitàPrevista: peak.intensità,
        esecuzioniStimate: peak.esecuzioni
      });
    });

    // Carico stimato per la prossima settimana
    const weekTotal = Object.values(weekdayStats.dettaglio).reduce((sum: number, d: any) => sum + d.esecuzioni, 0);
    predictions.caricoStimato = {
      settimanale: weekTotal,
      giornaliero: Math.round(weekTotal / 7),
      orario: Math.round(weekTotal / (7 * 24))
    };

    return predictions;
  }

  /**
   * Analizza il carico di lavoro
   */
  private analyzeWorkload(executions: any[]): any {
    // Calcola metriche di carico
    const totalDuration = executions
      .filter(e => e.executionTime)
      .reduce((sum, e) => sum + parseInt(e.executionTime), 0);
    
    const concurrentExecutions = this.calculateConcurrency(executions);
    
    // Identifica sovraccarichi
    const overloads = this.identifyOverloads(executions);
    
    // Calcola utilizzo risorse
    const resourceUtilization = this.calculateResourceUtilization(executions);

    return {
      metriche: {
        esecuzioniTotali: executions.length,
        tempoTotaleEsecuzione: this.formatDuration(totalDuration),
        esecuzioniConcorrenti: concurrentExecutions,
        utilizzoRisorse: resourceUtilization
      },
      sovraccarichi: overloads,
      distribuzione: this.analyzeLoadDistribution(executions),
      raccomandazioni: this.generateLoadRecommendations(concurrentExecutions, overloads)
    };
  }

  /**
   * Genera raccomandazioni per ottimizzazione
   */
  private generateOptimizationRecommendations(patterns: any, workload: any): string[] {
    const recommendations: string[] = [];

    // Raccomandazioni basate su pattern
    if (patterns.tipoAttività === 'Concentrata') {
      recommendations.push('⏰ Attività concentrata in poche ore: considera di distribuire il carico');
    }
    
    if (patterns.periodiInattivi.length > 12) {
      recommendations.push('💤 Molte ore inattive: possibilità di sfruttare meglio le risorse');
    }
    
    if (patterns.consistenza === 'Altamente variabile') {
      recommendations.push('📊 Alta variabilità: implementa meccanismi di load balancing');
    }

    // Raccomandazioni basate su carico
    if (workload.sovraccarichi.length > 0) {
      recommendations.push('⚠️ Rilevati picchi di sovraccarico: aumenta capacità o implementa queue management');
    }
    
    if (workload.metriche.esecuzioniConcorrenti.max > 10) {
      recommendations.push('🔄 Alte esecuzioni concorrenti: verifica limiti di sistema');
    }

    // Raccomandazioni generali
    if (patterns.distribuzioneCarico === 'Solo giorni lavorativi') {
      recommendations.push('📅 Nessuna attività weekend: valuta automazioni per maintenance weekend');
    }

    if (recommendations.length === 0) {
      recommendations.push('✅ Distribuzione del carico ottimale');
    }

    return recommendations;
  }

  // Metodi helper

  private getIntensityLevel(intensity: number): string {
    if (intensity >= 0.8) return 'Molto alta';
    if (intensity >= 0.6) return 'Alta';
    if (intensity >= 0.4) return 'Media';
    if (intensity >= 0.2) return 'Bassa';
    return 'Molto bassa';
  }

  private calculateAverageExecutionsPerHour(data: any): number {
    let totalCount = 0;
    let hourCount = 0;
    
    if (typeof data === 'object' && data.dati) {
      // Per heatmap data
      Object.values(data.dati).forEach((dayData: any) => {
        Object.values(dayData).forEach((hourData: any) => {
          totalCount += hourData.count;
          hourCount++;
        });
      });
    } else if (Array.isArray(data)) {
      // Per array di esecuzioni
      return data.length / (24 * 7); // Media settimanale
    }
    
    return hourCount > 0 ? totalCount / hourCount : 0;
  }

  private calculateIntensityLevel(count: number, total: number): string {
    const percentage = (count / total) * 100;
    if (percentage >= 10) return 'Molto alta';
    if (percentage >= 7) return 'Alta';
    if (percentage >= 4) return 'Media';
    if (percentage >= 2) return 'Bassa';
    return 'Molto bassa';
  }

  private identifyHotspots(matrix: Record<string, Record<string, number>>): any[] {
    const hotspots: any[] = [];
    const allValues: number[] = [];
    
    // Raccogli tutti i valori
    Object.values(matrix).forEach(dayData => {
      Object.values(dayData).forEach(count => {
        allValues.push(count);
      });
    });
    
    // Calcola threshold per hotspot (top 10%)
    allValues.sort((a, b) => b - a);
    const threshold = allValues[Math.floor(allValues.length * 0.1)] || 1;
    
    // Identifica hotspots
    Object.entries(matrix).forEach(([day, dayData]) => {
      Object.entries(dayData).forEach(([hour, count]) => {
        if (count >= threshold && count > 0) {
          hotspots.push({
            giorno: day,
            ora: `${hour}:00`,
            esecuzioni: count,
            intensità: 'Alta'
          });
        }
      });
    });
    
    return hotspots.sort((a, b) => b.esecuzioni - a.esecuzioni).slice(0, 10);
  }

  private calculateActivityStdDev(values: number[]): number {
    if (values.length === 0) return 0;
    
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const squaredDiffs = values.map(value => Math.pow(value - mean, 2));
    const avgSquaredDiff = squaredDiffs.reduce((a, b) => a + b, 0) / values.length;
    
    return Math.sqrt(avgSquaredDiff);
  }

  private calculateConfidence(value: number, allValues: any[]): string {
    const values = allValues.map(v => v.esecuzioni || 0);
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const stdDev = this.calculateActivityStdDev(values);
    
    if (stdDev === 0) return 'Alta';
    
    const zScore = Math.abs((value - mean) / stdDev);
    if (zScore < 1) return 'Alta';
    if (zScore < 2) return 'Media';
    return 'Bassa';
  }

  private calculateConcurrency(executions: any[]): any {
    const concurrentCounts: number[] = [];
    
    executions.forEach(exec => {
      const start = new Date(exec.startedAt || exec.createdAt).getTime();
      const end = exec.finishedAt ? new Date(exec.finishedAt).getTime() : start + (parseInt(exec.executionTime) || 0);
      
      let concurrent = 0;
      executions.forEach(other => {
        if (other.id === exec.id) return;
        
        const otherStart = new Date(other.startedAt || other.createdAt).getTime();
        const otherEnd = other.finishedAt ? new Date(other.finishedAt).getTime() : otherStart + (parseInt(other.executionTime) || 0);
        
        // Controlla sovrapposizione
        if ((start >= otherStart && start <= otherEnd) || 
            (end >= otherStart && end <= otherEnd) ||
            (start <= otherStart && end >= otherEnd)) {
          concurrent++;
        }
      });
      
      concurrentCounts.push(concurrent);
    });
    
    return {
      max: Math.max(...concurrentCounts, 0),
      media: concurrentCounts.length > 0 ? concurrentCounts.reduce((a, b) => a + b, 0) / concurrentCounts.length : 0,
      min: Math.min(...concurrentCounts, 0)
    };
  }

  private identifyOverloads(executions: any[]): any[] {
    const overloads: any[] = [];
    const threshold = 10; // Più di 10 esecuzioni in un'ora è considerato sovraccarico
    
    // Raggruppa per ora
    const hourlyGroups: Record<string, any[]> = {};
    executions.forEach(exec => {
      const date = new Date(exec.startedAt || exec.createdAt);
      const hourKey = `${date.toISOString().split('T')[0]} ${date.getHours()}:00`;
      
      if (!hourlyGroups[hourKey]) {
        hourlyGroups[hourKey] = [];
      }
      hourlyGroups[hourKey].push(exec);
    });
    
    // Identifica sovraccarichi
    Object.entries(hourlyGroups)
      .filter(([_, execs]) => execs.length >= threshold)
      .forEach(([hour, execs]) => {
        overloads.push({
          periodo: hour,
          esecuzioni: execs.length,
          gravità: execs.length >= threshold * 2 ? 'Alta' : 'Media',
          durataMedia: this.formatDuration(
            execs.filter(e => e.executionTime)
              .reduce((sum, e) => sum + parseInt(e.executionTime), 0) / execs.length
          )
        });
      });
    
    return overloads.sort((a, b) => b.esecuzioni - a.esecuzioni);
  }

  private calculateResourceUtilization(executions: any[]): string {
    // Stima utilizzo risorse basato su esecuzioni e durata
    const totalTime = 7 * 24 * 60 * 60 * 1000; // Una settimana in ms
    const executionTime = executions
      .filter(e => e.executionTime)
      .reduce((sum, e) => sum + parseInt(e.executionTime), 0);
    
    const utilization = (executionTime / totalTime) * 100;
    
    if (utilization < 10) return 'Basso (<10%)';
    if (utilization < 30) return 'Moderato (10-30%)';
    if (utilization < 60) return 'Alto (30-60%)';
    return 'Molto alto (>60%)';
  }

  private analyzeLoadDistribution(executions: any[]): any {
    // Analizza come il carico è distribuito nel tempo
    const distribution: Record<string, number> = {
      mattina: 0,     // 6-12
      pomeriggio: 0,  // 12-18
      sera: 0,        // 18-24
      notte: 0        // 0-6
    };
    
    executions.forEach(exec => {
      const hour = new Date(exec.startedAt || exec.createdAt).getHours();
      
      if (hour >= 6 && hour < 12) distribution.mattina++;
      else if (hour >= 12 && hour < 18) distribution.pomeriggio++;
      else if (hour >= 18 && hour < 24) distribution.sera++;
      else distribution.notte++;
    });
    
    const total = executions.length;
    
    return {
      mattina: `${Math.round((distribution.mattina / total) * 100)}%`,
      pomeriggio: `${Math.round((distribution.pomeriggio / total) * 100)}%`,
      sera: `${Math.round((distribution.sera / total) * 100)}%`,
      notte: `${Math.round((distribution.notte / total) * 100)}%`,
      tipologia: this.determineLoadType(distribution, total)
    };
  }

  private determineLoadType(distribution: Record<string, number>, total: number): string {
    const percentages = Object.entries(distribution).map(([period, count]) => ({
      period,
      percentage: (count / total) * 100
    }));
    
    const max = Math.max(...percentages.map(p => p.percentage));
    const dominant = percentages.find(p => p.percentage === max);
    
    if (max > 50) {
      return `Concentrato ${dominant?.period}`;
    }
    
    const variance = this.calculateActivityStdDev(percentages.map(p => p.percentage));
    if (variance < 5) {
      return 'Uniforme';
    }
    
    return 'Variabile';
  }

  private generateLoadRecommendations(concurrency: any, overloads: any[]): string[] {
    const recommendations: string[] = [];
    
    if (concurrency.max > 20) {
      recommendations.push('Implementa throttling per limitare esecuzioni concorrenti');
    }
    
    if (overloads.length > 5) {
      recommendations.push('Frequenti sovraccarichi: considera scaling orizzontale');
    }
    
    if (concurrency.media < 1) {
      recommendations.push('Bassa concorrenza: possibile sotto-utilizzo risorse');
    }
    
    return recommendations;
  }

  private generateASCIIHeatmap(matrix: any): string {
    const { matrice } = matrix;
    const days = ['Dom', 'Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab'];
    let ascii = '\n    Heatmap Esecuzioni (Ora x Giorno)\n';
    ascii += '    ';
    
    // Header ore
    for (let h = 0; h < 24; h++) {
      ascii += h.toString().padStart(3, ' ');
    }
    ascii += '\n';
    
    // Righe per giorno
    days.forEach(day => {
      ascii += day + ' ';
      for (let h = 0; h < 24; h++) {
        const value = matrice[day][h.toString()];
        const symbol = this.getHeatmapSymbol(value);
        ascii += ' ' + symbol + ' ';
      }
      ascii += '\n';
    });
    
    ascii += '\n    Legenda: · (0) ░ (1-2) ▒ (3-5) ▓ (6-9) █ (10+)\n';
    
    return ascii;
  }

  private getHeatmapSymbol(value: number): string {
    if (value === 0) return '·';
    if (value <= 2) return '░';
    if (value <= 5) return '▒';
    if (value <= 9) return '▓';
    return '█';
  }
}

/**
 * Definizione del tool per execution heatmap
 */
export const executionHeatmapTool: Tool = {
  name: 'get_execution_heatmap',
  description: 'Genera una mappa calore delle esecuzioni per identificare pattern e picchi di attività',
  inputSchema: {
    type: 'object',
    properties: {
      days: {
        type: 'number',
        description: 'Numero di giorni da analizzare (default: 7)',
        minimum: 1,
        maximum: 30
      },
      workflowId: {
        type: 'string',
        description: 'ID workflow specifico da analizzare (opzionale)'
      }
    }
  }
};