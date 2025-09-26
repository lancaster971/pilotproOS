"""
API endpoints for dynamic model management
Add/Remove/Switch models WITHOUT rebuilding container!
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from .llm_manager import get_llm_manager
from loguru import logger

router = APIRouter(prefix="/api/models", tags=["models"])

class ModelConfig(BaseModel):
    """Model configuration"""
    provider: str = Field(..., description="Provider: groq, google, openrouter, anthropic, openai")
    model: str = Field(..., description="Model name/ID")
    enabled: bool = Field(default=True, description="Enable model immediately")
    api_key_env: str = Field(..., description="Environment variable for API key")
    temperature: float = Field(default=0.7, description="Temperature")
    max_tokens: Optional[int] = Field(default=2000, description="Max tokens")
    description: Optional[str] = Field(default="", description="Model description")
    base_url: Optional[str] = Field(default=None, description="Base URL for OpenRouter")

class SwitchModelRequest(BaseModel):
    """Request to switch active model"""
    model_id: str = Field(..., description="Model ID to switch to")

@router.get("/list")
async def list_models():
    """
    List all configured models
    Shows which are enabled, loaded, and available
    """
    manager = get_llm_manager()
    return {
        "models": manager.list_models(),
        "default_model": manager.config.get('default_model'),
        "fallback_chain": manager.config.get('fallback_chain', [])
    }

@router.post("/add/{model_id}")
async def add_model(model_id: str, config: ModelConfig):
    """
    ADD A NEW MODEL WITHOUT REBUILDING!

    Example:
    POST /api/models/add/new-gemini-model
    {
        "provider": "google",
        "model": "gemini-2.0-pro",
        "enabled": true,
        "api_key_env": "GOOGLE_API_KEY",
        "temperature": 0.8,
        "description": "New Gemini Pro model"
    }
    """
    try:
        manager = get_llm_manager()
        manager.add_model(model_id, config.dict())

        return {
            "status": "success",
            "message": f"Model {model_id} added successfully",
            "model_id": model_id,
            "loaded": model_id in manager.models
        }
    except Exception as e:
        logger.error(f"Failed to add model: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/remove/{model_id}")
async def remove_model(model_id: str):
    """
    Remove a model from configuration
    """
    try:
        manager = get_llm_manager()
        manager.remove_model(model_id)

        return {
            "status": "success",
            "message": f"Model {model_id} removed"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/enable/{model_id}")
async def enable_model(model_id: str):
    """
    Enable a model (load it into memory)
    """
    try:
        manager = get_llm_manager()

        if model_id not in manager.config['models']:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

        # Update config
        manager.config['models'][model_id]['enabled'] = True

        # Load model
        model = manager.load_model(model_id)

        if model:
            return {
                "status": "success",
                "message": f"Model {model_id} enabled and loaded"
            }
        else:
            return {
                "status": "error",
                "message": f"Model {model_id} enabled but failed to load (check API key)"
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/disable/{model_id}")
async def disable_model(model_id: str):
    """
    Disable a model (unload from memory)
    """
    try:
        manager = get_llm_manager()

        if model_id not in manager.config['models']:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

        # Update config
        manager.config['models'][model_id]['enabled'] = False

        # Remove from loaded models
        if model_id in manager.models:
            del manager.models[model_id]

        return {
            "status": "success",
            "message": f"Model {model_id} disabled"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/switch")
async def switch_model(request: SwitchModelRequest):
    """
    Switch the default model
    """
    try:
        manager = get_llm_manager()

        # Check if model exists
        if request.model_id not in manager.config['models']:
            raise HTTPException(status_code=404, detail=f"Model {request.model_id} not found")

        # Load model if not loaded
        if request.model_id not in manager.models:
            model = manager.load_model(request.model_id)
            if not model:
                raise HTTPException(status_code=400, detail=f"Failed to load model {request.model_id}")

        # Update default
        manager.config['default_model'] = request.model_id

        # Save config
        import json
        with open(manager.config_path, 'w') as f:
            json.dump(manager.config, f, indent=2)

        return {
            "status": "success",
            "message": f"Switched to model {request.model_id}",
            "active_model": request.model_id
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reload")
async def reload_config():
    """
    Reload configuration from file
    Useful after manual edits to models.json
    """
    try:
        manager = get_llm_manager()
        manager.reload_config()

        return {
            "status": "success",
            "message": "Configuration reloaded",
            "models_loaded": len(manager.models)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/test/{model_id}")
async def test_model(model_id: str, message: str = "Hello, test message"):
    """
    Test a specific model
    """
    try:
        manager = get_llm_manager()
        model = manager.get_model(model_id)

        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found or not loaded")

        # Test the model
        response = await model.ainvoke(message)

        return {
            "status": "success",
            "model_id": model_id,
            "test_message": message,
            "response": response.content if hasattr(response, 'content') else str(response),
            "model_info": manager.config['models'][model_id].get('description', '')
        }

    except Exception as e:
        return {
            "status": "error",
            "model_id": model_id,
            "error": str(e)
        }

@router.get("/costs")
async def get_costs():
    """
    Get cost information for all models
    """
    costs = {
        "free_tier": {
            "groq-llama": "FREE - 7,000 req/min",
            "groq-mixtral": "FREE - 7,000 req/min",
            "gemini-free": "FREE - 15 req/min, 1M tokens/min",
            "gemini-8b": "FREE - 15 req/min, 4M tokens/min"
        },
        "ultra_cheap": {
            "openrouter-cheap": "$0.15 per 1M tokens",
            "openrouter-deepseek": "$0.14 per 1M tokens",
            "claude-haiku": "$0.80 per 1M input tokens"
        },
        "premium": {
            "claude-sonnet": "$3 per 1M input tokens",
            "gpt-4o": "$2.50 per 1M input tokens"
        }
    }

    return costs