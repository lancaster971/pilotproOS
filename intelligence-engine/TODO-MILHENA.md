# TODO-MILHENA: System Agent Implementation Plan

> **Enterprise-Grade Multi-Agent Orchestrator**
> Production-ready implementation following LangGraph 2025 best practices

**Status**: 🟡 **PLANNING**
**Version**: 1.0.0
**Last Updated**: 2025-09-27
**Branch**: `system-agent`

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Dependencies & Requirements](#dependencies--requirements)
4. [Implementation Plan](#implementation-plan)
5. [Best Practices & Patterns](#best-practices--patterns)
6. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
7. [Testing Strategy](#testing-strategy)
8. [Deployment Checklist](#deployment-checklist)

---

## 🎯 Executive Summary

### Objectives
Implementare **Milhena**, un orchestratore multi-agente **deterministico** per supporto interno sistema PilotProOS che:

- **Elimina allucinazioni** attraverso validazione rigorosa
- **Maschera completamente** la tecnologia sottostante
- **Garantisce consistenza** delle risposte
- **Scala orizzontalmente** per deployment enterprise

### Key Differentiators

| Feature | Value |
|---------|-------|
| **Zero Allucinazioni** | Validatore + Masking deterministico |
| **Response Time** | <500ms p95 con Redis cache |
| **Uptime Target** | 99.9% availability |
| **Scalability** | Stateless agents, connection pooling |

---

## 🏗️ Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│              INTELLIGENCE ENGINE (Universal Platform)        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           SYSTEM AGENTS (Trusted)                     │  │
│  │  • Milhena (Support Agent) ◀── THIS PROJECT          │  │
│  │  • Monitor (Health Check)                            │  │
│  │  • Analytics (Reporting)                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          CUSTOMER AGENTS (Sandboxed)                  │  │
│  │  • Custom workflows                                   │  │
│  │  • n8n integrations only                             │  │
│  │  • NO database access                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Milhena Architecture (Hybrid Approach)

```
User Query
    │
    ▼
┌─────────────────┐
│ Classifier      │  (Agent with LLM)
│ Agent           │  Categorizes: BUSINESS_DATA | HELP | GREETING | TECHNOLOGY
└────────┬────────┘
         │
         ├─────────────▶ BUSINESS_DATA Pipeline
         │              │
         │              ▼
         │         ┌─────────────────┐
         │         │ Data Analyst    │  (Agent with BusinessIntelligentQueryTool)
         │         │ Agent           │  Executes DB queries (read-only user)
         │         └────────┬────────┘
         │                  │
         │                  ▼
         │         ┌─────────────────┐
         │         │ Validator       │  (Agent with LLM)
         │         │ Agent           │  Eliminates hallucinations
         │         └────────┬────────┘
         │                  │
         │                  ▼
         │         ┌─────────────────┐
         │         │ Business        │  (Deterministic Library - NOT an agent)
         │         │ Masking Layer   │  Fixed dictionary, zero LLM calls
         │         └────────┬────────┘
         │                  │
         │                  ▼
         │            Final Response (100% business language)
         │
         └─────────────▶ Direct Response
                        (Static for HELP/GREETING/TECHNOLOGY)
```

### Key Design Decisions

#### ✅ **Why Masking is a Library, NOT an Agent**

| Aspect | Agent Approach | Library Approach ✅ |
|--------|----------------|---------------------|
| **Consistency** | Variable (LLM) | Guaranteed (dictionary) |
| **Allucinazioni** | Possibili | IMPOSSIBILI |
| **Performance** | Lento (LLM call) | Veloce (O(1) lookup) |
| **Testabilità** | Difficile | Unit test facili |
| **Costo** | $$ per query | $0 |

**Decisione**: Usare LIBRARY per enterprise reliability.

#### ✅ **Why Direct DB Access for System Agents**

| Consideration | API Approach | Direct DB ✅ |
|---------------|--------------|--------------|
| **Latency** | +100ms overhead | Immediate |
| **Flexibility** | Limited by API | Full SQL power |
| **Complexity** | 2 components | 1 component |
| **Security** | Via backend | Read-only user |

**Decisione**: Direct DB con utente read-only PostgreSQL dedicato.

---

## 📦 Dependencies & Requirements

### Current Versions (requirements.txt)

```python
# CRITICAL UPGRADE NEEDED
langgraph==0.2.61  # ❌ OUTDATED - Upgrade to 0.6.7
```

### Required Upgrades

```python
# Core LangGraph (UPGRADE)
langgraph==0.6.7  # ⬆️ From 0.2.61
langgraph-checkpoint-postgres==2.0.11  # ➕ NEW - For durable execution
langsmith==0.3.0  # ➕ NEW - For observability

# Keep Current (Already Optimal)
langchain==0.3.27
langchain-core==0.3.76
langchain-openai==0.3.33

# Database (Production Consideration)
psycopg2==2.9.10  # ⚠️ Change from psycopg2-binary in production
asyncpg==0.30.0  # Keep
redis==5.2.0  # Keep

# LLMs
openai>=1.104.2
anthropic==0.40.0

# API
fastapi==0.115.5
uvicorn[standard]==0.32.1
```

### New Database User (PostgreSQL)

```sql
-- Execute as postgres admin
CREATE USER pilotpros_agent_ro WITH PASSWORD 'SecureAgentPass2025!';

-- Grant READ-ONLY access
GRANT CONNECT ON DATABASE pilotpros_db TO pilotpros_agent_ro;
GRANT USAGE ON SCHEMA pilotpros TO pilotpros_agent_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA pilotpros TO pilotpros_agent_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA pilotpros
  GRANT SELECT ON TABLES TO pilotpros_agent_ro;

-- Verify permissions
\du pilotpros_agent_ro
```

### Environment Variables (.env)

```bash
# Milhena System Agent
MILHENA_DB_USER=pilotpros_agent_ro
MILHENA_DB_PASSWORD=SecureAgentPass2025!
MILHENA_DB_TIMEOUT=5000  # 5 seconds

# Redis Cache
MILHENA_CACHE_TTL=60  # seconds
MILHENA_CACHE_PREFIX=milhena:

# LangSmith (Observability)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=pilotpros-milhena
LANGCHAIN_API_KEY=<your-key>

# Performance
MILHENA_MAX_RETRIES=3
MILHENA_CONNECTION_POOL_SIZE=5
```

---

## 🔧 Implementation Plan

### Phase 1: Core Infrastructure (Week 1)

#### 1.1 Upgrade Dependencies

```bash
cd intelligence-engine
pip install --upgrade langgraph==0.6.7
pip install langgraph-checkpoint-postgres==2.0.11
pip install langsmith==0.3.0
pip freeze > requirements.txt
```

#### 1.2 Create Directory Structure

```bash
mkdir -p app/core
mkdir -p app/system_agents/milhena
mkdir -p app/customer_agents
touch app/core/__init__.py
touch app/core/registry.py
touch app/core/db_access.py
touch app/core/business_masking.py
touch app/system_agents/__init__.py
touch app/system_agents/milhena/__init__.py
touch app/system_agents/milhena/orchestrator.py
touch app/system_agents/milhena/agents.py
touch app/system_agents/milhena/tools.py
touch app/customer_agents/.gitkeep
```

#### 1.3 Create DB Read-Only User

Execute SQL script in PostgreSQL (see above).

### Phase 2: Core Components (Week 2)

#### 2.1 Business Masking Library (`app/core/business_masking.py`)

**Key Requirements**:
- Deterministic translation (dictionary-based)
- Zero LLM calls
- Validation to prevent tech leaks
- Unit testable

**Tech → Business Dictionary**:
```python
TECH_TO_BUSINESS = {
    'workflow': 'Business Process',
    'execution': 'Process Run',
    'n8n': 'Automation System',
    'node': 'Process Step',
    'webhook': 'Integration Point',
    'postgres': 'Data Storage',
    'redis': 'Performance Cache',
    'failed': 'Requires Attention',
    'success': 'Completed Successfully',
    # ... 50+ mappings
}
```

#### 2.2 Secure DB Access (`app/core/db_access.py`)

**Features**:
- Connection pooling (max 5)
- Read-only user enforcement
- Query timeout (5s)
- Prepared statements only
- Audit logging

**Pattern**:
```python
class SecureDBAccess:
    def __init__(self):
        self.pool = create_pool(
            user='pilotpros_agent_ro',  # READ-ONLY
            max_size=5,
            timeout=5
        )

    def query(self, sql: str, params: tuple) -> List[Dict]:
        # Validate SELECT only
        # Execute with timeout
        # Log audit trail
        pass
```

#### 2.3 Agent Registry (`app/core/registry.py`)

**Purpose**: Universal registration system per system/customer agents.

```python
class AgentRegistry:
    def register_system_agent(name, agent_class):
        # Full privileges
        pass

    def register_customer_agent(name, agent_class):
        # Sandboxed
        pass
```

### Phase 3: Milhena Agents (Week 3)

#### 3.1 Classifier Agent

- **Model**: `gpt-4o-mini` (fast, cheap)
- **Temperature**: 0 (deterministic)
- **Output**: One of 4 categories
- **No tools**: Pure classification

#### 3.2 Data Analyst Agent

- **Model**: `gpt-4o-mini`
- **Temperature**: 0
- **Tools**: `BusinessIntelligentQueryTool` (mandatory)
- **Cache**: Redis 60s TTL
- **Rule**: MUST use tool, cannot invent data

#### 3.3 Validator Agent

- **Model**: `gpt-4o-mini`
- **Temperature**: 0
- **No tools**: Pure validation logic
- **Rules**:
  - Remove speculative statements
  - Flag inconsistencies
  - Return only verifiable facts

### Phase 4: Tools & Integration (Week 4)

#### 4.1 BusinessIntelligentQueryTool

**Capabilities**:
- Pre-defined safe queries
- Anti-hallucination keywords blocking
- Redis caching
- Connection pooling

**Anti-Hallucination Features**:
```python
FORBIDDEN_KEYWORDS = [
    'fatturato',  # No financial speculation
    'clienti',    # No customer count guesses
    'previsione', # No predictions
    # ... extensive list
]
```

#### 4.2 LangGraph Orchestrator

**State Schema** (TypedDict):
```python
class MilhenaState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    classification: str
    raw_data: Dict
    validated_data: Dict
    masked_response: str
    errors: List[str]
```

**Graph Structure**:
```python
workflow = StateGraph(MilhenaState)
workflow.add_node("classify", classifier_agent)
workflow.add_node("analyze", data_analyst_agent)
workflow.add_node("validate", validator_agent)
workflow.add_node("mask", business_masking_function)  # Not an agent!

# Conditional routing
workflow.add_conditional_edges(
    "classify",
    route_classification,
    {
        "BUSINESS_DATA": "analyze",
        "HELP": END,
        "GREETING": END,
        "TECHNOLOGY": END
    }
)
```

### Phase 5: Testing & Validation (Week 5)

#### 5.1 Unit Tests

```bash
pytest tests/core/test_business_masking.py  # 100% coverage
pytest tests/core/test_db_access.py
pytest tests/milhena/test_agents.py
```

#### 5.2 Integration Tests

```bash
pytest tests/integration/test_milhena_e2e.py
```

#### 5.3 Load Tests

```bash
locust -f tests/load/milhena_load.py --users 100
```

---

## ✅ Best Practices & Patterns

### LangGraph 2025 Best Practices

#### 1. **Durable Execution** (LangGraph 0.6.7)

```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver(connection_string)
app = workflow.compile(checkpointer=checkpointer)

# Automatically resumes from failures
```

#### 2. **State Management**

- Use `TypedDict` for type safety
- Use `Annotated` with reducers for list fields
- Keep state immutable
- Avoid nested state (flat is better)

#### 3. **Error Handling**

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def query_with_retry():
    pass
```

#### 4. **Observability with LangSmith**

```python
from langsmith import traceable

@traceable(name="milhena_classify")
def classify(state):
    # Automatically traced
    pass
```

#### 5. **Connection Pooling**

```python
# DON'T: Create new connection per query
conn = psycopg2.connect(...)  # ❌

# DO: Use connection pool
from psycopg2.pool import ThreadedConnectionPool
pool = ThreadedConnectionPool(minconn=1, maxconn=5, ...)  # ✅
```

### Security Best Practices

#### 1. **Read-Only DB User**

✅ Dedicated user with SELECT only
❌ Never use admin user

#### 2. **Prepared Statements**

```python
# DON'T
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # ❌ SQL Injection!

# DO
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))  # ✅ Safe
```

#### 3. **Secrets Management**

```python
# DON'T
DB_PASSWORD = "hardcoded_password"  # ❌

# DO (Production)
from google.cloud import secretmanager  # ✅
# or AWS Secrets Manager, HashiCorp Vault
```

### Performance Best Practices

#### 1. **Redis Caching**

```python
@redis_cache(ttl=60, key_prefix="milhena:")
def expensive_query():
    pass
```

#### 2. **Query Optimization**

- Use indexes (already 49 in pilotpros schema)
- Limit results (LIMIT 100 default)
- Avoid SELECT *
- Use EXPLAIN ANALYZE for slow queries

#### 3. **Async Where Possible**

```python
# For I/O-bound operations
import asyncio
results = await asyncio.gather(*tasks)
```

---

## ⚠️ Anti-Patterns to Avoid

### 1. **Making Masking an Agent**

```python
# ❌ DON'T - Variable output, possible hallucinations
class MaskingAgent:
    def run(self, state):
        return llm.invoke("Translate to business language...")

# ✅ DO - Deterministic, guaranteed consistency
def mask_response(data: dict) -> dict:
    return {k: TECH_TO_BUSINESS.get(k, k) for k in data}
```

### 2. **Over 5 Agents in Pipeline**

📊 Research shows 75% of systems with >5 agents become unmaintainable.

**Milhena**: 3 agents + 1 library = Perfect balance ✅

### 3. **Nested State**

```python
# ❌ DON'T
class State(TypedDict):
    data: Dict[str, Dict[str, List[Dict]]]  # Too nested!

# ✅ DO
class State(TypedDict):
    users: List[User]  # Flat
    metrics: Metrics   # Flat
```

### 4. **Synchronous DB in Async Context**

```python
# ❌ DON'T
async def handler():
    result = psycopg2_sync_query()  # Blocks event loop!

# ✅ DO
async def handler():
    result = await asyncpg_query()  # Non-blocking
```

### 5. **Missing Timeout**

```python
# ❌ DON'T
conn.execute(query)  # Could hang forever

# ✅ DO
conn.execute("SET statement_timeout = 5000")  # 5s timeout
conn.execute(query)
```

---

## 🧪 Testing Strategy

### Unit Tests (Target: 100% Coverage)

```python
# tests/core/test_business_masking.py
def test_mask_workflow_term():
    assert mask_term('workflow') == 'Business Process'

def test_no_tech_leak():
    response = mask_response(data)
    assert 'postgres' not in response
    assert 'n8n' not in response

# tests/core/test_db_access.py
def test_read_only_enforcement():
    with pytest.raises(PermissionError):
        db.execute("DELETE FROM users")

def test_query_timeout():
    with pytest.raises(TimeoutError):
        db.execute("SELECT pg_sleep(10)")
```

### Integration Tests

```python
# tests/integration/test_milhena_e2e.py
async def test_full_pipeline():
    state = {
        "messages": [HumanMessage("How many users?")]
    }
    result = await app.ainvoke(state)
    assert 'users' not in result['masked_response'].lower()
    assert 'team members' in result['masked_response'].lower()
```

### Load Tests

```bash
# Target: 100 concurrent users, <500ms p95
locust -f tests/load/milhena_load.py \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --host http://localhost:8000
```

**Acceptance Criteria**:
- ✅ p50 < 200ms
- ✅ p95 < 500ms
- ✅ p99 < 1000ms
- ✅ Error rate < 0.1%

---

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] All tests passing (unit + integration + load)
- [ ] Code review completed
- [ ] Security audit passed
- [ ] Performance benchmarks met
- [ ] Documentation updated

### Database Setup

- [ ] Read-only user created (`pilotpros_agent_ro`)
- [ ] Permissions verified
- [ ] Connection pooling tested
- [ ] Backup strategy confirmed

### Dependencies

- [ ] LangGraph upgraded to 0.6.7
- [ ] All requirements.txt updated
- [ ] No conflicting versions
- [ ] Development vs production deps separated

### Configuration

- [ ] Environment variables set
- [ ] Secrets in vault (not .env)
- [ ] Logging level appropriate (INFO in prod)
- [ ] Monitoring enabled

### Observability

- [ ] LangSmith integration working
- [ ] Prometheus metrics exposed
- [ ] Grafana dashboards created
- [ ] Alerts configured

### Rollout

- [ ] Canary deployment (5% traffic)
- [ ] Monitor for 24h
- [ ] Gradual rollout (25% → 50% → 100%)
- [ ] Rollback plan tested

---

## 📊 Success Metrics (KPIs)

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Response Time (p95)** | <500ms | TBD | 🟡 |
| **Uptime** | 99.9% | TBD | 🟡 |
| **Error Rate** | <0.1% | TBD | 🟡 |
| **Cache Hit Rate** | >80% | TBD | 🟡 |
| **Zero Hallucinations** | 100% | TBD | 🟡 |
| **Tech Term Leaks** | 0 | TBD | 🟡 |

---

## 🚀 Next Steps

1. ✅ **Review this document** with team
2. ⏳ **Create `system-agent` branch**
3. ⏳ **Phase 1: Upgrade dependencies**
4. ⏳ **Phase 2: Implement core components**
5. ⏳ **Phase 3: Build Milhena agents**
6. ⏳ **Phase 4: Testing & validation**
7. ⏳ **Phase 5: Production deployment**

---

## 📚 References

- [LangGraph Official Docs](https://langchain-ai.github.io/langgraph/)
- [LangSmith Observability](https://smith.langchain.com/)
- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Don%27t_Do_This)
- [FastAPI Performance Tips](https://fastapi.tiangolo.com/deployment/)
- [Redis Caching Strategies](https://redis.io/docs/manual/patterns/)

---

**Document Owner**: PilotProOS Intelligence Team
**Last Review**: 2025-09-27
**Next Review**: Weekly during implementation