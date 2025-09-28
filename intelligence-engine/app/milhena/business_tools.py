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
                emoji = "🟢" if r[3] >= 90 else "🟡" if r[3] >= 70 else "🔴"
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
                response = "**⚠️ Processi che richiedono attenzione:**\n"
                for r in results:
                    issues = []
                    if r[1] > 0:
                        issues.append(f"{r[1]} errori")
                    if r[2] > 0:
                        issues.append(f"{r[2]} esecuzioni lente (>10s)")
                    response += f"- {r[0]}: {', '.join(issues)} (media: {r[3]:.1f}s)\n"
            else:
                response = "✅ Nessun collo di bottiglia identificato"

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
            health_status = "🟢 Ottimale" if error_rate < 5 else "🟡 Attenzione" if error_rate < 20 else "🔴 Critico"

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
                alerts.append(f"⚠️ {stuck[0]} esecuzioni bloccate da oltre 30 minuti")

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
                alerts.append(f"🔴 Alto tasso errori: {recent[1]}/{recent[0]} nell'ultima ora")

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
                alerts.append(f"❌ '{f[0]}' ha {f[1]} errori consecutivi")

            response = "**Alert Sistema:**\n" + "\n".join(alerts) if alerts else "✅ Nessun alert attivo"

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
- SLA: {'✅ Rispettato' if uptime >= 99 else '⚠️ Sotto target' if uptime >= 95 else '🔴 Critico'}"""

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
    Get business analytics and reports.

    Args:
        query_type: "summary", "comparison", "roi", "patterns", "forecast"

    Returns:
        Business analytics insights
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