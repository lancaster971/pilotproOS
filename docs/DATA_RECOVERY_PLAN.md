# 🔴 DATA RECOVERY PLAN - PILOTPROS
*Aggiornato: 2025-09-05 - CRITICO: Docker volumes cancellati accidentalmente*

## 🆘 SITUAZIONE ATTUALE

### ❌ VOLUMI DOCKER CANCELLATI (Docker Reset Accidentale)
- **PostgreSQL Volume**: `pilotpros_postgres_dev_data` - PERSO
- **n8n Volume**: `pilotpros_n8n_dev_data` - PERSO
- **Dati contenuti**: 31 workflow + 600+ executions + credentials + business analytics

### ✅ Sistema Operativo
- **Backend**: tRPC + Express API funzionanti
- **Frontend**: Vue 3 + WorkflowCommandCenter killer feature pronta
- **Database Schema**: PostgreSQL dual-schema configurato
- **Container Stack**: Tutti i servizi healthy ma DATABASE VUOTO

### ⚠️ STATUS RECOVERY: IN ATTESA BACKUP VOLUMI

## 📦 BACKUP NECESSARI PER RECOVERY

### ❌ MANCANTI - File backup volumi Docker (formato .tar.gz)
**RICHIESTI URGENTEMENTE**:
- `postgres-volume-YYYYMMDD-HHMMSS.tar.gz` - Backup volume PostgreSQL
- `n8n-volume-YYYYMMDD-HHMMSS.tar.gz` - Backup volume n8n

**Posizione**: Mettere i file nella directory root del progetto (`/Users/tizianoannicchiarico/pilotproOS/`)

### ⚠️ BU_Hostinger NON È LA SOLUZIONE
File in `/BU_Hostinger/` (workflows.json, credentials.json) sono export parziali, NON i volumi completi.

## 🔄 PROCEDURA RECOVERY COMPLETA

### STEP 0: PREREQUISITO CRITICO - Ottenere i backup volumi
```bash
# I file backup devono essere messi in:
# /Users/tizianoannicchiarico/pilotproOS/postgres-volume-YYYYMMDD-HHMMSS.tar.gz
# /Users/tizianoannicchiarico/pilotproOS/n8n-volume-YYYYMMDD-HHMMSS.tar.gz

# Verificare presenza backup:
ls -la *.tar.gz
# Dovrebbe mostrare i due file di backup dei volumi
```

### STEP 1: Stop Docker Stack
```bash
# Ferma tutti i container per volume recovery
npm run docker:stop

# Verifica stop completo
docker ps
# Non dovrebbe mostrare container pilotpros
```

### STEP 2: Ripristino Volume PostgreSQL
```bash
# Ricrea volume PostgreSQL
docker volume rm pilotpros_postgres_dev_data 2>/dev/null || true
docker volume create pilotpros_postgres_dev_data

# Ripristina dati PostgreSQL dal backup
docker run --rm \
  -v pilotpros_postgres_dev_data:/data \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/postgres-volume-YYYYMMDD-HHMMSS.tar.gz -C /

echo "✅ Volume PostgreSQL ripristinato"
```

### STEP 3: Ripristino Volume n8n  
```bash
# Ricrea volume n8n
docker volume rm pilotpros_n8n_dev_data 2>/dev/null || true
docker volume create pilotpros_n8n_dev_data

# Ripristina dati n8n dal backup
docker run --rm \
  -v pilotpros_n8n_dev_data:/data \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/n8n-volume-YYYYMMDD-HHMMSS.tar.gz -C /

echo "✅ Volume n8n ripristinato"
```

### STEP 4: Restart Docker Stack
```bash
# Riavvia stack completo con dati ripristinati
npm run dev

# Attendi che tutti i container siano healthy
docker ps
# Tutti i container dovrebbero mostrare (healthy)
```

### STEP 5: Verifica Recovery Completa
```bash
# Test database PostgreSQL
npm run docker:psql
```
```sql
-- Verifica workflow ripristinati
SELECT COUNT(*) FROM n8n.workflow_entity;  
-- Dovrebbe essere 31

-- Verifica executions ripristinate  
SELECT COUNT(*) FROM n8n.execution_entity; 
-- Dovrebbe essere 600+

-- Verifica credentials ripristinate
SELECT COUNT(*) FROM n8n.credentials_entity;
-- Dovrebbe essere 10+
```

```bash
# Test n8n UI
open http://localhost:5678
# Dovrebbe mostrare 31 workflow nella dashboard

# Test tRPC API integration
curl "http://localhost:3001/api/trpc/processes.getAll?input=%7B%7D"
# Dovrebbe restituire 31 workflow

# Test frontend WorkflowCommandCenter
open http://localhost:3000
# Dashboard dovrebbe mostrare KPI reali (31 workflows, 600+ exec)
```

## 🚨 EMERGENCY STATUS

### ⚠️ CURRENT CRITICAL STATE
- **Database**: EMPTY (0 workflows instead of 31)
- **System Status**: OPERATIONAL but NO BUSINESS DATA
- **Business Impact**: WorkflowCommandCenter, Analytics, Timeline Modal all EMPTY
- **Recovery Dependency**: Waiting for Docker volume backup files

### 🔴 IMMEDIATE ACTIONS REQUIRED
1. **FIND** the Docker volume backup files (.tar.gz format)
2. **PLACE** them in `/Users/tizianoannicchiarico/pilotproOS/`
3. **EXECUTE** recovery procedure above
4. **VERIFY** 31 workflows + 600+ executions restored

## 🔒 PREVENZIONE FUTURA

### ⚠️ CRITICAL WARNING SYSTEM
```bash
# SEMPRE fare backup prima di operazioni distruttive:
npm run docker:backup

# VERIFICARE presenza backup:
ls -la *-volume-*.tar.gz

# MAI usare docker:reset senza backup:
npm run docker:reset-safe  # (con backup automatico)
```

### Sistema Backup Automatico
- ✅ `npm run docker:backup` - Backup timestamped volumi
- ✅ `npm run docker:reset-safe` - Reset con backup pre-operazione
- ⚠️ `npm run docker:reset` - BLOCCATO per prevenire data loss
- ✅ Warning nel CLAUDE.md per operazioni distruttive

### Recovery Files Pattern
```bash
# Nomi file backup volumi:
postgres-volume-YYYYMMDD-HHMMSS.tar.gz  # Database completo
n8n-volume-YYYYMMDD-HHMMSS.tar.gz       # n8n data + workflows
```

## 📊 POST-RECOVERY TARGETS

Dopo recovery completo il sistema dovrà avere:
- **31 workflows** attivi nel WorkflowCommandCenter
- **600+ executions** con business data completa  
- **10+ credentials** per integrazioni esterne
- **KPI Dashboard** con metriche reali non mock
- **Timeline Modal** con business intelligence data-driven
- **Analytics** con performance metrics storiche

---

## 🎯 NEXT STEPS AFTER RECOVERY

Una volta ripristinati i dati:
1. **Validate System**: Test completo tRPC + frontend integration
2. **Business Analytics**: Verificare business_execution_data populated
3. **Performance Test**: Load test con 31 workflows reali  
4. **Backup Schedule**: Setup backup automatici giornalieri
5. **Documentation Update**: Aggiornare status in CLAUDE.md

**STATO ATTUALE**: ⚠️ CRITICO - IN ATTESA BACKUP VOLUMI PER RECOVERY