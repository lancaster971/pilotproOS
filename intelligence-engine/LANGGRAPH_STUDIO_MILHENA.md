# 🎨 LANGGRAPH STUDIO - MILHENA v3.0

## 🚀 ACCESSO A MILHENA IN LANGGRAPH STUDIO - SOLUZIONE DEFINITIVA

### ⚠️ PROBLEMA RISOLTO: Safari/Brave Blocca HTTP su localhost

Safari e Brave bloccano il traffico HTTP su localhost per motivi di sicurezza. La soluzione ufficiale è usare **Cloudflare Tunnel** che fornisce HTTPS automatico.

---

## 📋 PROCEDURA CORRETTA (FIX DEFINITIVO)

### 1️⃣ **INSTALLA/AGGIORNA LANGGRAPH-CLI**

```bash
pip install -U "langgraph-cli>=0.2.6"
```

### 2️⃣ **AVVIA CON CLOUDFLARE TUNNEL**

```bash
cd /path/to/intelligence-engine
langgraph dev --tunnel
```

Il comando scarica automaticamente `cloudflared` e crea un tunnel HTTPS temporaneo.

### 3️⃣ **USA L'URL GENERATO**

Dopo ~10 secondi vedrai output simile a:

```
🚀 API: https://bargains-logic-agreement-meyer.trycloudflare.com
🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=https://bargains-logic-agreement-meyer.trycloudflare.com
```

**⚠️ IMPORTANTE**: L'URL del tunnel cambia ad ogni avvio! Usa sempre l'URL mostrato nell'output.

### 4️⃣ **APRI LANGGRAPH STUDIO**

Clicca sull'URL **Studio UI** o aprilo manualmente nel browser:

```
https://smith.langchain.com/studio/?baseUrl=https://[IL-TUO-TUNNEL].trycloudflare.com
```

### 5️⃣ **SELEZIONA IL GRAFO MILHENA**

Nel pannello di LangGraph Studio vedrai 2 grafi:
- **`milhena`** ✅ - Grafo Milhena v3.0 completo (9 nodi)
- **`react_agent`** - ReAct agent standard

Clicca su **`milhena`** per visualizzare il workflow!

---

## 📊 GRAFO MILHENA v3.0 - STRUTTURA COMPLETA

### **Nodi del Workflow (9 nodi):**

```
                    [START]
                       ↓
                [check_cache] ──────────────┐
                       ↓                     │
                [disambiguate]               │ (se cached)
                       ↓                     │
                [analyze_intent]             │
                    /  |  \                  │
                   /   |   \                 │
    (technical) /     |     \ (tool_needed)  │
               /      |      \                │
     [handle_error]   |   [tools]            │
                      |       ↓               │
                      |  [select_llm]        │
                      |       ↓               │
                      └─> [generate_response]│
                              ↓               │
                        [mask_response] <────┘
                              ↓
                        [record_feedback]
                              ↓
                            [END]
```

### **Routing Condizionale:**

1. **Cache Hit** → Salta direttamente a `mask_response`
2. **Intent TECHNICAL** → Va a `handle_error` (blocca query tecniche)
3. **Intent TOOL_NEEDED** → Va a `tools` (usa business tools)
4. **Intent BUSINESS** → Va a `select_llm` → `generate_response`

### **Business Tools (3 strumenti):**

1. **`check_business_status`** - Stato processi business
2. **`get_business_metrics`** - Metriche giornaliere
3. **`get_process_info`** - Info su processo specifico

---

## 🧪 TEST IN LANGGRAPH STUDIO

### **Test 1: Query Semplice**

Input JSON:
```json
{
  "messages": [
    {"role": "human", "content": "Ciao Milhena, come stai?"}
  ],
  "query": "Ciao Milhena, come stai?",
  "session_id": "studio-test-001",
  "context": {},
  "disambiguated": false,
  "cached": false,
  "masked": false,
  "token_count": 0
}
```

**Path atteso:** check_cache → disambiguate → analyze_intent → select_llm → generate_response → mask_response → record_feedback

---

### **Test 2: Disambiguazione (Linguaggio Volgare)**

Input JSON:
```json
{
  "messages": [
    {"role": "human", "content": "Il sistema è andato a puttane"}
  ],
  "query": "Il sistema è andato a puttane",
  "session_id": "studio-test-002",
  "context": {},
  "disambiguated": false,
  "cached": false,
  "masked": false,
  "token_count": 0
}
```

**Path atteso:** check_cache → disambiguate (pulisce query) → analyze_intent → select_llm → generate_response → mask_response → record_feedback

**Risultato:** La query viene trasformata in "Il sistema ha problemi di funzionamento"

---

### **Test 3: Query Tecnica (Deflection)**

Input JSON:
```json
{
  "messages": [
    {"role": "human", "content": "Dammi il codice Python del database"}
  ],
  "query": "Dammi il codice Python del database",
  "session_id": "studio-test-003",
  "context": {},
  "disambiguated": false,
  "cached": false,
  "masked": false,
  "token_count": 0
}
```

**Path atteso:** check_cache → disambiguate → analyze_intent → **handle_error** (END)

**Risultato:** "Per informazioni tecniche, contatta il team IT."

---

### **Test 4: Tool Usage**

Input JSON:
```json
{
  "messages": [
    {"role": "human", "content": "Qual è lo stato del sistema?"}
  ],
  "query": "Qual è lo stato del sistema?",
  "session_id": "studio-test-004",
  "context": {},
  "disambiguated": false,
  "cached": false,
  "masked": false,
  "token_count": 0
}
```

**Path atteso:** check_cache → disambiguate → analyze_intent → **tools** → generate_response → mask_response → record_feedback

**Risultato:** Usa `check_business_status` per ottenere info reali

---

## 🔍 DEBUG IN LANGGRAPH STUDIO

### **Visualizzazione Real-time:**

- **Nodi Verdi** ✅ = Eseguiti con successo
- **Nodi Gialli** 🟡 = In esecuzione
- **Nodi Rossi** ❌ = Errore
- **Frecce Blu** → = Percorso seguito

### **State Inspector:**

Clicca su qualsiasi nodo per vedere:
- **Input State** - Stato prima dell'esecuzione
- **Output State** - Stato dopo l'esecuzione
- **Execution Time** - Tempo impiegato
- **LLM Calls** - Chiamate AI (se presenti)

### **Modifica Live:**

1. Clicca su un nodo già eseguito
2. Modifica lo state (es. cambia `intent`)
3. Clicca **"Replay from here"**
4. Il grafo ripartirà da quel punto con il nuovo state!

---

## 🎯 FEATURES MILHENA v3.0

### **1. Multi-LLM Strategy**

Il nodo `select_llm` sceglie automaticamente:
- **GROQ** (llama-3.3-70b) per query <10 parole (FREE)
- **OpenAI** (gpt-4o-mini) per query complesse

Visibile nello state come `llm_choice`.

### **2. Disambiguazione Intelligente**

Il nodo `disambiguate` pulisce linguaggio volgare:
- "puttane" → query pulita
- "cazzo" → query pulita
- "merda" → query pulita

### **3. Masking Tecnico**

Il nodo `mask_response` maschera termini tecnici:
- database → archivio dati
- API → interfaccia
- server → sistema
- PostgreSQL → sistema di archiviazione
- Redis → sistema di cache
- Docker → ambiente

### **4. Learning System**

Il nodo `record_feedback` registra ogni interazione con:
- Session ID
- Query originale
- Intent classificato
- LLM usato
- Token consumati

### **5. LangSmith Tracing**

Ogni nodo ha decorator `@traceable` per tracciamento completo in LangSmith.

---

## ⚠️ TROUBLESHOOTING

### **Problema: "Failed to initialize LangGraph Studio"**

**Causa:** Safari/Brave blocca HTTP su localhost

**Soluzione:** Usa `langgraph dev --tunnel` invece di `langgraph dev`

---

### **Problema: "Cannot connect to API"**

**Causa:** Tunnel non ancora pronto o scaduto

**Soluzione:**
1. Aspetta 10-15 secondi dopo l'avvio
2. Ricarica la pagina del browser
3. Se persiste, ferma (Ctrl+C) e rilancia `langgraph dev --tunnel`

---

### **Problema: "Graph not found"**

**Causa:** File `langgraph.json` non punta al grafo corretto

**Soluzione:** Verifica che `langgraph.json` contenga:
```json
{
  "dependencies": ["."],
  "graphs": {
    "milhena": "./app/milhena_complete.py:graph",
    "react_agent": "./app/graph.py:graph"
  },
  "env": ".env"
}
```

---

### **Problema: Tunnel scade dopo un po'**

**Causa:** I tunnel gratuiti di Cloudflare hanno timeout

**Soluzione:** Questo è normale. Riavvia semplicemente con `langgraph dev --tunnel` quando serve.

---

## 📚 FILE CHIAVE

- **`app/milhena_complete.py`** - Grafo completo Milhena v3.0
- **`langgraph.json`** - Configurazione LangGraph Studio
- **`.env`** - API keys (OPENAI_API_KEY, GROQ_API_KEY, LANGCHAIN_API_KEY)

---

## 🚀 COMANDI RAPIDI

```bash
# Avvia con tunnel (RACCOMANDATO)
langgraph dev --tunnel

# Avvia porta specifica + tunnel
langgraph dev --port 8080 --tunnel

# Aggiorna langgraph-cli
pip install -U langgraph-cli

# Controlla versione
langgraph --version
```

---

## 🎉 RISULTATO FINALE

Con **Cloudflare Tunnel** hai:

✅ **HTTPS automatico** - Nessun problema con Safari/Brave
✅ **Accesso universale** - Funziona su tutti i browser
✅ **Setup zero** - Nessuna configurazione manuale
✅ **Debugging completo** - Visualizza ogni nodo in real-time
✅ **Grafo completo** - Tutti i 9 nodi + 3 tools + routing condizionale

**Milhena v3.0 è ora completamente operativa in LangGraph Studio!** 🚀