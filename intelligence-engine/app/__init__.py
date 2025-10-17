"""
PilotProOS Intelligence Engine
Enterprise-Grade Business Assistant for Workflow Monitoring
Version: 3.5.6 - Self-Contained Agent Architecture
"""

# v3.5.6: Import from self-contained agent structure
from .agents.v3_5.graph import AgentGraph, get_agent_graph

__all__ = [
    'AgentGraph',
    'get_agent_graph'
]