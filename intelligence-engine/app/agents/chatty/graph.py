"""
Chatty Agent - Minimal Self-Contained Chat Implementation

Pure conversational agent with no tools, no classification, just simple chat.
Perfect demonstration of v3.5.6 self-contained architecture.
"""
import os
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import logging

from .state import ChattyState

logger = logging.getLogger(__name__)


class ChattyGraph:
    """
    Chatty Agent - Pure Chat Implementation

    Simple single-node graph that just responds to messages.
    No tools, no classification, no complexity - just conversation.
    """

    def __init__(self):
        """Initialize Chatty Agent"""
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=500,
            api_key=os.getenv("GROQ_API_KEY")
        )

        # Build graph
        self.compiled_graph = self._build_graph()

        logger.info("✅ Chatty Agent initialized - Pure chat mode")

    def _build_graph(self) -> Any:
        """Build minimal LangGraph with single chat node"""

        # Define workflow
        workflow = StateGraph(ChattyState)

        # Single node: chat
        workflow.add_node("chat", self._chat_node)

        # Simple flow: start → chat → end
        workflow.set_entry_point("chat")
        workflow.add_edge("chat", END)

        # Compile with memory checkpointer
        checkpointer = MemorySaver()
        compiled = workflow.compile(checkpointer=checkpointer)

        logger.info("✅ Chatty graph compiled (1 node: chat)")

        return compiled

    async def _chat_node(self, state: ChattyState) -> ChattyState:
        """
        Pure chat node - just respond to last message

        Args:
            state: Current state with messages

        Returns:
            Updated state with AI response
        """
        messages = state["messages"]

        # Get last user message
        last_message = messages[-1] if messages else HumanMessage(content="Ciao!")

        logger.info(f"[Chatty] Received: {last_message.content[:50]}...")

        # System prompt for friendly chat
        system_prompt = """Sei Chatty, un assistente conversazionale amichevole e simpatico.

Rispondi in modo naturale, cordiale e conciso.
Usa un tono informale e spontaneo.
Massimo 2-3 frasi per risposta."""

        # Get LLM response
        full_messages = [
            HumanMessage(content=system_prompt),
            last_message
        ]

        response = await self.llm.ainvoke(full_messages)

        logger.info(f"[Chatty] Responded: {response.content[:50]}...")

        # Update state
        return {
            "messages": messages + [response],
            "response": response.content
        }

    async def process(self, query: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Process a chat query

        Args:
            query: User message
            session_id: Session identifier for memory

        Returns:
            Response dict with success, response, etc.
        """
        try:
            logger.info(f"[Chatty] Processing query: {query[:50]}...")

            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=query)],
                "response": ""
            }

            # Run graph
            config = {"configurable": {"thread_id": session_id}}
            result = await self.compiled_graph.ainvoke(initial_state, config)

            return {
                "success": True,
                "response": result["response"],
                "model": "chatty-v1.0",
                "session_id": session_id
            }

        except Exception as e:
            logger.error(f"[Chatty] Error: {e}")
            return {
                "success": False,
                "response": f"Oops! Qualcosa è andato storto: {str(e)}",
                "model": "chatty-v1.0",
                "session_id": session_id
            }
