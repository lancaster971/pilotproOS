/**
 * KPI Model
 * 
 * Definisce le interfacce TypeScript per le tabelle KPI e metriche aggregate.
 * Gestisce snapshot temporali, benchmark e statistiche di performance.
 */

/**
 * Interfaccia per la tabella kpi_snapshots
 * Snapshot KPI per diversi periodi temporali
 */
export interface KpiSnapshotModel {
  id: number;
  workflow_id?: string;          // NULL per KPI globali di sistema
  period_type: PeriodType;       // Tipo di periodo temporale
  snapshot_date: Date;           // Data dello snapshot
  
  // KPI Esecuzioni
  total_executions: number;      // Totale esecuzioni nel periodo
  successful_executions: number; // Esecuzioni con successo
  failed_executions: number;     // Esecuzioni fallite
  success_rate: number;          // Tasso di successo percentuale
  
  // KPI Performance (in millisecondi)
  avg_duration_ms?: number;      // Durata media
  p50_duration_ms?: number;      // Mediana (50° percentile)
  p90_duration_ms?: number;      // 90° percentile
  p95_duration_ms?: number;      // 95° percentile
  p99_duration_ms?: number;      // 99° percentile
  
  // KPI Volume dati
  total_data_processed_mb: number;     // Totale dati processati in MB
  avg_data_per_execution_kb: number;   // Media dati per esecuzione in KB
  
  // KPI Affidabilità
  error_rate: number;            // Tasso di errore percentuale
  mtbf_hours?: number;           // Mean Time Between Failures in ore
  mttr_minutes?: number;         // Mean Time To Recovery in minuti
  
  // Scores aggregati
  avg_complexity_score?: number;  // Media complexity score
  avg_reliability_score?: number; // Media reliability score
  avg_efficiency_score?: number;  // Media efficiency score
  
  created_at: Date;
}

/**
 * Enum per i tipi di periodo temporale
 */
export enum PeriodType {
  HOURLY = '1h',                 // Snapshot orario
  DAILY = '24h',                 // Snapshot giornaliero
  WEEKLY = '7d',                 // Snapshot settimanale
  MONTHLY = '30d',               // Snapshot mensile
  QUARTERLY = '90d',             // Snapshot trimestrale
  YEARLY = '365d'                // Snapshot annuale
}

/**
 * Interfaccia per la tabella hourly_stats
 * Statistiche orarie per pattern analysis
 */
export interface HourlyStatsModel {
  id: number;
  workflow_id?: string;          // NULL per stats globali
  stat_date: Date;               // Data delle statistiche
  stat_hour: number;             // Ora del giorno (0-23)
  
  // Contatori esecuzioni
  execution_count: number;       // Totale esecuzioni nell'ora
  success_count: number;         // Esecuzioni con successo
  failure_count: number;         // Esecuzioni fallite
  
  // Performance
  avg_duration_ms?: number;      // Durata media
  min_duration_ms?: number;      // Durata minima
  max_duration_ms?: number;      // Durata massima
  
  // Carico sistema
  concurrent_executions_max?: number;  // Max esecuzioni concorrenti
  queue_size_max?: number;             // Max dimensione coda
  
  created_at: Date;
}

/**
 * Interfaccia per la tabella performance_benchmarks
 * Benchmark di performance dettagliati
 */
export interface PerformanceBenchmarkModel {
  id: number;
  workflow_id: string;
  benchmark_date: Date;          // Data del benchmark
  
  // Percentili durata (in millisecondi)
  p1_duration_ms?: number;       // 1° percentile (più veloce)
  p5_duration_ms?: number;       // 5° percentile
  p10_duration_ms?: number;      // 10° percentile
  p25_duration_ms?: number;      // Primo quartile
  p50_duration_ms?: number;      // Mediana
  p75_duration_ms?: number;      // Terzo quartile
  p90_duration_ms?: number;      // 90° percentile
  p95_duration_ms?: number;      // 95° percentile
  p99_duration_ms?: number;      // 99° percentile
  p99_9_duration_ms?: number;    // 99.9° percentile (più lento)
  
  // Statistiche
  mean_duration_ms?: number;     // Media aritmetica
  std_deviation_ms?: number;     // Deviazione standard
  sample_size: number;           // Numero di esecuzioni nel campione
  
  // Throughput
  executions_per_hour?: number;  // Esecuzioni per ora
  executions_per_day?: number;   // Esecuzioni per giorno
  
  created_at: Date;
}

/**
 * Interfaccia per la tabella tags
 * Sistema di categorizzazione con tags
 */
export interface TagModel {
  id: number;
  name: string;                  // Nome del tag (univoco)
  description?: string;          // Descrizione del tag
  color?: string;                // Colore HEX per UI
  icon?: string;                 // Nome icona per UI
  
  // Statistiche uso
  usage_count: number;           // Quante volte è usato
  
  created_at: Date;
  updated_at: Date;
}

/**
 * Interfaccia per la tabella workflow_tags
 * Relazione many-to-many tra workflow e tags
 */
export interface WorkflowTagModel {
  workflow_id: string;
  tag_id: number;
  created_at: Date;
}

/**
 * Interfaccia per metriche aggregate globali
 * Utilizzata per dashboard di sistema
 */
export interface GlobalMetrics {
  // Contatori generali
  total_workflows: number;
  active_workflows: number;
  total_executions_today: number;
  total_executions_week: number;
  total_executions_month: number;
  
  // Performance sistema
  system_health_score: number;   // Score salute globale (0-100)
  avg_response_time_ms: number;  // Tempo risposta medio
  system_load: number;           // Carico sistema (0-100)
  
  // Affidabilità
  global_success_rate: number;   // Success rate globale
  global_error_rate: number;     // Error rate globale
  critical_errors_24h: number;   // Errori critici ultime 24h
  
  // Utilizzo risorse
  cpu_usage_percent?: number;    // Utilizzo CPU
  memory_usage_mb?: number;      // Utilizzo memoria
  disk_usage_gb?: number;        // Utilizzo disco
  
  // Trend
  execution_trend: TrendDirection;     // Trend esecuzioni
  error_trend: TrendDirection;         // Trend errori
  performance_trend: TrendDirection;   // Trend performance
  
  last_updated: Date;
}

/**
 * Enum per direzione del trend
 */
export enum TrendDirection {
  UP = 'up',                     // In aumento
  DOWN = 'down',                 // In diminuzione
  STABLE = 'stable',             // Stabile
  VOLATILE = 'volatile'          // Volatile/irregolare
}

/**
 * Interfaccia per analisi pattern temporali
 */
export interface TemporalPattern {
  pattern_type: PatternType;
  description: string;
  confidence: number;            // Confidenza del pattern (0-100)
  
  // Dettagli pattern
  peak_hours?: number[];         // Ore di picco
  peak_days?: string[];          // Giorni di picco
  seasonal_factor?: number;      // Fattore stagionale
  
  // Predizioni basate sul pattern
  next_peak?: Date;              // Prossimo picco previsto
  expected_load?: number;        // Carico previsto
}

/**
 * Enum per tipi di pattern temporali
 */
export enum PatternType {
  DAILY = 'daily',               // Pattern giornaliero
  WEEKLY = 'weekly',             // Pattern settimanale
  MONTHLY = 'monthly',           // Pattern mensile
  SEASONAL = 'seasonal',         // Pattern stagionale
  IRREGULAR = 'irregular',       // Irregolare
  CONSTANT = 'constant'          // Costante
}

/**
 * Interfaccia per confronto KPI tra periodi
 */
export interface KpiComparison {
  current_period: KpiSnapshotModel;
  previous_period: KpiSnapshotModel;
  
  // Variazioni calcolate
  execution_change_percent: number;
  success_rate_change: number;
  avg_duration_change_ms: number;
  error_rate_change: number;
  
  // Valutazione variazioni
  performance_improved: boolean;
  reliability_improved: boolean;
  volume_increased: boolean;
  
  // Raccomandazioni
  recommendations: string[];
}

/**
 * Helper per calcolare percentili da array di valori
 */
export function calculatePercentile(values: number[], percentile: number): number {
  if (values.length === 0) return 0;
  
  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.ceil((percentile / 100) * sorted.length) - 1;
  return sorted[Math.max(0, index)];
}

/**
 * Helper per calcolare MTBF (Mean Time Between Failures)
 */
export function calculateMTBF(
  totalOperatingHours: number,
  numberOfFailures: number
): number {
  if (numberOfFailures === 0) return totalOperatingHours;
  return totalOperatingHours / numberOfFailures;
}

/**
 * Helper per calcolare MTTR (Mean Time To Recovery)
 */
export function calculateMTTR(
  totalDowntimeMinutes: number,
  numberOfIncidents: number
): number {
  if (numberOfIncidents === 0) return 0;
  return totalDowntimeMinutes / numberOfIncidents;
}

/**
 * Helper per determinare il trend da una serie di valori
 */
export function detectTrend(values: number[]): TrendDirection {
  if (values.length < 3) return TrendDirection.STABLE;
  
  // Calcola pendenza con regressione lineare semplice
  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
  const n = values.length;
  
  for (let i = 0; i < n; i++) {
    sumX += i;
    sumY += values[i];
    sumXY += i * values[i];
    sumX2 += i * i;
  }
  
  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const avgValue = sumY / n;
  const slopePercent = Math.abs(slope / avgValue) * 100;
  
  // Calcola volatilità
  const mean = sumY / n;
  const variance = values.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / n;
  const stdDev = Math.sqrt(variance);
  const cv = (stdDev / mean) * 100; // Coefficiente di variazione
  
  // Determina trend
  if (cv > 50) return TrendDirection.VOLATILE;
  if (slopePercent < 5) return TrendDirection.STABLE;
  return slope > 0 ? TrendDirection.UP : TrendDirection.DOWN;
}

/**
 * Helper per calcolare health score globale
 */
export function calculateGlobalHealthScore(metrics: {
  successRate: number;
  avgResponseTime: number;
  errorRate: number;
  systemLoad: number;
}): number {
  // Pesi per ogni metrica
  const weights = {
    successRate: 0.4,
    responseTime: 0.2,
    errorRate: 0.3,
    systemLoad: 0.1
  };
  
  // Normalizza metriche (0-100)
  const normalizedSuccessRate = metrics.successRate;
  const normalizedResponseTime = Math.max(0, 100 - (metrics.avgResponseTime / 50)); // 5s = 0 score
  const normalizedErrorRate = Math.max(0, 100 - (metrics.errorRate * 10)); // 10% = 0 score
  const normalizedSystemLoad = Math.max(0, 100 - metrics.systemLoad);
  
  // Calcola score ponderato
  const score = 
    normalizedSuccessRate * weights.successRate +
    normalizedResponseTime * weights.responseTime +
    normalizedErrorRate * weights.errorRate +
    normalizedSystemLoad * weights.systemLoad;
  
  return Math.round(Math.min(100, Math.max(0, score)));
}