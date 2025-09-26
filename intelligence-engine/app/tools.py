"""
LangChain Tools for Business Intelligence
"""

from langchain.tools import BaseTool, StructuredTool, tool
from langchain.pydantic_v1 import BaseModel, Field
from typing import Optional, Type, Dict, Any, List
import httpx
import json
from datetime import datetime, timedelta
import asyncio

class BusinessDataInput(BaseModel):
    """Input schema for business data queries"""
    query: str = Field(description="The business data query to execute")
    time_range: Optional[str] = Field(default="7d", description="Time range for the query")

class BusinessDataTool(BaseTool):
    """Tool for querying business data from PostgreSQL"""

    name: str = "business_data_query"
    description: str = """Query business process data including:
    - Process execution statistics
    - Performance metrics
    - Error rates and issues
    - Process efficiency data
    Use this when users ask about workflows, processes, or business metrics."""

    args_schema: Type[BaseModel] = BusinessDataInput

    async def _arun(self, query: str, time_range: str = "7d") -> str:
        """Async execution of business data query"""
        try:
            # Connect to backend API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://backend-dev:3001/api/intelligence/query",
                    json={
                        "query": query,
                        "time_range": time_range,
                        "source": "business_data"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return self._format_business_response(data)
                else:
                    return f"Unable to retrieve business data: {response.status_code}"

        except Exception as e:
            return f"Error querying business data: {str(e)}"

    def _run(self, query: str, time_range: str = "7d") -> str:
        """Sync execution wrapper"""
        return asyncio.run(self._arun(query, time_range))

    def _format_business_response(self, data: Dict) -> str:
        """Format response in business terms"""
        formatted = []

        if "processes" in data:
            formatted.append(f"Active Business Processes: {data['processes']['active']}")
            formatted.append(f"Completed Today: {data['processes']['completed_today']}")
            formatted.append(f"Success Rate: {data['processes']['success_rate']}%")

        if "metrics" in data:
            formatted.append(f"\nKey Metrics:")
            for metric, value in data["metrics"].items():
                formatted.append(f"  • {metric}: {value}")

        return "\n".join(formatted)

class WorkflowInput(BaseModel):
    """Input for workflow operations"""
    action: str = Field(description="Action to perform: list, status, trigger, analyze")
    workflow_id: Optional[str] = Field(default=None, description="Specific workflow ID")
    parameters: Optional[Dict] = Field(default={}, description="Additional parameters")

class WorkflowTool(BaseTool):
    """Tool for interacting with n8n workflows"""

    name: str = "workflow_management"
    description: str = """Manage and interact with business process workflows:
    - List available workflows
    - Check workflow status
    - Trigger workflow execution
    - Analyze workflow performance
    Use this for workflow-specific operations."""

    args_schema: Type[BaseModel] = WorkflowInput

    async def _arun(self, action: str, workflow_id: str = None, parameters: Dict = None) -> str:
        """Execute workflow operations"""
        try:
            async with httpx.AsyncClient() as client:
                if action == "list":
                    response = await client.get("http://automation-engine-dev:5678/api/v1/workflows")

                elif action == "status" and workflow_id:
                    response = await client.get(
                        f"http://automation-engine-dev:5678/api/v1/workflows/{workflow_id}"
                    )

                elif action == "trigger" and workflow_id:
                    response = await client.post(
                        f"http://automation-engine-dev:5678/api/v1/workflows/{workflow_id}/activate",
                        json=parameters or {}
                    )

                elif action == "analyze" and workflow_id:
                    response = await client.get(
                        f"http://automation-engine-dev:5678/api/v1/executions?workflowId={workflow_id}"
                    )

                else:
                    return f"Invalid action or missing workflow_id"

                if response.status_code == 200:
                    return self._format_workflow_response(action, response.json())
                else:
                    return f"Workflow operation failed: {response.status_code}"

        except Exception as e:
            return f"Error in workflow operation: {str(e)}"

    def _run(self, action: str, workflow_id: str = None, parameters: Dict = None) -> str:
        """Sync execution wrapper"""
        return asyncio.run(self._arun(action, workflow_id, parameters))

    def _format_workflow_response(self, action: str, data: Any) -> str:
        """Format workflow response"""
        if action == "list":
            workflows = data.get("data", [])
            return f"Found {len(workflows)} business processes:\n" + \
                   "\n".join([f"  • {w['name']} (ID: {w['id']})" for w in workflows[:10]])

        elif action == "status":
            return f"Process '{data['name']}' is {data['active']} with {data['nodes']} steps"

        elif action == "analyze":
            execs = data.get("data", [])
            success = len([e for e in execs if e["finished"]])
            return f"Process Analysis: {len(execs)} runs, {success} successful, " \
                   f"{len(execs) - success} failed"

        return json.dumps(data, indent=2)

class MetricsInput(BaseModel):
    """Input for metrics calculation"""
    metric_type: str = Field(description="Type of metric: performance, cost, efficiency, quality")
    period: str = Field(default="7d", description="Time period for metrics")
    aggregation: str = Field(default="avg", description="Aggregation method: avg, sum, max, min")

class MetricsTool(BaseTool):
    """Tool for business metrics calculation"""

    name: str = "metrics_calculator"
    description: str = """Calculate and analyze business metrics:
    - Performance metrics (response time, throughput)
    - Cost analysis
    - Efficiency ratios
    - Quality indicators
    Use this for KPI calculations and metric analysis."""

    args_schema: Type[BaseModel] = MetricsInput

    def _run(self, metric_type: str, period: str = "7d", aggregation: str = "avg") -> str:
        """Calculate business metrics"""

        # Simulated metric calculation
        metrics = {
            "performance": {
                "avg_response_time": "124ms",
                "throughput": "1,247 processes/hour",
                "success_rate": "94.3%",
                "uptime": "99.9%"
            },
            "cost": {
                "cost_per_process": "$0.0012",
                "total_cost": "$847.23",
                "cost_savings": "$2,341.56",
                "roi": "276%"
            },
            "efficiency": {
                "automation_rate": "87%",
                "manual_interventions": "13%",
                "avg_completion_time": "4.2 minutes",
                "optimization_potential": "23%"
            },
            "quality": {
                "error_rate": "0.6%",
                "data_accuracy": "99.4%",
                "compliance_score": "98%",
                "customer_satisfaction": "4.7/5"
            }
        }

        selected_metrics = metrics.get(metric_type, {})

        result = [f"Business Metrics ({metric_type}) for {period}:"]
        for key, value in selected_metrics.items():
            formatted_key = key.replace("_", " ").title()
            result.append(f"  • {formatted_key}: {value}")

        return "\n".join(result)

    async def _arun(self, metric_type: str, period: str = "7d", aggregation: str = "avg") -> str:
        """Async wrapper"""
        return self._run(metric_type, period, aggregation)

# Helper function to create tools
def get_all_business_tools() -> List[BaseTool]:
    """Return all available business intelligence tools"""
    return [
        BusinessDataTool(),
        WorkflowTool(),
        MetricsTool()
    ]

# Decorator-based tools for simple functions
@tool
def calculate_roi(investment: float, returns: float) -> str:
    """Calculate ROI for business investments

    Args:
        investment: Initial investment amount
        returns: Total returns amount
    """
    roi = ((returns - investment) / investment) * 100
    return f"ROI: {roi:.2f}% (Investment: ${investment:,.2f}, Returns: ${returns:,.2f})"

@tool
def format_business_report(data: str, report_type: str = "executive") -> str:
    """Format data into a business report

    Args:
        data: Raw data to format
        report_type: Type of report (executive, detailed, summary)
    """
    templates = {
        "executive": "EXECUTIVE SUMMARY\n{data}\n\nKEY INSIGHTS\n• To be determined",
        "detailed": "DETAILED ANALYSIS\n{data}\n\nMETRICS\n• To be calculated",
        "summary": "QUICK SUMMARY\n{data}"
    }

    template = templates.get(report_type, templates["summary"])
    return template.format(data=data)