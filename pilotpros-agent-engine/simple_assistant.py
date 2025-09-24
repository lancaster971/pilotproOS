"""
Simple Assistant - Direct OpenAI and OpenRouter integration
"""

import os
import logging
from typing import Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class SimpleAssistant:
    """Simple assistant that works with OpenAI and OpenRouter"""

    def __init__(self):
        """Initialize the assistant with multiple providers"""
        self.clients = {}
        self.available = False

        # Setup OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.clients['openai'] = OpenAI(api_key=openai_key)
            self.available = True
            logger.info("✅ OpenAI initialized")

        # Setup OpenRouter
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            self.clients['openrouter'] = OpenAI(
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1"
            )
            self.available = True
            logger.info("✅ OpenRouter initialized")

        # Setup Groq (gratis e veloce)
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            self.clients['groq'] = OpenAI(
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1"
            )
            self.available = True
            logger.info("✅ Groq initialized (FREE)")

        # Setup Together AI
        together_key = os.getenv("TOGETHER_API_KEY")
        if together_key:
            self.clients['together'] = OpenAI(
                api_key=together_key,
                base_url="https://api.together.xyz/v1"
            )
            self.available = True
            logger.info("✅ Together AI initialized")

        # Setup DeepInfra
        deepinfra_key = os.getenv("DEEPINFRA_API_KEY")
        if deepinfra_key:
            self.clients['deepinfra'] = OpenAI(
                api_key=deepinfra_key,
                base_url="https://api.deepinfra.com/v1/openai"
            )
            self.available = True
            logger.info("✅ DeepInfra initialized")

        if not self.available:
            logger.warning("⚠️ No API keys available - SimpleAssistant limited")

    def get_available_models(self) -> Dict[str, list]:
        """Ritorna tutti i modelli disponibili per provider"""
        available = {}

        if 'groq' in self.clients:
            available['groq'] = [
                "llama-3.2-90b-vision-preview",
                "llama-3.2-70b-versatile",
                "llama-3.1-70b-versatile",
                "mixtral-8x7b-32768",
                "gemma2-9b-it"
            ]

        if 'openrouter' in self.clients:
            available['openrouter'] = [
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4o",
                "google/gemini-pro-1.5",
                "qwen/qwen-2.5-72b-instruct",
                "meta-llama/llama-3.2-90b-instruct"
            ]

        if 'openai' in self.clients:
            available['openai'] = [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-3.5-turbo"
            ]

        if 'together' in self.clients:
            available['together'] = [
                "meta-llama/Llama-3.2-90B-Vision-Instruct",
                "Qwen/Qwen2.5-72B-Instruct-Turbo"
            ]

        if 'deepinfra' in self.clients:
            available['deepinfra'] = [
                "meta-llama/Meta-Llama-3.1-70B-Instruct",
                "Qwen/Qwen2.5-72B-Instruct"
            ]

        return available

    def answer_question(self,
                       question: str,
                       language: str = "italian",
                       provider: Optional[str] = None,
                       model: Optional[str] = None,
                       prefer_free: bool = True) -> Dict[str, Any]:
        """
        Answer a question using specified or auto-selected model

        Args:
            question: The question to answer
            language: Language for response ('italian' or 'english')
            provider: Specific provider to use ('openai', 'groq', 'openrouter', etc.)
            model: Specific model to use (e.g., 'gpt-4o', 'llama-3.2-90b-vision-preview')
            prefer_free: Prefer free models like Groq (default True)

        Returns:
            Response dict with answer, confidence, model info

        Examples:
            # Usa modello gratuito automaticamente
            answer_question("ciao")

            # Usa GPT-4o specificamente
            answer_question("ciao", provider="openai", model="gpt-4o")

            # Usa Claude via OpenRouter
            answer_question("ciao", provider="openrouter", model="anthropic/claude-3.5-sonnet")
        """
        if not self.available:
            return {
                "success": False,
                "answer": "Assistant non disponibile. Configura API keys.",
                "confidence": 0.0
            }

        try:
            # Create system prompt based on language
            if language == "italian":
                system_prompt = """Sei PilotPro Assistant, un assistente AI per il sistema PilotProOS.
                Rispondi in italiano in modo professionale e conciso.
                Sei esperto di processi aziendali, automazione e analisi dati."""
            else:
                system_prompt = """You are PilotPro Assistant, an AI assistant for PilotProOS system.
                Answer professionally and concisely.
                You are an expert in business processes, automation, and data analysis."""

            response = None
            used_model = None
            used_provider = None

            # Se specificato un provider e modello, usa quelli
            if provider and model and provider in self.clients:
                try:
                    response = self.clients[provider].chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": question}
                        ],
                        temperature=0.7,
                        max_tokens=500
                    )
                    used_model = model
                    used_provider = provider
                    logger.info(f"Using specified {provider}/{model}")
                except Exception as e:
                    logger.error(f"Failed with {provider}/{model}: {e}")
                    # Continue to auto-selection if specified model fails

            # Auto-selection if no response yet
            if not response:
                # Define models per provider
                provider_models = {
                'groq': [  # GRATIS e velocissimi
                    "llama-3.2-90b-vision-preview",  # Llama 3.2 90B con vision
                    "llama-3.2-70b-versatile",       # Llama 3.2 70B
                    "llama-3.1-70b-versatile",       # Llama 3.1 70B
                    "mixtral-8x7b-32768",            # Mixtral veloce
                    "gemma2-9b-it"                   # Gemma 2 9B
                ],
                'together': [  # Modelli open source
                    "meta-llama/Llama-3.2-90B-Vision-Instruct",
                    "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
                    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                    "Qwen/Qwen2.5-72B-Instruct-Turbo",
                    "mistralai/Mixtral-8x22B-Instruct-v0.1",
                    "deepseek-ai/deepseek-coder-33b-instruct"
                ],
                'deepinfra': [  # Economici
                    "meta-llama/Meta-Llama-3.1-405B-Instruct",
                    "meta-llama/Meta-Llama-3.1-70B-Instruct",
                    "Qwen/Qwen2.5-72B-Instruct",
                    "mistralai/Mistral-7B-Instruct-v0.3",
                    "google/gemma-2-27b-it"
                ]
            }

            # Order providers based on prefer_free setting
            if prefer_free:
                provider_order = ['groq', 'deepinfra', 'together', 'openrouter', 'openai']
            else:
                provider_order = ['openai', 'openrouter', 'together', 'groq', 'deepinfra']

            # Try providers in order
            for prov in provider_order:
                if response:
                    break
                if prov not in self.clients:
                    continue

                if prov == 'groq':
                    for model in provider_models.get('groq', []):
                        try:
                            response = self.clients['groq'].chat.completions.create(
                                model=model,
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": question}
                                ],
                                temperature=0.7,
                                max_tokens=500
                            )
                            used_model = model
                            used_provider = "Groq (FREE)"
                            logger.info(f"Using Groq model: {model}")
                            break
                        except Exception as e:
                            logger.debug(f"Groq model {model} not available: {e}")
                            continue

            # Try OpenRouter if preferred and available
            if not response and prefer_openrouter and 'openrouter' in self.clients:
                openrouter_models = [
                    # Modelli TOP 2025
                    "anthropic/claude-3.5-sonnet-20240620",  # Claude 3.5 Sonnet più recente
                    "anthropic/claude-3-opus-20240229",      # Claude 3 Opus più potente
                    "openai/gpt-4o-2024-08-06",             # GPT-4o più recente
                    "google/gemini-pro-1.5-latest",         # Gemini Pro 1.5 più recente
                    "google/gemini-2.0-flash-exp",          # Gemini 2.0 Flash sperimentale

                    # Modelli GRATIS / Low Cost
                    "qwen/qwen-2.5-72b-instruct",           # Qwen 2.5 72B - GRATIS
                    "qwen/qwen-2.5-coder-32b-instruct",     # Qwen 2.5 Coder - GRATIS per coding
                    "meta-llama/llama-3.2-90b-instruct",    # Llama 3.2 90B
                    "meta-llama/llama-3.2-70b-instruct",    # Llama 3.2 70B
                    "meta-llama/llama-3.1-405b-instruct",   # Llama 3.1 405B
                    "deepseek/deepseek-chat",               # DeepSeek Chat - economico
                    "deepseek/deepseek-coder",              # DeepSeek Coder - per coding
                    "mistralai/mistral-large-2411",         # Mistral Large novembre 2024
                    "mistralai/mixtral-8x22b-instruct",     # Mixtral MoE
                    "cohere/command-r-plus-08-2024",        # Cohere Command R+

                    # Modelli specializzati
                    "perplexity/llama-3.1-sonar-huge",      # Perplexity con ricerca web
                    "x-ai/grok-2-1212",                     # Grok 2 di X.AI
                    "x-ai/grok-2-vision-1212",              # Grok 2 Vision
                    "nvidia/llama-3.1-nemotron-70b",        # NVIDIA Nemotron
                    "alibaba/qwen-vl-max",                  # Qwen Vision Language

                    # Modelli economici/fallback
                    "openai/gpt-4o-mini",                   # GPT-4o Mini economico
                    "anthropic/claude-3-haiku",             # Claude Haiku veloce
                    "google/gemini-1.5-flash",              # Gemini Flash veloce
                    "openai/gpt-3.5-turbo"                  # Fallback finale
                ]

                for model in openrouter_models:
                    try:
                        response = self.clients['openrouter'].chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": question}
                            ],
                            temperature=0.7,
                            max_tokens=500
                        )
                        used_model = model
                        used_provider = "OpenRouter"
                        logger.info(f"Using OpenRouter model: {model}")
                        break
                    except Exception as e:
                        logger.debug(f"OpenRouter model {model} not available: {e}")
                        continue

            # Try Together AI if no response
            if not response and 'together' in self.clients:
                for model in provider_models.get('together', []):
                    try:
                        response = self.clients['together'].chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": question}
                            ],
                            temperature=0.7,
                            max_tokens=500
                        )
                        used_model = model
                        used_provider = "Together AI"
                        logger.info(f"Using Together AI model: {model}")
                        break
                    except Exception as e:
                        logger.debug(f"Together AI model {model} not available: {e}")
                        continue

            # Try DeepInfra if no response
            if not response and 'deepinfra' in self.clients:
                for model in provider_models.get('deepinfra', []):
                    try:
                        response = self.clients['deepinfra'].chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": question}
                            ],
                            temperature=0.7,
                            max_tokens=500
                        )
                        used_model = model
                        used_provider = "DeepInfra"
                        logger.info(f"Using DeepInfra model: {model}")
                        break
                    except Exception as e:
                        logger.debug(f"DeepInfra model {model} not available: {e}")
                        continue

            # Try OpenAI if no other response
            if not response and 'openai' in self.clients:
                openai_models = [
                    "gpt-4o",           # Ultimo modello multimodale 2025
                    "gpt-4o-2025-01",   # Versione datata gennaio 2025
                    "gpt-4-turbo-2025", # Turbo aggiornato 2025
                    "gpt-4o-mini",      # Versione economica di gpt-4o
                    "gpt-4-turbo",      # Fallback turbo precedente
                    "gpt-3.5-turbo"     # Fallback finale
                ]

                for model in openai_models:
                    try:
                        response = self.clients['openai'].chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": question}
                            ],
                            temperature=0.7,
                            max_tokens=500
                        )
                        used_model = model
                        used_provider = "OpenAI"
                        logger.info(f"Using OpenAI model: {model}")
                        break
                    except Exception as e:
                        logger.debug(f"OpenAI model {model} not available: {e}")
                        continue

            if not response:
                raise Exception("Nessun modello disponibile")

            answer = response.choices[0].message.content

            # Format model info
            model_info = f"{used_model}"
            if used_provider:
                model_info = f"{used_provider}/{used_model}"

            return {
                "success": True,
                "answer": answer,
                "confidence": 0.95,
                "model": model_info,
                "provider": used_provider
            }

        except Exception as e:
            logger.error(f"SimpleAssistant error: {e}")
            return {
                "success": False,
                "answer": f"Errore: {str(e)}",
                "confidence": 0.0,
                "model": "none",
                "provider": "none"
            }