#!/usr/bin/env python3
"""
Cache Semantica e Timeout Manager per Milhena
Ottimizzazioni per velocizzare risposte business
"""

import hashlib
import json
import time
import signal
import asyncio
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SemanticCache:
    """Cache semantica per risposte business frequenti"""

    def __init__(self, ttl_seconds: int = 60):
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl = ttl_seconds
        self.hits = 0
        self.misses = 0

    def _generate_key(self, question: str, question_type: str) -> str:
        """Genera chiave semantica normalizzata"""
        # Normalizza la domanda
        normalized = question.lower().strip()

        # Rimuovi variazioni comuni
        replacements = {
            "quanti": "numero",
            "workflow attivi": "active_workflows",
            "ci sono": "",
            "abbiamo": "",
            "nel database": "",
            "?": "",
            "!": "",
            ".": ""
        }

        for old, new in replacements.items():
            normalized = normalized.replace(old, new)

        # Genera hash
        content = f"{question_type}:{normalized}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, question: str, question_type: str) -> Optional[Any]:
        """Recupera dalla cache se disponibile e valida"""
        key = self._generate_key(question, question_type)

        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                self.hits += 1
                logger.info(f"✅ CACHE HIT ({self.hits}/{self.hits + self.misses})")
                return value
            else:
                # Scaduto, rimuovi
                del self.cache[key]

        self.misses += 1
        return None

    def set(self, question: str, question_type: str, response: Any):
        """Salva in cache"""
        # Cache solo risposte business data e analysis
        if question_type in ["BUSINESS_DATA", "ANALYSIS"]:
            key = self._generate_key(question, question_type)
            self.cache[key] = (response, time.time())
            logger.info(f"💾 Cached {question_type} response")

    def stats(self) -> Dict[str, Any]:
        """Statistiche cache"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "entries": len(self.cache)
        }


class TimeoutManager:
    """Gestione timeout con risposta parziale"""

    def __init__(self, timeout_seconds: int = 30):
        self.timeout = timeout_seconds
        self.partial_result = None

    async def execute_with_timeout(self, coroutine, partial_message: str = None) -> Tuple[Any, bool]:
        """
        Esegue coroutine con timeout

        Returns:
            (result, timed_out)
        """
        try:
            # Crea task
            task = asyncio.create_task(coroutine)

            # Attendi con timeout
            result = await asyncio.wait_for(task, timeout=self.timeout)
            return result, False

        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Timeout dopo {self.timeout}s")

            # Cancella il task
            task.cancel()

            # Ritorna messaggio parziale
            if partial_message:
                return partial_message, True
            else:
                return {
                    "response": f"⚠️ L'analisi sta impiegando più tempo del previsto ({self.timeout}s). "
                               f"I nostri sistemi stanno elaborando una risposta completa. "
                               f"Nel frattempo, posso aiutarti con domande più specifiche.",
                    "timed_out": True
                }, True

        except Exception as e:
            logger.error(f"❌ Errore in timeout manager: {e}")
            raise


class LLMCallTracker:
    """Traccia chiamate LLM per diagnostica"""

    def __init__(self):
        self.calls = []

    def track_call(self, agent: str, model: str, input_tokens: int = 0,
                   output_tokens: int = 0, duration_ms: float = 0):
        """Registra chiamata LLM"""
        self.calls.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "duration_ms": duration_ms
        })

        logger.info(f"📊 LLM Call: {agent} -> {model} "
                   f"({input_tokens}+{output_tokens} tokens, {duration_ms:.0f}ms)")

    def get_summary(self) -> Dict[str, Any]:
        """Riassunto chiamate"""
        if not self.calls:
            return {"total_calls": 0}

        total_input = sum(c["input_tokens"] for c in self.calls)
        total_output = sum(c["output_tokens"] for c in self.calls)
        total_time = sum(c["duration_ms"] for c in self.calls)

        # Raggruppa per modello
        by_model = {}
        for call in self.calls:
            model = call["model"]
            if model not in by_model:
                by_model[model] = {"calls": 0, "tokens": 0, "time_ms": 0}
            by_model[model]["calls"] += 1
            by_model[model]["tokens"] += call["input_tokens"] + call["output_tokens"]
            by_model[model]["time_ms"] += call["duration_ms"]

        return {
            "total_calls": len(self.calls),
            "total_tokens": total_input + total_output,
            "total_time_ms": total_time,
            "by_model": by_model,
            "calls": self.calls[-5:]  # Ultime 5 chiamate
        }


# Singleton instances
_semantic_cache = None
_timeout_manager = None
_llm_tracker = None

def get_semantic_cache() -> SemanticCache:
    """Ottieni istanza singleton cache"""
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache(ttl_seconds=60)
    return _semantic_cache

def get_timeout_manager(timeout: int = 30) -> TimeoutManager:
    """Ottieni istanza timeout manager"""
    global _timeout_manager
    if _timeout_manager is None:
        _timeout_manager = TimeoutManager(timeout_seconds=timeout)
    return _timeout_manager

def get_llm_tracker() -> LLMCallTracker:
    """Ottieni istanza LLM tracker"""
    global _llm_tracker
    if _llm_tracker is None:
        _llm_tracker = LLMCallTracker()
    return _llm_tracker


# Test
if __name__ == "__main__":
    import asyncio

    # Test cache
    cache = get_semantic_cache()
    cache.set("Quanti workflow attivi abbiamo?", "BUSINESS_DATA", "42 workflow")

    # Dovrebbe trovare in cache anche con variazioni
    result = cache.get("Quanti workflow attivi ci sono nel database?", "BUSINESS_DATA")
    print(f"Cache test: {result}")
    print(f"Stats: {cache.stats()}")

    # Test timeout
    async def slow_task():
        await asyncio.sleep(5)
        return "Completed"

    async def test_timeout():
        manager = get_timeout_manager(timeout=2)
        result, timed_out = await manager.execute_with_timeout(slow_task())
        print(f"Timeout test: {result}, timed_out={timed_out}")

    asyncio.run(test_timeout())