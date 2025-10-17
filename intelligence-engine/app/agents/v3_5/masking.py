"""
Masking v3.5 - Business Abstraction Layer

Extracted from graph.py:2661-2679 (CONTEXT-SYSTEM.md compliance)
"""
import logging
from langsmith import traceable
from app.agents.v3_5.utils.state import AgentState

logger = logging.getLogger(__name__)


class Masking:
    """
    Masking Component - Final business terminology enforcement

    Removes technical terms from responses (n8n, PostgreSQL, workflow, etc.)
    to maintain business abstraction layer.
    """

    def __init__(self, masking_engine):
        self.masking_engine = masking_engine

    @traceable(name="MilhenaMaskResponse")
    async def mask_response(self, state: AgentState) -> AgentState:
        """Apply final masking to response"""
        response = state.get("response", "")

        if response:
            try:
                # Apply smart masking that preserves workflow names
                masked = self.masking_engine.mask(response)
                state["response"] = masked
                state["masked"] = True
                logger.info("Response masked (preserving workflow names)")
            except Exception as e:
                logger.error(f"Masking failed: {e}")
                state["masked"] = False
        else:
            state["masked"] = False

        return state
