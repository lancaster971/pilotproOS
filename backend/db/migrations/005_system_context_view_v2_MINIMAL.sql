-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Migration 005 v2: System Context View (MINIMAL - n8n schema only)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
--
-- Purpose: Single-query aggregation for Dynamic Context System v3.5.0
-- Scope: Uses ONLY n8n.workflow_entity + n8n.execution_entity (confirmed tables)
-- Created: 2025-10-15
-- Author: Claude Code
--
-- Column Name Convention: n8n uses camelCase (createdAt, workflowId, startedAt)
--
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- Drop existing view if exists
DROP VIEW IF EXISTS pilotpros.v_system_context CASCADE;

-- Create MINIMAL system context view (n8n data only)
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
                'createdAt', "createdAt",
                'updatedAt', "updatedAt"
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
        COUNT(*) FILTER (WHERE "stoppedAt" IS NOT NULL) as esecuzioni_stoppate,

        -- Last 7 days stats
        COUNT(*) FILTER (WHERE "startedAt" >= NOW() - INTERVAL '7 days') as esecuzioni_7giorni,
        COUNT(*) FILTER (WHERE "startedAt" >= NOW() - INTERVAL '7 days' AND finished = true) as esecuzioni_7giorni_completate,

        -- Success rate (last 7 days, using status column)
        CASE
            WHEN COUNT(*) FILTER (WHERE "startedAt" >= NOW() - INTERVAL '7 days' AND finished = true) > 0
            THEN ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE "startedAt" >= NOW() - INTERVAL '7 days'
                    AND finished = true
                    AND status = 'success'
                ) / NULLIF(COUNT(*) FILTER (WHERE "startedAt" >= NOW() - INTERVAL '7 days' AND finished = true), 0),
                1
            )::float
            ELSE 0
        END as success_rate_7giorni,

        -- Average duration (last 7 days, completed only)
        COALESCE(
            ROUND(
                EXTRACT(EPOCH FROM AVG("stoppedAt" - "startedAt") FILTER (
                    WHERE "startedAt" >= NOW() - INTERVAL '7 days'
                    AND finished = true
                    AND "stoppedAt" IS NOT NULL
                ))::numeric,
                2
            )::float,
            0
        ) as durata_media_secondi_7giorni,

        -- Error count (last 7 days, using status column)
        COUNT(*) FILTER (
            WHERE "startedAt" >= NOW() - INTERVAL '7 days'
            AND finished = true
            AND status = 'error'
        ) as errori_7giorni,

        -- Today's errors
        COUNT(*) FILTER (
            WHERE "startedAt" >= CURRENT_DATE
            AND finished = true
            AND status = 'error'
        ) as errori_oggi

    FROM n8n.execution_entity
    WHERE "deletedAt" IS NULL  -- Exclude soft-deleted executions
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

    -- Error statistics (derived from execution_entity.status)
    COALESCE(es.errori_7giorni, 0) as errori_7giorni,
    COALESCE(es.errori_oggi, 0) as errori_oggi,

    -- Table count (for "quante tabelle?" query)
    COALESCE(ts.tabelle_pilotpros_count, 0) as tabelle_pilotpros_count,

    -- Placeholder fields (for future expansion when pilotpros tables exist)
    0 as email_totali,
    0 as email_7giorni,
    0 as email_oggi,
    0 as mittenti_unici,
    0 as mittenti_unici_7giorni,
    0 as workflows_con_errori,
    '[]'::json as top_5_workflows_errori,
    0 as node_executions_totali,
    0 as node_executions_7giorni,
    0 as node_types_unici,
    0 as durata_media_node_secondi_7giorni

FROM workflow_summary ws
CROSS JOIN execution_summary es
CROSS JOIN table_summary ts;

-- Grant SELECT permission to pilotpros_user
GRANT SELECT ON pilotpros.v_system_context TO pilotpros_user;

-- Add comment for documentation
COMMENT ON VIEW pilotpros.v_system_context IS
'Dynamic Context System v3.5.0 - MINIMAL version using n8n schema only.
Aggregates workflow names, execution stats, error counts (from execution_entity.status).
Used by get_system_context_tool() for real-time disambiguation.

MINIMAL SCOPE: Uses ONLY n8n.workflow_entity + n8n.execution_entity (confirmed tables).
Email/node execution fields set to 0 (placeholder for future pilotpros tables).

Column naming: Uses n8n camelCase convention (createdAt, startedAt, workflowId).';

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- VERIFICATION QUERY (test view output)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
--
-- SELECT * FROM pilotpros.v_system_context;
--
-- Expected output:
-- - workflows_attivi_count: 6-8 (ChatOne, Flow_2, Flow_4, etc.)
-- - esecuzioni_7giorni: 1000+ (typical weekly activity)
-- - success_rate_7giorni: 85-95% (healthy system)
-- - errori_7giorni: 10-50 (depends on traffic)
--
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
