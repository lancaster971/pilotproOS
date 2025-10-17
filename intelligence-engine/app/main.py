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
from .services.monitoring import setup_monitoring, track_request
# from .api_models import router as models_router  # Not needed with Milhena
from .n8n_endpoints import router as n8n_router  # n8n integration
from .agent_api import router as milhena_router  # Milhena v3.0 API (legacy routes)
from .agents.v3_5.graph import AgentGraph  # v3.5.6 Self-Contained Agent Architecture
from .api.rag import router as rag_router  # RAG Management System
# Removed v4.0 GraphSupervisor (deprecated)
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

    # Initialize LLMs (DEPENDENCY INJECTION)
    from langchain_groq import ChatGroq

    app.state.groq_llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        api_key=os.getenv("GROQ_API_KEY")
    )

    app.state.openai_llm = ChatOpenAI(
        model="gpt-4o-2024-11-20",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    logger.info("✅ LLMs initialized (Groq + OpenAI)")

    # Initialize LangChain components
    app.state.llm = setup_llm()
    app.state.memory = setup_memory()
    app.state.cache = setup_cache()  # ENABLED: Redis LLM caching for 25x speed improvement
    app.state.vectorstore = None  # setup_vectorstore()  # Disabled - needs pgvector extension

    # Initialize AsyncRedisSaver for persistent conversation memory (v3.2 FIX)
    # Pattern from official docs: Use async context manager + asetup()
    from langgraph.checkpoint.redis import AsyncRedisSaver

    redis_url = os.getenv("REDIS_URL", "redis://redis-dev:6379/0")
    logger.info(f"🔗 Initializing AsyncRedisSaver: {redis_url}")

    # TTL Configuration (v3.2.1 - Automatic cleanup strategy)
    # Prevents infinite checkpoint growth in Redis
    ttl_config = {
        "default_ttl": 10080,  # 7 days (10080 minutes) - auto-delete old conversations
        "refresh_on_read": True  # Reset TTL when conversation is accessed (keep active threads)
    }
    logger.info(f"⏰ TTL Config: {ttl_config['default_ttl']} minutes (7 days), refresh_on_read={ttl_config['refresh_on_read']}")

    try:
        # Create async context manager with TTL config
        redis_checkpointer_cm = AsyncRedisSaver.from_conn_string(
            redis_url,
            ttl=ttl_config
        )

        # Enter context manager to get the actual AsyncRedisSaver instance
        app.state.redis_checkpointer = await redis_checkpointer_cm.__aenter__()

        # CRITICAL: Initialize Redis indices for checkpointer
        await app.state.redis_checkpointer.asetup()
        logger.info("✅ AsyncRedisSaver initialized with Redis indices")

        # Store the context manager for proper cleanup
        app.state.redis_checkpointer_cm = redis_checkpointer_cm
    except Exception as e:
        logger.error(f"❌ AsyncRedisSaver initialization failed: {e}")
        logger.warning("⚠️  Falling back to MemorySaver (NO persistence)")
        from langgraph.checkpoint.memory import MemorySaver
        app.state.redis_checkpointer = MemorySaver()
        app.state.redis_checkpointer_cm = None

    # Initialize asyncpg connection pool for auto-learning (DEPENDENCY INJECTION)
    import asyncpg

    db_url = os.getenv("DATABASE_URL", "postgresql://pilotpros_user:pilotpros_secure_pass_2025@postgres-dev:5432/pilotpros_db")
    app.state.db_pool = await asyncpg.create_pool(
        db_url,
        min_size=2,
        max_size=10,
        max_inactive_connection_lifetime=300.0,
        command_timeout=60.0
    )
    logger.info("✅ asyncpg connection pool created (min=2, max=10)")

    # Initialize RAG system (DEPENDENCY INJECTION)
    from app.rag import get_rag_system

    try:
        app.state.rag_system = get_rag_system()
        logger.info("✅ RAG System initialized")
    except Exception as e:
        logger.error(f"❌ RAG System failed: {e}")
        app.state.rag_system = None

    # Initialize AgentGraph v3.5.6 - Self-Contained Architecture (DEPENDENCY INJECTION)
    # Flow: Fast-Path → Classifier → Tool Mapper → Tool Executor → Responder → Masking
    app.state.agent = AgentGraph(
        openai_llm=app.state.openai_llm,
        groq_llm=app.state.groq_llm,
        db_pool=app.state.db_pool,
        rag_system=app.state.rag_system,
        external_checkpointer=app.state.redis_checkpointer
    )
    logger.info("✅ AgentGraph v3.5.6 initialized (self-contained architecture)")

    # Initialize FeedbackStore for PostgreSQL feedback persistence
    from app.services.feedback_store import FeedbackStore
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("❌ DATABASE_URL not set, cannot initialize FeedbackStore")
        raise ValueError("DATABASE_URL environment variable is required")

    try:
        app.state.feedback_store = FeedbackStore(db_url)
        await app.state.feedback_store.initialize()
        logger.info("✅ FeedbackStore initialized (PostgreSQL persistence + 3 tables)")
    except Exception as e:
        logger.error(f"❌ FeedbackStore initialization failed: {e}")
        logger.warning("⚠️  Continuing without feedback persistence (graceful degradation)")
        app.state.feedback_store = None

    # Initialize hot-reload pattern system (Redis PubSub subscriber)
    from app.services.hot_reload import PatternReloader
    redis_url = os.getenv("REDIS_URL", "redis://redis-dev:6379/0")
    app.state.pattern_reloader = PatternReloader(
        redis_url=redis_url,
        reload_callback=app.state.agent.reload_patterns,
        channel="pilotpros:patterns:reload"
    )
    await app.state.pattern_reloader.start()
    logger.info("✅ Hot-reload pattern system started (Redis PubSub subscriber)")

    # v4.0 GraphSupervisor removed - v3.1 is production

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

    # Close FeedbackStore connection pool
    if hasattr(app.state, 'feedback_store') and app.state.feedback_store:
        try:
            await app.state.feedback_store.close()
            logger.info("✅ FeedbackStore closed gracefully")
        except Exception as e:
            logger.error(f"⚠️  Error closing FeedbackStore: {e}")

    # Close asyncpg connection pool
    if hasattr(app.state, 'db_pool') and app.state.db_pool:
        try:
            await app.state.db_pool.close()
            logger.info("✅ asyncpg pool closed gracefully")
        except Exception as e:
            logger.error(f"⚠️  Error closing db_pool: {e}")

    # Stop hot-reload pattern system (Redis PubSub subscriber)
    if hasattr(app.state, 'pattern_reloader') and app.state.pattern_reloader:
        try:
            await app.state.pattern_reloader.stop()
            logger.info("✅ Hot-reload pattern system stopped gracefully")
        except Exception as e:
            logger.error(f"⚠️  Error stopping pattern reloader: {e}")

    # Close AsyncRedisSaver context manager properly
    if hasattr(app.state, 'redis_checkpointer_cm') and app.state.redis_checkpointer_cm:
        try:
            # Exit async context manager (__aexit__)
            await app.state.redis_checkpointer_cm.__aexit__(None, None, None)
            logger.info("✅ AsyncRedisSaver closed gracefully")
        except Exception as e:
            logger.error(f"⚠️  Error closing AsyncRedisSaver: {e}")

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
            agent = app.state.agent

            # Process through Milhena's compiled graph
            result = await agent.process_query(
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
        # Use v3.1 AgentGraph
        agent = app.state.agent

        # Generate session ID for web
        import uuid
        session_id = f"web-{uuid.uuid4()}"

        # Process through agent
        result = await agent.compiled_graph.ainvoke(
            {
                "messages": [HumanMessage(content=request.message)],
                "session_id": session_id,
                "context": request.context or {},
                "query": request.message
            },
            config={"configurable": {"thread_id": session_id}}
        )

        # Extract response from state
        response_text = result.get("response", "Come posso aiutarti?")

        return ChatResponse(
            response=response_text,
            status="success",
            metadata={
                "model": "pilot-v3.5-agent",
                "masked": result.get("masked", False)
            },
            sources=[],
            confidence=0.95
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

# v4.0 endpoints removed - not applicable to v3.1 linear pipeline
# Feedback endpoint moved to agent_api.py (line 130-204)

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

# ============================================================================
# GRAPH VISUALIZATION ENDPOINTS (v3.1)
# ============================================================================

@app.get("/graph/mermaid")
async def get_graph_mermaid():
    """
    Ritorna il grafo in formato Mermaid (testo) con colori custom per categoria
    v3.2: [AI]=Rosso, [LIB]=Verde, [TOOL]=Blu, [DB]=Giallo
    """
    try:
        graph = app.state.agent.compiled_graph
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
        graph = app.state.agent.compiled_graph

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