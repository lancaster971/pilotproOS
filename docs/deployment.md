# Deployment Overview

Questa guida riassume i percorsi di deployment e rimanda ai runbook completi.

## Ambienti Supportati
- Sviluppo locale (docker-compose.yml)
- VPS ottimizzato (2–4 GB RAM): vedi `docs/VPS_DEPLOYMENT_GUIDE.md`
- Enterprise (16–64+ GB RAM): vedi `docs/ENTERPRISE_SERVER_OPTIMIZATION.md`

## Reverse Proxy e Branding
- Unico ingresso pubblico via Nginx, dual path: `/` cliente, `/dev-panel` team dev
- Dettagli, script e test: `docs/REVERSE_PROXY_README.md`

## Compose e Profili
- `docker-compose.yml`: stack di sviluppo
- `docker-compose.prod.yml`: configurazione di produzione base
- AI Agent disabilitato di default via profilo: eseguirlo solo con `COMPOSE_PROFILES=ai`

## Passi Tipici (VPS)
1) Preparazione VPS e Docker: `docs/VPS_DEPLOYMENT_GUIDE.md`
2) Configurare `.env` con credenziali e segreti
3) Avviare stack: `docker-compose up -d`
4) Configurare reverse proxy/SSL: vedi guida VPS e reverse proxy

## Database e Migrazioni
- PostgreSQL con dual schema (`n8n`, `pilotpros`); init e viste: `docs/postgresql-setup.md`

## Troubleshooting Upgrade n8n
- Procedure di diagnosi e rollback: `docs/n8n-upgrade-troubleshooting.md`

