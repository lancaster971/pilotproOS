#!/bin/bash
# 🚨 EMERGENCY RECOVERY SCRIPT per Agent Engine
# Usa solo se container è stato distrutto per errore

set -e

echo "🔒 EMERGENCY RECOVERY - Agent Engine Container"
echo "=============================================="

# Verifica se il container funzionante esiste ancora
if docker images | grep -q "pilotproos-agent-engine-dev.*locked-v1.0-crewai-0.193.2"; then
    echo "✅ Backup image trovato: locked-v1.0-crewai-0.193.2"

    # Ripristina dal backup
    docker tag pilotproos-agent-engine-dev:locked-v1.0-crewai-0.193.2 pilotproos-agent-engine-dev:latest
    echo "✅ Image restored from backup"

    # Riavvia container
    docker-compose up -d agent-engine-dev
    echo "✅ Container restarted"

    # Test health
    sleep 5
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo "🎉 SUCCESS: Agent Engine recovered and working!"
        exit 0
    else
        echo "❌ Health check failed - manual intervention needed"
        exit 1
    fi
else
    echo "❌ NO BACKUP FOUND - Manual rebuild required"
    echo ""
    echo "🛠️  MANUAL RECOVERY STEPS:"
    echo "1. cd pilotpros-agent-engine"
    echo "2. cp container-lock/requirements-fixed.txt requirements-fixed.txt"
    echo "3. cp container-lock/Dockerfile.working Dockerfile"
    echo "4. docker-compose build agent-engine-dev --no-cache"
    echo "5. docker-compose up -d agent-engine-dev"
    echo ""
    echo "⏰ Build time: ~5-10 minutes"
    exit 1
fi