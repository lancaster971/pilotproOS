"""Responder v3.5 - LLM synthesis"""
import logging
from langsmith import traceable
from app.utils.state import AgentState

logger = logging.getLogger(__name__)

class Responder:
    def __init__(self, groq_llm=None, openai_llm=None):
        self.groq_llm = groq_llm
        self.openai_llm = openai_llm

    @traceable(name="Responder", run_type="chain", metadata={"version": "3.5.5"})
    async def generate_final_response(self, state: AgentState) -> AgentState:
        tool_results = state.get("tool_results", [])
        if not tool_results:
            state["response"] = "Non ho trovato dati. Riformula la domanda."
            return state
        
        tool_data = "\n\n".join([f"[{r.get('tool')}]\n{r.get('result')}" for r in tool_results])
        prompt = f"Sintetizza in italiano business-friendly:\n\n{tool_data}"
        
        try:
            llm = self.groq_llm or self.openai_llm
            response = await llm.ainvoke(prompt)
            state["response"] = response.content
        except Exception as e:
            logger.error(f"Responder failed: {e}")
            state["response"] = str(tool_results[0].get("result", ""))[:500]
        
        return state
