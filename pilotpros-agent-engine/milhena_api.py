#!/usr/bin/env python3
"""
Milhena Enterprise API - REST API con FastAPI
Espone il sistema multi-agent Milhena via HTTP con autenticazione e rate limiting
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import asyncio
import json
import time
import jwt
import os
from datetime import datetime, timedelta
from pathlib import Path
import uvicorn
from dotenv import load_dotenv

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import Milhena Enterprise
from agents.crews.milhena_orchestrator_enterprise import MilhenaEnterpriseOrchestrator

# Load environment
load_dotenv()

# ============= CONFIGURATION =============
API_VERSION = "v1"
API_TITLE = "Milhena Enterprise API"
API_DESCRIPTION = """
🤖 **Milhena Multi-Agent System API**

Enterprise-grade conversational AI with:
- 🧠 Persistent memory per user
- 🌍 Multi-language support (IT, EN, FR, ES, DE)
- 📊 Analytics and monitoring
- 💾 Response caching
- 🔐 JWT authentication
- ⚡ Rate limiting
- 📡 WebSocket support for real-time
"""

# Security
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# ============= MODELS =============
class QuestionRequest(BaseModel):
    """Request model for questions"""
    question: str = Field(..., min_length=1, max_length=1000, description="User question")
    context: Optional[str] = Field(None, max_length=500, description="Additional context")
    user_id: Optional[str] = Field("default", description="User identifier for memory")
    language: Optional[str] = Field(None, description="Force specific language (it/en/fr/es/de)")

class QuestionResponse(BaseModel):
    """Response model for answers"""
    success: bool
    response: Optional[str] = None
    question_type: Optional[str] = None
    language: Optional[str] = None
    confidence: Optional[float] = None
    cached: bool = False
    response_time_ms: float
    user_id: str
    memory_interactions: int = 0
    error: Optional[str] = None

class TokenRequest(BaseModel):
    """Request model for authentication"""
    username: str
    password: str

class TokenResponse(BaseModel):
    """Response model for authentication"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60

class StatsResponse(BaseModel):
    """Response model for system statistics"""
    total_users: int
    total_requests: int
    cache_hit_rate: float
    avg_response_time_ms: float
    top_question_types: List[tuple]
    languages_used: Dict[str, int]
    error_rate: float

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    version: str
    uptime_seconds: float
    memory_mb: float

# ============= AUTHENTICATION =============
security = HTTPBearer()

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

# ============= APPLICATION =============
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version="2.0.0",
    docs_url=f"/api/{API_VERSION}/docs",
    redoc_url=f"/api/{API_VERSION}/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize Milhena
orchestrator = MilhenaEnterpriseOrchestrator(
    enable_memory=True,
    enable_analytics=True,
    enable_cache=True
)

# Track API uptime
START_TIME = time.time()

# ============= ENDPOINTS =============

@app.post(f"/api/{API_VERSION}/auth/token", response_model=TokenResponse)
async def login(request: TokenRequest):
    """
    Authenticate and receive JWT token

    Default credentials for testing:
    - username: admin
    - password: milhena2025
    """
    # Simple authentication (replace with real auth in production)
    if request.username == "admin" and request.password == "milhena2025":
        access_token = create_access_token(data={"sub": request.username})
        return TokenResponse(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

@app.post(
    f"/api/{API_VERSION}/ask",
    response_model=QuestionResponse,
    dependencies=[Depends(verify_token)]
)
@limiter.limit("30/minute")
async def ask_question(
    request: Request,
    question_request: QuestionRequest,
    background_tasks: BackgroundTasks
):
    """
    Ask a question to Milhena multi-agent system

    Features:
    - Automatic language detection
    - User-specific memory
    - Response caching
    - Analytics tracking
    """
    try:
        # Execute question
        result = await orchestrator.analyze_question_enterprise(
            question=question_request.question,
            context=question_request.context,
            user_id=question_request.user_id
        )

        # Background task for additional processing if needed
        background_tasks.add_task(log_interaction, question_request.dict(), result)

        return QuestionResponse(**result)

    except Exception as e:
        return QuestionResponse(
            success=False,
            response=None,
            error=str(e),
            response_time_ms=0,
            user_id=question_request.user_id
        )

@app.get(
    f"/api/{API_VERSION}/stats",
    response_model=StatsResponse,
    dependencies=[Depends(verify_token)]
)
async def get_statistics():
    """
    Get system statistics and analytics
    """
    stats = orchestrator.get_system_stats()
    analytics = stats.get("analytics", {})

    return StatsResponse(
        total_users=stats.get("users_tracked", 0),
        total_requests=analytics.get("total_requests", 0),
        cache_hit_rate=stats.get("cache", {}).get("hit_rate", 0),
        avg_response_time_ms=analytics.get("avg_response_time_ms", 0),
        top_question_types=analytics.get("top_question_types", []),
        languages_used=analytics.get("languages_detected", {}),
        error_rate=analytics.get("error_rate", 0)
    )

@app.get(
    f"/api/{API_VERSION}/health",
    response_model=HealthResponse
)
async def health_check():
    """
    Health check endpoint
    """
    import psutil

    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024

    return HealthResponse(
        status="healthy",
        version="2.0.0",
        uptime_seconds=time.time() - START_TIME,
        memory_mb=round(memory_mb, 2)
    )

@app.delete(
    f"/api/{API_VERSION}/cache/clear",
    dependencies=[Depends(verify_token)]
)
async def clear_cache():
    """
    Clear response cache
    """
    if orchestrator.cache:
        orchestrator.cache.clear_expired()
        return {"message": "Cache cleared successfully"}
    return {"message": "Cache not enabled"}

@app.get(
    f"/api/{API_VERSION}/memory/{{user_id}}",
    dependencies=[Depends(verify_token)]
)
async def get_user_memory(user_id: str):
    """
    Get memory for specific user
    """
    memory = orchestrator.get_or_create_memory(user_id)
    if memory:
        return {
            "user_id": user_id,
            "interactions_count": memory.user_profile.get("interactions_count", 0),
            "last_interaction": memory.user_profile.get("last_interaction"),
            "preferred_language": memory.user_profile.get("preferred_language"),
            "recent_interactions": list(memory.memory)[-5:]  # Last 5 interactions
        }
    return {"error": "Memory not enabled"}

@app.delete(
    f"/api/{API_VERSION}/memory/{{user_id}}",
    dependencies=[Depends(verify_token)]
)
async def clear_user_memory(user_id: str):
    """
    Clear memory for specific user
    """
    if user_id in orchestrator.memory_store:
        del orchestrator.memory_store[user_id]
        return {"message": f"Memory cleared for user {user_id}"}
    return {"message": "User not found"}

# ============= WEBSOCKET SUPPORT =============
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    """WebSocket connection manager"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket(f"/api/{API_VERSION}/ws/{{user_id}}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time communication
    """
    await manager.connect(websocket)

    try:
        while True:
            # Receive question
            data = await websocket.receive_json()

            # Process question
            result = await orchestrator.analyze_question_enterprise(
                question=data.get("question", ""),
                context=data.get("context"),
                user_id=user_id
            )

            # Send response
            await websocket.send_json(result)

            # Broadcast to all connections (optional)
            await manager.broadcast({
                "type": "activity",
                "user": user_id,
                "timestamp": datetime.now().isoformat()
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast({
            "type": "disconnect",
            "user": user_id
        })

# ============= BACKGROUND TASKS =============
def log_interaction(request_data: dict, response_data: dict):
    """Background task to log interactions"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "request": request_data,
        "response": {
            "success": response_data.get("success"),
            "question_type": response_data.get("question_type"),
            "language": response_data.get("language"),
            "cached": response_data.get("cached"),
            "response_time_ms": response_data.get("response_time_ms")
        }
    }

    # Save to file (or send to external service)
    log_file = Path("milhena_persistence/api_interactions.jsonl")
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

# ============= STARTUP/SHUTDOWN =============
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger = logging.getLogger(__name__)
    logger.info("🚀 Milhena API starting...")
    logger.info(f"📁 Persistence directory: milhena_persistence/")
    logger.info(f"🔐 Authentication: Enabled")
    logger.info(f"⚡ Rate limiting: 30 requests/minute")
    logger.info(f"📡 WebSocket: Enabled")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger = logging.getLogger(__name__)
    logger.info("👋 Milhena API shutting down...")

    # Save final statistics
    if orchestrator.analytics:
        stats = orchestrator.get_system_stats()
        with open("milhena_persistence/final_stats.json", "w") as f:
            json.dump(stats, f, indent=2)

# ============= MAIN =============
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║          MILHENA ENTERPRISE API - Starting...           ║
    ║                                                          ║
    ║  Endpoints:                                              ║
    ║  - POST   /api/v1/auth/token    (Get JWT token)         ║
    ║  - POST   /api/v1/ask           (Ask question)          ║
    ║  - GET    /api/v1/stats         (Get statistics)        ║
    ║  - GET    /api/v1/health        (Health check)          ║
    ║  - DELETE /api/v1/cache/clear   (Clear cache)           ║
    ║  - GET    /api/v1/memory/{id}   (Get user memory)       ║
    ║  - WS     /api/v1/ws/{id}       (WebSocket)             ║
    ║                                                          ║
    ║  Docs:    http://localhost:8000/api/v1/docs             ║
    ║  Auth:    admin / milhena2025                           ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "milhena_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )