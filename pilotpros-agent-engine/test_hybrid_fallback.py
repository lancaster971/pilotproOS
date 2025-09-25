#!/usr/bin/env python3
"""
Test sistema ibrido con fallback forzato
"""

import asyncio
import os
from fast_bypass import TokenSaver

async def test_forced_fallback():
    """Testa il fallback OpenRouter quando Gemini fallisce"""

    # Configura API keys
    os.environ["GEMINI_API_KEY"] = "fake_key_to_force_failure"  # Forza fallback
    os.environ["OPENROUTER_API_KEY"] = "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"

    print("🧪 TEST FALLBACK FORZATO: Gemini → OpenRouter")
    print("=" * 50)

    saver = TokenSaver()

    test_messages = [
        "Ciao!",
        "Che tecnologie usate?",
        "Come funzioni?"
    ]

    for msg in test_messages:
        print(f"\n📝 '{msg}'")
        result = await saver.smart_response(msg)

        print(f"   🛤️  Path: {result['path']}")
        print(f"   🏢 Provider: {result.get('provider', 'unknown')}")
        print(f"   💬 Response: {result['response'][:80]}...")
        print(f"   ⚡ Tokens saved: {result.get('tokens_saved', False)}")

    print(f"\n📊 STATISTICHE FINALI:")
    stats = saver.get_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")

    # Statistiche provider
    print(f"\n🔄 PROVIDER STATS:")
    print(f"   Gemini requests: {saver.bypass_stats['gemini_requests']}")
    print(f"   OpenRouter fallbacks: {saver.bypass_stats['openrouter_fallbacks']}")
    print(f"   Both failed: {saver.bypass_stats['both_providers_failed']}")

if __name__ == "__main__":
    asyncio.run(test_forced_fallback())