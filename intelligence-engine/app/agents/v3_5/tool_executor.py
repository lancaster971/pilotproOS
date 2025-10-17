"""
Tool Executor v3.5 - Direct async execution

Extracted from graph.py:2411-2476 (CONTEXT-SYSTEM.md compliance)
"""
import logging
from langsmith import traceable
from app.agents.v3_5.utils.state import AgentState
from app.agents.v3_5.tool_mapper import map_category_to_tools

logger = logging.getLogger(__name__)


@traceable(
    name="MilhenaToolExecution",
    run_type="tool",
    metadata={"component": "tool_execution", "version": "3.5.0"}
)
async def execute_tools_direct(state: AgentState) -> AgentState:
    """
    v3.5.0: Direct tool execution (NO agent)

    Flow:
    1. Get category + params from classifier
    2. Map category → tool function(s)
    3. Call tool.invoke(params) directly
    4. Save RAW data in state (NO synthesis here)

    Synthesis happens in Responder Agent (separate node)
    """
    classification = state.get("supervisor_decision", {})
    category = classification.get("category")
    params = classification.get("params", {})

    logger.info(f"[TOOL EXECUTION v3.5.0] category={category}, params={params}")

    if not category:
        logger.error("[TOOL EXECUTION] No category in classification!")
        state["tool_results"] = []
        return state

    try:
        # Get tool function(s) + normalized params from mapper
        tool_functions, normalized_params = map_category_to_tools(category, params)

        if not tool_functions:
            logger.warning(f"[TOOL EXECUTION] No tools mapped for category: {category}")
            state["tool_results"] = []
            return state

        logger.info(f"[TOOL EXECUTION] Normalized params: {normalized_params}")

        # Execute tool(s) directly
        results = []
        for tool_fn in tool_functions:
            logger.info(f"[TOOL EXECUTION] Calling {tool_fn.name}...")

            try:
                # Use normalized params from tool_mapper
                result = await tool_fn.ainvoke(normalized_params)

                # DEBUG: Log result content
                result_preview = result[:200] if isinstance(result, str) else str(result)[:200]
                logger.info(f"[TOOL EXECUTION] Tool {tool_fn.name} returned: {result_preview}")

                results.append({
                    "tool": tool_fn.name,
                    "result": result
                })
                logger.info(f"[TOOL EXECUTION] ✅ {tool_fn.name} completed")
            except Exception as tool_error:
                logger.error(f"[TOOL EXECUTION] Tool {tool_fn.name} failed: {tool_error}")
                # Continue with other tools instead of failing completely
                results.append({
                    "tool": tool_fn.name,
                    "result": f"Error: {str(tool_error)}"
                })

        # Save RAW results (Responder will synthesize)
        state["tool_results"] = results
        logger.info(f"[TOOL EXECUTION] {len(results)} tool(s) executed successfully")

    except Exception as e:
        logger.error(f"[TOOL EXECUTION] Failed: {e}")
        state["tool_results"] = []
        state["context"]["tool_error"] = str(e)

    return state
