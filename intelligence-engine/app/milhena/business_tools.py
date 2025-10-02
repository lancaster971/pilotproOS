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
    Get workflow information from n8n.

    Args:
        query_type: "active", "inactive", "all", "top_used", "complex", "recent", "errors"

    Returns:
        Workflow information formatted for business users
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

            response = f"""**📊 Report Automazione:**

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
    Get detailed information about a specific workflow/process.

    Args:
        workflow_name: Name of the workflow to get details for

    Returns:
        Detailed workflow information including execution history and status
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

**📊 Statistiche Esecuzioni:**
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

        conn.close()
        return response

    except Exception as e:
        return f"Errore recupero dettagli processo: {str(e)}"


@tool
@traceable(name="MilhenaAllErrors", run_type="tool")
def get_all_errors_summary_tool(hours: int = 24) -> str:
    """
    Get summary of ALL workflows that had errors (no details, just list).

    Use this when user asks general questions:
    - "che errori abbiamo oggi?"
    - "quali processi hanno avuto problemi?"
    - "ci sono errori?"

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

    IMPORTANT: workflow_name is REQUIRED! If user mentions a workflow name in previous messages,
    extract it from conversation history.

    Use this when user asks:
    - "che errore ha il processo X?" → workflow_name="X"
    - "spiegami l'errore di X" → workflow_name="X"
    - "perché è fallito X?" → workflow_name="X"
    - "che tipo di errore è?" (follow-up to previous error message) → extract name from history

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

        response = f"[ERRORE] **Errori per '{errors[0][0]}'** (ultime {hours}h):\n\n"

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
        # Parse date (support both DD/MM/YY and DD/MM/YYYY)
        date_parts = date.split('/')
        if len(date_parts) == 3:
            day, month, year = date_parts
            # Convert 2-digit year to 4-digit
            if len(year) == 2:
                year = f"20{year}"

            # PostgreSQL date format: YYYY-MM-DD
            pg_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        else:
            return f"[AVVISO] Formato data non valido. Usa DD/MM/YYYY o DD/MM/YY (es: 29/09/25)"

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
    Search the knowledge base for information about processes, system features, and procedures.

    Use this when:
    - User asks "what does process X do?"
    - User asks "how do I...?"
    - User needs business/operational information
    - Database tools only return technical data

    Args:
        query: Search query (process name, feature name, or question)
        top_k: Number of results to return (default 3)

    Returns:
        Business-friendly information from knowledge base
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