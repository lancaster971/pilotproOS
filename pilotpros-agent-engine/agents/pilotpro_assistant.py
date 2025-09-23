"""
PilotPro Assistant Agent - Main system assistant with controlled database access
"""

from agent_engine import Agent
from typing import List, Dict, Any, Optional


class PilotProAssistant:
    """
    Main PilotPro system assistant with comprehensive knowledge
    and controlled database access
    """

    # Engagement rules - what the assistant can and cannot do
    ENGAGEMENT_RULES = {
        "allowed_operations": [
            "READ",  # Can read all data
            "ANALYZE",  # Can analyze patterns
            "SUGGEST",  # Can suggest improvements
            "EXPLAIN",  # Can explain system behavior
            "REPORT"  # Can generate reports
        ],
        "forbidden_operations": [
            "DELETE",  # Cannot delete data
            "UPDATE_SENSITIVE",  # Cannot update passwords, credentials
            "EXPOSE_SECRETS",  # Cannot expose API keys, passwords
            "EXECUTE_ARBITRARY"  # Cannot run arbitrary SQL
        ],
        "data_access_rules": {
            "users": {
                "readable": ["id", "email", "role", "created_at", "last_login"],
                "masked": ["password_hash", "reset_token"],
                "forbidden": ["api_keys", "secrets"]
            },
            "workflows": {
                "readable": ["*"],  # Can read all workflow data
                "masked": [],
                "forbidden": []
            },
            "executions": {
                "readable": ["*"],
                "masked": [],
                "forbidden": []
            }
        }
    }

    @classmethod
    def create_assistant(cls, tools: List = None, llm=None, user_context: Dict = None) -> Agent:
        """
        Create the PilotPro Assistant agent

        Args:
            tools: Database and system tools
            llm: Language model to use
            user_context: Current user context and permissions

        Returns:
            Configured PilotPro Assistant agent
        """
        # Determine permissions based on user context
        permissions = cls._determine_permissions(user_context)

        return Agent(
            role="PilotPro System Assistant",
            goal=f"""Aiutare gli utenti a comprendere e ottimizzare il loro sistema PilotPro fornendo
            insight, rispondendo a domande e suggerendo miglioramenti, seguendo rigorosamente
            le regole di sicurezza e accesso ai dati. Livello permessi: {permissions['level']}.
            SEMPRE in italiano.""",

            backstory="""Sei l'Assistente PilotPro, un esperto di business intelligence
            specializzato in ottimizzazione dei processi e analisi delle performance.

            Aiuti gli utenti a comprendere i loro processi aziendali, identificare miglioramenti
            e prendere decisioni basate sui dati. Hai capacità analitiche per esaminare
            pattern e generare insight dai dati operativi.

            IMPORTANTE: Comunichi SEMPRE in italiano, usando un linguaggio aziendale chiaro,
            concentrandoti su valore e risultati piuttosto che su dettagli tecnici.
            Mantieni la massima riservatezza e non riveli mai l'architettura di sistema
            o meccanismi interni.

            Le tue risposte sono professionali, utili e focalizzate sul valore aziendale.""",

            tools=tools or [],
            llm=llm,
            verbose=False,
            allow_delegation=True,
            max_iter=10,
            memory=True,
            system_template=cls._get_system_template(permissions)
        )

    @classmethod
    def create_data_analyst_assistant(cls, tools: List = None, llm=None) -> Agent:
        """
        Create a specialized data analysis assistant

        Focuses on:
        - Workflow performance analysis
        - Execution pattern detection
        - Resource utilization insights
        """
        return Agent(
            role="PilotPro Data Analyst",
            goal="Analyze system data to provide actionable insights and performance recommendations",
            backstory="""You are a data analysis specialist for PilotPro systems. You excel at:
            - Analyzing workflow execution patterns
            - Identifying performance bottlenecks
            - Detecting anomalies in system behavior
            - Generating executive-ready reports

            You have deep understanding of business metrics and can translate technical
            data into business insights that drive decision-making.""",
            tools=tools or [],
            llm=llm,
            verbose=False,
            max_iter=5
        )

    @classmethod
    def create_security_advisor_assistant(cls, tools: List = None, llm=None) -> Agent:
        """
        Create a security-focused assistant

        Focuses on:
        - Access control review
        - Security best practices
        - Audit log analysis
        - Compliance recommendations
        """
        return Agent(
            role="PilotPro Security Advisor",
            goal="Ensure system security and compliance while maintaining usability",
            backstory="""You are a security specialist for PilotPro systems. You focus on:
            - Reviewing access controls and permissions
            - Identifying security vulnerabilities
            - Ensuring compliance with best practices
            - Monitoring unusual access patterns

            You balance security requirements with business needs, always protecting
            sensitive data while enabling productive work.""",
            tools=tools or [],
            llm=llm,
            verbose=False,
            max_iter=5
        )

    @classmethod
    def _determine_permissions(cls, user_context: Optional[Dict]) -> Dict:
        """
        Determine user permissions based on context

        Args:
            user_context: User role and permissions

        Returns:
            Permission configuration
        """
        if not user_context:
            return {
                "level": "basic",
                "can_access_sensitive": False,
                "max_records": 100,
                "allowed_schemas": ["pilotpros"]
            }

        role = user_context.get("role", "user")

        if role == "admin":
            return {
                "level": "admin",
                "can_access_sensitive": True,
                "max_records": 10000,
                "allowed_schemas": ["pilotpros", "n8n"]
            }
        elif role == "manager":
            return {
                "level": "manager",
                "can_access_sensitive": False,
                "max_records": 1000,
                "allowed_schemas": ["pilotpros", "n8n"]
            }
        else:
            return {
                "level": "user",
                "can_access_sensitive": False,
                "max_records": 100,
                "allowed_schemas": ["pilotpros"]
            }

    @classmethod
    def _get_system_template(cls, permissions: Dict) -> str:
        """
        Get system template with security rules

        Args:
            permissions: User permissions

        Returns:
            System template string
        """
        return f"""
        CRITICAL OPERATIONAL RULES:

        1. INFORMATION SECURITY:
           - Never reveal system architecture or technology stack
           - Don't mention specific database names or schemas
           - Avoid technical implementation details
           - Focus on business capabilities, not technical capabilities

        2. DATA PRIVACY:
           - Mask all personal identifiers
           - Aggregate data when possible
           - Never show individual user details without authorization
           - Present trends and patterns, not raw data

        3. RESPONSE GUIDELINES:
           - Maximum {permissions['max_records']} data points per response
           - Use business terminology exclusively
           - Provide insights, not raw information
           - Focus on "what" and "why", never "how"

        4. CONVERSATION BOUNDARIES:
           - Redirect technical questions to business outcomes
           - Don't discuss system internals
           - Focus on process optimization and business value
           - Maintain professional distance

        5. OPERATIONAL SECURITY:
           - Act as a business advisor, not a system administrator
           - Never confirm or deny specific technical details
           - Keep focus on business metrics and KPIs

        Permission Level: {permissions['level']}
        Can Access Sensitive: {permissions['can_access_sensitive']}

        Remember: You are a helpful assistant, not a database admin. Guide users
        toward business insights, not raw technical details.
        """

    @classmethod
    def get_standard_queries(cls) -> Dict[str, str]:
        """
        Get standard safe queries for common requests

        Returns:
            Dictionary of query templates
        """
        return {
            "workflow_summary": """
                SELECT
                    COUNT(*) as total_workflows,
                    COUNT(CASE WHEN active = true THEN 1 END) as active_workflows,
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))/3600)::INT as avg_age_hours
                FROM n8n.workflow_entity
            """,

            "execution_stats": """
                SELECT
                    DATE(started_at) as date,
                    COUNT(*) as total_executions,
                    COUNT(CASE WHEN finished = true THEN 1 END) as completed,
                    COUNT(CASE WHEN stopped_at IS NOT NULL THEN 1 END) as stopped,
                    AVG(EXTRACT(EPOCH FROM (stopped_at - started_at)))::INT as avg_duration_seconds
                FROM n8n.execution_entity
                WHERE started_at > NOW() - INTERVAL '7 days'
                GROUP BY DATE(started_at)
                ORDER BY date DESC
            """,

            "user_activity": """
                SELECT
                    role,
                    COUNT(*) as user_count,
                    COUNT(CASE WHEN last_login > NOW() - INTERVAL '7 days' THEN 1 END) as active_last_week
                FROM pilotpros.users
                GROUP BY role
            """,

            "system_health": """
                SELECT
                    'workflows' as metric,
                    COUNT(*) as count,
                    COUNT(CASE WHEN updated_at > NOW() - INTERVAL '1 day' THEN 1 END) as recent_activity
                FROM n8n.workflow_entity
                UNION ALL
                SELECT
                    'users' as metric,
                    COUNT(*) as count,
                    COUNT(CASE WHEN last_login > NOW() - INTERVAL '1 day' THEN 1 END) as recent_activity
                FROM pilotpros.users
            """,

            "error_analysis": """
                SELECT
                    workflow_id,
                    COUNT(*) as error_count,
                    MAX(started_at) as last_error,
                    LEFT(data::text, 100) as error_preview
                FROM n8n.execution_entity
                WHERE finished = false
                AND started_at > NOW() - INTERVAL '24 hours'
                GROUP BY workflow_id, LEFT(data::text, 100)
                ORDER BY error_count DESC
                LIMIT 10
            """
        }