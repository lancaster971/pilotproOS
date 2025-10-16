"""
MilhenaCore - Main orchestrator for Business Workflow Assistant
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MilhenaConfig:
    """Configuration for Milhena Assistant"""
    database_url: str = os.getenv("DATABASE_URL", "")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    langchain_tracing: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    langchain_project: str = os.getenv("LANGCHAIN_PROJECT", "milhena-production")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    max_response_length: int = 2000  # Increased for complete responses
    cache_ttl: int = 300  # 5 minutes
    rate_limit_per_minute: int = 30
    budget_limit_per_day: float = 10.0  # $10 per day

class MilhenaRole:
    """
    Milhena è l'interfaccia business-friendly per i workflow n8n
    """

    CAPABILITIES = {
        "monitor": "Monitoraggio esecuzioni workflow",
        "translate": "Traduzione tech → business language",
        "report": "Generazione report in linguaggio naturale",
        "alert": "Notifiche problemi in modo comprensibile",
        "assist": "Supporto cliente senza esporre tecnicismi"
    }

    PROTECTION = {
        "hide": ["n8n", "PostgreSQL", "Docker", "nodes", "webhook"],
        "translate_to": ["processo", "database", "sistema", "passaggi", "integrazione"],
        "deflect_technical": "Per informazioni tecniche contatta il supporto IT"
    }

class MilhenaCore:
    """
    Core orchestrator for Milhena Business Assistant
    """

    def __init__(self, config: Optional[MilhenaConfig] = None):
        self.config = config or MilhenaConfig()
        self._setup_logging()
        self.role = MilhenaRole()
        self._initialize_components()

    def _setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _initialize_components(self):
        """Initialize all Milhena components"""
        from .masking import TechnicalMaskingEngine
        from .intent_analyzer import IntentAnalyzer
        from .response_generator import ResponseGenerator
        from .llm_strategy import LLMRouter
        from .cache_manager import CacheManager

        self.masking_engine = TechnicalMaskingEngine()
        self.intent_analyzer = IntentAnalyzer(self.config)
        self.response_generator = ResponseGenerator(self.config, self.masking_engine)
        self.llm_router = LLMRouter(self.config)
        self.cache_manager = CacheManager(self.config)

        logger.info("Milhena Core initialized successfully")

    async def process_query(
        self,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing user queries
        """
        try:
            # Check cache first
            cached_response = await self.cache_manager.get(query, session_id)
            if cached_response:
                logger.info(f"Cache hit for session {session_id}")
                return cached_response

            # Analyze intent
            intent = await self.intent_analyzer.classify(query)
            logger.info(f"Intent classified as: {intent}")

            # Route based on intent
            if intent == "TECHNICAL":
                # Deflect technical queries
                response = self.role.PROTECTION["deflect_technical"]
            else:
                # Process business query
                response = await self._process_business_query(
                    query=query,
                    intent=intent,
                    context=context
                )

            # Mask any technical terms that might have slipped through
            masked_response = self.masking_engine.mask(response)

            # Prepare result
            result = {
                "success": True,
                "response": masked_response,
                "intent": intent,
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id
            }

            # Cache the result
            await self.cache_manager.set(query, session_id, result)

            return result

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "success": False,
                "response": "Mi dispiace, c'è stato un problema temporaneo. Riprova tra qualche istante.",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id
            }

    async def _process_business_query(
        self,
        query: str,
        intent: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process business-related queries
        """
        # Get appropriate LLM based on query complexity
        complexity = self._assess_complexity(query)
        llm = await self.llm_router.get_llm(complexity)

        # Generate response
        response = await self.response_generator.generate(
            query=query,
            intent=intent,
            llm=llm,
            context=context
        )

        return response

    def _assess_complexity(self, query: str) -> str:
        """
        Assess query complexity for LLM selection
        """
        word_count = len(query.split())

        if word_count < 10:
            return "simple"
        elif word_count < 30:
            return "medium"
        else:
            return "complex"

    async def analyze_with_masking(
        self,
        data: Dict[str, Any],
        analysis_type: str
    ) -> Dict[str, Any]:
        """
        Analyze data with technical masking applied
        Used by n8n integration
        """
        # Mask all technical terms in the data
        masked_data = self.masking_engine.mask_json(data)

        # Perform analysis based on type
        if analysis_type == "summary":
            result = await self._generate_summary(masked_data)
        elif analysis_type == "validation":
            result = await self._validate_data(masked_data)
        elif analysis_type == "error_translation":
            result = await self._translate_errors(masked_data)
        else:
            result = {"message": "Tipo di analisi non riconosciuto"}

        return result

    async def _generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate business-friendly summary"""
        summary = f"Processo completato con {len(data.get('items', []))} elementi elaborati"
        return {"summary": summary}

    async def _validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean data"""
        is_valid = all(key not in str(data).lower() for key in self.role.PROTECTION["hide"])
        return {"is_valid": is_valid, "cleaned_data": data}

    async def _translate_errors(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Translate technical errors to business language"""
        if "error" in data:
            error_msg = data["error"]
            business_msg = self.masking_engine.mask(error_msg)
            return {"original": error_msg, "business_friendly": business_msg}
        return {"message": "Nessun errore da tradurre"}

    async def translate_error(
        self,
        error: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Translate technical error to business-friendly message
        """
        # Apply masking
        masked = self.masking_engine.mask(error)

        # Further simplify if needed
        if any(term in masked.lower() for term in ["error", "exception", "failed"]):
            masked = "Si è verificato un problema temporaneo. Il team tecnico è stato notificato."

        return masked

    def assess_severity(self, error_message: str) -> str:
        """
        Assess error severity
        """
        error_lower = error_message.lower()

        if any(term in error_lower for term in ["critical", "fatal", "emergency"]):
            return "critical"
        elif any(term in error_lower for term in ["error", "failed", "refused"]):
            return "high"
        elif any(term in error_lower for term in ["warning", "timeout", "slow"]):
            return "medium"
        else:
            return "low"