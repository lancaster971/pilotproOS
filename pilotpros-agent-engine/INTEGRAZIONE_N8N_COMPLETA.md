# 🔗 INTEGRAZIONE COMPLETA: Agent Engine ↔ n8n

## 🏗️ ARCHITETTURA BIDIREZIONALE

```
┌──────────────────────────────┐         ┌──────────────────────────────┐
│      PILOTPROS CORE          │         │      AGENT ENGINE            │
│                              │         │                              │
│  ┌────────────────────────┐  │         │  ┌────────────────────────┐  │
│  │        n8n             │  │◄────────►  │   CrewAI Agents        │  │
│  │  Workflow Engine       │  │ WEBHOOK │  │   Multi-Model AI       │  │
│  └────────────────────────┘  │         │  └────────────────────────┘  │
│           │                  │         │           │                  │
│           ▼                  │         │           ▼                  │
│  ┌────────────────────────┐  │         │  ┌────────────────────────┐  │
│  │     Backend API        │  │◄────────►  │    FastAPI             │  │
│  │   Express (3001)       │  │  HTTP   │  │    Port 8000           │  │
│  └────────────────────────┘  │         │  └────────────────────────┘  │
│           │                  │         │           │                  │
│           ▼                  │         │           ▼                  │
│  ┌────────────────────────┐  │         │  ┌────────────────────────┐  │
│  │    PostgreSQL          │  │◄────────►  │     Redis Queue        │  │
│  │  Dual Schema DB        │  │         │  │   Job Processing       │  │
│  └────────────────────────┘  │         │  └────────────────────────┘  │
└──────────────────────────────┘         └──────────────────────────────┘
```

## 📡 FLUSSI DI COMUNICAZIONE

### 1️⃣ **n8n → Agent Engine** (n8n chiede analisi AI)

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
    "secret": "pilotpros_n8n_secret_2025"
  }
}
```

**Agent Engine riceve e processa:**
```python
# agent-engine/api.py
@app.post("/api/v1/n8n/webhook")
async def n8n_webhook(request: N8nRequest):
    if request.action == "analyze":
        # Usa CrewAI per analisi
        agents = BusinessAnalysisAgents()
        result = agents.analyze_business(
            request.data.process,
            request.data.context
        )
        return result
```

### 2️⃣ **Agent Engine → n8n** (AI triggera workflow)

```python
# Agent Engine triggera workflow n8n
async def trigger_workflow_from_ai():
    # L'AI decide di triggerare un workflow
    integration = N8nIntegration()

    result = await integration.trigger_n8n_workflow(
        webhook_path="customer-onboarding",
        data={
            "customer_name": "Acme Corp",
            "ai_analysis": "Cliente high-value, applicare fast-track",
            "priority": "high"
        }
    )
```

**n8n Webhook Node riceve:**
```javascript
// n8n Webhook Node configurato su path: customer-onboarding
{
  "customer_name": "Acme Corp",
  "ai_analysis": "Cliente high-value, applicare fast-track",
  "priority": "high",
  "source": "agent-engine",
  "timestamp": "2025-09-24T..."
}
// → Workflow processa automaticamente
```

### 3️⃣ **Backend ↔ Agent Engine** (Via API)

```javascript
// Backend chiama Agent Engine
const axios = require('axios');

async function askAI(question) {
  const response = await axios.post('http://agent-engine-dev:8000/api/v1/assistant', {
    question: question,
    language: 'italian',
    jwt: req.headers.authorization
  });

  return response.data;
}
```

## 🔧 SETUP INTEGRAZIONE

### 1. Configura Network Docker
```yaml
# docker-compose.yml
networks:
  pilotpros-network:
    name: pilotpros-network
    driver: bridge

services:
  n8n-dev:
    networks:
      - pilotpros-network

  agent-engine-dev:
    networks:
      - pilotpros-network
```

### 2. Aggiungi Webhook in n8n
1. Apri n8n: http://localhost:5678
2. Crea nuovo workflow
3. Aggiungi **Webhook Node**:
   - Path: `ai-analysis`
   - Method: POST
   - Response Mode: Last Node

4. Aggiungi **HTTP Request Node** per chiamare Agent Engine:
   - URL: `http://agent-engine-dev:8000/api/v1/assistant`
   - Method: POST
   - Body:
   ```json
   {
     "question": "{{ $json.question }}",
     "context": "{{ $json }}",
     "language": "italian"
   }
   ```

### 3. Configura Agent Engine Endpoints
```python
# Aggiungi in agent-engine/api.py
@app.post("/api/v1/n8n/webhook")
async def handle_n8n_webhook(
    action: str,
    workflowId: str,
    data: dict,
    secret: str
):
    # Valida secret
    if secret != os.getenv("N8N_WEBHOOK_SECRET"):
        raise HTTPException(401)

    # Processa in base all'azione
    if action == "analyze":
        return await analyze_with_agents(data)
    elif action == "generate_report":
        return await generate_report(data)
    # etc...
```

## 📋 ESEMPI PRATICI

### Esempio 1: Analisi Ordini con AI
```javascript
// n8n Workflow: Analisi Ordini
1. Trigger: Nuovo ordine ricevuto
2. HTTP Request → Agent Engine:
   {
     "action": "analyze_order",
     "data": {
       "order_id": "ORD-2025-001",
       "amount": 25000,
       "customer": "Acme Corp"
     }
   }
3. Agent Engine risponde con analisi
4. n8n processa in base all'analisi:
   - Se high-risk → workflow approvazione
   - Se normal → workflow standard
   - Se VIP → workflow express
```

### Esempio 2: Report Automatici
```python
# Agent Engine genera report e triggera invio
async def generate_monthly_report():
    # 1. Genera report con AI
    report = await create_report_with_agents()

    # 2. Triggera workflow n8n per invio
    await trigger_n8n_workflow(
        "send-report",
        {
            "report": report,
            "recipients": ["management@company.com"],
            "format": "pdf"
        }
    )
```

### Esempio 3: Customer Support Intelligente
```javascript
// n8n riceve ticket support
1. Webhook riceve ticket
2. Chiama Agent Engine per analisi sentiment e urgenza
3. Agent Engine risponde:
   {
     "sentiment": "negative",
     "urgency": "high",
     "suggested_action": "escalate_to_manager",
     "auto_response": "Ci scusiamo per il disagio..."
   }
4. n8n processa in base alla risposta AI
```

## 🚀 COMANDI RAPIDI

### Test Integrazione
```bash
# 1. Test n8n → Agent Engine
curl -X POST http://localhost:5678/webhook/test-ai \
  -H "Content-Type: application/json" \
  -d '{"question": "Test integrazione"}'

# 2. Test Agent Engine → n8n
docker exec pilotpros-agent-engine-dev python -c "
from n8n_integration import N8nIntegration
import asyncio

async def test():
    integration = N8nIntegration()
    result = await integration.trigger_n8n_workflow(
        'test-webhook',
        {'message': 'Test from AI'}
    )
    print(result)

asyncio.run(test())
"

# 3. Monitor logs
docker logs -f pilotpros-n8n
docker logs -f pilotpros-agent-engine-dev
```

## ✅ CHECKLIST INTEGRAZIONE

- [ ] Network Docker condiviso configurato
- [ ] Webhook secret configurato in entrambi i sistemi
- [ ] n8n webhooks creati per ricevere da AI
- [ ] Agent Engine endpoints per ricevere da n8n
- [ ] Test bidirezionale funzionante
- [ ] Logs e monitoring attivi
- [ ] Error handling implementato
- [ ] Rate limiting configurato

## 🔐 SICUREZZA

1. **Webhook Secret**: Sempre validare il secret
2. **Network Isolation**: Container comunicano solo via network interno
3. **Rate Limiting**: Limita chiamate per evitare loop
4. **Validation**: Valida sempre i dati in input
5. **Timeout**: Configura timeout per evitare hanging

## 📊 MONITORING

```bash
# Dashboard real-time
watch -n 2 'docker exec redis-dev redis-cli INFO | grep instantaneous'

# Queue status
docker exec redis-dev redis-cli LLEN agent-engine-jobs:high

# Webhook calls
docker exec pilotpros-n8n tail -f /home/node/.n8n/logs/webhook.log
```