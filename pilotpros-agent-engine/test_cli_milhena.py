#!/usr/bin/env python3
"""
Test CLI Milhena - Non-interactive test
"""

import asyncio
import os
import time

# Set GROQ API key
os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY', 'your_groq_api_key_here')

from agents.crews.milhena_orchestrator_enterprise import MilhenaEnterpriseOrchestrator

async def test_cli_milhena():
    """Test Milhena from CLI"""

    print("🤖 MILHENA ENTERPRISE - CLI TEST")
    print("="*50)

    # Initialize
    orchestrator = MilhenaEnterpriseOrchestrator(
        enable_cache=True,
        fast_mode=True
    )

    # Test questions
    test_questions = [
        "Ciao!",
        "Come funzioni?",
        "Quante esecuzioni abbiamo fatto oggi?",
        "Ciao!"  # Cache test
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n❓ Domanda {i}: '{question}'")

        start = time.time()
        result = await orchestrator.analyze_question_enterprise(
            question=question,
            user_id="cli_test_user"
        )
        elapsed = time.time() - start

        if result.get("success"):
            # Performance info
            cached = result.get("cached", False)
            fast_path = result.get("fast_path", False)

            if cached:
                icon = "⚡⚡⚡ CACHE HIT"
            elif fast_path:
                icon = "⚡ FAST PATH"
            else:
                icon = "🔧 CREW FLOW"

            print(f"{icon} - {elapsed*1000:.0f}ms")
            print(f"Tipo: {result.get('question_type')}")
            print(f"\n🤖 Milhena: {result['response'][:150]}...")
        else:
            print(f"❌ Errore: {result.get('error')}")

    # Stats
    print(f"\n{'='*50}")
    stats = orchestrator.get_system_stats()
    print(f"📊 STATISTICHE:")
    print(f"  • Utenti: {stats['users_tracked']}")
    if stats.get('analytics'):
        print(f"  • Richieste: {stats['analytics']['total_requests']}")
        print(f"  • Cache hit rate: {stats['cache']['hit_rate']:.1%}")

if __name__ == "__main__":
    asyncio.run(test_cli_milhena())