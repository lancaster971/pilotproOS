#!/usr/bin/env python3
"""
Test Smart LLM Router with LIVE LLMs
Tests actual API calls with real keys
"""
import asyncio
import os
from app.core.router import SmartLLMRouter, RouterConfig, ModelTier

async def test_live_routing():
    """Test router with real LLM API calls"""

    # Initialize router with real API keys from environment
    config = RouterConfig.from_env()

    if not config.groq_api_key:
        print("⚠️  GROQ_API_KEY not set, skipping Groq tests")

    if not config.openai_api_key:
        print("⚠️  OPENAI_API_KEY not set, skipping OpenAI tests")

    router = SmartLLMRouter(config)

    print("\n" + "="*80)
    print("SMART LLM ROUTER - LIVE API TESTING")
    print("="*80)

    # Test different tier models if APIs are available
    test_queries = {
        ModelTier.FREE_GROQ: {
            "query": "Ciao, come stai?",
            "expected": "Simple greeting response"
        },
        ModelTier.SPECIAL_NANO: {
            "query": "Qual è l'ultimo messaggio?",
            "expected": "Message query response"
        },
        ModelTier.SPECIAL_MINI: {
            "query": "Analizza i dati di oggi",
            "expected": "Analysis response"
        }
    }

    for tier, test_case in test_queries.items():
        print(f"\n📝 Testing {tier.value}...")
        print(f"   Query: {test_case['query']}")

        try:
            # Route query
            decision = await router.route(test_case['query'], force_tier=tier)
            print(f"   ✅ Routing: {decision.model_name} (confidence: {decision.confidence:.1%})")

            # Get model instance
            model = router.get_model(tier)

            # Test actual API call if key exists
            if tier == ModelTier.FREE_GROQ and config.groq_api_key and config.groq_api_key != "test_key":
                try:
                    response = await model.ainvoke(test_case['query'])
                    print(f"   🤖 Response: {str(response.content)[:100]}...")
                except Exception as e:
                    print(f"   ❌ API Error: {e}")

            elif tier in [ModelTier.SPECIAL_NANO, ModelTier.SPECIAL_MINI] and config.openai_api_key and config.openai_api_key != "test_key":
                try:
                    response = await model.ainvoke(test_case['query'])
                    print(f"   🤖 Response: {str(response.content)[:100]}...")
                except Exception as e:
                    print(f"   ❌ API Error: {e}")
            else:
                print(f"   ⏭️  Skipped (no valid API key)")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Test the ML classifier accuracy
    print("\n" + "="*80)
    print("ML CLASSIFIER ACCURACY TEST")
    print("="*80)

    accuracy_tests = [
        ("Ciao!", ModelTier.FREE_GROQ),
        ("Mostra tutti i processi", ModelTier.FREE_GEMINI),
        ("Ultimo messaggio del workflow", ModelTier.SPECIAL_NANO),
        ("Analisi complessa dei dati", ModelTier.SPECIAL_MINI),
    ]

    correct = 0
    for query, expected_tier in accuracy_tests:
        decision = await router.route(query)
        is_correct = decision.model_tier == expected_tier
        correct += is_correct

        symbol = "✅" if is_correct else "❌"
        print(f"{symbol} Query: {query[:30]:<30} | Expected: {expected_tier.value:<15} | Got: {decision.model_tier.value}")

    accuracy = (correct / len(accuracy_tests)) * 100
    print(f"\n📊 Accuracy: {accuracy:.1f}% ({correct}/{len(accuracy_tests)})")

    # Show usage statistics
    stats = router.get_usage_stats()
    print(f"\n💰 Total cost so far: ${stats['total_cost']:.6f}")
    print(f"✨ Savings: {stats['savings_percentage']:.1f}%")

    print("\n✅ Live testing completed!")

if __name__ == "__main__":
    # Set test API keys if needed (or use real ones from environment)
    if not os.getenv("GROQ_API_KEY"):
        os.environ["GROQ_API_KEY"] = "test_key"  # Replace with real key for live test

    if not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "test_key"  # Replace with real key for live test

    asyncio.run(test_live_routing())