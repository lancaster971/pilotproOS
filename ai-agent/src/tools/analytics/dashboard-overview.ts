/**
 * Dashboard Overview Handler
 * 
 * Fornisce una vista unificata di tutte le metriche del sistema n8n.
 * Aggrega dati da workflow, esecuzioni e metriche di performance.
 */

import { BaseAnalyticsHandler } from './base-handler.js';
import { ToolCallResult } from '../../types/index.js';
import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * Handler per ottenere una dashboard overview completa
 */
export class DashboardOverviewHandler extends BaseAnalyticsHandler {
  /**
   * Esegue la richiesta per ottenere la dashboard overview
   * 
   * @param args - Argomenti (opzionale: days per periodo analisi)
   * @returns Dashboard con metriche aggregate
   */
  async execute(args: Record<string, unknown>): Promise<ToolCallResult> {
    try {
      const days = (args.days as number) || 7; // Default ultimi 7 giorni

      // Ottieni dati dai vari endpoint
      const [workflows, executions] = await Promise.all([
        this.apiService.listWorkflows(),
        this.apiService.listExecutions({ limit: 100 })
      ]);

      // Calcola metriche aggregate
      const totalWorkflows = workflows.length;
      const activeWorkflows = workflows.filter((w: any) => w.active).length;
      const inactiveWorkflows = totalWorkflows - activeWorkflows;

      // Analizza esecuzioni
      const recentExecutions = this.filterRecentExecutions(executions, days);
      const executionStats = this.calculateExecutionStats(recentExecutions);
      
      // Calcola metriche per workflow
      const workflowMetrics = this.calculateWorkflowMetrics(workflows, recentExecutions);
      
      // Identifica workflow problematici
      const problematicWorkflows = this.identifyProblematicWorkflows(workflowMetrics);
      
      // Top performers
      const topPerformers = this.getTopPerformers(workflowMetrics);

      // Crea dashboard response
      const dashboard = {
        periodo: `Ultimi ${days} giorni`,
        dataAggiornamento: new Date().toISOString(),
        
        // Metriche generali
        riepilogo: {
          totaleWorkflow: totalWorkflows,
          workflowAttivi: activeWorkflows,
          workflowInattivi: inactiveWorkflows,
          tassoAttivazione: `${Math.round((activeWorkflows / totalWorkflows) * 100)}%`
        },
        
        // Statistiche esecuzioni
        esecuzioni: {
          totale: executionStats.total,
          successo: executionStats.success,
          fallite: executionStats.failed,
          inCorso: executionStats.running,
          tassoSuccesso: `${executionStats.successRate}%`,
          durataMedia: this.formatDuration(executionStats.avgDuration),
          tempoTotaleEsecuzione: this.formatDuration(executionStats.totalDuration)
        },
        
        // Performance
        performance: {
          workflowPiuVeloce: topPerformers.fastest,
          workflowPiuLento: topPerformers.slowest,
          workflowPiuAffidabile: topPerformers.mostReliable,
          workflowMenoAffidabile: topPerformers.leastReliable
        },
        
        // Alert e problemi
        alert: {
          workflowProblematici: problematicWorkflows.length,
          dettagli: problematicWorkflows
        },
        
        // Trend orari (simulato per ora)
        trendOrari: this.calculateHourlyTrend(recentExecutions),
        
        // Distribuzione errori
        distribuzioneErrori: this.calculateErrorDistribution(recentExecutions)
      };

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(dashboard, null, 2),
          },
        ],
        isError: false,
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Filtra le esecuzioni recenti in base al periodo
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
   * Calcola statistiche aggregate delle esecuzioni
   */
  private calculateExecutionStats(executions: any[]): any {
    const total = executions.length;
    const success = executions.filter(e => e.finished && !e.stoppedAt).length;
    const failed = executions.filter(e => e.stoppedAt || (e.finished && e.data?.resultData?.error)).length;
    const running = executions.filter(e => !e.finished).length;
    
    const durations = executions
      .filter(e => e.finished && e.executionTime)
      .map(e => parseInt(e.executionTime));
    
    const avgDuration = durations.length > 0 
      ? durations.reduce((a, b) => a + b, 0) / durations.length 
      : 0;
    
    const totalDuration = durations.reduce((a, b) => a + b, 0);

    return {
      total,
      success,
      failed,
      running,
      successRate: total > 0 ? Math.round((success / total) * 100) : 0,
      avgDuration: Math.round(avgDuration),
      totalDuration
    };
  }

  /**
   * Calcola metriche per ogni workflow
   */
  private calculateWorkflowMetrics(workflows: any[], executions: any[]): any[] {
    return workflows.map(workflow => {
      const workflowExecs = executions.filter(e => e.workflowId === workflow.id);
      const successExecs = workflowExecs.filter(e => e.finished && !e.stoppedAt);
      
      const durations = workflowExecs
        .filter(e => e.finished && e.executionTime)
        .map(e => parseInt(e.executionTime));
      
      const avgDuration = durations.length > 0
        ? durations.reduce((a, b) => a + b, 0) / durations.length
        : 0;

      // Calcola scores
      const nodeCount = workflow.nodes?.length || 0;
      const connectionCount = workflow.connections ? Object.keys(workflow.connections).length : 0;
      const uniqueNodeTypes = workflow.nodes 
        ? new Set(workflow.nodes.map((n: any) => n.type)).size 
        : 0;

      return {
        id: workflow.id,
        name: workflow.name,
        active: workflow.active,
        executions: workflowExecs.length,
        successCount: successExecs.length,
        failureCount: workflowExecs.length - successExecs.length,
        avgDuration: Math.round(avgDuration),
        complexityScore: this.calculateComplexityScore(nodeCount, connectionCount, uniqueNodeTypes),
        reliabilityScore: this.calculateReliabilityScore(successExecs.length, workflowExecs.length),
        efficiencyScore: this.calculateEfficiencyScore(avgDuration)
      };
    });
  }

  /**
   * Identifica workflow con problemi
   */
  private identifyProblematicWorkflows(metrics: any[]): any[] {
    return metrics
      .filter(m => {
        // Criteri per workflow problematico
        return (
          m.reliabilityScore < 70 || // Bassa affidabilità
          m.failureCount > 5 || // Molti fallimenti
          (m.executions > 0 && m.successCount === 0) // Nessun successo
        );
      })
      .map(m => ({
        id: m.id,
        nome: m.name,
        problemi: [
          m.reliabilityScore < 70 ? `Bassa affidabilità: ${m.reliabilityScore}%` : null,
          m.failureCount > 5 ? `Alto numero di fallimenti: ${m.failureCount}` : null,
          (m.executions > 0 && m.successCount === 0) ? 'Nessuna esecuzione con successo' : null
        ].filter(Boolean),
        metriche: {
          affidabilità: `${m.reliabilityScore}%`,
          esecuzioni: m.executions,
          fallimenti: m.failureCount
        }
      }));
  }

  /**
   * Ottiene i top performer per varie categorie
   */
  private getTopPerformers(metrics: any[]): any {
    const activeMetrics = metrics.filter(m => m.executions > 0);
    
    if (activeMetrics.length === 0) {
      return {
        fastest: null,
        slowest: null,
        mostReliable: null,
        leastReliable: null
      };
    }

    // Ordina per velocità
    const bySpeed = [...activeMetrics].sort((a, b) => a.avgDuration - b.avgDuration);
    
    // Ordina per affidabilità
    const byReliability = [...activeMetrics].sort((a, b) => b.reliabilityScore - a.reliabilityScore);

    return {
      fastest: bySpeed[0] ? {
        nome: bySpeed[0].name,
        durataMedia: this.formatDuration(bySpeed[0].avgDuration)
      } : null,
      slowest: bySpeed[bySpeed.length - 1] ? {
        nome: bySpeed[bySpeed.length - 1].name,
        durataMedia: this.formatDuration(bySpeed[bySpeed.length - 1].avgDuration)
      } : null,
      mostReliable: byReliability[0] ? {
        nome: byReliability[0].name,
        affidabilità: `${byReliability[0].reliabilityScore}%`
      } : null,
      leastReliable: byReliability[byReliability.length - 1] ? {
        nome: byReliability[byReliability.length - 1].name,
        affidabilità: `${byReliability[byReliability.length - 1].reliabilityScore}%`
      } : null
    };
  }

  /**
   * Calcola trend orario delle esecuzioni
   */
  private calculateHourlyTrend(executions: any[]): any {
    const hourlyCount: Record<number, number> = {};
    
    // Inizializza tutte le ore
    for (let i = 0; i < 24; i++) {
      hourlyCount[i] = 0;
    }
    
    // Conta esecuzioni per ora
    executions.forEach(exec => {
      const date = new Date(exec.startedAt || exec.createdAt);
      const hour = date.getHours();
      hourlyCount[hour]++;
    });

    // Trova ore di picco
    const maxCount = Math.max(...Object.values(hourlyCount));
    const peakHours = Object.entries(hourlyCount)
      .filter(([_, count]) => count === maxCount)
      .map(([hour, _]) => parseInt(hour));

    return {
      distribuzioneOraria: hourlyCount,
      oreDiPicco: peakHours,
      esecuzioniPicco: maxCount
    };
  }

  /**
   * Calcola distribuzione degli errori
   */
  private calculateErrorDistribution(executions: any[]): any {
    const errors: Record<string, number> = {};
    
    executions
      .filter(e => e.data?.resultData?.error)
      .forEach(exec => {
        const errorMessage = exec.data.resultData.error.message || 'Errore sconosciuto';
        const errorType = this.categorizeError(errorMessage);
        errors[errorType] = (errors[errorType] || 0) + 1;
      });

    return {
      totaleErrori: Object.values(errors).reduce((a, b) => a + b, 0),
      tipiErrore: errors,
      errorePiuFrequente: Object.entries(errors).sort((a, b) => b[1] - a[1])[0] || null
    };
  }

}

/**
 * Definizione del tool per la dashboard overview
 */
export const dashboardOverviewTool: Tool = {
  name: 'get_dashboard_overview',
  description: 'Ottiene una dashboard completa con metriche aggregate del sistema n8n',
  inputSchema: {
    type: 'object',
    properties: {
      days: {
        type: 'number',
        description: 'Numero di giorni da analizzare (default: 7)',
        minimum: 1,
        maximum: 90
      }
    }
  }
};