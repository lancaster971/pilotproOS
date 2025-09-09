-- Migrazione 004: Aggiunge TUTTI i campi mancanti identificati dall'analisi API completa
-- Data: 2025-08-12
-- Descrizione: Completa lo schema per catturare TUTTI i dati disponibili dalle API n8n

-- =====================================================
-- WORKFLOWS - Campi strutturali mancanti
-- =====================================================

-- Aggiungi campi JSON per struttura completa workflow
ALTER TABLE workflows 
ADD COLUMN IF NOT EXISTS nodes JSONB,
ADD COLUMN IF NOT EXISTS connections JSONB;

COMMENT ON COLUMN workflows.nodes IS 'Array completo dei nodi del workflow (struttura originale n8n)';
COMMENT ON COLUMN workflows.connections IS 'Mappa completa delle connessioni tra nodi';

-- Aggiungi campi per classificazione avanzata
ALTER TABLE workflows
ADD COLUMN IF NOT EXISTS webhook_node_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS has_wait_node BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS has_manual_trigger BOOLEAN DEFAULT false;

COMMENT ON COLUMN workflows.webhook_node_count IS 'Numero di nodi webhook nel workflow';
COMMENT ON COLUMN workflows.has_wait_node IS 'Se il workflow ha nodi di attesa';
COMMENT ON COLUMN workflows.has_manual_trigger IS 'Se il workflow ha trigger manuali';

-- =====================================================
-- EXECUTIONS - Campi mancanti critici
-- =====================================================

-- Aggiungi flag finished (importante per monitoraggio)
ALTER TABLE executions
ADD COLUMN IF NOT EXISTS finished BOOLEAN DEFAULT false;

COMMENT ON COLUMN executions.finished IS 'Se l''esecuzione è completata';

-- Correggi tipo di stopped_at da BIGINT a TIMESTAMP
ALTER TABLE executions
ADD COLUMN IF NOT EXISTS stopped_at TIMESTAMP;

-- Aggiungi wait_till per esecuzioni in attesa
ALTER TABLE executions
ADD COLUMN IF NOT EXISTS wait_till TIMESTAMP;

COMMENT ON COLUMN executions.wait_till IS 'Timestamp fino a quando l''esecuzione è in attesa';

-- Aggiungi workflow_data per snapshot del workflow al momento dell'esecuzione
ALTER TABLE executions
ADD COLUMN IF NOT EXISTS workflow_data JSONB;

COMMENT ON COLUMN executions.workflow_data IS 'Snapshot del workflow al momento dell''esecuzione';

-- Aggiungi dettagli errore
ALTER TABLE executions
ADD COLUMN IF NOT EXISTS error_node_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS error_node_type VARCHAR(100);

COMMENT ON COLUMN executions.error_node_id IS 'ID del nodo che ha causato l''errore';
COMMENT ON COLUMN executions.error_node_type IS 'Tipo del nodo che ha causato l''errore';

-- =====================================================
-- WORKFLOW_NODES - Campi aggiuntivi
-- =====================================================

-- Aggiungi campi mancanti per i nodi
ALTER TABLE workflow_nodes
ADD COLUMN IF NOT EXISTS webhook_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS continue_on_fail BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS execute_once BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS notes_in_flow BOOLEAN DEFAULT false;

COMMENT ON COLUMN workflow_nodes.webhook_id IS 'ID webhook per nodi trigger webhook';
COMMENT ON COLUMN workflow_nodes.continue_on_fail IS 'Continua workflow se il nodo fallisce';
COMMENT ON COLUMN workflow_nodes.execute_once IS 'Esegui nodo solo una volta';
COMMENT ON COLUMN workflow_nodes.notes_in_flow IS 'Mostra note nel flow';

-- =====================================================
-- NUOVA TABELLA: workflow_runs_metadata
-- Per tracciare metadata aggiuntivi delle esecuzioni
-- =====================================================

CREATE TABLE IF NOT EXISTS workflow_run_metadata (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,
    workflow_id VARCHAR(255) NOT NULL,
    
    -- Metadata esecuzione
    trigger_type VARCHAR(50), -- webhook, schedule, manual, api
    trigger_node_id VARCHAR(255),
    trigger_timestamp TIMESTAMP,
    
    -- Context
    user_id VARCHAR(255),
    user_email VARCHAR(255),
    api_key_used VARCHAR(100),
    source_ip VARCHAR(45),
    
    -- Performance
    total_nodes_executed INTEGER DEFAULT 0,
    nodes_skipped INTEGER DEFAULT 0,
    nodes_failed INTEGER DEFAULT 0,
    
    -- Data size
    input_data_size_bytes INTEGER,
    output_data_size_bytes INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_workflow_run_metadata_execution ON workflow_run_metadata(execution_id);
CREATE INDEX IF NOT EXISTS idx_workflow_run_metadata_workflow ON workflow_run_metadata(workflow_id);

-- =====================================================
-- NUOVA TABELLA: workflow_versions
-- Per tracciare versioni dei workflow
-- =====================================================

CREATE TABLE IF NOT EXISTS workflow_versions (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    version_id VARCHAR(100) NOT NULL,
    version_number INTEGER,
    
    -- Snapshot completo
    workflow_data JSONB NOT NULL,
    
    -- Metadata versione
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_description TEXT,
    
    -- Flags
    is_current BOOLEAN DEFAULT false,
    is_published BOOLEAN DEFAULT false,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    UNIQUE(workflow_id, version_id)
);

CREATE INDEX IF NOT EXISTS idx_workflow_versions_workflow ON workflow_versions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_versions_current ON workflow_versions(workflow_id, is_current) WHERE is_current = true;

-- =====================================================
-- NUOVA TABELLA: workflow_schedules
-- Per tracciare scheduling dei workflow
-- =====================================================

CREATE TABLE IF NOT EXISTS workflow_schedules (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    
    -- Cron expression
    cron_expression VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Stato
    is_active BOOLEAN DEFAULT true,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    
    -- Stats
    total_runs INTEGER DEFAULT 0,
    successful_runs INTEGER DEFAULT 0,
    failed_runs INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    UNIQUE(workflow_id)
);

CREATE INDEX IF NOT EXISTS idx_workflow_schedules_next_run ON workflow_schedules(next_run_at) WHERE is_active = true;

-- =====================================================
-- NUOVA TABELLA: workflow_webhooks
-- Per tracciare webhook dei workflow
-- =====================================================

CREATE TABLE IF NOT EXISTS workflow_webhooks (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    webhook_id VARCHAR(255) NOT NULL,
    
    -- Config webhook
    path VARCHAR(255),
    method VARCHAR(10) DEFAULT 'POST',
    
    -- Auth
    requires_auth BOOLEAN DEFAULT false,
    auth_type VARCHAR(50), -- basic, bearer, custom
    
    -- Stats
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    failed_calls INTEGER DEFAULT 0,
    last_called_at TIMESTAMP,
    
    -- Rate limiting
    rate_limit INTEGER, -- calls per minute
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    UNIQUE(webhook_id)
);

CREATE INDEX IF NOT EXISTS idx_workflow_webhooks_workflow ON workflow_webhooks(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_webhooks_path ON workflow_webhooks(path);

-- =====================================================
-- VISTE AVANZATE
-- =====================================================

-- Vista workflow con tutti i dettagli
CREATE OR REPLACE VIEW workflow_complete AS
SELECT 
    w.*,
    COUNT(DISTINCT wn.node_id) as actual_node_count,
    COUNT(DISTINCT wc.id) as actual_connection_count,
    COUNT(DISTINCT wt.tag_id) as tag_count,
    MAX(e.started_at) as last_execution_start,
    COUNT(DISTINCT e.id) FILTER (WHERE e.started_at > NOW() - INTERVAL '24 hours') as executions_last_24h,
    COUNT(DISTINCT e.id) FILTER (WHERE e.started_at > NOW() - INTERVAL '7 days') as executions_last_7d,
    COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'error' AND e.started_at > NOW() - INTERVAL '24 hours') as errors_last_24h
FROM workflows w
LEFT JOIN workflow_nodes wn ON w.id = wn.workflow_id
LEFT JOIN workflow_connections wc ON w.id = wc.workflow_id
LEFT JOIN workflow_tags wt ON w.id = wt.workflow_id
LEFT JOIN executions e ON w.id = e.workflow_id
GROUP BY w.id;

-- Vista esecuzioni con dettagli workflow
CREATE OR REPLACE VIEW execution_details AS
SELECT 
    e.*,
    w.name as workflow_name,
    w.active as workflow_active,
    w.workflow_type,
    EXTRACT(EPOCH FROM (e.stopped_at - e.started_at)) * 1000 as calculated_duration_ms,
    CASE 
        WHEN e.status = 'success' THEN 'Successo'
        WHEN e.status = 'error' THEN 'Errore'
        WHEN e.status = 'running' THEN 'In Esecuzione'
        WHEN e.status = 'waiting' THEN 'In Attesa'
        ELSE 'Sconosciuto'
    END as status_label
FROM executions e
JOIN workflows w ON e.workflow_id = w.id;

-- Vista per monitoraggio real-time
CREATE OR REPLACE VIEW monitoring_dashboard AS
SELECT 
    (SELECT COUNT(*) FROM workflows WHERE active = true AND is_archived = false) as active_workflows,
    (SELECT COUNT(*) FROM executions WHERE status = 'running') as running_executions,
    (SELECT COUNT(*) FROM executions WHERE status = 'error' AND started_at > NOW() - INTERVAL '1 hour') as recent_errors,
    (SELECT AVG(duration_ms) FROM executions WHERE started_at > NOW() - INTERVAL '1 hour' AND duration_ms IS NOT NULL) as avg_duration_last_hour,
    (SELECT COUNT(*) FROM executions WHERE started_at > NOW() - INTERVAL '1 hour') as executions_last_hour,
    (SELECT COUNT(DISTINCT workflow_id) FROM executions WHERE started_at > NOW() - INTERVAL '1 hour') as unique_workflows_last_hour;

-- =====================================================
-- FUNZIONI UTILITY
-- =====================================================

-- Funzione per calcolare statistiche workflow
CREATE OR REPLACE FUNCTION calculate_workflow_stats(p_workflow_id VARCHAR)
RETURNS TABLE (
    total_executions BIGINT,
    successful_executions BIGINT,
    failed_executions BIGINT,
    avg_duration_ms NUMERIC,
    success_rate NUMERIC,
    last_7d_executions BIGINT,
    last_30d_executions BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_executions,
        COUNT(*) FILTER (WHERE status = 'success')::BIGINT as successful_executions,
        COUNT(*) FILTER (WHERE status = 'error')::BIGINT as failed_executions,
        AVG(duration_ms)::NUMERIC as avg_duration_ms,
        (COUNT(*) FILTER (WHERE status = 'success')::NUMERIC / NULLIF(COUNT(*), 0) * 100)::NUMERIC as success_rate,
        COUNT(*) FILTER (WHERE started_at > NOW() - INTERVAL '7 days')::BIGINT as last_7d_executions,
        COUNT(*) FILTER (WHERE started_at > NOW() - INTERVAL '30 days')::BIGINT as last_30d_executions
    FROM executions
    WHERE workflow_id = p_workflow_id;
END;
$$ LANGUAGE plpgsql;

-- Funzione per pulire vecchie esecuzioni
CREATE OR REPLACE FUNCTION cleanup_old_executions(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM executions 
    WHERE started_at < NOW() - INTERVAL '1 day' * days_to_keep
    AND workflow_id NOT IN (
        SELECT DISTINCT workflow_id 
        FROM workflows 
        WHERE workflow_type IN ('critical', 'audit')
    );
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RAISE NOTICE 'Eliminate % esecuzioni più vecchie di % giorni', deleted_count, days_to_keep;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- INDICI AGGIUNTIVI PER PERFORMANCE
-- =====================================================

-- Indici su campi JSONB per query veloci
CREATE INDEX IF NOT EXISTS idx_workflows_nodes_gin ON workflows USING GIN (nodes);
CREATE INDEX IF NOT EXISTS idx_workflows_connections_gin ON workflows USING GIN (connections);
CREATE INDEX IF NOT EXISTS idx_workflows_meta_gin ON workflows USING GIN (meta);
CREATE INDEX IF NOT EXISTS idx_executions_data_gin ON executions USING GIN (data);
CREATE INDEX IF NOT EXISTS idx_executions_workflow_data_gin ON executions USING GIN (workflow_data);

-- Indici per query comuni
CREATE INDEX IF NOT EXISTS idx_executions_status_started ON executions(status, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_executions_workflow_status ON executions(workflow_id, status);
CREATE INDEX IF NOT EXISTS idx_workflows_active_not_archived ON workflows(active, is_archived) WHERE is_archived = false;

-- Indice per ricerca full-text nei nomi
CREATE INDEX IF NOT EXISTS idx_workflows_name_trgm ON workflows USING GIN (name gin_trgm_ops);

-- =====================================================
-- GRANT PERMISSIONS (se necessario)
-- =====================================================

-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO app_user;

-- Fine migrazione 004