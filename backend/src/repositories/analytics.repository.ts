/**
 * Analytics Repository
 * 
 * Repository per la gestione di KPI, metriche e analisi aggregate.
 * Fornisce metodi per calcolare, aggregare e recuperare dati analitici.
 */

import { BaseRepository } from './base.repository.js';
import {
  KpiSnapshotModel,
  PeriodType,
  HourlyStatsModel,
  PerformanceBenchmarkModel,
  TagModel,
  WorkflowTagModel,
  GlobalMetrics,
  TrendDirection,
  TemporalPattern,
  PatternType,
  KpiComparison,
  calculatePercentile,
  calculateMTBF,
  calculateMTTR,
  detectTrend,
  calculateGlobalHealthScore,
  PaginatedResult
} from '../models/index.js';

/**
 * Repository per gestione analytics e KPI
 */
export class AnalyticsRepository extends BaseRepository<KpiSnapshotModel> {
  constructor() {
    super('kpi_snapshots');
  }

  /**
   * Crea snapshot KPI per un periodo
   * 
   * @param workflowId - ID workflow (null per globale)
   * @param periodType - Tipo di periodo
   * @param metrics - Metriche da salvare
   * @returns Snapshot creato
   */
  async createSnapshot(
    workflowId: string | null,
    periodType: PeriodType,
    metrics: Partial<KpiSnapshotModel>
  ): Promise<KpiSnapshotModel> {
    const query = `
      INSERT INTO kpi_snapshots (
        workflow_id, period_type, snapshot_date,
        total_executions, successful_executions, failed_executions, success_rate,
        avg_duration_ms, p50_duration_ms, p90_duration_ms, p95_duration_ms, p99_duration_ms,
        total_data_processed_mb, avg_data_per_execution_kb,
        error_rate, mtbf_hours, mttr_minutes,
        avg_complexity_score, avg_reliability_score, avg_efficiency_score
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
      RETURNING *
    `;

    const values = [
      workflowId,
      periodType,
      metrics.snapshot_date || new Date(),
      metrics.total_executions || 0,
      metrics.successful_executions || 0,
      metrics.failed_executions || 0,
      metrics.success_rate || 0,
      metrics.avg_duration_ms,
      metrics.p50_duration_ms,
      metrics.p90_duration_ms,
      metrics.p95_duration_ms,
      metrics.p99_duration_ms,
      metrics.total_data_processed_mb || 0,
      metrics.avg_data_per_execution_kb || 0,
      metrics.error_rate || 0,
      metrics.mtbf_hours,
      metrics.mttr_minutes,
      metrics.avg_complexity_score,
      metrics.avg_reliability_score,
      metrics.avg_efficiency_score
    ];

    return await this.db.insert<KpiSnapshotModel>(query, values);
  }

  /**
   * Ottiene snapshot KPI per un workflow
   * 
   * @param workflowId - ID del workflow
   * @param periodType - Tipo di periodo (opzionale)
   * @param limit - Limite risultati
   * @returns Array di snapshot
   */
  async getWorkflowSnapshots(
    workflowId: string,
    periodType?: PeriodType,
    limit: number = 30
  ): Promise<KpiSnapshotModel[]> {
    let query = `
      SELECT * FROM kpi_snapshots 
      WHERE workflow_id = $1
    `;
    
    const params: any[] = [workflowId];
    
    if (periodType) {
      query += ` AND period_type = $2`;
      params.push(periodType);
    }
    
    query += ` ORDER BY snapshot_date DESC LIMIT ${limit}`;
    
    return await this.db.getMany<KpiSnapshotModel>(query, params);
  }

  /**
   * Ottiene snapshot globali di sistema
   * 
   * @param periodType - Tipo di periodo
   * @param days - Giorni da considerare
   * @returns Array di snapshot globali
   */
  async getGlobalSnapshots(
    periodType: PeriodType,
    days: number = 30
  ): Promise<KpiSnapshotModel[]> {
    const query = `
      SELECT * FROM kpi_snapshots 
      WHERE workflow_id IS NULL
        AND period_type = $1
        AND snapshot_date > NOW() - INTERVAL '${days} days'
      ORDER BY snapshot_date DESC
    `;
    
    return await this.db.getMany<KpiSnapshotModel>(query, [periodType]);
  }

  /**
   * Salva statistiche orarie
   * 
   * @param stats - Statistiche da salvare
   * @returns Statistiche salvate
   */
  async saveHourlyStats(stats: Partial<HourlyStatsModel>): Promise<HourlyStatsModel> {
    const query = `
      INSERT INTO hourly_stats (
        workflow_id, stat_date, stat_hour,
        execution_count, success_count, failure_count,
        avg_duration_ms, min_duration_ms, max_duration_ms,
        concurrent_executions_max, queue_size_max
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
      ON CONFLICT (workflow_id, stat_date, stat_hour) 
      DO UPDATE SET
        execution_count = EXCLUDED.execution_count,
        success_count = EXCLUDED.success_count,
        failure_count = EXCLUDED.failure_count,
        avg_duration_ms = EXCLUDED.avg_duration_ms,
        min_duration_ms = EXCLUDED.min_duration_ms,
        max_duration_ms = EXCLUDED.max_duration_ms,
        concurrent_executions_max = EXCLUDED.concurrent_executions_max,
        queue_size_max = EXCLUDED.queue_size_max
      RETURNING *
    `;

    const values = [
      stats.workflow_id || null,
      stats.stat_date || new Date(),
      stats.stat_hour || new Date().getHours(),
      stats.execution_count || 0,
      stats.success_count || 0,
      stats.failure_count || 0,
      stats.avg_duration_ms,
      stats.min_duration_ms,
      stats.max_duration_ms,
      stats.concurrent_executions_max,
      stats.queue_size_max
    ];

    return await this.db.insert<HourlyStatsModel>(query, values);
  }

  /**
   * Ottiene pattern orari per un workflow
   * 
   * @param workflowId - ID del workflow (null per globale)
   * @param days - Giorni da analizzare
   * @returns Array di statistiche orarie
   */
  async getHourlyPatterns(
    workflowId: string | null,
    days: number = 7
  ): Promise<HourlyStatsModel[]> {
    const query = `
      SELECT 
        stat_hour,
        AVG(execution_count) as execution_count,
        AVG(success_count) as success_count,
        AVG(failure_count) as failure_count,
        AVG(avg_duration_ms) as avg_duration_ms,
        MIN(min_duration_ms) as min_duration_ms,
        MAX(max_duration_ms) as max_duration_ms,
        MAX(concurrent_executions_max) as concurrent_executions_max
      FROM hourly_stats
      WHERE stat_date > NOW() - INTERVAL '${days} days'
        ${workflowId ? 'AND workflow_id = $1' : 'AND workflow_id IS NULL'}
      GROUP BY stat_hour
      ORDER BY stat_hour
    `;
    
    const params = workflowId ? [workflowId] : [];
    return await this.db.getMany<HourlyStatsModel>(query, params);
  }

  /**
   * Salva benchmark di performance
   * 
   * @param benchmark - Benchmark da salvare
   * @returns Benchmark salvato
   */
  async saveBenchmark(benchmark: Partial<PerformanceBenchmarkModel>): Promise<PerformanceBenchmarkModel> {
    const query = `
      INSERT INTO performance_benchmarks (
        workflow_id, benchmark_date,
        p1_duration_ms, p5_duration_ms, p10_duration_ms,
        p25_duration_ms, p50_duration_ms, p75_duration_ms,
        p90_duration_ms, p95_duration_ms, p99_duration_ms, p99_9_duration_ms,
        mean_duration_ms, std_deviation_ms, sample_size,
        executions_per_hour, executions_per_day
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
      RETURNING *
    `;

    const values = [
      benchmark.workflow_id,
      benchmark.benchmark_date || new Date(),
      benchmark.p1_duration_ms,
      benchmark.p5_duration_ms,
      benchmark.p10_duration_ms,
      benchmark.p25_duration_ms,
      benchmark.p50_duration_ms,
      benchmark.p75_duration_ms,
      benchmark.p90_duration_ms,
      benchmark.p95_duration_ms,
      benchmark.p99_duration_ms,
      benchmark.p99_9_duration_ms,
      benchmark.mean_duration_ms,
      benchmark.std_deviation_ms,
      benchmark.sample_size || 0,
      benchmark.executions_per_hour,
      benchmark.executions_per_day
    ];

    return await this.db.insert<PerformanceBenchmarkModel>(query, values);
  }

  /**
   * Ottiene ultimo benchmark per un workflow
   * 
   * @param workflowId - ID del workflow
   * @returns Ultimo benchmark o null
   */
  async getLatestBenchmark(workflowId: string): Promise<PerformanceBenchmarkModel | null> {
    const query = `
      SELECT * FROM performance_benchmarks
      WHERE workflow_id = $1
      ORDER BY benchmark_date DESC
      LIMIT 1
    `;
    
    return await this.db.getOne<PerformanceBenchmarkModel>(query, [workflowId]);
  }

  /**
   * Confronta benchmark tra due date
   * 
   * @param workflowId - ID del workflow
   * @param startDate - Data inizio
   * @param endDate - Data fine
   * @returns Array di benchmark per confronto
   */
  async compareBenchmarks(
    workflowId: string,
    startDate: Date,
    endDate: Date
  ): Promise<PerformanceBenchmarkModel[]> {
    const query = `
      SELECT * FROM performance_benchmarks
      WHERE workflow_id = $1
        AND benchmark_date BETWEEN $2 AND $3
      ORDER BY benchmark_date
    `;
    
    return await this.db.getMany<PerformanceBenchmarkModel>(query, [workflowId, startDate, endDate]);
  }

  /**
   * Gestione Tags
   */

  /**
   * Crea o aggiorna un tag
   * 
   * @param tag - Tag da salvare
   * @returns Tag salvato
   */
  async saveTag(tag: Partial<TagModel>): Promise<TagModel> {
    const query = `
      INSERT INTO tags (name, description, color, icon)
      VALUES ($1, $2, $3, $4)
      ON CONFLICT (name) DO UPDATE SET
        description = EXCLUDED.description,
        color = EXCLUDED.color,
        icon = EXCLUDED.icon,
        updated_at = CURRENT_TIMESTAMP
      RETURNING *
    `;

    const values = [
      tag.name,
      tag.description || null,
      tag.color || null,
      tag.icon || null
    ];

    return await this.db.insert<TagModel>(query, values);
  }

  /**
   * Ottiene tutti i tag
   * 
   * @param orderBy - Campo ordinamento
   * @returns Array di tag
   */
  async getAllTags(orderBy: 'name' | 'usage_count' = 'name'): Promise<TagModel[]> {
    const query = `
      SELECT * FROM tags
      ORDER BY ${orderBy} ${orderBy === 'usage_count' ? 'DESC' : 'ASC'}
    `;
    
    return await this.db.getMany<TagModel>(query);
  }

  /**
   * Associa tag a workflow
   * 
   * @param workflowId - ID del workflow
   * @param tagIds - IDs dei tag
   * @returns Numero di associazioni create
   */
  async assignTags(workflowId: string, tagIds: number[]): Promise<number> {
    if (tagIds.length === 0) return 0;

    const values = tagIds.map((tagId, index) => 
      `($1, $${index + 2})`
    ).join(', ');

    const query = `
      INSERT INTO workflow_tags (workflow_id, tag_id)
      VALUES ${values}
      ON CONFLICT (workflow_id, tag_id) DO NOTHING
    `;

    const params = [workflowId, ...tagIds];
    const result = await this.db.query(query, params);
    
    // Aggiorna contatore utilizzo
    await this.updateTagUsageCount(tagIds);
    
    return result.rowCount || 0;
  }

  /**
   * Rimuove tag da workflow
   * 
   * @param workflowId - ID del workflow
   * @param tagIds - IDs dei tag da rimuovere
   * @returns Numero di associazioni rimosse
   */
  async removeTags(workflowId: string, tagIds: number[]): Promise<number> {
    if (tagIds.length === 0) return 0;

    const query = `
      DELETE FROM workflow_tags
      WHERE workflow_id = $1 AND tag_id = ANY($2)
    `;

    const result = await this.db.delete(query, [workflowId, tagIds]);
    
    // Aggiorna contatore utilizzo
    await this.updateTagUsageCount(tagIds);
    
    return result;
  }

  /**
   * Aggiorna contatore utilizzo tag
   * 
   * @param tagIds - IDs dei tag da aggiornare
   */
  private async updateTagUsageCount(tagIds: number[]): Promise<void> {
    const query = `
      UPDATE tags
      SET usage_count = (
        SELECT COUNT(*) FROM workflow_tags WHERE tag_id = tags.id
      )
      WHERE id = ANY($1)
    `;
    
    await this.db.update(query, [tagIds]);
  }

  /**
   * Ottiene tag di un workflow
   * 
   * @param workflowId - ID del workflow
   * @returns Array di tag
   */
  async getWorkflowTags(workflowId: string): Promise<TagModel[]> {
    const query = `
      SELECT t.* FROM tags t
      JOIN workflow_tags wt ON t.id = wt.tag_id
      WHERE wt.workflow_id = $1
      ORDER BY t.name
    `;
    
    return await this.db.getMany<TagModel>(query, [workflowId]);
  }

  /**
   * Calcolo metriche globali
   */

  /**
   * Calcola metriche globali di sistema
   * 
   * @returns Metriche globali
   */
  async calculateGlobalMetrics(): Promise<GlobalMetrics> {
    // Query parallele per efficienza
    const queries = {
      workflows: `
        SELECT 
          COUNT(*) as total,
          COUNT(CASE WHEN active = true THEN 1 END) as active
        FROM workflows
      `,
      executions: `
        SELECT 
          COUNT(CASE WHEN started_at > NOW() - INTERVAL '1 day' THEN 1 END) as today,
          COUNT(CASE WHEN started_at > NOW() - INTERVAL '7 days' THEN 1 END) as week,
          COUNT(CASE WHEN started_at > NOW() - INTERVAL '30 days' THEN 1 END) as month,
          AVG(CASE WHEN started_at > NOW() - INTERVAL '1 hour' THEN duration_ms END) as avg_response_time,
          COUNT(CASE WHEN status = 'success' AND started_at > NOW() - INTERVAL '24 hours' THEN 1 END) as success_24h,
          COUNT(CASE WHEN started_at > NOW() - INTERVAL '24 hours' THEN 1 END) as total_24h
        FROM executions
      `,
      errors: `
        SELECT 
          COUNT(CASE WHEN severity = 'critical' AND occurred_at > NOW() - INTERVAL '24 hours' THEN 1 END) as critical_24h,
          COUNT(CASE WHEN occurred_at > NOW() - INTERVAL '24 hours' THEN 1 END) as total_24h
        FROM error_logs
      `
    };

    const [workflowStats, executionStats, errorStats] = await Promise.all([
      this.db.getOne<any>(queries.workflows),
      this.db.getOne<any>(queries.executions),
      this.db.getOne<any>(queries.errors)
    ]);

    // Calcola tassi
    const successRate = executionStats?.total_24h > 0 
      ? (executionStats.success_24h / executionStats.total_24h) * 100 
      : 0;
    
    const errorRate = executionStats?.total_24h > 0
      ? ((executionStats.total_24h - executionStats.success_24h) / executionStats.total_24h) * 100
      : 0;

    // Calcola trend (ultime 7 giorni)
    const trendData = await this.getExecutionTrends(7);
    const executionTrend = detectTrend(trendData.map(d => d.total_executions));
    const errorTrend = detectTrend(trendData.map(d => d.failed_executions));
    const performanceTrend = detectTrend(trendData.map(d => d.avg_duration_ms || 0));

    // Calcola system load basato su esecuzioni concorrenti
    const systemLoad = await this.calculateSystemLoad();

    // Calcola health score
    const healthScore = calculateGlobalHealthScore({
      successRate,
      avgResponseTime: parseFloat(executionStats?.avg_response_time || '0'),
      errorRate,
      systemLoad
    });

    return {
      total_workflows: parseInt(workflowStats?.total || '0'),
      active_workflows: parseInt(workflowStats?.active || '0'),
      total_executions_today: parseInt(executionStats?.today || '0'),
      total_executions_week: parseInt(executionStats?.week || '0'),
      total_executions_month: parseInt(executionStats?.month || '0'),
      system_health_score: healthScore,
      avg_response_time_ms: parseFloat(executionStats?.avg_response_time || '0'),
      system_load: systemLoad,
      global_success_rate: successRate,
      global_error_rate: errorRate,
      critical_errors_24h: parseInt(errorStats?.critical_24h || '0'),
      execution_trend: executionTrend,
      error_trend: errorTrend,
      performance_trend: performanceTrend,
      last_updated: new Date()
    };
  }

  /**
   * Calcola il carico del sistema basato su metriche di esecuzione
   * 
   * @returns Percentuale di carico del sistema (0-100)
   */
  private async calculateSystemLoad(): Promise<number> {
    try {
      // Conta esecuzioni attive nell'ultima ora
      const activeQuery = `
        SELECT COUNT(*) as active
        FROM n8n.execution_entity
        WHERE "stoppedAt" IS NULL
        OR "startedAt" > NOW() - INTERVAL '1 hour'
      `;
      
      // Conta esecuzioni totali nell'ultima ora per confronto
      const totalQuery = `
        SELECT COUNT(*) as total
        FROM n8n.execution_entity
        WHERE "startedAt" > NOW() - INTERVAL '1 hour'
      `;
      
      const [activeResult, totalResult] = await Promise.all([
        this.db.getOne<{ active: string }>(activeQuery),
        this.db.getOne<{ total: string }>(totalQuery)
      ]);
      
      const active = parseInt(activeResult?.active || '0');
      const total = parseInt(totalResult?.total || '0');
      
      // Calcola load come percentuale
      // Assumiamo che 100 esecuzioni/ora = 100% load
      const loadPercentage = Math.min(100, (total / 100) * 100);
      
      // Aggiusta per esecuzioni attive (peso maggiore)
      const adjustedLoad = Math.min(100, loadPercentage + (active * 5));
      
      return Math.round(adjustedLoad);
    } catch (error) {
      console.error('Error calculating system load:', error);
      return 0;
    }
  }

  /**
   * Ottiene trend esecuzioni giornalieri
   * 
   * @param days - Giorni da considerare
   * @returns Array di snapshot giornalieri
   */
  private async getExecutionTrends(days: number): Promise<any[]> {
    const query = `
      SELECT 
        DATE(started_at) as date,
        COUNT(*) as total_executions,
        COUNT(CASE WHEN status = 'error' THEN 1 END) as failed_executions,
        AVG(duration_ms) as avg_duration_ms
      FROM executions
      WHERE started_at > NOW() - INTERVAL '${days} days'
      GROUP BY DATE(started_at)
      ORDER BY date
    `;
    
    return await this.db.getMany(query);
  }

  /**
   * Confronta KPI tra periodi
   * 
   * @param workflowId - ID workflow (null per globale)
   * @param periodType - Tipo di periodo
   * @param currentDate - Data corrente
   * @returns Confronto KPI
   */
  async compareKpiPeriods(
    workflowId: string | null,
    periodType: PeriodType,
    currentDate: Date = new Date()
  ): Promise<KpiComparison | null> {
    // Determina intervallo in base al periodo
    const intervalMap = {
      [PeriodType.HOURLY]: '1 hour',
      [PeriodType.DAILY]: '1 day',
      [PeriodType.WEEKLY]: '7 days',
      [PeriodType.MONTHLY]: '30 days',
      [PeriodType.QUARTERLY]: '90 days',
      [PeriodType.YEARLY]: '365 days'
    };
    
    const interval = intervalMap[periodType];
    
    const query = `
      SELECT * FROM kpi_snapshots
      WHERE workflow_id ${workflowId ? '= $1' : 'IS NULL'}
        AND period_type = $2
        AND snapshot_date >= $3 - INTERVAL '${interval}'
      ORDER BY snapshot_date DESC
      LIMIT 2
    `;
    
    const params = workflowId 
      ? [workflowId, periodType, currentDate]
      : [periodType, currentDate];
    
    const snapshots = await this.db.getMany<KpiSnapshotModel>(query, params);
    
    if (snapshots.length < 2) return null;
    
    const [current, previous] = snapshots;
    
    // Calcola variazioni
    const executionChange = previous.total_executions > 0
      ? ((current.total_executions - previous.total_executions) / previous.total_executions) * 100
      : 0;
    
    const successRateChange = current.success_rate - previous.success_rate;
    
    const avgDurationChange = (current.avg_duration_ms || 0) - (previous.avg_duration_ms || 0);
    
    const errorRateChange = current.error_rate - previous.error_rate;
    
    // Valuta miglioramenti
    const performanceImproved = avgDurationChange < 0;
    const reliabilityImproved = successRateChange > 0;
    const volumeIncreased = executionChange > 0;
    
    // Genera raccomandazioni
    const recommendations: string[] = [];
    
    if (errorRateChange > 5) {
      recommendations.push('Investigare aumento errori');
    }
    
    if (avgDurationChange > 1000) {
      recommendations.push('Performance degradata - ottimizzare');
    }
    
    if (successRateChange < -10) {
      recommendations.push('Affidabilità ridotta - verificare configurazione');
    }
    
    if (volumeIncreased && avgDurationChange > 500) {
      recommendations.push('Considerare scaling per gestire aumento carico');
    }
    
    return {
      current_period: current,
      previous_period: previous,
      execution_change_percent: executionChange,
      success_rate_change: successRateChange,
      avg_duration_change_ms: avgDurationChange,
      error_rate_change: errorRateChange,
      performance_improved: performanceImproved,
      reliability_improved: reliabilityImproved,
      volume_increased: volumeIncreased,
      recommendations
    };
  }

  /**
   * Rileva pattern temporali
   * 
   * @param workflowId - ID workflow (null per globale)
   * @param days - Giorni da analizzare
   * @returns Pattern temporale rilevato
   */
  async detectTemporalPattern(
    workflowId: string | null,
    days: number = 30
  ): Promise<TemporalPattern> {
    const hourlyStats = await this.getHourlyPatterns(workflowId, days);
    
    if (hourlyStats.length === 0) {
      return {
        pattern_type: PatternType.IRREGULAR,
        description: 'Dati insufficienti per rilevare pattern',
        confidence: 0
      };
    }
    
    // Analizza distribuzione oraria
    const hourlyExecs = hourlyStats.map(s => s.execution_count);
    const maxHourly = Math.max(...hourlyExecs);
    const minHourly = Math.min(...hourlyExecs);
    const avgHourly = hourlyExecs.reduce((a, b) => a + b, 0) / hourlyExecs.length;
    
    // Identifica ore di picco (> 150% della media)
    const peakHours = hourlyStats
      .filter(s => s.execution_count > avgHourly * 1.5)
      .map(s => s.stat_hour);
    
    // Calcola coefficiente di variazione
    const variance = hourlyExecs.reduce((acc, val) => 
      acc + Math.pow(val - avgHourly, 2), 0) / hourlyExecs.length;
    const stdDev = Math.sqrt(variance);
    const cv = (stdDev / avgHourly) * 100;
    
    // Determina pattern
    let patternType: PatternType;
    let description: string;
    let confidence: number;
    
    if (cv < 20) {
      patternType = PatternType.CONSTANT;
      description = 'Carico costante durante il giorno';
      confidence = 90;
    } else if (peakHours.length > 0 && peakHours.length <= 4) {
      patternType = PatternType.DAILY;
      description = `Picchi alle ore: ${peakHours.join(', ')}`;
      confidence = 80;
    } else if (cv > 100) {
      patternType = PatternType.IRREGULAR;
      description = 'Pattern altamente variabile';
      confidence = 60;
    } else {
      patternType = PatternType.WEEKLY;
      description = 'Pattern settimanale rilevato';
      confidence = 70;
    }
    
    return {
      pattern_type: patternType,
      description,
      confidence,
      peak_hours: peakHours,
      seasonal_factor: maxHourly / minHourly
    };
  }

  /**
   * Calcola percentili per metriche performance
   * 
   * @param workflowId - ID del workflow
   * @param metricField - Campo metrica (es. 'duration_ms')
   * @param days - Giorni da considerare
   * @returns Oggetto con percentili calcolati
   */
  async calculatePercentiles(
    workflowId: string,
    metricField: string,
    days: number = 7
  ): Promise<{
    p1: number;
    p5: number;
    p10: number;
    p25: number;
    p50: number;
    p75: number;
    p90: number;
    p95: number;
    p99: number;
    p99_9: number;
    mean: number;
    stdDev: number;
    sampleSize: number;
  }> {
    // Query per ottenere array di valori
    const query = `
      SELECT ${metricField} as value
      FROM executions
      WHERE workflow_id = $1
        AND started_at > NOW() - INTERVAL '${days} days'
        AND ${metricField} IS NOT NULL
      ORDER BY ${metricField}
    `;
    
    const results = await this.db.getMany<{ value: number }>(query, [workflowId]);
    const values = results.map(r => r.value);
    
    if (values.length === 0) {
      return {
        p1: 0, p5: 0, p10: 0, p25: 0, p50: 0,
        p75: 0, p90: 0, p95: 0, p99: 0, p99_9: 0,
        mean: 0, stdDev: 0, sampleSize: 0
      };
    }
    
    // Calcola percentili
    const percentiles = {
      p1: calculatePercentile(values, 1),
      p5: calculatePercentile(values, 5),
      p10: calculatePercentile(values, 10),
      p25: calculatePercentile(values, 25),
      p50: calculatePercentile(values, 50),
      p75: calculatePercentile(values, 75),
      p90: calculatePercentile(values, 90),
      p95: calculatePercentile(values, 95),
      p99: calculatePercentile(values, 99),
      p99_9: calculatePercentile(values, 99.9)
    };
    
    // Calcola media e deviazione standard
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const variance = values.reduce((acc, val) => 
      acc + Math.pow(val - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);
    
    return {
      ...percentiles,
      mean,
      stdDev,
      sampleSize: values.length
    };
  }

  /**
   * Pulisce vecchi snapshot KPI
   * 
   * @param daysToKeep - Giorni da mantenere per tipo periodo
   * @returns Numero di record eliminati
   */
  async cleanOldSnapshots(daysToKeep: Record<PeriodType, number>): Promise<number> {
    let totalDeleted = 0;
    
    for (const [periodType, days] of Object.entries(daysToKeep)) {
      const query = `
        DELETE FROM kpi_snapshots
        WHERE period_type = $1
          AND snapshot_date < NOW() - INTERVAL '${days} days'
      `;
      
      const deleted = await this.db.delete(query, [periodType]);
      totalDeleted += deleted;
    }
    
    return totalDeleted;
  }
}