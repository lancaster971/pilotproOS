-- ===============================================
-- Migration 007: Security Audit Premium Tables
-- ===============================================
-- Aggiunge tabelle per funzionalità Security Premium
-- - Security audits storici
-- - Security metrics tracking  
-- - Compliance reports
-- - Security incidents log

-- Tabella per security audits storici
CREATE TABLE IF NOT EXISTS security_audits (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(255) NOT NULL,
  security_score INTEGER NOT NULL CHECK (security_score >= 0 AND security_score <= 100),
  risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
  total_issues INTEGER DEFAULT 0,
  critical_issues INTEGER DEFAULT 0,
  high_issues INTEGER DEFAULT 0,
  medium_issues INTEGER DEFAULT 0,
  low_issues INTEGER DEFAULT 0,
  audit_data JSONB NOT NULL, -- Full audit report
  n8n_audit_raw JSONB, -- Raw n8n audit response
  categories_analyzed TEXT[], -- Array di categorie analizzate
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indici separati per security_audits
CREATE INDEX IF NOT EXISTS idx_security_audits_tenant_date ON security_audits (tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_audits_score ON security_audits (security_score);
CREATE INDEX IF NOT EXISTS idx_security_audits_risk ON security_audits (risk_level);

-- Tabella per security metrics time-series
CREATE TABLE IF NOT EXISTS security_metrics (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(255) NOT NULL,
  metric_type VARCHAR(100) NOT NULL, -- 'credentials_count', 'workflows_active', 'users_admin', etc.
  metric_value DECIMAL(15,4) NOT NULL,
  metric_metadata JSONB, -- Additional context data
  recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indici separati per security_metrics
CREATE INDEX IF NOT EXISTS idx_security_metrics_tenant_type_time ON security_metrics (tenant_id, metric_type, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_metrics_time ON security_metrics (recorded_at DESC);

-- Tabella per compliance reports
CREATE TABLE IF NOT EXISTS compliance_reports (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(255) NOT NULL,
  compliance_standard VARCHAR(50) NOT NULL, -- 'GDPR', 'SOC2', 'ISO27001', etc.
  compliant BOOLEAN NOT NULL,
  compliance_score INTEGER CHECK (compliance_score >= 0 AND compliance_score <= 100),
  issues JSONB NOT NULL, -- Array di issues specifici
  recommendations JSONB, -- Array di raccomandazioni
  evidence JSONB, -- Supporting evidence/data
  report_data JSONB NOT NULL, -- Full compliance report
  audit_id INTEGER REFERENCES security_audits(id) ON DELETE SET NULL,
  generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  valid_until TIMESTAMP, -- Quando scade questo report
  
  -- Constraint unico per evitare duplicati per stesso audit
  UNIQUE(tenant_id, compliance_standard, audit_id)
);

-- Indici separati per compliance_reports
CREATE INDEX IF NOT EXISTS idx_compliance_reports_tenant_standard ON compliance_reports (tenant_id, compliance_standard);
CREATE INDEX IF NOT EXISTS idx_compliance_reports_date ON compliance_reports (generated_at DESC);

-- Tabella per security incidents tracking
CREATE TABLE IF NOT EXISTS security_incidents (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(255) NOT NULL,
  incident_type VARCHAR(100) NOT NULL, -- 'credential_breach', 'unauthorized_access', etc.
  severity VARCHAR(20) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
  title VARCHAR(500) NOT NULL,
  description TEXT,
  affected_resources JSONB, -- Workflows, users, credentials affected
  detection_method VARCHAR(100), -- 'audit', 'monitoring', 'manual', etc.
  status VARCHAR(50) DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED')),
  assigned_to VARCHAR(255), -- User ID or email
  resolution_notes TEXT,
  detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  resolved_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indici separati per security_incidents
CREATE INDEX IF NOT EXISTS idx_security_incidents_tenant_status ON security_incidents (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_security_incidents_severity ON security_incidents (severity, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_incidents_date ON security_incidents (detected_at DESC);

-- Tabella per security recommendations tracking
CREATE TABLE IF NOT EXISTS security_recommendations (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(255) NOT NULL,
  audit_id INTEGER REFERENCES security_audits(id) ON DELETE CASCADE,
  category VARCHAR(100) NOT NULL,
  priority VARCHAR(20) NOT NULL CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
  title VARCHAR(500) NOT NULL,
  description TEXT NOT NULL,
  recommendation_data JSONB, -- Detailed recommendation info
  effort_level VARCHAR(20) CHECK (effort_level IN ('LOW', 'MEDIUM', 'HIGH')),
  impact_level VARCHAR(20) CHECK (impact_level IN ('LOW', 'MEDIUM', 'HIGH')),
  status VARCHAR(50) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'DISMISSED')),
  implemented_at TIMESTAMP,
  dismissed_reason TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indici separati per security_recommendations
CREATE INDEX IF NOT EXISTS idx_security_recommendations_tenant_priority ON security_recommendations (tenant_id, priority, status);
CREATE INDEX IF NOT EXISTS idx_security_recommendations_audit ON security_recommendations (audit_id);
CREATE INDEX IF NOT EXISTS idx_security_recommendations_status ON security_recommendations (status, created_at DESC);

-- Tabella per security configuration
CREATE TABLE IF NOT EXISTS security_config (
  id SERIAL PRIMARY KEY,
  tenant_id VARCHAR(255) NOT NULL,
  config_key VARCHAR(200) NOT NULL,
  config_value JSONB NOT NULL,
  description TEXT,
  is_active BOOLEAN DEFAULT true,
  created_by VARCHAR(255),
  updated_by VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(tenant_id, config_key)
);

-- Indici separati per security_config
CREATE INDEX IF NOT EXISTS idx_security_config_tenant_key ON security_config (tenant_id, config_key);

-- View per quick security overview
CREATE OR REPLACE VIEW security_overview AS
SELECT 
  sa.tenant_id,
  sa.security_score as current_score,
  sa.risk_level as current_risk,
  sa.total_issues,
  sa.critical_issues,
  sa.created_at as last_audit,
  
  -- Score trend (confronto con audit precedente)
  LAG(sa.security_score) OVER (
    PARTITION BY sa.tenant_id 
    ORDER BY sa.created_at
  ) as previous_score,
  
  -- Incident count (ultimi 30 giorni)
  (SELECT COUNT(*) 
   FROM security_incidents si 
   WHERE si.tenant_id = sa.tenant_id 
     AND si.detected_at >= NOW() - INTERVAL '30 days'
     AND si.status != 'CLOSED'
  ) as open_incidents,
  
  -- Pending recommendations
  (SELECT COUNT(*) 
   FROM security_recommendations sr 
   WHERE sr.tenant_id = sa.tenant_id 
     AND sr.status = 'PENDING'
  ) as pending_recommendations

FROM security_audits sa
WHERE sa.id IN (
  -- Solo l'audit più recente per ogni tenant
  SELECT DISTINCT ON (tenant_id) id 
  FROM security_audits 
  ORDER BY tenant_id, created_at DESC
);

-- Inserimento configurazioni default per security
INSERT INTO security_config (tenant_id, config_key, config_value, description) VALUES
('default', 'audit_frequency_days', '7', 'How often to run security audits (in days)'),
('default', 'alert_on_critical_issues', 'true', 'Send alerts when critical security issues are found'),
('default', 'auto_generate_compliance_reports', 'true', 'Automatically generate compliance reports after audits'),
('default', 'retention_days_audits', '90', 'How long to keep security audit data (in days)'),
('default', 'min_security_score_alert', '60', 'Security score threshold below which to send alerts')
ON CONFLICT (tenant_id, config_key) DO NOTHING;

-- Trigger per auto-update di updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Applica trigger a tutte le tabelle con updated_at
CREATE TRIGGER update_security_audits_updated_at 
  BEFORE UPDATE ON security_audits 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_security_incidents_updated_at 
  BEFORE UPDATE ON security_incidents 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_security_recommendations_updated_at 
  BEFORE UPDATE ON security_recommendations 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_security_config_updated_at 
  BEFORE UPDATE ON security_config 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Commenti sulle tabelle per documentazione
COMMENT ON TABLE security_audits IS 'Storico completo dei security audits per ogni tenant';
COMMENT ON TABLE security_metrics IS 'Time-series data per metriche di sicurezza';
COMMENT ON TABLE compliance_reports IS 'Reports di compliance generati dagli audit';
COMMENT ON TABLE security_incidents IS 'Tracking degli incidenti di sicurezza';
COMMENT ON TABLE security_recommendations IS 'Raccomandazioni di sicurezza e loro stato';
COMMENT ON TABLE security_config IS 'Configurazioni di sicurezza per tenant';
COMMENT ON VIEW security_overview IS 'Vista rapida dello stato di sicurezza per tenant';

-- Migration completata - Security Audit Premium Tables v007