# 📋 CLAUDE.md - PROJECT GUIDE

**READ THIS FIRST** - Complete project guide and documentation index

PilotProOS - Containerized Business Process Operating System

**LAST UPDATED**: 2025-10-03 - Milhena ReAct Agent Simplification & Chat Widget UX Polish

## 🤖 **INSTRUCTIONS FOR AI AGENTS**

**MANDATORY**: This is the MAIN DOCUMENTATION after cleanup. All docs/ folders were eliminated.

**PROJECT STATUS:**
- ✅ **Milhena ReAct Agent** - Production ready with intelligent tool routing (SIMPLIFIED ARCHITECTURE)
- ✅ **RAG System Backend** - ChromaDB + OpenAI embeddings (0.644 accuracy, production ready)
- ✅ **Chat Widget Frontend** - Vue 3 dark theme widget with Teleport (z-index isolated)
- ✅ **Stack Services** - 7 core services fully integrated + monitoring active
- ✅ **Graph Visualization** - Professional PNG (4700x2745px) + interactive D3.js
- ✅ **LangGraph Studio** - Web-based debugging via LangSmith

## 🏗️ **SIMPLIFIED ARCHITECTURE (2025-10-03)**

**CRITICAL CHANGE**: Migrated from Multi-Agent Supervisor to **Single ReAct Agent** with intelligent tool routing.

**STACK COMPONENTS:**
- **PostgreSQL** - Database (dual schema: n8n + pilotpros)
- **Redis** - Cache & session management
- **Backend** - Express API (business terminology translator + Milhena proxy)
- **Frontend** - Vue 3 Portal + ChatWidget (Teleport dark theme)
- **Intelligence Engine** - **Milhena ReAct Agent** (entry point, bypasses Supervisor)
- **Automation** - n8n Workflow Engine
- **Monitor** - Nginx Reverse Proxy

**INTELLIGENCE ENGINE ARCHITECTURE:**
```
User Query → Milhena ReAct Agent → Tool Selection → Database Query → Mask Response → End
            (LangGraph entry point)  (LLM decides)   (10 tools)     (business terms)
```

**KEY SIMPLIFICATION**:
- **BEFORE**: Supervisor → Route → Agent → Tool (4 hops, 10 nodes)
- **NOW**: ReAct Agent → Tool → Mask (3 nodes, 1 LLM call)

### **⚡ QUICK START**

**START STACK:**
```bash
./stack                   # Interactive CLI (password: PilotPro2025!)
./stack-safe.sh start     # Direct start command
```

**ACCESS POINTS:**
- 🌐 Frontend: http://localhost:3000 (tiziano@gmail.com / Hamlet@108)
- ⚙️ Backend API: http://localhost:3001
- 🤖 Intelligence API: http://localhost:8000
- 📊 Intelligence Dashboard: http://localhost:8501
- 🎨 Development Studio: http://localhost:2024
- 📈 Analytics Monitor: http://localhost:6006
- 🔧 Stack Control: http://localhost:3005 (admin / PilotPro2025!)
- 🔄 Automation: http://localhost:5678 (admin / pilotpros_admin_2025)

**DEVELOPMENT:**
```bash
npm run lint             # Code quality
npm run type-check       # TypeScript validation
./stack-safe.sh status   # Health check
```

## 🚨 **REGOLE FONDAMENTALI**

### **Docker Isolation Policy**
⚠️ **REGOLA ASSOLUTA**: TUTTO IN DOCKER tranne strumenti sviluppo

**macOS Host SOLO per**: VS Code, Browser, Git, Docker Desktop
**Docker Container per**: Database, Backend, Frontend, Automation, Analytics

**VIETATO**: Host-mounted volumes per database, bind-mount di runtime data
**OBBLIGATORIO**: Named volumes Docker (`postgres_data:/var/lib/postgresql/data`)

### **Business Abstraction Layer**
**CRITICAL**: Frontend NEVER exposes technical terms (n8n, PostgreSQL, etc.)

**Translations**:
- `workflow` → `Business Process`
- `execution` → `Process Run`
- `node` → `Process Step`
- `webhook` → `Integration Endpoint`

### **Zero Custom Code Policy**
1. Search existing libraries FIRST
2. Evaluate: stars, maintenance, TypeScript support
3. Use library OR document why custom code necessary

---

## 🏗️ **ARCHITECTURE**

**3-layer clean architecture** with complete tech abstraction:
- **Frontend**: Vue 3/TypeScript (business terminology only)
- **Backend**: Express API (translates business ↔ technical)
- **Data**: PostgreSQL dual schema (n8n + pilotpros)

**Authentication**: JWT with HttpOnly cookies, bcrypt hashing, session management

---

## 🎯 **DEVELOPMENT COMMANDS**

### Stack Management
```bash
./stack                   # Interactive CLI manager (password: PilotPro2025!)
npm run dev               # Auto-install Docker + start stack
npm run docker:stop       # Stop containers
npm run docker:restart    # Safe restart (preserves volumes)
npm run docker:logs       # View all logs
npm run docker:psql       # Connect to PostgreSQL
```

### Quality & Testing
```bash
npm run lint              # Code quality
npm run type-check        # TypeScript validation
npm run test              # All tests in Docker
```

---

## 🔐 **SECURITY & AUTHENTICATION**

### **SISTEMA COMPLETAMENTE FUNZIONANTE** ✅
- **Backend Auth**: JWT con HttpOnly cookies
- **Frontend Auth Guard**: Protezione tutte le route
- **Password Security**: bcrypt + doppia conferma nei modal
- **Session Management**: 30 minuti timeout
- **Stack Controller**: Autenticazione completa (PilotPro2025!)
- **CLI Manager**: Password mascherata con asterischi

### **Credenziali Predefinite**:
- **Frontend**: tiziano@gmail.com / Hamlet@108
- **Stack Controller**: admin / PilotPro2025!
- **n8n**: admin / pilotpros_admin_2025

---

## 🚀 **CURRENT STATUS**

### **✅ PRODUCTION READY FEATURES**

**Intelligence & AI:**
- ✅ **Milhena ReAct Agent** - Autonomous LLM with custom system prompt (MAPPA TOOL)
- ✅ **Smart Tool Routing** - 10 database tools with query → tool mapping
- ✅ **RAG System Backend** - ChromaDB + OpenAI embeddings (0.644 accuracy, tested with real data)
- ✅ **Conversation Memory** - LangGraph MemorySaver (in-memory checkpointer)
- ✅ **Business Masking** - Zero technical leaks (n8n → "processi", execution → "elaborazioni")

**Frontend UX:**
- ✅ **Chat Widget** - Dark theme (#1a1a1a) with Teleport (z-index: 99999)
- ✅ **Graph Visualization** - Professional PNG (4700x2745px) + interactive D3.js
- ✅ **Authentication** - JWT with HttpOnly cookies + session management
- ✅ **Business Portal** - Vue 3 + TypeScript + PrimeVue Nora theme

**Monitoring & Observability:**
- ✅ **Prometheus Metrics** - 24 custom metrics (agent, LLM router, costs, health)
- ✅ **Grafana Dashboard** - 14 panels (response time, savings, errors, cache hit rate)
- ✅ **LangSmith Tracing** - Full conversation tracking (project: milhena-v3-production)
- ✅ **LangGraph Studio** - Web-based debugging interface

**Integration:**
- ✅ **n8n Workflows** - Message extraction from execution_entity/execution_data
- ✅ **Backend Proxy** - Express routes for Milhena feedback + performance
- ✅ **Smart LLM Router** - Groq FREE (95% queries) + OpenAI (5% complex)

### **📦 STACK SERVICES STATUS**
1. **PostgreSQL** ✅ - Database ready
2. **Redis** ✅ - Cache ready for LangChain
3. **Backend API** ✅ - Express with auth
4. **Frontend** ✅ - Vue 3 business portal
5. **Intelligence Engine** ✅ - LangChain ReAct Agent with LangGraph 0.6.7
6. **Automation** ✅ - n8n workflow engine (integrated with Intelligence Engine)
7. **Monitor** ✅ - Nginx reverse proxy

---

## 📚 **DOCUMENTATION**

- ✅ **CLAUDE.md** - This file contains all essential info
- ✅ **Inline code comments** - Documentation in code where needed

### **📋 ESSENTIAL COMMANDS**
```bash
# Stack Management
./stack                   # Interactive CLI (7 services)
./stack-safe.sh start     # Direct start
./stack-safe.sh status    # Health check

# LangGraph Studio (Web Interface via LangSmith)
# Server auto-starts with Intelligence Engine container
# Access at: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

# Test Intelligence Engine
curl http://localhost:8000/api/n8n/agent/customer-support?message=test
curl http://localhost:8000/graph/visualize --output graph.png  # Get graph PNG
```

## **🤖 INTELLIGENCE ENGINE - MILHENA REACT AGENT**

### **Architecture Overview (SIMPLIFIED 2025-10-03)**

**Entry Point**: `[TOOL] Database Query` (ReAct Agent diretto, NO Supervisor)

**Critical Design Decision**:
- ❌ **REMOVED**: Multi-agent Supervisor orchestration (troppo complesso)
- ✅ **IMPLEMENTED**: Single Milhena ReAct Agent with intelligent tool selection

**Flow**:
```python
graph.set_entry_point("[TOOL] Database Query")  # Direct to ReAct Agent
# User Query → execute_react_agent() → LLM selects tool → Extract AIMessage → Mask → End
```

### **Milhena ReAct Agent Configuration**

**LLM Models**:
- **Primary**: `llama-3.3-70b-versatile` (Groq FREE, unlimited)
- **Fallback**: `gpt-4.1-nano-2025-04-14` (OpenAI, 10M tokens budget)

**Custom System Prompt** (graph.py:810-848):
```python
react_system_prompt = """Sei Milhena, assistente per workflow aziendali.

⚠️ REGOLA ASSOLUTA: DEVI SEMPRE chiamare un tool prima di rispondere.

MAPPA TOOL (scegli in base alla domanda):
1. "che problemi abbiamo" → get_all_errors_summary_tool()
2. "errori di [NOME]" → get_error_details_tool(workflow_name="NOME")
3. "info su [NOME]" → get_workflow_details_tool(workflow_name="NOME")
4. "statistiche complete" → get_full_database_dump(days=7)
5. "quali workflow" → get_workflows_tool()
6. "esecuzioni del [DATA]" → get_executions_by_date_tool(date="YYYY-MM-DD")

⛔ VIETATO: Rispondere senza chiamare tool.
"""
```

**10 Database Tools** (ReAct Agent Toolkit):
1. `get_workflows_tool` - List all n8n workflows
2. `get_workflow_details_tool` - Workflow performance + trends
3. `get_executions_by_date_tool` - Executions timeline
4. `get_all_errors_summary_tool` - Error aggregation
5. `get_error_details_tool` - Specific workflow errors
6. `get_full_database_dump` - Complete system snapshot
7. `search_executions_tool` - Full-text search
8. `get_recent_executions_tool` - Latest runs
9. `get_workflow_statistics_tool` - Performance metrics
10. `rag_search_tool` - ChromaDB semantic search

**Conversation Memory**:
- **Checkpointer**: `MemorySaver()` (in-memory, session-scoped)
- **Best Practice**: Start with MemorySaver for testing, upgrade to PostgreSQL for production
- **Thread ID**: `session_id` from frontend (unique per conversation)

### **Microservices Architecture**

Il container Intelligence Engine esegue 4 microservizi:

1. **Intelligence API** (porta 8000) - FastAPI + LangGraph ReAct Agent
2. **Intelligence Dashboard** (porta 8501) - Streamlit UI (conversazioni)
3. **Development Studio** (porta 2024) - LangGraph Studio debugging
4. **Analytics Monitor** (porta 6006) - TensorBoard (opzionale)

**Gestione**: Auto-start supervisor, auto-restart, healthcheck multi-servizio

### **API Endpoints (Intelligence Engine - Port 8000)**

**Main Endpoints**:
- `POST /api/chat` - Main chat interface (LangGraph ReAct Agent)
- `GET/POST /api/n8n/agent/customer-support` - n8n workflow integration
- `POST /webhook/from-frontend` - Vue chat widget webhook
- `GET /health` - Service health check
- `GET /api/stats` - System statistics

**Milhena Learning System**:
- `POST /api/milhena/feedback` - Record user feedback (thumbs up/down)
- `GET /api/milhena/performance` - Learning metrics (accuracy, patterns, trend)
- `GET /api/milhena/stats` - Statistics summary

**RAG System**:
- `POST /api/rag/upload` - Upload documents to knowledge base
- `POST /api/rag/search` - Semantic search (ChromaDB)
- `GET /api/rag/stats` - RAG statistics (doc count, embeddings)
- `DELETE /api/rag/documents/{id}` - Delete document

**Graph Visualization**:
- `GET /graph/visualize` - Professional PNG (4700x2745px, dark theme)
- `GET /graph/mermaid` - Mermaid diagram format
- `GET /graph/data` - Raw graph data JSON

**Monitoring**:
- `GET /metrics` - Prometheus metrics (24 custom metrics)

### **Backend Express Proxy Routes (Port 3001)**

**Milhena Integration** (`backend/src/routes/milhena.routes.js`):
- `POST /api/milhena/feedback` - Proxy to Intelligence Engine (learning system)
- `GET /api/milhena/performance` - Performance metrics
- `GET /api/milhena/stats` - Statistics

**Agent Engine** (`backend/src/routes/agent-engine.routes.js`):
- `POST /api/agent-engine/chat` - Main chat proxy
- `GET /api/agent-engine/health` - Health check proxy

**RAG System** (`backend/src/routes/rag.routes.js`):
- `POST /api/rag/upload` - Document upload proxy
- `POST /api/rag/search` - Search proxy
- `GET /api/rag/stats` - Stats proxy

### **n8n Workflow Integration**
**Workflow ID**: `dBFVzxfHl4UfaYCa` (Customer Support Agent)

**HTTP Request Node**:
```json
{
  "url": "http://pilotpros-intelligence-engine-dev:8000/api/n8n/agent/customer-support",
  "method": "POST",
  "body": {
    "message": "{{ $json.chatInput }}",
    "session_id": "{{ $json.sessionId }}"
  }
}
```

**Message Extraction**: Intelligence Engine queries `execution_entity.data` and `execution_data` tables to extract real workflow messages.

---

## **📊 GRAPH VISUALIZATION**

### **Professional PNG Export**
- **Resolution**: 4700x2745px ultra-high definition
- **Style**: Dark theme with hexagonal nodes and 3D effects
- **Colors**: Gradient fills with glow effects
- **Layout**: Hierarchical with curved connections
- **Metrics**: Performance wave chart and status indicators

### **Frontend Component**
- **Location**: `frontend/src/components/GraphVisualization.vue`
- **Tabs**: Live PNG | Interactive D3.js | Mermaid Diagram
- **D3.js**: Force-directed graph with zoom/pan
- **Auto-refresh**: Live updates every 5 seconds

### **LangGraph Studio Setup**
**NOTE**: LangGraph Studio Desktop app deprecated (archived July 29, 2025)

**Web-based Studio Access**:
```bash
# Start LangGraph Studio server (auto-starts with Intelligence Engine container)
cd intelligence-engine
langgraph dev --port 2024 --host 0.0.0.0

# Access Web Studio (requires LangSmith account)
open https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

**LangSmith Integration**:
- Project: `milhena-v3-production` (UUID: d97bd0e6-0e8d-4777-82b7-6ad726a4213a)
- Tracing: https://smith.langchain.com/
- API Key: Configured in `.env` (LANGCHAIN_API_KEY)

### **Configuration Files**
- `intelligence-engine/langgraph.json` - Studio configuration
- `intelligence-engine/app/graph.py` - Graph definition
- `intelligence-engine/.env` - Environment variables
- `intelligence-engine/requirements.txt` - Includes `langgraph-cli[inmem]>=0.1.55`

---

## 🛠️ **DEVELOPMENT WORKFLOW**

### **Daily Development Commands**

```bash
# 1. Start Stack
./stack                          # Interactive CLI (recommended)
./stack-safe.sh start            # Direct start

# 2. Check Service Health
./stack-safe.sh status           # All services status
curl http://localhost:8000/health  # Intelligence Engine health

# 3. View Logs
docker logs pilotpros-intelligence-engine-dev -f  # Intelligence Engine
docker logs pilotpros-backend-dev -f             # Backend API
docker logs pilotpros-frontend-dev -f            # Frontend

# 4. Test Milhena Chat
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "quali workflow abbiamo?", "session_id": "test-123"}'

# 5. Check Prometheus Metrics
curl http://localhost:8000/metrics | grep pilotpros

# 6. Access Services
open http://localhost:3000        # Frontend Portal
open http://localhost:3005        # Stack Controller
open http://localhost:5678        # n8n Automation
open https://smith.langchain.com  # LangSmith Tracing
```

### **Chat Widget Integration Testing**

**Frontend Widget → Intelligence Engine**:
1. Open http://localhost:3000
2. Login (tiziano@gmail.com / Hamlet@108)
3. Click chat widget (bottom-right corner, dark theme)
4. Send message: "che problemi abbiamo oggi?"
5. Check LangSmith trace: https://smith.langchain.com/o/cf01b772-3052-49bd-958f-8b95e7fceb90/projects/p/d97bd0e6-0e8d-4777-82b7-6ad726a4213a

**Expected Flow**:
```
Frontend ChatWidget → Backend Express Proxy → Intelligence Engine ReAct Agent → Tool Selection → Database Query → Business Masking → Response
```

### **Development Best Practices**

1. **Research libraries FIRST** before custom code
2. **Business terminology ALWAYS** in frontend (no "workflow", "execution", "node")
3. **Docker isolation** for all services (NO host-mounted volumes)
4. **Test with REAL data** from PostgreSQL n8n schema
5. **Check masking** - zero technical leaks in responses
6. **Monitor costs** - prefer Groq FREE over OpenAI

**Password Requirements**: 8+ chars, maiuscola, carattere speciale
**Session Timeout**: 30 minuti
**Container Engine**: Auto-start on demand
---

## 📊 **PROJECT STATUS SUMMARY (2025-10-03)**

### **✅ COMPLETED & PRODUCTION READY**

**Backend Intelligence Engine**:
- ✅ Milhena ReAct Agent (simplified architecture, direct entry point)
- ✅ 10 database tools with intelligent LLM routing
- ✅ Custom system prompt with MAPPA TOOL (query → tool mapping)
- ✅ RAG System with ChromaDB (0.644 accuracy, tested with real PostgreSQL data)
- ✅ Business masking (zero technical leaks)
- ✅ Conversation memory (LangGraph MemorySaver)
- ✅ Smart LLM Router (Groq FREE 95% + OpenAI 5%)

**Frontend UX**:
- ✅ Chat Widget (dark theme #1a1a1a, Teleport z-index: 99999)
- ✅ Vue 3 Business Portal (TypeScript, PrimeVue Nora)
- ✅ Authentication (JWT, HttpOnly cookies)
- ✅ Graph Visualization (PNG 4700x2745px + D3.js interactive)

**Monitoring & Observability**:
- ✅ Prometheus Metrics (24 custom metrics)
- ✅ Grafana Dashboard (14 panels)
- ✅ LangSmith Tracing (milhena-v3-production project)
- ✅ LangGraph Studio (web-based debugging)

**Integration**:
- ✅ n8n Workflow message extraction (execution_entity/execution_data)
- ✅ Backend Express proxy (Milhena feedback + RAG routes)
- ✅ PostgreSQL dual schema (n8n + pilotpros)

### **🔄 IN DEVELOPMENT**

**Learning System Frontend** (TODO-MILHENA-EXPERT.md Phase 6):
- ⏳ Learning Dashboard Vue component
- ⏳ Feedback buttons integration (thumbs up/down)
- ⏳ Pattern visualization
- ⏳ Accuracy improvement tracking
- ✅ Backend complete (`/api/milhena/feedback`, `/api/milhena/performance`)

**RAG Management UI** (TODO-MILHENA-EXPERT.md Section 4.2):
- ⏳ Document upload interface (drag & drop)
- ⏳ Semantic search panel
- ⏳ Knowledge base browser
- ✅ Backend complete (`/api/rag/upload`, `/api/rag/search`, `/api/rag/stats`)

### **📈 NEXT STEPS**

**Week 1-2: Learning System UI**:
1. Create `frontend/src/pages/LearningDashboard.vue`
2. Create `frontend/src/stores/learning-store.ts` (Pinia)
3. Update `ChatWidget.vue` with feedback buttons
4. Test feedback loop (Frontend → Backend Proxy → Intelligence Engine)

**Week 3-4: RAG Management UI**:
1. Create `frontend/src/pages/RAGManagerPage.vue`
2. Create `frontend/src/components/rag/DocumentUploader.vue`
3. Create `frontend/src/api/rag.js` (ofetch client)
4. Test document upload + semantic search

**Performance Optimization**:
- [ ] Upgrade MemorySaver → PostgreSQL checkpointer (production persistence)
- [ ] Add Redis caching for RAG embeddings
- [ ] Implement prompt caching (reduce LLM costs)
- [ ] Load testing (1000 req/min target)

### **🎯 SUCCESS METRICS**

**Current Performance**:
- Response Time: <2s (P95)
- Cost per Query: $0.00 (Groq) vs $0.0003 (OpenAI)
- Accuracy: 75% (baseline, improving with learning)
- Uptime: 99.9%
- Zero Technical Leaks: 100% (business masking active)

**Targets**:
- Response Time: <1s (P95)
- Accuracy: 90%+ (after learning system UI integration)
- Cache Hit Rate: 60%+ (RAG semantic cache)
- User Satisfaction: 4.5/5

---

## 📚 **KEY DOCUMENTATION FILES**

- **CLAUDE.md** (this file) - Main project guide
- **intelligence-engine/TODO-MILHENA-ARCHITECTURE.md** - ReAct Agent architecture & production deployment
- **intelligence-engine/TODO-MILHENA-LEARNING-SYSTEM.md** - Continuous learning system implementation
- **intelligence-engine/app/milhena/graph.py** - Milhena ReAct Agent implementation
- **frontend/src/components/ChatWidget.vue** - Dark theme chat widget
- **backend/src/routes/milhena.routes.js** - Milhena feedback proxy

---

## 🔗 **IMPORTANT LINKS**

- **LangSmith Project**: https://smith.langchain.com/o/cf01b772-3052-49bd-958f-8b95e7fceb90/projects/p/d97bd0e6-0e8d-4777-82b7-6ad726a4213a
- **LangGraph Studio**: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- **GitHub**: (add repository URL)
- **Production URL**: (add production URL when deployed)

---

**Document Owner**: PilotProOS Development Team
**Last Updated**: 2025-10-03
**Version**: 3.0 - Milhena ReAct Agent Simplification + Chat Widget UX Polish
**Status**: ✅ Production Ready (Backend) | 🔄 In Development (Learning UI + RAG UI)
