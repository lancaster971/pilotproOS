"""
🚀 PilotProOS Enterprise Load Testing Framework
===============================================

RIGOROUS LOAD TESTING per Intelligence Engine
- Target: 1000+ req/min sustained
- P95 Latency < 2000ms
- P99 Latency < 3000ms
- Sistema health score > 80% sotto carico
- Test con DATI REALI (no mock)
- Integrazione Prometheus metrics real-time

Basato su documentazione ufficiale Locust:
https://docs.locust.io/en/stable/

Author: PilotProOS Development Team
Version: 1.0.0 Enterprise
Date: 2025-09-29
"""

from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_printer
from locust.contrib.fasthttp import FastHttpUser
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
import logging
import threading
from prometheus_client import CollectorRegistry, Counter, Histogram, Gauge, push_to_gateway
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics registry
registry = CollectorRegistry()

# Custom Prometheus metrics per load testing
load_test_requests = Counter(
    'locust_requests_total',
    'Total HTTP requests during load test',
    ['method', 'endpoint', 'status'],
    registry=registry
)

load_test_response_times = Histogram(
    'locust_response_time_seconds',
    'Response time distribution during load test',
    ['endpoint'],
    registry=registry
)

load_test_concurrent_users = Gauge(
    'locust_concurrent_users',
    'Number of concurrent users during test',
    registry=registry
)

load_test_system_health = Gauge(
    'locust_target_system_health',
    'Target system health score during load test',
    registry=registry
)

class PilotProOSLoadTester(FastHttpUser):
    """
    Enterprise Load Testing User per Intelligence Engine

    Utilizza FastHttpUser per performance ottimali come da documentazione:
    https://docs.locust.io/en/stable/increase-performance.html
    """

    # Wait time between tasks (realistic user behavior)
    wait_time = between(1, 3)

    # Host target configurabile via environment
    host = os.getenv('LOAD_TEST_HOST', 'http://localhost:8000')

    def on_start(self):
        """
        Setup iniziale per ogni user (chiamato all'inizio del test)
        Segue pattern documentazione ufficiale Locust
        """
        logger.info(f"🚀 Starting load test user against {self.host}")

        # Verifica che il sistema sia operativo
        response = self.client.get("/health", catch_response=True)
        if response.status_code != 200:
            logger.error(f"❌ Sistema non operativo: {response.status_code}")
            response.failure("Sistema non operativo")
        else:
            health_data = response.json()
            logger.info(f"✅ Sistema health check OK: {health_data.get('status', 'unknown')}")

        # Initialize session data per utente
        self.session_id = f"load_test_session_{random.randint(1000, 9999)}"
        self.user_queries = self._get_realistic_queries()

    def _get_realistic_queries(self) -> List[str]:
        """
        Query realistiche per test con dati reali (NO MOCK)
        Basate su casi d'uso business reali PilotProOS
        """
        return [
            "Ciao Milhena, come stai?",
            "Qual è lo stato del sistema oggi?",
            "Ci sono problemi nei processi?",
            "Mostrami l'ultimo messaggio dal workflow Fatture",
            "Quante elaborazioni sono state completate oggi?",
            "Come va la performance del sistema?",
            "Ci sono errori da segnalare?",
            "Stato della connessione database",
            "Controllo salute sistema generale",
            "Rapporto attività utenti attivi"
        ]

    @task(10)  # Weight: 40% delle richieste
    def test_health_endpoint(self):
        """
        Test endpoint /health - critico per monitoring
        Alta frequenza per simulare health checks produzione
        """
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    # Success - track metrics
                    load_test_requests.labels(method='GET', endpoint='/health', status='success').inc()
                    load_test_response_times.labels(endpoint='/health').observe(response.elapsed.total_seconds())
                else:
                    response.failure(f"Unhealthy status: {data.get('status')}")
                    load_test_requests.labels(method='GET', endpoint='/health', status='unhealthy').inc()
            else:
                response.failure(f"Health check failed: {response.status_code}")
                load_test_requests.labels(method='GET', endpoint='/health', status='error').inc()

    @task(8)  # Weight: 32% delle richieste
    def test_metrics_endpoint(self):
        """
        Test endpoint /metrics Prometheus
        Essenziale per monitoring in produzione
        """
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code == 200:
                # Verifica che contenga metriche reali
                content = response.text
                if "pilotpros_" in content and "python_gc_" in content:
                    load_test_requests.labels(method='GET', endpoint='/metrics', status='success').inc()
                    load_test_response_times.labels(endpoint='/metrics').observe(response.elapsed.total_seconds())

                    # Extract system health from metrics if available
                    self._extract_system_health_from_metrics(content)
                else:
                    response.failure("Metrics endpoint not returning expected PilotProOS metrics")
                    load_test_requests.labels(method='GET', endpoint='/metrics', status='invalid').inc()
            else:
                response.failure(f"Metrics failed: {response.status_code}")
                load_test_requests.labels(method='GET', endpoint='/metrics', status='error').inc()

    @task(5)  # Weight: 20% delle richieste
    def test_chat_api_with_real_queries(self):
        """
        Test endpoint /api/chat con query realistiche
        Usa DATI REALI e agenti veri (no mock)
        """
        query = random.choice(self.user_queries)

        payload = {
            "message": query,
            "session_id": self.session_id,
            "user_level": "BUSINESS"  # Test masking level
        }

        with self.client.post("/api/chat", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()

                    # Validate response structure
                    if "response" in data and isinstance(data["response"], str):
                        # Check for technical leaks (critical security test)
                        response_text = data["response"].lower()
                        forbidden_terms = ["n8n", "postgresql", "docker", "langchain", "workflow"]

                        leak_detected = any(term in response_text for term in forbidden_terms)

                        if leak_detected:
                            response.failure(f"SECURITY LEAK detected in response: {query}")
                            load_test_requests.labels(method='POST', endpoint='/api/chat', status='security_leak').inc()
                        else:
                            # Success - valid business response
                            load_test_requests.labels(method='POST', endpoint='/api/chat', status='success').inc()
                            load_test_response_times.labels(endpoint='/api/chat').observe(response.elapsed.total_seconds())

                            # Log successful realistic interaction
                            logger.info(f"✅ Chat success: '{query[:30]}...' -> {len(data['response'])} chars")
                    else:
                        response.failure(f"Invalid response structure: {data}")
                        load_test_requests.labels(method='POST', endpoint='/api/chat', status='invalid_structure').inc()

                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
                    load_test_requests.labels(method='POST', endpoint='/api/chat', status='json_error').inc()
            else:
                response.failure(f"Chat API failed: {response.status_code}")
                load_test_requests.labels(method='POST', endpoint='/api/chat', status='http_error').inc()

    @task(2)  # Weight: 8% delle richieste
    def test_n8n_customer_support_integration(self):
        """
        Test integrazione n8n customer support con agent reale
        Workflow ID reale: dBFVzxfHl4UfaYCa
        """
        payload = {
            "message": f"Test support query {random.randint(1, 1000)}",
            "session_id": f"n8n_test_{self.session_id}"
        }

        with self.client.post("/api/n8n/agent/customer-support", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "response" in data:
                        load_test_requests.labels(method='POST', endpoint='/api/n8n/agent', status='success').inc()
                        load_test_response_times.labels(endpoint='/api/n8n/agent').observe(response.elapsed.total_seconds())
                    else:
                        response.failure("N8N endpoint missing response field")
                        load_test_requests.labels(method='POST', endpoint='/api/n8n/agent', status='invalid').inc()
                except json.JSONDecodeError:
                    response.failure("N8N endpoint JSON error")
                    load_test_requests.labels(method='POST', endpoint='/api/n8n/agent', status='json_error').inc()
            else:
                response.failure(f"N8N integration failed: {response.status_code}")
                load_test_requests.labels(method='POST', endpoint='/api/n8n/agent', status='error').inc()

    def _extract_system_health_from_metrics(self, metrics_content: str):
        """
        Estrae system health score dalle metriche Prometheus
        """
        try:
            for line in metrics_content.split('\n'):
                if line.startswith('pilotpros_system_health '):
                    health_value = float(line.split(' ')[1])
                    load_test_system_health.set(health_value)
                    break
        except Exception as e:
            logger.warning(f"Could not extract health score: {e}")

class EnterprisePilotProOSUser(PilotProOSLoadTester):
    """
    Enterprise variant con pattern più aggressivi
    Per test di stress avanzati
    """

    # Tempi più aggressivi per enterprise testing
    wait_time = between(0.5, 2)

    @task(3)
    def test_concurrent_chat_stress(self):
        """
        Test stress con multiple chat concorrenti
        Simula picchi di utilizzo enterprise
        """
        queries = [
            "Stato sistema critico",
            "Report immediato performance",
            "Alert check urgente"
        ]

        for query in queries:
            payload = {
                "message": query,
                "session_id": f"stress_{self.session_id}_{random.randint(1, 9999)}"
            }

            # Non blocking request per stress test
            self.client.post("/api/chat", json=payload, catch_response=False)

# Event listeners per monitoring avanzato seguendo documentazione Locust
@events.request.add_listener
def request_handler(request_type, name, response_time, response_length, response, context, exception, start_time, url, **kwargs):
    """
    Custom request handler per monitoring avanzato
    Segue pattern documentazione: https://docs.locust.io/en/stable/extending-locust.html
    """
    if exception:
        logger.error(f"❌ Request failed: {request_type} {name} - {exception}")
    else:
        # Log only slow requests to avoid spam
        if response_time > 2000:  # 2+ seconds
            logger.warning(f"⚠️ Slow request: {request_type} {name} - {response_time:.0f}ms")

@events.spawning_complete.add_listener
def on_spawning_complete(environment, **kwargs):
    """
    Callback quando tutti gli user sono spawned
    """
    user_count = environment.runner.user_count
    logger.info(f"🚀 Load test active with {user_count} concurrent users")
    load_test_concurrent_users.set(user_count)

@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """
    Cleanup al termine del test
    """
    logger.info("🏁 Load test completed - generating final report")

    # Export final metrics se Prometheus gateway disponibile
    gateway_url = os.getenv('PROMETHEUS_GATEWAY')
    if gateway_url:
        try:
            push_to_gateway(gateway_url, job='pilotpros_load_test', registry=registry)
            logger.info(f"✅ Metrics pushed to Prometheus Gateway: {gateway_url}")
        except Exception as e:
            logger.warning(f"Could not push to Prometheus Gateway: {e}")

# Background monitor per system health seguendo docs Locust
def system_health_monitor(environment):
    """
    Background monitoring del system health durante test
    Pattern da documentazione: https://docs.locust.io/en/stable/extending-locust.html
    """
    while not environment.runner.state in ["stopping", "stopped"]:
        try:
            # Check target system health
            response = requests.get(f"{environment.host}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") != "healthy":
                    logger.warning(f"⚠️ Target system health degraded: {health_data}")

                    # Auto-stop test se sistema critico
                    components = health_data.get("components", {})
                    if not all(status in ["active", "connected", "ready"] for status in components.values()):
                        logger.error("🛑 System critical - stopping load test")
                        environment.runner.quit()
                        break
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Health monitor error: {e}")

        time.sleep(10)  # Check ogni 10 secondi

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """
    Inizializzazione sistema monitoring
    """
    if not isinstance(environment.runner, type(None)):
        # Start background health monitor
        health_thread = threading.Thread(target=system_health_monitor, args=(environment,))
        health_thread.daemon = True
        health_thread.start()
        logger.info("✅ Background health monitor started")

if __name__ == "__main__":
    """
    Entry point per esecuzione diretta
    Configurazione base per quick test
    """
    print("🚀 PilotProOS Enterprise Load Testing Framework")
    print("=" * 50)
    print("Target host:", os.getenv('LOAD_TEST_HOST', 'http://localhost:8000'))
    print("Prometheus Gateway:", os.getenv('PROMETHEUS_GATEWAY', 'Not configured'))
    print("=" * 50)

    # Quick validation run
    try:
        host = os.getenv('LOAD_TEST_HOST', 'http://localhost:8000')
        response = requests.get(f"{host}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Target system is healthy - ready for load testing")
        else:
            print(f"❌ Target system not ready: {response.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to target system: {e}")
        exit(1)