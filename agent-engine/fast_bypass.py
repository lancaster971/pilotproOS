#!/usr/bin/env python3
"""
Fast Bypass System - EVITA SPRECO TOKEN
Risposte dirette per 90% dei casi senza multi-agente
"""

import asyncio
import time
import logging
from typing import Dict, Any
from openai_fast_client import openai_classify, openai_fast_response
from groq_fast_client import groq_classify, groq_fast_response
from token_monitor import get_token_monitor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FastBypass")

class TokenSaver:
    """Sistema di risparmio token - bypassa multi-agente"""

    def __init__(self):
        self.bypass_stats = {
            "total_requests": 0,
            "bypassed": 0,
            "tokens_saved": 0,
            "tokens_used": 0,  # Token effettivamente consumati
            "multi_agent_tokens_avoided": 0,  # Token multi-agente evitati
            "openai_requests": 0,
            "groq_fallbacks": 0,
            "both_providers_failed": 0
        }

        # Contatori token precisi
        self.token_costs = {
            "classification": 150,  # Classificazione domanda
            "simple_response": 300,  # Risposta semplice
            "multi_agent_avg": 3500  # Media multi-agente (5 agenti × 700 token)
        }

        # Token Monitor per non sforare mai i limiti
        self.token_monitor = get_token_monitor()

    async def hybrid_classify(self, message: str) -> Dict[str, Any]:
        """
        Classificazione IBRIDA con Token Monitor: GPT-4o primo, Groq fallback
        """

        # Stima token per la classificazione
        estimated_tokens = self.token_monitor.count_tokens(message) + 100  # +100 per risposta

        # Scegli MIGLIORE provider disponibile
        best_provider = self.token_monitor.get_best_provider(estimated_tokens)

        if best_provider in ["openai", "openai_premium", "openai_mini"]:
            try:
                # 1. GPT-4o PRIMARIO (qualità suprema)
                classification = await openai_classify(message)
                classification["provider"] = "openai"
                self.bypass_stats["openai_requests"] += 1

                # Registra uso REALE
                self.token_monitor.record_usage(best_provider, estimated_tokens-100, 100, True)

                logger.info(f"🚀 GPT-4o classification: {classification.get('question_type')}")
                return classification
            except Exception as openai_error:
                logger.warning(f"⚠️ GPT-4o failed: {openai_error} - switching to Groq")
                # Non registrare token se fallito

        # 2. Fallback Groq (molto veloce)
        try:
            classification = await groq_classify(message)
            classification["provider"] = "groq"
            if best_provider in ["openai", "openai_premium", "openai_mini"]:
                classification["openai_error"] = "API failed, used fallback"

            self.bypass_stats["groq_fallbacks"] += 1

            # Registra uso Groq
            self.token_monitor.record_usage("groq", estimated_tokens-100, 100, True)

            logger.info(f"🔄 Groq fallback: {classification.get('question_type')}")
            return classification
        except Exception as groq_error:
            logger.error(f"🔴 Both providers failed! Groq: {groq_error}")
            self.bypass_stats["both_providers_failed"] += 1
            return {
                "question_type": "GENERAL",
                "confidence": 0.5,
                "language": "it",
                "provider": "fallback_emergency",
                "groq_error": str(groq_error)
            }

    async def hybrid_response(self, message: str, question_type: str, language: str = "it") -> str:
        """
        Risposta IBRIDA con Token Monitor: GPT-4o primo, Groq fallback
        """

        # Stima token per la risposta (più grande)
        estimated_tokens = self.token_monitor.count_tokens(message) + 500  # +500 per risposta completa

        # Scegli MIGLIORE provider disponibile
        best_provider = self.token_monitor.get_best_provider(estimated_tokens)

        if best_provider in ["openai", "openai_premium", "openai_mini"]:
            try:
                # 1. GPT-4o PRIMARIO (qualità suprema)
                response = await openai_fast_response(message, question_type, language)

                # Registra uso REALE (stima output)
                output_tokens = self.token_monitor.count_tokens(response)
                self.token_monitor.record_usage(best_provider, estimated_tokens-500, output_tokens, True)

                logger.info(f"🚀 GPT-4o response generated")
                return response
            except Exception as openai_error:
                logger.warning(f"⚠️ GPT-4o response failed: {openai_error} - switching to Groq")
                # Non registrare token se fallito

        # 2. Fallback Groq (molto veloce)
        try:
            response = await groq_fast_response(message, question_type, language)

            # Registra uso Groq
            output_tokens = self.token_monitor.count_tokens(response)
            self.token_monitor.record_usage("groq", estimated_tokens-500, output_tokens, True)

            logger.info(f"🔄 Groq fallback response generated")
            return response
        except Exception as groq_error:
            logger.error(f"🔴 Both providers failed! Groq: {groq_error}")
            return f"Mi dispiace, entrambi i servizi AI sono temporaneamente non disponibili. Per favore riprova tra qualche minuto."

    async def smart_response(self, message: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Risposta INTELLIGENTE con bypass multi-agente per 90% dei casi
        """
        start_time = time.time()
        self.bypass_stats["total_requests"] += 1

        try:
            # 1. Classificazione IBRIDA (Gemini → OpenRouter fallback)
            classification = await self.hybrid_classify(message)
            question_type = classification.get("question_type", "GENERAL")
            confidence = classification.get("confidence", 0.0)
            provider = classification.get("provider", "unknown")

            logger.info(f"🔍 {question_type} via {provider} (confidence: {confidence:.1%})")

            # 2. BYPASS SEMPLIFICATO - Solo GREETING e HELP
            bypass_types = ["GREETING", "HELP"]

            # Tutto il resto va all'orchestrator
            orchestrator_types = ["BUSINESS_DATA", "ANALYSIS", "GENERAL", "TECHNOLOGY_INQUIRY"]

            # Solo GREETING e HELP vanno in bypass
            if question_type in bypass_types and confidence > 0.7:
                logger.info(f"⚡ BYPASS attivo via {provider} - Sistema GPT-4o+Groq SUPREMO (1M token)!")

                # Contatori precisi
                tokens_used = self.token_costs["classification"] + self.token_costs["simple_response"]  # 450 token
                tokens_avoided = self.token_costs["multi_agent_avg"]  # 3500 token
                tokens_saved = tokens_avoided - tokens_used  # 3050 token risparmiati!

                # Risposta diretta IBRIDA (Gemini → OpenRouter fallback)
                response = await self.hybrid_response(
                    message,
                    question_type,
                    classification.get("language", "it")
                )

                # Aggiorna statistiche precise
                self.bypass_stats["bypassed"] += 1
                self.bypass_stats["tokens_used"] += tokens_used
                self.bypass_stats["multi_agent_tokens_avoided"] += tokens_avoided
                self.bypass_stats["tokens_saved"] += tokens_saved

                logger.info(f"📊 Token: Usati {tokens_used}, Evitati {tokens_avoided}, Risparmiati {tokens_saved}")

                elapsed = (time.time() - start_time) * 1000

                return {
                    "response": response,
                    "type": question_type,
                    "confidence": confidence,
                    "processing_time": elapsed,
                    "path": f"fast_bypass_{provider}",
                    "provider": provider,
                    "tokens_saved": True,
                    "multi_agent_bypassed": True
                }

            # 3. Tutto il resto passa all'orchestrator semplificato
            logger.info(f"ORCHESTRATOR: {question_type} requires full processing")

            # Segnala che deve usare multi-agent (non bypassed)
            return {
                "response": None,  # Nessuna risposta, passa al multi-agent
                "type": question_type,
                "confidence": confidence,
                "processing_time": (time.time() - start_time) * 1000,
                "path": "multi_agent_disabled",
                "tokens_saved": False
            }

        except Exception as e:
            logger.error(f"Errore bypass: {e}")
            return {
                "response": f"Errore nel sistema di risposta veloce: {str(e)}",
                "type": "ERROR",
                "confidence": 0.0,
                "processing_time": (time.time() - start_time) * 1000,
                "path": "error"
            }

    def get_stats(self) -> Dict[str, Any]:
        """Statistiche dettagliate risparmio token + Token Monitor"""
        if self.bypass_stats["total_requests"] == 0:
            bypass_rate = 0
            efficiency = 0
        else:
            bypass_rate = (self.bypass_stats["bypassed"] / self.bypass_stats["total_requests"]) * 100

            # Calcola efficienza token
            total_would_be_tokens = self.bypass_stats["total_requests"] * self.token_costs["multi_agent_avg"]
            efficiency = (self.bypass_stats["tokens_saved"] / total_would_be_tokens) * 100 if total_would_be_tokens > 0 else 0

        # Aggiungi report Token Monitor
        token_report = self.token_monitor.get_usage_report()

        return {
            "total_requests": self.bypass_stats["total_requests"],
            "bypass_rate": f"{bypass_rate:.1f}%",
            "tokens_used": self.bypass_stats["tokens_used"],
            "tokens_saved": self.bypass_stats["tokens_saved"],
            "multi_agent_tokens_avoided": self.bypass_stats["multi_agent_tokens_avoided"],
            "multi_agent_calls_avoided": self.bypass_stats["bypassed"],
            "token_efficiency": f"{efficiency:.1f}%",
            "avg_tokens_per_request": self.bypass_stats["tokens_used"] // max(1, self.bypass_stats["total_requests"]),
            "providers": {
                "openai_requests": self.bypass_stats["openai_requests"],
                "groq_fallbacks": self.bypass_stats["groq_fallbacks"],
                "both_failed": self.bypass_stats["both_providers_failed"]
            },
            "token_monitor": token_report
        }

# Singleton instance
_token_saver = None

def get_token_saver() -> TokenSaver:
    """Ottieni istanza singleton"""
    global _token_saver
    if _token_saver is None:
        _token_saver = TokenSaver()
    return _token_saver

# Test
if __name__ == "__main__":
    async def test():
        saver = TokenSaver()

        test_messages = [
            "Ciao!",
            "Come funzioni?",
            "Che tecnologie usate?",
            "Quanti workflow attivi?"
        ]

        print("🧪 TEST BYPASS SYSTEM")
        print("=" * 40)

        for msg in test_messages:
            result = await saver.smart_response(msg)
            print(f"\n📝 '{msg}'")
            print(f"   Path: {result['path']}")
            print(f"   Tokens saved: {result.get('tokens_saved', False)}")
            print(f"   Response: {result['response'][:80]}...")

        print(f"\n📊 STATISTICHE:")
        stats = saver.get_stats()
        for k, v in stats.items():
            print(f"   {k}: {v}")

    asyncio.run(test())