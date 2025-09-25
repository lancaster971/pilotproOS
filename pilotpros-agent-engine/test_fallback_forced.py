#!/usr/bin/env python3
"""
TEST FALLBACK FORZATO: Gemini FAKE → OpenRouter REALE
"""

import asyncio
import os
from fast_bypass import TokenSaver

async def test_fallback_forced():
    """Forza errore Gemini per testare fallback OpenRouter"""

    # FORZA ERRORE GEMINI
    os.environ["GEMINI_API_KEY"] = "fake_key_per_testare_fallback"
    os.environ["OPENROUTER_API_KEY"] = "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"

    print("🧪 TEST FALLBACK FORZATO")
    print("=" * 40)
    print("🎯 Gemini: API FAKE (deve fallire)")
    print("🎯 OpenRouter: API REALE (deve funzionare)")
    print("=" * 40)

    saver = TokenSaver()

    test_cases = [
        ("Ciao!", "GREETING", "Verifica saluto"),
        ("Che tecnologie usate?", "TECHNOLOGY_INQUIRY", "Verifica masking"),
        ("Come funzioni?", "HELP", "Verifica spiegazione")
    ]

    for question, expected_type, description in test_cases:
        print(f"\n❓ '{question}' ({description})")
        print("-" * 50)

        result = await saver.smart_response(question)

        provider = result.get('provider', 'unknown')
        actual_type = result.get('type', 'unknown')
        response = result.get('response', '')

        print(f"   🏢 Provider: {provider}")
        print(f"   🎯 Tipo: {actual_type} (atteso: {expected_type})")
        print(f"   ⏱️  Tempo: {result.get('processing_time', 0):.0f}ms")

        # Verifica masking solo per technology
        if expected_type == "TECHNOLOGY_INQUIRY":
            forbidden = ["n8n", "crewai", "postgresql", "docker"]
            violations = [w for w in forbidden if w.lower() in response.lower()]
            masking_ok = len(violations) == 0
            print(f"   🔒 Masking: {'✅ OK' if masking_ok else '❌ VIOLATO'}")
            if violations:
                print(f"   🚨 Violazioni: {violations}")

        print(f"   💬 Risposta: {response[:150]}...")

        # Verifica che sia stato usato il fallback
        success = provider == "openrouter"
        print(f"   🔄 Fallback OK: {'✅' if success else '❌'}")

    print("\n" + "=" * 40)
    print("📊 STATISTICHE FALLBACK")
    print("=" * 40)

    stats = saver.get_stats()
    print(f"🔄 Provider Stats:")
    print(f"   Gemini requests: {saver.bypass_stats['gemini_requests']}")
    print(f"   OpenRouter fallbacks: {saver.bypass_stats['openrouter_fallbacks']}")
    print(f"   Both failed: {saver.bypass_stats['both_providers_failed']}")

    # Verdetto
    fallback_working = saver.bypass_stats['openrouter_fallbacks'] > 0
    print(f"\n🏆 VERDETTO: {'✅ FALLBACK FUNZIONA!' if fallback_working else '❌ FALLBACK NON FUNZIONA!'}")

if __name__ == "__main__":
    asyncio.run(test_fallback_forced())