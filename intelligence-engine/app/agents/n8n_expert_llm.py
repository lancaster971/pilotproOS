"""
N8n Expert Agent with REAL LLM
Specialized agent for n8n workflows using GPT-4o-mini
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


class N8nExpertAgent:
    """
    REAL N8n Expert Agent with GPT-4o-mini
    Specialized for workflow data extraction using ACTUAL LLM
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize N8n Expert with REAL LLM

        Args:
            openai_api_key: OpenAI API key (defaults to env var)
        """
        # Get API key
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for REAL agent")

        # Initialize REAL LLM
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            model="gpt-4o-mini",
            temperature=0.3,  # Lower temperature for more precise extraction
            max_tokens=1500,
            timeout=30,
            max_retries=2
        )

        # Specialized tools for n8n operations
        self.tools = [
            get_last_message_from_workflow,
            extract_webhook_data,
            search_workflow_messages,
            get_workflow_execution_history,
            extract_batch_messages
        ]

        # Memory for conversation
        self.memory = MemorySaver()

        # Specialized system prompt for n8n operations
        self.system_prompt = """You are an N8n Expert Agent specialized in workflow data extraction.

Your expertise includes:
1. Extracting messages from workflow executions
2. Analyzing webhook data and payloads
3. Retrieving execution history and statistics
4. Troubleshooting workflow issues

CRITICAL RULES:
- ALWAYS translate technical terms to business language:
  * workflow → processo
  * execution → elaborazione
  * node → fase
  * webhook → integrazione
  * error → anomalia
- NEVER expose technical details like SQL, JSON structure, or API internals
- Use the provided tools to get REAL data from the database
- If no data is found, explain clearly and suggest alternatives

You have access to specialized tools for:
- Getting messages from specific workflows
- Extracting webhook integration data
- Searching across all workflows
- Retrieving execution history
- Batch processing multiple workflows

When users ask about workflows, use the appropriate tool to get REAL data, then present it in a business-friendly format."""

        # Create REAL ReAct agent
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            checkpointer=self.memory
        )

        # Masking engine
        self.masking_engine = MultiLevelMaskingEngine()

        logger.info("N8n Expert Agent initialized with GPT-4o-mini")

    @traceable(name="N8nExpertLLMProcess")
    async def process(
        self,
        query: str,
        session_id: str,
        user_level: UserLevel = UserLevel.BUSINESS,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process n8n-related queries using REAL LLM

        Args:
            query: User query about workflows/n8n
            session_id: Session ID for continuity
            user_level: User authorization level
            context: Optional context

        Returns:
            Dict with response and metadata
        """
        start_time = datetime.now()

        try:
            # Config for agent with session
            config = {
                "configurable": {
                    "thread_id": session_id
                }
            }

            # Prepare messages with system prompt
            messages = {
                "messages": [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=query)
                ]
            }

            # Add context if provided
            if context:
                if "workflow_name" in context:
                    context_msg = f"Focus on workflow: {context['workflow_name']}"
                    messages["messages"].insert(0, SystemMessage(content=context_msg))

            # Invoke REAL agent
            logger.info(f"N8n Expert processing with GPT-4o-mini: {query[:50]}...")

            response = await self.agent.ainvoke(
                messages,
                config=config
            )

            # Extract response
            if response and "messages" in response:
                final_message = response["messages"][-1].content
            else:
                final_message = "Non sono riuscito ad estrarre i dati richiesti."

            # Apply masking
            masked_response = self.masking_engine.mask(
                final_message,
                user_level=user_level
            )

            # Metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            tokens_used = len(query.split()) * 1.5 + len(final_message.split()) * 1.5

            return {
                "success": True,
                "response": masked_response.masked,
                "agent_name": "n8n_expert",
                "processing_time": processing_time,
                "tokens_used": int(tokens_used),
                "cost": tokens_used * 0.00015 / 1000,  # GPT-4o-mini pricing
                "metadata": {
                    "session_id": session_id,
                    "user_level": user_level.value,
                    "llm_model": "gpt-4o-mini",
                    "tools_used": self._extract_tools_used(response),
                    "masking_applied": masked_response.replacements_made > 0,
                    "specialization": "n8n_workflows"
                }
            }

        except Exception as e:
            logger.error(f"N8n Expert LLM error: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()

            fallback = """Mi dispiace, ho riscontrato un problema nell'estrazione dei dati.

Posso comunque aiutarti con:
- Messaggi dai processi aziendali
- Cronologia delle elaborazioni
- Dati dalle integrazioni
- Analisi delle anomalie

Specifica il nome del processo o riprova."""

            return {
                "success": False,
                "response": fallback,
                "agent_name": "n8n_expert",
                "processing_time": processing_time,
                "error": str(e)
            }

    def _extract_tools_used(self, response: Dict) -> List[str]:
        """Extract which tools were used"""
        tools_used = []

        if response and "messages" in response:
            for msg in response["messages"]:
                if hasattr(msg, 'tool_calls'):
                    for tool_call in msg.tool_calls:
                        tools_used.append(tool_call.get("name", "unknown"))

                if hasattr(msg, 'additional_kwargs'):
                    if 'tool_calls' in msg.additional_kwargs:
                        for tc in msg.additional_kwargs['tool_calls']:
                            if 'function' in tc:
                                tools_used.append(tc['function'].get('name'))

        return list(set(tools_used))

    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ):
        """
        Execute for compatibility with base agent
        """
        session_id = session_id or f"n8n-session-{datetime.now().timestamp()}"

        result = await self.process(
            query=query,
            session_id=session_id,
            context=context
        )

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
        Check if this agent can handle n8n/workflow queries
        """
        query_lower = query.lower()

        # N8n specific keywords
        n8n_keywords = [
            "messaggio", "message",
            "workflow", "processo",
            "execution", "elaborazione",
            "webhook", "integrazione",
            "n8n", "automazione",
            "errore", "anomalia",
            "fatture", "ordini",  # Common workflow names
            "estrai", "mostra", "recupera"
        ]

        return any(keyword in query_lower for keyword in n8n_keywords)

    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "status": "active",
            "agent_name": "n8n_expert",
            "llm_model": "gpt-4o-mini",
            "capabilities": [
                "workflow_messages",
                "execution_data",
                "webhook_extraction",
                "error_analysis",
                "batch_processing"
            ],
            "tools_available": len(self.tools),
            "using_real_llm": True,
            "specialization": "n8n_workflows",
            "api_connected": bool(self.api_key)
        }


def create_n8n_expert_agent(api_key: Optional[str] = None) -> N8nExpertAgent:
    """Factory function to create N8n Expert agent"""
    return N8nExpertAgent(openai_api_key=api_key)