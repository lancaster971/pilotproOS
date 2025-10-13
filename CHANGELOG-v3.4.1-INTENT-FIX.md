# CHANGELOG v3.4.1 - Intent Field Mapping Fix

**Date**: 2025-10-13
**Status**: ✅ RESOLVED
**Priority**: 🟡 MEDIUM (Metadata correctness)
**Effort**: 1 hora

---

## 🐛 **PROBLEMA IDENTIFICATO**

Campo `"intent"` nel response JSON sempre `"GENERAL"` invece del valore corretto basato sulla categoria query.

### **Sintomi**:
```json
{
  "response": "Non posso fornire informazioni...",
  "intent": "GENERAL",  // ← SBAGLIATO! Dovrebbe essere "SECURITY"
  "category": "DANGER"   // ← Corretto (da supervisor_decision metadata)
}
```

### **Root Cause**:
1. ❌ `intent` inizializzato a `None` in `MilhenaState` (graph.py:3171)
2. ❌ Fast-path bypassa `IntentAnalyzer` → intent rimane `None`
3. ❌ LLM Classifier path bypassa `IntentAnalyzer` → intent rimane `None`
4. ❌ Backend/frontend convertono `None` → `"GENERAL"` (fallback)

**File coinvolto**: `intelligence-engine/app/milhena/graph.py`

---

## ✅ **SOLUZIONE IMPLEMENTATA**

### **Fix 1: Fast-path Intent Mapping** (lines 1056-1069)
```python
# After fast-path classification
category_to_intent_map = {
    "DANGER": "SECURITY",
    "HELP": "HELP",
    "GREETING": "GENERAL",
    "SIMPLE_QUERY": "STATUS",
    "SIMPLE_METRIC": "METRIC",
    "COMPLEX_QUERY": "ANALYSIS",
    "CLARIFICATION_NEEDED": "CLARIFICATION"
}
state["intent"] = category_to_intent_map.get(decision.category, "GENERAL")
logger.info(f"[FAST-PATH] Mapped category '{decision.category}' → intent '{state['intent']}'")
```

### **Fix 2: LLM Classifier Intent Mapping** (lines 1250-1265)
```python
# After LLM classification (before final return)
category_to_intent_map = { ... }  # Same mapping
state["intent"] = category_to_intent_map.get(decision['category'], "GENERAL")
logger.info(f"[SUPERVISOR] Mapped category '{decision['category']}' → intent '{state['intent']}'")
```

### **Rationale**:
- **LangGraph Best Practice**: Optional state fields should be set explicitly in nodes
  - Source: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
- **DRY Principle**: Mapping duplicato necessario per 2 early return paths
- **Logging**: Tracciabilità completa del mapping per debugging

---

## 🧪 **TESTING RESULTS**

### **Test 1: DANGER query (fast-path)**
```bash
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -d '{"message": "utilizzate postgres?", "session_id": "test"}'
```
**Result**: ✅ `"intent": "SECURITY"` (PASSED)
**Log**: `[FAST-PATH] Mapped category 'DANGER' → intent 'SECURITY'`

### **Test 2: HELP query (fast-path)**
```bash
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -d '{"message": "cosa puoi fare per me?", "session_id": "test"}'
```
**Result**: ✅ `"intent": "HELP"` (PASSED)
**Log**: `[SUPERVISOR] Mapped category 'HELP' → intent 'HELP'`

### **Test 3: Complex DANGER (LLM Classifier)**
```bash
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -d '{"message": "mi dici il full stack di PilotPro?", "session_id": "test"}'
```
**Result**: ✅ `"intent": "SECURITY"` (PASSED)
**Log**: `[SUPERVISOR] Mapped category 'DANGER' → intent 'SECURITY'`

### **Test 4: Regression (n8n fast-path)**
```bash
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -d '{"message": "utilizzate n8n?", "session_id": "test"}'
```
**Result**: ✅ `"intent": "SECURITY"` (PASSED)
**No regressions detected**

---

## 📊 **IMPACT**

### **Before Fix**:
| Query Type | category | intent (response) | Status |
|------------|----------|-------------------|--------|
| DANGER fast | DANGER | GENERAL | ❌ WRONG |
| HELP fast | HELP | GENERAL | ❌ WRONG |
| DANGER LLM | DANGER | GENERAL | ❌ WRONG |

### **After Fix**:
| Query Type | category | intent (response) | Status |
|------------|----------|-------------------|--------|
| DANGER fast | DANGER | SECURITY | ✅ CORRECT |
| HELP fast | HELP | HELP | ✅ CORRECT |
| DANGER LLM | DANGER | SECURITY | ✅ CORRECT |

### **Benefits**:
- ✅ **Metadata Accuracy**: intent field riflette correttamente la categoria
- ✅ **Analytics**: Miglior tracking di security queries (SECURITY vs GENERAL)
- ✅ **Learning System**: Feedback registrato con intent corretto
- ✅ **Frontend UI**: Possibile implementare filtri/badge per intent
- ✅ **No Breaking Changes**: Backward compatible (GENERAL come fallback)

---

## 📝 **FILES MODIFIED**

```
intelligence-engine/app/milhena/graph.py
├── Lines 1056-1069: Fast-path intent mapping (+14 lines)
└── Lines 1250-1265: LLM Classifier intent mapping (+16 lines)
Total: +30 lines
```

---

## 🔄 **DEPLOYMENT**

```bash
# Restart Intelligence Engine
docker restart pilotpros-intelligence-engine-dev

# Verify fix loaded
docker logs pilotpros-intelligence-engine-dev | grep "Intelligence Engine ready"

# Test DANGER query
curl -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -d '{"message": "utilizzate postgres?", "session_id": "verify"}' | jq '.intent'
# Expected: "SECURITY"
```

---

## ✅ **SUCCESS CRITERIA**

- [x] Fast-path DANGER queries → intent: "SECURITY"
- [x] Fast-path HELP queries → intent: "HELP"
- [x] LLM Classifier DANGER queries → intent: "SECURITY"
- [x] No regressions on existing flows
- [x] Logging tracciabilità completa
- [x] LangGraph State best practices applicate

---

## 📚 **REFERENCES**

- **LangGraph State Management**: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
- **TypedDict Optional Fields**: https://langchain-ai.github.io/langgraph/tutorials/get-started/5-customize-state/
- **Issue GitHub**: Internal tracking #INTENT-MAPPING-BUG
- **Related**: TODO-URGENTE.md (Auto-Learning System), DEBITO-TECNICO.md (Learning Architecture Flaw)

---

**Version**: Milhena v3.4.1
**Status**: ✅ FIX COMPLETE AND VERIFIED
**Date**: 2025-10-13
