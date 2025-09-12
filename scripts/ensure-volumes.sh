#!/bin/bash
# Ensure Docker volumes exist for enterprise-grade persistence

echo "🗄️ Ensuring Docker volumes exist..."

VOLUMES=(
    "pilotpros_postgres_dev_data"
    "pilotpros_n8n_dev_data" 
    "pilotpros_pgadmin_dev_data"
    "pilotpros_ollama_models"
)

for volume in "${VOLUMES[@]}"; do
    if ! docker volume inspect "$volume" >/dev/null 2>&1; then
        echo "📦 Creating volume: $volume"
        docker volume create "$volume"
    else
        echo "✅ Volume exists: $volume"
    fi
done

echo "✅ All volumes ready for enterprise persistence"