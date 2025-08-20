-- PilotProOS Business Schema with Correct n8n Column Names
-- Cross-schema integration with proper n8n column references

-- Business Process Analytics (corrected for n8n column names)
CREATE TABLE IF NOT EXISTS pilotpros.business_analytics (
    id SERIAL PRIMARY KEY,
    n8n_workflow_id VARCHAR(36) UNIQUE,
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

-- Business Users
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

-- Process Templates
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

-- AI Conversations
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

-- System Metrics
CREATE TABLE IF NOT EXISTS pilotpros.system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(12,4),
    metric_unit VARCHAR(50),
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Business Process Overview (CORRECTED with n8n camelCase columns)
CREATE OR REPLACE VIEW pilotpros.business_process_overview AS
SELECT 
    w.id as process_id,
    w.name as process_name,
    w.active as is_active,
    w."createdAt" as process_created,
    w."updatedAt" as last_modified,
    
    -- Analytics from pilotpros schema
    COALESCE(ba.success_rate, 0) as success_rate,
    COALESCE(ba.avg_duration_ms, 0) as avg_duration_ms,
    COALESCE(ba.total_executions, 0) as total_executions,
    ba.last_execution,
    ba.trend_direction,
    COALESCE(ba.business_impact_score, 50) as business_impact_score,
    
    -- Real-time metrics from n8n (CORRECTED column names)
    (
        SELECT COUNT(*) 
        FROM n8n.execution_entity e 
        WHERE e."workflowId" = w.id 
        AND e."startedAt" >= CURRENT_DATE
    ) as executions_today,
    
    (
        SELECT COUNT(*) 
        FROM n8n.execution_entity e 
        WHERE e."workflowId" = w.id 
        AND (e.finished = false OR e.data->>'error' IS NOT NULL)
        AND e."startedAt" >= NOW() - INTERVAL '24 hours'
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

-- Process Execution Summary (CORRECTED)
CREATE OR REPLACE VIEW pilotpros.process_execution_summary AS
SELECT 
    DATE_TRUNC('day', e."startedAt") as execution_date,
    w.name as process_name,
    COUNT(*) as total_runs,
    COUNT(CASE WHEN e.finished = true AND e.data->>'error' IS NULL THEN 1 END) as successful_runs,
    COUNT(CASE WHEN e.finished = false OR e.data->>'error' IS NOT NULL THEN 1 END) as failed_runs,
    AVG(EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) * 1000) as avg_duration_ms
FROM n8n.execution_entity e
JOIN n8n.workflow_entity w ON e."workflowId" = w.id
WHERE e."startedAt" >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', e."startedAt"), w.name
ORDER BY execution_date DESC, process_name;

-- Function to update business analytics (CORRECTED)
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
            AVG(EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) * 1000), 0
        ) as avg_duration_ms,
        COUNT(e.id) as total_executions,
        COUNT(CASE WHEN e.finished = false OR e.data->>'error' IS NOT NULL THEN 1 END) as failed_executions,
        MAX(e."startedAt") as last_execution,
        NOW() as updated_at
    FROM n8n.workflow_entity w
    LEFT JOIN n8n.execution_entity e ON w.id = e."workflowId"
    WHERE e."startedAt" >= NOW() - INTERVAL '24 hours' OR e."startedAt" IS NULL
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

-- Create trigger for automatic analytics updates (CORRECTED)
CREATE OR REPLACE FUNCTION pilotpros.trigger_analytics_update()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pilotpros.update_business_analytics();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop and recreate trigger with correct table name
DROP TRIGGER IF EXISTS execution_analytics_trigger ON n8n.execution_entity;
CREATE TRIGGER execution_analytics_trigger
    AFTER INSERT OR UPDATE ON n8n.execution_entity
    FOR EACH STATEMENT
    EXECUTE FUNCTION pilotpros.trigger_analytics_update();

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_business_analytics_workflow ON pilotpros.business_analytics(n8n_workflow_id);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_session ON pilotpros.ai_conversations(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON pilotpros.audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_time ON pilotpros.system_metrics(metric_name, timestamp);

-- Insert default admin user
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
    '{"name": "Customer Onboarding Process", "description": "Automated customer onboarding workflow", "nodes": []}'::jsonb
),
(
    'Order Processing', 
    'E-Commerce',
    'Automated order validation and fulfillment process', 
    'Gestisce automaticamente gli ordini: validazione, calcolo totali, conferma cliente',
    '{"name": "Order Processing Automation", "description": "Automated order processing workflow", "nodes": []}'::jsonb
),
(
    'Support Ticket Routing',
    'Customer Service', 
    'Automated support ticket categorization and routing',
    'Smista automaticamente i ticket di supporto al reparto corretto in base alla categoria',
    '{"name": "Support Ticket Routing", "description": "Automated support ticket routing workflow", "nodes": []}'::jsonb
) ON CONFLICT DO NOTHING;

-- Log setup completion
INSERT INTO pilotpros.system_metrics (metric_name, metric_value, tags) 
VALUES ('schema_setup_completed', 1, '{"timestamp": "' || NOW()::text || '", "version": "1.0.0"}'::jsonb);

-- Display setup summary
SELECT 
    'PilotProOS Business Schema Setup Complete' as status,
    NOW() as completed_at,
    (SELECT COUNT(*) FROM pilotpros.users) as users_created,
    (SELECT COUNT(*) FROM pilotpros.process_templates) as templates_available,
    (SELECT COUNT(*) FROM n8n.workflow_entity) as n8n_workflows;