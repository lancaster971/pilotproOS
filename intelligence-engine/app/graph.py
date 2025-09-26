"""
LangGraph Studio - Graph definition for PilotProOS Intelligence Engine
"""

from typing import TypedDict, List
from langchain_core.messages import BaseMessage
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import os

# Define the state
class AgentState(TypedDict):
    messages: List[BaseMessage]

# Create some example tools
@tool
def get_users():
    """Get list of users from the database"""
    return "Users: John, Jane, Bob"

@tool
def get_system_status():
    """Get current system status"""
    return "System Status: Operational"

@tool
def query_business_data():
    """Query business data"""
    return "Revenue: $100k, Users: 500"

# Create the tools list
tools = [get_users, get_system_status, query_business_data]

# Create the LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7
)

# Create the ReAct agent graph without checkpointer (handled by platform)
graph = create_react_agent(
    llm,
    tools
)

# Compile and export
app = graph

# Export for LangGraph Studio
__all__ = ["app", "graph"]