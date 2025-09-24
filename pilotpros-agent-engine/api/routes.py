"""
API Routes for Agent Engine
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json
import uuid

logger = logging.getLogger(__name__)

api_router = APIRouter()


class AnalysisRequest(BaseModel):
    """Request model for analysis submission"""
    type: str  # process_analysis, data_interpretation, etc.
    data: Dict[str, Any]
    callback_url: Optional[str] = None
    priority: str = "normal"  # high, normal, low
    context: Optional[Dict[str, Any]] = None


class AnalysisResponse(BaseModel):
    """Response model for analysis submission"""
    success: bool
    job_id: str
    status: str
    position_in_queue: Optional[int] = None
    estimated_start: Optional[datetime] = None
    websocket_channel: str
    status_url: str


@api_router.post("/analyze", response_model=AnalysisResponse)
async def submit_analysis(request: AnalysisRequest):
    """
    Submit a new analysis job to the Agent Engine

    Analysis types:
    - process_analysis: Analyze business process performance
    - data_interpretation: Interpret complex datasets
    - trend_analysis: Identify patterns and trends
    - optimization_review: Generate optimization recommendations
    - custom_analysis: Custom analysis with specific agents
    """
    try:
        from main import job_manager

        if not job_manager:
            raise Exception("Job Manager not initialized")

        # Create job
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "type": request.type,
            "data": request.data,
            "context": request.context,
            "priority": request.priority,
            "callback_url": request.callback_url
        }

        # Submit to queue
        job_info = await job_manager.submit_job(job_data)

        return AnalysisResponse(
            success=True,
            job_id=job_info["job_id"],
            status=job_info["status"],
            position_in_queue=job_info.get("position_in_queue"),
            estimated_start=job_info.get("estimated_start"),
            websocket_channel=job_info["websocket_channel"],
            status_url=job_info["status_url"]
        )

    except Exception as e:
        logger.error(f"Failed to submit analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@api_router.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """
    Get the status of a specific job
    """
    try:
        from main import job_manager

        if not job_manager:
            raise Exception("Job Manager not initialized")

        status = await job_manager.get_job_status(job_id)

        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@api_router.get("/jobs/{job_id}/result")
async def get_job_result(job_id: str):
    """
    Get the result of a completed job
    """
    try:
        from main import job_manager

        if not job_manager:
            raise Exception("Job Manager not initialized")

        status = await job_manager.get_job_status(job_id)

        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        if status.get("status") not in ["completed", "failed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job {job_id} is not completed yet. Status: {status.get('status')}"
            )

        return {
            "job_id": job_id,
            "status": status.get("status"),
            "result": status.get("result", {}),
            "completed_at": status.get("completed_at"),
            "created_at": status.get("created_at"),
            "processing_time": None  # Calculate from timestamps if needed
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@api_router.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
):
    """
    List jobs with optional filtering by status
    """
    try:
        # TODO: Implement with JobManager
        return {
            "jobs": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@api_router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a pending or running job
    """
    try:
        # TODO: Implement with JobManager
        return {
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancelled successfully"
        }
    except Exception as e:
        logger.error(f"Failed to cancel job: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or cannot be cancelled"
        )


class AssistantRequest(BaseModel):
    """Request model for PilotPro Assistant"""
    question: str
    context: Optional[Dict[str, Any]] = None
    language: str = "italian"
    jwt_token: Optional[str] = None


class AssistantResponse(BaseModel):
    """Response model for PilotPro Assistant"""
    success: bool
    answer: str
    confidence: float
    sources: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None


@api_router.post("/assistant", response_model=AssistantResponse)
async def ask_assistant(request: AssistantRequest, req: Request):
    """
    Ask a question to the PilotPro Assistant

    The assistant speaks Italian by default and has access to:
    - Business process data
    - Performance metrics
    - Historical analysis
    - Best practices
    """
    try:
        from main import job_manager, llm_manager

        # Create job for assistant
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "type": "assistant",
            "question": request.question,
            "context": request.context,
            "jwt_token": request.jwt_token,
            "priority": "high"
        }

        # Submit job
        await job_manager.submit_job(job_data)

        # Wait for quick response (assistant jobs are high priority)
        result = await job_manager.wait_for_result(job_id, timeout=30)

        if result and result.get("success"):
            return AssistantResponse(
                success=True,
                answer=result.get("answer", "Non ho una risposta al momento."),
                confidence=result.get("confidence", 0.8),
                sources=result.get("sources"),
                suggestions=result.get("suggestions")
            )
        else:
            return AssistantResponse(
                success=False,
                answer="Mi dispiace, non sono riuscito a elaborare la tua domanda.",
                confidence=0.0
            )

    except Exception as e:
        logger.error(f"Assistant error: {e}")
        return AssistantResponse(
            success=False,
            answer=f"Errore nell'elaborazione: {str(e)}",
            confidence=0.0
        )


class BusinessAnalysisRequest(BaseModel):
    """Request for business process analysis"""
    process_description: str = Field(..., description="Description of business process")
    data_context: Optional[str] = Field(None, description="Additional data context")


class QuickInsightsRequest(BaseModel):
    """Request for quick business insights"""
    question: str = Field(..., description="Business question")
    context: Optional[str] = Field(None, description="Additional context")


@api_router.post("/business-analysis")
async def business_analysis_endpoint(request: BusinessAnalysisRequest, req: Request):
    """
    Analyze business processes with multi-agent crew
    """
    try:
        from main import job_manager

        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "type": "business_analysis",
            "process_description": request.process_description,
            "data_context": request.data_context,
            "priority": "normal"
        }

        await job_manager.submit_job(job_data)
        result = await job_manager.wait_for_result(job_id, timeout=60)

        if result:
            return result
        else:
            return {
                "success": False,
                "error": "Analysis timeout",
                "job_id": job_id
            }

    except Exception as e:
        logger.error(f"Business analysis error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@api_router.post("/quick-insights")
async def quick_insights_endpoint(request: QuickInsightsRequest, req: Request):
    """
    Get quick business insights with single agent
    """
    try:
        from main import job_manager

        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "type": "quick_insights",
            "question": request.question,
            "context": request.context,
            "priority": "high"
        }

        await job_manager.submit_job(job_data)
        result = await job_manager.wait_for_result(job_id, timeout=30)

        if result:
            return result
        else:
            return {
                "success": False,
                "error": "Insights timeout",
                "job_id": job_id
            }

    except Exception as e:
        logger.error(f"Quick insights error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@api_router.get("/health/llm")
async def llm_health(req: Request):
    """
    Get LLM service health and available models
    """
    try:
        from main import llm_manager

        if not llm_manager:
            raise Exception("LLM Manager not initialized")

        model_info = llm_manager.get_model_info()

        return {
            "status": "healthy",
            "available_models": model_info["available_models"],
            "models_by_provider": model_info["models_by_provider"],
            "active_providers": model_info["active_providers"],
            "free_models": [
                m for m in model_info["models"]
                if m.get("tier") == "free"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


