# 🧪 Tool Mapper Test Report

**Date**: 2025-10-16 22:35
**Version**: Milhena v3.5.5
**Test Suite**: test-tool-mapper.sh (10 queries)

---

## 📊 RISULTATI

| Test | Category | Tool Atteso | Esito | Nota |
|------|----------|-------------|-------|------|
| 1 | PROCESS_LIST | get_workflows_tool | ✅ CHIAMATO | params vuoti → parziale successo |
| 2 | PROCESS_DETAIL | smart_workflow_query_tool | ❌ FAILED | validation error (workflow_id missing) |
| 3 | EXECUTION_QUERY | smart_executions_query_tool | ❌ FAILED | validation error |
| 4 | ERROR_ANALYSIS | get_error_details_tool | ❌ FAILED | validation error |
| 5 | ANALYTICS | smart_analytics_query_tool | ❌ FAILED | validation error |
| 6 | STEP_DETAIL | get_node_execution_details_tool | ❌ FAILED | 2 validation errors |
| 7 | EMAIL_ACTIVITY | get_chatone_email_details_tool | ❌ FAILED | validation error |
| 8 | PROCESS_ACTION | toggle_workflow_tool | ❌ FAILED | 2 validation errors |
| 9 | SYSTEM_OVERVIEW | get_full_database_dump | ❌ FAILED | validation error |
| 10 | CLARIFICATION_NEEDED | direct_response | ✅ NO TOOL | comportamento corretto |

**Score**: 1/10 tool eseguiti con successo (10% pass rate)

---

## 🐛 BUG IDENTIFICATI

### **BUG #1: Tool Execution sync/async** ✅ FIXATO

**Problema**: Tool chiamati con `tool_fn.invoke()` (sync) invece di `await tool_fn.ainvoke()` (async)

**Errore**:
```
StructuredTool does not support sync invocation
```

**Fix applicato** (graph.py:2338):
```python
# PRIMA (sync - ERRATO)
result = tool_fn.invoke(params)

# DOPO (async - CORRETTO)
result = await tool_fn.ainvoke(params)
```

**Status**: ✅ RISOLTO

---

### **BUG #2: Params non passati ai tool** ⚠️ DA FIXARE

**Problema**: Tool ricevono sempre `params={}` vuoto nonostante Classifier li ritorni correttamente

**Evidenza dai log**:
```
[CLASSIFIER] Parsed: params={'workflow_id': 'GESTIONE_LEAD'} ✅
[TOOL EXECUTION] category=PROCESS_DETAIL, params={} ❌
```

**Root Cause**: `state["supervisor_decision"]` non contiene campo `params`

**Linea problematica** (graph.py:2314):
```python
params = classification.get("params", {})  # ← Sempre {}
```

**Fix necessario**: Aggiungere campo `params` al model SupervisorDecision

**Status**: ⚠️ DA IMPLEMENTARE

---

## ✅ COMPONENTI VALIDATI

### **1. Fast-Path** ✅
- DANGER keywords detection: FUNZIONA
- GREETING keywords detection: FUNZIONA
- Fallback a Classifier: FUNZIONA

### **2. Classifier** ✅
- 9 categorie riconosciute correttamente (100% accuracy su query univoche)
- Confidence score calcolato
- Reasoning fornito
- **Params generati ma persi nel flusso** ⚠️

### **3. Tool Mapper** ✅
- `map_category_to_tools()` funzione eseguita
- 9 mapping statici corretti:
  - PROCESS_LIST → get_workflows_tool ✅
  - PROCESS_DETAIL → smart_workflow_query_tool ✅
  - ERROR_ANALYSIS → get_error_details_tool ✅
  - (altri 6 verificati) ✅

### **4. Tool Execution** ❌
- Async fix applicato ✅
- Params vuoti causano validation errors ❌
- Try/catch per error handling ✅

### **5-6. Responder + Masking** ⏳
- Non testati (dipendono da tool_results validi)

---

## 🔧 AZIONI NECESSARIE

1. **FIX params bug** (priorità ALTA)
   - File: intelligence-engine/app/milhena/graph.py
   - Cercare SupervisorDecision model definition
   - Aggiungere campo `params: Dict[str, Any] = {}`
   - Verificare model_dump() includa params

2. **Re-run test suite completo**
   - Eseguire ./test-tool-mapper.sh
   - Verificare 9/10 tool execution success

3. **Test Responder + Masking**
   - Creare test suite dedicato
   - Validare output user-friendly
   - Verificare masking termini tecnici

---

## 📂 FILE MODIFICATI

### test-tool-mapper.sh (NEW)
- 10 test cases con session_id univoci
- Output colorato con grep classification/tool
- Expected tool validation

### graph.py (MODIFIED)
- Linea 2338: `invoke()` → `await ainvoke()`
- Linee 2337-2352: Try/catch per error handling granulare

### CONTEXT-SYSTEM.md (REWRITTEN)
- Architettura visuale ASCII
- 6 componenti documentati
- Bug section con root cause

---

## 📈 METRICHE

**Test Duration**: ~3 minuti (10 query × 2-3s cadauna)
**Container Restarts**: 1 (dopo async fix)
**Log Lines Analyzed**: ~500
**Bugs Found**: 2 (1 fixato, 1 pending)

---

**Conclusione**: Tool Mapper FUNZIONA correttamente. Il bug è in Tool Execution (params mancanti).

**Next Step**: Fix params bug in SupervisorDecision model → Re-test completo.
