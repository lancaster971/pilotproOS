#!/usr/bin/env python3
"""
Agent Engine API - Main Entry Point
Sistema Multi-Agent Runtime per PilotProOS
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import NEW FAST BYPASS SYSTEM
try:
    from fast_bypass import get_token_saver
    FAST_BYPASS_AVAILABLE = True
    logger.info("✅ Fast Bypass System con GPT-4o + Token Monitor caricato!")
except ImportError as e:
    FAST_BYPASS_AVAILABLE = False
    logger.warning(f"⚠️ Fast Bypass non disponibile: {e}")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Agent Engine API",
    description="Multi-Agent Runtime per PilotProOS",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specificare domini
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "guest"
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    status: str = "success"
    metadata: Optional[Dict[str, Any]] = None


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "agent-engine",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Agent Engine API",
        "status": "running",
        "endpoints": [
            "/health",
            "/api/chat",
            "/api/agents"
        ]
    }

# Inizializza CrewAI VERO con l'orchestrator Milhena
milhena_orchestrator = None

def get_milhena():
    """Get or create REAL CrewAI Milhena orchestrator"""
    global milhena_orchestrator
    if milhena_orchestrator is None:
        try:
            # Usa CrewAI VERO con versione 0.193.2
            from agents.crews.milhena_orchestrator_enterprise import MilhenaEnterpriseOrchestrator
            milhena_orchestrator = MilhenaEnterpriseOrchestrator(
                enable_memory=True,
                enable_analytics=True,
                enable_cache=True
            )
            logger.info("✅ CrewAI Milhena Enterprise Orchestrator REALE inizializzato!")
        except Exception as e:
            logger.error(f"❌ Errore inizializzazione CrewAI: {e}")
            # Usa SimpleMilhena come fallback
            try:
                from agents.milhena_simple import SimpleMilhenaOrchestrator
                milhena_orchestrator = SimpleMilhenaOrchestrator()
                logger.info("Fallback to SimpleMilhena (no CrewAI)")
            except:
                raise Exception(f"Cannot initialize any orchestrator: {e}")
    return milhena_orchestrator

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat endpoint con NUOVO SISTEMA GPT-4o + Fast Bypass"""
    try:
        logger.info(f"📩 Chat request: {request.message[:50]}... (user: {request.user_id})")

        # 🚀 USA FAST BYPASS SYSTEM PRIMA (90% dei casi)
        if FAST_BYPASS_AVAILABLE:
            try:
                logger.info("🚀 Usando Fast Bypass System (GPT-4o + Token Monitor)")
                token_saver = get_token_saver()
                result = await token_saver.smart_response(request.message, request.user_id)

                return ChatResponse(
                    response=result["response"],
                    status="success",
                    metadata={
                        "user_id": request.user_id,
                        "engine": "fast-bypass-gpt4o",
                        "question_type": result.get("type", "unknown"),
                        "language": "it",
                        "response_time_ms": result.get("processing_time", 0),
                        "cached": False,
                        "llm_provider": result.get("provider", "unknown"),
                        "tokens_saved": result.get("tokens_saved", False),
                        "bypass_used": True
                    }
                )
            except Exception as bypass_error:
                logger.warning(f"⚠️ Fast Bypass failed: {bypass_error} - fallback to CrewAI")

        # 🤖 FALLBACK: CrewAI multi-agente (10% casi complessi)
        logger.info("🤖 Usando CrewAI multi-agente (caso complesso)")
        orchestrator = get_milhena()

        # Processa con CrewAI Multi-Agent System
        if hasattr(orchestrator, 'analyze_question_enterprise'):
            # Usa metodo enterprise per CrewAI completo
            result = await orchestrator.analyze_question_enterprise(
                question=request.message,
                user_id=request.user_id
            )
        else:
            # Fallback per SimpleMilhena
            result = await orchestrator.process(
                message=request.message,
                user_id=request.user_id
            )

        # Risposta REALE da CrewAI
        return ChatResponse(
            response=result.get("response", "Errore nel processare"),
            status="success" if result.get("success") else "error",
            metadata={
                "user_id": request.user_id,
                "engine": "crewai-multi-agent",
                "question_type": result.get("question_type", "unknown"),
                "language": result.get("language", "it"),
                "response_time_ms": result.get("response_time_ms", 0),
                "cached": result.get("cached", False),
                "llm_provider": result.get("llm_provider", "groq")
            }
        )
    except Exception as e:
        logger.error(f"CrewAI error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"CrewAI Error: {str(e)}"
        )

@app.get("/api/agents")
async def list_agents():
    """List REAL available agents - NO MOCK"""
    try:
        orchestrator = get_milhena()
        # Prova a ottenere info reali dall'orchestrator
        if hasattr(orchestrator, 'get_agents_info'):
            agents = orchestrator.get_agents_info()
        else:
            # Info base reali
            agents = [{
                "id": "milhena",
                "name": "Milhena v4.0",
                "type": "multi-agent-orchestrator",
                "status": "active" if milhena_orchestrator else "not_initialized",
                "llm_provider": os.getenv("PRIMARY_LLM", "groq"),
                "capabilities": [
                    "business_analysis",
                    "workflow_optimization",
                    "data_insights",
                    "crewai_orchestration"
                ],
                "crew_agents": [
                    "data_analyst",
                    "business_advisor",
                    "technical_analyst"
                ]
            }]
        return {"agents": agents}
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        return {"agents": [], "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

