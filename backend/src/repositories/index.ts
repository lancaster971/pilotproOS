/**
 * Database Repositories Index
 * 
 * Esporta tutti i repository per accesso centralizzato.
 * I repository gestiscono l'accesso ai dati nel database.
 */

// Esporta repository base
export { BaseRepository } from './base.repository.js';

// Esporta repository specifici
export { WorkflowRepository } from './workflow.repository.js';
export { ExecutionRepository } from './execution.repository.js';
export { AnalyticsRepository } from './analytics.repository.js';

// Singleton instances per evitare duplicazioni
import { WorkflowRepository } from './workflow.repository.js';
import { ExecutionRepository } from './execution.repository.js';
import { AnalyticsRepository } from './analytics.repository.js';

/**
 * Istanze singleton dei repository
 * Utilizzare queste istanze invece di creare nuove istanze
 */
export const repositories = {
  workflows: new WorkflowRepository(),
  executions: new ExecutionRepository(),
  analytics: new AnalyticsRepository()
};

/**
 * Helper per inizializzare tutti i repository
 * Utile per verificare connessione database all'avvio
 */
export async function initializeRepositories(): Promise<boolean> {
  try {
    // Verifica connessione database con query semplici
    await Promise.all([
      repositories.workflows.count(),
      repositories.executions.count(),
      repositories.analytics.count()
    ]);
    
    console.log('✅ Repository inizializzati con successo');
    return true;
  } catch (error) {
    console.error('❌ Errore inizializzazione repository:', error);
    return false;
  }
}

/**
 * Helper per ottenere statistiche sui repository
 * Utile per monitoring e debugging
 */
export async function getRepositoryStats(): Promise<{
  workflows: { total: number; active: number };
  executions: { total: number; running: number; last24h: number };
  kpiSnapshots: { total: number; lastSnapshot: Date | null };
}> {
  const [workflowCount, activeWorkflows, executionCount, runningExecutions, recentExecutions, snapshotCount, lastSnapshot] = await Promise.all([
    repositories.workflows.count(),
    repositories.workflows.count({ active: true }),
    repositories.executions.count(),
    repositories.executions.findRunning().then(r => r.length),
    repositories.executions.count({ 
      started_at: { 
        min: new Date(Date.now() - 24 * 60 * 60 * 1000) 
      } 
    }),
    repositories.analytics.count(),
    repositories.analytics.findAll({ 
      orderBy: 'snapshot_date', 
      orderDir: 'DESC', 
      limit: 1 
    }).then(r => r[0]?.snapshot_date || null)
  ]);

  return {
    workflows: {
      total: workflowCount,
      active: activeWorkflows
    },
    executions: {
      total: executionCount,
      running: runningExecutions,
      last24h: recentExecutions
    },
    kpiSnapshots: {
      total: snapshotCount,
      lastSnapshot
    }
  };
}

/**
 * Type guards per repository
 */
export function isWorkflowRepository(repo: any): repo is WorkflowRepository {
  return repo instanceof WorkflowRepository;
}

export function isExecutionRepository(repo: any): repo is ExecutionRepository {
  return repo instanceof ExecutionRepository;
}

export function isAnalyticsRepository(repo: any): repo is AnalyticsRepository {
  return repo instanceof AnalyticsRepository;
}