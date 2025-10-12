-- Migration 004: Auto-Learned Patterns Table
-- Purpose: Store high-confidence LLM classifications for instant pattern matching
-- Target: Reduce latency from 200-500ms (LLM) to <1ms (database lookup)
-- Author: PilotProOS Development Team
-- Created: 2025-10-10
-- Updated: 2025-10-12 (optimized with partial indexes + CHECK constraints)
-- Reference: TODO-URGENTE.md lines 237-254

-- ============================================================================
-- ROLLBACK INSTRUCTIONS
-- ============================================================================
-- To rollback this migration, execute:
--
-- BEGIN;
-- DROP INDEX IF EXISTS pilotpros.idx_category_enabled;
-- DROP INDEX IF EXISTS pilotpros.idx_enabled_partial;
-- DROP INDEX IF EXISTS pilotpros.idx_accuracy_desc;
-- DROP INDEX IF EXISTS pilotpros.idx_normalized_pattern;
-- DROP TABLE IF EXISTS pilotpros.auto_learned_patterns CASCADE;
-- COMMIT;
--
-- Verification:
-- SELECT COUNT(*) FROM pg_tables
-- WHERE schemaname = 'pilotpros' AND tablename = 'auto_learned_patterns';
-- Expected: 0
-- ============================================================================

BEGIN;

-- ============================================================================
-- TABLE: pilotpros.auto_learned_patterns
-- ============================================================================
-- Description:
--   Stores auto-learned classification patterns from Milhena v3.3.1 ReAct Agent.
--   When LLM classifier returns confidence >0.9, the pattern is saved for
--   instant matching on future similar queries.
--
-- Pattern Matching Flow:
--   1. Query arrives → normalize (lowercase, remove temporal words, strip punctuation)
--   2. Check this table: SELECT WHERE normalized_pattern = $1 AND enabled = true
--   3. If match found → return category instantly (<1ms)
--   4. If no match → call LLM classifier (200-500ms) → maybe save if confidence >0.9
--
-- Normalization Examples:
--   "Ci sono problemi oggi?" → "ci sono problemi"
--   "ci sono problemi adesso?" → "ci sono problemi"
--   (Same normalized_pattern, different original pattern)
-- ============================================================================

CREATE TABLE IF NOT EXISTS pilotpros.auto_learned_patterns (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Pattern data (original vs normalized for matching)
    pattern VARCHAR(200) UNIQUE NOT NULL,
    normalized_pattern VARCHAR(200) NOT NULL,

    -- Classification result
    category VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL
        CHECK (confidence >= 0.0 AND confidence <= 1.0),

    -- Accuracy tracking
    times_used INT DEFAULT 0 NOT NULL
        CHECK (times_used >= 0),
    times_correct INT DEFAULT 0 NOT NULL
        CHECK (times_correct >= 0 AND times_correct <= times_used),
    accuracy FLOAT DEFAULT 0.0 NOT NULL
        CHECK (accuracy >= 0.0 AND accuracy <= 1.0),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_used_at TIMESTAMPTZ,
    created_by VARCHAR(20) DEFAULT 'llm' NOT NULL,
    enabled BOOLEAN DEFAULT true NOT NULL
);

-- ============================================================================
-- INDEXES (Optimized with partial indexes for enabled=true patterns only)
-- ============================================================================

-- Index 1: Fast pattern lookup (CRITICAL - 99% of queries)
-- Query: SELECT category, confidence FROM auto_learned_patterns
--        WHERE normalized_pattern = $1 AND enabled = true LIMIT 1;
-- Expected: <1ms (B-tree scan, 10K rows)
CREATE INDEX IF NOT EXISTS idx_normalized_pattern
    ON pilotpros.auto_learned_patterns(normalized_pattern)
    WHERE enabled = true;

-- Index 2: Dashboard sorting by accuracy (10-50 queries/day)
-- Query: SELECT * FROM auto_learned_patterns
--        WHERE enabled = true ORDER BY accuracy DESC LIMIT 50;
-- Expected: <5ms
CREATE INDEX IF NOT EXISTS idx_accuracy_desc
    ON pilotpros.auto_learned_patterns(accuracy DESC)
    WHERE enabled = true;

-- Index 3: Enabled filter optimization (partial index for space savings)
-- Query: SELECT COUNT(*) FROM auto_learned_patterns WHERE enabled = true;
-- Expected: <2ms
-- Note: Partial index reduces size by ~50% (stores only enabled=true rows)
CREATE INDEX IF NOT EXISTS idx_enabled_partial
    ON pilotpros.auto_learned_patterns(enabled)
    WHERE enabled = true;

-- Index 4: Category filtering for admin dashboard
-- Query: SELECT * FROM auto_learned_patterns
--        WHERE category = 'SIMPLE_QUERY' AND enabled = true;
-- Expected: <3ms
CREATE INDEX IF NOT EXISTS idx_category_enabled
    ON pilotpros.auto_learned_patterns(category, enabled)
    WHERE enabled = true;

-- ============================================================================
-- TABLE & COLUMN COMMENTS
-- ============================================================================

COMMENT ON TABLE pilotpros.auto_learned_patterns IS
    'Auto-learned patterns from Milhena v3.3.1 ReAct Agent. Stores high-confidence (>0.9) LLM classifications for instant pattern matching (<1ms vs 200-500ms LLM call). Updated via Redis PubSub hot-reload system.';

COMMENT ON COLUMN pilotpros.auto_learned_patterns.pattern IS
    'Original query text (case-sensitive, with punctuation)';

COMMENT ON COLUMN pilotpros.auto_learned_patterns.normalized_pattern IS
    'Normalized for matching: lowercase, no temporal words, no punctuation';

COMMENT ON COLUMN pilotpros.auto_learned_patterns.category IS
    'LLM classification category (SIMPLE_QUERY, DANGER, HELP, ANALYTICS, etc.)';

COMMENT ON COLUMN pilotpros.auto_learned_patterns.confidence IS
    'LLM confidence score (0.0-1.0, minimum 0.9 for auto-learning)';

COMMENT ON COLUMN pilotpros.auto_learned_patterns.times_used IS
    'Number of times this pattern was matched';

COMMENT ON COLUMN pilotpros.auto_learned_patterns.times_correct IS
    'Number of times user confirmed correctness (via feedback)';

COMMENT ON COLUMN pilotpros.auto_learned_patterns.accuracy IS
    'Calculated as times_correct / times_used (0-1)';

COMMENT ON COLUMN pilotpros.auto_learned_patterns.created_at IS
    'When pattern was first learned (timezone-aware)';

COMMENT ON COLUMN pilotpros.auto_learned_patterns.last_used_at IS
    'Last time pattern was matched (updated on each use)';

COMMENT ON COLUMN pilotpros.auto_learned_patterns.created_by IS
    'Source: llm (auto-learned) or manual (admin-added)';

COMMENT ON COLUMN pilotpros.auto_learned_patterns.enabled IS
    'Soft delete flag: false to disable pattern without removing';

COMMENT ON INDEX pilotpros.idx_normalized_pattern IS
    'Partial index for fast pattern matching on enabled patterns only. Critical performance index.';

COMMENT ON INDEX pilotpros.idx_accuracy_desc IS
    'Partial index for sorting by accuracy (dashboard metrics). DESC order for best patterns first.';

COMMENT ON INDEX pilotpros.idx_enabled_partial IS
    'Partial index on enabled flag. Smaller than full index, covers active patterns only.';

COMMENT ON INDEX pilotpros.idx_category_enabled IS
    'Composite index for filtering by category with enabled check. Dashboard category breakdown.';

-- ============================================================================
-- PERFORMANCE NOTES
-- ============================================================================
-- Expected volume: 100-1000 patterns initially, 10K+ long-term
-- Growth rate: ~10-50 patterns/day
-- Read queries: 1000+/day (pattern matching)
-- Write queries: 10-50/day (new patterns + usage updates)
--
-- Index sizes (estimated for 10K patterns):
-- - idx_normalized_pattern: ~100KB
-- - idx_accuracy_desc: ~80KB
-- - idx_enabled_partial: ~60KB (partial)
-- - idx_category_enabled: ~120KB
-- Total: ~360KB (negligible overhead)
--
-- Query performance targets:
-- - Pattern lookup: <1ms (10x better than <10ms target)
-- - Insert: <2ms
-- - Update usage: <1ms (PK lookup)
-- - Dashboard: <5ms
-- ============================================================================

COMMIT;
