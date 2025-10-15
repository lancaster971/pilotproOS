"""
Business Tools for Milhena - n8n Database Queries
Complete set of business-critical queries for workflow automation insights
"""

import os
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from langsmith import traceable
import json
import logging

logger = logging.getLogger(__name__)

# Database connection helper
def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres-dev"),
        port=5432,
        dbname="pilotpros_db",
        user="pilotpros_user",
        password="pilotpros_secure_pass_2025"
    )

# ============================================================================
# WORKFLOW MANAGEMENT TOOLS
# ============================================================================

@tool
@traceable(name="MilhenaWorkflows", run_type="tool")
def get_workflows_tool(query_type: str = "active") -> str:
    """
    Get BASIC workflow list (names only, NO statistics/metrics).

    🔑 KEYWORDS: processi, workflow, flussi, business process, lista

    USE THIS ONLY for simple lists like:
    - "quali workflow esistono?"
    - "mostra i workflow attivi"
    - "lista processi"

    DO NOT use for statistics/metrics - use get_full_database_dump instead!

    Args:
        query_type: "active", "inactive", "all", "top_used", "complex", "recent", "errors"

    Returns:
        Workflow names list (NO execution stats, NO performance data)
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if query_type == "active":
            cur.execute("""
                SELECT name, "triggerCount", "createdAt"
                FROM n8n.workflow_entity
                WHERE active = true
                ORDER BY name
            """)
            results = cur.fetchall()
            workflows = [f"- {r[0]} (Trigger: {r[1]}, Creato: {r[2].strftime('%d/%m/%Y')})" for r in results]
            response = f"**Processi Attivi: {len(results)}**\n" + "\n".join(workflows) if workflows else "Nessun processo attivo"

        elif query_type == "inactive":
            cur.execute("""
                SELECT name, "updatedAt"
                FROM n8n.workflow_entity
                WHERE active = false
                ORDER BY "updatedAt" DESC
                LIMIT 10
            """)
            results = cur.fetchall()
            workflows = [f"- {r[0]} (Ultimo aggiornamento: {r[1].strftime('%d/%m/%Y')})" for r in results]
            response = f"**Processi Inattivi:**\n" + "\n".join(workflows) if workflows else "Tutti i processi sono attivi"

        elif query_type == "top_used":
            cur.execute("""
                SELECT we.name, COUNT(ee.id) as exec_count,
                       MAX(ee."startedAt") as last_run
                FROM n8n.workflow_entity we
                LEFT JOIN n8n.execution_entity ee ON we.id = ee."workflowId"
                GROUP BY we.id, we.name
                HAVING COUNT(ee.id) > 0
                ORDER BY exec_count DESC
                LIMIT 5
            """)
            results = cur.fetchall()
            workflows = []
            for r in results:
                last_run = r[2].strftime('%d/%m %H:%M') if r[2] else "Mai"
                workflows.append(f"- {r[0]}: {r[1]} esecuzioni (Ultima: {last_run})")
            response = "**Top 5 Processi più utilizzati:**\n" + "\n".join(workflows)

        elif query_type == "complex":
            cur.execute("""
                SELECT name, JSON_ARRAY_LENGTH(nodes) as node_count
                FROM n8n.workflow_entity
                ORDER BY JSON_ARRAY_LENGTH(nodes) DESC
                LIMIT 5
            """)
            results = cur.fetchall()
            workflows = [f"- {r[0]}: {r[1]} passaggi" for r in results]
            response = "**Processi più complessi:**\n" + "\n".join(workflows)

        elif query_type == "recent":
            cur.execute("""
                SELECT name, "updatedAt", active
                FROM n8n.workflow_entity
                ORDER BY "updatedAt" DESC
                LIMIT 5
            """)
            results = cur.fetchall()
            workflows = []
            for r in results:
                status = "Attivo" if r[2] else "Inattivo"
                workflows.append(f"- {r[0]} ({status}) - Aggiornato: {r[1].strftime('%d/%m %H:%M')}")
            response = "**Processi modificati di recente:**\n" + "\n".join(workflows)

        elif query_type == "errors":
            cur.execute("""
                SELECT we.name, COUNT(ee.id) as error_count,
                       MAX(ee."startedAt") as last_error
                FROM n8n.workflow_entity we
                JOIN n8n.execution_entity ee ON we.id = ee."workflowId"
                WHERE ee.status = 'error'
                GROUP BY we.id, we.name
                ORDER BY error_count DESC
                LIMIT 5
            """)
            results = cur.fetchall()
            if results:
                workflows = []
                for r in results:
                    last_error = r[2].strftime('%d/%m %H:%M') if r[2] else "N/A"
                    workflows.append(f"- {r[0]}: {r[1]} errori (Ultimo: {last_error})")
                response = "**Processi con più errori:**\n" + "\n".join(workflows)
            else:
                response = "Nessun processo con errori recenti"

        else:  # all
            cur.execute("""
                SELECT COUNT(*),
                       COUNT(CASE WHEN active = true THEN 1 END) as active,
                       COUNT(CASE WHEN active = false THEN 1 END) as inactive
                FROM n8n.workflow_entity
            """)
            result = cur.fetchone()
            response = f"""**Riepilogo Processi:**
- Totali: {result[0]}
- Attivi: {result[1]}
- Inattivi: {result[2]}
- Tasso attivazione: {(result[1]/result[0]*100 if result[0] > 0 else 0):.1f}%"""

        conn.close()
        return response

    except Exception as e:
        return f"Errore accesso processi: {str(e)}"

# ============================================================================
# PERFORMANCE METRICS TOOLS
# ============================================================================

@tool
@traceable(name="MilhenaPerformance", run_type="tool")
def get_performance_metrics_tool(query_type: str = "overview") -> str:
    """
    Get performance metrics from workflow executions.

    Args:
        query_type: "overview", "speed", "success_rate", "trends", "bottlenecks"

    Returns:
        Performance metrics in business language
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if query_type == "overview":
            # Overall performance metrics
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) as errors,
                    AVG(CASE WHEN "stoppedAt" IS NOT NULL
                        THEN EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt")) END) as avg_duration
                FROM n8n.execution_entity
                WHERE "startedAt" >= CURRENT_DATE - INTERVAL '7 days'
            """)
            result = cur.fetchone()
            success_rate = (result[1]/result[0]*100) if result[0] > 0 else 0
            avg_duration = result[3] if result[3] else 0

            response = f"""**Performance ultimi 7 giorni:**
- Esecuzioni totali: {result[0]}
- Successi: {result[1]}
- Errori: {result[2]}
- Tasso successo: {success_rate:.1f}%
- Durata media: {avg_duration:.1f} secondi"""

        elif query_type == "speed":
            # Fastest and slowest workflows
            cur.execute("""
                SELECT
                    we.name,
                    AVG(EXTRACT(EPOCH FROM (ee."stoppedAt" - ee."startedAt"))) as avg_duration,
                    COUNT(*) as exec_count
                FROM n8n.workflow_entity we
                JOIN n8n.execution_entity ee ON we.id = ee."workflowId"
                WHERE ee."stoppedAt" IS NOT NULL AND ee.status = 'success'
                GROUP BY we.id, we.name
                HAVING COUNT(*) >= 3
                ORDER BY avg_duration DESC
            """)
            results = cur.fetchall()

            if results:
                slowest = results[:3]
                fastest = results[-3:] if len(results) > 3 else []

                response = "**Analisi Velocità Processi:**\n"
                response += "\n🐌 Più lenti:\n"
                for r in slowest:
                    response += f"- {r[0]}: {r[1]:.1f}s (media su {r[2]} esecuzioni)\n"

                if fastest:
                    response += "\n⚡ Più veloci:\n"
                    for r in reversed(fastest):
                        response += f"- {r[0]}: {r[1]:.1f}s (media su {r[2]} esecuzioni)\n"
            else:
                response = "Dati insufficienti per analisi velocità"

        elif query_type == "success_rate":
            # Success rate by workflow
            cur.execute("""
                SELECT
                    we.name,
                    COUNT(*) as total,
                    COUNT(CASE WHEN ee.status = 'success' THEN 1 END) as success,
                    ROUND(COUNT(CASE WHEN ee.status = 'success' THEN 1 END) * 100.0 / COUNT(*), 1) as success_rate
                FROM n8n.workflow_entity we
                JOIN n8n.execution_entity ee ON we.id = ee."workflowId"
                GROUP BY we.id, we.name
                HAVING COUNT(*) >= 5
                ORDER BY success_rate ASC
                LIMIT 10
            """)
            results = cur.fetchall()

            response = "**Tasso di successo per processo:**\n"
            for r in results:
                emoji = "[OK]" if r[3] >= 90 else "[!]" if r[3] >= 70 else "[!!]"
                response += f"{emoji} {r[0]}: {r[3]}% ({r[2]}/{r[1]} successi)\n"

        elif query_type == "trends":
            # Performance trends
            cur.execute("""
                SELECT
                    DATE("startedAt") as day,
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as success
                FROM n8n.execution_entity
                WHERE "startedAt" >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE("startedAt")
                ORDER BY day DESC
            """)
            results = cur.fetchall()

            response = "**Trend settimanale:**\n"
            for r in results:
                success_rate = (r[2]/r[1]*100) if r[1] > 0 else 0
                trend = "📈" if success_rate >= 90 else "📊" if success_rate >= 70 else "📉"
                response += f"{trend} {r[0].strftime('%d/%m')}: {r[1]} esecuzioni, {success_rate:.0f}% successo\n"

        elif query_type == "bottlenecks":
            # Identify bottlenecks
            cur.execute("""
                SELECT
                    we.name,
                    COUNT(CASE WHEN ee.status = 'error' THEN 1 END) as errors,
                    COUNT(CASE WHEN EXTRACT(EPOCH FROM (ee."stoppedAt" - ee."startedAt")) > 10 THEN 1 END) as slow_runs,
                    AVG(EXTRACT(EPOCH FROM (ee."stoppedAt" - ee."startedAt"))) as avg_duration
                FROM n8n.workflow_entity we
                JOIN n8n.execution_entity ee ON we.id = ee."workflowId"
                WHERE ee."startedAt" >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY we.id, we.name
                HAVING COUNT(CASE WHEN ee.status = 'error' THEN 1 END) > 0
                    OR COUNT(CASE WHEN EXTRACT(EPOCH FROM (ee."stoppedAt" - ee."startedAt")) > 10 THEN 1 END) > 0
                ORDER BY errors DESC, slow_runs DESC
                LIMIT 5
            """)
            results = cur.fetchall()

            if results:
                response = "**[AVVISO] Processi che richiedono attenzione:**\n"
                for r in results:
                    issues = []
                    if r[1] > 0:
                        issues.append(f"{r[1]} errori")
                    if r[2] > 0:
                        issues.append(f"{r[2]} esecuzioni lente (>10s)")
                    response += f"- {r[0]}: {', '.join(issues)} (media: {r[3]:.1f}s)\n"
            else:
                response = "[OK] Nessun collo di bottiglia identificato"

        conn.close()
        return response

    except Exception as e:
        return f"Errore analisi performance: {str(e)}"

# ============================================================================
# SYSTEM MONITORING TOOLS
# ============================================================================

@tool
@traceable(name="MilhenaMonitoring", run_type="tool")
def get_system_monitoring_tool(query_type: str = "health") -> str:
    """
    Monitor system health and alerts.

    Args:
        query_type: "health", "alerts", "queue", "resources", "availability"

    Returns:
        System monitoring information
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if query_type == "health":
            # System health check
            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM n8n.execution_entity
                     WHERE "startedAt" >= CURRENT_TIMESTAMP - INTERVAL '1 hour') as recent_execs,
                    (SELECT COUNT(*) FROM n8n.execution_entity
                     WHERE status = 'error' AND "startedAt" >= CURRENT_TIMESTAMP - INTERVAL '1 hour') as recent_errors,
                    (SELECT COUNT(*) FROM n8n.execution_entity
                     WHERE finished = false) as running,
                    (SELECT COUNT(*) FROM n8n.workflow_entity WHERE active = true) as active_workflows
            """)
            result = cur.fetchone()

            error_rate = (result[1]/result[0]*100) if result[0] > 0 else 0
            health_status = "[OK] Ottimale" if error_rate < 5 else "[!] Attenzione" if error_rate < 20 else "[!!] Critico"

            response = f"""**Stato Sistema:**
{health_status}

**Ultima ora:**
- Esecuzioni: {result[0]}
- Errori: {result[1]} ({error_rate:.1f}%)
- In corso: {result[2]}
- Processi attivi: {result[3]}"""

        elif query_type == "alerts":
            # Critical alerts
            alerts = []

            # Check for stuck executions
            cur.execute("""
                SELECT COUNT(*), MIN("startedAt")
                FROM n8n.execution_entity
                WHERE finished = false
                AND "startedAt" < CURRENT_TIMESTAMP - INTERVAL '30 minutes'
            """)
            stuck = cur.fetchone()
            if stuck[0] > 0:
                alerts.append(f"[AVVISO] {stuck[0]} esecuzioni bloccate da oltre 30 minuti")

            # Check for high error rate
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) as errors
                FROM n8n.execution_entity
                WHERE "startedAt" >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
            """)
            recent = cur.fetchone()
            if recent[0] > 0 and (recent[1]/recent[0]) > 0.2:
                alerts.append(f"[!!] Alto tasso errori: {recent[1]}/{recent[0]} nell'ultima ora")

            # Check for workflows with consecutive failures
            cur.execute("""
                SELECT we.name, COUNT(*) as consecutive_errors
                FROM n8n.workflow_entity we
                JOIN n8n.execution_entity ee ON we.id = ee."workflowId"
                WHERE ee.status = 'error'
                AND ee."startedAt" >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
                AND NOT EXISTS (
                    SELECT 1 FROM n8n.execution_entity ee2
                    WHERE ee2."workflowId" = we.id
                    AND ee2.status = 'success'
                    AND ee2."startedAt" > ee."startedAt"
                )
                GROUP BY we.id, we.name
                HAVING COUNT(*) >= 3
            """)
            failing = cur.fetchall()
            for f in failing:
                alerts.append(f"[ERRORE] '{f[0]}' ha {f[1]} errori consecutivi")

            response = "**Alert Sistema:**\n" + "\n".join(alerts) if alerts else "[OK] Nessun alert attivo"

        elif query_type == "queue":
            # Execution queue status
            cur.execute("""
                SELECT
                    COUNT(CASE WHEN finished = false THEN 1 END) as running,
                    COUNT(CASE WHEN "waitTill" IS NOT NULL AND "waitTill" > CURRENT_TIMESTAMP THEN 1 END) as scheduled,
                    MIN("startedAt") as oldest_running
                FROM n8n.execution_entity
                WHERE finished = false OR ("waitTill" IS NOT NULL AND "waitTill" > CURRENT_TIMESTAMP)
            """)
            result = cur.fetchone()

            response = f"""**Stato Coda Esecuzioni:**
- In esecuzione: {result[0]}
- Programmate: {result[1]}"""

            if result[2]:
                running_since = (datetime.now(result[2].tzinfo) - result[2]).total_seconds() / 60
                response += f"\n- Esecuzione più vecchia: da {running_since:.0f} minuti"

        elif query_type == "resources":
            # Resource usage
            cur.execute("""
                SELECT
                    pg_database_size('pilotpros_db') / 1024 / 1024 as db_size_mb,
                    (SELECT COUNT(*) FROM n8n.execution_entity) as total_executions,
                    (SELECT COUNT(*) FROM n8n.workflow_entity) as total_workflows,
                    (SELECT SUM(pg_column_size(nodes)) / 1024 / 1024 FROM n8n.workflow_entity) as workflow_data_mb
            """)
            result = cur.fetchone()

            response = f"""**Utilizzo Risorse:**
- Database: {result[0]:.1f} MB
- Esecuzioni totali: {result[1]}
- Processi totali: {result[2]}
- Dati workflow: {result[3]:.1f} MB"""

        elif query_type == "availability":
            # System availability
            cur.execute("""
                WITH hourly_stats AS (
                    SELECT
                        date_trunc('hour', "startedAt") as hour,
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as success
                    FROM n8n.execution_entity
                    WHERE "startedAt" >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
                    GROUP BY date_trunc('hour', "startedAt")
                )
                SELECT
                    COUNT(*) as active_hours,
                    AVG(success::float / NULLIF(total, 0) * 100) as avg_success_rate
                FROM hourly_stats
                WHERE total > 0
            """)
            result = cur.fetchone()

            uptime = (result[0] / 24.0 * 100) if result[0] else 0
            success_rate = result[1] if result[1] else 0

            response = f"""**Disponibilità Sistema (24h):**
- Uptime: {uptime:.1f}%
- Ore attive: {result[0]}/24
- Tasso successo medio: {success_rate:.1f}%
- SLA: {'[OK] Rispettato' if uptime >= 99 else '[!] Sotto target' if uptime >= 95 else '[!!] Critico'}"""

        conn.close()
        return response

    except Exception as e:
        return f"Errore monitoraggio: {str(e)}"

# ============================================================================
# BUSINESS ANALYTICS TOOLS
# ============================================================================

@tool
@traceable(name="MilhenaFullData", run_type="tool")
def get_full_database_dump(days: int = 7) -> str:
    """
    **USE THIS FOR STATISTICS, METRICS, TRENDS, COMPLETE DATA**

    🔑 KEYWORDS: tutto, completo, full report, overview completa, dump totale

    USE THIS WHEN:
    - User chiede statistiche complete ("statistiche complete", "full report")
    - User chiede metriche approfondite ("metriche dettagliate", "analytics completo")
    - User chiede dati completi sistema ("tutto", "overview completa", "dump totale")
    - User chiede analisi dettagliata ("analisi approfondita", "report esteso")
    - User chiede trend temporali ("trend settimanale", "trend mensile")
    - User chiede performance globale ("performance tutti workflow")
    - ANY request needing execution stats, success rates, error counts COMPLETI
    - MASSIVA QUERY - Estrae TUTTI i dati PostgreSQL

    DO NOT USE WHEN:
    - User chiede statistiche singolo workflow (usa smart_workflow_query_tool)
    - User chiede metriche limitate (usa smart_analytics_query_tool)
    - User chiede lista semplice (usa get_workflows_tool)

    Args:
        days: Numero di giorni da analizzare (default: 7, usa 30 per "mese")

    Returns:
        Dump completo con 4 sezioni: esecuzioni, statistiche workflow, trend giornalieri, riepilogo globale
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # QUERY 1: TUTTE LE ESECUZIONI CON DETTAGLI COMPLETI
        cur.execute("""
            SELECT
                ee.id,
                we.name as workflow_name,
                ee."startedAt",
                ee."stoppedAt",
                ee.status,
                EXTRACT(EPOCH FROM (ee."stoppedAt" - ee."startedAt")) as duration_seconds,
                ee.mode,
                ee.finished,
                DATE(ee."startedAt") as execution_date,
                ed.data as error_data
            FROM n8n.execution_entity ee
            JOIN n8n.workflow_entity we ON ee."workflowId" = we.id
            LEFT JOIN n8n.execution_data ed ON ed."executionId" = ee.id
            WHERE ee."startedAt" >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY ee."startedAt" DESC
        """, (days,))

        all_executions = cur.fetchall()

        # QUERY 2: STATISTICHE AGGREGATE PER WORKFLOW
        cur.execute("""
            SELECT
                we.name,
                we.active,
                COUNT(ee.id) as total_executions,
                COUNT(CASE WHEN ee.status = 'success' THEN 1 END) as success_count,
                COUNT(CASE WHEN ee.status = 'error' THEN 1 END) as error_count,
                AVG(EXTRACT(EPOCH FROM (ee."stoppedAt" - ee."startedAt"))) as avg_duration,
                MIN(ee."startedAt") as first_execution,
                MAX(ee."startedAt") as last_execution
            FROM n8n.workflow_entity we
            LEFT JOIN n8n.execution_entity ee ON we.id = ee."workflowId"
                AND ee."startedAt" >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY we.id, we.name, we.active
            ORDER BY total_executions DESC
        """, (days,))

        workflow_stats = cur.fetchall()

        # QUERY 3: TREND GIORNALIERO
        cur.execute("""
            SELECT
                DATE(ee."startedAt") as day,
                COUNT(*) as total,
                COUNT(CASE WHEN ee.status = 'success' THEN 1 END) as success,
                COUNT(CASE WHEN ee.status = 'error' THEN 1 END) as errors,
                AVG(EXTRACT(EPOCH FROM (ee."stoppedAt" - ee."startedAt"))) as avg_duration
            FROM n8n.execution_entity ee
            WHERE ee."startedAt" >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(ee."startedAt")
            ORDER BY day DESC
        """, (days,))

        daily_trends = cur.fetchall()

        # QUERY 4: TOP ERRORI
        cur.execute("""
            SELECT
                we.name,
                COUNT(*) as error_count,
                MAX(ee."startedAt") as last_error
            FROM n8n.execution_entity ee
            JOIN n8n.workflow_entity we ON ee."workflowId" = we.id
            WHERE ee.status = 'error'
            AND ee."startedAt" >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY we.name
            ORDER BY error_count DESC
            LIMIT 20
        """, (days,))

        top_errors = cur.fetchall()

        cur.close()
        conn.close()

        # FORMATTA OUTPUT COMPLETO
        response = f"""=== DUMP COMPLETO DATABASE (ultimi {days} giorni) ===

[SEZIONE 1] TREND GIORNALIERO ({len(daily_trends)} giorni)
"""

        for day, total, success, errors, avg_dur in daily_trends:
            success_rate = (success/total*100) if total > 0 else 0
            response += f"\n{day.strftime('%d/%m/%Y')}: {total} esecuzioni, {success_rate:.0f}% successo ({success} OK, {errors} ERR), media {avg_dur:.1f}s"

        response += f"""\n\n[SEZIONE 2] STATISTICHE PER WORKFLOW ({len(workflow_stats)} workflow)
"""

        for name, active, total, success, errors, avg_dur, first, last in workflow_stats:
            if total and total > 0:
                success_rate = (success/total*100) if total else 0
                status = "[ATTIVO]" if active else "[PAUSA]"
                response += f"\n{status} {name}:"
                response += f"\n  - Esecuzioni: {total} (Success: {success}, Error: {errors}, Rate: {success_rate:.0f}%)"
                response += f"\n  - Durata media: {avg_dur:.1f}s"
                if last:
                    response += f"\n  - Ultima: {last.strftime('%d/%m %H:%M')}"

        response += f"""\n\n[SEZIONE 3] TOP 20 WORKFLOW CON ERRORI
"""

        for name, err_count, last_err in top_errors:
            response += f"\n{name}: {err_count} errori (ultimo: {last_err.strftime('%d/%m %H:%M')})"

        response += f"""\n\n[SEZIONE 4] LISTA COMPLETA ESECUZIONI ({len(all_executions)} totali)
"""

        # Mostra solo le ultime 50 per non saturare il contesto
        for i, (exec_id, wf_name, started, stopped, status, duration, mode, finished, exec_date, err_data) in enumerate(all_executions[:50], 1):
            status_icon = "[OK]" if status == "success" else "[ERR]"
            dur_str = f"{duration:.0f}s" if duration else "N/A"
            response += f"\n{i}. {status_icon} {wf_name} - {started.strftime('%d/%m %H:%M')} - {dur_str}"

        if len(all_executions) > 50:
            response += f"\n\n[NOTA] Mostrate prime 50 esecuzioni su {len(all_executions)} totali"

        response += f"""\n\n[RIEPILOGO GLOBALE]
- Periodo analizzato: {days} giorni
- Totale esecuzioni: {len(all_executions)}
- Workflow unici: {len(workflow_stats)}
- Giorni con attività: {len(daily_trends)}
"""

        return response

    except Exception as e:
        logger.error(f"Error in full database dump: {e}")
        return f"[ERRORE] Impossibile estrarre dati: {str(e)}"


@tool
@traceable(name="MilhenaAnalytics", run_type="tool")
def get_analytics_tool(query_type: str = "summary") -> str:
    """
    Get business analytics and execution statistics.

    Use this when user asks about:
    - "quante esecuzioni oggi?" → use query_type="summary"
    - "quante esecuzioni questa settimana?" → use query_type="summary"
    - "confronto con settimana scorsa" → use query_type="comparison"
    - ANY question about execution counts, totals, or statistics

    Args:
        query_type:
            - "summary" (DEFAULT): Esecuzioni oggi + settimana (use for "quante esecuzioni")
            - "comparison": Confronto settimana vs settimana scorsa
            - "roi": Return on investment analysis
            - "patterns": Pattern detection
            - "forecast": Trend forecasting

    Returns:
        Business analytics insights with execution counts and success rates
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if query_type == "summary":
            # Daily/Weekly summary
            cur.execute("""
                WITH today_stats AS (
                    SELECT
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
                        AVG(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt"))) as avg_duration
                    FROM n8n.execution_entity
                    WHERE DATE("startedAt") = CURRENT_DATE
                ),
                week_stats AS (
                    SELECT
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
                        AVG(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt"))) as avg_duration
                    FROM n8n.execution_entity
                    WHERE "startedAt" >= CURRENT_DATE - INTERVAL '7 days'
                )
                SELECT
                    t.total as today_total,
                    t.success as today_success,
                    t.avg_duration as today_duration,
                    w.total as week_total,
                    w.success as week_success,
                    w.avg_duration as week_duration
                FROM today_stats t, week_stats w
            """)
            result = cur.fetchone()

            today_rate = (result[1]/result[0]*100) if result[0] and result[0] > 0 else 0
            week_rate = (result[4]/result[3]*100) if result[3] and result[3] > 0 else 0

            response = f"""**Report Automazione:**

**Oggi:**
- Esecuzioni: {result[0] or 0}
- Successi: {result[1] or 0} ({today_rate:.1f}%)
- Tempo medio: {(result[2] or 0):.1f}s

**Settimana:**
- Esecuzioni: {result[3] or 0}
- Successi: {result[4] or 0} ({week_rate:.1f}%)
- Tempo medio: {(result[5] or 0):.1f}s"""

        elif query_type == "comparison":
            # Week over week comparison
            cur.execute("""
                WITH this_week AS (
                    SELECT
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
                        AVG(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt"))) as avg_duration
                    FROM n8n.execution_entity
                    WHERE "startedAt" >= CURRENT_DATE - INTERVAL '7 days'
                ),
                last_week AS (
                    SELECT
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
                        AVG(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt"))) as avg_duration
                    FROM n8n.execution_entity
                    WHERE "startedAt" >= CURRENT_DATE - INTERVAL '14 days'
                    AND "startedAt" < CURRENT_DATE - INTERVAL '7 days'
                )
                SELECT
                    tw.total as tw_total,
                    tw.success as tw_success,
                    lw.total as lw_total,
                    lw.success as lw_success,
                    tw.avg_duration as tw_duration,
                    lw.avg_duration as lw_duration
                FROM this_week tw, last_week lw
            """)
            result = cur.fetchone()

            volume_change = ((result[0] - result[2]) / result[2] * 100) if result[2] > 0 else 0
            success_change = ((result[1] - result[3]) / result[3] * 100) if result[3] > 0 else 0

            trend_volume = "📈" if volume_change > 0 else "📉" if volume_change < 0 else "➡️"
            trend_success = "📈" if success_change > 0 else "📉" if success_change < 0 else "➡️"

            response = f"""**Confronto Settimanale:**

**Volume esecuzioni:**
- Questa settimana: {result[0]}
- Settimana scorsa: {result[2]}
- Variazione: {trend_volume} {volume_change:+.1f}%

**Successi:**
- Questa settimana: {result[1]}
- Settimana scorsa: {result[3]}
- Variazione: {trend_success} {success_change:+.1f}%"""

        elif query_type == "roi":
            # ROI calculation
            cur.execute("""
                SELECT
                    COUNT(*) as total_executions,
                    SUM(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt"))) / 3600 as total_hours,
                    AVG(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt"))) as avg_seconds,
                    COUNT(DISTINCT "workflowId") as unique_workflows
                FROM n8n.execution_entity
                WHERE status = 'success'
                AND "startedAt" >= CURRENT_DATE - INTERVAL '30 days'
            """)
            result = cur.fetchone()

            # Assume each automated task saves 10 minutes of manual work
            manual_minutes_per_task = 10
            hours_saved = (result[0] * manual_minutes_per_task) / 60 if result[0] else 0
            automation_hours = result[1] if result[1] else 0
            roi_ratio = (hours_saved / automation_hours) if automation_hours > 0 else 0

            response = f"""**💰 ROI Automazione (30 giorni):**

**Metriche:**
- Processi automatizzati: {result[0]}
- Tempo macchina: {automation_hours:.1f} ore
- Tempo medio processo: {(result[2] or 0):.1f} secondi

**Risparmio stimato:**
- Ore lavoro risparmiate: {hours_saved:.0f} ore
- Efficienza: {roi_ratio:.1f}x
- Valore: {hours_saved * 30:.0f}€ (a 30€/ora)

**Impatto:**
- Processi unici: {result[3]}
- Produttività: +{(roi_ratio * 100):.0f}%"""

        elif query_type == "patterns":
            # Usage patterns
            cur.execute("""
                SELECT
                    EXTRACT(HOUR FROM "startedAt") as hour,
                    COUNT(*) as executions,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as success
                FROM n8n.execution_entity
                WHERE "startedAt" >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY EXTRACT(HOUR FROM "startedAt")
                ORDER BY executions DESC
                LIMIT 5
            """)
            peak_hours = cur.fetchall()

            cur.execute("""
                SELECT
                    EXTRACT(DOW FROM "startedAt") as day_of_week,
                    COUNT(*) as executions
                FROM n8n.execution_entity
                WHERE "startedAt" >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY EXTRACT(DOW FROM "startedAt")
                ORDER BY day_of_week
            """)
            weekly_pattern = cur.fetchall()

            days = ['Dom', 'Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab']

            response = "**📈 Pattern di Utilizzo:**\n\n"
            response += "**Ore di picco:**\n"
            for h in peak_hours[:3]:
                response += f"- {int(h[0])}:00: {h[1]} esecuzioni\n"

            response += "\n**Distribuzione settimanale:**\n"
            for d in weekly_pattern:
                day_name = days[int(d[0])]
                bar = "█" * min(20, int(d[1] / 10))
                response += f"{day_name}: {bar} {d[1]}\n"

        elif query_type == "forecast":
            # Simple forecast based on trends
            cur.execute("""
                WITH daily_counts AS (
                    SELECT
                        DATE("startedAt") as day,
                        COUNT(*) as executions
                    FROM n8n.execution_entity
                    WHERE "startedAt" >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE("startedAt")
                )
                SELECT
                    AVG(executions) as avg_daily,
                    STDDEV(executions) as stddev_daily,
                    MAX(executions) as max_daily,
                    MIN(executions) as min_daily
                FROM daily_counts
            """)
            result = cur.fetchone()

            avg_daily = result[0] if result[0] else 0
            projected_monthly = avg_daily * 30

            response = f"""**🔮 Previsioni (base ultimi 30 giorni):**

**Statistiche giornaliere:**
- Media: {avg_daily:.0f} esecuzioni/giorno
- Massimo: {result[2]:.0f}
- Minimo: {result[3]:.0f}
- Deviazione: ±{(result[1] or 0):.0f}

**Proiezioni mensili:**
- Esecuzioni previste: {projected_monthly:.0f}
- Range: {(projected_monthly - result[1]*30):.0f} - {(projected_monthly + result[1]*30):.0f}

**Trend:** {"📈 Crescita" if avg_daily > 50 else "📊 Stabile" if avg_daily > 20 else "📉 Basso utilizzo"}"""

        conn.close()
        return response

    except Exception as e:
        return f"Errore analytics: {str(e)}"


# ============================================================================
# NEW ENHANCED TOOLS - WORKFLOW DETAILS & ERRORS
# ============================================================================

@tool
@traceable(name="MilhenaWorkflowDetails", run_type="tool")
def get_workflow_details_tool(workflow_name: str) -> str:
    """
    Get COMPLETE detailed information about a specific workflow/process.

    **USE THIS when user asks about a specific workflow/process by name:**
    - "info su ChatOne"
    - "dettagli workflow X"
    - "com'è andato il processo Y"
    - "statistiche di Z"

    Returns COMPLETE data:
    - Basic info (stato, complessità, date)
    - Execution statistics (totali, successi, errori, percentuali)
    - Performance metrics (durata media/min/max)
    - Trend ultimi 7 giorni (esecuzioni giornaliere)
    - Ultime 10 esecuzioni dettagliate

    Args:
        workflow_name: Name of the workflow (can be partial, will use LIKE match)

    Returns:
        Complete workflow details with performance, trends, and execution history
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get workflow basic info
        cur.execute("""
            SELECT
                we.id,
                we.name,
                we.active,
                we."createdAt",
                we."updatedAt",
                we."triggerCount",
                JSON_ARRAY_LENGTH(we.nodes) as node_count
            FROM n8n.workflow_entity we
            WHERE LOWER(we.name) LIKE LOWER(%s)
            LIMIT 1
        """, (f"%{workflow_name}%",))

        workflow = cur.fetchone()

        if not workflow:
            return f"Processo '{workflow_name}' non trovato. Verifica il nome o contatta IT."

        wf_id, name, active, created, updated, trigger_count, node_count = workflow

        # Get execution stats
        cur.execute("""
            SELECT
                COUNT(*) as total_executions,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
                COUNT(CASE WHEN status = 'error' THEN 1 END) as failed,
                MAX("startedAt") as last_execution,
                MAX(CASE WHEN status = 'success' THEN "startedAt" END) as last_success,
                MAX(CASE WHEN status = 'error' THEN "startedAt" END) as last_error
            FROM n8n.execution_entity
            WHERE "workflowId" = %s
        """, (wf_id,))

        stats = cur.fetchone()
        total_exec, successful, failed, last_exec, last_success, last_error = stats

        # Build response
        status_emoji = "[ATTIVO]" if active else "[PAUSA]"
        status_text = "Attivo" if active else "Inattivo"

        response = f"""**{status_emoji} Processo: {name}**

**Stato:** {status_text}
**Complessità:** {node_count} passaggi
**Creato:** {created.strftime('%d/%m/%Y alle %H:%M')}
**Ultimo aggiornamento:** {updated.strftime('%d/%m/%Y alle %H:%M')}

**[STATISTICHE ESECUZIONI]**
- Totali: {total_exec or 0}
- Successo: {successful or 0} ({(successful/total_exec*100 if total_exec else 0):.1f}%)
- Errori: {failed or 0} ({(failed/total_exec*100 if total_exec else 0):.1f}%)
"""

        if last_exec:
            response += f"\n**[i] Ultima Esecuzione:** {last_exec.strftime('%d/%m/%Y alle %H:%M')}"

        if last_success:
            response += f"\n**[OK] Ultimo Successo:** {last_success.strftime('%d/%m/%Y alle %H:%M')}"

        if last_error:
            response += f"\n**[ERRORE] Ultimo Errore:** {last_error.strftime('%d/%m/%Y alle %H:%M')}"

        if not last_exec:
            response += "\n\n[AVVISO] Questo processo non è mai stato eseguito."

        # AGGIUNGI DETTAGLI AVANZATI

        # 1. DURATA MEDIA E TREND
        cur.execute("""
            SELECT
                AVG(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt"))) as avg_duration,
                MIN(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt"))) as min_duration,
                MAX(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt"))) as max_duration
            FROM n8n.execution_entity
            WHERE "workflowId" = %s
            AND "stoppedAt" IS NOT NULL
        """, (wf_id,))

        duration_stats = cur.fetchone()
        if duration_stats and duration_stats[0]:
            avg_dur, min_dur, max_dur = duration_stats
            response += f"\n\n**[PERFORMANCE]**"
            response += f"\n- Durata media: {avg_dur:.1f}s"
            response += f"\n- Durata min/max: {min_dur:.1f}s / {max_dur:.1f}s"

        # 2. TREND ULTIMI 7 GIORNI
        cur.execute("""
            SELECT
                DATE("startedAt") as day,
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as success
            FROM n8n.execution_entity
            WHERE "workflowId" = %s
            AND "startedAt" >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE("startedAt")
            ORDER BY day DESC
            LIMIT 7
        """, (wf_id,))

        daily_trend = cur.fetchall()
        if daily_trend:
            response += f"\n\n**[TREND ULTIMI 7 GIORNI]**"
            for day, total, success in daily_trend:
                rate = (success/total*100) if total > 0 else 0
                response += f"\n- {day.strftime('%d/%m')}: {total} esec, {rate:.0f}% successo"

        # 3. ULTIME 10 ESECUZIONI DETTAGLIATE
        cur.execute("""
            SELECT
                "startedAt",
                "stoppedAt",
                status,
                EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt")) as duration
            FROM n8n.execution_entity
            WHERE "workflowId" = %s
            ORDER BY "startedAt" DESC
            LIMIT 10
        """, (wf_id,))

        recent_execs = cur.fetchall()
        if recent_execs:
            response += f"\n\n**[ULTIME 10 ESECUZIONI]**"
            for started, stopped, status, duration in recent_execs:
                status_icon = "[OK]" if status == "success" else "[ERR]"
                dur_str = f"{duration:.0f}s" if duration else "N/A"
                response += f"\n{status_icon} {started.strftime('%d/%m %H:%M')} - {dur_str}"

        conn.close()
        return response

    except Exception as e:
        return f"Errore recupero dettagli processo: {str(e)}"


@tool
@traceable(name="MilhenaAllErrors", run_type="tool")
def get_all_errors_summary_tool(hours: int = 24) -> str:
    """
    Get summary of ALL workflows that had errors (no details, just list).

    🔑 KEYWORDS: errori, ci sono problemi, summary errori, quali errori, riepilogo

    USE THIS WHEN:
    - User chiede panoramica errori generali ("che errori ci sono?", "ci sono problemi?")
    - User chiede quali workflow hanno errori ("quali processi falliscono?")
    - User chiede riepilogo errori ("riassunto errori", "summary problemi")

    DO NOT USE WHEN:
    - User chiede errore di workflow SPECIFICO (usa get_error_details_tool con nome workflow)
    - User chiede dettagli errore (usa get_error_details_tool)
    - User chiede statistiche sistema (usa smart_analytics_query_tool)

    Returns: List of workflow names with error counts
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        time_cutoff = datetime.now() - timedelta(hours=hours)

        # All workflows with errors
        cur.execute("""
            SELECT
                we.name,
                COUNT(*) as error_count,
                MAX(ee."startedAt") as last_error
            FROM n8n.execution_entity ee
            JOIN n8n.workflow_entity we ON ee."workflowId" = we.id
            WHERE ee.status = 'error'
              AND ee."startedAt" >= %s
            GROUP BY we.name
            ORDER BY error_count DESC
            LIMIT 10
        """, (time_cutoff,))

        errors = cur.fetchall()

        if not errors:
            return f"[OK] Nessun errore rilevato nelle ultime {hours} ore. Sistema operativo."

        # SMART RESPONSE: Se c'è UN SOLO errore, mostra subito i dettagli!
        if len(errors) == 1:
            workflow_name = errors[0][0]

            # Ottieni dettagli errore inline (non possiamo chiamare altro @tool)
            cur.execute("""
                SELECT
                    we.name,
                    ee."startedAt",
                    ee."stoppedAt",
                    ee.status,
                    ee.id,
                    ed.data
                FROM n8n.execution_entity ee
                JOIN n8n.workflow_entity we ON ee."workflowId" = we.id
                LEFT JOIN n8n.execution_data ed ON ed."executionId" = ee.id
                WHERE LOWER(we.name) LIKE LOWER(%s)
                  AND ee.status = 'error'
                  AND ee."startedAt" >= %s
                ORDER BY ee."startedAt" DESC
                LIMIT 5
            """, (f"%{workflow_name}%", time_cutoff))

            error_details = cur.fetchall()

            if error_details:
                # Mostra dettagli completi (riusa la logica del tool dettagliato)
                response = f"[ERRORE] **Errore in '{workflow_name}'**:\n\n"

                for idx, (name, started, stopped, status, exec_id, error_data) in enumerate(error_details[:1], 1):  # Solo il primo
                    duration = (stopped - started).total_seconds() if stopped else 0
                    response += f"**Errore del {started.strftime('%d/%m/%Y alle %H:%M')}** (durata: {duration:.0f}s)\n"

                    if error_data:
                        try:
                            # Decompressione errore (inline)
                            data = json.loads(error_data)

                            def decompress(obj, array):
                                if isinstance(obj, dict):
                                    return {k: decompress(v, array) for k, v in obj.items()}
                                elif isinstance(obj, list):
                                    return [decompress(item, array) for item in obj]
                                elif isinstance(obj, str) and obj.isdigit():
                                    idx = int(obj)
                                    if 0 <= idx < len(array):
                                        return decompress(array[idx], array)
                                return obj

                            decompressed = decompress(data[0], data)
                            result_data = decompressed.get('resultData', {})
                            error_obj = result_data.get('error', {})

                            error_msg = error_obj.get('message', 'Errore sconosciuto')
                            node_name = error_obj.get('node', {}).get('name', 'N/A')

                            response += f"[!] **Passaggio fallito:** {node_name}\n"

                            # Trova spiegazione (pattern matching inline)
                            if 'unable to sign without access token' in error_msg.lower():
                                response += "\n[CAUSA] Le credenziali di accesso al file esterno (Google Sheets/Excel) sono scadute o mancanti."
                                response += "\n[SOLUZIONE] Contatta IT per riautorizzare l'accesso al file. Servirà riconnettere l'account Google/Microsoft."
                            elif 'timeout' in error_msg.lower() or 'ETIMEDOUT' in error_msg:
                                response += "\n[CAUSA] Il servizio esterno non ha risposto in tempo."
                                response += "\n[SOLUZIONE] Riprova tra 5 minuti. Se persiste, contatta IT."
                            elif '401' in error_msg or 'unauthorized' in error_msg.lower():
                                response += "\n[CAUSA] Credenziali non valide o scadute."
                                response += "\n[SOLUZIONE] Contatta IT per aggiornare le credenziali."
                            elif '403' in error_msg or 'forbidden' in error_msg.lower():
                                response += "\n[CAUSA] Permessi insufficienti."
                                response += "\n[SOLUZIONE] Contatta IT per richiedere i permessi necessari."
                            elif '429' in error_msg or 'rate limit' in error_msg.lower():
                                response += "\n[CAUSA] Troppo richieste. Limite raggiunto."
                                response += "\n[SOLUZIONE] Attendi 1 ora prima di riprovare."
                            elif 'ECONNREFUSED' in error_msg:
                                response += "\n[CAUSA] Impossibile connettersi al servizio esterno."
                                response += "\n[SOLUZIONE] Contatta IT per verificare lo stato del servizio."
                            else:
                                response += f"\n[INFO] {error_msg}"
                                response += "\n[SOLUZIONE] Contatta IT con questo messaggio e l'orario dell'errore."

                        except Exception as e:
                            logger.error(f"Error parsing error data: {e}")
                            response += "[AVVISO] Dettagli errore non disponibili"
                    else:
                        response += "[AVVISO] Dettagli errore non disponibili"

                cur.close()
                conn.close()
                return response

        # Se ci sono MULTIPLI errori, mostra solo la lista
        response = f"[ERRORE] **Processi con errori** (ultime {hours}h):\n\n"

        for i, (name, count, last_error) in enumerate(errors, 1):
            severity = "[!!!]" if count >= 5 else "[!!]" if count >= 2 else "[!]"
            response += f"{severity} **{name}**\n"
            response += f"   Errori: {count} | Ultimo: {last_error.strftime('%d/%m %H:%M')}\n\n"

        response += f"**Totale processi con errori:** {len(errors)}\n\n"

        # Suggerisci di chiedere dettagli
        response += "[SUGGERIMENTO] Per vedere i dettagli di un errore specifico, chiedi: \"spiegami l'errore di [nome processo]\""

        # Critical alert
        critical = [e for e in errors if e[1] >= 5]
        if critical:
            response += f"\n\n[CRITICO] {len(critical)} processi con errori multipli. Contatta IT urgentemente."

        cur.close()
        conn.close()

        return response

    except Exception as e:
        return f"Errore recupero lista errori: {str(e)}"


@tool
@traceable(name="MilhenaErrorDetails", run_type="tool")
def get_error_details_tool(workflow_name: str, hours: int = 24) -> str:
    """
    Get DETAILED error explanation with cause, failed step, and solution for a SPECIFIC workflow.

    🔑 KEYWORDS: errore, failure, problema, issue, fallimento

    USE THIS WHEN:
    - User chiede errore di workflow SPECIFICO ("che errore ha ChatOne?", "perché fallisce X?")
    - User chiede spiegazione errore ("spiegami errore", "cosa è andato storto")
    - User chiede dettagli failure ("dettagli problema processo X")
    - User chiede soluzione errore ("come risolvo errore X?")
    - IMPORTANT: workflow_name REQUIRED (estrai da query o history)

    DO NOT USE WHEN:
    - User chiede lista errori generali (usa get_all_errors_summary_tool)
    - User chiede statistiche sistema (usa smart_analytics_query_tool)
    - User chiede esecuzioni (usa smart_executions_query_tool)

    Args:
        workflow_name: REQUIRED - Name of workflow to analyze (extract from user query or history)
        hours: Time range in hours (default: last 24 hours)

    Returns:
        Detailed error with: timestamp, failed node/step name, error cause in business terms, solution
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        time_cutoff = datetime.now() - timedelta(hours=hours)

        # Errors for specific workflow WITH error data
        cur.execute("""
            SELECT
                we.name,
                ee."startedAt",
                ee."stoppedAt",
                ee.status,
                ee.id,
                ed.data
            FROM n8n.execution_entity ee
            JOIN n8n.workflow_entity we ON ee."workflowId" = we.id
            LEFT JOIN n8n.execution_data ed ON ed."executionId" = ee.id
            WHERE LOWER(we.name) LIKE LOWER(%s)
              AND ee.status = 'error'
              AND ee."startedAt" >= %s
            ORDER BY ee."startedAt" DESC
            LIMIT 10
        """, (f"%{workflow_name}%", time_cutoff))

        errors = cur.fetchall()

        if not errors:
            return f"Nessun errore trovato per il processo '{workflow_name}' nelle ultime {hours} ore."

        workflow_full_name = errors[0][0]

        response = f"[ERRORE] **Errori per '{workflow_full_name}'** (ultime {hours}h):\n\n"

        # AUTO-ENRICHMENT: Aggiungi statistiche workflow per context completo
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE ee.status = 'success') as successes,
                COUNT(*) FILTER (WHERE ee.status = 'error') as errors_count,
                COUNT(*) as total_execs,
                AVG(EXTRACT(EPOCH FROM (ee."stoppedAt" - ee."startedAt"))) as avg_duration
            FROM n8n.execution_entity ee
            JOIN n8n.workflow_entity we ON ee."workflowId" = we.id
            WHERE LOWER(we.name) LIKE LOWER(%s)
              AND ee."startedAt" >= %s
        """, (f"%{workflow_name}%", time_cutoff))

        stats = cur.fetchone()
        if stats and stats[2] > 0:
            success_rate = (stats[0] / stats[2] * 100) if stats[2] > 0 else 0
            response += f"**📊 Context Performance** (ultime {hours}h):\n"
            response += f"  • Esecuzioni totali: {stats[2]}\n"
            response += f"  • Successi: {stats[0]} | Errori: {stats[1]}\n"
            response += f"  • Success Rate: {success_rate:.1f}%\n"
            response += f"  • Durata media: {stats[3]:.1f}s\n\n"

        response += f"**🔍 Dettaglio Errori:**\n\n"

        # Helper function to decompress n8n error data
        def decompress_error_data(data_str):
            """Decomprime il formato JSON indicizzato di n8n"""
            try:
                data = json.loads(data_str)

                def decompress(obj, array):
                    if isinstance(obj, dict):
                        return {k: decompress(v, array) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [decompress(item, array) for item in obj]
                    elif isinstance(obj, str) and obj.isdigit():
                        idx = int(obj)
                        if 0 <= idx < len(array):
                            return decompress(array[idx], array)
                    return obj

                decompressed = decompress(data[0], data)
                result_data = decompressed.get('resultData', {})
                error = result_data.get('error', {})

                return {
                    'message': error.get('message', 'Errore sconosciuto'),
                    'node': error.get('node', {}).get('name', 'N/A'),
                    'type': error.get('name', 'N/A')
                }
            except Exception as e:
                logger.error(f"Error decompressing error data: {e}")
                return None

        # Helper function to explain error in business terms
        def explain_error(error_msg, node_name):
            """Spiega l'errore in linguaggio business con soluzione"""
            explanations = {
                # OAuth / Autenticazione
                'Unable to sign without access token': {
                    'reason': 'Le credenziali di accesso al file esterno (Google Sheets/Excel) sono scadute o mancanti.',
                    'solution': 'Contatta IT per riautorizzare l\'accesso al file. Servirà riconnettere l\'account Google/Microsoft.'
                },
                'authentication': {
                    'reason': 'Problema di autenticazione con servizio esterno.',
                    'solution': 'Contatta IT per verificare credenziali e permessi di accesso.'
                },
                'invalid credentials': {
                    'reason': 'Le credenziali di accesso non sono corrette o sono scadute.',
                    'solution': 'Contatta IT per aggiornare le credenziali di accesso al servizio.'
                },
                'unauthorized': {
                    'reason': 'Accesso negato al servizio esterno. Credenziali mancanti o non valide.',
                    'solution': 'Contatta IT per verificare i permessi e le credenziali dell\'account.'
                },

                # Timeout / Connessione
                'timeout': {
                    'reason': 'Il sistema esterno non ha risposto in tempo.',
                    'solution': 'Riprova tra qualche minuto. Se persiste, contatta IT per verificare la connessione.'
                },
                'ETIMEDOUT': {
                    'reason': 'Tempo di attesa scaduto durante la connessione al servizio esterno.',
                    'solution': 'Il servizio esterno è lento o non disponibile. Riprova tra 5 minuti.'
                },
                'ECONNREFUSED': {
                    'reason': 'Impossibile connettersi al servizio esterno. Il servizio potrebbe essere offline.',
                    'solution': 'Contatta IT per verificare lo stato del servizio esterno.'
                },
                'network error': {
                    'reason': 'Problema di connessione di rete con il servizio esterno.',
                    'solution': 'Verifica la connessione internet. Se il problema persiste, contatta IT.'
                },

                # Permessi / Rate Limit
                'permission': {
                    'reason': 'Permessi insufficienti per accedere alla risorsa.',
                    'solution': 'Contatta IT per verificare i permessi dell\'account sul servizio esterno.'
                },
                'forbidden': {
                    'reason': 'Accesso negato alla risorsa. I permessi sono insufficienti.',
                    'solution': 'Contatta IT per richiedere i permessi necessari sul file o servizio.'
                },
                'rate limit': {
                    'reason': 'Raggiunto il limite di richieste consentite dal servizio esterno.',
                    'solution': 'Attendi 1 ora prima di riprovare. Se urgente, contatta IT per aumentare i limiti.'
                },
                'too many requests': {
                    'reason': 'Troppe richieste inviate al servizio esterno in breve tempo.',
                    'solution': 'Attendi 30 minuti prima di riprovare l\'elaborazione.'
                },

                # Dati / Formato
                'not found': {
                    'reason': 'Il file o la risorsa richiesta non esiste o è stata spostata.',
                    'solution': 'Verifica che il file esista nella posizione corretta. Contatta IT se non lo trovi.'
                },
                'invalid format': {
                    'reason': 'Il formato dei dati ricevuti non è quello atteso dal sistema.',
                    'solution': 'Contatta IT per verificare la struttura del file o dei dati di input.'
                },
                'required parameter': {
                    'reason': 'Mancano informazioni obbligatorie per completare l\'elaborazione.',
                    'solution': 'Contatta IT specificando quale elaborazione è fallita. Potrebbero servire dati aggiuntivi.'
                },
                'invalid json': {
                    'reason': 'I dati ricevuti dal servizio esterno sono malformati.',
                    'solution': 'Errore tecnico del servizio esterno. Contatta IT per una verifica approfondita.'
                },

                # Email / SMTP
                'SMTP': {
                    'reason': 'Impossibile inviare l\'email. Problema con il server di posta.',
                    'solution': 'Contatta IT per verificare la configurazione del server email.'
                },
                'invalid recipient': {
                    'reason': 'Uno o più destinatari email non sono validi.',
                    'solution': 'Verifica gli indirizzi email dei destinatari. Contatta IT se il problema persiste.'
                },

                # Database / Storage
                'duplicate': {
                    'reason': 'Il record esiste già nel sistema. Impossibile creare duplicati.',
                    'solution': 'Verifica che il dato non sia già presente. Se è corretto, contatta IT.'
                },
                'constraint violation': {
                    'reason': 'Violazione delle regole di integrità dei dati.',
                    'solution': 'I dati non rispettano i vincoli definiti. Contatta IT per una verifica.'
                },

                # API / Servizi esterni
                'API key': {
                    'reason': 'La chiave di accesso al servizio esterno non è valida o è scaduta.',
                    'solution': 'Contatta IT per rinnovare la chiave di accesso al servizio.'
                },
                'quota exceeded': {
                    'reason': 'Superato il limite di utilizzo del servizio esterno per il mese corrente.',
                    'solution': 'Contatta IT per aumentare la quota o attendere il rinnovo mensile.'
                },
                'service unavailable': {
                    'reason': 'Il servizio esterno è temporaneamente non disponibile.',
                    'solution': 'Riprova tra 15 minuti. Se persiste, contatta IT per verifiche.'
                },

                # HTTP Status Codes
                '400': {
                    'reason': 'La richiesta inviata contiene dati non validi o incompleti.',
                    'solution': 'Contatta IT con l\'orario dell\'errore. Potrebbero servire correzioni alla configurazione.'
                },
                '401': {
                    'reason': 'Credenziali non valide o scadute per accedere al servizio.',
                    'solution': 'Contatta IT per aggiornare le credenziali di autenticazione.'
                },
                '403': {
                    'reason': 'Accesso negato. L\'account non ha i permessi necessari.',
                    'solution': 'Contatta IT per richiedere i permessi mancanti sull\'account.'
                },
                '404': {
                    'reason': 'La risorsa richiesta non esiste o è stata rimossa.',
                    'solution': 'Verifica che il file/dato esista. Contatta IT se il problema persiste.'
                },
                '429': {
                    'reason': 'Troppe richieste inviate. Limite del servizio esterno raggiunto.',
                    'solution': 'Attendi 1 ora prima di riprovare. Contatta IT se urgente per aumentare i limiti.'
                },
                '500': {
                    'reason': 'Errore interno del servizio esterno.',
                    'solution': 'Il problema è sul servizio esterno. Riprova tra 30 minuti. Se persiste, contatta IT.'
                },
                '502': {
                    'reason': 'Errore di comunicazione tra servizi. Gateway non raggiungibile.',
                    'solution': 'Problema temporaneo del servizio esterno. Riprova tra 10 minuti.'
                },
                '503': {
                    'reason': 'Servizio esterno temporaneamente in manutenzione.',
                    'solution': 'Riprova tra 20 minuti. Se urgente, verifica lo stato del servizio esterno.'
                },

                # Errori specifici servizi comuni
                'ENOTFOUND': {
                    'reason': 'Impossibile trovare l\'indirizzo del servizio esterno.',
                    'solution': 'Verifica connessione internet. Se funziona, contatta IT per verificare la configurazione.'
                },
                'certificate': {
                    'reason': 'Problema con il certificato di sicurezza del servizio esterno.',
                    'solution': 'Errore di sicurezza della connessione. Contatta IT per verificare i certificati.'
                },
                'SSL': {
                    'reason': 'Errore nella connessione sicura (SSL/TLS) al servizio.',
                    'solution': 'Problema di sicurezza della connessione. Contatta IT immediatamente.'
                },
                'refresh token': {
                    'reason': 'Il token di accesso è scaduto e il rinnovo automatico è fallito.',
                    'solution': 'Contatta IT per riautenticare l\'account e rinnovare i permessi.'
                },
                'webhook': {
                    'reason': 'Il punto di ricezione dati automatico non è raggiungibile o configurato correttamente.',
                    'solution': 'Contatta IT per verificare la configurazione del punto di ricezione dati.'
                },
                'execution': {
                    'reason': 'Errore generico durante l\'elaborazione del processo.',
                    'solution': 'Contatta IT specificando l\'orario esatto dell\'errore per una diagnosi dettagliata.'
                }
            }

            # Cerca spiegazione
            for key, expl in explanations.items():
                if key.lower() in error_msg.lower():
                    return f"\n   [CAUSA] {expl['reason']}\n   [SOLUZIONE] {expl['solution']}"

            return f"\n   [INFO] {error_msg}\n   [SOLUZIONE] Contatta IT con questo messaggio e l'orario dell'errore."

        for i, (name, started, stopped, status, exec_id, error_data) in enumerate(errors, 1):
            duration = (stopped - started).total_seconds() if stopped else 0
            response += f"**{i}. Errore del {started.strftime('%d/%m/%Y alle %H:%M')}** (durata: {duration:.0f}s)\n"

            # Estrai e spiega errore
            if error_data:
                error_info = decompress_error_data(error_data)
                if error_info:
                    response += f"   [!] **Passaggio fallito:** {error_info['node']}\n"
                    response += explain_error(error_info['message'], error_info['node'])
                else:
                    response += "   [AVVISO] Dettagli errore non disponibili"
            else:
                response += "   [AVVISO] Dettagli errore non disponibili"

            response += "\n\n"

        response += f"**Totale errori:** {len(errors)}"

        if len(errors) >= 3:
            response += "\n\n[ATTENZIONE] Errori ripetuti rilevati. Contatta il reparto IT urgentemente con questi dettagli."

        conn.close()
        return response

    except Exception as e:
        return f"Errore recupero dettagli errore: {str(e)}"


# ============================================================================
# KNOWLEDGE BASE TOOL (RAG)
# ============================================================================

@tool
@traceable(name="MilhenaExecutionsList", run_type="tool")
def get_executions_by_date_tool(date: str, workflow_name: Optional[str] = None) -> str:
    """
    Get detailed list of ALL executions for a specific date.

    Use this when user asks for:
    - "tutte le esecuzioni del DD/MM/YY"
    - "dammi le esecuzioni di oggi/ieri/data"
    - "cosa è stato eseguito il DD/MM"
    - "elenco esecuzioni del DD/MM"

    Args:
        date: Date in format DD/MM/YYYY or DD/MM/YY (e.g., "29/09/25", "01/10/2025")
        workflow_name: Optional - filter by workflow name

    Returns:
        Detailed list with: processo name, execution time, status, duration
    """
    import psycopg2
    from datetime import datetime

    try:
        # Parse date (support DD/MM/YY, DD/MM/YYYY, YYYY-MM-DD, and "oggi"/"ieri")
        from datetime import datetime, timedelta

        # Handle special keywords
        if date.lower() in ["oggi", "today"]:
            pg_date = datetime.now().strftime("%Y-%m-%d")
        elif date.lower() in ["ieri", "yesterday"]:
            pg_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        # Check if ISO format (YYYY-MM-DD)
        elif '-' in date and len(date.split('-')) == 3:
            parts = date.split('-')
            if len(parts[0]) == 4:  # Year first (ISO format)
                pg_date = date  # Already in PostgreSQL format
            else:
                return f"[AVVISO] Formato data non valido. Usa DD/MM/YYYY o YYYY-MM-DD (es: 03/10/2025 o 2025-10-03)"
        # Italian format DD/MM/YY or DD/MM/YYYY
        elif '/' in date:
            date_parts = date.split('/')
            if len(date_parts) == 3:
                day, month, year = date_parts
                # Convert 2-digit year to 4-digit
                if len(year) == 2:
                    year = f"20{year}"
                pg_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                return f"[AVVISO] Formato data non valido. Usa DD/MM/YYYY o YYYY-MM-DD (es: 03/10/2025 o 2025-10-03)"
        else:
            return f"[AVVISO] Formato data non valido. Usa DD/MM/YYYY o YYYY-MM-DD (es: 03/10/2025 o 2025-10-03)"

        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to get ALL executions for the date
        query = """
            SELECT
                w.name,
                TO_CHAR(e.\"startedAt\", 'HH24:MI:SS') as execution_time,
                e.status,
                EXTRACT(EPOCH FROM (e.\"stoppedAt\" - e.\"startedAt\")) as duration_seconds
            FROM execution_entity e
            JOIN workflow_entity w ON e.\"workflowId\" = w.id
            WHERE DATE(e.\"startedAt\") = %s
        """

        params = [pg_date]

        if workflow_name:
            query += " AND w.name ILIKE %s"
            params.append(f"%{workflow_name}%")

        query += " ORDER BY e.\"startedAt\" DESC"

        cursor.execute(query, params)
        executions = cursor.fetchall()

        cursor.close()
        conn.close()

        if not executions:
            return f"Nessuna esecuzione trovata per il {date}"

        # Format response with ALL executions listed
        response = f"**Esecuzioni del {date}** (Totale: {len(executions)})\n\n"

        for idx, (name, exec_time, status, duration) in enumerate(executions, 1):
            status_icon = "[OK]" if status == "success" else "[ERR]"
            duration_str = f"{int(duration)}s" if duration else "N/A"

            response += f"{idx}. {status_icon} **{name}**\n"
            response += f"   • Orario: {exec_time}\n"
            response += f"   • Stato: {status}\n"
            response += f"   • Durata: {duration_str}\n\n"

        return response

    except Exception as e:
        logger.error(f"Error getting executions by date: {e}")
        return f"[ERRORE] Impossibile recuperare esecuzioni per {date}: {str(e)}"


@tool
@traceable(name="MilhenaKnowledgeBase", run_type="tool")
async def search_knowledge_base_tool(query: str, top_k: int = 3) -> str:
    """
    Search knowledge base for DOCUMENTATION, HOW-TO, PROCEDURES (NOT for workflow stats!).

    🔑 KEYWORDS: documenti, RAG, knowledge base, archivio, ricerca semantica

    USE THIS WHEN:
    - User chiede documentazione concettuale ("come funziona X?", "cosa fa Y?")
    - User chiede procedure ("how do I...", "come posso...")
    - User chiede info knowledge base ("cerca documenti", "ricerca semantica")
    - Database tools return no data (fallback search)

    DO NOT USE WHEN:
    - User chiede info workflow (usa smart_workflow_query_tool)
    - User chiede statistiche (usa smart_analytics_query_tool)
    - User chiede dettagli processo (usa smart_workflow_query_tool)
    - User chiede esecuzioni (usa smart_executions_query_tool)

    Args:
        query: Search query (conceptual questions, procedures, documentation)
        top_k: Number of results to return (default 3)

    Returns:
        Documentation from knowledge base (NOT execution stats)
    """
    try:
        from app.rag import get_rag_system

        rag = get_rag_system()
        results = await rag.search(query=query, top_k=top_k)

        if not results or len(results) == 0:
            return "Nessuna informazione trovata nella knowledge base. Contatta il reparto IT per maggiori dettagli."

        # Format results business-friendly
        response = "📚 **Informazioni dalla Knowledge Base:**\n\n"

        for i, result in enumerate(results, 1):
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            score = result.get("relevance_score", 0)

            # Only show highly relevant results (score > 0.5)
            if score < 0.5:
                continue

            # Extract title and category
            title = metadata.get("title", "Informazione")
            category = metadata.get("category", "")

            response += f"**{i}. {title}**\n"
            if category:
                response += f"*Categoria: {category}*\n\n"
            response += f"{content}\n\n"
            response += "---\n\n"

        if response == "📚 **Informazioni dalla Knowledge Base:**\n\n":
            return "Nessun risultato rilevante trovato. Per informazioni specifiche, contatta il reparto IT."

        return response

    except Exception as e:
        return f"Errore ricerca knowledge base. Contatta IT per assistenza. (Dettaglio tecnico: {str(e)})"


# ============================================================================
# HTTP CLIENT HELPER - Call PilotProOS Backend APIs
# ============================================================================

async def call_backend_api(endpoint: str, timeout: float = 10.0) -> dict:
    """
    Call PilotProOS backend API from Intelligence Engine.
    Uses service-to-service authentication with shared secret.

    Args:
        endpoint: API path (e.g., "/api/business/top-performers")
        timeout: Request timeout in seconds

    Returns:
        JSON response from backend
    """
    import httpx

    backend_url = os.getenv("BACKEND_URL", "http://pilotpros-backend-dev:3001")
    service_token = os.getenv("SERVICE_AUTH_TOKEN", "intelligence-engine-service-token-2025")

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            headers = {
                "X-Service-Auth": service_token,
                "Content-Type": "application/json"
            }
            response = await client.get(f"{backend_url}{endpoint}", headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.error(f"Backend API timeout: {endpoint}")
        return {"error": "timeout", "endpoint": endpoint}
    except httpx.HTTPStatusError as e:
        logger.error(f"Backend API error {e.response.status_code}: {endpoint}")
        return {"error": f"http_{e.response.status_code}", "endpoint": endpoint}
    except Exception as e:
        logger.error(f"Backend API exception: {endpoint} - {e}")
        return {"error": str(e), "endpoint": endpoint}


# ============================================================================
# NODE-LEVEL TOOLS - Query singoli nodi di workflow
# ============================================================================

@tool
@traceable(name="MilhenaNodeDetails", run_type="tool")
def get_node_execution_details_tool(
    workflow_name: str,
    node_name: str,
    date: str = "oggi"
) -> str:
    """
    Estrae dati di esecuzione di un NODO SPECIFICO di un workflow.

    🔑 KEYWORDS: nodo, step, task, fase, passaggio

    USE THIS WHEN:
    - User chiede output nodo specifico ("output del nodo X", "cosa ha prodotto step Y")
    - User chiede input nodo ("input ricevuto da Z", "che dati ha ricevuto")
    - User chiede dettagli passaggio workflow ("dettagli task X", "info fase Y")
    - User chiede cosa ha fatto un nodo ("cosa ha fatto nodo X?")

    DO NOT USE WHEN:
    - User chiede timeline completa workflow (usa get_raw_modal_data_tool)
    - User chiede dettagli workflow generale (usa smart_workflow_query_tool)
    - User chiede esecuzioni workflow (usa smart_executions_query_tool)

    Args:
        workflow_name: Nome del workflow (es: "ChatOne", "CHATBOT COMMERCIALE")
        node_name: Nome esatto del nodo (es: "Rispondi a mittente", "Ricezione Mail")
        date: Data esecuzione (DD/MM/YYYY, YYYY-MM-DD, "oggi", "ieri")

    Returns:
        Input/output del nodo specifico con timestamp e parametri
    """
    try:
        from datetime import datetime, timedelta

        # Parse date
        if date.lower() in ["oggi", "today"]:
            pg_date = datetime.now().strftime("%Y-%m-%d")
        elif date.lower() in ["ieri", "yesterday"]:
            pg_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        elif '-' in date:
            pg_date = date  # ISO format
        elif '/' in date:
            parts = date.split('/')
            if len(parts) == 3:
                day, month, year = parts
                if len(year) == 2:
                    year = f"20{year}"
                pg_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                return "[ERRORE] Formato data non valido. Usa DD/MM/YYYY o YYYY-MM-DD"
        else:
            return "[ERRORE] Formato data non valido. Usa DD/MM/YYYY o YYYY-MM-DD"

        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to get execution data with node outputs
        query = """
            SELECT
                ee.id as execution_id,
                w.name as workflow_name,
                TO_CHAR(ee."startedAt", 'DD/MM/YYYY HH24:MI:SS') as started_at,
                ee.status,
                ed.data::jsonb -> 'resultData' -> 'runData' -> %s as node_data
            FROM n8n.execution_entity ee
            JOIN n8n.workflow_entity w ON ee."workflowId" = w.id
            JOIN n8n.execution_data ed ON ed."executionId" = ee.id
            WHERE w.name ILIKE %s
              AND DATE(ee."startedAt") = %s
              AND ed.data::jsonb -> 'resultData' -> 'runData' -> %s IS NOT NULL
            ORDER BY ee."startedAt" DESC
            LIMIT 5
        """

        cursor.execute(query, [node_name, f"%{workflow_name}%", pg_date, node_name])
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        if not results:
            return f"[INFO] Nessuna esecuzione trovata per il nodo '{node_name}' nel workflow '{workflow_name}' in data {date}."

        response = f"**Dettagli Nodo: {node_name}** ({workflow_name})\n\n"

        for exec_id, wf_name, started, status, node_data in results:
            response += f"**Esecuzione {exec_id}** - {started}\n"
            response += f"Stato: {status}\n\n"

            # Extract node execution data (first run)
            if node_data and len(node_data) > 0:
                first_run = node_data[0]

                # Input data
                if first_run.get('data', {}).get('main'):
                    main_data = first_run['data']['main'][0]
                    if main_data and len(main_data) > 0:
                        output_json = main_data[0].get('json', {})

                        # Format key fields
                        response += "**Output del nodo:**\n"
                        for key, value in list(output_json.items())[:10]:  # Limit to 10 fields
                            if isinstance(value, str) and len(value) > 200:
                                value = value[:200] + "..."
                            response += f"  • {key}: {value}\n"

                        response += "\n"

            response += "---\n\n"

        return response

    except Exception as e:
        logger.error(f"Error getting node execution details: {e}")
        return f"[ERRORE] Impossibile recuperare dettagli nodo: {str(e)}"


@tool
@traceable(name="MilhenaChatOneEmails", run_type="tool")
def get_chatone_email_details_tool(date: str = "oggi", limit: int = 5) -> str:
    """
    Mostra email ricevute e risposte inviate dal workflow ChatOne (email automation bot).

    🔑 KEYWORDS: email, conversazioni, ChatOne, messaggi, bot chat

    USE THIS WHEN:
    - User chiede email ricevute da ChatOne ("email oggi", "messaggi ricevuti")
    - User chiede risposte inviate da bot ("cosa ha risposto ChatOne?", "reply del bot")
    - User chiede conversazioni email ("ultima conversazione", "chat email")
    - User chiede dettagli ChatOne specifici ("attività ChatOne", "email automatiche")

    DO NOT USE WHEN:
    - User chiede dettagli altri workflow (usa smart_workflow_query_tool)
    - User chiede nodi generici (usa get_node_execution_details_tool)
    - User chiede errori ChatOne (usa get_error_details_tool con workflow="ChatOne")

    Args:
        date: Data esecuzione (DD/MM/YYYY, YYYY-MM-DD, "oggi", "ieri")
        limit: Numero massimo di conversazioni da mostrare (default 5)

    Returns:
        Lista conversazioni: email ricevuta + risposta inviata
    """
    try:
        from datetime import datetime, timedelta

        # Parse date
        if date.lower() in ["oggi", "today"]:
            pg_date = datetime.now().strftime("%Y-%m-%d")
        elif date.lower() in ["ieri", "yesterday"]:
            pg_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        elif '-' in date:
            pg_date = date
        elif '/' in date:
            parts = date.split('/')
            if len(parts) == 3:
                day, month, year = parts
                if len(year) == 2:
                    year = f"20{year}"
                pg_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                return "[ERRORE] Formato data non valido"
        else:
            return "[ERRORE] Formato data non valido"

        conn = get_db_connection()
        cursor = conn.cursor()

        # Query ChatOne workflow executions with email nodes data
        query = """
            SELECT
                ee.id,
                TO_CHAR(ee."startedAt", 'DD/MM/YYYY HH24:MI') as started,
                ed.data::jsonb -> 'resultData' -> 'runData' -> 'Ricezione Mail' -> 0 -> 'data' -> 'main' -> 0 -> 0 -> 'json' as email_received,
                ed.data::jsonb -> 'resultData' -> 'runData' -> 'Rispondi a mittente' -> 0 -> 'data' -> 'main' -> 0 -> 0 -> 'json' as email_reply
            FROM n8n.execution_entity ee
            JOIN n8n.workflow_entity w ON ee."workflowId" = w.id
            JOIN n8n.execution_data ed ON ed."executionId" = ee.id
            WHERE w.name = 'ChatOne'
              AND DATE(ee."startedAt") = %s
              AND ed.data::jsonb -> 'resultData' -> 'runData' -> 'Ricezione Mail' IS NOT NULL
            ORDER BY ee."startedAt" DESC
            LIMIT %s
        """

        cursor.execute(query, [pg_date, limit])
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        if not results:
            return f"[INFO] Nessuna email gestita da ChatOne in data {date}."

        response = f"**📧 Conversazioni Email ChatOne** ({date})\n\n"

        for exec_id, started, email_in, email_out in results:
            response += f"**Conversazione del {started}**\n\n"

            # Email ricevuta
            if email_in:
                sender = email_in.get('from', {})
                if isinstance(sender, dict):
                    sender_email = sender.get('emailAddress', {}).get('address', 'N/A')
                else:
                    sender_email = str(sender)

                subject = email_in.get('subject', 'N/A')
                body = email_in.get('bodyPreview', email_in.get('body', {}).get('content', 'N/A'))

                if isinstance(body, str) and len(body) > 150:
                    body = body[:150] + "..."

                response += f"📨 **Email ricevuta:**\n"
                response += f"  • Da: {sender_email}\n"
                response += f"  • Oggetto: {subject}\n"
                response += f"  • Contenuto: {body}\n\n"

            # Risposta inviata
            if email_out:
                reply_message = email_out.get('message', 'N/A')
                if isinstance(reply_message, str) and len(reply_message) > 200:
                    # Remove HTML tags for readability
                    import re
                    reply_clean = re.sub(r'<[^>]+>', '', reply_message)
                    reply_clean = reply_clean[:200] + "..."
                else:
                    reply_clean = reply_message

                response += f"🤖 **Risposta bot:**\n"
                response += f"  {reply_clean}\n\n"

            response += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

        return response

    except Exception as e:
        logger.error(f"Error getting ChatOne email details: {e}")
        return f"[ERRORE] Impossibile recuperare conversazioni email: {str(e)}"


# ============================================================================
# FRONTEND API INTEGRATION TOOLS - Dati aggregati dal backend
# ============================================================================

@tool
@traceable(name="MilhenaTopPerformers", run_type="tool")
async def get_top_performers_tool() -> str:
    """
    Top 5 workflow che performano meglio (ultimi 30 giorni).

    Use cases:
    - "quali workflow sono i migliori?"
    - "processi più affidabili"
    - "chi performa meglio?"
    - "workflow con più successi"

    Returns:
        Top 5 workflow ordinati per success rate + execution count
    """
    try:
        data = await call_backend_api("/api/business/top-performers")

        if "error" in data:
            return "[ERRORE] Impossibile recuperare top performers dal backend."

        performers = data.get("data", [])

        if not performers:
            return "[INFO] Nessun workflow con esecuzioni sufficienti negli ultimi 30 giorni."

        response = "**🏆 Top 5 Workflow Performanti** (ultimi 30 giorni)\n\n"

        for idx, perf in enumerate(performers, 1):
            name = perf.get("process_name", "N/A")
            exec_count = perf.get("execution_count", 0)
            success_rate = perf.get("success_rate", 0)
            avg_duration = perf.get("avg_duration_ms", 0)

            response += f"{idx}. **{name}**\n"
            response += f"   • Esecuzioni: {exec_count}\n"
            response += f"   • Success Rate: {success_rate}%\n"
            response += f"   • Tempo medio: {int(avg_duration)}ms\n\n"

        return response

    except Exception as e:
        logger.error(f"Error getting top performers: {e}")
        return f"[ERRORE] Impossibile recuperare top performers: {str(e)}"


@tool
@traceable(name="MilhenaHourlyAnalytics", run_type="tool")
async def get_hourly_analytics_tool() -> str:
    """
    Distribuzione oraria delle esecuzioni (24h) con peak hours e quiet hours.

    Use cases:
    - "quando gira di più il sistema?"
    - "orari di picco attività"
    - "momenti più attivi della giornata"
    - "quando ci sono meno esecuzioni?"

    Returns:
        Distribuzione 24h + peak/quiet hours + total executions
    """
    try:
        data = await call_backend_api("/api/business/hourly-analytics")

        if "error" in data:
            return "[ERRORE] Impossibile recuperare analytics orarie dal backend."

        insights = data.get("insights", {})
        hourly_stats = data.get("hourlyStats", [])

        peak_hour = insights.get("peakHour", 0)
        quiet_hour = insights.get("quietHour", 0)
        avg_load = insights.get("avgHourlyLoad", 0)
        peak_value = insights.get("peakValue", 0)
        total_day = insights.get("totalDayExecutions", 0)

        response = f"**⏰ Distribuzione Oraria Attività** (ultimi 7 giorni)\n\n"
        response += f"📊 **Metriche principali:**\n"
        response += f"  • Picco attività: ore {peak_hour}:00 ({peak_value} esecuzioni)\n"
        response += f"  • Momento più calmo: ore {quiet_hour}:00\n"
        response += f"  • Carico medio orario: {avg_load} esecuzioni/h\n"
        response += f"  • Totale giornaliero: {total_day} esecuzioni\n\n"

        # Show top 5 busiest hours
        sorted_hours = sorted(hourly_stats, key=lambda x: x.get('executions', 0), reverse=True)[:5]

        response += "**Orari più attivi:**\n"
        for hour_stat in sorted_hours:
            hour = hour_stat.get('hour', 'N/A')
            execs = hour_stat.get('executions', 0)
            success = hour_stat.get('success_rate', 0)

            response += f"  • {hour}: {execs} esecuzioni ({success}% successo)\n"

        return response

    except Exception as e:
        logger.error(f"Error getting hourly analytics: {e}")
        return f"[ERRORE] Impossibile recuperare analytics orarie: {str(e)}"


@tool
@traceable(name="MilhenaIntegrationHealth", run_type="tool")
async def get_integration_health_tool() -> str:
    """
    Stato di salute delle integrazioni e automazioni attive.

    Use cases:
    - "salute delle integrazioni"
    - "uptime del sistema"
    - "connessioni attive"
    - "ci sono problemi con le integrazioni?"

    Returns:
        Status generale, uptime%, connessioni healthy/total, issues count
    """
    try:
        data = await call_backend_api("/api/business/integration-health")

        if "error" in data:
            return "[ERRORE] Impossibile recuperare health integrazioni dal backend."

        status = data.get("status", "unknown")
        uptime = data.get("uptime", 0)
        healthy_conn = data.get("healthyConnections", 0)
        total_conn = data.get("totalConnections", 0)
        issues = data.get("issuesCount", 0)
        top_services = data.get("topServices", [])

        # Status emoji
        status_emoji = "🟢" if status == "healthy" else "🟡" if status == "degraded" else "🔴"

        response = f"**{status_emoji} Salute Integrazioni**\n\n"
        response += f"**Status generale:** {status.upper()}\n"
        response += f"**Uptime:** {uptime:.1f}%\n"
        response += f"**Connessioni:** {healthy_conn}/{total_conn} healthy\n"
        response += f"**Issues:** {issues}\n\n"

        if top_services and len(top_services) > 0:
            response += "**Servizi principali:**\n"
            for svc in top_services[:5]:
                svc_name = svc.get("name", "N/A")
                svc_status = svc.get("status", "unknown")
                svc_emoji = "✅" if svc_status == "operational" else "⚠️"

                response += f"  {svc_emoji} {svc_name}: {svc_status}\n"

        return response

    except Exception as e:
        logger.error(f"Error getting integration health: {e}")
        return f"[ERRORE] Impossibile recuperare health integrazioni: {str(e)}"


@tool
@traceable(name="MilhenaDailyTrend", run_type="tool")
async def get_daily_trend_tool(days: int = 7) -> str:
    """
    Trend giornaliero esecuzioni (ultimi 7-30 giorni).

    Use cases:
    - "trend degli ultimi giorni"
    - "come sta andando questa settimana?"
    - "grafico esecuzioni giornaliere"
    - "andamento ultimi 7 giorni"

    Args:
        days: Numero di giorni da analizzare (7 o 30)

    Returns:
        Trend giornaliero con success/failures per giorno
    """
    try:
        data = await call_backend_api("/api/business/daily-trend")

        if "error" in data:
            return "[ERRORE] Impossibile recuperare trend giornaliero dal backend."

        daily_stats = data.get("dailyStats", [])

        if not daily_stats:
            return "[INFO] Nessun dato disponibile per il trend giornaliero."

        # Filter last N days
        recent_days = daily_stats[-days:] if len(daily_stats) > days else daily_stats

        response = f"**📈 Trend Giornaliero** (ultimi {len(recent_days)} giorni)\n\n"

        # Calculate totals
        total_execs = sum(d.get('executions', 0) for d in recent_days)
        total_success = sum(d.get('successes', 0) for d in recent_days)
        total_failures = sum(d.get('failures', 0) for d in recent_days)
        avg_success_rate = sum(d.get('success_rate', 0) for d in recent_days) / len(recent_days) if recent_days else 0

        response += f"**Riepilogo periodo:**\n"
        response += f"  • Esecuzioni totali: {total_execs}\n"
        response += f"  • Successi: {total_success}\n"
        response += f"  • Errori: {total_failures}\n"
        response += f"  • Success rate medio: {avg_success_rate:.1f}%\n\n"

        response += "**Dettaglio giornaliero:**\n"
        for day in recent_days[-7:]:  # Show last 7 days detail
            date = day.get('date', 'N/A')
            execs = day.get('executions', 0)
            success = day.get('successes', 0)
            fail = day.get('failures', 0)
            rate = day.get('success_rate', 0)

            status_emoji = "🟢" if rate >= 80 else "🟡" if rate >= 50 else "🔴"

            response += f"{status_emoji} {date}: {execs} exec ({success}✓ / {fail}✗) - {rate}%\n"

        return response

    except Exception as e:
        logger.error(f"Error getting daily trend: {e}")
        return f"[ERRORE] Impossibile recuperare trend giornaliero: {str(e)}"


@tool
@traceable(name="MilhenaAutomationInsights", run_type="tool")
async def get_automation_insights_tool() -> str:
    """
    Insights su automazioni: crescita settimanale, automation rate, trend.

    Use cases:
    - "come crescono le automazioni?"
    - "insights sulle automazioni"
    - "tendenze automazione"
    - "performance generale automazioni"

    Returns:
        Weekly growth, automation rate, active processes, trend indicators
    """
    try:
        data = await call_backend_api("/api/business/automation-insights")

        if "error" in data:
            return "[ERRORE] Impossibile recuperare automation insights dal backend."

        total_procs = data.get("totalProcesses", 0)
        active_procs = data.get("activeProcesses", 0)
        weekly_growth = data.get("weeklyGrowth", 0)
        automation_rate = data.get("automationRate", 0)
        success_rate = data.get("successRate", 0)
        trend = data.get("trend", "stable")

        # Trend emoji
        trend_emoji = "📈" if trend == "up" else "📉" if trend == "down" else "➡️"

        response = f"**🤖 Automation Insights**\n\n"
        response += f"**Processi:**\n"
        response += f"  • Totali: {total_procs}\n"
        response += f"  • Attivi: {active_procs}\n"
        response += f"  • Automation rate: {automation_rate:.1f}%\n\n"

        response += f"**Performance:**\n"
        response += f"  • Success rate: {success_rate:.1f}%\n"
        response += f"  • Crescita settimanale: {weekly_growth:+.1f}%\n"
        response += f"  • Trend: {trend_emoji} {trend}\n"

        return response

    except Exception as e:
        logger.error(f"Error getting automation insights: {e}")
        return f"[ERRORE] Impossibile recuperare automation insights: {str(e)}"
# ============================================================================
# ANALYTICS & STATISTICS TOOLS - Comprehensive system metrics
# ============================================================================

@tool
@traceable(name="MilhenaAnalytics", run_type="tool")
async def get_analytics_overview_tool() -> str:
    """
    Overview analytics completo: processi totali, esecuzioni, success rate, trend 7 giorni.

    Use cases:
    - "analytics generale"
    - "overview sistema"
    - "metriche complete"
    - "statistiche generali"

    Returns:
        Total processes, executions, success rate, trend chart 7 days
    """
    try:
        data = await call_backend_api("/api/business/analytics")

        if "error" in data:
            return "[ERRORE] Impossibile recuperare analytics dal backend."

        overview = data.get("overview", {})
        trend = data.get("trendData", {})

        response = "**📊 Analytics Sistema Completo**\n\n"
        response += f"**Processi:**\n"
        response += f"  • Totali: {overview.get('totalProcesses', 0)}\n"
        response += f"  • Attivi: {overview.get('activeProcesses', 0)}\n\n"

        response += f"**Esecuzioni:**\n"
        response += f"  • Totali: {overview.get('totalExecutions', 0)}\n"
        response += f"  • Success Rate: {overview.get('successRate', 0)}%\n"
        response += f"  • Durata media: {overview.get('avgDurationSeconds', 0)}s\n\n"

        if trend and trend.get('datasets'):
            exec_data = trend['datasets'][0].get('data', [])
            total_week = sum(exec_data)
            response += f"**Trend 7 giorni:**\n"
            response += f"  • Esecuzioni settimana: {total_week}\n"
            response += f"  • Distribuzione: {exec_data}\n"

        return response

    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return f"[ERRORE] Impossibile recuperare analytics: {str(e)}"


@tool
@traceable(name="MilhenaStatistics", run_type="tool")
async def get_statistics_tool() -> str:
    """
    Statistiche di sistema: processi, esecuzioni, success rate, processing time.

    Use cases:
    - "statistiche sistema"
    - "numeri chiave"
    - "KPI principali"

    Returns:
        Core KPIs: total processes, active, executions, success rate, avg time
    """
    try:
        data = await call_backend_api("/api/business/statistics")

        if "error" in data:
            return "[ERRORE] Impossibile recuperare statistiche dal backend."

        stats = data.get("data", {})

        response = "**📈 Statistiche Sistema**\n\n"
        response += f"• Processi totali: {stats.get('totalProcesses', 0)}\n"
        response += f"• Processi attivi: {stats.get('activeProcesses', 0)}\n"
        response += f"• Esecuzioni totali: {stats.get('totalExecutions', 0)}\n"
        response += f"• Success rate: {stats.get('successRate', 0)}%\n"
        response += f"• Tempo elaborazione medio: {stats.get('avgProcessingTime', 0)}ms\n"

        return response

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return f"[ERRORE] Impossibile recuperare statistiche: {str(e)}"


@tool
@traceable(name="MilhenaPerformanceMetrics", run_type="tool")
async def get_performance_metrics_frontend_tool() -> str:
    """
    Performance metrics dettagliati dal frontend.

    Use cases:
    - "performance dettagliate"
    - "metriche performance"
    - "KPI performance"

    Returns:
        Performance KPIs from frontend API
    """
    try:
        data = await call_backend_api("/api/business/performance-metrics")

        if "error" in data:
            return "[ERRORE] Impossibile recuperare performance metrics dal backend."

        return f"**⚡ Performance Metrics**\n\n{json.dumps(data, indent=2, ensure_ascii=False)}"

    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return f"[ERRORE] Impossibile recuperare performance metrics: {str(e)}"


# ============================================================================
# WORKFLOW DETAILS TOOLS - Deep dive su workflow specifici
# ============================================================================

@tool
@traceable(name="MilhenaWorkflowDashboard", run_type="tool")
async def get_workflow_dashboard_tool(workflow_id: str) -> str:
    """
    Dashboard completo di un workflow con recentActivity (email, AI responses, orders).

    Use cases:
    - "dashboard completo di [WORKFLOW]"
    - "attività recenti di [WORKFLOW]"
    - "cosa ha fatto [WORKFLOW] ultimamente"

    Args:
        workflow_id: ID del workflow (es: iZnBHM7mDFS2wW0u per ChatOne)

    Returns:
        Workflow info, capabilities, recentActivity (INCLUDE EMAIL DETAILS!)
    """
    try:
        data = await call_backend_api(f"/api/business/dashboard/{workflow_id}")

        if "error" in data:
            return f"[ERRORE] Impossibile recuperare dashboard per workflow {workflow_id}."

        workflow = data.get("workflow", {})
        recent = data.get("recentActivity", [])

        response = f"**📊 Dashboard: {workflow.get('name', 'N/A')}**\n\n"
        response += f"**Status:** {'Attivo' if workflow.get('active') else 'Inattivo'}\n"
        response += f"**Complessità:** {workflow.get('nodeCount', 0)} passaggi\n\n"

        if recent:
            response += f"**🔔 Attività Recenti** ({len(recent)} eventi):\n\n"
            for idx, activity in enumerate(recent[:10], 1):
                activity_type = activity.get('type', 'N/A')
                summary = activity.get('summary', 'N/A')
                timestamp = activity.get('timestamp', 'N/A')

                response += f"{idx}. [{activity_type}] {summary}\n"
                response += f"   {timestamp}\n\n"

        return response

    except Exception as e:
        logger.error(f"Error getting workflow dashboard: {e}")
        return f"[ERRORE] Impossibile recuperare dashboard workflow: {str(e)}"


@tool
@traceable(name="MilhenaWorkflowFullStats", run_type="tool")
async def get_workflow_full_stats_tool(workflow_id: str, days: int = 30) -> str:
    """
    Statistiche complete workflow: KPIs, trend, performance (stesso dato del Command Center).

    Use cases:
    - "statistiche complete di [WORKFLOW]"
    - "performance dettagliate [WORKFLOW]"
    - "full stats [WORKFLOW]"

    Args:
        workflow_id: ID workflow
        days: Periodo analisi (default 30)

    Returns:
        Complete stats: executions, success rate, durations, trend
    """
    try:
        data = await call_backend_api(f"/api/business/workflow/{workflow_id}/full-stats?days={days}")

        if "error" in data:
            return f"[ERRORE] Impossibile recuperare full stats per workflow {workflow_id}."

        kpis = data.get("kpis", {})
        trend = data.get("trend", [])

        response = f"**📈 Full Statistics** ({days} giorni)\n\n"
        response += f"**KPIs:**\n"
        response += f"  • Esecuzioni totali: {kpis.get('totalExecutions', 0)}\n"
        response += f"  • Successi: {kpis.get('successfulExecutions', 0)}\n"
        response += f"  • Errori: {kpis.get('failedExecutions', 0)}\n"
        response += f"  • Canceled: {kpis.get('canceledExecutions', 0)}\n"
        response += f"  • Success rate: {kpis.get('successRate', 0)}%\n"
        response += f"  • Tempo medio: {kpis.get('avgRunTime', 0)}ms\n"
        response += f"  • Ultime 24h: {kpis.get('last24hExecutions', 0)} esecuzioni\n\n"

        if trend:
            response += f"**Trend ultimi {len(trend)} giorni:**\n"
            for day in trend[-7:]:
                date = day.get('date', 'N/A')
                execs = day.get('executions', 0)
                success = day.get('successful', 0)
                response += f"  {date}: {execs} exec ({success} successi)\n"

        return response

    except Exception as e:
        logger.error(f"Error getting workflow full stats: {e}")
        return f"[ERRORE] Impossibile recuperare full stats: {str(e)}"


@tool
@traceable(name="MilhenaWorkflowCards", run_type="tool")
async def get_workflow_cards_tool() -> str:
    """
    Card overview di TUTTI i workflow con metriche essenziali.

    🔑 KEYWORDS: card, scheda, overview processi, riepilogo, vista generale

    USE THIS WHEN:
    - User chiede overview generale workflow ("overview tutti i workflow", "panoramica processi")
    - User chiede card riepilogo ("card processi", "schede workflow")
    - User chiede vista generale sistema ("vista generale", "riepilogo sistema")

    DO NOT USE WHEN:
    - User chiede dettagli workflow specifico (usa smart_workflow_query_tool)
    - User chiede statistiche dettagliate (usa smart_analytics_query_tool)
    - User chiede lista semplice nomi (usa get_workflows_tool)

    Returns:
        Lista card con: nome, status, esecuzioni, success rate per ogni workflow
    """
    try:
        data = await call_backend_api("/api/business/workflow-cards")

        if "error" in data:
            return "[ERRORE] Impossibile recuperare workflow cards dal backend."

        cards = data.get("cards", [])

        if not cards:
            return "[INFO] Nessun workflow trovato."

        response = "**🗂️ Workflow Cards** (overview completo)\n\n"

        for idx, card in enumerate(cards[:15], 1):  # Limit 15
            name = card.get('name', 'N/A')
            active = card.get('active', False)
            execs = card.get('executionCount', 0)
            success_rate = card.get('successRate', 0)

            status_emoji = "🟢" if active else "⚪"

            response += f"{idx}. {status_emoji} **{name}**\n"
            response += f"   Esecuzioni: {execs} | Success: {success_rate}%\n"

        return response

    except Exception as e:
        logger.error(f"Error getting workflow cards: {e}")
        return f"[ERRORE] Impossibile recuperare workflow cards: {str(e)}"


# ============================================================================
# EXECUTIONS TOOLS - Query su esecuzioni specifiche
# ============================================================================

@tool
@traceable(name="MilhenaExecutionsList", run_type="tool")
async def get_executions_list_tool(limit: int = 20) -> str:
    """
    Lista esecuzioni recenti (tutte i workflow).

    Use cases:
    - "ultime esecuzioni"
    - "lista run recenti"
    - "cosa è stato eseguito di recente"

    Args:
        limit: Numero esecuzioni da mostrare (default 20)

    Returns:
        Lista esecuzioni: workflow, status, timestamp, duration
    """
    try:
        data = await call_backend_api(f"/api/business/executions?limit={limit}")

        if "error" in data:
            return "[ERRORE] Impossibile recuperare executions dal backend."

        executions = data.get("data", [])

        if not executions:
            return "[INFO] Nessuna esecuzione recente trovata."

        response = f"**🔄 Ultime {len(executions)} Esecuzioni**\n\n"

        for idx, exe in enumerate(executions[:20], 1):
            workflow_name = exe.get('workflowName', 'N/A')
            status = exe.get('status', 'N/A')
            started = exe.get('startedAt', 'N/A')[:19] if exe.get('startedAt') else 'N/A'
            duration = exe.get('duration', 0)

            status_emoji = "✅" if status == "success" else "❌" if status == "error" else "⏸️"

            response += f"{idx}. {status_emoji} **{workflow_name}**\n"
            response += f"   {started} | {int(duration)}ms | {status}\n"

        return response

    except Exception as e:
        logger.error(f"Error getting executions list: {e}")
        return f"[ERRORE] Impossibile recuperare executions: {str(e)}"


@tool
@traceable(name="MilhenaWorkflowExecutions", run_type="tool")
async def get_workflow_executions_tool(workflow_id: str, limit: int = 10) -> str:
    """
    Esecuzioni di un workflow SPECIFICO.

    Use cases:
    - "esecuzioni di [WORKFLOW]"
    - "run di [WORKFLOW]"
    - "storia esecuzioni [WORKFLOW]"

    Args:
        workflow_id: ID del workflow
        limit: Numero esecuzioni (default 10)

    Returns:
        Lista esecuzioni del workflow specifico
    """
    try:
        data = await call_backend_api(f"/api/business/process-executions/{workflow_id}?limit={limit}")

        if "error" in data:
            return f"[ERRORE] Impossibile recuperare executions per workflow {workflow_id}."

        executions = data.get("data", [])

        if not executions:
            return f"[INFO] Nessuna esecuzione trovata per workflow {workflow_id}."

        response = f"**🔄 Esecuzioni Workflow** (ultime {len(executions)})\n\n"

        for idx, exe in enumerate(executions, 1):
            status = exe.get('status', 'N/A')
            started = exe.get('startedAt', 'N/A')[:19] if exe.get('startedAt') else 'N/A'
            duration = exe.get('duration', 0)

            status_emoji = "✅" if status == "success" else "❌"

            response += f"{idx}. {status_emoji} {started} | {int(duration)}ms | {status}\n"

        return response

    except Exception as e:
        logger.error(f"Error getting workflow executions: {e}")
        return f"[ERRORE] Impossibile recuperare workflow executions: {str(e)}"


@tool
@traceable(name="MilhenaExecutionStatus", run_type="tool")
async def get_execution_status_tool(execution_id: int) -> str:
    """
    Status dettagliato di una ESECUZIONE SPECIFICA.

    Use cases:
    - "status esecuzione [ID]"
    - "dettagli run [ID]"
    - "cosa è successo nell'esecuzione [ID]"

    Args:
        execution_id: ID esecuzione

    Returns:
        Status, duration, error details (if any)
    """
    try:
        data = await call_backend_api(f"/api/business/execution-status/{execution_id}")

        if "error" in data:
            return f"[ERRORE] Impossibile recuperare status per execution {execution_id}."

        exe = data.get("data", {})

        response = f"**🔍 Execution {execution_id}**\n\n"
        response += f"• Workflow: {exe.get('workflowName', 'N/A')}\n"
        response += f"• Status: {exe.get('status', 'N/A')}\n"
        response += f"• Started: {exe.get('startedAt', 'N/A')[:19]}\n"
        response += f"• Duration: {exe.get('duration', 0)}ms\n"

        if exe.get('status') == 'error':
            error_msg = exe.get('errorMessage', 'N/A')
            response += f"\n❌ **Errore:** {error_msg}\n"

        return response

    except Exception as e:
        logger.error(f"Error getting execution status: {e}")
        return f"[ERRORE] Impossibile recuperare execution status: {str(e)}"


# ============================================================================
# TIMELINE & EVENTS TOOLS - Real-time monitoring
# ============================================================================

@tool
@traceable(name="MilhenaLiveEvents", run_type="tool")
async def get_live_events_tool() -> str:
    """
    Eventi in tempo reale (esecuzioni attive, errori, completamenti).

    🔑 KEYWORDS: eventi, real-time, stream, live, in corso

    USE THIS WHEN:
    - User chiede cosa sta succedendo ora ("cosa sta succedendo?", "attività corrente")
    - User chiede eventi live ("eventi real-time", "stream live")
    - User chiede cosa sta girando ("cosa è in esecuzione?", "processi attivi ora")
    - User chiede monitoring tempo reale ("monitoring live", "status adesso")

    DO NOT USE WHEN:
    - User chiede storico esecuzioni (usa smart_executions_query_tool)
    - User chiede statistiche (usa smart_analytics_query_tool)
    - User chiede errori passati (usa get_error_details_tool)

    Returns:
        Live events stream con timestamp
    """
    try:
        data = await call_backend_api("/api/business/live-events")

        if "error" in data:
            return "[ERRORE] Impossibile recuperare live events dal backend."

        events = data.get("events", [])

        if not events:
            return "[INFO] Nessun evento live al momento. Sistema in standby."

        response = "**🔴 Eventi Live**\n\n"

        for idx, event in enumerate(events[:15], 1):
            event_type = event.get('type', 'N/A')
            workflow_name = event.get('workflowName', 'N/A')
            timestamp = event.get('timestamp', 'N/A')

            emoji = "▶️" if event_type == "started" else "✅" if event_type == "success" else "❌"

            response += f"{idx}. {emoji} {workflow_name} - {event_type}\n"
            response += f"   {timestamp}\n"

        return response

    except Exception as e:
        logger.error(f"Error getting live events: {e}")
        return f"[ERRORE] Impossibile recuperare live events: {str(e)}"


@tool
@traceable(name="MilhenaRawModalData", run_type="tool")
async def get_raw_modal_data_tool(workflow_id: str, execution_id: int = None) -> str:
    """
    Raw data per modal Timeline: NODE-LEVEL data completi con business intelligence.

    🔑 KEYWORDS: timeline, sequenza, traccia esecuzione, log dettagliato, percorso

    USE THIS WHEN:
    - User chiede timeline completa workflow ("timeline dettagliata X", "sequenza esecuzione")
    - User chiede dettagli node-by-node ("cosa ha fatto ogni nodo", "percorso completo")
    - User chiede traccia esecuzione ("log esecuzione completo", "breakdown workflow")
    - User chiede dettagli business nodes ("business data", "dati completi esecuzione")
    - QUESTO È IL TOOL PIÙ POTENTE per dettagli node-by-node!

    DO NOT USE WHEN:
    - User chiede singolo nodo (usa get_node_execution_details_tool)
    - User chiede statistiche workflow (usa smart_workflow_query_tool)
    - User chiede lista esecuzioni (usa smart_executions_query_tool)

    Args:
        workflow_id: ID workflow
        execution_id: ID esecuzione specifica (opzionale, default=latest)

    Returns:
        Business nodes con input/output, AI summaries, email details, order data
    """
    try:
        url = f"/api/business/raw-data-for-modal/{workflow_id}"
        if execution_id:
            url += f"?executionId={execution_id}"

        data = await call_backend_api(url)

        if "error" in data:
            return f"[ERRORE] Impossibile recuperare raw modal data per workflow {workflow_id}."

        result = data.get("data", {})
        business_nodes = result.get("businessNodes", [])
        workflow = result.get("workflow", {})

        response = f"**🔬 Timeline Dettagliata: {workflow.get('name', 'N/A')}**\n\n"

        if not business_nodes:
            return f"[INFO] Nessun nodo business configurato per questo workflow. Aggiungi note 'show-1', 'show-2' ai nodi in n8n."

        for idx, node in enumerate(business_nodes, 1):
            node_name = node.get('businessName') or node.get('name', 'N/A')
            node_type = node.get('nodeType', 'N/A')
            status = node.get('status', 'unknown')

            status_emoji = "✅" if status == "success" else "❌" if status == "error" else "⚙️"

            response += f"{idx}. {status_emoji} **{node_name}**\n"
            response += f"   Tipo: {node_type}\n"

            # Extract business data
            data_obj = node.get('data', {})

            # Email data
            if data_obj.get('emailSender'):
                response += f"   📧 Email da: {data_obj.get('emailSender')}\n"
                response += f"   📝 Oggetto: {data_obj.get('emailSubject', 'N/A')[:60]}\n"

            # AI response
            if data_obj.get('aiResponse'):
                ai_resp = data_obj.get('aiResponse')[:100]
                response += f"   🤖 AI: {ai_resp}...\n"

            # Order data
            if data_obj.get('orderId'):
                response += f"   📦 Order: {data_obj.get('orderId')}\n"

            response += "\n"

        return response

    except Exception as e:
        logger.error(f"Error getting raw modal data: {e}")
        return f"[ERRORE] Impossibile recuperare raw modal data: {str(e)}"


# ============================================================================
# ACTION TOOLS - Execute, toggle, stop workflows
# ============================================================================

@tool
@traceable(name="MilhenaExecuteWorkflow", run_type="tool")
async def execute_workflow_tool(workflow_id: str) -> str:
    """
    ESEGUE un workflow manualmente (trigger manual execution).

    🔑 KEYWORDS: esegui, avvia, lancia, run workflow, start processo

    USE THIS WHEN:
    - User chiede esecuzione manuale workflow ("esegui X", "avvia workflow Y")
    - User chiede di lanciare processo ("lancia processo X", "start workflow Y")
    - User chiede trigger manuale ("triggera X", "run manualmente Y")
    - ⚠️ AZIONE CRITICA - Esegue effettivamente il workflow!

    DO NOT USE WHEN:
    - User chiede info workflow (usa smart_workflow_query_tool)
    - User chiede status esecuzione (usa smart_executions_query_tool)
    - User chiede attivare/disattivare (usa toggle_workflow_tool)

    Args:
        workflow_id: ID del workflow da eseguire

    Returns:
        Execution ID e status iniziale
    """
    try:
        import httpx
        backend_url = os.getenv("BACKEND_URL", "http://pilotpros-backend-dev:3001")
        service_token = os.getenv("SERVICE_AUTH_TOKEN", "intelligence-engine-service-token-2025")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{backend_url}/api/business/execute-workflow/{workflow_id}",
                headers={
                    "X-Service-Auth": service_token,
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            data = response.json()

        if data.get("success"):
            exec_id = data.get("executionId", "N/A")
            return f"✅ Workflow avviato con successo!\n\nExecution ID: {exec_id}\n\nPuoi monitorare lo stato con get_execution_status_tool({exec_id})"
        else:
            return f"❌ Errore avvio workflow: {data.get('message', 'Unknown error')}"

    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        return f"[ERRORE] Impossibile eseguire workflow: {str(e)}"


@tool
@traceable(name="MilhenaToggleWorkflow", run_type="tool")
async def toggle_workflow_tool(workflow_id: str, active: bool) -> str:
    """
    ATTIVA o DISATTIVA un workflow.

    🔑 KEYWORDS: attiva, disattiva, enable, disable, on/off

    USE THIS WHEN:
    - User chiede attivazione workflow ("attiva X", "enable processo Y")
    - User chiede disattivazione workflow ("disattiva X", "disable processo Y", "spegni X")
    - User chiede cambio stato workflow ("accendi X", "on/off Y")
    - ⚠️ AZIONE CRITICA - Modifica stato workflow!

    DO NOT USE WHEN:
    - User chiede esecuzione manuale (usa execute_workflow_tool)
    - User chiede info workflow (usa smart_workflow_query_tool)
    - User chiede status esecuzione (usa smart_executions_query_tool)

    Args:
        workflow_id: ID workflow
        active: True per attivare, False per disattivare

    Returns:
        Nuovo status del workflow
    """
    try:
        import httpx
        backend_url = os.getenv("BACKEND_URL", "http://pilotpros-backend-dev:3001")
        service_token = os.getenv("SERVICE_AUTH_TOKEN", "intelligence-engine-service-token-2025")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{backend_url}/api/business/toggle-workflow/{workflow_id}",
                headers={
                    "X-Service-Auth": service_token,
                    "Content-Type": "application/json"
                },
                json={"active": active}
            )
            response.raise_for_status()
            data = response.json()

        if data.get("success"):
            action = "attivato" if active else "disattivato"
            return f"✅ Workflow {action} con successo!\n\nNuovo status: {'ATTIVO' if active else 'INATTIVO'}"
        else:
            return f"❌ Errore toggle workflow: {data.get('message', 'Unknown error')}"

    except Exception as e:
        logger.error(f"Error toggling workflow: {e}")
        return f"[ERRORE] Impossibile modificare stato workflow: {str(e)}"


# ============================================================================
# SMART CONSOLIDATED TOOLS - Riducono 30 tools → 12 tools
# ============================================================================

@tool
@traceable(name="MilhenaSmartAnalytics", run_type="tool")
async def smart_analytics_query_tool(
    metric_type: str = "statistics",
    period_days: int = 7
) -> str:
    """
    Smart Analytics Query - Consolida 9 tool analytics in UNO.

    🔑 KEYWORDS: statistiche, metriche, KPI, analytics, performance

    USE THIS WHEN:
    - User chiede statistiche sistema ("statistiche", "KPI", "metriche")
    - User chiede performance overview ("analytics", "overview completo")
    - User chiede top performers ("migliori workflow", "top processi")
    - User chiede distribuzione oraria ("orari picco", "quando più attivo")
    - User chiede trend temporali ("trend ultimi giorni", "andamento")
    - User chiede health integrazioni ("salute", "status integrazioni")
    - User chiede automation insights ("automazioni", "crescita", "rate")

    DO NOT USE WHEN:
    - User chiede dettagli workflow specifico (usa smart_workflow_query_tool)
    - User chiede esecuzioni specifiche (usa smart_executions_query_tool)
    - User chiede errori (usa get_error_details_tool o get_all_errors_summary_tool)
    - User chiede lista processi senza metriche (usa get_workflows_tool)

    Args:
        metric_type: Tipo metrica richiesta
          - "statistics": KPI core sistema (default)
          - "overview": Analytics overview con trend
          - "top_performers": Top 5 workflow migliori
          - "hourly": Distribuzione oraria 24h
          - "daily_trend": Trend giornaliero N giorni
          - "automation": Automation insights (growth, rate)
          - "integration_health": Health integrazioni
          - "performance": Performance metrics dettagliati
        period_days: Periodo analisi in giorni (7 o 30)

    Returns:
        Metriche richieste formattate per business user
    """
    try:
        # Route to appropriate backend API based on metric_type
        if metric_type == "statistics":
            data = await call_backend_api("/api/business/statistics")
            if "error" in data:
                return "[ERRORE] Impossibile recuperare statistiche."
            stats = data.get("data", {})
            return f"""📈 Statistiche Sistema

• Processi totali: {stats.get('totalProcesses', 0)}
• Processi attivi: {stats.get('activeProcesses', 0)}
• Esecuzioni totali: {stats.get('totalExecutions', 0)}
• Success rate: {stats.get('successRate', 0)}%
• Tempo elaborazione medio: {stats.get('avgProcessingTime', 0)}ms"""

        elif metric_type == "overview":
            data = await call_backend_api("/api/business/analytics")
            if "error" in data:
                return "[ERRORE] Impossibile recuperare analytics overview."
            overview = data.get("overview", {})
            return f"""📊 Analytics Sistema Completo

Processi: {overview.get('totalProcesses', 0)} totali, {overview.get('activeProcesses', 0)} attivi
Esecuzioni: {overview.get('totalExecutions', 0)} totali, {overview.get('successRate', 0)}% successo
Durata media: {overview.get('avgDurationSeconds', 0)}s"""

        elif metric_type == "top_performers":
            data = await call_backend_api("/api/business/top-performers")
            if "error" in data:
                return "[ERRORE] Impossibile recuperare top performers."
            performers = data.get("data", [])
            response = "🏆 Top 5 Workflow Performanti\n\n"
            for idx, perf in enumerate(performers[:5], 1):
                response += f"{idx}. {perf.get('process_name')} - {perf.get('success_rate')}% ({perf.get('execution_count')} exec)\n"
            return response

        elif metric_type == "hourly":
            data = await call_backend_api("/api/business/hourly-analytics")
            insights = data.get("insights", {})
            return f"""⏰ Distribuzione Oraria

Picco: ore {insights.get('peakHour', 0)}:00 ({insights.get('peakValue', 0)} exec)
Calmo: ore {insights.get('quietHour', 0)}:00
Media oraria: {insights.get('avgHourlyLoad', 0)} exec/h"""

        elif metric_type == "daily_trend":
            data = await call_backend_api("/api/business/daily-trend")
            daily_stats = data.get("dailyStats", [])[-period_days:]
            total = sum(d.get('executions', 0) for d in daily_stats)
            success = sum(d.get('successes', 0) for d in daily_stats)
            return f"""📈 Trend Ultimi {period_days} Giorni

Esecuzioni totali: {total}
Successi: {success}
Errori: {total-success}"""

        elif metric_type == "automation":
            data = await call_backend_api("/api/business/automation-insights")
            return f"""🤖 Automation Insights

Processi: {data.get('totalProcesses', 0)} totali, {data.get('activeProcesses', 0)} attivi
Success rate: {data.get('successRate', 0):.1f}%
Crescita settimanale: {data.get('weeklyGrowth', 0):+.1f}%"""

        elif metric_type == "integration_health":
            data = await call_backend_api("/api/business/integration-health")
            return f"""🟢 Salute Integrazioni

Status: {data.get('status', 'N/A').upper()}
Uptime: {data.get('uptime', 0):.1f}%
Connessioni: {data.get('healthyConnections', 0)}/{data.get('totalConnections', 0)}"""

        elif metric_type == "performance":
            data = await call_backend_api("/api/business/performance-metrics")
            return f"⚡ Performance Metrics\n\n{json.dumps(data, indent=2, ensure_ascii=False)[:500]}"

        else:
            return f"[ERRORE] metric_type '{metric_type}' non valido. Usa: statistics, overview, top_performers, hourly, daily_trend, automation, integration_health, performance"

    except Exception as e:
        logger.error(f"Error in smart analytics query: {e}")
        return f"[ERRORE] Impossibile recuperare analytics: {str(e)}"


@tool
@traceable(name="MilhenaSmartWorkflow", run_type="tool")
async def smart_workflow_query_tool(
    workflow_id: str,
    detail_level: str = "dashboard"
) -> str:
    """
    Smart Workflow Query - Consolida 3 tool workflow details in UNO.

    🔑 KEYWORDS: dettagli workflow, dashboard, info processo, card, scheda

    USE THIS WHEN:
    - User chiede info su workflow SPECIFICO ("dettagli ChatOne", "info processo X")
    - User chiede dashboard processo ("dashboard X", "mostra card X")
    - User chiede statistiche workflow specifico ("statistiche ChatOne", "KPI processo X")
    - User chiede attività recenti processo ("cosa ha fatto X", "ultimi eventi X")

    DO NOT USE WHEN:
    - User chiede lista workflow (usa get_workflows_tool)
    - User chiede statistiche GENERALI sistema (usa smart_analytics_query_tool)
    - User chiede esecuzioni specifiche (usa smart_executions_query_tool)
    - User chiede errori (usa get_error_details_tool)

    Args:
        workflow_id: ID workflow (es: "iZnBHM7mDFS2wW0u") o nome (es: "ChatOne")
        detail_level: Livello dettaglio richiesto
          - "basic": Status, errori recenti, performance base
          - "dashboard": Dashboard completo + recentActivity (EMAIL, AI responses)
          - "full_stats": Statistiche complete 30gg (KPIs, trend, durations)

    Returns:
        Dettagli workflow al livello richiesto
    """
    try:
        # Call appropriate backend API based on detail_level
        if detail_level == "basic":
            # Use DB query for basic info
            return get_workflow_details_tool(workflow_name=workflow_id)

        elif detail_level == "dashboard":
            # Use dashboard API (has recentActivity!)
            data = await call_backend_api(f"/api/business/dashboard/{workflow_id}")
            if "error" in data:
                return f"[ERRORE] Impossibile recuperare dashboard workflow."

            workflow = data.get("workflow", {})
            recent = data.get("recentActivity", [])

            response = f"""📊 Dashboard: {workflow.get('name', 'N/A')}

Status: {'Attivo' if workflow.get('active') else 'Inattivo'}
Complessità: {workflow.get('nodeCount', 0)} passaggi

🔔 Attività Recenti ({len(recent)} eventi):
"""
            for idx, act in enumerate(recent[:5], 1):
                response += f"{idx}. [{act.get('type')}] {act.get('summary', '')[:80]}\n"
            return response

        elif detail_level == "full_stats":
            # Use full-stats API
            data = await call_backend_api(f"/api/business/workflow/{workflow_id}/full-stats?days=30")
            if "error" in data:
                return f"[ERRORE] Impossibile recuperare full stats workflow."

            kpis = data.get("kpis", {})
            return f"""📈 Statistiche Complete (30 giorni)

Esecuzioni: {kpis.get('totalExecutions', 0)} totali
Successi: {kpis.get('successfulExecutions', 0)} ({kpis.get('successRate', 0)}%)
Errori: {kpis.get('failedExecutions', 0)}
Tempo medio: {kpis.get('avgRunTime', 0)}ms
Ultime 24h: {kpis.get('last24hExecutions', 0)} esecuzioni"""

        else:
            return f"[ERRORE] detail_level '{detail_level}' non valido. Usa: basic, dashboard, full_stats"

    except Exception as e:
        logger.error(f"Error in smart workflow query: {e}")
        return f"[ERRORE] Impossibile recuperare dati workflow: {str(e)}"


@tool
@traceable(name="MilhenaSmartExecutions", run_type="tool")
async def smart_executions_query_tool(
    scope: str = "recent_all",
    target: str = None,
    limit: int = 20
) -> str:
    """
    Smart Executions Query - Consolida 4 tool executions in UNO.

    🔑 KEYWORDS: esecuzioni, run, risultati, execution history, cronologia

    USE THIS WHEN:
    - User chiede ultime esecuzioni generali ("ultime esecuzioni", "cosa è stato eseguito")
    - User chiede esecuzioni per data ("esecuzioni di oggi", "run di ieri")
    - User chiede esecuzioni workflow specifico ("esecuzioni ChatOne", "run processo X")
    - User chiede status esecuzione specifica ("status esecuzione 123", "dettagli run ID")

    DO NOT USE WHEN:
    - User chiede statistiche sistema (usa smart_analytics_query_tool)
    - User chiede dettagli workflow (usa smart_workflow_query_tool)
    - User chiede errori specifici (usa get_error_details_tool)
    - User chiede lista processi (usa get_workflows_tool)

    Args:
        scope: Tipo query esecuzioni
          - "recent_all": Ultime N esecuzioni (cross-workflow)
          - "by_date": Esecuzioni per data specifica
          - "by_workflow": Esecuzioni di workflow specifico
          - "specific": Status esecuzione singola
        target: Valore filtro (date | workflow_id | execution_id)
        limit: Numero risultati (default 20)

    Returns:
        Lista esecuzioni o status specifico
    """
    try:
        if scope == "recent_all":
            # Call backend API for recent executions
            data = await call_backend_api(f"/api/business/executions?limit={limit}")
            if "error" in data:
                return "[ERRORE] Impossibile recuperare esecuzioni."

            executions = data.get("data", [])
            if not executions:
                return "[INFO] Nessuna esecuzione recente."

            response = f"🔄 Ultime {len(executions)} Esecuzioni\n\n"
            for idx, exe in enumerate(executions[:limit], 1):
                status_emoji = "✅" if exe.get('status') == "success" else "❌"
                response += f"{idx}. {status_emoji} {exe.get('workflowName', 'N/A')} - {exe.get('status')}\n"
            return response

        elif scope == "by_date":
            if not target:
                return "[ERRORE] Specifica target=date per scope='by_date'"
            # Use DB query for date-specific
            return get_executions_by_date_tool(date=target)

        elif scope == "by_workflow":
            if not target:
                return "[ERRORE] Specifica target=workflow_id per scope='by_workflow'"
            # Call backend API
            data = await call_backend_api(f"/api/business/process-executions/{target}?limit={limit}")
            if "error" in data:
                return f"[ERRORE] Impossibile recuperare executions workflow."

            executions = data.get("data", [])
            response = f"🔄 Esecuzioni Workflow ({len(executions)})\n\n"
            for idx, exe in enumerate(executions, 1):
                response += f"{idx}. {exe.get('status')} - {exe.get('startedAt', '')[:16]}\n"
            return response

        elif scope == "specific":
            if not target:
                return "[ERRORE] Specifica target=execution_id per scope='specific'"
            # Call backend API
            data = await call_backend_api(f"/api/business/execution-status/{target}")
            if "error" in data:
                return f"[ERRORE] Impossibile recuperare execution status."

            exe = data.get("data", {})
            return f"""🔍 Execution {target}

Workflow: {exe.get('workflowName', 'N/A')}
Status: {exe.get('status', 'N/A')}
Started: {exe.get('startedAt', 'N/A')[:19]}
Duration: {exe.get('duration', 0)}ms"""

        else:
            return f"[ERRORE] scope '{scope}' non valido. Usa: recent_all, by_date, by_workflow, specific"

    except Exception as e:
        logger.error(f"Error in smart executions query: {e}")
        return f"[ERRORE] Impossibile recuperare executions: {str(e)}"


# ============================================================================
# BACKWARD COMPATIBILITY WRAPPERS - Per codice legacy che chiama tool vecchi
# ============================================================================

@tool
@traceable(name="MilhenaPerformanceMetricsLegacy", run_type="tool")
def get_performance_metrics_tool(query_type: str = "overview") -> str:
    """LEGACY wrapper → usa smart_analytics_query_tool"""
    import asyncio
    return asyncio.run(smart_analytics_query_tool(metric_type="performance"))


@tool
@traceable(name="MilhenaSystemMonitoringLegacy", run_type="tool")
def get_system_monitoring_tool(query_type: str = "health") -> str:
    """LEGACY wrapper → usa smart_analytics_query_tool"""
    import asyncio
    return asyncio.run(smart_analytics_query_tool(metric_type="integration_health"))


@tool
@traceable(name="MilhenaAnalyticsLegacy", run_type="tool")
def get_analytics_tool(query_type: str = "overview") -> str:
    """LEGACY wrapper → usa smart_analytics_query_tool"""
    import asyncio
    return asyncio.run(smart_analytics_query_tool(metric_type="overview"))


# ============================================================================
# DYNAMIC CONTEXT SYSTEM v3.5.2 - REMOVED (replaced by async query in graph.py)
# ============================================================================
# get_system_context_tool() was removed in v3.5.2 refactoring:
# - Context now injected directly in Classifier prompt via _get_system_context_light()
# - Uses asyncpg pool (graph.py:_load_context_from_db) instead of psycopg2 sync
# - Query only necessary fields (workflows_attivi_list + esecuzioni_7giorni)
# - 89% token reduction (200 vs 1800) + RAM cache (5min TTL)
# - Removed 253 lines: tool + 3 helper functions (_extract_workflow_names, _build_business_dictionary, _build_usage_examples)
# ============================================================================
