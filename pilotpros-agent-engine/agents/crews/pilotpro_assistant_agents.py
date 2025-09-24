"""
PilotPro Assistant Agent System - Main system assistant with backend API access
"""

from typing import Dict, Any, Optional
from agent_engine import AgentEngine, Mission, Process
from agents.pilotpro_assistant import PilotProAssistant
from tools.backend_api_tools import (
    BackendAPITool,
    WorkflowAPITool,
    AnalyticsAPITool,
    ProcessInsightTool
)
import logging

logger = logging.getLogger(__name__)


class PilotProAssistantAgents:
    """
    PilotPro Assistant Agent System - Safe system access through backend APIs
    """

    def __init__(self, jwt_token: Optional[str] = None, backend_url: str = "http://backend-dev:3001"):
        """
        Initialize PilotPro Assistant Agents

        Args:
            jwt_token: JWT token for backend authentication
            backend_url: Backend service URL
        """
        self.jwt_token = jwt_token
        self.backend_url = backend_url
        self.tools = self._initialize_tools()
        self.assistant = self._initialize_assistant()

    def _initialize_tools(self):
        """Initialize backend API tools"""
        return [
            BackendAPITool(self.backend_url, self.jwt_token),
            WorkflowAPITool(self.backend_url, self.jwt_token),
            AnalyticsAPITool(self.backend_url, self.jwt_token),
            ProcessInsightTool(self.backend_url, self.jwt_token)
        ]

    def _initialize_assistant(self):
        """Initialize PilotPro Assistant"""
        user_context = {
            "role": "user",  # Will be updated based on JWT
            "permissions": ["read", "analyze"]
        }

        return PilotProAssistant.create_assistant(
            tools=self.tools,
            user_context=user_context
        )

    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a user question about the PilotPro system

        Args:
            question: User's question

        Returns:
            Assistant's response
        """
        try:
            # Create mission for the question
            mission = Mission(
                description=f"""
                Answer the following question about the PilotPro system:

                Question: {question}

                Guidelines:
                - Use the available API tools to gather information
                - Provide clear, business-focused answers
                - Include relevant metrics and insights
                - Suggest actionable next steps when appropriate
                - Never reveal technical implementation details
                - Focus on business value and outcomes

                If the question requires data, use the appropriate API tool:
                - WorkflowAPI for workflow information
                - AnalyticsAPI for performance metrics
                - ProcessInsights for recommendations
                """,
                agent=self.assistant,
                expected_output="Clear, helpful answer focused on business value"
            )

            # Create single-agent system
            crew = AgentEngine(
                agents=[self.assistant],
                tasks=[mission],
                process=Process.sequential,
                verbose=False,
                memory=True
            )

            # Execute
            logger.info(f"Processing question: {question[:100]}...")
            result = crew.kickoff()

            return {
                "success": True,
                "question": question,
                "answer": str(result),
                "sources": ["Backend APIs", "Business Intelligence"]
            }

        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_answer": self._get_fallback_answer(question)
            }

    def generate_report(self, report_type: str) -> Dict[str, Any]:
        """
        Generate a business report

        Args:
            report_type: Type of report (daily, weekly, performance, health)

        Returns:
            Generated report
        """
        try:
            # Create mission for report generation
            mission = Mission(
                description=f"""
                Generate a {report_type} report for the PilotPro system.

                Report Requirements:
                1. Executive Summary
                2. Key Metrics and KPIs
                3. Performance Trends
                4. Issues and Risks
                5. Recommendations
                6. Next Steps

                Use the API tools to gather current data:
                - Get workflow statistics
                - Analyze performance metrics
                - Identify trends and patterns
                - Generate actionable insights

                Format the report professionally with clear sections.
                """,
                agent=self.assistant,
                expected_output=f"Complete {report_type} report with insights"
            )

            # Create agent system
            crew = AgentEngine(
                agents=[self.assistant],
                tasks=[mission],
                process=Process.sequential,
                verbose=False
            )

            # Execute
            logger.info(f"Generating {report_type} report...")
            result = crew.kickoff()

            return {
                "success": True,
                "report_type": report_type,
                "report": str(result),
                "generated_at": self._get_timestamp()
            }

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def analyze_performance(self, timeframe: str = "7d") -> Dict[str, Any]:
        """
        Analyze system performance

        Args:
            timeframe: Analysis timeframe

        Returns:
            Performance analysis
        """
        try:
            # Create analysis mission
            mission = Mission(
                description=f"""
                Analyze PilotPro system performance for the last {timeframe}.

                Analysis should include:
                1. Overall system health
                2. Workflow execution metrics
                3. Error rates and patterns
                4. Resource utilization
                5. Bottlenecks and inefficiencies
                6. Improvement opportunities

                Use AnalyticsAPI to get performance data.
                Use ProcessInsights to identify optimization opportunities.

                Present findings in business terms with specific recommendations.
                """,
                agent=self.assistant,
                expected_output="Comprehensive performance analysis with recommendations"
            )

            # Create agent system
            crew = AgentEngine(
                agents=[self.assistant],
                tasks=[mission],
                process=Process.sequential,
                verbose=False
            )

            # Execute
            logger.info(f"Analyzing performance for {timeframe}...")
            result = crew.kickoff()

            return {
                "success": True,
                "timeframe": timeframe,
                "analysis": str(result)
            }

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_fallback_answer(self, question: str) -> str:
        """Provide fallback answer when assistant fails"""
        question_lower = question.lower()

        if "workflow" in question_lower:
            return "To view workflow information, please check the Workflows section in your dashboard."
        elif "performance" in question_lower or "metric" in question_lower:
            return "Performance metrics are available in the Analytics section of your dashboard."
        elif "error" in question_lower or "problem" in question_lower:
            return "For error analysis, please review the Executions log in your system."
        elif "help" in question_lower:
            return "I'm here to help with business process optimization and system insights. What would you like to know?"
        else:
            return "I can help you understand your business processes and identify optimization opportunities. Please be more specific about what you'd like to know."

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()


# Example usage
def example_usage():
    """
    Example of using PilotPro Assistant Agents
    """
    # Initialize crew (in production, JWT token would come from authenticated user)
    crew = PilotProAssistantAgents(
        jwt_token="example_jwt_token",
        backend_url="http://localhost:3001"
    )

    # Answer a question
    response = crew.answer_question(
        "What is the current performance of our order processing workflow?"
    )
    print("Answer:", response)

    # Generate a report
    report = crew.generate_report("weekly")
    print("Report:", report)

    # Analyze performance
    analysis = crew.analyze_performance("30d")
    print("Analysis:", analysis)


if __name__ == "__main__":
    example_usage()