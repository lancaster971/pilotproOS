# 🎯 Milhena v3.5.5 - ARCHITETTURA REALE

**Date**: 2025-10-16
**Status**: ⚠️ BUG IN TOOL EXECUTION (params non passati ai tool)

---

## 🏗️ ARCHITETTURA VISUALE

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER QUERY                              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │  [1] FAST-PATH              │  ⚡ <1ms
        │  ─────────────              │
        │  • DANGER keywords?         │
        │  • GREETING keywords?       │
        │                             │
        │  YES → direct_response      │────┐
        │  NO  → None                 │    │
        └─────────────┬───────────────┘    │
                      │                    │
                      ▼                    │
        ┌─────────────────────────────┐    │
        │  [2] CLASSIFIER (LLM)       │  🧠 200-500ms
        │  ─────────────────────      │    │
        │  Input:                     │    │
        │  • query                    │    │
        │  • system_context (cache)   │    │
        │                             │    │
        │  Output:                    │    │
        │  • category (9 types)       │    │
        │  • confidence               │    │
        │  • reasoning                │    │
        │  • params ⚠️ (NON arrivano) │    │
        └─────────────┬───────────────┘    │
                      │                    │
                      ▼                    │
        ┌─────────────────────────────┐    │
        │  [3] TOOL MAPPER            │  📋 <1ms
        │  ────────────────            │    │
        │  map_category_to_tools()    │    │
        │                             │    │
        │  category → [tool_fn, ...]  │    │
        │                             │    │
        │  9 mappings statici         │    │
        └─────────────┬───────────────┘    │
                      │                    │
                      ▼                    │
        ┌─────────────────────────────┐    │
        │  [4] TOOL EXECUTION         │  🔧 async
        │  ───────────────────         │    │
        │  for tool_fn in tools:      │    │
        │    result = await           │    │
        │      tool_fn.ainvoke(       │    │
        │        params ⚠️             │    │  ⚠️ BUG: params={}
        │      )                       │    │     sempre vuoto!
        │                             │    │
        │  tool_results = [...]       │    │
        └─────────────┬───────────────┘    │
                      │                    │
                      ▼                    │
        ┌─────────────────────────────┐    │
        │  [5] RESPONDER (LLM)        │  💬 1-2s
        │  ────────────────────        │    │
        │  Sintetizza tool_results    │    │
        │  in risposta business       │    │
        │                             │    │
        │  LLM: llama-3.3-70b (Groq)  │    │
        └─────────────┬───────────────┘    │
                      │                    │
                      ▼                    │
        ┌─────────────────────────────┐    │
        │  [6] MASKING                │  🎭 <1ms
        │  ────────────                │    │
        │  Rimuove termini tecnici    │◄───┘
        │  (n8n, PostgreSQL, etc.)    │
        └─────────────┬───────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │      RISPOSTA FINALE        │
        └─────────────────────────────┘
```

**Legenda**:
- ⚡ Fast-path: keyword detection
- 🧠 LLM: chiamata modello AI
- 📋 Libreria: funzione Python pura
- 🔧 Async: esecuzione tool con await
- 💬 LLM: sintesi risposta
- 🎭 Libreria: masking termini

---

## 📋 FILES

- **graph.py:356-386** - Tool Mapper (`map_category_to_tools`)
- **graph.py:1165-1400** - Classifier (`supervisor_orchestrator`)
- **graph.py:2300-2356** - Tool Execution (`execute_tools_direct`)
- **graph.py:2409-2540** - Responder (`generate_final_response`)
- **graph.py:2542-2592** - Masking (`mask_response`)

---

## 🐛 BUG TROVATO (2025-10-16)

**Test Tool Mapper**: 10 query → 10 fallimenti

**Root Cause**:
```python
# Tool Execution (linea 2314)
params = classification.get("params", {})  # ← Sempre {} vuoto!

# Classifier ritorna params ma non arrivano a state["supervisor_decision"]
```

**Evidenza dai log**:
```
Classifier: params={'workflow_id': 'GESTIONE_LEAD'} ✅
Tool Execution: params={} ❌
Result: validation error - workflow_id required
```

**Fix necessario**: SupervisorDecision deve includere campo `params` in model_dump()

---

## ✅ COMPONENTI TESTATI

- ✅ Fast-Path: FUNZIONA (DANGER/GREETING detection)
- ✅ Classifier: FUNZIONA (9 categorie, 100% accuracy su univoche)
- ✅ Tool Mapper: FUNZIONA (category → tool list)
- ❌ Tool Execution: BUG params vuoti
- ⏳ Responder: Non testato (dipende da tool_results)
- ⏳ Masking: Non testato

---

## 🔧 PROSSIMO FIX

1. Aggiungere campo `params` a SupervisorDecision model
2. Verificare model_dump() includa params
3. Re-run test suite
4. Validare tool execution completa

---

**Version**: v3.5.5
**Last Update**: 2025-10-16 22:30
