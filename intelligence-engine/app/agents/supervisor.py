"""
Supervisor Agent
Orchestrates multiple specialized agents using LangGraph
"""
from typing import Dict, Any, Optional, List, Literal, TypedDict, Annotated
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langsmith import traceable
from pydantic import BaseModel, Field

from app.core.router import SmartLLMRouter, RouterConfig, ModelTier
from app.security import MultiLevelMaskingEngine, UserLevel, MaskingConfig
from .base_agent import BaseAgent, AgentConfig, AgentResult, AgentState

logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Types of available agents"""
    MILHENA = "milhena"          # Business assistant
    N8N_EXPERT = "n8n_expert"    # n8n workflow specialist
    DATA_ANALYST = "data_analyst" # Data analysis
    CUSTOMER = "customer"         # Customer-specific agents

@dataclass
class RoutingDecision:
    """Decision made by supervisor"""
    target_agent: AgentType
    reasoning: str
    confidence: float
    fallback_agent: Optional[AgentType] = None
    parallel_agents: Optional[List[AgentType]] = None

class SupervisorState(TypedDict):
    """State for supervisor orchestration"""
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    session_id: str
    context: Dict[str, Any]
    current_agent: Optional[str]
    routing_decision: Optional[RoutingDecision]
    agent_results: Dict[str, AgentResult]
    final_response: Optional[str]
    error: Optional[str]
    metadata: Dict[str, Any]

class AgentRouter(BaseModel):
    """Pydantic model for routing decisions"""
    next_agent: str = Field(description="Name of the agent to route to")
    reasoning: str = Field(description="Reasoning for the routing decision")
    confidence: float = Field(description="Confidence level 0-1")
    requires_multiple_agents: bool = Field(default=False, description="Whether multiple agents are needed")
    parallel_agents: Optional[List[str]] = Field(default=None, description="Agents to run in parallel")

class SupervisorAgent:
    """
    Main orchestrator agent using LangGraph
    Routes requests to appropriate specialist agents
    """

    SUPERVISOR_PROMPT = """You are the Supervisor Agent for PilotProOS Intelligence Engine.
Your role is to analyze user queries and route them to the most appropriate specialist agent.

Available agents and their capabilities:
1. MILHENA - General business assistant, handles greetings, status checks, and general queries
2. N8N_EXPERT - Specialized in n8n workflows, executions, and message extraction
3. DATA_ANALYST - Handles data analysis, metrics, and reporting
4. CUSTOMER - Customer-specific domain agents

User Query: {query}
Context: {context}

Analyze the query and decide:
1. Which agent should handle this query?
2. Why is this agent the best choice?
3. How confident are you in this decision (0-1)?
4. Do we need multiple agents working together?

Consider:
- Query complexity and domain
- Required expertise
- Data access needs
- User intent

Respond with your routing decision."""

    def __init__(
        self,
        router_config: Optional[RouterConfig] = None,
        masking_config: Optional[MaskingConfig] = None
    ):
        """Initialize supervisor agent"""
        self.router = SmartLLMRouter(router_config or RouterConfig.from_env())
        self.masking = MultiLevelMaskingEngine(masking_config or MaskingConfig())

        # Agent registry
        self.agents: Dict[AgentType, BaseAgent] = {}

        # Initialize supervisor LLM
        self.supervisor_llm = None
        self._initialize_llm()

        # Build the orchestration graph
        self.graph = None
        self._build_graph()

        logger.info("SupervisorAgent initialized")

    def _initialize_llm(self):
        """Initialize the supervisor LLM"""
        try:
            # Check if we have a valid OpenAI key
            import os
            openai_key = os.environ.get("OPENAI_API_KEY", "")

            if not openai_key or openai_key == "test-key" or openai_key == "test":
                # Use a mock LLM for testing
                logger.warning("No valid OpenAI API key found, using mock LLM")
                self.supervisor_llm = self._create_mock_llm()
            else:
                # Use real OpenAI model
                self.supervisor_llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.3,
                    api_key=openai_key
                ).with_structured_output(AgentRouter)
                logger.info("Supervisor using OpenAI gpt-4o-mini")

        except Exception as e:
            logger.warning(f"Failed to initialize LLM: {e}")
            # Fallback to mock
            self.supervisor_llm = self._create_mock_llm()

    def _create_mock_llm(self):
        """Create a mock LLM for testing without API key"""
        class MockLLM:
            async def ainvoke(self, prompt):
                # Simple rule-based routing for testing
                router = AgentRouter(
                    next_agent="milhena",
                    reasoning="Mock routing based on keywords",
                    confidence=0.8,
                    requires_multiple_agents=False,
                    parallel_agents=None
                )

                # Basic keyword detection
                if isinstance(prompt, str):
                    prompt_lower = prompt.lower()
                    if "messaggio" in prompt_lower or "workflow" in prompt_lower:
                        router.next_agent = "n8n_expert"
                        router.reasoning = "Query contains workflow/message keywords"
                    elif "analisi" in prompt_lower or "report" in prompt_lower:
                        router.next_agent = "data_analyst"
                        router.reasoning = "Query requires data analysis"

                return router

            def invoke(self, prompt):
                return asyncio.create_task(self.ainvoke(prompt))

        return MockLLM()

    def register_agent(self, agent_type: AgentType, agent: BaseAgent):
        """
        Register a specialist agent

        Args:
            agent_type: Type of agent
            agent: Agent instance
        """
        self.agents[agent_type] = agent
        logger.info(f"Registered agent: {agent_type.value}")

    def _build_graph(self):
        """Build the LangGraph orchestration graph"""
        # Create state graph
        graph = StateGraph(SupervisorState)

        # Add nodes
        graph.add_node("analyze_query", self.analyze_query)
        graph.add_node("route_to_agent", self.route_to_agent)
        graph.add_node("execute_agent", self.execute_agent)
        graph.add_node("execute_parallel", self.execute_parallel)  # Added missing node
        graph.add_node("combine_results", self.combine_results)
        graph.add_node("apply_masking", self.apply_masking)
        graph.add_node("handle_error", self.handle_error)

        # Set entry point
        graph.set_entry_point("analyze_query")

        # Add edges
        graph.add_edge("analyze_query", "route_to_agent")

        graph.add_conditional_edges(
            "route_to_agent",
            self.check_routing,
            {
                "single": "execute_agent",
                "parallel": "execute_parallel",
                "error": "handle_error"
            }
        )

        graph.add_edge("execute_agent", "combine_results")
        graph.add_edge("execute_parallel", "combine_results")
        graph.add_edge("combine_results", "apply_masking")
        graph.add_edge("apply_masking", END)
        graph.add_edge("handle_error", END)

        # Compile graph
        self.graph = graph.compile()

        logger.info("Supervisor graph compiled")

    def _quick_classify(self, query: str) -> Optional[AgentType]:
        """
        Quick pattern matching for common queries (bypasses LLM routing)

        Returns:
            AgentType if pattern matches, None for LLM routing fallback
        """
        q = query.lower().strip()

        # GREETING → Milhena (NO LLM)
        greetings = {"ciao", "buongiorno", "buonasera", "salve", "hello", "hi", "hey"}
        if q in greetings:
            return AgentType.MILHENA

        # HELP → Milhena (NO LLM)
        if "cosa puoi fare" in q or "help" in q or "aiuto" in q or "che puoi" in q:
            return AgentType.MILHENA

        # WORKFLOW/ERROR queries → N8nExpert (NO LLM)
        workflow_keywords = ["workflow", "processo", "processi", "esecuzione", "esecuzioni", "messaggio", "errori", "errore", "problemi", "problema", "fallito", "failed"]
        if any(kw in q for kw in workflow_keywords):
            return AgentType.N8N_EXPERT

        # ANALYTICS queries → DataAnalyst (NO LLM)
        analytics_keywords = ["performance", "metriche", "statistiche", "analisi", "andamento", "trend"]
        if any(kw in q for kw in analytics_keywords):
            return AgentType.DATA_ANALYST

        return None  # Fallback to LLM routing

    @traceable(name="SupervisorAnalyzeQuery")
    async def analyze_query(self, state: SupervisorState) -> SupervisorState:
        """Analyze the incoming query with fast-path optimization"""
        query = state.get("query", "")

        # Extract from messages if needed
        if not query and state.get("messages"):
            last_msg = state["messages"][-1]
            query = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
            state["query"] = query

        # Initialize session if needed
        if not state.get("session_id"):
            state["session_id"] = f"supervisor-{datetime.now().timestamp()}"

        # Initialize containers
        state["agent_results"] = {}
        state["metadata"] = {
            "timestamp": datetime.now().isoformat(),
            "query_length": len(query),
            "fast_path": False
        }

        # FAST-PATH: Try quick classification first (bypasses LLM)
        quick_agent = self._quick_classify(query)
        if quick_agent:
            # Create routing decision WITHOUT calling LLM
            state["routing_decision"] = RoutingDecision(
                target_agent=quick_agent,
                reasoning="Fast-path pattern match",
                confidence=0.95,
                parallel_agents=None
            )
            state["current_agent"] = quick_agent.value.lower()
            state["metadata"]["fast_path"] = True
            logger.info(f"[FAST-PATH] Routed to {quick_agent.value} (<50ms, no LLM)")
            return state

        logger.info(f"Analyzing query (LLM routing): {query[:100]}...")
        return state

    @traceable(name="SupervisorRouteToAgent")
    async def route_to_agent(self, state: SupervisorState) -> SupervisorState:
        """Route query to appropriate agent(s)"""
        # CHECK: If fast-path already set routing, skip LLM
        if state.get("metadata", {}).get("fast_path"):
            logger.info("[FAST-PATH] Skipping LLM routing (already decided)")
            return state

        query = state["query"]
        context = state.get("context", {})

        try:
            # Create routing prompt
            prompt = self.SUPERVISOR_PROMPT.format(
                query=query,
                context=context
            )

            # Get routing decision from LLM
            routing: AgentRouter = await self.supervisor_llm.ainvoke(prompt)

            # Create routing decision - normalize agent names
            # Map from OpenAI response to our enum values
            agent_name_map = {
                "milhena": AgentType.MILHENA,
                "n8n_expert": AgentType.N8N_EXPERT,
                "data_analyst": AgentType.DATA_ANALYST,
                "customer": AgentType.CUSTOMER
            }

            # Get the correct agent type
            agent_key = routing.next_agent.lower().replace(" ", "_")
            target_agent = agent_name_map.get(agent_key, AgentType.MILHENA)

            # Handle parallel agents
            parallel_agents = None
            if routing.parallel_agents:
                parallel_agents = []
                for agent in routing.parallel_agents:
                    agent_key = agent.lower().replace(" ", "_")
                    if agent_key in agent_name_map:
                        parallel_agents.append(agent_name_map[agent_key])

            decision = RoutingDecision(
                target_agent=target_agent,
                reasoning=routing.reasoning,
                confidence=routing.confidence,
                parallel_agents=parallel_agents
            )

            state["routing_decision"] = decision
            state["current_agent"] = routing.next_agent

            logger.info(f"Routing to {routing.next_agent} (confidence: {routing.confidence:.2f})")

            # Add routing metadata
            state["metadata"]["routing"] = {
                "agent": routing.next_agent.lower(),
                "confidence": routing.confidence,
                "reasoning": routing.reasoning
            }

            return state

        except Exception as e:
            logger.error(f"Routing error: {e}")
            state["error"] = f"Routing failed: {str(e)}"
            state["current_agent"] = "milhena"  # Default fallback
            return state

    def check_routing(self, state: SupervisorState) -> Literal["single", "parallel", "error"]:
        """Check routing decision"""
        if state.get("error"):
            return "error"

        decision = state.get("routing_decision")
        if decision and decision.parallel_agents:
            return "parallel"

        return "single"

    @traceable(name="SupervisorExecuteAgent")
    async def execute_agent(self, state: SupervisorState) -> SupervisorState:
        """Execute the selected agent"""
        query = state["query"]
        context = state.get("context", {})
        session_id = state["session_id"]

        try:
            # Get agent from routing decision
            routing_decision = state.get("routing_decision")
            if routing_decision:
                agent_type = routing_decision.target_agent
            else:
                # Fallback to default
                agent_type = AgentType.MILHENA

            agent = self.agents.get(agent_type)

            if not agent:
                logger.warning(f"Agent {agent_type.value} not found, using Milhena")
                agent = self.agents.get(AgentType.MILHENA)

            if agent:
                # Execute agent
                result = await agent.execute(
                    query=query,
                    context=context,
                    session_id=session_id
                )

                # Store result
                state["agent_results"][agent_type.value] = result

                # Track tokens and cost
                if result.tokens_used:
                    state["metadata"]["tokens_used"] = result.tokens_used
                if result.cost:
                    state["metadata"]["cost"] = result.cost

                logger.info(f"Agent {agent_type.value} completed: success={result.success}")

            else:
                # No agents available
                state["error"] = "No agents available"

        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            state["error"] = f"Agent execution failed: {str(e)}"

        return state

    @traceable(name="SupervisorCombineResults")
    async def combine_results(self, state: SupervisorState) -> SupervisorState:
        """Combine results from agent(s)"""
        results = state.get("agent_results", {})

        if not results:
            state["final_response"] = "Mi dispiace, non sono riuscito a processare la richiesta."
            return state

        # Get primary result from routing decision
        routing_decision = state.get("routing_decision")
        if routing_decision:
            primary_agent = routing_decision.target_agent.value.lower()
        else:
            primary_agent = "milhena"

        primary_result = results.get(primary_agent)

        if primary_result and primary_result.success:
            # Use primary result
            state["final_response"] = str(primary_result.output)

            # Add metadata
            state["metadata"]["primary_agent"] = primary_agent
            state["metadata"]["processing_time"] = primary_result.processing_time

        else:
            # Try fallback agents
            for agent_name, result in results.items():
                if result.success:
                    state["final_response"] = str(result.output)
                    state["metadata"]["fallback_agent"] = agent_name
                    break
            else:
                state["final_response"] = "Si è verificato un problema nel processare la richiesta."

        return state

    @traceable(name="SupervisorApplyMasking")
    async def apply_masking(self, state: SupervisorState) -> SupervisorState:
        """Apply security masking to final response"""
        response = state.get("final_response", "")

        if response:
            # Apply masking based on user level
            masked_result = self.masking.mask(response)

            state["final_response"] = masked_result.masked

            # Track masking stats
            state["metadata"]["masking"] = {
                "replacements": masked_result.replacements_made,
                "leaks_detected": len(masked_result.leaks_detected)
            }

            logger.info(f"Masking applied: {masked_result.replacements_made} replacements")

        return state

    @traceable(name="SupervisorExecuteParallel")
    async def execute_parallel(self, state: SupervisorState) -> SupervisorState:
        """Execute multiple agents in parallel"""
        decision = state.get("routing_decision")
        if not decision or not decision.parallel_agents:
            state["error"] = "No parallel agents specified"
            return state

        query = state["query"]
        context = state.get("context", {})
        session_id = state["session_id"]

        parallel_tasks = []
        agent_names = []

        try:
            # Create tasks for each parallel agent
            for agent_type in decision.parallel_agents:
                agent = self.agents.get(agent_type)
                if agent:
                    task = agent.execute(
                        query=query,
                        context=context,
                        session_id=session_id
                    )
                    parallel_tasks.append(task)
                    agent_names.append(agent_type.value)
                else:
                    logger.warning(f"Agent {agent_type.value} not found for parallel execution")

            if parallel_tasks:
                # Execute all agents in parallel
                results = await asyncio.gather(*parallel_tasks, return_exceptions=True)

                # Store results
                for agent_name, result in zip(agent_names, results):
                    if isinstance(result, Exception):
                        logger.error(f"Parallel execution error for {agent_name}: {result}")
                        error_result = AgentResult(
                            success=False,
                            output=None,
                            agent_name=agent_name,
                            processing_time=0,
                            error=str(result)
                        )
                        state["agent_results"][agent_name] = error_result
                    else:
                        state["agent_results"][agent_name] = result

                        # Track aggregated metrics
                        if result.tokens_used:
                            current_tokens = state["metadata"].get("tokens_used", 0)
                            state["metadata"]["tokens_used"] = current_tokens + result.tokens_used
                        if result.cost:
                            current_cost = state["metadata"].get("cost", 0)
                            state["metadata"]["cost"] = current_cost + result.cost

                logger.info(f"Parallel execution completed for {len(agent_names)} agents")

                # Set the primary agent as the most confident one
                if decision.target_agent:
                    state["current_agent"] = decision.target_agent.value
                else:
                    state["current_agent"] = agent_names[0] if agent_names else "milhena"
            else:
                state["error"] = "No agents available for parallel execution"

        except Exception as e:
            logger.error(f"Parallel execution error: {e}")
            state["error"] = f"Parallel execution failed: {str(e)}"

        return state

    async def handle_error(self, state: SupervisorState) -> SupervisorState:
        """Handle errors gracefully"""
        error = state.get("error", "Unknown error")

        logger.error(f"Supervisor error: {error}")

        # Create user-friendly error message
        state["final_response"] = (
            "Mi dispiace, si è verificato un problema tecnico. "
            "Riprova tra qualche istante o contatta il supporto."
        )

        # Add error metadata
        state["metadata"]["error"] = error
        state["metadata"]["error_time"] = datetime.now().isoformat()

        return state

    async def process(
        self,
        query: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        user_level: UserLevel = UserLevel.BUSINESS
    ) -> Dict[str, Any]:
        """
        Process a query through the supervisor

        Args:
            query: User query
            session_id: Optional session ID
            context: Optional context
            user_level: User authorization level

        Returns:
            Processing result
        """
        # Update masking config for user level
        self.masking.config.user_level = user_level

        # Prepare initial state
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "query": query,
            "session_id": session_id or f"session-{datetime.now().timestamp()}",
            "context": context or {},
            "agent_results": {},
            "metadata": {}
        }

        try:
            # Run the graph
            result = await self.graph.ainvoke(initial_state)

            return {
                "success": True,
                "response": result.get("final_response", ""),
                "routing": result.get("routing_decision"),
                "metadata": result.get("metadata", {}),
                "session_id": result["session_id"]
            }

        except Exception as e:
            logger.error(f"Supervisor processing error: {e}")
            return {
                "success": False,
                "response": "Si è verificato un errore nel sistema.",
                "error": str(e),
                "session_id": session_id
            }

    def get_status(self) -> Dict[str, Any]:
        """Get supervisor status"""
        return {
            "active": True,
            "registered_agents": list(self.agents.keys()),
            "router_stats": self.router.get_usage_stats() if self.router else {},
            "masking_stats": self.masking.get_stats() if self.masking else {}
        }