"""
Data Analyst Agent
Specialized agent for data analysis and reporting
"""
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncpg
from langsmith import traceable

from .base_agent import BaseAgent, AgentConfig, AgentResult
from app.database import get_db_connection

import logging
logger = logging.getLogger(__name__)


class DataAnalystAgent(BaseAgent):
    """
    Specialized agent for data analysis:
    - Generate reports and statistics
    - Analyze trends and patterns
    - Create summaries and insights
    - Performance metrics
    """

    def __init__(self):
        """Initialize Data Analyst Agent"""
        config = AgentConfig(
            name="data_analyst",
            description="Data analysis and reporting specialist",
            capabilities=[
                "report_generation",
                "trend_analysis",
                "statistics",
                "performance_metrics",
                "data_visualization",
                "insights_extraction"
            ],
            max_retries=3,
            timeout_seconds=45,
            cache_enabled=True,
            tracing_enabled=True
        )
        super().__init__(config)
        logger.info("Data Analyst Agent initialized")

    @traceable(name="DataAnalystProcess")
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> AgentResult:
        """
        Process data analysis queries

        Args:
            query: User query about data/analysis
            context: Optional context
            session_id: Session identifier

        Returns:
            AgentResult with analysis/report
        """
        start_time = datetime.now()

        try:
            query_lower = query.lower()

            if "report" in query_lower or "analisi" in query_lower:
                # Generate comprehensive report
                response = await self._generate_report(query)

            elif "trend" in query_lower:
                # Analyze trends
                response = await self._analyze_trends(query)

            elif "statistic" in query_lower or "metriche" in query_lower:
                # Get statistics
                response = await self._get_statistics(query)

            elif "performance" in query_lower or "prestazioni" in query_lower:
                # Analyze performance
                response = await self._analyze_performance(query)

            elif "confronta" in query_lower or "compare" in query_lower:
                # Comparative analysis
                response = await self._comparative_analysis(query)

            else:
                # General data query
                response = await self._general_analysis(query)

            processing_time = (datetime.now() - start_time).total_seconds()

            return AgentResult(
                success=True,
                output=response,
                agent_name=self.config.name,
                processing_time=processing_time,
                tokens_used=150,  # Estimate
                cost=0.0003,
                metadata={
                    "query_type": "data_analysis",
                    "session_id": session_id,
                    "data_points_analyzed": 100  # Estimate
                }
            )

        except Exception as e:
            logger.error(f"Data Analyst processing error: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()

            return AgentResult(
                success=False,
                output="Mi dispiace, non sono riuscito a completare l'analisi dei dati.",
                agent_name=self.config.name,
                processing_time=processing_time,
                error=str(e)
            )

    async def _generate_report(self, query: str) -> str:
        """Generate comprehensive report"""
        try:
            conn = await get_db_connection()

            # Determine time period
            period = self._extract_time_period(query)
            start_date = datetime.now() - period

            # Get workflow statistics
            workflow_stats = await self._get_workflow_stats(conn, start_date)

            # Get execution metrics
            execution_metrics = await self._get_execution_metrics(conn, start_date)

            # Get user activity
            user_activity = await self._get_user_activity(conn, start_date)

            await conn.close()

            # Build report
            report = f"""📊 **REPORT ANALITICO COMPLETO**
📅 Periodo: {start_date.strftime('%d/%m/%Y')} - {datetime.now().strftime('%d/%m/%Y')}

**1. PANORAMICA PROCESSI**
{workflow_stats}

**2. METRICHE ELABORAZIONI**
{execution_metrics}

**3. ATTIVITÀ UTENTI**
{user_activity}

**4. RACCOMANDAZIONI**
{self._generate_recommendations(workflow_stats, execution_metrics)}

📈 **Trend generale**: {self._calculate_trend(execution_metrics)}
"""
            return report

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return "Non sono riuscito a generare il report completo."

    async def _analyze_trends(self, query: str) -> str:
        """Analyze data trends"""
        try:
            conn = await get_db_connection()

            # Get daily execution counts for last 30 days
            sql = """
                SELECT
                    DATE(finished) as date,
                    COUNT(*) as executions,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) as errors
                FROM n8n.execution_entity
                WHERE finished > NOW() - INTERVAL '30 days'
                GROUP BY DATE(finished)
                ORDER BY date
            """

            results = await conn.fetch(sql)
            await conn.close()

            if results:
                # Calculate trends
                total_executions = [r['executions'] for r in results]
                avg_daily = sum(total_executions) / len(total_executions)

                # Find peak days
                peak_day = max(results, key=lambda x: x['executions'])

                # Calculate growth
                first_week = sum(r['executions'] for r in results[:7])
                last_week = sum(r['executions'] for r in results[-7:])
                growth = ((last_week - first_week) / first_week * 100) if first_week > 0 else 0

                response = f"""📈 **ANALISI TREND (30 giorni)**

**Volume elaborazioni:**
• Media giornaliera: {avg_daily:.0f} elaborazioni
• Picco massimo: {peak_day['executions']} ({peak_day['date'].strftime('%d/%m')})
• Crescita settimanale: {growth:+.1f}%

**Distribuzione:**
"""
                # Add weekly summary
                for i in range(0, min(len(results), 28), 7):
                    week_data = results[i:i+7]
                    week_total = sum(r['executions'] for r in week_data)
                    week_success = sum(r['success'] for r in week_data)
                    success_rate = (week_success / week_total * 100) if week_total > 0 else 0

                    week_num = i // 7 + 1
                    response += f"\nSettimana {week_num}: {week_total} elaborazioni ({success_rate:.1f}% successo)"

                return response
            else:
                return "Non ci sono dati sufficienti per l'analisi dei trend."

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return "Non sono riuscito ad analizzare i trend."

    async def _get_statistics(self, query: str) -> str:
        """Get detailed statistics"""
        try:
            conn = await get_db_connection()

            # Get overall statistics
            sql = """
                SELECT
                    COUNT(DISTINCT workflow_id) as unique_workflows,
                    COUNT(*) as total_executions,
                    AVG(EXTRACT(EPOCH FROM (finished - started))) as avg_duration,
                    MIN(started) as first_execution,
                    MAX(finished) as last_execution
                FROM n8n.execution_entity
                WHERE finished IS NOT NULL
            """

            stats = await conn.fetchrow(sql)

            # Get workflow-specific stats
            workflow_sql = """
                SELECT
                    w.name,
                    COUNT(e.id) as executions,
                    AVG(EXTRACT(EPOCH FROM (e.finished - e.started))) as avg_duration
                FROM n8n.workflow_entity w
                LEFT JOIN n8n.execution_entity e ON w.id = e.workflow_id
                WHERE w.active = true
                GROUP BY w.name
                ORDER BY executions DESC
                LIMIT 5
            """

            top_workflows = await conn.fetch(workflow_sql)
            await conn.close()

            if stats:
                response = f"""📊 **STATISTICHE SISTEMA**

**Generale:**
• Processi unici: {stats['unique_workflows']}
• Totale elaborazioni: {stats['total_executions']}
• Durata media: {stats['avg_duration']:.1f} secondi
• Prima elaborazione: {stats['first_execution'].strftime('%d/%m/%Y')}
• Ultima elaborazione: {stats['last_execution'].strftime('%d/%m/%Y %H:%M')}

**Top 5 Processi più attivi:**"""

                for wf in top_workflows:
                    response += f"\n• {wf['name']}: {wf['executions']} elaborazioni (media {wf['avg_duration']:.1f}s)"

                return response
            else:
                return "Non ci sono statistiche disponibili."

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return "Non sono riuscito a recuperare le statistiche."

    async def _analyze_performance(self, query: str) -> str:
        """Analyze system performance"""
        try:
            conn = await get_db_connection()

            # Performance metrics
            sql = """
                SELECT
                    AVG(EXTRACT(EPOCH FROM (finished - started))) as avg_duration,
                    MAX(EXTRACT(EPOCH FROM (finished - started))) as max_duration,
                    MIN(EXTRACT(EPOCH FROM (finished - started))) as min_duration,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) as median_duration,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (finished - started))) as p95_duration,
                    COUNT(CASE WHEN status = 'success' THEN 1 END)::FLOAT / COUNT(*) * 100 as success_rate,
                    COUNT(CASE WHEN EXTRACT(EPOCH FROM (finished - started)) > 60 THEN 1 END) as slow_executions
                FROM n8n.execution_entity
                WHERE finished IS NOT NULL
                AND finished > NOW() - INTERVAL '7 days'
            """

            perf = await conn.fetchrow(sql)

            # Get hourly distribution
            hourly_sql = """
                SELECT
                    EXTRACT(HOUR FROM finished) as hour,
                    COUNT(*) as count
                FROM n8n.execution_entity
                WHERE finished > NOW() - INTERVAL '7 days'
                GROUP BY EXTRACT(HOUR FROM finished)
                ORDER BY count DESC
                LIMIT 3
            """

            peak_hours = await conn.fetch(hourly_sql)
            await conn.close()

            if perf:
                response = f"""⚡ **ANALISI PERFORMANCE (ultimi 7 giorni)**

**Tempi di elaborazione:**
• Media: {perf['avg_duration']:.1f} secondi
• Mediana: {perf['median_duration']:.1f} secondi
• Minimo: {perf['min_duration']:.1f} secondi
• Massimo: {perf['max_duration']:.1f} secondi
• 95° percentile: {perf['p95_duration']:.1f} secondi

**Qualità:**
• Tasso di successo: {perf['success_rate']:.1f}%
• Elaborazioni lente (>60s): {perf['slow_executions']}

**Ore di punta:**"""

                for hour in peak_hours:
                    response += f"\n• {int(hour['hour'])}:00 - {hour['count']} elaborazioni"

                # Performance assessment
                if perf['success_rate'] > 95:
                    response += "\n\n✅ **Valutazione**: Performance eccellente"
                elif perf['success_rate'] > 90:
                    response += "\n\n👍 **Valutazione**: Performance buona"
                else:
                    response += "\n\n⚠️ **Valutazione**: Performance da migliorare"

                return response
            else:
                return "Non ci sono dati di performance disponibili."

        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
            return "Non sono riuscito ad analizzare le performance."

    async def _comparative_analysis(self, query: str) -> str:
        """Perform comparative analysis"""
        try:
            conn = await get_db_connection()

            # Compare this week vs last week
            sql = """
                WITH this_week AS (
                    SELECT
                        COUNT(*) as executions,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
                        AVG(EXTRACT(EPOCH FROM (finished - started))) as avg_duration
                    FROM n8n.execution_entity
                    WHERE finished > NOW() - INTERVAL '7 days'
                ),
                last_week AS (
                    SELECT
                        COUNT(*) as executions,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
                        AVG(EXTRACT(EPOCH FROM (finished - started))) as avg_duration
                    FROM n8n.execution_entity
                    WHERE finished > NOW() - INTERVAL '14 days'
                    AND finished <= NOW() - INTERVAL '7 days'
                )
                SELECT
                    tw.executions as tw_exec,
                    lw.executions as lw_exec,
                    tw.success as tw_success,
                    lw.success as lw_success,
                    tw.avg_duration as tw_duration,
                    lw.avg_duration as lw_duration
                FROM this_week tw, last_week lw
            """

            result = await conn.fetchrow(sql)
            await conn.close()

            if result:
                # Calculate changes
                exec_change = ((result['tw_exec'] - result['lw_exec']) / result['lw_exec'] * 100) if result['lw_exec'] > 0 else 0
                success_rate_tw = (result['tw_success'] / result['tw_exec'] * 100) if result['tw_exec'] > 0 else 0
                success_rate_lw = (result['lw_success'] / result['lw_exec'] * 100) if result['lw_exec'] > 0 else 0
                success_change = success_rate_tw - success_rate_lw
                duration_change = ((result['tw_duration'] - result['lw_duration']) / result['lw_duration'] * 100) if result['lw_duration'] else 0

                response = f"""📊 **ANALISI COMPARATIVA (settimana corrente vs precedente)**

**Volume elaborazioni:**
• Settimana corrente: {result['tw_exec']}
• Settimana precedente: {result['lw_exec']}
• Variazione: {exec_change:+.1f}% {self._get_trend_emoji(exec_change)}

**Tasso di successo:**
• Settimana corrente: {success_rate_tw:.1f}%
• Settimana precedente: {success_rate_lw:.1f}%
• Variazione: {success_change:+.1f}% {self._get_trend_emoji(success_change)}

**Tempo medio elaborazione:**
• Settimana corrente: {result['tw_duration']:.1f}s
• Settimana precedente: {result['lw_duration']:.1f}s
• Variazione: {duration_change:+.1f}% {self._get_trend_emoji(-duration_change)}

**Valutazione complessiva:** {self._get_overall_assessment(exec_change, success_change, duration_change)}
"""
                return response
            else:
                return "Non ci sono dati sufficienti per l'analisi comparativa."

        except Exception as e:
            logger.error(f"Error in comparative analysis: {e}")
            return "Non sono riuscito a completare l'analisi comparativa."

    async def _general_analysis(self, query: str) -> str:
        """Handle general analysis queries"""
        return """Posso aiutarti con:
• 📊 Report dettagliati
• 📈 Analisi dei trend
• 📉 Statistiche complete
• ⚡ Analisi performance
• 🔄 Confronti temporali

Cosa vorresti analizzare nello specifico?"""

    async def _get_workflow_stats(self, conn, start_date: datetime) -> str:
        """Get workflow statistics for report"""
        sql = """
            SELECT
                COUNT(DISTINCT w.id) as total_workflows,
                COUNT(DISTINCT CASE WHEN w.active = true THEN w.id END) as active_workflows,
                COUNT(e.id) as total_executions
            FROM n8n.workflow_entity w
            LEFT JOIN n8n.execution_entity e ON w.id = e.workflow_id AND e.finished > $1
        """
        result = await conn.fetchrow(sql, start_date)

        return f"""• Processi totali: {result['total_workflows']}
• Processi attivi: {result['active_workflows']}
• Elaborazioni nel periodo: {result['total_executions']}"""

    async def _get_execution_metrics(self, conn, start_date: datetime) -> str:
        """Get execution metrics for report"""
        sql = """
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
                COUNT(CASE WHEN status = 'error' THEN 1 END) as errors,
                AVG(EXTRACT(EPOCH FROM (finished - started))) as avg_duration
            FROM n8n.execution_entity
            WHERE finished > $1
        """
        result = await conn.fetchrow(sql, start_date)

        success_rate = (result['success'] / result['total'] * 100) if result['total'] > 0 else 0

        return f"""• Totale elaborazioni: {result['total']}
• Successi: {result['success']} ({success_rate:.1f}%)
• Errori: {result['errors']}
• Durata media: {result['avg_duration']:.1f} secondi"""

    async def _get_user_activity(self, conn, start_date: datetime) -> str:
        """Get user activity for report"""
        sql = """
            SELECT COUNT(DISTINCT session_id) as sessions
            FROM users.sessions
            WHERE created_at > $1
        """
        result = await conn.fetchrow(sql, start_date)

        return f"• Sessioni attive: {result['sessions'] if result else 0}"

    def _generate_recommendations(self, workflow_stats: str, execution_metrics: str) -> str:
        """Generate recommendations based on analysis"""
        recommendations = []

        # Parse success rate from execution metrics
        import re
        success_match = re.search(r'Successi:.*\((\d+\.\d+)%\)', execution_metrics)
        if success_match:
            success_rate = float(success_match.group(1))
            if success_rate < 90:
                recommendations.append("⚠️ Tasso di successo sotto il 90% - verificare configurazioni")
            elif success_rate > 95:
                recommendations.append("✅ Tasso di successo eccellente")

        # Parse duration
        duration_match = re.search(r'Durata media: (\d+\.\d+)', execution_metrics)
        if duration_match:
            avg_duration = float(duration_match.group(1))
            if avg_duration > 30:
                recommendations.append("⏱️ Tempi di elaborazione elevati - considerare ottimizzazione")

        return "\n".join(recommendations) if recommendations else "✅ Sistema in condizioni ottimali"

    def _calculate_trend(self, execution_metrics: str) -> str:
        """Calculate overall trend"""
        # Simple trend calculation based on metrics
        if "Successi" in execution_metrics:
            return "📈 Positivo"
        return "📊 Stabile"

    def _extract_time_period(self, query: str) -> timedelta:
        """Extract time period from query"""
        query_lower = query.lower()

        if "oggi" in query_lower or "today" in query_lower:
            return timedelta(days=1)
        elif "settimana" in query_lower or "week" in query_lower:
            return timedelta(days=7)
        elif "mese" in query_lower or "month" in query_lower:
            return timedelta(days=30)
        elif "anno" in query_lower or "year" in query_lower:
            return timedelta(days=365)
        else:
            return timedelta(days=7)  # Default to last week

    def _get_trend_emoji(self, change: float) -> str:
        """Get emoji for trend"""
        if change > 10:
            return "📈"
        elif change > 0:
            return "↗️"
        elif change < -10:
            return "📉"
        elif change < 0:
            return "↘️"
        else:
            return "➡️"

    def _get_overall_assessment(self, exec_change: float, success_change: float, duration_change: float) -> str:
        """Get overall assessment"""
        score = 0

        if exec_change > 0:
            score += 1
        if success_change > 0:
            score += 2
        if duration_change < 0:  # Lower duration is better
            score += 1

        if score >= 3:
            return "🎯 Miglioramento significativo"
        elif score >= 2:
            return "👍 Andamento positivo"
        elif score >= 1:
            return "📊 Andamento stabile"
        else:
            return "⚠️ Richiede attenzione"

    def can_handle(self, query: str, intent: Optional[str] = None) -> bool:
        """
        Check if this agent can handle the query

        Args:
            query: User query
            intent: Optional detected intent

        Returns:
            True if agent can handle analysis queries
        """
        analysis_keywords = [
            "analisi", "analyze", "analysis",
            "report", "rapporto",
            "statistic", "metriche", "metrics",
            "trend", "andamento",
            "performance", "prestazioni",
            "confronta", "compare",
            "dati", "data",
            "grafico", "chart"
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in analysis_keywords)

    def get_status(self) -> Dict[str, Any]:
        """Get agent status with analysis specific info"""
        status = super().get_status()
        status.update({
            "specialized_for": "data analysis and reporting",
            "analysis_types": [
                "trend_analysis",
                "performance_metrics",
                "comparative_analysis",
                "statistical_reports"
            ],
            "real_time_analysis": True
        })
        return status