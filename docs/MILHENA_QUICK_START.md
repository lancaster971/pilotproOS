# 🚀 MILHENA - Quick Start Guide

**Avvia Milhena Multi-Agent AI System in 5 minuti!**

---

## ⚡ **SETUP RAPIDO**

### **Prerequisiti** (2 minuti)
```bash
# 1. Verifica Docker
docker --version
docker-compose --version

# 2. Verifica Node.js (per stack manager)
node --version  # >= 16.x
```

### **Installazione Lampo** (3 minuti)
```bash
# 1. Clone repository
git clone https://github.com/lancaster971/pilotproOS.git
cd pilotproOS
git checkout Milhena

# 2. Configura API keys (GRATUITE)
cd pilotpros-agent-engine
cp .env.example .env

# 3. Modifica .env con le tue chiavi
nano .env
```

**Nel file `.env`:**
```env
# Gemini API (GRATUITA) - Ottieni qui: https://aistudio.google.com/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Groq API (Opzionale per backup) - Ottieni qui: https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key_here
```

### **Avvio Sistema**
```bash
# Torna alla root del progetto
cd ..

# Avvia stack completo
./stack
# Oppure: npm run dev
```

### **Test Funzionamento**
```bash
# Entra nel container agent
docker exec -it pilotpros-agent-engine-dev ./agent-cli

# Seleziona: 4 - 🤖 Milhena Assistant
# Prova: "Ciao!" → Risposta in < 1 secondo!
```

---

## 🎯 **PRIMI PASSI**

### **Conversazione Base**
```
Tu: Ciao Milhena!
🤖: Ciao! Come posso aiutarti oggi con i processi business?

Tu: Come funzioni?
🤖: Sono un assistente AI che può:
    • Analizzare dati business in tempo reale
    • Rispondere a domande sui processi aziendali
    • Fornire statistiche e insights
    • Tradurre dati tecnici in linguaggio comprensibile

Tu: Cosa è successo oggi?
🤖: 📅 **Riepilogo di oggi**:
    📩 Email gestite: 5 | 🧾 Ordini: 2 | 🤖 Interazioni AI: 12
```

### **Domande Business Tipiche**
```
• "Quante email abbiamo ricevuto oggi?"
• "Mostrami le statistiche della settimana"
• "Ci sono stati errori nei processi?"
• "Qual è l'ultima attività registrata?"
• "Analizza il trend delle vendite"
• "Dammi una panoramica generale"
```

### **Performance Attese**
- ⚡ **Saluti/Aiuto**: 200-600ms
- 📊 **Dati Business**: 500-1500ms
- 🔍 **Analisi**: 1-3 secondi
- 💾 **Cache Hit**: < 50ms

---

## 🔧 **CONFIGURAZIONI AVANZATE**

### **Solo Gemini (100% GRATUITO)**
```env
# File .env - Solo Gemini
GEMINI_API_KEY=your_key_here
# GROQ_API_KEY=  # Lascia vuoto
```

### **Performance Massima**
```python
# In pilotpros-agent-engine/cli.py
orchestrator = MilhenaEnterpriseOrchestrator(
    fast_mode=True,          # FastPath abilitato
    enable_cache=True,       # Cache aggressiva
    enable_memory=True,      # Memoria utenti
    enable_analytics=False   # Disabilita per max speed
)
```

### **Debug Mode**
```bash
# Container con logs dettagliati
docker exec pilotpros-agent-engine-dev python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)

from agents.crews.milhena_orchestrator_enterprise import MilhenaEnterpriseOrchestrator
orchestrator = MilhenaEnterpriseOrchestrator(verbose=True)
"
```

---

## 📚 **API USAGE**

### **REST API**
```bash
# Avvia API server (se non già running)
docker exec pilotpros-agent-engine-dev python3 milhena_api.py

# Test API
curl -X POST http://localhost:8089/api/assistant/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Ciao!", "user_id": "demo", "language": "it"}'
```

### **Python Integration**
```python
import asyncio
from agents.crews.milhena_orchestrator_enterprise import MilhenaEnterpriseOrchestrator

async def chat_milhena():
    milhena = MilhenaEnterpriseOrchestrator(fast_mode=True)

    result = await milhena.process_question(
        question="Mostrami le statistiche",
        user_id="demo_user"
    )

    print("🤖:", result['response'])
    print(f"⏱️ {result['response_time_ms']:.0f}ms")

# Esegui
asyncio.run(chat_milhena())
```

---

## 🔍 **TROUBLESHOOTING RAPIDO**

### ❌ **Problemi Comuni**

#### **"API key not valid"**
```bash
# Verifica chiave Gemini
echo $GEMINI_API_KEY

# Test diretto
docker exec pilotpros-agent-engine-dev python3 -c "
import google.generativeai as genai
genai.configure(api_key='YOUR_KEY_HERE')
print('✅ Gemini OK')
"
```

#### **"Container not running"**
```bash
# Verifica containers
docker-compose ps

# Riavvia se necessario
./stack down
./stack
```

#### **"Slow responses"**
```bash
# Check rate limits
# Gemini free: 15 req/min
# Se superato, usa Groq come backup

# Verifica cache
docker exec pilotpros-agent-engine-dev ls -la milhena_persistence/
```

#### **"Database connection error"**
```bash
# Test database
docker exec pilotpros-agent-engine-dev python3 -c "
from tools.business_intelligent_query_tool import BusinessIntelligentQueryTool
tool = BusinessIntelligentQueryTool()
print(tool._run('test connessione'))
"
```

### 🧪 **Test Suite Rapido**
```bash
# Test completo sistema
docker exec pilotpros-agent-engine-dev python3 test_milhena_complete.py

# Test singoli componenti
docker exec pilotpros-agent-engine-dev python3 test_quick.py
```

---

## 🎨 **PERSONALIZZAZIONI**

### **Modifica Risposte**
```python
# In business_intelligent_query_tool.py
def _get_fallback_response(self, question_type: str, language: str) -> str:
    fallbacks = {
        "it": {
            "GREETING": "Ciao! Il tuo messaggio personalizzato qui!",
            # ... altre personalizzazioni
        }
    }
```

### **Aggiungi Nuovi Tipi Domande**
```python
# In gemini_fast_client.py
async def classify_question(self, question: str) -> Dict[str, Any]:
    prompt = f"""Classifica questa domanda:

    Domanda: {question}

    Categorie:
    - GREETING (saluti)
    - HELP (aiuto)
    - BUSINESS_DATA (dati)
    - ANALYSIS (analisi)
    - PREDICTION (previsioni)
    - CUSTOM_TYPE (il tuo tipo personalizzato)

    Rispondi SOLO con la categoria.
    """
```

### **Custom Business Queries**
```python
# In business_intelligent_query_tool.py
def _analyze_and_respond(self, question: str, cursor) -> str:
    question_lower = question.lower()

    # Aggiungi la tua logica personalizzata
    if "vendite" in question_lower:
        return self._get_sales_data(cursor)
    elif "clienti vip" in question_lower:
        return self._get_vip_customers(cursor)
    # ... altre query personalizzate
```

---

## 📈 **MONITORAGGIO**

### **Performance Metrics**
```bash
# Visualizza statistiche
docker exec pilotpros-agent-engine-dev cat milhena_persistence/milhena_stats.json

# Logs in tempo reale
docker exec pilotpros-agent-engine-dev tail -f milhena_persistence/milhena_analytics.log
```

### **Health Check**
```bash
# Status completo sistema
curl http://localhost:8089/health

# Risposta attesa:
# {"status": "healthy", "timestamp": "2025-01-15T10:30:00", ...}
```

### **Memory Usage**
```bash
# Controlla memoria e cache
docker exec pilotpros-agent-engine-dev python3 -c "
import os
print('Cache files:', os.listdir('milhena_persistence/'))

# Dimensioni cache
for f in os.listdir('milhena_persistence/'):
    size = os.path.getsize(f'milhena_persistence/{f}')
    print(f'{f}: {size/1024:.1f}KB')
"
```

---

## 🚀 **NEXT STEPS**

### **Dopo il Setup**
1. **Esplora i dati**: Prova diverse domande business
2. **Personalizza**: Modifica risposte e query
3. **Integra**: Usa API REST nei tuoi sistemi
4. **Monitora**: Traccia performance e usage

### **Documentazione Completa**
- 📖 **[Documentazione Principale](MILHENA_AGENT_DOCUMENTATION.md)**
- 🏗️ **[Architettura Tecnica](MILHENA_TECHNICAL_ARCHITECTURE.md)**
- 🔧 **[Repository GitHub](https://github.com/lancaster971/pilotproOS/tree/Milhena)**

### **Supporto**
- 🐛 **Issues**: [GitHub Issues](https://github.com/lancaster971/pilotproOS/issues)
- 💬 **Community**: Forum sviluppatori
- 📧 **Support**: enterprise@pilotpros.com

---

## ✨ **ESEMPI AVANZATI**

### **Batch Processing**
```python
# Processa multiple domande
questions = [
    "Quante email oggi?",
    "Ci sono errori?",
    "Performance generale?"
]

for q in questions:
    result = await milhena.process_question(q, "batch_user")
    print(f"Q: {q}")
    print(f"A: {result['response'][:100]}...")
    print(f"Time: {result['response_time_ms']:.0f}ms\n")
```

### **Custom Context**
```python
# Aggiungi contesto specifico
result = await milhena.process_question(
    question="Come stiamo andando?",
    user_id="manager_user",
    context="Riunione mensile performance team vendite",
    language="it"
)
```

### **Analytics Integration**
```python
# Traccia metriche personalizzate
from agents.crews.milhena_orchestrator_enterprise import PersistentAnalyticsTracker

analytics = PersistentAnalyticsTracker()
analytics.track_custom_event("business_query", {
    "department": "sales",
    "query_complexity": "high",
    "user_role": "manager"
})
```

---

**🚀 Milhena Quick Start - Powered by PilotProOS**
*In produzione in 5 minuti - Scalabile all'infinito*

**🎯 Prossimo passo:** Prova il sistema con `./stack` e inizia a fare domande!