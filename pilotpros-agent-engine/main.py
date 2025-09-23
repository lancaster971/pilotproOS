"""
PilotProOS Agent Engine - Multi-Agent AI System
Async-first architecture with Redis job queue
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client.core import CollectorRegistry
from fastapi.responses import PlainTextResponse

from config.settings import Settings
from api.routes import api_router
from services.job_manager import JobManager
from services.monitoring_service import MonitoringService
from services.llm_manager import LLMManager
from services.agent_orchestrator import AgentOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load settings
settings = Settings()

# Metrics
registry = CollectorRegistry()
job_submitted = Counter('agent_engine_jobs_submitted_total', 'Total jobs submitted', registry=registry)
job_completed = Counter('agent_engine_jobs_completed_total', 'Total jobs completed', registry=registry)
job_failed = Counter('agent_engine_jobs_failed_total', 'Total jobs failed', registry=registry)
job_duration = Histogram('agent_engine_job_duration_seconds', 'Job processing time', registry=registry)
queue_size = Gauge('agent_engine_queue_size', 'Current queue size', registry=registry)

# Global instances
redis_client: Optional[redis.Redis] = None
job_manager: Optional[JobManager] = None
monitoring_service: Optional[MonitoringService] = None
llm_manager: Optional[LLMManager] = None
agent_orchestrator: Optional[AgentOrchestrator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle - startup and shutdown
    """
    global redis_client, job_manager, monitoring_service, llm_manager, agent_orchestrator

    # Startup
    logger.info("Starting Agent Engine Service...")

    try:
        # Initialize Redis connection
        redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("✅ Redis connection established")

        # Initialize LLM Manager
        llm_manager = LLMManager(settings)
        model_info = llm_manager.get_model_info()
        logger.info(f"✅ LLM Manager initialized: {model_info['available_models']} models available")

        # Log available providers
        for provider, models in model_info['models_by_provider'].items():
            logger.info(f"   {provider}: {len(models)} models")

        # Initialize services
        job_manager = JobManager(redis_client, settings)
        monitoring_service = MonitoringService(redis_client, settings)
        agent_orchestrator = AgentOrchestrator(settings, redis_client)

        # Start background tasks
        await monitoring_service.start()

        logger.info("✅ Agent Engine Service started successfully")

    except Exception as e:
        logger.error(f"❌ Failed to start Agent Engine: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Agent Engine Service...")

    if monitoring_service:
        await monitoring_service.stop()

    if redis_client:
        await redis_client.close()

    logger.info("Agent Engine Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="PilotProOS Agent Engine",
    description="Multi-Agent AI System for Business Process Analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend dev
        "http://localhost:3001",  # Backend dev
        "http://localhost",       # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for Stack Controller
    """
    try:
        # Check Redis connection
        if redis_client:
            await redis_client.ping()
        else:
            raise Exception("Redis client not initialized")

        # Check job manager
        if not job_manager:
            raise Exception("Job manager not initialized")

        # Get queue stats
        queue_stats = await job_manager.get_queue_stats()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "agent-engine",
            "version": "1.0.0",
            "redis": "connected",
            "queue": queue_stats
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Metrics endpoint
@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Prometheus metrics endpoint
    """
    try:
        # Update queue size gauge
        if job_manager:
            stats = await job_manager.get_queue_stats()
            queue_size.set(stats.get("pending", 0))

        return generate_latest(registry)
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return PlainTextResponse("", status_code=500)


# Info endpoint
@app.get("/")
async def info():
    """
    Service information endpoint
    """
    return {
        "service": "PilotProOS Agent Engine",
        "description": "Multi-Agent AI System",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "api_docs": "/docs",
            "analysis": "/api/v1/analyze"
        },
        "features": [
            "Async job processing with Redis queue",
            "Multi-agent collaborative analysis",
            "Real-time progress via WebSocket",
            "JWT authentication",
            "Prometheus monitoring"
        ]
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )