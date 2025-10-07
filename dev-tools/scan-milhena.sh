#!/bin/bash
# =============================================================================
# MILHENA AGENT VISUAL DEBUGGER - Agentic Radar Scanner
# =============================================================================
# Description: Scan Milhena ReAct Agent for security vulnerabilities and
#              generate interactive visual workflow graph
# Usage: ./dev-tools/scan-milhena.sh
# Output: dev-tools/reports/milhena-YYYYMMDD-HHMMSS.html
# =============================================================================

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 MILHENA VISUAL DEBUGGER${NC}"
echo "=================================================="

# Check if agentic-radar is installed
if ! command -v agentic-radar &> /dev/null; then
    echo -e "${YELLOW}⚠️  Agentic Radar not found. Installing...${NC}"
    cd intelligence-engine
    python3 -m pip install agentic-radar --quiet
    cd ..
    echo -e "${GREEN}✅ Agentic Radar installed${NC}"
fi

# Generate timestamp for report filename
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_NAME="milhena-${TIMESTAMP}.html"
REPORT_PATH="dev-tools/reports/${REPORT_NAME}"

echo -e "${BLUE}📊 Scanning Milhena ReAct Agent...${NC}"
echo "   Target: intelligence-engine/app/milhena"
echo "   Framework: LangGraph"
echo ""

# Run agentic-radar scan with optimized graph layout
cd intelligence-engine
agentic-radar scan langgraph \
    -i app/milhena \
    -o "../${REPORT_PATH}" \
    --verbose  # More detailed output for better graph
cd ..

# Post-process HTML for better readability (increase graph size)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS: Increase canvas size in HTML
    sed -i '' 's/width: 800px/width: 1600px/g' "${REPORT_PATH}" 2>/dev/null || true
    sed -i '' 's/height: 600px/height: 1200px/g' "${REPORT_PATH}" 2>/dev/null || true
fi

# Check if report was generated
if [ -f "${REPORT_PATH}" ]; then
    REPORT_SIZE=$(du -h "${REPORT_PATH}" | cut -f1)
    echo ""
    echo -e "${GREEN}✅ SCAN COMPLETE${NC}"
    echo "=================================================="
    echo "   Report: ${REPORT_PATH}"
    echo "   Size: ${REPORT_SIZE}"
    echo ""
    echo -e "${BLUE}🌐 Opening report in browser...${NC}"

    # Open report in default browser (macOS/Linux compatible)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "${REPORT_PATH}"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "${REPORT_PATH}" 2>/dev/null || echo "Open manually: ${REPORT_PATH}"
    else
        echo "   Please open manually: ${REPORT_PATH}"
    fi

    echo ""
    echo -e "${GREEN}✅ Visual debugging ready!${NC}"
else
    echo -e "${YELLOW}⚠️  Report not generated. Check errors above.${NC}"
    exit 1
fi
