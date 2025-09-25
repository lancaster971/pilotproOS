#!/bin/bash
# 🔒 AGENT ENGINE SAFE COMMANDS
# Comandi sicuri per gestire Agent Engine senza rebuild accidentali

set -e

case "$1" in
    "start"|"up")
        echo "🚀 Starting Agent Engine (NO REBUILD)"
        docker-compose up -d agent-engine-dev
        echo "✅ Agent Engine started"
        ;;

    "stop")
        echo "⏸️  Stopping Agent Engine (preserving container)"
        docker-compose stop agent-engine-dev
        echo "✅ Agent Engine stopped"
        ;;

    "restart")
        echo "🔄 Restarting Agent Engine (NO REBUILD)"
        docker-compose restart agent-engine-dev
        echo "✅ Agent Engine restarted"
        ;;

    "logs")
        echo "📋 Agent Engine logs:"
        docker logs pilotpros-agent-engine-dev -f --tail 50
        ;;

    "status"|"health")
        echo "🏥 Agent Engine Health Check:"
        if curl -s http://localhost:8000/health | jq '.'; then
            echo "✅ Agent Engine is healthy"
        else
            echo "❌ Agent Engine not responding"
        fi
        ;;

    "test")
        echo "🧪 Testing Milhena chat:"
        curl -X POST http://localhost:8000/api/chat \
            -H "Content-Type: application/json" \
            -d '{"message": "Ciao Milhena, come stai?", "user_id": "test"}' \
            | jq '.'
        ;;

    "agents")
        echo "🤖 Available agents:"
        curl -s http://localhost:8000/api/agents | jq '.agents[].name'
        ;;

    "backup")
        echo "💾 Creating backup image..."
        docker tag pilotproos-agent-engine-dev:latest \
            pilotproos-agent-engine-dev:backup-$(date +%Y%m%d-%H%M%S)
        echo "✅ Backup created"
        ;;

    "recovery")
        echo "🚨 Running emergency recovery..."
        ./pilotpros-agent-engine/EMERGENCY_RECOVERY.sh
        ;;

    "DANGER-rebuild")
        echo "⚠️  DANGER ZONE: This will rebuild the container!"
        echo "Are you ABSOLUTELY sure? This will take 5-10 minutes."
        echo "Type 'YES-I-WANT-TO-REBUILD' to confirm:"
        read -r confirm
        if [ "$confirm" = "YES-I-WANT-TO-REBUILD" ]; then
            echo "🏗️  Rebuilding container..."
            docker-compose build agent-engine-dev --no-cache
            docker-compose up -d agent-engine-dev
            echo "✅ Rebuild completed"
        else
            echo "❌ Rebuild cancelled"
        fi
        ;;

    *)
        echo "🔒 AGENT ENGINE SAFE COMMANDS"
        echo "============================"
        echo ""
        echo "SAFE COMMANDS:"
        echo "  start     - Start Agent Engine (no rebuild)"
        echo "  stop      - Stop Agent Engine (preserve container)"
        echo "  restart   - Restart Agent Engine (no rebuild)"
        echo "  logs      - View live logs"
        echo "  status    - Check health status"
        echo "  test      - Test Milhena chat"
        echo "  agents    - List available agents"
        echo "  backup    - Create backup image"
        echo "  recovery  - Emergency recovery from backup"
        echo ""
        echo "DANGER COMMANDS:"
        echo "  DANGER-rebuild - Rebuild container (takes 5-10 min)"
        echo ""
        echo "Current status:"
        if docker ps | grep -q pilotpros-agent-engine-dev; then
            echo "  ✅ Agent Engine is running"
        else
            echo "  ⏸️  Agent Engine is stopped"
        fi
        ;;
esac