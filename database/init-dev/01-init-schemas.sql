-- PilotProOS Development Database Initialization
-- Creates the dual-schema structure: n8n + pilotpros

-- Create schemas
CREATE SCHEMA IF NOT EXISTS n8n;
CREATE SCHEMA IF NOT EXISTS pilotpros;

-- Set search path to include both schemas
ALTER DATABASE pilotpros_db SET search_path TO pilotpros, n8n, public;

-- Grant permissions to pilotpros_user
GRANT ALL PRIVILEGES ON SCHEMA n8n TO pilotpros_user;
GRANT ALL PRIVILEGES ON SCHEMA pilotpros TO pilotpros_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA n8n TO pilotpros_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA pilotpros TO pilotpros_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA n8n TO pilotpros_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA pilotpros TO pilotpros_user;

-- Grant default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA n8n GRANT ALL ON TABLES TO pilotpros_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA n8n GRANT ALL ON SEQUENCES TO pilotpros_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA pilotpros GRANT ALL ON TABLES TO pilotpros_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA pilotpros GRANT ALL ON SEQUENCES TO pilotpros_user;

-- Development utilities
-- Create a development admin user for easy access
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = 'dev_admin'
    ) THEN
        CREATE ROLE dev_admin WITH LOGIN PASSWORD 'dev_admin_2025' SUPERUSER;
    END IF;
END
$$;

-- Log the initialization
INSERT INTO information_schema.sql_features 
VALUES ('PILOTPROS_DEV_INIT', 'CORE', 'YES', 'Development database initialized');

COMMENT ON SCHEMA n8n IS 'n8n workflow engine schema - managed by n8n';
COMMENT ON SCHEMA pilotpros IS 'PilotProOS business logic schema - managed by application';

-- Create development-specific tables in pilotpros schema
CREATE TABLE IF NOT EXISTS pilotpros.dev_info (
    id SERIAL PRIMARY KEY,
    initialized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version VARCHAR(50) DEFAULT '1.0.0-dev',
    environment VARCHAR(20) DEFAULT 'development',
    notes TEXT
);

INSERT INTO pilotpros.dev_info (notes) 
VALUES ('Development environment initialized with dual-schema PostgreSQL setup');

-- Development logging table
CREATE TABLE IF NOT EXISTS pilotpros.dev_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20),
    message TEXT,
    context JSONB,
    service VARCHAR(50)
);

COMMENT ON TABLE pilotpros.dev_logs IS 'Development logging for debugging and monitoring';

-- Create indexes for development performance
CREATE INDEX IF NOT EXISTS idx_dev_logs_timestamp ON pilotpros.dev_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_dev_logs_service ON pilotpros.dev_logs(service);

-- Final success message
INSERT INTO pilotpros.dev_logs (level, message, service) 
VALUES ('INFO', 'Database initialization completed successfully', 'postgres-init');