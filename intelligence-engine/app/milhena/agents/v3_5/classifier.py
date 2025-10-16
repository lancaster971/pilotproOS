"""
Classifier v3.5 - Conservative Reasoning

Fast-Path + LLM classification with explicit 1-word rule.
"""
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable
import logging
import json
import re
import time

from app.milhena.utils.state import SupervisorDecision, MilhenaState

logger = logging.getLogger(__name__)

CLASSIFIER_PROMPT = """# Ruolo
Sei Milhena, assistente PilotProOS. Classifica query in 9 categorie.

# Categorie
1. PROCESS_LIST 2. PROCESS_DETAIL 3. EXECUTION_QUERY 4. ERROR_ANALYSIS
5. ANALYTICS 6. STEP_DETAIL 7. EMAIL_ACTIVITY 8. PROCESS_ACTION 9. SYSTEM_OVERVIEW

**Regola**: Query 1 parola senza oggetto = CLARIFICATION_NEEDED

# Output JSON
{{"category": "X", "confidence": 0.8, "reasoning": "...", "params": {{}}}}

Query: "{query}"
Data: {current_date}
"""

class Classifier:
    def __init__(self, learning_system, cache_manager, supervisor_llm, db_pool, system_context_cache=None, cache_ttl=300):
        self.learning_system = learning_system
        self.cache_manager = cache_manager
        self.supervisor_llm = supervisor_llm
        self.db_pool = db_pool
        self._system_context_cache = system_context_cache or ""
        self._cache_timestamp = 0
        self._cache_ttl = cache_ttl

    @traceable(name="Classifier", run_type="chain", metadata={"version": "3.5.5"})
    async def classify(self, state: MilhenaState) -> MilhenaState:
        query = state["query"]
        instant = self._instant_classify(query)
        if instant:
            decision = SupervisorDecision(**instant)
            state["supervisor_decision"] = decision.model_dump()
            state["waiting_clarification"] = False
            if decision.direct_response:
                state["response"] = decision.direct_response
            state["intent"] = {"DANGER": "SECURITY", "GREETING": "GENERAL"}.get(decision.category, "GENERAL")
            return state

        # LLM Classification
        from datetime import datetime
        prompt = CLASSIFIER_PROMPT.format(query=query, current_date=datetime.now().strftime("%Y-%m-%d"))
        messages = [SystemMessage(content=prompt), HumanMessage(content=query)]
        
        try:
            response = await self.supervisor_llm.ainvoke(messages)
            classification = json.loads(response.content)
        except:
            classification = {"category": "CLARIFICATION_NEEDED", "confidence": 0.5, "reasoning": "Fallback"}
        
        classification["llm_used"] = "openai-4.1-nano"
        decision_obj = SupervisorDecision(**{
            "action": "react",
            "category": classification.get("category", "SIMPLE_QUERY"),
            "confidence": classification.get("confidence", 0.7),
            "reasoning": classification.get("reasoning", ""),
            "needs_database": True,
            "llm_used": classification["llm_used"]
        })
        state["supervisor_decision"] = decision_obj.model_dump()
        state["waiting_clarification"] = (decision_obj.category == "CLARIFICATION_NEEDED")
        state["intent"] = "GENERAL"
        return state

    def _instant_classify(self, query: str) -> Optional[Dict[str, Any]]:
        q = query.lower().strip()
        danger_kw = ["password", "credential", "api key", "secret", "postgres", "docker", "n8n"]
        if any(kw in q for kw in danger_kw):
            return {"action": "respond", "category": "DANGER", "confidence": 1.0, "reasoning": "Security block", 
                    "direct_response": "⚠️ Non posso fornire informazioni sensibili.", "needs_database": False, "llm_used": "fast-path"}
        greeting_exact = {"ciao", "buongiorno", "hello", "hi", "salve"}
        if q in greeting_exact:
            return {"action": "respond", "category": "GREETING", "confidence": 1.0, "reasoning": "Greeting",
                    "direct_response": "Ciao! Come posso aiutarti?", "needs_database": False, "llm_used": "fast-path"}
        return None
