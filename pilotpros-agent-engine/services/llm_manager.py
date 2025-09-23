"""
Enhanced LLM Manager with ALL providers and smart selection
Chooses the right model based on task complexity and cost
"""

import os
import logging
from typing import Optional, Any, Dict, List
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"        # Basic Q&A, summaries
    MODERATE = "moderate"    # Analysis, reports
    COMPLEX = "complex"      # Deep reasoning, creativity
    CRITICAL = "critical"    # High-stakes decisions


@dataclass
class LLMModel:
    """LLM Model configuration"""
    provider: str
    model: str
    tier: str  # free, cheap, premium
    cost_per_1k: float  # USD per 1000 tokens
    capabilities: List[TaskComplexity]
    speed: str  # fast, medium, slow
    quality: str  # low, medium, high, very_high
    context_window: int
    requires_api_key: bool


class LLMManager:
    """
    Complete LLM Manager with all providers
    """

    # Complete model catalog
    MODELS = {
        # OpenAI Models
        "gpt-4-turbo": LLMModel(
            provider="openai", model="gpt-4-turbo-preview", tier="premium",
            cost_per_1k=0.03, capabilities=[TaskComplexity.COMPLEX, TaskComplexity.CRITICAL],
            speed="medium", quality="very_high", context_window=128000, requires_api_key=True
        ),
        "gpt-4": LLMModel(
            provider="openai", model="gpt-4", tier="premium",
            cost_per_1k=0.06, capabilities=[TaskComplexity.COMPLEX, TaskComplexity.CRITICAL],
            speed="slow", quality="very_high", context_window=8192, requires_api_key=True
        ),
        "gpt-3.5-turbo": LLMModel(
            provider="openai", model="gpt-3.5-turbo", tier="cheap",
            cost_per_1k=0.002, capabilities=[TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
            speed="fast", quality="high", context_window=16385, requires_api_key=True
        ),

        # Anthropic Models
        "claude-3-opus": LLMModel(
            provider="anthropic", model="claude-3-opus-20240229", tier="premium",
            cost_per_1k=0.075, capabilities=[TaskComplexity.COMPLEX, TaskComplexity.CRITICAL],
            speed="medium", quality="very_high", context_window=200000, requires_api_key=True
        ),
        "claude-3-sonnet": LLMModel(
            provider="anthropic", model="claude-3-sonnet-20240229", tier="cheap",
            cost_per_1k=0.018, capabilities=[TaskComplexity.MODERATE, TaskComplexity.COMPLEX],
            speed="fast", quality="high", context_window=200000, requires_api_key=True
        ),
        "claude-3-haiku": LLMModel(
            provider="anthropic", model="claude-3-haiku-20240307", tier="cheap",
            cost_per_1k=0.0015, capabilities=[TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
            speed="very_fast", quality="medium", context_window=200000, requires_api_key=True
        ),

        # Google Models
        "gemini-pro": LLMModel(
            provider="google", model="gemini-pro", tier="free",
            cost_per_1k=0.0, capabilities=[TaskComplexity.MODERATE, TaskComplexity.COMPLEX],
            speed="fast", quality="high", context_window=32000, requires_api_key=True
        ),
        "gemini-pro-vision": LLMModel(
            provider="google", model="gemini-pro-vision", tier="free",
            cost_per_1k=0.0, capabilities=[TaskComplexity.MODERATE],
            speed="fast", quality="high", context_window=16000, requires_api_key=True
        ),

        # Mistral Models
        "mistral-large": LLMModel(
            provider="mistral", model="mistral-large-latest", tier="cheap",
            cost_per_1k=0.024, capabilities=[TaskComplexity.COMPLEX],
            speed="medium", quality="high", context_window=32000, requires_api_key=True
        ),
        "mistral-medium": LLMModel(
            provider="mistral", model="mistral-medium-latest", tier="cheap",
            cost_per_1k=0.0027, capabilities=[TaskComplexity.MODERATE],
            speed="fast", quality="medium", context_window=32000, requires_api_key=True
        ),
        "mistral-small": LLMModel(
            provider="mistral", model="mistral-small-latest", tier="cheap",
            cost_per_1k=0.0006, capabilities=[TaskComplexity.SIMPLE],
            speed="very_fast", quality="medium", context_window=32000, requires_api_key=True
        ),

        # Cohere Models
        "command-r-plus": LLMModel(
            provider="cohere", model="command-r-plus", tier="cheap",
            cost_per_1k=0.03, capabilities=[TaskComplexity.COMPLEX],
            speed="medium", quality="high", context_window=128000, requires_api_key=True
        ),
        "command-r": LLMModel(
            provider="cohere", model="command-r", tier="cheap",
            cost_per_1k=0.0015, capabilities=[TaskComplexity.MODERATE],
            speed="fast", quality="medium", context_window=128000, requires_api_key=True
        ),

        # Groq Models (FAST!)
        "groq-llama2-70b": LLMModel(
            provider="groq", model="llama2-70b-4096", tier="free",
            cost_per_1k=0.0, capabilities=[TaskComplexity.MODERATE, TaskComplexity.COMPLEX],
            speed="ultra_fast", quality="high", context_window=4096, requires_api_key=True
        ),
        "groq-mixtral": LLMModel(
            provider="groq", model="mixtral-8x7b-32768", tier="free",
            cost_per_1k=0.0, capabilities=[TaskComplexity.MODERATE],
            speed="ultra_fast", quality="high", context_window=32768, requires_api_key=True
        ),

        # Together AI Models
        "together-llama2-70b": LLMModel(
            provider="together", model="meta-llama/Llama-2-70b-chat-hf", tier="cheap",
            cost_per_1k=0.0009, capabilities=[TaskComplexity.MODERATE],
            speed="fast", quality="high", context_window=4096, requires_api_key=True
        ),

        # Perplexity Models
        "perplexity-sonar-large": LLMModel(
            provider="perplexity", model="sonar-large-32k-chat", tier="cheap",
            cost_per_1k=0.001, capabilities=[TaskComplexity.MODERATE],
            speed="fast", quality="high", context_window=32000, requires_api_key=True
        ),

        # Replicate Models
        "replicate-llama2-70b": LLMModel(
            provider="replicate", model="meta/llama-2-70b-chat", tier="cheap",
            cost_per_1k=0.001, capabilities=[TaskComplexity.MODERATE],
            speed="medium", quality="high", context_window=4096, requires_api_key=True
        ),

        # Ollama Models (LOCAL FREE!)
        "ollama-llama2": LLMModel(
            provider="ollama", model="llama2", tier="free",
            cost_per_1k=0.0, capabilities=[TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
            speed="medium", quality="medium", context_window=4096, requires_api_key=False
        ),
        "ollama-mistral": LLMModel(
            provider="ollama", model="mistral", tier="free",
            cost_per_1k=0.0, capabilities=[TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
            speed="fast", quality="medium", context_window=8192, requires_api_key=False
        ),
        "ollama-codellama": LLMModel(
            provider="ollama", model="codellama", tier="free",
            cost_per_1k=0.0, capabilities=[TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
            speed="fast", quality="medium", context_window=4096, requires_api_key=False
        ),
        "ollama-phi": LLMModel(
            provider="ollama", model="phi", tier="free",
            cost_per_1k=0.0, capabilities=[TaskComplexity.SIMPLE],
            speed="very_fast", quality="low", context_window=2048, requires_api_key=False
        ),
        "ollama-neural-chat": LLMModel(
            provider="ollama", model="neural-chat", tier="free",
            cost_per_1k=0.0, capabilities=[TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
            speed="fast", quality="medium", context_window=4096, requires_api_key=False
        ),
        "ollama-starling": LLMModel(
            provider="ollama", model="starling-lm", tier="free",
            cost_per_1k=0.0, capabilities=[TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
            speed="fast", quality="medium", context_window=8192, requires_api_key=False
        ),
        "ollama-vicuna": LLMModel(
            provider="ollama", model="vicuna", tier="free",
            cost_per_1k=0.0, capabilities=[TaskComplexity.SIMPLE],
            speed="fast", quality="medium", context_window=2048, requires_api_key=False
        ),

        # HuggingFace Inference
        "huggingface-zephyr": LLMModel(
            provider="huggingface", model="HuggingFaceH4/zephyr-7b-beta", tier="free",
            cost_per_1k=0.0, capabilities=[TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
            speed="medium", quality="medium", context_window=4096, requires_api_key=True
        ),

        # AI21 Models
        "ai21-j2-ultra": LLMModel(
            provider="ai21", model="j2-ultra", tier="cheap",
            cost_per_1k=0.03, capabilities=[TaskComplexity.COMPLEX],
            speed="medium", quality="high", context_window=8192, requires_api_key=True
        ),

        # Mock (Always Available)
        "mock": LLMModel(
            provider="mock", model="mock", tier="free",
            cost_per_1k=0.0, capabilities=[TaskComplexity.SIMPLE],
            speed="instant", quality="low", context_window=1000, requires_api_key=False
        )
    }

    def __init__(self, settings):
        """
        Initialize LLM Manager

        Args:
            settings: Application settings with API keys
        """
        self.settings = settings
        self.available_models = self._detect_available_models()
        self.initialized_providers = {}

    def _detect_available_models(self) -> List[str]:
        """
        Detect which models are available based on API keys

        Returns:
            List of available model names
        """
        available = ["mock"]  # Always available

        # Check API keys
        if os.getenv("OPENAI_API_KEY"):
            available.extend(["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"])

        if os.getenv("ANTHROPIC_API_KEY"):
            available.extend(["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"])

        if os.getenv("GOOGLE_API_KEY"):
            available.extend(["gemini-pro", "gemini-pro-vision"])

        if os.getenv("MISTRAL_API_KEY"):
            available.extend(["mistral-large", "mistral-medium", "mistral-small"])

        if os.getenv("COHERE_API_KEY"):
            available.extend(["command-r-plus", "command-r"])

        if os.getenv("GROQ_API_KEY"):
            available.extend(["groq-llama2-70b", "groq-mixtral"])

        if os.getenv("TOGETHER_API_KEY"):
            available.extend(["together-llama2-70b"])

        if os.getenv("PERPLEXITY_API_KEY"):
            available.extend(["perplexity-sonar-large"])

        if os.getenv("REPLICATE_API_TOKEN"):
            available.extend(["replicate-llama2-70b"])

        if os.getenv("HUGGINGFACE_API_KEY"):
            available.extend(["huggingface-zephyr"])

        if os.getenv("AI21_API_KEY"):
            available.extend(["ai21-j2-ultra"])

        # Check Ollama
        if self._check_ollama():
            available.extend([
                "ollama-llama2", "ollama-mistral", "ollama-codellama",
                "ollama-phi", "ollama-neural-chat", "ollama-starling", "ollama-vicuna"
            ])

        logger.info(f"✅ Available models: {len(available)}")
        return available

    def _check_ollama(self) -> bool:
        """Check if Ollama is running"""
        try:
            import requests
            response = requests.get(f"{os.getenv('OLLAMA_HOST', 'http://localhost:11434')}/api/tags", timeout=1)
            return response.status_code == 200
        except:
            return False

    def select_model_for_task(
        self,
        task_complexity: TaskComplexity,
        prefer_free: bool = True,
        max_cost: float = 0.01
    ) -> Optional[str]:
        """
        Smart model selection based on task complexity

        Args:
            task_complexity: Complexity of the task
            prefer_free: Prefer free models when possible
            max_cost: Maximum cost per 1k tokens

        Returns:
            Best model name or None
        """
        suitable_models = []

        for model_name in self.available_models:
            if model_name not in self.MODELS:
                continue

            model = self.MODELS[model_name]

            # Check if model can handle complexity
            if task_complexity not in model.capabilities:
                continue

            # Check cost constraint
            if model.cost_per_1k > max_cost:
                continue

            suitable_models.append((model_name, model))

        if not suitable_models:
            return "mock"  # Fallback

        # Sort by preference
        def sort_key(item):
            name, model = item
            score = 0

            # Prefer free if requested
            if prefer_free and model.tier == "free":
                score -= 1000

            # Quality bonus
            quality_scores = {"low": 0, "medium": 10, "high": 20, "very_high": 30}
            score -= quality_scores.get(model.quality, 0)

            # Speed bonus
            speed_scores = {"instant": 50, "ultra_fast": 40, "very_fast": 30, "fast": 20, "medium": 10, "slow": 0}
            score -= speed_scores.get(model.speed, 0)

            # Cost penalty
            score += model.cost_per_1k * 100

            return score

        suitable_models.sort(key=sort_key)

        selected = suitable_models[0][0]
        model_info = self.MODELS[selected]

        logger.info(f"📊 Selected model: {selected}")
        logger.info(f"   Provider: {model_info.provider}")
        logger.info(f"   Quality: {model_info.quality}")
        logger.info(f"   Cost: ${model_info.cost_per_1k}/1k tokens")

        return selected

    def get_llm_client(self, model_name: str):
        """
        Get initialized LLM client for model

        Args:
            model_name: Name of the model

        Returns:
            LLM client instance
        """
        if model_name not in self.MODELS:
            logger.error(f"Unknown model: {model_name}")
            return None

        model = self.MODELS[model_name]

        # Check if already initialized
        if model_name in self.initialized_providers:
            return self.initialized_providers[model_name]

        # Initialize based on provider
        client = self._initialize_provider(model)
        if client:
            self.initialized_providers[model_name] = client

        return client

    def _initialize_provider(self, model: LLMModel):
        """Initialize specific provider"""
        try:
            if model.provider == "openai":
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model=model.model,
                    temperature=0.7
                )

            elif model.provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY"),
                    model=model.model,
                    temperature=0.7
                )

            elif model.provider == "google":
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(
                    google_api_key=os.getenv("GOOGLE_API_KEY"),
                    model=model.model,
                    temperature=0.7
                )

            elif model.provider == "mistral":
                from langchain_mistralai import ChatMistralAI
                return ChatMistralAI(
                    mistral_api_key=os.getenv("MISTRAL_API_KEY"),
                    model=model.model,
                    temperature=0.7
                )

            elif model.provider == "cohere":
                from langchain_cohere import ChatCohere
                return ChatCohere(
                    cohere_api_key=os.getenv("COHERE_API_KEY"),
                    model=model.model,
                    temperature=0.7
                )

            elif model.provider == "groq":
                from langchain_groq import ChatGroq
                return ChatGroq(
                    groq_api_key=os.getenv("GROQ_API_KEY"),
                    model_name=model.model,
                    temperature=0.7
                )

            elif model.provider == "ollama":
                from langchain_community.llms import Ollama
                return Ollama(
                    base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                    model=model.model,
                    temperature=0.7
                )

            elif model.provider == "mock":
                from services.llm_provider import MockLLM
                return MockLLM()

            else:
                logger.warning(f"Provider {model.provider} not implemented yet")
                return None

        except Exception as e:
            logger.error(f"Failed to initialize {model.provider}: {e}")
            return None

    def analyze_task_complexity(self, prompt: str) -> TaskComplexity:
        """
        Analyze task complexity from prompt

        Args:
            prompt: User prompt

        Returns:
            Task complexity level
        """
        prompt_lower = prompt.lower()

        # Critical indicators
        if any(word in prompt_lower for word in ["critical", "urgent", "importante", "decisione"]):
            return TaskComplexity.CRITICAL

        # Complex indicators
        if any(word in prompt_lower for word in ["analizza", "strategia", "complesso", "dettagliato"]):
            return TaskComplexity.COMPLEX

        # Moderate indicators
        if any(word in prompt_lower for word in ["report", "riassumi", "confronta", "valuta"]):
            return TaskComplexity.MODERATE

        # Default to simple
        return TaskComplexity.SIMPLE

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about available models

        Returns:
            Model information
        """
        info = {
            "total_models": len(self.MODELS),
            "available_models": len(self.available_models),
            "models_by_tier": {
                "free": [],
                "cheap": [],
                "premium": []
            },
            "models_by_provider": {},
            "recommendations": []
        }

        for model_name in self.available_models:
            if model_name in self.MODELS:
                model = self.MODELS[model_name]
                info["models_by_tier"][model.tier].append(model_name)

                if model.provider not in info["models_by_provider"]:
                    info["models_by_provider"][model.provider] = []
                info["models_by_provider"][model.provider].append(model_name)

        # Recommendations
        if not any(self.MODELS[m].tier == "free" for m in self.available_models if m != "mock"):
            info["recommendations"].append("Setup Ollama for free local LLM")

        if "groq" not in info["models_by_provider"]:
            info["recommendations"].append("Get Groq API key for ultra-fast free inference")

        if "gemini-pro" not in self.available_models:
            info["recommendations"].append("Get Google API key for free Gemini Pro access")

        return info