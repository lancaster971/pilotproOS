#!/bin/bash
# =============================================================================
# MILHENA READABLE GRAPH GENERATOR
# =============================================================================
# Uses Agentic Radar JSON export + Custom Graphviz visualization
# Generates CLEAN, READABLE graph diagrams
# =============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🎨 MILHENA READABLE GRAPH GENERATOR${NC}"
echo "======================================================"

# Check dependencies
if ! command -v dot &> /dev/null; then
    echo -e "${YELLOW}⚠️  Graphviz not found. Installing...${NC}"
    brew install graphviz 2>/dev/null || {
        echo "Please install graphviz manually:"
        echo "  macOS: brew install graphviz"
        echo "  Linux: sudo apt install graphviz"
        exit 1
    }
fi

# Generate JSON export
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
JSON_FILE="dev-tools/reports/milhena-${TIMESTAMP}.json"
HTML_FILE="dev-tools/reports/milhena-${TIMESTAMP}.html"

echo -e "${BLUE}📊 Step 1: Export graph JSON...${NC}"
cd intelligence-engine
agentic-radar scan langgraph \
    -i app/milhena \
    -o "../${JSON_FILE}" \
    --export-graph-json
cd ..

echo -e "${GREEN}✅ JSON exported: ${JSON_FILE}${NC}"

# Generate readable HTML report (without graph JSON flag)
echo -e "${BLUE}📊 Step 2: Generate HTML report...${NC}"
cd intelligence-engine
agentic-radar scan langgraph \
    -i app/milhena \
    -o "../${HTML_FILE}"
cd ..

echo -e "${GREEN}✅ HTML report: ${HTML_FILE}${NC}"

# Create Python script for custom visualization
echo -e "${BLUE}🎨 Step 3: Generate custom visualization...${NC}"

cat > /tmp/visualize_milhena.py << 'PYTHON_SCRIPT'
import json
import sys
from graphviz import Digraph

# Read JSON
with open(sys.argv[1], 'r') as f:
    data = json.load(f)

# Create graph
dot = Digraph(comment='Milhena ReAct Agent', format='png')
dot.attr(rankdir='TB', bgcolor='#1a1a1a', pad='1.0', nodesep='2.0', ranksep='2.5')
dot.attr('node', shape='box', style='rounded,filled', fontname='Arial Bold',
         fontsize='14', margin='0.5,0.3', height='1.0', width='3.0',
         fontcolor='white')
dot.attr('edge', fontname='Arial', fontsize='11', fontcolor='white',
         color='#666666', penwidth='2.0')

# Add nodes
nodes = data.get('nodes', [])
for node in nodes:
    node_id = node.get('id', '')
    label = node.get('label', node_id)
    node_type = node.get('type', 'default')

    # Color coding
    if 'start' in node_id.lower():
        color = '#4CAF50'  # Green
    elif 'rephraser' in node_id.lower():
        color = '#2196F3'  # Blue
    elif 'agent' in node_id.lower() or 'milhena' in node_id.lower():
        color = '#FF9800'  # Orange
    elif 'tool' in node_id.lower():
        color = '#9C27B0'  # Purple
    elif 'end' in node_id.lower():
        color = '#F44336'  # Red
    else:
        color = '#455A64'  # Grey

    dot.node(node_id, label, fillcolor=color)

# Add edges
edges = data.get('edges', [])
for edge in edges:
    source = edge.get('source', '')
    target = edge.get('target', '')
    label = edge.get('label', '')

    if source and target:
        dot.edge(source, target, label=label)

# Render
output = sys.argv[2]
dot.render(output, cleanup=True)
print(f"✅ Generated: {output}.png")
PYTHON_SCRIPT

# Run visualization
OUTPUT_BASE="dev-tools/reports/milhena-readable-${TIMESTAMP}"
python3 /tmp/visualize_milhena.py "${JSON_FILE}" "${OUTPUT_BASE}"

PNG_FILE="${OUTPUT_BASE}.png"

echo ""
echo -e "${GREEN}✅ READABLE VISUALIZATION COMPLETE${NC}"
echo "======================================================"
echo "   JSON: ${JSON_FILE}"
echo "   HTML Report: ${HTML_FILE}"
echo "   PNG Graph: ${PNG_FILE}"
echo ""

# Open PNG
if [ -f "${PNG_FILE}" ]; then
    echo -e "${BLUE}🌐 Opening readable graph...${NC}"
    open "${PNG_FILE}"
else
    echo -e "${YELLOW}⚠️  PNG not generated. Check errors above.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Visual debugging ready!${NC}"
