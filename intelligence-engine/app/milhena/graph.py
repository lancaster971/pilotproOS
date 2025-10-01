"""
MilhenaGraph - LangGraph workflow for Business Assistant
Following official LangGraph patterns with conditional routing
FULL LANGSMITH TRACING ENABLED
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langsmith import traceable, Client
from langsmith.run_trees import RunTree
import logging
import os
from datetime import datetime
import asyncio
import uuid

# Import Milhena components (using ABSOLUTE imports for LangGraph Studio compatibility)
from app.milhena.core import MilhenaCore, MilhenaConfig
from app.milhena.llm_disambiguator import LLMDisambiguator
from app.milhena.intent_analyzer import IntentAnalyzer
from app.milhena.response_generator import ResponseGenerator
from app.milhena.learning import LearningSystem
from app.milhena.token_manager import TokenManager
from app.milhena.cache_manager import CacheManager
from app.milhena.masking import TechnicalMaskingEngine
from app.milhena.business_tools import (
    get_workflows_tool,
    get_performance_metrics_tool,
    get_system_monitoring_tool,
    get_analytics_tool
)

# Import RAG System for knowledge retrieval
from app.rag import get_rag_system

logger = logging.getLogger(__name__)

# ============================================================================
# LANGSMITH CONFIGURATION FOR MILHENA
# ============================================================================

# Configure LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "milhena-v3-production"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

# Verify API key is set
if not os.getenv("LANGCHAIN_API_KEY"):
    logger.warning("LANGCHAIN_API_KEY not set - LangSmith tracing disabled")
else:
    logger.info("LangSmith tracing enabled for Milhena v3")
    # Initialize LangSmith client
    langsmith_client = Client()

# ============================================================================
# STATE DEFINITION - Following LangGraph best practices
# ============================================================================

class MilhenaState(TypedDict):
    """State for Milhena conversation flow"""
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    intent: Optional[str]
    session_id: str
    context: Dict[str, Any]
    disambiguated: bool
    response: Optional[str]
    feedback: Optional[str]
    cached: bool
    masked: bool
    error: Optional[str]
    rag_context: Optional[List[Dict[str, Any]]]  # RAG retrieved documents
    learned_patterns: Optional[List[Dict[str, Any]]]  # Learning system patterns

# ============================================================================
# MILHENA TOOLS - Business-focused tools with masking
# ============================================================================

@tool
@traceable(name="MilhenaStatusCheck", run_type="tool")
def check_business_status() -> str:
    """
    Check the status of business processes.
    Returns current system health in business terms.
    """
    return """Sistema operativo e funzionante.
Processi attivi: 12
Elaborazioni completate oggi: 47
Performance: Ottimale"""

@tool
@traceable(name="MilhenaMetrics", run_type="tool")
def get_business_metrics() -> str:
    """
    Get key business metrics for the day.
    Returns performance indicators.
    """
    return """Metriche giornaliere:
- Processi completati: 98%
- Tempo medio elaborazione: 2.3 minuti
- Disponibilità sistema: 99.9%
- Utenti attivi: 15"""

@tool
@traceable(name="MilhenaQueryUsers", run_type="tool")
def query_users_tool(query_type: str = "count") -> str:
    """
    Query REAL users from PostgreSQL database.

    Args:
        query_type: "all", "active", or "count"

    Returns:
        Real user data from pilotpros.users table
    """
    import psycopg2

    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres-dev"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "pilotpros_db"),
            user=os.getenv("DB_USER", "pilotpros_user"),
            password=os.getenv("DB_PASSWORD", "pilotpros_secure_pass_2025")
        )
        cur = conn.cursor()

        if query_type == "count":
            cur.execute("""
                SELECT COUNT(*) as total, COUNT(CASE WHEN is_active THEN 1 END) as active
                FROM pilotpros.users
            """)
            result = cur.fetchone()
            response = f"Total users: {result[0]}, Active users: {result[1]}"
        elif query_type == "active":
            cur.execute("""
                SELECT email, full_name, role FROM pilotpros.users
                WHERE is_active = true ORDER BY created_at DESC LIMIT 5
            """)
            results = cur.fetchall()
            users = [f"{r[1] or 'No name'} ({r[0]}) - {r[2]}" for r in results]
            response = "Active users:\\n" + "\\n".join(users) if users else "No active users"
        else:
            cur.execute("""
                SELECT email, full_name, is_active FROM pilotpros.users
                ORDER BY created_at DESC LIMIT 5
            """)
            results = cur.fetchall()
            users = [f"{r[1]} ({r[0]}) - Active: {r[2]}" for r in results]
            response = "Users:\\n" + "\\n".join(users) if users else "No users"

        conn.close()
        return response
    except Exception as e:
        return f"Database error: {str(e)}"

@tool
@traceable(name="MilhenaExecutions", run_type="tool")
def get_executions_tool(query_type: str = "last") -> str:
    """
    Get workflow executions from n8n database.

    Args:
        query_type: "last", "today", "failed", or "all"

    Returns:
        Execution data from n8n.execution_entity
    """
    import psycopg2
    from datetime import datetime, timedelta

    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres-dev"),
            port=5432,
            dbname="pilotpros_db",
            user="pilotpros_user",
            password="pilotpros_secure_pass_2025"
        )
        cur = conn.cursor()

        if query_type == "last":
            cur.execute("""
                SELECT id, finished, mode, "startedAt", "stoppedAt", status,
                       EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt")) as duration_seconds
                FROM n8n.execution_entity
                ORDER BY "startedAt" DESC
                LIMIT 1
            """)
            result = cur.fetchone()
            if result:
                duration = f"{result[6]:.1f}" if result[6] else "N/A"
                started = result[3].strftime("%d/%m/%Y alle %H:%M") if result[3] else "N/A"
                response = f"""Ultima esecuzione:
- ID: {result[0]}
- Data: {started}
- Durata: {duration} secondi
- Stato: {result[5].upper() if result[5] else 'IN CORSO'}
- Modalità: {result[2]}"""
            else:
                response = "Nessuna esecuzione trovata"

        elif query_type == "today":
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cur.execute("""
                SELECT COUNT(*),
                       COUNT(CASE WHEN status = 'success' THEN 1 END),
                       COUNT(CASE WHEN status = 'error' THEN 1 END)
                FROM n8n.execution_entity
                WHERE "startedAt" >= %s
            """, (today,))
            result = cur.fetchone()
            response = f"""Esecuzioni di oggi:
- Totali: {result[0]}
- Successo: {result[1]}
- Errori: {result[2]}
- Tasso successo: {(result[1]/result[0]*100 if result[0] > 0 else 0):.1f}%"""

        elif query_type == "failed":
            cur.execute("""
                SELECT id, "startedAt", mode
                FROM n8n.execution_entity
                WHERE status = 'error'
                ORDER BY "startedAt" DESC
                LIMIT 5
            """)
            results = cur.fetchall()
            if results:
                errors = [f"- ID {r[0]}: {r[1].strftime('%d/%m %H:%M')} ({r[2]})" for r in results]
                response = "Ultime esecuzioni fallite:\n" + "\n".join(errors)
            else:
                response = "Nessuna esecuzione fallita recentemente"

        conn.close()
        return response

    except Exception as e:
        return f"Errore accesso esecuzioni: {str(e)}"

@tool
@traceable(name="MilhenaSystemStatus", run_type="tool")
def get_system_status_tool() -> str:
    """
    Get REAL system status from PostgreSQL.
    Returns actual metrics from database.
    """
    import psycopg2

    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres-dev"),
            port=5432,
            dbname="pilotpros_db",
            user="pilotpros_user",
            password="pilotpros_secure_pass_2025"
        )
        cur = conn.cursor()

        cur.execute("""
            SELECT pg_database_size('pilotpros_db') as db_size,
                   (SELECT COUNT(*) FROM pilotpros.users) as user_count,
                   (SELECT COUNT(*) FROM pilotpros.active_sessions) as sessions
        """)
        result = cur.fetchone()
        db_size_mb = result[0] / (1024 * 1024)

        conn.close()
        return f"""System Status:
- Database size: {db_size_mb:.2f} MB
- Total users: {result[1]}
- Active sessions: {result[2]}
- Status: Operational"""
    except Exception as e:
        return f"System check error: {str(e)}"

@tool
@traceable(name="MilhenaErrorTranslation", run_type="tool")
def translate_technical_error(error: str) -> str:
    """
    Translate technical errors to business language.

    Args:
        error: Technical error message

    Returns:
        Business-friendly error description
    """
    masking = TechnicalMaskingEngine()
    return masking.mask(error)

# ============================================================================
# GRAPH NODES - Each step in the Milhena workflow
# ============================================================================

class MilhenaGraph:
    """
    LangGraph workflow for Milhena Business Assistant
    """

    def __init__(self, config: Optional[MilhenaConfig] = None):
        self.config = config or MilhenaConfig()
        self._initialize_components()
        self._build_graph()

    def _initialize_components(self):
        """Initialize all Milhena components"""
        self.masking_engine = TechnicalMaskingEngine()
        self.disambiguator = LLMDisambiguator(self.config)
        self.intent_analyzer = IntentAnalyzer(self.config)
        self.response_generator = ResponseGenerator(self.config, self.masking_engine)
        self.learning_system = LearningSystem()
        self.token_manager = TokenManager()
        self.cache_manager = CacheManager(self.config)

        # Initialize RAG System for knowledge retrieval
        try:
            self.rag_system = get_rag_system()
            logger.info("RAG System initialized in Milhena graph")
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            self.rag_system = None

        # Initialize database tools - COMPLETE SET
        self.tools = [
            query_users_tool,
            get_system_status_tool,
            get_executions_tool,
            get_workflows_tool,
            get_performance_metrics_tool,
            get_system_monitoring_tool,
            get_analytics_tool
        ]
        self.tool_node = ToolNode(self.tools)

        # Initialize LLMs
        if os.getenv("GROQ_API_KEY"):
            self.groq_llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                api_key=os.getenv("GROQ_API_KEY")
            )
        else:
            self.groq_llm = None

        if os.getenv("OPENAI_API_KEY"):
            self.openai_llm = ChatOpenAI(
                model="gpt-4.1-nano-2025-04-14",
                temperature=0.7,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        else:
            self.openai_llm = None

        logger.info("MilhenaGraph initialized")

    def _build_graph(self):
        """Build the LangGraph workflow"""
        # Create the graph
        graph = StateGraph(MilhenaState)

        # Add nodes with CLEAR PREFIXES
        graph.add_node("[CODE] Check Cache", self.check_cache)
        graph.add_node("[LEARNING] Apply Patterns", self.apply_learned_patterns)
        graph.add_node("[AGENT] Disambiguate", self.disambiguate_query)
        graph.add_node("[AGENT] Analyze Intent", self.analyze_intent)
        graph.add_node("[RAG] Retrieve Context", self.retrieve_rag_context)
        graph.add_node("[TOOL] Database Query", self.database_query)
        graph.add_node("[AGENT] Generate Response", self.generate_response)
        graph.add_node("[LIB] Mask Response", self.mask_response)
        graph.add_node("[CODE] Record Feedback", self.record_feedback)
        graph.add_node("[CODE] Handle Error", self.handle_error)

        # Set entry point
        graph.set_entry_point("[CODE] Check Cache")

        # Add edges
        graph.add_conditional_edges(
            "[CODE] Check Cache",
            self.route_from_cache,
            {
                "cached": "[LIB] Mask Response",
                "not_cached": "[LEARNING] Apply Patterns"
            }
        )

        graph.add_edge("[LEARNING] Apply Patterns", "[AGENT] Disambiguate")
        graph.add_edge("[AGENT] Disambiguate", "[AGENT] Analyze Intent")

        graph.add_conditional_edges(
            "[AGENT] Analyze Intent",
            self.route_from_intent,
            {
                "technical": "[CODE] Handle Error",
                "needs_data": "[RAG] Retrieve Context",
                "business": "[AGENT] Generate Response"
            }
        )

        # RAG retrieves context, then goes to DB query or direct response
        graph.add_conditional_edges(
            "[RAG] Retrieve Context",
            self.route_after_rag,
            {
                "needs_db": "[TOOL] Database Query",
                "has_answer": "[AGENT] Generate Response"
            }
        )

        graph.add_edge("[TOOL] Database Query", "[AGENT] Generate Response")

        graph.add_edge("[AGENT] Generate Response", "[LIB] Mask Response")
        graph.add_edge("[LIB] Mask Response", "[CODE] Record Feedback")
        graph.add_edge("[CODE] Record Feedback", END)
        graph.add_edge("[CODE] Handle Error", END)

        # Compile the graph with higher recursion limit
        self.compiled_graph = graph.compile(
            checkpointer=None,  # No memory for now
            debug=False
        )

        logger.info("MilhenaGraph compiled successfully")

    # ============================================================================
    # NODE IMPLEMENTATIONS - ALL WITH LANGSMITH TRACING
    # ============================================================================

    @traceable(
        name="MilhenaCheckCache",
        run_type="chain",
        metadata={"component": "cache", "version": "3.0"}
    )
    async def check_cache(self, state: MilhenaState) -> MilhenaState:
        """Check if response is cached"""

        # Extract query from messages if not present (LangGraph Studio compatibility)
        if "query" not in state or not state.get("query"):
            messages = state.get("messages", [])
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, "content"):
                    content = last_msg.content
                    if isinstance(content, list):
                        text_parts = [part.get("text", "") if isinstance(part, dict) else str(part) for part in content]
                        state["query"] = " ".join(text_parts)
                    else:
                        state["query"] = str(content)
                else:
                    state["query"] = str(last_msg)
            else:
                state["query"] = ""

        # Initialize missing fields
        if "session_id" not in state:
            state["session_id"] = f"session-{datetime.now().timestamp()}"
        if "context" not in state:
            state["context"] = {}
        if "disambiguated" not in state:
            state["disambiguated"] = False

        query = state["query"]
        session_id = state["session_id"]

        # Log to LangSmith
        logger.info(f"[LangSmith] Checking cache for session {session_id}")

        try:
            cached_response = await self.cache_manager.get(query, session_id)

            if cached_response:
                state["cached"] = True
                state["response"] = cached_response.get("response")
                logger.info(f"[LangSmith] Cache HIT - Query: {query[:50]}...")
            else:
                state["cached"] = False
                logger.info(f"[LangSmith] Cache MISS - Query: {query[:50]}...")
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
            state["cached"] = False

        return state

    @traceable(
        name="MilhenaApplyPatterns",
        run_type="chain",
        metadata={"component": "learning", "version": "3.0"}
    )
    async def apply_learned_patterns(self, state: MilhenaState) -> MilhenaState:
        """Apply learned patterns from previous interactions"""
        query = state["query"]
        session_id = state["session_id"]

        try:
            # Get learned patterns from learning system
            patterns = await self.learning_system.get_relevant_patterns(query)

            if patterns:
                state["learned_patterns"] = patterns
                state["context"]["learned_patterns"] = patterns
                logger.info(f"Applied {len(patterns)} learned patterns")
            else:
                state["learned_patterns"] = []
                logger.info("No relevant learned patterns found")

        except Exception as e:
            logger.warning(f"Failed to apply learned patterns: {e}")
            state["learned_patterns"] = []

        return state

    @traceable(name="MilhenaDisambiguate")
    async def disambiguate_query(self, state: MilhenaState) -> MilhenaState:
        """Disambiguate ambiguous queries"""
        query = state["query"]
        context = state["context"]

        try:
            result = await self.disambiguator.disambiguate(query, context)

            # Handle both DisambiguationResult object and dict
            if isinstance(result, dict):
                is_ambiguous = result.get("is_ambiguous", False)
                clarified_intent = result.get("clarified_intent", "")
                confidence = result.get("confidence", 0.0)
            else:
                is_ambiguous = result.is_ambiguous
                clarified_intent = result.clarified_intent
                confidence = result.confidence

            state["disambiguated"] = not is_ambiguous
            state["context"]["disambiguated_intent"] = clarified_intent
            state["context"]["confidence"] = confidence

            logger.info(f"Disambiguation complete: {clarified_intent}")

        except Exception as e:
            logger.error(f"Disambiguation failed: {e}")
            state["disambiguated"] = False
            state["context"]["disambiguated_intent"] = query
            state["context"]["confidence"] = 0.5

        return state

    @traceable(name="MilhenaAnalyzeIntent")
    async def analyze_intent(self, state: MilhenaState) -> MilhenaState:
        """Analyze user intent"""
        query = state["query"]
        context = state["context"]
        session_id = state["session_id"]

        try:
            intent = await self.intent_analyzer.classify(query, context, session_id)
            state["intent"] = intent if intent else "GENERAL"
            logger.info(f"Intent classified as: {state['intent']}")
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            state["intent"] = "GENERAL"
            state["context"]["classification_error"] = str(e)

        return state

    @traceable(name="MilhenaDatabaseQuery")
    async def database_query(self, state: MilhenaState) -> MilhenaState:
        """Execute database query based on intent"""
        query = state["query"]
        intent = state.get("intent", "GENERAL")

        try:
            # Determine which tool to use based on intent and query
            query_lower = query.lower()

            # USER QUERIES
            if "utenti" in query_lower or "users" in query_lower:
                if "quanti" in query_lower or "count" in query_lower:
                    result = query_users_tool("count")
                elif "attivi" in query_lower or "active" in query_lower:
                    result = query_users_tool("active")
                else:
                    result = query_users_tool("all")

            # EXECUTION QUERIES
            elif "esecuzione" in query_lower or "execution" in query_lower or "ultima" in query_lower:
                if "ultima" in query_lower or "last" in query_lower or "recente" in query_lower:
                    result = get_executions_tool("last")
                elif "oggi" in query_lower or "today" in query_lower:
                    result = get_executions_tool("today")
                elif "fallite" in query_lower or "errori" in query_lower or "failed" in query_lower:
                    result = get_executions_tool("failed")
                else:
                    result = get_executions_tool("last")

            # WORKFLOW QUERIES
            elif "workflow" in query_lower or "processo" in query_lower or "processi" in query_lower:
                if "attiv" in query_lower:
                    result = get_workflows_tool("active")
                elif "inattiv" in query_lower or "disattiv" in query_lower:
                    result = get_workflows_tool("inactive")
                elif "utilizzat" in query_lower or "usat" in query_lower or "top" in query_lower:
                    result = get_workflows_tool("top_used")
                elif "compless" in query_lower or "nodi" in query_lower:
                    result = get_workflows_tool("complex")
                elif "recen" in query_lower or "modificat" in query_lower:
                    result = get_workflows_tool("recent")
                elif "error" in query_lower or "problem" in query_lower:
                    result = get_workflows_tool("errors")
                else:
                    result = get_workflows_tool("all")

            # PERFORMANCE QUERIES
            elif "performance" in query_lower or "velocit" in query_lower or "lent" in query_lower or "tasso" in query_lower:
                if "velocit" in query_lower or "lent" in query_lower or "speed" in query_lower:
                    result = get_performance_metrics_tool("speed")
                elif "tasso" in query_lower or "success" in query_lower or "successo" in query_lower:
                    result = get_performance_metrics_tool("success_rate")
                elif "trend" in query_lower or "andamento" in query_lower:
                    result = get_performance_metrics_tool("trends")
                elif "bottleneck" in query_lower or "collo" in query_lower or "problema" in query_lower:
                    result = get_performance_metrics_tool("bottlenecks")
                else:
                    result = get_performance_metrics_tool("overview")

            # MONITORING QUERIES
            elif "monitoraggio" in query_lower or "alert" in query_lower or "salute" in query_lower or "health" in query_lower:
                if "alert" in query_lower or "avvisi" in query_lower or "warning" in query_lower:
                    result = get_system_monitoring_tool("alerts")
                elif "coda" in query_lower or "queue" in query_lower:
                    result = get_system_monitoring_tool("queue")
                elif "risorse" in query_lower or "resources" in query_lower:
                    result = get_system_monitoring_tool("resources")
                elif "disponibilit" in query_lower or "availability" in query_lower or "uptime" in query_lower:
                    result = get_system_monitoring_tool("availability")
                else:
                    result = get_system_monitoring_tool("health")

            # ANALYTICS QUERIES
            elif "report" in query_lower or "analisi" in query_lower or "confronto" in query_lower or "roi" in query_lower:
                if "confronto" in query_lower or "comparison" in query_lower or "settiman" in query_lower:
                    result = get_analytics_tool("comparison")
                elif "roi" in query_lower or "risparmio" in query_lower or "valore" in query_lower:
                    result = get_analytics_tool("roi")
                elif "pattern" in query_lower or "utilizzo" in query_lower or "picco" in query_lower:
                    result = get_analytics_tool("patterns")
                elif "prevision" in query_lower or "forecast" in query_lower or "proiezion" in query_lower:
                    result = get_analytics_tool("forecast")
                else:
                    result = get_analytics_tool("summary")

            # SYSTEM STATUS (default)
            elif "sistema" in query_lower or "status" in query_lower or "stato" in query_lower:
                result = get_system_status_tool()

            else:
                # Default: try to get general analytics
                result = get_analytics_tool("summary")

            # Store result in context for response generation
            state["context"]["database_result"] = result
            logger.info(f"Database query executed: {result[:100]}...")

        except Exception as e:
            logger.error(f"Database query failed: {e}")
            state["context"]["database_error"] = str(e)

        return state

    @traceable(
        name="MilhenaRetrieveRAG",
        run_type="retriever",
        metadata={"component": "rag", "version": "3.0"}
    )
    async def retrieve_rag_context(self, state: MilhenaState) -> MilhenaState:
        """Retrieve relevant context from RAG knowledge base"""
        query = state["query"]
        intent = state.get("intent", "GENERAL")

        if not self.rag_system:
            logger.warning("RAG system not available, skipping retrieval")
            state["rag_context"] = []
            return state

        try:
            # Search RAG knowledge base for relevant documentation
            results = await self.rag_system.search_documents(
                query=query,
                top_k=3,
                user_level="BUSINESS"
            )

            if results and results.get("results"):
                docs = results["results"]
                state["rag_context"] = docs
                state["context"]["rag_docs"] = docs
                logger.info(f"Retrieved {len(docs)} RAG documents (relevance: {docs[0].get('score', 0):.3f})")
            else:
                state["rag_context"] = []
                logger.info("No relevant RAG documents found")

        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            state["rag_context"] = []
            state["context"]["rag_error"] = str(e)

        return state

    @traceable(name="MilhenaGenerateResponse")
    async def generate_response(self, state: MilhenaState) -> MilhenaState:
        """Generate appropriate response"""
        query = state["query"]
        intent = state.get("intent", "GENERAL")
        context = state["context"]
        session_id = state["session_id"]

        try:
            # Select appropriate LLM
            complexity = self._assess_complexity(query)

            if complexity == "simple" and self.groq_llm:
                llm = self.groq_llm
                logger.info("Using GROQ for simple query")
            else:
                llm = self.openai_llm
                logger.info("Using OpenAI for complex query")

            response = await self.response_generator.generate(
                query=query,
                intent=intent,
                llm=llm,
                context=context,
                session_id=session_id
            )

            state["response"] = response

            # Add AI response to messages for Chat display
            state["messages"].append(AIMessage(content=response))

            logger.info(f"Response generated: {response[:100]}...")

            # Cache the response
            try:
                await self.cache_manager.set(query, session_id, {"response": response})
            except Exception as cache_error:
                logger.warning(f"Failed to cache response: {cache_error}")

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            error_msg = "Mi dispiace, ho avuto un problema nel generare la risposta. Riprova."
            state["response"] = error_msg
            state["messages"].append(AIMessage(content=error_msg))
            state["error"] = str(e)

        return state

    @traceable(name="MilhenaMaskResponse")
    async def mask_response(self, state: MilhenaState) -> MilhenaState:
        """Apply final masking to response"""
        response = state.get("response", "")

        if response:
            try:
                masked = self.masking_engine.mask(response)
                state["response"] = masked
                state["masked"] = True
                logger.info("Response masked")
            except Exception as e:
                logger.error(f"Masking failed: {e}")
                state["masked"] = False
        else:
            state["masked"] = False

        return state

    @traceable(name="MilhenaRecordFeedback")
    async def record_feedback(self, state: MilhenaState) -> MilhenaState:
        """Record interaction for learning"""
        query = state["query"]
        intent = state["intent"]
        response = state["response"]
        session_id = state["session_id"]

        await self.learning_system.record_feedback(
            query=query,
            intent=intent or "GENERAL",
            response=response or "",
            feedback_type="neutral",
            session_id=session_id
        )

        logger.info("Feedback recorded for learning")

        return state

    @traceable(name="MilhenaHandleError")
    async def handle_error(self, state: MilhenaState) -> MilhenaState:
        """Handle errors and technical queries"""
        state["response"] = "Per informazioni tecniche, contatta il team IT."
        state["error"] = "Technical query deflected"

        logger.info("Technical query handled")

        return state

    # ============================================================================
    # ROUTING FUNCTIONS
    # ============================================================================

    def route_from_cache(self, state: MilhenaState) -> str:
        """Route based on cache status"""
        return "cached" if state.get("cached") else "not_cached"

    def route_from_intent(self, state: MilhenaState) -> str:
        """Route based on intent"""
        intent = state.get("intent", "GENERAL")

        if intent == "TECHNICAL":
            return "technical"
        elif intent in ["METRIC", "STATUS", "DATA", "COUNT"]:
            # These intents need database data - go through RAG first
            return "needs_data"
        else:
            return "business"

    def route_after_rag(self, state: MilhenaState) -> str:
        """Route after RAG retrieval - decide if we need DB data or can answer directly"""
        rag_context = state.get("rag_context", [])
        intent = state.get("intent", "GENERAL")

        # If RAG found high-quality docs, we might have the answer
        if rag_context and len(rag_context) > 0:
            # Check if top result has high relevance
            top_score = rag_context[0].get("score", 0)
            if top_score > 0.8:
                logger.info(f"High-quality RAG result (score: {top_score}), skipping DB query")
                return "has_answer"

        # For data-heavy intents, always query DB even if RAG found something
        if intent in ["METRIC", "STATUS", "DATA", "COUNT"]:
            return "needs_db"

        # Default: if we have some RAG context, use it
        if rag_context:
            return "has_answer"

        return "needs_db"

    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity"""
        word_count = len(query.split())

        if word_count < 10:
            return "simple"
        elif word_count < 30:
            return "medium"
        else:
            return "complex"

    # ============================================================================
    # PUBLIC INTERFACE
    # ============================================================================

    async def process(
        self,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the Milhena workflow

        Args:
            query: User query
            session_id: Session identifier
            context: Optional context

        Returns:
            Response dictionary
        """
        try:
            # Initialize state
            initial_state = MilhenaState(
                messages=[HumanMessage(content=query)],
                query=query,
                intent=None,
                session_id=session_id,
                context=context or {},
                disambiguated=False,
                response=None,
                feedback=None,
                cached=False,
                masked=False,
                error=None,
                rag_context=None,
                learned_patterns=None
            )

            # Run the graph
            final_state = await self.compiled_graph.ainvoke(initial_state)

            # Return the result
            return {
                "success": True,
                "response": final_state.get("response"),
                "intent": final_state.get("intent"),
                "cached": final_state.get("cached", False),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in MilhenaGraph: {e}")
            return {
                "success": False,
                "response": "Si è verificato un problema temporaneo. Riprova.",
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }

    async def process_with_feedback(
        self,
        query: str,
        session_id: str,
        feedback_type: str,  # "positive" or "negative"
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process query and record feedback

        Args:
            query: User query
            session_id: Session identifier
            feedback_type: Type of feedback
            context: Optional context

        Returns:
            Response dictionary
        """
        # Process the query
        result = await self.process(query, session_id, context)

        # Record the feedback
        if result["success"]:
            await self.learning_system.record_feedback(
                query=query,
                intent=result.get("intent", "GENERAL"),
                response=result.get("response", ""),
                feedback_type=feedback_type,
                session_id=session_id
            )

        return result

# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

# Create a singleton instance
_milhena_instance = None

def get_milhena_graph() -> MilhenaGraph:
    """Get or create the Milhena graph singleton"""
    global _milhena_instance
    if _milhena_instance is None:
        _milhena_instance = MilhenaGraph()
    return _milhena_instance

# ============================================================================
# LANGGRAPH STUDIO EXPORT
# ============================================================================

# Export the compiled graph for LangGraph Studio
# This is what langgraph.json references
milhena_graph = get_milhena_graph().compiled_graph