#!/usr/bin/env python3
"""
TEST SEMPLICE MONITORING
========================
Test veloce del monitoring con chiamate API reali
"""

import requests
import time
from datetime import datetime

# Color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
RESET = '\033[0m'

print(f"{BOLD}🔬 TEST MONITORING VELOCE{RESET}")
print(f"Timestamp: {datetime.now().isoformat()}\n")

# Test queries
queries = [
    "Ciao!",
    "Come stai?",
    "Mostra utenti attivi",
    "Analizza performance",
    "Status sistema"
]

print(f"{YELLOW}Generando {len(queries)} chiamate API...{RESET}\n")

for query in queries:
    try:
        start = time.time()
        response = requests.post(
            "http://localhost:8000/api/chat",
            json={"message": query, "user_id": "test-monitoring"},
            timeout=10
        )
        elapsed = time.time() - start

        if response.status_code == 200:
            data = response.json()
            metadata = data.get("metadata", {})
            agent = metadata.get("primary_agent", "unknown")
            cost = metadata.get("cost", 0)

            print(f"  {GREEN}✓{RESET} '{query[:20]}...' → {agent} ({elapsed:.2f}s, ${cost:.6f})")
        else:
            print(f"  ✗ '{query[:20]}...' → Error {response.status_code}")

        time.sleep(0.5)  # Small delay

    except Exception as e:
        print(f"  ✗ '{query[:20]}...' → {e}")

print(f"\n{YELLOW}Verificando metriche...{RESET}")

# Check metrics
try:
    response = requests.get("http://localhost:8000/metrics")
    metrics = response.text

    # Count specific metrics
    api_calls = metrics.count("pilotpros_api_requests_total")
    agent_calls = metrics.count("pilotpros_agent_requests_total")

    print(f"  API calls tracked: {api_calls}")
    print(f"  Agent calls tracked: {agent_calls}")

    if "pilotpros_router_savings_dollars" in metrics:
        print(f"  {GREEN}✓{RESET} Cost savings metrics active")

    if "pilotpros_system_health" in metrics:
        print(f"  {GREEN}✓{RESET} System health metrics active")

except Exception as e:
    print(f"  Error checking metrics: {e}")

print(f"\n{GREEN}{BOLD}✅ TEST COMPLETATO{RESET}")
print("\nProssimi passi:")
print("1. Verifica metriche: curl http://localhost:8000/metrics | grep pilotpros_")
print("2. Importa dashboard Grafana: monitoring/grafana-dashboard.json")
print("3. Configura Prometheus scraping")