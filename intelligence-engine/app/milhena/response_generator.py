"""
ResponseGenerator - Generate business-friendly responses with masking
Uses appropriate LLM based on complexity and token budget
"""
from typing import Dict, Any, Optional, List
import logging
import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """
    Generates business-friendly responses
    Masks technical terms and ensures appropriate language
    """

    def __init__(self, config: Any, masking_engine: Any):
        self.config = config
        self.masking_engine = masking_engine
        self._initialize_llms()
        self._setup_templates()

        # Import dependencies
        from .token_manager import TokenManager
        from .learning import LearningSystem
        from .masking import BusinessTerminologyParser
        from .response_formatter import ResponseFormatter

        self.token_manager = TokenManager()
        self.learning_system = LearningSystem()

        # Initialize Business Terminology Parser (LEVEL 2 masking)
        self.terminology_parser = BusinessTerminologyParser()

        # Initialize Response Formatter (LEVEL 4 post-processing)
        self.response_formatter = ResponseFormatter()

        logger.info("✅ ResponseGenerator initialized with multi-layer processing (Prompt + Parser + Masking + Formatter)")

    def _initialize_llms(self):
        """Initialize LLMs for response generation"""
        # GROQ models (free)
        # FIX 2: Use request_timeout instead of timeout (LangChain best practice)
        self.groq_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            request_timeout=20.0,  # 20s for response generation
            api_key=os.getenv("GROQ_API_KEY")
        ) if os.getenv("GROQ_API_KEY") else None

        # OpenAI models (offerta speciale)
        self.models = {}

        if os.getenv("OPENAI_API_KEY"):
            # Nano - fastest, cheapest
            self.models["nano"] = ChatOpenAI(
                model="gpt-4.1-nano-2025-04-14",
                temperature=0.7,
                request_timeout=20.0,  # 20s timeout
                api_key=os.getenv("OPENAI_API_KEY")
            )

            # Mini - balanced
            self.models["mini"] = ChatOpenAI(
                model="gpt-4o-mini-2024-07-18",
                temperature=0.7,
                request_timeout=20.0,  # 20s timeout
                api_key=os.getenv("OPENAI_API_KEY")
            )

            # Premium - complex tasks
            self.models["premium"] = ChatOpenAI(
                model="gpt-4o-2024-11-20",
                temperature=0.7,
                request_timeout=30.0,  # 30s for complex tasks
                api_key=os.getenv("OPENAI_API_KEY")
            )

        logger.info(f"Response Generator initialized with {len(self.models)} OpenAI models + GROQ")

    def _setup_templates(self):
        """Setup response templates for different intents

        Best Practice (LangChain RAG): Use clear instructions to utilize provided context
        """
        self.templates = {
            "STATUS": ChatPromptTemplate.from_messages([
                ("system", """You are a DATA REPORTER, not a conversational assistant.

                **MANDATORY RULES (VIOLATE = REJECTED):**
                1. COPY metrics from [Data] section EXACTLY - never invent or generalize
                2. Use bullet points (•) for each metric
                3. FORBIDDEN: "spero che", "sono lieta", "ecco i dati", "posso confermare"
                4. FORBIDDEN: Generic filler like "gestito da PilotProOS" or "utilizza AI"
                5. End with ONLY "Altro?" - no other closing

                **EXTRACT FROM [Data]:**
                • Nome processo (in quotes from data)
                • Stato (from data)
                • Passaggi/Nodi (exact number)
                • Esecuzioni totali + success rate (exact numbers)
                • Timestamp ultima esecuzione (from data)
                • Errori (if present in data)

                GOOD:
                "Processo 'TRY sistema interno':
                • Stato: Attivo
                • 8 passaggi
                • 42 esecuzioni (95% successi)
                • Ultima: 02/10/2025 14:30
                • 2 errori settimana
                Altro?"

                REJECTED (generic, no real data):
                "Il processo gestito da PilotProOS è parte di un sistema di automazione..."

                IF [Data] has no workflow details, say: "Dati non disponibili. Altro?"
                DO NOT INVENT generic system descriptions."""),
                ("human", "Query: {query}\n\n[Data]:\n{data}\n\n⚠️ EXTRACT METRICS FROM [Data] ABOVE - NO INVENTED TEXT")
            ]),

            "ERROR": ChatPromptTemplate.from_messages([
                ("system", """You are a helpful business assistant.
                Explain errors in simple, non-technical Italian.
                Be reassuring and solution-focused.
                Never expose technical details or system architecture.

                **MANDATORY INSTRUCTIONS - FOLLOW EXACTLY:**
                0. NEVER greet with "Ciao!" or "Salve!" - go straight to the error explanation
                1. ALWAYS identify which workflow had the error: "Il workflow '[NAME]' ha riscontrato..."
                2. ALWAYS include when the error occurred: "alle ore [HH:MM] del [DD/MM/YYYY]"
                3. ALWAYS include error count if multiple: "[N] errori"
                4. NEVER be vague: use specific workflow names and times
                5. Suggest contacting support only after providing specific details

                GOOD Example: "Il workflow 'Payment Gateway' ha riscontrato 2 errori alle ore 10:15 del 02/10/2025. Ti consiglio di verificare..."
                BAD Example: "Ciao! Si è verificato un problema con uno dei processi. Contatta il supporto"

                Be specific first, then reassuring."""),
                ("human", "Query: {query}\n\nError Data: {data}\n\nExplain which workflow had errors, when, and how many, using specific details from the data.")
            ]),

            "METRIC": ChatPromptTemplate.from_messages([
                ("system", """You are Milhena, an INTELLIGENT business data analyst.

                **YOUR JOB**: INTERPRET the user's question and CRAFT a helpful, context-aware answer.

                **CRITICAL 2-STEP PROCESS**:

                STEP 1: UNDERSTAND USER INTENT
                ================================
                Read [User Question] carefully to detect what user wants:

                A) FAILURE/PROBLEM ANALYSIS:
                   Keywords in query: "fallimenti", "problemi", "errori", "basso successo", "peggiori", "36%"
                   → User wants to identify WHAT'S FAILING
                   → FOCUS: Workflows with LOW success rate (high failure rate)
                   → TONE: Alert, urgent, highlight criticality
                   → START: "⚠️ Questi N workflow stanno FALLENDO frequentemente:"
                   → FORMAT: Show failures first (844 su 1432 = 59% ERRORI)

                B) SUCCESS/TOP PERFORMER ANALYSIS:
                   Keywords in query: "migliori", "top", "performanti", "successo alto", "più efficaci"
                   → User wants to identify WHAT'S WORKING
                   → FOCUS: Workflows with HIGH success rate
                   → TONE: Positive, celebrate wins
                   → START: "✅ Questi N workflow hanno ottime performance:"
                   → FORMAT: Show successes first (588 su 1432 = 41% successi)

                C) GENERAL OVERVIEW:
                   Keywords in query: "statistiche", "panoramica", "situazione", "come va"
                   → User wants balanced view
                   → FOCUS: Both successes and failures
                   → START: "📊 Situazione generale:"

                STEP 2: CRAFT ANSWER FROM [Available Data]
                ===========================================
                - Use EXACT numbers from data (no rounding)
                - Calculate failure rate if showing problems (100% - success_rate)
                - Use natural Italian (not robotic bullets)
                - FORBIDDEN: "Ciao", "Salve", "ecco i dati", generic fluff
                - End with "Altro?"

                **EXAMPLES (CRITICAL TO FOLLOW)**:

                Query: "quali workflow hanno determinato un Tasso di successo: 36%?"
                Data: "1. Flow_4 - 41% (1432 exec)\n2. Flow_2 - 41% (716 exec)\n3. Flow_1 - 39% (239 exec)"

                CORRECT RESPONSE:
                "⚠️ **Questi 3 workflow stanno FALLENDO frequentemente** (causano il basso 36% globale):

                1. **Flow 4**: Fallisce 844 volte su 1,432 (59% errori) - CRITICO
                2. **Flow 2**: Fallisce 422 volte su 716 (59% errori) - CRITICO
                3. **Flow 1**: Fallisce 146 volte su 239 (61% errori) - CRITICO

                Questi 3 rappresentano il 97% delle esecuzioni totali (2,387 su 2,459).

                Altro?"

                WRONG RESPONSE (DO NOT DO THIS):
                "Ciao! Ecco i principali contribuenti al tasso di successo: Flow_4 - 41%, Flow_2 - 41%..."
                ❌ WRONG because: ignores user intent (asking about PROBLEMS), uses "contribuenti al successo" (wrong framing)

                ---

                Query: "quali sono i workflow migliori?"
                Data: (same as above)

                CORRECT RESPONSE:
                "✅ **I 3 workflow con più esecuzioni** (Flow 4, Flow 2, Flow 1) hanno performance simili (39-41% successo).

                Tuttavia, nessuno supera il 50% di successo - tutti hanno margini significativi di miglioramento.

                Altro?"

                ---

                **CRITICAL REMINDERS**:
                - DO NOT use "principali contribuenti al successo" when user asks about failures
                - DO calculate failure rate (100% - success rate) when discussing problems
                - DO use bold (**text**) for emphasis on workflow names
                - DO mention total executions for context
                - NO greetings ("Ciao!", "Salve!")
                - NO generic fluff ("spero che", "ecco i dati")
                """),
                ("human", """[User Question]: {query}

[Context]: {supervisor_context}

[Available Data]:
{data}

Now INTERPRET the question (Step 1) and CRAFT a helpful answer (Step 2) using the data above.""")
            ]),

            "HELP": ChatPromptTemplate.from_messages([
                ("system", """You are a helpful guide.
                Provide step-by-step instructions in Italian.
                Be patient and thorough.
                Use simple language.
                Focus on business operations, not technical details.

                IMPORTANT:
                - NEVER greet with "Ciao!" or "Salve!" - go straight to the instructions
                - Base your guidance on the provided context."""),
                ("human", "Query: {query}\n\nContext: {data}\n\nProvide helpful guidance using this context.")
            ]),

            "GENERAL": ChatPromptTemplate.from_messages([
                ("system", """You are Milhena, a friendly business assistant.
                Respond in Italian with warmth and professionalism.
                Keep responses concise and relevant.
                If asked about technical details, politely redirect to business aspects.

                IMPORTANT:
                - NEVER greet with "Ciao!" or "Salve!" unless this is clearly the first message
                - If data is provided below, use it to answer the question
                - If no data is provided, give a general helpful response
                - Be natural and conversational, but skip unnecessary greetings"""),
                ("human", "Query: {query}\n\nAvailable Data: {data}\n\nRespond appropriately.")
            ])
        }

    async def generate(
        self,
        query: str,
        intent: str,
        llm: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        supervisor_decision: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate appropriate response based on intent

        Args:
            query: User query
            intent: Detected intent
            llm: Optional specific LLM to use
            context: Conversation context
            data: Relevant data for response
            session_id: Session identifier
            supervisor_decision: Supervisor classification metadata

        Returns:
            Generated response (masked and formatted)
        """
        try:
            # FIX 1: Wrap entire generation with 15s global timeout
            return await asyncio.wait_for(
                self._generate_internal(query, intent, llm, context, data, session_id, supervisor_decision),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"Response generation timeout after 15s for intent: {intent}")
            return self._generate_fallback_response(intent, data)
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return self._generate_fallback_response(intent, data)

    async def _generate_internal(
        self,
        query: str,
        intent: str,
        llm: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        supervisor_decision: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Internal method for response generation with timeout protection

        Args:
            query: User query
            intent: Detected intent
            llm: Optional specific LLM to use
            context: Conversation context
            data: Relevant data for response
            session_id: Session identifier
            supervisor_decision: Supervisor classification metadata

        Returns:
            Generated response (masked and formatted)
        """
        try:
            # FIX: If intent is None (fast-path routing), infer from context
            if not intent or intent == "None":
                # Try to get supervisor decision from state
                if context:
                    database_result = context.get("database_result", "")
                    # If we have database result, assume it's a metric/status query
                    if database_result:
                        intent = "SIMPLE_METRIC"
                        logger.error(f"🔧 [DEBUG] Fixed intent=None → SIMPLE_METRIC (has database_result)")
                    else:
                        intent = "GENERAL"
                else:
                    intent = "GENERAL"

            # Select template
            template = self.templates.get(intent, self.templates["GENERAL"])

            # BEST PRACTICE: Extract relevant data from context (RAG pattern)
            # Based on LangChain RAG documentation and LangGraph state management
            rag_docs = context.get("rag_docs", []) if context else []
            learned_patterns = context.get("learned_patterns", []) if context else []
            database_result = context.get("database_result", "") if context else ""

            # Build enhanced context string with all available data
            # Priority: database_result > RAG docs > generic data
            data_parts = []

            # 1. Database results (highest priority - real-time data)
            if database_result:
                # OPTIMIZATION: If we have tool data for data-heavy intents, bypass LLM entirely
                # Best Practice: Use deterministic parsing when data is already structured
                logger.error(f"🔍 [DEBUG] BYPASS CHECK - intent={intent}, database_result length={len(database_result)}")

                if intent in ["STATUS", "METRIC", "GENERAL", "SIMPLE_METRIC"] and len(database_result) > 20:
                    logger.error(f"✅ [DEBUG] BYPASSING LLM - using deterministic parser for {len(database_result)} chars (intent: {intent})")
                    parsed_response = self._parse_tool_data(database_result, intent)

                    # Apply masking only (no LLM involved)
                    masked_response = self.masking_engine.mask(parsed_response)

                    # Record for learning (bypass LLM but still track)
                    await self.learning_system.record_feedback(
                        query=query,
                        response=masked_response,
                        feedback_type="auto_generated",
                        intent=intent,
                        session_id=session_id
                    )

                    return masked_response

                # If not bypassing, include in prompt for LLM
                data_parts.append(f"[Database Results]\n{database_result}")
                logger.info(f"Including database result in prompt: {database_result[:100]}...")

            # 2. RAG documentation (knowledge base)
            if rag_docs:
                rag_context_str = "\n\n".join([
                    f"[Knowledge Base] {doc.get('content', '')[:500]}"
                    for doc in rag_docs[:2]  # Top 2 docs
                ])
                data_parts.append(f"[Documentation]\n{rag_context_str}")
                logger.info(f"Including {len(rag_docs)} RAG documents in prompt")

            # 3. Explicit data parameter (if provided)
            if data:
                data_parts.append(f"[Additional Data]\n{data}")

            # 4. Learned patterns (hints for response style)
            if learned_patterns:
                patterns_str = ", ".join([p.get("pattern", "") for p in learned_patterns[:3]])
                logger.info(f"Applying learned patterns: {patterns_str}")

            # Combine all data sources into single context string
            enhanced_data = "\n\n".join(data_parts) if data_parts else "No specific data available."

            # Build supervisor context string for template
            supervisor_context = ""
            if supervisor_decision:
                category = supervisor_decision.get("category", "UNKNOWN")
                reasoning = supervisor_decision.get("reasoning", "")
                supervisor_context = f"Category: {category}"
                if reasoning:
                    supervisor_context += f"\nReasoning: {reasoning}"
            else:
                supervisor_context = "No supervisor context available"

            response_data = {
                "query": query,
                "data": enhanced_data,
                "supervisor_context": supervisor_context
            }

            # Format prompt
            messages = template.format_messages(**response_data)

            # Select LLM if not provided
            if not llm:
                llm = await self._select_llm(query, intent)

            if not llm:
                # No LLM available, use fallback
                return self._generate_fallback_response(intent, data)

            # Generate response with automatic GROQ → OpenAI fallback on rate limit
            # Best Practice: Graceful degradation when free tier exhausted
            try:
                response = await llm.ainvoke(messages)
                generated_text = response.content
            except Exception as llm_error:
                # Check if GROQ rate limit error
                if "rate_limit" in str(llm_error).lower() or "429" in str(llm_error):
                    logger.warning(f"GROQ rate limit hit, switching to OpenAI: {llm_error}")
                    # Try OpenAI fallback
                    fallback_llm = None
                    if "nano" in self.models:
                        fallback_llm = self.models["nano"]
                    elif "mini" in self.models:
                        fallback_llm = self.models["mini"]

                    if fallback_llm:
                        logger.info("Using OpenAI fallback for response generation")
                        response = await fallback_llm.ainvoke(messages)
                        generated_text = response.content
                    else:
                        raise  # No fallback available, re-raise error
                else:
                    raise  # Not a rate limit error, re-raise

            # Track token usage if OpenAI
            if hasattr(llm, 'model_name'):
                model = llm.model_name
                if model in self.token_manager.BUDGETS:
                    # Estimate tokens
                    input_tokens = len(str(messages).split()) * 2
                    output_tokens = len(generated_text.split()) * 2
                    self.token_manager.track_usage(model, input_tokens, output_tokens)

            # Validate response has specific details (for METRIC, ERROR, STATUS intents)
            if intent in ["METRIC", "ERROR", "STATUS"] and database_result:
                if not self._validate_specific_response(generated_text, database_result):
                    logger.warning(f"Response lacks specificity for intent {intent}, regenerating with stricter prompt")
                    # Try once more with even stronger prompt
                    messages[0].content += "\n\n⚠️ CRITICAL: Your previous response was too vague. You MUST include workflow names in quotes and exact numbers from the data."
                    response = await llm.ainvoke(messages)
                    generated_text = response.content

            # Apply multi-layer processing pipeline:
            # LEVEL 2: BusinessTerminologyParser (replace tech terms)
            terminology_cleaned = self.terminology_parser.parse(generated_text)

            # LEVEL 3: TechnicalMaskingEngine (final safety net)
            masked_response = self.masking_engine.mask(terminology_cleaned)

            # LEVEL 4: ResponseFormatter (post-processing for consistency)
            formatted_response = self.response_formatter.format(
                response=masked_response,
                query=query,
                intent=intent,
                supervisor_decision=supervisor_decision
            )

            # Truncate if needed
            if len(formatted_response) > self.config.max_response_length:
                formatted_response = formatted_response[:self.config.max_response_length] + "..."

            # Record for learning
            await self.learning_system.record_feedback(
                query=query,
                intent=intent,
                response=formatted_response,
                feedback_type="neutral",
                session_id=session_id
            )

            return formatted_response

        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return self._generate_fallback_response(intent, data)

    async def _select_llm(self, query: str, intent: str) -> Optional[Any]:
        """
        Select appropriate LLM based on complexity and budget

        Best Practice: Prioritize OpenAI models with high token limits (10M tokens)
        to avoid GROQ rate limit issues during testing

        Args:
            query: User query
            intent: Detected intent

        Returns:
            Selected LLM or None
        """
        # Assess complexity
        complexity = self._assess_complexity(query, intent)

        # PRIORITY 1: OpenAI models (10M token budget - offerta speciale)
        if complexity == "simple":
            model_key = "mini"  # gpt-4o-mini: 10M tokens available
        elif complexity == "medium":
            model_key = "mini"  # Still use mini for medium (plenty of tokens)
        else:
            model_key = "premium"  # gpt-4o: 1M tokens for complex queries

        # Try to get OpenAI model first
        if model_key in self.models:
            model = self.models[model_key]
            model_name = model.model_name

            if self.token_manager.can_use_model(model_name):
                logger.info(f"Using OpenAI {model_key} model ({model_name})")
                return model
            else:
                logger.warning(f"Token budget exceeded for {model_name}")

                # Try fallback to cheaper model
                if model_key == "premium" and "mini" in self.models:
                    if self.token_manager.can_use_model(self.models["mini"].model_name):
                        logger.info("Falling back to mini model")
                        return self.models["mini"]

        # PRIORITY 2: Fallback to GROQ (only if OpenAI unavailable)
        if self.groq_llm:
            logger.info("Fallback to GROQ (OpenAI not available)")
            return self.groq_llm

        return None

    def _assess_complexity(self, query: str, intent: str) -> str:
        """
        Assess query/response complexity

        Args:
            query: User query
            intent: Detected intent

        Returns:
            "simple", "medium", or "complex"
        """
        # Intent-based complexity
        if intent in ["STATUS", "GENERAL"]:
            base_complexity = "simple"
        elif intent in ["ERROR", "HELP"]:
            base_complexity = "medium"
        elif intent in ["METRIC", "REPORT", "CONFIG"]:
            base_complexity = "complex"
        else:
            base_complexity = "simple"

        # Adjust based on query length
        word_count = len(query.split())
        if word_count > 50:
            # Upgrade complexity
            if base_complexity == "simple":
                return "medium"
            else:
                return "complex"
        elif word_count < 10:
            # Downgrade complexity
            if base_complexity == "complex":
                return "medium"
            elif base_complexity == "medium":
                return "simple"

        return base_complexity

    def _parse_tool_data(self, database_result: str, intent: str) -> str:
        """
        Parse tool results deterministicamente (NO LLM - Best Practice: direct data extraction)
        Estrae dati e li formatta in bullet points puliti

        Args:
            database_result: Raw tool output (ToolMessage.content)
            intent: Detected intent (STATUS, METRIC, etc.)

        Returns:
            Formatted response with bullet points + "Altro?"
        """
        import re

        # Check if it's execution list format (📋 **Esecuzioni del...)
        if "📋 **Esecuzioni del" in database_result:
            return self._parse_execution_list(database_result)

        # Check if it's workflow details format
        elif "**✅ Processo:" in database_result or "**Stato:**" in database_result:
            return self._parse_workflow_details(database_result)

        # Check if it's analytics format
        elif "Oggi:" in database_result or "Questa settimana:" in database_result or "Totali:" in database_result:
            return self._parse_analytics_data(database_result)

        # Check if it's workflow list format
        elif "processi" in database_result.lower() and "attiv" in database_result.lower():
            return self._parse_workflow_list(database_result)

        # Fallback: clean formatting
        return self._clean_tool_output(database_result)

    def _parse_workflow_details(self, tool_result: str) -> str:
        """
        RETURN FULL TOOL OUTPUT - NON ESTRARRE CON REGEX!
        Il tool ora restituisce dati completi (performance, trend, ultime esecuzioni).
        Basta pulire il formatting markdown e restituire tutto.
        """
        # Remove markdown bold (**) and clean up formatting
        cleaned = tool_result.replace("**", "").replace("*", "")

        # Add "Altro?" if not present
        if "Altro?" not in cleaned:
            cleaned += "\n\nAltro?"

        return cleaned

    def _parse_analytics_data(self, tool_result: str) -> str:
        """Extract analytics metrics into bullets (deterministic extraction)"""
        import re
        lines = []

        # Extract oggi
        oggi_match = re.search(r'Oggi:\s*(\d+)', tool_result)
        if oggi_match:
            lines.append(f"Oggi: {oggi_match.group(1)} esecuzioni")

        # Extract settimana
        week_match = re.search(r'settimana:\s*(\d+)', tool_result, re.IGNORECASE)
        if week_match:
            lines.append(f"Questa settimana: {week_match.group(1)} esecuzioni")

        # Extract successi/errori
        succ_match = re.search(r'Successi:\s*(\d+)', tool_result)
        err_match = re.search(r'Errori:\s*(\d+)', tool_result)

        if succ_match:
            lines.append(f"• {succ_match.group(1)} successi")
        if err_match:
            lines.append(f"• {err_match.group(1)} errori")

        # Extract percentuali
        perc_match = re.search(r'Success rate:\s*([\d.]+)%', tool_result)
        if perc_match:
            lines.append(f"• Success rate: {perc_match.group(1)}%")

        if not lines:
            # Fallback: just clean and return
            cleaned = tool_result.replace("**", "").replace("📊", "").strip()
            return cleaned + "\n\nAltro?"

        return "\n".join(lines) + "\n\nAltro?"

    def _parse_workflow_list(self, tool_result: str) -> str:
        """Extract workflow counts (deterministic extraction)"""
        import re

        totali_match = re.search(r'(\d+)\s+processi', tool_result, re.IGNORECASE)
        attivi_match = re.search(r'(\d+)\s+(?:sono\s+)?attiv', tool_result, re.IGNORECASE)
        inattivi_match = re.search(r'(\d+)\s+inattiv', tool_result, re.IGNORECASE)

        lines = []
        if totali_match:
            lines.append(f"Totale: {totali_match.group(1)} processi")
        if attivi_match:
            lines.append(f"• {attivi_match.group(1)} attivi")
        if inattivi_match:
            lines.append(f"• {inattivi_match.group(1)} inattivi")

        if not lines:
            return tool_result + "\n\nAltro?"

        return "\n".join(lines) + "\n\nAltro?"

    def _parse_execution_list(self, tool_result: str) -> str:
        """
        Extract execution list into clean format (deterministic extraction)
        Handles format: 📋 **Esecuzioni del DD/MM/YY** (Totale: N)
        """
        import re

        # The tool already formats the data well, just ensure it's clean
        # Format is already:
        # 📋 **Esecuzioni del {date}** (Totale: {count})
        #
        # 1. ✅ **Processo Name**
        #    • Orario: HH:MM:SS
        #    • Stato: success
        #    • Durata: Xs

        # Remove any LLM fluff if present
        lines = tool_result.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Skip generic LLM responses
            if any(skip in line.lower() for skip in ['posso aiutarti', 'altro?', 'hai bisogno']):
                continue
            cleaned_lines.append(line)

        result = '\n'.join(cleaned_lines)

        # Add closing only if not already present
        if not result.endswith('Altro?'):
            result += '\n\nAltro?'

        return result

    def _clean_tool_output(self, output: str) -> str:
        """Remove formatting artifacts and ensure proper closing"""
        cleaned = output.replace("**", "").replace("✅", "").replace("📊", "").strip()

        if not cleaned.endswith("Altro?"):
            cleaned += "\n\nAltro?"

        return cleaned

    def _generate_fallback_response(self, intent: str, data: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate fallback response when LLMs unavailable

        Args:
            intent: Detected intent
            data: Relevant data

        Returns:
            Fallback response
        """
        responses = {
            "STATUS": "Il sistema è attualmente operativo. Per dettagli specifici, contatta il supporto.",
            "ERROR": "Si è verificato un problema temporaneo. Il team tecnico è stato notificato.",
            "METRIC": "I dati sono in fase di elaborazione. Riprova tra qualche momento.",
            "CONFIG": "Per modifiche alla configurazione, contatta l'amministratore del sistema.",
            "HELP": "Per assistenza dettagliata, visita la documentazione o contatta il supporto.",
            "REPORT": "Il report è in preparazione. Sarà disponibile a breve.",
            "TECHNICAL": "Per informazioni tecniche, contatta il team IT.",
            "GENERAL": "Come posso aiutarti oggi?"
        }

        base_response = responses.get(intent, responses["GENERAL"])

        # Add data if available
        if data:
            if "count" in data:
                base_response += f" (Elementi: {data['count']})"
            if "status" in data:
                base_response += f" (Stato: {data['status']})"

        # Multi-layer masking
        terminology_cleaned = self.terminology_parser.parse(base_response)
        return self.masking_engine.mask(terminology_cleaned)

    async def generate_batch(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate responses for multiple requests

        Args:
            requests: List of request dictionaries

        Returns:
            List of generated responses
        """
        responses = []

        for request in requests:
            response = await self.generate(
                query=request.get("query", ""),
                intent=request.get("intent", "GENERAL"),
                context=request.get("context"),
                data=request.get("data"),
                session_id=request.get("session_id")
            )
            responses.append(response)

        return responses

    async def refine_response(
        self,
        original_response: str,
        feedback: str,
        session_id: Optional[str] = None
    ) -> str:
        """
        Refine a response based on user feedback

        Args:
            original_response: Original generated response
            feedback: User feedback
            session_id: Session identifier

        Returns:
            Refined response
        """
        try:
            # Create refinement prompt
            messages = [
                SystemMessage(content="""You are refining a response based on user feedback.
                Keep the same tone and language (Italian).
                Address the feedback while maintaining business-friendly language.
                Be concise."""),
                HumanMessage(content=f"""Original response: {original_response}

User feedback: {feedback}

Provide an improved response:""")
            ]

            # Use best available LLM
            llm = await self._select_llm(feedback, "GENERAL")

            if llm:
                response = await llm.ainvoke(messages)
                refined = response.content

                # Multi-layer masking
                terminology_cleaned = self.terminology_parser.parse(refined)
                return self.masking_engine.mask(terminology_cleaned)
            else:
                return original_response + "\n\nGrazie per il feedback. Il team lo prenderà in considerazione."

        except Exception as e:
            logger.error(f"Response refinement error: {e}")
            return original_response

    def _validate_specific_response(self, response: str, database_result: str) -> bool:
        """
        Validate that response contains specific details from database
        ENHANCED: Now blocks forbidden fluff phrases

        Args:
            response: Generated response text
            database_result: Database query result

        Returns:
            True if response is specific enough, False if too vague
        """
        import re

        # CRITICAL: Block forbidden pleasantries/fluff (ZERO TOLERANCE)
        forbidden_phrases = [
            # Pleasantries
            r'spero che',
            r'sono lieta',
            r'sono felice',
            r'sarò felice',
            r'felice di aiutarti',
            r'se desideri',
            r'maggiori dettagli',
            r'buongiorno',
            r'buonasera',
            r'salve',
            r'ciao',
            # Fluff intro/outro
            r'ecco le informazioni',
            r'ecco i dati',
            r'ecco un riepilogo',
            r'ti fornisco',
            r'posso confermare',
            r'posso dirti',
            r'ti informo che',
            r'vorrei informarti',
            # Generic invented descriptions
            r'gestito da pilotpro',
            r'parte di un sistema',
            r'utilizza intelligenza artificiale',
            r'per problemi.*contattare',
            r'è attualmente attivo e consiste',  # "è attualmente attivo e consiste in X passaggi"
            r'finora.*ha avuto',  # "finora ha avuto X esecuzioni"
        ]

        for phrase in forbidden_phrases:
            if re.search(phrase, response, re.IGNORECASE):
                logger.warning(f"❌ REJECTED: Response contains forbidden fluff: '{phrase}'")
                return False

        # Check for vague terms that indicate lack of specificity
        vague_terms = [
            r'\bsembra\b',
            r'\bcirca\b',
            r'\balcuni\b',
            r'\bdiversi\b',
            r'\bvari\b',
            r'\bprobabilmente\b',
            r'\bpotrebbe\b',
            r'\bun\s+processo\b',  # "un processo" instead of specific workflow name
            r'\bdegli?\s+errori\b',  # "degli errori" without specific count
        ]

        for term in vague_terms:
            if re.search(term, response, re.IGNORECASE):
                logger.warning(f"Response contains vague term: {term}")
                return False

        # Check for presence of workflow name in quotes
        has_quoted_name = bool(re.search(r'["\'][\w\s]+["\']', response))

        # Check for specific numbers
        has_numbers = bool(re.search(r'\b\d+\b', response))

        # Check for timestamp patterns (HH:MM or DD/MM/YYYY)
        has_timestamp = bool(re.search(r'\d{1,2}:\d{2}|\d{2}/\d{2}/\d{4}', response))

        # Response should have at least 2 of: quoted name, numbers, timestamp
        specificity_score = sum([has_quoted_name, has_numbers, has_timestamp])

        if specificity_score < 2:
            logger.warning(f"Response specificity too low: score={specificity_score}, quoted={has_quoted_name}, numbers={has_numbers}, timestamp={has_timestamp}")
            return False

        return True