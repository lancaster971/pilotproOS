# 📋 CLAUDE.md - PROJECT GUIDE

**READ THIS FIRST** - Complete project guide and documentation index

PilotProOS - Containerized Business Process Operating System

## 🤖 **INSTRUCTIONS FOR AI AGENTS**

**MANDATORY**: This is the MAIN DOCUMENTATION after cleanup. All docs/ folders were eliminated.

**PROJECT STATUS:**
- ✅ **LangGraph Intelligence Engine** - Universal platform for system & customer agents
- 🟡 **Milhena System Agent** - In planning (see TODO-MILHENA.md)
- ✅ **Stack Services** - 7 core services fully integrated
- ✅ **Graph Visualization** - Professional PNG & interactive D3.js views
- ✅ **LangGraph Studio** - Desktop debugging interface ready

## 🏗️ **CLEANED ARCHITECTURE**

**ARCHITECTURE:**
- **PostgreSQL** - Database (dual schema: n8n + pilotpros)
- **Redis** - Cache & Queue for session management
- **Backend** - Express API (business terminology)
- **Frontend** - Vue 3 Business Portal with graph visualization
- **Intelligence Engine** - LangGraph ReAct Agent
- **Automation** - n8n Workflow Engine
- **Monitor** - Nginx Reverse Proxy

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

### **✅ WORKING FEATURES**
- ✅ **LangGraph ReAct Agent** - GPT-4o-mini with tool execution
- ✅ **RAG System** - ChromaDB with OpenAI embeddings (production ready)
- ✅ **Graph Visualization** - Professional PNG (4700x2745px) with 3D effects
- ✅ **Interactive D3.js** - Force-directed graph in frontend
- ✅ **LangGraph Studio** - Web-based debugging interface via LangSmith
- ✅ **Authentication System** - JWT with HttpOnly cookies
- ✅ **n8n Integration** - Full workflow automation support

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

## **🤖 INTELLIGENCE ENGINE**

### **Microservices Architecture**
Il container Intelligence Engine esegue 4 microservizi gestiti automaticamente:

1. **Intelligence API** (porta 8000)
   - FastAPI server principale
   - LangGraph ReAct Agent
   - Endpoints REST

2. **Intelligence Dashboard** (porta 8501)
   - Streamlit UI interattiva
   - Visualizzazione conversazioni
   - Monitoring in tempo reale

3. **Development Studio** (porta 2024)
   - LangGraph Studio UI
   - Debugging grafi
   - Test agent interattivi

4. **Analytics Monitor** (porta 6006)
   - TensorBoard (opzionale)
   - Metriche performance

**Gestione Microservizi:**
- Auto-start con supervisor script
- Auto-restart in caso di crash
- Healthcheck completo multi-servizio
- CLI Stack opzione 'i':
  - Status dettagliato tutti i microservizi
  - Restart selettivo (opzione 'r')
  - Start supervisor (opzione 's')
  - Controllo completo senza riavvio container

### **LangGraph ReAct Agent**
- **Framework**: LangGraph 0.6.7 with ReAct pattern
- **Model**: GPT-4o-mini (fast) with GPT-4o fallback
- **Tools**: 6 database query tools
- **Memory**: Session-based conversation history
- **Integration**: Full n8n workflow support

### **API Endpoints**
- `POST /api/chat` - Main chat interface
- `GET/POST /api/n8n/agent/customer-support` - n8n integration
- `POST /webhook/from-frontend` - Vue widget webhook
- `GET /health` - Service health check
- `GET /api/stats` - System statistics
- `GET /graph/visualize` - Professional PNG graph (4700x2745px)
- `GET /graph/mermaid` - Mermaid diagram format
- `GET /graph/data` - Raw graph data JSON

### **n8n Workflow Integration**
**Workflow ID**: `dBFVzxfHl4UfaYCa`
**HTTP Request Node Configuration**:
- URL: `http://pilotpros-intelligence-engine-dev:8000/api/n8n/agent/customer-support`
- Method: POST
- Body: `{"message": "{{ $json.chatInput }}", "session_id": "{{ $json.sessionId }}"}`

### **Database Tools**
1. `get_database_schema_tool` - Get table schemas
2. `query_users_tool` - Query user data
3. `query_sessions_tool` - Active sessions info
4. `query_business_data_tool` - Business metrics
5. `query_system_status_tool` - System health
6. `execute_sql_query_tool` - Custom SQL (SELECT only)

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

1. **Research libraries** → Business terminology → Docker testing
2. **Use CLI manager** `./stack` per gestione container
3. **Business Portal** http://localhost:3000 (auto-start via CLI option 7)
4. **Stack Controller** http://localhost:3005
5. **n8n Admin** http://localhost:5678

**Password Requirements**: 8+ chars, maiuscola, carattere speciale
**Session Timeout**: 30 minuti
**Container Engine**: Auto-start on demand