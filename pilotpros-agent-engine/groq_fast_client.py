#!/usr/bin/env python3
"""
Groq Fast Client - Chiamate dirette per velocità massima
Bypassa CrewAI per ottenere risposte in 200-500ms
"""

import os
import json
import asyncio
import httpx
from typing import Dict, Any, Optional
import time
from groq import Groq

class GroqFastClient:
    """Client diretto Groq per velocità massima"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY non configurata!")

        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"  # Velocissimo!

    async def classify_question(self, question: str) -> Dict[str, Any]:
        """
        Classificazione ULTRA-VELOCE della domanda
        Ritorna in 200-500ms invece di 2-3 secondi
        """
        start = time.time()

        prompt = f"""Classifica questa domanda in una categoria. Rispondi SOLO con JSON.

Domanda: "{question}"

Categorie possibili:
- GREETING: saluti, convenevoli
- HELP: richieste di aiuto, cosa puoi fare
- BUSINESS_DATA: metriche, KPI, numeri, esecuzioni, statistiche
- ANALYSIS: analisi complesse, trend, pattern, insights
- GENERAL: tutto il resto

Output JSON richiesto:
{{"question_type": "CATEGORIA", "confidence": 0.0-1.0, "language": "it/en/etc"}}
"""

        try:
            # Chiamata diretta VELOCISSIMA
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100
            )

            # Parse JSON dalla risposta
            result_text = response.choices[0].message.content

            # Estrai JSON anche se c'è testo extra
            import re
            json_match = re.search(r'\{.*?\}', result_text, re.DOTALL)

            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback se non trova JSON
                result = {
                    "question_type": "GENERAL",
                    "confidence": 0.5,
                    "language": "it"
                }

            elapsed = (time.time() - start) * 1000
            result["response_time_ms"] = elapsed

            return result

        except Exception as e:
            # In caso di errore, default a GENERAL
            return {
                "question_type": "GENERAL",
                "confidence": 0.5,
                "language": "it",
                "error": str(e),
                "response_time_ms": (time.time() - start) * 1000
            }

    async def generate_fast_response(self,
                                   question: str,
                                   question_type: str,
                                   language: str = "it",
                                   context: Optional[str] = None) -> str:
        """
        Genera risposta DIRETTA via Groq per domande semplici
        GREETING e GENERAL in 300-800ms
        """
        start = time.time()

        # Prompt specifici per tipo
        prompts = {
            "GREETING": {
                "it": f"Sei Milhena, assistente business. Rispondi cordialmente a: '{question}'",
                "en": f"You are Milhena, business assistant. Reply warmly to: '{question}'"
            },
            "GENERAL": {
                "it": f"Sei Milhena, assistente business professionale. Rispondi in modo utile e conciso a: '{question}'",
                "en": f"You are Milhena, professional business assistant. Reply helpfully and concisely to: '{question}'"
            },
            "HELP": {
                "it": f"Sei Milhena. Spiega brevemente cosa puoi fare per aiutare con processi business e analytics: '{question}'",
                "en": f"You are Milhena. Briefly explain how you can help with business processes and analytics: '{question}'"
            }
        }

        # Seleziona prompt
        prompt_dict = prompts.get(question_type, prompts["GENERAL"])
        prompt = prompt_dict.get(language, prompt_dict["it"])

        if context:
            prompt += f"\n\nContesto: {context}"

        try:
            # Chiamata DIRETTA per velocità massima
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )

            result = response.choices[0].message.content
            elapsed = (time.time() - start) * 1000

            print(f"⚡ FastPath response in {elapsed:.0f}ms")

            return result

        except Exception as e:
            return f"Mi dispiace, c'è stato un problema: {str(e)}"


# Singleton instance
_fast_client = None

def get_fast_client() -> GroqFastClient:
    """Ottieni istanza singleton del client veloce"""
    global _fast_client
    if _fast_client is None:
        _fast_client = GroqFastClient()
    return _fast_client


async def groq_classify(question: str) -> Dict[str, Any]:
    """Funzione helper per classificazione veloce"""
    client = get_fast_client()
    return await client.classify_question(question)


async def groq_fast_response(question: str,
                            question_type: str,
                            language: str = "it") -> str:
    """Funzione helper per risposta veloce"""
    client = get_fast_client()
    return await client.generate_fast_response(
        question, question_type, language
    )


# Test standalone
if __name__ == "__main__":
    async def test():
        print("🚀 TEST GROQ FAST CLIENT\n")

        client = GroqFastClient()

        # Test classificazione
        questions = [
            "Ciao! Come stai?",
            "Quante esecuzioni oggi?",
            "Analizza il trend"
        ]

        for q in questions:
            print(f"\n❓ '{q}'")

            # Classificazione veloce
            classification = await client.classify_question(q)
            print(f"   📊 Tipo: {classification['question_type']}")
            print(f"   ⏱️  Classificazione: {classification['response_time_ms']:.0f}ms")

            # Risposta veloce per GREETING/GENERAL
            if classification['question_type'] in ["GREETING", "GENERAL", "HELP"]:
                response = await client.generate_fast_response(
                    q,
                    classification['question_type'],
                    classification.get('language', 'it')
                )
                print(f"   💬 Risposta: {response[:100]}...")

    asyncio.run(test())