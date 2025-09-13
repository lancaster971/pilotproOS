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

---

## 🎯 **ZERO CUSTOM CODE POLICY**

⚠️ **REGOLA FONDAMENTALE**: Battle-tested libraries FIRST, custom code LAST RESORT

### Process:
1. Search existing libraries (`npm search [functionality]`)
2. Evaluate: stars, maintenance, TypeScript support
3. Test POC with library
4. Use library OR document why custom code necessary

### Battle-Tested Wins:
- Toast: Custom 181 lines → Vue Toastification
- Icons: 29 SVG → Iconify (200k+ icons)
- Database: Raw SQL → Drizzle ORM
- Validation: Custom → tRPC + Zod

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
npm run docker:backup     # Backup volumes (CRITICAL before reset)
```

### Testing
```bash
npm run test              # All tests in Docker
npm run test:backend      # Backend tests
npm run test:frontend     # Frontend tests
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

**Data Flow**: Frontend → Backend business API → Database (joins both schemas)

### Development Patterns

**Frontend (Vue 3 + TypeScript)**:
1. Business terminology only in all components
2. Composition API with TypeScript interfaces
3. Pinia stores for state management
4. VueFlow for workflow visualization

**Backend Translation**:
1. All APIs use `/api/business/*` endpoints
2. Join queries across both database schemas
3. Enterprise security middleware
4. Audit logging for all operations

**Icon System**:
- Location: `frontend/src/components/N8nIcon.vue`
- Pattern: Direct SVG imports with 1:1 n8n node type mapping
- Business colors, 48x48px icons

## Security & Deployment

### Client Deployment Sanitization
- **Zero Technical Exposure**: Client never sees Docker, n8n, PostgreSQL
- **Auto-Setup**: Single command deployment with business branding
- **Anonymous Containers**: "business-database", "automation-engine"
- **Silent n8n Setup**: Automated headless configuration

### Development Environment
- **Cross-OS**: Works identically on Windows/macOS/Linux
- **Auto-Install**: Docker setup automated
- **Hot-Reload**: All services with live development
- **HTTPS Ready**: SSL setup for production webhooks

## Key Constraints

1. **Zero Custom Code Tolerance**: Research libraries FIRST
2. **Business Language Only**: No technical terms in frontend
3. **Single Container Deploy**: All services in Docker
4. **Enterprise Security**: JWT, SSL, rate limiting required
5. **Italian AI Support**: Primary language for business queries

## Current Status

### Production Ready Features
- ✅ PostgreSQL dual schema with 31 workflows
- ✅ Vue 3 + VueFlow enterprise visualization  
- ✅ n8n HTTPS integration (admin/pilotpros_admin_2025)
- ✅ Business data extraction from all workflow types
- ✅ Zero mock data across all components
- ✅ Docker development with hot-reload
- ✅ Universal timeline system with pattern-based analysis
- ✅ SEC-001 RISOLTO: Zero valori hardcoded
- ✅ Sistema completamente deployabile in produzione

### Recent Updates (2025-09-12)
- ✅ **SEC-001 COMPLETATO**: Tutti i valori hardcoded rimossi
- ✅ **Ollama RIMOSSO**: Sostituito con pattern-based analysis
- ✅ **Documentazione PULITA**: Rimossi 4 documenti obsoleti
- ✅ **Production READY**: Sistema deployabile senza modifiche

## Documentation Structure

Essential docs in `/docs/` folder:
- `architecture.md` - Technical architecture details
- `postgresql-setup.md` - Database setup procedures  
- `n8n-upgrade-troubleshooting.md` - n8n compatibility system
- `developer-access-instructions.md` - Developer setup guide
- `DATA_RECOVERY_PLAN.md` - Backup and recovery procedures
- `Debiti_Tecnici.md` - Technical debt (32 attivi, 2 risolti)
- `Business_Intelligence_Service.md` - Pattern-based Timeline analysis
- `CUSTOMIZATION-STRATEGY.md` - Deployment customization
- `REVERSE_PROXY_README.md` - Reverse proxy configuration

---

**Development Workflow**: Research libraries → Business terminology → Docker testing → Enterprise deployment