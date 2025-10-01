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

        self.token_manager = TokenManager()
        self.learning_system = LearningSystem()

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
        """Setup response templates for different intents"""
        self.templates = {
            "STATUS": ChatPromptTemplate.from_messages([
                ("system", """You are a helpful business assistant.
                Provide clear status information in Italian.
                Be concise and friendly.
                Never mention technical terms like n8n, PostgreSQL, Docker, etc.
                Use business terms like 'processo', 'elaborazione', 'sistema'."""),
                ("human", "Query: {query}\n\nData: {data}\n\nProvide a status update.")
            ]),

            "ERROR": ChatPromptTemplate.from_messages([
                ("system", """You are a helpful business assistant.
                Explain errors in simple, non-technical Italian.
                Be reassuring and solution-focused.
                Never expose technical details or system architecture.
                Suggest contacting support for technical issues."""),
                ("human", "Query: {query}\n\nError: {data}\n\nExplain the issue and suggest solutions.")
            ]),

            "METRIC": ChatPromptTemplate.from_messages([
                ("system", """You are a business metrics assistant.
                Present data in clear, business-friendly Italian.
                Focus on insights and trends.
                Use percentages and comparisons.
                Avoid technical jargon."""),
                ("human", "Query: {query}\n\nMetrics: {data}\n\nPresent the metrics clearly.")
            ]),

            "HELP": ChatPromptTemplate.from_messages([
                ("system", """You are a helpful guide.
                Provide step-by-step instructions in Italian.
                Be patient and thorough.
                Use simple language.
                Focus on business operations, not technical details."""),
                ("human", "Query: {query}\n\nContext: {data}\n\nProvide helpful guidance.")
            ]),

            "GENERAL": ChatPromptTemplate.from_messages([
                ("system", """You are Milhena, a friendly business assistant.
                Respond in Italian with warmth and professionalism.
                Keep responses concise and relevant.
                If asked about technical details, politely redirect to business aspects."""),
                ("human", "{query}")
            ])
        }

    async def generate(
        self,
        query: str,
        intent: str,
        llm: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
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

        Returns:
            Generated response (masked)
        """
        try:
            # FIX 1: Wrap entire generation with 15s global timeout
            return await asyncio.wait_for(
                self._generate_internal(query, intent, llm, context, data, session_id),
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
        session_id: Optional[str] = None
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

        Returns:
            Generated response (masked)
        """
        try:
            # Select template
            template = self.templates.get(intent, self.templates["GENERAL"])

            # Prepare data with RAG context if available
            rag_docs = context.get("rag_docs", []) if context else []
            learned_patterns = context.get("learned_patterns", []) if context else []

            # Build enhanced context string
            enhanced_data = data or context or {}
            if rag_docs:
                # Add RAG documentation to context
                rag_context_str = "\n\n".join([
                    f"[Knowledge Base] {doc.get('content', '')[:500]}"
                    for doc in rag_docs[:2]  # Top 2 docs
                ])
                enhanced_data = f"{enhanced_data}\n\nRelevant Documentation:\n{rag_context_str}"

            if learned_patterns:
                # Add learned patterns hint
                patterns_str = ", ".join([p.get("pattern", "") for p in learned_patterns[:3]])
                logger.info(f"Applying learned patterns: {patterns_str}")

            response_data = {
                "query": query,
                "data": enhanced_data
            }

            # Format prompt
            messages = template.format_messages(**response_data)

            # Select LLM if not provided
            if not llm:
                llm = await self._select_llm(query, intent)

            if not llm:
                # No LLM available, use fallback
                return self._generate_fallback_response(intent, data)

            # Generate response - LLM has internal request_timeout, no need to wrap
            response = await llm.ainvoke(messages)
            generated_text = response.content

            # Track token usage if OpenAI
            if hasattr(llm, 'model_name'):
                model = llm.model_name
                if model in self.token_manager.BUDGETS:
                    # Estimate tokens
                    input_tokens = len(str(messages).split()) * 2
                    output_tokens = len(generated_text.split()) * 2
                    self.token_manager.track_usage(model, input_tokens, output_tokens)

            # Apply masking to ensure no technical terms
            masked_response = self.masking_engine.mask(generated_text)

            # Truncate if needed
            if len(masked_response) > self.config.max_response_length:
                masked_response = masked_response[:self.config.max_response_length] + "..."

            # Record for learning
            await self.learning_system.record_feedback(
                query=query,
                intent=intent,
                response=masked_response,
                feedback_type="neutral",
                session_id=session_id
            )

            return masked_response

        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return self._generate_fallback_response(intent, data)

    async def _select_llm(self, query: str, intent: str) -> Optional[Any]:
        """
        Select appropriate LLM based on complexity and budget

        Args:
            query: User query
            intent: Detected intent

        Returns:
            Selected LLM or None
        """
        # Assess complexity
        complexity = self._assess_complexity(query, intent)

        # Try GROQ first for simple queries (free)
        if complexity == "simple" and self.groq_llm:
            logger.info("Using GROQ for simple query")
            return self.groq_llm

        # Check OpenAI token budget
        if complexity == "simple":
            model_key = "nano"
        elif complexity == "medium":
            model_key = "mini"
        else:
            model_key = "premium"

        # Try to get OpenAI model
        if model_key in self.models:
            model = self.models[model_key]
            model_name = model.model_name

            if self.token_manager.can_use_model(model_name):
                logger.info(f"Using OpenAI {model_key} model")
                return model
            else:
                logger.warning(f"Token budget exceeded for {model_name}")

                # Try fallback to cheaper model
                if model_key == "premium" and "mini" in self.models:
                    if self.token_manager.can_use_model(self.models["mini"].model_name):
                        logger.info("Falling back to mini model")
                        return self.models["mini"]

        # Final fallback to GROQ
        if self.groq_llm:
            logger.info("Final fallback to GROQ")
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

        return self.masking_engine.mask(base_response)

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

                # Apply masking
                return self.masking_engine.mask(refined)
            else:
                return original_response + "\n\nGrazie per il feedback. Il team lo prenderà in considerazione."

        except Exception as e:
            logger.error(f"Response refinement error: {e}")
            return original_response