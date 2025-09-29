"""
Base Agent Class
Foundation for all specialized agents
"""
from typing import Dict, Any, Optional, List, TypedDict
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import logging
from datetime import datetime
from langchain_core.messages import BaseMessage
from langsmith import traceable

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    UNAVAILABLE = "unavailable"

@dataclass
class AgentConfig:
    """Configuration for an agent"""
    name: str
    description: str
    capabilities: List[str]
    max_retries: int = 3
    timeout_seconds: int = 30
    cache_enabled: bool = True
    tracing_enabled: bool = True

@dataclass
class AgentResult:
    """Result from agent processing"""
    success: bool
    output: Any
    agent_name: str
    processing_time: float
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentState(TypedDict):
    """Base state for agent processing"""
    messages: List[BaseMessage]
    query: str
    session_id: str
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    result: Optional[AgentResult]

class BaseAgent(ABC):
    """
    Abstract base class for all agents
    Provides common functionality and interface
    """

    def __init__(self, config: AgentConfig):
        """Initialize base agent"""
        self.config = config
        self.status = AgentStatus.IDLE
        self._processing_start = None
        self._initialize()
        logger.info(f"Agent '{config.name}' initialized")

    def _initialize(self):
        """Initialize agent-specific components"""
        pass

    @abstractmethod
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> AgentResult:
        """
        Process a query

        Args:
            query: User query
            context: Optional context
            session_id: Session identifier

        Returns:
            AgentResult with processing outcome
        """
        pass

    @abstractmethod
    def can_handle(self, query: str, intent: Optional[str] = None) -> bool:
        """
        Check if this agent can handle the query

        Args:
            query: User query
            intent: Optional detected intent

        Returns:
            True if agent can handle
        """
        pass

    @traceable(name="BaseAgentProcess")
    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> AgentResult:
        """
        Execute agent processing with error handling

        Args:
            query: User query
            context: Optional context
            session_id: Session identifier

        Returns:
            AgentResult
        """
        self.status = AgentStatus.PROCESSING
        self._processing_start = datetime.now()

        try:
            # Process query
            result = await self.process(query, context, session_id)

            # Calculate processing time
            processing_time = (datetime.now() - self._processing_start).total_seconds()
            result.processing_time = processing_time

            self.status = AgentStatus.IDLE
            return result

        except Exception as e:
            logger.error(f"Agent {self.config.name} error: {e}")
            self.status = AgentStatus.ERROR

            processing_time = (datetime.now() - self._processing_start).total_seconds()

            return AgentResult(
                success=False,
                output=None,
                agent_name=self.config.name,
                processing_time=processing_time,
                error=str(e)
            )

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities"""
        return self.config.capabilities

    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "name": self.config.name,
            "status": self.status.value,
            "capabilities": self.config.capabilities,
            "cache_enabled": self.config.cache_enabled,
            "tracing_enabled": self.config.tracing_enabled
        }

    def is_available(self) -> bool:
        """Check if agent is available"""
        return self.status in [AgentStatus.IDLE, AgentStatus.PROCESSING]

    def __str__(self) -> str:
        """String representation"""
        return f"{self.config.name} ({self.status.value})"

    def __repr__(self) -> str:
        """Detailed representation"""
        return f"<{self.__class__.__name__} name='{self.config.name}' status={self.status.value}>"