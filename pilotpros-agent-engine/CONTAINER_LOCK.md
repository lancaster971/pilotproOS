# 🔒 CONTAINER LOCK - NON TOCCARE MAI PIÙ!

## ⚠️ ATTENZIONE: Container Funzionante - NON RICOSTRUIRE!

Questo container ha richiesto 3+ ore di debugging per risolvere i conflitti di CrewAI.

## Container Bloccato
- **Image**: `pilotproos-agent-engine-dev:latest`
- **Build Date**: 2025-09-25
- **CrewAI Version**: 0.193.2 (ULTIMA VERSIONE - OBBLIGATORIO!)
- **Python**: 3.11-slim

## 🚨 REGOLA: CrewAI Versione COMPATIBILE!
**IMPORTANTE**: CrewAI ha breaking changes frequenti - usa versione TESTATA!
- ✅ Versione 0.193.2 = TESTATA e FUNZIONANTE
- ❌ Versioni 0.28.0 e precedenti = ImportError BaseTool
- ⚠️ NON aggiornare a caso - testare sempre prima
- 📋 API changes: `crewai.tools` → `crewai_tools` tra versioni

## Comandi Sicuri
```bash
# AVVIA (senza rebuild)
docker-compose up -d agent-engine-dev

# RIAVVIA (senza rebuild)
docker-compose restart agent-engine-dev

# LOGS
docker logs pilotpros-agent-engine-dev -f

# STOP (preserva container)
docker-compose stop agent-engine-dev
```

## ❌ COMANDI VIETATI
```bash
# NON FARE MAI:
docker-compose build agent-engine-dev        # NO!
docker-compose up --build agent-engine-dev   # NO!
docker-compose down                          # NO! (distrugge container)
rm requirements*.txt                          # NO!
```

## Backup Files Critici
Salvati in `pilotpros-agent-engine/container-lock/`:
- `requirements-fixed.txt` - Dipendenze funzionanti
- `Dockerfile.working` - Dockerfile funzionante
- `start.sh` - Script avvio corretto

## Note Tecniche
- CrewAI 0.193.2 + Pydantic v2 (finalmente compatibili!)
- Vecchie versioni 0.28.0 causavano errori import (`BaseTool from crewai.tools`)
- Nuova versione usa: `from crewai_tools import BaseTool`
- 143+ dipendenze con conflitti risolti manualmente
- Build time: ~5 minuti su M1, ~10 minuti su x86
- Container size: ~2GB (normale per ML/AI stack)

## 📝 CHANGELOG FIX CrewAI
- **PRIMA**: CrewAI 0.28.0 → ImportError: cannot import name 'BaseTool' from 'crewai.tools'
- **DOPO**: CrewAI 0.193.2 → `from crewai_tools import BaseTool` → FUNZIONA! ✅

## Recovery
Se per errore il container viene distrutto:
```bash
cd pilotpros-agent-engine
cp container-lock/requirements-fixed.txt requirements-fixed.txt
cp container-lock/Dockerfile.working Dockerfile  
docker-compose build agent-engine-dev --no-cache
```