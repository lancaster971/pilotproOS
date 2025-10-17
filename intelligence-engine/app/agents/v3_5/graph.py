"""
AgentGraph v3.5.6 - Minimal LangGraph Orchestrator

SELF-CONTAINED ARCHITECTURE:
- Imports 6 components from self-contained modules
- ONLY LangGraph wiring (add_node, add_edge, routing, compile)
- ZERO business logic (delegated to components)

Components:
1. Fast-Path (fast_path.py) - DANGER/GREETING checks
2. Classifier (classifier.py) - LLM classification
3. Tool Mapper (tool_mapper.py) - Category → Tools
4. Tool Executor (tool_executor.py) - Async execution
5. Responder (responder.py) - LLM synthesis
6. Masking (masking.py) - Business masking

Reference: CONTEXT-SYSTEM.md v3.5.5
"""
import os
import logging
from typing import Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

# Self-contained component imports
from app.agents.v3_5.fast_path import FastPath
from app.agents.v3_5.classifier import Classifier
from app.agents.v3_5.tool_mapper import map_category_to_tools
from app.agents.v3_5.tool_executor import execute_tools_direct
from app.agents.v3_5.responder import Responder
from app.agents.v3_5.masking import Masking
from app.agents.v3_5.utils.state import AgentState
from app.agents.v3_5.utils.masking import TechnicalMaskingEngine
from app.agents.v3_5.utils.learning import LearningSystem

logger = logging.getLogger(__name__)


class AgentGraph:
    """
    Minimal LangGraph Orchestrator - v3.5.6 Self-Contained Architecture

    Responsibility: ONLY LangGraph wiring
    Business logic: Delegated to 6 self-contained components
    """

    def __init__(
        self,
        openai_llm,
        groq_llm,
        db_pool,
        rag_system=None,
        external_checkpointer: Optional[BaseCheckpointSaver] = None,
        system_context_cache=None,
        cache_ttl=300
    ):
        """Initialize AgentGraph with 6 self-contained components"""

        # Store dependencies
        self.openai_llm = openai_llm
        self.groq_llm = groq_llm
        self.db_pool = db_pool
        self.rag_system = rag_system
        self.external_checkpointer = external_checkpointer

        # Initialize utility systems
        self.masking_engine = TechnicalMaskingEngine()
        self.learning_system = LearningSystem()  # Uses default storage_path

        # Initialize 6 self-contained components
        logger.info("🔧 Initializing 6 self-contained components...")

        # Component 1: Fast-Path
        self.fast_path = FastPath()
        logger.info("✅ [1/6] Fast-Path initialized")

        # Component 2: Classifier
        self.classifier = Classifier(
            supervisor_llm=openai_llm,
            db_pool=db_pool,
            system_context_cache=system_context_cache,
            cache_ttl=cache_ttl
        )
        logger.info("✅ [2/6] Classifier initialized")

        # Component 3: Tool Mapper (function, no class)
        # Already imported as map_category_to_tools
        logger.info("✅ [3/6] Tool Mapper ready")

        # Component 4: Tool Executor (function, no class)
        # Already imported as execute_tools_direct
        logger.info("✅ [4/6] Tool Executor ready")

        # Component 5: Responder
        self.responder = Responder(
            groq_llm=groq_llm,
            openai_llm=openai_llm
        )
        logger.info("✅ [5/6] Responder initialized")

        # Component 6: Masking
        self.masking = Masking(masking_engine=self.masking_engine)
        logger.info("✅ [6/6] Masking initialized")

        # Build LangGraph
        self.compiled_graph = self._build_graph()
        logger.info("🎯 AgentGraph v3.5.6 compiled successfully")

    def _build_graph(self):
        """
        Build LangGraph with 6-component pipeline

        ONLY wiring logic - NO business logic
        """
        graph = StateGraph(AgentState)

        # ====================================================================
        # NODES: 6-step pipeline
        # ====================================================================

        # Step 1: Fast-Path (DANGER + GREETING instant checks)
        graph.add_node("[FAST-PATH]", self.fast_path.check)

        # Step 2: Classifier (Simple LLM with context)
        graph.add_node("[AI] Classifier", self.classifier.classify)

        # Step 3: Tool Execution (direct async calls)
        graph.add_node("[TOOL] Execute Tools", execute_tools_direct)

        # Step 4: Responder (RAW data → business language)
        graph.add_node("[AI] Responder", self.responder.generate_final_response)

        # Step 5: Masking (technical → business terminology)
        graph.add_node("[LIB] Mask Response", self.masking.mask_response)

        # Step 6: Feedback recording
        graph.add_node("[DB] Record Feedback", self._record_feedback)

        # ====================================================================
        # ROUTING: Entry point + conditional edges
        # ====================================================================

        # Entry point: Fast-Path (first check)
        graph.set_entry_point("[FAST-PATH]")

        # Router 1: After Fast-Path
        # If match (DANGER/GREETING) → END immediately
        # Otherwise → Continue to Classifier
        def route_after_fast_path(state: AgentState) -> str:
            """Route after Fast-Path: END if match, else Classifier"""
            if state.get("response"):
                logger.info("[ROUTER] Fast-Path match detected → END immediately")
                return END
            else:
                logger.info("[ROUTER] No Fast-Path match → Continue to Classifier")
                return "[AI] Classifier"

        graph.add_conditional_edges(
            "[FAST-PATH]",
            route_after_fast_path,
            {
                END: END,
                "[AI] Classifier": "[AI] Classifier"
            }
        )

        # Router 2: After Classifier
        # If CLARIFICATION_NEEDED or direct response → END
        # Otherwise → Continue to Tool Execution
        def route_after_classifier(state: AgentState) -> str:
            """Route after Classifier: END if direct_response, else tools"""
            if state.get("response"):
                logger.info("[ROUTER] Classifier direct response → END")
                return END
            else:
                logger.info("[ROUTER] Classifier needs tools → Continue to Tool Execution")
                return "[TOOL] Execute Tools"

        graph.add_conditional_edges(
            "[AI] Classifier",
            route_after_classifier,
            {
                END: END,
                "[TOOL] Execute Tools": "[TOOL] Execute Tools"
            }
        )

        # ====================================================================
        # LINEAR FLOW: Tools → Responder → Masking → Feedback → END
        # ====================================================================

        graph.add_edge("[TOOL] Execute Tools", "[AI] Responder")
        graph.add_edge("[AI] Responder", "[LIB] Mask Response")
        graph.add_edge("[LIB] Mask Response", "[DB] Record Feedback")
        graph.add_edge("[DB] Record Feedback", END)

        # ====================================================================
        # COMPILE: With checkpointer for memory
        # ====================================================================

        if self.external_checkpointer:
            logger.info("✅ Using AsyncRedisSaver checkpointer (7-day TTL)")
        else:
            logger.warning("⚠️  No external checkpointer - memory disabled")

        compiled = graph.compile(
            checkpointer=self.external_checkpointer if self.external_checkpointer else MemorySaver(),
            debug=False
        )

        logger.info("✅ LangGraph compiled with 6-node pipeline")
        return compiled

    async def _record_feedback(self, state: AgentState) -> AgentState:
        """Record interaction for learning (node implementation)"""
        query = state["query"]
        intent = state.get("intent")
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

    async def reload_patterns(self):
        """Reload patterns from database (hot-reload trigger)"""
        await self.learning_system._load_learned_patterns()
        logger.info(f"[HOT-RELOAD] Patterns reloaded ({len(self.learning_system.learned_patterns)} patterns)")

    async def process_query(self, query: str, session_id: str, context: dict) -> dict:
        """Process query through compiled graph"""
        from langchain_core.messages import HumanMessage

        result = await self.compiled_graph.ainvoke(
            {
                "messages": [HumanMessage(content=query)],
                "query": query,
                "session_id": session_id,
                "context": context
            },
            config={"configurable": {"thread_id": session_id}}
        )

        return {
            "success": True,
            "response": result.get("response", ""),
            "metadata": {"masked": result.get("masked", False)},
            "sources": [],
            "confidence": 0.95
        }


# ============================================================================
# FACTORY FUNCTION: Singleton pattern for LangGraph Studio
# ============================================================================

_agent_graph_instance = None

def get_agent_graph(
    openai_llm=None,
    groq_llm=None,
    db_pool=None,
    rag_system=None,
    external_checkpointer=None,
    system_context_cache=None,
    cache_ttl=300
) -> AgentGraph:
    """
    Get or create AgentGraph singleton instance

    Used by LangGraph Studio and main.py
    """
    global _agent_graph_instance

    if _agent_graph_instance is None:
        # First call - create instance
        _agent_graph_instance = AgentGraph(
            openai_llm=openai_llm,
            groq_llm=groq_llm,
            db_pool=db_pool,
            rag_system=rag_system,
            external_checkpointer=external_checkpointer,
            system_context_cache=system_context_cache,
            cache_ttl=cache_ttl
        )
        logger.info("✅ AgentGraph singleton created")

    return _agent_graph_instance


# ============================================================================
# EXPORT: For LangGraph Studio
# ============================================================================

# This will be initialized by main.py lifespan with proper dependencies
agent_graph = None  # Placeholder - set by main.py after async initialization
