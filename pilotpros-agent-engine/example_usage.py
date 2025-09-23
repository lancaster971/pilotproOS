"""
Example usage of Agent Engine
Shows how to create and run an analysis with our rebranded framework
"""

from agent_engine import AgentEngine, Mission, Process
from agents.business_analyst import create_business_analyst_agent
from agents.process_optimizer import create_process_optimizer_agent
from agents.data_intelligence import create_data_intelligence_agent


def run_process_analysis(process_data):
    """
    Run a complete process analysis using Agent Engine

    Args:
        process_data: Data about the business process to analyze

    Returns:
        Analysis results
    """
    # Create our agents
    business_analyst = create_business_analyst_agent()
    process_optimizer = create_process_optimizer_agent()
    data_intelligence = create_data_intelligence_agent()

    # Define missions (tasks)
    analyze_performance = Mission(
        description=f"""
        Analyze the performance of the business process provided.

        Process Data: {process_data}

        Provide:
        1. Current performance summary
        2. Key performance indicators
        3. Identified bottlenecks
        4. Industry benchmark comparison
        5. Improvement recommendations

        Focus on business impact and ROI potential.
        """,
        agent=business_analyst,
        expected_output="Comprehensive business performance report"
    )

    identify_optimizations = Mission(
        description=f"""
        Based on the performance analysis, identify specific optimization opportunities.

        Focus on:
        1. Process bottlenecks that can be eliminated
        2. Automation opportunities with ROI estimates
        3. Resource reallocation recommendations
        4. Implementation effort and timeline

        Prioritize by potential impact and ease of implementation.
        """,
        agent=process_optimizer,
        expected_output="Prioritized list of optimization opportunities"
    )

    generate_insights = Mission(
        description=f"""
        Extract strategic insights from the data and analysis.

        Provide:
        1. Hidden patterns and correlations
        2. Predictive insights for future performance
        3. Risk factors to monitor
        4. Strategic recommendations

        Present insights in executive-ready format.
        """,
        agent=data_intelligence,
        expected_output="Strategic insights and recommendations"
    )

    # Create the Agent Engine (our rebrand of Crew)
    engine = AgentEngine(
        agents=[business_analyst, process_optimizer, data_intelligence],
        tasks=[analyze_performance, identify_optimizations, generate_insights],
        process=Process.sequential,  # Or Process.hierarchical
        verbose=False,  # Clean output for production
        memory=True,  # Enable memory for context
        max_iter=10  # Maximum iterations
    )

    # Execute the analysis
    result = engine.kickoff()

    return result


if __name__ == "__main__":
    # Example process data
    sample_data = {
        "process_name": "Order Fulfillment",
        "avg_cycle_time": "3.5 days",
        "error_rate": "2.3%",
        "volume": "1000 orders/day",
        "cost_per_transaction": "$45"
    }

    # Run analysis
    print("Starting Agent Engine analysis...")
    result = run_process_analysis(sample_data)
    print("\n=== Analysis Results ===")
    print(result)