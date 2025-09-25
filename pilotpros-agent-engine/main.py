#!/usr/bin/env python3
"""
Milhena Enterprise - Main Entry Point
Sistema Multi-Agent Intelligente per PilotProOS
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.crews.milhena_orchestrator_enterprise import MilhenaEnterpriseOrchestrator


async def main():
    """Main function to demonstrate Milhena Enterprise usage"""

    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║           MILHENA ENTERPRISE - MULTI-AGENT SYSTEM        ║
    ║                    PilotProOS Intelligence               ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    # Initialize orchestrator
    orchestrator = MilhenaEnterpriseOrchestrator(
        enable_memory=True,
        enable_analytics=True,
        enable_cache=True
    )

    print("🚀 Sistema inizializzato con successo!\n")
    print("Comandi disponibili:")
    print("  - 'stats' : Mostra statistiche")
    print("  - 'clear' : Pulisci cache")
    print("  - 'exit'  : Esci\n")

    user_id = input("👤 Il tuo nome/ID (default: guest): ").strip() or "guest"
    print(f"\n✅ Benvenuto {user_id}! Sono Milhena, la tua assistente business.\n")

    while True:
        try:
            # Get user input
            question = input("❓ Tu: ").strip()

            if not question:
                continue

            # Handle special commands
            if question.lower() == 'exit':
                print("\n👋 Arrivederci! A presto!")
                break

            elif question.lower() == 'stats':
                stats = orchestrator.get_system_stats()
                print("\n📊 STATISTICHE SISTEMA:")
                print(f"  • Utenti tracciati: {stats['users_tracked']}")
                if stats['analytics']:
                    print(f"  • Richieste totali: {stats['analytics']['total_requests']}")
                    print(f"  • Cache hit rate: {stats['cache']['hit_rate']:.1%}")
                    print(f"  • Lingue usate: {stats['analytics'].get('languages_detected', {})}")
                print()
                continue

            elif question.lower() == 'clear':
                if orchestrator.cache:
                    orchestrator.cache.clear_expired()
                    print("✅ Cache pulita!\n")
                continue

            # Process question
            print("\n💭 Sto elaborando la tua richiesta...")

            result = await orchestrator.analyze_question_enterprise(
                question=question,
                user_id=user_id
            )

            if result['success']:
                print(f"\n🤖 Milhena: {result['response']}")
                print(f"\n📈 [{result['question_type']} | {result['language']} | "
                      f"{result['response_time_ms']:.0f}ms | "
                      f"{'📦 cached' if result['cached'] else '🔄 fresh'}]\n")
            else:
                print(f"\n❌ Errore: {result.get('error', 'Sconosciuto')}")
                print(f"🤖 Milhena: {result.get('fallback_response', 'Mi dispiace, riprova.')}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Interrotto. Arrivederci!")
            break
        except Exception as e:
            print(f"\n❌ Errore imprevisto: {e}\n")

    # Save final stats
    print("\n💾 Salvataggio statistiche finali...")
    if orchestrator.analytics:
        final_stats = orchestrator.get_system_stats()
        print(f"✅ Sessione completata: {final_stats['analytics']['total_requests']} richieste processate")


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())