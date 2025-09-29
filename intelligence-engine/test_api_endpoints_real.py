#!/usr/bin/env python3
"""
TEST RIGOROSO degli API Endpoints con DATI REALI
Verifica che tutte le nuove API funzionino correttamente
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Configurazione
API_BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Colori per output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_test_header(test_name: str):
    """Stampa header del test"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}🧪 TEST: {test_name}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")

def print_result(success: bool, message: str):
    """Stampa risultato del test"""
    if success:
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
    else:
        print(f"{Colors.RED}❌ {message}{Colors.END}")

async def test_health_endpoint():
    """Test endpoint /health"""
    print_test_header("Health Check")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/health") as response:
                data = await response.json()

                print(f"Status Code: {response.status}")
                print(f"Response: {json.dumps(data, indent=2)}")

                # Verifica campi richiesti
                required_fields = ["status", "service", "version", "components"]
                for field in required_fields:
                    if field in data:
                        print_result(True, f"Campo '{field}' presente")
                    else:
                        print_result(False, f"Campo '{field}' mancante")

                return response.status == 200
        except Exception as e:
            print_result(False, f"Errore: {e}")
            return False

async def test_agents_status():
    """Test endpoint /api/agents/status"""
    print_test_header("Agents Status")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/api/agents/status") as response:
                data = await response.json()

                print(f"Status Code: {response.status}")

                if data.get("success"):
                    status = data.get("status", {})

                    # Mostra agenti registrati
                    print("\n📊 Agenti Registrati:")
                    agents = status.get("agents", {})
                    for agent_name, agent_info in agents.items():
                        print(f"  - {agent_name}:")
                        print(f"    Descrizione: {agent_info.get('description')}")
                        print(f"    Modello: {agent_info.get('model')}")
                        print(f"    Registrato: {agent_info.get('registered')}")

                    # Mostra sistemi core
                    print("\n🔧 Sistemi Core:")
                    core = status.get("core_systems", {})
                    for system, active in core.items():
                        status_icon = "✅" if active else "❌"
                        print(f"  {status_icon} {system}: {'Attivo' if active else 'Non inizializzato'}")

                    # Health score
                    health = status.get("health_score", "0%")
                    print(f"\n💚 Health Score: {health}")

                    print_result(True, "Status degli agenti recuperato con successo")
                    return True
                else:
                    print_result(False, f"Errore: {data.get('error')}")
                    return False

        except Exception as e:
            print_result(False, f"Errore: {e}")
            return False

async def test_agents_capabilities():
    """Test endpoint /api/agents/capabilities"""
    print_test_header("Agents Capabilities")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/api/agents/capabilities") as response:
                data = await response.json()

                print(f"Status Code: {response.status}")

                if data.get("success"):
                    capabilities = data.get("capabilities", {})

                    print(f"\n🤖 Totale Agenti: {capabilities.get('total_agents')}")
                    print(f"🎯 Totale Capacità: {capabilities.get('total_capabilities')}")

                    print("\n📋 Dettagli Agenti:")
                    for agent_name, info in capabilities.get("agents", {}).items():
                        print(f"\n  {agent_name.upper()}:")
                        print(f"    Descrizione: {info.get('description')}")
                        print(f"    Modello: {info.get('model')}")
                        print(f"    Costo: {info.get('cost_range')}")
                        print(f"    Capacità:")
                        for cap in info.get("capabilities", []):
                            print(f"      - {cap}")

                    print("\n💰 Costi Stimati (per 1000 query):")
                    costs = capabilities.get("estimated_costs", {}).get("per_1000_queries", {})
                    for service, cost in costs.items():
                        print(f"  {service}: {cost}")

                    print_result(True, "Capacità degli agenti recuperate con successo")
                    return True
                else:
                    print_result(False, f"Errore: {data.get('error')}")
                    return False

        except Exception as e:
            print_result(False, f"Errore: {e}")
            return False

async def test_token_usage():
    """Test endpoint /api/tokens/usage"""
    print_test_header("Token Usage")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/api/tokens/usage?period=24h") as response:
                data = await response.json()

                print(f"Status Code: {response.status}")

                print(f"\n📊 Uso Token (periodo: {data.get('period')}):")
                print(f"  Token totali: {data.get('total_tokens')}")
                print(f"  Token prompt: {data.get('prompt_tokens')}")
                print(f"  Token completamento: {data.get('completion_tokens')}")
                print(f"  Costo stimato: ${data.get('cost_estimate'):.3f}")

                print("\n🤖 Per Agente:")
                for agent, usage in data.get("by_agent", {}).items():
                    print(f"  {agent}:")
                    print(f"    Token: {usage.get('tokens')}")
                    print(f"    Richieste: {usage.get('requests')}")
                    print(f"    Costo: ${usage.get('cost'):.3f}")

                print("\n📝 Per Sessione:")
                session_stats = data.get("by_session", {})
                print(f"  Sessioni attive: {session_stats.get('active')}")
                print(f"  Sessioni completate: {session_stats.get('completed')}")
                print(f"  Token medi: {session_stats.get('average_tokens')}")

                print_result(True, "Statistiche token recuperate con successo")
                return response.status == 200

        except Exception as e:
            print_result(False, f"Errore: {e}")
            return False

async def test_prometheus_metrics():
    """Test endpoint /metrics (Prometheus)"""
    print_test_header("Prometheus Metrics")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/metrics") as response:
                text = await response.text()

                print(f"Status Code: {response.status}")
                print("\n📈 Metriche Prometheus:")

                # Mostra prime righe delle metriche
                lines = text.split('\n')[:20]
                for line in lines:
                    print(f"  {line}")

                print(f"\n  ... ({len(text.split(chr(10)))} righe totali)")

                # Verifica formato Prometheus
                has_help = "# HELP" in text
                has_type = "# TYPE" in text
                has_metrics = "gauge" in text or "counter" in text or "histogram" in text

                print_result(has_help, "Contiene dichiarazioni HELP")
                print_result(has_type, "Contiene dichiarazioni TYPE")
                print_result(has_metrics, "Contiene metriche valide")

                return response.status == 200 and has_metrics

        except Exception as e:
            print_result(False, f"Errore: {e}")
            return False

async def test_chat_endpoint():
    """Test endpoint /api/chat con query REALI"""
    print_test_header("Chat Endpoint con Multi-Agent Routing")

    test_queries = [
        {
            "message": "Ciao, come stai oggi?",
            "expected_agent": "milhena",
            "description": "Saluto generale"
        },
        {
            "message": "Mostrami i workflow attivi nel sistema",
            "expected_agent": "n8n_expert",
            "description": "Query n8n"
        },
        {
            "message": "Analizza le performance dell'ultimo mese",
            "expected_agent": "data_analyst",
            "description": "Analisi dati"
        }
    ]

    async with aiohttp.ClientSession() as session:
        success_count = 0

        for i, test in enumerate(test_queries, 1):
            print(f"\n{i}. {test['description']}:")
            print(f"   Query: '{test['message']}'")

            payload = {
                "message": test["message"],
                "user_id": f"test-user-{i}",
                "context": {"user_level": "business"}
            }

            try:
                async with session.post(
                    f"{API_BASE_URL}/api/chat",
                    json=payload,
                    headers=HEADERS
                ) as response:
                    data = await response.json()

                    if data.get("status") == "success":
                        print(f"   ✅ Risposta ricevuta")
                        print(f"   Response: {data.get('response')[:100]}...")

                        metadata = data.get("metadata", {})
                        if "routing" in metadata:
                            agent = metadata["routing"].get("agent")
                            print(f"   Agente: {agent}")
                            if agent == test["expected_agent"]:
                                print_result(True, "Routing corretto")
                            else:
                                print_result(False, f"Routing errato (atteso: {test['expected_agent']})")

                        success_count += 1
                    else:
                        print_result(False, f"Errore: {data.get('metadata', {}).get('error')}")

            except Exception as e:
                print_result(False, f"Errore: {e}")

        print(f"\n📊 Risultati: {success_count}/{len(test_queries)} query completate")
        return success_count > 0

async def test_agent_routing():
    """Test endpoint /api/agents/route"""
    print_test_header("Agent Routing Test")

    test_queries = [
        "Quali sono i messaggi nel workflow?",
        "Genera un report delle vendite",
        "Ciao, mi serve aiuto"
    ]

    async with aiohttp.ClientSession() as session:
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")

            payload = {"message": query}

            try:
                async with session.post(
                    f"{API_BASE_URL}/api/agents/route",
                    json=payload,
                    headers=HEADERS
                ) as response:
                    data = await response.json()

                    print(f"  Agente probabile: {data.get('likely_agent')}")

                    hints = data.get("routing_hints", [])
                    if hints:
                        print("  Suggerimenti routing:")
                        for hint in hints:
                            print(f"    - {hint['agent']}: {hint['reason']}")

                    print(f"  Catena fallback: {' -> '.join(data.get('fallback_chain', []))}")

            except Exception as e:
                print_result(False, f"Errore: {e}")

async def run_all_api_tests():
    """Esegui TUTTI i test API con dati REALI"""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}🚀 TEST COMPLETO API ENDPOINTS CON DATI REALI{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"📅 Test avviato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API Base URL: {API_BASE_URL}")

    # Verifica API key
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key and openai_key not in ["test-key", "test"]:
        print(f"{Colors.GREEN}✅ OpenAI API Key configurata{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠️ OpenAI API Key non trovata o non valida{Colors.END}")

    # Test da eseguire
    tests = [
        ("Health Check", test_health_endpoint),
        ("Agents Status", test_agents_status),
        ("Agents Capabilities", test_agents_capabilities),
        ("Token Usage", test_token_usage),
        ("Prometheus Metrics", test_prometheus_metrics),
        ("Chat Endpoint", test_chat_endpoint),
        ("Agent Routing", test_agent_routing)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n{Colors.RED}❌ Test {test_name} fallito con errore: {e}{Colors.END}")
            results.append((test_name, False))

    # Riepilogo
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}📋 RIEPILOGO TEST API{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")

    all_passed = True
    for test_name, passed in results:
        status = f"{Colors.GREEN}✅ PASSATO{Colors.END}" if passed else f"{Colors.RED}❌ FALLITO{Colors.END}"
        print(f"{test_name:25} {status}")
        if not passed:
            all_passed = False

    print(f"{Colors.BOLD}{'='*80}{Colors.END}")

    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 TUTTI I TEST API SONO PASSATI!{Colors.END}")
        print(f"{Colors.GREEN}✅ Le API con multi-agent routing sono PRONTE per PRODUZIONE!{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠️ Alcuni test sono falliti. Verificare la configurazione.{Colors.END}")

    return all_passed

if __name__ == "__main__":
    # Verifica se il server è in esecuzione
    import requests
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        print(f"{Colors.GREEN}✅ Server Intelligence Engine è in esecuzione{Colors.END}")
    except:
        print(f"{Colors.RED}❌ ERRORE: Server non raggiungibile su {API_BASE_URL}{Colors.END}")
        print(f"{Colors.YELLOW}Avviare il server con: cd intelligence-engine && uvicorn app.main:app --reload{Colors.END}")
        sys.exit(1)

    # Esegui test
    success = asyncio.run(run_all_api_tests())
    sys.exit(0 if success else 1)