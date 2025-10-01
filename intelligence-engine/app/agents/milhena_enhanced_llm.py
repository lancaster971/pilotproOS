"""
Enhanced Milhena Agent with REAL LLM
Business assistant using GPT-4o-mini for intelligent responses
REAL AGENT - NO MOCK - NO SIMPLIFIED VERSION
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

from app.tools.n8n_message_tools import (
    get_last_message_from_workflow,
    extract_webhook_data,
    search_workflow_messages,
    get_workflow_execution_history,
    extract_batch_messages
)
from app.security import MultiLevelMaskingEngine, UserLevel

import logging
logger = logging.getLogger(__name__)


class EnhancedMilhenaAgent:
    """
    REAL Milhena Agent with GPT-4o-mini
    Business assistant with n8n expertise using ACTUAL LLM
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize Enhanced Milhena with REAL LLM

        Args:
            openai_api_key: OpenAI API key (defaults to env var)
        """
        # Get API key from env if not provided
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for REAL agent")

        # Initialize REAL LLM
        # FIX 2: Use request_timeout (not timeout) + reduce retries
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1000,
            request_timeout=30.0,
            max_retries=1
        )

        # Tools for the agent
        self.tools = [
            get_last_message_from_workflow,
            extract_webhook_data,
            search_workflow_messages,
            get_workflow_execution_history,
            extract_batch_messages
        ]

        # Memory for conversation continuity
        self.memory = MemorySaver()

        # System prompt for Milhena
        self.system_prompt = """Tu sei Milhena, l'assistente aziendale intelligente di PilotProOS.

Il tuo ruolo è:
1. Assistere gli utenti con i processi aziendali
2. Fornire informazioni sui workflow (chiamati "processi")
3. Estrarre e presentare dati in modo business-friendly
4. NON menzionare MAI termini tecnici come: n8n, workflow, node, PostgreSQL, Docker, LangGraph

Regole di comunicazione:
- Usa SEMPRE terminologia business (processo invece di workflow)
- Rispondi in italiano in modo professionale ma amichevole
- Se non hai dati, suggerisci come ottenerli
- Maschera sempre i dettagli tecnici

Hai accesso a tools per:
- Estrarre messaggi dai processi
- Verificare stato elaborazioni
- Analizzare cronologia
- Cercare informazioni

Usa questi tools quando necessario per rispondere con dati REALI."""

        # Create REAL ReAct agent
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            checkpointer=self.memory
        )

        # Masking engine for output
        self.masking_engine = MultiLevelMaskingEngine()

        logger.info("Enhanced Milhena Agent initialized with GPT-4o-mini")

    @traceable(name="MilhenaLLMProcess")
    async def process(
        self,
        query: str,
        session_id: str,
        user_level: UserLevel = UserLevel.BUSINESS,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process query using REAL LLM with tools

        Args:
            query: User query in natural language
            session_id: Session ID for conversation continuity
            user_level: User authorization level for masking
            context: Optional conversation context

        Returns:
            Dict with response and metadata
        """
        start_time = datetime.now()

        try:
            # Prepare config for agent with session
            config = {
                "configurable": {
                    "thread_id": session_id
                }
            }

            # Prepare the input message with system prompt
            messages = {
                "messages": [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=query)
                ]
            }

            # Add context if provided
            if context:
                context_msg = f"Contesto precedente: {context}"
                messages["messages"].insert(0, SystemMessage(content=context_msg))

            # Invoke REAL agent with LLM
            logger.info(f"Invoking Milhena with GPT-4o-mini for: {query[:50]}...")

            response = await self.agent.ainvoke(
                messages,
                config=config
            )

            # Extract the final message
            if response and "messages" in response:
                final_message = response["messages"][-1].content
            else:
                final_message = "Mi dispiace, non sono riuscita a elaborare la richiesta."

            # Apply masking based on user level
            masked_response = self.masking_engine.mask(
                final_message,
                user_level=user_level
            )

            # Calculate metrics
            processing_time = (datetime.now() - start_time).total_seconds()

            # Estimate tokens (rough approximation)
            tokens_used = len(query.split()) * 1.5 + len(final_message.split()) * 1.5

            return {
                "success": True,
                "response": masked_response.masked,
                "agent_name": "milhena_enhanced",
                "processing_time": processing_time,
                "tokens_used": int(tokens_used),
                "cost": tokens_used * 0.00015 / 1000,  # GPT-4o-mini pricing
                "metadata": {
                    "session_id": session_id,
                    "user_level": user_level.value,
                    "llm_model": "gpt-4o-mini",
                    "tools_used": self._extract_tools_used(response),
                    "masking_applied": masked_response.replacements_made > 0
                }
            }

        except Exception as e:
            logger.error(f"Milhena LLM processing error: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()

            # Fallback response
            fallback = """Mi dispiace, ho riscontrato un problema temporaneo.

Posso comunque aiutarti con:
- Stato dei processi aziendali
- Informazioni sulle elaborazioni
- Analisi delle performance

Riprova tra qualche istante o riformula la domanda."""

            return {
                "success": False,
                "response": fallback,
                "agent_name": "milhena_enhanced",
                "processing_time": processing_time,
                "error": str(e)
            }

    def _extract_tools_used(self, response: Dict) -> List[str]:
        """Extract which tools were used in the response"""
        tools_used = []

        if response and "messages" in response:
            for msg in response["messages"]:
                # Check if message is a tool call
                if hasattr(msg, 'tool_calls'):
                    for tool_call in msg.tool_calls:
                        tools_used.append(tool_call.get("name", "unknown"))

                # Check for function calls in content
                if hasattr(msg, 'additional_kwargs'):
                    if 'tool_calls' in msg.additional_kwargs:
                        for tc in msg.additional_kwargs['tool_calls']:
                            if 'function' in tc:
                                tools_used.append(tc['function'].get('name', 'unknown'))

        return list(set(tools_used))  # Remove duplicates

    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ):
        """
        Execute method for compatibility with base agent interface
        """
        session_id = session_id or f"session-{datetime.now().timestamp()}"

        result = await self.process(
            query=query,
            session_id=session_id,
            context=context
        )

        # Convert to AgentResult format for compatibility
        from app.agents.base_agent import AgentResult

        return AgentResult(
            success=result["success"],
            output=result["response"],
            agent_name=result["agent_name"],
            processing_time=result["processing_time"],
            tokens_used=result.get("tokens_used"),
            cost=result.get("cost"),
            metadata=result.get("metadata", {}),
            error=result.get("error")
        )

    def can_handle(self, query: str, intent: Optional[str] = None) -> bool:
        """
        Check if Milhena can handle the query
        As primary agent, handles most general business queries
        """
        # Milhena is the default agent and handles most queries
        query_lower = query.lower()

        # Always handle greetings
        greetings = ["ciao", "buongiorno", "salve", "hello"]
        if any(g in query_lower for g in greetings):
            return True

        # Handle status and general queries
        general_keywords = ["stato", "come va", "aiuto", "help", "processo", "elaborazione"]
        if any(k in query_lower for k in general_keywords):
            return True

        # Default to True as primary agent
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "status": "active",
            "agent_name": "milhena_enhanced",
            "llm_model": "gpt-4o-mini",
            "capabilities": [
                "greeting",
                "status_check",
                "workflow_info",
                "message_extraction",
                "general_assistance"
            ],
            "tools_available": len(self.tools),
            "using_real_llm": True,
            "api_connected": bool(self.api_key)
        }


# For backward compatibility
def create_milhena_agent(api_key: Optional[str] = None) -> EnhancedMilhenaAgent:
    """Factory function to create Milhena agent"""
    return EnhancedMilhenaAgent(openai_api_key=api_key)