"""
n8n Integration Endpoints - API/Webhook Communication
Direct communication between LangChain Agents and n8n workflows
NO CUSTOM NODES - Only standard HTTP Request/Webhook integration
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
import asyncio
import json
from urllib.parse import urlparse

# LangChain imports for agent functionality
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.tools import Tool
from langchain.memory import ConversationBufferWindowMemory

from .llm_manager import get_llm_manager
from .config import settings
# Import NEW ReAct Agent instead of old CustomerSupportAgent
from .langchain_react_agent import get_react_agent
from loguru import logger

router = APIRouter(prefix="/api/n8n", tags=["n8n-integration"])

# ============================================================================
# CUSTOMER SUPPORT AGENT ENDPOINT FOR n8n HTTP REQUEST NODE
# ============================================================================

class CustomerSupportRequest(BaseModel):
    """Request for customer support agent"""
    message: str = Field(..., description="Customer question or issue")
    customer_id: Optional[str] = Field(default=None, description="Customer ID for context")
    email: Optional[str] = Field(default=None, description="Customer email for lookup")
    session_id: Optional[str] = Field(default="default", description="Session ID for conversation")

@router.post("/agent/customer-support")
async def customer_support_chat(request: CustomerSupportRequest):
    """
    Customer Support Agent - Called by n8n HTTP Request Node

    n8n HTTP Request Configuration:
    - Method: POST
    - URL: http://pilotpros-intelligence-engine:8000/api/n8n/agent/customer-support
    - Body: {"message": "user question", "customer_id": "123"}

    Returns customer support response with database lookups
    """
    try:
        logger.info(f"🎧 Customer support request: {request.message[:50]}...")

        # Use customer_id or try to extract from email
        customer_context = request.customer_id or request.email

        # Use NEW ReAct agent instead of old customer support
        react_agent = get_react_agent()

        # Add customer context to message if provided
        enhanced_message = request.message
        if customer_context:
            enhanced_message = f"[Customer ID: {customer_context}] {request.message}"

        result = await react_agent.chat(
            message=enhanced_message,
            session_id=request.session_id
        )

        if result.get("success"):
            logger.info(f"✅ Customer support completed in {result.get('response_time', 0):.1f}s")

            return {
                "success": True,
                "agent_response": result["response"],
                "response_time": result.get("processing_time_ms", 0) / 1000,
                "customer_id": customer_context,
                "session_id": request.session_id,
                "agent_type": "customer_support",
                "database_used": len(result.get("tools_used", [])) > 0,
                "timestamp": result["timestamp"]
            }
        else:
            logger.error(f"❌ Customer support error: {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error"),
                "fallback_response": result.get("response"),
                "agent_type": "customer_support"
            }

    except Exception as e:
        logger.error(f"❌ Customer support endpoint error: {e}")
        return {
            "success": False,
            "error": str(e),
            "fallback_response": "I apologize, our support system is temporarily unavailable. Please try again later."
        }

@router.get("/agent/customer-support")
async def customer_support_get(message: str, customer_id: Optional[str] = None, session_id: str = "default"):
    """
    Customer Support Agent - GET version for simple n8n HTTP Request

    n8n HTTP Request Configuration:
    - Method: GET
    - URL: http://pilotpros-intelligence-engine:8000/api/n8n/agent/customer-support
    - Query Params: message="user question"&customer_id="123"

    Simpler for n8n configuration
    """
    try:
        # Convert GET to POST format
        request = CustomerSupportRequest(
            message=message,
            customer_id=customer_id,
            session_id=session_id
        )

        # Use the same logic as POST
        return await customer_support_chat(request)

    except Exception as e:
        logger.error(f"❌ Customer support GET error: {e}")
        return {
            "success": False,
            "error": str(e),
            "fallback_response": "Support system error. Please try again."
        }

# ============================================================================
# PYDANTIC MODELS FOR n8n COMMUNICATION
# ============================================================================

class AgentChatRequest(BaseModel):
    """Chat with LangChain Agent via n8n HTTP Request Node"""
    message: str = Field(..., description="User message to agent")
    agent_type: str = Field(default="general", description="Agent type: general, business, analysis")
    model: Optional[str] = Field(default=None, description="Override default model")
    temperature: Optional[float] = Field(default=0.7, description="LLM temperature")
    max_tokens: Optional[int] = Field(default=2000, description="Max response tokens")
    session_id: Optional[str] = Field(default="default", description="Session for conversation memory")
    n8n_webhook_url: Optional[str] = Field(default=None, description="Webhook URL for response callback")

class AgentTaskRequest(BaseModel):
    """Execute specific task with LangChain Agent"""
    task_type: str = Field(..., description="Task type: analyze, summarize, extract, generate")
    input_data: Dict[str, Any] = Field(..., description="Task input data")
    instructions: Optional[str] = Field(default="", description="Additional instructions")
    model: Optional[str] = Field(default=None, description="Override default model")
    n8n_webhook_url: Optional[str] = Field(default=None, description="Webhook URL for results")

class WorkflowTriggerRequest(BaseModel):
    """Trigger n8n workflow from LangChain Agent"""
    workflow_id: Optional[str] = Field(default=None, description="n8n workflow ID")
    webhook_url: str = Field(..., description="n8n webhook URL to trigger")
    data: Dict[str, Any] = Field(..., description="Data to send to workflow")
    wait_for_completion: bool = Field(default=False, description="Wait for workflow completion")

class N8nResponse(BaseModel):
    """Standard response format for n8n integration"""
    success: bool
    data: Dict[str, Any] = {}
    error: Optional[str] = None
    agent_info: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ============================================================================
# AGENT MANAGEMENT
# ============================================================================

class LangChainAgentManager:
    """Manage LangChain Agents for n8n integration"""

    def __init__(self):
        self.agents: Dict[str, AgentExecutor] = {}
        self.memories: Dict[str, ConversationBufferWindowMemory] = {}

    def get_agent(self, agent_type: str, model: Optional[str] = None) -> AgentExecutor:
        """Get or create agent of specified type"""
        agent_key = f"{agent_type}_{model or 'default'}"

        if agent_key not in self.agents:
            self.agents[agent_key] = self._create_agent(agent_type, model)

        return self.agents[agent_key]

    def _create_agent(self, agent_type: str, model: Optional[str] = None) -> AgentExecutor:
        """Create new LangChain agent"""
        manager = get_llm_manager()
        llm = manager.get_model(model) if model else manager.get_default_model()

        if not llm:
            raise ValueError(f"Model {model} not available")

        # Define agent-specific tools and prompts
        tools = self._get_tools_for_agent(agent_type)
        prompt = self._get_prompt_for_agent(agent_type)

        # Create agent
        agent = create_openai_functions_agent(llm, tools, prompt)

        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5,
            return_intermediate_steps=True
        )

    def _get_tools_for_agent(self, agent_type: str) -> List[Tool]:
        """Get tools based on agent type"""
        common_tools = [
            Tool(
                name="current_time",
                description="Get current date and time",
                func=lambda x: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        ]

        if agent_type == "business":
            common_tools.append(
                Tool(
                    name="business_analysis",
                    description="Analyze business data and metrics",
                    func=self._business_analysis_tool
                )
            )
        elif agent_type == "analysis":
            common_tools.append(
                Tool(
                    name="data_analysis",
                    description="Perform data analysis and generate insights",
                    func=self._data_analysis_tool
                )
            )

        return common_tools

    def _business_analysis_tool(self, query: str) -> str:
        """Business analysis tool"""
        return f"Business analysis for: {query} - Placeholder implementation"

    def _data_analysis_tool(self, query: str) -> str:
        """Data analysis tool"""
        return f"Data analysis for: {query} - Placeholder implementation"

    def _get_prompt_for_agent(self, agent_type: str) -> ChatPromptTemplate:
        """Get prompt template for agent type"""
        if agent_type == "business":
            system_message = """You are a business intelligence agent. You analyze business data,
            generate insights, and help with strategic decisions. Always provide actionable recommendations."""
        elif agent_type == "analysis":
            system_message = """You are a data analysis agent. You examine data, identify patterns,
            and provide detailed analytical insights with supporting evidence."""
        else:  # general
            system_message = """You are a helpful AI assistant. You can help with various tasks
            including analysis, planning, and problem-solving."""

        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

    def get_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """Get or create conversation memory for session"""
        if session_id not in self.memories:
            self.memories[session_id] = ConversationBufferWindowMemory(
                k=10,  # Keep last 10 exchanges
                return_messages=True
            )
        return self.memories[session_id]

# Global agent manager
agent_manager = LangChainAgentManager()

# ============================================================================
# n8n → INTELLIGENCE ENGINE ENDPOINTS
# ============================================================================

@router.post("/agent/chat")
async def agent_chat(request: AgentChatRequest) -> N8nResponse:
    """
    Chat with LangChain Agent - Called from n8n HTTP Request Node

    n8n Workflow Example:
    HTTP Request Node → POST /api/n8n/agent/chat → Response → Process Result
    """
    try:
        logger.info(f"🤖 Agent chat request: {request.agent_type} - {request.message[:50]}...")

        # Get agent and memory
        agent = agent_manager.get_agent(request.agent_type, request.model)
        memory = agent_manager.get_memory(request.session_id)

        # Execute agent
        start_time = datetime.utcnow()
        result = await asyncio.to_thread(
            agent.invoke,
            {"input": request.message}
        )

        response_time = (datetime.utcnow() - start_time).total_seconds()

        # Prepare response
        response_data = {
            "response": result["output"],
            "agent_type": request.agent_type,
            "model_used": request.model or "default",
            "response_time_seconds": response_time,
            "session_id": request.session_id,
            "intermediate_steps": result.get("intermediate_steps", [])
        }

        # If webhook URL provided, send async callback
        if request.n8n_webhook_url:
            asyncio.create_task(
                send_webhook_callback(request.n8n_webhook_url, response_data)
            )

        logger.info(f"✅ Agent chat completed in {response_time:.2f}s")

        return N8nResponse(
            success=True,
            data=response_data,
            agent_info={
                "agent_type": request.agent_type,
                "model": request.model,
                "session_id": request.session_id
            }
        )

    except Exception as e:
        logger.error(f"❌ Agent chat error: {e}")
        return N8nResponse(
            success=False,
            error=str(e),
            agent_info={"agent_type": request.agent_type}
        )

@router.post("/agent/task")
async def agent_task(request: AgentTaskRequest) -> N8nResponse:
    """
    Execute specific task with LangChain Agent - Called from n8n HTTP Request Node

    Task Types:
    - analyze: Analyze provided data
    - summarize: Create summary of content
    - extract: Extract information from data
    - generate: Generate content based on input
    """
    try:
        logger.info(f"📋 Agent task request: {request.task_type}")

        # Get agent
        agent = agent_manager.get_agent("general", request.model)

        # Create task-specific prompt
        task_instructions = {
            "analyze": "Analyze the following data and provide detailed insights:",
            "summarize": "Summarize the following content concisely:",
            "extract": "Extract the key information from the following data:",
            "generate": "Generate content based on the following requirements:"
        }

        instruction = task_instructions.get(request.task_type, "Process the following:")
        full_prompt = f"{instruction}\n\n{request.instructions}\n\nData: {json.dumps(request.input_data, indent=2)}"

        # Execute task
        start_time = datetime.utcnow()
        result = await asyncio.to_thread(
            agent.invoke,
            {"input": full_prompt}
        )
        response_time = (datetime.utcnow() - start_time).total_seconds()

        # Prepare response
        response_data = {
            "result": result["output"],
            "task_type": request.task_type,
            "input_data": request.input_data,
            "model_used": request.model or "default",
            "response_time_seconds": response_time
        }

        # Send webhook callback if provided
        if request.n8n_webhook_url:
            asyncio.create_task(
                send_webhook_callback(request.n8n_webhook_url, response_data)
            )

        logger.info(f"✅ Agent task completed in {response_time:.2f}s")

        return N8nResponse(
            success=True,
            data=response_data,
            agent_info={"task_type": request.task_type}
        )

    except Exception as e:
        logger.error(f"❌ Agent task error: {e}")
        return N8nResponse(
            success=False,
            error=str(e),
            agent_info={"task_type": request.task_type}
        )

# ============================================================================
# INTELLIGENCE ENGINE → n8n ENDPOINTS
# ============================================================================

@router.post("/webhook/trigger")
async def trigger_n8n_workflow(request: WorkflowTriggerRequest) -> N8nResponse:
    """
    Trigger n8n workflow from Intelligence Engine Agent
    Agent can call this to trigger workflows based on analysis results
    """
    try:
        logger.info(f"🔗 Triggering n8n workflow: {request.workflow_id or 'webhook'}")

        # Validate webhook URL
        parsed_url = urlparse(request.webhook_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid webhook URL")

        # Prepare payload
        payload = {
            "triggered_by": "intelligence_engine",
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": request.workflow_id,
            "data": request.data
        }

        # Send webhook request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                request.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            response.raise_for_status()

            # If waiting for completion, monitor the workflow
            result_data = response.json() if response.content else {}

            logger.info(f"✅ n8n workflow triggered successfully")

            return N8nResponse(
                success=True,
                data={
                    "workflow_triggered": True,
                    "webhook_url": request.webhook_url,
                    "workflow_id": request.workflow_id,
                    "response_status": response.status_code,
                    "response_data": result_data
                }
            )

    except Exception as e:
        logger.error(f"❌ n8n workflow trigger error: {e}")
        return N8nResponse(
            success=False,
            error=str(e)
        )

# ============================================================================
# WEBHOOK CALLBACK UTILITIES
# ============================================================================

async def send_webhook_callback(webhook_url: str, data: Dict[str, Any]):
    """Send async webhook callback to n8n"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                webhook_url,
                json={
                    "callback_type": "agent_response",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": data
                }
            )
        logger.info(f"✅ Webhook callback sent to {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Webhook callback failed: {e}")

# ============================================================================
# HEALTH AND STATUS ENDPOINTS
# ============================================================================

@router.get("/status")
async def n8n_integration_status():
    """Check n8n integration status and agent availability"""
    try:
        # Check n8n connectivity
        n8n_status = "unknown"
        if settings.N8N_URL:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{settings.N8N_URL}/healthz")
                    n8n_status = "connected" if response.status_code == 200 else "error"
            except:
                n8n_status = "disconnected"

        return {
            "n8n_integration": "active",
            "n8n_url": settings.N8N_URL,
            "n8n_status": n8n_status,
            "available_agents": ["general", "business", "analysis"],
            "active_sessions": len(agent_manager.memories),
            "loaded_agents": len(agent_manager.agents),
            "endpoints": {
                "agent_chat": "/api/n8n/agent/chat",
                "agent_task": "/api/n8n/agent/task",
                "webhook_trigger": "/api/n8n/webhook/trigger"
            }
        }

    except Exception as e:
        logger.error(f"❌ n8n status check error: {e}")
        return {"error": str(e)}

@router.get("/examples")
async def integration_examples():
    """Get examples of how to integrate with n8n"""
    return {
        "n8n_to_intelligence": {
            "description": "Use n8n HTTP Request Node to call Intelligence Engine",
            "examples": [
                {
                    "name": "Chat with Agent",
                    "method": "POST",
                    "url": "/api/n8n/agent/chat",
                    "body": {
                        "message": "Analyze our sales performance this month",
                        "agent_type": "business",
                        "session_id": "sales_analysis_session"
                    }
                },
                {
                    "name": "Execute Analysis Task",
                    "method": "POST",
                    "url": "/api/n8n/agent/task",
                    "body": {
                        "task_type": "analyze",
                        "input_data": {"sales": [100, 200, 150], "period": "Q1 2025"},
                        "instructions": "Identify trends and provide recommendations"
                    }
                }
            ]
        },
        "intelligence_to_n8n": {
            "description": "Intelligence Engine triggers n8n workflows",
            "examples": [
                {
                    "name": "Trigger Workflow from Agent",
                    "method": "POST",
                    "url": "/api/n8n/webhook/trigger",
                    "body": {
                        "webhook_url": "https://your-n8n.com/webhook/analysis-complete",
                        "data": {"analysis_result": "...", "recommendations": "..."}
                    }
                }
            ]
        }
    }