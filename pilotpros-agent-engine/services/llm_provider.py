"""
LLM Provider Service with multiple fallback options
Supports OpenAI, Anthropic, and Ollama (free local)
"""

import os
import logging
from typing import Optional, Any, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    MOCK = "mock"  # For testing without API


class LLMService:
    """
    Service for managing LLM providers with fallback chain
    """

    def __init__(self, settings):
        """
        Initialize LLM service with settings

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.providers = self._initialize_providers()
        self.current_provider = None

    def _initialize_providers(self) -> Dict[LLMProvider, Any]:
        """
        Initialize available LLM providers

        Returns:
            Dictionary of initialized providers
        """
        providers = {}

        # Try OpenAI
        if self.settings.OPENAI_API_KEY:
            try:
                from langchain_openai import ChatOpenAI
                providers[LLMProvider.OPENAI] = ChatOpenAI(
                    api_key=self.settings.OPENAI_API_KEY,
                    model="gpt-4-turbo-preview",
                    temperature=0.7
                )
                logger.info("✅ OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"❌ OpenAI initialization failed: {e}")

        # Try Anthropic
        if self.settings.ANTHROPIC_API_KEY:
            try:
                from langchain_anthropic import ChatAnthropic
                providers[LLMProvider.ANTHROPIC] = ChatAnthropic(
                    api_key=self.settings.ANTHROPIC_API_KEY,
                    model="claude-3-sonnet-20240229",
                    temperature=0.7
                )
                logger.info("✅ Anthropic provider initialized")
            except Exception as e:
                logger.warning(f"❌ Anthropic initialization failed: {e}")

        # Try Ollama (FREE LOCAL)
        try:
            from langchain_community.llms import Ollama
            # Check if Ollama is running
            import requests
            response = requests.get(f"{self.settings.OLLAMA_HOST}/api/tags", timeout=2)
            if response.status_code == 200:
                providers[LLMProvider.OLLAMA] = Ollama(
                    base_url=self.settings.OLLAMA_HOST,
                    model="llama2",  # or "mistral", "codellama", etc.
                    temperature=0.7
                )
                logger.info("✅ Ollama provider initialized (FREE LOCAL)")
            else:
                logger.warning("❌ Ollama not responding")
        except Exception as e:
            logger.warning(f"❌ Ollama initialization failed: {e}")

        # Always add Mock provider as last fallback
        providers[LLMProvider.MOCK] = MockLLM()
        logger.info("✅ Mock provider initialized (fallback)")

        return providers

    def get_llm(self) -> Any:
        """
        Get the best available LLM provider

        Returns:
            LLM instance or Mock if none available
        """
        # Priority order: OpenAI > Anthropic > Ollama > Mock
        priority = [
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
            LLMProvider.OLLAMA,
            LLMProvider.MOCK
        ]

        for provider in priority:
            if provider in self.providers:
                self.current_provider = provider
                logger.info(f"Using LLM provider: {provider.value}")
                return self.providers[provider]

        # Should never reach here due to Mock
        logger.error("No LLM provider available!")
        return MockLLM()

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about available providers

        Returns:
            Provider status information
        """
        return {
            "available_providers": [p.value for p in self.providers.keys()],
            "current_provider": self.current_provider.value if self.current_provider else None,
            "has_paid_api": any(p in self.providers for p in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC]),
            "has_local": LLMProvider.OLLAMA in self.providers,
            "fallback_available": LLMProvider.MOCK in self.providers
        }


class MockLLM:
    """
    Mock LLM for testing and fallback
    Provides pattern-based responses without API calls
    """

    def __init__(self):
        self.responses = {
            "workflow": "I processi aziendali sono attualmente operativi. Suggerisco di monitorare le metriche di performance per identificare opportunità di ottimizzazione.",
            "performance": "Le performance del sistema mostrano un'efficienza del 75%. Ci sono margini di miglioramento del 20-30% attraverso l'automazione.",
            "error": "Ho rilevato alcuni errori ricorrenti nei processi. Consiglio un'analisi approfondita per identificare le cause principali.",
            "optimization": "Le opportunità di ottimizzazione includono: automazione dei task ripetitivi, ottimizzazione dei tempi di attesa, e miglioramento del flusso dati.",
            "default": "Sono l'assistente PilotPro. Posso aiutarti ad analizzare i processi aziendali e identificare opportunità di miglioramento."
        }

    def invoke(self, prompt: str, **kwargs) -> Any:
        """Mock invoke method compatible with LangChain"""
        return self._generate_response(prompt)

    def __call__(self, prompt: str, **kwargs) -> str:
        """Make the mock callable"""
        return self._generate_response(prompt)

    def _generate_response(self, prompt: str) -> str:
        """
        Generate a mock response based on keywords

        Args:
            prompt: Input prompt

        Returns:
            Mock response in Italian
        """
        prompt_lower = prompt.lower()

        # Check for keywords and return appropriate response
        for keyword, response in self.responses.items():
            if keyword in prompt_lower:
                return response

        return self.responses["default"]

    def generate(self, prompts, **kwargs):
        """Mock generate method for compatibility"""
        return [[self._generate_response(p)] for p in prompts]

    def predict(self, text: str, **kwargs) -> str:
        """Mock predict method for compatibility"""
        return self._generate_response(text)


def setup_ollama_instructions():
    """
    Instructions for setting up Ollama locally (FREE)
    """
    return """
    🚀 SETUP OLLAMA (FREE LOCAL LLM):

    1. INSTALL OLLAMA:
       - Mac: brew install ollama
       - Linux: curl -fsSL https://ollama.ai/install.sh | sh
       - Windows: Download from https://ollama.ai/download

    2. START OLLAMA:
       ollama serve

    3. PULL A MODEL (choose one):
       ollama pull llama2        # 7B parameters, good general purpose
       ollama pull mistral       # 7B, faster and efficient
       ollama pull codellama     # 7B, optimized for code
       ollama pull phi          # 2.7B, very small and fast

    4. VERIFY:
       curl http://localhost:11434/api/tags

    5. SET IN .env:
       OLLAMA_HOST=http://localhost:11434

    That's it! Free local LLM ready to use.

    For Docker on Mac, use:
       OLLAMA_HOST=http://host.docker.internal:11434
    """