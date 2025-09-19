# 📋 CLAUDE.md - PROJECT GUIDE

**READ THIS FIRST** - Complete project guide and documentation index

PilotProOS - Containerized Business Process Operating System

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
- **Frontend**: tiziano@gmail.com / testtest123
- **Stack Controller**: admin / PilotPro2025!
- **n8n**: admin / pilotpros_admin_2025

---

## 🚀 **CURRENT STATUS**

### **Development Ready Features** ✅ (LOCAL ONLY)
- ✅ **Authentication System**: Completo e funzionante
- ✅ **PostgreSQL**: Dual schema con workflows
- ✅ **Vue 3 + VueFlow**: Enterprise visualization
- ✅ **n8n Integration**: Automation engine
- ✅ **Business Data Extraction**: Tutti i workflow types
- ✅ **Docker Development**: Hot-reload
- ✅ **CLI Stack Manager**: Auto-start Container Engine
- ✅ **Password Security**: Double confirmation
- ✅ **Timeline Analysis**: Pattern-based

### **Production Deployment** 🔴 **DA IMPLEMENTARE**
- 🔴 **VPS Configurations**: docker-compose.vps.yml missing
- 🔴 **Environment Detection**: Auto-tier selection missing
- 🔴 **SSL Automation**: Let's Encrypt integration missing
- 🔴 **VPS Templates**: Golden image creation needed
- 🔴 **Enterprise Scripts**: Multi-environment deployment missing

### **CLI Stack Manager Features** 🎯
- Password authentication con asterischi mascherati
- Auto-start Container Engine quando Docker è down
- Business Portal integration (option 7)
- Smart stack startup quando opening Portal
- Session management 30-minute timeout
- Fix double input bug macOS
- Business terminology only (no technical terms)

---

## 📚 **DOCUMENTATION**

### Structure (Reorganized 2025-09-19)
```
docs/
├── IMPLEMENTED/     # What works NOW
│   └── CURRENT_ARCHITECTURE.md
├── TODO/           # What needs implementation
│   └── PRODUCTION_DEPLOYMENT_TODO.md
└── STRATEGY/       # Future plans
    ├── VPS_TEMPLATE_STRATEGY.md
    └── ENTERPRISE_SCRIPTING_STRATEGY.md
```

### Reading Sequence (START HERE)
1. **FIRST**: `docs/README.md` - Documentation index and navigation
2. **For developers**: `docs/IMPLEMENTED/CURRENT_ARCHITECTURE.md` - What works now
3. **For tech details**: `docs/IMPLEMENTED/architecture.md` - Technical design
4. **For next steps**: `docs/TODO/PRODUCTION_DEPLOYMENT_TODO.md` - Implementation priorities
5. **For business**: `docs/STRATEGY/VPS_TEMPLATE_STRATEGY.md` - Deployment strategy

### Quick Commands Reference
```bash
# Development
npm run dev               # Start local development stack
./stack                   # Interactive CLI manager (password: PilotPro2025!)

# Access points
http://localhost:3000     # Business Portal (tiziano@gmail.com / testtest123)
http://localhost:3005     # Stack Controller (admin / PilotPro2025!)
```

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