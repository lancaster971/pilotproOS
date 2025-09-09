-- Migrazione 005: Schema Multi-Tenant con JSONB Storage
-- Data: 2025-08-12
-- Descrizione: Trasforma il database per supportare 1000+ tenant diversi con schema flessibile

-- =====================================================
-- STEP 1: TENANTS - Tabella principale per multi-tenancy
-- =====================================================

CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    
    -- Configurazione n8n
    n8n_api_url VARCHAR(500) NOT NULL,
    n8n_version VARCHAR(20),
    instance_type VARCHAR(50), -- cloud, self-hosted, docker, kubernetes
    
    -- Schema capabilities
    api_capabilities JSONB DEFAULT '{}',  -- Quali endpoint/campi supporta questa istanza
    schema_signature VARCHAR(100),        -- Hash dello schema rilevato
    last_schema_check TIMESTAMP,
    
    -- Configurazione sync
    sync_enabled BOOLEAN DEFAULT true,
    sync_interval_minutes INTEGER DEFAULT 5,
    max_executions_to_keep INTEGER DEFAULT 10000,
    
    -- Stats
    total_workflows INTEGER DEFAULT 0,
    total_executions INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TIMESTAMP
);

-- Indici per performance
CREATE INDEX IF NOT EXISTS idx_tenants_sync_enabled ON tenants(sync_enabled);
CREATE INDEX IF NOT EXISTS idx_tenants_schema_signature ON tenants(schema_signature);

-- =====================================================
-- STEP 2: WORKFLOWS Multi-Tenant con JSONB
-- =====================================================

CREATE TABLE IF NOT EXISTS tenant_workflows (
    -- Identificativi
    id VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    
    -- CAMPI UNIVERSALI (garantiti su TUTTE le versioni n8n)
    name VARCHAR(255) NOT NULL,
    active BOOLEAN DEFAULT false,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    -- TUTTO IL RESTO in JSONB per flessibilità massima
    raw_data JSONB NOT NULL,
    
    -- Campi calcolati per performance (aggiunti tramite trigger invece di generated columns)
    node_count INTEGER DEFAULT 0,
    has_webhook BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    
    -- Metadata
    schema_version VARCHAR(20) DEFAULT '1.0',
    last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- Indici ottimizzati
CREATE INDEX IF NOT EXISTS idx_tenant_workflows_tenant ON tenant_workflows(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_workflows_active ON tenant_workflows(tenant_id, active);
CREATE INDEX IF NOT EXISTS idx_tenant_workflows_archived ON tenant_workflows(tenant_id, is_archived);
CREATE INDEX IF NOT EXISTS idx_tenant_workflows_webhook ON tenant_workflows(tenant_id, has_webhook);
CREATE INDEX IF NOT EXISTS idx_tenant_workflows_updated ON tenant_workflows(tenant_id, updated_at DESC);

-- Indice GIN per query complesse su JSONB
CREATE INDEX IF NOT EXISTS idx_tenant_workflows_raw_data_gin ON tenant_workflows USING GIN (raw_data);

-- Indici specifici per query comuni
CREATE INDEX IF NOT EXISTS idx_tenant_workflows_nodes_gin ON tenant_workflows USING GIN ((raw_data->'nodes'));
CREATE INDEX IF NOT EXISTS idx_tenant_workflows_settings_gin ON tenant_workflows USING GIN ((raw_data->'settings'));

-- =====================================================
-- STEP 3: EXECUTIONS Multi-Tenant con JSONB  
-- =====================================================

CREATE TABLE IF NOT EXISTS tenant_executions (
    -- Identificativi
    id VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    workflow_id VARCHAR(255) NOT NULL,
    
    -- CAMPI UNIVERSALI
    started_at TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'running',
    mode VARCHAR(50) DEFAULT 'manual',
    
    -- TUTTO IL RESTO in JSONB
    raw_data JSONB NOT NULL,
    
    -- Campi calcolati per performance (aggiunti tramite trigger)
    finished BOOLEAN DEFAULT false,
    stopped_at TIMESTAMP,
    duration_ms INTEGER,
    has_error BOOLEAN DEFAULT false,
    
    -- Metadata
    last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, workflow_id) REFERENCES tenant_workflows(tenant_id, id) ON DELETE CASCADE
);

-- Indici ottimizzati
CREATE INDEX IF NOT EXISTS idx_tenant_executions_tenant ON tenant_executions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_executions_workflow ON tenant_executions(tenant_id, workflow_id);
CREATE INDEX IF NOT EXISTS idx_tenant_executions_status ON tenant_executions(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_tenant_executions_started ON tenant_executions(tenant_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_tenant_executions_error ON tenant_executions(tenant_id, has_error) WHERE has_error = true;

-- Indice GIN per JSONB
CREATE INDEX IF NOT EXISTS idx_tenant_executions_raw_data_gin ON tenant_executions USING GIN (raw_data);

-- =====================================================
-- STEP 4: TENANT SCHEMA DISCOVERY
-- =====================================================

CREATE TABLE IF NOT EXISTS tenant_schema_discoveries (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(100) NOT NULL,
    
    -- Discovery result
    discovery_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    n8n_version_detected VARCHAR(20),
    
    -- Endpoints disponibili
    available_endpoints JSONB DEFAULT '[]',
    
    -- Campi rilevati per endpoint
    workflow_fields JSONB DEFAULT '[]',
    execution_fields JSONB DEFAULT '[]',
    
    -- Custom nodes rilevati
    custom_nodes JSONB DEFAULT '[]',
    
    -- Schema capabilities
    supports_webhooks BOOLEAN DEFAULT false,
    supports_credentials BOOLEAN DEFAULT false,
    supports_tags BOOLEAN DEFAULT false,
    supports_projects BOOLEAN DEFAULT false,
    
    -- Stats
    total_workflows_analyzed INTEGER DEFAULT 0,
    total_executions_analyzed INTEGER DEFAULT 0,
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_schema_discoveries_tenant ON tenant_schema_discoveries(tenant_id);
CREATE INDEX IF NOT EXISTS idx_schema_discoveries_date ON tenant_schema_discoveries(discovery_date DESC);

-- =====================================================
-- STEP 5: SYNC LOGS Multi-Tenant
-- =====================================================

CREATE TABLE IF NOT EXISTS tenant_sync_logs (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(100) NOT NULL,
    
    -- Sync info
    sync_type VARCHAR(50) NOT NULL, -- workflows, executions, full
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'running', -- running, completed, failed
    
    -- Results
    items_processed INTEGER DEFAULT 0,
    items_added INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,
    items_deleted INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    
    -- Error tracking
    error_message TEXT,
    error_details JSONB,
    
    -- Performance
    duration_ms INTEGER,
    api_calls_made INTEGER DEFAULT 0,
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sync_logs_tenant ON tenant_sync_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sync_logs_started ON tenant_sync_logs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_sync_logs_status ON tenant_sync_logs(status);

-- =====================================================
-- STEP 6: FUNZIONI UTILITY Multi-Tenant
-- =====================================================

-- Funzione per calcolare campi derivati nei workflows
CREATE OR REPLACE FUNCTION calculate_workflow_derived_fields()
RETURNS TRIGGER AS $$
BEGIN
    -- Calcola node_count
    NEW.node_count = CASE 
        WHEN NEW.raw_data->'nodes' IS NOT NULL 
        THEN jsonb_array_length(NEW.raw_data->'nodes')
        ELSE 0 
    END;
    
    -- Calcola has_webhook
    NEW.has_webhook = (NEW.raw_data->'nodes' @> '[{"type": "n8n-nodes-base.webhook"}]' 
                      OR NEW.raw_data->'nodes' @> '[{"type": "webhook"}]');
    
    -- Calcola is_archived
    NEW.is_archived = COALESCE((NEW.raw_data->>'isArchived')::boolean, false);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Funzione per calcolare campi derivati nelle executions  
CREATE OR REPLACE FUNCTION calculate_execution_derived_fields()
RETURNS TRIGGER AS $$
BEGIN
    -- Calcola finished
    NEW.finished = COALESCE((NEW.raw_data->>'finished')::boolean, false);
    
    -- Calcola stopped_at
    NEW.stopped_at = CASE 
        WHEN NEW.raw_data->>'stoppedAt' IS NOT NULL 
        THEN (NEW.raw_data->>'stoppedAt')::timestamp
        ELSE NULL 
    END;
    
    -- Calcola duration_ms
    NEW.duration_ms = CASE 
        WHEN NEW.raw_data->>'stoppedAt' IS NOT NULL AND NEW.raw_data->>'startedAt' IS NOT NULL
        THEN EXTRACT(EPOCH FROM ((NEW.raw_data->>'stoppedAt')::timestamp - (NEW.raw_data->>'startedAt')::timestamp)) * 1000
        ELSE NULL
    END::integer;
    
    -- Calcola has_error
    NEW.has_error = (NEW.status = 'error' OR NEW.raw_data->>'status' = 'error');
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Funzione per aggiornare last_synced_at automaticamente
CREATE OR REPLACE FUNCTION update_tenant_last_sync()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE tenants 
    SET last_sync_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.tenant_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger per calcolare campi derivati
CREATE TRIGGER trigger_calculate_workflow_fields
    BEFORE INSERT OR UPDATE ON tenant_workflows
    FOR EACH ROW
    EXECUTE FUNCTION calculate_workflow_derived_fields();

CREATE TRIGGER trigger_calculate_execution_fields
    BEFORE INSERT OR UPDATE ON tenant_executions
    FOR EACH ROW
    EXECUTE FUNCTION calculate_execution_derived_fields();

-- Trigger per aggiornare automaticamente tenant sync timestamp
CREATE TRIGGER trigger_update_tenant_sync_workflows
    AFTER INSERT OR UPDATE ON tenant_workflows
    FOR EACH ROW
    EXECUTE FUNCTION update_tenant_last_sync();

CREATE TRIGGER trigger_update_tenant_sync_executions
    AFTER INSERT OR UPDATE ON tenant_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_tenant_last_sync();

-- Funzione per ottenere stats tenant
CREATE OR REPLACE FUNCTION get_tenant_stats(p_tenant_id VARCHAR)
RETURNS TABLE (
    total_workflows BIGINT,
    active_workflows BIGINT,
    total_executions BIGINT,
    recent_executions BIGINT,
    success_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_workflows,
        COUNT(*) FILTER (WHERE active = true)::BIGINT as active_workflows,
        (SELECT COUNT(*) FROM tenant_executions WHERE tenant_id = p_tenant_id)::BIGINT as total_executions,
        (SELECT COUNT(*) FROM tenant_executions WHERE tenant_id = p_tenant_id AND started_at > NOW() - INTERVAL '24 hours')::BIGINT as recent_executions,
        (SELECT 
            CASE 
                WHEN COUNT(*) > 0 THEN
                    (COUNT(*) FILTER (WHERE status = 'success')::NUMERIC / COUNT(*) * 100)
                ELSE 0 
            END
         FROM tenant_executions 
         WHERE tenant_id = p_tenant_id 
           AND started_at > NOW() - INTERVAL '7 days'
        )::NUMERIC as success_rate
    FROM tenant_workflows 
    WHERE tenant_id = p_tenant_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- STEP 7: VISTE Multi-Tenant
-- =====================================================

-- Vista workflows attivi per tenant
CREATE OR REPLACE VIEW tenant_active_workflows AS
SELECT 
    tenant_id,
    id,
    name,
    active,
    node_count,
    has_webhook,
    updated_at,
    raw_data->>'description' as description,
    raw_data->'settings'->>'executionOrder' as execution_order
FROM tenant_workflows 
WHERE active = true AND is_archived = false;

-- Vista executions recenti per tenant  
CREATE OR REPLACE VIEW tenant_recent_executions AS
SELECT 
    tenant_id,
    id,
    workflow_id,
    started_at,
    status,
    finished,
    duration_ms,
    has_error,
    raw_data->>'mode' as execution_mode
FROM tenant_executions 
WHERE started_at > NOW() - INTERVAL '24 hours'
ORDER BY started_at DESC;

-- Vista tenant health dashboard
CREATE OR REPLACE VIEW tenant_health_dashboard AS
SELECT 
    t.id as tenant_id,
    t.name as tenant_name,
    t.n8n_version,
    t.instance_type,
    COUNT(w.id) as total_workflows,
    COUNT(w.id) FILTER (WHERE w.active = true) as active_workflows,
    COUNT(e.id) FILTER (WHERE e.started_at > NOW() - INTERVAL '24 hours') as executions_24h,
    COUNT(e.id) FILTER (WHERE e.has_error = true AND e.started_at > NOW() - INTERVAL '24 hours') as errors_24h,
    CASE 
        WHEN COUNT(e.id) FILTER (WHERE e.started_at > NOW() - INTERVAL '24 hours') > 0 THEN
            ROUND(
                (COUNT(e.id) FILTER (WHERE e.status = 'success' AND e.started_at > NOW() - INTERVAL '24 hours')::NUMERIC / 
                 COUNT(e.id) FILTER (WHERE e.started_at > NOW() - INTERVAL '24 hours') * 100), 2
            )
        ELSE NULL 
    END as success_rate_24h
FROM tenants t
LEFT JOIN tenant_workflows w ON t.id = w.tenant_id
LEFT JOIN tenant_executions e ON t.id = e.tenant_id
WHERE t.sync_enabled = true
GROUP BY t.id, t.name, t.n8n_version, t.instance_type;

-- =====================================================
-- STEP 8: STORED PROCEDURES
-- =====================================================

-- Procedura per cleanup vecchie esecuzioni per tenant
CREATE OR REPLACE FUNCTION cleanup_tenant_executions(
    p_tenant_id VARCHAR,
    p_days_to_keep INTEGER DEFAULT 90
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM tenant_executions 
    WHERE tenant_id = p_tenant_id
      AND started_at < NOW() - INTERVAL '1 day' * p_days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RAISE NOTICE 'Eliminate % esecuzioni per tenant % più vecchie di % giorni', 
                 deleted_count, p_tenant_id, p_days_to_keep;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Procedura per migrazione dati da schema singolo a multi-tenant
CREATE OR REPLACE FUNCTION migrate_to_multitenant(
    p_tenant_id VARCHAR,
    p_tenant_name VARCHAR,
    p_n8n_api_url VARCHAR
)
RETURNS VOID AS $$
BEGIN
    -- 1. Crea tenant
    INSERT INTO tenants (id, name, n8n_api_url, schema_signature)
    VALUES (p_tenant_id, p_tenant_name, p_n8n_api_url, 'legacy_migration')
    ON CONFLICT (id) DO NOTHING;
    
    -- 2. Migra workflows
    INSERT INTO tenant_workflows (id, tenant_id, name, active, created_at, updated_at, raw_data)
    SELECT 
        w.id,
        p_tenant_id,
        w.name,
        w.active,
        w.created_at,
        w.updated_at,
        jsonb_build_object(
            'description', w.description,
            'isArchived', w.is_archived,
            'nodes', w.nodes,
            'connections', w.connections,
            'settings', w.settings,
            'staticData', w.static_data,
            'pinnedData', w.pinned_data,
            'meta', w.meta,
            'shared', w.shared,
            'versionId', w.version_id,
            'triggerCount', w.trigger_count,
            'tags', w.tags,
            'projectId', w.project_id,
            'ownerEmail', w.owner_email,
            'workflowType', w.workflow_type,
            'hasErrorHandler', w.has_error_handler,
            'modifiedBy', w.modified_by,
            'templateId', w.template_id,
            'nodeCount', w.node_count,
            'connectionCount', w.connection_count,
            'uniqueNodeTypes', w.unique_node_types,
            'aiNodeCount', w.ai_node_count,
            'databaseNodeCount', w.database_node_count,
            'httpNodeCount', w.http_node_count,
            'webhookNodeCount', w.webhook_node_count,
            'hasWaitNode', w.has_wait_node,
            'hasManualTrigger', w.has_manual_trigger,
            'complexityScore', w.complexity_score,
            'reliabilityScore', w.reliability_score,
            'efficiencyScore', w.efficiency_score,
            'healthScore', w.health_score,
            'executionCount', w.execution_count,
            'successCount', w.success_count,
            'failureCount', w.failure_count,
            'avgDurationMs', w.avg_duration_ms,
            'minDurationMs', w.min_duration_ms,
            'maxDurationMs', w.max_duration_ms,
            'lastExecutionAt', w.last_execution_at,
            'lastSuccessAt', w.last_success_at,
            'lastFailureAt', w.last_failure_at
        )
    FROM workflows w
    ON CONFLICT (tenant_id, id) DO NOTHING;
    
    -- 3. Migra executions
    INSERT INTO tenant_executions (id, tenant_id, workflow_id, started_at, status, mode, raw_data)
    SELECT 
        e.id,
        p_tenant_id,
        e.workflow_id,
        e.started_at,
        e.status,
        e.mode,
        jsonb_build_object(
            'finished', e.finished,
            'finishedAt', e.finished_at,
            'stoppedAt', e.stopped_at,
            'durationMs', e.duration_ms,
            'retryOf', e.retry_of,
            'retrySuccessId', e.retry_success_id,
            'data', e.data,
            'workflowData', e.workflow_data,
            'waitTill', e.wait_till,
            'nodesExecuted', e.nodes_executed,
            'errorMessage', e.error_message,
            'errorNode', e.error_node,
            'errorNodeId', e.error_node_id,
            'errorNodeType', e.error_node_type,
            'errorStack', e.error_stack,
            'dataInKb', e.data_in_kb,
            'dataOutKb', e.data_out_kb,
            'startedAt', e.started_at,
            'createdAt', e.created_at
        )
    FROM executions e
    ON CONFLICT (tenant_id, id) DO NOTHING;
    
    RAISE NOTICE 'Migrazione completata per tenant %', p_tenant_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- STEP 9: SECURITY & PERFORMANCE
-- =====================================================

-- Row Level Security per isolamento tenant
ALTER TABLE tenant_workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_executions ENABLE ROW LEVEL SECURITY;

-- Esempio policy (da adattare in base alle esigenze di auth)
-- CREATE POLICY tenant_isolation_workflows ON tenant_workflows
--   FOR ALL TO app_user
--   USING (tenant_id = current_setting('app.current_tenant_id'));

-- CREATE POLICY tenant_isolation_executions ON tenant_executions  
--   FOR ALL TO app_user
--   USING (tenant_id = current_setting('app.current_tenant_id'));

-- Commenti per documentazione
COMMENT ON TABLE tenants IS 'Tabella principale per multi-tenancy - ogni cliente è un tenant';
COMMENT ON TABLE tenant_workflows IS 'Workflows multi-tenant con JSONB per massima flessibilità schema';
COMMENT ON TABLE tenant_executions IS 'Executions multi-tenant con JSONB per adattabilità';
COMMENT ON TABLE tenant_schema_discoveries IS 'Discovery automatico delle capacità schema per ogni tenant';
COMMENT ON TABLE tenant_sync_logs IS 'Log delle sincronizzazioni per ogni tenant';

COMMENT ON COLUMN tenant_workflows.raw_data IS 'JSONB con TUTTI i dati del workflow - si adatta a qualsiasi versione n8n';
COMMENT ON COLUMN tenant_executions.raw_data IS 'JSONB con TUTTI i dati execution - compatibile con tutte le versioni';
COMMENT ON COLUMN tenants.api_capabilities IS 'JSONB con elenco endpoint/campi supportati da questa istanza n8n';
COMMENT ON COLUMN tenants.schema_signature IS 'Hash che identifica la "firma" dello schema di questo tenant';

-- Fine migrazione 005