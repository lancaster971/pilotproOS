-- =====================================================
-- AUTH ENHANCEMENT MIGRATION FIX
-- Fix UUID foreign key constraints for user_id fields
-- =====================================================

-- Drop existing tables that were created with wrong foreign key types
DROP TABLE IF EXISTS pilotpros.user_mfa CASCADE;
DROP TABLE IF EXISTS pilotpros.mfa_sessions CASCADE;
DROP TABLE IF EXISTS pilotpros.user_auth_methods CASCADE;

-- MFA User Settings Table (FIXED with UUID)
CREATE TABLE pilotpros.user_mfa (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES pilotpros.users(id) ON DELETE CASCADE,
    secret TEXT NOT NULL,
    backup_codes JSONB DEFAULT '[]',
    enabled BOOLEAN DEFAULT false,
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- MFA Session Tracking Table (FIXED with UUID)
CREATE TABLE pilotpros.mfa_sessions (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES pilotpros.users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    mfa_verified BOOLEAN DEFAULT false,
    expires_at TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Authentication Methods Table (FIXED with UUID)
CREATE TABLE pilotpros.user_auth_methods (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES pilotpros.users(id) ON DELETE CASCADE,
    method VARCHAR(20) NOT NULL CHECK (method IN ('local', 'ldap')),
    ldap_dn VARCHAR(255),
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, method)
);

-- Indexes for performance
CREATE INDEX idx_user_mfa_user_id ON pilotpros.user_mfa(user_id);
CREATE INDEX idx_user_mfa_enabled ON pilotpros.user_mfa(enabled);
CREATE INDEX idx_mfa_sessions_token ON pilotpros.mfa_sessions(session_token);
CREATE INDEX idx_mfa_sessions_user_expires ON pilotpros.mfa_sessions(user_id, expires_at);
CREATE INDEX idx_user_auth_methods_user_method ON pilotpros.user_auth_methods(user_id, method);

-- Apply triggers for updated_at
CREATE TRIGGER update_user_mfa_updated_at
    BEFORE UPDATE ON pilotpros.user_mfa
    FOR EACH ROW EXECUTE FUNCTION pilotpros.update_updated_at_column();