"""
LangGraph Studio - Graph definition for PilotProOS Intelligence Engine
PRODUCTION-READY with REAL DATABASE TOOLS
Following LangGraph best practices and official documentation
"""

from typing import TypedDict, List, Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
import os
from datetime import datetime

# Import configuration
try:
    from config import settings
    DATABASE_URL = settings.DATABASE_URL
except ImportError:
    # Fallback for local development
    DATABASE_URL = "postgresql://pilotpros_user:pilotpros_secure_pass_2025@localhost:5432/pilotpros_db"

# ============================================================================
# STATE DEFINITION - Following LangGraph best practices
# ============================================================================

# We don't need custom state - LangGraph will handle it

# ============================================================================
# REAL DATABASE TOOLS - NO FAKE DATA!
# ============================================================================

@tool
def get_database_info() -> str:
    """
    Get database schema information for PilotProOS.
    Returns the structure of all tables in the database.

    This is REAL information about the actual database structure!
    """
    return """Database: pilotpros_db

Tables in pilotpros schema:
- users: User accounts (id, email, full_name, role, is_active, created_at)
- active_sessions: Active user sessions (user_id, last_activity, ip_address)
- business_execution_data: Process execution data (workflow_id, execution_id, data)
- system_settings: Configuration settings (setting_key, setting_value)

Use these table names in your queries to get real data."""

@tool
def query_users(query_type: str = "all") -> str:
    """
    Query users from the PostgreSQL database.

    Args:
        query_type: Type of query - "all", "active", or "count"

    Returns:
        Real user data from the database (NOT fake data!)
    """
    import psycopg2
    import json

    try:
        # Connect to the real database
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="pilotpros_db",
            user="pilotpros_user",
            password="pilotpros_secure_pass_2025"
        )
        cur = conn.cursor()

        if query_type == "count":
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN is_active THEN 1 END) as active
                FROM pilotpros.users
            """)
            result = cur.fetchone()
            response = f"Total users: {result[0]}, Active users: {result[1]}"

        elif query_type == "active":
            cur.execute("""
                SELECT email, full_name, role
                FROM pilotpros.users
                WHERE is_active = true
                ORDER BY created_at DESC
                LIMIT 5
            """)
            results = cur.fetchall()
            users = [f"{r[1] or 'No name'} ({r[0]}) - {r[2]}" for r in results]
            response = "Active users:\n" + "\n".join(users) if users else "No active users found"

        else:  # all
            cur.execute("""
                SELECT email, full_name, role, is_active
                FROM pilotpros.users
                ORDER BY created_at DESC
                LIMIT 5
            """)
            results = cur.fetchall()
            users = [f"{r[1] or 'No name'} ({r[0]}) - {r[2]} - Active: {r[3]}" for r in results]
            response = "Users in database:\n" + "\n".join(users) if users else "No users found"

        conn.close()
        return response

    except Exception as e:
        return f"Database connection error: {str(e)}. Make sure Docker containers are running."

@tool
def query_sessions() -> str:
    """
    Query active sessions from the PostgreSQL database.
    Returns real session data, not fake data!
    """
    import psycopg2

    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="pilotpros_db",
            user="pilotpros_user",
            password="pilotpros_secure_pass_2025"
        )
        cur = conn.cursor()

        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN last_activity > NOW() - INTERVAL '30 minutes' THEN 1 END) as active
            FROM pilotpros.active_sessions
        """)
        result = cur.fetchone()

        conn.close()
        return f"Total sessions: {result[0]}, Active (last 30 min): {result[1]}"

    except Exception as e:
        return f"Database error: {str(e)}"

@tool
def get_system_status() -> str:
    """
    Get system status and database health information.
    Returns real system metrics from PostgreSQL!
    """
    import psycopg2

    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="pilotpros_db",
            user="pilotpros_user",
            password="pilotpros_secure_pass_2025"
        )
        cur = conn.cursor()

        cur.execute("""
            SELECT
                current_database() as db,
                pg_database_size(current_database()) as size,
                current_user as user,
                version() as version
        """)
        result = cur.fetchone()

        size_mb = result[1] / (1024 * 1024) if result[1] else 0

        conn.close()

        return f"""System Status:
- Database: {result[0]}
- Size: {size_mb:.2f} MB
- User: {result[2]}
- PostgreSQL Version: {result[3][:30]}...
- Status: OPERATIONAL"""

    except Exception as e:
        return f"System check error: {str(e)}"

@tool
def execute_business_query(query: str) -> str:
    """
    Execute a safe SELECT query on the business data.
    Only SELECT queries are allowed for safety.

    Args:
        query: SQL SELECT query to execute

    Returns:
        Query results from the real PostgreSQL database
    """
    import psycopg2
    import json

    # Safety checks
    query_lower = query.lower().strip()
    if not query_lower.startswith('select'):
        return "ERROR: Only SELECT queries are allowed for safety"

    dangerous = ['drop', 'delete', 'truncate', 'update', 'insert', 'alter', 'create']
    if any(word in query_lower for word in dangerous):
        return "ERROR: Dangerous SQL keywords detected"

    # Add limit if missing
    if 'limit' not in query_lower:
        query = query.rstrip(';') + ' LIMIT 20'

    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="pilotpros_db",
            user="pilotpros_user",
            password="pilotpros_secure_pass_2025"
        )
        cur = conn.cursor()

        cur.execute(query)

        # Get column names
        columns = [desc[0] for desc in cur.description]

        # Fetch results
        results = cur.fetchall()

        # Convert to list of dicts
        data = []
        for row in results:
            data.append(dict(zip(columns, [str(val) if val is not None else None for val in row])))

        conn.close()

        return json.dumps(data, indent=2) if data else "Query returned no results"

    except Exception as e:
        return f"Query error: {str(e)}"

# ============================================================================
# LLM CONFIGURATION - Production settings
# ============================================================================

# Create the LLM with production configuration
llm = ChatOpenAI(
    model="gpt-4o-mini",  # Fast and cost-effective
    temperature=0.3,      # Lower temperature for more consistent responses
    max_retries=3,
    request_timeout=30,
    openai_api_key=os.environ.get("OPENAI_API_KEY")
)

# ============================================================================
# TOOLS LIST - All real database tools
# ============================================================================

tools = [
    get_database_info,    # Schema information
    query_users,          # User queries
    query_sessions,       # Session queries
    get_system_status,    # System health
    execute_business_query # Custom SQL queries
]

# ============================================================================
# SYSTEM PROMPT - Professional agent instructions
# ============================================================================

system_prompt = """You are PilotProOS Intelligence Assistant, a professional database query agent.

You have access to a PostgreSQL database with real business data.
Your tools connect to the actual database and return real information, not fake data.

Available tables:
- pilotpros.users: User accounts
- pilotpros.active_sessions: Active sessions
- pilotpros.business_execution_data: Process execution data
- pilotpros.system_settings: System configuration

When users ask questions:
1. Use the appropriate tool to query the database
2. Provide accurate information based on real data
3. If you need to explore the schema, use get_database_info first
4. For custom queries, use execute_business_query with proper SQL

Remember: All your responses are based on REAL DATA from the PostgreSQL database, not fake or mocked data.
Current time: {current_time}
""".format(current_time=datetime.now().isoformat())

# ============================================================================
# CREATE REACT AGENT - Following LangGraph best practices
# ============================================================================

# Create the ReAct agent graph
# Simplest form - let LangGraph handle everything
graph = create_react_agent(
    llm,
    tools
)

# Compile and export for LangGraph Studio
app = graph

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ["app", "graph", "tools"]