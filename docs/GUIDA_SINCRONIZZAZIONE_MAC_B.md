# 🚀 GUIDA SINCRONIZZAZIONE MAC B - PilotProOS Team Sync

**Data Export**: 2 Settembre 2025  
**Mac A → Mac B**: Sincronizzazione completa Docker stack  
**File Export**: `team-export-manual-2025-09-02-23-18-41.tar.gz` (2.2MB)

---

## 📋 PREREQUISITI MAC B

### Requisiti Sistema
- **macOS**: Qualsiasi versione recente
- **Node.js**: v18+ (controllare con `node --version`)
- **Git**: Installato (controllare con `git --version`)
- **Docker**: NON necessario (si auto-installa)

### Connessione Internet
- ✅ Per clone GitHub repository
- ✅ Per download Docker (se mancante)  
- ✅ Per download dipendenze Node.js

---

## 🎯 STEP 1: CLONE REPOSITORY

Apri il Terminale su Mac B ed esegui:

```bash
# 1. Clone repository da GitHub
git clone https://github.com/lancaster971/pilotproOS.git

# 2. Entra nella directory
cd pilotproOS

# 3. Verifica di essere sul branch main
git branch
# Output: * main
```

**✅ Verifica**: Dovresti vedere questi file/cartelle:
```
backend/
frontend/
ai-agent/
scripts/
docs/
docker-compose.dev.yml
package.json
TEAM_WORKFLOW.md
.env.example
```

### 🔑 Setup Variabili Ambiente (OPZIONALE)
```bash
# Se vuoi personalizzare le credenziali (altrimenti usa i default)
cp .env.example .env
# Modifica .env se necessario (default vanno bene per sviluppo)
```

---

## 🐳 STEP 2: SETUP DOCKER STACK

```bash
# Auto-setup completo (installa Docker se manca)
npm run dev
```

**Cosa fa questo comando:**
1. **Controlla Docker**: Se mancante → auto-installa Docker Desktop
2. **Installa dipendenze**: `npm install` in tutte le cartelle
3. **Avvia stack completo**: PostgreSQL + n8n + Backend + Frontend + AI Agent
4. **Aspetta health check**: Verifica che tutti i container siano pronti

**⏱️ Tempo stimato**: 5-10 minuti (prima volta include download Docker)

**✅ Stack pronto quando vedi:**
```
✅ Frontend: http://localhost:3000
✅ Backend:  http://localhost:3001  
✅ n8n:      http://localhost:5678
✅ Database: PostgreSQL pronto
```

---

## 📥 STEP 3: TRASFERIMENTO FILE EXPORT

### 🗂️ Prima: Crea cartella di destinazione
```bash
# Assicurati di essere in pilotproOS/
cd pilotproOS

# Crea cartella per file export (non esiste dopo clone)
mkdir -p team-sync-exports
```

### 🔑 IMPORTANTE: Copia credenziali n8n
Il file export contiene anche `.env` con le credenziali necessarie per n8n:

```bash
# Dopo aver estratto l'archivio, copia il file .env:
cp team-sync-exports/export-*/env .env

# Verifica che esista:
ls -la .env
# Deve mostrare il file .env copiato
```

**⚠️ CRITICO**: Senza .env Mac B non potrà accedere alle API n8n e l'import fallirà!

### Opzione A: Google Drive/Dropbox
1. **Mac A** carica `team-export-manual-2025-09-02-23-18-41.tar.gz` su Google Drive
2. **Mac A** condivide link con Mac B  
3. **Mac B** scarica il file
4. **Mac B** mette il file in `pilotproOS/team-sync-exports/`

### Opzione B: AirDrop (Mac locali)
1. **Mac A** → AirDrop del file `team-export-manual-2025-09-02-23-18-41.tar.gz`
2. **Mac B** → Sposta in `pilotproOS/team-sync-exports/`

### Opzione C: USB/Email
1. **Mac A** copia su USB o allega email
2. **Mac B** mette in `pilotproOS/team-sync-exports/`

### Opzione D: Download diretto con curl/wget (se hai URL)
```bash
# Se Mac A fornisce URL diretto
cd team-sync-exports
curl -O "URL_DEL_FILE_EXPORT"
# oppure
wget "URL_DEL_FILE_EXPORT"
```

**✅ Verifica posizione file:**
```bash
ls -la team-sync-exports/
# Devi vedere: team-export-manual-2025-09-02-23-18-41.tar.gz
```

---

## 🔄 STEP 4: IMPORT DATI DA MAC A

```bash
# Importa tutti i dati da Mac A
npm run team:import
```

**Il sistema ti mostrerà:**
```
⚠️  ATTENZIONE: Questa operazione sovrascriverà tutti i dati attuali!
📋 Verrà eseguito:
   1. Stop Docker stack
   2. Pulizia database e volumi
   3. Import dati dal collega
   4. Riavvio completo

❓ Vuoi continuare? [y/N]:
```

**Digita:** `y` e premi Enter

**⏱️ Processo import (3-4 minuti):**
1. ✅ Trova archivio più recente
2. ✅ Estrae archivio  
3. ✅ Ferma Docker stack
4. ✅ Pulisce database
5. ✅ Riavvia stack pulito
6. ✅ Importa database PostgreSQL completo
7. ✅ Verifica n8n con 31 workflows
8. ✅ Pulizia file temporanei

---

## 🎉 STEP 5: VERIFICA SINCRONIZZAZIONE

### Test Frontend
```bash
open http://localhost:3000
```
**✅ Dovresti vedere**: Dashboard PilotProOS identico a Mac A

### Test Backend API
```bash
curl http://localhost:3001/api/health
```
**✅ Output atteso**: `{"status":"ok","database":"connected"}`

### Test n8n Workflows
```bash
open http://localhost:5678
```
**✅ Login**: `admin` / `pilotpros_admin_2025`  
**✅ Workflows**: Dovresti vedere tutti e 31 i workflows da Mac A

### Test Database
```bash
npm run docker:psql
```
```sql
-- Conta workflows importati
SELECT COUNT(*) FROM n8n.workflow_entity;
-- Output atteso: 31

-- Verifica workflow Milena
SELECT name, active FROM n8n.workflow_entity WHERE name LIKE '%Milena%';
-- Output: MIlena | t (true = attivo)
```

---

## ✅ SINCRONIZZAZIONE COMPLETATA!

**🎯 MAC B ora ha IDENTICAMENTE:**
- ✅ **31 workflows n8n** con configurazioni complete
- ✅ **Database PostgreSQL** con tutti i dati business  
- ✅ **Credenziali** per integrazioni esterne
- ✅ **Configurazioni Docker** identiche a Mac A
- ✅ **Stesso branch Git** con codice aggiornato

### Accessi Mac B
```
🌐 Frontend:    http://localhost:3000
🔧 Backend:     http://localhost:3001  
🤖 n8n:         http://localhost:5678 (admin / pilotpros_admin_2025)
🗄️ Database:    localhost:5432 (pilotpros_db)
🔍 PgAdmin:     http://localhost:5050 (se attivato)
```

### Comandi Utili Mac B
```bash
npm run dev                 # Avvia stack completo
npm run docker:stop         # Ferma tutti i container  
npm run docker:logs         # Vedi log in real-time
npm run docker:psql         # Accesso diretto database
npm run team:export         # Esporta tue modifiche per Mac A
```

---

## 🔄 WORKFLOW FUTURO TEAM

### Ogni Mattina (Inizio Lavoro)
```bash
# 1. Sincronizza codice
git pull origin main

# 2. Importa dati più recenti dal team
npm run team:import
# ⚠️ ATTENZIONE: Sovrascrive i tuoi dati locali!

# 3. Verifica sincronizzazione
npm run dev
```

### Ogni Sera (Fine Lavoro) 
```bash
# 1. Salva codice
git add .
git commit -m "✨ FEATURE: Descrizione modifiche"
git push origin main

# 2. Esporta dati per il team
npm run team:export
# 📁 Crea: team-sync-exports/team-export-TIMESTAMP.tar.gz

# 3. Condividi con Mac A (Google Drive, Slack, etc.)
```

---

## 🆘 TROUBLESHOOTING

### "Docker stack non attivo"
```bash
# Riavvia Docker Desktop manualmente, poi:
npm run dev
```

### "Nessun archivio trovato"  
```bash
# Controlla posizione file:
ls -la team-sync-exports/
# Il file deve essere nella directory team-sync-exports/
```

### "Timeout avvio database"
```bash
# Riprova import (normale con primo avvio)
npm run team:import
```

### "Errore import database: Command failed"
```bash
# Se il comando docker exec fallisce, verifica:

# 1. Container PostgreSQL attivo?
docker ps | grep postgres
# Deve vedere: pilotpros-postgres-dev (healthy)

# 2. Database accessibile?
docker exec pilotpros-postgres-dev pg_isready -U pilotpros_user -d pilotpros_db
# Output: accepting connections

# 3. File SQL presente?
ls -la team-sync-exports/*/database-complete.sql
# Deve esistere il file

# 4. Se persistente, import manuale:
docker exec -i pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db
# Poi dentro psql: \i /path/to/database-complete.sql
```

### "n8n non risponde"
```bash
# Aspetta 1-2 minuti per l'avvio, poi verifica:
docker ps
# Tutti i container devono essere "healthy"
```

### Reset Completo (Ultimo Resort)
```bash
# Pulisce tutto e ricomincia
npm run docker:clean
npm run dev
npm run team:import
```

---

## 📞 SUPPORTO

**GitHub Repository**: https://github.com/lancaster971/pilotproOS  
**Documentazione**: `docs/TEAM_WORKFLOW.md`  
**Script**: `scripts/team-import.js`, `scripts/team-export.js`

**🎯 Sistema pronto per sviluppo team distribuito!**

---

*Generato automaticamente dal Team Sync System PilotProOS*  
*Mac A Export Date: 2 Settembre 2025 - 23:18*