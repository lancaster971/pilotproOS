-- Migrazione 003: Aggiunge campi mancanti dalle API n8n
-- Data: 2025-08-12
-- Descrizione: Aggiunge campi importanti scoperti dall'analisi API

-- 1. Aggiungi campo meta (metadata workflow)
ALTER TABLE workflows 
ADD COLUMN IF NOT EXISTS meta JSONB;

COMMENT ON COLUMN workflows.meta IS 'Metadata del workflow (es. templateCredsSetupCompleted)';

-- 2. Aggiungi campo trigger_count
ALTER TABLE workflows 
ADD COLUMN IF NOT EXISTS trigger_count INTEGER DEFAULT 0;

COMMENT ON COLUMN workflows.trigger_count IS 'Numero di trigger nel workflow';

-- 3. Aggiungi campo shared (informazioni condivisione/ownership)
ALTER TABLE workflows 
ADD COLUMN IF NOT EXISTS shared JSONB;

COMMENT ON COLUMN workflows.shared IS 'Info su ownership e condivisione del workflow';

-- 4. Aggiungi campo project_id per organizzazione
ALTER TABLE workflows 
ADD COLUMN IF NOT EXISTS project_id VARCHAR(100);

COMMENT ON COLUMN workflows.project_id IS 'ID del progetto a cui appartiene il workflow';

-- 5. Aggiungi campo owner_email estratto da shared
ALTER TABLE workflows 
ADD COLUMN IF NOT EXISTS owner_email VARCHAR(255);

COMMENT ON COLUMN workflows.owner_email IS 'Email del proprietario del workflow';

-- 6. Aggiungi campo workflow_type basato sui nodi
ALTER TABLE workflows 
ADD COLUMN IF NOT EXISTS workflow_type VARCHAR(50);

COMMENT ON COLUMN workflows.workflow_type IS 'Tipo di workflow (webhook, schedule, manual, etc.)';

-- 7. Aggiungi campo has_error_handler
ALTER TABLE workflows 
ADD COLUMN IF NOT EXISTS has_error_handler BOOLEAN DEFAULT false;

COMMENT ON COLUMN workflows.has_error_handler IS 'Se il workflow ha gestione errori';

-- 8. Crea tabella per i tags dei workflow (many-to-many)
CREATE TABLE IF NOT EXISTS workflow_tags (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    tag_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    UNIQUE(workflow_id, tag_name)
);

CREATE INDEX IF NOT EXISTS idx_workflow_tags_workflow ON workflow_tags(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_tags_tag ON workflow_tags(tag_name);

-- 9. Crea tabella per memorizzare info sui progetti
CREATE TABLE IF NOT EXISTS projects (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50), -- personal, team, organization
    owner_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Aggiungi foreign key per project_id
ALTER TABLE workflows 
ADD CONSTRAINT fk_workflow_project 
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL;

-- 11. Aggiungi campo per tracking delle modifiche
ALTER TABLE workflows 
ADD COLUMN IF NOT EXISTS modified_by VARCHAR(255);

COMMENT ON COLUMN workflows.modified_by IS 'Ultimo utente che ha modificato il workflow';

-- 12. Aggiungi campo per template source
ALTER TABLE workflows 
ADD COLUMN IF NOT EXISTS template_id VARCHAR(100);

COMMENT ON COLUMN workflows.template_id IS 'ID del template da cui è stato creato';

-- 13. Aggiungi indici per performance
CREATE INDEX IF NOT EXISTS idx_workflows_archived ON workflows(is_archived);
CREATE INDEX IF NOT EXISTS idx_workflows_project ON workflows(project_id);
CREATE INDEX IF NOT EXISTS idx_workflows_owner ON workflows(owner_email);
CREATE INDEX IF NOT EXISTS idx_workflows_type ON workflows(workflow_type);

-- 14. Crea vista per workflow attivi non archiviati (quelli visibili nell'UI)
CREATE OR REPLACE VIEW visible_workflows AS
SELECT * FROM workflows 
WHERE is_archived = false
ORDER BY active DESC, updated_at DESC;

-- 15. Crea vista per statistiche per progetto
CREATE OR REPLACE VIEW project_stats AS
SELECT 
    p.id as project_id,
    p.name as project_name,
    COUNT(w.id) as total_workflows,
    COUNT(CASE WHEN w.active = true THEN 1 END) as active_workflows,
    COUNT(CASE WHEN w.is_archived = true THEN 1 END) as archived_workflows,
    AVG(w.health_score) as avg_health_score,
    SUM(w.execution_count) as total_executions
FROM projects p
LEFT JOIN workflows w ON p.id = w.project_id
GROUP BY p.id, p.name;

-- 16. Funzione per estrarre owner_email da shared JSON
CREATE OR REPLACE FUNCTION extract_owner_email_from_shared()
RETURNS TRIGGER AS $$
BEGIN
    -- Estrai email dal campo shared se presente
    IF NEW.shared IS NOT NULL AND jsonb_array_length(NEW.shared) > 0 THEN
        NEW.owner_email := NEW.shared->0->'project'->'projectRelations'->0->'user'->>'email';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 17. Trigger per auto-popolare owner_email
DROP TRIGGER IF EXISTS trigger_extract_owner_email ON workflows;
CREATE TRIGGER trigger_extract_owner_email
    BEFORE INSERT OR UPDATE OF shared ON workflows
    FOR EACH ROW
    EXECUTE FUNCTION extract_owner_email_from_shared();

-- 18. Funzione per determinare workflow_type dai nodi
CREATE OR REPLACE FUNCTION determine_workflow_type()
RETURNS TRIGGER AS $$
DECLARE
    node_record RECORD;
    has_webhook BOOLEAN := false;
    has_schedule BOOLEAN := false;
    has_form BOOLEAN := false;
BEGIN
    -- Controlla i tipi di nodi nel workflow
    FOR node_record IN 
        SELECT node_type FROM workflow_nodes WHERE workflow_id = NEW.id
    LOOP
        IF node_record.node_type ILIKE '%webhook%' THEN
            has_webhook := true;
        ELSIF node_record.node_type ILIKE '%schedule%' OR node_record.node_type ILIKE '%cron%' THEN
            has_schedule := true;
        ELSIF node_record.node_type ILIKE '%form%' THEN
            has_form := true;
        END IF;
    END LOOP;
    
    -- Determina il tipo
    IF has_webhook THEN
        NEW.workflow_type := 'webhook';
    ELSIF has_schedule THEN
        NEW.workflow_type := 'scheduled';
    ELSIF has_form THEN
        NEW.workflow_type := 'form';
    ELSIF NEW.trigger_count > 0 THEN
        NEW.workflow_type := 'triggered';
    ELSE
        NEW.workflow_type := 'manual';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 19. Trigger per auto-determinare workflow_type
DROP TRIGGER IF EXISTS trigger_determine_workflow_type ON workflows;
CREATE TRIGGER trigger_determine_workflow_type
    BEFORE INSERT OR UPDATE ON workflows
    FOR EACH ROW
    EXECUTE FUNCTION determine_workflow_type();

-- 20. Aggiungi colonna per contare nodi di specifici tipi
ALTER TABLE workflows
ADD COLUMN IF NOT EXISTS ai_node_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS database_node_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS http_node_count INTEGER DEFAULT 0;

COMMENT ON COLUMN workflows.ai_node_count IS 'Numero di nodi AI/LLM nel workflow';
COMMENT ON COLUMN workflows.database_node_count IS 'Numero di nodi database nel workflow';
COMMENT ON COLUMN workflows.http_node_count IS 'Numero di nodi HTTP request nel workflow';

-- Fine migrazione 003