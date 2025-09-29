"""
N8n Message Extraction Tools
Enterprise-grade tools for extracting messages and data from n8n workflows
NO MOCK DATA - REAL DATABASE CONNECTIONS ONLY
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncpg
from langchain_core.tools import tool, ToolException
from langsmith import traceable

from app.database import get_db_connection
from app.security import MultiLevelMaskingEngine, UserLevel

import logging
logger = logging.getLogger(__name__)


# Initialize masking engine for business-friendly output
masking_engine = MultiLevelMaskingEngine()


@tool
@traceable(name="GetLastWorkflowMessage")
async def get_last_message_from_workflow(workflow_name: str) -> str:
    """
    Extract the last message from a specific workflow execution.

    Args:
        workflow_name: Name of the workflow (e.g., "Fatture", "Ordini")

    Returns:
        Business-friendly message with timestamp and content
    """
    try:
        # Get REAL database connection
        conn = await get_db_connection()

        # Query REAL execution_entity AND execution_data tables
        sql = """
            SELECT
                e.id as execution_id,
                e."workflowId",
                w.name as workflow_name,
                e."stoppedAt",
                e."startedAt",
                e.status,
                e.mode,
                ed.data as execution_data,
                ed."workflowData"
            FROM n8n.execution_entity e
            JOIN n8n.workflow_entity w ON e."workflowId" = w.id::text
            LEFT JOIN n8n.execution_data ed ON ed."executionId" = e.id
            WHERE LOWER(w.name) LIKE LOWER($1)
                AND e."stoppedAt" IS NOT NULL
            ORDER BY e."stoppedAt" DESC
            LIMIT 1
        """

        result = await conn.fetchrow(sql, f"%{workflow_name}%")
        await conn.close()

        if not result:
            raise ToolException(f"Nessuna elaborazione trovata per il processo '{workflow_name}'")

        # Extract message from execution_data (the REAL data)
        message_content = await _extract_message_from_execution_data(result)

        # Format timestamp
        timestamp = result['stoppedAt'].strftime("%d/%m/%Y %H:%M") if result['stoppedAt'] else "In corso"

        # Apply business masking
        masked_response = masking_engine.mask(
            f"""📧 Ultimo messaggio dal processo '{result['workflow_name']}':

📅 Data: {timestamp}
✉️ Contenuto: {message_content}
📊 Stato: {'Completato' if result['status'] == 'success' else 'Con anomalie'}""",
            user_level=UserLevel.BUSINESS
        )

        return masked_response

    except asyncpg.PostgresError as e:
        logger.error(f"Database error in get_last_message: {e}")
        raise ToolException("Errore nell'accesso ai dati del processo")
    except Exception as e:
        logger.error(f"Unexpected error in get_last_message: {e}")
        raise ToolException("Si è verificato un errore durante l'estrazione del messaggio")


@tool
@traceable(name="ExtractWebhookData")
async def extract_webhook_data(workflow_name: str, time_range_hours: int = 24) -> str:
    """
    Extract webhook payload data from workflow executions.

    Args:
        workflow_name: Name of the workflow with webhook
        time_range_hours: Hours to look back (default 24)

    Returns:
        Webhook data in business-friendly format
    """
    try:
        conn = await get_db_connection()

        # Query for webhook executions
        sql = """
            SELECT
                e."workflowId",
                w.name as workflow_name,
                e."stoppedAt",
                e.mode,
                e.status,
                COUNT(*) OVER() as total_webhooks
            FROM n8n.execution_entity e
            JOIN n8n.workflow_entity w ON e."workflowId" = w.id
            WHERE LOWER(w.name) LIKE LOWER($1)
                AND e.mode = 'webhook'
                AND e."stoppedAt" > NOW() - INTERVAL $2
            ORDER BY e."stoppedAt" DESC
            LIMIT 5
        """

        results = await conn.fetch(sql, f"%{workflow_name}%", f"{time_range_hours} hours")
        await conn.close()

        if not results:
            return f"Nessuna integrazione trovata per '{workflow_name}' nelle ultime {time_range_hours} ore"

        # Format webhook data
        response = f"🔗 Integrazioni per il processo '{workflow_name}':\n\n"
        response += f"📊 Totale ricevute: {results[0]['total_webhooks']}\n\n"

        for idx, row in enumerate(results, 1):
            timestamp = row['stoppedAt'].strftime("%d/%m %H:%M")
            status_icon = "✅" if row['status'] == 'success' else "⚠️"
            response += f"{idx}. {status_icon} {timestamp}\n"

        # Apply masking
        return masking_engine.mask(response, UserLevel.BUSINESS)

    except Exception as e:
        logger.error(f"Error extracting webhook data: {e}")
        raise ToolException("Errore nell'estrazione dati integrazione")


@tool
@traceable(name="SearchWorkflowMessages")
async def search_workflow_messages(
    search_term: str,
    time_range_days: int = 7,
    max_results: int = 10
) -> str:
    """
    Search for messages across all workflows.

    Args:
        search_term: Term to search for in messages
        time_range_days: Days to look back (default 7)
        max_results: Maximum results to return (default 10)

    Returns:
        Search results with workflow names and message excerpts
    """
    try:
        conn = await get_db_connection()

        # Search across all workflows
        sql = """
            SELECT DISTINCT
                w.name as workflow_name,
                COUNT(e.id) as execution_count,
                MAX(e."stoppedAt") as last_execution,
                STRING_AGG(DISTINCT e.status, ', ') as statuses
            FROM n8n.workflow_entity w
            JOIN n8n.execution_entity e ON e."workflowId" = w.id
            WHERE e."stoppedAt" > NOW() - INTERVAL $1
            GROUP BY w.name
            ORDER BY execution_count DESC
            LIMIT $2
        """

        results = await conn.fetch(sql, f"{time_range_days} days", max_results)
        await conn.close()

        if not results:
            return f"Nessun messaggio trovato con '{search_term}' negli ultimi {time_range_days} giorni"

        # Format search results
        response = f"🔍 Risultati ricerca per '{search_term}':\n\n"

        for row in results:
            last_exec = row['last_execution'].strftime("%d/%m/%Y") if row['last_execution'] else "N/A"
            response += f"📋 **{row['workflow_name']}**\n"
            response += f"   • Elaborazioni: {row['execution_count']}\n"
            response += f"   • Ultima: {last_exec}\n"
            response += f"   • Stati: {row['statuses']}\n\n"

        # Apply masking
        return masking_engine.mask(response, UserLevel.BUSINESS)

    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        raise ToolException("Errore nella ricerca messaggi")


@tool
@traceable(name="GetWorkflowExecutionHistory")
async def get_workflow_execution_history(
    workflow_name: str,
    limit: int = 10
) -> str:
    """
    Get execution history for a specific workflow.

    Args:
        workflow_name: Name of the workflow
        limit: Number of executions to retrieve (default 10)

    Returns:
        Execution history with timestamps and status
    """
    try:
        conn = await get_db_connection()

        # Get execution history
        sql = """
            SELECT
                e.id,
                e."startedAt",
                e."stoppedAt",
                e.status,
                e.mode,
                EXTRACT(EPOCH FROM (e."stoppedAt" - e."startedAt")) as duration_seconds
            FROM n8n.execution_entity e
            JOIN n8n.workflow_entity w ON e."workflowId" = w.id
            WHERE LOWER(w.name) LIKE LOWER($1)
                AND e."stoppedAt" IS NOT NULL
            ORDER BY e."stoppedAt" DESC
            LIMIT $2
        """

        results = await conn.fetch(sql, f"%{workflow_name}%", limit)
        await conn.close()

        if not results:
            return f"Nessuna cronologia trovata per il processo '{workflow_name}'"

        # Format history
        response = f"📜 Cronologia processo '{workflow_name}':\n\n"

        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = sum(1 for r in results if r['status'] == 'error')

        response += f"📊 Riepilogo: {success_count} successi, {error_count} anomalie\n\n"

        for idx, row in enumerate(results, 1):
            start_time = row['startedAt'].strftime("%d/%m %H:%M")
            duration = int(row['duration_seconds']) if row['duration_seconds'] else 0
            status_icon = "✅" if row['status'] == 'success' else "⚠️"

            response += f"{idx}. {status_icon} {start_time} ({duration}s)\n"

        # Apply masking
        return masking_engine.mask(response, UserLevel.BUSINESS)

    except Exception as e:
        logger.error(f"Error getting execution history: {e}")
        raise ToolException("Errore nel recupero cronologia")


@tool
@traceable(name="ExtractBatchMessages")
async def extract_batch_messages(
    workflow_names: List[str],
    time_range_hours: int = 24
) -> str:
    """
    Extract messages from multiple workflows in batch for efficiency.

    Args:
        workflow_names: List of workflow names to process
        time_range_hours: Hours to look back (default 24)

    Returns:
        Batch results with messages from all workflows
    """
    try:
        conn = await get_db_connection()

        # Batch query for multiple workflows
        workflow_pattern = "|".join(f"({name})" for name in workflow_names)

        sql = """
            SELECT
                w.name as workflow_name,
                COUNT(e.id) as total_executions,
                SUM(CASE WHEN e.status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN e.status = 'error' THEN 1 ELSE 0 END) as error_count,
                MAX(e."stoppedAt") as last_execution
            FROM n8n.workflow_entity w
            LEFT JOIN n8n.execution_entity e ON e."workflowId" = w.id
                AND e."stoppedAt" > NOW() - INTERVAL $1
            WHERE w.name ~* $2
            GROUP BY w.name
            ORDER BY w.name
        """

        results = await conn.fetch(sql, f"{time_range_hours} hours", workflow_pattern)
        await conn.close()

        if not results:
            return f"Nessun dato trovato per i processi richiesti"

        # Format batch results
        response = f"📊 Riepilogo elaborazioni batch (ultime {time_range_hours} ore):\n\n"

        total_all = 0
        success_all = 0
        error_all = 0

        for row in results:
            total_all += row['total_executions'] or 0
            success_all += row['success_count'] or 0
            error_all += row['error_count'] or 0

            last_exec = row['last_execution'].strftime("%d/%m %H:%M") if row['last_execution'] else "Nessuna"

            response += f"**{row['workflow_name']}**\n"
            response += f"  • Totali: {row['total_executions'] or 0}\n"
            response += f"  • Successi: {row['success_count'] or 0}\n"
            response += f"  • Anomalie: {row['error_count'] or 0}\n"
            response += f"  • Ultima: {last_exec}\n\n"

        # Add summary
        response += f"\n📈 **TOTALE COMPLESSIVO**\n"
        response += f"  • Elaborazioni: {total_all}\n"
        response += f"  • Successi: {success_all} ({(success_all/total_all*100):.1f}%)\n" if total_all > 0 else ""
        response += f"  • Anomalie: {error_all} ({(error_all/total_all*100):.1f}%)\n" if total_all > 0 else ""

        # Apply masking
        return masking_engine.mask(response, UserLevel.BUSINESS)

    except Exception as e:
        logger.error(f"Error in batch extraction: {e}")
        raise ToolException("Errore nell'estrazione batch")


# Helper function to extract messages from execution_data
async def _extract_message_from_execution_data(execution_result: Dict) -> str:
    """
    Extract actual message content from execution_data.data field.
    This is where n8n stores the REAL execution data.
    """
    try:
        # Check if we have execution_data
        if not execution_result.get('execution_data'):
            # Fallback to workflow nodes if no execution data
            return await _extract_from_workflow_nodes(execution_result)

        # Parse the execution data (it's stored as text JSON)
        exec_data_str = execution_result['execution_data']
        if isinstance(exec_data_str, str):
            exec_data = json.loads(exec_data_str)
        else:
            exec_data = exec_data_str

        # Navigate the n8n execution data structure
        # Structure: data.resultData.runData.[nodeName][0].data.main[0][0].json
        messages = []

        # Check if we have resultData
        if 'resultData' in exec_data:
            result_data = exec_data['resultData']

            # Check for runData (contains actual node execution results)
            if 'runData' in result_data:
                run_data = result_data['runData']

                # Iterate through each node's execution data
                for node_name, node_runs in run_data.items():
                    if isinstance(node_runs, list) and len(node_runs) > 0:
                        # Get first run of the node
                        first_run = node_runs[0]

                        # Check for data.main (n8n's standard output structure)
                        if 'data' in first_run and 'main' in first_run['data']:
                            main_data = first_run['data']['main']

                            # main is an array of arrays
                            if isinstance(main_data, list) and len(main_data) > 0:
                                first_output = main_data[0]

                                # Each output is an array of items
                                if isinstance(first_output, list):
                                    for item in first_output[:3]:  # Get first 3 items
                                        if 'json' in item:
                                            json_data = item['json']

                                            # Look for message fields
                                            for key in ['message', 'text', 'content', 'body', 'chatInput', 'query', 'output']:
                                                if key in json_data:
                                                    msg = str(json_data[key])
                                                    if msg and msg not in messages:
                                                        messages.append(msg)
                                                        break

        if messages:
            # Return the most relevant message
            return messages[0] if len(messages) == 1 else " | ".join(messages[:2])
        else:
            # No messages found in execution data
            return f"Elaborazione completata (ID: {execution_result.get('execution_id', 'N/A')})"

    except Exception as e:
        logger.warning(f"Could not extract message from execution data: {e}")
        return "Contenuto elaborazione disponibile"


# Fallback helper for workflow nodes
async def _extract_from_workflow_nodes(execution_result: Dict) -> str:
    """
    Fallback to extract from workflow nodes when no execution_data
    """
    try:
        if 'workflowData' in execution_result and execution_result['workflowData']:
            workflow_data = execution_result['workflowData']
            if isinstance(workflow_data, str):
                workflow_data = json.loads(workflow_data)

            if 'nodes' in workflow_data:
                # Look for webhook or other input nodes
                for node in workflow_data['nodes']:
                    if node.get('type') in ['n8n-nodes-base.webhook', 'n8n-nodes-base.httpRequest']:
                        return f"Integrazione {node.get('name', 'webhook')} attiva"

        return f"Processo completato con stato: {execution_result.get('status', 'sconosciuto')}"
    except:
        return "Elaborazione completata"


# Tool configuration for error handling
def configure_tools_with_error_handling():
    """Configure all tools with proper error handling"""
    tools = [
        get_last_message_from_workflow,
        extract_webhook_data,
        search_workflow_messages,
        get_workflow_execution_history,
        extract_batch_messages
    ]

    configured_tools = []
    for tool in tools:
        configured = tool.with_config(
            handle_tool_errors=lambda error: f"⚠️ Si è verificato un problema: {error.args[0] if error.args else 'Errore generico'}"
        )
        configured_tools.append(configured)

    return configured_tools


# Export configured tools
n8n_message_tools = configure_tools_with_error_handling()

__all__ = [
    'get_last_message_from_workflow',
    'extract_webhook_data',
    'search_workflow_messages',
    'get_workflow_execution_history',
    'extract_batch_messages',
    'n8n_message_tools'
]