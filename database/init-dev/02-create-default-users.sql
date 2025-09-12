-- ============================================================================
-- PILOTPROS DEFAULT USERS - ENTERPRISE GRADE SETUP
-- Auto-executed on database initialization
-- ============================================================================

-- Create users table if not exists
CREATE TABLE IF NOT EXISTS pilotpros.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- UPSERT default users with consistent passwords
-- Password hash for 'admin123' - NEVER CHANGES
INSERT INTO pilotpros.users (email, password_hash, full_name, role, is_active) 
VALUES 
    ('admin@pilotpros.dev', '$2a$12$XzE.fb1kwuJqvCR/JGsW5./FCn3EM2b6pLMmubh48jChfMnscKyUC', 'PilotPro Admin', 'admin', true),
    ('tiziano@gmail.com', '$2a$12$XzE.fb1kwuJqvCR/JGsW5./FCn3EM2b6pLMmubh48jChfMnscKyUC', 'Tiziano', 'admin', true),
    ('admin@test.com', '$2a$12$XzE.fb1kwuJqvCR/JGsW5./FCn3EM2b6pLMmubh48jChfMnscKyUC', 'Test Admin', 'admin', true),
    ('test@example.com', '$2a$12$XzE.fb1kwuJqvCR/JGsW5./FCn3EM2b6pLMmubh48jChfMnscKyUC', 'Test User', 'viewer', true)
ON CONFLICT (email) 
DO UPDATE SET 
    password_hash = EXCLUDED.password_hash,
    full_name = EXCLUDED.full_name,
    role = EXCLUDED.role,
    updated_at = CURRENT_TIMESTAMP;

-- Log successful seeding
DO $$ 
BEGIN 
    RAISE NOTICE '✅ PilotProOS: Default users created/updated successfully';
    RAISE NOTICE 'Login: any email above with password "admin123"';
END $$;