#!/bin/bash
# Script per riavviare il container con la versione multi-agente

echo "🛑 Fermando container vecchio..."
docker stop pilotpros-intelligence-engine-dev
docker rm pilotpros-intelligence-engine-dev

echo "🚀 Avviando container multi-agente v2.0..."
docker run -d \
  --name pilotpros-intelligence-engine-dev \
  --network pilotpros-network \
  -p 8000:8000 \
  -p 8501:8501 \
  -p 2024:2024 \
  -p 6006:6006 \
  -v $(pwd):/app \
  -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
  -e DATABASE_URL="postgresql://admin:pilotpros_admin_2025@postgres-dev:5432/pilotpros" \
  -e REDIS_URL="redis://redis-dev:6379" \
  pilotpros-intelligence-engine:v2.0-multiagent

echo "✅ Container avviato!"
echo ""
echo "📊 Verifica stato:"
docker ps | grep intelligence

echo ""
echo "📋 Per vedere i log:"
echo "docker logs -f pilotpros-intelligence-engine-dev"