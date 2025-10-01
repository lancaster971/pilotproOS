"""
Milhena API Endpoints - FastAPI routes with LangSmith tracing
Fully integrated with LangSmith for monitoring and debugging
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from langsmith import traceable
import uuid

# Import Milhena components
from .graph import MilhenaGraph, get_milhena_graph
from .learning import LearningSystem
from .token_manager import TokenManager
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="/api/milhena",
    tags=["milhena"],
    responses={404: {"description": "Not found"}},
)

# ============================================================================
# GLOBAL SINGLETON INSTANCES
# ============================================================================
# Learning System singleton - maintains state across requests
_learning_system_instance: Optional[LearningSystem] = None

def get_learning_system() -> LearningSystem:
    """Get or create singleton LearningSystem instance"""
    global _learning_system_instance
    if _learning_system_instance is None:
        _learning_system_instance = LearningSystem()
        logger.info("✅ LearningSystem singleton initialized")
    return _learning_system_instance

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class MilhenaRequest(BaseModel):
    """Request model for Milhena"""
    query: str = Field(..., description="User query in Italian")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

class MilhenaResponse(BaseModel):
    """Response model for Milhena"""
    success: bool
    response: str
    intent: Optional[str] = None
    session_id: str
    cached: bool = False
    timestamp: str
    trace_id: Optional[str] = None

class FeedbackRequest(BaseModel):
    """Feedback request model following LangSmith best practices"""
    session_id: str
    query: str
    response: str
    feedback_type: str = Field(..., description="'positive', 'negative', or 'correction'")
    intent: Optional[str] = None
    trace_id: Optional[str] = Field(None, description="LangSmith trace ID for linking feedback to traces")

class StatsResponse(BaseModel):
    """Statistics response model"""
    total_queries: int
    cache_hit_rate: float
    accuracy_rate: float
    token_usage: Dict[str, Any]
    active_sessions: int

# ============================================================================
# API ENDPOINTS WITH LANGSMITH TRACING
# ============================================================================

@router.post("/chat", response_model=MilhenaResponse)
@traceable(
    name="MilhenaChat",
    run_type="chain",
    metadata={"endpoint": "chat", "version": "3.0"}
)
async def chat_with_milhena(request: MilhenaRequest) -> MilhenaResponse:
    """
    Main chat endpoint for Milhena Business Assistant
    Fully traced in LangSmith for monitoring
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Generate trace ID for LangSmith
        trace_id = str(uuid.uuid4())

        logger.info(f"[LangSmith] New chat request - Session: {session_id}, Trace: {trace_id}")

        # Get Milhena graph instance
        milhena = get_milhena_graph()

        # Process the query
        result = await milhena.process(
            query=request.query,
            session_id=session_id,
            context=request.context
        )

        # Log success to LangSmith
        logger.info(f"[LangSmith] Chat completed - Intent: {result.get('intent')}, Cached: {result.get('cached')}")

        return MilhenaResponse(
            success=result["success"],
            response=result["response"],
            intent=result.get("intent"),
            session_id=session_id,
            cached=result.get("cached", False),
            timestamp=result["timestamp"],
            trace_id=trace_id
        )

    except Exception as e:
        logger.error(f"[LangSmith] Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
@traceable(
    name="MilhenaFeedback",
    run_type="chain",
    metadata={"endpoint": "feedback", "version": "3.0"}
)
async def submit_feedback(request: FeedbackRequest) -> Dict[str, str]:
    """
    Submit feedback for continuous learning
    Tracked in LangSmith for improvement analysis
    """
    try:
        logger.info(f"[LangSmith] Feedback received - Type: {request.feedback_type}, Session: {request.session_id}, Trace: {request.trace_id or 'none'}")

        # Get learning system singleton
        learning = get_learning_system()

        # Record feedback in Learning System
        await learning.record_feedback(
            query=request.query,
            intent=request.intent or "GENERAL",
            response=request.response,
            feedback_type=request.feedback_type,
            session_id=request.session_id
        )

        # Record feedback in LangSmith if trace_id provided (following official pattern)
        if request.trace_id:
            try:
                from langsmith import Client
                client = Client()

                # Convert feedback_type to LangSmith score (0-1)
                score = 1.0 if request.feedback_type == "positive" else 0.0

                # Create feedback linked to trace (non-blocking in Python)
                client.create_feedback(
                    run_id=request.trace_id,
                    key="user_feedback",
                    score=score,
                    comment=f"Intent: {request.intent or 'GENERAL'} | Query: {request.query[:100]}"
                )
                logger.info(f"[LangSmith] Feedback linked to trace: {request.trace_id}")
            except Exception as langsmith_error:
                # Don't fail the request if LangSmith is unavailable
                logger.warning(f"[LangSmith] Failed to record feedback: {langsmith_error}")

        response_data = {
            "status": "success",
            "message": f"Feedback recorded: {request.feedback_type}"
        }

        # Add langsmith_linked only if trace_id was provided
        if request.trace_id:
            response_data["langsmith_trace_id"] = request.trace_id

        return response_data

    except Exception as e:
        logger.error(f"[LangSmith] Feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
@traceable(
    name="MilhenaPerformance",
    run_type="chain",
    metadata={"endpoint": "performance", "version": "3.0"}
)
async def get_performance_report() -> Dict[str, Any]:
    """
    Get complete learning performance report
    Following LangSmith pattern for continuous improvement
    """
    try:
        logger.info("[LangSmith] Performance report requested")

        # Get learning system singleton
        learning = get_learning_system()
        report = learning.get_performance_report()

        # Add recent feedback (last 50 entries)
        recent_feedback = [
            {
                "timestamp": entry.timestamp.isoformat(),
                "query": entry.query,
                "intent": entry.intent,
                "response": entry.response,
                "feedback_type": entry.feedback_type,
                "session_id": entry.session_id
            }
            for entry in learning.feedback_entries[-50:]
        ]

        # Add learned patterns (high confidence only)
        learned_patterns = [
            {
                "pattern": p.pattern,
                "correct_intent": p.correct_intent,
                "confidence": p.confidence,
                "occurrences": p.occurrences,
                "success_rate": p.success_rate,
                "last_seen": p.last_seen.isoformat()
            }
            for p in learning.learned_patterns.values()
            if p.confidence > 0.5
        ]

        return {
            "success": True,
            "metrics": report["metrics"],
            "recent_feedback": recent_feedback,
            "learned_patterns": learned_patterns,
            "pattern_count": report["pattern_count"],
            "high_confidence_patterns": report["high_confidence_patterns"],
            "recent_accuracy": report["recent_accuracy"],
            "top_corrections": report["top_corrections"],
            "improvement_trend": report["improvement_trend"]
        }

    except Exception as e:
        logger.error(f"[LangSmith] Performance report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=StatsResponse)
@traceable(
    name="MilhenaStats",
    run_type="chain",
    metadata={"endpoint": "stats", "version": "3.0"}
)
async def get_milhena_stats() -> StatsResponse:
    """
    Get Milhena statistics and performance metrics
    Visible in LangSmith dashboard
    """
    try:
        logger.info("[LangSmith] Stats requested")

        # Get components
        learning = LearningSystem()
        token_manager = TokenManager()
        cache_manager = CacheManager(None)

        # Get performance report
        perf_report = learning.get_performance_report()
        cache_stats = cache_manager.get_stats()
        token_stats = token_manager.get_usage_stats()

        return StatsResponse(
            total_queries=perf_report["metrics"]["total_queries"],
            cache_hit_rate=float(cache_stats["hit_rate"].strip("%")) / 100,
            accuracy_rate=perf_report["metrics"]["accuracy_rate"],
            token_usage=token_stats,
            active_sessions=10  # Placeholder
        )

    except Exception as e:
        logger.error(f"[LangSmith] Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
@traceable(
    name="MilhenaTest",
    run_type="chain",
    metadata={"endpoint": "test", "version": "3.0"}
)
async def test_milhena() -> Dict[str, Any]:
    """
    Test endpoint to verify Milhena is working and visible in LangSmith
    """
    try:
        logger.info("[LangSmith] Test endpoint called")

        # Test queries
        test_queries = [
            "Ciao Milhena, come stai?",
            "Il sistema sembra andato a puttane",
            "Qual è lo stato dei processi?",
            "Mostrami le metriche di oggi"
        ]

        results = []
        milhena = get_milhena_graph()

        for query in test_queries:
            result = await milhena.process(
                query=query,
                session_id="test-session",
                context={"test": True}
            )
            results.append({
                "query": query,
                "intent": result.get("intent"),
                "response": result.get("response")[:100] + "..."
            })

        return {
            "status": "success",
            "message": "Milhena is working correctly",
            "test_results": results,
            "langsmith_project": "milhena-v3-production",
            "trace_url": "Check https://smith.langchain.com for traces"
        }

    except Exception as e:
        logger.error(f"[LangSmith] Test error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "Milhena Business Assistant v3.0",
        "langsmith": "enabled" if os.getenv("LANGCHAIN_API_KEY") else "disabled"
    }

# ============================================================================
# LANGSMITH DATASETS AND TESTING
# ============================================================================

@router.post("/create-dataset")
@traceable(
    name="MilhenaCreateDataset",
    run_type="chain",
    metadata={"endpoint": "create-dataset", "version": "3.0"}
)
async def create_langsmith_dataset() -> Dict[str, str]:
    """
    Create a LangSmith dataset for Milhena testing
    """
    try:
        from langsmith import Client

        client = Client()

        # Create dataset
        dataset_name = "milhena-v3-test-queries"

        # Example test cases
        examples = [
            {
                "input": {"query": "Ciao Milhena, come va oggi?"},
                "output": {"intent": "GENERAL", "response_contains": "Ciao"}
            },
            {
                "input": {"query": "Il sistema è andato a puttane"},
                "output": {"intent": "ERROR", "response_contains": "problema"}
            },
            {
                "input": {"query": "Mostra lo stato dei processi"},
                "output": {"intent": "STATUS", "response_contains": "processi"}
            },
            {
                "input": {"query": "Quali sono le metriche di oggi?"},
                "output": {"intent": "METRIC", "response_contains": "metriche"}
            },
            {
                "input": {"query": "Come configuro il workflow?"},
                "output": {"intent": "CONFIG", "response_contains": "configurazione"}
            }
        ]

        # Create dataset
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description="Test queries for Milhena v3.0 Business Assistant"
        )

        # Add examples
        for example in examples:
            client.create_example(
                inputs=example["input"],
                outputs=example["output"],
                dataset_id=dataset.id
            )

        return {
            "status": "success",
            "dataset_name": dataset_name,
            "examples_count": len(examples),
            "message": "Dataset created in LangSmith"
        }

    except Exception as e:
        logger.error(f"[LangSmith] Dataset creation error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# Import os for environment check
import os