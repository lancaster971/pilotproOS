# P3 - Workflow Guidelines (n8n)

Linee guida per la creazione e gestione dei processi business con n8n.

## Terminologia Business
- Frontend e documenti usano: Business Process (workflow), Process Run (execution), Process Step (node), Integration Endpoint (webhook).

## Accesso Editor (Dev)
- Produzione: `https://<dominio>/dev-panel` (basic auth). Vedi `docs/developer-access-instructions.md`.
- Sviluppo: `http://localhost:5678` (credenziali admin da `.env`).

## Naming e Categorie
- Usa nomi business chiari (es. “Customer Onboarding”) e categorie coerenti.
- Evita tecnicismi nei nomi dei workflow.

## Integrazione con Backend
- Il backend accede ai dati tramite DB (`n8n.workflow_entity`, `n8n.execution_entity`) e li traduce in API business.
- Viste e analytics nel namespace `pilotpros`. Vedi `docs/postgresql-setup.md`.

## Timeline e Business Intelligence
- Output voluminosi sono sintetizzati con il Business Intelligence Service. Vedi `docs/Business_Intelligence_Service.md`.

## Template e Deploy
- Template business disponibili in `templates/` e caricati da script di deploy.
- Per best practice di deploy: vedi `docs/deployment.md`.

