# 🚀 Dynamic Context System v3.5.0 - SPEC

**Date**: 2025-10-15
**Status**: 🔄 DA IMPLEMENTARE
**Effort**: 4-6 ore

---

## 🎯 OBIETTIVO

Classifier disambigua termini business → Classifica in 9 categorie → Tool execution → Response umana.

---

## 🏗️ ARCHITETTURA (6 COMPONENTI)

```
User Query
  ↓
[1] Fast-Path (<1ms) - DANGER/GREETING keywords → blocco/risposta
  ↓
[2] Classifier Agent (ReAct) - Disambigua + Classifica in 9 categorie
    Tool: get_system_context_tool()
    Output: {category: "PROCESS_DETAIL", confidence: 1.0}
  ↓
[3] Tool Mapper (libreria) - Categoria → Tool(s)
    PROCESS_DETAIL → smart_workflow_query_tool(id)
  ↓
[4] Tool Execution - Chiamata diretta tool
    Result: RAW data (JSON)
  ↓
[5] Responder Agent - RAW data → Linguaggio business umano
  ↓
[6] Masking - Filtra termini proibiti
  ↓
Response
```

---

## 📋 COMPONENTI DETTAGLIO

### **[1] Fast-Path** (ESISTENTE ✅)
**File**: `graph.py:1513-1590`
**Logica**: 53 DANGER keywords + 10 GREETING exact match
**Output**: `{category: "DANGER"/"GREETING"}` o `None`

---

### **[2] Classifier Agent** (DA RIFARE 🔧)
**Tipo**: ReAct Agent (create_react_agent)
**Prompt**: `REACT-PROMPT.md` (USER fornito)
**Tool unico**: `get_system_context_tool()`
**LLM**: Groq llama-3.3-70b

**Compito**:
1. Disambigua query (chiama tool se serve)
2. Classifica in 9 categorie
3. Return: `{category: "X", confidence: 1.0, params: {...}}`

**9 Categorie**:
```
1. PROCESS_LIST      → get_workflows_tool()
2. PROCESS_DETAIL    → smart_workflow_query_tool(id)
3. EXECUTION_QUERY   → smart_executions_query_tool(scope)
4. ERROR_ANALYSIS    → get_error_details_tool(workflow)
5. ANALYTICS         → smart_analytics_query_tool(metric)
6. STEP_DETAIL       → get_node_execution_details_tool()
7. EMAIL_ACTIVITY    → get_chatone_email_details_tool(date)
8. PROCESS_ACTION    → toggle/execute_workflow_tool()
9. SYSTEM_OVERVIEW   → get_full_database_dump(days)
```

**Output JSON**:
```json
{
  "category": "PROCESS_DETAIL",
  "confidence": 1.0,
  "params": {"workflow_id": "CHATBOT_MAIL__SIMPLE"}
}
```

---

### **[3] Tool Mapper** (DA CREARE 🆕)
**Tipo**: Funzione Python (switch/case)
**Input**: `{category, params}`
**Output**: Lista tool function calls

**Esempio**:
```python
def map_category_to_tools(category: str, params: dict) -> List[Callable]:
    mapping = {
        "PROCESS_LIST": [get_workflows_tool],
        "PROCESS_DETAIL": [smart_workflow_query_tool],
        "ERROR_ANALYSIS": [get_error_details_tool],
        # ... 6 altri
    }
    return mapping[category]
```

---

### **[4] Tool Execution** (SEMPLIFICARE 🔧)
**Tipo**: Direct function call (NO agent)
**Input**: Tool functions + params
**Output**: RAW data (JSON/dict)

**Elimina**: ReAct Agent con 18 tools (graph.py:1061-1214)

---

### **[5] Responder Agent** (ESISTENTE ✅)
**File**: `graph.py:1418-1511`
**Input**: RAW data da tools
**Output**: Risposta linguaggio business umano
**LLM**: Groq llama-3.3-70b

---

### **[6] Masking** (ESISTENTE ✅)
**File**: `graph.py:mask_response`
**Logica**: workflow → processo, execution → attività

---

## 📦 TOOL: get_system_context_tool()

**File**: `business_tools.py:3279-3429` (ESISTENTE ✅)
**DB View**: `v_system_context` (migration 005) (ESISTENTE ✅)

**Output JSON** (4 sezioni):
```json
{
  "workflows_attivi": {
    "count": 7,
    "nomi": ["CHATBOT_MAIL__SIMPLE", "GommeGo__Flow_1", ...]
  },
  "dizionario_business": {
    "clienti": {
      "significa": "Email ChatOne",
      "tool": "get_chatone_email_details_tool",
      "dato_reale": "234 email 7gg"
    }
  },
  "statistiche": {
    "esecuzioni_7d": 2217,
    "errori_oggi": 0
  },
  "esempi_uso": [...]
}
```

---

## 🔄 MODIFICHE NECESSARIE

### **1. Sostituire CLASSIFIER_PROMPT** (30 min)
**File**: `graph.py:194-286`
**Azione**: Eliminare CLASSIFIER_PROMPT, usare REACT-PROMPT.md

---

### **2. Rifare Classifier come ReAct Agent** (60 min)
**File**: `graph.py:1216-1376 (supervisor_orchestrator)`
**Azione**:
```python
# Before: LLM + JsonOutputParser
classification = await chain.ainvoke(prompt)

# After: create_react_agent
classifier_agent = create_react_agent(
    model=self.supervisor_llm,
    tools=[get_system_context_tool],
    prompt=REACT_PROMPT  # da REACT-PROMPT.md
)
result = await classifier_agent.ainvoke({"query": query})
```

---

### **3. Creare Tool Mapper** (20 min)
**File**: `graph.py` (nuova funzione)
**Azione**: Funzione switch/case 9 categorie → tools

---

### **4. Eliminare ReAct Agent corrente** (30 min)
**File**: `graph.py:1061-1214`
**Azione**: Rimuovere react_node + loop, sostituire con direct tool calls

---

### **5. Aggiornare Graph Routing** (30 min)
**File**: `graph.py:745-786`
**Azione**:
```
Before:
Classifier → (AMBIGUOUS?) → Context Loader → ReAct → Responder

After:
Fast-Path → Classifier (ReAct) → Tool Mapper → Tool Execution → Responder → Masking
```

---

## ⏱️ TIMELINE

| Task | Time | Risk |
|------|------|------|
| 1. Replace CLASSIFIER_PROMPT | 30 min | 🟢 |
| 2. Classifier = ReAct Agent | 60 min | 🟡 |
| 3. Tool Mapper function | 20 min | 🟢 |
| 4. Remove old ReAct Agent | 30 min | 🟢 |
| 5. Update Graph routing | 30 min | 🟡 |
| 6. Testing (4 test cases) | 60 min | 🟢 |
| **TOTAL** | **4h 30m** | **MID** |

---

## 🧪 TEST CASES

```bash
# Test 1: Disambiguazione
"clienti" → Classifier chiama get_system_context_tool → "Email ChatOne? 234 7gg"

# Test 2: Workflow inesistente
"errori ChatOne" → Classifier verifica → "ChatOne non esiste. Workflow: [lista]"

# Test 3: Query chiara
"errori CHATBOT_MAIL oggi" → PROCESS_DETAIL → tool diretto → risposta

# Test 4: Safety
"password database" → Fast-path DANGER → blocco
```

---

## 📈 BENEFICI

- **Disambiguation**: Workflow names validati (zero hallucination)
- **Clarity**: 9 categorie esplicite (vs generic SIMPLE/COMPLEX)
- **Simplicity**: Tool Mapper (50 righe) vs ReAct Agent (200 righe)
- **Accuracy**: Classifier con context > 95%

---

## 🚨 BREAKING CHANGES

1. ❌ Eliminare CLASSIFIER_PROMPT (194-286)
2. ❌ Eliminare react_system_prompt (831-975)
3. ❌ Eliminare ReAct Agent node (1061-1214)
4. ❌ Eliminare Context Loader node (1378-1416)
5. ✅ Nuovo: Classifier ReAct Agent con REACT-PROMPT.md
6. ✅ Nuovo: Tool Mapper (switch/case)

---

**END** - 90 righe, architettura chiara 🎯
