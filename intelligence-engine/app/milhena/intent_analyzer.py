"""
IntentAnalyzer - LLM-powered intent classification with learning
Uses hybrid approach: learned patterns + LLM disambiguation
"""
from typing import Dict, Any, Optional, Tuple
import logging
import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class IntentAnalyzer:
    """
    Analyzes user intent using hybrid approach:
    1. Check learned patterns first (fast)
    2. Use LLM for disambiguation if needed
    3. Learn from feedback to improve
    """

    # Intent categories
    INTENTS = {
        "STATUS": "Checking system or process status",
        "ERROR": "Reporting or investigating errors",
        "METRIC": "Requesting metrics or performance data",
        "CONFIG": "Configuration or setup questions",
        "HELP": "General help or how-to questions",
        "REPORT": "Requesting reports or summaries",
        "TECHNICAL": "Technical implementation details",
        "GENERAL": "General conversation or unclear intent"
    }

    def __init__(self, config: Any):
        self.config = config
        self._initialize_llms()
        self._setup_prompts()

        # Import dependencies
        from .llm_disambiguator import LLMDisambiguator
        from .learning import LearningSystem
        from .token_manager import TokenManager

        self.disambiguator = LLMDisambiguator(config)
        self.learning_system = LearningSystem()
        self.token_manager = TokenManager()

    def _initialize_llms(self):
        """Initialize LLMs for intent classification"""
        # GROQ - Free tier
        self.groq_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.2,  # Lower temp for classification
            api_key=os.getenv("GROQ_API_KEY")
        ) if os.getenv("GROQ_API_KEY") else None

        # OpenAI - Backup
        self.openai_llm = ChatOpenAI(
            model="gpt-4.1-nano-2025-04-14",
            temperature=0.2,
            api_key=os.getenv("OPENAI_API_KEY")
        ) if os.getenv("OPENAI_API_KEY") else None

        logger.info(f"Intent Analyzer initialized - GROQ: {bool(self.groq_llm)}, OpenAI: {bool(self.openai_llm)}")

    def _setup_prompts(self):
        """Setup intent classification prompts"""
        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intent classifier for a business workflow monitoring system.
            Classify user queries into one of these intents:

            STATUS - Checking system or process status
            ERROR - Reporting or investigating errors/failures
            METRIC - Requesting metrics or performance data
            CONFIG - Configuration or setup questions
            HELP - General help or how-to questions
            REPORT - Requesting reports or summaries
            TECHNICAL - Technical implementation details (should be deflected)
            GENERAL - General conversation or unclear intent

            Consider context and be accurate. Output only the intent category."""),
            ("human", "Query: {query}\n\nContext: {context}\n\nIntent:")
        ])

    async def classify(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Classify user intent

        Args:
            query: User query
            context: Conversation context
            session_id: Session identifier

        Returns:
            Intent category
        """
        try:
            # Step 1: Check learned patterns
            learned_suggestion = self.learning_system.suggest_intent(query)
            if learned_suggestion and learned_suggestion[1] > 0.8:
                intent, confidence = learned_suggestion
                logger.info(f"Using learned intent: {intent} (confidence: {confidence:.2f})")
                return intent

            # Step 2: Check for ambiguity and disambiguate
            disambiguation_result = await self.disambiguator.disambiguate(query, context)

            if not disambiguation_result.is_ambiguous and disambiguation_result.confidence > 0.7:
                # Map disambiguation result to intent
                intent = self._map_response_type_to_intent(
                    disambiguation_result.suggested_response_type
                )
                logger.info(f"Disambiguated to intent: {intent}")
                return intent

            # Step 3: Use LLM for classification
            intent = await self._classify_with_llm(query, context)

            # Step 4: Record for learning (neutral feedback initially)
            await self.learning_system.record_feedback(
                query=query,
                intent=intent,
                response="",  # Will be filled by response generator
                feedback_type="neutral",
                session_id=session_id
            )

            return intent

        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return "GENERAL"

    async def _classify_with_llm(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Classify intent using LLM

        Args:
            query: User query
            context: Conversation context

        Returns:
            Intent category
        """
        formatted = self.intent_prompt.format_messages(
            query=query,
            context=context or {}
        )

        # Try GROQ first (free)
        if self.groq_llm:
            try:
                response = await self.groq_llm.ainvoke(formatted)
                intent = response.content.strip().upper()

                # Validate intent
                if intent in self.INTENTS:
                    logger.info(f"GROQ classified intent: {intent}")

                    # Track token usage (GROQ is free but good to track)
                    # Approximate token count
                    token_count = len(query.split()) * 2
                    self.token_manager.track_usage("groq-llama-70b", token_count, 10)

                    return intent
            except Exception as e:
                logger.warning(f"GROQ classification failed: {e}")

        # Fallback to OpenAI
        if self.openai_llm:
            try:
                # Check token budget
                if not self.token_manager.can_use_model("gpt-4.1-nano-2025-04-14", 100):
                    logger.warning("OpenAI token budget exceeded")
                    return self._rule_based_classification(query)

                response = await self.openai_llm.ainvoke(formatted)
                intent = response.content.strip().upper()

                if intent in self.INTENTS:
                    logger.info(f"OpenAI classified intent: {intent}")

                    # Track token usage
                    token_count = len(query.split()) * 2
                    self.token_manager.track_usage("gpt-4.1-nano-2025-04-14", token_count, 10)

                    return intent
            except Exception as e:
                logger.warning(f"OpenAI classification failed: {e}")

        # Final fallback to rule-based
        return self._rule_based_classification(query)

    def _map_response_type_to_intent(self, response_type: str) -> str:
        """
        Map disambiguation response type to intent

        Args:
            response_type: Response type from disambiguator

        Returns:
            Intent category
        """
        mapping = {
            "status": "STATUS",
            "error": "ERROR",
            "metric": "METRIC",
            "help": "HELP",
            "general": "GENERAL"
        }
        return mapping.get(response_type, "GENERAL")

    def _rule_based_classification(self, query: str) -> str:
        """
        Rule-based intent classification as final fallback

        Args:
            query: User query

        Returns:
            Intent category
        """
        query_lower = query.lower()

        # Check for patterns
        if any(word in query_lower for word in ["stato", "status", "funziona", "attivo"]):
            return "STATUS"
        elif any(word in query_lower for word in ["errore", "problema", "fallito", "rotto"]):
            return "ERROR"
        elif any(word in query_lower for word in ["metriche", "performance", "statistiche"]):
            return "METRIC"
        elif any(word in query_lower for word in ["configura", "imposta", "setup"]):
            return "CONFIG"
        elif any(word in query_lower for word in ["aiuto", "come", "help", "?"]):
            return "HELP"
        elif any(word in query_lower for word in ["report", "riassunto", "sommario"]):
            return "REPORT"
        elif any(word in query_lower for word in ["codice", "api", "database", "docker"]):
            return "TECHNICAL"
        else:
            return "GENERAL"

    async def record_correction(
        self,
        query: str,
        detected_intent: str,
        correct_intent: str,
        session_id: Optional[str] = None
    ):
        """
        Record an intent correction for learning

        Args:
            query: Original query
            detected_intent: What we detected
            correct_intent: What it should have been
            session_id: Session identifier
        """
        await self.learning_system.record_feedback(
            query=query,
            intent=detected_intent,
            response="",
            feedback_type="correction",
            correction_data={"correct_intent": correct_intent},
            session_id=session_id
        )

        logger.info(f"Intent correction recorded: {detected_intent} → {correct_intent}")

    def get_intent_confidence(self, query: str) -> Tuple[str, float]:
        """
        Get intent with confidence score

        Args:
            query: User query

        Returns:
            Tuple of (intent, confidence)
        """
        # Check learned patterns
        learned = self.learning_system.suggest_intent(query)
        if learned:
            return learned

        # Use rule-based with lower confidence
        intent = self._rule_based_classification(query)
        confidence = 0.5  # Medium confidence for rule-based

        return intent, confidence

    def explain_intent(self, intent: str) -> str:
        """
        Get explanation for an intent

        Args:
            intent: Intent category

        Returns:
            Human-readable explanation
        """
        return self.INTENTS.get(intent, "Unknown intent")

    async def analyze_batch(
        self,
        queries: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple queries in batch

        Args:
            queries: List of queries

        Returns:
            List of analysis results
        """
        results = []

        for query in queries:
            intent = await self.classify(query)
            confidence = self.get_intent_confidence(query)[1]

            results.append({
                "query": query,
                "intent": intent,
                "confidence": confidence,
                "explanation": self.explain_intent(intent)
            })

        return results