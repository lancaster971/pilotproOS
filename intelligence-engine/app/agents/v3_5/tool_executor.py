"""Tool Executor v3.5 - Direct async execution"""
import logging
from langsmith import traceable
from app.agents.v3_5.utils.state import AgentState
from app.agents.v3_5.tool_mapper import map_category_to_tools

logger = logging.getLogger(__name__)

@traceable(name="ToolExecution", run_type="tool", metadata={"version": "3.5.5"})
async def execute_tools_direct(state: AgentState, tool_mapper_fn=None) -> AgentState:
    classification = state.get("supervisor_decision", {})
    category = classification.get("category")
    params = classification.get("params", {})
    
    if not category:
        state["tool_results"] = []
        return state

    # Use tool_mapper_fn if provided (for testing), otherwise use default
    mapper = tool_mapper_fn or map_category_to_tools
    tool_functions, normalized_params = mapper(category, params)
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
