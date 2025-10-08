#!/usr/bin/env python3
"""
ON-PREMISE EMBEDDINGS SERVICE - FastAPI
100% GRATUITO - ZERO token costs

Provides REST API for:
- stella-en-1.5B-v5 (MIT, MTEB retrieval leader)
- gte-Qwen2-1.5B-instruct (Apache 2.0, MTEB 70.24)
- nomic-embed-text-v1.5 (Apache 2.0, MTEB 62.39)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from loguru import logger
import sys
import os

# Configure logging
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

# Import embedding functions
from app.rag.on_premise_embeddings import (
    get_embedding_function,
    AVAILABLE_MODELS,
    StellaEmbeddingFunction,
    GteQwenEmbeddingFunction,
    NomicEmbeddingFunction
)

# FastAPI app
app = FastAPI(
    title="ON-PREMISE Embeddings Service",
    description="Self-hosted embeddings - ZERO token costs, 100% privacy",
    version="1.0.0"
)

# Global model cache
_model_cache = {}


class EmbedRequest(BaseModel):
    """Request for embedding generation"""
    texts: List[str] = Field(..., description="Texts to embed", min_length=1)
    model: Literal["stella", "gte-qwen2", "nomic"] = Field(
        default="stella",
        description="Embedding model to use"
    )
    dimension: Optional[int] = Field(
        default=None,
        description="Embedding dimension (only for stella: 512, 768, 1024, 2048, 4096, 6144, 8192)"
    )


class EmbedResponse(BaseModel):
    """Response with embeddings"""
    embeddings: List[List[float]] = Field(..., description="Generated embeddings")
    model: str = Field(..., description="Model used")
    dimension: int = Field(..., description="Embedding dimension")
    count: int = Field(..., description="Number of embeddings")


class ModelsResponse(BaseModel):
    """Available models info"""
    models: dict


def get_cached_model(model_type: str, dimension: Optional[int] = None):
    """
    Get model from cache or load it

    Args:
        model_type: Model type (stella, gte-qwen2, nomic)
        dimension: Dimension (only for stella)

    Returns:
        Embedding function
    """
    cache_key = f"{model_type}_{dimension or 'default'}"

    if cache_key not in _model_cache:
        logger.info(f"Loading model: {cache_key}")
        _model_cache[cache_key] = get_embedding_function(
            model_type=model_type,
            dimension=dimension
        )
        logger.success(f"✅ Model loaded: {cache_key}")

    return _model_cache[cache_key]


@app.post("/embed", response_model=EmbedResponse)
async def generate_embeddings(request: EmbedRequest):
    """
    Generate embeddings for texts

    Example:
        POST /embed
        {
            "texts": ["Hello world", "PilotProOS automation"],
            "model": "stella",
            "dimension": 1024
        }

    Returns:
        {
            "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...]],
            "model": "stella",
            "dimension": 1024,
            "count": 2
        }
    """
    try:
        # Get model
        model_fn = get_cached_model(request.model, request.dimension)

        # Generate embeddings
        embeddings = model_fn(request.texts)

        return EmbedResponse(
            embeddings=embeddings,
            model=request.model,
            dimension=len(embeddings[0]),
            count=len(embeddings)
        )

    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models", response_model=ModelsResponse)
async def list_models():
    """
    List available embedding models

    Returns:
        {
            "models": {
                "stella": {...},
                "gte-qwen2": {...},
                "nomic": {...}
            }
        }
    """
    return ModelsResponse(models=AVAILABLE_MODELS)


@app.get("/health")
async def health_check():
    """
    Health check endpoint

    Returns:
        Service status
    """
    return {
        "status": "healthy",
        "service": "on-premise-embeddings",
        "version": "1.0.0",
        "models_loaded": len(_model_cache),
        "available_models": list(AVAILABLE_MODELS.keys())
    }


@app.on_event("startup")
async def startup_event():
    """Pre-load default model on startup"""
    logger.info("🚀 Starting ON-PREMISE Embeddings Service")

    # Get default model from env (nomic is lightweight, stella is heavy)
    default_model = os.getenv("DEFAULT_MODEL", "nomic")
    logger.info(f"Loading default model: {default_model}...")

    try:
        if default_model == "nomic":
            # Pre-load nomic (lightweight: 137M params, 2-3GB RAM)
            get_cached_model("nomic")
            logger.success("✅ Default model loaded: nomic-embed-v1.5 (lightweight)")
        elif default_model == "stella":
            # Pre-load stella 1024d (heavier: 1.5B params, 8-10GB RAM)
            get_cached_model("stella", dimension=1024)
            logger.success("✅ Default model loaded: stella-1024d (heavy)")
        else:
            # Pre-load gte-qwen2
            get_cached_model("gte-qwen2")
            logger.success("✅ Default model loaded: gte-qwen2")
    except Exception as e:
        logger.warning(f"⚠️  Failed to pre-load model: {e}")

    logger.info("Service ready! Endpoints:")
    logger.info("  POST /embed - Generate embeddings")
    logger.info("  GET /models - List available models")
    logger.info("  GET /health - Health check")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down ON-PREMISE Embeddings Service")
    _model_cache.clear()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
