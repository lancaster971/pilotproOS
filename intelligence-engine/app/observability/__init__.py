"""
Monitoring and Observability Module for PilotProOS Intelligence Engine
Production-ready metrics with Prometheus and Grafana
"""

from .observability import (
    # Decorators
    track_agent_execution,
    track_langgraph_node,
    track_graph_execution,

    # Tracking functions
    track_token_usage,
    track_routing_decision,
    track_n8n_operation,
    track_rag_operation,
    track_api_request,
    track_business_value,

    # System functions
    update_system_health,
    setup_monitoring_server,
    get_current_metrics,
    initialize_monitoring,

    # Export functions
    export_grafana_dashboard,
    export_alert_rules,

    # Metrics (for direct access if needed)
    agent_requests_total,
    agent_response_time,
    agent_tokens_used,
    agent_cost_total,
    langgraph_nodes_executed,
    langgraph_graph_executions,
    langgraph_graph_duration,
    router_decisions,
    router_savings,
    n8n_workflows_queried,
    n8n_messages_extracted,
    rag_searches,
    rag_documents_processed,
    embedding_cache_hits,
    system_health,
    active_sessions,
    database_connections,
    redis_memory_used,
    errors_total,
    api_requests,
    api_latency,
    business_value_generated
)

__all__ = [
    # Main functions
    'initialize_monitoring',
    'setup_monitoring_server',
    'get_current_metrics',
    'update_system_health',

    # Decorators
    'track_agent_execution',
    'track_langgraph_node',
    'track_graph_execution',

    # Tracking functions
    'track_token_usage',
    'track_routing_decision',
    'track_n8n_operation',
    'track_rag_operation',
    'track_api_request',
    'track_business_value',

    # Export functions
    'export_grafana_dashboard',
    'export_alert_rules',
]