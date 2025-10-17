#!/bin/bash

# Test DETTAGLIATO: Stampa TUTTI i messaggi del ReAct Agent

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 TEST: ReAct Agent con query 'clienti'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

curl -s -X POST http://localhost:8000/api/n8n/agent/customer-support \
  -H "Content-Type: application/json" \
  -d '{"message": "clienti", "session_id": "test-messages-detail"}' \
  --max-time 60 | jq -r '.response' | head -50

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Verifica log container per tool calls:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker logs pilotpros-intelligence-engine-dev --tail 100 2>&1 | grep -E "Tool.*call|ToolMessage|get_system_context" | head -20

if [ $? -ne 0 ]; then
    echo "❌ NO tool calls found in logs"
else
    echo "✅ Tool calls detected"
fi
