"""
LLMDisambiguator - Intelligent query disambiguation using LLMs
Uses GROQ for free calls, fallback to OpenAI for complex cases
"""
from typing import Dict, Any, Optional, Tuple
import logging
import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class DisambiguationResult(BaseModel):
    """Result from disambiguation process"""
    is_ambiguous: bool = Field(description="Whether the query is ambiguous")
    confidence: float = Field(description="Confidence score 0-1")
    clarified_intent: str = Field(description="Clarified intent")
    suggested_response_type: str = Field(description="Type of response needed")
    requires_technical_info: bool = Field(description="If technical information is needed")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")

class LLMDisambiguator:
    """
    Disambiguates ambiguous queries using LLM intelligence
    Example: "il sistema è andato a puttane" → "system failure inquiry"
    """

    def __init__(self, config: Any):
        self.config = config
        self._initialize_llms()
        self._setup_prompts()

    def _initialize_llms(self):
        """Initialize GROQ (free) and OpenAI (backup) models"""
        # GROQ - Free tier
        # FIX 2: Use request_timeout instead of timeout (LangChain best practice)
        self.groq_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            request_timeout=15.0,  # 15s timeout for disambiguation
            api_key=os.getenv("GROQ_API_KEY")
        ) if os.getenv("GROQ_API_KEY") else None

        # OpenAI - Offerta speciale models
        self.openai_nano = ChatOpenAI(
            model="gpt-4.1-nano-2025-04-14",  # 10M tokens
            temperature=0.3,
            request_timeout=15.0,  # 15s timeout
            api_key=os.getenv("OPENAI_API_KEY")
        ) if os.getenv("OPENAI_API_KEY") else None

        self.openai_mini = ChatOpenAI(
            model="gpt-4o-mini-2024-07-18",  # 10M tokens
            temperature=0.3,
            request_timeout=15.0,  # 15s timeout
            api_key=os.getenv("OPENAI_API_KEY")
        ) if os.getenv("OPENAI_API_KEY") else None

        logger.info(f"LLM Disambiguator initialized - GROQ: {bool(self.groq_llm)}, OpenAI: {bool(self.openai_nano)}")

    def _setup_prompts(self):
        """Setup disambiguation prompts"""
        self.disambiguation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at understanding user intent in business workflow contexts.
            Your task is to disambiguate unclear or ambiguous queries.

            Context: This is a business workflow monitoring system where users ask about:
            - Process status and health
            - Error conditions
            - Performance metrics
            - Integration issues

            Analyze the query and provide structured output."""),
            ("human", """Query: {query}

            Previous context: {context}

            Disambiguate this query and extract:
            1. Is it ambiguous? (true/false)
            2. Confidence score (0-1)
            3. Clarified intent in clear English
            4. What type of response is needed
            5. Does it require technical information?
            6. Key entities mentioned

            Common Italian slang translations:
            - "andato a puttane" = "failed/broken"
            - "casino" = "mess/chaos"
            - "fottuto" = "broken"
            - "merda" = "bad situation"

            Output JSON format:
            {{
                "is_ambiguous": boolean,
                "confidence": float,
                "clarified_intent": string,
                "suggested_response_type": "status"|"error"|"metric"|"help"|"general",
                "requires_technical_info": boolean,
                "entities": {{}}
            }}""")
        ])

        self.parser = JsonOutputParser(pydantic_object=DisambiguationResult)

    async def disambiguate(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DisambiguationResult:
        """
        Disambiguate an ambiguous query
        FIX 3: Removed nested asyncio.wait_for - trust LLM internal request_timeout

        Args:
            query: User query that may be ambiguous
            context: Previous conversation context

        Returns:
            DisambiguationResult with clarified intent
        """
        try:
            # Format prompt
            formatted = self.disambiguation_prompt.format_messages(
                query=query,
                context=context or {}
            )

            # Try GROQ first (free) - uses internal request_timeout=15s
            if self.groq_llm:
                try:
                    logger.info("Disambiguating with GROQ (free tier)")
                    response = await self.groq_llm.ainvoke(formatted)
                    result_dict = self.parser.parse(response.content)
                    result = DisambiguationResult(**result_dict) if isinstance(result_dict, dict) else result_dict
                    logger.info(f"GROQ disambiguation successful: {result.clarified_intent}")
                    return result
                except Exception as e:
                    logger.warning(f"GROQ disambiguation failed: {e}")

            # Fallback to OpenAI Nano - uses internal request_timeout=15s
            if self.openai_nano:
                try:
                    logger.info("Fallback to OpenAI Nano")
                    response = await self.openai_nano.ainvoke(formatted)
                    result_dict = self.parser.parse(response.content)
                    result = DisambiguationResult(**result_dict) if isinstance(result_dict, dict) else result_dict
                    logger.info(f"OpenAI Nano disambiguation successful: {result.clarified_intent}")
                    return result
                except Exception as e:
                    logger.warning(f"OpenAI Nano failed: {e}")

            # Fallback to OpenAI Mini if Nano fails - uses internal request_timeout=15s
            if self.openai_mini:
                logger.info("Final fallback to OpenAI Mini")
                response = await self.openai_mini.ainvoke(formatted)
                result_dict = self.parser.parse(response.content)
                result = DisambiguationResult(**result_dict) if isinstance(result_dict, dict) else result_dict
                return result

            # If all LLMs fail, return basic disambiguation
            logger.warning("All LLMs unavailable, using rule-based fallback")
            return self._rule_based_disambiguation(query)

        except Exception as e:
            logger.error(f"Disambiguation error: {e}")
            return self._rule_based_disambiguation(query)

    def _rule_based_disambiguation(self, query: str) -> DisambiguationResult:
        """
        Fallback rule-based disambiguation when LLMs unavailable
        """
        query_lower = query.lower()

        # Check for common patterns
        is_error = any(term in query_lower for term in [
            "puttane", "error", "problema", "failed", "rotto", "casino"
        ])

        is_status = any(term in query_lower for term in [
            "stato", "status", "come va", "funziona", "andamento"
        ])

        if is_error:
            return DisambiguationResult(
                is_ambiguous=True,
                confidence=0.6,
                clarified_intent="User is reporting a system error or failure",
                suggested_response_type="error",
                requires_technical_info=True,
                entities={"issue_type": "system_failure"}
            )
        elif is_status:
            return DisambiguationResult(
                is_ambiguous=False,
                confidence=0.7,
                clarified_intent="User is asking about system status",
                suggested_response_type="status",
                requires_technical_info=False,
                entities={"query_type": "status_check"}
            )
        else:
            return DisambiguationResult(
                is_ambiguous=True,
                confidence=0.3,
                clarified_intent="Unclear query requiring clarification",
                suggested_response_type="help",
                requires_technical_info=False,
                entities={}
            )

    async def improve_from_feedback(
        self,
        original_query: str,
        disambiguation_result: DisambiguationResult,
        user_feedback: str  # "correct" or "incorrect"
    ):
        """
        Learn from user feedback to improve future disambiguation
        """
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": original_query,
            "disambiguation": disambiguation_result.dict(),
            "feedback": user_feedback
        }

        # Store in learning system (will be implemented in learning.py)
        logger.info(f"Feedback stored for learning: {feedback_entry}")

    def assess_complexity(self, query: str) -> str:
        """
        Assess query complexity for LLM routing
        """
        word_count = len(query.split())

        # Check for technical terms
        technical_terms = ["workflow", "node", "execution", "webhook", "integration", "API"]
        has_technical = any(term.lower() in query.lower() for term in technical_terms)

        # Check for multiple questions
        question_marks = query.count("?")

        if word_count > 50 or question_marks > 2 or has_technical:
            return "complex"
        elif word_count > 20 or question_marks > 0:
            return "medium"
        else:
            return "simple"