"""Tool Mapper v3.5 - Category to Tools mapping + parameter normalization"""
import logging
from typing import Dict, Any, Optional, List
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

def map_category_to_tools(category: str, raw_params: Optional[Dict[str, Any]] = None) -> tuple:
    """
    Map classification category to appropriate tool function(s) + normalized params.

    Args:
        category: One of 9 categories (PROCESS_LIST, PROCESS_DETAIL, etc.)
        raw_params: Raw parameters from classifier (may need normalization)

    Returns:
        (tools_list, normalized_params_dict)

    Normalization rules:
    - workflow_name → workflow_id (standardization)
    - Missing required params → use fallback tool if available
    - Add default params where needed (e.g., active=true for toggle)
    """
    # Import tools here to avoid circular imports
    from app.utils.business_tools import (
        smart_analytics_query_tool,
        smart_workflow_query_tool,
        smart_executions_query_tool,
        get_error_details_tool,
        get_all_errors_summary_tool,
        get_node_execution_details_tool,
        get_chatone_email_details_tool,
        get_workflows_tool,
        execute_workflow_tool,
        toggle_workflow_tool,
        get_full_database_dump
    )

    params = raw_params or {}

    # Normalize workflow_name → workflow_id (common case)
    if "workflow_name" in params and "workflow_id" not in params:
        params["workflow_id"] = params.pop("workflow_name")

    # Category-specific mapping + normalization
    if category == "PROCESS_LIST":
        return [get_workflows_tool], {}

    elif category == "PROCESS_DETAIL":
        # Requires: workflow_id
        return [smart_workflow_query_tool], params

    elif category == "EXECUTION_QUERY":
        # Params: date (optional), workflow_id (optional)
        return [smart_executions_query_tool], params

    elif category == "ERROR_ANALYSIS":
        # Requires: workflow_name
        # If no workflow_name → use get_all_errors_summary_tool instead
        if "workflow_name" not in params and "workflow_id" in params:
            params["workflow_name"] = params.pop("workflow_id")

        if "workflow_name" in params:
            return [get_error_details_tool], params
        else:
            logger.info("[TOOL MAPPER] ERROR_ANALYSIS without workflow_name → using get_all_errors_summary_tool")
            return [get_all_errors_summary_tool], {}

    elif category == "ANALYTICS":
        # Params: metric, period, workflow (all optional)
        return [smart_analytics_query_tool], params

    elif category == "STEP_DETAIL":
        # Requires: workflow_name + node_name
        if "workflow_id" in params and "workflow_name" not in params:
            params["workflow_name"] = params.pop("workflow_id")

        # Fallback: If node_name missing → user wants ALL steps (use PROCESS_DETAIL)
        if "node_name" not in params:
            logger.info("[TOOL MAPPER] STEP_DETAIL without node_name → using smart_workflow_query_tool for all steps")
            # Convert workflow_name → workflow_id for smart_workflow_query_tool
            if "workflow_name" in params:
                params["workflow_id"] = params.pop("workflow_name")
            return [smart_workflow_query_tool], params

        return [get_node_execution_details_tool], params

    elif category == "EMAIL_ACTIVITY":
        # Params: metric, workflow (optional)
        return [get_chatone_email_details_tool], params

    elif category == "PROCESS_ACTION":
        # Requires: workflow_id
        # For toggle_workflow_tool: also needs active (default: true)
        tools = [execute_workflow_tool, toggle_workflow_tool]

        # Add default active=true for toggle if missing
        if "active" not in params:
            params["active"] = True

        return tools, params

    elif category == "SYSTEM_OVERVIEW":
        return [get_full_database_dump], {}

    else:
        logger.warning(f"[TOOL MAPPER] Unknown category: {category}, returning empty list")
        return [], {}
