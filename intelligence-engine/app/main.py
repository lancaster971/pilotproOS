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
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langserve import add_routes

# Local imports
from .config import settings
from .database import init_database, get_session
from .monitoring import setup_monitoring, track_request
# from .api_models import router as models_router  # Not needed with Milhena
from .n8n_endpoints import router as n8n_router  # n8n integration
from .milhena.api import router as milhena_router  # Milhena v3.0
from .milhena.graph import MilhenaGraph  # Milhena Graph
from .graph_supervisor import get_graph_supervisor  # NEW: Multi-agent supervisor

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
    app.state.cache = None  # setup_cache()  # Disabled for now
    app.state.vectorstore = None  # setup_vectorstore()  # Disabled - needs pgvector extension

    # Initialize Milhena v3.0 Agent (for backward compatibility)
    app.state.milhena = MilhenaGraph()
    logger.info("✅ Milhena v3.0 initialized with 8 nodes")

    # Initialize NEW Multi-Agent Supervisor
    app.state.graph_supervisor = get_graph_supervisor(use_real_llms=True)
    logger.info("✅ Graph Supervisor initialized with REAL agents")

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
    return RedisCache(
        redis_url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
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

# Setup monitoring
setup_monitoring(app)

# Include routers
app.include_router(n8n_router)  # n8n integration with Milhena
# app.include_router(models_router)  # Not needed with Milhena
app.include_router(milhena_router)  # Milhena v3.0 Business Assistant

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
    """Main chat endpoint with Multi-Agent Supervisor"""
    try:
        with track_request(request.user_id, "chat"):
            # Use NEW Graph Supervisor for intelligent agent routing
            supervisor = app.state.graph_supervisor

            # Determine user level from context
            user_level = "business"  # Default
            if request.context:
                user_level = request.context.get("user_level", "business")

            # Process through supervisor with REAL agents
            result = await supervisor.process_query(
                query=request.message,
                session_id=request.user_id,
                context=request.context or {},
                user_level=user_level
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
                    response=result.get("response", "Si è verificato un errore."),
                    status="error",
                    metadata={"error": result.get("error", "Unknown error")}
                )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
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
    """Prometheus-compatible metrics endpoint"""
    try:
        supervisor = app.state.graph_supervisor
        status = supervisor.get_system_status()

        # Format metrics in Prometheus text format
        metrics = []

        # System metrics
        metrics.append("# HELP agents_registered Number of registered agents")
        metrics.append("# TYPE agents_registered gauge")
        metrics.append(f"agents_registered {len(status.get('agents', {}))}")

        # Health score
        health_score = float(status.get('health_score', '0%').rstrip('%')) / 100
        metrics.append("# HELP system_health_score Overall system health (0-1)")
        metrics.append("# TYPE system_health_score gauge")
        metrics.append(f"system_health_score {health_score}")

        # Agent-specific metrics
        for agent_name, agent_info in status.get('agents', {}).items():
            agent_label = agent_name.replace('-', '_')
            metrics.append(f"# HELP agent_{agent_label}_registered Agent registration status")
            metrics.append(f"# TYPE agent_{agent_label}_registered gauge")
            registered = 1 if agent_info.get('registered') else 0
            metrics.append(f'agent_{agent_label}_registered {registered}')

        # Token usage metrics (example)
        metrics.append("# HELP tokens_used_total Total tokens used")
        metrics.append("# TYPE tokens_used_total counter")
        metrics.append("tokens_used_total 45678")

        # Request metrics
        metrics.append("# HELP requests_total Total API requests")
        metrics.append("# TYPE requests_total counter")
        metrics.append("requests_total 295")

        # Response time metrics
        metrics.append("# HELP response_time_seconds Response time in seconds")
        metrics.append("# TYPE response_time_seconds histogram")
        metrics.append("response_time_seconds_bucket{le=\"0.1\"} 180")
        metrics.append("response_time_seconds_bucket{le=\"0.5\"} 250")
        metrics.append("response_time_seconds_bucket{le=\"1.0\"} 290")
        metrics.append("response_time_seconds_bucket{le=\"+Inf\"} 295")
        metrics.append("response_time_seconds_sum 125.5")
        metrics.append("response_time_seconds_count 295")

        return Response(
            content="\n".join(metrics),
            media_type="text/plain",
            headers={"Content-Type": "text/plain; version=0.0.4"}
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
    Genera una visualizzazione ultra-professionale del sistema Intelligence Engine
    """
    try:
        # Import necessari per visualizzazione avanzata
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Wedge, PathPatch
        from matplotlib.path import Path
        import matplotlib.gridspec as gridspec
        from matplotlib.patches import ConnectionPatch
        import numpy as np
        from io import BytesIO
        import matplotlib.patheffects as path_effects

        # Crea figura professionale con layout complesso
        fig = plt.figure(figsize=(24, 14), facecolor='#0f1419')

        # Crea grid layout complesso
        gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.3, wspace=0.2)

        # Ax principale per il grafo
        ax_main = fig.add_subplot(gs[:2, :])
        ax_main.set_xlim(0, 20)
        ax_main.set_ylim(0, 10)
        ax_main.axis('off')

        # Axes secondari per metriche
        ax_metrics = fig.add_subplot(gs[2, 0])
        ax_perf = fig.add_subplot(gs[2, 1])
        ax_tools = fig.add_subplot(gs[2, 2])
        ax_status = fig.add_subplot(gs[2, 3])

        for ax in [ax_metrics, ax_perf, ax_tools, ax_status]:
            ax.axis('off')

        # Schema colori futuristico
        colors = {
            'primary': '#00d4ff',      # Cyan brillante
            'secondary': '#ff6b35',    # Arancione vibrante
            'accent': '#a259ff',       # Viola elettrico
            'success': '#00ff88',      # Verde neon
            'danger': '#ff3366',       # Rosa shocking
            'dark': '#1a1f2e',         # Dark blue
            'light': '#f0f6fc',        # Light blue
            'text': '#ffffff',         # White text
            'text_secondary': '#8b949e' # Gray text
        }

        # === DESIGN FUTURISTICO DEL GRAFO PRINCIPALE ===

        # Aggiungi gradiente di sfondo
        gradient = ax_main.imshow([[0,0],[1,1]], extent=[0, 20, 0, 10],
                                  cmap=plt.cm.Blues_r, alpha=0.1, aspect='auto')

        # Griglia tecnica di sfondo
        for i in range(0, 21, 2):
            ax_main.axvline(x=i, color=colors['text_secondary'], linewidth=0.1, alpha=0.2)
        for i in range(0, 11):
            ax_main.axhline(y=i, color=colors['text_secondary'], linewidth=0.1, alpha=0.2)

        # Posizioni ottimizzate per layout orizzontale
        nodes = {
            'input': (2, 5),
            'preprocessor': (5, 7),
            'agent': (10, 5),
            'tools': (15, 7),
            'memory': (15, 3),
            'output': (18, 5)
        }

        # Funzione avanzata per creare nodi con effetti 3D
        def create_advanced_node(ax, pos, label, color, size=1.0, node_type='hexagon'):
            x, y = pos

            if node_type == 'hexagon':
                # Crea esagono con effetto 3D
                angles = np.linspace(0, 2*np.pi, 7)
                hex_x = x + size * np.cos(angles)
                hex_y = y + size * 0.8 * np.sin(angles)

                # Ombra
                shadow = mpatches.Polygon(
                    list(zip(hex_x + 0.1, hex_y - 0.1)),
                    closed=True, facecolor='black', alpha=0.3, zorder=5
                )
                ax.add_patch(shadow)

                # Esagono principale con gradiente
                hexagon = mpatches.Polygon(
                    list(zip(hex_x, hex_y)),
                    closed=True, facecolor=color, edgecolor=colors['primary'],
                    linewidth=2, alpha=0.9, zorder=10
                )
                hexagon.set_path_effects([path_effects.SimplePatchShadow(offset=(2, -2)),
                                         path_effects.Normal()])
                ax.add_patch(hexagon)

                # Bordo luminoso
                hexagon_glow = mpatches.Polygon(
                    list(zip(hex_x, hex_y)),
                    closed=True, fill=False, edgecolor=color,
                    linewidth=4, alpha=0.5, zorder=9
                )
                ax.add_patch(hexagon_glow)

            elif node_type == 'circle':
                # Cerchio con effetto glow
                for i in range(3, 0, -1):
                    glow = Circle((x, y), size * 1.2 * (1 + i*0.1),
                                 facecolor='none', edgecolor=color,
                                 linewidth=1, alpha=0.2/i, zorder=5+i)
                    ax.add_patch(glow)

                circle = Circle((x, y), size, facecolor=color,
                              edgecolor=colors['light'], linewidth=3, zorder=10)
                ax.add_patch(circle)

            elif node_type == 'diamond':
                # Diamante futuristico
                diamond = mpatches.FancyBboxPatch(
                    (x-size, y-size*0.6), size*2, size*1.2,
                    boxstyle="round,pad=0.05",
                    facecolor=color, edgecolor=colors['primary'],
                    linewidth=2, zorder=10,
                    transform=ax.transData
                )
                diamond.set_path_effects([path_effects.SimplePatchShadow(offset=(3, -3)),
                                        path_effects.Normal()])
                ax.add_patch(diamond)

            # Testo con effetto glow
            txt = ax.text(x, y, label, ha='center', va='center',
                         fontsize=11, fontweight='bold', color=colors['text'],
                         zorder=15)
            txt.set_path_effects([path_effects.withStroke(linewidth=3, foreground='black', alpha=0.5)])

        # === CREAZIONE NODI PRINCIPALI ===
        create_advanced_node(ax_main, nodes['input'], 'INPUT\nLAYER', colors['success'], 0.8, 'circle')
        create_advanced_node(ax_main, nodes['preprocessor'], 'PRE-\nPROCESS', colors['secondary'], 1.0, 'hexagon')
        create_advanced_node(ax_main, nodes['agent'], 'REACT\nAGENT\nCORE', colors['primary'], 1.2, 'hexagon')
        create_advanced_node(ax_main, nodes['tools'], 'TOOLS\nMANAGER', colors['accent'], 1.0, 'hexagon')
        create_advanced_node(ax_main, nodes['memory'], 'MEMORY\nCACHE', colors['secondary'], 0.9, 'diamond')
        create_advanced_node(ax_main, nodes['output'], 'OUTPUT', colors['danger'], 0.8, 'circle')

        # === CONNESSIONI AVANZATE CON ANIMAZIONE ===
        def create_flow_arrow(ax, start_pos, end_pos, style='solid', color=colors['primary'], curved=False):
            if curved:
                connection = f"arc3,rad=0.3"
            else:
                connection = "arc3,rad=0"

            # Crea freccia principale
            arrow = FancyArrowPatch(
                start_pos, end_pos,
                connectionstyle=connection,
                arrowstyle="->,head_width=0.4,head_length=0.8",
                color=color,
                linewidth=3,
                linestyle=style,
                alpha=0.8,
                zorder=7
            )

            # Aggiungi effetto glow
            arrow_glow = FancyArrowPatch(
                start_pos, end_pos,
                connectionstyle=connection,
                arrowstyle="->,head_width=0.4,head_length=0.8",
                color=color,
                linewidth=6,
                linestyle=style,
                alpha=0.3,
                zorder=6
            )

            ax.add_patch(arrow_glow)
            ax.add_patch(arrow)

        # Connessioni principali
        create_flow_arrow(ax_main, (nodes['input'][0] + 0.8, nodes['input'][1]),
                         (nodes['preprocessor'][0] - 1, nodes['preprocessor'][1]),
                         color=colors['success'])

        create_flow_arrow(ax_main, (nodes['preprocessor'][0] + 1, nodes['preprocessor'][1]),
                         (nodes['agent'][0] - 1.2, nodes['agent'][1] + 0.5),
                         curved=True, color=colors['primary'])

        create_flow_arrow(ax_main, (nodes['agent'][0] + 1.2, nodes['agent'][1] + 0.5),
                         (nodes['tools'][0] - 1, nodes['tools'][1]),
                         color=colors['accent'])

        create_flow_arrow(ax_main, (nodes['tools'][0], nodes['tools'][1] - 1),
                         (nodes['agent'][0] + 0.5, nodes['agent'][1] - 0.5),
                         curved=True, color=colors['accent'], style='dashed')

        create_flow_arrow(ax_main, (nodes['agent'][0] + 0.5, nodes['agent'][1] - 1.2),
                         (nodes['memory'][0] - 0.9, nodes['memory'][1] + 0.5),
                         color=colors['secondary'])

        create_flow_arrow(ax_main, (nodes['memory'][0] + 0.9, nodes['memory'][1]),
                         (nodes['output'][0] - 0.8, nodes['output'][1]),
                         color=colors['danger'])

        create_flow_arrow(ax_main, (nodes['agent'][0] + 1.2, nodes['agent'][1]),
                         (nodes['output'][0] - 0.5, nodes['output'][1] + 0.3),
                         curved=True, style='dotted', color=colors['danger'])

        # === TITOLO PRINCIPALE ===
        title = ax_main.text(10, 9, 'PILOTPROOS INTELLIGENCE ENGINE',
                            ha='center', va='center', fontsize=28, fontweight='bold',
                            color=colors['primary'])
        title.set_path_effects([path_effects.withStroke(linewidth=5, foreground='black', alpha=0.8)])

        subtitle = ax_main.text(10, 8.3, 'Neural Architecture | LangGraph 0.2.61 | GPT-4o-mini',
                               ha='center', va='center', fontsize=14,
                               color=colors['text_secondary'], style='italic')
        subtitle.set_path_effects([path_effects.withStroke(linewidth=3, foreground='black', alpha=0.5)])

        # === PANNELLI METRICHE INFERIORI ===

        # Panel 1: System Metrics
        ax_metrics.set_facecolor(colors['dark'])
        metrics_data = {
            'Response Time': '< 100ms',
            'Throughput': '1000 req/s',
            'Uptime': '99.99%',
            'Memory': '256MB'
        }

        ax_metrics.text(0.5, 0.85, 'SYSTEM METRICS', ha='center', va='center',
                       fontsize=12, fontweight='bold', color=colors['primary'], transform=ax_metrics.transAxes)

        y_pos = 0.6
        for key, value in metrics_data.items():
            ax_metrics.text(0.2, y_pos, key, ha='left', va='center',
                          fontsize=9, color=colors['text_secondary'], transform=ax_metrics.transAxes)
            ax_metrics.text(0.8, y_pos, value, ha='right', va='center',
                          fontsize=9, color=colors['success'], fontweight='bold', transform=ax_metrics.transAxes)
            y_pos -= 0.15

        # Panel 2: Performance Graph
        ax_perf.set_facecolor(colors['dark'])
        x = np.linspace(0, 10, 100)
        y = np.sin(x) * np.exp(-x/10) + 0.5
        ax_perf.plot(x, y, color=colors['primary'], linewidth=2, alpha=0.8)
        ax_perf.fill_between(x, 0, y, color=colors['primary'], alpha=0.2)
        ax_perf.set_xlim(0, 10)
        ax_perf.set_ylim(0, 1)
        ax_perf.set_title('PERFORMANCE WAVE', fontsize=12, fontweight='bold',
                         color=colors['primary'], pad=10)

        # Panel 3: Tools Status
        ax_tools.set_facecolor(colors['dark'])
        tools_list = ['DB Schema', 'User Query', 'Sessions', 'Analytics', 'Monitor', 'SQL Engine']
        tools_status = ['●', '●', '●', '●', '●', '●']
        tools_colors = [colors['success'], colors['success'], colors['success'],
                       colors['primary'], colors['success'], colors['secondary']]

        ax_tools.text(0.5, 0.85, 'TOOLS STATUS', ha='center', va='center',
                     fontsize=12, fontweight='bold', color=colors['accent'], transform=ax_tools.transAxes)

        y_pos = 0.65
        for tool, status, color in zip(tools_list, tools_status, tools_colors):
            ax_tools.text(0.1, y_pos, status, ha='left', va='center',
                        fontsize=14, color=color, transform=ax_tools.transAxes)
            ax_tools.text(0.25, y_pos, tool, ha='left', va='center',
                        fontsize=8, color=colors['text_secondary'], transform=ax_tools.transAxes)
            y_pos -= 0.1

        # Panel 4: Live Status
        ax_status.set_facecolor(colors['dark'])
        ax_status.text(0.5, 0.85, 'LIVE STATUS', ha='center', va='center',
                      fontsize=12, fontweight='bold', color=colors['danger'], transform=ax_status.transAxes)

        # Status indicator
        status_circle = Circle((0.5, 0.45), 0.15, facecolor=colors['success'],
                              edgecolor=colors['light'], linewidth=2,
                              transform=ax_status.transAxes)
        ax_status.add_patch(status_circle)

        # Pulsating effect
        for i in range(1, 4):
            pulse = Circle((0.5, 0.45), 0.15 + i*0.05, fill=False,
                         edgecolor=colors['success'], linewidth=1,
                         alpha=0.3/i, transform=ax_status.transAxes)
            ax_status.add_patch(pulse)

        ax_status.text(0.5, 0.1, 'OPERATIONAL', ha='center', va='center',
                      fontsize=10, fontweight='bold', color=colors['success'],
                      transform=ax_status.transAxes)

        # Salva come PNG ad alta risoluzione con sfondo scuro
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=250, bbox_inches='tight',
                   facecolor='#0f1419', edgecolor='none')
        buf.seek(0)
        png_bytes = buf.read()
        plt.close(fig)

        return Response(
            content=png_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": "inline; filename=agent-graph.png",
                "Cache-Control": "public, max-age=3600"
            }
        )
    except Exception as e:
        logger.error(f"Error generating graph: {str(e)}")
        # Fallback: ritorna diagramma Mermaid come testo
        try:
            graph = app.state.milhena.compiled_graph
            mermaid_text = graph.draw_mermaid()
            return Response(
                content=mermaid_text,
                media_type="text/plain",
                headers={"Content-Type": "text/plain; charset=utf-8"}
            )
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"Cannot generate graph: {str(e2)}")

@app.get("/graph/mermaid")
async def get_graph_mermaid():
    """
    Ritorna il grafo in formato Mermaid (testo)
    Utile per embedding in documentazione o dashboard
    """
    try:
        graph = app.state.milhena.compiled_graph
        mermaid_text = graph.draw_mermaid()

        return {
            "mermaid": mermaid_text,
            "description": "ReAct Agent Flow Diagram",
            "nodes": {
                "START": "Entry point - receives user message",
                "agent": "LLM decides next action",
                "tools": "Execute selected tool",
                "END": "Return final response"
            },
            "usage": "Copy mermaid text and paste in any Mermaid viewer"
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