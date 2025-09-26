"""
LangGraph Agent Tools for PilotProOS Database
Real tools for querying PostgreSQL database with safety and validation
"""

from typing import Optional, Dict, Any, List
from langchain_core.tools import tool
from pydantic import BaseModel, Field, validator
import asyncpg
import json
from datetime import datetime, timedelta
from loguru import logger
from .config import settings

# ============================================================================
# PYDANTIC MODELS FOR TOOL INPUTS
# ============================================================================

class UserQueryInput(BaseModel):
    """Input for user queries with validation"""
    query_type: str = Field(
        description="Type of query: all, active, by_email, by_id, recent, count"
    )
    parameter: Optional[str] = Field(
        default=None,
        description="Parameter for query (email, id, etc.)"
    )
    limit: int = Field(
        default=10,
        description="Number of results to return",
        ge=1,
        le=100
    )

    @validator('query_type')
    def validate_query_type(cls, v):
        allowed = ['all', 'active', 'by_email', 'by_id', 'recent', 'count', 'by_role']
        if v not in allowed:
            raise ValueError(f"query_type must be one of {allowed}")
        return v

class SessionQueryInput(BaseModel):
    """Input for session queries"""
    query_type: str = Field(
        description="Type: active, expired, by_user, count"
    )
    user_id: Optional[str] = Field(default=None)

class BusinessQueryInput(BaseModel):
    """Input for business analytics queries"""
    metric_type: str = Field(
        description="Metric type: executions, performance, errors, costs"
    )
    time_range: str = Field(
        default="7d",
        description="Time range: 1d, 7d, 30d, 90d"
    )

class SystemStatusInput(BaseModel):
    """Input for system status queries"""
    component: str = Field(
        description="Component: database, services, health, settings"
    )

# ============================================================================
# DATABASE CONNECTION HELPER
# ============================================================================

async def execute_safe_query(query: str, params: List[Any] = None) -> Dict[str, Any]:
    """
    Execute a safe SELECT query on PostgreSQL

    Args:
        query: SQL query (must be SELECT)
        params: Query parameters for prepared statement

    Returns:
        Dict with success status and data
    """
    try:
        # Validate query is SELECT only
        query_lower = query.lower().strip()
        if not query_lower.startswith('select'):
            return {
                "success": False,
                "error": "Only SELECT queries are allowed",
                "data": []
            }

        # Block dangerous keywords
        dangerous = ['insert', 'update', 'delete', 'drop', 'create', 'alter', 'truncate', 'exec', 'execute']
        if any(keyword in query_lower for keyword in dangerous):
            return {
                "success": False,
                "error": "Dangerous SQL keywords detected",
                "data": []
            }

        # Execute query with timeout
        conn = await asyncpg.connect(
            settings.DATABASE_URL,
            timeout=10,
            command_timeout=5
        )

        try:
            # Use prepared statement for safety
            if params:
                rows = await conn.fetch(query, *params)
            else:
                rows = await conn.fetch(query)

            # Convert to dict format
            data = []
            for row in rows:
                row_dict = {}
                for key, value in row.items():
                    # Handle special types
                    if isinstance(value, datetime):
                        row_dict[key] = value.isoformat()
                    elif isinstance(value, (dict, list)):
                        row_dict[key] = value
                    else:
                        row_dict[key] = str(value) if value is not None else None
                data.append(row_dict)

            logger.info(f"Query executed successfully: {len(data)} rows returned")

            return {
                "success": True,
                "data": data,
                "count": len(data)
            }

        finally:
            await conn.close()

    except asyncpg.exceptions.QueryCanceledError:
        logger.error("Query timeout")
        return {
            "success": False,
            "error": "Query timeout - query took too long",
            "data": []
        }
    except Exception as e:
        logger.error(f"Database query error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }

# ============================================================================
# TOOL 1: QUERY USERS
# ============================================================================

@tool(args_schema=UserQueryInput)
async def query_users_tool(
    query_type: str,
    parameter: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Query users from PilotProOS database.

    Use this tool to get information about users in the system.
    Supports different query types: all, active, by_email, by_id, recent, count, by_role.

    Args:
        query_type: Type of query to execute
        parameter: Optional parameter for the query
        limit: Maximum number of results

    Returns:
        JSON string with user data or error message
    """

    queries = {
        'all': "SELECT id, email, full_name, role, is_active, created_at FROM pilotpros.users ORDER BY created_at DESC LIMIT $1",
        'active': "SELECT id, email, full_name, role, last_login FROM pilotpros.users WHERE is_active = true ORDER BY last_login DESC NULLS LAST LIMIT $1",
        'by_email': "SELECT * FROM pilotpros.users WHERE email ILIKE $1 LIMIT 1",
        'by_id': "SELECT * FROM pilotpros.users WHERE id = $1::uuid",
        'recent': "SELECT id, email, full_name, created_at FROM pilotpros.users ORDER BY created_at DESC LIMIT $1",
        'count': "SELECT COUNT(*) as total_users, COUNT(CASE WHEN is_active THEN 1 END) as active_users FROM pilotpros.users",
        'by_role': "SELECT id, email, full_name, role FROM pilotpros.users WHERE role = $1 ORDER BY full_name LIMIT $2"
    }

    query = queries.get(query_type)
    if not query:
        return json.dumps({"error": f"Unknown query type: {query_type}"})

    # Prepare parameters
    params = []
    if query_type == 'by_email':
        if not parameter:
            return json.dumps({"error": "Email parameter required"})
        params = [f'%{parameter}%']
    elif query_type == 'by_id':
        if not parameter:
            return json.dumps({"error": "ID parameter required"})
        params = [parameter]
    elif query_type == 'by_role':
        if not parameter:
            return json.dumps({"error": "Role parameter required"})
        params = [parameter, limit]
    elif query_type != 'count':
        params = [limit]

    result = await execute_safe_query(query, params)

    if result['success']:
        return json.dumps({
            "query_type": query_type,
            "data": result['data'],
            "count": result['count']
        }, indent=2)
    else:
        return json.dumps({"error": result['error']})

# ============================================================================
# TOOL 2: QUERY SESSIONS
# ============================================================================

@tool(args_schema=SessionQueryInput)
async def query_sessions_tool(
    query_type: str,
    user_id: Optional[str] = None
) -> str:
    """
    Query active sessions from PilotProOS database.

    Use this tool to get information about user sessions.
    Query types: active, expired, by_user, count.

    Args:
        query_type: Type of session query
        user_id: Optional user ID for filtering

    Returns:
        JSON string with session data
    """

    queries = {
        'active': """
            SELECT user_id, created_at, last_activity, ip_address
            FROM pilotpros.active_sessions
            WHERE last_activity > NOW() - INTERVAL '30 minutes'
            ORDER BY created_at DESC
            LIMIT 20
        """,
        'expired': """
            SELECT user_id, created_at, last_activity
            FROM pilotpros.active_sessions
            WHERE last_activity <= NOW() - INTERVAL '30 minutes'
            ORDER BY last_activity DESC
            LIMIT 20
        """,
        'by_user': """
            SELECT s.*, u.email, u.full_name
            FROM pilotpros.active_sessions s
            JOIN pilotpros.users u ON s.user_id = u.id
            WHERE s.user_id = $1::uuid
            ORDER BY s.created_at DESC
        """,
        'count': """
            SELECT
                COUNT(*) as total_sessions,
                COUNT(CASE WHEN last_activity > NOW() - INTERVAL '30 minutes' THEN 1 END) as active_sessions,
                COUNT(DISTINCT user_id) as unique_users
            FROM pilotpros.active_sessions
        """
    }

    query = queries.get(query_type)
    if not query:
        return json.dumps({"error": f"Unknown query type: {query_type}"})

    params = []
    if query_type == 'by_user':
        if not user_id:
            return json.dumps({"error": "user_id parameter required"})
        params = [user_id]

    result = await execute_safe_query(query, params)

    if result['success']:
        return json.dumps({
            "query_type": query_type,
            "data": result['data'],
            "count": result['count']
        }, indent=2)
    else:
        return json.dumps({"error": result['error']})

# ============================================================================
# TOOL 3: QUERY BUSINESS DATA
# ============================================================================

@tool(args_schema=BusinessQueryInput)
async def query_business_data_tool(
    metric_type: str,
    time_range: str = "7d"
) -> str:
    """
    Query business analytics and metrics from PilotProOS.

    Use this tool to get business intelligence data.
    Metrics: executions, performance, errors, costs.
    Time ranges: 1d, 7d, 30d, 90d.

    Args:
        metric_type: Type of business metric
        time_range: Time range for the query

    Returns:
        JSON string with business data
    """

    # Parse time range
    time_map = {
        '1d': "interval '1 day'",
        '7d': "interval '7 days'",
        '30d': "interval '30 days'",
        '90d': "interval '90 days'"
    }

    interval = time_map.get(time_range, "interval '7 days'")

    queries = {
        'executions': f"""
            SELECT
                COUNT(*) as total_executions,
                AVG(CAST(data->>'duration' AS FLOAT)) as avg_duration_ms,
                MAX(CAST(data->>'duration' AS FLOAT)) as max_duration_ms,
                MIN(CAST(data->>'duration' AS FLOAT)) as min_duration_ms
            FROM pilotpros.business_execution_data
            WHERE created_at > NOW() - {interval}
        """,
        'performance': f"""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as executions,
                AVG(CAST(data->>'duration' AS FLOAT)) as avg_duration
            FROM pilotpros.business_execution_data
            WHERE created_at > NOW() - {interval}
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """,
        'errors': f"""
            SELECT
                COUNT(*) as total_errors,
                data->>'error_type' as error_type,
                COUNT(*) as error_count
            FROM pilotpros.business_execution_data
            WHERE created_at > NOW() - {interval}
                AND data->>'status' = 'error'
            GROUP BY data->>'error_type'
            ORDER BY error_count DESC
        """,
        'costs': f"""
            SELECT
                SUM(CAST(data->>'cost' AS FLOAT)) as total_cost,
                AVG(CAST(data->>'cost' AS FLOAT)) as avg_cost,
                COUNT(*) as transaction_count
            FROM pilotpros.business_analytics
            WHERE created_at > NOW() - {interval}
                AND data->>'cost' IS NOT NULL
        """
    }

    query = queries.get(metric_type)
    if not query:
        return json.dumps({"error": f"Unknown metric type: {metric_type}"})

    result = await execute_safe_query(query)

    if result['success']:
        return json.dumps({
            "metric_type": metric_type,
            "time_range": time_range,
            "data": result['data'],
            "count": result['count']
        }, indent=2)
    else:
        return json.dumps({"error": result['error']})

# ============================================================================
# TOOL 4: SYSTEM STATUS
# ============================================================================

@tool(args_schema=SystemStatusInput)
async def query_system_status_tool(component: str) -> str:
    """
    Query system status and configuration from PilotProOS.

    Use this tool to check system health and settings.
    Components: database, services, health, settings.

    Args:
        component: System component to check

    Returns:
        JSON string with system status
    """

    queries = {
        'database': """
            SELECT
                current_database() as database,
                pg_database_size(current_database()) as size_bytes,
                (SELECT count(*) FROM pilotpros.users) as total_users,
                (SELECT count(*) FROM pilotpros.active_sessions WHERE last_activity > NOW() - INTERVAL '30 minutes') as active_sessions,
                NOW() as current_time
        """,
        'services': """
            SELECT
                setting_key,
                setting_value,
                updated_at
            FROM pilotpros.system_settings
            WHERE setting_key LIKE 'service_%'
            ORDER BY setting_key
        """,
        'health': """
            SELECT
                'database' as component,
                'healthy' as status,
                NOW() as checked_at
            UNION ALL
            SELECT
                'sessions' as component,
                CASE
                    WHEN COUNT(*) > 0 THEN 'active'
                    ELSE 'no_active_sessions'
                END as status,
                NOW() as checked_at
            FROM pilotpros.active_sessions
            WHERE last_activity > NOW() - INTERVAL '30 minutes'
        """,
        'settings': """
            SELECT
                setting_key,
                setting_value,
                description,
                updated_at
            FROM pilotpros.system_settings
            ORDER BY setting_key
            LIMIT 50
        """
    }

    query = queries.get(component)
    if not query:
        return json.dumps({"error": f"Unknown component: {component}"})

    result = await execute_safe_query(query)

    if result['success']:
        return json.dumps({
            "component": component,
            "status": "operational",
            "data": result['data'],
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    else:
        return json.dumps({"error": result['error']})

# ============================================================================
# TOOL 5: GENERIC SQL QUERY (WITH EXTRA SAFETY)
# ============================================================================

class SQLQueryInput(BaseModel):
    """Input for generic SQL queries"""
    query: str = Field(
        description="SQL SELECT query to execute"
    )
    explanation: str = Field(
        description="Explanation of what this query does"
    )

@tool(args_schema=SQLQueryInput)
async def execute_sql_query_tool(query: str, explanation: str) -> str:
    """
    Execute a custom SQL query on PilotProOS database.

    SAFETY: Only SELECT queries allowed. Query is validated and sanitized.
    Use this for complex queries not covered by other tools.

    Args:
        query: SQL SELECT query to execute
        explanation: What this query does

    Returns:
        JSON string with query results
    """

    logger.info(f"Executing custom SQL: {explanation}")

    # Extra validation
    if not query.lower().strip().startswith('select'):
        return json.dumps({
            "error": "Only SELECT queries are allowed",
            "explanation": explanation
        })

    # Limit results for safety
    if 'limit' not in query.lower():
        query = f"{query.strip()} LIMIT 100"

    result = await execute_safe_query(query)

    if result['success']:
        return json.dumps({
            "explanation": explanation,
            "query": query,
            "data": result['data'],
            "count": result['count']
        }, indent=2)
    else:
        return json.dumps({
            "error": result['error'],
            "explanation": explanation,
            "query": query
        })

# ============================================================================
# TOOL 6: DATABASE SCHEMA INFO
# ============================================================================

@tool
async def get_database_schema_tool() -> str:
    """
    Get the database schema information for PilotProOS.

    Use this tool to understand the structure of tables before making queries.

    Returns:
        JSON string with table schemas
    """

    # Hardcoded schema info to avoid queries
    schema_info = {
        "users": {
            "columns": ["id (uuid)", "email", "password_hash", "full_name", "role", "is_active", "last_login", "preferences", "created_at", "updated_at", "auth_method", "mfa_enabled"],
            "description": "User accounts table"
        },
        "active_sessions": {
            "columns": ["id", "user_id (uuid)", "token_id (uuid)", "ip_address", "created_at", "last_activity"],
            "description": "Active user sessions - NO expires_at column, use last_activity instead"
        },
        "business_execution_data": {
            "columns": ["id", "workflow_id", "execution_id", "data (jsonb)", "created_at"],
            "description": "Business process execution data"
        },
        "business_analytics": {
            "columns": ["id", "metric_name", "metric_value", "data (jsonb)", "created_at"],
            "description": "Business analytics metrics"
        },
        "system_settings": {
            "columns": ["setting_key", "setting_value", "description", "updated_at"],
            "description": "System configuration settings"
        },
        "failed_login_attempts": {
            "columns": ["id", "email", "attempt_time", "ip_address"],
            "description": "Failed login attempts log"
        }
    }

    return json.dumps({
        "database": "pilotpros_db",
        "schema": "pilotpros",
        "tables": schema_info,
        "notes": [
            "Use last_activity for session expiry (30 minutes threshold)",
            "All user IDs are UUID type",
            "JSONB columns can store complex data structures",
            "Timestamps are in UTC"
        ]
    }, indent=2)

# ============================================================================
# EXPORT ALL TOOLS
# ============================================================================

def get_all_agent_tools():
    """
    Get all tools for the LangGraph agent.

    Returns:
        List of tool functions
    """
    return [
        get_database_schema_tool,  # First tool - helps agent understand database
        query_users_tool,
        query_sessions_tool,
        query_business_data_tool,
        query_system_status_tool,
        execute_sql_query_tool
    ]

# Helper function for tool descriptions
def get_tools_description() -> str:
    """Get a formatted description of all available tools"""
    tools = get_all_agent_tools()
    descriptions = []
    for tool in tools:
        descriptions.append(f"- {tool.name}: {tool.description}")
    return "\n".join(descriptions)