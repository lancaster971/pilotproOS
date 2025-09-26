"""
LangGraph ReAct Agent for PilotProOS
Production-ready agent with database tools and streaming support
"""

from typing import Dict, Any, List, Optional, Annotated, Sequence
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    AIMessage,
    ToolMessage
)
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from loguru import logger
import json
import time
import asyncio
from datetime import datetime

from .agent_tools import get_all_agent_tools, get_tools_description
from .config import settings

# ============================================================================
# SYSTEM PROMPT
# ============================================================================

PILOTPRO_SYSTEM_PROMPT = """You are an intelligent assistant for PilotProOS, a business process automation platform.

Your primary role is to help users by:
1. Answering questions about the system
2. Querying the PostgreSQL database for user and business data
3. Providing insights about system status and performance
4. Helping troubleshoot issues

## Available Tools:
{tools_description}

## Guidelines:
- Always be helpful and professional
- When asked about users, sessions, or business data, use the appropriate tools
- Explain your reasoning when making complex queries
- If a query fails, try an alternative approach
- Provide clear, concise answers based on the data
- Respect user privacy - only query what's necessary
- If you don't have enough information, ask for clarification

## Important:
- You have direct access to the PilotProOS PostgreSQL database
- All queries are read-only for safety
- Query results are limited to prevent overload
- Always verify data before providing answers

Current time: {current_time}
System: PilotProOS Intelligence Engine v2.0
Database: PostgreSQL with real-time data
"""

# ============================================================================
# REACT AGENT CLASS
# ============================================================================

class PilotProReActAgent:
    """
    Production-ready ReAct agent using LangGraph
    """

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.1,
        max_iterations: int = 10,
        use_memory: bool = True
    ):
        """
        Initialize the ReAct agent with LangGraph.

        Args:
            model_name: LLM model to use
            temperature: Model temperature (0-1)
            max_iterations: Maximum reasoning iterations
            use_memory: Enable conversation memory
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_iterations = max_iterations
        self.use_memory = use_memory

        # Initialize components
        self._setup_llm()
        self._setup_tools()
        self._setup_agent()

        logger.info(f"✅ PilotPro ReAct Agent initialized with {model_name}")

    def _setup_llm(self):
        """Initialize the language model"""
        try:
            self.llm = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                streaming=True,
                max_tokens=2000,
                openai_api_key=settings.OPENAI_API_KEY
            )
            logger.info(f"LLM initialized: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            # Fallback to a simpler model
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=self.temperature,
                streaming=True
            )
            logger.warning("Fallback to gpt-3.5-turbo")

    def _setup_tools(self):
        """Setup all agent tools"""
        self.tools = get_all_agent_tools()
        logger.info(f"Loaded {len(self.tools)} tools: {[t.name for t in self.tools]}")

    def _setup_agent(self):
        """Setup the LangGraph ReAct agent"""
        # Create system prompt
        tools_desc = get_tools_description()
        self.system_prompt = PILOTPRO_SYSTEM_PROMPT.format(
            tools_description=tools_desc,
            current_time=datetime.now().isoformat()
        )

        # Setup memory if enabled
        if self.use_memory:
            self.checkpointer = MemorySaver()
        else:
            self.checkpointer = None

        # Create the ReAct agent using LangGraph
        # The prompt parameter accepts a SystemMessage or string
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self.system_prompt,  # This will be added as SystemMessage
            checkpointer=self.checkpointer
        )

        logger.info("ReAct agent created with LangGraph")

    async def chat(
        self,
        message: str,
        session_id: str = "default",
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Process a chat message through the ReAct agent.

        Args:
            message: User message
            session_id: Session ID for memory
            stream: Enable streaming responses

        Returns:
            Dict with response and metadata
        """
        start_time = time.time()

        try:
            # Prepare configuration
            # Formula: recursion_limit = 2 * max_iterations + 1
            # For 5 tool calls: 2 * 5 + 1 = 11
            config = {
                "configurable": {"thread_id": session_id},
                "recursion_limit": 2 * self.max_iterations + 1  # Correct formula from LangGraph docs
            }

            # Create message (system prompt already added via prompt parameter)
            messages = [HumanMessage(content=message)]

            logger.info(f"Processing message for session {session_id}: {message[:100]}...")

            if stream:
                # Stream the response
                response_text = ""
                tool_calls = []

                async for event in self.agent.astream(
                    {"messages": messages},
                    config,
                    stream_mode="values"
                ):
                    # Get the last message
                    last_message = event["messages"][-1]

                    if isinstance(last_message, AIMessage):
                        response_text = last_message.content

                        # Check for tool calls
                        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                            tool_calls.extend([tc['name'] for tc in last_message.tool_calls])

                    elif isinstance(last_message, ToolMessage):
                        # Tool response received
                        logger.debug(f"Tool response: {last_message.content[:100]}...")

            else:
                # Non-streaming response
                result = await self.agent.ainvoke(
                    {"messages": messages},
                    config
                )

                # Get the final AI message
                final_message = result["messages"][-1]
                response_text = final_message.content if isinstance(final_message, AIMessage) else str(final_message)

                # Extract tool calls
                tool_calls = []
                for msg in result["messages"]:
                    if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_calls.extend([tc['name'] for tc in msg.tool_calls])

            processing_time = int((time.time() - start_time) * 1000)

            # Log the interaction
            logger.info(f"Response generated in {processing_time}ms using tools: {tool_calls}")

            return {
                "success": True,
                "response": response_text,
                "session_id": session_id,
                "model": self.model_name,
                "tools_used": list(set(tool_calls)),
                "processing_time_ms": processing_time,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in ReAct agent: {str(e)}")
            processing_time = int((time.time() - start_time) * 1000)

            return {
                "success": False,
                "response": "Mi dispiace, si è verificato un errore nell'elaborazione della richiesta. Per favore riprova.",
                "error": str(e),
                "session_id": session_id,
                "model": self.model_name,
                "processing_time_ms": processing_time,
                "timestamp": datetime.now().isoformat()
            }

    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session ID

        Returns:
            List of messages in the session
        """
        if not self.checkpointer:
            return []

        try:
            config = {"configurable": {"thread_id": session_id}}
            state = await self.agent.aget_state(config)

            history = []
            if state and "messages" in state.values:
                for msg in state.values["messages"]:
                    if isinstance(msg, HumanMessage):
                        history.append({"role": "human", "content": msg.content})
                    elif isinstance(msg, AIMessage):
                        history.append({"role": "assistant", "content": msg.content})

            return history

        except Exception as e:
            logger.error(f"Error getting session history: {e}")
            return []

    async def clear_session(self, session_id: str) -> bool:
        """
        Clear conversation history for a session.

        Args:
            session_id: Session ID

        Returns:
            Success status
        """
        if not self.checkpointer:
            return True

        try:
            config = {"configurable": {"thread_id": session_id}}
            # Clear by starting fresh conversation
            await self.agent.ainvoke(
                {"messages": []},
                config
            )
            logger.info(f"Cleared session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            return False

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about the agent configuration.

        Returns:
            Dict with agent information
        """
        return {
            "type": "ReAct Agent (LangGraph)",
            "model": self.model_name,
            "temperature": self.temperature,
            "max_iterations": self.max_iterations,
            "memory_enabled": self.use_memory,
            "tools": [t.name for t in self.tools],
            "tool_count": len(self.tools),
            "version": "2.0"
        }

# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_agent_instance: Optional[PilotProReActAgent] = None

def get_react_agent(
    model_name: str = None,
    temperature: float = None,
    force_new: bool = False
) -> PilotProReActAgent:
    """
    Get or create the ReAct agent instance.

    Args:
        model_name: Override default model
        temperature: Override default temperature
        force_new: Force create new instance

    Returns:
        PilotProReActAgent instance
    """
    global _agent_instance

    if force_new or _agent_instance is None:
        # Use defaults from settings if not provided
        if model_name is None:
            model_name = settings.DEFAULT_LLM_MODEL if settings.DEFAULT_LLM_MODEL else "gpt-4o-mini"
        if temperature is None:
            temperature = settings.DEFAULT_TEMPERATURE if settings.DEFAULT_TEMPERATURE else 0.1

        _agent_instance = PilotProReActAgent(
            model_name=model_name,
            temperature=temperature,
            max_iterations=10,
            use_memory=True
        )
        logger.info("Created new ReAct agent instance")

    return _agent_instance

# ============================================================================
# TESTING FUNCTION
# ============================================================================

async def test_agent():
    """Test function for the ReAct agent"""
    agent = get_react_agent()

    test_queries = [
        "Quanti utenti ci sono nel sistema?",
        "Mostra gli ultimi 5 utenti registrati",
        "Quali sono le sessioni attive?",
        "Qual è lo stato del sistema?",
        "Cerca utenti con ruolo admin"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")

        result = await agent.chat(query)

        if result["success"]:
            print(f"Response: {result['response']}")
            print(f"Tools used: {result['tools_used']}")
            print(f"Time: {result['processing_time_ms']}ms")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    # Test the agent
    import asyncio
    asyncio.run(test_agent())