# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PilotProOS is a containerized Business Process Operating System - a comprehensive automation platform designed for SMB deployment. The system provides a business-friendly interface that completely abstracts away the underlying technical stack (n8n, PostgreSQL, Express) through an anonymization layer.

**Key Architecture Pattern**: 3-layer clean architecture with complete technology abstraction:
- **Frontend**: Vue 3/TypeScript SPA using business terminology
- **Backend**: Express API middleware that translates between business language and technical implementation  
- **Data Layer**: PostgreSQL with dual schema (n8n + app) for complete isolation

## Development Commands

### ⚠️ **CRITICAL WARNING: DOCKER VOLUME BACKUP**
**SEMPRE fare backup dei volumi Docker prima di operazioni distruttive!**
- `docker:reset` con `-v` flag **CANCELLA DEFINITIVAMENTE** tutti i dati (PostgreSQL + n8n)
- `docker:clean` **RIMUOVE TUTTO** inclusi volumi e immagini
- **REGOLA FERREA**: Backup prima di qualsiasi reset/clean operation

**Quick Backup Command**:
```bash
# SEMPRE eseguire prima di docker:reset o docker:clean
docker run --rm -v pilotpros_postgres_dev_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres-volume-$(date +%Y%m%d-%H%M%S).tar.gz /data
docker run --rm -v pilotpros_n8n_dev_data:/data -v $(pwd):/backup ubuntu tar czf /backup/n8n-volume-$(date +%Y%m%d-%H%M%S).tar.gz /data
```

### Root-level Commands (Docker-First Cross-OS Development)
```bash
# 🚀 DOCKER-FIRST DEVELOPMENT (Auto-installs Docker if missing)
npm run dev               # Ensures Docker installed → Starts complete stack
npm run setup             # Install all Node.js dependencies
npm run reset             # Clean reset: stop containers + reinstall

# 🐳 DOCKER MANAGEMENT
npm run docker:stop       # Stop all development containers
npm run docker:restart    # Safe restart containers (preserva volumi)
npm run docker:reset      # ⚠️ BLOCCATO - mostra warning per prevenire data loss
npm run docker:reset-safe # Reset con backup automatico prima
npm run docker:logs       # View all container logs in real-time
npm run docker:psql       # Connect to PostgreSQL database directly
npm run docker:backup     # Crea backup timestamped dei volumi
npm run docker:clean      # ⚠️ Remove all containers, volumes, and images

# ⚠️ CRITICAL: BACKUP DOCKER VOLUMES BEFORE DESTRUCTIVE OPERATIONS
# SEMPRE fare backup prima di docker:reset, docker:clean, o operazioni con -v flag
docker volume list | grep pilotpros  # List volumes to backup
docker run --rm -v pilotpros_postgres_dev_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres-volume-$(date +%Y%m%d-%H%M%S).tar.gz /data
docker run --rm -v pilotpros_n8n_dev_data:/data -v $(pwd):/backup ubuntu tar czf /backup/n8n-volume-$(date +%Y%m%d-%H%M%S).tar.gz /data
# RECOVERY: docker volume create pilotpros_postgres_dev_data && docker run --rm -v pilotpros_postgres_dev_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/postgres-volume-YYYYMMDD-HHMMSS.tar.gz -C /

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
- **Frontend Vue 3** with hot reload  
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

**Business Execution Data Persistence**:
- `pilotpros.business_execution_data`: Core table storing parsed business data from workflow executions
- **CURRENT STATUS**: ✅ **FULLY IMPLEMENTED & VALIDATED** - Universal system working across all workflows
- **Architecture**: Pure PostgreSQL trigger with backend fallback for complex data decompression
- **Universal Coverage**: Works with ANY workflow - auto-detects show-X tagged nodes and classifies by n8n node type
- **Business Content**: Extracts actual output data (AI responses, email content, etc.) not just metadata
- **Frontend Pattern**: TimelineModal calls rawDataForModal API which reads from business_execution_data table first
- **Core Value Proposition**: Complete visibility into agent activities without checking external systems

**Production Architecture (FULLY VALIDATED)**:
```
n8n Execution Completes → PostgreSQL Trigger → Universal Node Detection → business_execution_data Table
                                    ↓                      ↓
                            show-X Tag Detection    Node Type Classification
                                    ↓                      ↓
                            Extract Business Data   Backend Fallback (if needed)
                                                           ↓
Frontend TimelineModal → rawDataForModal API → Read from business_execution_data (database-first)
```

**Universal System Features**:
- **Auto-Detection**: Automatically finds show-X tagged nodes in any workflow
- **Node Classification**: Universal mapping based on n8n node types (ai, email, database, generic, etc.)
- **Content Extraction**: Gets actual business output data, not just execution metadata
- **Terminology Sanitization**: Converts n8n technical terms to business language (n8n → WFEngine)
- **Tested Workflows**: Validated with multiple workflows (Milena: 7 nodes, GRAB INFO SUPPLIER: 5 nodes)
- **Perfect Consistency**: Database records match API responses exactly

### Development Patterns

**When working with the Frontend (Vue 3 + TypeScript + VueFlow)**:
1. Always use business terminology in components and APIs
2. Use Vue 3 Composition API with TypeScript interfaces for reactive workflows
3. Premium workflow visualization in `WorkflowCommandCenter.vue` with VueFlow integration
4. Node classification system: AI (rectangular), Tools (circular), Storage/Process (styled rectangles)
5. Multi-handle architecture: Agent nodes with main lateral + AI tool bottom connections
6. Bezier curve connections with dynamic handle positioning and smart edge routing
7. State management uses Pinia stores with real-time workflow data updates
8. Premium animations: 3D hover effects, pulse animations, glow effects for active states
9. **Modal System**: TimelineModal uses rawDataForModal API for consistent data across all sources
   - Supports calls from WorkflowsPage, ExecutionsTable, Dashboard, AgentsPage
   - Shows only show-n business-critical nodes (7 for Milena workflow)
   - Maintains data consistency between execution-specific and latest-execution views

**Icon System (Direct Assignment)**:
- **Location**: `frontend/src/components/N8nIcon.vue` - Central icon mapping component
- **Pattern**: Direct SVG imports with 1:1 mapping to n8n node types
- **Format**: All icons must be 48x48px with viewBox="0 0 512 512" 
- **Business Colors**: Use #F8FAFC (light), #10B981 (primary), avoid technical symbols
- **Mapping Process**:
  1. Import SVG: `import newIcon from '../assets/nodeIcons/svg/newIcon.svg'`
  2. Add to iconMap: `'exact-n8n-node-type': newIcon`
  3. Query database for exact node type: `docker exec pilotpros-postgres-dev psql -d pilotpros_db -c "SELECT DISTINCT type FROM n8n.workflow_entity"`
- **Node Type Examples**: `n8n-nodes-base.cron`, `@n8n/n8n-nodes-langchain.agent`, `n8n-nodes-base.httpRequest`
- **Hot Reload**: Vite automatically updates icons during development - no restart needed

**When working with the Backend**:
1. All public APIs use `/api/business/*` endpoints
2. Database queries must join both schemas for complete business data
3. Always apply security middleware stack
4. Log all business operations to audit trail
5. **rawDataForModal System**: Use `/api/business/raw-data-for-modal/:workflowId` for modal data extraction
   - Centralizes show-n nodes extraction from workflow definition
   - Merges with execution data intelligently
   - Supports multi-source modal calls (workflow view, executions table, dashboard)
   - Guarantees data consistency across all modal consumers

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

### Timeline Business Intelligence System (v1.5.1 - Latest)
- **Universal Node Enrichment**: Real business content extraction from all 7 workflow node types
- **Intelligent Content Parsing**: 
  - **Email Nodes**: Full message content extraction (received/sent emails with HTML cleanup)
  - **AI Agents**: Complete AI response parsing with category classification
  - **Vector Search**: Document search results with content previews
  - **Order/Parcel**: Order details, customer info, tracking numbers, delivery status
  - **Sub-Workflows**: Execution metrics, duration, nodes processed, success status
- **Premium Business Timeline**: Complete redesign with business process overview boxes
- **Customer-Centric Display**: Input/Output data presentation in business language with value statements
- **Real-Time Enrichment**: Live data processing with comprehensive debug logging and error handling
- **Production Validation**: Tested across multiple workflow types with 100% data consistency

### Modal System Implementation (v1.5.0)
- **Complete Modal Framework**: Developed comprehensive modal system with 3 component types
- **Business Data Parser**: Advanced `useBusinessParser.ts` composable for converting technical JSON to business language
- **Timeline Modal Enhancement**: Premium timeline visualization with step-by-step business process parsing
- **Integration Examples**: Complete practical examples in `docs/MODAL_INTEGRATION_EXAMPLES.md`
- **Component Library**: 
  - `SimpleModal.vue` - Form-based modal with validation
  - `DetailModal.vue` - Multi-tab modal with refresh capabilities
  - `TimelineModal.vue` - Process timeline with intelligent data parsing and universal enrichment
  - `useModal.ts` - Shared modal state management composable
- **Business Language Compliance**: Zero technical terminology exposed, complete n8n → Business Process translation
- **Premium UX**: Glassmorphism effects, smooth animations, responsive design
- **TypeScript Integration**: Full type safety across all modal components
- **Documentation**: Complete implementation guide + TODO checklist + integration examples

### Font Consistency & UI Cleanup (v1.4.0)
- **Typography Standardization**: Fixed global font-weight override that broke modal text hierarchy
- **Modal Font Consistency**: All modals now use standardized text sizes (text-lg for titles, text-base for content, text-sm for details)
- **Design System Integration**: Removed custom CSS in favor of global design system classes (btn-control, control-card)
- **CSV Export Removal**: Eliminated debug Export CSV functionality and related logic for cleaner codebase
- **Code Cleanup**: Removed 12k+ unused files from backend/n8n-icons/ directory

### Direct Icon Assignment System (v1.4.0)
- **File-Based Icon System**: Complete transition from dynamic loading to direct SVG imports
- **N8nIcon Component**: Central icon mapping with Record<string, string> pattern matching
- **Business Node Classification**: 4-tier system (AI Agents, AI Tools, Storage/Process, Triggers)
- **Icon Mapping Pattern**:
  ```typescript
  const iconMap: Record<string, string> = {
    'n8n-nodes-base.cron': cronIcon,
    'n8n-nodes-base.scheduleTrigger': scheduleIcon,
    '@n8n/n8n-nodes-langchain.agent': agentIcon,
    '@n8n/n8n-nodes-langchain.toolCalculator': calculatorIcon,
    // Direct 1:1 mapping of n8n node types to SVG imports
  }
  ```
- **Icon Creation Process**: 48x48px with viewBox="0 0 512 512", business-appropriate colors, no technical symbols
- **Hot Reload Integration**: Vite automatically updates icons during development
- **Agent Icon System**: New rectangular robot-style icons for LangChain agents vs circular tool icons

### Premium Workflow Visualization System (v1.3.0)
- **n8n-Style Command Center**: Enterprise-grade workflow visualization with VueFlow integration
- **Premium Node Design**: 4 distinct node types with professional gradients and animations
  - 🤖 **AI Agents**: Rectangular nodes (180x100px) with multi-handle support
  - 🟣 **AI Tools**: Circular nodes (90x90px) with smart auto-detection  
  - 🔵 **Storage**: Rectangular data nodes with professional styling
  - 🔴 **Triggers**: Rounded event handler nodes with distinct colors
- **Advanced Connection System**: Bezier curves, multiple handles, main vs AI tool connections
- **Real-Time Data**: Zero mock data - all 31 workflows from PostgreSQL with live statistics
- **Multi-Handle Architecture**: Agent nodes with lateral (main) + bottom (AI tools) handle positioning
- **Smart Classification**: Auto-detects node types from names and business categories
- **Premium Animations**: 3D hover effects, pulse animations, glow effects for active workflows

### Timeline Enrichment System (v1.5.0)
- **Universal Business Parser**: Complete composable for extracting real business content from all node types
- **Node Type Detection**: Automatic classification of email, AI, vector, order, workflow nodes with specific parsers
- **Real Content Extraction**: Email messages, AI responses, search results, order data, workflow status from raw JSON
- **Business Language Translation**: Converts technical data to customer-friendly summaries 
- **Premium Timeline UI**: Redesigned timeline with business process overview, input/output boxes, value statements
- **Debug Integration**: Comprehensive logging for enrichment process debugging and validation

### Enhanced Backend Integration (v1.3.0)
- **All Connection Types**: Backend now returns ai_tool, ai_memory, ai_languageModel connections (not just main)
- **31 Workflows**: Complete database integration returning all workflow entities 
- **Smart Handle Mapping**: Dynamic handle assignment based on connection types
- **CORS Optimized**: Removed problematic cache headers for seamless frontend integration
- **Real KPI Calculations**: Live execution counts, failure rates, time saved from actual data
- **Zero Mock Data**: Complete elimination of placeholder data throughout the system
- **rawDataForModal System**: Centralized modal data extraction with show-X nodes focus
  - Single endpoint `/api/business/raw-data-for-modal/:workflowId` serves all modal consumers
  - Universal fallback system extracts all 7 show-X tagged nodes from workflow definition
  - Merges with execution data intelligently (handles executed and non-executed nodes)
  - Maintains data consistency across WorkflowsPage, ExecutionsTable, Dashboard, AgentsPage calls
  - Workflow active status integration for proper timeline display

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

### Production-Ready Environment Status (v1.5.1 - Timeline Business Intelligence)
- **✅ PostgreSQL**: Dual schema (n8n + pilotpros) with 31 workflows verified
- **✅ n8n HTTPS**: https://localhost/dev/n8n/ on PostgreSQL backend (admin / pilotpros_admin_2025) - Version 1.108.1
- **✅ HTTPS Development**: Complete SSL setup with self-signed certificates + SAN for all domains/IPs
- **✅ OAuth Providers**: Microsoft Outlook ✅, Google ✅, Supabase ✅ - All tested and working with HTTPS
- **✅ SSL Infrastructure**: nginx SSL termination, automatic certificate generation, Docker SSL volumes
- **✅ Webhook HTTPS**: https://localhost/webhook/ - Ready for external integrations
- **✅ Premium Frontend**: Vue 3 + VueFlow with n8n-style workflow visualization
- **✅ Backend API**: Enhanced to return ALL connection types (ai_tool, ai_memory, etc.)
- **✅ Workflow Command Center**: Enterprise visualization with bezier curves and smart handles
- **✅ Node Classification**: 4 distinct node types with professional styling and animations
- **✅ Real-Time KPIs**: Live execution statistics, failure rates, active workflow counts
- **✅ Multi-Handle System**: Complex Agent nodes with lateral + bottom connection points
- **✅ Zero Mock Data**: Complete elimination of placeholder data across all components
- **✅ Docker Development**: Hot-reload enabled for all services with cross-OS compatibility + HTTPS
- **✅ Premium UX**: 3D effects, glow animations, hover transitions matching enterprise standards
- **✅ Font Consistency**: Standardized typography across all modals and components with DM Sans
- **✅ Direct Icon System**: Complete SVG import system with business-appropriate icons for all node types
- **✅ Code Cleanup**: Removed debug functionality and 12k+ unused backend files for optimized codebase
- **✅ SSL Automation**: Complete setup script (scripts/setup-ssl-dev.sh) for one-command HTTPS deployment
- **✅ Universal Data Persistence**: PostgreSQL trigger-based automatic business data capture for ALL workflows
- **✅ Business Content Extraction**: Captures actual AI responses, email content, and process outputs (not just metadata)
- **✅ Show-X Tag System**: Universal node marking system working across any workflow type
- **✅ Validated Architecture**: Tested with multiple workflows (Milena: 7 nodes, GRAB INFO SUPPLIER: 5 nodes)
- **✅ Perfect Data Consistency**: Database records match API responses with 100% accuracy
- **✅ Timeline Business Intelligence**: Universal enrichment system extracting real content from all 7 node types
- **✅ Customer-Centric Display**: Email messages, AI responses, search results, order data in business language
- **✅ Premium Timeline UI**: Business process overview with input/output boxes and value statements
- **✅ Real-Time Enrichment**: Live data processing with debug logging and comprehensive error handling
- **✅ Production Validated**: Complete system tested with actual workflow data and customer scenarios

## 📚 **DOCUMENTATION COMPLETA**

Per informazioni dettagliate consultare la documentazione tecnica completa in `/docs/`:

- **`docs/architecture.md`** - Architettura 3-layer dettagliata con Clean Architecture + n8n Compatibility System
- **`docs/deployment.md`** - Sistema deployment 4-script enterprise (5 minuti) + Zero-Downtime n8n Upgrades  
- **`docs/ai-agent.md`** - AI Agent conversazionale con NLP italiano
- **`docs/postgresql-setup.md`** - Configurazione PostgreSQL per n8n integration + Migration Management
- **`docs/n8n-upgrade-troubleshooting.md`** - Troubleshooting completo per upgrade n8n e compatibility issues

**NOTA IMPORTANTE**: I docs/ contengono l'architettura COMPLETA del sistema con tutti i dettagli implementativi, script di deployment, configurazioni di sicurezza, e specifiche tecniche avanzate. Consultare sempre i docs/ prima di modificare il sistema.