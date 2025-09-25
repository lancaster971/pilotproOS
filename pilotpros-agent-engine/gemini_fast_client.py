#!/usr/bin/env python3
"""
Gemini Fast Client - Cliente ultra-veloce per Google Gemini (GRATUITO)
Integrazione con Gemini 1.5 Flash e Pro per Milhena
"""

import os
import asyncio
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Logger configurato
logger = logging.getLogger("GeminiClient")
logger.setLevel(logging.INFO)


class GeminiFastClient:
    """Cliente ottimizzato per Gemini - 100% GRATUITO"""

    # Rate limits per modello (free tier)
    RATE_LIMITS = {
        "gemini-1.5-flash": {"rpm": 15, "tpm": 1000000, "rpd": 1500},
        "gemini-1.5-pro": {"rpm": 2, "tpm": 32000, "rpd": 50}
    }

    def __init__(self, api_key: Optional[str] = None):
        """Inizializza client Gemini con API key gratuita"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY mancante! Ottieni gratis: https://aistudio.google.com/apikey")

        # Configura Gemini
        genai.configure(api_key=self.api_key)

        # Modelli disponibili
        self.flash_model = genai.GenerativeModel('gemini-1.5-flash')
        self.pro_model = genai.GenerativeModel('gemini-1.5-pro')

        # Tracking rate limits
        self.last_requests = {
            "flash": [],
            "pro": []
        }

        logger.info("✅ Gemini Client inizializzato (FREE tier)")

    async def classify_question(self, question: str) -> Dict[str, Any]:
        """
        Classifica domanda usando Gemini Flash (velocissimo)

        Returns:
            Dict con tipo domanda e confidence
        """
        start_time = time.time()

        prompt = f"""Classifica questa domanda in una categoria.

Domanda: {question}

Categorie possibili:
- GREETING (saluti, ciao, buongiorno)
- HELP (come funzioni, aiuto, cosa puoi fare)
- GENERAL (domande generiche su business/processi)
- BUSINESS_DATA (richieste dati specifici, metriche, KPI)
- ERROR_ANALYSIS (problemi, errori, debugging)
- PREDICTION (previsioni, trend, analisi predittive)

Rispondi SOLO con la categoria, niente altro.
"""

        try:
            # Controlla rate limit
            if not self._check_rate_limit("flash"):
                logger.warning("Rate limit Gemini Flash, attendo...")
                await asyncio.sleep(2)

            # Genera classificazione
            response = self.flash_model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=20
                )
            )

            category = response.text.strip().upper()
            elapsed = (time.time() - start_time) * 1000

            logger.info(f"⚡ Gemini Flash: Classificato come {category} in {elapsed:.0f}ms")

            return {
                "type": category,
                "confidence": 0.95,
                "model": "gemini-flash",
                "latency_ms": elapsed
            }

        except Exception as e:
            logger.error(f"Errore Gemini classificazione: {e}")
            # Fallback response
            return {
                "type": "GENERAL",
                "confidence": 0.5,
                "error": str(e)
            }

    async def generate_fast_response(self, question: str, question_type: str, language: str = "it") -> str:
        """
        Genera risposta veloce con Gemini Flash

        Args:
            question: Domanda utente
            question_type: Tipo classificato
            language: Lingua risposta

        Returns:
            Risposta in linguaggio naturale
        """
        start_time = time.time()

        # Prompt ottimizzati per tipo
        prompts = {
            "GREETING": f"""Rispondi cordialmente a questo saluto in {language}: '{question}'
            Sii breve, amichevole e professionale. Max 2 frasi.""",

            "HELP": f"""Spiega brevemente le tue capacità come assistente AI business.
            Domanda: {question}
            Lingua: {language}
            Menziona: analisi dati, automazione processi, supporto decisionale.""",

            "GENERAL": f"""Rispondi a questa domanda business in modo chiaro e conciso.
            Domanda: {question}
            Lingua: {language}
            Max 3-4 frasi, focus su valore pratico."""
        }

        prompt = prompts.get(question_type, prompts["GENERAL"])

        try:
            # Controlla rate limit
            if not self._check_rate_limit("flash"):
                await asyncio.sleep(2)

            # Genera risposta
            response = self.flash_model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=200
                )
            )

            elapsed = (time.time() - start_time) * 1000
            logger.info(f"⚡ Gemini Flash response in {elapsed:.0f}ms")

            return response.text.strip()

        except Exception as e:
            logger.error(f"Errore generazione risposta: {e}")
            return self._get_fallback_response(question_type, language)

    async def analyze_business_data(self, query: str, data: Dict[str, Any]) -> str:
        """
        Analisi avanzata business data con Gemini Pro (quando serve qualità)

        Args:
            query: Domanda dell'utente
            data: Dati business da analizzare

        Returns:
            Analisi dettagliata in linguaggio naturale
        """
        # Usa Pro solo per analisi complesse, altrimenti Flash
        use_pro = "previsione" in query.lower() or "trend" in query.lower() or "analisi" in query.lower()

        if use_pro and self._check_rate_limit("pro"):
            model = self.pro_model
            model_name = "gemini-pro"
            logger.info("🎯 Usando Gemini Pro per analisi avanzata")
        else:
            model = self.flash_model
            model_name = "gemini-flash"
            logger.info("⚡ Usando Gemini Flash per analisi veloce")

        prompt = f"""Analizza questi dati business e rispondi alla domanda in modo professionale.

DATI:
{self._format_data_for_prompt(data)}

DOMANDA: {query}

Fornisci:
1. Risposta diretta alla domanda
2. Insight rilevanti dai dati
3. Suggerimenti pratici (se applicabile)

Usa un linguaggio business comprensibile, evita tecnicismi."""

        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.5,
                    max_output_tokens=500
                )
            )

            self._track_request(model_name)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Errore analisi business: {e}")
            return f"Analisi temporaneamente non disponibile. Dati grezzi: {data}"

    def _check_rate_limit(self, model_type: str) -> bool:
        """Verifica se possiamo fare una richiesta rispettando rate limits"""
        now = time.time()

        if model_type == "flash":
            key = "flash"
            rpm_limit = 15
        else:
            key = "pro"
            rpm_limit = 2

        # Rimuovi richieste vecchie (> 1 minuto)
        self.last_requests[key] = [
            t for t in self.last_requests[key]
            if now - t < 60
        ]

        # Controlla se sotto il limite
        return len(self.last_requests[key]) < rpm_limit

    def _track_request(self, model_type: str):
        """Traccia richiesta per rate limiting"""
        key = "flash" if "flash" in model_type else "pro"
        self.last_requests[key].append(time.time())

    def _format_data_for_prompt(self, data: Dict[str, Any]) -> str:
        """Formatta dati per prompt in modo leggibile"""
        formatted = []
        for key, value in data.items():
            if isinstance(value, dict):
                formatted.append(f"{key}:")
                for k, v in value.items():
                    formatted.append(f"  - {k}: {v}")
            else:
                formatted.append(f"- {key}: {value}")
        return "\n".join(formatted)

    def _get_fallback_response(self, question_type: str, language: str) -> str:
        """Risposte fallback quando API non disponibile"""
        fallbacks = {
            "it": {
                "GREETING": "Ciao! Come posso aiutarti oggi?",
                "HELP": "Sono Milhena, posso aiutarti con analisi dati, automazione processi e supporto decisionale.",
                "GENERAL": "Sto elaborando la tua richiesta. Riprova tra poco."
            },
            "en": {
                "GREETING": "Hello! How can I help you today?",
                "HELP": "I'm Milhena, I can help with data analysis, process automation and decision support.",
                "GENERAL": "Processing your request. Please try again shortly."
            }
        }

        lang = language if language in fallbacks else "it"
        return fallbacks[lang].get(question_type, fallbacks[lang]["GENERAL"])


class HybridModelRouter:
    """Router intelligente per scegliere tra Gemini e Groq"""

    def __init__(self):
        """Inizializza router con entrambi i client"""
        self.gemini_client = GeminiFastClient()

        # Import Groq client se disponibile
        try:
            from groq_fast_client import GroqFastClient
            self.groq_client = GroqFastClient()
            self.has_groq = True
            logger.info("✅ Router ibrido Gemini+Groq pronto")
        except Exception as e:
            logger.warning(f"Groq non disponibile, solo Gemini: {e}")
            self.groq_client = None
            self.has_groq = False

    async def classify_with_best_model(self, question: str) -> Dict[str, Any]:
        """Classifica usando il modello migliore disponibile"""

        # Prova prima Gemini (gratuito)
        try:
            result = await self.gemini_client.classify_question(question)
            if result.get("confidence", 0) > 0.8:
                return result
        except Exception as e:
            logger.warning(f"Gemini fallito, provo Groq: {e}")

        # Fallback a Groq se disponibile
        if self.has_groq and self.groq_client:
            try:
                return await self.groq_client.classify_question(question)
            except Exception as e:
                logger.error(f"Anche Groq fallito: {e}")

        # Fallback finale
        return {
            "type": "GENERAL",
            "confidence": 0.3,
            "model": "fallback"
        }

    async def generate_response(self, question: str, question_type: str, use_fast: bool = True) -> str:
        """Genera risposta con il modello ottimale"""

        if use_fast:
            # Per risposte veloci, usa Gemini Flash o Groq
            try:
                return await self.gemini_client.generate_fast_response(
                    question, question_type, "it"
                )
            except Exception as e:
                logger.warning(f"Gemini fallito: {e}")
                if self.has_groq:
                    return await self.groq_client.generate_fast_response(
                        question, question_type, "it"
                    )
        else:
            # Per analisi complesse, preferisci Gemini Pro
            return await self.gemini_client.analyze_business_data(
                question, {}
            )

        return "Sistema temporaneamente non disponibile"


# Test standalone
if __name__ == "__main__":
    async def test():
        # Test Gemini
        print("🧪 TEST GEMINI CLIENT")
        print("=" * 50)

        client = GeminiFastClient()

        # Test classificazione
        test_questions = [
            "Ciao!",
            "Come funzioni?",
            "Quante vendite abbiamo fatto oggi?",
            "Analizza il trend delle vendite"
        ]

        for q in test_questions:
            print(f"\n📝 Domanda: {q}")
            result = await client.classify_question(q)
            print(f"   Tipo: {result['type']} (confidence: {result.get('confidence', 0):.1%})")
            print(f"   Latenza: {result.get('latency_ms', 0):.0f}ms")

            # Genera risposta
            response = await client.generate_fast_response(q, result['type'], 'it')
            print(f"   Risposta: {response[:100]}...")

        # Test router ibrido
        print("\n" + "=" * 50)
        print("🧪 TEST ROUTER IBRIDO")

        router = HybridModelRouter()
        result = await router.classify_with_best_model("Mostrami le statistiche")
        print(f"Router result: {result}")

    asyncio.run(test())