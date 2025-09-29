"""
Enhanced Milhena Agent
Business assistant with n8n expertise and full system knowledge
"""
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncpg
from langsmith import traceable

from .base_agent import BaseAgent, AgentConfig, AgentResult
from app.database import get_db_connection

import logging
logger = logging.getLogger(__name__)


class EnhancedMilhenaAgent(BaseAgent):
    """
    Enhanced Milhena - The main business assistant
    Handles greetings, status queries, and general business assistance
    with deep knowledge of n8n workflows and system operations
    """

    def __init__(self):
        """Initialize Enhanced Milhena Agent"""
        config = AgentConfig(
            name="milhena",
            description="Enhanced business assistant with system expertise",
            capabilities=[
                "greeting",
                "status_check",
                "general_assistance",
                "workflow_knowledge",
                "business_guidance",
                "system_overview"
            ],
            max_retries=3,
            timeout_seconds=20,
            cache_enabled=True,
            tracing_enabled=True
        )
        super().__init__(config)
        self.greeting_cache = {}
        logger.info("Enhanced Milhena Agent initialized")

    @traceable(name="EnhancedMilhenaProcess")
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> AgentResult:
        """
        Process user queries with enhanced business intelligence

        Args:
            query: User query
            context: Optional context from previous interactions
            session_id: Session identifier for continuity

        Returns:
            AgentResult with business-friendly response
        """
        start_time = datetime.now()

        try:
            query_lower = query.lower()

            # Determine query type and respond accordingly
            if self._is_greeting(query_lower):
                response = await self._handle_greeting(query, session_id)

            elif self._is_status_query(query_lower):
                response = await self._handle_status_query()

            elif self._is_help_query(query_lower):
                response = await self._handle_help_query()

            elif "processo" in query_lower or "elaborazione" in query_lower:
                response = await self._handle_process_query(query)

            elif self._is_farewell(query_lower):
                response = await self._handle_farewell(session_id)

            else:
                # General assistance
                response = await self._provide_general_assistance(query, context)

            processing_time = (datetime.now() - start_time).total_seconds()

            return AgentResult(
                success=True,
                output=response,
                agent_name=self.config.name,
                processing_time=processing_time,
                tokens_used=50,  # Estimate
                cost=0.0001,
                metadata={
                    "query_type": self._classify_query(query_lower),
                    "session_id": session_id,
                    "enhanced": True
                }
            )

        except Exception as e:
            logger.error(f"Enhanced Milhena processing error: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()

            return AgentResult(
                success=False,
                output=self._get_error_response(),
                agent_name=self.config.name,
                processing_time=processing_time,
                error=str(e)
            )

    async def _handle_greeting(self, query: str, session_id: Optional[str]) -> str:
        """Handle greetings with personalization"""
        hour = datetime.now().hour

        # Time-based greeting
        if hour < 12:
            time_greeting = "Buongiorno"
        elif hour < 18:
            time_greeting = "Buon pomeriggio"
        else:
            time_greeting = "Buonasera"

        # Check if returning user
        if session_id and session_id in self.greeting_cache:
            return f"{time_greeting}! Ben tornato! Come posso assisterti oggi?"

        # Store greeting
        if session_id:
            self.greeting_cache[session_id] = datetime.now()

        responses = [
            f"{time_greeting}! Sono Milhena, il tuo assistente aziendale intelligente. Come posso aiutarti oggi?",
            f"{time_greeting}! Benvenuto nel sistema PilotProOS. Sono qui per guidarti nei processi aziendali.",
            f"{time_greeting}! Sono Milhena, pronta ad assisterti con i tuoi processi e le tue attività."
        ]

        # Return varied response
        import random
        return random.choice(responses)

    async def _handle_status_query(self) -> str:
        """Handle system status queries with real data"""
        try:
            conn = await get_db_connection()

            # Get system metrics
            workflow_count = await conn.fetchval(
                "SELECT COUNT(*) FROM n8n.workflow_entity WHERE active = true"
            )

            recent_executions = await conn.fetchval(
                """SELECT COUNT(*) FROM n8n.execution_entity
                   WHERE \"stoppedAt\" > NOW() - INTERVAL '1 hour'"""
            )

            last_error = await conn.fetchrow(
                """SELECT \"stoppedAt\", \"workflowId\" FROM n8n.execution_entity
                   WHERE status = 'error'
                   ORDER BY \"stoppedAt\" DESC NULLS LAST LIMIT 1"""
            )

            active_sessions = await conn.fetchval(
                """SELECT COUNT(*) FROM users.sessions
                   WHERE expires_at > NOW()"""
            )

            await conn.close()

            # Build status response
            status_emoji = "🟢" if recent_executions > 0 else "🟡"

            response = f"""{status_emoji} **STATO SISTEMA PILOTPRO**

**Operatività:**
• Processi attivi: {workflow_count}
• Elaborazioni ultima ora: {recent_executions}
• Sessioni utente attive: {active_sessions if active_sessions else 0}

**Salute sistema:**
• Database: ✅ Operativo
• Automazione: ✅ Attiva
• Intelligenza: ✅ Online"""

            if last_error and last_error['stoppedAt']:
                time_diff = datetime.now() - last_error['stoppedAt'].replace(tzinfo=None)
                hours_ago = time_diff.total_seconds() / 3600
                if hours_ago < 1:
                    response += f"\n\n⚠️ Ultima anomalia: {int(time_diff.total_seconds() / 60)} minuti fa"

            else:
                response += "\n\n✨ Nessuna anomalia recente rilevata."

            return response

        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return """🟢 Sistema operativo e pronto all'uso.

Tutti i servizi principali sono attivi. Se hai bisogno di assistenza specifica, sono qui per aiutarti!"""

    async def _handle_help_query(self) -> str:
        """Provide help and guidance"""
        return """🎯 **COME POSSO AIUTARTI**

Sono Milhena, il tuo assistente intelligente per PilotProOS. Posso assisterti con:

**📊 Processi Aziendali:**
• Monitoraggio elaborazioni
• Estrazione messaggi
• Verifica stato processi

**📈 Analisi e Report:**
• Statistiche performance
• Trend e andamenti
• Report personalizzati

**🔧 Assistenza Sistema:**
• Stato operativo
• Risoluzione anomalie
• Guida all'utilizzo

**💡 Esempi di richieste:**
• "Mostra l'ultimo messaggio del processo Fatture"
• "Come va il sistema oggi?"
• "Genera un report settimanale"
• "Analizza le performance degli ultimi giorni"

Cosa vorresti fare? Descrivimi la tua necessità e ti guiderò!"""

    async def _handle_process_query(self, query: str) -> str:
        """Handle queries about processes/workflows"""
        try:
            conn = await get_db_connection()

            # Get workflow information
            workflows = await conn.fetch(
                """SELECT name, active, \"updatedAt\"
                   FROM n8n.workflow_entity
                   WHERE active = true
                   ORDER BY \"updatedAt\" DESC
                   LIMIT 5"""
            )

            await conn.close()

            if workflows:
                response = "📋 **I TUOI PROCESSI AZIENDALI**\n\n"
                for wf in workflows:
                    status = "✅" if wf['active'] else "⏸️"
                    response += f"{status} **{wf['name']}**\n"
                    response += f"   Ultimo aggiornamento: {wf['updatedAt'].strftime('%d/%m/%Y')}\n\n"

                response += "\n💡 *Per dettagli su un processo specifico, chiedi: 'Mostra dettagli processo [nome]'*"
                return response
            else:
                return "Non ho trovato processi attivi. Vuoi che ti aiuti a configurarne uno nuovo?"

        except Exception as e:
            logger.error(f"Error handling process query: {e}")
            return """Posso aiutarti con i processi aziendali.

Per informazioni specifiche, prova a chiedere:
• "Mostra i processi attivi"
• "Stato del processo Fatture"
• "Ultime elaborazioni"

Come posso assisterti?"""

    async def _handle_farewell(self, session_id: Optional[str]) -> str:
        """Handle farewell messages"""
        # Clean session cache if exists
        if session_id and session_id in self.greeting_cache:
            del self.greeting_cache[session_id]

        farewells = [
            "Arrivederci! È stato un piacere assisterti. A presto! 👋",
            "Buona giornata! Sono sempre qui quando hai bisogno. 🌟",
            "A presto! Ricorda che sono disponibile 24/7 per le tue necessità aziendali. 💼"
        ]

        import random
        return random.choice(farewells)

    async def _provide_general_assistance(self, query: str, context: Optional[Dict]) -> str:
        """Provide general assistance based on query"""
        # Check context for conversation continuity
        if context and "previous_queries" in context:
            return f"""Capisco che hai bisogno di assistenza con: "{query}"

Basandomi sulla nostra conversazione, posso suggerirti di:
1. Verificare lo stato dei processi attivi
2. Consultare i report più recenti
3. Analizzare eventuali anomalie

Quale di queste opzioni preferisci approfondire?"""

        # Default assistance
        return f"""Ho ricevuto la tua richiesta: "{query}"

Per assisterti al meglio, potrei:
• Mostrarti lo stato attuale del sistema
• Cercare informazioni sui processi correlati
• Generare un'analisi specifica

Cosa preferisci che faccia?"""

    def _is_greeting(self, query_lower: str) -> bool:
        """Check if query is a greeting"""
        greetings = [
            "ciao", "buongiorno", "buonasera", "buon pomeriggio",
            "salve", "hello", "hi", "hey", "buondì", "saluti"
        ]
        return any(greeting in query_lower for greeting in greetings)

    def _is_status_query(self, query_lower: str) -> bool:
        """Check if query is asking for status"""
        status_keywords = [
            "stato", "status", "come va", "come stai",
            "sistema", "operativo", "funziona", "attivo"
        ]
        return any(keyword in query_lower for keyword in status_keywords)

    def _is_help_query(self, query_lower: str) -> bool:
        """Check if query is asking for help"""
        help_keywords = [
            "aiuto", "help", "cosa puoi fare", "come funziona",
            "guida", "assistenza", "capabilities", "funzioni"
        ]
        return any(keyword in query_lower for keyword in help_keywords)

    def _is_farewell(self, query_lower: str) -> bool:
        """Check if query is a farewell"""
        farewells = [
            "arrivederci", "ciao ciao", "bye", "goodbye",
            "a presto", "buonanotte", "ci vediamo"
        ]
        return any(farewell in query_lower for farewell in farewells)

    def _classify_query(self, query_lower: str) -> str:
        """Classify the query type"""
        if self._is_greeting(query_lower):
            return "greeting"
        elif self._is_status_query(query_lower):
            return "status"
        elif self._is_help_query(query_lower):
            return "help"
        elif self._is_farewell(query_lower):
            return "farewell"
        elif "processo" in query_lower or "workflow" in query_lower:
            return "process"
        elif "messaggio" in query_lower:
            return "message"
        elif "report" in query_lower or "analisi" in query_lower:
            return "analysis"
        else:
            return "general"

    def _get_error_response(self) -> str:
        """Get user-friendly error response"""
        return """Mi dispiace, ho incontrato una difficoltà temporanea.

Riprova tra qualche istante, o se il problema persiste, prova a riformulare la richiesta.

Sono sempre qui per assisterti! 💫"""

    def can_handle(self, query: str, intent: Optional[str] = None) -> bool:
        """
        Check if Milhena can handle the query
        As the primary agent, Milhena can handle most general queries

        Args:
            query: User query
            intent: Optional detected intent

        Returns:
            True for most queries (primary agent)
        """
        # Milhena is the default agent and can handle most queries
        # Only specific technical queries should go to specialized agents

        query_lower = query.lower()

        # Definitely handle greetings and general queries
        if self._is_greeting(query_lower):
            return True
        if self._is_status_query(query_lower):
            return True
        if self._is_help_query(query_lower):
            return True
        if self._is_farewell(query_lower):
            return True

        # Handle if no specific technical terms
        technical_terms = [
            "sql", "database", "query",
            "webhook", "api",
            "analisi dettagliata", "report completo",
            "trend analysis", "performance metrics"
        ]

        has_technical = any(term in query_lower for term in technical_terms)

        # Milhena handles non-technical queries
        return not has_technical

    def get_status(self) -> Dict[str, Any]:
        """Get agent status with Milhena specific info"""
        status = super().get_status()
        status.update({
            "role": "Primary Business Assistant",
            "personality": "Friendly, Professional, Knowledgeable",
            "languages": ["Italian", "English"],
            "cache_size": len(self.greeting_cache),
            "enhanced_features": True
        })
        return status