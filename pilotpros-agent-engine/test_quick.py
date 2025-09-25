#!/usr/bin/env python3
"""
Test veloce del sistema Milhena Enterprise
Verifica funzionalità e performance
"""

import asyncio
import time
import json
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.crews.milhena_orchestrator_enterprise import MilhenaEnterpriseOrchestrator


async def test_milhena_system():
    """Test completo del sistema con misurazioni performance"""

    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║         MILHENA ENTERPRISE - TEST DI SISTEMA             ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    # Inizializza orchestrator
    print("🔄 Inizializzazione sistema...")
    start = time.time()

    orchestrator = MilhenaEnterpriseOrchestrator(
        enable_memory=True,
        enable_analytics=True,
        enable_cache=True
    )

    init_time = (time.time() - start) * 1000
    print(f"✅ Sistema inizializzato in {init_time:.0f}ms\n")

    # Test questions
    test_questions = [
        {
            "question": "Ciao! Come stai?",
            "expected_type": "GREETING",
            "user_id": "test_user",
            "test_name": "Test Saluto Italiano"
        },
        {
            "question": "Hello! What can you do?",
            "expected_type": "HELP",
            "user_id": "test_user",
            "test_name": "Test Help Inglese"
        },
        {
            "question": "Quante esecuzioni abbiamo fatto oggi?",
            "expected_type": "BUSINESS_DATA",
            "user_id": "test_user",
            "test_name": "Test Dati Business"
        },
        {
            "question": "Analizza i trend delle performance",
            "expected_type": "ANALYSIS",
            "user_id": "test_user",
            "test_name": "Test Analisi"
        }
    ]

    results = []

    print("🧪 ESECUZIONE TEST:\n")

    for i, test in enumerate(test_questions, 1):
        print(f"📝 Test {i}/{len(test_questions)}: {test['test_name']}")
        print(f"   Domanda: '{test['question'][:50]}...'")

        # Prima esecuzione (no cache)
        start = time.time()
        result1 = await orchestrator.analyze_question_enterprise(
            question=test['question'],
            user_id=test['user_id']
        )
        time1 = (time.time() - start) * 1000

        # Seconda esecuzione (possibile cache hit)
        start = time.time()
        result2 = await orchestrator.analyze_question_enterprise(
            question=test['question'],
            user_id=test['user_id']
        )
        time2 = (time.time() - start) * 1000

        # Analizza risultati
        test_result = {
            "test_name": test['test_name'],
            "success": result1.get('success', False),
            "question_type": result1.get('question_type'),
            "expected_type": test['expected_type'],
            "type_match": result1.get('question_type') == test['expected_type'],
            "language": result1.get('language'),
            "confidence": result1.get('confidence', 0),
            "time_first_ms": time1,
            "time_second_ms": time2,
            "cache_hit": result2.get('cached', False),
            "speedup": time1 / max(time2, 0.1)
        }

        results.append(test_result)

        # Print risultati immediati
        status_icon = "✅" if test_result['success'] else "❌"
        print(f"   {status_icon} Successo: {test_result['success']}")
        print(f"   📊 Tipo: {test_result['question_type']} (atteso: {test_result['expected_type']})")
        print(f"   🌍 Lingua: {test_result['language']}")
        print(f"   🎯 Confidence: {test_result['confidence']:.2f}")
        print(f"   ⏱️ Prima: {time1:.0f}ms | Seconda: {time2:.0f}ms")

        if test_result['cache_hit']:
            print(f"   💾 CACHE HIT! Speedup: {test_result['speedup']:.1f}x")

        if result1.get('response'):
            print(f"   💬 Risposta: '{result1['response'][:100]}...'")

        print()

    # STATISTICHE FINALI
    print("\n" + "="*60)
    print("📊 STATISTICHE FINALI:")
    print("="*60)

    # Success rate
    success_count = sum(1 for r in results if r['success'])
    print(f"\n✅ Success Rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")

    # Type matching
    type_match_count = sum(1 for r in results if r['type_match'])
    print(f"🎯 Type Matching: {type_match_count}/{len(results)} ({type_match_count/len(results)*100:.1f}%)")

    # Performance
    avg_first_time = sum(r['time_first_ms'] for r in results) / len(results)
    avg_second_time = sum(r['time_second_ms'] for r in results) / len(results)
    cache_hits = sum(1 for r in results if r['cache_hit'])

    print(f"\n⚡ PERFORMANCE:")
    print(f"   • Tempo medio prima richiesta: {avg_first_time:.0f}ms")
    print(f"   • Tempo medio seconda richiesta: {avg_second_time:.0f}ms")
    print(f"   • Cache hits: {cache_hits}/{len(results)}")
    print(f"   • Speedup medio con cache: {avg_first_time/max(avg_second_time, 0.1):.1f}x")

    # Language detection
    languages = set(r['language'] for r in results if r.get('language'))
    print(f"\n🌍 Lingue rilevate: {', '.join(languages)}")

    # Confidence
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    print(f"🎯 Confidence media: {avg_confidence:.2f}")

    # System stats
    print(f"\n📈 STATISTICHE SISTEMA:")
    system_stats = orchestrator.get_system_stats()
    print(f"   • Utenti tracciati: {system_stats['users_tracked']}")
    if system_stats.get('analytics'):
        print(f"   • Richieste totali: {system_stats['analytics']['total_requests']}")
        print(f"   • Cache hit rate: {system_stats['cache']['hit_rate']:.1%}")

    # Check persistence
    print(f"\n💾 PERSISTENZA:")
    persistence_dir = Path("milhena_persistence")
    if persistence_dir.exists():
        files = list(persistence_dir.glob("*"))
        print(f"   • Directory esistente: ✅")
        print(f"   • File creati: {len(files)}")
        for file in files[:5]:  # Mostra primi 5 file
            size = file.stat().st_size
            print(f"     - {file.name} ({size} bytes)")
    else:
        print(f"   • Directory non trovata ❌")

    # Risultati per tipo
    print(f"\n📋 RISULTATI PER TIPO:")
    for test_type in ["GREETING", "HELP", "BUSINESS_DATA", "ANALYSIS"]:
        type_results = [r for r in results if r['question_type'] == test_type]
        if type_results:
            avg_time = sum(r['time_first_ms'] for r in type_results) / len(type_results)
            print(f"   • {test_type}: {len(type_results)} test, tempo medio: {avg_time:.0f}ms")

    # VERDETTO FINALE
    print("\n" + "="*60)
    if success_count == len(results):
        print("🎉 TUTTI I TEST PASSATI! Sistema funzionante al 100%!")
    elif success_count >= len(results) * 0.75:
        print("✅ Sistema funzionante bene! Alcuni test minori falliti.")
    elif success_count >= len(results) * 0.5:
        print("⚠️ Sistema parzialmente funzionante. Verificare i problemi.")
    else:
        print("❌ Sistema con problemi critici. Debug necessario.")

    print("="*60)

    # Salva report
    report_file = Path("test_report.json")
    with open(report_file, 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": results,
            "summary": {
                "success_rate": success_count / len(results),
                "type_match_rate": type_match_count / len(results),
                "avg_first_time_ms": avg_first_time,
                "avg_second_time_ms": avg_second_time,
                "cache_hits": cache_hits,
                "avg_confidence": avg_confidence,
                "languages": list(languages)
            }
        }, f, indent=2)

    print(f"\n📄 Report salvato in: {report_file}")

    return success_count == len(results)


async def test_single_question():
    """Test singola domanda interattiva"""
    print("\n🎯 TEST SINGOLA DOMANDA\n")

    orchestrator = MilhenaEnterpriseOrchestrator(
        enable_memory=True,
        enable_analytics=True,
        enable_cache=True
    )

    question = input("Inserisci una domanda di test: ").strip()
    if not question:
        question = "Ciao! Quali sono le performance di oggi?"

    print(f"\n🔄 Elaborazione: '{question}'")
    print("-" * 40)

    start = time.time()
    result = await orchestrator.analyze_question_enterprise(
        question=question,
        user_id="interactive_test"
    )
    elapsed = (time.time() - start) * 1000

    if result['success']:
        print(f"✅ SUCCESSO!")
        print(f"📊 Tipo: {result['question_type']}")
        print(f"🌍 Lingua: {result['language']}")
        print(f"🎯 Confidence: {result['confidence']:.2f}")
        print(f"⏱️ Tempo: {elapsed:.0f}ms")
        print(f"💾 Cache: {'Sì' if result['cached'] else 'No'}")
        print(f"\n💬 Risposta:\n{result['response']}")
    else:
        print(f"❌ ERRORE: {result.get('error')}")
        print(f"💬 Fallback: {result.get('fallback_response')}")

    print("-" * 40)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Milhena Enterprise System")
    parser.add_argument("--full", action="store_true", help="Run full test suite")
    parser.add_argument("--single", action="store_true", help="Test single question")
    args = parser.parse_args()

    if args.single:
        asyncio.run(test_single_question())
    else:
        # Default: full test
        success = asyncio.run(test_milhena_system())
        sys.exit(0 if success else 1)