"""Tool Executor v3.5 - Direct async execution"""
import logging
from langsmith import traceable
from app.milhena.utils.state import MilhenaState

logger = logging.getLogger(__name__)

@traceable(name="ToolExecution", run_type="tool", metadata={"version": "3.5.5"})
async def execute_tools_direct(state: MilhenaState, tool_mapper_fn) -> MilhenaState:
    classification = state.get("supervisor_decision", {})
    category = classification.get("category")
    params = classification.get("params", {})
    
    if not category:
        state["tool_results"] = []
        return state
    
    tool_functions, normalized_params = tool_mapper_fn(category, params)
    if not tool_functions:
        state["tool_results"] = []
        return state
    
    results = []
    for tool_fn in tool_functions:
        try:
            result = await tool_fn.ainvoke(normalized_params)
            results.append({"tool": tool_fn.name, "result": result})
        except Exception as e:
            logger.error(f"Tool {tool_fn.name} failed: {e}")
            results.append({"tool": tool_fn.name, "result": f"Error: {str(e)}"})
    
    state["tool_results"] = results
    return state
