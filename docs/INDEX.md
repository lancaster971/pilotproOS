# Documentation Index

**PilotProOS Documentation Catalog**

Complete directory of all project documentation organized by category.

Last Updated: 2025-10-12

---

## Getting Started

Essential documentation for new developers and users.

| Document | Description | Location |
|----------|-------------|----------|
| **README.md** | Quick Start + Architecture Overview | [/README.md](../README.md) |
| **CLAUDE.md** | Complete Project Guide (main reference) | [/CLAUDE.md](../CLAUDE.md) |
| **TODO-URGENTE.md** | Critical Fixes + Development Roadmap (17-23h) | [/TODO-URGENTE.md](../TODO-URGENTE.md) |
| **CONTRIBUTING.md** | Development Guidelines + Best Practices | [/docs/CONTRIBUTING.md](./CONTRIBUTING.md) |
| **API_DOCUMENTATION.md** | Intelligence Engine API Reference | [/API_DOCUMENTATION.md](../API_DOCUMENTATION.md) |

---

## Architecture & Implementation

Technical architecture and implementation details.

| Document | Description | Location |
|----------|-------------|----------|
| **CURRENT_ARCHITECTURE.md** | System Architecture Overview (7 services) | [/docs/IMPLEMENTED/CURRENT_ARCHITECTURE.md](./IMPLEMENTED/CURRENT_ARCHITECTURE.md) |
| **TODO-MILHENA-ARCHITECTURE.md** | Milhena v3.1 ReAct Agent Details | [/intelligence-engine/TODO-MILHENA-ARCHITECTURE.md](../intelligence-engine/TODO-MILHENA-ARCHITECTURE.md) |
| **CONTAINER_PROTECTION_SYSTEM.md** | Docker Container Protection Mechanisms | [/docs/IMPLEMENTED/CONTAINER_PROTECTION_SYSTEM.md](./IMPLEMENTED/CONTAINER_PROTECTION_SYSTEM.md) |
| **API-VAULT-ARCHITECTURE.md** | API Credential Management Architecture | [/API-VAULT-ARCHITECTURE.md](../API-VAULT-ARCHITECTURE.md) |
| **REDIS-TTL-STRATEGY.md** | Redis TTL + Checkpointer Strategy | [/REDIS-TTL-STRATEGY.md](../REDIS-TTL-STRATEGY.md) |

---

## Testing & Quality

Testing guides, bug fixes, and quality assurance documentation.

| Document | Description | Location |
|----------|-------------|----------|
| **TEST-HOT-RELOAD.md** | Hot-Reload Pattern Testing Guide | [/TEST-HOT-RELOAD.md](../TEST-HOT-RELOAD.md) |
| **CORRECTED-FIX-RESULTS.md** | AsyncRedisSaver Fix Validation | [/CORRECTED-FIX-RESULTS.md](../CORRECTED-FIX-RESULTS.md) |
| **LATENCY-FIX-ROOT-CAUSE-ANALYSIS.md** | Latency Issue Root Cause Analysis | [/LATENCY-FIX-ROOT-CAUSE-ANALYSIS.md](../LATENCY-FIX-ROOT-CAUSE-ANALYSIS.md) |
| **TODO-CLASSIFIER-V4-FIX.md** | Classifier Template String Bug Fix | [/TODO-CLASSIFIER-V4-FIX.md](../TODO-CLASSIFIER-V4-FIX.md) |

---

## Release Notes & Changelogs

Version history and release documentation.

| Document | Description | Location |
|----------|-------------|----------|
| **CHANGELOG.md** | Complete Version History (all releases) | [/CHANGELOG.md](../CHANGELOG.md) |
| **CHANGELOG-v3.3.1.md** | v3.3.1 Hot-Reload Release Notes | [/CHANGELOG-v3.3.1.md](../CHANGELOG-v3.3.1.md) |
| **IMPLEMENTATION-HOT-RELOAD.md** | Hot-Reload Technical Implementation Report | [/IMPLEMENTATION-HOT-RELOAD.md](../IMPLEMENTATION-HOT-RELOAD.md) |

---

## Development & Planning

Development roadmap, technical debt, and future features.

| Document | Description | Location |
|----------|-------------|----------|
| **TODO-URGENTE.md** | Critical Fixes + Development Roadmap | [/TODO-URGENTE.md](../TODO-URGENTE.md) |
| **NICE-TO-HAVE-FEATURES.md** | Future Features Wishlist (auto-learning, UI) | [/NICE-TO-HAVE-FEATURES.md](../NICE-TO-HAVE-FEATURES.md) |
| **DEBITO-TECNICO.md** | Technical Debt + Post-Production Cleanup | [/DEBITO-TECNICO.md](../DEBITO-TECNICO.md) |
| **PRODUCTION_DEPLOYMENT_TODO.md** | Production Deployment Checklist | [/docs/TODO/PRODUCTION_DEPLOYMENT_TODO.md](./TODO/PRODUCTION_DEPLOYMENT_TODO.md) |

---

## Best Practices & Research

Research findings and best practices documentation.

| Document | Description | Location |
|----------|-------------|----------|
| **API-VAULT-BEST-PRACTICES-RESEARCH.md** | API Credential Management Best Practices | [/API-VAULT-BEST-PRACTICES-RESEARCH.md](../API-VAULT-BEST-PRACTICES-RESEARCH.md) |
| **API-VAULT-EXECUTIVE-SUMMARY.md** | API Vault System Executive Summary | [/API-VAULT-EXECUTIVE-SUMMARY.md](../API-VAULT-EXECUTIVE-SUMMARY.md) |
| **CONTRIBUTING.md** | Development Best Practices | [/docs/CONTRIBUTING.md](./CONTRIBUTING.md) |

---

## Implementation Files (Key Code)

Critical implementation files to reference.

| File | Description | Location |
|------|-------------|----------|
| **graph.py** | Milhena v3.1 Main Implementation (1900+ lines) | [/intelligence-engine/app/milhena/graph.py](../intelligence-engine/app/milhena/graph.py) |
| **hot_reload.py** | Hot-Reload Pattern System (297 lines) | [/intelligence-engine/app/milhena/hot_reload.py](../intelligence-engine/app/milhena/hot_reload.py) |
| **ChatWidget.vue** | Frontend Chat Widget (dark theme) | [/frontend/src/components/ChatWidget.vue](../frontend/src/components/ChatWidget.vue) |
| **milhena.routes.js** | Backend Milhena Proxy + Admin Endpoints | [/backend/src/routes/milhena.routes.js](../backend/src/routes/milhena.routes.js) |

---

## Quick Command Reference

Essential commands for daily development.

### Stack Management

```bash
./stack                          # Interactive CLI
./stack-safe.sh start            # Start all services
./stack-safe.sh status           # Health check
./stack-safe.sh stop             # Stop services
./graph                          # LangGraph Studio
```

### Logs & Debugging

```bash
docker logs pilotpros-intelligence-engine-dev -f
docker logs pilotpros-backend-dev -f
docker logs pilotpros-frontend-dev -f
docker exec pilotpros-redis-dev redis-cli KEYS "*checkpoint*"
```

### Testing

```bash
# Test Intelligence Engine
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "quali workflow?", "session_id": "test"}'

# Test Hot-Reload
curl -X POST http://localhost:3001/api/milhena/patterns/reload \
  -H "Content-Type: application/json" \
  -d '{}'

# Check Redis Checkpoints
docker exec pilotpros-redis-dev redis-cli KEYS "*checkpoint*" | wc -l
```

---

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | tiziano@gmail.com / Hamlet@108 |
| **Backend API** | http://localhost:3001 | - |
| **Intelligence** | http://localhost:8000 | - |
| **Stack Control** | http://localhost:3005 | admin / PilotPro2025! |
| **n8n (Process Automation)** | http://localhost:5678 | admin / pilotpros_admin_2025 |

---

## Documentation Categories

### By Priority

1. **CRITICAL** - Must read for all developers
   - README.md
   - CLAUDE.md
   - TODO-URGENTE.md

2. **HIGH** - Important for active development
   - CONTRIBUTING.md
   - API_DOCUMENTATION.md
   - CURRENT_ARCHITECTURE.md

3. **MEDIUM** - Reference when needed
   - TEST-HOT-RELOAD.md
   - CHANGELOG.md
   - NICE-TO-HAVE-FEATURES.md

4. **LOW** - Background information
   - DEBITO-TECNICO.md
   - Research documents (API-VAULT-*)
   - Historical changelogs

### By Audience

**New Developers**:
- Start with: README.md → CLAUDE.md → CONTRIBUTING.md
- Then: CURRENT_ARCHITECTURE.md → API_DOCUMENTATION.md

**Contributors**:
- Focus on: TODO-URGENTE.md → CONTRIBUTING.md → DEBITO-TECNICO.md
- Reference: NICE-TO-HAVE-FEATURES.md → Specific implementation docs

**Architects/Reviewers**:
- Review: CLAUDE.md → CURRENT_ARCHITECTURE.md → TODO-MILHENA-ARCHITECTURE.md
- Deep dive: Research documents (API-VAULT-*, REDIS-TTL-STRATEGY.md)

---

## Document Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Complete and up-to-date |
| 🔄 | In development |
| ⚠️ | Needs update |
| 📋 | Planning/draft stage |

---

## Need Help?

- **General Questions**: Read CLAUDE.md
- **Setup Issues**: Check README.md Quick Start
- **Development Guidelines**: See CONTRIBUTING.md
- **API Reference**: Check API_DOCUMENTATION.md
- **Bugs/Issues**: Review TODO-URGENTE.md

---

**Maintained by**: PilotProOS Development Team
**Last Review**: 2025-10-12
**Documentation Standard**: Markdown + GitHub-flavored
