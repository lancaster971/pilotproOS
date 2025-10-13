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
async def submit_feedback(feedback_request: FeedbackRequest, request: Request) -> Dict[str, str]:
    """
    Submit feedback for continuous learning
    Persisted to PostgreSQL + tracked in LangSmith
    """
    try:
        logger.info(f"[Feedback] Received - Type: {feedback_request.feedback_type}, Session: {feedback_request.session_id}, Trace: {feedback_request.trace_id or 'none'}")

        # Save to PostgreSQL via FeedbackStore
        feedback_store = request.app.state.feedback_store

        if feedback_store:
            try:
                feedback_id = await feedback_store.save_feedback(
                    session_id=feedback_request.session_id,
                    query=feedback_request.query,
                    response=feedback_request.response,
                    feedback_type=feedback_request.feedback_type,
                    detected_intent=feedback_request.intent or "GENERAL",
                    run_id=feedback_request.trace_id,
                    metadata={
                        "source": "chat_widget",
                        "timestamp": datetime.utcnow().isoformat(),
                        "user_agent": request.headers.get("User-Agent", "unknown")
                    }
                )
                logger.info(f"[Feedback] Saved to PostgreSQL - ID: {feedback_id}")
            except Exception as db_error:
                # Don't fail the request if database is unavailable
                logger.error(f"[Feedback] PostgreSQL save failed: {db_error}")
                # Continue to LangSmith anyway
        else:
            logger.warning("[Feedback] FeedbackStore not initialized, skipping PostgreSQL persistence")

        # Record feedback in LangSmith if trace_id provided (following official pattern)
        if feedback_request.trace_id:
            try:
                from langsmith import Client
                client = Client()

                # Convert feedback_type to LangSmith score (0-1)
                score = 1.0 if feedback_request.feedback_type == "positive" else 0.0

                # Create feedback linked to trace (non-blocking in Python)
                client.create_feedback(
                    run_id=feedback_request.trace_id,
                    key="user_feedback",
                    score=score,
                    comment=f"Intent: {feedback_request.intent or 'GENERAL'} | Query: {feedback_request.query[:100]}"
                )
                logger.info(f"[LangSmith] Feedback linked to trace: {feedback_request.trace_id}")
            except Exception as langsmith_error:
                # Don't fail the request if LangSmith is unavailable
                logger.warning(f"[LangSmith] Failed to record feedback: {langsmith_error}")

        response_data = {
            "status": "success",
            "message": f"Feedback recorded: {feedback_request.feedback_type}"
        }

        # Add langsmith_linked only if trace_id was provided
        if feedback_request.trace_id:
            response_data["langsmith_trace_id"] = feedback_request.trace_id

        return response_data

    except Exception as e:
        logger.error(f"[Feedback] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
@traceable(
    name="MilhenaPerformance",
    run_type="chain",
    metadata={"endpoint": "performance", "version": "3.0"}
)
async def get_performance_report(request: Request) -> Dict[str, Any]:
    """
    Get complete learning performance report from PostgreSQL
    Returns data in format expected by frontend Learning Dashboard
    """
    try:
        logger.info("[Performance] Report requested - reading from PostgreSQL")

        feedback_store = request.app.state.feedback_store
        milhena_graph = request.app.state.milhena

        if not feedback_store:
            logger.warning("[Performance] FeedbackStore not available, returning empty metrics")
            return _empty_performance_report()

        # Get recent feedback from PostgreSQL
        recent_feedback_db = await feedback_store.get_recent_feedback(limit=50)

        # Get patterns from milhena graph (auto_learned_patterns table)
        patterns_data = milhena_graph.get_patterns()

        # Calculate metrics
        total_feedback = len(recent_feedback_db)
        positive_count = sum(1 for f in recent_feedback_db if f['feedback_type'] == 'positive')

        accuracy_rate = (positive_count / total_feedback) if total_feedback > 0 else 0.0

        # Count pattern types
        auto_learned_count = sum(1 for p in patterns_data if p.get('source') == 'auto_learned')
        hardcoded_count = len(patterns_data) - auto_learned_count

        # Calculate average confidence
        avg_confidence = sum(p.get('confidence', 0) for p in patterns_data) / len(patterns_data) if patterns_data else 0.0

        # Total usages from patterns
        total_usages = sum(p.get('times_used', 0) for p in patterns_data)

        # Cost savings calculation (simplified)
        fast_path_queries = sum(p.get('times_used', 0) for p in patterns_data if p.get('source') == 'auto_learned')
        fast_path_coverage = (fast_path_queries / total_usages * 100) if total_usages > 0 else 0.0
        llm_coverage = 100 - fast_path_coverage

        # Assume $0.0003 per LLM call, $0 for fast-path
        monthly_savings = fast_path_queries * 0.0003 * 30  # Rough estimate
        total_savings = fast_path_queries * 0.0003

        # Format patterns for frontend
        top_patterns = [
            {
                "id": str(p.get('id', '')),
                "query": p.get('pattern', ''),
                "normalized_query": p.get('normalized_pattern', ''),
                "classification": p.get('category', 'GENERAL'),
                "confidence": p.get('confidence', 0.0),
                "times_used": p.get('times_used', 0),
                "times_correct": p.get('times_correct', 0),
                "accuracy": (p.get('times_correct', 0) / p.get('times_used', 1)) if p.get('times_used', 0) > 0 else 0.0,
                "created_at": p.get('created_at', ''),
                "last_used_at": p.get('last_used_at', ''),
                "is_active": p.get('enabled', True),
                "source": 'auto_learned' if p.get('source') == 'auto_learned' else 'hardcoded'
            }
            for p in patterns_data[:50]  # Top 50
        ]

        # Generate accuracy trend from feedback timestamps
        accuracy_trend = []
        if recent_feedback_db:
            # Group by day and calculate daily accuracy
            from collections import defaultdict
            daily_stats = defaultdict(lambda: {"positive": 0, "total": 0})

            for fb in recent_feedback_db:
                date_key = fb['timestamp'].date().isoformat()
                daily_stats[date_key]["total"] += 1
                if fb['feedback_type'] == 'positive':
                    daily_stats[date_key]["positive"] += 1

            # Generate trend points
            for date_key in sorted(daily_stats.keys())[-7:]:  # Last 7 days
                stats = daily_stats[date_key]
                accuracy_trend.append({
                    "timestamp": f"{date_key}T12:00:00Z",
                    "accuracy": stats["positive"] / stats["total"] if stats["total"] > 0 else 0.0,
                    "total_queries": stats["total"],
                    "correct_queries": stats["positive"]
                })

        # Return in format expected by frontend (types/learning.ts)
        return {
            # Main metrics (root level - not nested!)
            "total_patterns": len(patterns_data),
            "auto_learned_count": auto_learned_count,
            "hardcoded_count": hardcoded_count,
            "average_confidence": avg_confidence,
            "total_usages": total_usages,
            "accuracy_rate": accuracy_rate,

            # Cost savings
            "cost_savings": {
                "monthly": monthly_savings,
                "total": total_savings,
                "fast_path_coverage": fast_path_coverage,
                "llm_coverage": llm_coverage
            },

            # Patterns and trends
            "top_patterns": top_patterns,
            "accuracy_trend": accuracy_trend,

            # Legacy fields for backward compatibility
            "success": True,
            "recent_feedback": [
                {
                    "timestamp": f['timestamp'].isoformat(),
                    "query": f['query'],
                    "feedback_type": f['feedback_type'],
                    "session_id": f['session_id']
                }
                for f in recent_feedback_db[:20]
            ]
        }

    except Exception as e:
        logger.error(f"[Performance] Report error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def _empty_performance_report() -> Dict[str, Any]:
    """Return empty report when FeedbackStore not available"""
    return {
        "total_patterns": 0,
        "auto_learned_count": 0,
        "hardcoded_count": 0,
        "average_confidence": 0.0,
        "total_usages": 0,
        "accuracy_rate": 0.0,
        "cost_savings": {
            "monthly": 0.0,
            "total": 0.0,
            "fast_path_coverage": 0.0,
            "llm_coverage": 100.0
        },
        "top_patterns": [],
        "accuracy_trend": [],
        "success": True,
        "recent_feedback": []
    }

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