-- Aggiorna schema database per supportare execution data ricchi
-- Migrazione 008: Execution data arricchiti per AI Agent Transparency

-- Aggiungi colonne per execution data dettagliati
ALTER TABLE tenant_executions 
ADD COLUMN IF NOT EXISTS has_detailed_data BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS detailed_steps JSONB,
ADD COLUMN IF NOT EXISTS business_context JSONB,
ADD COLUMN IF NOT EXISTS total_nodes INTEGER,
ADD COLUMN IF NOT EXISTS successful_nodes INTEGER,
ADD COLUMN IF NOT EXISTS failed_nodes INTEGER;

-- Indici per performance su query AI agents
CREATE INDEX IF NOT EXISTS idx_tenant_executions_detailed_data 
ON tenant_executions(tenant_id, has_detailed_data) 
WHERE has_detailed_data = true;

CREATE INDEX IF NOT EXISTS idx_tenant_executions_workflow_started 
ON tenant_executions(workflow_id, started_at DESC);

-- Indice JSONB per business context queries
CREATE INDEX IF NOT EXISTS idx_tenant_executions_business_context_gin 
ON tenant_executions USING gin(business_context);

-- Commenti per documentazione
COMMENT ON COLUMN tenant_executions.has_detailed_data IS 'Indica se execution ha dati step-by-step importati da n8n API';
COMMENT ON COLUMN tenant_executions.detailed_steps IS 'Array di step eseguiti con input/output per ogni nodo';
COMMENT ON COLUMN tenant_executions.business_context IS 'Business context estratto: emails, ordini, classificazioni, etc.';
COMMENT ON COLUMN tenant_executions.total_nodes IS 'Numero totale nodi eseguiti';
COMMENT ON COLUMN tenant_executions.successful_nodes IS 'Numero nodi completati con successo';
COMMENT ON COLUMN tenant_executions.failed_nodes IS 'Numero nodi falliti';