#!/bin/bash
# 🔒 PILOTPRO STACK SAFE COMMANDS
# Comandi sicuri per gestire l'intero stack senza rebuild accidentali

set -e

show_status() {
    echo "🚀 PILOTPRO STACK STATUS"
    echo "======================="
    echo ""

    # Check containers
    if docker ps | grep -q pilotpros-frontend-dev; then
        echo "  ✅ Frontend: Running"
    else
        echo "  ⏸️  Frontend: Stopped"
    fi

    if docker ps | grep -q pilotpros-backend-dev; then
        echo "  ✅ Backend: Running"
    else
        echo "  ⏸️  Backend: Stopped"
    fi

    # Agent Engine REMOVED (CrewAI eliminated)

    if docker ps | grep -q pilotpros-postgres-dev; then
        echo "  ✅ PostgreSQL: Running"
    else
        echo "  ⏸️  PostgreSQL: Stopped"
    fi

    if docker ps | grep -q pilotpros-redis-dev; then
        echo "  ✅ Redis: Running"
    else
        echo "  ⏸️  Redis: Stopped"
    fi

    if docker ps | grep -q pilotpros-automation-engine-dev; then
        echo "  ✅ Automation: Running"
    else
        echo "  ⏸️  Automation: Stopped"
    fi

    if docker ps | grep -q pilotpros-nginx-dev; then
        echo "  ✅ System Monitor: Running"
    else
        echo "  ⏸️  System Monitor: Stopped"
    fi

    echo ""
    echo "Access Points:"
    echo "  🌐 Frontend:      http://localhost:3000"
    echo "  ⚙️  Backend API:   http://localhost:3001"
    echo "  🔧 Stack Control: http://localhost:3005"
    echo "  🔄 Automation:    http://localhost:5678"
}

case "$1" in
    "start"|"up")
        echo "🚀 Starting PilotPro Stack (NO REBUILD)"
        docker-compose up -d
        echo "✅ Stack started"
        show_status
        ;;

    "stop")
        echo "⏸️  Stopping PilotPro Stack (preserving containers)"
        docker-compose stop
        echo "✅ Stack stopped"
        ;;

    "restart")
        echo "🔄 Restarting PilotPro Stack (NO REBUILD)"
        docker-compose restart
        echo "✅ Stack restarted"
        show_status
        ;;

    "logs")
        service="$2"
        if [ -z "$service" ]; then
            echo "📋 All services logs (use Ctrl+C to exit):"
            docker-compose logs -f --tail 50
        else
            echo "📋 $service logs:"
            docker-compose logs -f --tail 50 "$service"
        fi
        ;;

    "status"|"health")
        show_status
        echo ""
        echo "🏥 Health Checks:"

        # Backend health
        if curl -s http://localhost:3001/api/health >/dev/null 2>&1; then
            echo "  ✅ Backend API: Healthy"
        else
            echo "  ❌ Backend API: Not responding"
        fi

        # Agent Engine REMOVED (CrewAI eliminated)

        # Frontend (check if serving)
        if curl -s http://localhost:3000 >/dev/null 2>&1; then
            echo "  ✅ Frontend: Serving"
        else
            echo "  ❌ Frontend: Not serving"
        fi
        ;;

    "test")
        echo "🧪 Testing Stack Components:"

        # Test Backend
        echo -n "  Backend API: "
        if curl -s http://localhost:3001/api/health | grep -q "ok"; then
            echo "✅ OK"
        else
            echo "❌ Failed"
        fi

        # Agent Engine and Milhena REMOVED (CrewAI eliminated)
        ;;

    "backup")
        echo "💾 Creating backup images..."
        docker tag pilotproos-frontend-dev:latest \
            pilotproos-frontend-dev:backup-$(date +%Y%m%d-%H%M%S)
        docker tag pilotproos-backend-dev:latest \
            pilotproos-backend-dev:backup-$(date +%Y%m%d-%H%M%S)
        echo "✅ Backups created (Agent Engine REMOVED)"
        ;;

    "recovery")
        echo "🚨 Running emergency recovery..."
        echo "This will restore from locked images:"
        echo "  - Frontend: locked-v1.0-stable"
        echo "  - Backend: locked-v1.0-stable"
        echo "  - Agent Engine: REMOVED (CrewAI eliminated)"
        echo ""
        echo "Continue? (y/N)"
        read -r confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            docker tag pilotproos-frontend-dev:locked-v1.0-stable pilotproos-frontend-dev:latest
            docker tag pilotproos-backend-dev:locked-v1.0-stable pilotproos-backend-dev:latest
            docker-compose up -d
            echo "✅ Emergency recovery completed (Agent Engine excluded)"
        else
            echo "❌ Recovery cancelled"
        fi
        ;;

    "DANGER-rebuild")
        echo "⚠️  DANGER ZONE: This will rebuild ALL custom containers!"
        echo "This will take 5-10 minutes and rebuild:"
        echo "  - Frontend (Vue 3 + TypeScript)"
        echo "  - Backend (Express + Auth)"
        echo "  - Agent Engine: REMOVED (CrewAI eliminated)"
        echo ""
        echo "Type 'YES-I-WANT-TO-REBUILD-ALL' to confirm:"
        read -r confirm
        if [ "$confirm" = "YES-I-WANT-TO-REBUILD-ALL" ]; then
            echo "🏗️  Rebuilding all containers..."
            docker-compose build --no-cache frontend-dev backend-dev
            docker-compose up -d
            echo "✅ Full rebuild completed (Agent Engine excluded)"
        else
            echo "❌ Rebuild cancelled"
        fi
        ;;

    "frontend")
        case "$2" in
            "rebuild")
                echo "🏗️  Rebuilding Frontend only..."
                docker-compose build --no-cache frontend-dev
                docker-compose up -d frontend-dev
                ;;
            *)
                echo "Frontend commands: rebuild"
                ;;
        esac
        ;;

    "backend")
        case "$2" in
            "rebuild")
                echo "🏗️  Rebuilding Backend only..."
                docker-compose build --no-cache backend-dev
                docker-compose up -d backend-dev
                ;;
            *)
                echo "Backend commands: rebuild"
                ;;
        esac
        ;;

    *)
        echo "🔒 PILOTPRO STACK SAFE COMMANDS"
        echo "==============================="
        echo ""
        echo "SAFE COMMANDS:"
        echo "  start     - Start entire stack (no rebuild)"
        echo "  stop      - Stop entire stack (preserve containers)"
        echo "  restart   - Restart entire stack (no rebuild)"
        echo "  logs [service] - View logs (all or specific service)"
        echo "  status    - Show stack status and health"
        echo "  test      - Test all components"
        echo "  backup    - Create backup images"
        echo "  recovery  - Emergency recovery from locked images"
        echo ""
        echo "COMPONENT COMMANDS:"
        echo "  frontend rebuild  - Rebuild only frontend"
        echo "  backend rebuild   - Rebuild only backend"
        echo ""
        echo "DANGER COMMANDS:"
        echo "  DANGER-rebuild - Rebuild all containers (10-15 min)"
        echo ""
        show_status
        ;;
esac