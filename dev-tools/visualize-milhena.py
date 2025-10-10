#!/usr/bin/env python3
"""
Milhena Agent Visual Debugger - Enhanced Visualization
Generates multiple readable graph formats from Milhena ReAct Agent
"""

import os
import sys
from pathlib import Path
from datetime import datetime

try:
    import graphviz
except ImportError:
    print("⚠️  Installing graphviz...")
    os.system("pip3 install graphviz --quiet")
    import graphviz

# Add intelligence-engine to path
sys.path.insert(0, str(Path(__file__).parent.parent / "intelligence-engine"))

from app.milhena.graph import MilhenaGraph

def generate_graphviz_visualization():
    """Generate clean Graphviz DOT format visualization"""

    print("🔍 Loading Milhena Graph...")
    milhena = MilhenaGraph()

    # Create Graphviz graph
    dot = graphviz.Digraph(
        comment='Milhena ReAct Agent',
        format='png',
        graph_attr={
            'rankdir': 'TB',  # Top to Bottom
            'bgcolor': '#1a1a1a',
            'pad': '0.5',
            'splines': 'ortho',  # Orthogonal edges (cleaner)
            'nodesep': '1.0',
            'ranksep': '1.5',
            'fontname': 'Arial',
            'fontsize': '14',
            'fontcolor': 'white'
        },
        node_attr={
            'shape': 'box',
            'style': 'rounded,filled',
            'fontname': 'Arial',
            'fontsize': '12',
            'margin': '0.3,0.2',
            'height': '0.8',
            'width': '2.0'
        },
        edge_attr={
            'fontname': 'Arial',
            'fontsize': '10',
            'color': '#666666',
            'fontcolor': 'white'
        }
    )

    print("📊 Analyzing graph structure...")

    # Get graph structure from LangGraph
    graph = milhena.graph

    # Add nodes with colors based on type
    node_colors = {
        'START': '#4CAF50',  # Green
        'REPHRASER': '#2196F3',  # Blue
        'MILHENA': '#FF9800',  # Orange (main agent)
        'tools': '#9C27B0',  # Purple
        'END': '#F44336'  # Red
    }

    # Map LangGraph nodes
    print("   Adding nodes...")
    for node_name in graph.nodes:
        if node_name == "__start__":
            dot.node('START', 'START',
                    fillcolor='#4CAF50', fontcolor='white')
        elif node_name == "__end__":
            dot.node('END', 'END',
                    fillcolor='#F44336', fontcolor='white')
        elif 'rephraser' in node_name.lower():
            dot.node(node_name, node_name.upper(),
                    fillcolor='#2196F3', fontcolor='white')
        elif 'milhena' in node_name.lower() or 'agent' in node_name.lower():
            dot.node(node_name, node_name.upper(),
                    fillcolor='#FF9800', fontcolor='white')
        elif 'tool' in node_name.lower():
            dot.node(node_name, node_name,
                    fillcolor='#9C27B0', fontcolor='white')
        else:
            dot.node(node_name, node_name,
                    fillcolor='#455A64', fontcolor='white')

    # Add edges
    print("   Adding edges...")
    for edge in graph.edges:
        if hasattr(edge, 'source') and hasattr(edge, 'target'):
            dot.edge(edge.source, edge.target)

    # Generate output
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    output_path = Path(__file__).parent / 'reports' / f'milhena-clean-{timestamp}'

    print(f"💾 Generating visualization...")
    dot.render(output_path, cleanup=True)

    png_path = f"{output_path}.png"
    print(f"\n✅ VISUALIZATION GENERATED")
    print(f"   Output: {png_path}")
    print(f"   Format: PNG (high resolution)")

    # Open in default viewer
    if sys.platform == 'darwin':  # macOS
        os.system(f'open "{png_path}"')
    elif sys.platform.startswith('linux'):
        os.system(f'xdg-open "{png_path}"')

    return png_path

def generate_ascii_tree():
    """Generate simple ASCII tree for terminal viewing"""
    print("\n📋 MILHENA GRAPH STRUCTURE (ASCII):")
    print("=" * 60)
    print("""
    START
      │
      ├─> [REPHRASER] Check Ambiguity
      │       │
      │       ├─> (clear) ──> MILHENA ReAct Agent
      │       └─> (ambiguous) ──> [REPHRASER] Rephrase ──┐
      │                                                    │
      ├─────────────────────────────────────────────────<─┘
      │
      └─> MILHENA ReAct Agent
            │
            ├─> [TOOLS] Smart Analytics Query (metric_type, period)
            ├─> [TOOLS] Smart Workflow Query (workflow_id, detail_level)
            ├─> [TOOLS] Smart Executions Query (scope, target, limit)
            ├─> [TOOLS] Get Error Details (workflow_name)
            ├─> [TOOLS] Get All Errors Summary
            ├─> [TOOLS] Get Node Execution Details
            ├─> [TOOLS] Get ChatOne Email Details
            ├─> [TOOLS] Get Raw Modal Data
            ├─> [TOOLS] Get Live Events
            ├─> [TOOLS] Get Workflows List
            ├─> [TOOLS] Get Workflow Cards
            ├─> [TOOLS] Search Knowledge Base (RAG)
            │
            └─> Response (with Business Masking)
                  │
                  └─> END
    """)
    print("=" * 60)
    print("\n💡 TIP: Use ./dev-tools/visualize-milhena.py for PNG diagram")

if __name__ == "__main__":
    print("🎨 MILHENA ENHANCED VISUALIZER\n")

    try:
        # Generate both formats
        generate_ascii_tree()
        print("\n" + "=" * 60 + "\n")
        png_path = generate_graphviz_visualization()

        print("\n✅ All visualizations ready!")
        print(f"   PNG: {png_path}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nFallback: Use ASCII tree above")
        sys.exit(1)
