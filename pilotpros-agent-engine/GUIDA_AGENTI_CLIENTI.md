# 🚀 GUIDA: Creare Agenti AI per Clienti

## 📦 COME FUNZIONA IL SISTEMA

### Architettura Container
```
pilotpros-agent-engine-dev (Docker Container)
├── /app/crews/              # I tuoi agenti vanno qui
│   ├── client_xxx_crew.py   # Agent per cliente XXX
│   ├── client_yyy_crew.py   # Agent per cliente YYY
│   └── ...
├── /app/api.py              # API FastAPI
├── /app/worker.py           # Worker che processa i job
└── /app/cli.py              # CLI per testare
```

## 🎯 STEP 1: CREA L'AGENT PER IL CLIENTE

### Template Base Agent
```python
# File: /app/crews/client_NOMECLIENTE_crew.py

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
import os

class ClientNOMECLIENTEAgents:
    """Agent personalizzato per NOMECLIENTE"""

    def __init__(self):
        # Scegli il modello (GRATIS con Groq!)
        self.llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY")
        )

    def create_agents(self):
        """Crea gli agent specifici per il cliente"""

        # Agent 1: Specialista del dominio cliente
        specialist = Agent(
            role="Esperto SETTORE_CLIENTE",
            goal="OBIETTIVO_SPECIFICO_CLIENTE",
            backstory="BACKGROUND_RILEVANTE",
            llm=self.llm,
            verbose=True
        )

        # Agent 2: Analista dati cliente
        analyst = Agent(
            role="Analista Dati NOMECLIENTE",
            goal="Analizzare metriche e KPI specifici",
            backstory="Esperto nei dati del settore",
            llm=self.llm,
            verbose=True
        )

        return [specialist, analyst]

    def process_request(self, request: str):
        """Processa richiesta del cliente"""
        agents = self.create_agents()

        # Task specifici per il cliente
        tasks = [
            Task(
                description=f"Analizza: {request}",
                agent=agents[0],
                expected_output="Analisi dettagliata"
            ),
            Task(
                description=f"Genera insights per: {request}",
                agent=agents[1],
                expected_output="Insights e raccomandazioni"
            )
        ]

        # Esegui
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential
        )

        result = crew.kickoff()

        return {
            "success": True,
            "output": result.output if hasattr(result, 'output') else str(result),
            "client": "NOMECLIENTE"
        }
```

## 🎯 STEP 2: REGISTRA L'AGENT NEL WORKER

```python
# Modifica: /app/worker.py

# Aggiungi import
from crews.client_NOMECLIENTE_crew import ClientNOMECLIENTEAgents

# Nel metodo process_job aggiungi:
elif job_type == "client_NOMECLIENTE":
    agent = ClientNOMECLIENTEAgents()
    result = agent.process_request(job_data.get("request"))
```

## 🎯 STEP 3: AGGIUNGI ENDPOINT API

```python
# Modifica: /app/api.py

@app.post("/api/v1/client/{client_name}")
async def process_client_request(
    client_name: str,
    request: ClientRequest,
    background_tasks: BackgroundTasks
):
    """Endpoint per cliente specifico"""

    job_id = str(uuid.uuid4())
    job_data = {
        "id": job_id,
        "type": f"client_{client_name}",
        "request": request.text,
        "timestamp": datetime.now().isoformat()
    }

    # Aggiungi alla coda
    await redis_client.lpush(
        "agent-engine-jobs:high",
        json.dumps(job_data)
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "client": client_name
    }
```

## 🎯 STEP 4: DEPLOY NEL CONTAINER

### 1. Copia il file nel container
```bash
# Da locale a container
docker cp ./crews/client_esempio_crew.py pilotpros-agent-engine-dev:/app/crews/
```

### 2. Riavvia il worker
```bash
docker exec pilotpros-agent-engine-dev sh -c "killall python; cd /app && python worker.py &"
```

### 3. Test con CLI
```bash
docker exec -it pilotpros-agent-engine-dev python -c "
from crews.client_esempio_crew import ClientEsempioAgents
agent = ClientEsempioAgents()
result = agent.process_request('Analizza le vendite del Q4')
print(result)
"
```

## 🎯 STEP 5: TEST CON CURL

```bash
# Crea job per cliente
curl -X POST http://localhost:8000/api/v1/client/esempio \
  -H "Content-Type: application/json" \
  -d '{"text": "Analizza performance ultimo mese"}'

# Controlla risultato
curl http://localhost:8000/api/v1/job/{job_id}/result
```

## 📋 ESEMPI PRATICI PER SETTORE

### 🏭 Cliente MANIFATTURIERO
```python
class ClientManufacturingAgents:
    def create_agents(self):
        return [
            Agent(
                role="Ingegnere di Produzione",
                goal="Ottimizzare linea produttiva e ridurre scarti",
                backstory="20 anni esperienza in lean manufacturing"
            ),
            Agent(
                role="Analista Supply Chain",
                goal="Ottimizzare inventario e logistica",
                backstory="Esperto in JIT e supply chain management"
            ),
            Agent(
                role="Controllore Qualità",
                goal="Garantire standard ISO e ridurre difetti",
                backstory="Certificato Six Sigma Black Belt"
            )
        ]
```

### 🛒 Cliente E-COMMERCE
```python
class ClientEcommerceAgents:
    def create_agents(self):
        return [
            Agent(
                role="E-commerce Specialist",
                goal="Aumentare conversioni e AOV",
                backstory="Esperto in ottimizzazione funnel"
            ),
            Agent(
                role="Marketing Analyst",
                goal="Ottimizzare ROAS e CAC",
                backstory="Specialista in marketing digitale"
            ),
            Agent(
                role="Customer Experience Manager",
                goal="Migliorare retention e LTV",
                backstory="Esperto in customer journey"
            )
        ]
```

### 🏥 Cliente HEALTHCARE
```python
class ClientHealthcareAgents:
    def create_agents(self):
        return [
            Agent(
                role="Clinical Data Analyst",
                goal="Analizzare outcome pazienti",
                backstory="Biostatistico con esperienza clinica"
            ),
            Agent(
                role="Healthcare Operations Manager",
                goal="Ottimizzare flussi ospedalieri",
                backstory="Esperto in gestione sanitaria"
            )
        ]
```

## 🔧 CONFIGURAZIONE MODELLI PER CLIENTE

### Cliente con BUDGET LIMITATO (GRATIS)
```python
self.llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",  # GRATIS!
    api_key=os.getenv("GROQ_API_KEY")
)
```

### Cliente PREMIUM (Massima qualità)
```python
self.llm = ChatOpenAI(
    model_name="gpt-4o",  # Top quality
    api_key=os.getenv("OPENAI_API_KEY")
)
```

### Cliente MISTO (Bilanciato)
```python
# Agent critico con GPT-4
critical_agent = Agent(
    llm=ChatOpenAI(model_name="gpt-4o"),
    ...
)

# Agent supporto con Groq GRATIS
support_agent = Agent(
    llm=ChatGroq(model_name="llama-3.3-70b-versatile"),
    ...
)
```

## 🚀 COMANDO RAPIDO PER DEPLOY

```bash
# Script deploy.sh
#!/bin/bash
CLIENT=$1
echo "Deploy agent per cliente: $CLIENT"

# 1. Copia file
docker cp ./crews/client_${CLIENT}_crew.py pilotpros-agent-engine-dev:/app/crews/

# 2. Riavvia worker
docker exec pilotpros-agent-engine-dev sh -c "
    ps aux | grep worker.py | awk '{print \$2}' | xargs kill 2>/dev/null
    cd /app && python worker.py > /tmp/worker.log 2>&1 &
"

# 3. Test
sleep 3
docker exec pilotpros-agent-engine-dev python -c "
from crews.client_${CLIENT}_crew import Client${CLIENT}Agents
print('Agent ${CLIENT} caricato con successo!')
"

echo "Deploy completato!"
```

## 📊 MONITORAGGIO

### Logs in tempo reale
```bash
# Worker logs
docker exec pilotpros-agent-engine-dev tail -f /tmp/worker.log

# API logs
docker logs -f pilotpros-agent-engine-dev

# Redis queue
docker exec redis-dev redis-cli LLEN agent-engine-jobs:high
```

### Dashboard Status
```bash
docker exec pilotpros-agent-engine-dev python -c "
import redis
r = redis.Redis(host='redis-dev')
print(f'Jobs in coda: {r.llen(\"agent-engine-jobs:high\")}')
print(f'Jobs completati: {len(r.keys(\"job:result:*\"))}')
"
```

## ✅ CHECKLIST NUOVO CLIENTE

- [ ] Crea file `client_NOME_crew.py`
- [ ] Definisci ruoli agent specifici per settore
- [ ] Scegli modello (GRATIS/PREMIUM)
- [ ] Aggiungi al worker.py
- [ ] Copia nel container
- [ ] Test con CLI
- [ ] Test con API
- [ ] Documenta configurazione

## 💡 BEST PRACTICES

1. **Inizia sempre con Groq GRATIS** per prototipare
2. **Usa GPT-4o solo per agent critici**
3. **Massimo 3-5 agent per crew** (performance)
4. **Cache risultati** per richieste simili
5. **Log dettagliati** per debug
6. **Test incrementali** prima di production

## 🆘 TROUBLESHOOTING

### Agent non risponde
```bash
# Check worker
docker exec pilotpros-agent-engine-dev ps aux | grep worker

# Restart worker
docker exec -d pilotpros-agent-engine-dev python /app/worker.py
```

### Errori modello
```bash
# Test modello diretto
docker exec pilotpros-agent-engine-dev python -c "
from langchain_groq import ChatGroq
llm = ChatGroq(model_name='llama-3.3-70b-versatile')
print(llm.invoke('test'))
"
```

### Coda bloccata
```bash
# Pulisci coda
docker exec redis-dev redis-cli FLUSHDB
```