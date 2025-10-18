-- Migration 006: Refresh Tokens Table
-- Purpose: Implement refresh token strategy for secure token rotation
-- CVSS Impact: 6.5 → Prevents token theft exploitation
-- Date: 2025-10-18

-- Create refresh_tokens table
CREATE TABLE IF NOT EXISTS pilotpros.refresh_tokens (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES pilotpros.users(id) ON DELETE CASCADE,
  token TEXT NOT NULL UNIQUE,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  revoked_at TIMESTAMP DEFAULT NULL,

  -- Constraints
  CONSTRAINT token_not_empty CHECK (LENGTH(token) > 0),
  CONSTRAINT valid_expiry CHECK (expires_at > created_at)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_refresh_token ON pilotpros.refresh_tokens(token);
CREATE INDEX IF NOT EXISTS idx_user_active_tokens ON pilotpros.refresh_tokens(user_id, revoked_at)
  WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_expiry ON pilotpros.refresh_tokens(expires_at);

-- Comments for documentation
COMMENT ON TABLE pilotpros.refresh_tokens IS 'Stores refresh tokens for JWT token rotation strategy';
COMMENT ON COLUMN pilotpros.refresh_tokens.token IS 'Cryptographically secure random token (64 chars hex)';
COMMENT ON COLUMN pilotpros.refresh_tokens.expires_at IS 'Token expiry timestamp (typically 7 days from creation)';
COMMENT ON COLUMN pilotpros.refresh_tokens.revoked_at IS 'NULL = active, timestamp = revoked (logout/security)';

-- Verify table created
SELECT
  table_name,
  column_name,
  data_type,
  is_nullable
FROM information_schema.columns
WHERE table_schema = 'pilotpros'
  AND table_name = 'refresh_tokens'
ORDER BY ordinal_position;
