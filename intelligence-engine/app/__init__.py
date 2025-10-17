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
# Environment variable: AGENT_VERSION (default: v3_5)
# Future versions: AGENT_VERSION=v4_0 docker-compose up

AGENT_VERSION = os.getenv("AGENT_VERSION", "v3_5")

if AGENT_VERSION == "v3_5":
    logger.info("🤖 Loading Agent v3.5.6 (production)")
    from .agents.v3_5.graph import AgentGraph, get_agent_graph

else:
    raise ValueError(f"Unknown AGENT_VERSION: {AGENT_VERSION}. Currently only 'v3_5' is available.")

__all__ = [
    'AgentGraph',
    'get_agent_graph',
    'AGENT_VERSION'
]