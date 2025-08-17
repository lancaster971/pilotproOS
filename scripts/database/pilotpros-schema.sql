-- ============================================================================
-- PilotProOS Database Schema
-- Business Process Operating System - PostgreSQL Setup
-- ============================================================================

-- Database and Schema Setup
CREATE DATABASE IF NOT EXISTS pilotpros_db 
    WITH ENCODING='UTF8' 
    LC_COLLATE='C' 
    LC_CTYPE='C' 
    TEMPLATE=template0;

-- Connect to database
\c pilotpros_db;

-- Create schemas with proper isolation
CREATE SCHEMA IF NOT EXISTS n8n;        -- n8n workflow engine (hands-off)
CREATE SCHEMA IF NOT EXISTS pilotpros;  -- PilotProOS business logic

-- ============================================================================
-- PILOTPROS BUSINESS SCHEMA
-- ============================================================================

-- Business Users (simplified authentication)
CREATE TABLE IF NOT EXISTS pilotpros.users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
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

-- Business Process Analytics (aggregated from n8n data)
CREATE TABLE IF NOT EXISTS pilotpros.business_analytics (
    id SERIAL PRIMARY KEY,
    n8n_workflow_id VARCHAR(255) UNIQUE,
    process_name VARCHAR(255) NOT NULL,
    process_category VARCHAR(100),
    success_rate DECIMAL(5,2) DEFAULT 0,
    avg_duration_ms INTEGER DEFAULT 0,
    total_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    last_execution TIMESTAMP,
    trend_direction VARCHAR(20) DEFAULT 'stable',
    business_impact_score INTEGER DEFAULT 50,
    optimization_suggestions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Process Templates (business workflow templates)
CREATE TABLE IF NOT EXISTS pilotpros.process_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(255) NOT NULL,
    template_category VARCHAR(100),
    description TEXT,
    business_description TEXT,
    template_data JSONB NOT NULL,
    estimated_setup_time INTEGER DEFAULT 10,
    industry_tags JSONB DEFAULT '[]',
    complexity_level VARCHAR(20) DEFAULT 'medium',
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Conversations (chat logs for analytics)
CREATE TABLE IF NOT EXISTS pilotpros.ai_conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES pilotpros.users(id),
    session_id VARCHAR(255),
    query_text TEXT NOT NULL,
    intent_detected VARCHAR(100),
    intent_confidence DECIMAL(3,2),
    mcp_tools_called JSONB DEFAULT '[]',
    response_generated TEXT,
    response_time_ms INTEGER,
    user_satisfaction INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Audit Logs
CREATE TABLE IF NOT EXISTS pilotpros.audit_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES pilotpros.users(id),
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Metrics (monitoring)
CREATE TABLE IF NOT EXISTS pilotpros.system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(12,4),
    metric_unit VARCHAR(50),
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- BUSINESS VIEWS (Cross-Schema Analytics)
-- ============================================================================

-- Business Process Overview (main business view)
CREATE OR REPLACE VIEW pilotpros.business_process_overview AS
SELECT 
    w.id as process_id,
    w.name as process_name,
    w.active as is_active,
    w.created_at as process_created,
    w.updated_at as last_modified,
    
    -- Analytics from pilotpros schema
    COALESCE(ba.success_rate, 0) as success_rate,
    COALESCE(ba.avg_duration_ms, 0) as avg_duration_ms,
    COALESCE(ba.total_executions, 0) as total_executions,
    ba.last_execution,
    ba.trend_direction,
    COALESCE(ba.business_impact_score, 50) as business_impact_score,
    
    -- Real-time metrics from n8n
    (
        SELECT COUNT(*) 
        FROM n8n.execution_entity e 
        WHERE e.workflow_id = w.id 
        AND e.started_at >= CURRENT_DATE
    ) as executions_today,
    
    (
        SELECT COUNT(*) 
        FROM n8n.execution_entity e 
        WHERE e.workflow_id = w.id 
        AND (e.finished = false OR e.data->>'error' IS NOT NULL)
        AND e.started_at >= NOW() - INTERVAL '24 hours'
    ) as errors_last_24h,
    
    -- Health status calculation
    CASE 
        WHEN COALESCE(ba.success_rate, 0) >= 98 THEN 'Excellent'
        WHEN COALESCE(ba.success_rate, 0) >= 90 THEN 'Good'
        WHEN COALESCE(ba.success_rate, 0) >= 75 THEN 'Fair'
        ELSE 'Needs Attention'
    END as health_status

FROM n8n.workflow_entity w
LEFT JOIN pilotpros.business_analytics ba ON w.id = ba.n8n_workflow_id
ORDER BY ba.business_impact_score DESC NULLS LAST;

-- Process Execution Summary
CREATE OR REPLACE VIEW pilotpros.process_execution_summary AS
SELECT 
    DATE_TRUNC('day', e.started_at) as execution_date,
    w.name as process_name,
    COUNT(*) as total_runs,
    COUNT(CASE WHEN e.finished = true AND e.data->>'error' IS NULL THEN 1 END) as successful_runs,
    COUNT(CASE WHEN e.finished = false OR e.data->>'error' IS NOT NULL THEN 1 END) as failed_runs,
    AVG(EXTRACT(EPOCH FROM (e.stopped_at - e.started_at)) * 1000) as avg_duration_ms
FROM n8n.execution_entity e
JOIN n8n.workflow_entity w ON e.workflow_id = w.id
WHERE e.started_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', e.started_at), w.name
ORDER BY execution_date DESC, process_name;

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- Indexes for optimal performance
CREATE INDEX IF NOT EXISTS idx_business_analytics_workflow ON pilotpros.business_analytics(n8n_workflow_id);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_session ON pilotpros.ai_conversations(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON pilotpros.audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_time ON pilotpros.system_metrics(metric_name, timestamp);

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Create default admin user
INSERT INTO pilotpros.users (email, password_hash, full_name, role) 
VALUES (
    'admin@pilotpros.local',
    '$2b$12$LQv3c1yqBWVHxkd0LQ4YCOWheHfCo1BEv3Qa7dLbNAUbZM4ZJ.Wv.', -- password: admin123
    'System Administrator',
    'admin'
) ON CONFLICT (email) DO NOTHING;

-- Insert sample process templates
INSERT INTO pilotpros.process_templates (template_name, template_category, description, business_description, template_data) VALUES
(
    'Customer Onboarding', 
    'Customer Management',
    'Automated customer registration and welcome process',
    'Automatizza la registrazione di nuovi clienti con email di benvenuto e setup account',
    '{"name": "Customer Onboarding Process", "description": "Automated customer onboarding workflow", "nodes": []}'
),
(
    'Order Processing', 
    'E-Commerce',
    'Automated order validation and fulfillment process', 
    'Gestisce automaticamente gli ordini: validazione, calcolo totali, conferma cliente',
    '{"name": "Order Processing Automation", "description": "Automated order processing workflow", "nodes": []}'
),
(
    'Support Ticket Routing',
    'Customer Service', 
    'Automated support ticket categorization and routing',
    'Smista automaticamente i ticket di supporto al reparto corretto in base alla categoria',
    '{"name": "Support Ticket Routing", "description": "Automated support ticket routing workflow", "nodes": []}'
) ON CONFLICT DO NOTHING;

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update business analytics automatically
CREATE OR REPLACE FUNCTION pilotpros.update_business_analytics()
RETURNS VOID AS $$
BEGIN
    INSERT INTO pilotpros.business_analytics (
        n8n_workflow_id,
        process_name,
        success_rate,
        avg_duration_ms,
        total_executions,
        failed_executions,
        last_execution,
        updated_at
    )
    SELECT 
        w.id,
        w.name,
        COALESCE(
            (COUNT(CASE WHEN e.finished = true AND e.data->>'error' IS NULL THEN 1 END)::float / 
             NULLIF(COUNT(e.id), 0)) * 100, 0
        ) as success_rate,
        COALESCE(
            AVG(EXTRACT(EPOCH FROM (e.stopped_at - e.started_at)) * 1000), 0
        ) as avg_duration_ms,
        COUNT(e.id) as total_executions,
        COUNT(CASE WHEN e.finished = false OR e.data->>'error' IS NOT NULL THEN 1 END) as failed_executions,
        MAX(e.started_at) as last_execution,
        NOW() as updated_at
    FROM n8n.workflow_entity w
    LEFT JOIN n8n.execution_entity e ON w.id = e.workflow_id
    WHERE e.started_at >= NOW() - INTERVAL '24 hours' OR e.started_at IS NULL
    GROUP BY w.id, w.name
    
    ON CONFLICT (n8n_workflow_id) 
    DO UPDATE SET
        process_name = EXCLUDED.process_name,
        success_rate = EXCLUDED.success_rate,
        avg_duration_ms = EXCLUDED.avg_duration_ms,
        total_executions = EXCLUDED.total_executions,
        failed_executions = EXCLUDED.failed_executions,
        last_execution = EXCLUDED.last_execution,
        updated_at = EXCLUDED.updated_at;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic analytics updates
CREATE OR REPLACE FUNCTION pilotpros.trigger_analytics_update()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pilotpros.update_business_analytics();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on n8n executions (only if n8n schema exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'n8n') THEN
        -- Drop trigger if exists
        DROP TRIGGER IF EXISTS execution_analytics_trigger ON n8n.execution_entity;
        
        -- Create trigger for analytics updates
        CREATE TRIGGER execution_analytics_trigger
            AFTER INSERT OR UPDATE ON n8n.execution_entity
            FOR EACH STATEMENT
            EXECUTE FUNCTION pilotpros.trigger_analytics_update();
    END IF;
END $$;

-- ============================================================================
-- PERMISSIONS SETUP
-- ============================================================================

-- Ensure proper permissions for pilotpros user
GRANT USAGE ON SCHEMA pilotpros TO pilotpros_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA pilotpros TO pilotpros_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA pilotpros TO pilotpros_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA pilotpros TO pilotpros_user;

-- Grant read access to n8n schema for analytics
GRANT USAGE ON SCHEMA n8n TO pilotpros_user;
GRANT SELECT ON ALL TABLES IN SCHEMA n8n TO pilotpros_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA pilotpros GRANT ALL ON TABLES TO pilotpros_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA pilotpros GRANT ALL ON SEQUENCES TO pilotpros_user;

-- ============================================================================
-- INITIAL ANALYTICS UPDATE
-- ============================================================================

-- Run initial analytics calculation (if n8n data exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'n8n' AND table_name = 'workflow_entity') THEN
        PERFORM pilotpros.update_business_analytics();
    END IF;
END $$;

-- ============================================================================
-- SETUP COMPLETION
-- ============================================================================

-- Log setup completion
INSERT INTO pilotpros.system_metrics (metric_name, metric_value, tags) 
VALUES ('schema_setup_completed', 1, '{"timestamp": "' || NOW() || '", "version": "1.0.0"}');

-- Display setup summary
SELECT 
    'PilotProOS Database Setup Complete' as status,
    NOW() as completed_at,
    (SELECT COUNT(*) FROM pilotpros.users) as users_created,
    (SELECT COUNT(*) FROM pilotpros.process_templates) as templates_available;