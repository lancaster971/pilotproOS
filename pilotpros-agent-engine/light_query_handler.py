#!/usr/bin/env python3
"""
Light Query Handler - Fast Path per Query Semplici
Bypassa CrewAI per query deterministiche su workflow
"""

import logging
import time
from typing import Dict, Any, Optional
from tools.business_intelligent_query_tool import BusinessIntelligentQueryTool

logger = logging.getLogger(__name__)

class LightQueryHandler:
    """Handler veloce per query semplici senza orchestrazione multi-agent"""

    def __init__(self):
        self.bi_tool = BusinessIntelligentQueryTool()
        self.simple_patterns = [
            # Pattern per query semplici deterministiche
            "quanti workflow",
            "workflow attivi",
            "numero workflow",
            "active workflows",
            "esecuzioni oggi",
            "executions today",
            "stato sistema",
            "system status",
            "workflow totali",
            "total workflows"
        ]

        # Query che richiedono analisi complessa (NON light path)
        self.complex_triggers = [
            "analizza",
            "analyze",
            "trend",
            "confronta",
            "compare",
            "errore",
            "error",
            "problema",
            "issue",
            "ottimizza",
            "optimize",
            "suggerisci",
            "suggest",
            "perché",
            "why",
            "come mai",
            "causa",
            "reason"
        ]

    def is_simple_query(self, question: str) -> bool:
        """
        Determina se una query è semplice e deterministica

        Criteri:
        - Contiene pattern di query semplice
        - NON contiene trigger di complessità
        - Lunghezza ragionevole (< 100 caratteri)
        """
        question_lower = question.lower()

        # Check lunghezza
        if len(question) > 100:
            return False

        # Check trigger complessi
        for trigger in self.complex_triggers:
            if trigger in question_lower:
                logger.debug(f"Query complessa rilevata: contiene '{trigger}'")
                return False

        # Check pattern semplici
        for pattern in self.simple_patterns:
            if pattern in question_lower:
                logger.debug(f"Query semplice rilevata: match '{pattern}'")
                return True

        # Default: se è molto corta e sembra una metrica
        if len(question) < 50 and any(word in question_lower for word in ["quanti", "how many", "numero", "count"]):
            return True

        return False

    def handle_simple_query(self, question: str) -> Dict[str, Any]:
        """
        Gestisce query semplice con accesso diretto al tool

        Returns:
            Dict con response e metadata
        """
        start_time = time.time()

        try:
            logger.info(f"LIGHT PATH: Query diretta al tool per '{question[:50]}...'")

            # Chiamata diretta al tool, bypassa CrewAI
            response = self.bi_tool._run(question)

            elapsed = (time.time() - start_time) * 1000
            logger.info(f"LIGHT PATH: Risposta in {elapsed:.0f}ms (vs 15000ms multi-agent)")

            return {
                "success": True,
                "response": response,
                "fast_path": True,
                "light_query": True,
                "response_time_ms": elapsed,
                "agents_used": ["direct_tool_access"],
                "crew_bypassed": True
            }

        except Exception as e:
            logger.error(f"Errore in light query handler: {e}")
            # Fallback: ritorna None per usare il path normale
            return None


class DataSnapshotAgent:
    """
    Agente monolitico leggero per snapshot dati
    NO orchestrazione, NO delegazione, solo tool access
    """

    def __init__(self):
        self.bi_tool = BusinessIntelligentQueryTool()
        self.role = "DataSnapshotResponder"
        self.goal = "Rispondere direttamente a domande semplici su workflow ed esecuzioni"

    async def execute(self, question: str) -> str:
        """
        Esegue query diretta senza overhead CrewAI
        """
        start = time.time()

        try:
            # Nessun LLM call, nessuna validazione, solo tool
            result = self.bi_tool._run(question)

            elapsed = (time.time() - start) * 1000
            logger.info(f"SNAPSHOT AGENT: Completato in {elapsed:.0f}ms")

            return result

        except Exception as e:
            logger.error(f"Snapshot agent error: {e}")
            return f"Impossibile recuperare i dati: {str(e)}"


def get_light_handler() -> LightQueryHandler:
    """Factory per ottenere handler singleton"""
    if not hasattr(get_light_handler, "_instance"):
        get_light_handler._instance = LightQueryHandler()
    return get_light_handler._instance


def get_snapshot_agent() -> DataSnapshotAgent:
    """Factory per ottenere agent singleton"""
    if not hasattr(get_snapshot_agent, "_instance"):
        get_snapshot_agent._instance = DataSnapshotAgent()
    return get_snapshot_agent._instance


# Test
if __name__ == "__main__":
    handler = get_light_handler()

    # Test detection
    simple_queries = [
        "Quanti workflow attivi abbiamo?",
        "Numero di workflow totali",
        "Workflow attivi nel database",
        "How many active workflows?"
    ]

    complex_queries = [
        "Analizza le performance dei workflow",
        "Perché i workflow sono lenti?",
        "Confronta i workflow di oggi con ieri",
        "Suggerisci ottimizzazioni per i processi"
    ]

    print("TEST DETECTION QUERY SEMPLICI:")
    print("-" * 50)
    for q in simple_queries:
        is_simple = handler.is_simple_query(q)
        print(f"[{'SIMPLE' if is_simple else 'COMPLEX'}] {q}")

    print("\nTEST DETECTION QUERY COMPLESSE:")
    print("-" * 50)
    for q in complex_queries:
        is_simple = handler.is_simple_query(q)
        print(f"[{'SIMPLE' if is_simple else 'COMPLEX'}] {q}")

    # Test execution
    print("\nTEST ESECUZIONE LIGHT PATH:")
    print("-" * 50)
    result = handler.handle_simple_query("Quanti workflow attivi?")
    if result:
        print(f"Response time: {result['response_time_ms']:.0f}ms")
        print(f"Response: {result['response'][:200]}...")