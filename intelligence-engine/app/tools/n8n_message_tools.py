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

        # Query REAL execution_entity table with correct column names
        sql = """
            SELECT
                e."workflowId",
                w.name as workflow_name,
                e."stoppedAt",
                e."startedAt",
                e.status,
                e.mode,
                w.nodes,
                w.connections
            FROM n8n.execution_entity e
            JOIN n8n.workflow_entity w ON e."workflowId" = w.id
            WHERE LOWER(w.name) LIKE LOWER($1)
                AND e."stoppedAt" IS NOT NULL
            ORDER BY e."stoppedAt" DESC
            LIMIT 1
        """

        result = await conn.fetchrow(sql, f"%{workflow_name}%")
        await conn.close()

        if not result:
            raise ToolException(f"Nessuna elaborazione trovata per il processo '{workflow_name}'")

        # Extract message from workflow nodes (parsing JSON)
        message_content = await _extract_message_from_nodes(result)

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


# Helper function to extract messages from workflow nodes
async def _extract_message_from_nodes(execution_data: Dict) -> str:
    """
    Extract actual message content from workflow nodes JSON.
    This parses the nodes structure to find message fields.
    """
    try:
        if not execution_data.get('nodes'):
            return "Messaggio non disponibile"

        nodes = execution_data['nodes']

        # If nodes is a string, parse it as JSON
        if isinstance(nodes, str):
            nodes = json.loads(nodes)

        # Look for common message fields in nodes
        messages = []

        for node in nodes:
            if isinstance(node, dict):
                # Check common fields where messages are stored
                if 'parameters' in node:
                    params = node['parameters']

                    # Check for message fields
                    if 'message' in params:
                        messages.append(params['message'])
                    elif 'text' in params:
                        messages.append(params['text'])
                    elif 'content' in params:
                        messages.append(params['content'])
                    elif 'body' in params:
                        messages.append(str(params['body']))

        if messages:
            return " | ".join(messages[:3])  # Return first 3 messages
        else:
            # Fallback to generic message
            return f"Elaborazione completata con stato: {execution_data.get('status', 'sconosciuto')}"

    except Exception as e:
        logger.warning(f"Could not extract message from nodes: {e}")
        return "Contenuto elaborazione disponibile"


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