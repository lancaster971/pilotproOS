-- Migration 005: System Context View for Dynamic Context System v3.5.0
-- Purpose: Single-query aggregation of all PilotProOS metadata for get_system_context_tool()
-- Created: 2025-10-14
-- Author: Claude Code (Dynamic Context System implementation)

-- Drop existing view if exists
DROP VIEW IF EXISTS pilotpros.v_system_context CASCADE;

-- Create comprehensive system context view
CREATE OR REPLACE VIEW pilotpros.v_system_context AS
WITH workflow_summary AS (
    -- Active workflows with details
    SELECT
        COUNT(*) FILTER (WHERE active = true) as workflows_attivi_count,
        COUNT(*) as workflows_totali_count,
        json_agg(
            json_build_object(
                'id', id,
                'name', name,
                'active', active,
                'created_at', created_at,
                'updated_at', updated_at
            ) ORDER BY name
        ) FILTER (WHERE active = true) as workflows_attivi_list,
        json_agg(
            json_build_object(
                'id', id,
                'name', name,
                'active', active
            ) ORDER BY name
        ) as workflows_tutti_list
    FROM n8n.workflow_entity
),
execution_summary AS (
    -- Execution statistics (all time + last 7 days)
    SELECT
        COUNT(*) as esecuzioni_totali,
        COUNT(*) FILTER (WHERE finished = true) as esecuzioni_completate,
        COUNT(*) FILTER (WHERE finished = false) as esecuzioni_in_corso,
        COUNT(*) FILTER (WHERE stopped_at IS NOT NULL) as esecuzioni_stoppate,

        -- Last 7 days stats
        COUNT(*) FILTER (WHERE started_at >= NOW() - INTERVAL '7 days') as esecuzioni_7giorni,
        COUNT(*) FILTER (WHERE started_at >= NOW() - INTERVAL '7 days' AND finished = true) as esecuzioni_7giorni_completate,

        -- Success rate (last 7 days for relevance)
        CASE
            WHEN COUNT(*) FILTER (WHERE started_at >= NOW() - INTERVAL '7 days' AND finished = true) > 0
            THEN ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE started_at >= NOW() - INTERVAL '7 days'
                    AND finished = true
                    AND stopped_at IS NULL
                ) / NULLIF(COUNT(*) FILTER (WHERE started_at >= NOW() - INTERVAL '7 days' AND finished = true), 0),
                1
            )
            ELSE 0
        END as success_rate_7giorni,

        -- Average duration (last 7 days, completed only)
        ROUND(
            EXTRACT(EPOCH FROM AVG(stopped_at - started_at))::numeric,
            2
        ) FILTER (
            WHERE started_at >= NOW() - INTERVAL '7 days'
            AND finished = true
            AND stopped_at IS NOT NULL
        ) as durata_media_secondi_7giorni

    FROM n8n.execution_entity
),
chatone_summary AS (
    -- Email activity from chatone_emails table (for "clienti" dictionary)
    SELECT
        COUNT(*) as email_totali,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as email_7giorni,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as email_oggi,
        COUNT(DISTINCT sender) as mittenti_unici,
        COUNT(DISTINCT sender) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as mittenti_unici_7giorni
    FROM pilotpros.chatone_emails
),
error_summary AS (
    -- Error breakdown (for "problemi" dictionary)
    SELECT
        COUNT(*) as errori_totali,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as errori_7giorni,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as errori_oggi,
        COUNT(DISTINCT workflow_id) as workflows_con_errori,

        -- Top error workflows (last 7 days)
        json_agg(
            json_build_object(
                'workflow_id', workflow_id,
                'workflow_name', workflow_name,
                'error_count', error_count
            ) ORDER BY error_count DESC
        ) FILTER (WHERE rn <= 5) as top_5_workflows_errori

    FROM (
        SELECT
            ee.workflow_id,
            we.name as workflow_name,
            ee.created_at,
            COUNT(*) OVER (PARTITION BY ee.workflow_id) as error_count,
            ROW_NUMBER() OVER (PARTITION BY ee.workflow_id ORDER BY ee.created_at DESC) as rn
        FROM pilotpros.execution_errors ee
        LEFT JOIN n8n.workflow_entity we ON ee.workflow_id = we.id::text
        WHERE ee.created_at >= NOW() - INTERVAL '7 days'
    ) errors_ranked
    WHERE rn = 1  -- Keep only one row per workflow for aggregation
),
node_execution_summary AS (
    -- Node execution statistics (for "passi" dictionary)
    SELECT
        COUNT(*) as node_executions_totali,
        COUNT(*) FILTER (WHERE started_at >= NOW() - INTERVAL '7 days') as node_executions_7giorni,
        COUNT(DISTINCT node_name) as node_types_unici,

        -- Average node duration (last 7 days)
        ROUND(
            EXTRACT(EPOCH FROM AVG(finished_at - started_at))::numeric,
            2
        ) FILTER (
            WHERE started_at >= NOW() - INTERVAL '7 days'
            AND finished_at IS NOT NULL
        ) as durata_media_node_secondi_7giorni

    FROM pilotpros.node_executions
),
table_summary AS (
    -- Database table count (for "quante tabelle?" query)
    SELECT
        COUNT(*) as tabelle_pilotpros_count
    FROM information_schema.tables
    WHERE table_schema = 'pilotpros'
      AND table_type = 'BASE TABLE'
)

-- Final aggregation
SELECT
    NOW() as generated_at,

    -- Workflow metadata
    COALESCE(ws.workflows_attivi_count, 0) as workflows_attivi_count,
    COALESCE(ws.workflows_totali_count, 0) as workflows_totali_count,
    COALESCE(ws.workflows_attivi_list, '[]'::json) as workflows_attivi_list,
    COALESCE(ws.workflows_tutti_list, '[]'::json) as workflows_tutti_list,

    -- Execution statistics
    COALESCE(es.esecuzioni_totali, 0) as esecuzioni_totali,
    COALESCE(es.esecuzioni_completate, 0) as esecuzioni_completate,
    COALESCE(es.esecuzioni_in_corso, 0) as esecuzioni_in_corso,
    COALESCE(es.esecuzioni_stoppate, 0) as esecuzioni_stoppate,
    COALESCE(es.esecuzioni_7giorni, 0) as esecuzioni_7giorni,
    COALESCE(es.esecuzioni_7giorni_completate, 0) as esecuzioni_7giorni_completate,
    COALESCE(es.success_rate_7giorni, 0) as success_rate_7giorni,
    COALESCE(es.durata_media_secondi_7giorni, 0) as durata_media_secondi_7giorni,

    -- Email/ChatOne statistics (for "clienti" mapping)
    COALESCE(cs.email_totali, 0) as email_totali,
    COALESCE(cs.email_7giorni, 0) as email_7giorni,
    COALESCE(cs.email_oggi, 0) as email_oggi,
    COALESCE(cs.mittenti_unici, 0) as mittenti_unici,
    COALESCE(cs.mittenti_unici_7giorni, 0) as mittenti_unici_7giorni,

    -- Error statistics (for "problemi" mapping)
    COALESCE(err.errori_totali, 0) as errori_totali,
    COALESCE(err.errori_7giorni, 0) as errori_7giorni,
    COALESCE(err.errori_oggi, 0) as errori_oggi,
    COALESCE(err.workflows_con_errori, 0) as workflows_con_errori,
    COALESCE(err.top_5_workflows_errori, '[]'::json) as top_5_workflows_errori,

    -- Node execution statistics (for "passi" mapping)
    COALESCE(ns.node_executions_totali, 0) as node_executions_totali,
    COALESCE(ns.node_executions_7giorni, 0) as node_executions_7giorni,
    COALESCE(ns.node_types_unici, 0) as node_types_unici,
    COALESCE(ns.durata_media_node_secondi_7giorni, 0) as durata_media_node_secondi_7giorni,

    -- Table count (for "quante tabelle?" query)
    COALESCE(ts.tabelle_pilotpros_count, 0) as tabelle_pilotpros_count

FROM workflow_summary ws
CROSS JOIN execution_summary es
CROSS JOIN chatone_summary cs
CROSS JOIN error_summary err
CROSS JOIN node_execution_summary ns
CROSS JOIN table_summary ts;

-- Grant SELECT permission to pilotpros_user
GRANT SELECT ON pilotpros.v_system_context TO pilotpros_user;

-- Add comment for documentation
COMMENT ON VIEW pilotpros.v_system_context IS
'Dynamic Context System v3.5.0 - Aggregates all PilotProOS metadata for AI agent context loading.
Provides workflow names, execution stats, error summaries, and business term mappings in single query.
Used by get_system_context_tool() for real-time disambiguation and business dictionary enrichment.';
