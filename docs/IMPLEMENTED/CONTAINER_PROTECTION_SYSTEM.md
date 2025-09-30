# 🔒 SISTEMA DI PROTEZIONE CONTAINER

**Sistema completo di protezione contro rebuild accidentali dei container custom**

## 🎯 OBIETTIVO

Evitare i lunghi tempi di rebuild (5-15 minuti) e i problemi di dependency hell per i container personalizzati:
- **Frontend**: Vue 3 + TypeScript + Vite
- **Backend**: Express + JWT + Auth
- **Agent Engine**: CrewAI 0.193.2 + Milhena v4.0

## 🔒 CONTAINER BLINDATI

### Backup Images Locked
```bash
pilotproos-frontend-dev:locked-v1.0-stable           # Vue 3 stabile
pilotproos-backend-dev:locked-v1.0-stable            # Express stabile
pilotproos-agent-engine-dev:locked-v1.0-crewai-0.193.2  # CrewAI funzionante
```

### Container Standard (non blindati)
- `postgres:16-alpine` - Image Docker Hub
- `redis:7-alpine` - Image Docker Hub
- `nginx:alpine` - Image Docker Hub
- `n8nio/n8n:1.110.1` - Image Docker Hub

## 📋 COMANDI SICURI

### Stack Completo
```bash
# ✅ SAFE COMMANDS
./stack-safe.sh start         # Avvia tutto (NO rebuild)
./stack-safe.sh status        # Status + health check completo
./stack-safe.sh test          # Test tutti i componenti
./stack-safe.sh restart       # Restart sicuro (NO rebuild)
./stack-safe.sh logs [service] # Logs (all o servizio specifico)

# 💾 BACKUP & RECOVERY
./stack-safe.sh backup        # Crea backup timestamp
./stack-safe.sh recovery      # Recovery da locked images

# ⚠️ DEVELOPMENT ONLY
./stack-safe.sh frontend rebuild  # Solo frontend
./stack-safe.sh backend rebuild   # Solo backend
./stack-safe.sh DANGER-rebuild    # TUTTO (10-15 min!)
```

### Agent Engine Specifico
```bash
./agent-engine-safe.sh status     # Health check
./agent-engine-safe.sh test       # Test Milhena
./agent-engine-safe.sh restart    # Restart singolo
./agent-engine-safe.sh recovery   # Recovery specifico
```

## 🚨 EMERGENCY RECOVERY

### Recovery Automatico Stack
```bash
./stack-safe.sh recovery
# Ripristina da:
# - frontend: locked-v1.0-stable
# - backend: locked-v1.0-stable
# - agent-engine: locked-v1.0-crewai-0.193.2
```

### Recovery Singolo Agent Engine
```bash
./pilotpros-agent-engine/EMERGENCY_RECOVERY.sh
# Verifica backup, ripristina, testa health
```

## 📄 FILE PROTEZIONE

### Scripts
- `stack-safe.sh` - Comandi sicuri stack completo
- `agent-engine-safe.sh` - Comandi specifici Agent Engine
- `pilotpros-agent-engine/EMERGENCY_RECOVERY.sh` - Recovery automatico

### Docker Compose Protetto
- `docker-compose.protected.yml` - Versione senza build context
- Usa solo locked images, nessun rebuild possibile

### Documentazione
- `CONTAINER_LOCK.md` - Regole versioning Agent Engine
- `CONTAINER_PROTECTION_SYSTEM.md` - Questo documento

## ⚖️ VANTAGGI

### Performance
- **Avvio istantaneo**: 5-10 secondi vs 10-15 minuti
- **Nessun npm install**: Dependencies già installate
- **Nessun build step**: Tutto pronto

### Affidabilità
- **No dependency hell**: Versioni fisse e testate
- **No breaking changes**: Container stabili
- **Recovery automatico**: Ripristino in 30 secondi

### Developer Experience
- **Comandi sicuri**: Impossibile fare rebuild accidentali
- **Health check**: Status completo di tutti i servizi
- **Test integrati**: Verifica funzionamento end-to-end

## 📊 TEMPI DI BUILD

### Prima (rebuild ogni volta)
- **Frontend**: 5-8 minuti (npm install + Vite build)
- **Backend**: 2-3 minuti (npm install + dependencies)
- **Agent Engine**: 5-10 minuti (CrewAI dependencies hell)
- **TOTALE**: 12-21 minuti

### Dopo (containers blindati)
- **Stack startup**: 5-10 secondi
- **Recovery**: 30 secondi
- **Health check**: 2 secondi
- **TOTALE**: <1 minuto

## 🛡️ PROTEZIONI IMPLEMENTATE

1. **Locked Images**: Backup immutabili testati
2. **Safe Commands**: Scripts con conferme per operazioni pericolose
3. **Emergency Recovery**: Ripristino automatico
4. **Health Monitoring**: Verifica stato servizi
5. **Documentation**: Guide per ogni scenario

## 🔧 DEVELOPMENT WORKFLOW

### Uso Normale (99%)
```bash
./stack-safe.sh start     # Mattina
./stack-safe.sh status    # Check salute
./stack-safe.sh test      # Verifica funzionamento
```

### Sviluppo (1%)
```bash
# Solo se modifichi codice frontend
./stack-safe.sh frontend rebuild

# Solo se modifichi codice backend
./stack-safe.sh backend rebuild

# Solo se modifichi Agent Engine (raro!)
./agent-engine-safe.sh DANGER-rebuild
```

### Emergenza (0.1%)
```bash
./stack-safe.sh recovery  # Se tutto è rotto
```

Il sistema garantisce **zero downtime accidentali** e **avvio istantaneo** dello stack!