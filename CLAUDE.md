# CLAUDE.md

This file provides guidance to Claude Code when working with this PilotProOS repository.

## 🚨 **REGOLA FERREA - DOCKER ISOLATION POLICY**

⚠️ **REGOLA ASSOLUTA**: TUTTO IN DOCKER tranne strumenti sviluppo

### **macOS Host SOLO per**:
- ✅ VS Code / Editor
- ✅ Browser / Testing tools
- ✅ Git / Version control
- ✅ Docker Desktop management

### **Docker Container per**:
- 🗄️ **Database**: PostgreSQL, Redis, etc - MAI host-mount
- 🔧 **Backend**: Node.js, Python, API servers
- 🎨 **Frontend**: Build tools, dev servers
- 🤖 **Automation**: n8n, workflow engines
- 📊 **Analytics**: Data processing, AI models

### **VIETATO ASSOLUTAMENTE**:
❌ Host-mounted volumes per database (`./data:/var/lib/postgresql/data`)
❌ Bind-mount di runtime data su macOS filesystem
❌ Mixed permissions tra Linux container e macOS host
❌ Direct filesystem access per dati persistenti

### **SOLO Named Volumes Docker**:
```yaml
# CORRETTO - ISOLAMENTO TOTALE:
volumes:
  postgres_data:/var/lib/postgresql/data  # Docker filesystem

# SBAGLIATO - CAUSA CORRUZIONE:
volumes:
  ./data:/var/lib/postgresql/data  # macOS filesystem
```

### **USER MANAGEMENT POLICY**:
⚠️ **REGOLA ENTERPRISE**: User management SOLO via UI/database diretta

- ✅ **Modifiche utenti**: Via interfaccia web o SQL dirette
- ✅ **Password changes**: Via UI o bcrypt manual update
- ❌ **ZERO backend seeding**: Nessun override automatico
- ❌ **ZERO init script** per utenti production: Solo schema/struttura

---

## 🎯 **ZERO CUSTOM CODE POLICY**

⚠️ **REGOLA FONDAMENTALE**: Battle-tested libraries FIRST, custom code LAST RESORT

### Process:
1. Search existing libraries (`npm search [functionality]`)
2. Evaluate: stars, maintenance, TypeScript support
3. Test POC with library
4. Use library OR document why custom code necessary

### Icon System Enterprise:
- **Location**: `frontend/src/components/N8nIcon.vue`
- **Pattern**: Direct Iconify imports con 1:1 n8n node type mapping
- **Categories**: 12 categorie semantiche con colori enterprise
- **Coverage**: 40+ nodi con icone professionali

## Project Overview

**PilotProOS**: Containerized Business Process Operating System
- **Architecture**: 3-layer clean with complete tech abstraction
- **Frontend**: Vue 3/TypeScript (business terminology only)
- **Backend**: Express API (translates business ↔ technical)
- **Data**: PostgreSQL dual schema (n8n + pilotpros)

## Development Commands

### Docker-First Development
```bash
npm run dev               # Auto-install Docker + start stack
npm run setup             # Install dependencies
npm run docker:stop       # Stop containers
npm run docker:restart    # Safe restart (preserves volumes)
npm run docker:logs       # View all logs
npm run docker:psql       # Connect to PostgreSQL
```

### Testing
```bash
npm run test              # All tests in Docker
npm run lint              # Code quality
npm run type-check        # TypeScript validation
```

## Architecture Principles

### Business Abstraction Layer
**CRITICAL**: Frontend NEVER exposes n8n, PostgreSQL, or technical terms

**Translations**:
- `workflow` → `Business Process`
- `execution` → `Process Run`
- `node` → `Process Step`
- `webhook` → `Integration Endpoint`

### Database Strategy
**Dual Schema**:
- `n8n`: n8n-managed tables
- `pilotpros`: Business application data

## Key Constraints

1. **Zero Custom Code Tolerance**: Research libraries FIRST
2. **Business Language Only**: No technical terms in frontend
3. **Single Container Deploy**: All services in Docker
4. **Enterprise Security**: JWT, SSL, rate limiting required

## Current Status

### Production Blockers
- ❌ **CRITICAL**: Authentication system DISABLED - vedere `docs/AUTH_TECHNICAL_DEBT.md`
- ❌ Sistema NON deployabile in produzione fino a fix auth

### Working Features
- ✅ PostgreSQL dual schema with workflows
- ✅ Vue 3 + VueFlow enterprise visualization
- ✅ n8n integration (admin/pilotpros_admin_2025)
- ✅ Business data extraction from all workflow types
- ✅ Docker development with hot-reload
- ✅ Pattern-based Timeline analysis

## Documentation Structure

Essential docs in `/docs/` folder:

### Core Technical Docs
- `architecture.md` - Technical architecture
- `AUTH_TECHNICAL_DEBT.md` - **CRITICAL: Auth system disabled**
- `Debiti_Tecnici.md` - Active technical debt

### Setup & Configuration
- `postgresql-setup.md` - Database setup
- `n8n-upgrade-troubleshooting.md` - n8n compatibility
- `developer-access-instructions.md` - Developer setup
- `security.md` - Security controls

### Features
- `Business_Intelligence_Service.md` - Timeline analysis
- `workflows.md` - Workflow guidelines

### Deployment
- `deployment.md` - Deployment overview
- `VPS_DEPLOYMENT_GUIDE.md` - VPS deployment (2-4GB RAM)
- `ENTERPRISE_SERVER_OPTIMIZATION.md` - Enterprise setup (16GB+ RAM)
- `DOCKER_OPTIMIZATION_PLAN.md` - Container optimization
- `CUSTOMIZATION-STRATEGY.md` - White-label customization
- `REVERSE_PROXY_README.md` - Reverse proxy config

---

**Development Workflow**: Research libraries → Business terminology → Docker testing → Fix auth before deploy