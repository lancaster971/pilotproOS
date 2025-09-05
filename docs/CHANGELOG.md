# Changelog

All notable changes to PilotProOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-08-17

### Added
- **Complete n8n Integration**: Local n8n 1.106.3 with PostgreSQL dual-schema
- **PostgreSQL Database**: Dual schema architecture (n8n + pilotpros)
- **Developer Security Model**: VPN + authentication for n8n access
- **Business Abstraction Layer**: Complete technology anonymization
- **AI Agent Integration**: MCP-based conversational interface
- **Automated Setup Scripts**: One-command environment setup
- **Task Runners**: n8n task runners enabled for improved performance
- **Enterprise Security**: Nginx reverse proxy configuration
- **Database Migrations**: 67 n8n migrations + custom pilotpros schema
- **Backup System**: Automated database backup before upgrades

### Technical Details
- **n8n Version**: 1.106.3 (latest)
- **PostgreSQL**: 16.9 with libpq client
- **Node.js**: 18.0.0+ LTS support
- **Database Tables**: 42 total (36 n8n + 6 pilotpros)
- **Task Runners**: Enabled on port 5679
- **Security**: Complete technology hiding from clients

### Scripts & Commands
- `npm run n8n:setup` - Complete PostgreSQL + n8n setup
- `npm run n8n:start` - Start n8n with PostgreSQL
- `npm run n8n:stop` - Stop n8n server
- `npm run dev` - Full development stack (all services)
- `npm run install:all` - Install all workspace dependencies

### Security Features
- **Client Isolation**: Never sees n8n interface or technical terms
- **Developer Access**: Protected by VPN + IP whitelist + authentication
- **Database Security**: Proper schema isolation and permissions
- **Technology Anonymization**: Complete hiding of technical stack
- **Enterprise Headers**: Security headers and technology masking

### Architecture
- **Frontend**: React 18.2+ with TypeScript (port 3000)
- **Backend**: Express.js API middleware (port 3001)
- **AI Agent**: MCP integration server (port 3002)
- **n8n Engine**: Workflow engine (port 5678, dev-only)
- **Database**: PostgreSQL with dual-schema isolation

### Documentation
- **CLAUDE.md**: Complete development guidance
- **README.md**: Updated with modern setup instructions
- **Nginx Config**: Production security configuration
- **Developer Access**: VPN and authentication setup

### Database Schema
- **n8n schema**: 36 tables for workflow engine
- **pilotpros schema**: 6 tables for business logic
  - users (authentication)
  - business_analytics (aggregated metrics)
  - process_templates (workflow templates)
  - ai_conversations (chat logs)
  - audit_logs (security logs)
  - system_metrics (monitoring)

### Migrations Applied
- RenameAnalyticsToInsights1741167584277
- AddScopesColumnToApiKeys1742918400000
- ClearEvaluation1745322634000
- AddWorkflowStatisticsRootCount1745587087521
- AddWorkflowArchivedColumn1745934666076
- DropRoleTable1745934666077
- AddProjectDescriptionColumn1747824239000
- AddLastActiveAtColumnToUser1750252139166
- AddInputsOutputsToTestCaseExecution1752669793000

### Configuration Updates
- Removed deprecated `N8N_BINARY_DATA_TTL`
- Added `N8N_RUNNERS_ENABLED=true`
- Updated security settings for production
- Enhanced PostgreSQL permissions

### Developer Experience
- **Local Development**: http://localhost:5678 (admin/pilotpros_admin_2025)
- **Production Access**: https://client-domain.com/dev/workflows/
- **Database Access**: `psql pilotpros_db` with proper PATH setup
- **Automated Backups**: Before any major operations

### Known Issues
- Some npm audit warnings (non-critical)
- punycode deprecation warning (Node.js issue)

### Future Enhancements
- Frontend React components integration
- Business workflow templates loading
- AI agent workflow intelligence
- Advanced analytics and insights