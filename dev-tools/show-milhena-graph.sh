#!/bin/bash
# =============================================================================
# MILHENA GRAPH VIEWER - Simple API-based visualization
# =============================================================================
# Uses Intelligence Engine built-in /graph/visualize endpoint
# NO Agentic Radar, NO Graphviz, NO bullshit - JUST WORKS
# =============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}📊 MILHENA GRAPH VIEWER${NC}"
echo "=============================================="

# Check if Intelligence Engine is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}❌ Intelligence Engine not running${NC}"
    echo ""
    echo "Start it with:"
    echo "  ./stack-safe.sh start"
    echo ""
    exit 1
fi

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT="dev-tools/reports/milhena-graph-${TIMESTAMP}.png"

echo -e "${BLUE}📥 Downloading graph from API...${NC}"
curl -s http://localhost:8000/graph/visualize --output "${OUTPUT}"

if [ -f "${OUTPUT}" ]; then
    SIZE=$(du -h "${OUTPUT}" | cut -f1)
    echo ""
    echo -e "${GREEN}✅ GRAPH READY${NC}"
    echo "=============================================="
    echo "   File: ${OUTPUT}"
    echo "   Size: ${SIZE}"
    echo ""
    echo -e "${BLUE}🌐 Opening graph...${NC}"
    open "${OUTPUT}"
    echo -e "${GREEN}✅ Done!${NC}"
else
    echo -e "${RED}❌ Failed to download graph${NC}"
    exit 1
fi
