#!/usr/bin/env python3
"""
Test v3.1 Strategy - Flash per cazzate, Pro per dati critici
"""

import asyncio
from gemini_fast_client import GeminiFastClient
from tools.business_intelligent_query_tool import BusinessIntelligentQueryTool

async def test_strategy():
    print("=" * 60)
    print("🧪 TEST STRATEGIA v3.1: Flash vs Pro")
    print("=" * 60)

    client = GeminiFastClient()
    tool = BusinessIntelligentQueryTool()

    # Test queries divise per tipo
    test_cases = [
        # CAZZATE → dovrebbe usare Flash
        ("Ciao!", "Flash (semplice)"),
        ("Come funzioni?", "Flash (help)"),
        ("Buongiorno", "Flash (saluto)"),

        # CRITICHE → dovrebbe usare Pro
        ("Qual è il fatturato?", "Pro (dati business)"),
        ("Chi sono i clienti?", "Pro (dati sensibili)"),
        ("Quanti workflow sono attivi?", "Pro (metriche)"),
        ("Analizza le performance", "Pro (analisi)"),
    ]

    print("\n📊 CLASSIFICAZIONE CON STRATEGIA v3.1:\n")

    for question, expected in test_cases:
        try:
            # Test classificazione
            result = await client.classify_question(question)

            print(f"Q: {question}")
            print(f"   Modello: {result.get('model', 'unknown')}")
            print(f"   Categoria: {result.get('type', 'unknown')}")
            print(f"   Confidence: {result.get('confidence', 0):.0%}")
            print(f"   Latenza: {result.get('latency_ms', 0):.0f}ms")
            print(f"   ✓ Atteso: {expected}")
            print()

            # Piccola pausa per evitare rate limit
            await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Errore: {e}\n")

    print("\n" + "=" * 60)
    print("📊 TEST QUERY TOOL (deve bloccare dati inesistenti):\n")

    # Test che il tool blocchi correttamente
    critical_questions = [
        "Qual è il fatturato di oggi?",
        "Chi sono i nostri clienti?",
        "Quanti ordini abbiamo?",
        "Quanti workflow ci sono?"
    ]

    for q in critical_questions:
        response = tool._run(q)
        print(f"Q: {q}")
        print(f"R: {response[:100]}")

        # Verifica che NON inventi dati
        if any(forbidden in response.lower() for forbidden in ["€", "euro", "clienti serviti"]):
            print("❌ ATTENZIONE: Possibile allucinazione!")
        else:
            print("✅ Risposta sicura")
        print()

if __name__ == "__main__":
    print("""
    🎯 STRATEGIA v3.1:
    - Flash → Solo per saluti e help (veloce ma meno accurato)
    - Pro → Per tutto il resto (lento ma affidabile)

    ⚠️ NOTA: Se vedi errori di quota, è normale.
    Il sistema fa fallback automatico.
    """)

    asyncio.run(test_strategy())