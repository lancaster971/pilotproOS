"""
Classifier v3.5.9 - KNOWLEDGE_BASE_SEARCH Category

Extracted from graph.py:1165-1500 (CONTEXT-SYSTEM.md compliance)

NEW v3.5.9: KNOWLEDGE_BASE_SEARCH category for didactic queries (how it works, guides, explanations)
v3.5.8: Polisemia disambiguation, Double negation normalization, Hypothetical queries
v3.5.7: Explicit CoT structured reasoning in prompt
PURE LLM classification (NO fast-path logic - that's in fast_path.py)
"""
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable
import logging
import json
import re
import time

from app.agents.v3_5.utils.state import SupervisorDecision, AgentState

logger = logging.getLogger(__name__)

CLASSIFIER_PROMPT = """# Ruolo e Obiettivo

Sei Milhena, assistente per PilotProOS (sistema monitoraggio processi business automatizzati).

Classifica richieste utente in categorie operative per attivare le funzioni corrette del sistema.

# Contesto PilotProOS

**Sistema gestisce:**
- Processi business (workflow automatizzati)
- Esecuzioni (run di processi)
- Errori/fallimenti
- Step interni ai processi
- Performance metrics

## Terminologia Ambigua (Polisemia)

Alcuni termini hanno significati multipli. Usa contesto query per disambiguare:

- **"esecuzioni"**: Default = workflow runs UNLESS query menziona "database" o "SQL"
- **"report"**: Default = analytics query UNLESS query menziona "genera" o "PDF"
- **"attività"**: Default = workflow executions UNLESS query menziona "business" o "vendite"
- **"stato"**: Default = workflow status SE query menziona processo specifico, ELSE system health
- **"processo"**: Default = workflow UNLESS query menziona "business process"

**Regola**: Se ambiguità persiste dopo context check → CLARIFICATION_NEEDED

# Istruzioni

## Principi di Ragionamento
- Comprendi l'intento business reale
- Usa il contesto fornito e traduci terminologia business
- **Query senza oggetto/contesto richiedono chiarimenti** (es: "quanti?", "stato", "report")
- Valuta se hai informazioni sufficienti per essere genuinamente utile
- Fidati del tuo giudizio ma sii conservativo con query ultra-vaghe

### Gestione Negazioni

Le negazioni NON cambiano categoria, ma tone della risposta:

- "Hai problemi?" → ERROR_ANALYSIS (neutral tone)
- "Non hai problemi?" → ERROR_ANALYSIS (confirmation tone, expect positive answer)

**Nel reasoning (Step 1)**: Identifica negazione e normalizza per category mapping.
**Nei params**: Aggiungi `"tone": "confirmation"` se query ha negazione.

Esempi:
- "Non ci sono errori?" → ERROR_ANALYSIS + `{{"tone": "confirmation"}}`
- "Il workflow non fallisce?" → ERROR_ANALYSIS + `{{"workflow_id": "X", "tone": "confirmation"}}`

## Processo
1. Analizza richiesta → intento business
2. **Verifica presenza oggetto/contesto** → se manca, chiedi chiarimenti
3. Traduci terminologia → significato PilotProOS
4. Mappa al contesto → workflow/dati disponibili
5. Classifica nella categoria più appropriata

**Regola critica**: Query di 1 parola senza oggetto chiaro = CLARIFICATION_NEEDED

# Categorie

1. **PROCESS_LIST** - Elencare processi business
2. **PROCESS_DETAIL** - Dettagli workflow specifico
3. **EXECUTION_QUERY** - Info esecuzioni/attività
4. **ERROR_ANALYSIS** - Problemi/errori/troubleshooting
5. **ANALYTICS** - Metriche/statistiche/trend
6. **STEP_DETAIL** - Step specifici processi
7. **EMAIL_ACTIVITY** - Gestione email ChatOne
8. **PROCESS_ACTION** - Attivare/disattivare/eseguire
9. **SYSTEM_OVERVIEW** - Panoramica completa
10. **KNOWLEDGE_BASE_SEARCH** - Query didattiche (come funziona, spiegazioni, guide)
11. **CLARIFICATION_NEEDED** - Query ambigua, ipotetica, o non supportata

# Gestione Query Ipotetiche

Il sistema NON supporta:
- Simulazioni what-if ("se faccio X, cosa succede?")
- Raccomandazioni ("quale processo dovrei...")
- Predizioni future ("quanti errori avrò domani?")

**Per query ipotetiche**: Classifica CLARIFICATION_NEEDED e offri alternative concrete.

Esempi:
- "Se disattivo X?" → "Non supporto simulazioni. Vuoi vedere dipendenze di X o stato attuale?"
- "Quale workflow eseguire?" → "Non fornisco raccomandazioni. Vuoi lista workflow disponibili?"
- "Errori futuri?" → "Non posso predire. Vuoi trend errori ultimi 7 giorni?"

# Gestione Query Didattiche (KNOWLEDGE_BASE_SEARCH)

Query che richiedono spiegazioni/documentazione invece di dati operativi:

**Trigger keywords**:
- "come funziona X"
- "spiegami X"
- "cos'è X"
- "cosa significa X"
- "guida X"
- "manuale X"
- "documentazione X"
- "tutorial X"

**Esempi**:
- "come funziona pilotpro" → KNOWLEDGE_BASE_SEARCH (non SYSTEM_OVERVIEW dati)
- "spiegami i workflow" → KNOWLEDGE_BASE_SEARCH (non PROCESS_LIST)
- "cos'è un processo business" → KNOWLEDGE_BASE_SEARCH
- "guida per usare il sistema" → KNOWLEDGE_BASE_SEARCH

**Distinzione chiave**:
- "quali workflow?" → PROCESS_LIST (dati operativi)
- "come funzionano i workflow?" → KNOWLEDGE_BASE_SEARCH (spiegazione)

# Chain of Thought Process

IMPORTANT: Before classifying, think through these steps explicitly:

1. **Query Analysis**
   - What is the user literally asking?
   - What business intent might be behind it?
   - Are there ambiguous terms that need translation?

2. **Context Check**
   - Does the query reference specific entities (workflow names, timeframes)?
   - What information would I need to answer this usefully?
   - Is there enough context to proceed or do I need clarification?

3. **Category Mapping**
   - Which category best matches the business intent?
   - What params would make the answer most useful?
   - What's my confidence level (0.0-1.0)?

4. **Self-Verification**
   - Does my classification make sense given the query?
   - Would this category lead to a useful answer?
   - Should I ask for clarification instead?

**Output your reasoning for each step in the "reasoning" field.**

# Output Format

**JSON response (max 300 tokens):**

```json
{{
  "category": "CATEGORY_NAME",
  "confidence": 0.8,
  "reasoning": "STEP-BY-STEP THOUGHT PROCESS:\n1. Query Analysis: ...\n2. Context Check: ...\n3. Category Mapping: ...\n4. Decision: ...",
  "params": {{}}
}}
```

**Per chiarimenti:**
```json
{{
  "category": "CLARIFICATION_NEEDED",
  "confidence": 0.4,
  "reasoning": "Perché è ambiguo",
  "clarification_question": "Domanda specifica"
}}
```

# Esempi

**Query diretta:**
Utente: "Gestione Lead ha problemi?"
```json
{{
  "category": "ERROR_ANALYSIS",
  "confidence": 0.9,
  "reasoning": "Workflow specifico + 'problemi'=errori nel dizionario",
  "params": {{"workflow_id": "GESTIONE_LEAD", "focus": "errors"}}
}}
```

**Query ultra-vaga (1 parola senza oggetto):**
Utente: "quanti?"
```json
{{
  "category": "CLARIFICATION_NEEDED",
  "confidence": 0.2,
  "reasoning": "Interrogativo senza oggetto - potrebbe essere processi, errori, email, esecuzioni",
  "clarification_question": "Quanti cosa? Processi attivi, errori, email, o esecuzioni?"
}}
```

**Query vaga ma inferibile:**
Utente: "attività"
```json
{{
  "category": "CLARIFICATION_NEEDED",
  "confidence": 0.4,
  "reasoning": "'Attività'=esecuzioni ma troppo generico",
  "clarification_question": "Esecuzioni recenti, statistiche, o di processo specifico?"
}}
```

**Query vaga ma contestualizzabile:**
Utente: "dati"
```json
{{
  "category": "SYSTEM_OVERVIEW",
  "confidence": 0.7,
  "reasoning": "Generico ma nel contesto significa panoramica generale",
  "params": {{"scope": "general"}}
}}
```

**Pronome senza riferimento:**
Utente: "quello"
```json
{{
  "category": "CLARIFICATION_NEEDED",
  "confidence": 0.1,
  "reasoning": "Pronome senza riferimento chiaro",
  "clarification_question": "A cosa ti riferisci? Sii più specifico"
}}
```

**Query ultra-vaga (verbo senza oggetto):**
Utente: "stato"
```json
{{
  "category": "CLARIFICATION_NEEDED",
  "confidence": 0.2,
  "reasoning": "Sostantivo generico senza specificare di cosa - processi, sistema, errori",
  "clarification_question": "Stato di cosa? Processi, sistema generale, o situazione errori?"
}}
```

**Query didattica (KNOWLEDGE_BASE_SEARCH):**
Utente: "come funziona pilotpro"
```json
{{
  "category": "KNOWLEDGE_BASE_SEARCH",
  "confidence": 0.9,
  "reasoning": "1. Query Analysis: 'come funziona' = richiesta spiegazione didattica, non dati operativi.\n2. Context Check: Query generica su funzionamento sistema.\n3. Category Mapping: KNOWLEDGE_BASE_SEARCH per cercare documentazione/guide.\n4. Decision: Alta confidenza, query didattica chiara.",
  "params": {{"query": "pilotpro funzionamento overview"}}
}}
```

# Contesto Sistema Attuale (fornito dal sistema)

Il sistema ha iniettato contesto reale qui sotto con:
- Lista workflow attivi e loro nomi
- Statistiche esecuzioni ultimi 7 giorni
- Traduzioni terminologia business comune

Usa questi dati per validare nomi workflow, capire cosa è disponibile, e classificare con precisione.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Analizza e Classifica

**Query utente:** "{query}"
**Data corrente:** {current_date}

Analizza la richiesta usando contesto fornito e reasoning.

**CRITICAL**: Work through the Chain of Thought process above BEFORE deciding.
Show your step-by-step reasoning explicitly in the "reasoning" field.
This helps ensure accurate classification and builds trust with the user.

Return JSON SOLO (no text, no markdown).
"""

class Classifier:
    """
    Classifier Component - PURE LLM classification (no fast-path)

    Based on graph.py:1165-1500 supervisor_orchestrator
    Fast-path logic is in separate fast_path.py component
    """

    def __init__(self, supervisor_llm, db_pool, system_context_cache=None, cache_ttl=300):
        self.supervisor_llm = supervisor_llm
        self.db_pool = db_pool
        self._system_context_cache = system_context_cache or ""
        self._cache_timestamp = 0
        self._cache_ttl = cache_ttl

    @traceable(name="Classifier", run_type="chain", metadata={"version": "3.5.9"})
    async def classify(self, state: AgentState) -> AgentState:
        """
        v3.5.9: KNOWLEDGE_BASE_SEARCH Category (CONTEXT-SYSTEM.md compliance)

        NEW v3.5.9: KNOWLEDGE_BASE_SEARCH for didactic queries (how it works, guides)
        v3.5.8: Polisemia disambiguation, Double negation, Hypothetical queries
        v3.5.7: Explicit Chain of Thought reasoning in prompt

        Pipeline Step 2 (after Fast-Path):
        1. LLM Classification with system context + CoT + edge cases + RAG category
        2. Parse JSON response (includes structured reasoning + params)
        3. Handle CLARIFICATION_NEEDED
        """
        query = state["query"]

        logger.info(f"[CLASSIFIER v3.5.9] Starting classification with KNOWLEDGE_BASE_SEARCH category for: {query[:50]}...")

        # ========================================================================
        # STEP 1: LLM Classification with System Context + CoT + Edge Cases
        # From graph.py:1342-1418
        # v3.5.8: Edge case handling (polisemia, negations, hypothetical)
        # v3.5.7: Enhanced with explicit Chain of Thought reasoning
        # ========================================================================
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        prompt = CLASSIFIER_PROMPT.format(query=query, current_date=current_date)

        # v3.5.2: Inject light context in prompt (RAM cache, 5min TTL, asyncpg query)
        system_context_light = await self._get_system_context_light()
        prompt_with_context = prompt + "\n\n" + system_context_light

        logger.info(f"🔍 [CLASSIFIER v3.5.9] Starting LLM call with CoT + KNOWLEDGE_BASE_SEARCH - query: '{query}'")

        try:
            # v3.5.2: Simple LLM call (no ReAct overhead, context already in prompt)
            # Force OpenAI 4.1-nano for Classifier (Groq rate limit issues)
            base_model = self.supervisor_llm  # Always use OpenAI gpt-4.1-nano

            # Build messages for LLM (context in system, query in user message)
            messages = [
                SystemMessage(content=prompt_with_context),  # v3.5.1: Prompt + light context
                HumanMessage(content=query)
            ]

            # Direct LLM call (single shot, no tools, no loop)
            response = await base_model.ainvoke(messages)
            response_text = response.content

            logger.info(f"[CLASSIFIER v3.5.9] LLM completed - response length: {len(response_text)} chars")

            # ====================================================================
            # STEP 3: Parse JSON from Response
            # From graph.py:1395-1418
            # v3.5.8: Response includes CoT reasoning + edge case handling
            # ====================================================================
            try:
                classification = json.loads(response_text)
                logger.info(f"[CLASSIFIER v3.5.9] Parsed classification: {classification}")
            except json.JSONDecodeError:
                # Fallback: extract JSON from text
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    classification = json.loads(json_match.group(0))
                    logger.warning(f"[CLASSIFIER v3.5.9] Extracted JSON from text: {classification}")
                else:
                    # Ultimate fallback
                    logger.error(f"[CLASSIFIER v3.5.9] Failed to parse JSON from: {response_text}")
                    classification = self._fallback_classification(query)

            classification["llm_used"] = "openai-4.1-nano"  # v3.5.2: Always OpenAI for Classifier

        except Exception as e:
            logger.error(f"[CLASSIFIER v3.5.9] LLM call failed: {e}")
            classification = self._fallback_classification(query)
            classification["llm_used"] = "rule-based"
            logger.warning("[CLASSIFIER v3.5.9] Using rule-based fallback")

        # ========================================================================
        # STEP 4: Save SupervisorDecision
        # From graph.py:1419-1449
        # ========================================================================
        try:
            # FIX: Ensure all required fields exist with defaults
            required_defaults = {
                "action": "react",
                "category": "SIMPLE_QUERY",
                "confidence": 0.7,
                "reasoning": "Auto-generated",
                "direct_response": None,
                "needs_rag": False,
                "needs_database": True,
                "clarification_options": None,
                "llm_used": classification.get("llm_used", "unknown"),
                "params": classification.get("params", {})  # Extract params field
            }

            # Merge with defaults (classification wins)
            full_classification = {**required_defaults, **classification}

            decision_obj = SupervisorDecision(**full_classification)
            # CRITICAL: Convert BaseModel to dict for LangGraph state compatibility
            decision = decision_obj.model_dump()
            state["supervisor_decision"] = decision
        except Exception as dec_error:
            logger.error(f"[CRITICAL] Failed to create SupervisorDecision: {dec_error}")
            logger.error(f"[CRITICAL] Classification keys: {list(classification.keys())}")
            logger.error(f"[CRITICAL] Classification values: {classification}")
            raise

        # ========================================================================
        # STEP 3: Handle CLARIFICATION_NEEDED
        # From graph.py:1456-1467
        # ========================================================================
        if decision["category"] == "CLARIFICATION_NEEDED":
            state["waiting_clarification"] = True
            state["original_query"] = query
            # Use clarification_question as direct response to user
            state["response"] = classification.get("clarification_question", "Mi dispiace, non ho capito. Puoi essere più specifico?")
            logger.info(f"[CLASSIFIER] Waiting clarification with {len(decision.get('clarification_options') or [])} options")
        else:
            state["waiting_clarification"] = False
            if decision.get("direct_response"):
                # Direct response (GREETING, DANGER already handled by fast-path)
                state["response"] = decision["direct_response"]
                logger.info(f"[CLASSIFIER] Direct response for {decision['category']}")

        logger.info(f"[CLASSIFIER] Decision: {decision['category']} → needs_rag={decision['needs_rag']}, needs_db={decision['needs_database']}")

        # Map category to intent (LangGraph State best practice)
        category_to_intent_map = {
            "PROCESS_LIST": "STATUS",
            "PROCESS_DETAIL": "ANALYSIS",
            "EXECUTION_QUERY": "METRIC",
            "ERROR_ANALYSIS": "ANALYSIS",
            "ANALYTICS": "METRIC",
            "STEP_DETAIL": "ANALYSIS",
            "EMAIL_ACTIVITY": "METRIC",
            "PROCESS_ACTION": "ACTION",
            "SYSTEM_OVERVIEW": "STATUS",
            "KNOWLEDGE_BASE_SEARCH": "KNOWLEDGE",
            "CLARIFICATION_NEEDED": "CLARIFICATION"
        }
        state["intent"] = category_to_intent_map.get(decision["category"], "GENERAL")
        logger.info(f"[CLASSIFIER] Mapped category '{decision['category']}' → intent '{state['intent']}'")

        return state

    async def _get_system_context_light(self) -> str:
        """
        v3.5.2: Get light system context from RAM cache (5min TTL)
        From graph.py:1650-1675
        """
        # Check cache validity
        if self._system_context_cache and (time.time() - self._cache_timestamp < self._cache_ttl):
            logger.info("[CACHE HIT] Using cached system context")
            return self._system_context_cache

        # CACHE MISS - Load from DB (async query via asyncpg pool)
        logger.info("[CACHE MISS] Fetching fresh system context from DB")
        light_context = await self._load_context_from_db()

        if light_context:
            # Update cache
            self._system_context_cache = light_context
            self._cache_timestamp = time.time()
            logger.info(f"[CACHE UPDATED] Next refresh in {self._cache_ttl}s")

        return light_context

    async def _load_context_from_db(self) -> str:
        """Load light context from PostgreSQL via asyncpg pool"""
        # Placeholder - implement actual DB query
        return ""  # Graceful fallback

    def _fallback_classification(self, query: str) -> Dict[str, Any]:
        """
        Fallback classification when LLM fails
        From graph.py (implicit fallback logic)
        """
        return {
            "action": "react",
            "category": "CLARIFICATION_NEEDED",
            "confidence": 0.3,
            "reasoning": "LLM classification fallback - richiesta chiarimenti",
            "direct_response": None,
            "clarification_question": "Mi dispiace, non ho capito bene. Puoi essere più specifico?",
            "needs_rag": False,
            "needs_database": False,
            "clarification_options": None,
            "params": {}
        }
