"""
Data Intelligence Agent - Part of PilotProOS Agent Engine
Transforms complex data into actionable business insights
"""

from agent_engine import Agent
from typing import List, Dict, Any


def create_data_intelligence_agent(tools: List = None, llm=None) -> Agent:
    """
    Create a Data Intelligence Specialist agent

    This agent specializes in:
    - Interpreting complex datasets
    - Pattern and anomaly detection
    - Correlation analysis
    - Predictive insight generation

    Args:
        tools: List of tools available to the agent
        llm: Language model to use

    Returns:
        Configured Data Intelligence agent
    """
    return Agent(
        role="Business Data Intelligence Specialist",
        goal="Transform complex data patterns into clear, actionable business insights that drive strategic decisions",
        backstory="""You are a data intelligence specialist with expertise in
        advanced analytics and business intelligence. You've helped organizations
        uncover hidden insights in their data that led to breakthrough improvements.
        You excel at finding meaningful patterns in noise, detecting anomalies that
        matter, and translating complex statistical findings into clear business
        language that executives can act upon.""",
        tools=tools or [],
        llm=llm,
        verbose=False,
        allow_delegation=True,
        max_iter=5,
        memory=True
    )


def create_pattern_recognition_expert() -> Agent:
    """
    Create Pattern Recognition Expert agent

    Focuses on:
    - Trend identification
    - Anomaly detection
    - Predictive pattern analysis
    """
    return Agent(
        role="Pattern Recognition and Trend Expert",
        goal="Identify meaningful patterns and trends that predict future business outcomes",
        backstory="""You are a pattern recognition expert with deep expertise in
        time series analysis and predictive modeling. You have successfully predicted
        market trends, customer behavior patterns, and operational anomalies that
        saved companies from significant losses. Your pattern detection has enabled
        proactive decision-making across industries.""",
        verbose=False,
        allow_delegation=False,
        max_iter=3
    )


def create_insight_synthesizer() -> Agent:
    """
    Create Insight Synthesizer agent

    Focuses on:
    - Cross-functional data correlation
    - Insight prioritization
    - Recommendation synthesis
    """
    return Agent(
        role="Business Insight Synthesizer",
        goal="Synthesize data findings into prioritized, actionable business recommendations",
        backstory="""You are an insight synthesizer who excels at connecting dots
        across different data sources and business functions. You have a talent for
        identifying which insights matter most and presenting them in ways that
        drive immediate action. Your synthesized recommendations have guided
        multi-million dollar business decisions.""",
        verbose=False,
        allow_delegation=False,
        max_iter=4
    )