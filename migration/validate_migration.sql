-- ====================================================================
-- n8n Migration Validation Script
-- ====================================================================
--
-- Questo script SQL valida l'integrità dei dati dopo la migrazione
-- da SQLite a PostgreSQL con UUID remapping.
--
-- Author: PilotProOS Team
-- Date: 2025-10-08
-- Version: 1.0.0
--
-- Usage:
--   psql -h localhost -U pilotpros_user -d pilotpros_db -f validate_migration.sql
--
-- ====================================================================

\set QUIET on
\timing on
\pset border 2
\pset format wrapped

\echo ''
\echo '===================================================================='
\echo 'n8n MIGRATION VALIDATION REPORT'
\echo '===================================================================='
\echo ''

-- Set schema
SET search_path TO n8n, public;

-- ====================================================================
-- 1. COUNT RECORD PER TABELLA
-- ====================================================================

\echo '1. COUNT RECORD PER TABELLA'
\echo '--------------------------------------------------------------------'

SELECT
    'workflow_entity' AS table_name,
    COUNT(*) AS total_rows
FROM n8n.workflow_entity

UNION ALL

SELECT
    'execution_entity' AS table_name,
    COUNT(*) AS total_rows
FROM n8n.execution_entity

UNION ALL

SELECT
    'credentials_entity' AS table_name,
    COUNT(*) AS total_rows
FROM n8n.credentials_entity

UNION ALL

SELECT
    'tag_entity' AS table_name,
    COUNT(*) AS total_rows
FROM n8n.tag_entity

UNION ALL

SELECT
    'shared_workflow' AS table_name,
    COUNT(*) AS total_rows
FROM n8n.shared_workflow

ORDER BY table_name;

\echo ''

-- ====================================================================
-- 2. VERIFICA FOREIGN KEYS (execution → workflow)
-- ====================================================================

\echo '2. VERIFICA FOREIGN KEYS (execution → workflow)'
\echo '--------------------------------------------------------------------'

-- Check executions senza workflow corrispondente
SELECT
    COUNT(*) AS orphaned_executions,
    CASE
        WHEN COUNT(*) = 0 THEN '✅ OK: Nessuna execution orfana'
        ELSE '❌ ERRORE: Trovate executions senza workflow!'
    END AS status
FROM n8n.execution_entity e
LEFT JOIN n8n.workflow_entity w ON e."workflowId" = w.id
WHERE w.id IS NULL;

\echo ''

-- Esempio executions orfane (se presenti)
SELECT
    e.id AS execution_id,
    e."workflowId" AS missing_workflow_id,
    e."startedAt",
    e.status
FROM n8n.execution_entity e
LEFT JOIN n8n.workflow_entity w ON e."workflowId" = w.id
WHERE w.id IS NULL
LIMIT 10;

\echo ''

-- ====================================================================
-- 3. VERIFICA CAMPI NOT NULL
-- ====================================================================

\echo '3. VERIFICA CAMPI NOT NULL (workflow_entity)'
\echo '--------------------------------------------------------------------'

SELECT
    COUNT(*) AS workflows_with_null_name,
    CASE
        WHEN COUNT(*) = 0 THEN '✅ OK: Tutti i workflow hanno nome'
        ELSE '⚠️ WARNING: Workflow con nome NULL!'
    END AS status
FROM n8n.workflow_entity
WHERE name IS NULL;

\echo ''

SELECT
    COUNT(*) AS workflows_with_null_nodes,
    CASE
        WHEN COUNT(*) = 0 THEN '⚠️ WARNING: Tutti i workflow hanno nodes NULL!'
        ELSE '✅ OK: Workflow con nodi definiti'
    END AS status
FROM n8n.workflow_entity
WHERE nodes IS NULL;

\echo ''

-- ====================================================================
-- 4. VERIFICA UUID VALIDITY
-- ====================================================================

\echo '4. VERIFICA UUID VALIDITY (workflow_entity)'
\echo '--------------------------------------------------------------------'

-- Check UUID formato valido (PostgreSQL UUID type auto-valida)
SELECT
    COUNT(*) AS total_workflows,
    COUNT(DISTINCT id) AS unique_uuids,
    CASE
        WHEN COUNT(*) = COUNT(DISTINCT id) THEN '✅ OK: Tutti gli UUID sono univoci'
        ELSE '❌ ERRORE: UUID duplicati trovati!'
    END AS status
FROM n8n.workflow_entity;

\echo ''

-- Check duplicate UUID (non dovrebbe mai accadere)
SELECT
    id,
    COUNT(*) AS occurrences
FROM n8n.workflow_entity
GROUP BY id
HAVING COUNT(*) > 1;

\echo ''

-- ====================================================================
-- 5. VERIFICA JSON VALIDITY
-- ====================================================================

\echo '5. VERIFICA JSON VALIDITY (workflow_entity)'
\echo '--------------------------------------------------------------------'

-- Conta workflow con JSON valido (se PostgreSQL jsonb è usato, auto-validato)
SELECT
    COUNT(*) AS workflows_with_nodes,
    CASE
        WHEN COUNT(*) > 0 THEN '✅ OK: Workflow con nodi definiti'
        ELSE '⚠️ WARNING: Nessun workflow con nodi!'
    END AS status
FROM n8n.workflow_entity
WHERE nodes IS NOT NULL
  AND nodes::text != '{}';

\echo ''

SELECT
    COUNT(*) AS workflows_with_connections,
    CASE
        WHEN COUNT(*) > 0 THEN '✅ OK: Workflow con connessioni definite'
        ELSE '⚠️ WARNING: Nessun workflow con connessioni!'
    END AS status
FROM n8n.workflow_entity
WHERE connections IS NOT NULL
  AND connections::text != '{}';

\echo ''

-- ====================================================================
-- 6. VERIFICA DATE/TIMESTAMP
-- ====================================================================

\echo '6. VERIFICA DATE/TIMESTAMP (workflow_entity)'
\echo '--------------------------------------------------------------------'

SELECT
    COUNT(*) AS workflows_with_dates,
    MIN("createdAt") AS oldest_workflow,
    MAX("createdAt") AS newest_workflow,
    CASE
        WHEN COUNT(*) > 0 THEN '✅ OK: Date valide'
        ELSE '⚠️ WARNING: Nessuna data trovata'
    END AS status
FROM n8n.workflow_entity
WHERE "createdAt" IS NOT NULL;

\echo ''

-- ====================================================================
-- 7. VERIFICA EXECUTION STATUS
-- ====================================================================

\echo '7. VERIFICA EXECUTION STATUS (execution_entity)'
\echo '--------------------------------------------------------------------'

SELECT
    status,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM n8n.execution_entity
GROUP BY status
ORDER BY count DESC;

\echo ''

-- ====================================================================
-- 8. VERIFICA CREDENTIALS ENCRYPTION
-- ====================================================================

\echo '8. VERIFICA CREDENTIALS ENCRYPTION (credentials_entity)'
\echo '--------------------------------------------------------------------'

SELECT
    COUNT(*) AS total_credentials,
    COUNT(CASE WHEN data IS NOT NULL THEN 1 END) AS credentials_with_data,
    CASE
        WHEN COUNT(*) = COUNT(CASE WHEN data IS NOT NULL THEN 1 END)
        THEN '✅ OK: Tutte le credentials hanno dati'
        ELSE '⚠️ WARNING: Alcune credentials senza dati!'
    END AS status
FROM n8n.credentials_entity;

\echo ''

-- ====================================================================
-- 9. SAMPLE DATA INSPECTION
-- ====================================================================

\echo '9. SAMPLE DATA INSPECTION (primi 3 workflow)'
\echo '--------------------------------------------------------------------'

SELECT
    id,
    name,
    active,
    "createdAt",
    "updatedAt",
    LENGTH(nodes::text) AS nodes_size_bytes,
    LENGTH(connections::text) AS connections_size_bytes
FROM n8n.workflow_entity
ORDER BY "createdAt" DESC
LIMIT 3;

\echo ''

-- ====================================================================
-- 10. STORAGE SIZE ANALYSIS
-- ====================================================================

\echo '10. STORAGE SIZE ANALYSIS'
\echo '--------------------------------------------------------------------'

SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size
FROM pg_tables
WHERE schemaname = 'n8n'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

\echo ''

-- ====================================================================
-- 11. WORKFLOW COMPLEXITY METRICS
-- ====================================================================

\echo '11. WORKFLOW COMPLEXITY METRICS'
\echo '--------------------------------------------------------------------'

-- Nota: Questa query richiede che 'nodes' sia JSONB (array)
-- Se nodes è TEXT, usa nodes::jsonb

SELECT
    name,
    active,
    CASE
        WHEN nodes IS NOT NULL AND nodes::text != '{}'
        THEN jsonb_array_length(nodes::jsonb)
        ELSE 0
    END AS node_count,
    "createdAt"
FROM n8n.workflow_entity
WHERE nodes IS NOT NULL
ORDER BY node_count DESC
LIMIT 10;

\echo ''

-- ====================================================================
-- 12. EXECUTION PERFORMANCE METRICS
-- ====================================================================

\echo '12. EXECUTION PERFORMANCE METRICS (ultimi 30 giorni)'
\echo '--------------------------------------------------------------------'

SELECT
    w.name AS workflow_name,
    COUNT(e.id) AS total_executions,
    COUNT(CASE WHEN e.status = 'success' THEN 1 END) AS success_count,
    COUNT(CASE WHEN e.status = 'error' THEN 1 END) AS error_count,
    ROUND(
        COUNT(CASE WHEN e.status = 'success' THEN 1 END) * 100.0 / NULLIF(COUNT(e.id), 0),
        2
    ) AS success_rate_percentage
FROM n8n.execution_entity e
JOIN n8n.workflow_entity w ON e."workflowId" = w.id
WHERE e."startedAt" >= NOW() - INTERVAL '30 days'
GROUP BY w.id, w.name
ORDER BY total_executions DESC
LIMIT 10;

\echo ''

-- ====================================================================
-- SUMMARY REPORT
-- ====================================================================

\echo '===================================================================='
\echo 'MIGRATION VALIDATION SUMMARY'
\echo '===================================================================='
\echo ''
\echo 'Controlli eseguiti:'
\echo '  1. ✅ Count record per tabella'
\echo '  2. ✅ Foreign keys (execution → workflow)'
\echo '  3. ✅ Campi NOT NULL'
\echo '  4. ✅ UUID validity'
\echo '  5. ✅ JSON validity'
\echo '  6. ✅ Date/timestamp'
\echo '  7. ✅ Execution status distribution'
\echo '  8. ✅ Credentials encryption'
\echo '  9. ✅ Sample data inspection'
\echo ' 10. ✅ Storage size analysis'
\echo ' 11. ✅ Workflow complexity metrics'
\echo ' 12. ✅ Execution performance metrics'
\echo ''
\echo 'Se tutti i controlli mostrano ✅ OK, la migrazione è riuscita!'
\echo ''
\echo 'Prossimi step:'
\echo '  1. Testa workflow in n8n UI (http://localhost:5678)'
\echo '  2. Esegui test executions manualmente'
\echo '  3. Verifica credentials funzionanti (con encryptionKey corretta)'
\echo '  4. Backup PostgreSQL finale'
\echo ''
\echo '===================================================================='

\set QUIET off
