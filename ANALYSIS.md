# PilotProOS – Analisi e Mappa Documentazione

Scopo: offrire una vista di insieme e puntare ai documenti aggiornati, mantenendo coerenza con lo stack attuale (Vue 3 + Express + PostgreSQL + n8n, policy Docker‑first).

## Cosa è PilotProOS
- Business Process Operating System containerizzato, white‑label, con UI business, backend di traduzione e motore processi n8n su PostgreSQL dual schema (`n8n` + `pilotpros`).

## Documenti Chiave
- Architettura tecnica: `docs/architecture.md`
- Reverse proxy, dual access e branding: `docs/REVERSE_PROXY_README.md`
- Deployment VPS ottimizzato: `docs/VPS_DEPLOYMENT_GUIDE.md`
- Piano ottimizzazione Docker: `docs/DOCKER_OPTIMIZATION_PLAN.md`
- Ottimizzazione enterprise: `docs/ENTERPRISE_SERVER_OPTIMIZATION.md`
- Sicurezza (overview): `docs/security.md`
- Deployment (overview): `docs/deployment.md`
- Workflow e best practice: `docs/workflows.md`
- Accesso dev a n8n: `docs/developer-access-instructions.md`
- PostgreSQL setup e viste cross‑schema: `docs/postgresql-setup.md`
- Business Intelligence/Timeline: `docs/Business_Intelligence_Service.md`

## Policy Fondamentali
- Docker‑first e isolation: vedi `CLAUDE.md` e `docs/REVERSE_PROXY_README.md`.
- Terminologia business in frontend: vedi `docs/architecture.md` e `docs/workflows.md`.
- Compatibilità n8n versioni: vedi sezione dedicata in `docs/architecture.md` e `docs/n8n-upgrade-troubleshooting.md`.

## Stato
- Documentazione allineata a Vue 3 e schema `pilotpros`.
- AI Agent considerato opzionale/sperimentale; non abilitato di default (compose con `profiles: [ai]`).

