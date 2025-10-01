"""
Graph Supervisor Configuration
==============================
Configures and initializes the supervisor with ALL REAL agents
NO MOCK DATA - REAL AGENTS WITH REAL LLMs
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.agents.supervisor import SupervisorAgent, AgentType
from app.agents.milhena_enhanced_llm import EnhancedMilhenaAgent
from app.agents.n8n_expert_llm import N8nExpertAgent
from app.agents.data_analyst_llm import DataAnalystAgent
from app.core.router import RouterConfig
from app.security.masking_engine import MaskingConfig
from app.tools.n8n_message_tools import n8n_message_tools
from app.rag.maintainable_rag import get_rag_system
from app.cache.optimized_embeddings_cache import get_embeddings_cache

logger = logging.getLogger(__name__)


class GraphSupervisor:
    """
    Main orchestrator that configures and manages the multi-agent system
    Registers all REAL agents with proper routing
    """

    def __init__(
        self,
        use_real_llms: bool = True,
        router_config: Optional[RouterConfig] = None,
        masking_config: Optional[MaskingConfig] = None
    ):
        """
        Initialize the graph supervisor with all agents

        Args:
            use_real_llms: Whether to use real LLMs (requires API keys)
            router_config: Router configuration for token optimization
            masking_config: Security masking configuration
        """
        self.use_real_llms = use_real_llms
        self.agents_registry = {}
        self.tools_registry = {}

        # Initialize core systems
        self._initialize_core_systems()

        # Initialize supervisor
        logger.info("Initializing Supervisor Agent...")
        self.supervisor = SupervisorAgent(
            router_config=router_config or RouterConfig.from_env(),
            masking_config=masking_config or MaskingConfig()
        )

        # Register all REAL agents
        self._register_all_agents()

        # Configure routing rules
        self._configure_routing_rules()

        logger.info("GraphSupervisor initialized successfully")

    def _initialize_core_systems(self):
        """Initialize core systems (RAG, Cache, Tools)"""
        try:
            # Initialize RAG system
            logger.info("Initializing RAG system...")
            self.rag_system = get_rag_system()

            # Initialize embeddings cache
            logger.info("Initializing embeddings cache...")
            self.embeddings_cache = get_embeddings_cache()

            # Initialize n8n tools
            logger.info("Initializing n8n message tools...")
            self.n8n_tools = n8n_message_tools
            self.tools_registry["n8n_tools"] = self.n8n_tools

            logger.info("Core systems initialized")

        except Exception as e:
            # Handle expected "already exists" from concurrent RAG initialization
            if "already exists" in str(e).lower():
                logger.info(f"ℹ️ RAG collection already initialized (expected in multi-instance setup)")
                # RAG system is still functional, don't set to None
                self.rag_system = get_rag_system()
                self.embeddings_cache = get_embeddings_cache()
            else:
                # Unexpected error, log and disable systems
                logger.error(f"Failed to initialize core systems: {e}")
                self.rag_system = None
                self.embeddings_cache = None

    def _register_all_agents(self):
        """Register all REAL agents with the supervisor"""

        # Check for API keys
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        has_valid_openai = openai_key and openai_key not in ["test-key", "test", ""]

        if not has_valid_openai and self.use_real_llms:
            logger.warning("No valid OpenAI API key found. Agents may use fallback models.")

        try:
            # 1. Register Enhanced Milhena Agent (General Assistant)
            logger.info("Registering Enhanced Milhena Agent...")
            milhena_agent = EnhancedMilhenaAgent()
            self.supervisor.register_agent(AgentType.MILHENA, milhena_agent)
            self.agents_registry[AgentType.MILHENA] = {
                "agent": milhena_agent,
                "description": "General business assistant - Italian responses",
                "capabilities": [
                    "General queries",
                    "Greetings and conversation",
                    "Status checks",
                    "Default fallback"
                ],
                "model": "gpt-4o-mini",
                "cost_per_query": "$0.000004-$0.000010"
            }

            # 2. Register N8n Expert Agent (Workflow Specialist)
            logger.info("Registering N8n Expert Agent...")
            n8n_agent = N8nExpertAgent()  # N8n tools are already initialized internally
            self.supervisor.register_agent(AgentType.N8N_EXPERT, n8n_agent)
            self.agents_registry[AgentType.N8N_EXPERT] = {
                "agent": n8n_agent,
                "description": "n8n workflow and message extraction specialist",
                "capabilities": [
                    "Workflow analysis",
                    "Message extraction",
                    "Execution monitoring",
                    "n8n configuration"
                ],
                "model": "gpt-4o-mini",
                "cost_per_query": "$0.000013-$0.000016"
            }

            # 3. Register Data Analyst Agent (Analytics & Reporting)
            logger.info("Registering Data Analyst Agent...")
            analyst_agent = DataAnalystAgent()
            self.supervisor.register_agent(AgentType.DATA_ANALYST, analyst_agent)
            self.agents_registry[AgentType.DATA_ANALYST] = {
                "agent": analyst_agent,
                "description": "Data analysis and reporting specialist",
                "capabilities": [
                    "Performance metrics",
                    "Trend analysis",
                    "Report generation",
                    "Data visualization"
                ],
                "model": "gpt-4o-mini",
                "cost_per_query": "$0.000024-$0.000033"
            }

            # Log registration summary
            logger.info(f"Successfully registered {len(self.agents_registry)} agents:")
            for agent_type, info in self.agents_registry.items():
                logger.info(f"  - {agent_type.value}: {info['description']}")

        except Exception as e:
            logger.error(f"Error registering agents: {e}", exc_info=True)
            raise

    def _configure_routing_rules(self):
        """Configure advanced routing rules for the supervisor"""

        # Define routing keywords and patterns
        self.routing_rules = {
            AgentType.N8N_EXPERT: {
                "keywords": [
                    "workflow", "messaggio", "message", "execution",
                    "n8n", "webhook", "trigger", "node", "automazione"
                ],
                "patterns": [
                    r"workflow.*\d+",  # workflow with ID
                    r"execution.*failed",  # execution errors
                    r"messag\w+.*workflow",  # messages in workflow
                ],
                "confidence_boost": 0.2  # Boost confidence when matched
            },
            AgentType.DATA_ANALYST: {
                "keywords": [
                    "analisi", "report", "metriche", "statistiche",
                    "performance", "trend", "dati", "grafico", "dashboard"
                ],
                "patterns": [
                    r"analy[sz]e.*data",
                    r"report.*generat",
                    r"show.*metrics",
                    r"performance.*last.*\d+"
                ],
                "confidence_boost": 0.15
            },
            AgentType.MILHENA: {
                "keywords": [
                    "ciao", "hello", "aiuto", "help", "cosa",
                    "come", "stato", "status", "info"
                ],
                "patterns": [
                    r"^(ciao|hello|hi|salve)",
                    r"come.*stai",
                    r"cosa.*puoi.*fare"
                ],
                "confidence_boost": 0.1
            }
        }

        # Configure fallback chain
        self.fallback_chain = [
            AgentType.MILHENA,  # Primary fallback
            AgentType.DATA_ANALYST,  # Secondary fallback
            AgentType.N8N_EXPERT  # Last resort
        ]

        logger.info("Routing rules configured")

    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        user_level: str = "business"
    ) -> Dict[str, Any]:
        """
        Process a query through the supervisor

        Args:
            query: User query
            session_id: Session identifier
            context: Additional context
            user_level: User authorization level

        Returns:
            Processing result with response and metadata
        """
        try:
            # Convert user level string to enum
            from app.security.masking_engine import UserLevel
            level_map = {
                "business": UserLevel.BUSINESS,
                "admin": UserLevel.ADMIN,
                "developer": UserLevel.DEVELOPER
            }
            user_level_enum = level_map.get(user_level.lower(), UserLevel.BUSINESS)

            # Add routing hints to context based on patterns
            if context is None:
                context = {}

            # Check routing rules for hints
            routing_hints = []
            query_lower = query.lower()

            for agent_type, rules in self.routing_rules.items():
                # Check keywords
                for keyword in rules.get("keywords", []):
                    if keyword in query_lower:
                        routing_hints.append({
                            "agent": agent_type.value.lower(),
                            "reason": f"keyword '{keyword}' detected",
                            "boost": rules["confidence_boost"]
                        })
                        break

            if routing_hints:
                context["routing_hints"] = routing_hints
                logger.info(f"Routing hints: {routing_hints}")

            # Process through supervisor
            result = await self.supervisor.process(
                query=query,
                session_id=session_id,
                context=context,
                user_level=user_level_enum
            )

            # Add system metadata
            result["metadata"] = result.get("metadata", {})
            result["metadata"]["graph_version"] = "1.0.0"
            result["metadata"]["agents_available"] = len(self.agents_registry)
            result["metadata"]["timestamp"] = datetime.now().isoformat()

            return result

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                "success": False,
                "response": "Si è verificato un errore nel processare la richiesta.",
                "error": str(e),
                "metadata": {
                    "error_type": type(e).__name__,
                    "timestamp": datetime.now().isoformat()
                }
            }

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status

        Returns:
            System status including agents, tools, and core systems
        """
        status = {
            "supervisor": self.supervisor.get_status() if self.supervisor else None,
            "agents": {},
            "tools": {},
            "core_systems": {},
            "routing_rules": len(self.routing_rules),
            "timestamp": datetime.now().isoformat()
        }

        # Add agent status
        for agent_type, info in self.agents_registry.items():
            status["agents"][agent_type.value] = {
                "registered": True,
                "description": info["description"],
                "model": info["model"],
                "capabilities_count": len(info["capabilities"])
            }

        # Add tool status
        status["tools"]["n8n_tools"] = self.n8n_tools is not None

        # Add core system status
        status["core_systems"]["rag_system"] = self.rag_system is not None
        status["core_systems"]["embeddings_cache"] = self.embeddings_cache is not None

        # Calculate health score
        total_components = len(self.agents_registry) + 2  # agents + core systems
        active_components = len(self.agents_registry)
        if self.rag_system:
            active_components += 1
        if self.embeddings_cache:
            active_components += 1

        status["health_score"] = f"{(active_components / total_components) * 100:.0f}%"

        return status

    def get_agent_capabilities(self) -> Dict[str, Any]:
        """
        Get detailed capabilities of all agents

        Returns:
            Detailed agent capabilities and costs
        """
        capabilities = {
            "total_agents": len(self.agents_registry),
            "agents": {},
            "total_capabilities": 0,
            "estimated_costs": {}
        }

        for agent_type, info in self.agents_registry.items():
            capabilities["agents"][agent_type.value] = {
                "description": info["description"],
                "capabilities": info["capabilities"],
                "model": info["model"],
                "cost_range": info["cost_per_query"]
            }
            capabilities["total_capabilities"] += len(info["capabilities"])

        # Calculate estimated monthly costs (assuming 1000 queries per agent)
        capabilities["estimated_costs"]["per_1000_queries"] = {
            "milhena": "$4-$10",
            "n8n_expert": "$13-$16",
            "data_analyst": "$24-$33",
            "total_max": "$59"
        }

        return capabilities


# Singleton instance
_graph_supervisor = None

def get_graph_supervisor(
    use_real_llms: bool = True,
    force_new: bool = False
) -> GraphSupervisor:
    """
    Get or create singleton graph supervisor

    Args:
        use_real_llms: Whether to use real LLMs
        force_new: Force creation of new instance

    Returns:
        GraphSupervisor instance
    """
    global _graph_supervisor

    if _graph_supervisor is None or force_new:
        logger.info("Creating new GraphSupervisor instance...")
        _graph_supervisor = GraphSupervisor(use_real_llms=use_real_llms)

    return _graph_supervisor


# Export main components
__all__ = [
    "GraphSupervisor",
    "get_graph_supervisor"
]