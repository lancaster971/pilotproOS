-- ============================================================================
-- Schema Database n8n Analytics
-- Versione: 1.0.0
-- Descrizione: Schema completo per sistema di analytics avanzato n8n
-- Database supportati: PostgreSQL 12+, MySQL 8.0+
-- ============================================================================

-- ----------------------------------------------------------------------------
-- TABELLE PRINCIPALI
-- ----------------------------------------------------------------------------

-- Tabella workflows: contiene tutti i workflow con metriche calcolate
CREATE TABLE IF NOT EXISTS workflows (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Metriche calcolate
    complexity_score INTEGER DEFAULT 0,        -- Score complessità (0-100)
    reliability_score INTEGER DEFAULT 0,       -- Score affidabilità (0-100)
    efficiency_score INTEGER DEFAULT 0,        -- Score efficienza (0-100)
    health_score INTEGER DEFAULT 0,           -- Score salute generale (0-100)
    
    -- Statistiche esecuzione
    execution_count INTEGER DEFAULT 0,        -- Numero totale esecuzioni
    success_count INTEGER DEFAULT 0,          -- Numero esecuzioni con successo
    failure_count INTEGER DEFAULT 0,          -- Numero esecuzioni fallite
    avg_duration_ms INTEGER DEFAULT 0,        -- Durata media in millisecondi
    min_duration_ms INTEGER DEFAULT 0,        -- Durata minima
    max_duration_ms INTEGER DEFAULT 0,        -- Durata massima
    last_execution_at TIMESTAMP,              -- Ultima esecuzione
    last_success_at TIMESTAMP,                -- Ultimo successo
    last_failure_at TIMESTAMP,                -- Ultimo fallimento
    
    -- Contatori nodi
    node_count INTEGER DEFAULT 0,             -- Numero totale di nodi
    connection_count INTEGER DEFAULT 0,       -- Numero di connessioni
    unique_node_types INTEGER DEFAULT 0,      -- Tipi di nodi unici
    
    -- Metadati
    tags JSON,                                -- Array di tags
    settings JSON,                             -- Settings completi del workflow
    static_data JSON,                          -- Dati statici del workflow
    pinned_data JSON,                          -- Dati pinned per testing
    
    -- Informazioni versioning
    version_id VARCHAR(50),                   -- ID versione corrente
    is_latest BOOLEAN DEFAULT true,           -- Flag versione più recente
    
    -- Indici per performance
    INDEX idx_workflows_active (active),
    INDEX idx_workflows_complexity (complexity_score),
    INDEX idx_workflows_reliability (reliability_score),
    INDEX idx_workflows_last_execution (last_execution_at)
);

-- Tabella workflow_nodes: dettagli di ogni nodo nei workflow
CREATE TABLE IF NOT EXISTS workflow_nodes (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    node_id VARCHAR(255) NOT NULL,
    node_type VARCHAR(255) NOT NULL,          -- Tipo del nodo (es. n8n-nodes-base.httpRequest)
    node_name VARCHAR(255) NOT NULL,          -- Nome assegnato al nodo
    
    -- Configurazione nodo
    parameters JSON,                          -- Parametri del nodo
    position JSON,                             -- Posizione x,y nel canvas
    type_version DECIMAL(5,2),                -- Versione del tipo di nodo
    credentials JSON,                          -- ID credenziali utilizzate
    
    -- Metriche nodo
    execution_count INTEGER DEFAULT 0,        -- Quante volte è stato eseguito
    success_count INTEGER DEFAULT 0,          -- Esecuzioni con successo
    failure_count INTEGER DEFAULT 0,          -- Esecuzioni fallite
    avg_execution_time_ms INTEGER DEFAULT 0,  -- Tempo medio esecuzione
    error_rate DECIMAL(5,2) DEFAULT 0,        -- Tasso di errore percentuale
    
    -- Metadati
    disabled BOOLEAN DEFAULT false,           -- Se il nodo è disabilitato
    notes TEXT,                               -- Note sul nodo
    color VARCHAR(7),                         -- Colore personalizzato
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    UNIQUE KEY unique_workflow_node (workflow_id, node_id),
    INDEX idx_nodes_type (node_type),
    INDEX idx_nodes_workflow (workflow_id)
);

-- Tabella workflow_connections: mappa delle connessioni tra nodi
CREATE TABLE IF NOT EXISTS workflow_connections (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    
    -- Nodo sorgente
    source_node VARCHAR(255) NOT NULL,
    source_type VARCHAR(255),
    source_output INTEGER DEFAULT 0,          -- Indice output del nodo sorgente
    
    -- Nodo destinazione
    target_node VARCHAR(255) NOT NULL,
    target_type VARCHAR(255),
    target_input INTEGER DEFAULT 0,           -- Indice input del nodo destinazione
    
    -- Tipo connessione
    connection_type VARCHAR(50) DEFAULT 'main',  -- main, error, etc.
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    INDEX idx_connections_workflow (workflow_id),
    INDEX idx_connections_source (source_node),
    INDEX idx_connections_target (target_node)
);

-- Tabella executions: tracking completo delle esecuzioni
CREATE TABLE IF NOT EXISTS executions (
    id VARCHAR(255) PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    
    -- Timing
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    duration_ms INTEGER,                      -- Durata totale in millisecondi
    
    -- Status
    status VARCHAR(50) NOT NULL,              -- running, success, error, stopped
    mode VARCHAR(50),                         -- manual, trigger, webhook, cli
    retry_of VARCHAR(255),                    -- ID esecuzione che sta ritentando
    retry_success_id VARCHAR(255),            -- ID del retry che ha avuto successo
    
    -- Dati esecuzione
    data JSON,                                -- Dati completi esecuzione
    wait_till TIMESTAMP,                      -- Per esecuzioni in attesa
    
    -- Errori
    error_message TEXT,
    error_node VARCHAR(255),                  -- Nodo che ha causato l'errore
    error_stack TEXT,
    
    -- Metriche
    data_in_kb INTEGER DEFAULT 0,             -- Dimensione dati input in KB
    data_out_kb INTEGER DEFAULT 0,            -- Dimensione dati output in KB
    nodes_executed INTEGER DEFAULT 0,         -- Numero nodi eseguiti
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    INDEX idx_executions_workflow (workflow_id),
    INDEX idx_executions_status (status),
    INDEX idx_executions_started (started_at),
    INDEX idx_executions_finished (finished_at)
);

-- Tabella execution_node_results: risultati per ogni nodo in ogni esecuzione
CREATE TABLE IF NOT EXISTS execution_node_results (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(255) NOT NULL,
    workflow_id VARCHAR(255) NOT NULL,
    node_id VARCHAR(255) NOT NULL,
    node_type VARCHAR(255) NOT NULL,
    
    -- Timing
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    execution_time_ms INTEGER,                -- Tempo esecuzione del nodo
    
    -- Status
    status VARCHAR(50),                       -- success, error, skipped
    
    -- Dati
    items_input INTEGER DEFAULT 0,            -- Numero items in input
    items_output INTEGER DEFAULT 0,           -- Numero items in output
    data JSON,                                -- Dati output del nodo
    
    -- Errori
    error_message TEXT,
    error_details JSON,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    INDEX idx_node_results_execution (execution_id),
    INDEX idx_node_results_node (node_id)
);

-- ----------------------------------------------------------------------------
-- TABELLE ANALYTICS E KPI
-- ----------------------------------------------------------------------------

-- Tabella kpi_snapshots: snapshot KPI per diversi periodi temporali
CREATE TABLE IF NOT EXISTS kpi_snapshots (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255),                 -- NULL per KPI globali
    period_type VARCHAR(20) NOT NULL,         -- '24h', '7d', '30d', '90d'
    snapshot_date DATE NOT NULL,
    
    -- KPI Esecuzioni
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    
    -- KPI Performance
    avg_duration_ms INTEGER,
    p50_duration_ms INTEGER,                  -- Mediana
    p90_duration_ms INTEGER,                  -- 90° percentile
    p95_duration_ms INTEGER,                  -- 95° percentile
    p99_duration_ms INTEGER,                  -- 99° percentile
    
    -- KPI Volume
    total_data_processed_mb DECIMAL(10,2),
    avg_data_per_execution_kb DECIMAL(10,2),
    
    -- KPI Affidabilità
    error_rate DECIMAL(5,2),
    mtbf_hours DECIMAL(10,2),                 -- Mean Time Between Failures
    mttr_minutes DECIMAL(10,2),               -- Mean Time To Recovery
    
    -- Scores aggregati
    avg_complexity_score DECIMAL(5,2),
    avg_reliability_score DECIMAL(5,2),
    avg_efficiency_score DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    UNIQUE KEY unique_kpi_snapshot (workflow_id, period_type, snapshot_date),
    INDEX idx_kpi_date (snapshot_date),
    INDEX idx_kpi_period (period_type)
);

-- Tabella hourly_stats: statistiche orarie per pattern analysis
CREATE TABLE IF NOT EXISTS hourly_stats (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255),                 -- NULL per stats globali
    stat_date DATE NOT NULL,
    stat_hour INTEGER NOT NULL CHECK (stat_hour >= 0 AND stat_hour <= 23),
    
    -- Contatori
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    
    -- Performance
    avg_duration_ms INTEGER,
    min_duration_ms INTEGER,
    max_duration_ms INTEGER,
    
    -- Carico
    concurrent_executions_max INTEGER,        -- Max esecuzioni concorrenti
    queue_size_max INTEGER,                   -- Max dimensione coda
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    UNIQUE KEY unique_hourly_stat (workflow_id, stat_date, stat_hour),
    INDEX idx_hourly_date (stat_date),
    INDEX idx_hourly_workflow (workflow_id)
);

-- Tabella error_logs: log dettagliato degli errori
CREATE TABLE IF NOT EXISTS error_logs (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    execution_id VARCHAR(255),
    node_id VARCHAR(255),
    
    -- Errore
    error_type VARCHAR(100),                  -- Tipo/categoria errore
    error_code VARCHAR(50),
    error_message TEXT NOT NULL,
    error_stack TEXT,
    
    -- Contesto
    context JSON,                             -- Contesto aggiuntivo
    
    -- Classificazione
    severity VARCHAR(20),                     -- low, medium, high, critical
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    
    occurred_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (execution_id) REFERENCES executions(id) ON DELETE CASCADE,
    INDEX idx_errors_workflow (workflow_id),
    INDEX idx_errors_type (error_type),
    INDEX idx_errors_occurred (occurred_at)
);

-- Tabella workflow_audit_log: traccia tutte le modifiche ai workflow
CREATE TABLE IF NOT EXISTS workflow_audit_log (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    
    -- Azione
    action VARCHAR(50) NOT NULL,              -- created, updated, deleted, activated, deactivated
    user_id VARCHAR(255),                     -- Chi ha fatto la modifica
    user_email VARCHAR(255),
    
    -- Cambiamenti
    changes JSON,                             -- Diff dei cambiamenti
    old_values JSON,                          -- Valori precedenti
    new_values JSON,                          -- Nuovi valori
    
    -- Versioning
    version_before VARCHAR(50),
    version_after VARCHAR(50),
    
    -- Metadati
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    performed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    INDEX idx_audit_workflow (workflow_id),
    INDEX idx_audit_action (action),
    INDEX idx_audit_performed (performed_at)
);

-- Tabella performance_benchmarks: benchmark di performance
CREATE TABLE IF NOT EXISTS performance_benchmarks (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    benchmark_date DATE NOT NULL,
    
    -- Percentili durata (in millisecondi)
    p1_duration_ms INTEGER,                   -- 1° percentile (fastest)
    p5_duration_ms INTEGER,
    p10_duration_ms INTEGER,
    p25_duration_ms INTEGER,                  -- Primo quartile
    p50_duration_ms INTEGER,                  -- Mediana
    p75_duration_ms INTEGER,                  -- Terzo quartile
    p90_duration_ms INTEGER,
    p95_duration_ms INTEGER,
    p99_duration_ms INTEGER,
    p99_9_duration_ms INTEGER,                -- 99.9° percentile (slowest)
    
    -- Statistiche
    mean_duration_ms INTEGER,
    std_deviation_ms INTEGER,
    sample_size INTEGER,                      -- Numero di esecuzioni nel campione
    
    -- Throughput
    executions_per_hour DECIMAL(10,2),
    executions_per_day DECIMAL(10,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    UNIQUE KEY unique_benchmark (workflow_id, benchmark_date),
    INDEX idx_benchmark_date (benchmark_date)
);

-- ----------------------------------------------------------------------------
-- TABELLE TAGS E CATEGORIZZAZIONE
-- ----------------------------------------------------------------------------

-- Tabella tags: gestione tags per categorizzazione
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7),                         -- Colore HEX
    icon VARCHAR(50),                         -- Nome icona
    
    -- Statistiche uso
    usage_count INTEGER DEFAULT 0,            -- Quante volte è usato
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_tags_name (name)
);

-- Tabella workflow_tags: relazione many-to-many workflow-tags
CREATE TABLE IF NOT EXISTS workflow_tags (
    workflow_id VARCHAR(255) NOT NULL,
    tag_id INTEGER NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (workflow_id, tag_id),
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- VISTE ANALITICHE
-- ----------------------------------------------------------------------------

-- Vista workflow_health: dashboard salute workflow
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
    w.success_count,
    w.failure_count,
    CASE 
        WHEN w.execution_count > 0 THEN 
            ROUND((w.success_count::DECIMAL / w.execution_count) * 100, 2)
        ELSE 0 
    END as success_rate,
    w.avg_duration_ms,
    w.last_execution_at,
    CASE
        WHEN w.health_score >= 80 THEN 'Ottima'
        WHEN w.health_score >= 60 THEN 'Buona'
        WHEN w.health_score >= 40 THEN 'Attenzione'
        ELSE 'Critica'
    END as health_status,
    CASE
        WHEN w.last_execution_at IS NULL THEN 'Mai eseguito'
        WHEN w.last_execution_at > NOW() - INTERVAL '1 day' THEN 'Attivo'
        WHEN w.last_execution_at > NOW() - INTERVAL '7 days' THEN 'Recente'
        WHEN w.last_execution_at > NOW() - INTERVAL '30 days' THEN 'Inattivo'
        ELSE 'Dormiente'
    END as activity_status
FROM workflows w;

-- Vista execution_trends: trend giornalieri delle esecuzioni
CREATE OR REPLACE VIEW execution_trends AS
SELECT 
    DATE(e.started_at) as execution_date,
    e.workflow_id,
    w.name as workflow_name,
    COUNT(*) as total_executions,
    SUM(CASE WHEN e.status = 'success' THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN e.status = 'error' THEN 1 ELSE 0 END) as failed,
    ROUND(AVG(e.duration_ms)) as avg_duration_ms,
    MIN(e.duration_ms) as min_duration_ms,
    MAX(e.duration_ms) as max_duration_ms,
    ROUND(AVG(e.data_in_kb)) as avg_data_in_kb,
    ROUND(AVG(e.data_out_kb)) as avg_data_out_kb
FROM executions e
JOIN workflows w ON e.workflow_id = w.id
WHERE e.started_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(e.started_at), e.workflow_id, w.name
ORDER BY execution_date DESC, total_executions DESC;

-- Vista problematic_workflows: workflow che necessitano attenzione
CREATE OR REPLACE VIEW problematic_workflows AS
SELECT 
    w.id,
    w.name,
    w.reliability_score,
    w.failure_count,
    w.execution_count,
    CASE 
        WHEN w.execution_count > 0 THEN 
            ROUND((w.failure_count::DECIMAL / w.execution_count) * 100, 2)
        ELSE 0 
    END as failure_rate,
    (
        SELECT COUNT(*) 
        FROM error_logs el 
        WHERE el.workflow_id = w.id 
        AND el.occurred_at > NOW() - INTERVAL '7 days'
    ) as recent_errors,
    w.last_failure_at,
    ARRAY(
        SELECT DISTINCT el.error_type 
        FROM error_logs el 
        WHERE el.workflow_id = w.id 
        AND el.occurred_at > NOW() - INTERVAL '7 days'
        LIMIT 5
    ) as recent_error_types
FROM workflows w
WHERE w.reliability_score < 70
   OR w.failure_count > 5
   OR (w.execution_count > 0 AND w.success_count = 0)
ORDER BY w.reliability_score ASC, w.failure_count DESC;

-- Vista node_usage_stats: statistiche uso e performance nodi
CREATE OR REPLACE VIEW node_usage_stats AS
SELECT 
    wn.node_type,
    COUNT(DISTINCT wn.workflow_id) as workflows_using,
    COUNT(*) as total_instances,
    SUM(wn.execution_count) as total_executions,
    AVG(wn.error_rate) as avg_error_rate,
    AVG(wn.avg_execution_time_ms) as avg_execution_time,
    ARRAY_AGG(DISTINCT wn.workflow_id ORDER BY wn.execution_count DESC LIMIT 5) as top_workflows
FROM workflow_nodes wn
GROUP BY wn.node_type
ORDER BY total_executions DESC;

-- ----------------------------------------------------------------------------
-- INDICI AGGIUNTIVI PER PERFORMANCE
-- ----------------------------------------------------------------------------

-- Indici per query frequenti
CREATE INDEX IF NOT EXISTS idx_workflows_health ON workflows(health_score DESC);
CREATE INDEX IF NOT EXISTS idx_executions_workflow_status ON executions(workflow_id, status);
CREATE INDEX IF NOT EXISTS idx_executions_date_range ON executions(started_at, finished_at);
CREATE INDEX IF NOT EXISTS idx_errors_unresolved ON error_logs(workflow_id, is_resolved) WHERE is_resolved = false;
CREATE INDEX IF NOT EXISTS idx_kpi_recent ON kpi_snapshots(snapshot_date DESC, period_type);

-- ----------------------------------------------------------------------------
-- TRIGGER PER AGGIORNAMENTI AUTOMATICI
-- ----------------------------------------------------------------------------

-- Funzione per aggiornare updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Applica trigger a tabelle con updated_at
CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_nodes_updated_at BEFORE UPDATE ON workflow_nodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tags_updated_at BEFORE UPDATE ON tags
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- DATI INIZIALI
-- ----------------------------------------------------------------------------

-- Inserisci tags di default
INSERT INTO tags (name, description, color) VALUES 
    ('production', 'Workflow in produzione', '#00C853'),
    ('development', 'Workflow in sviluppo', '#FF6F00'),
    ('testing', 'Workflow in fase di test', '#2962FF'),
    ('deprecated', 'Workflow deprecato', '#B71C1C'),
    ('critical', 'Workflow critico per il business', '#D50000'),
    ('maintenance', 'Workflow di manutenzione', '#6A1B9A')
ON CONFLICT (name) DO NOTHING;

-- ----------------------------------------------------------------------------
-- STORED PROCEDURES PER CALCOLI COMPLESSI
-- ----------------------------------------------------------------------------

-- Procedura per calcolare health score di un workflow
CREATE OR REPLACE FUNCTION calculate_workflow_health_score(workflow_id_param VARCHAR(255))
RETURNS INTEGER AS $$
DECLARE
    health_score INTEGER;
    reliability_weight DECIMAL := 0.5;
    efficiency_weight DECIMAL := 0.3;
    complexity_weight DECIMAL := 0.2;
BEGIN
    SELECT 
        ROUND(
            (reliability_score * reliability_weight) +
            (efficiency_score * efficiency_weight) +
            ((100 - complexity_score) * complexity_weight)
        )
    INTO health_score
    FROM workflows
    WHERE id = workflow_id_param;
    
    RETURN COALESCE(health_score, 0);
END;
$$ LANGUAGE plpgsql;

-- Procedura per aggregare KPI per un periodo
CREATE OR REPLACE FUNCTION aggregate_kpi_for_period(
    workflow_id_param VARCHAR(255),
    period_type_param VARCHAR(20)
)
RETURNS VOID AS $$
DECLARE
    period_interval INTERVAL;
BEGIN
    -- Determina intervallo basato sul tipo di periodo
    CASE period_type_param
        WHEN '24h' THEN period_interval := INTERVAL '1 day';
        WHEN '7d' THEN period_interval := INTERVAL '7 days';
        WHEN '30d' THEN period_interval := INTERVAL '30 days';
        WHEN '90d' THEN period_interval := INTERVAL '90 days';
        ELSE period_interval := INTERVAL '1 day';
    END CASE;
    
    -- Inserisci o aggiorna KPI snapshot
    INSERT INTO kpi_snapshots (
        workflow_id,
        period_type,
        snapshot_date,
        total_executions,
        successful_executions,
        failed_executions,
        success_rate,
        avg_duration_ms,
        error_rate
    )
    SELECT 
        workflow_id_param,
        period_type_param,
        CURRENT_DATE,
        COUNT(*),
        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END),
        SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END),
        ROUND(100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*), 2),
        ROUND(AVG(duration_ms)),
        ROUND(100.0 * SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) / COUNT(*), 2)
    FROM executions
    WHERE workflow_id = workflow_id_param
      AND started_at >= NOW() - period_interval
    ON CONFLICT (workflow_id, period_type, snapshot_date)
    DO UPDATE SET
        total_executions = EXCLUDED.total_executions,
        successful_executions = EXCLUDED.successful_executions,
        failed_executions = EXCLUDED.failed_executions,
        success_rate = EXCLUDED.success_rate,
        avg_duration_ms = EXCLUDED.avg_duration_ms,
        error_rate = EXCLUDED.error_rate,
        created_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- GRANT PERMISSIONS (se necessario)
-- ----------------------------------------------------------------------------

-- Esempio per PostgreSQL (adatta secondo le tue necessità)
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;

-- ============================================================================
-- Fine Schema Database n8n Analytics
-- ============================================================================