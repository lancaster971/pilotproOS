// Learning Store - Pinia store for Auto-Learning system metrics
// PilotProOS v3.3.1 - Intelligence Engine API integration

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  LearningMetrics,
  PatternData,
  FeedbackEvent,
  FeedbackRequest,
  PatternReloadResponse,
  AccuracyDataPoint,
  HeatmapDataPoint
} from '../types/learning'

// Backend API base URL (port 3001) - Milhena endpoints proxied through backend
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:3001'

export const useLearningStore = defineStore('learning', () => {
  // ========== STATE ==========
  const metrics = ref<LearningMetrics | null>(null)
  const patterns = ref<PatternData[]>([])
  const feedbackEvents = ref<FeedbackEvent[]>([])
  const heatmapData = ref<HeatmapDataPoint[]>([])

  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdated = ref<string | null>(null)

  // Cache TTL (30 seconds)
  const CACHE_TTL_MS = 30 * 1000
  let lastFetchTime = 0

  // ========== COMPUTED / GETTERS ==========

  /**
   * Accuracy trend for Chart.js line chart
   * Returns last 7 days if available, otherwise generates from current metrics
   */
  const accuracyTrend = computed((): AccuracyDataPoint[] => {
    if (metrics.value?.accuracy_trend && metrics.value.accuracy_trend.length > 0) {
      return metrics.value.accuracy_trend
    }

    // Fallback: Generate single data point from current metrics
    if (metrics.value) {
      return [{
        timestamp: new Date().toISOString(),
        accuracy: metrics.value.accuracy_rate,
        total_queries: metrics.value.total_usages,
        correct_queries: Math.round(metrics.value.total_usages * metrics.value.accuracy_rate)
      }]
    }

    return []
  })

  /**
   * Cost trend for visualization
   * Shows monthly and total savings
   */
  const costTrend = computed(() => {
    if (!metrics.value?.cost_savings) return null

    return {
      monthly: metrics.value.cost_savings.monthly,
      total: metrics.value.cost_savings.total,
      fastPathCoverage: metrics.value.cost_savings.fast_path_coverage,
      llmCoverage: metrics.value.cost_savings.llm_coverage
    }
  })

  /**
   * Top performing patterns (sorted by usage)
   */
  const topPatterns = computed((): PatternData[] => {
    const result = patterns.value
      .filter(p => p.times_used > 0)
      .sort((a, b) => b.times_used - a.times_used)
      .slice(0, 10)

    console.log('🔄 topPatterns computed:', result.length, 'patterns')
    return result
  })

  /**
   * Pattern performance statistics
   */
  const patternStats = computed(() => {
    if (patterns.value.length === 0) return null

    const totalPatterns = patterns.value.length
    const autoLearnedCount = patterns.value.filter(p => p.source === 'auto_learned').length
    const hardcodedCount = totalPatterns - autoLearnedCount

    const avgAccuracy = patterns.value.reduce((sum, p) => {
      const accuracy = p.times_used > 0 ? (p.times_correct / p.times_used) : 0
      return sum + accuracy
    }, 0) / totalPatterns

    return {
      totalPatterns,
      autoLearnedCount,
      hardcodedCount,
      avgAccuracy,
      autoLearnedPercentage: (autoLearnedCount / totalPatterns) * 100
    }
  })

  /**
   * Recent feedback events (last 20)
   */
  const recentFeedback = computed((): FeedbackEvent[] => {
    return feedbackEvents.value
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 20)
  })

  // ========== ACTIONS ==========

  /**
   * Fetch learning metrics from Intelligence Engine
   * GET /api/milhena/performance
   */
  const fetchMetrics = async (forceRefresh = false): Promise<void> => {
    // Check cache TTL
    const now = Date.now()
    if (!forceRefresh && lastFetchTime > 0 && (now - lastFetchTime) < CACHE_TTL_MS) {
      console.log('📊 Using cached metrics (TTL not expired)')
      return
    }

    isLoading.value = true
    error.value = null

    try {
      console.log('📊 Fetching learning metrics from Intelligence Engine...')

      const response = await fetch(`${API_BASE}/api/milhena/performance`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch metrics: ${response.status} ${response.statusText}`)
      }

      const data: LearningMetrics = await response.json()
      console.log('✅ Learning metrics fetched:', data)

      // Update state (triggers Vue reactivity)
      // IMPORTANT: Create NEW array reference to force Vue re-render
      metrics.value = { ...data }
      patterns.value = [...(data.top_patterns || [])]
      lastUpdated.value = new Date().toISOString()
      lastFetchTime = now

      console.log('📊 Store updated:', {
        total_patterns: data.total_patterns,
        patterns_loaded: patterns.value.length,
        patterns_reference: patterns.value,
        approved_count: patterns.value.filter(p => p.status === 'approved').length,
        disabled_count: patterns.value.filter(p => p.status === 'disabled').length,
        pending_count: patterns.value.filter(p => p.status === 'pending').length
      })

      // Map recent_feedback from API to feedbackEvents (NEW array reference)
      if (data.recent_feedback && Array.isArray(data.recent_feedback)) {
        feedbackEvents.value = [...data.recent_feedback.map((fb: any) => ({
          session_id: fb.session_id || '',
          query: fb.query || '',
          classification: fb.classification || 'GENERAL',
          feedback: fb.feedback_type === 'positive' ? 'positive' : 'negative',
          timestamp: fb.timestamp || new Date().toISOString()
        }))]
        console.log(`📊 Mapped ${feedbackEvents.value.length} feedback events`)
      }

      // Generate heatmap data from patterns (NEW array reference)
      heatmapData.value = [...generateHeatmapData(patterns.value)]
      console.log(`📊 Generated ${heatmapData.value.length} heatmap data points`)

    } catch (err: any) {
      error.value = err.message || 'Failed to fetch learning metrics'
      console.error('❌ Failed to fetch metrics:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Send user feedback (positive/negative)
   * POST /api/milhena/feedback
   */
  const sendFeedback = async (request: FeedbackRequest): Promise<void> => {
    try {
      console.log('👍👎 Sending feedback:', request)

      const response = await fetch(`${API_BASE}/api/milhena/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(request)
      })

      if (!response.ok) {
        throw new Error(`Failed to send feedback: ${response.status}`)
      }

      const result = await response.json()
      console.log('✅ Feedback sent:', result)

      // Add to local feedback events
      const feedbackEvent: FeedbackEvent = {
        session_id: request.session_id,
        query: request.query || '',
        classification: request.classification || '',
        feedback: request.feedback,
        timestamp: new Date().toISOString()
      }
      feedbackEvents.value.unshift(feedbackEvent)

      // Refresh metrics after feedback (but don't throw if fails)
      try {
        await fetchMetrics(true)
      } catch (refreshErr) {
        console.warn('⚠️ Failed to refresh metrics after feedback:', refreshErr)
      }

    } catch (err: any) {
      error.value = err.message || 'Failed to send feedback'
      console.error('❌ Failed to send feedback:', err)
      throw err
    }
  }

  /**
   * Reload patterns from PostgreSQL (hot-reload via Redis PubSub)
   * POST /api/milhena/patterns/reload
   */
  const reloadPatterns = async (): Promise<PatternReloadResponse> => {
    isLoading.value = true
    error.value = null

    try {
      console.log('🔄 Triggering pattern reload...')

      const response = await fetch(`${API_BASE}/api/milhena/patterns/reload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`Failed to reload patterns: ${response.status}`)
      }

      const result: PatternReloadResponse = await response.json()
      console.log('✅ Patterns reloaded:', result)

      // Refresh metrics after reload
      await fetchMetrics(true)

      return result

    } catch (err: any) {
      error.value = err.message || 'Failed to reload patterns'
      console.error('❌ Failed to reload patterns:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Approve a pending pattern (admin action)
   * POST /api/milhena/patterns/:id/approve
   */
  const approvePattern = async (patternId: number): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      console.log(`✅ Approving pattern ${patternId}...`)

      const response = await fetch(`${API_BASE}/api/milhena/patterns/${patternId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Failed to approve pattern: ${response.status}`)
      }

      const result = await response.json()
      console.log('✅ Pattern approved:', result)

      // Refresh metrics after approval
      await fetchMetrics(true)

    } catch (err: any) {
      error.value = err.message || 'Failed to approve pattern'
      console.error('❌ Failed to approve pattern:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Disable a pattern (admin action)
   * POST /api/milhena/patterns/:id/disable
   */
  const disablePattern = async (patternId: number): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      console.log(`⚠️ Disabling pattern ${patternId}...`)

      const response = await fetch(`${API_BASE}/api/milhena/patterns/${patternId}/disable`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Failed to disable pattern: ${response.status}`)
      }

      const result = await response.json()
      console.log('⚠️ Pattern disabled:', result)

      // Refresh metrics after disable
      await fetchMetrics(true)

    } catch (err: any) {
      error.value = err.message || 'Failed to disable pattern'
      console.error('❌ Failed to disable pattern:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete a pattern permanently (admin action)
   * DELETE /api/milhena/patterns/:id
   */
  const deletePattern = async (patternId: number): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      console.log(`🗑️ Deleting pattern ${patternId}...`)

      const response = await fetch(`${API_BASE}/api/milhena/patterns/${patternId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Failed to delete pattern: ${response.status}`)
      }

      const result = await response.json()
      console.log('🗑️ Pattern deleted:', result)

      // Refresh metrics after delete
      await fetchMetrics(true)

    } catch (err: any) {
      error.value = err.message || 'Failed to delete pattern'
      console.error('❌ Failed to delete pattern:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Clear cache and force refresh
   */
  const clearCache = (): void => {
    lastFetchTime = 0
    console.log('🗑️ Learning metrics cache cleared')
  }

  /**
   * Reset store state
   */
  const resetState = (): void => {
    metrics.value = null
    patterns.value = []
    feedbackEvents.value = []
    heatmapData.value = []
    isLoading.value = false
    error.value = null
    lastUpdated.value = null
    lastFetchTime = 0
    console.log('🔄 Learning store reset')
  }

  // ========== HELPER FUNCTIONS ==========

  /**
   * Generate heatmap data from patterns
   * Groups patterns by category and hour of day
   */
  function generateHeatmapData(patterns: PatternData[]): HeatmapDataPoint[] {
    const heatmap: HeatmapDataPoint[] = []

    // Get unique categories
    const categories = [...new Set(patterns.map(p => p.classification))]

    // For each category and hour, calculate usage
    categories.forEach(category => {
      const categoryPatterns = patterns.filter(p => p.classification === category)

      // Distribute usage across 24 hours (simulated for now)
      // In production, this should come from backend with real timestamp data
      for (let hour = 0; hour < 24; hour++) {
        const totalUsage = categoryPatterns.reduce((sum, p) => sum + p.times_used, 0)
        const totalCorrect = categoryPatterns.reduce((sum, p) => sum + p.times_correct, 0)

        // Simulate hourly distribution (peaks at business hours 9-17)
        const hourlyFactor = hour >= 9 && hour <= 17 ? 1.5 : 0.5
        const usageCount = Math.round((totalUsage / 24) * hourlyFactor)
        const accuracy = totalUsage > 0 ? totalCorrect / totalUsage : 0

        heatmap.push({
          category,
          hour,
          usage_count: usageCount,
          accuracy
        })
      }
    })

    return heatmap
  }

  // ========== RETURN ==========
  return {
    // State
    metrics,
    patterns,
    feedbackEvents,
    heatmapData,
    isLoading,
    error,
    lastUpdated,

    // Computed
    accuracyTrend,
    costTrend,
    topPatterns,
    patternStats,
    recentFeedback,

    // Actions
    fetchMetrics,
    sendFeedback,
    reloadPatterns,
    approvePattern,
    disablePattern,
    deletePattern,
    clearCache,
    resetState
  }
})
