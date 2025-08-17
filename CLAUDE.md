# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PilotProOS is a containerized Business Process Operating System - a comprehensive automation platform designed for SMB deployment. The system provides a business-friendly interface that completely abstracts away the underlying technical stack (n8n, PostgreSQL, Express) through an anonymization layer.

**Key Architecture Pattern**: 3-layer clean architecture with complete technology abstraction:
- **Frontend**: React/TypeScript SPA using business terminology
- **Backend**: Express API middleware that translates between business language and technical implementation  
- **Data Layer**: PostgreSQL with dual schema (n8n + app) for complete isolation

## Development Commands

### Root-level Commands (Workspace Management)
```bash
# Install all dependencies across workspaces
npm run install:all

# Development (all services concurrently including n8n)
npm run dev

# Development (individual services)
npm run dev:frontend  # Port 3000 (Vite dev server)
npm run dev:backend   # Port 3001 (Express API)
npm run dev:ai-agent  # Port 3002 (AI Agent API)
npm run dev:n8n       # Port 5678 (n8n workflow engine)

# n8n Management
npm run n8n:setup     # Complete PostgreSQL + n8n setup
npm run n8n:start     # Start n8n with PostgreSQL
npm run n8n:stop      # Stop n8n server

# Build all
npm run build

# Production deployment
npm run start:all     # Includes n8n server

# Docker deployment
npm run docker:build
npm run docker:run

# Quick deployment (all 4 scripts)
npm run deploy:quick

# Testing
npm run test              # All tests
npm run test:backend      # Jest backend tests
npm run test:frontend     # Vitest frontend tests
npm run test:integration  # Full system integration tests
npm run test:postgresql   # PostgreSQL integration tests
```

### Frontend (React/TypeScript/Vite)
```bash
cd frontend

# Development
npm run dev              # Vite dev server on :3000
npm run build           # Production build
npm run preview         # Preview production build

# Testing
npm run test            # Vitest
npm run test:ui         # Vitest UI
npm run test:watch      # Watch mode
npm run test:coverage   # Coverage report

# Code quality
npm run lint            # ESLint
npm run build:check    # TypeScript check + build
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
- **Database**: pilotpros_db (schema: n8n)
- **Version**: 1.106.3 (latest)
- **Task Runners**: Enabled (port 5679)

**🔒 Security Model:**
- **Client Access**: NEVER sees n8n interface or mentions
- **Developer Access**: VPN + authentication + IP whitelist
- **Business Translation**: All technical terms translated by backend middleware

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

**Frontend Business Layer**:
- `frontend/src/components/processes/` - Business process management (NOT workflows)
- `frontend/src/services/api.ts` - API layer with business terminology
- `frontend/src/utils/constants.ts` - Business terminology mapping
- `frontend/src/store/` - Zustand state management

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

**When working with the Frontend**:
1. Always use business terminology in components and APIs
2. Check `utils/constants.ts` for approved business language
3. UI components are in `components/ui/` (shadcn/ui based)
4. State management uses Zustand stores in `store/`

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

### n8n Upgrade to 1.106.3 (Latest)
- **Task Runners**: Enabled for improved performance
- **Database Migrations**: 9 new migrations applied successfully
- **Deprecation Fixes**: Removed N8N_BINARY_DATA_TTL, added N8N_RUNNERS_ENABLED
- **Security**: Enhanced with latest security patches
- **Backup**: Automated backup system in `backups/` directory

### Development Environment Setup
- **PostgreSQL**: Dual schema (n8n + pilotpros) fully configured
- **Local n8n**: http://localhost:5678 (admin / pilotpros_admin_2025)
- **Database**: pilotpros_db with 42+ tables total
- **Scripts**: Automated setup with `npm run n8n:setup`