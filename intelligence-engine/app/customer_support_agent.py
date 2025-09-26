"""
Customer Support Agent - LangChain Agent with PostgreSQL Database Tool
Agent semplice per supporto clienti con accesso al database PilotPro
"""

import asyncio
import asyncpg
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from .llm_manager import get_llm_manager
from .config import settings
from loguru import logger

class DatabaseQueryTool:
    """Safe database query tool for customer support"""

    def __init__(self):
        self.db_url = settings.DATABASE_URL

    async def execute_safe_query(self, query: str) -> Dict[str, Any]:
        """Execute safe SELECT-only queries"""
        try:
            # Validate query is safe (only SELECT)
            query_lower = query.lower().strip()
            if not query_lower.startswith('select'):
                return {"error": "Only SELECT queries allowed", "data": []}

            # Block dangerous keywords
            dangerous_keywords = ['insert', 'update', 'delete', 'drop', 'create', 'alter', 'truncate']
            if any(keyword in query_lower for keyword in dangerous_keywords):
                return {"error": "Dangerous query detected", "data": []}

            # Execute query
            conn = await asyncpg.connect(self.db_url)
            try:
                rows = await conn.fetch(query)
                # Convert to dict format
                data = [dict(row) for row in rows]
                return {"success": True, "data": data, "count": len(data)}
            finally:
                await conn.close()

        except Exception as e:
            logger.error(f"Database query error: {e}")
            return {"error": str(e), "data": []}

    def get_common_queries(self) -> Dict[str, str]:
        """Get common customer support queries"""
        return {
            "list_users": "SELECT id, email, full_name, created_at FROM pilotpros.users WHERE active = true ORDER BY created_at DESC LIMIT 10",
            "recent_users": "SELECT id, email, full_name, created_at FROM pilotpros.users ORDER BY created_at DESC LIMIT 5",
            "user_by_email": "SELECT id, email, full_name, created_at, last_login FROM pilotpros.users WHERE email ILIKE '%{email}%'",
            "user_by_id": "SELECT id, email, full_name, created_at, last_login FROM pilotpros.users WHERE id = {user_id}",
            "user_sessions": "SELECT user_id, created_at, expires_at FROM pilotpros.active_sessions WHERE user_id = {user_id}",
            "failed_logins": "SELECT email, attempt_time, ip_address FROM pilotpros.failed_login_attempts ORDER BY attempt_time DESC LIMIT 10",
            "business_analytics": "SELECT * FROM pilotpros.business_analytics ORDER BY created_at DESC LIMIT 5",
            "system_health": "SELECT setting_key, setting_value FROM pilotpros.system_settings WHERE setting_key LIKE '%health%' OR setting_key LIKE '%status%'"
        }

class CustomerSupportAgent:
    """Simple Customer Support with LangChain LLM + Database Tool"""

    def __init__(self):
        self.db_tool = DatabaseQueryTool()
        self.llm_manager = get_llm_manager()
        self.llm = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize LLM for customer support"""
        try:
            # Get fast LLM
            self.llm = self.llm_manager.get_model("gpt-4o-mini")
            if not self.llm:
                self.llm = self.llm_manager.get_default_model()

            logger.info("✅ Customer Support LLM initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM: {e}")
            self.llm = None

    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent"""
        return [
            Tool(
                name="database_query",
                description="""Query the PilotProOS database for customer information.
                Input should be a SQL SELECT query or a common query type.
                Available common queries: list_users, recent_users, user_by_email, user_by_id,
                user_sessions, failed_logins, business_analytics, system_health.

                Examples:
                - "list_users" - get recent users
                - "user_by_email:john@example.com" - find user by email
                - "user_by_id:123" - get user by ID
                - Custom SELECT query (safe only)""",
                func=self._database_query_wrapper
            ),
            Tool(
                name="current_time",
                description="Get current date and time",
                func=lambda x: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ),
            Tool(
                name="help_suggestions",
                description="Get helpful suggestions for common customer issues",
                func=self._get_help_suggestions
            )
        ]

    def _database_query_wrapper(self, query_input: str) -> str:
        """Wrapper for database queries (sync for LangChain tool)"""
        try:
            # Handle common query patterns
            if ":" in query_input:
                query_type, param = query_input.split(":", 1)
                if query_type in self.db_tool.get_common_queries():
                    query = self.db_tool.get_common_queries()[query_type].format(
                        email=param, user_id=param
                    )
                else:
                    return f"Unknown query type: {query_type}"
            elif query_input in self.db_tool.get_common_queries():
                query = self.db_tool.get_common_queries()[query_input]
            else:
                query = query_input

            # Execute query (need to run async in sync context)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.db_tool.execute_safe_query(query))
            finally:
                loop.close()

            if result.get("success"):
                data = result.get("data", [])
                count = result.get("count", 0)

                if count == 0:
                    return "No data found for this query."
                elif count == 1:
                    return f"Found 1 record: {json.dumps(data[0], default=str, indent=2)}"
                else:
                    return f"Found {count} records. First few:\n{json.dumps(data[:3], default=str, indent=2)}"
            else:
                return f"Query error: {result.get('error', 'Unknown error')}"

        except Exception as e:
            return f"Database tool error: {str(e)}"

    def _get_help_suggestions(self, issue_type: str) -> str:
        """Get helpful suggestions for common issues"""
        suggestions = {
            "login": "Try resetting your password, check if account is locked, verify email address is correct",
            "account": "Check account status, verify personal information, review account permissions",
            "order": "Look up order by ID, check order status, review payment status",
            "technical": "Check system status, review error logs, verify browser compatibility",
            "general": "Provide your account email or ID for personalized help"
        }

        for key, suggestion in suggestions.items():
            if key in issue_type.lower():
                return suggestion

        return "I can help with: login issues, account problems, order status, technical support. What specifically do you need help with?"

    async def chat(self, message: str, customer_id: Optional[str] = None, session_id: str = "default") -> Dict[str, Any]:
        """Chat with customer support agent"""
        try:
            if not self.llm:
                return {
                    "error": "LLM not initialized",
                    "response": "Sorry, the support system is currently unavailable."
                }

            start_time = time.time()

            # Check if message requires database lookup
            database_info = ""
            database_used = False

            if any(keyword in message.lower() for keyword in ['utente', 'utenti', 'user', 'users', 'cliente', 'clienti', 'customer', 'customers', 'ordine', 'login', 'account', 'registrati', 'registrato']):
                # Determine query type
                if customer_id:
                    db_result = await self.db_tool.execute_safe_query(f"SELECT id, email, full_name, created_at FROM pilotpros.users WHERE id = {customer_id}")
                elif 'ultimi' in message.lower() or 'recent' in message.lower():
                    db_result = await self.db_tool.execute_safe_query("SELECT id, email, full_name, created_at FROM pilotpros.users ORDER BY created_at DESC LIMIT 5")
                elif '@' in message:
                    email = message.split('@')[0] + '@' + message.split('@')[1].split()[0]
                    db_result = await self.db_tool.execute_safe_query(f"SELECT id, email, full_name, created_at FROM pilotpros.users WHERE email ILIKE '%{email}%'")
                else:
                    db_result = await self.db_tool.execute_safe_query("SELECT COUNT(*) as total_users FROM pilotpros.users WHERE active = true")

                if db_result.get("success"):
                    database_info = f"\n\nDatabase info: {json.dumps(db_result['data'], default=str)}"
                    database_used = True

            # Create context-aware prompt
            system_prompt = f"""You are a helpful customer support agent for PilotProOS.

Customer Question: {message}
Customer ID: {customer_id or 'Not provided'}
{database_info}

Provide a helpful, professional response. If you have database information, use it to give specific answers.
If no specific data is found, provide general support guidance.
Keep response concise but helpful.

Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

            # Get LLM response
            response = await asyncio.to_thread(
                self.llm.invoke,
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=message)
                ]
            )

            response_time = time.time() - start_time

            return {
                "success": True,
                "response": response.content,
                "response_time": response_time,
                "customer_id": customer_id,
                "session_id": session_id,
                "agent_type": "customer_support",
                "database_used": database_used,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Customer Support Agent error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again or contact support directly.",
                "response_time": 0
            }

# Global agent instance
customer_agent = CustomerSupportAgent()