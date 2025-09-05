# DATA RECOVERY PLAN - PILOTPROS
*Creato: 2025-09-05 dopo Docker reset accidentale*

## 🆘 SITUAZIONE ATTUALE

### ❌ Dati Persi (Docker Reset Accidentale)
- **31 workflow** complessi con logica business
- **600+ executions** con history completa  
- **Credentials** per integrations (OpenAI, Telegram, Gmail, ecc.)
- **Business analytics** e metriche accumulate

### ✅ Sistema Operativo
- **Backend**: tRPC + Express API funzionanti
- **Frontend**: Vue 3 + WorkflowCommandCenter killer feature pronta
- **Database Schema**: PostgreSQL dual-schema configurato
- **Container Stack**: Tutti i servizi healthy e operativi

## 📦 BACKUP DISPONIBILI

### File Presenti in `/BU_Hostinger/`
- ✅ `workflows.json` (1.3MB) - Export completo workflow da produzione Hostinger
- ✅ `credentials.json` (28KB) - Credentials encrypted per tutte le integrazioni

### Recovery Tools
- ✅ `scripts/import-backup.js` - Script import automatico  
- ✅ n8n API - Per importazione programmatica
- ✅ Database diretto - Per import via SQL se necessario

## 🔄 PROCEDURA RECOVERY

### STEP 1: Setup n8n Admin (Prerequisito)
```bash
# n8n fresh install richiede setup owner account
# Accedi a http://localhost:5678 e configura:
# - Username: admin
# - Password: pilotpros_admin_2025  
# - Email: admin@pilotpros.local
```

### STEP 2: Import Automatico
```bash
npm run import:backup
# Script importa automaticamente:
# - Tutti i workflow da workflows.json
# - Tutte le credentials da credentials.json
# - Ricrea struttura dati completa
```

### STEP 3: Verifica tRPC Integration  
```bash
# Test che WorkflowCommandCenter carichi via tRPC
curl "http://localhost:3001/api/trpc/processes.getAll?input=%7B%7D"
# Dovrebbe restituire 31 workflow

# Test frontend
# Visita: http://localhost:3000/command-center
# Dovrebbe mostrare tutti i workflow nel selettore
```

### STEP 4: Validazione Completa
```bash
# Verifica database
npm run docker:psql
# SELECT COUNT(*) FROM n8n.workflow_entity;  -- Dovrebbe essere 31
# SELECT COUNT(*) FROM n8n.execution_entity; -- Dovrebbe essere 600+

# Test WorkflowCommandCenter killer feature
# - Selettore workflow popolato
# - VueFlow canvas con nodes/connections
# - KPI metrics real-time
# - Execute/Stop controls funzionanti
```

## 🔒 PREVENZIONE FUTURA

### Sistema Backup Implementato
- ✅ `npm run docker:backup` - Crea backup timestamped automatici
- ✅ `npm run docker:reset` - Bloccato con warning  
- ✅ `npm run docker:reset-safe` - Reset con backup automatico
- ✅ Warning prominenti in CLAUDE.md

### Recovery Files Pattern
```
postgres-volume-YYYYMMDD-HHMMSS.tar.gz
n8n-volume-YYYYMMDD-HHMMSS.tar.gz
```

## 📊 POST-RECOVERY EXPECTATION

Una volta completato il recovery:
- **WorkflowCommandCenter**: 31 workflow visibili, selettore popolato
- **InsightsPage**: KPI reali (31 workflows, 600+ exec, success rate)  
- **Analytics**: Metriche business complete
- **Timeline Modal**: Business intelligence con dati reali
- **tRPC System**: Type-safe API calls su tutti i dati

---

**NOTA**: Il sistema tRPC è completamente funzionante e testato. Il recovery ripristinerà solo i dati, l'architettura enterprise è già completa.