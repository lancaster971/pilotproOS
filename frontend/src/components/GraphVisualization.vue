<template>
  <div class="graph-visualization">
    <h2>Intelligence Engine Architecture</h2>

    <!-- Tabs per diverse visualizzazioni -->
    <div class="tabs">
      <button @click="activeTab = 'live'" :class="{active: activeTab === 'live'}">
        Live Graph
      </button>
      <button @click="activeTab = 'interactive'" :class="{active: activeTab === 'interactive'}">
        Interactive
      </button>
      <button @click="activeTab = 'mermaid'" :class="{active: activeTab === 'mermaid'}">
        Mermaid
      </button>
    </div>

    <!-- Visualizzazione PNG dal backend -->
    <div v-if="activeTab === 'live'" class="graph-container">
      <img
        :src="graphImageUrl"
        alt="Agent Graph"
        @error="handleImageError"
        v-if="!imageError"
      />
      <div v-else class="error">
        Unable to load graph image
      </div>
      <button @click="refreshGraph" class="refresh-btn">
        Refresh Graph
      </button>
    </div>

    <!-- Visualizzazione Interattiva con D3.js -->
    <div v-if="activeTab === 'interactive'" class="graph-container">
      <svg ref="svgGraph" width="800" height="600"></svg>
    </div>

    <!-- Visualizzazione Mermaid -->
    <div v-if="activeTab === 'mermaid'" class="graph-container">
      <div ref="mermaidContainer" class="mermaid">
        {{ mermaidDiagram }}
      </div>
      <button @click="loadMermaid" class="refresh-btn">
        Load Diagram
      </button>
    </div>

    <!-- Info Panel -->
    <div class="info-panel" v-if="graphStructure">
      <h3>Graph Information</h3>
      <div class="info-grid">
        <div class="info-item">
          <strong>Nodes:</strong> {{ graphStructure.graph?.nodes?.length || 0 }}
        </div>
        <div class="info-item">
          <strong>Tools:</strong> {{ graphStructure.tools?.length || 0 }}
        </div>
        <div class="info-item">
          <strong>Model:</strong> {{ graphStructure.agent_config?.model }}
        </div>
        <div class="info-item">
          <strong>Max Iterations:</strong> {{ graphStructure.agent_config?.max_iterations }}
        </div>
      </div>

      <div class="tools-list">
        <h4>Available Tools:</h4>
        <ul>
          <li v-for="tool in graphStructure.tools" :key="tool">
            {{ tool }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import * as d3 from 'd3';
import mermaid from 'mermaid';

export default {
  name: 'GraphVisualization',
  data() {
    return {
      activeTab: 'live',
      imageError: false,
      graphStructure: null,
      mermaidDiagram: '',
      graphImageUrl: 'http://localhost:8000/graph/visualize'
    };
  },
  mounted() {
    this.loadGraphStructure();
    mermaid.initialize({ startOnLoad: true });
  },
  methods: {
    async loadGraphStructure() {
      try {
        const response = await fetch('http://localhost:8000/graph/structure');
        this.graphStructure = await response.json();

        // Se tab interattivo è attivo, disegna il grafo
        if (this.activeTab === 'interactive') {
          this.drawInteractiveGraph();
        }
      } catch (error) {
        console.error('Error loading graph structure:', error);
      }
    },

    async loadMermaid() {
      try {
        const response = await fetch('http://localhost:8000/graph/mermaid');
        const data = await response.json();
        this.mermaidDiagram = data.mermaid;

        // Renderizza Mermaid
        this.$nextTick(() => {
          const element = this.$refs.mermaidContainer;
          if (element) {
            mermaid.render('mermaid-graph', this.mermaidDiagram, (svgCode) => {
              element.innerHTML = svgCode;
            });
          }
        });
      } catch (error) {
        console.error('Error loading Mermaid:', error);
      }
    },

    drawInteractiveGraph() {
      if (!this.graphStructure) return;

      const svg = d3.select(this.$refs.svgGraph);
      svg.selectAll("*").remove();

      const width = 800;
      const height = 600;

      // Crea nodi dal grafo
      const nodes = this.graphStructure.graph.nodes.map((id, i) => ({
        id,
        x: width / 2 + Math.cos(i * 2 * Math.PI / this.graphStructure.graph.nodes.length) * 200,
        y: height / 2 + Math.sin(i * 2 * Math.PI / this.graphStructure.graph.nodes.length) * 200
      }));

      // Crea links dagli edges
      const links = this.graphStructure.graph.edges.map(edge => ({
        source: nodes.find(n => n.id === edge[0]),
        target: nodes.find(n => n.id === edge[1])
      }));

      // Simulazione forza
      const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(150))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2));

      // Aggiungi frecce per i link
      svg.append("defs").selectAll("marker")
        .data(["end"])
        .enter().append("marker")
        .attr("id", String)
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 25)
        .attr("refY", 0)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("fill", "#999");

      // Disegna links
      const link = svg.append("g")
        .attr("class", "links")
        .selectAll("line")
        .data(links)
        .enter().append("line")
        .attr("stroke", "#999")
        .attr("stroke-width", 2)
        .attr("marker-end", "url(#end)");

      // Disegna nodi
      const node = svg.append("g")
        .attr("class", "nodes")
        .selectAll("g")
        .data(nodes)
        .enter().append("g")
        .call(d3.drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended));

      // Cerchi per i nodi
      node.append("circle")
        .attr("r", 25)
        .attr("fill", d => {
          if (d.id.includes('start')) return '#4CAF50';
          if (d.id.includes('end')) return '#f44336';
          if (d.id === 'agent') return '#2196F3';
          if (d.id === 'tools') return '#FF9800';
          return '#9C27B0';
        });

      // Labels per i nodi
      node.append("text")
        .text(d => d.id.replace(/__/g, ''))
        .attr("text-anchor", "middle")
        .attr("dy", 4)
        .attr("fill", "white")
        .style("font-size", "12px")
        .style("font-weight", "bold");

      // Aggiorna posizioni durante simulazione
      simulation.on("tick", () => {
        link
          .attr("x1", d => d.source.x)
          .attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x)
          .attr("y2", d => d.target.y);

        node.attr("transform", d => `translate(${d.x},${d.y})`);
      });

      // Funzioni drag
      function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      }

      function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
      }

      function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }
    },

    refreshGraph() {
      this.imageError = false;
      // Aggiungi timestamp per forzare il refresh
      this.graphImageUrl = `http://localhost:8000/graph/visualize?t=${Date.now()}`;
      this.loadGraphStructure();
      console.log('Refreshing graph:', this.graphImageUrl);
    },

    handleImageError(error) {
      console.error('Error loading graph image:', error);
      this.imageError = true;
    }
  },
  watch: {
    activeTab(newTab) {
      if (newTab === 'interactive' && this.graphStructure) {
        this.$nextTick(() => this.drawInteractiveGraph());
      } else if (newTab === 'mermaid') {
        this.loadMermaid();
      }
    }
  }
};
</script>

<style scoped>
.graph-visualization {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.tabs button {
  padding: 10px 20px;
  background: #f0f0f0;
  border: none;
  cursor: pointer;
  border-radius: 5px;
  transition: background 0.3s;
}

.tabs button:hover {
  background: #e0e0e0;
}

.tabs button.active {
  background: #2196F3;
  color: white;
}

.graph-container {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  min-height: 600px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.graph-container img {
  max-width: 100%;
  height: auto;
  border: 1px solid #eee;
  border-radius: 4px;
}

.refresh-btn {
  margin-top: 20px;
  padding: 10px 20px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.refresh-btn:hover {
  background: #45a049;
}

.error {
  color: #f44336;
  padding: 20px;
  text-align: center;
}

.info-panel {
  margin-top: 30px;
  background: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin: 15px 0;
}

.info-item {
  padding: 10px;
  background: white;
  border-radius: 4px;
}

.tools-list {
  margin-top: 20px;
}

.tools-list ul {
  list-style: none;
  padding: 0;
}

.tools-list li {
  padding: 5px 10px;
  background: white;
  margin: 5px 0;
  border-radius: 4px;
  border-left: 3px solid #2196F3;
}

/* SVG Styles */
svg {
  border: 1px solid #ddd;
  border-radius: 4px;
}

.mermaid {
  text-align: center;
}
</style>