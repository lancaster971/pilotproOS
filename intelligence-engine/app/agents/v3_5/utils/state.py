"""
Milhena State Models - v3.5.5

Pydantic models and TypedDict definitions for LangGraph state management.
"""
from typing import List, Dict, Any, Optional, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


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
    params: Optional[Dict[str, Any]] = None  # v3.5.5: NEW - Tool parameters from classifier
    suggested_tool: Optional[str] = None  # v3.5.0: DEPRECATED (context injected in prompt)
    llm_used: str


class AgentState(TypedDict):
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
    tool_results: Optional[List[Dict[str, Any]]]  # Tool execution results (v3.5.6)

    # NEW: Supervisor fields
    supervisor_decision: Optional[SupervisorDecision]
    waiting_clarification: bool
    original_query: Optional[str]  # For learning
    fast_path_match: bool  # True if fast-path handled query (DANGER/GREETING)
