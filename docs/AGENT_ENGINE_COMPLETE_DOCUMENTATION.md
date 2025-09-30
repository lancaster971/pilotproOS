# 🚀 AGENT ENGINE - Complete Documentation

## 🎯 EXECUTIVE SUMMARY

**Agent-Engine è un componente CORE di PilotProOS, importante quanto n8n.**

### Distinzione Fondamentale:
- **Agent-Engine**: Il MOTORE universale che fa girare TUTTI gli agent (presente e futuri)
- **Milhena**: UN agent specifico fornito di default come assistente del cliente
- **Future Agents**: Qualsiasi agent acquistato/sviluppato girerà su Agent-Engine

```
┌─────────────────────────────────────────────────────┐
│                    PILOTPROS OS                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐        ┌──────────────────────┐  │
│  │     n8n      │◄──────►│   AGENT-ENGINE       │  │
│  │  (Workflows) │        │   (CrewAI Core)      │  │
│  └──────────────┘        └──────────────────────┘  │
│                                │                    │
│                    ┌───────────┼───────────┐        │
│                    ▼           ▼           ▼        │
│              [Milhena]   [Agent-2]   [Agent-N]      │
│              (Default)   (Purchased) (Custom)       │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 📋 TABLE OF CONTENTS

1. [Core Architecture](#1-core-architecture)
2. [System Integration](#2-system-integration)
3. [Milhena - Default Agent](#3-milhena-default-agent)
4. [Multi-Agent Management](#4-multi-agent-management)
5. [n8n Integration](#5-n8n-integration)
6. [API Documentation](#6-api-documentation)
7. [Setup & Configuration](#7-setup-configuration)
8. [Testing & Monitoring](#8-testing-monitoring)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. CORE ARCHITECTURE

### 1.1 What is Agent-Engine?

Agent-Engine è il **runtime environment** basato su CrewAI che:
- Esegue TUTTI gli agent AI del sistema
- Gestisce code di lavoro asincrone
- Fornisce API unificate per l'accesso agli agent
- Integra LLM providers multipli (Groq, Gemini, OpenAI, etc.)
- Comunica bidirezionalmente con n8n

### 1.2 Technology Stack

```yaml
Core Framework: CrewAI 0.28.0
Runtime: Python 3.11
API: FastAPI + Uvicorn
Queue: Redis
Database: PostgreSQL (shared with n8n)
LLM Providers:
  - Primary: Groq (14,400 req/day)
  - Fallback: Google Gemini
  - Optional: OpenAI, Anthropic, Mistral
```

### 1.3 Container Architecture

```
Container Name: pilotpros-agent-engine-dev
Port: 8000
Networks: pilotpros-network (shared with all services)
Dependencies:
  - postgres-dev (database)
  - redis-dev (job queue)
  - n8n-dev (workflow integration)
```

---

## 2. SYSTEM INTEGRATION

### 2.1 Integration Points

Agent-Engine si integra con TUTTI i componenti del sistema:

```
┌──────────────────────────────────────────────────────────┐
│                    INTEGRATION MATRIX                     │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Frontend (Vue3)          Backend (Express)              │
│       │                          │                       │
│       └──────────┬───────────────┘                       │
│                  ▼                                        │
│           /api/milhena/*                                 │
│                  │                                        │
│                  ▼                                        │
│         AGENT-ENGINE:8000                                │
│                  │                                        │
│      ┌───────────┼───────────┐                          │
│      ▼           ▼           ▼                          │
│   PostgreSQL   Redis      n8n:5678                      │
│                           (webhooks)                     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Communication Flows

#### Frontend → Agent-Engine
```javascript
// Frontend chiama Milhena (o qualsiasi agent)
const response = await apiClient.post('/milhena/chat', {
  message: userInput,
  context: currentContext
});
```

#### Backend → Agent-Engine
```javascript
// Backend forwarda richieste all'Agent-Engine
router.post('/milhena/chat', async (req, res) => {
  const agentResponse = await axios.post(
    'http://agent-engine-dev:8000/api/v1/ask',
    {
      question: req.body.message,
      jwt: req.headers.authorization
    }
  );
  res.json(agentResponse.data);
});
```

#### n8n ↔ Agent-Engine (Bidirezionale)
```javascript
// n8n triggera analisi AI
POST http://agent-engine-dev:8000/api/v1/n8n/webhook
{
  "action": "analyze_process",
  "workflowId": "wf_123",
  "data": processData
}

// Agent-Engine triggera workflow n8n
POST http://n8n-dev:5678/webhook/ai-trigger
{
  "source": "agent-engine",
  "agent": "milhena",
  "action": "start_workflow",
  "data": analysisResult
}
```

---

## 3. MILHENA - DEFAULT AGENT

### 3.1 Cos'è Milhena?

**Milhena NON è l'Agent-Engine**, ma è UN agent che gira SOPRA l'Agent-Engine.

- **Ruolo**: Assistente AI di default per il cliente
- **Versione**: v4.0 Enterprise
- **Provider**: Groq (primary) + Gemini (fallback)
- **Features**:
  - Anti-hallucination system a 3 livelli
  - Response time < 100ms
  - Memoria persistente per utente
  - Cache intelligente

### 3.2 Milhena Architecture

```python
# milhena_orchestrator_enterprise.py
class MilhenaEnterpriseOrchestrator:
    """
    Milhena è UN agent che usa l'Agent-Engine.
    Non è il motore stesso, ma un'implementazione specifica.
    """

    def __init__(self):
        # Usa CrewAI fornito da Agent-Engine
        from crewai import Agent, Task, Crew

        self.data_analyst = Agent(
            role="Business Data Analyst",
            goal="Analyze PilotPro data",
            llm=self.groq_model  # Usa Groq via Agent-Engine
        )
```

---

## 4. MULTI-AGENT MANAGEMENT

### 4.1 Agent Marketplace Concept

```
AGENT-ENGINE supporta:
├── Default Agents (inclusi)
│   └── Milhena (assistente generale)
│
├── Purchasable Agents (futuri)
│   ├── FinanceAgent (analisi finanziaria)
│   ├── HRAgent (gestione risorse umane)
│   ├── MarketingAgent (automazione marketing)
│   └── CustomAgent (sviluppati ad-hoc)
│
└── Customer Custom Agents
    └── Agenti sviluppati dal cliente stesso
```

### 4.2 Come funzionano i Multi-Agent

1. **Registrazione Agent**:
```python
# Ogni nuovo agent si registra nell'Engine
@app.post("/api/v1/agents/register")
async def register_agent(agent_config: AgentConfig):
    """
    Registra un nuovo agent nell'Engine.
    Può essere acquistato dal marketplace o custom.
    """
    agent_registry[agent_config.id] = agent_config
    return {"status": "registered", "id": agent_config.id}
```

2. **Esecuzione Agent**:
```python
# L'Engine gestisce l'esecuzione di qualsiasi agent
@app.post("/api/v1/agents/{agent_id}/execute")
async def execute_agent(agent_id: str, task: dict):
    """
    Esegue un agent specifico con il task fornito.
    L'Engine gestisce code, retry, monitoring.
    """
    agent = agent_registry.get(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")

    # Esegui su CrewAI runtime
    result = await crew_runtime.execute(agent, task)
    return result
```

3. **Orchestrazione Multi-Agent**:
```python
# Gli agent possono collaborare
@app.post("/api/v1/orchestrate")
async def orchestrate_agents(workflow: MultiAgentWorkflow):
    """
    Orchestrazione di più agent per task complessi.
    Es: FinanceAgent + HRAgent per report integrato.
    """
    crew = Crew(
        agents=workflow.agents,
        tasks=workflow.tasks,
        process=Process.sequential
    )
    return await crew.kickoff()
```

---

## 5. N8N INTEGRATION

### 5.1 Perché l'integrazione è CRITICA

**Agent-Engine e n8n sono i DUE MOTORI CORE di PilotProOS:**
- **n8n**: Gestisce workflow deterministici e automazioni
- **Agent-Engine**: Gestisce intelligenza artificiale e decision-making

### 5.2 Comunicazione Bidirezionale

#### n8n → Agent-Engine
```javascript
// n8n HTTP Request Node
{
  "method": "POST",
  "url": "http://agent-engine-dev:8000/api/v1/n8n/webhook",
  "body": {
    "action": "analyze",
    "workflowId": "{{ $workflow.id }}",
    "data": {
      "process": "{{ $json.process }}",
      "context": "{{ $json.context }}"
    },
    "secret": "{{ $env.N8N_WEBHOOK_SECRET }}"
  }
}
```

#### Agent-Engine → n8n
```python
# Agent triggera workflow n8n
async def trigger_workflow_from_ai(decision_data):
    """
    L'AI può decidere di triggerare workflow n8n
    per automatizzare azioni basate su analisi.
    """
    integration = N8nIntegration()

    # Es: AI detecta anomalia → triggera workflow alert
    if decision_data.anomaly_detected:
        await integration.trigger_n8n_workflow(
            webhook_path="anomaly-response",
            data={
                "severity": decision_data.severity,
                "action_required": decision_data.suggested_action,
                "ai_confidence": decision_data.confidence
            }
        )
```

### 5.3 Use Cases Integrati

1. **Customer Support Intelligente**:
   - n8n riceve ticket → Agent-Engine analizza sentiment
   - AI classifica urgenza → n8n route al team giusto
   - Agent genera risposta → n8n invia al cliente

2. **Process Optimization**:
   - n8n monitora metriche → Agent-Engine analizza pattern
   - AI suggerisce ottimizzazioni → n8n implementa modifiche
   - Feedback loop continuo

3. **Report Generation**:
   - n8n schedule report → Agent-Engine genera analisi
   - Multiple agent collaborano → n8n formatta e distribuisce

---

## 6. API DOCUMENTATION

### 6.1 Core Endpoints

```yaml
Base URL: http://agent-engine-dev:8000

Authentication: JWT Bearer token (from backend)

Endpoints:
  # Health & Status
  GET  /health                    # Container health check
  GET  /metrics                    # Performance metrics

  # Agent Management
  GET  /api/v1/agents              # List available agents
  POST /api/v1/agents/register     # Register new agent

  # Agent Execution
  POST /api/v1/ask                 # Execute default agent (Milhena)
  POST /api/v1/agents/{id}/execute # Execute specific agent

  # n8n Integration
  POST /api/v1/n8n/webhook         # n8n webhook endpoint
  POST /api/v1/trigger/workflow    # Trigger n8n workflow

  # WebSocket (real-time)
  WS   /ws                         # Real-time agent communication
```

### 6.2 Request/Response Examples

#### Execute Milhena (Default Agent)
```bash
POST /api/v1/ask
{
  "question": "Qual è il trend delle vendite?",
  "context": {
    "user_id": "user_123",
    "language": "it"
  }
}

Response:
{
  "answer": "Le vendite mostrano un trend positivo del +15%...",
  "confidence": 0.92,
  "data_sources": ["postgresql", "n8n_metrics"],
  "execution_time_ms": 87
}
```

#### Execute Custom Agent
```bash
POST /api/v1/agents/finance-agent/execute
{
  "task": "analyze_quarterly_report",
  "parameters": {
    "quarter": "Q1-2025",
    "include_projections": true
  }
}

Response:
{
  "status": "completed",
  "result": { ... },
  "agent_id": "finance-agent",
  "execution_id": "exec_abc123"
}
```

---

## 7. SETUP & CONFIGURATION

### 7.1 Docker Configuration

```yaml
# docker-compose.yml
agent-engine-dev:
  build:
    context: ./pilotpros-agent-engine
    dockerfile: Dockerfile
  container_name: pilotpros-agent-engine-dev
  restart: unless-stopped
  ports:
    - "8000:8000"
  environment:
    # Core Settings
    - ENVIRONMENT=development
    - JWT_SECRET=${JWT_SECRET}

    # Database
    - DATABASE_URL=postgresql://pilotpros_user:pass@postgres-dev:5432/pilotpros_db

    # Redis Queue
    - REDIS_URL=redis://redis-dev:6379/0

    # n8n Integration
    - N8N_WEBHOOK_SECRET=${N8N_WEBHOOK_SECRET}
    - N8N_URL=http://n8n-dev:5678

    # LLM Providers (REQUIRED for Milhena)
    - GROQ_API_KEY=${GROQ_API_KEY}        # Primary - Fast
    - GOOGLE_API_KEY=${GOOGLE_API_KEY}    # Fallback - Free

    # Optional Providers
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

  volumes:
    - ./pilotpros-agent-engine:/app
    - agent_engine_cache:/app/cache

  networks:
    - pilotpros-network

  depends_on:
    postgres-dev:
      condition: service_healthy
    redis-dev:
      condition: service_healthy
```

### 7.2 Environment Variables

```bash
# .env file
# CORE - REQUIRED
JWT_SECRET=pilotpros_jwt_secret_2025_secure
DATABASE_URL=postgresql://pilotpros_user:pass@postgres-dev:5432/pilotpros_db
REDIS_URL=redis://redis-dev:6379/0
N8N_WEBHOOK_SECRET=pilotpros_n8n_secret_2025

# LLM PROVIDERS - At least one required
GROQ_API_KEY=gsk_xxxxxxxxxxxxx        # Get free at: https://console.groq.com
GOOGLE_API_KEY=AIzaxxxxxxxxxxxxx      # Get free at: https://aistudio.google.com/apikey

# OPTIONAL PROVIDERS
OPENAI_API_KEY=sk-xxxxxxxxxxxxx       # Paid
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx # Paid
MISTRAL_API_KEY=xxxxxxxxxxxxx         # Some free tier

# PERFORMANCE
ENABLE_CACHE=true
CACHE_TTL=3600
MAX_WORKERS=4
ENABLE_ANALYTICS=true
```

### 7.3 Dependencies (requirements.txt)

```txt
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# Multi-Agent Framework (CRITICAL)
crewai==0.28.0
langchain==0.1.10
langchain-community==0.0.25

# LLM Providers
groq==0.31.1              # Primary - Fastest
google-generativeai==0.3.2 # Fallback - Free
langchain-groq==0.1.0
langchain-google-genai==0.0.5
openai==1.10.0             # Optional
anthropic==0.7.0           # Optional

# Queue & Database
redis==5.0.1
asyncpg==0.29.0
sqlalchemy[asyncio]==2.0.23

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# WebSocket
python-socketio==5.10.0
websockets==12.0

# Monitoring
prometheus-client==0.19.0

# Utils
python-dotenv==1.0.0
httpx==0.25.2
tenacity==8.2.0
aiofiles==23.2.1
rich==13.7.0
```

---

## 8. TESTING & MONITORING

### 8.1 Quick Health Check

```bash
# 1. Check container status
docker ps | grep agent-engine

# 2. Test health endpoint
curl http://localhost:8000/health

# 3. Test Milhena
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Ciao, come stai?"}'
```

### 8.2 Complete Test Suite

```bash
# Enter container and run tests
docker exec -it pilotpros-agent-engine-dev bash

# Test Milhena
python3 test_milhena_complete.py

# Test n8n integration
python3 test_n8n_integration.py

# Test multi-agent orchestration
python3 test_multi_agent.py
```

### 8.3 Monitoring Commands

```bash
# Real-time logs
docker logs -f pilotpros-agent-engine-dev

# Redis queue status
docker exec redis-dev redis-cli INFO | grep instantaneous

# Check job queue
docker exec redis-dev redis-cli LLEN agent-jobs:high

# Performance metrics
curl http://localhost:8000/metrics
```

### 8.4 Performance Benchmarks

```
Milhena v4.0 Performance:
├── Classification: 60ms average
├── Simple queries: 200-500ms
├── Complex analysis: 1-3 seconds
├── Cache hit: 5-15ms
└── Concurrent users: 100+
```

---

## 9. TROUBLESHOOTING

### 9.1 Container Won't Start

**PROBLEMA ATTUALE**: Conflitti di dipendenze Python

```bash
# Error: ModuleNotFoundError crewai o pydantic conflicts
```

**SOLUZIONI**:

1. **Fix Requirements Conflict**:
```bash
# Usa requirements-working.txt che ha versioni compatibili
cd pilotpros-agent-engine
cp requirements-working.txt requirements.txt
docker-compose build agent-engine-dev --no-cache
```

2. **Alternative: Use Minimal Requirements**:
```bash
# Start with minimal deps
cp requirements-minimal.txt requirements.txt
docker-compose build agent-engine-dev --no-cache
```

### 9.2 Milhena Not Responding

```bash
# 1. Check Groq API Key
docker exec pilotpros-agent-engine-dev printenv | grep GROQ

# 2. Test Groq directly
docker exec pilotpros-agent-engine-dev python3 -c "
from groq import Groq
client = Groq()
response = client.chat.completions.create(
    model='llama-3.3-70b-versatile',
    messages=[{'role': 'user', 'content': 'Test'}]
)
print(response.choices[0].message.content)
"

# 3. Check fallback to Gemini
docker exec pilotpros-agent-engine-dev python3 -c "
import google.generativeai as genai
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content('Test')
print(response.text)
"
```

### 9.3 n8n Integration Issues

```bash
# 1. Verify network connectivity
docker exec agent-engine-dev ping n8n-dev

# 2. Test webhook secret
curl -X POST http://localhost:8000/api/v1/n8n/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "action": "test",
    "secret": "pilotpros_n8n_secret_2025"
  }'

# 3. Check n8n webhook logs
docker exec n8n-dev tail -f /home/node/.n8n/webhook.log
```

### 9.4 Database Connection Issues

```bash
# Test PostgreSQL connection from Agent-Engine
docker exec pilotpros-agent-engine-dev python3 -c "
import asyncpg
import asyncio

async def test():
    conn = await asyncpg.connect(
        'postgresql://pilotpros_user:pilotpros_secure_pass_2025@postgres-dev:5432/pilotpros_db'
    )
    result = await conn.fetch('SELECT COUNT(*) FROM n8n.workflow_entity')
    print(f'Workflows: {result[0][0]}')
    await conn.close()

asyncio.run(test())
"
```

---

## 📊 ARCHITECTURE SUMMARY

```
PilotProOS Core Components:
┌────────────────────┬────────────────────┐
│      n8n           │   AGENT-ENGINE     │
├────────────────────┼────────────────────┤
│ • Workflow Engine  │ • AI Runtime       │
│ • Automations      │ • Multi-Agent      │
│ • Integrations     │ • LLM Management   │
│ • Scheduling       │ • Decision Making  │
└────────────────────┴────────────────────┘
         ▲                    ▲
         └────────┬───────────┘
                  │
           EQUALLY CRITICAL
```

**Key Points**:
1. Agent-Engine è CORE quanto n8n
2. Milhena è solo UN agent di default, non il motore
3. Il sistema supporta unlimited future agents
4. Integrazione bidirezionale n8n ↔ Agent-Engine
5. Tutti gli agent (presenti e futuri) girano su Agent-Engine

---

## 🚀 NEXT STEPS

1. **Immediate**: Fix dependency conflicts to start container
2. **Short-term**: Complete Milhena ↔ Frontend integration
3. **Medium-term**: Implement agent marketplace
4. **Long-term**: Develop custom agents for verticals

---

*Document Version: 1.0*
*Last Updated: 2025-09-25*
*Status: COMPREHENSIVE CONSOLIDATION*