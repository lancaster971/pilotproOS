"""
Responder v3.5 - LLM synthesis from RAW tool data

Extracted from graph.py:2530-2609 (CONTEXT-SYSTEM.md compliance)
"""
import logging
from langsmith import traceable
from app.agents.v3_5.utils.state import AgentState

logger = logging.getLogger(__name__)


class Responder:
    """
    Responder Component - Synthesizes user-friendly responses from RAW tool data

    Separation of concerns:
    - Tool Execution: ONLY calls tools, returns RAW data
    - Responder: ONLY synthesizes response from tool data
    """

    def __init__(self, groq_llm=None, openai_llm=None):
        self.groq_llm = groq_llm
        self.openai_llm = openai_llm

    @traceable(
        name="MilhenaResponder",
        run_type="chain",
        metadata={"component": "responder", "version": "4.0"}
    )
    async def generate_final_response(self, state: AgentState) -> AgentState:
        """
        v3.5.0 RESPONDER: Synthesizes final user-friendly response from RAW tool data

        Separation of concerns:
        - Tool Execution: ONLY calls tools, returns RAW data in state["tool_results"]
        - Responder: ONLY synthesizes response from tool data
        """
        query = state["query"]
        classification = state.get("supervisor_decision", {}).get("category", "GENERAL")
        tool_results = state.get("tool_results", [])

        logger.info(f"[RESPONDER v3.5.0] Synthesizing response for: {query[:50]}")
        logger.info(f"[RESPONDER v3.5.0] Tool results: {len(tool_results)} tool(s)")

        if not tool_results:
            logger.warning("[RESPONDER] No tool results - generating fallback")
            state["response"] = "Non ho trovato dati specifici. Prova a riformulare la domanda."
            return state

        # Combine all tool data
        tool_data_parts = []
        for result in tool_results:
            tool_name = result.get("tool", "unknown")
            tool_result = result.get("result", "")
            tool_data_parts.append(f"[{tool_name}]\n{tool_result}")

        tool_data_combined = "\n\n".join(tool_data_parts)

        # Build Responder prompt
        responder_prompt = f"""Sei un RESPONSE GENERATOR per Milhena, assistente processi aziendali.

COMPITO: Sintetizza i dati ricevuti dai tools in una risposta user-friendly.

Query utente: "{query}"
Classification: {classification}

Dati tools (RAW):
{tool_data_combined}

REGOLE:
- Italiano chiaro e business-friendly
- Conciso ma completo
- Usa bullet points se ci sono 3+ elementi
- Numeri chiari (es: "145 esecuzioni oggi")
- Se ci sono trend, mostrali (es: "↑ +12% vs ieri")
- NON menzionare "workflow", "execution", "node" - usa linguaggio business

Genera risposta utile basata SOLO sui dati ricevuti."""

        try:
            # Try GROQ first (free + fast) per sintesi
            if self.groq_llm:
                response = await self.groq_llm.ainvoke(responder_prompt)
                final_response = response.content
                logger.info(f"[RESPONDER] GROQ response: {final_response[:100]}")
            else:
                # Fallback OpenAI
                response = await self.openai_llm.ainvoke(responder_prompt)
                final_response = response.content
                logger.info(f"[RESPONDER] OpenAI response: {final_response[:100]}")

            # Apply ResponseFormatter for consistent closing formulas and formatting
            from app.agents.v3_5.utils.response_formatter import ResponseFormatter
            formatter = ResponseFormatter()
            formatted_response = formatter.format(
                response=final_response,
                query=query,
                intent=classification,
                supervisor_decision=state.get("supervisor_decision")
            )

            state["response"] = formatted_response

        except Exception as e:
            logger.error(f"[RESPONDER] Failed: {e}")
            # Fallback: use first tool result as-is
            state["response"] = tool_results[0][:500] if tool_results else "Errore nella generazione della risposta."

        return state
