# 🎯 TODO: Fix Milhena Architecture - v4.0 Rollback to v3.1 + 19 Tools

**Branch**: `sugituhg`
**Status**: 🔴 ARCHITECTURE MISMATCH
**Date**: 2025-10-08

---

## 🚨 PROBLEMA

**v4.0 deployata NON corrisponde alle specifiche del progetto!**

**Architettura Attuale** (v4.0 GraphSupervisor):
```
User → Supervisor LLM → Agent Selection → Specialized Agent → Tool → Masking → Response
```
❌ 3 agent specializzati (Milhena/N8N/Analyst) = over-engineering
❌ Supervisor routing = overhead inutile
❌ 2 LLM calls invece di 1

**Architettura Target** (specifiche progetto):
```
User → Classifier → ReAct Agent → Response Agent → Masking → User
```
✅ 1 solo ReAct Agent con tutti i tools
✅ 4 fasi distinte: Classify → Act → Synthesize → Mask
✅ Architettura lineare, no branching

---

## ✅ SOLUZIONE

**v3.1 MilhenaGraph è IDENTICA alle specifiche!**

v3.1 ha già:
- ✅ IntentAnalyzer (Classifier Agent)
- ✅ ReAct Agent (tool selection)
- ✅ ResponseGenerator (Response Agent)
- ✅ MaskingEngine (Masking Module)

**Azione**: Riattivare v3.1 + aggiungere 19 tools da v4.0

---

## 📋 MIGRATION PLAN

### Step 1: Riattivare v3.1 MilhenaGraph
**File**: `intelligence-engine/app/main.py`

```python
# Line 69: DECOMMENTARE
app.state.milhena = MilhenaGraph()

# Line 73: COMMENTARE
# app.state.graph_supervisor = get_graph_supervisor(use_real_llms=True)
```

### Step 2: Aggiungere 19 tools a MilhenaGraph
**File**: `intelligence-engine/app/milhena/graph.py`

Importare da `app.tools.pilotpro_tools`:
```python
from app.tools.pilotpro_tools import (
    get_workflows_tool,
    get_all_errors_summary_tool,
    get_error_details_tool,
    get_executions_by_date_tool,
    get_node_execution_details_tool,
    get_chatone_email_details_tool,
    get_workflow_details_tool,
    get_workflow_cards_tool,
    # ... altri 11 tools
)
```

Aggiungere ai tools del ReAct Agent (circa riga 800-900).

### Step 3: Aggiornare endpoint n8n
**File**: `intelligence-engine/app/n8n_endpoints.py`

```python
# Line 52-56: CAMBIARE da GraphSupervisor a MilhenaGraph
from .main import app
milhena = app.state.milhena

result = await milhena.compiled_graph.ainvoke({
    "messages": [HumanMessage(content=request.message)],
    "session_id": session_id
})
```

### Step 4: Aggiornare visual debugger
**File**: `debug-visual-web.html`

Cambiare flowSteps a 6 step:
1. User Query
2. Classifier Agent (IntentAnalyzer)
3. ReAct Agent (tool selection + execution)
4. Response Agent (ResponseGenerator)
5. Masking Module
6. Final Response

Rimuovere:
- Supervisor LLM step
- Agent Selection step (diamond)
- 3 specialized agents

### Step 5: Clear cache + Restart
```bash
docker exec pilotpros-intelligence-engine-dev find /app -name "*.pyc" -delete
docker-compose restart intelligence-engine
sleep 40
```

### Step 6: Test
```bash
# Test 1: Error query
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "quali errori abbiamo oggi?", "session_id": "test-v3.1"}' \
  --max-time 15

# Expected: Success con get_all_errors_summary_tool

# Test 2: General query
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "ciao", "session_id": "test-v3.1-2"}' \
  --max-time 15

# Expected: Greeting response
```

### Step 7: Commit
```bash
git add intelligence-engine/app/main.py \
        intelligence-engine/app/milhena/graph.py \
        intelligence-engine/app/n8n_endpoints.py \
        debug-visual-web.html

git commit -m "feat: Rollback to v3.1 architecture + 19 tools integration

BREAKING CHANGE: Removed v4.0 GraphSupervisor (over-engineering)
Restored v3.1 MilhenaGraph with correct 4-agent pipeline:
- Classifier Agent (IntentAnalyzer)
- ReAct Agent (tool selection)
- Response Agent (ResponseGenerator)
- Masking Module

Added 19 tools from v4.0 pilotpro_tools.py to v3.1 ReAct Agent.

Benefits:
- Simpler architecture (1 agent vs 3)
- Faster (1 LLM call vs 2)
- Matches project specifications exactly

Tested: All 19 tools working correctly"
```

---

## 📊 CONFRONTO PERFORMANCE

| Metric | v4.0 (3 agents) | v3.1 (1 agent) |
|--------|-----------------|----------------|
| LLM Calls | 2 (Supervisor + Agent) | 1 (ReAct only) |
| Latency | ~8s average | ~5s expected |
| Complexity | HIGH (3 agents) | MEDIUM (1 agent) |
| Matches Specs | ❌ NO | ✅ YES |

---

## ✅ SUCCESS CRITERIA

- [ ] v3.1 MilhenaGraph attiva in main.py
- [ ] 19 tools disponibili nel ReAct Agent
- [ ] Endpoint n8n usa MilhenaGraph
- [ ] Visual debugger mostra 4 agent corretti
- [ ] Test errori/greetings/analytics funzionano
- [ ] Latency migliorata (<5s per query semplici)
- [ ] CLAUDE.md aggiornato con architettura v3.1

---

## 📁 FILES DA MODIFICARE

1. `intelligence-engine/app/main.py` - Switch v4.0 → v3.1
2. `intelligence-engine/app/milhena/graph.py` - Add 19 tools
3. `intelligence-engine/app/n8n_endpoints.py` - Use milhena instead of graph_supervisor
4. `debug-visual-web.html` - Update to 4-agent flow
5. `CLAUDE.md` - Document v3.1 as production architecture

---

## 🔍 VISUAL QUERY DEBUGGER

**File**: `debug-visual-web.html` (standalone, 100% client-side)

**Features**:
- Real-time query flow visualization
- SVG animated diagram with shapes:
  - 🔷 Hexagon = LLM Agent
  - 💎 Diamond = Decision/Routing
  - ▭ Rectangle = Technical step
  - ⭕ Circle = Input/Output
- 4 tabs: Visual Diagram | LangSmith Trace | Timeline | Raw Data
- Query history with replay
- Export results to JSON
- Execution statistics (latency, success rate, etc.)

**Usage**:
```bash
# Open in browser
open debug-visual-web.html

# Or serve with Python
python3 -m http.server 8080
# Then open: http://localhost:8080/debug-visual-web.html
```

**Purpose**:
- Debug query flow step-by-step
- Verify agent routing decisions
- Check business masking effectiveness
- Measure performance per step
- **MANDATORY for testing after v3.1 migration!**

---

**Estimated time**: 30 minutes
**Risk**: LOW (v3.1 already tested, just needs tools migration)
