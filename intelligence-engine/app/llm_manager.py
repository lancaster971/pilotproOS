"""
Dynamic LLM Manager - Add/Remove models WITHOUT rebuilding!
NO CREWAI BULLSHIT - Models are loaded dynamically
"""

import os
import json
from typing import Dict, Any, Optional
from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger

class DynamicLLMManager:
    """
    Manager that loads models DYNAMICALLY from config file
    NO REBUILD NEEDED when adding models!
    """

    def __init__(self, config_path: str = "/app/config/models.json"):
        self.config_path = config_path
        self.models: Dict[str, BaseLanguageModel] = {}
        self.active_model: Optional[str] = None
        self.load_config()

    def load_config(self):
        """Load model configuration from JSON file"""
        try:
            # If config doesn't exist, create default
            if not os.path.exists(self.config_path):
                self.create_default_config()

            with open(self.config_path, 'r') as f:
                self.config = json.load(f)

            logger.info(f"📚 Loaded {len(self.config['models'])} model configurations")

            # Initialize enabled models
            for model_id, model_config in self.config['models'].items():
                if model_config.get('enabled', False):
                    self.load_model(model_id)

        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            self.config = {"models": {}}

    def create_default_config(self):
        """Create default configuration file"""
        default_config = {
            "default_model": "groq-llama",
            "fallback_chain": ["groq-llama", "gemini-free", "openrouter-cheap"],
            "models": {
                "groq-llama": {
                    "provider": "groq",
                    "model": "llama-3.3-70b-versatile",
                    "enabled": True,
                    "api_key_env": "GROQ_API_KEY",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "description": "FREE - Groq Llama 3.3 70B"
                },
                "groq-mixtral": {
                    "provider": "groq",
                    "model": "mixtral-8x7b-32768",
                    "enabled": True,
                    "api_key_env": "GROQ_API_KEY",
                    "temperature": 0.7,
                    "max_tokens": 32768,
                    "description": "FREE - Groq Mixtral for coding"
                },
                "gemini-free": {
                    "provider": "google",
                    "model": "gemini-2.0-flash-exp",
                    "enabled": True,
                    "api_key_env": "GOOGLE_API_KEY",
                    "temperature": 0.7,
                    "max_tokens": 8192,
                    "description": "FREE - Google Gemini Flash"
                },
                "gemini-8b": {
                    "provider": "google",
                    "model": "gemini-1.5-flash-8b",
                    "enabled": False,
                    "api_key_env": "GOOGLE_API_KEY",
                    "temperature": 0.7,
                    "max_tokens": 8192,
                    "description": "FREE - Gemini 8B (4M tokens/min!)"
                },
                "openrouter-cheap": {
                    "provider": "openrouter",
                    "model": "google/gemini-2.0-flash-exp",
                    "enabled": True,
                    "api_key_env": "OPENROUTER_API_KEY",
                    "base_url": "https://openrouter.ai/api/v1",
                    "temperature": 0.7,
                    "description": "CHEAP - $0.15/1M tokens via OpenRouter"
                },
                "openrouter-deepseek": {
                    "provider": "openrouter",
                    "model": "deepseek/deepseek-r1",
                    "enabled": False,
                    "api_key_env": "OPENROUTER_API_KEY",
                    "base_url": "https://openrouter.ai/api/v1",
                    "temperature": 0.7,
                    "description": "CHEAP - DeepSeek R1 for reasoning"
                },
                "claude-haiku": {
                    "provider": "anthropic",
                    "model": "claude-3-5-haiku-20241022",
                    "enabled": False,
                    "api_key_env": "ANTHROPIC_API_KEY",
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "description": "CHEAP - Claude 3.5 Haiku ($0.80/1M)"
                },
                "claude-sonnet": {
                    "provider": "anthropic",
                    "model": "claude-3-5-sonnet-20241022",
                    "enabled": False,
                    "api_key_env": "ANTHROPIC_API_KEY",
                    "temperature": 0.7,
                    "max_tokens": 8192,
                    "description": "PREMIUM - Claude 3.5 Sonnet"
                },
                "gpt-4o-mini": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "enabled": False,
                    "api_key_env": "OPENAI_API_KEY",
                    "temperature": 0.7,
                    "max_tokens": 16384,
                    "description": "OpenAI GPT-4o Mini"
                }
            }
        }

        # Create config directory if not exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        # Save default config
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)

        logger.info("✅ Created default models configuration")
        self.config = default_config

    def load_model(self, model_id: str) -> Optional[BaseLanguageModel]:
        """
        Load a model dynamically based on configuration
        NO REBUILD NEEDED!
        """
        try:
            if model_id not in self.config['models']:
                logger.error(f"❌ Model {model_id} not found in config")
                return None

            model_config = self.config['models'][model_id]
            provider = model_config['provider']

            # Check if API key is available
            api_key_env = model_config.get('api_key_env')
            api_key = os.getenv(api_key_env) if api_key_env else None

            if not api_key and api_key_env:
                logger.warning(f"⚠️ No API key for {model_id} ({api_key_env})")
                return None

            # Create model based on provider
            if provider == "groq":
                model = ChatGroq(
                    model=model_config['model'],
                    temperature=model_config.get('temperature', 0.7),
                    max_tokens=model_config.get('max_tokens', 2000),
                    groq_api_key=api_key
                )

            elif provider == "google":
                model = ChatGoogleGenerativeAI(
                    model=model_config['model'],
                    temperature=model_config.get('temperature', 0.7),
                    max_output_tokens=model_config.get('max_tokens', 8192),
                    google_api_key=api_key
                )

            elif provider == "openrouter":
                model = ChatOpenAI(
                    model=model_config['model'],
                    base_url=model_config.get('base_url', "https://openrouter.ai/api/v1"),
                    api_key=api_key,
                    temperature=model_config.get('temperature', 0.7),
                    max_tokens=model_config.get('max_tokens', 4096),
                    default_headers={
                        "HTTP-Referer": "http://localhost:8000",
                        "X-Title": "PilotProOS Intelligence Engine"
                    }
                )

            elif provider == "anthropic":
                model = ChatAnthropic(
                    model=model_config['model'],
                    temperature=model_config.get('temperature', 0.7),
                    max_tokens=model_config.get('max_tokens', 4096),
                    anthropic_api_key=api_key
                )

            elif provider == "openai":
                model = ChatOpenAI(
                    model=model_config['model'],
                    temperature=model_config.get('temperature', 0.7),
                    max_tokens=model_config.get('max_tokens', 4096),
                    api_key=api_key
                )

            else:
                logger.error(f"❌ Unknown provider: {provider}")
                return None

            # Store model
            self.models[model_id] = model
            logger.info(f"✅ Loaded model: {model_id} ({model_config.get('description', '')})")
            return model

        except Exception as e:
            logger.error(f"❌ Failed to load model {model_id}: {e}")
            return None

    def get_model(self, model_id: Optional[str] = None) -> Optional[BaseLanguageModel]:
        """Get a specific model or the default one"""
        if model_id is None:
            model_id = self.config.get('default_model', 'groq-llama')

        # If model not loaded, try to load it
        if model_id not in self.models:
            self.load_model(model_id)

        return self.models.get(model_id)

    def get_fallback_chain(self) -> list:
        """Get list of models for fallback"""
        chain = []
        for model_id in self.config.get('fallback_chain', []):
            model = self.get_model(model_id)
            if model:
                chain.append(model)
        return chain

    def add_model(self, model_id: str, config: Dict[str, Any]):
        """
        ADD A NEW MODEL WITHOUT REBUILDING!
        Just add to config and reload
        """
        # Add to config
        self.config['models'][model_id] = config

        # Save updated config
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

        # Load the new model if enabled
        if config.get('enabled', False):
            self.load_model(model_id)

        logger.info(f"✅ Added new model: {model_id}")

    def remove_model(self, model_id: str):
        """Remove a model from configuration"""
        if model_id in self.config['models']:
            del self.config['models'][model_id]

            # Remove from loaded models
            if model_id in self.models:
                del self.models[model_id]

            # Save updated config
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)

            logger.info(f"✅ Removed model: {model_id}")

    def list_models(self) -> Dict[str, Dict]:
        """List all configured models"""
        return {
            model_id: {
                "description": config.get('description', ''),
                "enabled": config.get('enabled', False),
                "loaded": model_id in self.models,
                "provider": config.get('provider'),
                "model": config.get('model')
            }
            for model_id, config in self.config['models'].items()
        }

    def reload_config(self):
        """Reload configuration from file"""
        self.models.clear()
        self.load_config()
        logger.info("🔄 Configuration reloaded")

# Singleton instance
_manager = None

def get_llm_manager() -> DynamicLLMManager:
    """Get singleton LLM manager"""
    global _manager
    if _manager is None:
        _manager = DynamicLLMManager()
    return _manager