"""
Milhena Simple Graph for LangGraph Studio
Versione semplificata senza dipendenze complesse
"""
from typing import TypedDict, List, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
import os

# Simple state
class MilhenaState(TypedDict):
    """Stato semplice per Milhena"""
    messages: Annotated[List[BaseMessage], add_messages]

# Create graph
def create_milhena_simple():
    """Crea un grafo semplice per LangGraph Studio"""

    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY", "dummy-key")
    )

    # Define nodes
    async def process_message(state: MilhenaState) -> MilhenaState:
        """Processa il messaggio con Milhena"""
        messages = state["messages"]

        # Add system prompt
        system_msg = "Sei Milhena, un assistente business professionale. Rispondi in italiano."

        # Process with LLM
        response = llm.invoke([
            {"role": "system", "content": system_msg},
            *messages
        ])

        return {"messages": [response]}

    # Build graph
    graph = StateGraph(MilhenaState)
    graph.add_node("milhena", process_message)
    graph.set_entry_point("milhena")
    graph.add_edge("milhena", END)

    return graph.compile()

# Export for LangGraph Studio
graph = create_milhena_simple()

print("✅ Milhena Simple Graph loaded!")