-- =====================================================
-- AUTH ENHANCEMENT MIGRATION
-- Adds LDAP + MFA support to existing pilotpros schema
-- =====================================================

-- LDAP Configuration Table
CREATE TABLE IF NOT EXISTS pilotpros.ldap_config (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    server_url VARCHAR(255) NOT NULL,
    bind_dn VARCHAR(255),
    bind_password TEXT,
    user_search_base VARCHAR(255) NOT NULL,
    user_filter VARCHAR(255) DEFAULT '(&(objectClass=person)(mail={email}))',
    group_search_base VARCHAR(255),
    group_filter VARCHAR(255) DEFAULT '(objectClass=group)',
    enabled BOOLEAN DEFAULT true,
    ssl_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MFA User Settings Table
CREATE TABLE IF NOT EXISTS pilotpros.user_mfa (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES pilotpros.users(id) ON DELETE CASCADE,
    secret TEXT NOT NULL,
    backup_codes JSONB DEFAULT '[]',
    enabled BOOLEAN DEFAULT false,
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- MFA Session Tracking Table
CREATE TABLE IF NOT EXISTS pilotpros.mfa_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES pilotpros.users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    mfa_verified BOOLEAN DEFAULT false,
    expires_at TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Authentication Methods Table
CREATE TABLE IF NOT EXISTS pilotpros.user_auth_methods (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES pilotpros.users(id) ON DELETE CASCADE,
    method VARCHAR(20) NOT NULL CHECK (method IN ('local', 'ldap')),
    ldap_dn VARCHAR(255),
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, method)
);

-- Extend existing users table with LDAP fields
ALTER TABLE pilotpros.users 
ADD COLUMN IF NOT EXISTS ldap_dn VARCHAR(255),
ADD COLUMN IF NOT EXISTS auth_method VARCHAR(20) DEFAULT 'local' CHECK (auth_method IN ('local', 'ldap')),
ADD COLUMN IF NOT EXISTS last_ldap_sync TIMESTAMP,
ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN DEFAULT false;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ldap_config_enabled ON pilotpros.ldap_config(enabled);
CREATE INDEX IF NOT EXISTS idx_user_mfa_user_id ON pilotpros.user_mfa(user_id);
CREATE INDEX IF NOT EXISTS idx_user_mfa_enabled ON pilotpros.user_mfa(enabled);
CREATE INDEX IF NOT EXISTS idx_mfa_sessions_token ON pilotpros.mfa_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_mfa_sessions_user_expires ON pilotpros.mfa_sessions(user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_user_auth_methods_user_method ON pilotpros.user_auth_methods(user_id, method);
CREATE INDEX IF NOT EXISTS idx_users_auth_method ON pilotpros.users(auth_method);
CREATE INDEX IF NOT EXISTS idx_users_ldap_dn ON pilotpros.users(ldap_dn);

-- Initial LDAP configuration (example for Active Directory)
INSERT INTO pilotpros.ldap_config (
    name, server_url, user_search_base, user_filter, 
    group_search_base, group_filter, enabled
) VALUES (
    'Active Directory',
    'ldaps://your-domain-controller.local:636',
    'DC=your-company,DC=local',
    '(&(objectClass=user)(mail={email}))',
    'DC=your-company,DC=local',
    '(objectClass=group)',
    false  -- Disabled by default, requires configuration
) ON CONFLICT DO NOTHING;

-- Update trigger for updated_at columns
CREATE OR REPLACE FUNCTION pilotpros.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
DROP TRIGGER IF EXISTS update_ldap_config_updated_at ON pilotpros.ldap_config;
CREATE TRIGGER update_ldap_config_updated_at
    BEFORE UPDATE ON pilotpros.ldap_config
    FOR EACH ROW EXECUTE FUNCTION pilotpros.update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_mfa_updated_at ON pilotpros.user_mfa;
CREATE TRIGGER update_user_mfa_updated_at
    BEFORE UPDATE ON pilotpros.user_mfa
    FOR EACH ROW EXECUTE FUNCTION pilotpros.update_updated_at_column();