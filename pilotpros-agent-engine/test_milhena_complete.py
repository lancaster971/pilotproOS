#!/usr/bin/env python3
"""
Test COMPLETO Milhena Enterprise - Tutte le funzionalità
"""

import asyncio
import os
import time
import json
from datetime import datetime

# Set GROQ API key
os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY', 'your_groq_api_key_here')

from agents.crews.milhena_orchestrator_enterprise import MilhenaEnterpriseOrchestrator

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_section(title, color=Colors.HEADER):
    print(f"\n{color}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{color}{Colors.BOLD}{title}{Colors.ENDC}")
    print(f"{color}{'='*60}{Colors.ENDC}")

def print_result(question, result, elapsed):
    # Determina icona e colore
    cached = result.get("cached", False)
    fast_path = result.get("fast_path", False)
    success = result.get("success", False)

    if cached:
        icon = "⚡⚡⚡"
        color = Colors.CYAN
        method = "CACHE HIT"
    elif fast_path:
        icon = "⚡"
        color = Colors.GREEN
        method = "FAST PATH"
    else:
        icon = "🔧"
        color = Colors.YELLOW
        method = "CREW FLOW"

    # Mostra risultato
    print(f"\n{Colors.BOLD}❓ {question}{Colors.ENDC}")
    print(f"   {icon} {color}{method}{Colors.ENDC} - {elapsed*1000:.0f}ms")
    print(f"   📁 Tipo: {result.get('question_type', 'UNKNOWN')}")

    if success:
        response = result.get('response', '')
        if len(response) > 200:
            response = response[:200] + "..."
        print(f"   ✅ {response}")
    else:
        error = result.get('error', 'Unknown error')
        print(f"   ❌ {Colors.RED}Errore: {error}{Colors.ENDC}")

    return elapsed

async def test_milhena_complete():
    """Test completo di Milhena Enterprise"""

    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("╭─────────────────────────────────────────╮")
    print("│  🤖 MILHENA ENTERPRISE - TEST COMPLETO  │")
    print("│     Multi-Agent AI System Testing       │")
    print("╰─────────────────────────────────────────╯")
    print(Colors.ENDC)

    # Initialize
    print(f"{Colors.YELLOW}Inizializzazione Milhena Orchestrator...{Colors.ENDC}")
    orchestrator = MilhenaEnterpriseOrchestrator(
        enable_cache=True,
        fast_mode=True
    )
    print(f"{Colors.GREEN}✅ Orchestrator inizializzato{Colors.ENDC}")

    # Test cases organizzati per categoria
    test_categories = {
        "GREETING (Saluti)": [
            "Ciao!",
            "Buongiorno",
            "Hello",
            "Hey there!"
        ],
        "HELP (Aiuto)": [
            "Come funzioni?",
            "Cosa puoi fare?",
            "Help me understand your capabilities",
            "Quali sono le tue funzionalità?"
        ],
        "GENERAL (Domande Generali)": [
            "Cos'è PilotProOS?",
            "Spiegami l'automazione dei processi",
            "What is business process automation?",
            "Come posso ottimizzare i workflow?"
        ],
        "BUSINESS_DATA (Dati Business)": [
            "Quante esecuzioni abbiamo fatto oggi?",
            "Mostrami le statistiche dei processi",
            "Qual è il tasso di successo delle automazioni?",
            "Quanti workflow sono attivi?",
            "Analizza le performance dell'ultima settimana"
        ],
        "CACHE TEST (Test Cache)": [
            "Ciao!",  # Dovrebbe essere in cache
            "Come funzioni?",  # Dovrebbe essere in cache
            "Quante esecuzioni abbiamo fatto oggi?"  # Potrebbe essere in cache
        ]
    }

    # Statistiche
    stats = {
        "total_requests": 0,
        "cache_hits": 0,
        "fast_path_hits": 0,
        "crew_flows": 0,
        "errors": 0,
        "total_time": 0,
        "category_times": {},
        "response_times": []
    }

    # Test per categoria
    for category, questions in test_categories.items():
        print_section(f"📋 {category}", Colors.BLUE)

        category_time = 0
        for question in questions:
            stats["total_requests"] += 1

            try:
                start = time.time()
                result = await orchestrator.analyze_question_enterprise(
                    question=question,
                    user_id="test_user_complete"
                )
                elapsed = time.time() - start

                # Mostra risultato
                print_result(question, result, elapsed)

                # Aggiorna statistiche
                stats["total_time"] += elapsed
                category_time += elapsed
                stats["response_times"].append(elapsed)

                if result.get("cached"):
                    stats["cache_hits"] += 1
                elif result.get("fast_path"):
                    stats["fast_path_hits"] += 1
                else:
                    stats["crew_flows"] += 1

                if not result.get("success"):
                    stats["errors"] += 1

            except Exception as e:
                print(f"   ❌ {Colors.RED}Errore critico: {str(e)}{Colors.ENDC}")
                stats["errors"] += 1

            # Piccola pausa tra richieste
            await asyncio.sleep(0.1)

        stats["category_times"][category] = category_time

    # SEZIONE PERFORMANCE
    print_section("🚀 ANALISI PERFORMANCE", Colors.GREEN)

    avg_time = stats["total_time"] / stats["total_requests"] if stats["total_requests"] > 0 else 0
    cache_rate = (stats["cache_hits"] / stats["total_requests"] * 100) if stats["total_requests"] > 0 else 0

    print(f"📊 Richieste totali: {stats['total_requests']}")
    print(f"⏱️  Tempo totale: {stats['total_time']:.2f}s")
    print(f"⚡ Tempo medio risposta: {avg_time*1000:.0f}ms")
    print(f"")
    print(f"💾 Cache hits: {stats['cache_hits']} ({cache_rate:.1f}%)")
    print(f"⚡ Fast path: {stats['fast_path_hits']} ({stats['fast_path_hits']/stats['total_requests']*100:.1f}%)")
    print(f"🔧 Crew flows: {stats['crew_flows']} ({stats['crew_flows']/stats['total_requests']*100:.1f}%)")

    if stats["errors"] > 0:
        print(f"❌ Errori: {stats['errors']} ({stats['errors']/stats['total_requests']*100:.1f}%)")

    # Tempi per categoria
    print(f"\n📈 Tempi medi per categoria:")
    for category, cat_time in stats["category_times"].items():
        cat_requests = len(test_categories[category])
        avg_cat_time = cat_time / cat_requests if cat_requests > 0 else 0
        print(f"   • {category}: {avg_cat_time*1000:.0f}ms")

    # Response time distribution
    if stats["response_times"]:
        sorted_times = sorted(stats["response_times"])
        p50 = sorted_times[len(sorted_times)//2]
        p95 = sorted_times[int(len(sorted_times)*0.95)] if len(sorted_times) > 20 else sorted_times[-1]
        p99 = sorted_times[int(len(sorted_times)*0.99)] if len(sorted_times) > 100 else sorted_times[-1]

        print(f"\n📊 Distribuzione tempi di risposta:")
        print(f"   • P50 (mediana): {p50*1000:.0f}ms")
        print(f"   • P95: {p95*1000:.0f}ms")
        print(f"   • P99: {p99*1000:.0f}ms")
        print(f"   • Min: {min(sorted_times)*1000:.0f}ms")
        print(f"   • Max: {max(sorted_times)*1000:.0f}ms")

    # SEZIONE SISTEMA
    print_section("💻 STATO SISTEMA", Colors.CYAN)

    system_stats = orchestrator.get_system_stats()
    print(f"👥 Utenti tracciati: {system_stats.get('users_tracked', 0)}")

    if system_stats.get('analytics'):
        analytics = system_stats['analytics']
        print(f"📈 Richieste totali sistema: {analytics.get('total_requests', 0)}")
        print(f"📊 Distribuzione per tipo:")
        for q_type, count in analytics.get('by_type', {}).items():
            print(f"   • {q_type}: {count}")

    if system_stats.get('memory'):
        memory = system_stats['memory']
        print(f"\n🧠 Memoria:")
        print(f"   • Conversazioni salvate: {memory.get('total_conversations', 0)}")
        print(f"   • Interazioni totali: {memory.get('total_interactions', 0)}")

    # CONCLUSIONI
    print_section("✨ CONCLUSIONI", Colors.GREEN)

    if avg_time < 2:
        print(f"{Colors.GREEN}✅ Performance ECCELLENTE - Tempo medio < 2 secondi{Colors.ENDC}")
    elif avg_time < 5:
        print(f"{Colors.YELLOW}⚡ Performance BUONA - Tempo medio < 5 secondi{Colors.ENDC}")
    else:
        print(f"{Colors.RED}⚠️ Performance DA OTTIMIZZARE - Tempo medio > 5 secondi{Colors.ENDC}")

    if cache_rate > 30:
        print(f"{Colors.GREEN}✅ Cache efficace - Hit rate {cache_rate:.1f}%{Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}📈 Cache può migliorare - Hit rate {cache_rate:.1f}%{Colors.ENDC}")

    if stats["errors"] == 0:
        print(f"{Colors.GREEN}✅ Sistema stabile - Nessun errore rilevato{Colors.ENDC}")
    else:
        print(f"{Colors.RED}⚠️ Rilevati {stats['errors']} errori - Verifica i log{Colors.ENDC}")

    print(f"\n{Colors.BOLD}🎯 Test completato con successo!{Colors.ENDC}")
    print(f"{Colors.CYAN}Sistema Milhena Enterprise operativo e ottimizzato{Colors.ENDC}")

if __name__ == "__main__":
    asyncio.run(test_milhena_complete())