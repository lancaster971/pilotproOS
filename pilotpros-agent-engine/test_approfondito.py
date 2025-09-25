#!/usr/bin/env python3
"""
TEST APPROFONDITO SISTEMA IBRIDO GEMINI + OPENROUTER
Verifica qualità, velocità, masking e fallback
"""

import asyncio
import os
import time
from fast_bypass import TokenSaver

# Configura API keys
os.environ["GEMINI_API_KEY"] = "AIzaSyCtSVdKlTU-UoySn_-qerbIMWmw3kj7x2o"
os.environ["OPENROUTER_API_KEY"] = "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"

async def test_approfondito():
    """Test completo del sistema"""

    print("🧪 TEST APPROFONDITO SISTEMA IBRIDO")
    print("=" * 60)
    print("🎯 OBIETTIVI:")
    print("   ✅ Technology Masking (mai dire n8n, CrewAI, PostgreSQL, Docker)")
    print("   ✅ Qualità risposte business")
    print("   ✅ Velocità di risposta")
    print("   ✅ Classificazione accurata")
    print("   ✅ Fallback funzionante")
    print("=" * 60)

    saver = TokenSaver()

    # TEST 1: TECHNOLOGY MASKING CRITICO
    print("\n🔒 TEST 1: TECHNOLOGY MASKING")
    print("-" * 40)

    tech_questions = [
        "Che tecnologie usate?",
        "Mi parli di n8n?",
        "Usate PostgreSQL come database?",
        "Che strumenti di automazione avete?",
        "Come è fatto il vostro stack tecnologico?",
        "Parlami di CrewAI e degli agenti AI"
    ]

    tech_results = []
    for q in tech_questions:
        print(f"\n❓ '{q}'")
        start = time.time()
        result = await saver.smart_response(q)
        elapsed = (time.time() - start) * 1000

        response = result['response']

        # Verifica masking
        forbidden_words = ["n8n", "crewai", "postgresql", "docker", "opensource"]
        violations = [word for word in forbidden_words if word.lower() in response.lower()]

        masking_ok = len(violations) == 0
        tech_results.append({
            "question": q,
            "response": response[:120] + "..." if len(response) > 120 else response,
            "masking_ok": masking_ok,
            "violations": violations,
            "speed_ms": elapsed,
            "provider": result.get('provider', 'unknown')
        })

        print(f"   🏢 Provider: {result.get('provider', 'unknown')}")
        print(f"   ⏱️  Tempo: {elapsed:.0f}ms")
        print(f"   🔒 Masking: {'✅ OK' if masking_ok else '❌ VIOLATO'}")
        if violations:
            print(f"   🚨 Parole vietate trovate: {violations}")
        print(f"   💬 Risposta: {response[:100]}...")

    # TEST 2: QUALITÀ RISPOSTE BUSINESS
    print("\n\n💼 TEST 2: QUALITÀ RISPOSTE BUSINESS")
    print("-" * 40)

    business_questions = [
        "Ciao! Come stai?",
        "Come funzioni?",
        "Cosa puoi fare per la mia azienda?",
        "Aiutami con i processi business",
        "Spiegami le tue capacità di analytics"
    ]

    business_results = []
    for q in business_questions:
        print(f"\n❓ '{q}'")
        start = time.time()
        result = await saver.smart_response(q)
        elapsed = (time.time() - start) * 1000

        response = result['response']

        # Valuta qualità (lunghezza, contesto, professionalità)
        quality_score = 0
        if len(response) > 50: quality_score += 1  # Risposta sostanziosa
        if "milhena" in response.lower(): quality_score += 1  # Si identifica
        if any(word in response.lower() for word in ["business", "azienda", "processo", "analytics"]): quality_score += 1
        if response.endswith(('.', '!', '?')): quality_score += 1  # Ben formattata

        business_results.append({
            "question": q,
            "response": response,
            "quality_score": quality_score,
            "speed_ms": elapsed,
            "provider": result.get('provider', 'unknown')
        })

        print(f"   🏢 Provider: {result.get('provider', 'unknown')}")
        print(f"   ⏱️  Tempo: {elapsed:.0f}ms")
        print(f"   ⭐ Qualità: {quality_score}/4")
        print(f"   💬 Risposta: {response}")

    # TEST 3: CLASSIFICAZIONE ACCURATA
    print("\n\n🎯 TEST 3: CLASSIFICAZIONE ACCURATA")
    print("-" * 40)

    classification_tests = [
        ("Ciao!", "GREETING"),
        ("Come funzioni?", "HELP"),
        ("Che tecnologie usate?", "TECHNOLOGY_INQUIRY"),
        ("Quanti workflow attivi?", "BUSINESS_DATA"),
        ("Analizza i trend", "ANALYSIS"),
        ("Dimmi qualcosa", "GENERAL")
    ]

    classification_results = []
    for question, expected in classification_tests:
        print(f"\n❓ '{question}' (atteso: {expected})")
        result = await saver.smart_response(question)

        actual = result.get('type', 'UNKNOWN')
        correct = actual == expected

        classification_results.append({
            "question": question,
            "expected": expected,
            "actual": actual,
            "correct": correct,
            "provider": result.get('provider', 'unknown')
        })

        print(f"   🏢 Provider: {result.get('provider', 'unknown')}")
        print(f"   🎯 Classificazione: {actual} {'✅' if correct else '❌'}")

    # STATISTICHE FINALI
    print("\n\n📊 RISULTATI FINALI")
    print("=" * 60)

    # Technology Masking
    masking_success = sum(1 for r in tech_results if r['masking_ok'])
    masking_rate = (masking_success / len(tech_results)) * 100
    print(f"🔒 Technology Masking: {masking_success}/{len(tech_results)} ({masking_rate:.1f}%)")

    # Qualità Business
    avg_quality = sum(r['quality_score'] for r in business_results) / len(business_results)
    print(f"💼 Qualità Media Business: {avg_quality:.1f}/4 ({avg_quality/4*100:.1f}%)")

    # Classificazione
    classification_success = sum(1 for r in classification_results if r['correct'])
    classification_rate = (classification_success / len(classification_results)) * 100
    print(f"🎯 Accuratezza Classificazione: {classification_success}/{len(classification_results)} ({classification_rate:.1f}%)")

    # Velocità
    all_speeds = [r['speed_ms'] for r in tech_results + business_results]
    avg_speed = sum(all_speeds) / len(all_speeds)
    print(f"⏱️  Velocità Media: {avg_speed:.0f}ms")

    # Provider Usage
    all_providers = [r['provider'] for r in tech_results + business_results + classification_results]
    gemini_count = all_providers.count('gemini')
    openrouter_count = all_providers.count('openrouter')
    print(f"🏢 Provider Usage: Gemini {gemini_count}, OpenRouter {openrouter_count}")

    # Token Stats
    stats = saver.get_stats()
    print(f"📈 Token Efficiency: {stats['token_efficiency']}")
    print(f"🔄 Bypass Rate: {stats['bypass_rate']}")

    # VERDETTO FINALE
    print("\n" + "=" * 60)
    print("🏆 VERDETTO FINALE")
    print("-" * 60)

    overall_score = (masking_rate + avg_quality/4*100 + classification_rate) / 3

    if overall_score >= 90:
        verdict = "🥇 ECCELLENTE"
    elif overall_score >= 80:
        verdict = "🥈 MOLTO BUONO"
    elif overall_score >= 70:
        verdict = "🥉 BUONO"
    else:
        verdict = "❌ NEEDS IMPROVEMENT"

    print(f"Score Complessivo: {overall_score:.1f}% - {verdict}")

    if masking_rate < 100:
        print("⚠️  WARNING: Technology masking non perfetto!")
    if avg_speed > 2000:
        print("⚠️  WARNING: Velocità troppo lenta!")
    if classification_rate < 80:
        print("⚠️  WARNING: Classificazione inaccurata!")

    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_approfondito())