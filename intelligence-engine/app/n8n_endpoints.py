"""
n8n Integration Endpoints - Using Milhena v3.0
Provides endpoints for n8n workflow integration with Milhena agent
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
from loguru import logger
from langchain_core.messages import HumanMessage

router = APIRouter(prefix="/api/n8n", tags=["n8n"])

class N8nRequest(BaseModel):
    """Request from n8n workflow"""
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    workflow_id: Optional[str] = None
    execution_id: Optional[str] = None

class N8nResponse(BaseModel):
    """Response for n8n workflow"""
    response: str
    intent: Optional[str] = None
    cached: bool = False
    status: str = "success"
    metadata: Dict[str, Any] = {}

@router.post("/agent/customer-support", response_model=N8nResponse)
async def n8n_customer_support(request: N8nRequest):
    """
    n8n Customer Support Agent endpoint using Milhena v3.0
    Compatible with n8n HTTP Request node
    """
    try:
        from .main import app
        graph_supervisor = app.state.graph_supervisor  # v4.0 with fixed BaseModel

        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Add workflow context if provided
        context = request.context or {}
        if request.workflow_id:
            context["workflow_id"] = request.workflow_id
        if request.execution_id:
            context["execution_id"] = request.execution_id

        # Process with GraphSupervisor v4.0
        result = await graph_supervisor.process_query(
            query=request.message,
            session_id=session_id,
            context=context
        )

        # Extract agent info from routing decision
        routing = result.get("routing")
        agent_used = "unknown"
        if routing:
            agent_used = routing.target_agent.value if hasattr(routing.target_agent, 'value') else str(routing.target_agent)

        return N8nResponse(
            response=result.get("response", "Come posso aiutarti?"),
            intent=result.get("intent", "GENERAL"),
            cached=result.get("cached", False),
            status="success",
            metadata={
                "session_id": session_id,
                "model": "graph-supervisor-v4.0",
                "agent_used": agent_used,
                "workflow_id": request.workflow_id,
                "execution_id": request.execution_id
            }
        )

    except Exception as e:
        logger.error(f"n8n endpoint error: {str(e)}")
        return N8nResponse(
            response="Si è verificato un errore nell'elaborazione della richiesta.",
            status="error",
            metadata={"error": str(e)}
        )

@router.get("/agent/customer-support")
async def n8n_customer_support_get(message: str, session_id: Optional[str] = None):
    """
    GET version for n8n webhook compatibility
    """
    request = N8nRequest(message=message, session_id=session_id)
    return await n8n_customer_support(request)

@router.post("/webhook")
async def n8n_webhook(data: Dict[str, Any]):
    """
    Generic webhook endpoint for n8n workflows
    Accepts any JSON payload from n8n
    """
    try:
        # Extract message from various possible fields
        message = (
            data.get("message") or
            data.get("text") or
            data.get("query") or
            data.get("input") or
            "Richiesta da workflow n8n"
        )

        request = N8nRequest(
            message=message,
            session_id=data.get("session_id"),
            context=data,
            workflow_id=data.get("workflow", {}).get("id"),
            execution_id=data.get("execution", {}).get("id")
        )

        return await n8n_customer_support(request)

    except Exception as e:
        logger.error(f"n8n webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))