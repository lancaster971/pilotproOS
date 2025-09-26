"""
Intelligence Engine API - Powered by LangChain
Business Process Intelligence with full observability
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from typing import Optional, Dict, Any, List
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
from langchain_redis import RedisCache, RedisSemanticCache
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langserve import add_routes

# Local imports
from .config import settings
from .chains import create_business_chain, create_analysis_chain
from .tools import BusinessDataTool, WorkflowTool, MetricsTool
from .database import init_database, get_session
from .monitoring import setup_monitoring, track_request
from .n8n_endpoints import router as n8n_router
from .api_models import router as models_router

# Logging
from loguru import logger

# Initialize services on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup services"""
    logger.info("🚀 Starting Intelligence Engine...")

    # Initialize database
    await init_database()

    # Setup monitoring
    setup_monitoring(app)

    # Initialize LangChain components
    app.state.llm = setup_llm()
    app.state.memory = setup_memory()
    app.state.cache = setup_cache()
    app.state.vectorstore = setup_vectorstore()

    logger.info("✅ Intelligence Engine ready!")

    yield

    # Cleanup
    logger.info("🔄 Shutting down Intelligence Engine...")

def setup_llm():
    """Initialize Language Model with fallback"""
    primary_llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        streaming=True
    )

    fallback_llm = ChatAnthropic(
        model="claude-3-haiku-20240307",
        temperature=0.7
    )

    return primary_llm.with_fallbacks([fallback_llm])

def setup_memory():
    """Initialize conversation memory with Redis"""
    return ConversationSummaryBufferMemory(
        llm=ChatOpenAI(model="gpt-4o-mini"),
        max_token_limit=2000,
        return_messages=True
    )

def setup_cache():
    """Initialize Redis cache for responses"""
    return RedisSemanticCache(
        redis_url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        embedding=OpenAIEmbeddings(),
        score_threshold=0.95
    )

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

# Include routers
app.include_router(n8n_router)
app.include_router(models_router)

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
    """Main chat endpoint with LangChain processing"""
    try:
        with track_request(request.user_id, "chat"):
            # Check cache first
            if request.use_cache:
                cached = await app.state.cache.get(request.message)
                if cached:
                    logger.info(f"Cache hit for: {request.message[:50]}")
                    return ChatResponse(
                        response=cached,
                        status="success",
                        metadata={"cached": True}
                    )

            # Create business chain with tools
            chain = create_business_chain(
                llm=app.state.llm,
                memory=app.state.memory,
                tools=[
                    BusinessDataTool(),
                    WorkflowTool(),
                    MetricsTool()
                ]
            )

            # Process message
            response = await chain.ainvoke({
                "input": request.message,
                "user_id": request.user_id,
                "context": request.context
            })

            # Cache response
            if request.use_cache:
                await app.state.cache.set(request.message, response["output"])

            return ChatResponse(
                response=response["output"],
                status="success",
                metadata={
                    "model": response.get("model_used"),
                    "tools_used": response.get("tools_used", []),
                    "processing_time_ms": response.get("processing_time")
                },
                sources=response.get("sources"),
                confidence=response.get("confidence")
            )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Analysis endpoint
@app.post("/api/analyze")
async def analyze(request: AnalysisRequest):
    """Advanced analysis with LangChain"""
    try:
        with track_request("system", "analyze"):
            chain = create_analysis_chain(
                llm=app.state.llm,
                vectorstore=app.state.vectorstore
            )

            result = await chain.ainvoke({
                "query": request.query,
                "data_source": request.data_source,
                "time_range": request.time_range
            })

            return {
                "analysis": result["analysis"],
                "insights": result["insights"],
                "recommendations": result["recommendations"],
                "visualizations": result.get("charts", []),
                "confidence": result["confidence"]
            }

    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for streaming
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for streaming responses"""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            # Stream response
            chain = create_business_chain(
                llm=app.state.llm,
                memory=app.state.memory,
                streaming=True
            )

            async for chunk in chain.astream({
                "input": data["message"],
                "user_id": data.get("user_id", "guest")
            }):
                await websocket.send_json({
                    "type": "stream",
                    "content": chunk
                })

            await websocket.send_json({
                "type": "end",
                "content": "Stream completed"
            })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()

# LangServe routes for chain deployment
add_routes(
    app,
    create_business_chain(app.state.llm, app.state.memory),
    path="/business"
)

add_routes(
    app,
    create_analysis_chain(app.state.llm, app.state.vectorstore),
    path="/analysis"
)

# Statistics endpoint
@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "system": "intelligence-engine",
        "framework": "langchain",
        "active_sessions": await app.state.memory.session_count(),
        "cache_hits": await app.state.cache.stats(),
        "vector_documents": await app.state.vectorstore.count(),
        "models_available": ["gpt-4o", "claude-3", "llama-3"],
        "tools_available": ["business_data", "workflows", "metrics", "rag"],
        "uptime": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)