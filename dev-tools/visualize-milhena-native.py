#!/usr/bin/env python3
"""
MILHENA NATIVE VISUALIZER - Using LangGraph Built-in Methods
NO Agentic Radar, NO Graphviz bullshit - JUST LangGraph official API
"""

import sys
from pathlib import Path

# Add intelligence-engine to path
sys.path.insert(0, str(Path(__file__).parent.parent / "intelligence-engine"))

from app.milhena.graph import MilhenaGraph
from datetime import datetime

def visualize_milhena():
    """Generate clean PNG using LangGraph native draw_png()"""

    print("🔍 Loading Milhena Graph...")
    milhena = MilhenaGraph()
    graph = milhena.graph

    # Generate output path
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    output_dir = Path(__file__).parent / 'reports'
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f'milhena-native-{timestamp}.png'

    print(f"📊 Generating native LangGraph visualization...")

    try:
        # Use LangGraph's BUILT-IN draw_png method
        png_data = graph.get_graph().draw_png()

        # Save to file
        with open(output_path, 'wb') as f:
            f.write(png_data)

        print(f"\n✅ NATIVE VISUALIZATION COMPLETE")
        print(f"   Output: {output_path}")
        print(f"   Size: {len(png_data) // 1024}KB")

        # Open in default viewer
        import subprocess
        subprocess.run(['open', str(output_path)], check=False)

        return output_path

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n💡 TIP: Install pygraphviz if not present:")
        print("   pip install pygraphviz")
        return None

if __name__ == "__main__":
    visualize_milhena()
