# 🤖 Agent Engine - Runtime Multi-Agent per PilotProOS

Engine universale basato su CrewAI per l'esecuzione di tutti i sistemi multi-agent acquistati dai clienti.

## 🚨 REGOLA: CrewAI Versione COMPATIBILE!

**IMPORTANTE**: CrewAI ha breaking changes tra versioni - usa versione TESTATA e COMPATIBILE!

- ✅ **Versione FUNZIONANTE**: CrewAI 0.193.2 (testata e funzionante)
- ❌ **Versioni INCOMPATIBILI**: 0.28.0 e precedenti (ImportError BaseTool)
- ⚠️ **Aggiornamenti**: Testare sempre prima - non aggiornare a caso
- 🔍 **Breaking Changes**: API cambia spesso (`crewai.tools` → `crewai_tools`)

```dockerfile
# In Dockerfile - SEMPRE aggiornare alla versione più recente
RUN pip install --no-cache-dir crewai==0.193.2  # Aggiornare questo numero!
```

## Architettura

- **FastAPI Server**: API REST per comunicazione con frontend
- **CrewAI Multi-Agent**: Orchestrazione agenti specializzati
- **Groq/Gemini LLM**: Providers per inferenza rapida
- **Docker Container**: Isolamento completo dipendenze Python

## Agenti Disponibili

### Milhena v4.0 (Default)
- **Tipo**: Business Analyst multi-agent
- **Crew Agents**: Data Analyst, Business Advisor, Technical Analyst
- **Capabilities**: Analisi dati, ottimizzazione workflow, insights business

## API Endpoints

```bash
GET  /health                # Health check
GET  /                     # Service info
POST /api/chat            # Chat con agenti
GET  /api/agents          # Lista agenti disponibili
```

## Development

```bash
# Build container (con CrewAI ULTIMA versione)
docker-compose build agent-engine-dev --no-cache

# Start service
docker-compose up -d agent-engine-dev

# Test API
curl http://localhost:8000/health
```

## Ambiente Variabili

```bash
GROQ_API_KEY=gsk_xxx...        # Primary LLM
GEMINI_API_KEY=xxx...          # Fallback LLM
PRIMARY_LLM=groq               # groq | gemini
```

## 🔒 Container Lock

Vedi `CONTAINER_LOCK.md` per dettagli su build funzionanti e comandi sicuri vs vietati.

⚠️ **Non ricostruire mai senza motivo** - container richiede 3+ ore debug dipendenze!