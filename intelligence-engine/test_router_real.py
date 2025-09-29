#!/usr/bin/env python3
"""
Test Smart LLM Router with real queries
"""
import asyncio
import json
from app.core.router import SmartLLMRouter, RouterConfig

async def test_router_with_real_queries():
    """Test router with realistic Italian queries"""

    # Initialize router with test config
    config = RouterConfig(
        groq_api_key="test_key",
        openai_api_key="test_key",
        google_api_key="test_key",
        audit_enabled=False  # Disable DB logging for test
    )

    router = SmartLLMRouter(config)

    # Test queries in Italian
    test_cases = [
        # Simple greetings
        "Ciao Milhena",
        "Buongiorno, come stai?",
        "Tutto bene?",

        # Status checks
        "Come va il sistema oggi?",
        "Ci sono problemi?",

        # Message queries
        "Qual è l'ultimo messaggio del workflow Fatture?",
        "Mostra il messaggio di errore",
        "C'è un nuovo messaggio?",

        # Batch/List requests
        "Mostra tutti i processi attivi",
        "Elenca tutte le elaborazioni di oggi",
        "Dammi la lista completa",

        # Complex analysis
        "Analizza le performance degli ultimi 7 giorni",
        "Confronta i dati di questa settimana con la precedente",
        "Genera un report dettagliato con grafici e metriche",

        # Mixed complexity
        "Il processo Orders è fallito, cosa è successo?",
        "Quante elaborazioni sono state completate oggi?",
    ]

    print("\n" + "="*80)
    print("SMART LLM ROUTER - REAL QUERY TESTING")
    print("="*80)

    results = []

    for query in test_cases:
        decision = await router.route(query)

        result = {
            "query": query[:50] + "..." if len(query) > 50 else query,
            "tier": decision.model_tier.value,
            "model": decision.model_name,
            "confidence": f"{decision.confidence:.1%}",
            "tokens": decision.estimated_tokens,
            "cost": f"${decision.estimated_cost:.6f}",
            "reasoning": decision.reasoning
        }
        results.append(result)

        print(f"\n📝 Query: {result['query']}")
        print(f"   → Tier: {result['tier']}")
        print(f"   → Model: {result['model']}")
        print(f"   → Confidence: {result['confidence']}")
        print(f"   → Est. Cost: {result['cost']}")

    # Calculate totals
    print("\n" + "="*80)
    print("USAGE STATISTICS")
    print("="*80)

    stats = router.get_usage_stats()

    print(f"\n📊 Total Requests: {len(test_cases)}")
    print(f"💰 Total Tokens: {stats['total_tokens']}")
    print(f"💵 Total Cost: ${stats['total_cost']:.6f}")
    print(f"✨ Savings: {stats['savings_percentage']:.1f}%")

    print("\n📈 Distribution by Tier:")
    for tier, data in stats['by_tier'].items():
        if data['tokens'] > 0:
            print(f"   • {tier}: {data['tokens']} tokens ({data['percentage']:.1f}%) - ${data['cost']:.6f}")

    # Test feature extraction details
    print("\n" + "="*80)
    print("FEATURE EXTRACTION EXAMPLES")
    print("="*80)

    example_queries = [
        "Ciao Milhena",
        "Mostra l'ultimo messaggio del workflow",
        "Analizza tutti i processi e genera un report completo con grafici"
    ]

    for query in example_queries:
        features = router.feature_extractor.extract(query)
        print(f"\n📝 Query: {query}")
        print(f"   Features:")
        print(f"   • Greeting: {features['has_greeting']}")
        print(f"   • Technical: {features['has_technical_terms']}")
        print(f"   • Complexity: {features['complexity_score']:.2f}")
        print(f"   • Language: {features['language']}")
        print(f"   • Has 'messaggio': {features['has_messaggio']}")
        print(f"   • Is batch: {features['is_batch_request']}")

    print("\n✅ Test completed successfully!")

    return results

if __name__ == "__main__":
    results = asyncio.run(test_router_with_real_queries())

    # Save results to file
    with open("router_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n💾 Results saved to router_test_results.json")