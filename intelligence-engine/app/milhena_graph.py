"""
Milhena Custom Graph - Multi-Node Security Pipeline
===================================================
Grafo LangGraph con nodi separati visibili in Studio
"""

from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# Import Milhena components
from app.core.hybrid_classifier import HybridClassifier, IntentCategory
from app.core.hybrid_masking import HybridMaskingLibrary
from app.core.hybrid_validator import HybridValidator, ValidationResult
from app.core.simple_audit_logger import SimpleAuditLogger
from app.system_agents.milhena.data_analyst_agent import DataAnalystAgent

# Initialize components
classifier = HybridClassifier()
masking = HybridMaskingLibrary()
validator = HybridValidator()
audit = SimpleAuditLogger()
data_analyst = DataAnalystAgent()


class MilhenaState(TypedDict):
    """State per il grafo Milhena - compatibile con LangSmith"""
    messages: Annotated[list[BaseMessage], add_messages]
    category: str
    confidence: float
    raw_response: str
    masked_response: str
    validation_result: str
    final_response: str


def classify_node(state: MilhenaState) -> MilhenaState:
    """Node 1: Classify user intent"""
    # Estrai query dall'ultimo messaggio
    last_message = state["messages"][-1]
    query = last_message.content if hasattr(last_message, 'content') else str(last_message)

    category, confidence, reasoning = classifier.classify(query, use_llm_fallback=False)

    audit.log_classification(query, category.value, confidence)

    state["category"] = category.value
    state["confidence"] = confidence

    return state


def query_database_node(state: MilhenaState) -> MilhenaState:
    """Node 2: Query database for RAW data"""
    from app.graph import query_users, query_sessions, get_system_status, execute_business_query

    category = state["category"]
    last_message = state["messages"][-1]
    query = last_message.content if hasattr(last_message, 'content') else str(last_message)

    # Converti in stringa se è una lista
    if isinstance(query, list):
        query = str(query)

    if category == "GREETING":
        raw_response = "Greeting request"
    elif category == "BUSINESS_DATA":
        # Query database per dati RAW
        if "utenti" in query.lower():
            raw_response = query_users.invoke({"query_type": "count"})
        elif "sessioni" in query.lower():
            raw_response = query_sessions.invoke({"query_type": "active"})
        elif "nod" in query.lower() or "process" in query.lower() or "workflow" in query.lower():
            raw_response = execute_business_query.invoke({"query": "SELECT COUNT(*) as total FROM pilotpros.business_execution_data"})
        else:
            raw_response = get_system_status.invoke({})
    elif category == "HELP":
        raw_response = "Help request"
    else:
        raw_response = "Unknown request"

    state["raw_response"] = raw_response
    return state


def data_analyst_node(state: MilhenaState) -> MilhenaState:
    """Node 3: Data Analyst elabora dati RAW in risposta business"""
    category = state["category"]
    last_message = state["messages"][-1]
    query = last_message.content if hasattr(last_message, 'content') else str(last_message)

    # Converti in stringa se è una lista
    if isinstance(query, list):
        query = str(query)

    raw_data = state["raw_response"]

    if category == "GREETING":
        business_response = "Ciao! Come posso aiutarti con i dati aziendali?"
    elif category == "HELP":
        business_response = "Posso aiutarti a consultare: utenti, sessioni, stato sistema"
    elif category == "BUSINESS_DATA":
        # USA LLM per elaborare risposta concisa e business-friendly
        business_response = data_analyst.analyze(query, raw_data)
    else:
        business_response = "Non ho compreso la richiesta"

    state["raw_response"] = business_response
    return state


def masking_node(state: MilhenaState) -> MilhenaState:
    """Node 5: Mask technical terms and return final AIMessage"""
    raw = state["raw_response"]
    masked = masking.mask(raw)

    audit.log_masking(raw[:50], 1)

    # IMPORTANTE: Restituisci AIMessage per LangSmith chat
    state["masked_response"] = masked
    state["final_response"] = masked
    state["messages"].append(AIMessage(content=masked))

    return state


def validation_node(state: MilhenaState) -> MilhenaState:
    """Node 4: Validate response"""
    business_response = state["raw_response"]
    report = validator.validate(business_response, use_llm_fallback=False)

    audit.log_validation(business_response[:100], report.result.value, len(report.issues))

    state["validation_result"] = report.result.value

    if report.result == ValidationResult.VALID:
        state["raw_response"] = business_response
    else:
        state["raw_response"] = f"Risposta richiede revisione: {report.suggestions[0] if report.suggestions else 'Contatta supporto'}"

    return state


def generate_simple_response_node(state: MilhenaState) -> MilhenaState:
    """Node per risposte semplici (GREETING/HELP/TECHNOLOGY)"""
    category = state["category"]

    if category == "GREETING":
        response = "Ciao! Come posso aiutarti con i dati aziendali?"
    elif category == "HELP":
        response = "Posso aiutarti a consultare: utenti, sessioni, stato del sistema."
    elif category == "TECHNOLOGY":
        response = "Per informazioni tecniche, contatta il supporto IT."
    else:
        response = "Mi dispiace, non ho compreso la richiesta."

    state["final_response"] = response
    state["messages"].append(AIMessage(content=response))

    return state


def route_after_classifier(state: MilhenaState) -> str:
    """Routing function dopo classifier"""
    category = state["category"]

    if category == "BUSINESS_DATA":
        return "database_query"
    else:
        return "simple_response"


# Create Milhena graph
workflow = StateGraph(MilhenaState)

# Add nodes secondo architettura documento (righe 62-68)
workflow.add_node("classifier", classify_node)
workflow.add_node("simple_response", generate_simple_response_node)
workflow.add_node("database_query", query_database_node)
workflow.add_node("data_analyst", data_analyst_node)
workflow.add_node("validator", validation_node)
workflow.add_node("masking", masking_node)

# ROUTING CONDIZIONALE come da documento
workflow.set_entry_point("classifier")

# Classifier fa routing
workflow.add_conditional_edges(
    "classifier",
    route_after_classifier,
    {
        "simple_response": "simple_response",
        "database_query": "database_query"
    }
)

# Simple response va direttamente a END
workflow.add_edge("simple_response", END)

# Business data passa per pipeline completa
workflow.add_edge("database_query", "data_analyst")
workflow.add_edge("data_analyst", "validator")
workflow.add_edge("validator", "masking")
workflow.add_edge("masking", END)

# Compile graph
graph = workflow.compile()
graph.name = "Milhena Security Pipeline"


# Export also as invokable function for ReAct agent
def invoke_milhena(query: str) -> str:
    """
    Invoke Milhena pipeline with a user query

    Args:
        query: User query string

    Returns:
        Final response after Milhena pipeline
    """
    initial_state = {
        "query": query,
        "category": "",
        "confidence": 0.0,
        "raw_response": "",
        "masked_response": "",
        "validation_result": "",
        "final_response": "",
        "messages": [HumanMessage(content=query)]
    }

    result = graph.invoke(initial_state)
    return result.get("final_response", "Errore nel processamento")