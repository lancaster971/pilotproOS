-- Migration: Aggiungi tabelle per sync state e history
-- Timestamp: 2024-01-10

-- Tabella per stato sincronizzazione
CREATE TABLE IF NOT EXISTS sync_state (
    id VARCHAR(50) PRIMARY KEY,              -- ID stato (es. 'main')
    
    -- Timestamp ultimi sync
    last_workflow_sync TIMESTAMP,            -- Ultimo sync workflow
    last_execution_sync TIMESTAMP,           -- Ultimo sync esecuzioni
    last_full_sync TIMESTAMP,                -- Ultimo full sync
    last_kpi_calculation TIMESTAMP,          -- Ultimo calcolo KPI
    
    -- Checkpoint per recovery
    last_processed_workflow_id VARCHAR(255), -- Ultimo workflow processato
    last_processed_execution_id VARCHAR(255),-- Ultima esecuzione processata
    
    -- Contatori
    total_syncs INTEGER DEFAULT 0,           -- Totale sync eseguiti
    successful_syncs INTEGER DEFAULT 0,      -- Sync completati con successo
    failed_syncs INTEGER DEFAULT 0,          -- Sync falliti
    
    -- Stato corrente
    current_sync JSONB,                      -- Info sync in corso
    pending_retries JSONB DEFAULT '[]'::jsonb, -- Retry pendenti
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabella per storico sincronizzazioni
CREATE TABLE IF NOT EXISTS sync_history (
    id SERIAL PRIMARY KEY,
    
    -- Info sync
    sync_type VARCHAR(50) NOT NULL,          -- Tipo sync (incremental, full, etc)
    status VARCHAR(50) NOT NULL,             -- Status finale
    started_at TIMESTAMP NOT NULL,           -- Inizio sync
    finished_at TIMESTAMP,                   -- Fine sync
    duration_ms INTEGER,                     -- Durata in millisecondi
    
    -- Statistiche workflow
    workflows_processed INTEGER DEFAULT 0,   -- Workflow processati
    workflows_created INTEGER DEFAULT 0,     -- Nuovi workflow creati
    workflows_updated INTEGER DEFAULT 0,     -- Workflow aggiornati
    workflows_failed INTEGER DEFAULT 0,      -- Workflow con errori
    
    -- Statistiche esecuzioni
    executions_processed INTEGER DEFAULT 0,  -- Esecuzioni processate
    executions_created INTEGER DEFAULT 0,    -- Nuove esecuzioni create
    executions_updated INTEGER DEFAULT 0,    -- Esecuzioni aggiornate
    executions_failed INTEGER DEFAULT 0,     -- Esecuzioni con errori
    
    -- Metriche performance
    total_api_calls INTEGER DEFAULT 0,       -- Chiamate API totali
    total_db_operations INTEGER DEFAULT 0,   -- Operazioni DB totali
    
    -- Errori e metadata
    errors JSONB DEFAULT '[]'::jsonb,        -- Array errori
    metadata JSONB DEFAULT '{}'::jsonb,      -- Metadata aggiuntivi
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indici per performance
CREATE INDEX IF NOT EXISTS idx_sync_history_type ON sync_history(sync_type);
CREATE INDEX IF NOT EXISTS idx_sync_history_status ON sync_history(status);
CREATE INDEX IF NOT EXISTS idx_sync_history_started ON sync_history(started_at DESC);

-- Inizializza stato principale se non esiste
INSERT INTO sync_state (id, created_at, updated_at) 
VALUES ('main', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (id) DO NOTHING;

-- Vista per ultime sincronizzazioni
CREATE OR REPLACE VIEW recent_syncs AS
SELECT 
    sync_type,
    status,
    started_at,
    finished_at,
    duration_ms,
    workflows_processed + executions_processed as total_records,
    workflows_failed + executions_failed as total_failures,
    CASE 
        WHEN workflows_processed + executions_processed > 0 THEN
            ROUND(100.0 * (workflows_processed + executions_processed - workflows_failed - executions_failed) / 
                  (workflows_processed + executions_processed), 2)
        ELSE 100
    END as success_rate
FROM sync_history
WHERE started_at > NOW() - INTERVAL '7 days'
ORDER BY started_at DESC;

-- Funzione per cleanup vecchi sync history
CREATE OR REPLACE FUNCTION cleanup_old_sync_history()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sync_history
    WHERE created_at < NOW() - INTERVAL '30 days'
    AND status = 'completed';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;