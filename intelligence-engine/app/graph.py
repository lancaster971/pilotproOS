"""
MilhenaGraph - Active Version Wrapper

This file imports the currently active agent version.
To switch versions, simply change the import below.

Current: v3.5.5 (Production)
"""

# ✅ ACTIVE VERSION
from app.agents.v3_5.graph import MilhenaGraph, milhena_graph

# 🔄 TO ROLLBACK/SWITCH:
# from app.agents.v4_0.graph import MilhenaGraph, milhena_graph

__all__ = ["MilhenaGraph", "milhena_graph"]
