"""
Business Analyst Agent - Part of PilotProOS Agent Teams
Analyzes business processes and identifies optimization opportunities
"""

from crewai import Agent
from typing import List, Dict, Any


def create_business_analyst_agent(tools: List = None, llm=None) -> Agent:
    """
    Create a Business Analyst agent for process analysis

    This agent specializes in:
    - Performance analysis of business processes
    - KPI calculation and interpretation
    - ROI assessment and business impact
    - Strategic recommendation generation

    Args:
        tools: List of tools available to the agent
        llm: Language model to use

    Returns:
        Configured Business Analyst agent
    """
    return Agent(
        role="Senior Business Performance Analyst",
        goal="Analyze business processes and identify optimization opportunities that deliver measurable ROI",
        backstory="""You are a senior business analyst with 15+ years of experience
        in process optimization and KPI analysis. You have worked with Fortune 500
        companies to transform their operations, consistently delivering 20-30%
        efficiency improvements. You understand both operational efficiency and
        strategic business impact, always focusing on data-driven insights that
        translate to bottom-line results.""",
        tools=tools or [],
        llm=llm,
        verbose=False,  # Clean output for production
        allow_delegation=True,
        max_iter=5,
        memory=True
    )


def create_business_metrics_analyst() -> Agent:
    """
    Create specialized Business Metrics Analyst

    Focuses on:
    - Financial metrics and ROI calculation
    - Performance benchmarking
    - Trend analysis and forecasting
    """
    return Agent(
        role="Business Metrics Specialist",
        goal="Calculate and interpret key business metrics to drive data-informed decisions",
        backstory="""You are a metrics specialist who excels at translating complex
        data into clear business insights. You have expertise in financial analysis,
        statistical modeling, and predictive analytics. Your recommendations have
        helped companies save millions through precise metric-driven optimizations.""",
        verbose=False,
        allow_delegation=False,
        max_iter=3
    )


def create_strategic_advisor() -> Agent:
    """
    Create Strategic Business Advisor

    Focuses on:
    - Long-term strategic planning
    - Market positioning analysis
    - Competitive advantage identification
    """
    return Agent(
        role="Strategic Business Advisor",
        goal="Provide strategic recommendations aligned with business objectives and market dynamics",
        backstory="""You are a strategic advisor with experience at top consulting
        firms. You specialize in identifying strategic opportunities that create
        sustainable competitive advantages. Your insights help businesses navigate
        complex market conditions and achieve long-term growth.""",
        verbose=False,
        allow_delegation=True,
        max_iter=4
    )