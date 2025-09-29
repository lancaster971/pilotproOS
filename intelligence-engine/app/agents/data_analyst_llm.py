"""
Data Analyst Agent with REAL LLM
Analytics and insights generation using GPT-4o-mini
REAL AGENT - NO MOCK - NO SIMPLIFIED VERSION
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langsmith import traceable

from app.tools.n8n_message_tools import (
    search_workflow_messages,
    get_workflow_execution_history,
    extract_batch_messages
)
from app.database import get_db_connection
from app.security import MultiLevelMaskingEngine, UserLevel

import logging
logger = logging.getLogger(__name__)


# Additional data analysis tools
@tool
async def analyze_workflow_performance(time_range_days: int = 7) -> str:
    """
    Analyze workflow performance metrics.

    Args:
        time_range_days: Number of days to analyze

    Returns:
        Performance metrics summary
    """
    try:
        conn = await get_db_connection()

        # Get performance metrics
        sql = """
            SELECT
                COUNT(*) as total_executions,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
                COUNT(CASE WHEN status = 'error' THEN 1 END) as failed,
                AVG(EXTRACT(EPOCH FROM ("stoppedAt" - "startedAt"))) as avg_duration_seconds
            FROM n8n.execution_entity
            WHERE "stoppedAt" > NOW() - INTERVAL '%s days'
        """

        result = await conn.fetchrow(sql, time_range_days)
        await conn.close()

        if result:
            success_rate = (result['successful'] / result['total_executions'] * 100) if result['total_executions'] > 0 else 0

            return f"""📊 Performance Analysis (last {time_range_days} days):
• Total Executions: {result['total_executions']}
• Success Rate: {success_rate:.1f}%
• Average Duration: {result['avg_duration_seconds']:.2f} seconds
• Failed: {result['failed']}"""
        else:
            return "No performance data available for the specified period."

    except Exception as e:
        logger.error(f"Error analyzing performance: {e}")
        return "Unable to retrieve performance metrics."


@tool
async def get_workflow_trends(period_days: int = 30) -> str:
    """
    Get workflow execution trends over time.

    Args:
        period_days: Period to analyze

    Returns:
        Trend analysis
    """
    try:
        conn = await get_db_connection()

        sql = """
            SELECT
                DATE("stoppedAt") as date,
                COUNT(*) as executions,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as successful
            FROM n8n.execution_entity
            WHERE "stoppedAt" > NOW() - INTERVAL '%s days'
            GROUP BY DATE("stoppedAt")
            ORDER BY date DESC
            LIMIT 10
        """

        results = await conn.fetch(sql, period_days)
        await conn.close()

        if results:
            trend = "📈 Execution Trends:\n"
            for row in results:
                date = row['date'].strftime("%d/%m")
                success_rate = (row['successful'] / row['executions'] * 100) if row['executions'] > 0 else 0
                trend += f"• {date}: {row['executions']} runs ({success_rate:.0f}% success)\n"
            return trend
        else:
            return "No trend data available."

    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        return "Unable to retrieve trend data."


class DataAnalystAgent:
    """
    REAL Data Analyst Agent with GPT-4o-mini
    Generates insights and analytics using ACTUAL LLM
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize Data Analyst with REAL LLM

        Args:
            openai_api_key: OpenAI API key (defaults to env var)
        """
        # Get API key
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for REAL agent")

        # Initialize REAL LLM
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            model="gpt-4o-mini",
            temperature=0.5,  # Balanced for analytical insights
            max_tokens=2000,
            timeout=30,
            max_retries=2
        )

        # Analytics tools
        self.tools = [
            search_workflow_messages,
            get_workflow_execution_history,
            extract_batch_messages,
            analyze_workflow_performance,
            get_workflow_trends
        ]

        # Memory
        self.memory = MemorySaver()

        # System prompt for data analysis
        self.system_prompt = """You are a Data Analyst Agent specialized in business process analytics.

Your expertise includes:
1. Analyzing process performance and efficiency
2. Identifying trends and patterns in execution data
3. Generating actionable insights from metrics
4. Creating comprehensive reports

CRITICAL RULES:
- Present data in business-friendly format
- Use visualizations (emojis/charts) to enhance readability
- Translate technical metrics to business value:
  * execution time → process efficiency
  * success rate → reliability score
  * error rate → areas for improvement
- Provide actionable recommendations based on data
- NEVER expose technical implementation details

You have access to tools for:
- Analyzing workflow performance metrics
- Identifying execution trends
- Comparing historical data
- Batch analysis across multiple processes

When analyzing data:
1. Use tools to gather REAL metrics
2. Identify patterns and anomalies
3. Generate insights that drive business decisions
4. Present findings in executive-friendly format"""

        # Create REAL ReAct agent
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            checkpointer=self.memory
        )

        # Masking engine
        self.masking_engine = MultiLevelMaskingEngine()

        logger.info("Data Analyst Agent initialized with GPT-4o-mini")

    @traceable(name="DataAnalystLLMProcess")
    async def process(
        self,
        query: str,
        session_id: str,
        user_level: UserLevel = UserLevel.BUSINESS,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process analytics queries using REAL LLM

        Args:
            query: User query for analysis
            session_id: Session ID
            user_level: User authorization level
            context: Optional context

        Returns:
            Dict with analytical response and metadata
        """
        start_time = datetime.now()

        try:
            # Config for agent
            config = {
                "configurable": {
                    "thread_id": session_id
                }
            }

            # Prepare messages with system prompt
            messages = {
                "messages": [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=query)
                ]
            }

            # Add analytical context
            if context:
                if "time_range" in context:
                    context_msg = f"Analyze data for: {context['time_range']}"
                    messages["messages"].insert(0, SystemMessage(content=context_msg))

            # Invoke REAL agent
            logger.info(f"Data Analyst processing with GPT-4o-mini: {query[:50]}...")

            response = await self.agent.ainvoke(
                messages,
                config=config
            )

            # Extract response
            if response and "messages" in response:
                final_message = response["messages"][-1].content
            else:
                final_message = "Unable to complete analysis."

            # Apply masking
            masked_response = self.masking_engine.mask(
                final_message,
                user_level=user_level
            )

            # Metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            tokens_used = len(query.split()) * 1.5 + len(final_message.split()) * 1.5

            return {
                "success": True,
                "response": masked_response.masked,
                "agent_name": "data_analyst",
                "processing_time": processing_time,
                "tokens_used": int(tokens_used),
                "cost": tokens_used * 0.00015 / 1000,
                "metadata": {
                    "session_id": session_id,
                    "user_level": user_level.value,
                    "llm_model": "gpt-4o-mini",
                    "tools_used": self._extract_tools_used(response),
                    "masking_applied": masked_response.replacements_made > 0,
                    "analysis_type": self._detect_analysis_type(query)
                }
            }

        except Exception as e:
            logger.error(f"Data Analyst LLM error: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()

            fallback = """Mi dispiace, ho riscontrato un problema nell'analisi dei dati.

Posso comunque fornire:
- Report sulle performance
- Analisi dei trend
- Statistiche comparative
- Metriche di efficienza

Specifica il tipo di analisi desiderata."""

            return {
                "success": False,
                "response": fallback,
                "agent_name": "data_analyst",
                "processing_time": processing_time,
                "error": str(e)
            }

    def _extract_tools_used(self, response: Dict) -> List[str]:
        """Extract which tools were used"""
        tools_used = []

        if response and "messages" in response:
            for msg in response["messages"]:
                if hasattr(msg, 'tool_calls'):
                    for tool_call in msg.tool_calls:
                        tools_used.append(tool_call.get("name", "unknown"))

                if hasattr(msg, 'additional_kwargs'):
                    if 'tool_calls' in msg.additional_kwargs:
                        for tc in msg.additional_kwargs['tool_calls']:
                            if 'function' in tc:
                                tools_used.append(tc['function'].get('name'))

        return list(set(tools_used))

    def _detect_analysis_type(self, query: str) -> str:
        """Detect type of analysis requested"""
        query_lower = query.lower()

        if "trend" in query_lower:
            return "trend_analysis"
        elif "performance" in query_lower or "efficienza" in query_lower:
            return "performance_analysis"
        elif "report" in query_lower:
            return "comprehensive_report"
        elif "confronta" in query_lower or "compare" in query_lower:
            return "comparative_analysis"
        else:
            return "general_analysis"

    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ):
        """
        Execute for compatibility
        """
        session_id = session_id or f"analyst-{datetime.now().timestamp()}"

        result = await self.process(
            query=query,
            session_id=session_id,
            context=context
        )

        from app.agents.base_agent import AgentResult

        return AgentResult(
            success=result["success"],
            output=result["response"],
            agent_name=result["agent_name"],
            processing_time=result["processing_time"],
            tokens_used=result.get("tokens_used"),
            cost=result.get("cost"),
            metadata=result.get("metadata", {}),
            error=result.get("error")
        )

    def can_handle(self, query: str, intent: Optional[str] = None) -> bool:
        """
        Check if this agent can handle analytics queries
        """
        query_lower = query.lower()

        # Analytics keywords
        analytics_keywords = [
            "report", "analisi", "analysis",
            "trend", "andamento",
            "statistic", "metriche", "metrics",
            "performance", "prestazioni",
            "confronta", "compare",
            "efficienza", "efficiency",
            "insight", "dashboard"
        ]

        return any(keyword in query_lower for keyword in analytics_keywords)

    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "status": "active",
            "agent_name": "data_analyst",
            "llm_model": "gpt-4o-mini",
            "capabilities": [
                "performance_analysis",
                "trend_analysis",
                "comparative_analysis",
                "report_generation",
                "insights_extraction"
            ],
            "tools_available": len(self.tools),
            "using_real_llm": True,
            "specialization": "analytics",
            "api_connected": bool(self.api_key)
        }


def create_data_analyst_agent(api_key: Optional[str] = None) -> DataAnalystAgent:
    """Factory function to create Data Analyst agent"""
    return DataAnalystAgent(openai_api_key=api_key)