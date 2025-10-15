-- Migration 005: Pattern Approval System
-- Purpose: Add manual supervision for auto-learned patterns
-- Target: Allow admin approval/rejection before patterns go live
-- Author: PilotProOS Development Team
-- Created: 2025-10-13
-- Reference: Session #55 - Pattern Supervision Feature

-- ============================================================================
-- ROLLBACK INSTRUCTIONS
-- ============================================================================
-- To rollback this migration, execute:
--
-- BEGIN;
-- DROP INDEX IF EXISTS pilotpros.idx_status_enabled;
-- ALTER TABLE pilotpros.auto_learned_patterns DROP COLUMN IF EXISTS status;
-- COMMIT;
--
-- Verification:
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema = 'pilotpros' AND table_name = 'auto_learned_patterns' AND column_name = 'status';
-- Expected: 0 rows
-- ============================================================================

BEGIN;

-- ============================================================================
-- ADD STATUS COLUMN
-- ============================================================================
-- Description:
--   Adds workflow status to auto-learned patterns for manual supervision.
--
-- Status Flow:
--   1. LLM learns pattern (confidence >0.9) → status = 'pending'
--   2. Admin reviews in /learning/patterns → Approve/Reject
--   3. If approved → status = 'approved' (fast-path uses it)
--   4. If disabled → status = 'disabled' (fast-path ignores it)
--
-- Values:
--   - 'pending': Newly learned, awaiting admin approval
--   - 'approved': Admin approved, used in fast-path matching
--   - 'disabled': Admin rejected or disabled, not used
-- ============================================================================

ALTER TABLE pilotpros.auto_learned_patterns
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending' NOT NULL
    CHECK (status IN ('pending', 'approved', 'disabled'));

-- ============================================================================
-- BACKWARD COMPATIBILITY: Approve existing patterns
-- ============================================================================
-- All patterns created before this migration are assumed good (they were already
-- being used). Set them to 'approved' automatically.
-- ============================================================================

UPDATE pilotpros.auto_learned_patterns
SET status = 'approved'
WHERE status = 'pending';

-- ============================================================================
-- INDEX: Fast status filtering
-- ============================================================================
-- Query: SELECT * FROM auto_learned_patterns WHERE status = 'approved' AND enabled = true;
-- Expected: <2ms (composite index scan)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_status_enabled
    ON pilotpros.auto_learned_patterns(status, enabled)
    WHERE enabled = true;

-- ============================================================================
-- UPDATE TABLE COMMENT
-- ============================================================================

COMMENT ON COLUMN pilotpros.auto_learned_patterns.status IS
    'Approval status: pending (needs review) | approved (live) | disabled (rejected)';

COMMENT ON INDEX pilotpros.idx_status_enabled IS
    'Composite index for filtering by approval status. Fast-path uses status=approved only.';

-- ============================================================================
-- PERFORMANCE NOTES
-- ============================================================================
-- Expected volume: 10-30 pending patterns/day (awaiting approval)
-- Admin reviews: 1-2x/day (batch approval of 10-30 patterns)
--
-- Index size (estimated for 10K patterns):
-- - idx_status_enabled: ~100KB
--
-- Query performance targets:
-- - Fast-path lookup (approved only): <1ms (existing idx_normalized_pattern + status check)
-- - Admin pending list: <5ms (idx_status_enabled scan)
-- - Status update: <2ms (PK update + index maintenance)
-- ============================================================================

COMMIT;
