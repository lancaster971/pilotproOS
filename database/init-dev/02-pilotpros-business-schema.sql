-- PilotProOS Business Schema (Clean - No n8n Dependencies)
-- Basic business tables only - views will be created after n8n schema exists

-- Business Process Analytics
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Logs
CREATE TABLE IF NOT EXISTS pilotpros.audit_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES pilotpros.users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Settings
CREATE TABLE IF NOT EXISTS pilotpros.system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT false,
    updated_by UUID REFERENCES pilotpros.users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Process Schedules
CREATE TABLE IF NOT EXISTS pilotpros.process_schedules (
    id SERIAL PRIMARY KEY,
    n8n_workflow_id VARCHAR(36) NOT NULL,
    schedule_name VARCHAR(255) NOT NULL,
    cron_expression VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT true,
    next_run TIMESTAMP,
    last_run TIMESTAMP,
    run_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Business Intelligence Dashboards
CREATE TABLE IF NOT EXISTS pilotpros.dashboards (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    config JSONB NOT NULL,
    is_public BOOLEAN DEFAULT false,
    created_by UUID REFERENCES pilotpros.users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification Settings
CREATE TABLE IF NOT EXISTS pilotpros.notifications (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES pilotpros.users(id),
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    is_read BOOLEAN DEFAULT false,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_business_analytics_workflow_id ON pilotpros.business_analytics(n8n_workflow_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON pilotpros.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON pilotpros.audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON pilotpros.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON pilotpros.notifications(user_id, is_read);

-- Insert default system settings
INSERT INTO pilotpros.system_settings (setting_key, setting_value, description, is_public) 
VALUES 
    ('app_name', '"PilotProOS"', 'Application name', true),
    ('app_version', '"1.0.0"', 'Application version', true),
    ('maintenance_mode', 'false', 'System maintenance mode', true),
    ('max_concurrent_executions', '10', 'Maximum concurrent workflow executions', false)
ON CONFLICT (setting_key) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA pilotpros TO pilotpros_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA pilotpros TO pilotpros_user;