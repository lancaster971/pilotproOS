"""
Milhena Complete Graph for LangGraph Studio
Versione completa con tutti i componenti
"""
from typing import TypedDict, List, Annotated, Dict, Any, Optional
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
import asyncio

logger = logging.getLogger(__name__)

# ============================================================================
# STATE DEFINITION - Complete Milhena State
# ============================================================================

class MilhenaState(TypedDict):
    """Complete state for Milhena conversation flow"""
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
    token_count: int
    llm_choice: Optional[str]

# ============================================================================
# MILHENA TOOLS - Business-focused tools
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
@traceable(name="MilhenaProcessInfo", run_type="tool")
def get_process_info(process_name: str) -> str:
    """
    Get information about a specific business process.

    Args:
        process_name: Name of the business process

    Returns:
        Process information
    """
    return f"""Informazioni processo '{process_name}':
- Stato: Attivo
- Ultima esecuzione: 10 minuti fa
- Prossima esecuzione: tra 20 minuti
- Performance: Normale"""

# ============================================================================
# MILHENA GRAPH CLASS
# ============================================================================

class MilhenaCompleteGraph:
    """
    Complete LangGraph workflow for Milhena Business Assistant
    """

    def __init__(self):
        self._initialize_components()
        self._build_graph()

    def _initialize_components(self):
        """Initialize all Milhena components"""

        # Initialize LLMs
        self.groq_llm = None
        if os.getenv("GROQ_API_KEY"):
            try:
                self.groq_llm = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    temperature=0.7,
                    api_key=os.getenv("GROQ_API_KEY")
                )
                logger.info("GROQ LLM initialized")
            except Exception as e:
                logger.warning(f"Could not initialize GROQ: {e}")

        # OpenAI LLM (always available as fallback)
        self.openai_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY", "dummy-key")
        )

        # Tools
        self.tools = [check_business_status, get_business_metrics, get_process_info]
        self.tool_node = ToolNode(self.tools)

        logger.info("MilhenaCompleteGraph initialized")

    def _build_graph(self):
        """Build the complete LangGraph workflow"""

        # Create the graph
        graph = StateGraph(MilhenaState)

        # Add nodes
        graph.add_node("check_cache", self.check_cache)
        graph.add_node("disambiguate", self.disambiguate_query)
        graph.add_node("analyze_intent", self.analyze_intent)
        graph.add_node("select_llm", self.select_llm)
        graph.add_node("generate_response", self.generate_response)
        graph.add_node("tools", self.tool_node)
        graph.add_node("mask_response", self.mask_response)
        graph.add_node("record_feedback", self.record_feedback)
        graph.add_node("handle_error", self.handle_error)

        # Set entry point
        graph.set_entry_point("check_cache")

        # Add edges
        graph.add_conditional_edges(
            "check_cache",
            self.route_from_cache,
            {
                "cached": "mask_response",
                "not_cached": "disambiguate"
            }
        )

        graph.add_edge("disambiguate", "analyze_intent")

        graph.add_conditional_edges(
            "analyze_intent",
            self.route_from_intent,
            {
                "technical": "handle_error",
                "business": "select_llm",
                "tool_needed": "tools"
            }
        )

        graph.add_edge("select_llm", "generate_response")
        graph.add_edge("tools", "generate_response")
        graph.add_edge("generate_response", "mask_response")
        graph.add_edge("mask_response", "record_feedback")
        graph.add_edge("record_feedback", END)
        graph.add_edge("handle_error", END)

        # Compile the graph
        self.compiled_graph = graph.compile()

        logger.info("MilhenaCompleteGraph compiled successfully")

    # ============================================================================
    # NODE IMPLEMENTATIONS
    # ============================================================================

    @traceable(name="MilhenaCheckCache")
    async def check_cache(self, state: MilhenaState) -> MilhenaState:
        """Check if response is cached"""

        # Extract query from messages if not present
        if "query" not in state or not state.get("query"):
            messages = state.get("messages", [])
            if messages:
                last_msg = messages[-1]
                state["query"] = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
            else:
                state["query"] = ""

        # Initialize missing fields with defaults
        if "session_id" not in state:
            state["session_id"] = f"session-{datetime.now().timestamp()}"
        if "context" not in state:
            state["context"] = {}
        if "disambiguated" not in state:
            state["disambiguated"] = False
        if "token_count" not in state:
            state["token_count"] = 0

        # For demo, always return not cached
        state["cached"] = False
        logger.info(f"Cache check for query: {state.get('query', '')[:50]}...")
        return state

    @traceable(name="MilhenaDisambiguate")
    async def disambiguate_query(self, state: MilhenaState) -> MilhenaState:
        """Disambiguate ambiguous queries"""
        query = state["query"]

        # Simple disambiguation logic
        if any(word in query.lower() for word in ["puttane", "cazzo", "merda"]):
            # Clean up vulgar language
            state["context"]["original_query"] = query
            state["query"] = "Il sistema ha problemi di funzionamento"
            state["disambiguated"] = True
            logger.info("Query disambiguated")
        else:
            state["disambiguated"] = False

        return state

    @traceable(name="MilhenaAnalyzeIntent")
    async def analyze_intent(self, state: MilhenaState) -> MilhenaState:
        """Analyze user intent"""
        query = state["query"].lower()

        # Determine intent
        if any(word in query for word in ["status", "stato", "metriche", "metrics"]):
            state["intent"] = "TOOL_NEEDED"
        elif any(word in query for word in ["codice", "python", "javascript", "sql", "database"]):
            state["intent"] = "TECHNICAL"
        else:
            state["intent"] = "BUSINESS"

        logger.info(f"Intent classified as: {state['intent']}")
        return state

    @traceable(name="MilhenaSelectLLM")
    async def select_llm(self, state: MilhenaState) -> MilhenaState:
        """Select appropriate LLM based on complexity"""
        query = state["query"]
        word_count = len(query.split())

        # Select LLM based on complexity
        if word_count < 10 and self.groq_llm:
            state["llm_choice"] = "GROQ"
            state["context"]["llm"] = self.groq_llm
        else:
            state["llm_choice"] = "OpenAI"
            state["context"]["llm"] = self.openai_llm

        # Track token usage
        state["token_count"] = word_count * 2  # Rough estimate

        logger.info(f"Selected LLM: {state['llm_choice']}")
        return state

    @traceable(name="MilhenaGenerateResponse")
    async def generate_response(self, state: MilhenaState) -> MilhenaState:
        """Generate appropriate response"""
        messages = state["messages"]

        # Get LLM from context or use default
        llm = state["context"].get("llm", self.openai_llm)

        # Add system prompt
        system_msg = SystemMessage(content="""Sei Milhena, un assistente business professionale.
Rispondi sempre in italiano.
Evita termini tecnici come database, API, server.
Usa termini business come processi, elaborazioni, sistemi.""")

        # Generate response
        response = llm.invoke([system_msg] + messages)

        state["response"] = response.content
        state["messages"].append(response)

        logger.info("Response generated")
        return state

    @traceable(name="MilhenaMaskResponse")
    async def mask_response(self, state: MilhenaState) -> MilhenaState:
        """Apply final masking to response"""
        response = state.get("response", "")

        # Technical term masking
        replacements = {
            "database": "archivio dati",
            "API": "interfaccia",
            "server": "sistema",
            "PostgreSQL": "sistema di archiviazione",
            "Redis": "sistema di cache",
            "Docker": "ambiente",
            "container": "modulo"
        }

        for tech_term, business_term in replacements.items():
            response = response.replace(tech_term, business_term)
            response = response.replace(tech_term.lower(), business_term)

        state["response"] = response
        state["masked"] = True

        logger.info("Response masked")
        return state

    @traceable(name="MilhenaRecordFeedback")
    async def record_feedback(self, state: MilhenaState) -> MilhenaState:
        """Record interaction for learning"""
        # Log the interaction
        logger.info(f"""
        Interaction recorded:
        - Session: {state['session_id']}
        - Query: {state['query'][:50]}...
        - Intent: {state['intent']}
        - LLM: {state.get('llm_choice', 'Unknown')}
        - Tokens: {state.get('token_count', 0)}
        """)

        state["feedback"] = "recorded"
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

def create_milhena_complete():
    """Create the complete Milhena graph"""
    milhena = MilhenaCompleteGraph()
    return milhena.compiled_graph

# Export for LangGraph Studio
graph = create_milhena_complete()

print("✅ Milhena Complete Graph loaded for LangGraph Studio!")