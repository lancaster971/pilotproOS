# 🤖 DEMO: Milhena Assistant nel CLI Agent Engine

**Milhena è ora integrata nel CLI Agent Engine!**

## 🚀 Come usare Milhena

### 1. Avvia il CLI
```bash
python3 cli.py
```

### 2. Seleziona opzione 4
```
Menu Principale
┌─────┬───────────────────────────────────────────────────────┐
│  1  │ Chat Assistant - Parla con l'assistente AI           │
│  2  │ Business Analysis - Analisi processo con multi-agent │
│  3  │ Quick Insights - Insights rapidi su domande business │
│  4  │ 🤖 Milhena Assistant - Assistente business PilotProOS│  ← SCEGLI QUESTA
│  5  │ Demo - Visualizza gli agent al lavoro                │
│  6  │ Status - Stato del sistema                           │
│  q  │ ESCI DAL PROGRAMMA                                   │
└─────┴───────────────────────────────────────────────────────┘

Scegli opzione (q per uscire completamente) [1]: 4
```

### 3. Interagisci con Milhena

#### 🔸 Modalità Multi-Agent (Default)
```
🤖 ======= MILHENA ASSISTANT =======
Domanda per Milhena: Quante esecuzioni abbiamo avuto oggi?

🤖 Milhena (Multi-Agent Mode) sta elaborando...

🤖 Milhena Multi-Agent System:
Agenti usati: DATA_ANALYST → SECURITY_FILTER → MILHENA

┌─ Risposta Milhena ──────────────────────────────┐
│ Oggi nel sistema abbiamo registrato un totale  │
│ di 1247 esecuzioni, con un tasso di successo  │
│ del 94,2%. Questi numeri dimostrano un'ottima │
│ performance generale...                        │
└────────────────────────────────────────────────┘
```

#### ⚡ Modalità Quick (Singolo Agent)
```
Domanda per Milhena: quick: Ci sono errori nel sistema?

🤖 Milhena (Quick Mode) sta elaborando...

🤖 Milhena Quick Mode:

┌─ Risposta Milhena ──────────────────────────────┐
│ Al momento non sono stati rilevati errori      │
│ critici nel sistema. Le performance sono       │
│ nella norma con un tasso di successo del 94%   │
└────────────────────────────────────────────────┘
```

## 🎯 Esempi di domande per Milhena

### 📊 Domande su Performance
- "Quante esecuzioni abbiamo avuto oggi?"
- "Come stanno andando i nostri processi?"
- "Ci sono problemi di performance?"

### ❗ Domande su Errori
- "Ci sono errori nel sistema?"
- "Quali processi stanno fallendo?"
- "Come possiamo migliorare l'affidabilità?"

### 📈 Domande di Analisi
- "Mostrami le performance di questa settimana"
- "Quale workflow sta performando meglio?"
- "Abbiamo miglioramenti da fare?"

## 🔄 Modalità Disponibili

### 🔸 **Multi-Agent Mode (Default)**
- **Agenti**: DATA_ANALYST → SECURITY_FILTER → MILHENA
- **Processo**: Raccolta dati → Filtraggio tecnologico → Risposta italiana
- **Uso**: Analisi complesse e dettagliate
- **Comando**: Scrivi la domanda normalmente

### ⚡ **Quick Mode**
- **Agenti**: Solo MILHENA
- **Processo**: Risposta diretta e veloce
- **Uso**: Domande semplici e veloci
- **Comando**: `quick: la tua domanda`

## 🚪 Come uscire
- Scrivi: `exit`, `quit`, `q`, `uscire`, `stop`, `basta`
- Premi: `CTRL+C`

## 🎯 Caratteristiche Milhena

### ✅ **Technological Masking**
- Mai rivela tecnologie sottostanti (n8n, PostgreSQL, etc.)
- Usa solo terminologia business italiana
- Trasforma automaticamente termini tecnici

### 🇮🇹 **Lingua Italiana Professionale**
- Risponde sempre in italiano business
- Tono professionale ma amichevole
- Consigli proattivi e suggerimenti

### 🤖 **Multi-Agent Intelligence**
- Sistema sequenziale a 3 livelli
- Adaptive LLM selection per ogni agente
- Fallback robusto con mock data

## 🧪 Test Status

**✅ Sistema completamente operativo!**

```bash
# Test completo eseguito con successo
python3 test_milhena_cli.py

📊 SUMMARY: Milhena integration ready!
🎉 ALL CORE COMPONENTS WORKING!
```

---

**🚀 MILHENA È PRONTA PER L'USO NEL CLI!**

Esegui `python3 cli.py` e seleziona l'opzione 4 per iniziare! 🎉