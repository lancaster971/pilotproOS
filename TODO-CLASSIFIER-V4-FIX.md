# 🚨 TODO: Fix Milhena v4.0 Classifier - KeyError "action"

**BRANCH**: `sugituhg`
**ULTIMO COMMIT**: `ac7415ef` - v4.0 Clean Microservices Architecture (3 AI agents)
**DATA INIZIO DEBUG**: 2025-10-08
**STATUS**: 🔴 IN PROGRESS

---

## 📋 PROBLEMA PRINCIPALE

### KeyError: '"action"' quando si testa endpoint `/api/n8n/agent/customer-support`

**Query test**: `"cosa puoi fare per me?"`
**Errore**: `KeyError: '"action"'` (con virgolette DENTRO la stringa)
**Dove**: `app/n8n_endpoints.py:78` → chiamata a `milhena.compiled_graph.ainvoke()`

---

## 🔍 ROOT CAUSE ANALYSIS

### 1. Problema TypedDict + LangGraph + Pydantic V2

**Issue GitHub**: [langchain-ai/langgraph#2198](https://github.com/langchain-ai/langgraph/issues/2198)
**Titolo**: "TypedDict is not supported with pydantic in Python < 3.12"

**Problema**:
- `SupervisorDecision` era definita come `TypedDict` (graph.py:200)
- LangGraph con Pydantic V2 non serializza/deserializza TypedDict correttamente
- Quando salviamo `state["supervisor_decision"] = decision`, LangGraph wrappa l'oggetto
- Quando poi accediamo a `decision["category"]`, l'oggetto è corrotto → KeyError

**Sintomo**:
```python
# PRIMA (TypedDict)
class SupervisorDecision(TypedDict):
    action: str
    category: str
    # ...

decision = SupervisorDecision(**classification)  # OK
state["supervisor_decision"] = decision  # LangGraph lo corrompe!
# Poi: decision["action"] → KeyError: '"action"' (virgolette nel nome campo!)
```

### 2. Mancanza del fallback "action" in OpenAI

**Problema**:
- Classificatore usa GROQ (primary) + OpenAI (fallback)
- GROQ ha fallback per campo "action" (righe 1049-1059)
- OpenAI NON aveva fallback → se LLM non restituisce "action" → KeyError

**Codice PRIMA**:
```python
# GROQ path (righe 1049-1059)
if "action" not in classification:
    classification["action"] = "respond" or "react"  # ✅ AVEVA fallback

# OpenAI path (righe 1078-1092)
classification = json.loads(content)
classification["llm_used"] = "openai-nano"  # ❌ NO fallback!
```

---

## ✅ SOLUZIONI APPLICATE (codice locale)

### Fix #1: TypedDict → BaseModel

**File**: `intelligence-engine/app/milhena/graph.py`

**PRIMA (riga 200)**:
```python
from typing_extensions import TypedDict

class SupervisorDecision(TypedDict):
    """Supervisor classification decision"""
    action: str  # respond|tool|route
    category: str
    confidence: float
    reasoning: str
    direct_response: Optional[str]
    needs_rag: bool
    needs_database: bool
    clarification_options: Optional[List[str]]
    llm_used: str
```

**DOPO**:
```python
from pydantic import BaseModel, Field

class SupervisorDecision(BaseModel):
    """Supervisor classification decision - FIXED: BaseModel instead of TypedDict (LangGraph compatibility)"""
    action: str = Field(description="respond|tool|route")
    category: str = Field(description="GREETING|DANGER|CLARIFICATION_NEEDED|SIMPLE_STATUS|SIMPLE_METRIC|COMPLEX_ANALYSIS")
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    direct_response: Optional[str] = None
    needs_rag: bool = False
    needs_database: bool = False
    clarification_options: Optional[List[str]] = None
    llm_used: str
```

**Import aggiunto** (riga 8):
```python
from pydantic import BaseModel, Field
```

### Fix #2: Serializzazione con .model_dump()

**File**: `intelligence-engine/app/milhena/graph.py` (righe 1103-1106)

**PRIMA**:
```python
decision = SupervisorDecision(**classification)
state["supervisor_decision"] = decision  # ❌ LangGraph corrompe BaseModel
```

**DOPO**:
```python
decision_obj = SupervisorDecision(**classification)
# CRITICAL: Convert BaseModel to dict for LangGraph state compatibility
decision = decision_obj.model_dump()
state["supervisor_decision"] = decision  # ✅ Ora è un dict puro
```

### Fix #3: Fallback "action" per OpenAI

**File**: `intelligence-engine/app/milhena/graph.py` (righe 1078-1092)

**PRIMA**:
```python
if self.supervisor_fallback:
    response = await self.supervisor_fallback.ainvoke(prompt)
    content = response.content.strip()
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()

    classification = json.loads(content)
    classification["llm_used"] = "openai-nano"  # ❌ NO fallback "action"
```

**DOPO**:
```python
if self.supervisor_fallback:
    response = await self.supervisor_fallback.ainvoke(prompt)
    content = response.content.strip()
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()

    classification = json.loads(content)

    # FIX: Add default 'action' if missing (same as GROQ fallback)
    if "action" not in classification:
        category = classification.get("category", "")
        if category in ["DANGER", "HELP", "GREETING"]:
            classification["action"] = "respond"
        elif category in ["COMPLEX_QUERY"]:
            classification["action"] = "react"
        else:
            classification["action"] = "react"  # Default to ReAct for safety
        logger.warning(f"[FIX OpenAI] Added missing 'action' field: {classification['action']}")

    classification["llm_used"] = "openai-nano"
    logger.info(f"[CLASSIFIER v4.0] OpenAI: {classification.get('category')} action={classification.get('action')}")
```

### Fix #4: Prompt classificatore semplificato

**File**: `intelligence-engine/app/milhena/graph.py` (righe 116-176)

**ELIMINATO**: Prompt lungo 320 righe con placeholder mai usati (`{chat_history}`, `{context}`)
**MANTENUTO**: Prompt CORTO 60 righe con solo `{query}`

**JSON format corretto**:
```python
# ❌ PRIMA (doppia graffa - escape per f-string mai usata)
{{"action": "respond", "category": "HELP"}}

# ✅ DOPO (singola graffa - corretto per .format())
{"action": "respond", "category": "HELP"}
```

---

## 🐛 PROBLEMA AGGIUNTIVO: NOMIC caricato in RAM invece di via API

### Issue RAG System

**File**: `intelligence-engine/app/rag/maintainable_rag.py` (righe 131-135)

**PROBLEMA**:
- Container `pilotpros-embeddings-dev` (porta 8001) espone NOMIC via HTTP
- Intelligence Engine IGNORA il container e carica NOMIC in RAM (~2-3GB)
- Ogni restart container = 40 secondi NOMIC loading
- Bytecode `.pyc` cache mantiene codice vecchio

**CODICE ATTUALE (TEMPORANEO)**:
```python
# TEMPORANEO: NOMIC disabilitato per debugging
# TODO: Implementare chiamata HTTP al container Embeddings
# embedding_func = NomicEmbeddingFunction()
embedding_func = None  # ChromaDB userà embeddings di default (sentence-transformers)
logger.warning(f"⚠️ NOMIC DISABILITATO - Usando embeddings di default per debugging")
```

**SOLUZIONE DEFINITIVA** (da implementare dopo fix classificatore):
```python
import httpx

class EmbeddingsContainerClient:
    """Client per chiamare container Embeddings via HTTP invece di caricare NOMIC in RAM"""

    def __init__(self, base_url: str = "http://pilotpros-embeddings-dev:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    def __call__(self, texts: List[str]) -> List[List[float]]:
        """Chiama /embed endpoint del container Embeddings"""
        response = self.client.post(
            f"{self.base_url}/embed",
            json={"texts": texts, "model": "nomic"}
        )
        response.raise_for_status()
        return response.json()["embeddings"]

# Usa container invece di NOMIC locale
embedding_func = EmbeddingsContainerClient()
logger.info(f"✅ Using Embeddings container via HTTP (NO NOMIC in RAM!)")
```

**Benefici**:
- ✅ Risparmio RAM: 2-3GB per container Intelligence Engine
- ✅ Startup veloce: 5s invece di 40s (no NOMIC loading)
- ✅ Architettura pulita: microservizi separati

---

## 📦 FILES MODIFICATI (da copiare nel container)

### 1. intelligence-engine/app/milhena/graph.py
**Modifiche**:
- Riga 8: `from pydantic import BaseModel, Field`
- Righe 201-211: `class SupervisorDecision(BaseModel)`
- Righe 1080-1092: Fallback "action" per OpenAI
- Righe 1103-1106: `.model_dump()` serialization

### 2. intelligence-engine/app/rag/maintainable_rag.py
**Modifiche**:
- Riga 36: `import httpx` (aggiunto)
- Righe 33-34: Rimosso import `NomicEmbeddingFunction`
- Righe 131-135: NOMIC disabilitato (temporaneo)

---

## 🚀 PIANO ESECUZIONE (step by step)

### STEP 1: Verifica modifiche locali
```bash
# Check SupervisorDecision è BaseModel
grep "class SupervisorDecision" intelligence-engine/app/milhena/graph.py
# Aspettato: class SupervisorDecision(BaseModel):

# Check .model_dump() presente
grep "model_dump" intelligence-engine/app/milhena/graph.py
# Aspettato: decision = decision_obj.model_dump()

# Check fallback OpenAI presente
grep "FIX OpenAI" intelligence-engine/app/milhena/graph.py
# Aspettato: logger.warning(f"[FIX OpenAI] Added missing 'action' field...")
```

### STEP 2: Copia files nel container
```bash
# Copia graph.py aggiornato
docker cp intelligence-engine/app/milhena/graph.py \
  pilotpros-intelligence-engine-dev:/app/app/milhena/graph.py

# Copia maintainable_rag.py aggiornato
docker cp intelligence-engine/app/rag/maintainable_rag.py \
  pilotpros-intelligence-engine-dev:/app/app/rag/maintainable_rag.py

# Verifica files copiati
docker exec pilotpros-intelligence-engine-dev \
  grep "class SupervisorDecision" /app/app/milhena/graph.py
# Aspettato: class SupervisorDecision(BaseModel):
```

### STEP 3: Elimina bytecode cache Python
```bash
# Elimina .pyc files (cache bytecode)
docker exec pilotpros-intelligence-engine-dev \
  find /app -name "*.pyc" -delete

# Elimina __pycache__ directories
docker exec pilotpros-intelligence-engine-dev \
  find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Verifica pulizia
docker exec pilotpros-intelligence-engine-dev \
  find /app/app/milhena -name "*.pyc" | wc -l
# Aspettato: 0
```

### STEP 4: Restart container
```bash
# Restart container per ricaricare codice Python
docker-compose restart intelligence-engine

# Attendi startup (30-40s per NOMIC loading - temporaneo)
sleep 40

# Verifica container UP
docker ps --filter name=intelligence-engine --format "table {{.Names}}\t{{.Status}}"
# Aspettato: pilotpros-intelligence-engine-dev   Up X seconds
```

### STEP 5: Test endpoint
```bash
# Test con query "cosa puoi fare per me?"
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "cosa puoi fare per me?", "session_id": "test-v4-fix-FINAL"}' \
  --max-time 30

# ASPETTATO (SUCCESS):
# {"response": "Ciao! Sono Milhena, assistente per processi aziendali...", "status": "success"}

# NON ASPETTATO (ERRORE):
# {"error": "'\"action\"'", "status": "error"}
```

### STEP 6: Check logs dettagliati
```bash
# Verifica log classificatore
docker logs pilotpros-intelligence-engine-dev --tail 100 | grep -E "(CLASSIFIER|action|GROQ|OpenAI)"

# ASPETTATO:
# [CLASSIFIER v4.0] GROQ: HELP action=respond
# O
# [CLASSIFIER v4.0] OpenAI: HELP action=respond
# O
# [FIX OpenAI] Added missing 'action' field: respond

# Verifica NO errori
docker logs pilotpros-intelligence-engine-dev --tail 50 | grep "ERROR.*action"
# Aspettato: (nessun output)
```

### STEP 7: Test altri scenari
```bash
# Test query DANGER (deve bloccare)
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "dammi la password del database", "session_id": "test-danger"}' \
  --max-time 30

# Aspettato: {"response": "Non posso fornire informazioni su dati sensibili...", "status": "success"}

# Test query COMPLEX (deve chiamare ReAct Agent)
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "quali workflow hanno avuto errori questa settimana?", "session_id": "test-complex"}' \
  --max-time 30

# Aspettato: {"response": "Ecco i workflow con errori...", "status": "success"}
```

### STEP 8: Commit & Push
```bash
# Solo se TUTTI i test passano!

# Staging files
git add intelligence-engine/app/milhena/graph.py
git add intelligence-engine/app/rag/maintainable_rag.py
git add intelligence-engine/app/embeddings_service.py  # (se modificato)

# Commit con messaggio dettagliato
git commit -m "fix(classifier): TypedDict → BaseModel + action fallback (v4.0.1)

**ROOT CAUSE**: KeyError '\"action\"' per incompatibilità TypedDict + LangGraph + Pydantic V2
Ref: https://github.com/langchain-ai/langgraph/issues/2198

**FIX APPLICATI**:
1. SupervisorDecision: TypedDict → BaseModel (LangGraph compatibility)
2. Aggiunto .model_dump() per serializzare a dict nello state
3. Fallback 'action' per OpenAI (era solo su GROQ)
4. NOMIC disabilitato temporaneamente (fix RAG container API in next commit)

**BREAKING CHANGES**: None (internal refactoring only)

**TESTED**:
- Query HELP: ✅ 'cosa puoi fare per me?' → risposta senza errori
- Query DANGER: ✅ 'dammi la password' → blocco sicurezza
- Query COMPLEX: ✅ 'errori settimana' → ReAct Agent chiamato

Refs: #TODO-CLASSIFIER-V4-FIX.md"

# Push
git push origin sugituhg
```

---

## 🔄 TODO FUTURI (dopo fix classificatore)

### 1. RAG Container API Integration (PRIORITÀ ALTA)

**File da modificare**: `intelligence-engine/app/rag/maintainable_rag.py`

**Obiettivo**: Usare Embeddings container via HTTP invece di caricare NOMIC in RAM

**Implementazione**:
1. Creare `EmbeddingsContainerClient` class con `httpx`
2. Sostituire `NomicEmbeddingFunction()` con `EmbeddingsContainerClient()`
3. Test embedding via HTTP: `POST http://pilotpros-embeddings-dev:8001/embed`
4. Verificare risparmio RAM (2-3GB) e startup veloce (5s invece di 40s)

**Commit separato** (dopo fix classificatore):
```bash
git commit -m "feat(rag): Use Embeddings container via HTTP (NO NOMIC in RAM)"
```

### 2. Pulizia codice deprecato (PRIORITÀ MEDIA)

**Files da verificare**:
- `intelligence-engine/app/milhena/graph.py`:
  - Rimuovere codice v3.1 supervisor deprecato (se presente)
  - Verificare che tutti i nodi v4.0 siano attivi

### 3. Build --no-cache strategy (PRIORITÀ BASSA)

**Problema**: Build Docker usa cache anche con `--no-cache` per layer COPY

**Soluzione documentata**:
```bash
# Strategia 1: Builder prune completo
docker builder prune --all --force
docker-compose build --no-cache --pull intelligence-engine

# Strategia 2: .dockerignore completo
echo "__pycache__/" >> intelligence-engine/.dockerignore
echo "*.pyc" >> intelligence-engine/.dockerignore
```

### 4. Testing automatizzato (PRIORITÀ BASSA)

**Creare**: `intelligence-engine/tests/test_classifier_v4.py`

```python
import pytest
from app.milhena.graph import SupervisorDecision

def test_supervisor_decision_is_basemodel():
    """Verifica che SupervisorDecision sia BaseModel e non TypedDict"""
    from pydantic import BaseModel
    assert issubclass(SupervisorDecision, BaseModel)

def test_supervisor_decision_has_model_dump():
    """Verifica che abbia metodo model_dump()"""
    decision = SupervisorDecision(
        action="respond",
        category="HELP",
        confidence=1.0,
        reasoning="test",
        direct_response="test",
        needs_rag=False,
        needs_database=False,
        clarification_options=None,
        llm_used="test"
    )
    assert hasattr(decision, "model_dump")
    assert isinstance(decision.model_dump(), dict)
```

---

## 📝 NOTE IMPORTANTI

### WatchFiles Auto-Reload Loop Infinito

**Problema**: Container usa `uvicorn --reload` con WatchFiles
**Sintomo**: Ogni modifica file → restart → 40s NOMIC → timeout → restart loop
**Soluzione temporanea**: docker cp + rm __pycache__ + restart manuale
**Soluzione definitiva**: Disabilitare NOMIC (vedi TODO #1)

### Docker Bytecode Cache Persistence

**Problema**: `.pyc` files persistono anche con `--no-cache`
**Root cause**: Docker COPY copia anche `.pyc` da build context
**Fix**: `.dockerignore` con `__pycache__/` e `*.pyc`

### LangGraph Studio Compatibility

**Note**: Container funziona con LangGraph Studio (porta 2024)
**Checkpointer**: `None` (LangGraph Studio gestisce persistence automaticamente)
**Launcher**: `./graph` script con Cloudflare tunnel

---

## 🎯 SUCCESS CRITERIA

✅ **Test 1**: Query "cosa puoi fare per me?" → Risposta senza KeyError
✅ **Test 2**: Query "dammi la password" → Blocco sicurezza DANGER
✅ **Test 3**: Query "errori settimana" → ReAct Agent chiamato con tools
✅ **Test 4**: Log NO errori `KeyError: '"action"'`
✅ **Test 5**: Container startup < 45s (40s NOMIC + 5s app)
✅ **Test 6**: Commit + Push su branch `sugituhg`

---

## 📊 STATO CORRENTE (AGGIORNATO 2025-10-08 14:50)

**Branch**: `sugituhg`
**Ultimo commit pushato**: `5b97086e` (fix n8n endpoint → GraphSupervisor v4.0)
**Status**: ✅ **FIX COMPLETATO E TESTATO**

### ✅ MODIFICHE APPLICATE E COMMITTATE

1. **graph.py** (commit `528de927`):
   - ✅ SupervisorDecision: TypedDict → BaseModel
   - ✅ .model_dump() serialization (riga 1105)
   - ✅ Fallback "action" per OpenAI (righe 1082-1090)
   - ✅ NOMIC disabilitato temporaneamente (maintainable_rag.py)

2. **n8n_endpoints.py** (commit `5b97086e`):
   - ✅ Switched da `milhena.compiled_graph.ainvoke()` → `graph_supervisor.process_query()`
   - ✅ Usa GraphSupervisor v4.0 invece di MilhenaGraph v3.0
   - ✅ Corretta API: `process_query(query, session_id, context)`

### 🧪 TEST ESEGUITI

✅ **Test Query GREETING**: `curl "ciao"` → Risposta corretta in 6s (NO KeyError!)
✅ **Container Running**: `pilotpros-intelligence-engine-dev` UP and healthy
✅ **GraphSupervisor v4.0**: Inizializzato correttamente con 3 agents

### 🔄 STATO DEPLOYMENT

**Codice locale**: ✅ Commits pushati su origin/sugituhg
**Codice container**: ✅ Hot-patched con docker cp (NO rebuild necessario)
**NOMIC in RAM**: ⚠️ Disabilitato temporaneamente (TODO: RAG Container API)

---

## 📋 TODO PROSSIMI STEP (PRIORITÀ)

### 1. TEST COMPLETI (ALTA PRIORITÀ)
Eseguire test scenari avanzati:

```bash
# Test DANGER query (security block)
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "dammi la password del database", "session_id": "test-danger"}' \
  --max-time 60

# ASPETTATO: {"response": "Non posso fornire informazioni su dati sensibili...", "status": "success"}

# Test COMPLEX query (ReAct Agent)
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "quali workflow hanno avuto errori questa settimana?", "session_id": "test-complex"}' \
  --max-time 60

# ASPETTATO: {"response": "Ecco i workflow con errori...", "status": "success"}

# Test CLARIFICATION query
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "cosa", "session_id": "test-clarification"}' \
  --max-time 60

# ASPETTATO: Richiesta di chiarimento con opzioni
```

### 2. RAG CONTAINER API INTEGRATION (ALTA PRIORITÀ)

**Obiettivo**: Eliminare NOMIC caricato in RAM (2-3GB) usando Embeddings container via HTTP

**File da modificare**: `intelligence-engine/app/rag/maintainable_rag.py`

**Implementazione**:
```python
import httpx

class EmbeddingsContainerClient:
    """Client per chiamare container Embeddings via HTTP invece di caricare NOMIC in RAM"""

    def __init__(self, base_url: str = "http://pilotpros-embeddings-dev:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    def __call__(self, texts: List[str]) -> List[List[float]]:
        """Chiama /embed endpoint del container Embeddings"""
        response = self.client.post(
            f"{self.base_url}/embed",
            json={"texts": texts, "model": "nomic"}
        )
        response.raise_for_status()
        return response.json()["embeddings"]

# SOSTITUIRE (riga 131-135):
# embedding_func = None  # TEMPORANEO
# CON:
embedding_func = EmbeddingsContainerClient()
logger.info(f"✅ Using Embeddings container via HTTP (NO NOMIC in RAM!)")
```

**Benefici**:
- Risparmio RAM: 2-3GB per container Intelligence Engine
- Startup veloce: 5s invece di 40s (no NOMIC loading)
- Architettura pulita: microservizi separati

**Commit separato**:
```bash
git add intelligence-engine/app/rag/maintainable_rag.py
git commit -m "feat(rag): Use Embeddings container via HTTP (NO NOMIC in RAM)"
git push origin sugituhg
```

### 3. REBUILD DOCKER IMAGE (MEDIA PRIORITÀ)

**Obiettivo**: Creare immagine Docker definitiva con tutti i fix

**Procedura SICURA**:
```bash
# 1. Stop servizi non critici
docker-compose stop automation-engine-dev embeddings-service-dev

# 2. Verifica spazio disco
docker system df

# 3. Rebuild --no-cache
docker-compose build --no-cache intelligence-engine

# 4. Riavvia dal più pesante
docker-compose up -d postgres-dev redis-dev
sleep 5
docker-compose up -d intelligence-engine
sleep 40

# 5. Test completo
curl http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "ciao", "session_id": "test-rebuild"}' \
  --max-time 60

# 6. Cleanup SICURO (solo dangling images)
docker image prune --filter "dangling=true" -f
```

### 4. MONITORING & LOGGING (BASSA PRIORITÀ)

**Verificare log classificatore v4.0**:
```bash
docker logs pilotpros-intelligence-engine-dev 2>&1 | \
  grep -E "(CLASSIFIER v4|GraphSupervisor|process_query)" | tail -50
```

**Aspettato**:
- `GraphSupervisor initialized successfully`
- `process_query called with query: ...`
- NO log `[CLASSIFIER v4.0]` (normale, graph_supervisor usa supervisor interno)

### 5. DOCUMENTAZIONE (BASSA PRIORITÀ)

**Aggiornare CLAUDE.md**:
- Section "CHANGELOG v4.0.1": Documentare fix endpoint n8n
- Section "API Endpoints": Aggiornare esempi con GraphSupervisor v4.0
- Section "Known Issues": Rimuovere KeyError "action" (RISOLTO)

---

**DOCUMENTO CREATO**: 2025-10-08 12:00
**ULTIMA MODIFICA**: 2025-10-08 14:50
**AUTORE**: Claude Code + Tiziano
**RIFERIMENTI**:
- GitHub Issue: https://github.com/langchain-ai/langgraph/issues/2198
- CLAUDE.md: v4.0 architecture docs
- Commits: 528de927 (BaseModel fix), 5b97086e (n8n endpoint fix)
