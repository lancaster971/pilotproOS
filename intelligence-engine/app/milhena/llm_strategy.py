"""
LLMRouter - Intelligent routing between GROQ (free) and OpenAI (premium)
Manages fallback chains and token budgets
"""
from typing import Dict, Any, Optional, List
import logging
import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMRouter:
    """
    Routes queries to appropriate LLM based on:
    - Complexity
    - Token budget
    - Availability
    - Cost optimization
    """

    def __init__(self, config: Any):
        self.config = config
        self._initialize_all_llms()

        # Import token manager
        from .token_manager import TokenManager
        self.token_manager = TokenManager()

    def _initialize_all_llms(self):
        """Initialize all available LLMs"""
        self.llms = {
            "groq": {},
            "openai": {}
        }

        # GROQ Models (FREE)
        if os.getenv("GROQ_API_KEY"):
            groq_api_key = os.getenv("GROQ_API_KEY")

            self.llms["groq"]["llama-70b"] = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                api_key=groq_api_key
            )

            self.llms["groq"]["llama-90b"] = ChatGroq(
                model="llama-3.2-90b-text-preview",
                temperature=0.7,
                api_key=groq_api_key
            )

            self.llms["groq"]["mixtral"] = ChatGroq(
                model="mixtral-8x7b-32768",
                temperature=0.7,
                api_key=groq_api_key
            )

            self.llms["groq"]["deepseek"] = ChatGroq(
                model="deepseek-r1-distill-llama-70b",
                temperature=0.3,  # Lower for reasoning
                api_key=groq_api_key
            )

            logger.info(f"Initialized {len(self.llms['groq'])} GROQ models")

        # OpenAI Models (OFFERTA SPECIALE)
        if os.getenv("OPENAI_API_KEY"):
            openai_api_key = os.getenv("OPENAI_API_KEY")

            # 10M Token Budget Models
            self.llms["openai"]["nano"] = ChatOpenAI(
                model="gpt-4.1-nano-2025-04-14",
                temperature=0.7,
                api_key=openai_api_key
            )

            self.llms["openai"]["mini"] = ChatOpenAI(
                model="gpt-4o-mini-2024-07-18",
                temperature=0.7,
                api_key=openai_api_key
            )

            # 1M Token Budget Models
            self.llms["openai"]["4o"] = ChatOpenAI(
                model="gpt-4o-2024-11-20",
                temperature=0.7,
                api_key=openai_api_key
            )

            self.llms["openai"]["o1"] = ChatOpenAI(
                model="o1-2024-12-17",
                temperature=0.3,  # Reasoning model
                api_key=openai_api_key
            )

            logger.info(f"Initialized {len(self.llms['openai'])} OpenAI models")

    async def get_llm(
        self,
        complexity: str,
        task_type: Optional[str] = None,
        require_reasoning: bool = False,
        max_tokens: Optional[int] = None
    ) -> Optional[Any]:
        """
        Get appropriate LLM based on requirements

        Args:
            complexity: "simple", "medium", or "complex"
            task_type: Optional task type for specialized routing
            require_reasoning: If true, prefer reasoning models
            max_tokens: Maximum tokens needed

        Returns:
            Selected LLM or None
        """
        # Build preference chain
        preference_chain = self._build_preference_chain(
            complexity, task_type, require_reasoning
        )

        # Try each model in preference order
        for provider, model_key in preference_chain:
            if provider == "groq":
                if model_key in self.llms["groq"]:
                    llm = self.llms["groq"][model_key]
                    logger.info(f"Selected GROQ {model_key} (FREE)")
                    return llm

            elif provider == "openai":
                if model_key in self.llms["openai"]:
                    llm = self.llms["openai"][model_key]
                    model_name = llm.model_name

                    # Check token budget
                    estimated_tokens = max_tokens or 1000
                    if self.token_manager.can_use_model(model_name, estimated_tokens):
                        logger.info(f"Selected OpenAI {model_key}")
                        return llm
                    else:
                        logger.warning(f"Token budget exceeded for {model_name}")

        logger.error("No LLM available for request")
        return None

    def _build_preference_chain(
        self,
        complexity: str,
        task_type: Optional[str] = None,
        require_reasoning: bool = False
    ) -> List[Tuple[str, str]]:
        """
        Build preference chain for LLM selection

        Returns:
            List of (provider, model_key) tuples in preference order
        """
        chain = []

        if require_reasoning:
            # Reasoning tasks
            chain.extend([
                ("groq", "deepseek"),      # Free reasoning
                ("openai", "o1"),          # Premium reasoning
                ("openai", "4o"),          # Fallback
            ])
        elif complexity == "simple":
            # Simple tasks - prioritize free
            chain.extend([
                ("groq", "llama-70b"),     # Free & fast
                ("groq", "mixtral"),       # Free alternative
                ("openai", "nano"),        # Cheapest OpenAI
                ("openai", "mini"),        # Fallback
            ])
        elif complexity == "medium":
            # Medium tasks
            chain.extend([
                ("groq", "llama-90b"),     # Free large model
                ("groq", "llama-70b"),     # Free fallback
                ("openai", "mini"),        # Good balance
                ("openai", "nano"),        # Cheaper fallback
            ])
        else:
            # Complex tasks
            chain.extend([
                ("openai", "4o"),          # Best quality
                ("groq", "llama-90b"),     # Free alternative
                ("openai", "mini"),        # Cheaper fallback
                ("groq", "llama-70b"),     # Final free option
            ])

        # Add task-specific preferences
        if task_type == "code":
            # Prioritize Mixtral for code
            chain.insert(0, ("groq", "mixtral"))
        elif task_type == "translation":
            # Prioritize larger models
            chain.insert(0, ("groq", "llama-90b"))

        return chain

    def get_fallback_chain(self, primary_model: str) -> List[Any]:
        """
        Get fallback chain for a model

        Args:
            primary_model: Primary model that failed

        Returns:
            List of fallback LLMs
        """
        fallbacks = []

        # If GROQ failed, try other GROQ models first
        if "llama" in primary_model or "mixtral" in primary_model:
            for model_key, llm in self.llms["groq"].items():
                if model_key != primary_model:
                    fallbacks.append(llm)

        # Then add OpenAI models if budget allows
        for model_key in ["nano", "mini"]:  # Only cheap models for fallback
            if model_key in self.llms["openai"]:
                llm = self.llms["openai"][model_key]
                if self.token_manager.can_use_model(llm.model_name, 500):
                    fallbacks.append(llm)

        return fallbacks

    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all LLMs

        Returns:
            Status dictionary
        """
        status = {
            "groq": {
                "available": len(self.llms["groq"]),
                "models": list(self.llms["groq"].keys())
            },
            "openai": {
                "available": len(self.llms["openai"]),
                "models": list(self.llms["openai"].keys()),
                "token_usage": {}
            }
        }

        # Add token usage for OpenAI
        for model_key, llm in self.llms["openai"].items():
            usage = self.token_manager.get_usage_stats(llm.model_name)
            if usage and "error" not in usage:
                status["openai"]["token_usage"][model_key] = {
                    "used": usage.get("total_tokens", 0),
                    "daily_percent": usage.get("daily_usage_percent", 0),
                    "total_percent": usage.get("total_usage_percent", 0)
                }

        return status

    async def test_all_models(self) -> Dict[str, Any]:
        """
        Test all available models

        Returns:
            Test results
        """
        results = {}
        test_prompt = "Say 'Hello' in Italian in 3 words or less."

        # Test GROQ models
        for model_key, llm in self.llms["groq"].items():
            try:
                response = await llm.ainvoke(test_prompt)
                results[f"groq_{model_key}"] = {
                    "success": True,
                    "response": response.content[:50]
                }
            except Exception as e:
                results[f"groq_{model_key}"] = {
                    "success": False,
                    "error": str(e)
                }

        # Test OpenAI models
        for model_key, llm in self.llms["openai"].items():
            try:
                # Check budget first
                if not self.token_manager.can_use_model(llm.model_name, 20):
                    results[f"openai_{model_key}"] = {
                        "success": False,
                        "error": "Token budget exceeded"
                    }
                    continue

                response = await llm.ainvoke(test_prompt)
                results[f"openai_{model_key}"] = {
                    "success": True,
                    "response": response.content[:50]
                }

                # Track usage
                self.token_manager.track_usage(llm.model_name, 10, 10)

            except Exception as e:
                results[f"openai_{model_key}"] = {
                    "success": False,
                    "error": str(e)
                }

        return results

    def estimate_cost(self, tokens: int, model_key: str) -> float:
        """
        Estimate cost for token usage

        Args:
            tokens: Number of tokens
            model_key: Model key

        Returns:
            Estimated cost in USD
        """
        # GROQ is free
        if "groq" in model_key.lower() or model_key in self.llms["groq"]:
            return 0.0

        # OpenAI pricing (simplified)
        costs = {
            "nano": 0.00015,  # per 1K tokens
            "mini": 0.0006,
            "4o": 0.01,
            "o1": 0.015
        }

        for key, cost_per_1k in costs.items():
            if key in model_key.lower():
                return (tokens / 1000) * cost_per_1k

        return 0.0