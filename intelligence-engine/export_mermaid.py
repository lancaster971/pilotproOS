#!/usr/bin/env python3
"""Generate Mermaid diagram from Milhena graph"""

from app.milhena.graph import MilhenaGraph

def main():
    milhena = MilhenaGraph()
    graph = milhena.compiled_graph.get_graph()

    # Generate Mermaid syntax
    mermaid = ["graph TD"]

    # Add nodes
    for node in graph.nodes:
        node_id = node.replace(" ", "_").replace("[", "").replace("]", "")
        label = node
        mermaid.append(f'    {node_id}["{label}"]')

    # Add edges
    for edge in graph.edges:
        source = edge.source.replace(" ", "_").replace("[", "").replace("]", "")
        target = edge.target.replace(" ", "_").replace("[", "").replace("]", "")
        mermaid.append(f'    {source} --> {target}')

    # Print result
    result = "\n".join(mermaid)
    print(result)

    # Save to file
    with open("/tmp/milhena-graph.mmd", "w") as f:
        f.write(result)

    print("\n\n✅ Mermaid saved to: /tmp/milhena-graph.mmd", flush=True)

if __name__ == "__main__":
    main()
