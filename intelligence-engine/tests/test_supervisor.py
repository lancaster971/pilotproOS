#!/usr/bin/env python3
"""
Test Supervisor Agent
Comprehensive tests for multi-agent orchestration
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from app.agents import SupervisorAgent, AgentType, BaseAgent, AgentConfig, AgentResult
from app.security import UserLevel

# Mock agent for testing
class MockAgent(BaseAgent):
    """Mock agent for testing"""

    def __init__(self, name: str, can_handle_queries: list = None):
        config = AgentConfig(
            name=name,
            description=f"Mock {name} agent",
            capabilities=["test", "mock"]
        )
        super().__init__(config)
        self.can_handle_queries = can_handle_queries or []

    async def process(self, query: str, context=None, session_id=None) -> AgentResult:
        """Mock process method"""
        return AgentResult(
            success=True,
            output=f"Mock response from {self.config.name} for: {query}",
            agent_name=self.config.name,
            processing_time=0.1,
            tokens_used=10,
            cost=0.001
        )

    def can_handle(self, query: str, intent=None) -> bool:
        """Check if can handle query"""
        return any(keyword in query.lower() for keyword in self.can_handle_queries)

@pytest.fixture
def supervisor():
    """Create supervisor with mock configuration"""
    # Mock router and masking configs to avoid external dependencies
    from app.core.router import RouterConfig
    from app.security import MaskingConfig

    router_config = RouterConfig(
        groq_api_key="test",
        openai_api_key="test",
        google_api_key="test",
        audit_enabled=False
    )

    masking_config = MaskingConfig(
        user_level=UserLevel.BUSINESS,
        strict_mode=False,
        audit_enabled=False
    )

    supervisor = SupervisorAgent(router_config, masking_config)

    # Register mock agents
    milhena_agent = MockAgent("milhena", ["ciao", "status", "come"])
    n8n_agent = MockAgent("n8n_expert", ["workflow", "messaggio", "execution"])
    data_agent = MockAgent("data_analyst", ["analisi", "report", "metriche"])

    supervisor.register_agent(AgentType.MILHENA, milhena_agent)
    supervisor.register_agent(AgentType.N8N_EXPERT, n8n_agent)
    supervisor.register_agent(AgentType.DATA_ANALYST, data_agent)

    return supervisor

@pytest.mark.asyncio
async def test_supervisor_initialization(supervisor):
    """Test supervisor initialization"""
    assert supervisor is not None
    assert len(supervisor.agents) == 3
    assert AgentType.MILHENA in supervisor.agents
    assert AgentType.N8N_EXPERT in supervisor.agents
    assert AgentType.DATA_ANALYST in supervisor.agents

@pytest.mark.asyncio
async def test_agent_registration(supervisor):
    """Test agent registration"""
    # Create and register new agent
    custom_agent = MockAgent("custom", ["special"])
    supervisor.register_agent(AgentType.CUSTOMER, custom_agent)

    assert AgentType.CUSTOMER in supervisor.agents
    assert supervisor.agents[AgentType.CUSTOMER] == custom_agent

@pytest.mark.asyncio
async def test_analyze_query_node(supervisor):
    """Test analyze_query node"""
    from app.agents.supervisor import SupervisorState

    state = SupervisorState(
        messages=[],
        query="Test query",
        session_id="test-session",
        context={},
        agent_results={},
        metadata={}
    )

    result = await supervisor.analyze_query(state)

    assert result["query"] == "Test query"
    assert result["session_id"] == "test-session"
    assert "timestamp" in result["metadata"]
    assert result["metadata"]["query_length"] == 10

@pytest.mark.asyncio
async def test_route_to_agent_node(supervisor):
    """Test routing logic"""
    from app.agents.supervisor import SupervisorState
    from langchain_core.messages import HumanMessage

    # Mock the supervisor LLM
    mock_router = MagicMock()
    mock_router.next_agent = "milhena"
    mock_router.reasoning = "General greeting query"
    mock_router.confidence = 0.9
    mock_router.requires_multiple_agents = False
    mock_router.parallel_agents = None

    supervisor.supervisor_llm = AsyncMock(return_value=mock_router)

    state = SupervisorState(
        messages=[HumanMessage(content="Ciao come stai?")],
        query="Ciao come stai?",
        session_id="test-session",
        context={},
        agent_results={},
        metadata={}
    )

    result = await supervisor.route_to_agent(state)

    assert result["current_agent"] == "milhena"
    assert result["routing_decision"] is not None
    assert result["routing_decision"].confidence == 0.9

@pytest.mark.asyncio
async def test_execute_agent_node(supervisor):
    """Test agent execution"""
    from app.agents.supervisor import SupervisorState

    state = SupervisorState(
        messages=[],
        query="Ciao Milhena",
        session_id="test-session",
        context={},
        current_agent="milhena",
        agent_results={},
        metadata={}
    )

    result = await supervisor.execute_agent(state)

    assert "milhena" in result["agent_results"]
    assert result["agent_results"]["milhena"].success
    assert "Mock response" in result["agent_results"]["milhena"].output

@pytest.mark.asyncio
async def test_combine_results_node(supervisor):
    """Test result combination"""
    from app.agents.supervisor import SupervisorState

    # Create mock results
    milhena_result = AgentResult(
        success=True,
        output="Response from Milhena",
        agent_name="milhena",
        processing_time=0.1
    )

    state = SupervisorState(
        messages=[],
        query="Test",
        session_id="test-session",
        context={},
        current_agent="milhena",
        agent_results={"milhena": milhena_result},
        metadata={}
    )

    result = await supervisor.combine_results(state)

    assert result["final_response"] == "Response from Milhena"
    assert result["metadata"]["primary_agent"] == "milhena"
    assert result["metadata"]["processing_time"] == 0.1

@pytest.mark.asyncio
async def test_apply_masking_node(supervisor):
    """Test masking application"""
    from app.agents.supervisor import SupervisorState

    state = SupervisorState(
        messages=[],
        query="Test",
        session_id="test-session",
        context={},
        final_response="The n8n workflow is running",
        metadata={}
    )

    result = await supervisor.apply_masking(state)

    # Should mask technical terms
    assert "n8n" not in result["final_response"]
    assert "workflow" not in result["final_response"].lower()
    assert result["metadata"]["masking"]["replacements"] > 0

@pytest.mark.asyncio
async def test_error_handling(supervisor):
    """Test error handling"""
    from app.agents.supervisor import SupervisorState

    state = SupervisorState(
        messages=[],
        query="Test",
        session_id="test-session",
        context={},
        error="Test error",
        agent_results={},
        metadata={}
    )

    result = await supervisor.handle_error(state)

    assert "Mi dispiace" in result["final_response"]
    assert result["metadata"]["error"] == "Test error"
    assert "error_time" in result["metadata"]

@pytest.mark.asyncio
async def test_process_full_flow():
    """Test complete processing flow"""
    # This test is simplified as it requires full LangGraph setup
    # In production, would test with actual graph execution

    from app.core.router import RouterConfig
    from app.security import MaskingConfig

    router_config = RouterConfig(
        groq_api_key="test",
        openai_api_key="test",
        google_api_key="test",
        audit_enabled=False
    )

    masking_config = MaskingConfig(
        user_level=UserLevel.BUSINESS,
        strict_mode=False,
        audit_enabled=False
    )

    supervisor = SupervisorAgent(router_config, masking_config)

    # Would test full flow here with:
    # result = await supervisor.process("Test query")
    # assert result["success"]

    # For now just verify structure
    assert supervisor.graph is not None
    assert supervisor.router is not None
    assert supervisor.masking is not None

def test_supervisor_status(supervisor):
    """Test status reporting"""
    status = supervisor.get_status()

    assert status["active"] == True
    assert "registered_agents" in status
    assert len(status["registered_agents"]) > 0
    assert "router_stats" in status
    assert "masking_stats" in status

if __name__ == "__main__":
    pytest.main([__file__, "-v"])