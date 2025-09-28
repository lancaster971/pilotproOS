"""
Test completo di Milhena v3.0
Testa tutti i componenti end-to-end con query reali
"""
import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.milhena.llm_disambiguator import LLMDisambiguator
from app.milhena.intent_analyzer import IntentAnalyzer
from app.milhena.response_generator import ResponseGenerator
from app.milhena.core import MilhenaConfig
from app.milhena.masking import TechnicalMaskingEngine
from app.milhena.cache_manager import CacheManager

async def test_milhena_complete():
    """Test completo del workflow Milhena"""

    print("\n" + "="*80)
    print("🧪 TEST COMPLETO MILHENA v3.0")
    print("="*80 + "\n")

    # Initialize components
    config = MilhenaConfig()
    disambiguator = LLMDisambiguator(config)
    intent_analyzer = IntentAnalyzer(config)
    masking_engine = TechnicalMaskingEngine()
    response_generator = ResponseGenerator(config, masking_engine)

    # Test queries
    test_queries = [
        ("ciao", "Saluto semplice"),
        ("Quanti workflow ho attivi?", "Query business - conteggio"),
        ("Il sistema è andato a puttane", "Linguaggio volgare da disambiguare"),
        ("Mostrami gli errori di oggi", "Richiesta errori"),
        ("Dammi le statistiche del database PostgreSQL", "Query tecnica da bloccare"),
    ]

    results = []

    for query, description in test_queries:
        print(f"\n{'─'*80}")
        print(f"📝 TEST: {description}")
        print(f"Query: \"{query}\"")
        print(f"{'─'*80}\n")

        try:
            # Step 1: Disambiguate
            print("1️⃣ Disambiguating...")
            disambiguation = await disambiguator.disambiguate(query, {})

            if isinstance(disambiguation, dict):
                print(f"   ✅ Disambiguation (dict): {disambiguation}")
                is_ambiguous = disambiguation.get('is_ambiguous', False)
                clarified = disambiguation.get('clarified_intent', query)
                confidence = disambiguation.get('confidence', 0.0)
            else:
                print(f"   ✅ Disambiguation (object):")
                print(f"      - is_ambiguous: {disambiguation.is_ambiguous}")
                print(f"      - clarified_intent: {disambiguation.clarified_intent}")
                print(f"      - confidence: {disambiguation.confidence}")
                is_ambiguous = disambiguation.is_ambiguous
                clarified = disambiguation.clarified_intent
                confidence = disambiguation.confidence

            # Step 2: Classify Intent
            print(f"\n2️⃣ Classifying intent...")
            intent = await intent_analyzer.classify(query, {}, f"test-session-{hash(query)}")
            print(f"   ✅ Intent: {intent}")

            # Step 3: Generate Response
            print(f"\n3️⃣ Generating response...")
            response = await response_generator.generate(
                query=query,
                intent=intent,
                context={},
                session_id=f"test-{hash(query)}"
            )
            print(f"   ✅ Response: {response}")

            results.append({
                "query": query,
                "description": description,
                "disambiguation": {
                    "is_ambiguous": is_ambiguous,
                    "clarified": clarified,
                    "confidence": confidence
                },
                "intent": intent,
                "response": response,
                "success": True
            })

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "query": query,
                "description": description,
                "error": str(e),
                "success": False
            })

    # Print summary
    print("\n" + "="*80)
    print("📊 REPORT COMPLETO")
    print("="*80 + "\n")

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['description']}")
        print(f"   Query: \"{result['query']}\"")

        if result['success']:
            print(f"   ✅ SUCCESS")
            print(f"   Intent: {result['intent']}")
            print(f"   Disambiguazione: {result['disambiguation']['is_ambiguous']} (conf: {result['disambiguation']['confidence']:.2f})")
            print(f"   Risposta: {result['response'][:100]}...")
        else:
            print(f"   ❌ FAILED: {result['error']}")

    success_count = sum(1 for r in results if r['success'])
    print(f"\n{'='*80}")
    print(f"✅ Successi: {success_count}/{len(results)}")
    print(f"{'='*80}\n")

    return results

if __name__ == "__main__":
    results = asyncio.run(test_milhena_complete())