"""
Model Selector - Selezione semplificata modelli AI
Categorie: POTENTI, LEGGERI, GRATIS
"""

import os
from typing import Dict, List, Optional
from enum import Enum


class ModelCategory(Enum):
    POTENTE = "potente"    # Modelli più intelligenti (costosi)
    LEGGERO = "leggero"    # Modelli veloci ed economici
    GRATIS = "gratis"      # Modelli completamente gratuiti


class ModelSelector:
    """Selettore semplificato per modelli AI"""

    # Configurazione modelli per categoria e provider
    MODELS = {
        ModelCategory.POTENTE: {
            "openai": [
                "gpt-5",                    # GPT-5 con reasoning avanzato
                "gpt-5-turbo",             # GPT-5 Turbo
                "o1-preview",              # OpenAI o1 con reasoning
                "o1-mini",                 # OpenAI o1 mini
                "gpt-4o",                  # GPT-4 Omni multimodale
            ],
            "anthropic": [
                "claude-opus-4.1",         # Opus 4.1 con super reasoning
                "claude-4-opus",           # Claude 4 Opus
                "claude-3.5-sonnet",       # Claude 3.5 Sonnet
                "claude-3-opus"            # Claude 3 Opus
            ],
            "google": [
                "gemini-2.5-pro",          # Gemini 2.5 Pro reasoning
                "gemini-2.5-ultra",        # Gemini 2.5 Ultra
                "gemini-2.0-pro",          # Gemini 2.0 Pro
                "gemini-pro-1.5"           # Gemini Pro 1.5
            ],
            "x-ai": [
                "grok-4",                  # Grok 4 con reasoning
                "grok-3-mega",             # Grok 3 Mega
                "grok-2-1212"              # Grok 2 dicembre
            ],
            "openrouter": [
                "anthropic/claude-opus-4.1",      # Opus 4.1 via OpenRouter
                "openai/gpt-5",                   # GPT-5 via OpenRouter
                "openai/o1-preview",              # OpenAI o1 reasoning
                "google/gemini-2.5-ultra",        # Gemini 2.5 Ultra
                "x-ai/grok-4",                    # Grok 4
                "anthropic/claude-3.5-sonnet",    # Claude 3.5
                "openai/gpt-4o"                   # GPT-4o
            ],
            "together": [
                "meta-llama/Meta-Llama-3.3-405B-Instruct",  # Llama 3.3 405B
                "meta-llama/Meta-Llama-3.1-405B-Instruct"   # Llama 3.1 405B
            ],
            "mistral": [
                "mistral-large-2025",      # Mistral Large gennaio 2025
                "mixtral-8x22b-v2"         # Mixtral nuovo
            ]
        },

        ModelCategory.LEGGERO: {
            "openai": ["gpt-4o-mini", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-haiku"],
            "google": ["gemini-1.5-flash", "gemini-2.0-flash"],
            "mistral": ["mistral-medium", "mistral-small"],
            "openrouter": [
                "openai/gpt-4o-mini",
                "anthropic/claude-3-haiku",
                "google/gemini-1.5-flash"
            ],
            "together": ["mistralai/Mixtral-8x7B-Instruct-v0.1"],
            "deepinfra": ["mistralai/Mistral-7B-Instruct-v0.3"],
        },

        ModelCategory.GRATIS: {
            "groq": [  # GROQ è COMPLETAMENTE GRATIS!
                "llama-3.3-70b-versatile",           # Llama 3.3 70B NUOVO
                "llama-3.2-90b-vision-preview",      # Llama 3.2 90B con vision
                "llama-3.2-70b-versatile",           # Llama 3.2 70B
                "llama-3.1-70b-versatile",           # Llama 3.1 70B
                "mixtral-8x7b-32768",                # Mixtral MoE
                "gemma2-9b-it",                      # Google Gemma 2
                "llama3-groq-70b-8192-tool-use-preview"  # Con function calling
            ],
            "openrouter": [  # Modelli GRATIS via OpenRouter
                "qwen/qwen-2.5-72b-instruct",        # Qwen 2.5 GRATIS
                "qwen/qwen-2.5-coder-32b-instruct",  # Qwen Coder GRATIS
                "meta-llama/llama-3.3-70b-instruct", # Llama 3.3 GRATIS
                "meta-llama/llama-3.2-70b-instruct", # Llama 3.2 GRATIS
                "meta-llama/llama-3.2-11b-instruct", # Llama 3.2 11B GRATIS
                "google/gemma-2-9b-it",              # Gemma 2 GRATIS
                "microsoft/phi-3-medium-128k",       # Phi-3 GRATIS
                "deepseek/deepseek-chat",            # DeepSeek ECONOMICO
                "deepseek/deepseek-coder"            # DeepSeek Coder
            ],
            "together": [  # Modelli GRATIS o crediti trial Together AI
                "meta-llama/Llama-3.2-11B-Vision-Instruct",  # Vision GRATIS
                "meta-llama/Llama-Guard-3-8B",               # Safety GRATIS
                "microsoft/Phi-3.5-mini-instruct",           # Phi 3.5 GRATIS
                "Qwen/Qwen2.5-7B-Instruct",                  # Qwen piccolo GRATIS
            ],
            "huggingface": [  # HuggingFace Inference API GRATIS
                "meta-llama/Meta-Llama-3-8B-Instruct",
                "mistralai/Mistral-7B-Instruct-v0.3",
                "google/gemma-2-2b-it",
                "microsoft/Phi-3.5-mini-instruct"
            ],
            "replicate": [  # Replicate con crediti GRATIS trial
                "meta/llama-3.2-11b-vision-instruct",
                "mistralai/mixtral-8x7b-instruct-v0.1",
                "01-ai/yi-large"
            ],
            "local": [  # Ollama LOCALE 100% GRATIS
                "ollama/llama3.3",
                "ollama/llama3.2",
                "ollama/qwen2.5:72b",
                "ollama/mixtral:8x7b",
                "ollama/deepseek-v2.5",
                "ollama/gemma2:27b",
                "ollama/mistral",
                "ollama/phi3.5",
                "ollama/solar-pro"
            ],
            "cohere": [  # Cohere trial GRATIS
                "command-r",                # Command R base GRATIS trial
                "command-light"             # Command Light GRATIS
            ],
            "ai21": [  # AI21 trial GRATIS
                "j2-ultra",                 # Jurassic-2 trial
                "j2-grande"                 # Jurassic-2 Grande trial
            ]
        }
    }

    @classmethod
    def get_model(cls, category: ModelCategory = ModelCategory.GRATIS) -> tuple[str, str]:
        """
        Ottieni il miglior modello disponibile per categoria

        Args:
            category: POTENTE, LEGGERO o GRATIS

        Returns:
            (provider, model) tuple
        """
        models = cls.MODELS[category]

        # Controlla quali API keys sono disponibili
        available_providers = cls._get_available_providers()

        # Trova il primo modello disponibile nella categoria
        for provider, model_list in models.items():
            if provider in available_providers:
                if model_list:
                    return provider, model_list[0]

        # Fallback a modello mock se niente disponibile
        return "mock", "mock-model"

    @classmethod
    def _get_available_providers(cls) -> List[str]:
        """Controlla quali provider hanno API key configurate"""
        available = []

        if os.getenv("OPENAI_API_KEY"):
            available.append("openai")
        if os.getenv("ANTHROPIC_API_KEY"):
            available.append("anthropic")
        if os.getenv("GOOGLE_API_KEY"):
            available.append("google")
        if os.getenv("GROQ_API_KEY"):
            available.append("groq")
        if os.getenv("OPENROUTER_API_KEY"):
            available.append("openrouter")
        if os.getenv("TOGETHER_API_KEY"):
            available.append("together")
        if os.getenv("DEEPINFRA_API_KEY"):
            available.append("deepinfra")
        if os.getenv("MISTRAL_API_KEY"):
            available.append("mistral")
        if os.getenv("XAI_API_KEY"):
            available.append("x-ai")

        # Check if Ollama is running locally
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=1)
            if response.status_code == 200:
                available.append("local")
        except:
            pass

        return available

    @classmethod
    def list_available_models(cls) -> Dict[str, List[str]]:
        """Lista tutti i modelli disponibili per categoria"""
        available_providers = cls._get_available_providers()
        result = {
            "potenti": [],
            "leggeri": [],
            "gratis": []
        }

        for category in ModelCategory:
            category_models = []
            for provider, models in cls.MODELS[category].items():
                if provider in available_providers:
                    for model in models:
                        category_models.append(f"{provider}/{model}")

            result[category.value] = category_models

        return result

    @classmethod
    def get_quick_config(cls) -> Dict[str, tuple]:
        """
        Configurazione rapida: un modello per ogni categoria

        Returns:
            {
                "potente": (provider, model),
                "leggero": (provider, model),
                "gratis": (provider, model)
            }
        """
        return {
            "potente": cls.get_model(ModelCategory.POTENTE),
            "leggero": cls.get_model(ModelCategory.LEGGERO),
            "gratis": cls.get_model(ModelCategory.GRATIS)
        }


# Esempio di utilizzo
if __name__ == "__main__":
    # Mostra configurazione rapida
    config = ModelSelector.get_quick_config()
    print("=== CONFIGURAZIONE MODELLI ===")
    print(f"POTENTE: {config['potente'][0]}/{config['potente'][1]}")
    print(f"LEGGERO: {config['leggero'][0]}/{config['leggero'][1]}")
    print(f"GRATIS:  {config['gratis'][0]}/{config['gratis'][1]}")

    # Lista modelli disponibili
    print("\n=== MODELLI DISPONIBILI ===")
    available = ModelSelector.list_available_models()
    for category, models in available.items():
        print(f"\n{category.upper()}:")
        for model in models:
            print(f"  - {model}")