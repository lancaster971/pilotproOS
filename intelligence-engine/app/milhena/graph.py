"""
MilhenaGraph - LangGraph workflow for Business Assistant
Following official LangGraph patterns with conditional routing
FULL LANGSMITH TRACING ENABLED
"""
from typing import List, Dict, Any, Optional, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.redis import AsyncRedisSaver
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.output_parsers import JsonOutputParser
from langsmith import traceable, Client
from langsmith.run_trees import RunTree
import logging
import os
from datetime import datetime
import asyncio
import uuid
import json

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
    # SMART CONSOLIDATED TOOLS (3) - Reduce 30→12 decision space
    smart_analytics_query_tool,
    smart_workflow_query_tool,
    smart_executions_query_tool,
    # SPECIALIZED TOOLS (9) - Cannot be consolidated
    get_error_details_tool,
    get_all_errors_summary_tool,
    get_node_execution_details_tool,
    get_chatone_email_details_tool,
    get_raw_modal_data_tool,
    get_live_events_tool,
    get_workflows_tool,
    get_workflow_cards_tool,
    execute_workflow_tool,
    toggle_workflow_tool,
    search_knowledge_base_tool,
    get_full_database_dump,
    # DYNAMIC CONTEXT SYSTEM (1) - v3.5.0
    get_system_context_tool,
    # LEGACY WRAPPERS (3) - Backward compatibility
    get_performance_metrics_tool,
    get_system_monitoring_tool,
    get_analytics_tool
)

# Import RAG System for knowledge retrieval
from app.rag import get_rag_system

# v3.2: Mock Tools Integration for testing without database
from app.milhena.mock_tools import is_mock_enabled, get_mock_info
import os

logger = logging.getLogger(__name__)

# v3.2: Wrap tools with mock versions if USE_MOCK_DATA=true
if is_mock_enabled():
    logger.warning("=" * 80)
    logger.warning("⚠️  MOCK DATA ENABLED - Using fake data for testing")
    logger.warning("   Set USE_MOCK_DATA=false to use real PostgreSQL database")
    logger.warning("=" * 80)

    # Import mock functions
    from app.milhena.mock_tools import (
        get_mock_workflows,
        get_mock_errors,
        get_mock_workflow_details,
        get_mock_statistics,
        get_mock_executions_by_date
    )

    # Wrap real tools with mock implementations
    from langchain_core.tools import tool

    @tool
    def get_workflows_tool() -> str:
        """
        Get complete list of business processes with their status (active/inactive).

        🔑 KEYWORDS: processi, workflow, flussi, business process, automazione

        USE THIS WHEN:
        - User asks: "quanti processi abbiamo?", "quali workflow?", "elenco processi"
        - User wants to know total count of business processes
        - User asks about process names or status overview

        DO NOT USE WHEN:
        - User asks about "tabelle", "dati", "informazioni" (ambiguous terms - ask clarification first)
        - User asks about execution statistics (use smart_analytics_query_tool)
        - User asks about errors (use get_all_errors_summary_tool)
        - User asks about specific process details (use get_workflow_details_tool)

        Returns: Total count, active/inactive count, list of process names (MOCK DATA)
        """
        return get_mock_workflows()

    @tool
    def get_all_errors_summary_tool() -> str:
        """
        Get aggregated error summary by business process (last 7 days).

        🔑 KEYWORDS: errori totali, summary errori, riepilogo failure, tutti problemi, statistiche errori

        USE THIS WHEN:
        - User asks: "ci sono errori?", "quali processi hanno errori?", "summary errori"
        - User wants error overview across multiple processes
        - User needs to identify problematic processes

        DO NOT USE WHEN:
        - User asks for detailed error info for ONE specific process (use get_error_details_tool)
        - User asks about execution statistics (use smart_analytics_query_tool)
        - User asks about process list (use get_workflows_tool)

        Returns: Error count per process, most recent errors, affected processes (MOCK DATA)
        """
        return get_mock_errors()

    @tool
    def get_workflow_details_tool(workflow_name: str) -> str:
        """
        Get detailed information about ONE specific business process.

        🔑 KEYWORDS: dettagli processo, info workflow, specifiche flusso, configurazione, workflow detail

        USE THIS WHEN:
        - User asks: "dettagli processo X", "come funziona workflow Y", "info su processo Z"
        - User wants to know configuration, nodes, status of specific process
        - User mentions a specific process name

        DO NOT USE WHEN:
        - User asks for list of ALL processes (use get_workflows_tool)
        - User asks about execution history (use smart_executions_query_tool)
        - User asks about errors only (use get_error_details_tool)

        Args:
            workflow_name: Exact name of the business process (case-sensitive)

        Returns: Process configuration, number of nodes, active status, last update (MOCK DATA)
        """
        return get_mock_workflow_details(workflow_name)

    @tool
    def get_full_database_dump(days: int = 7) -> str:
        """
        Get COMPREHENSIVE system statistics for last N days (HEAVY tool).

        🔑 KEYWORDS: tutto, completo, full report, overview completa, dump totale

        USE THIS WHEN:
        - User EXPLICITLY asks for "complete overview", "full report", "everything", "all statistics"
        - User wants aggregated view across ALL metrics (executions + errors + performance)
        - User says "dammi tutto" or "report completo"

        DO NOT USE WHEN:
        - User asks about "tabelle", "dati", "informazioni" (AMBIGUOUS - ask clarification first!)
        - User asks about processes only (use get_workflows_tool - much faster)
        - User asks about errors only (use get_all_errors_summary_tool - much faster)
        - User asks about specific metric (use smart_analytics_query_tool - much faster)

        ⚠️ WARNING: Returns 2000+ lines of data. Use ONLY when user explicitly requests complete dump.

        Args:
            days: Number of days to look back (default: 7)

        Returns: Total executions, success/error rates, daily trends, all metrics aggregated (MOCK DATA)
        """
        return get_mock_statistics()

    logger.info("✅ Mock tools initialized successfully")
else:
    logger.info("✅ Using REAL database tools (PostgreSQL)")

# ============================================================================
# CLASSIFIER AGENT PROMPT (v3.5.0)
# Source: REACT-PROMPT.md
# ============================================================================

CLASSIFIER_PROMPT = """Sei Milhena, assistente intelligente per PilotProOS.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 COS'È PILOTPROS (contesto fisso):

PilotProOS è un sistema di monitoraggio e gestione di processi business automatizzati.

COSA GESTISCE:
- Processi business (automazioni workflow-based)
- Esecuzioni processi (ogni run di un'automazione)
- Errori/fallimenti (quando un processo non riesce)
- Step di processo (azioni interne ai processi)
- Performance metrics (durata, tasso successo, throughput)

ARCHITETTURA BASE:
- Database PostgreSQL (schema 'pilotpros' per analytics)
- Workflow engine per automazioni business
- Sistema di tracking esecuzioni real-time
- Sistema di error reporting

DATI TRACCIATI:
- Chi: Quali processi sono attivi/inattivi
- Cosa: Dettagli esecuzioni (successo/fallimento)
- Quando: Timestamp start/end, durate
- Dove: Errori in quali step specifici
- Perché: Error messages, logs, context

CASI D'USO TIPICI:
- Monitoraggio salute processi business
- Analisi errori e troubleshooting
- Statistiche performance e trend
- Gestione attivazione/disattivazione processi

TUO COMPITO (CLASSIFIER v3.5.2):
1. Leggere il CONTESTO SISTEMA fornito nel prompt (sotto)
2. Interpretare richieste utente usando workflows/statistiche/dizionario
3. Disambiguare termini ambigui consultando dizionario_business
4. Classificare in 1 delle 9 CATEGORIE
5. Return JSON: {{category, confidence, params}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 CONTESTO SISTEMA (già fornito nel prompt):

Il contesto reale del sistema è iniettato in questo prompt e contiene:
- WORKFLOWS ATTIVI: Count + lista nomi workflow esistenti
- ESECUZIONI (7 giorni): Statistiche reali
- DIZIONARIO BUSINESS: Mapping termini → significato
  * "clienti" = Email ChatOne
  * "problemi" = Errori
  * "attività" = Esecuzioni
  * "passi" = Nodi
  * "workflow" = Processi

⚠️ REGOLA CRITICA: LEGGI il contesto fornito sotto, NON inventare dati.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 STEP 1: CLASSIFICA (9 categorie)

Usa il contesto fornito per:
1. Verificare workflow names esistenti
2. Tradurre termini business via dizionario
3. Classificare con confidence 1.0
4. SE ancora ambiguo → Clarification (STEP 2)

┌────────────────────────────────────────────────┐
│ 1. PROCESS_LIST                                │
│    Sinonimi: processi, workflow, flussi        │
├────────────────────────────────────────────────┤
│ 2. PROCESS_DETAIL                              │
│    Sinonimi: dettagli processo X, info workflow│
├────────────────────────────────────────────────┤
│ 3. EXECUTION_QUERY                             │
│    Sinonimi: attività, lavori, task, run       │
├────────────────────────────────────────────────┤
│ 4. ERROR_ANALYSIS                              │
│    Sinonimi: problemi, errori, issues, guasti  │
├────────────────────────────────────────────────┤
│ 5. ANALYTICS                                   │
│    Sinonimi: performance, KPI, statistiche     │
├────────────────────────────────────────────────┤
│ 6. STEP_DETAIL                                 │
│    Sinonimi: passi, step, fasi, nodi           │
├────────────────────────────────────────────────┤
│ 7. EMAIL_ACTIVITY                              │
│    Sinonimi: email, conversazioni ChatOne, messaggi email│
├────────────────────────────────────────────────┤
│ 8. PROCESS_ACTION                              │
│    Sinonimi: attiva, disattiva, esegui         │
├────────────────────────────────────────────────┤
│ 9. SYSTEM_OVERVIEW                             │
│    Sinonimi: overview completo, full report    │
└────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📤 OUTPUT JSON STEP 1 (confidence 100%)

{{
  "category": "PROCESS_DETAIL",
  "confidence": 1.0,
  "params": {{
    "workflow_id": "CHATBOT_MAIL__SIMPLE"
  }}
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 STEP 2: CLARIFICATION (se confidence < 100%)

Template:
"PilotProOS gestisce [X] processi: [nomi].
Abbiamo [Y] esecuzioni e [Z] errori recenti.

Cosa intendi per '[termine ambiguo]'?
- Opzione 1: ...
- Opzione 2: ...
- Opzione 3: ...

Altro?"

Limite: Max 2 iterazioni clarification

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ REGOLE FINALI (v3.5.2):

1. ✅ LEGGI il CONTESTO SISTEMA fornito sotto (workflows, stats, dizionario)
2. ✅ Valida workflow names contro workflows_attivi forniti
3. ✅ Traduci termini business via dizionario fornito
4. ✅ Classifica in 1 delle 9 CATEGORIE (confidence 1.0)
5. ✅ SE ancora ambiguo → Clarification con dati reali dal contesto
6. ✅ Return JSON valido (1 LLM call, NO tool calls)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Query: "{query}"
Data corrente: {current_date}

Return JSON SOLO (no text, no markdown).
"""


# ============================================================================
# TOOL MAPPER - v3.5.0
# Maps 9 categories to business tools (LangGraph best practice pattern)
# ============================================================================

def map_category_to_tools(category: str) -> list:
    """
    Map classification category to appropriate tool function(s).

    Args:
        category: One of 9 categories (PROCESS_LIST, PROCESS_DETAIL, etc.)

    Returns:
        List of tool functions (NOT tuples - params passed separately)

    Note: Params come from classifier JSON and are passed to tool.invoke(params)
    """
    mapping = {
        "PROCESS_LIST": [get_workflows_tool],
        "PROCESS_DETAIL": [smart_workflow_query_tool],
        "EXECUTION_QUERY": [smart_executions_query_tool],
        "ERROR_ANALYSIS": [get_error_details_tool],
        "ANALYTICS": [smart_analytics_query_tool],
        "STEP_DETAIL": [get_node_execution_details_tool],
        "EMAIL_ACTIVITY": [get_chatone_email_details_tool],
        "PROCESS_ACTION": [execute_workflow_tool, toggle_workflow_tool],  # Both available
        "SYSTEM_OVERVIEW": [get_full_database_dump]
    }

    tools = mapping.get(category)
    if not tools:
        logger.warning(f"[TOOL MAPPER] Unknown category: {category}, returning empty list")
        return []

    logger.info(f"[TOOL MAPPER] {category} → {len(tools)} tool(s)")
    return tools


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

class SupervisorDecision(BaseModel):
    """
    Supervisor classification decision - v3.5.0 Dynamic Context System

    action: respond (direct answer) | tool (load context) | react (use ReAct agent)
    category: DANGER | HELP | AMBIGUOUS | SIMPLE | COMPLEX
    """
    action: str = Field(description="respond|tool|react")
    category: str = Field(description="DANGER|HELP|AMBIGUOUS|SIMPLE|COMPLEX")
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    direct_response: Optional[str] = None
    needs_rag: bool = False
    needs_database: bool = False
    needs_context: bool = False  # v3.5.0: NEW - True if AMBIGUOUS category
    clarification_options: Optional[List[str]] = None
    suggested_tool: Optional[str] = None  # v3.5.0: Tool to call (e.g., "get_system_context_tool")
    llm_used: str

class MilhenaState(TypedDict):
    """State for Milhena conversation flow - v3.5.0 with Dynamic Context System"""
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

    # NEW: Supervisor fields
    supervisor_decision: Optional[SupervisorDecision]
    waiting_clarification: bool
    original_query: Optional[str]  # For learning

    # NEW: Rephraser fields
    is_ambiguous: bool  # Rule-based ambiguity detection
    rephraser_triggered: bool  # Safety flag (max 1 rephrase)

    # v3.5.0: Dynamic Context System
    system_context: Optional[Dict[str, Any]]  # Pre-loaded context from get_system_context_tool()
    tool_results: Optional[List[Dict[str, Any]]]  # RAW data from tool execution (v3.5.0)

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

    def __init__(self, config: Optional[MilhenaConfig] = None, checkpointer=None):
        """
        Initialize MilhenaGraph

        Args:
            config: Optional MilhenaConfig for component initialization
            checkpointer: Optional checkpointer (AsyncRedisSaver, MemorySaver, etc.)
                         If None, will create MemorySaver as fallback
        """
        self.config = config or MilhenaConfig()
        self.external_checkpointer = checkpointer  # Store externally provided checkpointer
        self._initialize_components()
        self._build_graph()

    async def async_init(self):
        """
        Async initialization for components requiring async setup (DB pool, pattern loading).
        Must be called after __init__ from FastAPI lifespan.

        Usage in main.py:
            milhena_graph = MilhenaGraph(checkpointer=checkpointer)
            await milhena_graph.async_init()
        """
        import asyncpg
        import os

        # Create asyncpg connection pool
        try:
            db_url = os.getenv("DATABASE_URL", "postgresql://pilotpros_user:pilotpros_secure_pass_2025@postgres-dev:5432/pilotpros_db")
            self.db_pool = await asyncpg.create_pool(
                db_url,
                min_size=2,
                max_size=10,
                max_inactive_connection_lifetime=300.0,
                command_timeout=60.0
            )
            logger.info("[AUTO-LEARN] asyncpg connection pool created (min=2, max=10)")

            # Load learned patterns from database
            await self._load_learned_patterns()

        except Exception as e:
            logger.error(f"[AUTO-LEARN] Failed to create DB pool: {e}")
            self.db_pool = None
            self.learned_patterns = {}

    def _initialize_components(self):
        """Initialize all Milhena components"""
        self.masking_engine = TechnicalMaskingEngine()
        self.disambiguator = LLMDisambiguator(self.config)
        self.intent_analyzer = IntentAnalyzer(self.config)
        self.response_generator = ResponseGenerator(self.config, self.masking_engine)
        self.learning_system = LearningSystem()
        self.token_manager = TokenManager()
        self.cache_manager = CacheManager(self.config)

        # Initialize PostgreSQL connection pool for auto-learning
        # asyncpg best practice: share pool, not connections
        # Reference: https://magicstack.github.io/asyncpg/current/usage.html
        self.db_pool = None
        self.learned_patterns = {}  # In-memory cache of learned patterns

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

        # Initialize Rate Limiters (Best Practice: prevent rate limit errors)
        # Based on LangChain documentation and OpenAI Cookbook best practices
        # GROQ Free Tier: 100k tokens/day (~30 req/min safe limit)
        groq_rate_limiter = InMemoryRateLimiter(
            requests_per_second=0.5,  # 30 req/min = 0.5 req/sec (conservative)
            check_every_n_seconds=0.1,
            max_bucket_size=5  # Allow small bursts
        )

        # OpenAI Tier 1: 500 req/min, 30k req/day
        openai_rate_limiter = InMemoryRateLimiter(
            requests_per_second=8.0,  # 480 req/min (80% of limit for safety)
            check_every_n_seconds=0.1,
            max_bucket_size=10
        )

        # Initialize LLMs with rate limiters
        if os.getenv("GROQ_API_KEY"):
            self.groq_llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                api_key=os.getenv("GROQ_API_KEY"),
                rate_limiter=groq_rate_limiter
            )
        else:
            self.groq_llm = None

        if os.getenv("OPENAI_API_KEY"):
            self.openai_llm = ChatOpenAI(
                model="gpt-4o-2024-11-20",  # 1M TPM - better query interpretation than nano
                temperature=0.7,
                api_key=os.getenv("OPENAI_API_KEY"),
                rate_limiter=openai_rate_limiter
            )
        else:
            self.openai_llm = None

        # Initialize Supervisor LLM (GROQ primary + OpenAI fallback) with rate limiters
        self.supervisor_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,  # Low for consistent classification
            request_timeout=10.0,
            max_retries=1,
            api_key=os.getenv("GROQ_API_KEY"),
            rate_limiter=groq_rate_limiter
        ) if os.getenv("GROQ_API_KEY") else None

        self.supervisor_fallback = ChatOpenAI(
            model="gpt-4.1-nano-2025-04-14",
            temperature=0.3,
            request_timeout=10.0,
            max_retries=1,
            api_key=os.getenv("OPENAI_API_KEY"),
            rate_limiter=openai_rate_limiter
        ) if os.getenv("OPENAI_API_KEY") else None

        # v3.2: JsonOutputParser to handle JSON parsing robustly (FIX: '"action"' error)
        self.json_parser = JsonOutputParser()

        # v3.5.1: RAM Cache for system context (prevent tool loop)
        self._system_context_cache = None
        self._cache_timestamp = 0
        self._cache_ttl = 300  # 5 minutes TTL

        logger.info(f"Supervisor: GROQ={bool(self.supervisor_llm)}, Fallback={bool(self.supervisor_fallback)}")
        logger.info("MilhenaGraph initialized")

    def _build_graph(self):
        """Build the LangGraph workflow with Supervisor entry point"""
        # Create the graph
        graph = StateGraph(MilhenaState)

        # v3.1 MICROSERVICES ARCHITECTURE - 6 Nodes (PDF Best Practices)
        # 3 AI Agents: Classifier → ReAct (tools only) → Responder (synthesis)

        # Agent 1: Classifier (interprets ALL queries, NO whitelist)
        # v3.5.0: SIMPLIFIED ARCHITECTURE (6 components)
        # Fast-Path → Classifier (ReAct) → Tool Execution → Responder → Masking

        # Agent 1: Classifier (ReAct with get_system_context_tool for disambiguation)
        graph.add_node("[AI] Classifier", self.supervisor_orchestrator)

        # Component 2: Tool Execution (direct calls, NO agent)
        graph.add_node("[TOOL] Execute Tools", self.execute_tools_direct)

        # Agent 3: Responder (RAW data → business language)
        graph.add_node("[AI] Responder", self.generate_final_response)

        # Libraries: Masking & Persistence
        graph.add_node("[LIB] Mask Response", self.mask_response)
        graph.add_node("[DB] Record Feedback", self.record_feedback)

        # ENTRY POINT: Classifier (with memory + disambiguation)
        graph.set_entry_point("[AI] Classifier")

        # v3.5.0 FIX: Conditional routing after Classifier
        # If Fast-Path match (direct_response exists) → END immediately
        # Otherwise → Continue to Tool Execution
        def route_after_classifier(state: MilhenaState) -> str:
            """Route after Classifier: END if direct_response (Fast-Path), else continue"""
            if state.get("response"):
                logger.info("[ROUTER] Fast-Path response detected → END immediately")
                return END
            else:
                logger.info("[ROUTER] No direct response → Continue to Tool Execution")
                return "[TOOL] Execute Tools"

        graph.add_conditional_edges(
            "[AI] Classifier",
            route_after_classifier,
            {
                END: END,
                "[TOOL] Execute Tools": "[TOOL] Execute Tools"
            }
        )

        # Linear flow after Tool Execution: Tools → Responder → Masking → Feedback
        graph.add_edge("[TOOL] Execute Tools", "[AI] Responder")
        graph.add_edge("[AI] Responder", "[LIB] Mask Response")
        graph.add_edge("[LIB] Mask Response", "[DB] Record Feedback")
        graph.add_edge("[DB] Record Feedback", END)

        # v3.5.0: Checkpointer used by Classifier Agent (passed to create_react_agent)
        # AsyncRedisSaver initialized in main.py lifespan, shared across all graph nodes
        if self.external_checkpointer:
            logger.info("✅ Using AsyncRedisSaver checkpointer (7-day TTL)")
        else:
            logger.warning("⚠️  No external checkpointer - memory disabled")

        # v3.5.0: OLD ReAct Agent REMOVED (replaced by Tool Mapper + Direct Execution)
        # Architecture change: Classifier (ReAct) → Tool Mapper → Direct Tool Calls → Responder

        # v3.5.0: Legacy Classifier Prompt (NOT USED - moved to REACT-PROMPT.md)
        # Preserved for reference only
        LEGACY_CLASSIFIER_PROMPT_V350 = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 COS'È PILOTPROS (contesto fisso):

PilotProOS è un sistema di monitoraggio e gestione di processi business automatizzati.

COSA GESTISCE:
- Processi business (automazioni workflow-based)
- Esecuzioni processi (ogni run di un'automazione)
- Errori/fallimenti (quando un processo non riesce)
- Step di processo (azioni interne ai processi)
- Performance metrics (durata, tasso successo, throughput)

ARCHITETTURA BASE:
- Database PostgreSQL (schema 'pilotpros' per analytics)
- Workflow engine per automazioni business
- Sistema di tracking esecuzioni real-time
- Sistema di error reporting

DATI TRACCIATI:
- Chi: Quali processi sono attivi/inattivi
- Cosa: Dettagli esecuzioni (successo/fallimento)
- Quando: Timestamp start/end, durate
- Dove: Errori in quali step specifici
- Perché: Error messages, logs, context

CASI D'USO TIPICI:
- Monitoraggio salute processi business
- Analisi errori e troubleshooting
- Statistiche performance e trend
- Gestione attivazione/disattivazione processi

TUO COMPITO:
1. Interpretare richieste utente
2. Disambiguare termini ambigui
3. Tradurre terminologia business in categorie sistema
4. Chiamare tool appropriati
5. Rispondere in linguaggio business (NO technical terms)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ DYNAMIC CONTEXT SYSTEM

Quando ricevi query, system_context può essere PRE-CARICATO in state.

system_context contiene (se disponibile):
├─ workflows_attivi: {{count, nomi, dettagli}}
├─ dizionario_business: {{termine: {{sinonimi, categoria, tool, dati_reali}}}}
├─ statistiche: {{esecuzioni, errori, success_rate, etc.}}
└─ esempi_uso: [{{query, interpretazione, tool, response_template}}]

⚠️ USA system_context per:
1. Validare workflow names (usa SOLO nomi in context.workflows_attivi.nomi)
2. Tradurre terminologia business (consulta dizionario_business)
3. Offrire clarification con dati reali (usa statistiche)
4. Vedere esempi interpretazione (consulta esempi_uso)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 WORKFLOW INTERPRETAZIONE (5 STEP):

STEP 1: ANALIZZA QUERY
├─ system_context disponibile? (check state["system_context"])
│  ├─ SÌ → Consulta dizionario_business per tradurre termini
│  └─ NO → Procedi con query letterale
│
└─ Query contiene termini nel dizionario?
   ├─ SÌ → Traduci usando "significa" + "categoria"
   └─ NO → Query ambigua, serve clarification

STEP 2: CLARIFICATION (se query ambigua/generica)
├─ Leggi workflows_attivi.nomi da context
├─ Leggi statistiche da context
└─ Genera clarification con DATI REALI:

Template:
"PilotProOS gestisce [context.workflows_attivi.count] processi: [context.workflows_attivi.nomi].
Abbiamo [context.statistiche.esecuzioni_7d] esecuzioni e [context.statistiche.errori_7d] errori recenti.

Cosa intendi per '[termine ambiguo]'?
- Opzione 1: Lista processi?
- Opzione 2: Esecuzioni recenti?
- Opzione 3: Errori/problemi?
- Opzione 4: Statistiche performance?"

⚠️ LIMITE: Max 2 iterazioni clarification. Dopo, termina cortesemente.

STEP 3: CLASSIFICA RICHIESTA
Identifica CATEGORIA tra 9 disponibili:

┌────────────────────────────────────────────────┐
│ CATEGORIE SISTEMA (mapping a tools):           │
├────────────────────────────────────────────────┤
│ 1. PROCESS_LIST                                │
│    Sinonimi: processi, workflow, flussi        │
│    Tool: get_workflows_tool()                  │
├────────────────────────────────────────────────┤
│ 2. PROCESS_DETAIL                              │
│    Sinonimi: dettagli processo X, info workflow│
│    Tool: smart_workflow_query_tool(id)         │
├────────────────────────────────────────────────┤
│ 3. EXECUTION_QUERY                             │
│    Sinonimi: attività, lavori, task, run       │
│    Tool: smart_executions_query_tool(scope)    │
├────────────────────────────────────────────────┤
│ 4. ERROR_ANALYSIS                              │
│    Sinonimi: problemi, errori, issues, guasti  │
│    Tool: get_error_details_tool(workflow)      │
├────────────────────────────────────────────────┤
│ 5. ANALYTICS                                   │
│    Sinonimi: performance, KPI, statistiche     │
│    Tool: smart_analytics_query_tool(metric)    │
├────────────────────────────────────────────────┤
│ 6. STEP_DETAIL                                 │
│    Sinonimi: passi, step, fasi, nodi           │
│    Tool: get_node_execution_details_tool()     │
├────────────────────────────────────────────────┤
│ 7. EMAIL_ACTIVITY                              │
│    Sinonimi: email, conversazioni ChatOne, messaggi email│
│    Tool: get_chatone_email_details_tool(date)  │
├────────────────────────────────────────────────┤
│ 8. PROCESS_ACTION                              │
│    Sinonimi: attiva, disattiva, esegui         │
│    Tool: toggle/execute_workflow_tool()        │
├────────────────────────────────────────────────┤
│ 9. SYSTEM_OVERVIEW                             │
│    Sinonimi: overview completo, full report    │
│    Tool: get_full_database_dump(days)          │
└────────────────────────────────────────────────┘

STEP 4: CHIAMA TOOL(S)
├─ Categoria identificata → Chiama tool corrispondente
├─ Serve deep-dive? → Chiama MULTIPLI tool sequenziali
│  Esempio: "perché Flow_4 fallisce?" →
│    1. get_error_details_tool(workflow="Flow_4")
│    2. get_node_execution_details_tool(workflow="Flow_4", node=[dal primo tool])
│
└─ Parametri tool:
   - workflow_name: Valida contro context.workflows_attivi.nomi
   - date: "oggi" = current date, "recenti" = 7 giorni default
   - scope: "recent_all", "by_date", "by_workflow", "specific"

STEP 5: GENERA RISPOSTA
├─ Traduci output tool in linguaggio business
├─ NO greetings ("Ciao!"), NO fluff ("ecco i dati", "certo")
├─ Usa emoji contestuali:
│  - ⚠️ Per errori/problemi
│  - ✅ Per successi/performance positive
│  - 📊 Per statistiche/metriche
│  - 📧 Per email/ChatOne
│  - ⚡ Per azioni/modifiche
│
└─ Termina SEMPRE con "Altro?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 REGOLE MASKING (CRITICAL):

⛔ MAI esporre in response:
- Tool names (get_workflows_tool, smart_executions_query_tool, etc.)
- Database terms (execution_entity, workflow_entity, finished=false)
- Technical implementation (PostgreSQL, n8n, Redis, AsyncRedisSaver)
- API details (HTTP Request, SMTP, timeout, connection string)
- Code/query syntax (SELECT, WHERE, JOIN)

✅ USA SOLO:
- Terminologia business (processi, esecuzioni, errori, step, email)
- Workflow names reali da context (ChatOne, Flow_X)
- Dati numerici (counts, percentuali, date)
- Descrizioni funzionali ("assistente email", "processo operativo")

⚠️ Responder node applicherà final masking, ma TU sei prima linea difesa.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ REGOLE FINALI:

1. ✅ system_context disponibile? Consultalo SEMPRE prima di rispondere
2. ✅ Traduci termini business via dizionario_business
3. ✅ Valida workflow names contro workflows_attivi.nomi
4. ✅ Clarification con dati reali da statistiche
5. ✅ Classifica in 1 delle 9 CATEGORIE (mapping diretto tool)
6. ✅ Chiama tool(s) appropriati (multipli se deep-dive)
7. ✅ Response business-friendly, NO technical terms
8. ✅ Emoji contestuali (⚠️📊✅📧⚡)
9. ✅ Limite 2 iterazioni disambiguazione
10. ✅ End sempre con "Altro?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Data corrente: {current_date}
Timezone: Europe/Rome
"""

        # v3.5.0: No ReAct Agent initialization (replaced by direct tool calls)

        logger.info("✅ v3.5.0 Architecture: Classifier (ReAct + memory) → Tool Mapper → Direct Execution → Responder")

        # Compile the graph with checkpointer for memory
        # v3.5.0: AsyncRedisSaver used by Classifier Agent (passed to create_react_agent)
        self.compiled_graph = graph.compile(
            checkpointer=self.external_checkpointer if self.external_checkpointer else MemorySaver(),
            debug=False
        )

        logger.info("MilhenaGraph compiled with Supervisor entry point + Memory")

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
        name="SupervisorOrchestrator",
        run_type="chain",
        metadata={"component": "supervisor", "version": "3.1"}
    )
    async def supervisor_orchestrator(self, state: MilhenaState) -> MilhenaState:
        """
        Supervisor Orchestrator: classifica query e decide routing
        Best Practice 2025: Supervisor non fa lavoro, solo coordina
        """
        query = state["query"]
        session_id = state["session_id"]

        logger.error(f"🔍 [DEBUG] SUPERVISOR CALLED with query: '{query[:80]}'")
        logger.info(f"[SUPERVISOR] Analyzing query: {query[:50]}...")

        # STEP 0: Instant classification (fast-path bypass LLM)
        instant = self._instant_classify(query)
        if instant:
            logger.error(f"🎯 [DEBUG] INSTANT MATCH: {instant['category']} - needs_db={instant.get('needs_database')}, needs_rag={instant.get('needs_rag')}")
            logger.info(f"[FAST-PATH] Instant match: {instant['category']} (bypassed LLM)")

            # Learn instant matches too (treat as high-confidence patterns)
            instant_with_confidence = {**instant, "confidence": 1.0}  # Instant = 100% confidence
            await self._maybe_learn_pattern(query, instant_with_confidence)

            decision = SupervisorDecision(**instant)
            state["supervisor_decision"] = decision.model_dump()  # Convert to dict for state
            state["waiting_clarification"] = False
            if decision.direct_response:
                state["response"] = decision.direct_response

            # FIX v3.4.1: Map category to intent (fast-path early return)
            category_to_intent_map = {
                "DANGER": "SECURITY",
                "HELP": "HELP",
                "GREETING": "GENERAL",
                "SIMPLE_QUERY": "STATUS",
                "SIMPLE_METRIC": "METRIC",
                "COMPLEX_QUERY": "ANALYSIS",
                "CLARIFICATION_NEEDED": "CLARIFICATION"
            }
            state["intent"] = category_to_intent_map.get(decision.category, "GENERAL")
            logger.info(f"[FAST-PATH] Mapped category '{decision.category}' → intent '{state['intent']}'")

            return state

        # STEP 1: Check Learning System (pattern già appresi)
        learned_pattern = await self.learning_system.check_learned_clarifications(
            query, session_id
        )

        if learned_pattern:
            # Pattern appreso! Skip clarification
            logger.info(f"[LEARNING] Pattern appreso: '{query[:30]}...' → {learned_pattern}")
            decision = SupervisorDecision(
                action="tool",  # Pattern appreso richiede DB query
                category="SIMPLE_METRIC",  # Assume learned pattern è sempre metric/status
                confidence=1.0,
                reasoning=f"Pattern appreso dal learning system: {learned_pattern}",
                direct_response=None,
                needs_rag=False,
                needs_database=True,
                clarification_options=None,
                llm_used="learning-system"
            )
            state["supervisor_decision"] = decision.model_dump()  # Convert to dict for state
            state["waiting_clarification"] = False
            return state

        # STEP 2: Classify con LLM
        # Prepare chat history (following LangGraph best practices)
        messages_history = state.get("messages", [])
        chat_history_str = ""
        context_additional = state.get("context", {})

        if len(messages_history) > 1:
            # Show last 4 messages for context (2 turns = user + assistant)
            recent = messages_history[-5:-1] if len(messages_history) > 5 else messages_history[:-1]

            # Format as conversation (Human/AI labels)
            formatted_msgs = []
            for msg in recent:
                if hasattr(msg, "content"):
                    role = "User" if isinstance(msg, HumanMessage) else "Milhena"
                    formatted_msgs.append(f"{role}: {msg.content[:150]}")

            chat_history_str = "\n".join(formatted_msgs)
        else:
            chat_history_str = "(Prima interazione - nessuna cronologia)"

        # Additional context (metadata, etc.)
        context_str = json.dumps(context_additional, indent=2) if context_additional else "{}"

        # v3.5.0: Use ReAct Agent with get_system_context_tool + CONVERSATION MEMORY
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        prompt = CLASSIFIER_PROMPT.format(query=query, current_date=current_date)

        # v3.5.1: Inject light context in prompt (RAM cache, 5min TTL)
        system_context_light = self._get_system_context_light()
        prompt_with_context = prompt + "\n\n" + system_context_light

        logger.info(f"🔍 [CLASSIFIER v3.5.2] Starting Simple LLM (no ReAct) - query: '{query}'")

        try:
            # v3.5.2: Simple LLM call (no ReAct overhead, context already in prompt)
            # Force OpenAI 4.1-nano for Classifier (Groq rate limit issues)
            base_model = self.supervisor_fallback  # Always use OpenAI gpt-4.1-nano

            # Build messages for LLM (context in system, query in user message)
            from langchain_core.messages import SystemMessage, HumanMessage

            messages = [
                SystemMessage(content=prompt_with_context),  # v3.5.1: Prompt + light context
                HumanMessage(content=query)
            ]

            # Direct LLM call (single shot, no tools, no loop)
            response = await base_model.ainvoke(messages)
            response_text = response.content

            logger.info(f"[CLASSIFIER v3.5.2] Simple LLM completed - response length: {len(response_text)} chars")

            # Parse JSON from response (agent should return JSON)
            import json
            try:
                classification = json.loads(response_text)
                logger.info(f"[CLASSIFIER v3.5.2] Parsed classification: {classification}")
            except json.JSONDecodeError:
                # Fallback: extract JSON from text
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    classification = json.loads(json_match.group(0))
                    logger.warning(f"[CLASSIFIER v3.5.2] Extracted JSON from text: {classification}")
                else:
                    # Ultimate fallback
                    logger.error(f"[CLASSIFIER v3.5.2] Failed to parse JSON from: {response_text}")
                    classification = self._fallback_classification(query)

            classification["llm_used"] = "openai-4.1-nano"  # v3.5.2: Always OpenAI for Classifier

        except Exception as e:
            logger.error(f"[CLASSIFIER v3.5.2] Simple LLM failed: {e}")
            classification = self._fallback_classification(query)
            classification["llm_used"] = "rule-based"
            logger.warning("[CLASSIFIER v3.5.2] Using rule-based fallback")

        # STEP 3: Save decision
        try:
            logger.error(f"[DEBUG] Creating SupervisorDecision with classification: {classification}")

            # FIX: Ensure all required fields exist with defaults
            required_defaults = {
                "action": "react",
                "category": "SIMPLE_QUERY",
                "confidence": 0.7,
                "reasoning": "Auto-generated",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": classification.get("llm_used", "unknown")
            }

            # Merge with defaults (classification wins)
            full_classification = {**required_defaults, **classification}

            logger.error(f"[DEBUG] FULL classification with defaults: {full_classification}")

            decision_obj = SupervisorDecision(**full_classification)
            # CRITICAL: Convert BaseModel to dict for LangGraph state compatibility
            decision = decision_obj.model_dump()
            state["supervisor_decision"] = decision
        except Exception as dec_error:
            logger.error(f"[CRITICAL] Failed to create SupervisorDecision: {dec_error}")
            logger.error(f"[CRITICAL] Classification keys: {list(classification.keys())}")
            logger.error(f"[CRITICAL] Classification values: {classification}")
            raise

        # STEP 3.5: Auto-learn pattern if high confidence (TODO-URGENTE.md)
        # Call after LLM classification to save high-confidence patterns
        await self._maybe_learn_pattern(query, classification)

        # STEP 4: Handle waiting clarification
        if decision["category"] == "CLARIFICATION_NEEDED":
            state["waiting_clarification"] = True
            state["original_query"] = query
            state["response"] = decision["direct_response"]
            logger.info(f"[SUPERVISOR] Waiting clarification with {len(decision.get('clarification_options', []))} options")
        else:
            state["waiting_clarification"] = False
            if decision["direct_response"]:
                # Direct response (GREETING, DANGER)
                state["response"] = decision["direct_response"]
                logger.info(f"[SUPERVISOR] Direct response for {decision['category']}")

        # STEP 5: If previous message was clarification, record pattern
        if state.get("context", {}).get("previous_clarification_asked"):
            original = state["context"].get("previous_query")
            if original and original != query:
                # User ha risposto alla clarification
                await self.learning_system.record_clarification(
                    original_query=original,
                    clarification=query,
                    session_id=session_id
                )
                # Clear flag
                state["context"]["previous_clarification_asked"] = False
                logger.info(f"[LEARNING] Recorded clarification: '{original[:30]}...' → '{query[:30]}...'")

        # STEP 6: If asking clarification, set flag for next message
        if decision["category"] == "CLARIFICATION_NEEDED":
            if "context" not in state:
                state["context"] = {}
            state["context"]["previous_clarification_asked"] = True
            state["context"]["previous_query"] = query

        logger.info(f"[SUPERVISOR] Decision: {decision['category']} → needs_rag={decision['needs_rag']}, needs_db={decision['needs_database']}")

        # FIX v3.4.1: Map supervisor category to user intent (LangGraph State best practice)
        # Source: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
        # Rationale: intent field was None for fast-path queries (bypassed IntentAnalyzer)
        category_to_intent_map = {
            "DANGER": "SECURITY",          # Security-sensitive queries
            "HELP": "HELP",                # Help/capability questions
            "GREETING": "GENERAL",         # Greetings
            "SIMPLE_QUERY": "STATUS",      # "quanti workflow?"
            "SIMPLE_METRIC": "METRIC",     # "quante esecuzioni?"
            "COMPLEX_QUERY": "ANALYSIS",   # Multi-step analysis
            "CLARIFICATION_NEEDED": "CLARIFICATION"
        }
        state["intent"] = category_to_intent_map.get(decision['category'], "GENERAL")
        logger.info(f"[SUPERVISOR] Mapped category '{decision['category']}' → intent '{state['intent']}'")

        return state

    # v3.5.0: load_system_context REMOVED
    # Classifier Agent (ReAct) calls get_system_context_tool() directly when needed

    def _fallback_classification(self, query: str) -> Dict[str, Any]:
        """
        Rule-based fallback quando LLM non disponibili
        """
        query_lower = query.lower()

        # DANGER keywords (expanded based on LangChain security best practices)
        danger_keywords = [
            "password", "credential", "api key", "secret", "token",
            "connessione database", "connection string", "dsn",
            "api_key", "access_token", "chiave", "credenziali",
            "passwd", "pwd", "auth token", "bearer token",
            "access key", "refresh token", "private key"
        ]
        if any(kw in query_lower for kw in danger_keywords):
            return {
                "action": "respond",
                "category": "DANGER",
                "confidence": 1.0,  # Maximum confidence for security
                "reasoning": "Blocco sicurezza: richiesta dati sensibili",
                "direct_response": "Non posso fornire informazioni su dati sensibili del sistema.",
                "needs_rag": False,
                "needs_database": False,
                "clarification_options": None
            }

        # CLARIFICATION patterns (ambiguous queries - based on CLAMBER research)
        ambiguous_patterns = [
            "dammi info", "info sul", "come va", "dimmi tutto", "cosa c'è",
            "novità", "come è andata", "come sono andate", "dimmi",
            "il sistema", "questo", "quello", "la cosa",
            "errori" if len(query_lower.split()) <= 2 else None,  # "errori" alone is ambiguous
            "report" if len(query_lower.split()) <= 2 else None,
            "dati" if len(query_lower.split()) <= 2 else None,
        ]
        ambiguous_patterns = [p for p in ambiguous_patterns if p]  # Remove None

        if any(pattern in query_lower for pattern in ambiguous_patterns):
            return {
                "action": "respond",
                "category": "CLARIFICATION_NEEDED",
                "confidence": 0.8,
                "reasoning": "Query ambigua: manca specificità",
                "direct_response": "Cosa vuoi sapere esattamente?\n\n📊 Status generale sistema\n❌ Errori e problemi\n📈 Metriche e statistiche\n🔄 Esecuzioni processi\n📝 Report dettagliati",
                "needs_rag": False,
                "needs_database": False,
                "clarification_options": ["status", "errori", "metriche", "esecuzioni", "report"]
            }

        # GREETING keywords
        greeting_keywords = ["ciao", "buongiorno", "buonasera", "salve", "hello", "grazie", "arrivederci"]
        if any(kw in query_lower for kw in greeting_keywords) and len(query.split()) <= 3:
            return {
                "action": "respond",
                "category": "GREETING",
                "confidence": 0.85,
                "reasoning": "Rule-based: saluto rilevato",
                "direct_response": "Ciao! Come posso aiutarti?",
                "needs_rag": False,
                "needs_database": False,
                "clarification_options": None
            }

        # SIMPLE_METRIC keywords
        metric_keywords = ["quant", "numer", "count", "quanti", "quante"]
        if any(kw in query_lower for kw in metric_keywords):
            return {
                "action": "tool",
                "category": "SIMPLE_METRIC",
                "confidence": 0.7,
                "reasoning": "Rule-based: keyword metrica rilevata",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None
            }

        # Default: CLARIFICATION (conservative - meglio chiedere che sbagliare)
        return {
            "action": "respond",
            "category": "CLARIFICATION_NEEDED",
            "confidence": 0.6,
            "reasoning": "Query non riconosciuta: richiesta chiarimento",
            "direct_response": "Puoi essere più specifico? Cosa vuoi sapere?\n\n📊 Status sistema\n❌ Errori\n📈 Metriche\n🔄 Processi\n📝 Report",
            "needs_rag": False,
            "needs_database": False,
            "clarification_options": ["status", "errori", "metriche", "processi", "report"]
        }

    def _get_system_context_light(self) -> str:
        """
        v3.5.1: Get light system context from RAM cache (5min TTL)
        Prevents tool loop by injecting context directly in prompt

        Returns:
            Light context string (~200 tokens vs 1800 full JSON)
        """
        import time

        # Check cache validity
        if self._system_context_cache and (time.time() - self._cache_timestamp < self._cache_ttl):
            logger.info("[CACHE HIT] Using cached system context")
            return self._system_context_cache

        # CACHE MISS - Query DB via tool
        logger.info("[CACHE MISS] Fetching fresh system context from DB")
        try:
            full_context = get_system_context_tool.invoke({})

            # Parse JSON response
            import json
            context_data = json.loads(full_context) if isinstance(full_context, str) else full_context

            # Build light version (top 5 workflows + essentials)
            workflows = context_data.get("workflows", {})
            workflow_list = workflows.get("workflow_list", [])[:5]  # Top 5 only
            workflow_names = ", ".join([f'"{w}"' for w in workflow_list])

            stats = context_data.get("statistics", {})

            # Light format (200 token vs 1800)
            light_context = f"""
CONTESTO SISTEMA (aggiornato):
- WORKFLOWS ATTIVI ({workflows.get('active_count', 0)}): {workflow_names}
- ESECUZIONI (7 giorni): {stats.get('executions_last_7_days', 0)}
- DIZIONARIO: "clienti"=Email ChatOne, "problemi"=Errori, "attività"=Esecuzioni, "passi"=Nodi, "workflow"=Processi
"""

            # Update cache
            self._system_context_cache = light_context
            self._cache_timestamp = time.time()
            logger.info(f"[CACHE UPDATED] Next refresh in {self._cache_ttl}s")

            return light_context

        except Exception as e:
            logger.error(f"[CACHE ERROR] Failed to fetch context: {e}")
            return ""  # Fallback to empty context

    def _instant_classify(self, query: str) -> Optional[Dict[str, Any]]:
        """
        v3.5.0 SIMPLIFIED Fast-Path Classification - ONLY SAFETY CHECKS

        Principle: Fast-path = ONLY safety (DANGER + GREETING)
        Everything else → LLM Classifier decides

        Reference: CONTEXT-SYSTEM.md v3.5.0 Phase 1

        Returns classification dict or None (= pass to LLM)
        """
        query_lower = query.lower().strip()

        # ============================================================================
        # SAFETY CHECK 1: DANGER Keywords (Security-First)
        # ============================================================================
        danger_keywords = [
            # Credentials & Secrets
            "password", "credenziali", "credential", "api key", "token",
            "secret", "chiave", "accesso admin", "root password",
            "connection string", "dsn", "db url", "database url",
            "api_key", "access_token", "bearer", "auth token",
            "passwd", "pwd", "private key", "refresh token",

            # Tech Stack & Architecture (prevent technical leaks)
            "flowwise", "langflow", "langgraph", "langchain",
            "flowise", "n8n", "postgresql", "postgres", "mysql",
            "redis", "chromadb", "docker", "kubernetes", "k8s",
            "architettura", "struttura sistema", "stack tecnologico",
            "tech stack", "tecnologie", "framework", "librerie",
            "che database", "quale database", "usate database",
            "che sistema", "quale sistema", "sistema usa",
            "come funziona sistema", "come è fatto", "strutturato il sistema",

            # Infrastructure terms
            "nginx", "apache", "server", "hosting", "cloud provider",
            "aws", "azure", "gcp", "digitalocean", "heroku",

            # Development tools
            "git", "github", "gitlab", "jenkins", "ci/cd", "pipeline"
        ]
        if any(kw in query_lower for kw in danger_keywords):
            return {
                "action": "respond",
                "category": "DANGER",
                "confidence": 1.0,
                "reasoning": "Blocco sicurezza immediato (fast-path)",
                "direct_response": "⚠️ Non posso fornire informazioni sull'architettura tecnica o dati sensibili. Per assistenza contatta l'amministratore.",
                "needs_rag": False,
                "needs_database": False,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # ============================================================================
        # GREETING: Quick Response for Common Greetings
        # ============================================================================
        greeting_exact = {"ciao", "buongiorno", "buonasera", "hello", "hi", "salve",
                         "grazie", "arrivederci", "buonanotte", "hey"}
        if query_lower in greeting_exact:
            return {
                "action": "respond",
                "category": "GREETING",
                "confidence": 1.0,
                "reasoning": "Saluto comune (fast-path)",
                "direct_response": "Ciao! Come posso aiutarti?",
                "needs_rag": False,
                "needs_database": False,
                "clarification_options": None,
                "llm_used": "fast-path"
            }

        # ============================================================================
        # PASS TO LLM CLASSIFIER (Everything else)
        # ============================================================================
        # v3.5.0: LLM handles ALL intelligence (AMBIGUOUS/SIMPLE classification)
        # Fast-path handles ONLY safety (DANGER + GREETING above)
        return None

    # ============================================================================
    # AUTO-LEARNING FAST-PATH - Pattern Learning System
    # Reference: TODO-URGENTE.md lines 256-338
    # ============================================================================

    def _normalize_query(self, query: str) -> str:
        """
        Normalize query for pattern matching by removing temporal words and punctuation.

        Examples:
            "ci sono problemi oggi?" → "ci sono problemi"
            "ci sono problemi adesso?" → "ci sono problemi"
            "Workflow attivi OGGI" → "workflow attivi"

        Args:
            query: Original user query

        Returns:
            Normalized query string (lowercase, no temporal words, no trailing punctuation)
        """
        import string

        query = query.lower().strip()

        # Split and strip punctuation from each word BEFORE temporal word check
        # This ensures "oggi?" becomes "oggi" and gets removed correctly
        words = query.split()
        words = [w.strip(string.punctuation) for w in words]

        # Remove common temporal words (TODO-URGENTE.md line 268)
        temporal_words = ['oggi', 'adesso', 'ora', 'attualmente', 'ieri', 'domani',
                         'stamattina', 'stasera', 'questa', 'settimana', 'questo', 'mese']
        words = [w for w in words if w not in temporal_words and w]  # Also remove empty strings

        # Join and remove any remaining trailing punctuation
        normalized = ' '.join(words).rstrip('?!.')

        return normalized

    async def _load_learned_patterns(self):
        """
        Load auto-learned patterns from PostgreSQL into in-memory cache.
        Called on __init__ and after new pattern learning.

        Query: SELECT normalized_pattern, category, confidence FROM auto_learned_patterns
               WHERE enabled = TRUE
               ORDER BY accuracy DESC
        """
        if not hasattr(self, 'db_pool') or self.db_pool is None:
            logger.warning("[AUTO-LEARN] DB pool not initialized, skipping pattern load")
            self.learned_patterns = {}
            return

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT
                        id,
                        pattern,
                        normalized_pattern,
                        category,
                        confidence,
                        accuracy,
                        times_used,
                        times_correct,
                        created_at,
                        last_used_at,
                        enabled,
                        status
                    FROM pilotpros.auto_learned_patterns
                    WHERE enabled = TRUE AND status = 'approved'
                    ORDER BY accuracy DESC, times_used DESC
                """)

                self.learned_patterns = {}
                for row in rows:
                    self.learned_patterns[row['normalized_pattern']] = {
                        'id': int(row['id']),
                        'pattern': row['pattern'],
                        'normalized_pattern': row['normalized_pattern'],
                        'category': row['category'],
                        'confidence': float(row['confidence']),
                        'accuracy': float(row['accuracy']),
                        'times_used': int(row['times_used']),
                        'times_correct': int(row['times_correct']) if row['times_correct'] else 0,
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                        'last_used_at': row['last_used_at'].isoformat() if row['last_used_at'] else None,
                        'enabled': row['enabled'],
                        'status': row['status'],
                        'source': 'auto_learned'
                    }

                logger.info(f"[AUTO-LEARN] Loaded {len(self.learned_patterns)} patterns from database")

        except Exception as e:
            logger.error(f"[AUTO-LEARN] Failed to load patterns: {e}")
            self.learned_patterns = {}

    async def reload_patterns(self):
        """
        Reload patterns from database (triggered by hot-reload PubSub).
        Thread-safe update of in-memory learned_patterns dict.

        This method is called by PatternReloader when Redis PubSub receives reload message.
        Expected latency: <100ms

        Usage:
            # Called by PatternReloader background task
            await milhena_graph.reload_patterns()
        """
        import time
        start_time = time.time()

        try:
            # Call existing load method (already thread-safe with asyncpg pool)
            await self._load_learned_patterns()

            reload_duration = (time.time() - start_time) * 1000  # Convert to ms
            logger.info(f"[HOT-RELOAD] Patterns reloaded in {reload_duration:.2f}ms ({len(self.learned_patterns)} patterns)")

        except Exception as e:
            logger.error(f"[HOT-RELOAD] Failed to reload patterns: {e}")

    def get_patterns(self) -> List[Dict[str, Any]]:
        """
        Get all loaded patterns with complete statistics.
        Returns list of pattern dictionaries for API consumption.

        NOTE: This returns only APPROVED patterns (from self.learned_patterns cache).
        For ALL patterns (pending, approved, disabled), use get_all_patterns_from_db().

        Returns:
            List of dicts with all pattern fields from database
        """
        patterns = []
        for normalized_pattern, data in self.learned_patterns.items():
            patterns.append({
                'id': data.get('id'),
                'pattern': data.get('pattern', normalized_pattern),
                'normalized_pattern': normalized_pattern,
                'category': data.get('category'),
                'confidence': data.get('confidence', 0.0),
                'accuracy': data.get('accuracy', 0.0),
                'times_used': data.get('times_used', 0),
                'times_correct': data.get('times_correct', 0),
                'created_at': data.get('created_at'),
                'last_used_at': data.get('last_used_at'),
                'enabled': data.get('enabled', True),
                'status': data.get('status', 'approved'),  # Default 'approved' for loaded patterns
                'source': data.get('source', 'auto_learned')
            })
        return patterns

    async def get_all_patterns_from_db(self) -> List[Dict[str, Any]]:
        """
        Get ALL patterns from database (pending, approved, disabled).
        Used by admin UI to manage pattern approvals.

        Query: SELECT * FROM auto_learned_patterns (NO status filter)
        Returns: List of all patterns with all fields including status
        """
        if not hasattr(self, 'db_pool') or self.db_pool is None:
            logger.warning("[ADMIN] DB pool not initialized, returning empty list")
            return []

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT
                        id,
                        pattern,
                        normalized_pattern,
                        category,
                        confidence,
                        accuracy,
                        times_used,
                        times_correct,
                        created_at,
                        last_used_at,
                        enabled,
                        status,
                        created_by
                    FROM pilotpros.auto_learned_patterns
                    ORDER BY created_at DESC
                """)

                patterns = []
                for row in rows:
                    patterns.append({
                        'id': int(row['id']),
                        'pattern': row['pattern'],
                        'normalized_pattern': row['normalized_pattern'],
                        'category': row['category'],
                        'confidence': float(row['confidence']),
                        'accuracy': float(row['accuracy']),
                        'times_used': int(row['times_used']),
                        'times_correct': int(row['times_correct']) if row['times_correct'] else 0,
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                        'last_used_at': row['last_used_at'].isoformat() if row['last_used_at'] else None,
                        'enabled': row['enabled'],
                        'status': row['status'],
                        'source': 'auto_learned'
                    })

                logger.info(f"[ADMIN] Retrieved {len(patterns)} patterns from database (all statuses)")
                return patterns

        except Exception as e:
            logger.error(f"[ADMIN] Failed to get all patterns: {e}")
            return []

    async def _maybe_learn_pattern(self, query: str, llm_result: Dict[str, Any]):
        """
        Auto-learn new pattern if LLM classification has high confidence (>0.9).
        Saves to PostgreSQL and updates in-memory cache.

        Args:
            query: Original user query
            llm_result: LLM classification result with confidence score

        Logic (TODO-URGENTE.md lines 281-313):
        1. Check confidence > 0.9
        2. Normalize query
        3. Check if pattern already exists
        4. If new: INSERT into database
        5. If existing: UPDATE times_used counter

        FIX 2025-10-13: Added DANGER validation to prevent security leaks from being learned
        """
        if not hasattr(self, 'db_pool') or self.db_pool is None:
            return  # Silently skip if DB not available

        # Only learn high-confidence classifications (TODO-URGENTE.md line 284)
        confidence = llm_result.get('confidence', 0.0)
        if confidence < 0.9:
            logger.info(f"[AUTO-LEARN] Skipped learning (confidence={confidence:.2f} < 0.9): '{query[:50]}'")
            return

        category = llm_result.get('category', '')
        if not category:
            return

        # FIX 2025-10-13: NEVER learn DANGER patterns (security risk)
        if category == "DANGER":
            logger.warning(f"[AUTO-LEARN] BLOCKED learning DANGER pattern: '{query[:50]}' (security policy)")
            return

        # FIX 2025-10-13: Validate query doesn't contain tech keywords (double-check)
        query_lower = query.lower()
        danger_tech_keywords = [
            "flowwise", "langchain", "langgraph", "database", "postgres",
            "stack", "architettura", "tecnologie", "framework"
        ]
        if any(kw in query_lower for kw in danger_tech_keywords):
            logger.warning(f"[AUTO-LEARN] BLOCKED learning tech query: '{query[:50]}' (contains: {[kw for kw in danger_tech_keywords if kw in query_lower]})")
            return

        # FIX 2025-10-13: BLOCK ambiguous queries (need clarification, not learning)
        ambiguous_terms = [
            "tabelle", "dati", "informazioni", "cose", "roba",
            "tutto", "dimmi tutto", "overview", "generale",
            "info", "dettagli generici"
        ]
        if any(term in query_lower for term in ambiguous_terms):
            matched_terms = [term for term in ambiguous_terms if term in query_lower]
            logger.warning(f"[AUTO-LEARN] BLOCKED ambiguous query: '{query[:50]}' (contains: {matched_terms}) - needs clarification")
            return

        logger.info(f"[AUTO-LEARN] High confidence detected! confidence={confidence:.2f}, category={category}")

        # Normalize query for pattern matching
        normalized = self._normalize_query(query)

        # Skip very short patterns (< 3 chars)
        if len(normalized) < 3:
            return

        try:
            async with self.db_pool.acquire() as conn:
                # Check if pattern already exists
                existing = await conn.fetchrow("""
                    SELECT id, times_used, times_correct, accuracy
                    FROM pilotpros.auto_learned_patterns
                    WHERE normalized_pattern = $1
                """, normalized)

                if existing:
                    # Update usage counter (TODO-URGENTE.md lines 297-302)
                    await conn.execute("""
                        UPDATE pilotpros.auto_learned_patterns
                        SET times_used = times_used + 1,
                            last_used_at = NOW()
                        WHERE id = $1
                    """, existing['id'])
                    logger.info(f"[AUTO-LEARN] Pattern reused: '{normalized}' (times_used={existing['times_used']+1})")
                else:
                    # Insert new pattern (TODO-URGENTE.md lines 303-312)
                    result = await conn.fetchrow("""
                        INSERT INTO pilotpros.auto_learned_patterns
                        (pattern, normalized_pattern, category, confidence, created_by)
                        VALUES ($1, $2, $3, $4, 'llm')
                        RETURNING id
                    """, query, normalized, category, confidence)
                    pattern_id = result['id']
                    logger.info(f"[AUTO-LEARN] New pattern saved: '{normalized}' → {category} (confidence={confidence:.2f}, id={pattern_id})")

                    # Reload patterns cache
                    await self._load_learned_patterns()

                    # Trigger hot-reload via Redis PubSub (notify all replicas)
                    from app.milhena.hot_reload import publish_reload_message
                    redis_url = os.getenv("REDIS_URL", "redis://redis-dev:6379/0")
                    await publish_reload_message(redis_url, pattern_id=pattern_id)

        except Exception as e:
            logger.error(f"[AUTO-LEARN] Failed to save pattern: {e}")

    # ============================================================================
    # REPHRASER NODES - Lightweight pre-check for ambiguous queries
    # ============================================================================

    @traceable(
        name="Rephraser_CheckAmbiguity",
        run_type="chain",
        metadata={"component": "rephraser", "version": "1.0"}
    )
    async def check_ambiguity(self, state: MilhenaState) -> MilhenaState:
        """
        Rule-based ambiguity detection (<10ms overhead).
        Checks if query is too vague for direct ReAct Agent processing.
        """
        # FIX 1: Initialize session_id if missing (LangGraph Studio compatibility)
        if "session_id" not in state:
            state["session_id"] = f"session-{datetime.now().timestamp()}"

        # Extract query from messages if not present
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

        query = state["query"].lower().strip()

        # Initialize rephraser metadata
        state["rephraser_triggered"] = False
        state["original_query"] = state["query"]

        import re

        # WHITELIST: Query chiare che NON devono essere rephrasate
        clear_patterns = [
            r"\bqual[ie]\s+(workflow|errori|processi|esecuzioni)",  # "quali workflow", "quali errori"
            r"\b(workflow|processi)\b.*(hanno|con|in)\b",  # "workflow che hanno errori"
            r"\b(lista|mostra|dammi)\s+(workflow|processi|tutti)",  # "lista workflow"
            r"\berrori\s+(di|in|del|nel)\s+\w+",  # "errori di [nome]"
            r"\binfo\s+su\s+\w+",  # "info su [nome]"
        ]

        # Se query matcha whitelist → CHIARA, skip rephrase
        is_clear = any(re.search(pattern, query) for pattern in clear_patterns)

        if is_clear:
            is_vague = False
        else:
            # Pattern 1: Generic pronouns without context (es: "flussi problematici", "dammi info")
            vague_patterns = [
                r"\bflussi?\b.*\bproblematic[oi]\b",  # flussi problematici
                r"\bdammi\b.*\binfo\b(?!\s+su)",  # dammi info (NON "dammi info su X")
                r"\bcom[e']?\s*(va|vanno)\b(?!\s+\w+)",  # come va/vanno (senza specificare cosa)
                r"\b(quello|quella|quelli|quelle)\b",  # pronomi dimostrativi vaghi
            ]

            # Pattern 2: Ultra-short queries (<3 words) excluding greetings
            word_count = len(query.split())
            is_greeting = any(greet in query for greet in ["ciao", "hello", "salve", "buongiorno", "hey"])

            # Pattern 3: Questions without subject (es: "come funziona?", "quanti sono?")
            vague_questions = [
                r"\bcome\s+(funziona|va|sono)\b(?!\s+\w+)",
                r"\bquant[oi]\b(?!\s+(workflow|errori|processi))",
                r"\bdove\s+(sono|va)\b(?!\s+\w+)",
            ]

            is_vague = (
                any(re.search(pattern, query) for pattern in vague_patterns) or
                any(re.search(pattern, query) for pattern in vague_questions) or
                (word_count < 3 and not is_greeting)
            )

        state["is_ambiguous"] = is_vague

        if is_vague:
            logger.warning(f"[REPHRASER] Query AMBIGUA rilevata: '{query[:80]}' - attivo rephrase")
        else:
            logger.info(f"[REPHRASER] Query CHIARA: '{query[:80]}' - procedo diretto")

        return state

    @traceable(
        name="Rephraser_RephraseQuery",
        run_type="chain",
        metadata={"component": "rephraser", "version": "1.0"}
    )
    async def rephrase_query(self, state: MilhenaState) -> MilhenaState:
        """
        LLM-based query rephrasing using Groq (fast & free).
        Reformulates ambiguous queries to match MAPPA TOOL patterns.
        """
        original_query = state["original_query"]

        # Safety: Max 1 rephrase attempt
        if state.get("rephraser_triggered"):
            logger.warning("[REPHRASER] Max 1 rephrase già eseguito - skip")
            return state

        rephrase_prompt = f"""Sei un assistente che riformula query vaghe in query precise.

Query originale: "{original_query}"

TOOL DISPONIBILI (target output):
1. get_all_errors_summary_tool() → "quali errori abbiamo?"
2. get_error_details_tool(workflow_name) → "errori di [NOME_WORKFLOW]"
3. get_workflow_details_tool(workflow_name) → "info su [NOME_WORKFLOW]"
4. get_workflows_tool() → "lista tutti i workflow"
5. get_executions_by_date_tool(date) → "esecuzioni del [DATA]"

Riformula la query per matchare uno dei pattern sopra.
Se la query è già chiara, restituiscila invariata.

ESEMPI:
Input: "flussi problematici"
Output: "quali workflow hanno errori?"

Input: "dammi info"
Output: "lista tutti i workflow"

Input: "come va quello?"
Output: "quali errori abbiamo nel sistema?"

Rispondi SOLO con la query riformulata, nessun testo extra."""

        try:
            # Use Groq (free + fast) for rephrasing
            llm = self.supervisor_llm if self.supervisor_llm else self.supervisor_fallback

            response = await llm.ainvoke(rephrase_prompt)
            rephrased = response.content.strip()

            state["query"] = rephrased
            state["rephraser_triggered"] = True
            state["messages"].append(AIMessage(content=f"[REPHRASER] Query riformulata: {rephrased}"))

            logger.info(f"[REPHRASER] Query riformulata: '{original_query}' → '{rephrased}'")

        except Exception as e:
            logger.error(f"[REPHRASER] Errore rephrasing: {e} - uso query originale")
            state["query"] = original_query

        return state

    def route_after_ambiguity_check(self, state: MilhenaState) -> str:
        """Routing function dopo check ambiguity"""
        if state.get("is_ambiguous", False):
            return "rephrase"
        else:
            return "proceed"

    # ============================================================================
    # OPTIMIZATION NODES
    # ============================================================================

    @traceable(
        name="MilhenaClassifyComplexity",
        run_type="chain",
        metadata={"component": "optimization", "version": "3.0"}
    )
    async def classify_complexity(self, state: MilhenaState) -> MilhenaState:
        """
        Classify query complexity for fast-path optimization.
        Simple queries skip disambiguation and RAG retrieval.
        """
        query = state["query"].lower()
        word_count = len(query.split())

        # Keywords for simple STATUS queries
        simple_keywords = [
            "come va", "come vanno", "status", "stato",
            "ciao", "hello", "salve", "buongiorno",
            "sistema", "funziona", "ok", "bene"
        ]

        # Keywords for simple GREETING queries
        greeting_keywords = ["ciao", "hello", "salve", "buongiorno", "buonasera", "hey"]

        # Classify as simple if:
        # 1. Short query (<10 words) AND
        # 2. Contains simple/greeting keywords
        is_simple = (
            word_count < 10 and
            any(keyword in query for keyword in simple_keywords + greeting_keywords)
        )

        state["context"]["is_simple_query"] = is_simple
        state["context"]["word_count"] = word_count

        if is_simple:
            logger.info(f"[OPTIMIZATION] Classified as SIMPLE query (words: {word_count})")
        else:
            logger.info(f"[OPTIMIZATION] Classified as COMPLEX query (words: {word_count})")

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
        """Execute database query based on intent

        Best Practice (LangChain 2025): Use tool.invoke({args}) instead of tool(args)
        """
        query = state["query"]
        intent = state.get("intent", "GENERAL")

        try:
            # Determine which tool to use based on intent and query
            query_lower = query.lower()

            # USER QUERIES
            if "utenti" in query_lower or "users" in query_lower:
                if "quanti" in query_lower or "count" in query_lower:
                    result = query_users_tool.invoke({"query_type": "count"})
                elif "attivi" in query_lower or "active" in query_lower:
                    result = query_users_tool.invoke({"query_type": "active"})
                else:
                    result = query_users_tool.invoke({"query_type": "all"})

            # EXECUTION QUERIES
            elif "esecuzione" in query_lower or "execution" in query_lower or "ultima" in query_lower:
                if "ultima" in query_lower or "last" in query_lower or "recente" in query_lower:
                    result = get_executions_tool.invoke({"query_type": "last"})
                elif "oggi" in query_lower or "today" in query_lower:
                    result = get_executions_tool.invoke({"query_type": "today"})
                elif "fallite" in query_lower or "errori" in query_lower or "failed" in query_lower:
                    result = get_executions_tool.invoke({"query_type": "failed"})
                else:
                    result = get_executions_tool.invoke({"query_type": "last"})

            # WORKFLOW QUERIES
            elif "workflow" in query_lower or "processo" in query_lower or "processi" in query_lower:
                if "attiv" in query_lower:
                    result = get_workflows_tool.invoke({"query_type": "active"})
                elif "inattiv" in query_lower or "disattiv" in query_lower:
                    result = get_workflows_tool.invoke({"query_type": "inactive"})
                elif "utilizzat" in query_lower or "usat" in query_lower or "top" in query_lower:
                    result = get_workflows_tool.invoke({"query_type": "top_used"})
                elif "compless" in query_lower or "nodi" in query_lower:
                    result = get_workflows_tool.invoke({"query_type": "complex"})
                elif "recen" in query_lower or "modificat" in query_lower:
                    result = get_workflows_tool.invoke({"query_type": "recent"})
                elif "error" in query_lower or "problem" in query_lower:
                    result = get_workflows_tool.invoke({"query_type": "errors"})
                else:
                    result = get_workflows_tool.invoke({"query_type": "all"})

            # PERFORMANCE QUERIES
            elif "performance" in query_lower or "velocit" in query_lower or "lent" in query_lower or "tasso" in query_lower:
                if "velocit" in query_lower or "lent" in query_lower or "speed" in query_lower:
                    result = get_performance_metrics_tool.invoke({"query_type": "speed"})
                elif "tasso" in query_lower or "success" in query_lower or "successo" in query_lower:
                    result = get_performance_metrics_tool.invoke({"query_type": "success_rate"})
                elif "trend" in query_lower or "andamento" in query_lower:
                    result = get_performance_metrics_tool.invoke({"query_type": "trends"})
                elif "bottleneck" in query_lower or "collo" in query_lower or "problema" in query_lower:
                    result = get_performance_metrics_tool.invoke({"query_type": "bottlenecks"})
                else:
                    result = get_performance_metrics_tool.invoke({"query_type": "overview"})

            # MONITORING QUERIES
            elif "monitoraggio" in query_lower or "alert" in query_lower or "salute" in query_lower or "health" in query_lower:
                if "alert" in query_lower or "avvisi" in query_lower or "warning" in query_lower:
                    result = get_system_monitoring_tool.invoke({"query_type": "alerts"})
                elif "coda" in query_lower or "queue" in query_lower:
                    result = get_system_monitoring_tool.invoke({"query_type": "queue"})
                elif "risorse" in query_lower or "resources" in query_lower:
                    result = get_system_monitoring_tool.invoke({"query_type": "resources"})
                elif "disponibilit" in query_lower or "availability" in query_lower or "uptime" in query_lower:
                    result = get_system_monitoring_tool.invoke({"query_type": "availability"})
                else:
                    result = get_system_monitoring_tool.invoke({"query_type": "health"})

            # ANALYTICS QUERIES
            elif "report" in query_lower or "analisi" in query_lower or "confronto" in query_lower or "roi" in query_lower:
                if "confronto" in query_lower or "comparison" in query_lower or "settiman" in query_lower:
                    result = get_analytics_tool.invoke({"query_type": "comparison"})
                elif "roi" in query_lower or "risparmio" in query_lower or "valore" in query_lower:
                    result = get_analytics_tool.invoke({"query_type": "roi"})
                elif "pattern" in query_lower or "utilizzo" in query_lower or "picco" in query_lower:
                    result = get_analytics_tool.invoke({"query_type": "patterns"})
                elif "prevision" in query_lower or "forecast" in query_lower or "proiezion" in query_lower:
                    result = get_analytics_tool.invoke({"query_type": "forecast"})
                else:
                    result = get_analytics_tool.invoke({"query_type": "summary"})

            # ERROR QUERIES (generic error checking)
            elif "errori" in query_lower or "error" in query_lower:
                # Check if it's about executions specifically
                if "esecuz" in query_lower:
                    result = get_executions_tool.invoke({"query_type": "failed"})
                else:
                    # Generic error check: use system monitoring
                    result = get_system_monitoring_tool.invoke({"query_type": "alerts"})

            # SYSTEM STATUS (default)
            elif "sistema" in query_lower or "status" in query_lower or "stato" in query_lower:
                result = get_system_monitoring_tool.invoke({"query_type": "health"})

            else:
                # Default: try to get general analytics
                result = get_analytics_tool.invoke({"query_type": "summary"})

            # Store result in context for response generation
            state["context"]["database_result"] = result
            logger.info(f"Database query executed: {result[:100]}...")

        except Exception as e:
            logger.error(f"Database query failed: {e}")
            state["context"]["database_error"] = str(e)

        return state

    # ============================================================================
    # v3.2 FLATTENED REACT NODES - Direct integration (no nested graph)
    # ============================================================================

    # v3.5.0: OLD react_call_model + route_react_loop REMOVED
    # Replaced by: Classifier (ReAct) → Tool Execution (direct) → Responder

    @traceable(
        name="MilhenaToolExecution",
        run_type="tool",
        metadata={"component": "tool_execution", "version": "3.5.0"}
    )
    async def execute_tools_direct(self, state: MilhenaState) -> MilhenaState:
        """
        v3.5.0: Direct tool execution (NO agent)

        Flow:
        1. Get category + params from classifier
        2. Map category → tool function(s)
        3. Call tool.invoke(params) directly
        4. Save RAW data in state (NO synthesis here)

        Synthesis happens in Responder Agent (separate node)
        """
        classification = state.get("supervisor_decision", {})
        category = classification.get("category")
        params = classification.get("params", {})

        logger.info(f"[TOOL EXECUTION v3.5.0] category={category}, params={params}")

        if not category:
            logger.error("[TOOL EXECUTION] No category in classification!")
            state["tool_results"] = []
            return state

        try:
            # Get tool function(s) from mapper
            tool_functions = map_category_to_tools(category)

            if not tool_functions:
                logger.warning(f"[TOOL EXECUTION] No tools mapped for category: {category}")
                state["tool_results"] = []
                return state

            # Execute tool(s) directly
            results = []
            for tool_fn in tool_functions:
                logger.info(f"[TOOL EXECUTION] Calling {tool_fn.name}...")

                # Call tool with params from classifier
                result = tool_fn.invoke(params)

                results.append({
                    "tool": tool_fn.name,
                    "result": result
                })
                logger.info(f"[TOOL EXECUTION] ✅ {tool_fn.name} completed")

            # Save RAW results (Responder will synthesize)
            state["tool_results"] = results
            logger.info(f"[TOOL EXECUTION] {len(results)} tool(s) executed successfully")

        except Exception as e:
            logger.error(f"[TOOL EXECUTION] Failed: {e}")
            state["tool_results"] = []
            state["context"]["tool_error"] = str(e)

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
            # Using correct API: search() returns List[Dict] directly
            from app.rag.maintainable_rag import UserLevel

            docs = await self.rag_system.search(
                query=query,
                top_k=3,
                user_level=UserLevel.BUSINESS
            )

            if docs and len(docs) > 0:
                state["rag_context"] = docs
                state["context"]["rag_docs"] = docs
                # Relevance score: 1.0 = perfect match, 0.0 = no match
                top_relevance = docs[0].get('relevance_score', 0.0)
                logger.info(f"Retrieved {len(docs)} RAG documents (top relevance: {top_relevance:.3f})")
            else:
                state["rag_context"] = []
                logger.info("No relevant RAG documents found")

        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            state["rag_context"] = []
            state["context"]["rag_error"] = str(e)

        return state

    # ============================================================================
    # v3.1 RESPONDER - Synthesizes user-friendly response from tool data
    # ============================================================================

    @traceable(
        name="MilhenaResponder",
        run_type="chain",
        metadata={"component": "responder", "version": "4.0"}
    )
    async def generate_final_response(self, state: MilhenaState) -> MilhenaState:
        """
        v3.5.0 RESPONDER: Synthesizes final user-friendly response from RAW tool data

        Separation of concerns:
        - Tool Execution: ONLY calls tools, returns RAW data in state["tool_results"]
        - Responder: ONLY synthesizes response from tool data
        """
        query = state["query"]
        classification = state.get("supervisor_decision", {}).get("category", "GENERAL")
        tool_results = state.get("tool_results", [])

        logger.info(f"[RESPONDER v3.5.0] Synthesizing response for: {query[:50]}")
        logger.info(f"[RESPONDER v3.5.0] Tool results: {len(tool_results)} tool(s)")

        if not tool_results:
            logger.warning("[RESPONDER] No tool results - generating fallback")
            state["response"] = "Non ho trovato dati specifici. Prova a riformulare la domanda."
            return state

        # Combine all tool data
        tool_data_parts = []
        for result in tool_results:
            tool_name = result.get("tool", "unknown")
            tool_result = result.get("result", "")
            tool_data_parts.append(f"[{tool_name}]\n{tool_result}")

        tool_data_combined = "\n\n".join(tool_data_parts)

        # Build Responder prompt
        responder_prompt = f"""Sei un RESPONSE GENERATOR per Milhena, assistente processi aziendali.

COMPITO: Sintetizza i dati ricevuti dai tools in una risposta user-friendly.

Query utente: "{query}"
Classification: {classification}

Dati tools (RAW):
{tool_data_combined}

REGOLE:
- Italiano chiaro e business-friendly
- Conciso ma completo
- Usa bullet points se ci sono 3+ elementi
- Numeri chiari (es: "145 esecuzioni oggi")
- Se ci sono trend, mostrali (es: "↑ +12% vs ieri")
- NON menzionare "workflow", "execution", "node" - usa linguaggio business

Genera risposta utile basata SOLO sui dati ricevuti."""

        try:
            # Try GROQ first (free + fast) per sintesi
            if self.groq_llm:
                response = await self.groq_llm.ainvoke(responder_prompt)
                final_response = response.content
                logger.info(f"[RESPONDER] GROQ response: {final_response[:100]}")
            else:
                # Fallback OpenAI
                response = await self.openai_llm.ainvoke(responder_prompt)
                final_response = response.content
                logger.info(f"[RESPONDER] OpenAI response: {final_response[:100]}")

            # Apply ResponseFormatter for consistent closing formulas and formatting
            from .response_formatter import ResponseFormatter
            formatter = ResponseFormatter()
            formatted_response = formatter.format(
                response=final_response,
                query=query,
                intent=classification,
                supervisor_decision=state.get("supervisor_decision")
            )

            state["response"] = formatted_response

        except Exception as e:
            logger.error(f"[RESPONDER] Failed: {e}")
            # Fallback: use first tool result as-is
            state["response"] = tool_results[0][:500] if tool_results else "Errore nella generazione della risposta."

        return state

    @traceable(name="MilhenaGenerateResponse_DEPRECATED")
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
                session_id=session_id,
                supervisor_decision=state.get("supervisor_decision")
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
                # Apply smart masking that preserves workflow names
                masked = self.masking_engine.mask(response)
                state["response"] = masked
                state["masked"] = True
                logger.info("Response masked (preserving workflow names)")
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
        intent = state.get("intent")  # v3.2 FIX: Optional intent (fast-path bypasses intent analysis)
        response = state.get("response", "")
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

    def route_from_supervisor(self, state: MilhenaState) -> str:
        """
        Route based on Supervisor ACTION decision.
        Best Practice 2025: Action-based routing (respond/tool/route)

        IMPORTANTE: TUTTI i path passano SEMPRE per mask_response prima di END
        """
        decision = state.get("supervisor_decision")

        logger.error(f"🚦 [DEBUG] ROUTING - decision={decision}")

        if not decision:
            logger.warning("[ROUTING] No supervisor decision, defaulting to full pipeline")
            return "apply_patterns"

        action = decision.get("action", "route")  # Default: route (conservative)
        category = decision["category"]

        logger.error(f"🚦 [DEBUG] ROUTING - action={action}, category={category}")

        # ACTION: respond
        # Supervisor ha già generato direct_response, vai direttamente a Mask
        if action == "respond":
            logger.info(f"[ROUTING] action=respond (category={category}) → mask_response")
            return "mask_response"

        # ACTION: tool
        # Serve DB query per dati, poi genera risposta e va a Mask
        if action == "tool":
            logger.error(f"🚀 [DEBUG] ROUTING TO DATABASE_QUERY NODE")
            logger.info(f"[ROUTING] action=tool (category={category}) → database_query → generate_response → mask_response")
            return "database_query"

        # ACTION: route
        # Full pipeline: Disambiguate → RAG → Generate → Mask
        if action == "route":
            logger.info(f"[ROUTING] action=route (category={category}) → apply_patterns (full pipeline)")
            return "apply_patterns"

        # Fallback (non dovrebbe mai succedere)
        logger.warning(f"[ROUTING] Unknown action '{action}', defaulting to full pipeline")
        return "apply_patterns"

    def route_from_complexity(self, state: MilhenaState) -> str:
        """
        Route based on query complexity for fast-path optimization.
        Simple queries skip disambiguation/RAG and go directly to response generation.
        """
        is_simple = state.get("context", {}).get("is_simple_query", False)

        if is_simple:
            logger.info("[OPTIMIZATION] Taking FAST PATH - skipping disambiguation and RAG")
            return "simple"
        else:
            logger.info("[OPTIMIZATION] Taking FULL PATH - complex query needs full pipeline")
            return "complex"

    # v3.5.0: OLD routing functions REMOVED (linear flow replaces conditional routing)
    # - route_supervisor_simplified (AMBIGUOUS/SIMPLE/COMPLEX branching)
    # - load_system_context (Classifier calls tool directly now)
    # - react_call_model + route_react_loop (replaced by Tool Execution)

    def route_from_intent(self, state: MilhenaState) -> str:
        """Route based on intent (DEPRECATED in v3.1 - kept for backward compatibility)"""
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
            # Check if top result has high relevance (relevance_score: 1.0 = perfect)
            top_relevance = rag_context[0].get("relevance_score", 0.0)
            if top_relevance > 0.8:
                logger.info(f"High-quality RAG result (relevance: {top_relevance:.3f}), skipping DB query")
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
            # Config with thread_id for conversation memory (Best Practice: LangGraph Checkpointer)
            # thread_id = session_id ensures each user has their own conversation history
            config = {
                "configurable": {
                    "thread_id": session_id
                }
            }

            # CRITICAL FIX: Load conversation history BEFORE invoking graph
            # So supervisor can access it in state["messages"]
            previous_messages = []
            try:
                # Get last checkpoint for this thread
                state_snapshot = self.compiled_graph.get_state(config)
                if state_snapshot and hasattr(state_snapshot, 'values') and state_snapshot.values:
                    # Extract messages from previous state
                    prev_msgs = state_snapshot.values.get("messages", [])
                    # Keep last 10 messages max (5 turns) to avoid context explosion
                    previous_messages = prev_msgs[-10:] if len(prev_msgs) > 10 else prev_msgs
                    logger.info(f"[MEMORY] Loaded {len(previous_messages)} previous messages from session {session_id}")
            except Exception as e:
                logger.warning(f"[MEMORY] Could not load previous state: {e}")
                # Continue without history if loading fails

            # Initialize state WITH conversation history
            initial_state = MilhenaState(
                messages=previous_messages + [HumanMessage(content=query)],  # History + new message
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
                learned_patterns=None,
                supervisor_decision=None,
                waiting_clarification=False,
                original_query=None
            )

            # Run the graph with config (checkpointer saves NEW state after execution)
            final_state = await self.compiled_graph.ainvoke(initial_state, config)

            # Extract supervisor decision for metadata
            supervisor_decision = final_state.get("supervisor_decision")

            # Return the result
            return {
                "success": True,
                "response": final_state.get("response"),
                "intent": final_state.get("intent"),
                "cached": final_state.get("cached", False),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "supervisor_decision": supervisor_decision,
                    "supervisor_category": supervisor_decision.get("category") if supervisor_decision else None,
                    "supervisor_action": supervisor_decision.get("action") if supervisor_decision else None,
                    "supervisor_confidence": supervisor_decision.get("confidence") if supervisor_decision else None
                }
            }

        except Exception as e:
            logger.error(f"Error in MilhenaGraph: {e}", exc_info=True)  # Show full traceback
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

    async def process_query(
        self,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process query with enhanced metadata for API compatibility.
        Alias for process() with additional metadata extraction.

        Args:
            query: User query
            session_id: Session identifier
            context: Optional context

        Returns:
            Response dictionary with metadata (supervisor_decision, processing_time, etc.)
        """
        import time
        start_time = time.time()

        # Call the base process method
        result = await self.process(query, session_id, context)

        # Add processing time
        processing_time = time.time() - start_time

        # Enhance metadata with supervisor decision if available
        # (extract from final state if needed)
        metadata = result.get("metadata", {})
        metadata["processing_time"] = processing_time

        # Return enhanced result
        return {
            "success": result.get("success", False),
            "response": result.get("response", "Come posso aiutarti?"),
            "metadata": metadata,
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0.95)
        }

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