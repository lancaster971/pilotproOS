"""
PilotProOS Intelligence Engine
Enterprise-Grade Business Assistant for Workflow Monitoring
Version: 3.5.6 - Self-Contained Agent Architecture
"""
import os
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# AGENT VERSION SWITCHER (v3.5.6 Self-Contained Architecture)
# ============================================================================
# Environment variable: AGENT_VERSION=v3_5|chatty (default: v3_5)
# Example: AGENT_VERSION=chatty docker-compose up

AGENT_VERSION = os.getenv("AGENT_VERSION", "v3_5")

if AGENT_VERSION == "chatty":
    logger.info("🎭 Loading Chatty Agent (pure chat mode)")
    from .agents.chatty.graph import ChattyGraph as AgentGraph

    def get_agent_graph():
        return AgentGraph()

elif AGENT_VERSION == "v3_5":
    logger.info("🤖 Loading Agent v3.5.6 (production)")
    from .agents.v3_5.graph import AgentGraph, get_agent_graph

else:
    raise ValueError(f"Unknown AGENT_VERSION: {AGENT_VERSION}. Use 'v3_5' or 'chatty'")

__all__ = [
    'AgentGraph',
    'get_agent_graph',
    'AGENT_VERSION'
]