# Sicurezza – PilotProOS

Panoramica dei controlli di sicurezza, in coerenza con le policy Docker‑first e white‑label.

## Controlli Principali
- Reverse proxy con dual access: `/` cliente con branding injection, `/dev-panel` per team dev con basic auth e rate limiting. Vedi `docs/REVERSE_PROXY_README.md`.
- Network isolation: servizi backend e DB su rete interna; porte pubbliche limitate a 80/443.
- Autenticazione: JWT lato backend (variabili `.env`), bcrypt rounds configurabili.
- n8n protetto: basic auth attiva, accessibile solo via proxy dev panel in produzione.
- SSL/TLS: integrazione con Let's Encrypt su VPS. Vedi `docs/VPS_DEPLOYMENT_GUIDE.md`.
- Privacy: telemetria n8n disabilitata in default.

## Segreti e Configurazioni
- Tutti i segreti provengono da `.env` ed environment del compose (DB_PASSWORD, N8N_ADMIN_*, JWT_SECRET, ...).
- Niente valori hardcoded nei manifest: verificato e corretto in `docker-compose.yml`.

## Hardening Aggiuntivo
- Helmet, CORS, rate limit nel backend (vedi `docs/architecture.md`).
- Log rotation e limiti risorse dei container: vedi `docs/DOCKER_OPTIMIZATION_PLAN.md` e VPS guide.

