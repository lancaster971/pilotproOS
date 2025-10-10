-- Migration: Auto-Learning Fast-Path System
-- Description: Pattern learning table for Milhena classifier auto-improvement
-- Created: 2025-10-10
-- Reference: TODO-URGENTE.md lines 237-254

CREATE TABLE IF NOT EXISTS pilotpros.auto_learned_patterns (
    id SERIAL PRIMARY KEY,
    pattern VARCHAR(200) UNIQUE NOT NULL,
    normalized_pattern VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    times_used INT DEFAULT 0,
    times_correct INT DEFAULT 0,
    accuracy FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    created_by VARCHAR(20) DEFAULT 'llm',
    enabled BOOLEAN DEFAULT true
);

-- Indexes for performance (fast pattern lookup)
CREATE INDEX IF NOT EXISTS idx_auto_learned_normalized ON pilotpros.auto_learned_patterns(normalized_pattern);
CREATE INDEX IF NOT EXISTS idx_auto_learned_accuracy ON pilotpros.auto_learned_patterns(accuracy DESC);
CREATE INDEX IF NOT EXISTS idx_auto_learned_enabled ON pilotpros.auto_learned_patterns(enabled);
CREATE INDEX IF NOT EXISTS idx_auto_learned_category ON pilotpros.auto_learned_patterns(category);

-- Comment on table
COMMENT ON TABLE pilotpros.auto_learned_patterns IS 'Auto-learned query patterns from high-confidence LLM classifications (>0.9) for fast-path matching';
COMMENT ON COLUMN pilotpros.auto_learned_patterns.pattern IS 'Original query pattern as seen by user';
COMMENT ON COLUMN pilotpros.auto_learned_patterns.normalized_pattern IS 'Normalized version for matching (lowercase, no temporal words)';
COMMENT ON COLUMN pilotpros.auto_learned_patterns.confidence IS 'LLM confidence when pattern was learned (0.0-1.0)';
COMMENT ON COLUMN pilotpros.auto_learned_patterns.accuracy IS 'Calculated as times_correct / times_used';
COMMENT ON COLUMN pilotpros.auto_learned_patterns.created_by IS 'Source: llm (auto-learned) or admin (manually added)';
