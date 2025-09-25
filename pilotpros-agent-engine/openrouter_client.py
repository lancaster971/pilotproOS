#!/usr/bin/env python3
"""
OpenRouter Client - Fallback provider con Qwen e altri modelli gratuiti
Utilizzato quando Groq esaurisce i rate limits
"""

import os
import json
import asyncio
import httpx
import logging
from typing import Dict, Any, Optional
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenRouterClient")

class OpenRouterClient:
    """Client OpenRouter per fallback con modelli gratuiti"""

    # Modelli PAGATI per performance ottimale (economici $0.07-0.28/M token!)
    PAID_MODELS = {
        "qwen2.5-72b": "qwen/qwen-2.5-72b-instruct",  # $0.07/M in + $0.28/M out - MIGLIORE
        "qwen-max": "qwen/qwen-max",                   # Modello più potente Qwen
        "qwen3-72b": "qwen/qwen3-72b:free"            # Fallback free se necessario (limiti)
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY non configurata - fallback disabilitato")
            self.enabled = False
            return

        self.enabled = True
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_model = self.PAID_MODELS["qwen2.5-72b"]  # Qwen PAGATO 2.5-72B come default

        # Headers standard
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:8000",  # Per credits gratuiti
            "X-Title": "PilotProOS-FastBypass"
        }

        logger.info(f"✅ OpenRouter Client attivo - Default: {self.default_model} (PAGATO ~$1/mese!)")

    async def classify_question(self, question: str) -> Dict[str, Any]:
        """
        Classificazione veloce con Qwen (fallback da Groq)
        """
        if not self.enabled:
            return {"question_type": "GENERAL", "confidence": 0.3, "error": "OpenRouter disabled"}

        start_time = time.time()

        prompt = f"""Classifica questa domanda. Rispondi SOLO con JSON.

Domanda: "{question}"

Categorie: GREETING, HELP, TECHNOLOGY_INQUIRY, GENERAL, BUSINESS_DATA

Output JSON: {{"question_type": "CATEGORIA", "confidence": 0.0-1.0, "language": "it/en"}}"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.default_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 100
                    },
                    timeout=10.0
                )

                if response.status_code != 200:
                    logger.error(f"OpenRouter error: {response.status_code}")
                    return {"question_type": "GENERAL", "confidence": 0.5, "error": f"HTTP {response.status_code}"}

                result_text = response.json()["choices"][0]["message"]["content"]

                # Parse JSON dalla risposta
                import re
                json_match = re.search(r'\{.*?\}', result_text, re.DOTALL)

                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = {"question_type": "GENERAL", "confidence": 0.5, "language": "it"}

                elapsed = (time.time() - start_time) * 1000
                result["response_time_ms"] = elapsed
                result["provider"] = "openrouter"
                result["model"] = self.default_model

                logger.info(f"🔄 OpenRouter fallback: {result['question_type']} in {elapsed:.0f}ms")
                return result

        except Exception as e:
            logger.error(f"OpenRouter error: {e}")
            return {
                "question_type": "GENERAL",
                "confidence": 0.5,
                "error": str(e),
                "provider": "openrouter"
            }

    async def generate_fast_response(self,
                                   question: str,
                                   question_type: str,
                                   language: str = "it") -> str:
        """
        Genera risposta veloce con Qwen (fallback da Groq)
        """
        if not self.enabled:
            return "Servizio fallback temporaneamente non disponibile."

        # Prompts ottimizzati per Qwen
        prompts = {
            "GREETING": {
                "it": f"Sei Milhena, assistente business. Rispondi cordialmente a: '{question}'. Max 2 frasi.",
                "en": f"You are Milhena, business assistant. Reply warmly to: '{question}'. Max 2 sentences."
            },
            "TECHNOLOGY_INQUIRY": {
                "it": f"Sei Milhena. NON dire: n8n, CrewAI, PostgreSQL, Docker. Usa: 'soluzioni tecnologiche avanzate', 'sistemi di automazione business', 'database aziendale'. Domanda: '{question}'",
                "en": f"You are Milhena. DON'T say: n8n, CrewAI, PostgreSQL, Docker. Use: 'advanced tech solutions', 'business automation systems', 'enterprise database'. Question: '{question}'"
            },
            "HELP": {
                "it": f"Sei Milhena. Spiega brevemente come aiuti con processi business e analytics: '{question}'",
                "en": f"You are Milhena. Briefly explain how you help with business processes and analytics: '{question}'"
            },
            "GENERAL": {
                "it": f"Sei Milhena, assistente business. Rispondi utilmente a: '{question}'",
                "en": f"You are Milhena, business assistant. Reply helpfully to: '{question}'"
            }
        }

        prompt_dict = prompts.get(question_type, prompts["GENERAL"])
        prompt = prompt_dict.get(language, prompt_dict["it"])

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.default_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 400
                    },
                    timeout=15.0
                )

                if response.status_code != 200:
                    logger.error(f"OpenRouter response error: {response.status_code}")
                    return f"Errore temporaneo nel servizio fallback (HTTP {response.status_code})"

                result = response.json()["choices"][0]["message"]["content"]
                logger.info(f"🔄 OpenRouter fallback response generated")
                return result.strip()

        except Exception as e:
            logger.error(f"OpenRouter generation error: {e}")
            return f"Mi dispiace, c'è stato un problema con il servizio fallback: {str(e)}"

    async def test_connection(self) -> Dict[str, Any]:
        """Test connessione OpenRouter"""
        if not self.enabled:
            return {"status": "disabled", "reason": "API key missing"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self.headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    models = response.json()
                    qwen_models = [m for m in models.get("data", []) if "qwen" in m.get("id", "").lower()]

                    return {
                        "status": "connected",
                        "available_models": len(models.get("data", [])),
                        "qwen_models": len(qwen_models),
                        "default_model": self.default_model
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status_code}"
                    }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

# Singleton instance
_openrouter_client = None

def get_openrouter_client() -> OpenRouterClient:
    """Ottieni istanza singleton"""
    global _openrouter_client
    if _openrouter_client is None:
        _openrouter_client = OpenRouterClient()
    return _openrouter_client

# Test standalone
if __name__ == "__main__":
    async def test():
        print("🧪 TEST OPENROUTER CLIENT")
        print("=" * 40)

        client = OpenRouterClient()

        # Test connessione
        conn_test = await client.test_connection()
        print(f"Connection: {conn_test}")

        if client.enabled:
            # Test classificazione
            result = await client.classify_question("Ciao!")
            print(f"\nClassification: {result}")

            # Test risposta
            response = await client.generate_fast_response("Ciao!", "GREETING", "it")
            print(f"\nResponse: {response[:100]}...")

    asyncio.run(test())