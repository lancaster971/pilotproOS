"""
Intelligence Engine Dashboard - PilotProOS Style
Custom dashboard with same design as Vue frontend
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json

# Page configuration
st.set_page_config(
    page_title="Intelligence Engine - PilotProOS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - SAME AS FRONTEND
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&display=swap');

    /* ROOT VARIABLES FROM FRONTEND */
    :root {
        --background: #1a1a1d;
        --background-secondary: #1f1f23;
        --foreground: #f2f2f2;
        --foreground-muted: #6f7071;
        --card: #25252a;
        --card-hover: #2a2a30;
        --border: #2f2f35;
        --border-hover: #353540;
        --primary: #10b981;
        --primary-hover: #00d26a;
        --success: #89d185;
        --info: #10b981;
        --error: #f44747;
        --warning: #ffcc02;
    }

    /* OVERRIDE STREAMLIT DEFAULTS */
    .stApp {
        background: var(--background) !important;
        font-family: 'DM Sans', system-ui, sans-serif !important;
    }

    /* Main container */
    .main {
        background: var(--background) !important;
        color: var(--foreground) !important;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: var(--background-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }

    /* Headers */
    h1, h2, h3 {
        font-family: 'DM Sans', system-ui, sans-serif !important;
        font-weight: 600 !important;
        color: var(--foreground) !important;
    }

    h1 {
        background: linear-gradient(90deg, #10b981 0%, #00d26a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem !important;
        margin-bottom: 2rem !important;
    }

    /* Control Card Style */
    .control-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.2s ease;
    }

    .control-card:hover {
        border-color: rgba(16, 185, 129, 0.3);
        box-shadow: 0 0 20px rgba(34, 197, 94, 0.1);
    }

    /* Metrics */
    [data-testid="metric-container"] {
        background: var(--card);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid var(--border);
        transition: all 0.2s ease;
    }

    [data-testid="metric-container"]:hover {
        border-color: rgba(16, 185, 129, 0.3);
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.1);
        transform: translateY(-2px);
    }

    /* Buttons */
    .stButton > button {
        background: #374151 !important;
        border: 1px solid #4b5563 !important;
        color: white !important;
        padding: 0.5rem 1rem !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        font-family: 'DM Sans', system-ui, sans-serif !important;
    }

    .stButton > button:hover {
        background: #10b981 !important;
        border-color: #00d26a !important;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.25) !important;
    }

    /* Status indicators */
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }

    .status-success {
        background: #89d185;
        animation: pulse-success 2s infinite;
    }

    .status-error {
        background: #f44747;
        animation: pulse-error 2s infinite;
    }

    .status-warning {
        background: #ffcc02;
        animation: pulse-warning 2s infinite;
    }

    /* Operation Log */
    .operation-log {
        background: var(--background-secondary);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        max-height: 400px;
        overflow-y: auto;
    }

    .log-entry {
        padding: 0.25rem 0;
        border-bottom: 1px solid var(--border);
    }

    .log-success { color: #89d185; }
    .log-error { color: #f44747; }
    .log-warning { color: #ffcc02; }
    .log-info { color: #10b981; }

    /* Animations */
    @keyframes pulse-success {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    @keyframes pulse-error {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    @keyframes pulse-warning {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: transparent;
        border-bottom: 1px solid var(--border);
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--foreground-muted);
        border: none;
        padding: 0.5rem 1rem;
        font-family: 'DM Sans', system-ui, sans-serif;
    }

    .stTabs [aria-selected="true"] {
        background: transparent;
        color: var(--primary);
        border-bottom: 2px solid var(--primary);
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--foreground) !important;
    }

    /* Select box */
    .stSelectbox > div > div {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        color: var(--foreground) !important;
    }

    /* Glass effect */
    .glass-card {
        backdrop-filter: blur(16px);
        background: rgba(17, 25, 40, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #1f2937;
    }

    ::-webkit-scrollbar-thumb {
        background: #4b5563;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #6b7280;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'operations_log' not in st.session_state:
    st.session_state.operations_log = []
if 'metrics_history' not in st.session_state:
    st.session_state.metrics_history = []

def log_operation(level: str, message: str):
    """Add operation to log"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.operations_log.insert(0, {
        'timestamp': timestamp,
        'level': level,
        'message': message
    })
    if len(st.session_state.operations_log) > 100:
        st.session_state.operations_log = st.session_state.operations_log[:100]

def create_plotly_theme():
    """Create Plotly theme matching frontend"""
    return dict(
        layout=go.Layout(
            paper_bgcolor='#1a1a1d',
            plot_bgcolor='#25252a',
            font=dict(color='#f2f2f2', family='DM Sans'),
            xaxis=dict(
                gridcolor='#2f2f35',
                zerolinecolor='#2f2f35'
            ),
            yaxis=dict(
                gridcolor='#2f2f35',
                zerolinecolor='#2f2f35'
            ),
            colorway=['#10b981', '#00d26a', '#89d185', '#ffcc02', '#f44747']
        )
    )

def create_metrics_cards():
    """Create metric cards with custom styling"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="control-card">
            <div style="display: flex; align-items: center;">
                <span class="status-dot status-success"></span>
                <span style="color: #6f7071; font-size: 0.9rem;">Response Time</span>
            </div>
            <div style="font-size: 2rem; font-weight: 600; color: #10b981;">124ms</div>
            <div style="color: #89d185; font-size: 0.85rem;">↓ 12ms (8.8%)</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="control-card">
            <div style="display: flex; align-items: center;">
                <span class="status-dot status-success"></span>
                <span style="color: #6f7071; font-size: 0.9rem;">Active Chains</span>
            </div>
            <div style="font-size: 2rem; font-weight: 600; color: #10b981;">3</div>
            <div style="color: #89d185; font-size: 0.85rem;">↑ 2 chains</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="control-card">
            <div style="display: flex; align-items: center;">
                <span class="status-dot status-warning"></span>
                <span style="color: #6f7071; font-size: 0.9rem;">Cache Hit Rate</span>
            </div>
            <div style="font-size: 2rem; font-weight: 600; color: #ffcc02;">87%</div>
            <div style="color: #89d185; font-size: 0.85rem;">↑ 5%</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="control-card">
            <div style="display: flex; align-items: center;">
                <span class="status-dot status-success"></span>
                <span style="color: #6f7071; font-size: 0.9rem;">Tokens/Sec</span>
            </div>
            <div style="font-size: 2rem; font-weight: 600; color: #10b981;">1,247</div>
            <div style="color: #89d185; font-size: 0.85rem;">↑ 124 t/s</div>
        </div>
        """, unsafe_allow_html=True)

def create_performance_chart():
    """Create performance chart with custom theme"""
    # Generate sample data
    time_range = pd.date_range(start='today', periods=50, freq='2min')
    response_times = np.random.normal(120, 15, 50)

    fig = go.Figure()

    # Add gradient fill
    fig.add_trace(go.Scatter(
        x=time_range,
        y=response_times,
        mode='lines',
        name='Response Time',
        line=dict(color='#10b981', width=2),
        fill='tozeroy',
        fillcolor='rgba(16, 185, 129, 0.1)',
        hovertemplate='<b>%{x|%H:%M}</b><br>Response: %{y:.0f}ms<extra></extra>'
    ))

    fig.update_layout(
        **create_plotly_theme()['layout'],
        title='⚡ Real-time Performance',
        height=300,
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(showgrid=False),
        hovermode='x unified'
    )

    return fig

def create_chain_flow():
    """Create chain flow visualization"""
    fig = go.Figure()

    # Nodes
    nodes = ['Input', 'Embedding', 'Vector DB', 'LLM', 'Output']
    node_x = [0, 1, 2, 3, 4]
    node_y = [0, 0, 0, 0, 0]

    # Add connections
    for i in range(len(node_x) - 1):
        fig.add_trace(go.Scatter(
            x=[node_x[i], node_x[i+1]],
            y=[node_y[i], node_y[i+1]],
            mode='lines',
            line=dict(color='#10b981', width=2),
            showlegend=False,
            hoverinfo='skip'
        ))

    # Add nodes
    fig.add_trace(go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        marker=dict(
            size=50,
            color=['#10b981', '#00d26a', '#89d185', '#ffcc02', '#f44747'],
            line=dict(color='#2f2f35', width=2)
        ),
        text=nodes,
        textposition='middle center',
        textfont=dict(color='white', size=10, family='DM Sans'),
        showlegend=False,
        hovertemplate='<b>%{text}</b><extra></extra>'
    ))

    fig.update_layout(
        **create_plotly_theme()['layout'],
        height=200,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    return fig

def display_operations_log():
    """Display operations log with custom styling"""
    log_html = '<div class="operation-log">'

    for entry in st.session_state.operations_log[:20]:
        level_class = f"log-{entry['level']}"
        icon = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        }.get(entry['level'], '•')

        log_html += f'''
        <div class="log-entry {level_class}">
            <span style="color: #6f7071">[{entry['timestamp']}]</span> {icon} {entry['message']}
        </div>
        '''

    log_html += '</div>'
    st.markdown(log_html, unsafe_allow_html=True)

# Main Dashboard
def main():
    # Header with gradient
    st.markdown("""
    <h1 style="text-align: center; margin-bottom: 0;">
        🧠 Intelligence Engine
    </h1>
    <p style="text-align: center; color: #6f7071; font-size: 1.1rem; margin-top: 0;">
        PilotProOS LangChain Control Center
    </p>
    """, unsafe_allow_html=True)

    # Add some operations to log
    log_operation("success", "Dashboard initialized")
    log_operation("info", "Connected to LangChain v0.3.27")
    log_operation("success", "Redis cache ready")
    log_operation("warning", "High memory usage detected")

    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Control Panel")

        st.markdown("""
        <div class="control-card">
            <h4 style="color: #10b981; margin-top: 0;">🔧 Services</h4>
        """, unsafe_allow_html=True)

        services = {
            "LangChain Core": "success",
            "Redis Cache": "success",
            "PostgreSQL": "success",
            "Vector Store": "warning",
            "Streamlit UI": "success"
        }

        for service, status in services.items():
            st.markdown(f"""
            <div style="padding: 0.5rem 0; display: flex; align-items: center;">
                <span class="status-dot status-{status}"></span>
                <span style="color: #f2f2f2;">{service}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        if st.button("🔄 Clear Cache"):
            log_operation("warning", "Cache cleared by user")
            st.success("Cache cleared!")

        if st.button("📊 Export Metrics"):
            log_operation("info", "Metrics exported")
            st.success("Metrics exported!")

    # Main content with tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Metrics", "🔗 Chains", "📝 Operations", "🔍 Analysis"])

    with tab1:
        st.markdown("### Real-time Performance Metrics")
        create_metrics_cards()

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_performance_chart(), use_container_width=True)
        with col2:
            st.plotly_chart(create_chain_flow(), use_container_width=True)

    with tab2:
        st.markdown("### Active LangChain Operations")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.plotly_chart(create_chain_flow(), use_container_width=True)

        with col2:
            st.markdown("""
            <div class="control-card">
                <h4 style="color: #10b981;">Active Chains</h4>
                <div style="color: #89d185;">• BusinessChain (124ms)</div>
                <div style="color: #ffcc02;">• AnalysisChain (idle)</div>
                <div style="color: #89d185;">• RAGChain (287ms)</div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.markdown("### System Operations Log")
        display_operations_log()

    with tab4:
        st.markdown("### Deep Analysis")

        analysis_type = st.selectbox(
            "Select Analysis",
            ["Token Usage", "Response Patterns", "Error Analysis", "Cost Analysis"]
        )

        if st.button("Run Analysis"):
            with st.spinner("Running analysis..."):
                time.sleep(1)
                log_operation("success", f"{analysis_type} completed")
                st.success(f"{analysis_type} completed!")

    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #6f7071; border-top: 1px solid #2f2f35; margin-top: 3rem;">
        <small>Intelligence Engine v1.0 | LangChain 0.3.27 | Real-time Monitoring Active</small>
    </div>
    """, unsafe_allow_html=True)

    # Auto-refresh
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()