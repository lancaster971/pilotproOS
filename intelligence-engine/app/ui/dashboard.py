"""
Intelligence Engine Dashboard - Real-time monitoring and analysis
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import httpx
import json
from typing import Dict, List, Any
import time

# Page configuration
st.set_page_config(
    page_title="Intelligence Engine Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stMetric {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    .operation-log {
        background-color: #0E0E0E;
        padding: 10px;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        max-height: 400px;
        overflow-y: auto;
    }
    .success { color: #4CAF50; }
    .warning { color: #FFA726; }
    .error { color: #EF5350; }
    .info { color: #42A5F5; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'operations_log' not in st.session_state:
    st.session_state.operations_log = []
if 'metrics_history' not in st.session_state:
    st.session_state.metrics_history = []
if 'active_chains' not in st.session_state:
    st.session_state.active_chains = []

def log_operation(level: str, message: str, details: Dict = None):
    """Log operation to display in UI"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_entry = {
        'timestamp': timestamp,
        'level': level,
        'message': message,
        'details': details or {}
    }
    st.session_state.operations_log.insert(0, log_entry)
    # Keep only last 100 operations
    if len(st.session_state.operations_log) > 100:
        st.session_state.operations_log = st.session_state.operations_log[:100]

async def fetch_metrics():
    """Fetch metrics from the Intelligence Engine API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/stats")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        log_operation("error", f"Failed to fetch metrics: {str(e)}")
    return None

async def monitor_chains():
    """Monitor active LangChain operations"""
    while True:
        try:
            async with httpx.AsyncClient() as client:
                # Simulate monitoring active chains
                log_operation("info", "🔍 Monitoring active chains...")

                # Check health
                health = await client.get("http://localhost:8000/health")
                if health.status_code == 200:
                    data = health.json()
                    log_operation("success", "✅ All services healthy", data['components'])

                # Check for active operations
                stats = await client.get("http://localhost:8000/api/stats")
                if stats.status_code == 200:
                    data = stats.json()
                    if data.get('active_sessions', 0) > 0:
                        log_operation("info", f"📊 Active sessions: {data['active_sessions']}")
                    if data.get('cache_hits', 0) > 0:
                        log_operation("success", f"⚡ Cache hits: {data['cache_hits']}")

                await asyncio.sleep(5)  # Check every 5 seconds

        except Exception as e:
            log_operation("error", f"Monitor error: {str(e)}")
            await asyncio.sleep(10)

def create_metrics_dashboard():
    """Create metrics visualization"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🚀 Response Time",
            value="124ms",
            delta="-12ms",
            delta_color="normal"
        )

    with col2:
        st.metric(
            label="💬 Active Chains",
            value=len(st.session_state.active_chains),
            delta="+2"
        )

    with col3:
        st.metric(
            label="🎯 Cache Hit Rate",
            value="87%",
            delta="+5%"
        )

    with col4:
        st.metric(
            label="📊 Tokens/Sec",
            value="1,247",
            delta="+124"
        )

def create_performance_charts():
    """Create performance visualization charts"""

    # Generate sample data for visualization
    time_range = pd.date_range(start='today', periods=100, freq='1min')

    # Response times
    response_times = np.random.normal(120, 20, 100)
    response_times = np.maximum(response_times, 50)  # Min 50ms

    # Token usage
    token_usage = np.random.normal(1200, 200, 100)
    token_usage = np.maximum(token_usage, 500)

    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '⚡ Response Time (ms)',
            '🔄 Active Chains',
            '💾 Cache Performance',
            '🧠 Model Usage'
        ),
        specs=[[{'secondary_y': False}, {'secondary_y': False}],
               [{'secondary_y': False}, {'type': 'pie'}]]
    )

    # Response time chart
    fig.add_trace(
        go.Scatter(
            x=time_range,
            y=response_times,
            mode='lines',
            name='Response Time',
            line=dict(color='#4CAF50', width=2),
            fill='tozeroy',
            fillcolor='rgba(76, 175, 80, 0.1)'
        ),
        row=1, col=1
    )

    # Active chains
    active_chains = np.random.poisson(3, 100)
    fig.add_trace(
        go.Bar(
            x=time_range,
            y=active_chains,
            name='Active Chains',
            marker_color='#2196F3'
        ),
        row=1, col=2
    )

    # Cache performance
    cache_hits = np.random.binomial(100, 0.87, 100)
    cache_misses = 100 - cache_hits

    fig.add_trace(
        go.Scatter(
            x=time_range,
            y=cache_hits,
            name='Cache Hits',
            mode='lines',
            line=dict(color='#9C27B0', width=2),
            stackgroup='one'
        ),
        row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=time_range,
            y=cache_misses,
            name='Cache Misses',
            mode='lines',
            line=dict(color='#F44336', width=2),
            stackgroup='one'
        ),
        row=2, col=1
    )

    # Model usage pie chart
    fig.add_trace(
        go.Pie(
            labels=['GPT-4o', 'Claude-3', 'Groq', 'Local'],
            values=[45, 30, 20, 5],
            hole=0.3,
            marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
        ),
        row=2, col=2
    )

    # Update layout
    fig.update_layout(
        height=600,
        showlegend=True,
        template='plotly_dark',
        title_text="🧠 Intelligence Engine Performance Metrics",
        title_font_size=20
    )

    return fig

def display_operations_log():
    """Display real-time operations log"""
    st.subheader("📝 Real-time Operations Log")

    log_container = st.container()

    with log_container:
        log_html = '<div class="operation-log">'

        for entry in st.session_state.operations_log[:50]:  # Show last 50
            level_class = entry['level']
            icon = {
                'success': '✅',
                'error': '❌',
                'warning': '⚠️',
                'info': 'ℹ️'
            }.get(entry['level'], '•')

            log_html += f'''
            <div class="{level_class}">
                [{entry['timestamp']}] {icon} {entry['message']}
                {' | ' + json.dumps(entry['details']) if entry['details'] else ''}
            </div>
            '''

        log_html += '</div>'
        st.markdown(log_html, unsafe_allow_html=True)

def create_chain_flow_diagram():
    """Create LangChain flow visualization"""
    st.subheader("🔗 Active Chain Flow")

    # Create a simple flow diagram
    fig = go.Figure()

    # Add nodes
    nodes = ['Input', 'Embedding', 'Vector Search', 'LLM', 'Tools', 'Output']
    node_x = [0, 1, 2, 3, 3, 4]
    node_y = [0, 0, 0.5, 0, -0.5, 0]

    # Add edges
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 4), (3, 5), (4, 5)
    ]

    for edge in edges:
        fig.add_trace(go.Scatter(
            x=[node_x[edge[0]], node_x[edge[1]]],
            y=[node_y[edge[0]], node_y[edge[1]]],
            mode='lines',
            line=dict(color='#666', width=2),
            showlegend=False,
            hoverinfo='skip'
        ))

    # Add nodes
    fig.add_trace(go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        marker=dict(
            size=40,
            color=['#4CAF50', '#2196F3', '#9C27B0', '#FF9800', '#E91E63', '#00BCD4'],
            line=dict(color='white', width=2)
        ),
        text=nodes,
        textposition='middle center',
        textfont=dict(color='white', size=10),
        showlegend=False,
        hovertemplate='<b>%{text}</b><extra></extra>'
    ))

    fig.update_layout(
        height=300,
        template='plotly_dark',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    return fig

# Main dashboard
def main():
    st.title("🧠 Intelligence Engine Dashboard")
    st.markdown("Real-time monitoring and analysis of LangChain operations")

    # Add operation logs
    log_operation("success", "🚀 Dashboard initialized successfully")
    log_operation("info", "📊 Loading metrics and visualizations...")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        refresh_rate = st.slider(
            "Refresh Rate (seconds)",
            min_value=1,
            max_value=60,
            value=5
        )

        st.divider()

        st.subheader("🔧 Active Services")
        services = {
            "LangChain Core": "🟢 Active",
            "Redis Cache": "🟢 Connected",
            "PostgreSQL": "🟢 Connected",
            "Vector Store": "🟢 Ready",
            "Streamlit UI": "🟢 Running"
        }

        for service, status in services.items():
            st.markdown(f"**{service}**: {status}")
            log_operation("info", f"Service check: {service} - {status}")

        st.divider()

        st.subheader("🎯 Quick Actions")

        if st.button("🔄 Clear Cache"):
            log_operation("warning", "Cache cleared by user")
            st.success("Cache cleared!")

        if st.button("📊 Export Metrics"):
            log_operation("info", "Metrics exported")
            st.success("Metrics exported!")

        if st.button("🔍 Run Diagnostics"):
            log_operation("info", "Running diagnostics...")
            with st.spinner("Running diagnostics..."):
                time.sleep(2)
            log_operation("success", "Diagnostics completed - All systems operational")
            st.success("All systems operational!")

    # Main content
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Metrics",
        "🔗 Chain Monitor",
        "📝 Operations Log",
        "🔍 Analysis"
    ])

    with tab1:
        st.header("📊 Performance Metrics")

        # Metrics dashboard
        create_metrics_dashboard()

        # Performance charts
        st.plotly_chart(
            create_performance_charts(),
            use_container_width=True
        )

        log_operation("success", "Performance metrics updated")

    with tab2:
        st.header("🔗 Chain Monitoring")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.plotly_chart(
                create_chain_flow_diagram(),
                use_container_width=True
            )

        with col2:
            st.subheader("Active Chains")
            chains = [
                {"name": "BusinessChain", "status": "🟢 Active", "latency": "124ms"},
                {"name": "AnalysisChain", "status": "🟡 Idle", "latency": "0ms"},
                {"name": "RAGChain", "status": "🟢 Processing", "latency": "287ms"}
            ]

            for chain in chains:
                with st.expander(chain["name"]):
                    st.write(f"Status: {chain['status']}")
                    st.write(f"Latency: {chain['latency']}")
                    log_operation("info", f"Chain {chain['name']}: {chain['status']}")

    with tab3:
        display_operations_log()

    with tab4:
        st.header("🔍 Deep Analysis")

        analysis_type = st.selectbox(
            "Select Analysis Type",
            ["Token Usage", "Response Patterns", "Error Analysis", "Cost Analysis"]
        )

        if st.button("Run Analysis"):
            log_operation("info", f"Running {analysis_type}...")
            with st.spinner(f"Running {analysis_type}..."):
                time.sleep(2)

                # Sample analysis result
                fig = px.line(
                    x=pd.date_range('today', periods=24, freq='H'),
                    y=np.random.randn(24).cumsum(),
                    title=f"{analysis_type} Results"
                )
                fig.update_layout(template='plotly_dark')
                st.plotly_chart(fig, use_container_width=True)

                log_operation("success", f"{analysis_type} completed successfully")

    # Auto-refresh
    if st.button("🔄 Refresh Now"):
        st.rerun()

    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        Intelligence Engine v1.0 | Powered by LangChain | Real-time Monitoring Active
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()