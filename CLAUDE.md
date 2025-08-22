# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PilotProOS is a containerized Business Process Operating System - a comprehensive automation platform designed for SMB deployment. The system provides a business-friendly interface that completely abstracts away the underlying technical stack (n8n, PostgreSQL, Express) through an anonymization layer.

**Key Architecture Pattern**: 3-layer clean architecture with complete technology abstraction:
- **Frontend**: React/TypeScript SPA using business terminology
- **Backend**: Express API middleware that translates between business language and technical implementation  
- **Data Layer**: PostgreSQL with dual schema (n8n + app) for complete isolation

## Development Commands

### Root-level Commands (Docker-First Cross-OS Development)
```bash
# 🚀 DOCKER-FIRST DEVELOPMENT (Auto-installs Docker if missing)
npm run dev               # Ensures Docker installed → Starts complete stack
npm run setup             # Install all Node.js dependencies
npm run reset             # Clean reset: stop containers + reinstall

# 🐳 DOCKER MANAGEMENT
npm run docker:stop       # Stop all development containers
npm run docker:reset      # Reset containers + database + restart
npm run docker:logs       # View all container logs in real-time
npm run docker:psql       # Connect to PostgreSQL database directly
npm run docker:clean      # Remove all containers, volumes, and images

# 🔄 BACKUP & DATA
npm run import:backup     # Import workflow/credentials backup (from BU_Hostinger)
npm run export:backup     # Export current setup to backup files
npm run n8n:auto-setup    # Auto-configure n8n with client data (silent setup)

# 🏗️ BUILD & PRODUCTION
npm run build             # Build all services for production
npm run start:all         # Production start (non-Docker mode)

# 🌐 CLIENT DEPLOYMENT (Sanitized)
npm run deploy:client     # Deploy to client server (completely anonymous)
npm run package:client    # Package client deployment bundle
npm run build:image       # Build client deployment image

# 🧪 TESTING (All in Docker)
npm run test              # Run all tests in Docker containers
npm run test:backend      # Backend tests in container
npm run test:frontend     # Frontend tests in container
npm run test:integration  # Integration tests in container

# 🔄 REAL-TIME DATA TESTING
npm run test:api          # Test all backend API endpoints
npm run test:websocket    # Test WebSocket server connections
npm run monitor:db        # Monitor real-time database changes
npm run generate:data     # Generate test data in PostgreSQL
npm run check:mock        # Find remaining mock data in frontend
```

**🐳 Complete Docker Stack Includes:**
- **PostgreSQL 16** with dual schema (n8n + pilotpros)
- **n8n 1.107.3** with task runners enabled
- **Backend API** with hot reload
- **Frontend React** with hot reload  
- **AI Agent MCP** with hot reload
- **PgAdmin** for database management (optional)

**✅ Cross-OS Guarantee:**
Any developer with Node.js can run `npm run dev` and get identical environment on Windows/macOS/Linux.

### Frontend (Vue 3/TypeScript/Vite)
```bash
cd frontend

# Development - Same stack as n8n
npm run dev              # Vite dev server on :3000 with Vue 3
npm run build           # Vue TypeScript build
npm run preview         # Preview production build
npm run type-check      # TypeScript validation

# Code quality
npm run lint            # ESLint for Vue 3
```

### Backend (Express/Node.js)
```bash
cd backend

# Development 
npm run dev             # Nodemon with hot reload
npm start              # Production start
npm run build          # No-op (JavaScript)

# Testing
npm run test           # Jest
npm run test:watch     # Jest watch mode
npm run test:coverage  # Jest coverage
```

### AI Agent (MCP Integration)
```bash
cd ai-agent

# Development
npm run dev            # Nodemon with MCP server integration
npm start             # Production start
npm run test:mcp      # Test MCP integration
```

### n8n Workflow Engine (Local Installation)
```bash
# First-time setup (run once)
npm run n8n:setup     # Creates PostgreSQL database, user, schemas, permissions

# Daily development
npm run n8n:start     # Start n8n server with PostgreSQL
npm run n8n:stop      # Stop n8n server

# Manual n8n management
./start-n8n-postgres.sh    # Direct start script
npx n8n start             # Raw n8n command (requires env vars)

# Database access
export PATH="/opt/homebrew/opt/libpq/bin:$PATH"
psql pilotpros_db         # Connect to database
```

**n8n Access:**
- **Development**: http://localhost:5678 (admin / pilotpros_admin_2025)
- **Production**: https://client-domain.com/dev/workflows/ (developer credentials + VPN)
- **Database**: PostgreSQL pilotpros_db (schemas: n8n + pilotpros)
- **Version**: 1.107.3 (latest)
- **Task Runners**: Enabled (port 5679)
- **API Authentication**: Supports both N8N_API_KEY and basic auth (user/password) for backup import
- **Environment Variables**: Automatic .env loading with dotenv for N8N_URL, N8N_API_KEY, N8N_ADMIN_*

**🐳 Docker Development Environment:**
- **PostgreSQL**: localhost:5432 (dual-schema: n8n + pilotpros)
- **Schema Isolation**: n8n (36 tables) + pilotpros (8 tables)
- **Cross-Schema Views**: Business analytics with real-time n8n data
- **Auto-Setup**: Complete environment in Docker containers
- **Hot-Reload**: All services with live development updates

**🔒 Security Model:**
- **Client Access**: NEVER sees n8n interface or mentions
- **Developer Access**: VPN + authentication + IP whitelist
- **Business Translation**: All technical terms translated by backend middleware

## Cross-OS Development Strategy

### 🚀 Multi-Environment Architecture

**DEVELOPMENT**: Cross-platform compatibility for any developer
**PRODUCTION**: Sanitized client deployment with complete technology hiding

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEVELOPMENT ENVIRONMENTS                           │
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │    DOCKER STACK     │  │   LOCAL INSTALL     │  │   SQLITE FALLBACK   │  │
│  │  (Cross-Platform)   │  │  (OS-Dependent)     │  │     (Portable)      │  │
│  │                     │  │                     │  │                     │  │
│  │ 🐳 PostgreSQL       │  │ 🍺 Homebrew PG      │  │ 📁 SQLite File      │  │
│  │ 🐳 n8n Container    │  │ 📦 npx n8n          │  │ 📦 npx n8n          │  │
│  │ 🐳 Backend/Frontend │  │ 📱 npm run services │  │ 📱 npm run services │  │
│  │                     │  │                     │  │                     │  │
│  │ ✅ Windows/Mac/Linux│  │ ⚠️ macOS/Linux only │  │ ✅ Any OS + Node.js │  │
│  │ ✅ Zero setup       │  │ ❌ Manual DB setup  │  │ ✅ File-based       │  │
│  │ ✅ Production-like  │  │ ✅ Native speed     │  │ ⚠️ Limited features │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT DEPLOYMENT                                │
│                        (Complete Anonimization)                            │
│                                                                             │
│  🌐 Ubuntu Server + Docker → "Business Automation Platform"                │
│  🚫 Client NEVER sees: PostgreSQL, n8n, Docker, technical terms            │
│  ✅ Single command deploy: curl install.sh | bash -s domain.com            │
│  ⏱️ 5-minute setup: Domain → Working business platform                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 🔄 Docker-First Development Flow

```bash
# Docker-First npm run dev behavior:
if (docker not installed):
    → Auto-install Docker for current OS
    → "🚀 Installing Docker Desktop for cross-OS development..."
    
if (docker not running):
    → Auto-start Docker
    → "🐳 Starting Docker Desktop..."
    
always:
    → Launch complete Docker stack
    → "🚀 Starting PilotProOS Docker Development Stack..."

# Always results in:
# ✅ Frontend: http://localhost:3000 (React with hot-reload)
# ✅ Backend: http://localhost:3001 (Express with hot-reload)
# ✅ AI Agent: http://localhost:3002 (MCP with hot-reload)
# ✅ n8n: http://localhost:5678 (admin / pilotpros_admin_2025)
# ✅ Database: localhost:5432 (PostgreSQL with dual schema)
# ✅ PgAdmin: http://localhost:5050 (database management)
```

### 📦 Environment Portability

**Developer Onboarding**:
1. `git clone` the repository
2. `npm run dev` → Auto-detects Docker, installs if needed, starts complete stack
3. Immediate development ready with PostgreSQL + n8n

**Client Deployment** (Completely Sanitized):
1. `curl https://install.pilotpro.com/setup | bash` 
2. Client provides: domain, email, name, company
3. Script installs "Business Automation Platform" (never mentions Docker/PostgreSQL/n8n)
4. n8n auto-configures silently with client data (NO telemetry/updates flagged)
5. Client sees only: "✅ Business Platform Ready at https://domain.com"

**Backup Import/Export**:
```bash
npm run import:backup    # Load BU_Hostinger workflow backup
npm run export:backup    # Create portable backup files
npm run migrate:postgres # Upgrade SQLite → PostgreSQL seamlessly
```

**BU_Hostinger Production Backup**:
- **database.sqlite.gz**: Compressed SQLite production database from Hostinger deployment
- **workflows.json**: Exported workflow definitions with complete node configurations
- **credentials.json**: Encrypted credential data for workflow authentication
- **Purpose**: Real production data for testing backup import system and migration validation

## Code Architecture

### Fundamental Principle: Business Abstraction
**CRITICAL**: The entire system is designed around complete anonymization of technical terminology. The frontend NEVER exposes that it uses n8n, PostgreSQL, or other technical details.

**Terminology Translation**:
- `workflow` → `Business Process`
- `execution` → `Process Run`  
- `node` → `Process Step`
- `webhook` → `Integration Endpoint`
- `trigger` → `Event Handler`

### Key File Structure

**Frontend Business Layer (Vue 3 + TypeScript)**:
- `frontend/src/pages/` - Vue 3 pages with Composition API (LoginPage, DashboardPage, WorkflowsPage, etc.)
- `frontend/src/components/` - Reusable Vue components (layout, agents, workflows, etc.)
- `frontend/src/stores/` - Pinia state management (auth, ui, workflows)
- `frontend/src/services/api.ts` - Axios API layer with business terminology
- `frontend/src/types/` - TypeScript interfaces for type safety

**Backend Translation Layer**:
- `backend/src/controllers/` - Business API endpoints (/api/business/*)
- `backend/src/services/database.service.ts` - Database abstraction layer
- `backend/src/repositories/` - Data access with business models
- `backend/src/middleware/security.js` - Enterprise security stack

**AI Agent (MCP Integration)**:
- `ai-agent/src/index.js` - Main MCP client integration
- Connects to existing PilotProMT MCP server for workflow tools
- Processes Italian natural language business queries

### Database Architecture
**Dual Schema Strategy**:
- `n8n` schema: n8n-managed tables (workflow_entity, execution_entity)
- `pilotpros` schema: Application business data (business_analytics, users, audit_logs)

**Critical**: Never expose n8n schema directly to frontend. All data access goes through backend business translation layer.

### Development Patterns

**When working with the Frontend (Vue 3 + TypeScript)**:
1. Always use business terminology in components and APIs
2. Use Vue 3 Composition API with TypeScript interfaces
3. Pages are in `src/pages/` with full component structure
4. State management uses Pinia stores in `src/stores/`
5. Components are in `src/components/` organized by feature
6. API calls in `src/services/api.ts` with Axios interceptors

**When working with the Backend**:
1. All public APIs use `/api/business/*` endpoints
2. Database queries must join both schemas for complete business data
3. Always apply security middleware stack
4. Log all business operations to audit trail

**When working with AI Agent**:
1. Supports Italian natural language queries
2. Routes intents to appropriate MCP tools
3. Translates technical responses to business language
4. Maintains conversation context for analytics

## Testing Strategy

### Frontend Testing
- **Unit**: Vitest for component logic
- **Integration**: Testing Library for UI interactions  
- **E2E**: Custom scripts in `frontend/scripts/`

### Backend Testing
- **Unit**: Jest for business logic
- **Integration**: Supertest for API endpoints
- **Database**: Test PostgreSQL integration with `npm run test:postgresql`

### System Testing
- **Full Stack**: `npm run test:integration` 
- **Production**: `scripts/test-enterprise.sh` (simulates real deployment)

## Deployment Architecture

**Single Container Deployment**:
The system deploys as a single Docker container containing all services. Use the automated deployment scripts:

1. `scripts/01-system-setup.sh` - System infrastructure 
2. `scripts/02-application-deploy.sh` - Application stack
3. `scripts/03-security-hardening.sh` - Security configuration
4. `scripts/04-workflow-automation.sh` - Business templates

**Client Installation Sanitization System**:
Complete client deployment sanitization with zero technical exposure:

- **install-pilotpro-os.sh**: Professional "PilotPro OS" branding installation script
- **n8n-silent-setup.js**: Automated headless n8n configuration with client data
- **pilotpro-os-setup.sh**: Business-friendly setup process (domain, email, name, company)
- **Container Anonymization**: "business-database", "automation-engine", "business-api" naming
- **Complete Technology Hiding**: Client never sees Docker, PostgreSQL, n8n, or technical terms
- **Auto-Configuration**: n8n owner account, frontend branding, database schemas created automatically
- **Telemetry Disabled**: All n8n telemetry, updates, and surveys automatically disabled

**Environment Configuration**:
All environment variables are defined in project root. Key configs:
- Database: PostgreSQL connection with dual schema
- n8n: Internal localhost-only access on port 5678
- Security: SSL, JWT, rate limiting, CORS
- Client: White-label branding configuration

## Development Workflow

### Making Changes to Business Logic
1. Update backend business controller/service
2. Ensure database queries join both schemas appropriately  
3. Update frontend API service calls
4. Test business terminology consistency
5. Run integration tests to verify end-to-end flow

### Adding New Features
1. Design business terminology first (avoid technical jargon)
2. Implement backend API with proper security
3. Create frontend components using business language
4. Add appropriate tests at all layers
5. Update AI agent intent recognition if needed

### Security Considerations
- Never expose technical implementation details in APIs
- Always validate and sanitize user inputs
- Use JWT authentication for all business operations
- Log all business operations for audit compliance
- Rate limit all public endpoints

## Important Constraints

- **Business Terminology Only**: Frontend must never reference n8n, PostgreSQL, technical terms
- **Single Container**: All services must work within single Docker deployment
- **Security First**: Enterprise-grade security hardening required
- **Italian Language**: AI Agent primarily supports Italian business queries
- **Clean Architecture**: Maintain strict separation between business and technical layers

## Recent Updates

### Vue 3 + TypeScript Frontend Implementation (v1.2.0 - Latest)
- **Same Stack as n8n**: Vue 3.4.21 + TypeScript + Pinia + Vue Router - identical to n8n frontend
- **Complete Migration**: React → Vue 3 with same functionality and design
- **Real Backend Integration**: ZERO mock data - only real API calls to PilotProOS backend
- **29 Workflows Loaded**: All workflows from PostgreSQL database (1 active, 28 inactive)
- **AgentDetailModal**: Killer feature component with timeline step-by-step (backend-ready)
- **Composition API**: Modern Vue 3 patterns with TypeScript interfaces
- **Docker Optimized**: Vite + Vue perfect compatibility with Docker containers
- **Component Architecture**: LoginPage, Dashboard, Workflows, Executions, Stats, Security, AI Agents
- **State Management**: Pinia stores for auth, UI, workflows with reactive updates
- **API Layer**: Axios client with interceptors, same pattern as n8n

### Backend Real Data Integration (v1.2.0)
- **Database Filter Removed**: Now returns ALL 29 workflows (not just active)
- **Real API Endpoints**: `/api/business/processes` returns real PostgreSQL data
- **Business Terminology**: Complete workflow → business process anonymization
- **Zero Mock Data**: Frontend shows real backend data or explicit API errors
- **DatabaseCompatibilityService**: Updated to return complete workflow list
- **API Error Handling**: Clear error messages when endpoints not implemented

### Frontend Architecture Completed (v1.2.0)
- **Vue 3 + TypeScript**: Professional frontend matching n8n technology stack
- **Real Data Only**: No mock data, only backend API calls
- **Component System**: Reusable Vue components with TypeScript interfaces
- **Router Guards**: Authentication routing same pattern as n8n
- **Chart Integration**: Chart.js + vue-chartjs for analytics
- **Icon System**: Lucide Vue Next for consistent iconography
- **Responsive Design**: Mobile + desktop optimized
- **Hot Module Replacement**: Perfect HMR in Docker development

### Docker-First Development Strategy (v1.1.0)
- **Cross-OS Compatibility**: Windows/macOS/Linux identical environment
- **Auto-Installation**: Docker auto-install and setup
- **Container Stack**: PostgreSQL + n8n + all services in Docker
- **Hot-Reload Development**: All services with live updates
- **Zero Manual Setup**: `git clone` + `npm run dev` = ready

### PostgreSQL Integration Verified (Production Ready)
- **Database**: PostgreSQL 16 with dual-schema architecture
- **n8n Schema**: 36 tables (workflow_entity, execution_entity, credentials_entity, etc.)
- **PilotProOS Schema**: 8 tables (users, business_analytics, process_templates, etc.)
- **Cross-Schema Integration**: Trigger-based real-time analytics
- **Performance**: Optimized indexes and connection pooling

### n8n Version Compatibility System
- **DatabaseCompatibilityService**: Automatic n8n version detection and schema adaptation
- **N8nFieldMapper**: Cross-version field mapping for seamless upgrades
- **Graceful Degradation**: Fallback queries for version compatibility
- **Runtime Monitoring**: Real-time compatibility monitoring with API endpoints
- **Zero Downtime**: Backend remains functional during n8n version upgrades
- **Breaking Change Protection**: Automatic handling of schema changes between versions

### Development Environment Setup Status
- **✅ PostgreSQL**: Dual schema (n8n + pilotpros) verified working in Docker
- **✅ n8n**: http://localhost:5678 on PostgreSQL backend (admin@pilotpros.local / PilotPro2025!) - Version 1.108.1
- **✅ Backend**: Connected to PostgreSQL with cross-schema access - real data API working
- **✅ Frontend**: Vue 3 + TypeScript with hot-reload - same stack as n8n
- **✅ AI Agent**: MCP integration ready
- **✅ Database**: 44 tables total (36 n8n + 8 pilotpros) - 29 workflows loaded
- **✅ Docker**: Complete containerized development stack
- **✅ Real Data Integration**: Frontend uses only real backend data, zero mock data
- **✅ Business API**: `/api/business/processes` returns all 29 workflows from database
- **✅ Timeline Component**: AgentDetailModal ready for backend timeline API
- **✅ Navigation**: Vue Router with auth guards, complete SPA functionality
- **✅ State Management**: Pinia stores for reactive data management

## 📚 **DOCUMENTATION COMPLETA**

Per informazioni dettagliate consultare la documentazione tecnica completa in `/docs/`:

- **`docs/architecture.md`** - Architettura 3-layer dettagliata con Clean Architecture + n8n Compatibility System
- **`docs/deployment.md`** - Sistema deployment 4-script enterprise (5 minuti) + Zero-Downtime n8n Upgrades  
- **`docs/ai-agent.md`** - AI Agent conversazionale con NLP italiano
- **`docs/postgresql-setup.md`** - Configurazione PostgreSQL per n8n integration + Migration Management
- **`docs/n8n-upgrade-troubleshooting.md`** - Troubleshooting completo per upgrade n8n e compatibility issues

**NOTA IMPORTANTE**: I docs/ contengono l'architettura COMPLETA del sistema con tutti i dettagli implementativi, script di deployment, configurazioni di sicurezza, e specifiche tecniche avanzate. Consultare sempre i docs/ prima di modificare il sistema.