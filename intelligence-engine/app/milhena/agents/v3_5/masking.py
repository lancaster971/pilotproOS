"""Masking v3.5 - Business terminology"""
import logging
from app.milhena.utils.state import MilhenaState

logger = logging.getLogger(__name__)

async def mask_response(state: MilhenaState, masking_engine) -> MilhenaState:
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
