"""
Chatty Agent State - Minimal State Schema
"""
from typing import TypedDict, List
from langchain_core.messages import BaseMessage


class ChattyState(TypedDict):
    """Minimal state for pure chat agent"""
    messages: List[BaseMessage]
    response: str
