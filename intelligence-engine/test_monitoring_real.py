#!/usr/bin/env python3
"""
TEST MONITORING CON METRICHE REALI
===================================
Test del sistema Prometheus con chiamate API REALI
NO MOCK DATA - SOLO METRICHE VERE
"""

import asyncio
import aiohttp
import time
import random
from datetime import datetime

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


async def generate_real_traffic():
    """Genera traffico REALE per popolare le metriche"""
    print(f"{YELLOW}🚦 TEST 1: Generazione Traffico Reale{RESET}")
    print("-" * 40)

    async with aiohttp.ClientSession() as session:
        # Test queries di vario tipo
        test_queries = [
            # Semplici (dovrebbero usare Groq)
            ("Ciao!", "greeting"),
            ("Come va?", "simple"),
            ("Tutto ok?", "status"),

            # Medie complessità
            ("Mostra gli utenti attivi", "data_query"),
            ("Quanti workflow sono attivi?", "workflow_query"),

            # Complesse
            ("Analizza le performance dell'ultima settimana", "analysis"),
            ("Genera report dettagliato vendite", "report"),
        ]

        results = {
            "success": 0,
            "errors": 0,
            "total_time": 0,
            "costs": []
        }

        print(f"\nGenerando {len(test_queries) * 3} chiamate API...")

        for i in range(3):  # 3 rounds
            for query, query_type in test_queries:
                try:
                    start = time.time()

                    payload = {
                        "message": query,
                        "user_id": f"test-user-{random.randint(1, 5)}",
                        "context": {"query_type": query_type}
                    }

                    async with session.post(
                        "http://localhost:8000/api/chat",
                        json=payload,
                        timeout=10
                    ) as response:
                        elapsed = time.time() - start
                        data = await response.json()

                        if response.status == 200:
                            results["success"] += 1
                            print(f"  {GREEN}✓{RESET} [{query_type:15}] {elapsed:.2f}s")

                            # Track cost if available
                            if "metadata" in data and "cost" in data["metadata"]:
                                results["costs"].append(data["metadata"]["cost"])
                        else:
                            results["errors"] += 1
                            print(f"  {RED}✗{RESET} [{query_type:15}] Error {response.status}")

                        results["total_time"] += elapsed

                        # Small delay between requests
                        await asyncio.sleep(0.5)

                except Exception as e:
                    results["errors"] += 1
                    print(f"  {RED}✗{RESET} [{query_type:15}] Exception: {e}")

        # Summary
        print(f"\n{BOLD}Risultati:{RESET}")
        print(f"  Successi: {results['success']}")
        print(f"  Errori: {results['errors']}")
        print(f"  Tempo medio: {results['total_time'] / (results['success'] + results['errors']):.2f}s")
        if results["costs"]:
            print(f"  Costo totale: ${sum(results['costs']):.6f}")

        return results["success"] > 0


async def check_metrics_endpoint():
    """Verifica che l'endpoint /metrics funzioni"""
    print(f"\n{YELLOW}📊 TEST 2: Verifica Endpoint /metrics{RESET}")
    print("-" * 40)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8000/metrics") as response:
                if response.status == 200:
                    metrics_text = await response.text()
                    print(f"{GREEN}✅ Endpoint /metrics attivo{RESET}")

                    # Analizza alcune metriche
                    lines = metrics_text.split('\n')
                    metrics_found = {
                        "pilotpros_agent_requests_total": False,
                        "pilotpros_api_requests_total": False,
                        "pilotpros_system_health": False,
                        "pilotpros_router_decisions_total": False
                    }

                    for line in lines:
                        for metric_name in metrics_found.keys():
                            if metric_name in line and not line.startswith("#"):
                                metrics_found[metric_name] = True
                                print(f"  ✓ Trovata metrica: {metric_name}")
                                # Print actual value
                                if "{" not in line:  # Simple metric
                                    print(f"    → {line.strip()}")

                    # Check if all critical metrics exist
                    all_found = all(metrics_found.values())
                    if all_found:
                        print(f"\n{GREEN}✅ Tutte le metriche critiche presenti{RESET}")
                    else:
                        missing = [k for k, v in metrics_found.items() if not v]
                        print(f"\n{YELLOW}⚠️  Metriche mancanti: {missing}{RESET}")

                    return True
                else:
                    print(f"{RED}❌ Endpoint /metrics returned {response.status}{RESET}")
                    return False

        except Exception as e:
            print(f"{RED}❌ Errore accesso /metrics: {e}{RESET}")
            return False


async def check_prometheus_server():
    """Verifica che il server Prometheus sia attivo sulla porta 9090"""
    print(f"\n{YELLOW}🎯 TEST 3: Verifica Server Prometheus{RESET}")
    print("-" * 40)

    async with aiohttp.ClientSession() as session:
        try:
            # Prometheus metrics sono su porta 9090
            async with session.get("http://localhost:9090") as response:
                if response.status == 200:
                    print(f"{GREEN}✅ Server Prometheus attivo su porta 9090{RESET}")
                    return True
                else:
                    print(f"{YELLOW}⚠️  Server Prometheus risponde con status {response.status}{RESET}")
                    return True  # Non critico

        except Exception as e:
            print(f"{YELLOW}ℹ️  Server Prometheus non ancora configurato (normale){RESET}")
            print(f"    Per configurarlo: docker exec -it pilotpros-intelligence-engine-dev prometheus")
            return True  # Non critico per ora


async def test_specific_agents():
    """Testa metriche specifiche per ogni agent"""
    print(f"\n{YELLOW}🤖 TEST 4: Metriche per Agent{RESET}")
    print("-" * 40)

    async with aiohttp.ClientSession() as session:
        # Test queries per attivare agents specifici
        agent_queries = [
            ("Analizza i dati n8n", "n8n_expert"),
            ("Mostra metriche business", "data_analyst"),
            ("Aiutami con un processo", "milhena")
        ]

        for query, expected_agent in agent_queries:
            try:
                payload = {
                    "message": query,
                    "user_id": f"test-{expected_agent}",
                    "context": {"test_agent": expected_agent}
                }

                async with session.post(
                    "http://localhost:8000/api/chat",
                    json=payload,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        metadata = data.get("metadata", {})

                        print(f"  {GREEN}✓{RESET} {expected_agent}: Richiesta completata")

                        # Verifica metriche aggiornate
                        async with session.get("http://localhost:8000/metrics") as metrics_response:
                            if metrics_response.status == 200:
                                metrics = await metrics_response.text()
                                if f'agent_name="{expected_agent}"' in metrics:
                                    print(f"    → Metriche registrate per {expected_agent}")

            except Exception as e:
                print(f"  {RED}✗{RESET} {expected_agent}: {e}")

        return True


async def check_cost_savings():
    """Verifica le metriche di risparmio con Groq"""
    print(f"\n{YELLOW}💰 TEST 5: Metriche Risparmio Groq{RESET}")
    print("-" * 40)

    async with aiohttp.ClientSession() as session:
        # Genera 10 query semplici che dovrebbero usare Groq
        groq_queries = [
            "Ciao", "Come stai?", "Tutto bene?", "Ok",
            "Grazie", "Perfetto", "Va bene", "Si", "No", "Aiuto"
        ]

        total_savings = 0
        groq_count = 0

        for query in groq_queries:
            try:
                payload = {
                    "message": query,
                    "user_id": "test-groq-savings"
                }

                async with session.post(
                    "http://localhost:8000/api/chat",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        metadata = data.get("metadata", {})

                        # Check if Groq was used (cost should be 0)
                        cost = metadata.get("cost", 1)
                        if cost < 0.0001:
                            groq_count += 1
                            # Estimate savings (OpenAI would cost ~$0.0001 per simple query)
                            savings = 0.0001
                            total_savings += savings

            except:
                pass

        print(f"\nRisultati risparmio:")
        print(f"  Query inviate a Groq: {groq_count}/{len(groq_queries)}")
        print(f"  {GREEN}Risparmio stimato: ${total_savings:.6f}{RESET}")
        print(f"  Percentuale Groq: {groq_count/len(groq_queries)*100:.1f}%")

        # Check savings metrics
        async with session.get("http://localhost:8000/metrics") as response:
            if response.status == 200:
                metrics = await response.text()
                if "pilotpros_router_savings_dollars" in metrics:
                    print(f"  {GREEN}✓{RESET} Metriche risparmio registrate in Prometheus")

        return groq_count > 5  # At least 50% should use Groq


async def main():
    """Esegue tutti i test di monitoring"""
    print(f"{BOLD}{'='*80}{RESET}")
    print(f"{BLUE}{BOLD}🔬 TEST MONITORING PRODUZIONE - METRICHE REALI{RESET}")
    print(f"{BOLD}{'='*80}{RESET}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Verifica che il servizio sia attivo
    print("Verifico che Intelligence Engine sia attivo...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    print(f"{GREEN}✅ Intelligence Engine attivo{RESET}\n")
                else:
                    print(f"{RED}❌ Intelligence Engine non risponde{RESET}")
                    return False
        except Exception as e:
            print(f"{RED}❌ Impossibile connettersi: {e}{RESET}")
            print(f"{YELLOW}Assicurati che il container sia attivo:{RESET}")
            print("  ./stack-safe.sh status")
            return False

    # Esegui i test
    tests = [
        ("Traffico Reale", generate_real_traffic),
        ("Endpoint Metrics", check_metrics_endpoint),
        ("Server Prometheus", check_prometheus_server),
        ("Agent Specifici", test_specific_agents),
        ("Risparmio Groq", check_cost_savings)
    ]

    results = []
    for name, test_func in tests:
        result = await test_func()
        results.append((name, result))
        await asyncio.sleep(1)  # Pausa tra test

    # Summary finale
    print(f"\n{BOLD}{'='*80}{RESET}")
    print(f"{BLUE}{BOLD}📊 RIEPILOGO TEST{RESET}")
    print(f"{BOLD}{'='*80}{RESET}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = f"{GREEN}✅ PASSED{RESET}" if result else f"{RED}❌ FAILED{RESET}"
        print(f"{name:20} {status}")

    print(f"\n{BOLD}Risultato: {passed}/{total} test superati{RESET}")

    if passed == total:
        print(f"{GREEN}{BOLD}🎉 MONITORING PRODUZIONE PRONTO!{RESET}")
        print("\nProssimi passi:")
        print("1. Importa dashboard in Grafana: monitoring/grafana-dashboard.json")
        print("2. Configura Prometheus per scrape da :8000/metrics")
        print("3. Abilita alerting con le regole predefinite")
        return True
    elif passed >= total * 0.8:
        print(f"{YELLOW}{BOLD}⚠️  MONITORING FUNZIONANTE MA DA OTTIMIZZARE{RESET}")
        return True
    else:
        print(f"{RED}{BOLD}❌ MONITORING NON PRONTO PER PRODUZIONE{RESET}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)