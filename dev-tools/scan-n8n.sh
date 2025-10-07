#!/bin/bash
# =============================================================================
# N8N WORKFLOWS VISUAL DEBUGGER - Agentic Radar Scanner
# =============================================================================
# Description: Scan n8n workflows for security vulnerabilities
# Usage: ./dev-tools/scan-n8n.sh [workflow-export-path]
# Output: dev-tools/reports/n8n-YYYYMMDD-HHMMSS.html
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔍 N8N WORKFLOWS VISUAL DEBUGGER${NC}"
echo "=================================================="

# Check if workflow export path provided
N8N_PATH="${1:-n8n_workflows_export}"

if [ ! -d "${N8N_PATH}" ]; then
    echo -e "${RED}❌ ERROR: Workflow export directory not found${NC}"
    echo ""
    echo "Please export n8n workflows first:"
    echo "  1. Open n8n (http://localhost:5678)"
    echo "  2. Export workflows to JSON"
    echo "  3. Save to: ${N8N_PATH}/"
    echo ""
    echo "Or specify custom path:"
    echo "  ./dev-tools/scan-n8n.sh /path/to/workflows"
    exit 1
fi

# Check agentic-radar
if ! command -v agentic-radar &> /dev/null; then
    echo -e "${YELLOW}⚠️  Installing Agentic Radar...${NC}"
    cd intelligence-engine
    python3 -m pip install agentic-radar --quiet
    cd ..
fi

# Generate report
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_NAME="n8n-${TIMESTAMP}.html"
REPORT_PATH="dev-tools/reports/${REPORT_NAME}"

echo -e "${BLUE}📊 Scanning n8n workflows...${NC}"
echo "   Target: ${N8N_PATH}"
echo "   Framework: n8n"
echo ""

# Run scan
agentic-radar scan n8n \
    -i "${N8N_PATH}" \
    -o "${REPORT_PATH}"

# Open report
if [ -f "${REPORT_PATH}" ]; then
    REPORT_SIZE=$(du -h "${REPORT_PATH}" | cut -f1)
    echo ""
    echo -e "${GREEN}✅ SCAN COMPLETE${NC}"
    echo "=================================================="
    echo "   Report: ${REPORT_PATH}"
    echo "   Size: ${REPORT_SIZE}"
    echo ""

    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "${REPORT_PATH}"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "${REPORT_PATH}" 2>/dev/null
    fi

    echo -e "${GREEN}✅ Visual debugging ready!${NC}"
else
    echo -e "${RED}❌ Report generation failed${NC}"
    exit 1
fi
