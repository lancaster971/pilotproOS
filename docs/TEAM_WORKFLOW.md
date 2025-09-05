# 🚀 TEAM SYNC WORKFLOW - PilotProOS

Guida completa per sviluppo team distribuito con sincronizzazione automatica.

## 📋 PANORAMICA

**Problema**: 2+ sviluppatori su Mac diversi con Docker stack locali
**Soluzione**: Sistema automatico export/import per sincronizzazione dati

### Sistema Dual-Layer
```
CODICE → GitHub (git push/pull)
DATI   → Export/Import automatico (npm run team:export/import)
```

## 🛠 SETUP INIZIALE

### Mac A (già configurato)
```bash
# Niente da fare, già funzionante
git status  # Branch corrente: executions-details-tab
```

### Mac B (nuovo sviluppatore)
```bash
# 1. Clone repository
git clone https://github.com/tuorepo/pilotproOS.git
cd pilotproOS

# 2. Auto-setup completo (installa Docker se manca)
npm run dev

# 3. Aspetta setup completo
# ✅ Frontend: http://localhost:3000
# ✅ Backend:  http://localhost:3001  
# ✅ n8n:      http://localhost:5678
# ✅ Database: PostgreSQL pronto

# 4. Importa dati dal collega
npm run team:import
```

## 🔄 WORKFLOW QUOTIDIANO

### Mattina (Inizio Lavoro)
```bash
# 1. Sincronizza codice
git pull origin main
git checkout -b feature/mia-feature

# 2. Importa dati più recenti dal team
npm run team:import
# ⚠️ ATTENZIONE: Sovrascrive i tuoi dati locali!

# 3. Verifica sincronizzazione
npm run dev
```

### Sera (Fine Lavoro)
```bash
# 1. Salva codice
git add .
git commit -m "✨ FEATURE: Mia nuova funzionalità"
git push origin feature/mia-feature

# 2. Esporta dati per il team
npm run team:export
# 📁 Crea: team-sync-exports/team-export-TIMESTAMP.tar.gz

# 3. Condividi con il collega (Google Drive, Slack, etc.)
```

## ⚡ COMANDI DISPONIBILI

### `npm run team:export`
**Cosa fa:**
- Esporta database PostgreSQL completo
- Esporta tutti i workflows n8n (via API)
- Esporta credenziali n8n
- Crea archivio compresso con metadati
- Salva in `team-sync-exports/`

**Output:**
```
✅ EXPORT COMPLETATO CON SUCCESSO!
📁 Archivio: team-sync-exports/team-export-2025-01-15T14-30-00.tar.gz
📤 Per condividere:
   1. Carica su Google Drive/Dropbox
   2. Condividi link con il collega
   3. Il collega esegue: npm run team:import
```

### `npm run team:import`
**Cosa fa:**
- Trova archivio più recente in `team-sync-exports/`
- ⚠️ **FERMA Docker stack**
- ⚠️ **PULISCE database e volumi**
- Importa database completo
- Riavvia tutto
- Verifica sincronizzazione

**Interactive prompts:**
```
⚠️  ATTENZIONE: Questa operazione sovrascriverà tutti i dati attuali!
❓ Vuoi continuare? [y/N]:
```

### `npm run team:sync`
**Shortcut per:**
```bash
npm run team:export
echo "🔄 Ora chiedi al collega di eseguire: npm run team:import"
```

## 🔒 SICUREZZA E BEST PRACTICES

### File Ignorati (.gitignore)
```
# Team sync exports (private data - never commit)
team-sync-exports/
team-export-*.tar.gz
```

### Dati Sensibili
- **Credenziali n8n**: Esportate ma criptate
- **Database**: Include dati business reali
- **Mai committare**: File export su GitHub

### Compatibilità
- **Versione Check**: Automatico con warning se diverse
- **Metadata**: Data export, utente, hostname, versione
- **Graceful Degradation**: Funziona anche con metadati mancanti

## 🚨 TROUBLESHOOTING

### "Docker stack non attivo"
```bash
npm run dev
# Aspetta che tutti i container siano healthy
docker ps  # Verifica stato container
```

### "Nessun archivio trovato"
```bash
# Il collega deve eseguire prima:
npm run team:export

# Poi condividere il file .tar.gz
```

### "Timeout avvio database"
```bash
# Riprova import
npm run team:import

# O restart manuale
npm run docker:reset
```

### "Errore verifica n8n"
```bash
# Aspetta qualche secondo per l'avvio
# n8n impiega tempo per essere ready
# Script attende automaticamente 60 secondi
```

## 📊 MONITORAGGIO

### Verifica Sincronizzazione
```bash
# Database
npm run docker:psql
SELECT COUNT(*) FROM n8n.workflow_entity;

# n8n Web
open http://localhost:5678
# Login: admin / pilotpros_admin_2025
```

### Log Import/Export
```bash
# I comandi mostrano progress real-time con:
# ✅ Step completati
# ⚠️  Warning (ma continuano)
# ❌ Errori fatali (fermano processo)
```

## 🎯 VANTAGGI SISTEMA

### ✅ Pro
- **Setup 1 volta**: Mac B pronto in 10 minuti
- **Sync automatica**: 2 comandi (`export` + `import`)
- **Dati reali**: Database production con 31+ workflows
- **Zero conflicts**: Import sovrascrive tutto
- **Metadata tracking**: Chi, quando, che versione
- **Failsafe**: Backup automatici, rollback possibile

### ⚠️ Limitazioni
- **Sovrascrive tutto**: Non merge, ma replace completo
- **Richiede coordinamento**: Team deve coordinarsi per export/import
- **File grandi**: Archive ~50MB+ con database completo
- **Downtime**: ~2-3 minuti per import completo

## 🔄 WORKFLOW BRANCH STRATEGY

### Feature Branches
```bash
# Sempre creare branch per feature
git checkout -b feature/nome-feature
# ... lavoro ...
git push origin feature/nome-feature
# Pull request su GitHub
```

### Data Sync Strategy
```bash
# Mai mixare:
# ❌ git push + dati diversi = conflitti
# ✅ git push + team:export = sync perfetta
```

### Release Process
```bash
# 1. Merge feature su main
git checkout main
git pull origin main

# 2. Export dati finali
npm run team:export

# 3. Team import per allineamento
# Tutti eseguono: npm run team:import
```

---

**🚀 Sistema pronto!** Il team può ora lavorare in parallelo con sincronizzazione automatica dati + codice.