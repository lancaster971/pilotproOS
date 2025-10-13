// Learning System Types - PilotProOS v3.3.1
// TypeScript interfaces for Auto-Learning system metrics and feedback

/**
 * Pattern data from PostgreSQL auto_learned_patterns table
 */
export interface PatternData {
  id: number // MUST be number for PrimeVue DataTable dataKey compatibility
  pattern?: string // Pattern text (alias for query)
  query: string
  normalized_query: string
  category?: string // Category alias (same as classification)
  classification: string
  confidence: number
  times_used: number
  times_correct: number
  accuracy?: number // Computed: times_correct / times_used
  created_at?: string
  last_used_at?: string | null
  is_active?: boolean
  status?: 'pending' | 'approved' | 'disabled' // Pattern approval status (v3.4.0 supervision)
  source?: 'hardcoded' | 'auto_learned'
}

/**
 * Learning metrics response from Intelligence Engine
 * GET /api/milhena/performance
 */
export interface LearningMetrics {
  total_patterns: number
  auto_learned_count: number
  hardcoded_count: number
  average_confidence: number
  total_usages: number
  accuracy_rate: number // Global accuracy (0-1)
  cost_savings: CostSavings
  top_patterns: PatternData[]
  accuracy_trend?: AccuracyDataPoint[] // Historical data
  category_distribution?: CategoryStats[]
}

/**
 * Cost savings metrics
 */
export interface CostSavings {
  monthly: number // Monthly savings in $
  total: number // Total savings in $
  fast_path_coverage: number // Percentage (0-100)
  llm_coverage: number // Percentage (0-100)
}

/**
 * Accuracy data point for time series chart
 */
export interface AccuracyDataPoint {
  timestamp: string // ISO 8601
  accuracy: number // 0-1
  total_queries: number
  correct_queries: number
}

/**
 * Category statistics for distribution analysis
 */
export interface CategoryStats {
  category: string
  pattern_count: number
  usage_count: number
  average_accuracy: number
}

/**
 * User feedback event
 */
export interface FeedbackEvent {
  id?: string
  session_id: string
  query: string
  classification: string
  feedback: 'positive' | 'negative'
  timestamp: string
  reformulation_shown?: boolean
  reformulation_accepted?: boolean
}

/**
 * Feedback request payload
 * POST /api/milhena/feedback
 */
export interface FeedbackRequest {
  session_id: string
  feedback: 'positive' | 'negative'
  query?: string
  classification?: string
}

/**
 * Reformulation suggestion
 */
export interface ReformulationSuggestion {
  original_query: string
  suggested_query: string
  category: string
  reason: string
}

/**
 * Pattern reload response
 * POST /api/milhena/patterns/reload
 */
export interface PatternReloadResponse {
  success: boolean
  message: string
  patterns_loaded: number
  reload_time_ms: number
}

/**
 * Heatmap data point for D3.js visualization
 */
export interface HeatmapDataPoint {
  category: string
  hour: number // 0-23
  usage_count: number
  accuracy: number // 0-1
}

/**
 * Learning dashboard state
 */
export interface LearningDashboardState {
  metrics: LearningMetrics | null
  patterns: PatternData[]
  feedback_events: FeedbackEvent[]
  heatmap_data: HeatmapDataPoint[]
  is_loading: boolean
  error: string | null
  last_updated: string | null
}
