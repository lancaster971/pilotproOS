# 📋 SEC-001: Guida Migrazione - Rimozione Valori Hardcoded

## 🎯 Obiettivo
Risoluzione del debito tecnico **SEC-001** per rimuovere tutti i valori hardcoded dal codebase e centralizzare la configurazione tramite variabili d'ambiente.

## ✅ Modifiche Completate

### 1. **Rimozione Ollama**
- ✅ Rimosso completamente il progetto Ollama dal codebase
- ✅ Funzione `callLocalOllama` sostituita con `callLocalAI` (placeholder)
- ✅ Rimossi riferimenti da `.env.example` e documentazione

### 2. **Backend Configuration**
#### File modificati:
- `backend/src/server.js`
- `backend/src/websocket.js`
- `backend/src/db/connection.js`

#### Nuove variabili d'ambiente aggiunte:
```bash
# Application
BACKEND_HOST=127.0.0.1
BACKEND_PORT=3001
FRONTEND_URL=http://localhost:3000

# Database Pool
DB_POOL_MAX=20
DB_POOL_IDLE_TIMEOUT=30000
DB_CONNECTION_TIMEOUT=2000

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173

# WebSocket
WEBSOCKET_ORIGINS=http://localhost:3000,http://localhost:5173

# Rate Limiting
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=10000

# Security
JWT_SECRET=pilotpros_jwt_secret_2025_ultra_secure_min_32_chars
JWT_EXPIRY=24h
BCRYPT_ROUNDS=12
```

### 3. **Frontend Configuration**
#### File modificati:
- `frontend/src/services/api-client.ts`
- `frontend/src/utils/api-config.ts`

#### Implementazione:
- Usa `import.meta.env.VITE_API_URL` per configurare l'URL del backend
- Fallback automatico a localhost per development
- Supporto completo per deployment Docker e produzione

### 4. **Files di Configurazione**
- ✅ Creato `.env.example` con template completo
- ✅ Aggiornato `.env` esistente con nuova struttura
- ✅ Docker compose già configurato correttamente

## 🚀 Istruzioni per la Migrazione

### Per Sviluppatori Esistenti

1. **Backup del file .env attuale:**
```bash
cp .env .env.backup
```

2. **Aggiornare il file .env con le nuove variabili:**
```bash
# Confronta con .env.example per vedere tutte le nuove variabili
diff .env .env.example
```

3. **Aggiungere le variabili mancanti al tuo .env:**
```bash
# Variabili critiche da aggiungere:
BACKEND_HOST=127.0.0.1
BACKEND_PORT=3001
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173
WEBSOCKET_ORIGINS=http://localhost:3000,http://localhost:5173
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=10000
```

4. **Riavviare i servizi:**
```bash
npm run docker:restart
# oppure
docker compose -f docker-compose.dev.yml restart
```

### Per Nuovi Deployment

1. **Copiare il template:**
```bash
cp .env.example .env
```

2. **Configurare le variabili per il tuo ambiente:**
- Modificare URLs per produzione
- Impostare password sicure
- Configurare domini corretti

3. **Avviare l'applicazione:**
```bash
npm run dev  # Development
npm run docker:prod  # Production
```

## 🔒 Configurazione Produzione

### Variabili Critiche da Modificare:
```bash
# URLs - Sostituire con domini reali
FRONTEND_URL=https://your-domain.com
BACKEND_URL=https://api.your-domain.com
CORS_ORIGINS=https://your-domain.com
WEBSOCKET_ORIGINS=https://your-domain.com

# Security - Generare valori sicuri
JWT_SECRET=[generare stringa random 64+ caratteri]
DB_PASSWORD=[password sicura]
N8N_ADMIN_PASSWORD=[password sicura]

# Performance - Tunare per produzione
RATE_LIMIT_WINDOW_MS=900000  # 15 minuti
RATE_LIMIT_MAX_REQUESTS=100  # 100 richieste per IP
BCRYPT_ROUNDS=12  # Aumentare per maggior sicurezza
```

### Generare Secret Sicuri:
```bash
# JWT Secret
openssl rand -base64 64

# Database Password
openssl rand -base64 32
```

## 🐳 Docker Configuration

Il Docker Compose è già configurato per usare le variabili d'ambiente:

```yaml
# docker-compose.dev.yml esempio
backend-dev:
  environment:
    - NODE_ENV=${NODE_ENV}
    - BACKEND_PORT=${BACKEND_PORT}
    - DB_HOST=${DB_HOST}
    - CORS_ORIGINS=${CORS_ORIGINS}
    # ... altre variabili
```

## ⚠️ Breaking Changes

### Rimozione Ollama
- La funzionalità AI tramite Ollama è stata disabilitata
- Il Business Intelligence Service ritorna ora risposte placeholder
- Per riattivare AI, sarà necessario integrare un servizio alternativo (es. Claude API)

### Pool di Connessione
- Il pool di connessione database ora usa variabili configurabili
- Default: max=20, idle=30s, timeout=2s
- Tunare secondo il carico previsto

## 🔍 Verifica Post-Migrazione

### Test Checklist:
- [ ] Backend avvia senza errori
- [ ] Frontend si connette al backend
- [ ] Database connection pool funziona
- [ ] CORS permette richieste dal frontend
- [ ] WebSocket si connette correttamente
- [ ] Rate limiting attivo
- [ ] Nessun valore hardcoded nei log

### Comandi di Test:
```bash
# Test backend
cd backend && npm run dev

# Test frontend  
cd frontend && npm run dev

# Test completo con Docker
npm run dev

# Verificare configurazione
grep -r "localhost" backend/src --exclude-dir=node_modules
grep -r "3001\|3000\|5432" backend/src --exclude-dir=node_modules
```

## 📊 Benefici della Migrazione

1. **Sicurezza**: Nessun valore sensibile hardcoded nel codice
2. **Flessibilità**: Configurazione per ambiente senza modificare codice
3. **Manutenibilità**: Configurazione centralizzata in un unico file
4. **Scalabilità**: Facile deployment in diversi ambienti
5. **Best Practices**: Allineamento agli standard enterprise

## 🆘 Troubleshooting

### Errore: "Invalid URL" nel backend
- Verificare che tutte le variabili DB_* siano impostate nel .env
- Controllare che non ci siano spazi nelle variabili

### Errore: CORS blocked
- Verificare che CORS_ORIGINS includa l'URL del frontend
- Controllare che gli URL non abbiano trailing slash

### WebSocket non si connette
- Verificare WEBSOCKET_ORIGINS
- Controllare che il backend sia raggiungibile

## 📝 Note Finali

Questa migrazione risolve completamente il debito tecnico **SEC-001** identificato nell'analisi dei debiti tecnici. Il sistema è ora pronto per deployment in qualsiasi ambiente con semplice configurazione del file `.env`.

Per domande o problemi, consultare la documentazione principale in `/docs` o aprire una issue su GitHub.

---

**Data Completamento**: 2025-09-12  
**Branch**: `sec-001`  
**Status**: ✅ Completato