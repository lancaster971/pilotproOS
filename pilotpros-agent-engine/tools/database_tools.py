"""
Database tools for safe PostgreSQL access
Implements security rules and query sanitization
"""

import asyncpg
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from crewai.tools import BaseTool
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class SafeDatabaseQueryTool(BaseTool):
    """
    Safe database query tool with security constraints
    """

    name: str = "Safe Database Query"
    description: str = "Execute safe read-only queries on PilotPro database with security rules"

    def __init__(self, database_url: str, max_rows: int = 100):
        """
        Initialize database tool

        Args:
            database_url: PostgreSQL connection URL
            max_rows: Maximum rows to return
        """
        super().__init__()
        self.database_url = database_url
        self.max_rows = max_rows
        self.forbidden_keywords = [
            "DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT",
            "ALTER", "GRANT", "REVOKE", "CREATE", "REPLACE",
            "EXECUTE", "EXEC", "CALL", "PASSWORD", "SECRET"
        ]
        self.sensitive_columns = [
            "password", "password_hash", "api_key", "secret",
            "token", "jwt", "session_id", "salt", "private_key"
        ]

    async def _arun(self, query: str) -> str:
        """
        Execute query asynchronously

        Args:
            query: SQL query to execute

        Returns:
            Query results as JSON string
        """
        try:
            # Validate query safety
            validation = self._validate_query(query)
            if not validation["safe"]:
                return json.dumps({
                    "error": f"Query rejected: {validation['reason']}",
                    "suggestion": validation.get("suggestion", "Please modify your query")
                })

            # Add safety constraints
            safe_query = self._add_safety_constraints(query)

            # Execute query
            conn = await asyncpg.connect(self.database_url)
            try:
                # Set timeout
                await conn.execute("SET statement_timeout = '5000'")  # 5 seconds

                # Execute query
                rows = await conn.fetch(safe_query)

                # Process results
                results = self._process_results(rows)

                # Log for audit
                self._audit_log(query, len(rows))

                return json.dumps({
                    "success": True,
                    "row_count": len(rows),
                    "data": results,
                    "query_executed": safe_query[:200] + "..." if len(safe_query) > 200 else safe_query
                }, indent=2, default=str)

            finally:
                await conn.close()

        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return json.dumps({
                "error": "Database error occurred",
                "details": str(e)[:200]
            })
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return json.dumps({
                "error": "Query execution failed",
                "details": str(e)[:200]
            })

    def _run(self, query: str) -> str:
        """
        Synchronous wrapper for async execution
        """
        import asyncio
        return asyncio.run(self._arun(query))

    def _validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validate query for safety

        Args:
            query: SQL query to validate

        Returns:
            Validation result
        """
        query_upper = query.upper()

        # Check for forbidden operations
        for keyword in self.forbidden_keywords:
            if keyword in query_upper:
                return {
                    "safe": False,
                    "reason": f"Forbidden operation: {keyword}",
                    "suggestion": "Only SELECT queries are allowed"
                }

        # Ensure it's a SELECT query
        if not query_upper.strip().startswith("SELECT"):
            return {
                "safe": False,
                "reason": "Only SELECT queries are allowed",
                "suggestion": "Start your query with SELECT"
            }

        # Check for sensitive columns
        for column in self.sensitive_columns:
            if column.lower() in query.lower():
                return {
                    "safe": False,
                    "reason": f"Access to sensitive column '{column}' is forbidden",
                    "suggestion": "Remove sensitive columns from your query"
                }

        # Check for SQL injection patterns
        if re.search(r';\s*SELECT|UNION\s+ALL|UNION\s+SELECT', query_upper):
            return {
                "safe": False,
                "reason": "Potential SQL injection pattern detected",
                "suggestion": "Simplify your query structure"
            }

        return {"safe": True}

    def _add_safety_constraints(self, query: str) -> str:
        """
        Add safety constraints to query

        Args:
            query: Original query

        Returns:
            Query with safety constraints
        """
        # Remove any existing LIMIT
        query_clean = re.sub(r'LIMIT\s+\d+', '', query, flags=re.IGNORECASE)

        # Add our LIMIT
        if "LIMIT" not in query_clean.upper():
            query_clean = f"{query_clean.rstrip(';')} LIMIT {self.max_rows}"

        return query_clean

    def _process_results(self, rows: List[asyncpg.Record]) -> List[Dict]:
        """
        Process and sanitize query results

        Args:
            rows: Database rows

        Returns:
            Processed results
        """
        results = []
        for row in rows:
            row_dict = dict(row)

            # Mask any potentially sensitive data that got through
            for key in row_dict:
                if any(sensitive in key.lower() for sensitive in ["email", "phone", "ssn"]):
                    value = str(row_dict[key])
                    if "@" in value:  # Email
                        parts = value.split("@")
                        row_dict[key] = f"{parts[0][:3]}***@{parts[1]}"
                    elif len(value) > 6:  # Other sensitive data
                        row_dict[key] = value[:3] + "***" + value[-2:]

            results.append(row_dict)

        return results

    def _audit_log(self, query: str, row_count: int):
        """
        Log query for audit purposes

        Args:
            query: Executed query
            row_count: Number of rows returned
        """
        logger.info(f"Database query executed: {query[:100]}... Rows: {row_count}")


class WorkflowAnalyzerTool(BaseTool):
    """
    Specialized tool for analyzing n8n workflows
    """

    name: str = "Workflow Analyzer"
    description: str = "Analyze n8n workflows and execution patterns"

    def __init__(self, database_url: str):
        super().__init__()
        self.database_url = database_url

    def _run(self, analysis_type: str) -> str:
        """
        Run workflow analysis

        Args:
            analysis_type: Type of analysis to perform

        Returns:
            Analysis results
        """
        analyses = {
            "performance": self._analyze_performance,
            "errors": self._analyze_errors,
            "usage": self._analyze_usage,
            "bottlenecks": self._analyze_bottlenecks
        }

        if analysis_type.lower() in analyses:
            return analyses[analysis_type.lower()]()
        else:
            return json.dumps({
                "error": f"Unknown analysis type: {analysis_type}",
                "available": list(analyses.keys())
            })

    def _analyze_performance(self) -> str:
        """Analyze workflow performance metrics"""
        query = """
            SELECT
                w.name as workflow_name,
                w.active,
                COUNT(e.id) as execution_count,
                AVG(EXTRACT(EPOCH FROM (e.stopped_at - e.started_at))) as avg_duration_seconds,
                MAX(EXTRACT(EPOCH FROM (e.stopped_at - e.started_at))) as max_duration_seconds,
                COUNT(CASE WHEN e.finished = true THEN 1 END) as successful_runs,
                COUNT(CASE WHEN e.finished = false THEN 1 END) as failed_runs,
                MAX(e.started_at) as last_execution
            FROM n8n.workflow_entity w
            LEFT JOIN n8n.execution_entity e ON w.id = e.workflow_id
            WHERE e.started_at > NOW() - INTERVAL '7 days'
            GROUP BY w.id, w.name, w.active
            ORDER BY execution_count DESC
            LIMIT 20
        """

        # Use SafeDatabaseQueryTool to execute
        db_tool = SafeDatabaseQueryTool(self.database_url, max_rows=20)
        return db_tool._run(query)

    def _analyze_errors(self) -> str:
        """Analyze workflow errors"""
        query = """
            SELECT
                w.name as workflow_name,
                COUNT(*) as error_count,
                MAX(e.started_at) as last_error,
                SUBSTRING(e.data::text, 1, 200) as error_sample
            FROM n8n.execution_entity e
            JOIN n8n.workflow_entity w ON e.workflow_id = w.id
            WHERE e.finished = false
            AND e.started_at > NOW() - INTERVAL '24 hours'
            GROUP BY w.name, SUBSTRING(e.data::text, 1, 200)
            ORDER BY error_count DESC
            LIMIT 10
        """

        db_tool = SafeDatabaseQueryTool(self.database_url, max_rows=10)
        return db_tool._run(query)

    def _analyze_usage(self) -> str:
        """Analyze workflow usage patterns"""
        query = """
            SELECT
                DATE(started_at) as execution_date,
                EXTRACT(HOUR FROM started_at) as hour_of_day,
                COUNT(*) as execution_count,
                COUNT(DISTINCT workflow_id) as unique_workflows
            FROM n8n.execution_entity
            WHERE started_at > NOW() - INTERVAL '7 days'
            GROUP BY DATE(started_at), EXTRACT(HOUR FROM started_at)
            ORDER BY execution_date DESC, hour_of_day
        """

        db_tool = SafeDatabaseQueryTool(self.database_url, max_rows=50)
        return db_tool._run(query)

    def _analyze_bottlenecks(self) -> str:
        """Identify workflow bottlenecks"""
        query = """
            SELECT
                w.name as workflow_name,
                w.nodes::json as workflow_nodes,
                AVG(EXTRACT(EPOCH FROM (e.stopped_at - e.started_at))) as avg_duration,
                COUNT(*) as execution_count
            FROM n8n.workflow_entity w
            JOIN n8n.execution_entity e ON w.id = e.workflow_id
            WHERE e.started_at > NOW() - INTERVAL '7 days'
            AND e.finished = true
            GROUP BY w.id, w.name, w.nodes
            HAVING AVG(EXTRACT(EPOCH FROM (e.stopped_at - e.started_at))) > 30
            ORDER BY avg_duration DESC
            LIMIT 10
        """

        db_tool = SafeDatabaseQueryTool(self.database_url, max_rows=10)
        return db_tool._run(query)


class UserActivityTool(BaseTool):
    """
    Tool for analyzing user activity and access patterns
    """

    name: str = "User Activity Analyzer"
    description: str = "Analyze user activity and system usage patterns"

    def __init__(self, database_url: str):
        super().__init__()
        self.database_url = database_url

    def _run(self, timeframe: str = "7d") -> str:
        """
        Analyze user activity

        Args:
            timeframe: Time period (1d, 7d, 30d)

        Returns:
            Activity analysis
        """
        interval_map = {
            "1d": "1 day",
            "7d": "7 days",
            "30d": "30 days",
            "1h": "1 hour",
            "24h": "24 hours"
        }

        interval = interval_map.get(timeframe, "7 days")

        query = f"""
            SELECT
                role,
                COUNT(*) as total_users,
                COUNT(CASE WHEN last_login > NOW() - INTERVAL '{interval}' THEN 1 END) as active_users,
                AVG(EXTRACT(EPOCH FROM (NOW() - last_login))/86400)::INT as avg_days_since_login,
                MIN(created_at) as first_user_created,
                MAX(created_at) as latest_user_created
            FROM pilotpros.users
            GROUP BY role
            ORDER BY total_users DESC
        """

        db_tool = SafeDatabaseQueryTool(self.database_url)
        result = json.loads(db_tool._run(query))

        if result.get("success"):
            # Add interpretation
            result["interpretation"] = self._interpret_activity(result["data"])

        return json.dumps(result, indent=2)

    def _interpret_activity(self, data: List[Dict]) -> Dict:
        """
        Interpret activity data

        Args:
            data: Activity data

        Returns:
            Interpretation
        """
        total_users = sum(row.get("total_users", 0) for row in data)
        active_users = sum(row.get("active_users", 0) for row in data)

        engagement_rate = (active_users / total_users * 100) if total_users > 0 else 0

        return {
            "total_users": total_users,
            "active_users": active_users,
            "engagement_rate": f"{engagement_rate:.1f}%",
            "health_status": "Good" if engagement_rate > 60 else "Needs attention"
        }