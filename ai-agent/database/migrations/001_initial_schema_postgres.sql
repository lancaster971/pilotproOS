-- PostgreSQL Schema per n8n MCP Server
-- Database per sincronizzazione dati da n8n API

-- Abilita estensioni utili
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABELLE PRINCIPALI
-- ============================================

-- Tabella workflows
CREATE TABLE IF NOT EXISTS workflows (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT false,
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Metriche calcolate
    complexity_score INTEGER DEFAULT 0,
    reliability_score INTEGER DEFAULT 0,
    efficiency_score INTEGER DEFAULT 0,
    health_score INTEGER DEFAULT 0,
    
    -- Statistiche esecuzione
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_duration_ms NUMERIC(10,2) DEFAULT 0,
    min_duration_ms NUMERIC(10,2) DEFAULT 0,
    max_duration_ms NUMERIC(10,2) DEFAULT 0,
    last_execution_at TIMESTAMP,
    last_success_at TIMESTAMP,
    last_failure_at TIMESTAMP,
    
    -- Contatori struttura
    node_count INTEGER DEFAULT 0,
    connection_count INTEGER DEFAULT 0,
    unique_node_types INTEGER DEFAULT 0,
    
    -- Metadata JSON
    tags JSONB,
    settings JSONB,
    static_data JSONB,
    pinned_data JSONB,
    
    -- Versioning
    version_id VARCHAR(100),
    is_latest BOOLEAN DEFAULT true
);

-- Indici per workflows
CREATE INDEX IF NOT EXISTS idx_workflows_active ON workflows(active);
CREATE INDEX IF NOT EXISTS idx_workflows_updated ON workflows(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflows_health ON workflows(health_score DESC);

-- Tabella workflow_nodes
CREATE TABLE IF NOT EXISTS workflow_nodes (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) REFERENCES workflows(id) ON DELETE CASCADE,
    node_id VARCHAR(255) NOT NULL,
    node_type VARCHAR(255) NOT NULL,
    node_name VARCHAR(255),
    
    -- Configurazione
    parameters JSONB,
    position JSONB,
    type_version INTEGER DEFAULT 1,
    credentials JSONB,
    
    -- Metriche nodo
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_execution_time_ms NUMERIC(10,2) DEFAULT 0,
    error_rate NUMERIC(5,2) DEFAULT 0,
    
    -- Metadata
    disabled BOOLEAN DEFAULT false,
    notes TEXT,
    color VARCHAR(7),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(workflow_id, node_id)
);

-- Indici per workflow_nodes
CREATE INDEX IF NOT EXISTS idx_nodes_workflow ON workflow_nodes(workflow_id);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON workflow_nodes(node_type);

-- Tabella workflow_connections
CREATE TABLE IF NOT EXISTS workflow_connections (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) REFERENCES workflows(id) ON DELETE CASCADE,
    
    source_node VARCHAR(255) NOT NULL,
    source_type VARCHAR(255),
    source_output INTEGER DEFAULT 0,
    
    target_node VARCHAR(255) NOT NULL,
    target_type VARCHAR(255),
    target_input INTEGER DEFAULT 0,
    
    connection_type VARCHAR(50) DEFAULT 'main',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indici per connections
CREATE INDEX IF NOT EXISTS idx_connections_workflow ON workflow_connections(workflow_id);

-- Tabella executions
CREATE TABLE IF NOT EXISTS executions (
    id VARCHAR(255) PRIMARY KEY,
    workflow_id VARCHAR(255) REFERENCES workflows(id) ON DELETE CASCADE,
    
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    duration_ms INTEGER,
    
    status VARCHAR(50) DEFAULT 'running',
    mode VARCHAR(50) DEFAULT 'manual',
    
    retry_of VARCHAR(255),
    retry_success_id VARCHAR(255),
    
    data JSONB,
    nodes_executed INTEGER DEFAULT 0,
    
    error_message TEXT,
    error_node VARCHAR(255),
    error_stack TEXT,
    
    data_in_kb NUMERIC(10,2),
    data_out_kb NUMERIC(10,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indici per executions
CREATE INDEX IF NOT EXISTS idx_executions_workflow ON executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_started ON executions(started_at DESC);

-- Tabella execution_node_results
CREATE TABLE IF NOT EXISTS execution_node_results (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(255) REFERENCES executions(id) ON DELETE CASCADE,
    workflow_id VARCHAR(255) REFERENCES workflows(id) ON DELETE CASCADE,
    
    node_id VARCHAR(255) NOT NULL,
    node_type VARCHAR(255),
    
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    execution_time_ms INTEGER,
    
    status VARCHAR(50),
    items_input INTEGER DEFAULT 0,
    items_output INTEGER DEFAULT 0,
    
    data JSONB,
    error_message TEXT,
    error_details JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indici per node results
CREATE INDEX IF NOT EXISTS idx_node_results_execution ON execution_node_results(execution_id);

-- Tabella kpi_snapshots
CREATE TABLE IF NOT EXISTS kpi_snapshots (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255),
    period_type VARCHAR(10) NOT NULL,
    snapshot_date TIMESTAMP NOT NULL,
    
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    success_rate NUMERIC(5,2) DEFAULT 0,
    
    avg_duration_ms NUMERIC(10,2),
    p50_duration_ms NUMERIC(10,2),
    p90_duration_ms NUMERIC(10,2),
    p95_duration_ms NUMERIC(10,2),
    p99_duration_ms NUMERIC(10,2),
    
    total_data_processed_mb NUMERIC(10,2) DEFAULT 0,
    avg_data_per_execution_kb NUMERIC(10,2) DEFAULT 0,
    
    error_rate NUMERIC(5,2) DEFAULT 0,
    mtbf_hours NUMERIC(10,2),
    mttr_minutes NUMERIC(10,2),
    
    avg_complexity_score NUMERIC(5,2),
    avg_reliability_score NUMERIC(5,2),
    avg_efficiency_score NUMERIC(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(workflow_id, period_type, snapshot_date)
);

-- Indici per kpi
CREATE INDEX IF NOT EXISTS idx_kpi_workflow ON kpi_snapshots(workflow_id);
CREATE INDEX IF NOT EXISTS idx_kpi_date ON kpi_snapshots(snapshot_date DESC);

-- Tabella hourly_stats
CREATE TABLE IF NOT EXISTS hourly_stats (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255),
    stat_date DATE NOT NULL,
    stat_hour INTEGER NOT NULL CHECK (stat_hour >= 0 AND stat_hour <= 23),
    
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    
    avg_duration_ms NUMERIC(10,2),
    min_duration_ms NUMERIC(10,2),
    max_duration_ms NUMERIC(10,2),
    
    concurrent_executions_max INTEGER,
    queue_size_max INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(workflow_id, stat_date, stat_hour)
);

-- Tabella error_logs
CREATE TABLE IF NOT EXISTS error_logs (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255),
    execution_id VARCHAR(255),
    node_id VARCHAR(255),
    
    error_type VARCHAR(100),
    error_code VARCHAR(50),
    error_message TEXT,
    error_stack TEXT,
    
    context JSONB,
    severity VARCHAR(20) DEFAULT 'medium',
    
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indici per errors
CREATE INDEX IF NOT EXISTS idx_errors_workflow ON error_logs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_errors_unresolved ON error_logs(is_resolved) WHERE is_resolved = false;

-- Tabella workflow_audit_log
CREATE TABLE IF NOT EXISTS workflow_audit_log (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    
    action VARCHAR(50) NOT NULL,
    user_id VARCHAR(255),
    user_email VARCHAR(255),
    
    changes JSONB,
    old_values JSONB,
    new_values JSONB,
    
    version_before VARCHAR(100),
    version_after VARCHAR(100),
    
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indici per audit
CREATE INDEX IF NOT EXISTS idx_audit_workflow ON workflow_audit_log(workflow_id);
CREATE INDEX IF NOT EXISTS idx_audit_performed ON workflow_audit_log(performed_at DESC);

-- Tabella performance_benchmarks
CREATE TABLE IF NOT EXISTS performance_benchmarks (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    benchmark_date TIMESTAMP NOT NULL,
    
    p1_duration_ms NUMERIC(10,2),
    p5_duration_ms NUMERIC(10,2),
    p10_duration_ms NUMERIC(10,2),
    p25_duration_ms NUMERIC(10,2),
    p50_duration_ms NUMERIC(10,2),
    p75_duration_ms NUMERIC(10,2),
    p90_duration_ms NUMERIC(10,2),
    p95_duration_ms NUMERIC(10,2),
    p99_duration_ms NUMERIC(10,2),
    p99_9_duration_ms NUMERIC(10,2),
    
    mean_duration_ms NUMERIC(10,2),
    std_deviation_ms NUMERIC(10,2),
    sample_size INTEGER DEFAULT 0,
    
    executions_per_hour NUMERIC(10,2),
    executions_per_day NUMERIC(10,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(workflow_id, benchmark_date)
);

-- Tabella tags
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    color VARCHAR(7),
    icon VARCHAR(50),
    usage_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indici per tags
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);

-- Tabella workflow_tags (many-to-many)
CREATE TABLE IF NOT EXISTS workflow_tags (
    workflow_id VARCHAR(255) REFERENCES workflows(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (workflow_id, tag_id)
);

-- ============================================
-- VISTE MATERIALIZZATE
-- ============================================

-- Vista workflow health
CREATE OR REPLACE VIEW workflow_health AS
SELECT 
    w.id,
    w.name,
    w.active,
    w.health_score,
    w.complexity_score,
    w.reliability_score,
    w.efficiency_score,
    w.execution_count,
    w.failure_count,
    w.last_execution_at,
    CASE 
        WHEN w.health_score >= 80 THEN 'healthy'
        WHEN w.health_score >= 60 THEN 'warning'
        WHEN w.health_score >= 40 THEN 'critical'
        ELSE 'failing'
    END as health_status,
    CASE 
        WHEN w.last_execution_at IS NULL THEN 'never_run'
        WHEN w.last_execution_at < NOW() - INTERVAL '30 days' THEN 'stale'
        WHEN w.last_execution_at < NOW() - INTERVAL '7 days' THEN 'inactive'
        ELSE 'active'
    END as activity_status
FROM workflows w;

-- Vista execution trends
CREATE OR REPLACE VIEW execution_trends AS
SELECT 
    DATE(e.started_at) as execution_date,
    e.workflow_id,
    COUNT(*) as total_executions,
    SUM(CASE WHEN e.status = 'success' THEN 1 ELSE 0 END) as successful_executions,
    SUM(CASE WHEN e.status = 'error' THEN 1 ELSE 0 END) as failed_executions,
    AVG(e.duration_ms) as avg_duration_ms,
    MIN(e.duration_ms) as min_duration_ms,
    MAX(e.duration_ms) as max_duration_ms
FROM executions e
WHERE e.started_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(e.started_at), e.workflow_id;

-- Vista problematic workflows
CREATE OR REPLACE VIEW problematic_workflows AS
SELECT 
    w.id,
    w.name,
    w.failure_count,
    w.execution_count,
    CASE 
        WHEN w.execution_count > 0 
        THEN ROUND((w.failure_count::numeric / w.execution_count) * 100, 2)
        ELSE 0 
    END as error_rate,
    w.last_failure_at,
    COUNT(DISTINCT el.id) as unique_errors,
    w.health_score
FROM workflows w
LEFT JOIN error_logs el ON w.id = el.workflow_id AND el.is_resolved = false
WHERE w.failure_count > 0 
   OR w.health_score < 60
GROUP BY w.id, w.name, w.failure_count, w.execution_count, w.last_failure_at, w.health_score
ORDER BY w.health_score ASC, w.failure_count DESC;

-- ============================================
-- TRIGGERS E FUNZIONI
-- ============================================

-- Funzione per aggiornare updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Applica trigger a tabelle con updated_at
CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_nodes_updated_at BEFORE UPDATE ON workflow_nodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tags_updated_at BEFORE UPDATE ON tags
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- DATI INIZIALI
-- ============================================

-- Inserisci tag predefiniti
INSERT INTO tags (name, description, color) VALUES 
    ('production', 'Workflow in produzione', '#00C853'),
    ('development', 'Workflow in sviluppo', '#FFB300'),
    ('testing', 'Workflow in test', '#2196F3'),
    ('deprecated', 'Workflow deprecato', '#E53935'),
    ('critical', 'Workflow critico', '#D50000'),
    ('maintenance', 'In manutenzione', '#FFA726')
ON CONFLICT (name) DO NOTHING;