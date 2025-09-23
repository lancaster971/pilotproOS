"""
Agent Engine - Light rebrand wrapper for CrewAI
Maintains full compatibility for easy upgrades
"""

# Re-export CrewAI components with our naming
from crewai import Agent as BaseAgent
from crewai import Crew as AgentEngine
from crewai import Task as Mission
from crewai import Process
from crewai.project import CrewBase as AgentEngineBase

# Our branded Agent class (thin wrapper)
class Agent(BaseAgent):
    """
    PilotProOS Agent - Extends CrewAI Agent
    Maintains full compatibility while adding our branding
    """
    def __init__(self, *args, **kwargs):
        # Add any custom initialization here if needed
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"<AgentEngine.Agent: {self.role}>"


# Export with our naming conventions
__all__ = [
    'Agent',
    'AgentEngine',
    'Mission',
    'Process',
    'AgentEngineBase'
]


# Convenience factory functions
def create_agent_engine(agents, tasks, **kwargs):
    """
    Create an Agent Engine instance (wrapper for Crew)

    Args:
        agents: List of agents
        tasks: List of missions/tasks
        **kwargs: Additional Crew parameters

    Returns:
        AgentEngine instance
    """
    return AgentEngine(agents=agents, tasks=tasks, **kwargs)


def create_agent(role, goal, backstory, **kwargs):
    """
    Create an Agent instance

    Args:
        role: Agent role
        goal: Agent goal
        backstory: Agent backstory
        **kwargs: Additional Agent parameters

    Returns:
        Agent instance
    """
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        **kwargs
    )


def create_mission(description, agent, **kwargs):
    """
    Create a Mission instance (wrapper for Task)

    Args:
        description: Mission description
        agent: Assigned agent
        **kwargs: Additional Task parameters

    Returns:
        Mission instance
    """
    return Mission(
        description=description,
        agent=agent,
        **kwargs
    )