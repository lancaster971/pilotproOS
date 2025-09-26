"""
Intelligence Engine - CLEAN VERSION
Multi-LLM support without bullshit dependencies
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
import time

# Import ONLY what exists
from .llm_manager import get_llm_manager
from .performance_tracker import get_tracker
from .api_models import router as models_router
from .test_agent import router as test_router

# Create app
app = FastAPI(
    title="Intelligence Engine",
    description="Multi-LLM Engine with dynamic model management",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(models_router)
app.include_router(test_router)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    model_id: Optional[str] = None
    user_id: Optional[str] = "guest"

class ChatResponse(BaseModel):
    response: str
    model_used: str
    response_time_ms: float
    tokens: Optional[Dict[str, int]] = None
    cost: Optional[float] = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Intelligence Engine",
        "status": "running",
        "endpoints": [
            "/health",
            "/api/chat",
            "/api/models/list",
            "/api/models/test/{model_id}",
            "/api/stats"
        ]
    }

@app.get("/health")
async def health():
    """Health check"""
    manager = get_llm_manager()
    loaded_models = list(manager.models.keys())

    return {
        "status": "healthy",
        "models_loaded": len(loaded_models),
        "models": loaded_models,
        "default_model": manager.config.get('default_model')
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint with multi-LLM support"""
    start_time = time.time()

    try:
        manager = get_llm_manager()
        tracker = get_tracker()

        # Get model
        model = manager.get_model(request.model_id)
        if not model:
            # Try fallback chain
            fallback = manager.get_fallback_chain()
            if fallback:
                model = fallback[0]
                model_id = manager.config.get('default_model')
            else:
                raise HTTPException(status_code=404, detail="No models available")
        else:
            model_id = request.model_id or manager.config.get('default_model')

        # Call model
        response = await model.ainvoke(request.message)

        # Extract response
        if hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)

        # Calculate metrics
        response_time = (time.time() - start_time) * 1000

        # Track performance (simplified - no token counting for now)
        provider = manager.config['models'][model_id]['provider']
        metric = tracker.track_call(
            model_id=model_id,
            provider=provider,
            start_time=start_time,
            input_tokens=len(request.message.split()) * 2,  # Rough estimate
            output_tokens=len(response_text.split()) * 2,    # Rough estimate
            success=True
        )

        return ChatResponse(
            response=response_text,
            model_used=model_id,
            response_time_ms=round(response_time, 2),
            cost=metric.estimated_cost if metric else 0
        )

    except Exception as e:
        # Track error
        if 'model_id' in locals() and 'provider' in locals():
            tracker.track_call(
                model_id=model_id,
                provider=provider,
                start_time=start_time,
                input_tokens=0,
                output_tokens=0,
                success=False,
                error=str(e)
            )

        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get performance statistics"""
    tracker = get_tracker()

    return {
        "stats": tracker.get_model_stats(hours=24),
        "comparison": tracker.get_comparison_table(hours=24),
        "recommendations": tracker.get_recommendations()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)