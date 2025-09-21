-- Business-only views that hide n8n complexity
-- These views are what gets exported, not the raw n8n data

CREATE SCHEMA IF NOT EXISTS pilotpros_export;

-- Business Process View (hides n8n workflow internals)
CREATE OR REPLACE VIEW pilotpros_export.business_processes AS
SELECT
    MD5(w.id::text || 'salt2025') as process_id,  -- Obfuscated ID
    w.name as process_name,
    CASE
        WHEN w.active THEN 'Active'
        ELSE 'Inactive'
    END as status,
    jsonb_build_object(
        'created', w."createdAt",
        'modified', w."updatedAt",
        'version', w.staticdata->>'version'
    ) as metadata,
    -- Strip technical details, keep only business logic
    jsonb_build_object(
        'steps', jsonb_array_length(w.nodes),
        'connections', jsonb_array_length(w.connections),
        'description', w.settings->>'description'
    ) as process_info
FROM n8n.workflow_entity w
WHERE w.active = true;

-- Process Runs View (hides execution details)
CREATE OR REPLACE VIEW pilotpros_export.process_runs AS
SELECT
    MD5(e.id::text || 'salt2025') as run_id,
    MD5(e."workflowId"::text || 'salt2025') as process_id,
    CASE
        WHEN e.finished THEN 'Completed'
        WHEN e."stoppedAt" IS NOT NULL THEN 'Stopped'
        ELSE 'Running'
    END as status,
    e."startedAt" as started,
    e."stoppedAt" as completed,
    -- Hide technical error details
    CASE
        WHEN e.data->>'lastNodeExecuted' IS NOT NULL
        THEN 'Process step error'
        ELSE NULL
    END as error_summary
FROM n8n.execution_entity e
WHERE e."deletedAt" IS NULL;

-- Business Metrics View (aggregated, no raw data)
CREATE OR REPLACE VIEW pilotpros_export.business_metrics AS
SELECT
    DATE_TRUNC('day', e."startedAt") as date,
    COUNT(*) as total_runs,
    COUNT(CASE WHEN e.finished THEN 1 END) as successful_runs,
    COUNT(CASE WHEN NOT e.finished THEN 1 END) as failed_runs,
    AVG(EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt"))) as avg_duration_seconds
FROM n8n.execution_entity e
WHERE e."deletedAt" IS NULL
GROUP BY DATE_TRUNC('day', e."startedAt");

-- Integration Points View (hides webhook URLs and credentials)
CREATE OR REPLACE VIEW pilotpros_export.integration_points AS
SELECT
    MD5(w.id::text || wh.node || 'salt2025') as integration_id,
    w.name as process_name,
    'External System' as integration_type,
    CASE
        WHEN wh.httpmethod = 'POST' THEN 'Data Receiver'
        WHEN wh.httpmethod = 'GET' THEN 'Data Provider'
        ELSE 'Bidirectional'
    END as integration_role
FROM n8n.webhook_entity wh
JOIN n8n.workflow_entity w ON w.id::text = wh."workflowId"::text
WHERE w.active = true;

-- Export function that only exports business views
CREATE OR REPLACE FUNCTION pilotpros_export.export_business_data()
RETURNS TABLE (
    export_date timestamp,
    data_type text,
    data jsonb
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        NOW() as export_date,
        'business_processes' as data_type,
        jsonb_agg(row_to_json(bp.*)) as data
    FROM pilotpros_export.business_processes bp
    UNION ALL
    SELECT
        NOW() as export_date,
        'process_runs' as data_type,
        jsonb_agg(row_to_json(pr.*)) as data
    FROM pilotpros_export.process_runs pr
    UNION ALL
    SELECT
        NOW() as export_date,
        'business_metrics' as data_type,
        jsonb_agg(row_to_json(bm.*)) as data
    FROM pilotpros_export.business_metrics bm;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant limited access
GRANT USAGE ON SCHEMA pilotpros_export TO pilotpros_user;
GRANT SELECT ON ALL TABLES IN SCHEMA pilotpros_export TO pilotpros_user;
-- Explicitly deny access to n8n schema
REVOKE ALL ON SCHEMA n8n FROM pilotpros_user;