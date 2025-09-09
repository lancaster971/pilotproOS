-- Migration 006: Authentication System
-- Aggiunge sistema di autenticazione JWT con gestione utenti e permessi

-- Tabella utenti autenticazione
CREATE TABLE IF NOT EXISTS auth_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'readonly',
    tenant_id VARCHAR(100) REFERENCES tenants(id) ON DELETE SET NULL,
    permissions JSONB DEFAULT '[]'::jsonb,
    api_key VARCHAR(128) UNIQUE,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT auth_users_role_check CHECK (role IN ('admin', 'tenant', 'readonly'))
);

-- Indici per performance
CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email);
CREATE INDEX IF NOT EXISTS idx_auth_users_api_key ON auth_users(api_key);
CREATE INDEX IF NOT EXISTS idx_auth_users_tenant_id ON auth_users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_auth_users_role ON auth_users(role);
CREATE INDEX IF NOT EXISTS idx_auth_users_active ON auth_users(active);

-- Trigger per updated_at
CREATE OR REPLACE FUNCTION update_auth_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_auth_users_updated_at ON auth_users;
CREATE TRIGGER trigger_update_auth_users_updated_at
    BEFORE UPDATE ON auth_users
    FOR EACH ROW
    EXECUTE FUNCTION update_auth_users_updated_at();

-- Tabella sessioni JWT (opzionale, per blacklist/revoke)
CREATE TABLE IF NOT EXISTS auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    token_jti VARCHAR(255) UNIQUE NOT NULL, -- JWT ID per identificare il token
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked BOOLEAN DEFAULT false,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address INET
);

-- Indici per sessioni
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_token_jti ON auth_sessions(token_jti);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires_at ON auth_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_revoked ON auth_sessions(revoked);

-- Tabella audit log per autenticazione
CREATE TABLE IF NOT EXISTS auth_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth_users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL, -- login, logout, create_user, update_user, etc.
    resource_type VARCHAR(100), -- tenants, workflows, scheduler, etc.
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indici per audit log
CREATE INDEX IF NOT EXISTS idx_auth_audit_log_user_id ON auth_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_audit_log_action ON auth_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_auth_audit_log_created_at ON auth_audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_auth_audit_log_success ON auth_audit_log(success);

-- Funzione per cleanup sessioni scadute
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM auth_sessions 
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Crea utente admin di default se non esiste
DO $$
BEGIN
    -- Verifica se esistono già utenti
    IF NOT EXISTS (SELECT 1 FROM auth_users LIMIT 1) THEN
        -- Crea utente admin di default
        -- Password: "admin123" (hash bcrypt con 12 rounds)
        -- API Key: generata casualmente
        INSERT INTO auth_users (
            email, 
            password_hash, 
            role, 
            permissions, 
            api_key,
            active
        ) VALUES (
            'admin@n8n-mcp.local',
            '$2b$12$rQJ5qVK9C1nH9pN8oF2L2eQ8pG.HGjKrHn8/tR5xA.GQ4vQ2B4pZu', -- admin123
            'admin',
            '["scheduler:read","scheduler:write","scheduler:control","tenants:read","tenants:write","tenants:delete","users:read","users:write","users:delete","logs:read","stats:read","system:read"]'::jsonb,
            encode(gen_random_bytes(32), 'hex'),
            true
        );
        
        RAISE NOTICE 'Utente admin di default creato: admin@n8n-mcp.local / admin123';
    END IF;
END
$$;

-- Commenti sulle tabelle
COMMENT ON TABLE auth_users IS 'Utenti del sistema di autenticazione multi-tenant';
COMMENT ON TABLE auth_sessions IS 'Sessioni JWT attive e revocate';
COMMENT ON TABLE auth_audit_log IS 'Log di audit per azioni di autenticazione e autorizzazione';

COMMENT ON COLUMN auth_users.role IS 'Ruolo utente: admin (accesso completo), tenant (accesso al proprio tenant), readonly (solo lettura)';
COMMENT ON COLUMN auth_users.permissions IS 'Array JSON di permessi specifici per azioni granulari';
COMMENT ON COLUMN auth_users.api_key IS 'Chiave API per autenticazione senza JWT (per automazioni)';
COMMENT ON COLUMN auth_sessions.token_jti IS 'JWT ID univoco per identificare e revocare token specifici';
COMMENT ON COLUMN auth_audit_log.action IS 'Azione eseguita: login, logout, create_user, sync_tenant, etc.';