"""Masking v3.5 - Business terminology"""
import logging
from app.agents.v3_5.utils.state import AgentState

logger = logging.getLogger(__name__)

async def mask_response(state: AgentState, masking_engine) -> AgentState:
    response = state.get("response", "")
    if response:
        try:
            masked = masking_engine.mask(response)
            state["response"] = masked
            state["masked"] = True
        except Exception as e:
            logger.error(f"Masking failed: {e}")
            state["masked"] = False
    else:
        state["masked"] = False
    return state
