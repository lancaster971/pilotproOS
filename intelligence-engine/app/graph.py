"""
LangGraph Studio - Graph definition for PilotProOS Intelligence Engine
PRODUCTION-READY with REAL DATABASE TOOLS + MILHENA COMPONENTS
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

# Import Milhena components
from app.core.hybrid_classifier import HybridClassifier, IntentCategory
from app.core.hybrid_masking import HybridMaskingLibrary
from app.core.hybrid_validator import HybridValidator, ValidationResult
from app.core.simple_audit_logger import SimpleAuditLogger
from app.system_agents.milhena.data_analyst_agent import DataAnalystAgent

# Configure LangSmith tracing for Milhena
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "milhena-pipeline"

# Initialize Milhena components with tracing
from langsmith import traceable

@traceable(name="MilhenaClassifier", run_type="tool")
def traced_classify(text):
    """Traced classification for LangSmith visibility"""
    return classifier.classify(text, use_llm_fallback=False)

@traceable(name="MilhenaMasking", run_type="tool")
def traced_mask(text):
    """Traced masking for LangSmith visibility"""
    return masking.mask(text)

@traceable(name="MilhenaValidator", run_type="tool")
def traced_validate(text):
    """Traced validation for LangSmith visibility"""
    return validator.validate(text, use_llm_fallback=False)

# Initialize components
classifier = HybridClassifier()
masking = HybridMaskingLibrary()
validator = HybridValidator()
audit = SimpleAuditLogger()
data_analyst = DataAnalystAgent()

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
            host=os.getenv("DB_HOST", "postgres-dev"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "pilotpros_db"),
            user=os.getenv("DB_USER", "pilotpros_user"),
            password=os.getenv("DB_PASSWORD", "pilotpros_secure_pass_2025")
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
            host=os.getenv("DB_HOST", "postgres-dev"),
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
            host=os.getenv("DB_HOST", "postgres-dev"),
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
            host=os.getenv("DB_HOST", "postgres-dev"),
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

        # MASKING OBBLIGATORIO prima di restituire i dati!
        raw_json = json.dumps(data, indent=2) if data else "Query returned no results"

        # Applica masking per nascondere termini tecnici
        masked_result = masking.mask(raw_json)

        return masked_result

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
# MILHENA-ENHANCED TOOL
# ============================================================================

@tool
def milhena_query_processor(user_query: str) -> str:
    """
    Process user queries through Milhena pipeline for classification,
    validation, and masking before executing database queries.

    Args:
        user_query: Natural language query from user

    Returns:
        Masked and validated response
    """
    import json

    # Step 1: Classify intent (with tracing)
    category, confidence, reasoning = traced_classify(user_query)
    audit.log_classification(user_query, category.value, confidence)

    # Step 2: Route based on category
    if category == IntentCategory.GREETING:
        response = "Ciao! Come posso aiutarti con i dati aziendali?"

    elif category == IntentCategory.BUSINESS_DATA:
        # Step 2a: Query database per dati RAW
        if "utenti" in user_query.lower():
            raw_data = query_users.invoke({"query_type": "count"})
        elif "sessioni" in user_query.lower():
            raw_data = query_sessions.invoke({"query_type": "active"})
        elif "nod" in user_query.lower() or "process" in user_query.lower() or "workflow" in user_query.lower():
            raw_data = execute_business_query.invoke({"query": "SELECT COUNT(*) as total FROM pilotpros.business_execution_data LIMIT 1"})
        else:
            raw_data = get_system_status.invoke({})

        # Step 2b: Data Analyst elabora risposta business (USA LLM!)
        business_response = data_analyst.analyze(user_query, raw_data)

        # Step 3: Masking termini tecnici residui
        masked_response = traced_mask(business_response)
        audit.log_masking(business_response[:50], 1)

        # Step 4: Validazione finale
        validation_report = traced_validate(masked_response)
        audit.log_validation(masked_response[:100], validation_report.result.value, len(validation_report.issues))

        if validation_report.result == ValidationResult.VALID:
            response = masked_response
        else:
            response = f"Dati richiedono revisione."

    elif category == IntentCategory.HELP:
        response = "Posso aiutarti a consultare: numero utenti, sessioni attive, stato del sistema. Come posso assisterti?"

    else:
        response = "Mi dispiace, non ho compreso la richiesta. Puoi riformulare?"

    return response

# ============================================================================
# TOOLS LIST - All real database tools + Milhena
# ============================================================================

tools = [
    milhena_query_processor   # ONLY Milhena - all queries go through security pipeline
]

# ============================================================================
# SYSTEM PROMPT - Professional agent instructions
# ============================================================================

system_prompt = """Sei l'Assistente Intelligente PilotProOS protetto da Milhena Security Pipeline.

🔒 REGOLA DI SICUREZZA ASSOLUTA:
Hai UN SOLO TOOL: milhena_query_processor
USA SEMPRE E SOLO questo tool per QUALSIASI richiesta utente.

Il tool milhena_query_processor applica automaticamente:
✅ Classificazione intent
✅ Mascheramento termini tecnici
✅ Validazione risposte
✅ Audit logging

🚫 VIETATO ASSOLUTAMENTE mostrare:
- Termini tecnici raw: workflow_id, node_id, execution_id, postgres, docker, redis, n8n
- Nomi colonne database: id, email, created_at
- Dati non mascherati dal database

✅ USA SOLO linguaggio business:
- "Business Process" invece di "workflow"
- "Process Run" invece di "execution"
- "Process Step" invece di "node"
- "Database" invece di "postgres"

Rispondi SEMPRE in italiano usando SOLO il tool milhena_query_processor.

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