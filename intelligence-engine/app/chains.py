"""
LangChain Chains for Business Intelligence
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain.chains import ConversationChain, RetrievalQA
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from typing import List, Any, Dict
import json

def create_business_chain(llm, memory, tools: List[Tool] = None, streaming: bool = False):
    """
    Create a business intelligence chain with tools and memory
    """

    # Business-focused system prompt
    system_prompt = """You are an intelligent business assistant for PilotProOS.
    You help users understand their business processes, analyze workflow data, and provide insights.

    Key responsibilities:
    1. Answer questions about business processes and workflows
    2. Analyze performance metrics and provide insights
    3. Help optimize business operations
    4. Provide data-driven recommendations

    Always use business terminology instead of technical terms:
    - "workflow" → "business process"
    - "execution" → "process run"
    - "node" → "process step"
    - "webhook" → "integration endpoint"

    When using tools, explain what you're doing in business terms.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad", optional=True)
    ])

    if tools:
        # Create agent with tools
        agent = create_openai_functions_agent(
            llm=llm,
            tools=tools,
            prompt=prompt
        )

        chain = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            return_intermediate_steps=True,
            max_iterations=5,
            handle_parsing_errors=True
        )

    else:
        # Simple conversation chain without tools
        chain = ConversationChain(
            llm=llm,
            memory=memory,
            prompt=prompt,
            verbose=True
        )

    # Add streaming support
    if streaming:
        return chain.with_config({"streaming": True})

    return chain

def create_analysis_chain(llm, vectorstore):
    """
    Create an analysis chain with RAG capabilities
    """

    # Analysis prompt template
    analysis_prompt = ChatPromptTemplate.from_template("""
    Analyze the following business data and provide insights:

    Query: {query}
    Data Source: {data_source}
    Time Range: {time_range}

    Relevant Context:
    {context}

    Please provide:
    1. Key findings and patterns
    2. Performance metrics analysis
    3. Actionable recommendations
    4. Potential optimizations

    Format your response as structured JSON with the following keys:
    - analysis: Main analysis text
    - insights: List of key insights
    - recommendations: List of actionable recommendations
    - confidence: Confidence score (0-1)
    """)

    # Create retrieval chain
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )

    # Build the chain
    chain = (
        RunnableParallel({
            "context": retriever,
            "query": RunnablePassthrough(),
            "data_source": RunnablePassthrough(),
            "time_range": RunnablePassthrough()
        })
        | analysis_prompt
        | llm
        | JsonOutputParser()
    )

    return chain

def create_workflow_optimization_chain(llm):
    """
    Chain for workflow optimization recommendations
    """

    optimization_prompt = ChatPromptTemplate.from_template("""
    As a business process optimization expert, analyze the following workflow:

    Workflow Name: {workflow_name}
    Current Performance: {performance_metrics}
    Recent Issues: {issues}

    Provide optimization recommendations including:
    1. Bottleneck identification
    2. Process improvement suggestions
    3. Automation opportunities
    4. Cost reduction strategies
    5. Risk mitigation measures

    Be specific and actionable in your recommendations.
    """)

    chain = optimization_prompt | llm | StrOutputParser()

    return chain

def create_metric_monitoring_chain(llm):
    """
    Chain for monitoring and alerting on business metrics
    """

    monitoring_prompt = ChatPromptTemplate.from_template("""
    Monitor the following business metrics and identify any anomalies or trends:

    Metrics Data: {metrics}
    Baseline: {baseline}
    Time Period: {period}

    Analyze and report:
    1. Significant deviations from baseline
    2. Emerging trends (positive or negative)
    3. Predictive insights
    4. Alert priority level (low/medium/high/critical)
    5. Recommended actions

    Format as JSON with keys: anomalies, trends, predictions, alert_level, actions
    """)

    chain = monitoring_prompt | llm | JsonOutputParser()

    return chain

def create_document_qa_chain(llm, vectorstore):
    """
    Chain for Q&A over business documents
    """

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
        return_source_documents=True,
        verbose=True
    )

    return qa_chain

def create_report_generation_chain(llm):
    """
    Chain for generating business reports
    """

    report_prompt = ChatPromptTemplate.from_template("""
    Generate a comprehensive business report based on the following data:

    Report Type: {report_type}
    Data: {data}
    Period: {period}
    Requested Sections: {sections}

    Create a professional report including:
    1. Executive Summary
    2. Key Performance Indicators
    3. Detailed Analysis
    4. Trends and Patterns
    5. Recommendations
    6. Conclusion

    Use clear business language and include specific metrics where available.
    """)

    chain = report_prompt | llm | StrOutputParser()

    return chain