"""
Process Optimizer Agent - Part of PilotProOS Agent Teams
Identifies inefficiencies and recommends process improvements
"""

from crewai import Agent
from typing import List, Dict, Any


def create_process_optimizer_agent(tools: List = None, llm=None) -> Agent:
    """
    Create a Process Optimization Expert agent

    This agent specializes in:
    - Identifying bottlenecks in workflows
    - Analyzing automation opportunities
    - Resource optimization recommendations
    - Implementation effort estimation

    Args:
        tools: List of tools available to the agent
        llm: Language model to use

    Returns:
        Configured Process Optimizer agent
    """
    return Agent(
        role="Business Process Optimization Expert",
        goal="Identify inefficiencies and recommend actionable process improvements with clear implementation paths",
        backstory="""You are a process optimization expert with deep expertise in
        Lean Six Sigma and business workflow analysis. You've helped hundreds of
        organizations streamline their operations, reducing cycle times by 40-60%
        and cutting operational costs by millions. You excel at identifying hidden
        bottlenecks, suggesting practical automation opportunities, and providing
        realistic implementation roadmaps.""",
        tools=tools or [],
        llm=llm,
        verbose=False,
        allow_delegation=True,
        max_iter=5,
        memory=True
    )


def create_automation_specialist() -> Agent:
    """
    Create Automation Specialist agent

    Focuses on:
    - Automation opportunity assessment
    - Technology stack recommendations
    - Integration planning
    """
    return Agent(
        role="Automation and Integration Specialist",
        goal="Identify and prioritize automation opportunities that maximize ROI",
        backstory="""You are an automation specialist who understands both business
        processes and technology. You have implemented automation solutions that
        have saved companies thousands of hours annually. You excel at finding the
        right balance between automation complexity and business value.""",
        verbose=False,
        allow_delegation=False,
        max_iter=3
    )


def create_efficiency_analyst() -> Agent:
    """
    Create Efficiency Analyst agent

    Focuses on:
    - Time and motion studies
    - Resource utilization analysis
    - Waste identification and elimination
    """
    return Agent(
        role="Operational Efficiency Analyst",
        goal="Analyze operational efficiency and identify waste elimination opportunities",
        backstory="""You are an efficiency expert trained in Toyota Production System
        and modern operational excellence methodologies. You have a keen eye for
        identifying waste in all its forms - waiting, overproduction, unnecessary
        movement, defects, and more. Your recommendations consistently deliver
        20-30% efficiency gains.""",
        verbose=False,
        allow_delegation=False,
        max_iter=4
    )