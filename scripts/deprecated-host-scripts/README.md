# Deprecated Host Scripts

⚠️ **QUESTI SCRIPT VIOLANO LA REGOLA DOCKER ISOLATION**

## Motivo Deprecazione

Questi script eseguivano Node.js direttamente su macOS host, violando la regola FERREA:
**TUTTO IN DOCKER tranne strumenti sviluppo**

## Alternative Docker-First

Invece di usare questi script, usa:

```bash
# ❌ VECCHIO (violava regola):
node scripts/dev-auto-detect.js

# ✅ NUOVO (Docker isolation):
npm run dev  # → docker-compose up -d

# ❌ VECCHIO (violava regola):
node scripts/n8n-auto-setup.js  

# ✅ NUOVO (Docker isolation):
docker-compose exec automation-engine-dev n8n import:workflow

# ❌ VECCHIO (violava regola):
node scripts/import-backup.js

# ✅ NUOVO (Docker isolation):
docker exec postgres-dev psql -U user -d db < backup.sql
```

## Policy Enterprise

**macOS Host**: Solo VS Code, browser, git  
**Docker Container**: Database, backend, n8n, tutto il runtime  

**Zero exceptions!**