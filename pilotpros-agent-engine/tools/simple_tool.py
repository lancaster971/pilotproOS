"""
Simple Tool for CrewAI - Follows BaseTool pattern
"""

from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


class SimpleBackendInput(BaseModel):
    """Input schema for simple backend tool"""
    query: str = Field(..., description="The query to send to backend")


class SimpleBackendTool(BaseTool):
    """Simplified tool that works with CrewAI"""

    name: str = "Backend API"
    description: str = "Access backend APIs"
    args_schema: Type[BaseModel] = SimpleBackendInput

    def _run(self, query: str) -> str:
        """
        Simple run method that just returns mock data for now

        Args:
            query: The query string

        Returns:
            String response
        """
        return f"Backend response for: {query}"