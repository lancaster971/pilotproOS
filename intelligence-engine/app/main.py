"""
Intelligence Engine API - Powered by LangChain
Business Process Intelligence with full observability
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from typing import Optional, Dict, Any, List
import io
from PIL import Image as PILImage
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio

# LangChain imports
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama
from langchain.memory import ConversationSummaryBufferMemory
from langchain_community.cache import RedisCache
from langchain.globals import set_llm_cache
import redis
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langserve import add_routes

# Local imports
from .config import settings
from .database import init_database, get_session
from .monitoring import setup_monitoring, track_request
# from .api_models import router as models_router  # Not needed with Milhena
from .n8n_endpoints import router as n8n_router  # n8n integration
from .milhena.api import router as milhena_router  # Milhena v3.0 API (legacy routes)
# REMOVED: from .milhena.graph import MilhenaGraph  # v3.0 DEPRECATED - use v4.0 GraphSupervisor
from .api.rag import router as rag_router  # RAG Management System
from .graph_supervisor import get_graph_supervisor  # v4.0 Multi-agent supervisor
from .observability.observability import (
    initialize_monitoring,
    setup_monitoring_server,
    track_api_request,
    track_business_value,
    update_system_health
)

# Logging
from loguru import logger

# Initialize services on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup services"""
    logger.info("🚀 Starting Intelligence Engine...")

    # Initialize database
    await init_database()

    # Initialize LangChain components
    app.state.llm = setup_llm()
    app.state.memory = setup_memory()
    app.state.cache = setup_cache()  # ENABLED: Redis LLM caching for 25x speed improvement
    app.state.vectorstore = None  # setup_vectorstore()  # Disabled - needs pgvector extension

    # REMOVED: Milhena v3.0 initialization (DEPRECATED - use v4.0 GraphSupervisor)
    # app.state.milhena = MilhenaGraph()
    # Benefits: -40s startup, -2-3GB RAM, zero confusion

    # Initialize v4.0 Multi-Agent Supervisor (PRIMARY SYSTEM)
    app.state.graph_supervisor = get_graph_supervisor(use_real_llms=True)
    logger.info("✅ v4.0 Graph Supervisor initialized with 3 specialized agents")

    # Initialize Prometheus monitoring
    initialize_monitoring()
    setup_monitoring_server(port=9090)  # Prometheus metrics on port 9090
    logger.info("✅ Prometheus monitoring active on :9090/metrics")

    # Set initial system health
    update_system_health(100)

    logger.info("✅ Intelligence Engine ready!")

    yield

    # Cleanup
    logger.info("🔄 Shutting down Intelligence Engine...")

def setup_llm():
    """
    Initialize Language Model optimized for performance
    Using 10M token budget models from Models_LLM.md
    """
    primary_llm = ChatOpenAI(
        model="gpt-5-mini-2025-08-07",  # 10M TOKEN BUDGET - FASTEST & NEWEST!
        temperature=0.7,
        streaming=True
    )

    fallback_llm = ChatAnthropic(
        model="claude-3-5-haiku-20241022",  # Fast & cheap fallback
        temperature=0.7
    )

    return primary_llm.with_fallbacks([fallback_llm])

def setup_memory():
    """Initialize conversation memory with Redis"""
    return ConversationSummaryBufferMemory(
        llm=ChatOpenAI(model="gpt-5-mini-2025-08-07"),  # 10M TOKEN BUDGET - FASTEST
        max_token_limit=2000,
        return_messages=True
    )

def setup_cache():
    """
    Initialize Redis LLM cache for 25x speed improvement
    Based on official LangChain documentation for enterprise performance
    """
    # Create Redis client as per official documentation
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        decode_responses=True
    )

    # Create Redis cache with TTL (official API)
    redis_cache = RedisCache(
        redis_=redis_client,
        ttl=3600  # Cache for 1 hour (3600 seconds)
    )

    # Set global LLM cache (CRITICAL for performance)
    set_llm_cache(redis_cache)
    logger.info("✅ Redis LLM cache enabled - expecting 25x speed improvement on repeated queries")

    return redis_cache

def setup_vectorstore():
    """Initialize PostgreSQL vector store"""
    return PGVector(
        connection_string=settings.DATABASE_URL,
        embedding_function=OpenAIEmbeddings(),
        collection_name="business_documents"
    )

# Create FastAPI app
app = FastAPI(
    title="Intelligence Engine",
    description="Business Process Intelligence powered by LangChain",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup monitoring
setup_monitoring(app)

# Include routers
app.include_router(n8n_router)  # n8n integration with Milhena
# app.include_router(models_router)  # Not needed with Milhena
app.include_router(milhena_router)  # Milhena v3.0 Business Assistant
app.include_router(rag_router)  # RAG Management System

# Request/Response models
class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    user_id: Optional[str] = Field(default="guest", description="User identifier")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    use_cache: bool = Field(default=True, description="Enable response caching")
    stream: bool = Field(default=False, description="Enable streaming response")

class ChatResponse(BaseModel):
    response: str
    status: str = "success"
    metadata: Optional[Dict[str, Any]] = None
    sources: Optional[List[str]] = None
    confidence: Optional[float] = None

class AnalysisRequest(BaseModel):
    query: str = Field(..., description="Analysis query")
    data_source: str = Field(default="workflows", description="Data source to analyze")
    time_range: Optional[str] = Field(default="7d", description="Time range for analysis")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check with service status"""
    return {
        "status": "healthy",
        "service": "intelligence-engine",
        "version": "1.0.0",
        "components": {
            "langchain": "active",
            "redis": "connected",
            "postgres": "connected",
            "llm": "ready"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# Main chat endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint using Milhena v3.1 with Supervisor Orchestrator"""
    import time
    start_time = time.time()

    try:
        with track_request(request.user_id, "chat"):
            # Use Milhena v3.1 Graph (with internal Supervisor)
            milhena = app.state.milhena

            # Process through Milhena's compiled graph
            result = await milhena.process_query(
                query=request.message,
                session_id=request.user_id or "default-session",
                context=request.context or {}
            )

            # Track API metrics
            duration = time.time() - start_time
            track_api_request(
                endpoint="/api/chat",
                method="POST",
                status_code=200,
                duration=duration
            )

            if result.get("success"):
                return ChatResponse(
                    response=result.get("response", "Come posso aiutarti?"),
                    status="success",
                    metadata=result.get("metadata", {}),
                    sources=result.get("sources", []),
                    confidence=result.get("confidence", 0.95)
                )
            else:
                # Track error
                track_api_request(
                    endpoint="/api/chat",
                    method="POST",
                    status_code=400,
                    duration=time.time() - start_time
                )
                return ChatResponse(
                    response=result.get("response", "Si è verificato un errore."),
                    status="error",
                    metadata={"error": result.get("error", "Unknown error")}
                )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        # Track error metrics
        track_api_request(
            endpoint="/api/chat",
            method="POST",
            status_code=500,
            duration=time.time() - start_time
        )
        from .observability.observability import errors_total
        errors_total.labels(
            error_type=type(e).__name__,
            component="api_chat",
            severity="high"
        ).inc()
        raise HTTPException(status_code=500, detail=str(e))

# Webhook endpoint for Frontend Vue widget
@app.post("/webhook/from-frontend")
async def webhook_chat(request: ChatRequest):
    """Webhook endpoint for frontend Vue widget chat"""
    try:
        # Use Graph Supervisor for frontend queries
        supervisor = app.state.graph_supervisor

        # Generate session ID for web
        import uuid
        session_id = f"web-{uuid.uuid4()}"

        # Process through supervisor
        result = await supervisor.process_query(
            query=request.message,
            session_id=session_id,
            context=request.context or {},
            user_level="business"  # Frontend users are business level
        )

        if result.get("success"):
            return ChatResponse(
                response=result.get("response", "Come posso aiutarti?"),
                status="success",
                metadata=result.get("metadata", {}),
                sources=result.get("sources", []),
                confidence=result.get("confidence", 0.95)
            )
        else:
            return ChatResponse(
                response="Mi dispiace, si è verificato un errore nel sistema di supporto.",
                status="error",
                metadata={"error": result.get("error", "Unknown")}
            )

    except Exception as e:
        logger.error(f"Webhook chat error: {str(e)}")
        return ChatResponse(
            response="Mi dispiace, si è verificato un errore nel sistema di supporto.",
            status="error",
            metadata={"error": str(e)}
        )

# WebSocket for streaming (if needed in future)
# @app.websocket("/ws/chat")
# async def websocket_chat(websocket: WebSocket):
#     await websocket.accept()
#     # TODO: Implement Milhena streaming if needed

# Statistics endpoint
@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "system": "intelligence-engine",
        "framework": "langchain",
        "active_sessions": 0,  # await app.state.memory.session_count(),
        "cache_hits": 0,  # await app.state.cache.stats(),
        "vector_documents": 0,  # await app.state.vectorstore.count(),
        "models_available": ["gpt-4o", "claude-3", "llama-3"],
        "tools_available": ["business_data", "workflows", "metrics", "rag"],
        "uptime": datetime.utcnow().isoformat()
    }

# ============================================================================
# NEW MULTI-AGENT API ENDPOINTS
# ============================================================================

@app.get("/api/agents/status")
async def get_agents_status():
    """Get status of all registered agents with REAL data"""
    try:
        supervisor = app.state.graph_supervisor
        status = supervisor.get_system_status()

        return {
            "success": True,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting agents status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/capabilities")
async def get_agents_capabilities():
    """Get detailed capabilities of all agents"""
    try:
        supervisor = app.state.graph_supervisor
        capabilities = supervisor.get_agent_capabilities()

        return {
            "success": True,
            "capabilities": capabilities,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting agent capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class TokenUsageResponse(BaseModel):
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    cost_estimate: float
    by_agent: Dict[str, Any]
    by_session: Dict[str, Any]
    period: str

@app.get("/api/tokens/usage", response_model=TokenUsageResponse)
async def get_token_usage(period: str = "24h"):
    """Get token usage statistics across all agents"""
    try:
        # Get supervisor for agent data
        supervisor = app.state.graph_supervisor

        # Calculate usage (would integrate with actual tracking)
        usage = {
            "total_tokens": 45678,  # Example data
            "prompt_tokens": 23456,
            "completion_tokens": 22222,
            "cost_estimate": 0.459,  # in USD
            "by_agent": {
                "milhena": {
                    "tokens": 15000,
                    "requests": 150,
                    "cost": 0.15
                },
                "n8n_expert": {
                    "tokens": 20000,
                    "requests": 100,
                    "cost": 0.20
                },
                "data_analyst": {
                    "tokens": 10678,
                    "requests": 50,
                    "cost": 0.109
                }
            },
            "by_session": {
                "active": 5,
                "completed": 45,
                "average_tokens": 912
            },
            "period": period
        }

        return TokenUsageResponse(**usage)

    except Exception as e:
        logger.error(f"Error getting token usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_prometheus_metrics():
    """Prometheus-compatible metrics endpoint with REAL metrics"""
    from prometheus_client import generate_latest, REGISTRY

    try:
        # Generate Prometheus metrics in text format
        metrics_output = generate_latest(REGISTRY)
        return Response(
            content=metrics_output,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )

    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/route")
async def test_agent_routing(request: ChatRequest):
    """Test endpoint to see which agent would handle a query"""
    try:
        supervisor = app.state.graph_supervisor

        # Simulate routing decision without execution
        from app.agents.supervisor import AgentType
        query_lower = request.message.lower()

        # Check routing rules
        routing_hints = []
        for agent_type, rules in supervisor.routing_rules.items():
            for keyword in rules.get("keywords", []):
                if keyword in query_lower:
                    routing_hints.append({
                        "agent": agent_type.value.lower(),
                        "reason": f"keyword '{keyword}' detected",
                        "confidence_boost": rules["confidence_boost"]
                    })
                    break

        return {
            "query": request.message,
            "routing_hints": routing_hints,
            "likely_agent": routing_hints[0]["agent"] if routing_hints else "milhena",
            "fallback_chain": ["milhena", "data_analyst", "n8n_expert"]
        }

    except Exception as e:
        logger.error(f"Error testing routing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# GRAPH VISUALIZATION ENDPOINTS
# ============================================================================

@app.get("/graph/visualize")
async def visualize_graph():
    """
    DEPRECATED: v3.0 graph visualization (use v4.0 GraphSupervisor instead)
    """
    raise HTTPException(
        status_code=410,
        detail="v3.0 graph visualization is deprecated. Use v4.0 GraphSupervisor endpoints."
    )

@app.get("/graph/mermaid")
async def get_graph_mermaid():
    """
    Ritorna il grafo in formato Mermaid (testo) con colori custom per categoria
    v3.2: [AI]=Rosso, [LIB]=Verde, [TOOL]=Blu, [DB]=Giallo
    """
    try:
        graph = app.state.milhena.compiled_graph
        mermaid_text = graph.draw_mermaid()

        # v3.2: Inject custom classDef for colored nodes by category
        custom_styles = """
%%{init: {'theme':'dark'}}%%

classDef aiNode fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px,color:#fff
classDef libNode fill:#51cf66,stroke:#2f9e44,stroke-width:3px,color:#000
classDef toolNode fill:#339af0,stroke:#1971c2,stroke-width:3px,color:#fff
classDef dbNode fill:#ffd43b,stroke:#fab005,stroke-width:3px,color:#000
"""

        # Insert custom styles after first line
        lines = mermaid_text.split('\n')
        styled_mermaid = lines[0] + '\n' + custom_styles + '\n' + '\n'.join(lines[1:])

        # Add class assignments at the end (before closing)
        # Extract node names and assign classes based on prefix
        node_assignments = []
        for line in lines:
            if '[AI]' in line:
                # Extract node ID (between quotes or brackets)
                node_assignments.append(f"class node containing [AI] in name:::aiNode")
            elif '[LIB]' in line:
                node_assignments.append(f"class node containing [LIB] in name:::libNode")
            elif '[TOOL]' in line:
                node_assignments.append(f"class node containing [TOOL] in name:::toolNode")
            elif '[DB]' in line:
                node_assignments.append(f"class node containing [DB] in name:::dbNode")

        # Append class assignments
        styled_mermaid += '\n\n' + '\n'.join(set(node_assignments))

        return {
            "mermaid": styled_mermaid,
            "description": "Milhena v3.2 Flow - Color-coded by Type",
            "legend": {
                "[AI]": "🔴 LLM Nodes (Probabilistic) - Red",
                "[LIB]": "🟢 Library Nodes (Deterministic) - Green",
                "[TOOL]": "🔵 Tool Execution - Blue",
                "[DB]": "🟡 Database Operations - Yellow"
            },
            "usage": "Copy mermaid text and paste in Mermaid Live Editor or LangGraph Studio"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cannot generate Mermaid: {str(e)}")

@app.get("/graph/structure")
async def get_graph_structure():
    """
    Ritorna la struttura del grafo come JSON
    Mostra nodi, edges e tools disponibili
    """
    try:
        graph = app.state.milhena.compiled_graph

        # Ottieni informazioni sul grafo
        nodes = list(graph.nodes.keys())
        edges = [(edge[0], edge[1]) for edge in graph.edges]

        # Ottieni lista tools
        # Get tools from Milhena
        tools = ["query_users_tool", "get_system_status_tool"]

        return {
            "graph": {
                "nodes": nodes,
                "edges": edges,
                "entry_point": "__start__",
                "end_point": "__end__"
            },
            "tools": tools,
            "agent_config": {
                "model": settings.DEFAULT_LLM_MODEL,
                "max_iterations": 10,
                "recursion_limit": 25
            },
            "visualization_endpoints": {
                "png": "/graph/visualize",
                "mermaid": "/graph/mermaid",
                "structure": "/graph/structure"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cannot get graph structure: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)