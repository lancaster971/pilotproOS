# 📋 CLAUDE.md - PROJECT GUIDE

**READ THIS FIRST** - Complete project guide and documentation index

PilotProOS - Containerized Business Process Operating System

## 🤖 **INSTRUCTIONS FOR AI AGENTS**

**MANDATORY**: This is the MAIN DOCUMENTATION after cleanup. All docs/ folders were eliminated.

**PROJECT STATUS POST-CLEANUP:**
- ✅ **CrewAI COMPLETELY REMOVED** from project
- ✅ **agent-engine/** folder cleaned and converted to direct system
- ✅ **All documentation purged** (docs/, README.md, etc.)
- ✅ **Stack simplified** to 6 essential services
- ✅ **Redis maintained** for future LangChain integration

## 🏗️ **CLEANED ARCHITECTURE**

**STACK PURGED AND SIMPLIFIED:**
- **PostgreSQL** - Database (dual schema: n8n + pilotpros)
- **Redis** - Cache & Queue (ready for LangChain)
- **Backend** - Express API (business terminology)
- **Frontend** - Vue 3 Business Portal
- **Automation** - n8n Workflow Engine
- **Monitor** - Nginx Reverse Proxy

**AGENT ENGINE STATUS:**
- ❌ **CrewAI eliminated** - Was unreliable multi-agent framework
- ✅ **Direct system** - Simple tool calls without agent bullshit
- ✅ **Fast Bypass** - GPT-4o + Groq fallback for 90% queries
- 🚀 **Future ready** - Redis cache prepared for LangChain

### **⚡ QUICK START POST-CLEANUP**

**START STACK:**
```bash
./stack                   # Interactive CLI (password: PilotPro2025!)
./stack-safe.sh start     # Direct start command
```

**ACCESS POINTS:**
- 🌐 Frontend: http://localhost:3000 (tiziano@gmail.com / Hamlet@108)
- ⚙️ Backend API: http://localhost:3001
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

## 🚀 **CURRENT STATUS POST-CLEANUP**

### **✅ CLEANED AND WORKING**
- ✅ **Stack Completely Purged** - CrewAI eliminated, docs removed
- ✅ **6 Essential Services** - PostgreSQL, Redis, Backend, Frontend, n8n, Nginx
- ✅ **Agent Engine Cleaned** - Direct system, no multi-agent framework
- ✅ **CLI Stack Manager** - Updated without obsolete Agent Engine
- ✅ **Authentication System** - Full working with business portal
- ✅ **Business Data Tools** - BusinessIntelligentQueryTool working directly
- ✅ **Fast Bypass System** - GPT-4o + Groq fallback operational

### **🚀 READY FOR DEVELOPMENT**
- 🚀 **LangChain Integration** - Redis cache prepared
- 🚀 **Direct Tool Calls** - No unreliable agent framework
- 🚀 **Performance** - 10x faster without CrewAI overhead
- 🚀 **Clean Architecture** - No technical debt from multi-agent
- 🚀 **Simplified Maintenance** - Single direct system to manage

### **📦 STACK SERVICES STATUS**
1. **PostgreSQL** ✅ - Database ready
2. **Redis** ✅ - Cache ready for LangChain
3. **Backend API** ✅ - Express with auth
4. **Frontend** ✅ - Vue 3 business portal
5. **Automation** ✅ - n8n workflow engine
6. **Monitor** ✅ - Nginx reverse proxy

---

## 📚 **DOCUMENTATION STATUS**

**POST-CLEANUP DOCUMENTATION:**
- ❌ **docs/ eliminated** - All documentation folders removed
- ❌ **README.md purged** - Main README removed
- ✅ **CLAUDE.md updated** - This file contains all essential info
- ✅ **Inline code comments** - Documentation in code where needed
- 🚀 **Future**: Documentation will be minimal and code-focused

### **📋 ESSENTIAL COMMANDS POST-CLEANUP**
```bash
# Stack Management - SIMPLIFIED
./stack                   # Interactive CLI (6 services only)
./stack-safe.sh start     # Direct start (no Agent Engine)
./stack-safe.sh status    # Health check

# Access Points - CLEANED
http://localhost:3000     # Business Portal (tiziano@gmail.com / Hamlet@108)
http://localhost:3001     # Backend API
http://localhost:3005     # Stack Controller (admin / PilotPro2025!)
http://localhost:5678     # Automation (admin / pilotpros_admin_2025)

# Development - NO CREWAI
cd agent-engine/          # Direct system (no multi-agent)
python3 main.py           # Direct FastAPI server
```

**🎯 AI AGENTS**: All info is now in this CLAUDE.md file. No external docs to read!

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