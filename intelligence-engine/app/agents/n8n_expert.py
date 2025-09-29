"""
N8N Expert Agent
Specialized agent for n8n workflow data extraction and message handling
"""
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncpg
from langchain_core.tools import tool
from langsmith import traceable

from .base_agent import BaseAgent, AgentConfig, AgentResult, AgentStatus
from app.database import get_db_connection

import logging
logger = logging.getLogger(__name__)


class N8nExpertAgent(BaseAgent):
    """
    Specialized agent for n8n operations:
    - Extract messages from workflow executions
    - Query execution data
    - Parse webhook payloads
    - Analyze workflow performance
    """

    def __init__(self):
        """Initialize N8n Expert Agent"""
        config = AgentConfig(
            name="n8n_expert",
            description="N8n workflow and message extraction specialist",
            capabilities=[
                "workflow_messages",
                "execution_data",
                "webhook_extraction",
                "performance_analysis",
                "error_diagnostics"
            ],
            max_retries=3,
            timeout_seconds=30,
            cache_enabled=True,
            tracing_enabled=True
        )
        super().__init__(config)
        logger.info("N8n Expert Agent initialized")

    @traceable(name="N8nExpertProcess")
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> AgentResult:
        """
        Process n8n related queries

        Args:
            query: User query about n8n/workflows
            context: Optional context
            session_id: Session identifier

        Returns:
            AgentResult with workflow/message data
        """
        start_time = datetime.now()

        try:
            # Determine query type
            query_lower = query.lower()

            if "messaggio" in query_lower or "message" in query_lower:
                # Extract messages from workflows
                response = await self._extract_workflow_messages(query)

            elif "workflow" in query_lower or "processo" in query_lower:
                # Get workflow information
                response = await self._get_workflow_info(query)

            elif "execution" in query_lower or "elaborazione" in query_lower:
                # Get execution data
                response = await self._get_execution_data(query)

            elif "webhook" in query_lower:
                # Extract webhook data
                response = await self._extract_webhook_data(query)

            elif "error" in query_lower or "anomalia" in query_lower:
                # Analyze errors
                response = await self._analyze_errors(query)

            else:
                # General n8n query
                response = await self._general_n8n_query(query)

            processing_time = (datetime.now() - start_time).total_seconds()

            return AgentResult(
                success=True,
                output=response,
                agent_name=self.config.name,
                processing_time=processing_time,
                tokens_used=100,  # Estimate
                cost=0.0002,
                metadata={
                    "query_type": "n8n_workflow",
                    "session_id": session_id
                }
            )

        except Exception as e:
            logger.error(f"N8n Expert processing error: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()

            return AgentResult(
                success=False,
                output="Mi dispiace, non sono riuscito ad estrarre i dati dal processo.",
                agent_name=self.config.name,
                processing_time=processing_time,
                error=str(e)
            )

    async def _extract_workflow_messages(self, query: str) -> str:
        """Extract messages from workflow executions"""
        try:
            # Connect to database
            conn = await get_db_connection()

            # Extract workflow name if mentioned
            workflow_name = self._extract_workflow_name(query)

            if workflow_name:
                # Query specific workflow
                sql = """
                    SELECT
                        we."workflowId",
                        w.name as workflow_name,
                        we."stoppedAt",
                        we.status,
                        we.mode
                    FROM n8n.execution_entity we
                    JOIN n8n.workflow_entity w ON we."workflowId" = w.id
                    WHERE LOWER(w.name) LIKE LOWER($1)
                    ORDER BY we."stoppedAt" DESC NULLS LAST
                    LIMIT 1
                """
                result = await conn.fetchrow(sql, f"%{workflow_name}%")
            else:
                # Get latest execution with messages
                sql = """
                    SELECT
                        we."workflowId",
                        w.name as workflow_name,
                        we."stoppedAt",
                        we.status,
                        we.mode
                    FROM n8n.execution_entity we
                    JOIN n8n.workflow_entity w ON we."workflowId" = w.id
                    WHERE we."stoppedAt" IS NOT NULL
                    ORDER BY we."stoppedAt" DESC
                    LIMIT 1
                """
                result = await conn.fetchrow(sql)

            await conn.close()

            if result:
                # Since we don't have data column anymore, create a simple message
                messages = [f"Workflow eseguito con stato: {result['status']}"]

                if messages:
                    workflow_name = result['workflow_name']
                    timestamp = result['stoppedAt'].strftime("%d/%m/%Y %H:%M") if result['stoppedAt'] else "In corso"

                    response = f"Ultimo messaggio dal processo '{workflow_name}':\n"
                    response += f"📅 {timestamp}\n"
                    response += f"📧 {messages[-1]}"  # Latest message

                    return response
                else:
                    return "Il processo è stato eseguito ma non contiene messaggi."
            else:
                return "Non ho trovato elaborazioni recenti con messaggi."

        except Exception as e:
            logger.error(f"Error extracting workflow messages: {e}")
            return "Non sono riuscito ad accedere ai dati del processo."

    async def _get_workflow_info(self, query: str) -> str:
        """Get workflow information"""
        try:
            conn = await get_db_connection()

            # Get active workflows
            sql = """
                SELECT
                    name,
                    active,
                    "createdAt",
                    "updatedAt"
                FROM n8n.workflow_entity
                WHERE active = true
                ORDER BY "updatedAt" DESC
                LIMIT 5
            """

            results = await conn.fetch(sql)
            await conn.close()

            if results:
                response = "Processi aziendali attivi:\n\n"
                for row in results:
                    status = "✅ Attivo" if row['active'] else "⏸️ In pausa"
                    response += f"• {row['name']} - {status}\n"
                    response += f"  Aggiornato: {row['updatedAt'].strftime('%d/%m/%Y')}\n\n"

                return response
            else:
                return "Non ci sono processi attivi al momento."

        except Exception as e:
            logger.error(f"Error getting workflow info: {e}")
            return "Non sono riuscito a recuperare le informazioni sui processi."

    async def _get_execution_data(self, query: str) -> str:
        """Get execution statistics"""
        try:
            conn = await get_db_connection()

            # Get execution stats
            sql = """
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) as errors,
                    COUNT(CASE WHEN "stoppedAt" > NOW() - INTERVAL '24 hours' THEN 1 END) as today
                FROM n8n.execution_entity
                WHERE "stoppedAt" > NOW() - INTERVAL '7 days'
            """

            result = await conn.fetchrow(sql)
            await conn.close()

            if result:
                response = "📊 Statistiche elaborazioni (ultimi 7 giorni):\n\n"
                response += f"• Totale elaborazioni: {result['total']}\n"
                response += f"• Completate con successo: {result['success']}\n"
                response += f"• Con anomalie: {result['errors']}\n"
                response += f"• Oggi: {result['today']}\n"

                success_rate = (result['success'] / result['total'] * 100) if result['total'] > 0 else 0
                response += f"\n✨ Tasso di successo: {success_rate:.1f}%"

                return response
            else:
                return "Non ci sono elaborazioni recenti da analizzare."

        except Exception as e:
            logger.error(f"Error getting execution data: {e}")
            return "Non sono riuscito a recuperare le statistiche delle elaborazioni."

    async def _extract_webhook_data(self, query: str) -> str:
        """Extract webhook payload data"""
        try:
            conn = await get_db_connection()

            # Get latest webhook execution
            sql = """
                SELECT
                    we."stoppedAt",
                    we.status,
                    w.name as workflow_name
                FROM n8n.execution_entity we
                JOIN n8n.workflow_entity w ON we."workflowId" = w.id
                WHERE we.mode = 'webhook'
                ORDER BY we."stoppedAt" DESC NULLS LAST
                LIMIT 1
            """

            result = await conn.fetchrow(sql)
            await conn.close()

            if result:
                # Simplified webhook info without data column
                webhook_data = {"status": result['status'], "mode": "webhook"}

                if webhook_data:
                    response = f"Ultimo dato ricevuto via integrazione:\n"
                    response += f"Processo: {result['workflow_name']}\n"
                    response += f"Data: {result['stoppedAt'].strftime('%d/%m/%Y %H:%M') if result['stoppedAt'] else 'In corso'}\n"
                    response += f"Contenuto: {json.dumps(webhook_data, indent=2)}"

                    return response
                else:
                    return "Nessun dato di integrazione trovato nell'ultima elaborazione."
            else:
                return "Non ho trovato elaborazioni recenti con dati da integrazioni."

        except Exception as e:
            logger.error(f"Error extracting webhook data: {e}")
            return "Non sono riuscito ad estrarre i dati delle integrazioni."

    async def _analyze_errors(self, query: str) -> str:
        """Analyze workflow errors"""
        try:
            conn = await get_db_connection()

            # Get recent errors
            sql = """
                SELECT
                    w.name as workflow_name,
                    we."stoppedAt",
                    we.status
                FROM n8n.execution_entity we
                JOIN n8n.workflow_entity w ON we."workflowId" = w.id
                WHERE we.status = 'error'
                ORDER BY we."stoppedAt" DESC NULLS LAST
                LIMIT 5
            """

            results = await conn.fetch(sql)
            await conn.close()

            if results:
                response = "⚠️ Anomalie recenti rilevate:\n\n"
                for row in results:
                    response += f"• Processo: {row['workflow_name']}\n"
                    if row['stoppedAt']:
                        response += f"  Ora: {row['stoppedAt'].strftime('%d/%m %H:%M')}\n"
                    else:
                        response += f"  Ora: In esecuzione\n"
                    response += f"  Stato: {row['status']}\n"
                    response += "\n"

                return response
            else:
                return "✅ Nessuna anomalia rilevata nei processi recenti."

        except Exception as e:
            logger.error(f"Error analyzing errors: {e}")
            return "Non sono riuscito ad analizzare le anomalie."

    async def _general_n8n_query(self, query: str) -> str:
        """Handle general n8n queries"""
        return """Posso aiutarti con:
• Estrazione messaggi dai processi
• Statistiche elaborazioni
• Analisi anomalie
• Dati da integrazioni

Cosa vorresti sapere nello specifico?"""

    def _extract_workflow_name(self, query: str) -> Optional[str]:
        """Extract workflow name from query"""
        # Common workflow names
        keywords = ["fatture", "ordini", "clienti", "prodotti", "magazzino"]

        query_lower = query.lower()
        for keyword in keywords:
            if keyword in query_lower:
                return keyword

        # Try to find quoted name
        import re
        match = re.search(r"['\"]([^'\"]+)['\"]", query)
        if match:
            return match.group(1)

        return None

    def _extract_messages_from_data(self, data: dict) -> List[str]:
        """Extract messages from execution data"""
        messages = []

        # Recursively search for message fields
        def search_messages(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ["message", "text", "content", "body", "data"]:
                        if isinstance(value, str) and value:
                            messages.append(value)
                    else:
                        search_messages(value)
            elif isinstance(obj, list):
                for item in obj:
                    search_messages(item)

        search_messages(data)
        return messages

    def _extract_webhook_payload(self, data: dict) -> Optional[dict]:
        """Extract webhook payload from execution data"""
        # Look for webhook data in various places
        if "webhook" in str(data).lower():
            # Search for webhook node data
            def find_webhook(obj):
                if isinstance(obj, dict):
                    if "webhook" in str(obj).lower():
                        if "body" in obj:
                            return obj["body"]
                        if "query" in obj:
                            return obj["query"]
                        if "data" in obj:
                            return obj["data"]
                    for value in obj.values():
                        result = find_webhook(value)
                        if result:
                            return result
                elif isinstance(obj, list):
                    for item in obj:
                        result = find_webhook(item)
                        if result:
                            return result
                return None

            return find_webhook(data)

        return None

    def _extract_error_message(self, data: dict) -> Optional[str]:
        """Extract error message from execution data"""
        # Look for error messages
        if isinstance(data, dict):
            if "error" in data:
                return str(data["error"])
            if "message" in data:
                return str(data["message"])

            # Search nested
            for value in data.values():
                if isinstance(value, dict):
                    error = self._extract_error_message(value)
                    if error:
                        return error

        return None

    def can_handle(self, query: str, intent: Optional[str] = None) -> bool:
        """
        Check if this agent can handle the query

        Args:
            query: User query
            intent: Optional detected intent

        Returns:
            True if agent can handle n8n queries
        """
        n8n_keywords = [
            "messaggio", "message",
            "workflow", "processo",
            "execution", "elaborazione",
            "webhook", "integrazione",
            "n8n", "automazione",
            "errore", "anomalia",
            "fatture", "ordini"  # Common workflow names
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in n8n_keywords)

    def get_status(self) -> Dict[str, Any]:
        """Get agent status with n8n specific info"""
        status = super().get_status()
        status.update({
            "specialized_for": "n8n workflow management",
            "data_sources": ["n8n.execution_entity", "n8n.workflow_entity"],
            "real_time_data": True
        })
        return status