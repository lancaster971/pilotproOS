# 🎨 LANGGRAPH STUDIO - MILHENA v3.0

## 🚀 COME ACCEDERE A MILHENA IN LANGGRAPH STUDIO

### 1️⃣ **VERIFICA CHE IL SISTEMA SIA RUNNING**
```bash
docker ps | grep intelligence
# Deve mostrare: pilotpros-intelligence-engine-dev running sulla porta 2024
```

### 2️⃣ **ACCEDI A LANGGRAPH STUDIO**

#### **Opzione A: Link Diretto (Chrome/Chromium)**
```
http://localhost:2024
```

#### **Opzione B: Via LangSmith (Tutti i browser)**
```
https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

Con il tuo organization ID:
```
https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024&organizationId=21becea4-64dc-4805-8f62-afa4108504db
```

### 3️⃣ **SELEZIONA IL GRAFO MILHENA**

Una volta in Studio, vedrai 2 grafi disponibili:
- **`milhena`** - Il grafo Milhena v3.0 Business Assistant ✨
- **`react_agent`** - Il ReAct agent standard

**Clicca su `milhena`** per aprire il grafo!

## 📊 **COSA VEDRAI NEL GRAFO MILHENA**

### **Nodi del Workflow:**
```
[Start] → [check_cache] → [disambiguate] → [analyze_intent]
                ↓                              ↓
            [mask_response]            [generate_response]
                ↓                              ↓
          [record_feedback]           [handle_error]
                ↓                              ↓
              [End]                          [End]
```

### **Routing Condizionale:**
- **Cache Hit** → Salta direttamente a mask_response
- **Intent TECHNICAL** → Va a handle_error (deflects)
- **Intent BUSINESS** → Procede con generate_response

## 🧪 **TEST IN LANGGRAPH STUDIO**

### **1. Test Base**
Nella sezione **Input** di Studio, inserisci:
```json
{
  "messages": [
    {
      "role": "human",
      "content": "Ciao Milhena, come stai?"
    }
  ],
  "query": "Ciao Milhena, come stai?",
  "session_id": "studio-test-001",
  "context": {}
}
```

### **2. Test Disambiguazione**
```json
{
  "messages": [
    {
      "role": "human",
      "content": "Il sistema è andato a puttane"
    }
  ],
  "query": "Il sistema è andato a puttane",
  "session_id": "studio-test-002",
  "context": {}
}
```

### **3. Test Cache**
Ripeti la stessa query due volte - la seconda dovrebbe essere cached!

## 🔍 **DEBUGGING IN STUDIO**

### **Visualizzazione Real-time:**
- **Nodi Verdi** = Eseguiti con successo
- **Nodi Gialli** = In esecuzione
- **Nodi Rossi** = Errore
- **Frecce Blue** = Percorso seguito

### **State Inspector:**
Clicca su qualsiasi nodo per vedere:
- Input state
- Output state
- Execution time
- LLM calls (se presenti)

### **Modifica Live:**
1. Clicca su un nodo
2. Modifica lo state
3. Clicca **"Replay from here"**
4. Il grafo ripartirà da quel punto!

## 🎯 **FEATURES SPECIALI DI MILHENA IN STUDIO**

### **1. Tracciamento LangSmith**
Ogni esecuzione è tracciata con:
- `@traceable` decorators su ogni nodo
- Metadata con version "3.0"
- Project: `milhena-v3-production`

### **2. Multi-LLM Strategy**
Vedrai nel state quale LLM viene scelto:
- **GROQ** per query semplici (FREE)
- **OpenAI Nano/Mini** per query medie
- **OpenAI Premium** per query complesse

### **3. Learning System**
Il nodo `record_feedback` registra ogni interazione per migliorare nel tempo!

## ⚠️ **TROUBLESHOOTING**

### **Non vedo il grafo Milhena?**
```bash
# Riavvia il container
docker restart pilotpros-intelligence-engine-dev

# Aspetta 10 secondi e ricarica Studio
```

### **Errore "Cannot connect"?**
```bash
# Verifica che il container sia running
docker ps | grep intelligence

# Controlla i logs
docker logs pilotpros-intelligence-engine-dev --tail 50
```

### **Safari/Brave non funziona?**
Usa il link con HTTPS:
```
https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

## 📚 **RISORSE**

- **LangGraph Studio Docs**: https://docs.langchain.com/langgraph-platform/langgraph-studio
- **Milhena Code**: `/app/milhena/graph.py`
- **Config**: `/app/langgraph.json`

## 🎉 **FUNZIONALITÀ COMPLETE**

Con Milhena in LangGraph Studio puoi:
- ✅ **Visualizzare** il workflow completo
- ✅ **Debuggare** ogni nodo step-by-step
- ✅ **Modificare** state in real-time
- ✅ **Testare** diverse query
- ✅ **Vedere** LLM decisions e token usage
- ✅ **Tracciare** tutto in LangSmith
- ✅ **Esportare** traces per analisi

---

**Milhena v3.0 è ora completamente integrata con LangGraph Studio!** 🚀