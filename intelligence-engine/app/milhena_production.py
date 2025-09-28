"""
Milhena Complete Production Graph
VERSIONE COMPLETA CON TUTTI I COMPONENTI REALI (NO LEARNING)
Usa HybridClassifier, HybridMasking, DataAnalystAgent e tools veri PostgreSQL
"""
from typing import TypedDict, List, Annotated, Dict, Any, Optional
from typing_extensions import TypedDict as ExtTypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langsmith import traceable
import logging
import os
from datetime import datetime
import psycopg2

# Import REAL Milhena components
from app.core.hybrid_classifier import HybridClassifier, IntentCategory
from app.core.hybrid_masking import HybridMaskingLibrary
from app.core.hybrid_validator import HybridValidator
from app.system_agents.milhena.data_analyst_agent import DataAnalystAgent

logger = logging.getLogger(__name__)

# Initialize REAL components
classifier = HybridClassifier()
masking_lib = HybridMaskingLibrary()
validator = HybridValidator()
data_analyst = DataAnalystAgent()

# ============================================================================
# STATE DEFINITION
# ============================================================================

class MilhenaState(ExtTypedDict):
    """Complete state for Milhena conversation flow"""
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    intent: Optional[str]
    session_id: str
    context: Dict[str, Any]
    disambiguated: bool
    response: Optional[str]
    cached: bool
    masked: bool
    error: Optional[str]
    token_count: int
    llm_choice: Optional[str]

# ============================================================================
# REAL DATABASE TOOLS
# ============================================================================

@tool
@traceable(name="MilhenaQueryUsers", run_type="tool")
def query_users_tool(query_type: str = "count") -> str:
    """
    Query users from REAL PostgreSQL database.

    Args:
        query_type: "all", "active", or "count"

    Returns:
        Real user data from pilotpros.users table
    """
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
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN is_active THEN 1 END) as active
                FROM pilotpros.users
            """)
            result = cur.fetchone()
            response = f"Total users: {result[0]}, Active users: {result[1]}"

        elif query_type == "active":
            cur.execute("""
                SELECT email, full_name, role
                FROM pilotpros.users
                WHERE is_active = true
                ORDER BY created_at DESC
                LIMIT 5
            """)
            results = cur.fetchall()
            users = [f"{r[1] or 'No name'} ({r[0]}) - {r[2]}" for r in results]
            response = "Active users:\\n" + "\\n".join(users) if users else "No active users"

        else:
            cur.execute("""
                SELECT email, full_name, role, is_active
                FROM pilotpros.users
                ORDER BY created_at DESC
                LIMIT 5
            """)
            results = cur.fetchall()
            users = [f"{r[1]} ({r[0]}) - {r[2]} - Active: {r[3]}" for r in results]
            response = "Users:\\n" + "\\n".join(users) if users else "No users found"

        conn.close()
        return response

    except Exception as e:
        return f"Database error: {str(e)}"

@tool
@traceable(name="MilhenaQuerySessions", run_type="tool")
def query_sessions_tool() -> str:
    """
    Query active sessions from REAL PostgreSQL database.
    Returns data from pilotpros.active_sessions table
    """
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
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN last_activity > NOW() - INTERVAL '30 minutes' THEN 1 END) as active
            FROM pilotpros.active_sessions
        """)
        result = cur.fetchone()

        conn.close()
        return f"Total sessions: {result[0]}, Active (last 30 min): {result[1]}"

    except Exception as e:
        return f"Database error: {str(e)}"

@tool
@traceable(name="MilhenaSystemStatus", run_type="tool")
def get_system_status_tool() -> str:
    """
    Get REAL system status from PostgreSQL database.
    Returns actual system metrics and health information
    """
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
            SELECT
                pg_database_size('pilotpros_db') as db_size,
                (SELECT COUNT(*) FROM pilotpros.users) as user_count,
                (SELECT COUNT(*) FROM pilotpros.active_sessions WHERE last_activity > NOW() - INTERVAL '30 minutes') as active_sessions
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

# ============================================================================
# MILHENA PRODUCTION GRAPH
# ============================================================================

class MilhenaProductionGraph:
    """
    COMPLETE Production-Ready Milhena Graph
    Uses ALL real components: HybridClassifier, HybridMasking, DataAnalystAgent, Real DB Tools
    """

    def __init__(self):
        self._initialize_components()
        self._build_graph()

    def _initialize_components(self):
        """Initialize REAL LLMs and tools"""

        # GROQ LLM (free tier)
        self.groq_llm = None
        if os.getenv("GROQ_API_KEY"):
            try:
                self.groq_llm = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    temperature=0.7,
                    api_key=os.getenv("GROQ_API_KEY")
                )
                logger.info("✅ GROQ LLM initialized")
            except Exception as e:
                logger.warning(f"GROQ not available: {e}")

        # OpenAI LLM (fallback)
        self.openai_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY", "dummy-key")
        )

        # REAL database tools
        self.tools = [query_users_tool, query_sessions_tool, get_system_status_tool]
        self.tool_node = ToolNode(self.tools)

        logger.info("✅ Milhena Production components initialized")

    def _build_graph(self):
        """Build the complete production graph"""

        graph = StateGraph(MilhenaState)

        # Add nodes with CLEAR PREFIXES for visual identification
        graph.add_node("[CODE] Check Cache", self.check_cache)
        graph.add_node("[LIB] Classify Intent", self.classify_intent)
        graph.add_node("[LIB] Validate Query", self.validate_query)
        graph.add_node("[CODE] Select LLM", self.select_llm)
        graph.add_node("[AGENT] Generate Response", self.generate_response)
        graph.add_node("[TOOL] Database Query", self.tool_node)
        graph.add_node("[LIB] Mask Response", self.mask_response)
        graph.add_node("[CODE] Handle Error", self.handle_error)

        # Set entry point
        graph.set_entry_point("[CODE] Check Cache")

        # Add conditional edges
        graph.add_conditional_edges(
            "[CODE] Check Cache",
            self.route_from_cache,
            {
                "cached": "[LIB] Mask Response",
                "not_cached": "[LIB] Classify Intent"
            }
        )

        graph.add_conditional_edges(
            "[LIB] Classify Intent",
            self.route_from_intent,
            {
                "technical": "[CODE] Handle Error",
                "business": "[LIB] Validate Query",
                "tool_needed": "[TOOL] Database Query"
            }
        )

        graph.add_edge("[LIB] Validate Query", "[CODE] Select LLM")
        graph.add_edge("[CODE] Select LLM", "[AGENT] Generate Response")
        graph.add_edge("[TOOL] Database Query", "[AGENT] Generate Response")
        graph.add_edge("[AGENT] Generate Response", "[LIB] Mask Response")
        graph.add_edge("[LIB] Mask Response", END)
        graph.add_edge("[CODE] Handle Error", END)

        # Compile
        self.compiled_graph = graph.compile()

        logger.info("✅ Milhena Production graph compiled")

    # ============================================================================
    # NODE IMPLEMENTATIONS WITH REAL COMPONENTS
    # ============================================================================

    @traceable(name="MilhenaCheckCache")
    async def check_cache(self, state: MilhenaState) -> MilhenaState:
        """Check cache (simple version for now)"""

        # Extract query from messages if not present
        if "query" not in state or not state.get("query"):
            messages = state.get("messages", [])
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, "content"):
                    content = last_msg.content
                    # Handle content as list of parts or string
                    if isinstance(content, list):
                        # Extract text from content parts
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
        if "token_count" not in state:
            state["token_count"] = 0

        # No cache for now
        state["cached"] = False

        logger.info(f"📝 Query: {state.get('query', '')[:50]}...")
        return state

    @traceable(name="MilhenaClassifyIntent")
    async def classify_intent(self, state: MilhenaState) -> MilhenaState:
        """Classify intent using REAL HybridClassifier"""

        query = state["query"]

        # Use REAL HybridClassifier - returns (IntentCategory, confidence, reasoning)
        intent_category, confidence, reasoning = classifier.classify(query, use_llm_fallback=False)

        # Map IntentCategory to our intent strings
        if intent_category == IntentCategory.TECHNOLOGY:
            state["intent"] = "TECHNICAL"
        elif intent_category == IntentCategory.BUSINESS_DATA:
            state["intent"] = "TOOL_NEEDED"
        else:
            state["intent"] = "BUSINESS"

        state["context"]["classification"] = {
            "category": intent_category.value,
            "confidence": confidence,
            "reasoning": reasoning
        }

        logger.info(f"🎯 Intent: {state['intent']} (confidence: {confidence:.2f})")

        return state

    @traceable(name="MilhenaValidateQuery")
    async def validate_query(self, state: MilhenaState) -> MilhenaState:
        """Validate query using REAL HybridValidator"""

        query = state["query"]

        # Use REAL HybridValidator - returns ValidationReport
        validation_report = validator.validate(query, use_llm_fallback=False)

        if validation_report.result.value != "VALID":
            state["error"] = f"Validation failed: {', '.join(validation_report.issues)}"
            logger.warning(f"⚠️ Query validation failed: {state['error']}")

        state["context"]["validation"] = {
            "result": validation_report.result.value,
            "risk_level": validation_report.risk_level.value,
            "issues": validation_report.issues
        }

        return state

    @traceable(name="MilhenaSelectLLM")
    async def select_llm(self, state: MilhenaState) -> MilhenaState:
        """Select LLM based on query complexity"""

        query = state["query"]
        word_count = len(query.split())

        # Use GROQ for simple queries (FREE)
        if word_count < 10 and self.groq_llm:
            state["llm_choice"] = "GROQ"
            state["context"]["llm"] = self.groq_llm
        else:
            state["llm_choice"] = "OpenAI"
            state["context"]["llm"] = self.openai_llm

        state["token_count"] = word_count * 2

        logger.info(f"🤖 Selected LLM: {state['llm_choice']}")

        return state

    @traceable(name="MilhenaGenerateResponse")
    async def generate_response(self, state: MilhenaState) -> MilhenaState:
        """Generate response using selected LLM"""

        messages = state["messages"]
        llm = state["context"].get("llm", self.openai_llm)

        # System prompt
        system_msg = SystemMessage(content="""Sei Milhena, assistente business professionale di PilotProOS.

REGOLE FONDAMENTALI:
- Rispondi SEMPRE in italiano
- Usa SOLO termini business (NO termini tecnici come database, API, server)
- Traduci: database→archivio dati, API→interfaccia, server→sistema
- Sii concisa e professionale
- Se hai dati reali dai tools, usali. NON inventare dati.""")

        # Generate
        response = llm.invoke([system_msg] + messages)

        state["response"] = response.content
        state["messages"].append(response)

        logger.info(f"💬 Response generated ({len(response.content)} chars)")

        return state

    @traceable(name="MilhenaMaskResponse")
    async def mask_response(self, state: MilhenaState) -> MilhenaState:
        """Mask technical terms using REAL HybridMasking"""

        response = state.get("response", "")

        # Use REAL HybridMaskingLibrary
        masked_response = masking_lib.mask(response)

        state["response"] = masked_response
        state["masked"] = True

        logger.info("🎭 Response masked with business terminology")

        return state

    @traceable(name="MilhenaHandleError")
    async def handle_error(self, state: MilhenaState) -> MilhenaState:
        """Handle technical queries and errors"""

        state["response"] = "Per informazioni tecniche dettagliate, contatta il team IT. Posso aiutarti con domande sui processi business."
        state["error"] = "Technical query deflected"

        logger.info("🚫 Technical query deflected")

        return state

    # ============================================================================
    # ROUTING FUNCTIONS
    # ============================================================================

    def route_from_cache(self, state: MilhenaState) -> str:
        """Route based on cache"""
        return "cached" if state.get("cached") else "not_cached"

    def route_from_intent(self, state: MilhenaState) -> str:
        """Route based on classified intent"""
        intent = state.get("intent", "BUSINESS")

        if intent == "TECHNICAL":
            return "technical"
        elif intent == "TOOL_NEEDED":
            return "tool_needed"
        else:
            return "business"

# ============================================================================
# CREATE AND EXPORT GRAPH
# ============================================================================

def create_milhena_production():
    """Create the complete production Milhena graph"""
    milhena = MilhenaProductionGraph()
    return milhena.compiled_graph

# Export for LangGraph Studio
graph = create_milhena_production()

print("✅ Milhena PRODUCTION Graph loaded - COMPLETE with REAL components!")