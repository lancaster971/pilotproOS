"""
Business Analysis Agents - Multi-agent system for business analysis
Analyzes business processes and provides insights for PilotProOS
"""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
import os
from typing import Dict, Any


class BusinessAnalysisAgents:
    """
    Multi-agent system for analyzing business processes in PilotProOS
    """

    def __init__(self):
        """Initialize the crew with LLM"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0.7,
                api_key=api_key
            )
        else:
            # Will use default or mock
            self.llm = None

    def process_analyst_agent(self):
        """Agent that analyzes business processes"""
        return Agent(
            role="Business Process Analyst",
            goal="Analyze business processes and identify optimization opportunities",
            backstory="""You are an expert in business process analysis with 15 years
            of experience in process optimization. You specialize in identifying
            bottlenecks, inefficiencies, and automation opportunities in business workflows.""",
            verbose=False,
            allow_delegation=False,
            llm=self.llm
        )

    def data_analyst_agent(self):
        """Agent that analyzes business data"""
        return Agent(
            role="Business Data Analyst",
            goal="Extract insights from business data and create meaningful metrics",
            backstory="""You are a data analytics expert who specializes in business
            intelligence. You excel at finding patterns in data and translating them
            into actionable business insights.""",
            verbose=False,
            allow_delegation=False,
            llm=self.llm
        )

    def strategy_advisor_agent(self):
        """Agent that provides strategic recommendations"""
        return Agent(
            role="Strategic Business Advisor",
            goal="Provide strategic recommendations based on analysis",
            backstory="""You are a senior business consultant with expertise in
            digital transformation and process automation. You provide actionable
            recommendations that drive business value.""",
            verbose=False,
            allow_delegation=True,
            llm=self.llm
        )

    def analyze_process_task(self, agent, process_description: str):
        """Task to analyze a specific business process"""
        return Task(
            description=f"""
            Analyze the following business process and identify:
            1. Current inefficiencies and bottlenecks
            2. Automation opportunities
            3. Risk factors
            4. Performance metrics to track

            Process Description: {process_description}

            Provide a detailed analysis with specific findings.
            """,
            expected_output="Detailed process analysis with inefficiencies, opportunities, and metrics",
            agent=agent
        )

    def extract_insights_task(self, agent, data_context: str):
        """Task to extract insights from business data"""
        return Task(
            description=f"""
            Based on the process analysis, extract key business insights:
            1. Performance patterns and trends
            2. Resource utilization analysis
            3. Cost optimization opportunities
            4. Quality improvement areas

            Context: {data_context}

            Focus on actionable insights with quantifiable impact.
            """,
            expected_output="Business insights report with patterns, metrics, and opportunities",
            agent=agent
        )

    def recommend_strategy_task(self, agent):
        """Task to provide strategic recommendations"""
        return Task(
            description="""
            Based on the process analysis and data insights, provide strategic recommendations:
            1. Top 3 immediate actions (quick wins)
            2. Medium-term optimization plan (3-6 months)
            3. Long-term transformation strategy
            4. Expected ROI and business impact
            5. Implementation roadmap

            Make recommendations specific, actionable, and prioritized.
            """,
            expected_output="Strategic recommendations with prioritized actions and implementation roadmap",
            agent=agent
        )

    def analyze_business(self, process_description: str, data_context: str = "") -> Dict[str, Any]:
        """
        Run the business analysis crew

        Args:
            process_description: Description of the business process to analyze
            data_context: Additional data context for analysis

        Returns:
            Analysis results with insights and recommendations
        """
        try:
            # Create agents
            process_analyst = self.process_analyst_agent()
            data_analyst = self.data_analyst_agent()
            strategy_advisor = self.strategy_advisor_agent()

            # Create tasks
            process_task = self.analyze_process_task(process_analyst, process_description)
            insights_task = self.extract_insights_task(data_analyst, data_context or process_description)
            strategy_task = self.recommend_strategy_task(strategy_advisor)

            # Create agent system
            crew = Crew(
                agents=[process_analyst, data_analyst, strategy_advisor],
                tasks=[process_task, insights_task, strategy_task],
                process=Process.sequential,
                verbose=False
            )

            # Execute crew
            result = crew.kickoff()

            return {
                "success": True,
                "analysis": str(result),
                "system": "BusinessAnalysisAgents",
                "agents_used": 3,
                "model": "crewai-multi-agent"
            }

        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "details": traceback.format_exc()
            }


class QuickInsightsAgent:
    """
    Single agent system for quick business insights
    """

    def __init__(self):
        """Initialize the agent system"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0.5,
                api_key=api_key
            )
        else:
            self.llm = None

    def insight_agent(self):
        """Quick insights agent"""
        return Agent(
            role="Business Insights Specialist",
            goal="Provide quick, actionable business insights",
            backstory="""You are a business insights specialist who excels at
            quickly understanding situations and providing immediate, actionable advice.
            You focus on practical solutions that can be implemented quickly.""",
            verbose=False,
            allow_delegation=False,
            llm=self.llm
        )

    def get_insights(self, question: str, context: str = "") -> Dict[str, Any]:
        """
        Get quick insights on a business question

        Args:
            question: Business question or scenario
            context: Additional context

        Returns:
            Quick insights and recommendations
        """
        try:
            agent = self.insight_agent()

            task = Task(
                description=f"""
                Provide quick insights and recommendations for this business question:

                {question}

                {f"Context: {context}" if context else ""}

                Focus on:
                1. Key insight (1-2 sentences)
                2. Top 3 actionable recommendations
                3. Potential risks to consider
                4. Success metrics
                """,
                expected_output="Concise insights with actionable recommendations",
                agent=agent
            )

            crew = Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                verbose=False
            )

            result = crew.kickoff()

            return {
                "success": True,
                "insights": str(result),
                "system": "QuickInsightsAgent",
                "response_type": "quick_analysis"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }