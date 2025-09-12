# 🔴 HARDCODED_ISSUES - Analisi Dettagliata SEC-001

**Branch**: `Sec-001Debug`  
**Data Analisi**: 2025-09-12  
**Severity**: CRITICAL - Production Blocker  
**Impatto**: Sistema non funzionante in produzione

---

## 📊 **EXECUTIVE SUMMARY**

Il progetto PilotProOS contiene **valori hardcoded critici** che impediscono il deployment in produzione. Questi valori sono distribuiti tra frontend e backend, creando un accoppiamento stretto con l'ambiente di sviluppo locale.

### **Statistiche Problema:**
- **🔴 Componenti Critici Affetti**: 3
- **🟡 File con Hardcoding**: 8+
- **⚠️ Occorrenze Totali**: 20+
- **💥 Impatto**: Sistema completamente non funzionale in produzione

---

## 🎯 **COMPONENTI CRITICI AFFETTI**

### **1. Business Intelligence Service** ⚠️
- **File**: `backend/src/services/business-intelligence.service.js`
- **Linea**: 985
- **Valore Hardcoded**: `http://localhost:11434`
- **Servizio**: Ollama AI (MORTO/FALLITO)

### **2. API Client** 🔴 CRITICO
- **File**: `frontend/src/services/api-client.ts`
- **Linea**: 10
- **Valore Hardcoded**: `http://localhost:3001`
- **Servizio**: Backend API

### **3. WebSocket Service** 🔴 CRITICO
- **File**: `frontend/src/services/websocket.ts`
- **Linea**: 14
- **Valore Hardcoded**: `http://localhost:3001`
- **Servizio**: Real-time updates

---

## 🔍 **ANALISI DETTAGLIATA PER COMPONENTE**

### **1️⃣ Business Intelligence Service (Ollama)**

#### **Codice Problematico:**
```javascript
// Line 985 - business-intelligence.service.js
async callLocalOllama(prompt) {
  try {
    const response = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'gemma:2b',
        prompt: prompt,
        stream: false
      })
    });
```

#### **Problemi:**
- ❌ URL Ollama hardcoded su localhost:11434
- ❌ Modello AI hardcoded (gemma:2b)
- ❌ Nessun fallback se Ollama non esiste
- ❌ Progetto Ollama dichiarato FALLITO dall'utente

#### **Impatto:**
- Timeline AI analysis non funzionante
- Errori silenti nei log
- Feature "AI-assisted summaries" non disponibile

#### **Dove viene usato:**
- `Line 397`: `const aiResponse = await this.callLocalOllama(prompt);`
- Timeline processing per dati > 500KB

#### **Soluzione Proposta:**
```javascript
// ELIMINARE completamente Ollama
async processWithAI(data) {
  // Ritornare dati mock o usare solo pattern matching
  return {
    summary: "AI analysis temporarily unavailable",
    confidence: "low"
  };
}
```

---

### **2️⃣ API Client (Frontend → Backend)**

#### **Codice Problematico:**
```typescript
// Line 9-14 - api-client.ts
const baseFetch = ofetch.create({
  baseURL: 'http://localhost:3001',  // 🔴 HARDCODED!
  headers: {
    'Content-Type': 'application/json'
  }
})
```

#### **Problemi:**
- ❌ Backend URL hardcoded
- ❌ Non usa `api-config.ts` che ha già la logica Docker/Local
- ❌ Ogni API call fallisce in produzione
- ❌ CORS errors quando deployed

#### **Impatto:**
- 🔴 **TOTALE**: Frontend non può comunicare con backend
- Login non funziona
- Dashboard vuota
- Nessun dato caricato

#### **File api-config.ts ESISTENTE ma IGNORATO:**
```typescript
// api-config.ts - GIÀ PRESENTE MA NON USATO!
const isDocker = window.location.hostname !== 'localhost' 
export const API_BASE_URL = isDocker 
  ? 'http://pilotpros-backend-dev:3001'  // Docker
  : 'http://localhost:3001'              // Local
```

#### **Soluzione Proposta:**
```typescript
// api-client.ts - USARE api-config!
import { API_BASE_URL } from '../utils/api-config'

const baseFetch = ofetch.create({
  baseURL: API_BASE_URL,  // ✅ Usa configurazione dinamica
  headers: {
    'Content-Type': 'application/json'
  }
})
```

---

### **3️⃣ WebSocket Service (Real-time Updates)**

#### **Codice Problematico:**
```typescript
// Line 14 - websocket.ts
connect() {
  this.socket = io('http://localhost:3001', {  // 🔴 HARDCODED!
    withCredentials: true,
    transports: ['websocket', 'polling']
  });
}
```

#### **Problemi:**
- ❌ WebSocket URL hardcoded
- ❌ Non usa configurazione centralizzata
- ❌ Real-time updates non funzionano in produzione

#### **Impatto:**
- Nessun aggiornamento real-time
- Dashboard non si aggiorna automaticamente
- Notifiche non arrivano

#### **Soluzione Proposta:**
```typescript
// websocket.ts - Usa API_BASE_URL
import { API_BASE_URL } from '../utils/api-config'

connect() {
  this.socket = io(API_BASE_URL, {  // ✅ Configurazione dinamica
    withCredentials: true,
    transports: ['websocket', 'polling']
  });
}
```

---

## 📋 **ALTRI HARDCODING TROVATI**

### **Backend - server.js**
```javascript
// Linee multiple con hardcoding
Line 76:  host: process.env.DB_HOST || 'localhost',
Line 122-126: CORS origins hardcoded:
  'http://localhost:3000',
  'http://localhost:5173',
  'http://127.0.0.1:3000',
  'http://127.0.0.1:5173'
Line 382: await fetch('http://localhost:5678/rest/active-workflows');
Line 2222: const n8nUrl = process.env.N8N_URL || 'http://localhost:5678';
```

### **Backend - websocket.js**
```javascript
Line 8: origin: ["http://localhost:3000", "http://localhost:5173"],
```

### **Backend - database.js**
```javascript
Line 67: host: env.DB_HOST || 'localhost',
```

### **Frontend - Altri Componenti**
- `SettingsPage.vue` - Riferimenti localhost nei commenti
- `TimelineModal.vue` - Possibili URL hardcoded per export

---

## 🚨 **RISK ASSESSMENT**

### **Cosa succede modificando questi valori:**

#### **🔴 RISCHIO ALTO - API Client**
- **Se modificato male**: Frontend completamente rotto
- **Sintomi**: Schermata bianca, nessun dato, login fallito
- **Recovery**: Ripristinare valore originale

#### **🟡 RISCHIO MEDIO - WebSocket**
- **Se modificato male**: Solo real-time non funziona
- **Sintomi**: Dashboard statica, no notifiche
- **Recovery**: App funziona ma senza updates

#### **🟢 RISCHIO BASSO - Ollama**
- **Se modificato male**: Solo AI summaries non funzionano
- **Sintomi**: Timeline mostra dati raw invece di riassunti
- **Recovery**: Feature già non funzionante

---

## 🛠️ **PIANO DI RISOLUZIONE SICURO**

### **Fase 1: Preparazione** (Non rompe nulla)
1. ✅ Verificare che `api-config.ts` funzioni correttamente
2. ✅ Testare logica Docker detection
3. ✅ Backup del branch main funzionante

### **Fase 2: Fix Incrementali** (Uno alla volta)

#### **Step 1 - Rimuovere Ollama** (RISCHIO: Zero)
```javascript
// Sostituire callLocalOllama con funzione stub
async callLocalOllama(prompt) {
  return {
    summary: "AI temporarily disabled",
    confidence: "low"
  };
}
```

#### **Step 2 - Fix API Client** (RISCHIO: Alto, ma reversibile)
```typescript
// In api-client.ts
import { API_BASE_URL } from '../utils/api-config'
// Sostituire 'http://localhost:3001' con API_BASE_URL
```
**Test immediato**: Login deve funzionare

#### **Step 3 - Fix WebSocket** (RISCHIO: Medio)
```typescript
// In websocket.ts
import { API_BASE_URL } from '../utils/api-config'
// Sostituire 'http://localhost:3001' con API_BASE_URL
```
**Test immediato**: Check console per "WebSocket connected"

### **Fase 3: Testing**
1. ✅ Login funziona
2. ✅ Dashboard mostra dati
3. ✅ WebSocket connesso (check console)
4. ✅ Timeline carica (anche senza AI)

---

## 💡 **RACCOMANDAZIONI**

### **IMMEDIATE (Prima di toccare il codice):**
1. **NON** modificare tutti i file contemporaneamente
2. **NON** cambiare CORS finché frontend non funziona
3. **NON** toccare database connection strings per ora

### **APPROCCIO CONSIGLIATO:**
1. **Branch separato** per ogni fix
2. **Test dopo OGNI modifica**
3. **Commit frequenti** per rollback facile
4. **Docker restart** dopo ogni cambio backend

### **ORDINE DI PRIORITÀ:**
1. 🟢 **Prima**: Rimuovere Ollama (non critico)
2. 🔴 **Secondo**: Fix API Client (critico ma testabile)
3. 🟡 **Terzo**: Fix WebSocket (importante ma non bloccante)
4. ⚪ **Dopo**: Altri hardcoding minori

---

## 📝 **NOTE TECNICHE**

### **Perché api-config.ts non viene usato:**
Il file `api-config.ts` è stato creato con la logica corretta per gestire Docker vs Local, ma `api-client.ts` è stato probabilmente scritto prima o da un altro developer e non è mai stato aggiornato per usare la configurazione centralizzata.

### **Pattern da seguire:**
```typescript
// ✅ GIUSTO - Configurazione centralizzata
import { API_BASE_URL } from '../utils/api-config'
const url = API_BASE_URL

// ❌ SBAGLIATO - Hardcoded
const url = 'http://localhost:3001'
```

### **Environment Variables disponibili:**
- `VITE_API_URL` - Per override manuale del backend URL
- `NODE_ENV` - Per detection development/production
- `FRONTEND_URL` - Per CORS configuration

---

## 🎯 **CONCLUSIONI**

Il problema SEC-001 è **risolvibile** ma richiede **attenzione** per non rompere il sistema funzionante. L'approccio incrementale con test immediati dopo ogni modifica è fondamentale.

**Tempo stimato**: 2-4 ore con testing completo
**Rischio**: Alto se fatto male, Basso se seguito il piano
**Beneficio**: Sistema deployabile in produzione

---

**Documento creato**: 2025-09-12  
**Branch di lavoro**: `Sec-001Debug`  
**Autore**: Development Team  
**Status**: 🔴 Da risolvere