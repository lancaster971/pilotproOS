#!/usr/bin/env python3
"""
OpenAI GPT-4o Fast Client - Provider PRIMARIO con 1M token!
Il MIGLIORE al mondo per qualità e limiti generosi
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional
import time
import openai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenAIFastClient")

class OpenAIFastClient:
    """Client OpenAI GPT-4o per qualità suprema"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY non configurata!")

        # Client OpenAI
        openai.api_key = self.api_key
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        self.model_name = "gpt-4o-2024-11-20"  # Latest, 1M token limit!

        logger.info(f"✅ OpenAI Primary Client: {self.model_name} (1M TOKEN LIMIT!)")

    async def classify_question(self, question: str) -> Dict[str, Any]:
        """
        Classificazione SUPREMA con GPT-4o
        """
        start = time.time()

        prompt = f"""Classifica questa domanda in una categoria. Rispondi SOLO con JSON.

Domanda: "{question}"

Categorie possibili:
- GREETING: saluti, convenevoli
- HELP: richieste di aiuto, cosa puoi fare
- TECHNOLOGY_INQUIRY: domande su tecnologie, n8n, database, PostgreSQL, Docker, API, strumenti tecnici
- BUSINESS_DATA: metriche, KPI, numeri, esecuzioni, statistiche
- ANALYSIS: analisi complesse, trend, pattern, insights
- GENERAL: tutto il resto

Output JSON richiesto:
{{"question_type": "CATEGORIA", "confidence": 0.0-1.0, "language": "it/en/etc"}}
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100
            )

            result_text = response.choices[0].message.content

            # Verifica se la risposta contiene errori
            if not result_text or "error" in result_text.lower():
                raise Exception(f"OpenAI API error: {result_text[:100] if result_text else 'Empty response'}")

            # GPT-4o è perfetto con JSON, ma aggiungiamo sicurezza
            import re
            json_match = re.search(r'\{.*?\}', result_text, re.DOTALL)

            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback se non trova JSON (molto raro con GPT-4o)
                result = {
                    "question_type": "GENERAL",
                    "confidence": 0.8,
                    "language": "it"
                }

            elapsed = (time.time() - start) * 1000
            result["response_time_ms"] = elapsed
            result["provider"] = "openai"

            return result

        except Exception as e:
            # LANCIA ECCEZIONE per attivare fallback Groq
            logger.error(f"OpenAI classification failed: {e}")
            raise e

    async def generate_fast_response(self,
                                   question: str,
                                   question_type: str,
                                   language: str = "it",
                                   context: Optional[str] = None) -> str:
        """
        Genera risposta SUPREMA via GPT-4o
        """
        start = time.time()

        # Prompt specifici per tipo - GPT-4o capisce perfettamente
        prompts = {
            "GREETING": {
                "it": f"Sei Milhena, assistente business professionale e cordiale. Rispondi calorosamente a: '{question}'",
                "en": f"You are Milhena, a professional and warm business assistant. Reply warmly to: '{question}'"
            },
            "TECHNOLOGY_INQUIRY": {
                "it": f"""Sei Milhena, assistente business intelligente. 

REGOLA CRITICA - NON menzionare MAI questi termini tecnici:
- n8n → chiamalo "piattaforma di automazione aziendale"
- CrewAI → chiamalo "sistema AI multi-agente aziendale"  
- PostgreSQL → chiamalo "database aziendale avanzato"
- Docker → chiamalo "infrastruttura containerizzata"
- opensource → chiamalo "soluzioni tecnologiche moderne"

Domanda: '{question}'

Rispondi come esperta business che conosce la sostanza ma usa sempre terminologia aziendale, mai nomi tecnici specifici.""",
                "en": f"""You are Milhena, intelligent business assistant.

CRITICAL RULE - NEVER mention these technical terms:
- n8n → call it "enterprise automation platform"
- CrewAI → call it "multi-agent AI system"
- PostgreSQL → call it "advanced corporate database" 
- Docker → call it "containerized infrastructure"
- opensource → call it "modern technology solutions"

Question: '{question}'

Answer as business expert who knows the substance but always uses business terminology, never specific technical names."""
            },
            "GENERAL": {
                "it": f"Sei Milhena, assistente business professionale ed esperta. Fornisci una risposta utile, precisa e professionale a: '{question}'",
                "en": f"You are Milhena, professional and expert business assistant. Provide a helpful, accurate and professional answer to: '{question}'"
            },
            "HELP": {
                "it": f"Sei Milhena, assistente AI specializzata in processi aziendali e analytics. Spiega chiaramente le tue capacità per aiutare con: '{question}'",
                "en": f"You are Milhena, AI assistant specialized in business processes and analytics. Clearly explain your capabilities to help with: '{question}'"
            }
        }

        # Seleziona prompt - GPT-4o gestisce perfettamente il multilanguage
        prompt_dict = prompts.get(question_type, prompts["GENERAL"])
        prompt = prompt_dict.get(language, prompt_dict["it"])

        if context:
            prompt += f"\n\nContesto aggiuntivo: {context}"

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800  # GPT-4o è conciso ma completo
            )

            result_text = response.choices[0].message.content

            # Verifica se la risposta contiene errori
            if not result_text or "error" in result_text.lower():
                raise Exception(f"OpenAI API error: {result_text[:100] if result_text else 'Empty response'}")

            elapsed = (time.time() - start) * 1000
            logger.info(f"⚡ GPT-4o SUPREME response in {elapsed:.0f}ms")

            return result_text

        except Exception as e:
            # LANCIA ECCEZIONE per attivare fallback Groq
            logger.error(f"OpenAI response failed: {e}")
            raise e


# Singleton instance
_openai_client = None

def get_openai_client() -> OpenAIFastClient:
    """Ottieni istanza singleton del client OpenAI"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIFastClient()
    return _openai_client


async def openai_classify(question: str) -> Dict[str, Any]:
    """Funzione helper per classificazione suprema OpenAI"""
    client = get_openai_client()
    return await client.classify_question(question)


async def openai_fast_response(question: str,
                              question_type: str,
                              language: str = "it") -> str:
    """Funzione helper per risposta suprema OpenAI"""
    client = get_openai_client()
    return await client.generate_fast_response(
        question, question_type, language
    )
