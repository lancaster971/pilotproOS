#!/bin/bash
# 🔒 INTELLIGENCE ENGINE SAFE COMMANDS - CONTAINER LOCKED v1.0
# Comandi sicuri per gestire Intelligence Engine senza rebuild accidentali
# LOCKED IMAGE: pilotpros-intelligence-engine:locked-v1.0-langchain-0.3.27

set -e

CONTAINER_NAME="pilotpros-intelligence-engine"
IMAGE_NAME="pilotpros-intelligence-engine"
LOCKED_TAG="locked-v1.0-langchain-0.3.27"
LOCKED_IMAGE="${IMAGE_NAME}:${LOCKED_TAG}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_status() {
    echo -e "${BLUE}🧠 INTELLIGENCE ENGINE STATUS${NC}"
    echo "================================"
    echo ""

    # Check container
    if docker ps | grep -q $CONTAINER_NAME; then
        echo -e "  ${GREEN}✅ Intelligence Engine: Running${NC}"

        # Get container stats
        STATS=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" $CONTAINER_NAME 2>/dev/null | tail -n 1)
        if [ ! -z "$STATS" ]; then
            echo -e "  📊 Resources: $(echo $STATS | awk '{print "CPU: " $2 ", Memory: " $3}')"
        fi
    else
        if docker ps -a | grep -q $CONTAINER_NAME; then
            echo -e "  ${YELLOW}⏸️  Intelligence Engine: Stopped${NC}"
        else
            echo -e "  ${RED}❌ Intelligence Engine: Not found${NC}"
        fi
    fi

    echo ""
    echo "Access Points:"
    echo -e "  🚀 API:       ${GREEN}http://localhost:8000${NC}"
    echo -e "  📊 Dashboard: ${GREEN}http://localhost:8501${NC}"
    echo -e "  📈 Metrics:   ${GREEN}http://localhost:8000/metrics${NC}"
    echo ""
    echo -e "Locked Image: ${BLUE}${LOCKED_IMAGE}${NC}"
}

build_and_lock() {
    echo -e "${YELLOW}🔨 Building and locking Intelligence Engine image...${NC}"

    # Build the image
    docker build -t ${IMAGE_NAME}:latest ./intelligence-engine/

    # Tag as locked version
    docker tag ${IMAGE_NAME}:latest ${LOCKED_IMAGE}

    echo -e "${GREEN}✅ Image built and locked as: ${LOCKED_IMAGE}${NC}"
    echo ""
    echo -e "${BLUE}ℹ️  To prevent rebuilds, always use: ${LOCKED_IMAGE}${NC}"

    # Save image hash for verification
    IMAGE_ID=$(docker images -q ${LOCKED_IMAGE})
    echo "Image ID: $IMAGE_ID" > ./intelligence-engine/.locked-image-id
    echo -e "${GREEN}✅ Image ID saved for verification${NC}"
}

verify_image() {
    if [ -f ./intelligence-engine/.locked-image-id ]; then
        SAVED_ID=$(cat ./intelligence-engine/.locked-image-id | cut -d' ' -f3)
        CURRENT_ID=$(docker images -q ${LOCKED_IMAGE} 2>/dev/null)

        if [ "$SAVED_ID" == "$CURRENT_ID" ]; then
            echo -e "${GREEN}✅ Using verified locked image${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  Image mismatch detected${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  No locked image verification file found${NC}"
        return 1
    fi
}

case "$1" in
    "build-lock")
        build_and_lock
        ;;

    "start"|"up")
        echo -e "${GREEN}🚀 Starting Intelligence Engine (LOCKED - NO REBUILD)${NC}"

        # Verify locked image exists
        if ! docker images | grep -q "${IMAGE_NAME}.*${LOCKED_TAG}"; then
            echo -e "${RED}❌ Locked image not found!${NC}"
            echo -e "${YELLOW}Run: ./intelligence-engine-safe.sh build-lock${NC}"
            exit 1
        fi

        verify_image || echo -e "${YELLOW}⚠️  Continuing with existing image...${NC}"

        # Start using docker-compose but with locked image
        docker-compose up -d --no-build intelligence-engine

        echo -e "${GREEN}✅ Intelligence Engine started${NC}"
        show_status
        ;;

    "stop")
        echo -e "${YELLOW}⏸️  Stopping Intelligence Engine (preserving container)${NC}"
        docker stop $CONTAINER_NAME 2>/dev/null || true
        echo -e "${GREEN}✅ Intelligence Engine stopped${NC}"
        ;;

    "restart")
        echo -e "${BLUE}🔄 Restarting Intelligence Engine (NO REBUILD)${NC}"
        docker restart $CONTAINER_NAME 2>/dev/null || {
            echo -e "${YELLOW}Container not running, starting it...${NC}"
            docker-compose up -d --no-build intelligence-engine
        }
        echo -e "${GREEN}✅ Intelligence Engine restarted${NC}"
        show_status
        ;;

    "logs")
        echo -e "${BLUE}📋 Intelligence Engine logs (Ctrl+C to exit):${NC}"
        docker logs -f --tail 100 $CONTAINER_NAME
        ;;

    "dashboard")
        echo -e "${BLUE}📊 Opening Intelligence Engine Dashboard...${NC}"
        open http://localhost:8501 2>/dev/null || xdg-open http://localhost:8501 2>/dev/null || {
            echo -e "${GREEN}Dashboard URL: http://localhost:8501${NC}"
        }
        ;;

    "status"|"health")
        show_status

        # Health check
        echo -e "${BLUE}🏥 Health Check:${NC}"
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            HEALTH=$(curl -s http://localhost:8000/health)
            echo -e "  ${GREEN}✅ API: Healthy${NC}"
            echo "  Response: $(echo $HEALTH | jq -r '.status' 2>/dev/null || echo $HEALTH)"
        else
            echo -e "  ${RED}❌ API: Not responding${NC}"
        fi

        if curl -s http://localhost:8501 >/dev/null 2>&1; then
            echo -e "  ${GREEN}✅ Dashboard: Accessible${NC}"
        else
            echo -e "  ${YELLOW}⚠️  Dashboard: Not accessible${NC}"
        fi
        ;;

    "exec"|"shell")
        echo -e "${BLUE}🔧 Entering Intelligence Engine container...${NC}"
        docker exec -it $CONTAINER_NAME /bin/bash
        ;;

    "test")
        echo -e "${BLUE}🧪 Testing Intelligence Engine...${NC}"

        # Test API endpoint
        echo -e "\n${YELLOW}Testing API...${NC}"
        curl -X POST http://localhost:8000/api/chat \
            -H "Content-Type: application/json" \
            -d '{"message": "Hello, test the system", "user_id": "test_user"}' \
            2>/dev/null | jq '.' || echo -e "${RED}API test failed${NC}"

        echo -e "\n${GREEN}✅ Test completed${NC}"
        ;;

    "backup")
        echo -e "${BLUE}💾 Creating backup of locked image...${NC}"
        BACKUP_NAME="${LOCKED_IMAGE}-backup-$(date +%Y%m%d-%H%M%S).tar"
        docker save -o "$BACKUP_NAME" ${LOCKED_IMAGE}
        echo -e "${GREEN}✅ Backup saved as: $BACKUP_NAME${NC}"
        ;;

    "restore")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Usage: $0 restore <backup-file.tar>${NC}"
            exit 1
        fi
        echo -e "${BLUE}📥 Restoring from backup: $2${NC}"
        docker load -i "$2"
        echo -e "${GREEN}✅ Image restored${NC}"
        ;;

    "clean-logs")
        echo -e "${YELLOW}🧹 Cleaning Intelligence Engine logs...${NC}"
        docker exec $CONTAINER_NAME sh -c 'rm -f /app/logs/*.log' 2>/dev/null || true
        docker exec $CONTAINER_NAME sh -c 'echo "" > /app/logs/intelligence.log' 2>/dev/null || true
        echo -e "${GREEN}✅ Logs cleaned${NC}"
        ;;

    *)
        echo -e "${BLUE}🧠 Intelligence Engine Safe Commands${NC}"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Commands:"
        echo "  build-lock    - Build and lock the container image"
        echo "  start|up      - Start Intelligence Engine (no rebuild)"
        echo "  stop          - Stop Intelligence Engine"
        echo "  restart       - Restart Intelligence Engine"
        echo "  logs          - View logs"
        echo "  dashboard     - Open dashboard in browser"
        echo "  status|health - Show status and health"
        echo "  exec|shell    - Enter container shell"
        echo "  test          - Test Intelligence Engine"
        echo "  backup        - Backup locked image"
        echo "  restore       - Restore from backup"
        echo "  clean-logs    - Clean log files"
        echo ""
        echo -e "Locked Image: ${BLUE}${LOCKED_IMAGE}${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  IMPORTANT: Always use this script to avoid rebuilds!${NC}"
        exit 1
        ;;
esac