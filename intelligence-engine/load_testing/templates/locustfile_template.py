#!/usr/bin/env python3
"""
🎯 TEMPLATE: Generic Multi-Agent LLM Load Testing
================================================

Template riutilizzabile per load testing di qualsiasi sistema multi-agent LLM.
Adatta questo file per nuovi progetti modificando le sezioni marcate con # TODO.

Basato su: PilotProOS Intelligence Engine Load Testing Framework v1.0.0
Documentazione: LOAD_TESTING_FRAMEWORK.md

Usage:
    1. Copia questo file come locustfile_[project].py
    2. Modifica le sezioni TODO con i tuoi endpoint
    3. Aggiorna le query e scenari per il tuo dominio
    4. Configura le metriche custom per il tuo caso d'uso
"""

from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from prometheus_client import Counter, Histogram, Gauge

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO: UPDATE THESE METRICS FOR YOUR PROJECT
# Prometheus metrics per il tuo progetto
project_requests = Counter(
    'your_project_requests_total',  # TODO: Change to your project name
    'Total HTTP requests during load test',
    ['method', 'endpoint', 'status']
)

project_response_times = Histogram(
    'your_project_response_time_seconds',  # TODO: Change to your project name
    'Response time distribution during load test',
    ['endpoint']
)

project_concurrent_users = Gauge(
    'your_project_concurrent_users',  # TODO: Change to your project name
    'Number of concurrent users during test'
)

project_system_health = Gauge(
    'your_project_target_system_health',  # TODO: Change to your project name
    'Target system health score during load test'
)

class GenericMultiAgentLoadTester(FastHttpUser):
    """
    Template per load testing multi-agent LLM systems

    Modifica questa classe per il tuo progetto specifico:
    1. Cambia host con il tuo endpoint
    2. Aggiorna test_* methods con i tuoi API endpoints
    3. Modifica realistic_queries con query del tuo dominio
    4. Aggiorna business masking rules se necessario
    """

    # TODO: UPDATE TARGET SYSTEM
    wait_time = between(1, 3)  # Realistic user behavior
    host = "http://localhost:8000"  # TODO: Change to your system URL

    def on_start(self):
        """
        Setup iniziale per ogni user - ADATTA AL TUO SISTEMA
        """
        logger.info(f"🚀 Starting load test user against {self.host}")

        # TODO: UPDATE HEALTH CHECK ENDPOINT
        response = self.client.get("/health", catch_response=True)  # TODO: Your health endpoint
        if response.status_code != 200:
            logger.error(f"❌ Sistema non operativo: {response.status_code}")
            response.failure("Sistema non operativo")
        else:
            # TODO: UPDATE HEALTH CHECK VALIDATION
            try:
                health_data = response.json()
                logger.info(f"✅ Sistema health check OK: {health_data.get('status', 'unknown')}")
            except:
                logger.info("✅ Health endpoint responding")

        # Initialize session data per utente
        self.session_id = f"load_test_session_{random.randint(1000, 9999)}"
        self.user_queries = self._get_realistic_queries()

    def _get_realistic_queries(self) -> List[str]:
        """
        TODO: AGGIORNA CON QUERY REALISTICHE PER IL TUO DOMINIO

        Esempi per domini diversi:
        - E-commerce: ["Cerca prodotti", "Aggiungi al carrello", "Checkout"]
        - Finance: ["Saldo conto", "Trasferimento", "Storico transazioni"]
        - Healthcare: ["Prenotazione visita", "Risultati esami", "Cartella clinica"]
        - Education: ["Corsi disponibili", "Iscrizione corso", "Progressi studente"]
        """
        return [
            # TODO: Replace with domain-specific queries
            "Hello, how are you?",
            "What is the system status?",
            "Are there any issues today?",
            "Show me the latest updates",
            "How is performance?",
            "Any errors to report?",
            "Check database connection",
            "System health overview",
            "Active users report",
            "Performance metrics summary"
        ]

    @task(10)  # Weight: 40% delle richieste
    def test_health_endpoint(self):
        """
        Test endpoint /health - critico per monitoring
        TODO: Aggiorna endpoint se necessario
        """
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    # TODO: Update health validation logic for your system
                    if data.get("status") == "healthy":
                        project_requests.labels(method='GET', endpoint='/health', status='success').inc()
                        project_response_times.labels(endpoint='/health').observe(response.elapsed.total_seconds())
                    else:
                        response.failure(f"Unhealthy status: {data.get('status')}")
                        project_requests.labels(method='GET', endpoint='/health', status='unhealthy').inc()
                except:
                    # Health endpoint might not return JSON
                    project_requests.labels(method='GET', endpoint='/health', status='success').inc()
                    project_response_times.labels(endpoint='/health').observe(response.elapsed.total_seconds())
            else:
                response.failure(f"Health check failed: {response.status_code}")
                project_requests.labels(method='GET', endpoint='/health', status='error').inc()

    @task(8)  # Weight: 32% delle richieste
    def test_metrics_endpoint(self):
        """
        Test endpoint /metrics Prometheus (se disponibile)
        TODO: Rimuovi se il tuo sistema non ha Prometheus
        """
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code == 200:
                content = response.text
                # TODO: Update metrics validation for your project
                if "your_project_" in content:  # TODO: Change to your project prefix
                    project_requests.labels(method='GET', endpoint='/metrics', status='success').inc()
                    project_response_times.labels(endpoint='/metrics').observe(response.elapsed.total_seconds())
                else:
                    project_requests.labels(method='GET', endpoint='/metrics', status='success').inc()
                    project_response_times.labels(endpoint='/metrics').observe(response.elapsed.total_seconds())
            else:
                response.failure(f"Metrics failed: {response.status_code}")
                project_requests.labels(method='GET', endpoint='/metrics', status='error').inc()

    @task(5)  # Weight: 20% delle richieste
    def test_main_api_endpoint(self):
        """
        TODO: SOSTITUISCI CON IL TUO ENDPOINT PRINCIPALE

        Questo è l'endpoint più importante del tuo sistema.
        Per PilotProOS era /api/chat, per il tuo progetto potrebbe essere:
        - E-commerce: /api/products/search
        - Finance: /api/account/balance
        - Healthcare: /api/appointments
        - CRM: /api/contacts/search
        """
        query = random.choice(self.user_queries)

        # TODO: UPDATE REQUEST PAYLOAD FOR YOUR API
        payload = {
            "message": query,  # TODO: Change field names for your API
            "session_id": self.session_id,
            "user_level": "BUSINESS"  # TODO: Remove if not applicable
        }

        # TODO: UPDATE ENDPOINT URL
        with self.client.post("/api/chat", json=payload, catch_response=True) as response:  # TODO: Your main endpoint
            if response.status_code == 200:
                try:
                    data = response.json()

                    # TODO: UPDATE RESPONSE VALIDATION FOR YOUR API
                    if "response" in data and isinstance(data["response"], str):
                        # TODO: UPDATE BUSINESS RULES VALIDATION (if applicable)
                        response_text = data["response"].lower()

                        # Example: Check for technical leaks (adapt to your business rules)
                        forbidden_terms = ["error", "exception", "traceback"]  # TODO: Update for your domain
                        leak_detected = any(term in response_text for term in forbidden_terms)

                        if leak_detected:
                            response.failure(f"Business rule violation detected: {query}")
                            project_requests.labels(method='POST', endpoint='/api/main', status='business_rule_violation').inc()
                        else:
                            # Success - valid response
                            project_requests.labels(method='POST', endpoint='/api/main', status='success').inc()
                            project_response_times.labels(endpoint='/api/main').observe(response.elapsed.total_seconds())
                            logger.info(f"✅ API success: '{query[:30]}...' -> {len(data['response'])} chars")
                    else:
                        response.failure(f"Invalid response structure: {data}")
                        project_requests.labels(method='POST', endpoint='/api/main', status='invalid_structure').inc()

                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
                    project_requests.labels(method='POST', endpoint='/api/main', status='json_error').inc()
            else:
                response.failure(f"Main API failed: {response.status_code}")
                project_requests.labels(method='POST', endpoint='/api/main', status='http_error').inc()

    @task(2)  # Weight: 8% delle richieste
    def test_secondary_endpoint(self):
        """
        TODO: AGGIUNGI UN SECONDO ENDPOINT IMPORTANTE

        Esempi per domini diversi:
        - E-commerce: /api/cart/add
        - Finance: /api/transfer
        - Healthcare: /api/prescriptions
        - CRM: /api/leads/create
        """
        payload = {
            # TODO: Define payload for your secondary endpoint
            "action": f"secondary_test_{random.randint(1, 1000)}",
            "session_id": self.session_id
        }

        # TODO: UPDATE ENDPOINT URL
        with self.client.post("/api/secondary", json=payload, catch_response=True) as response:  # TODO: Your secondary endpoint
            if response.status_code == 200:
                try:
                    data = response.json()
                    # TODO: Add validation logic for your endpoint
                    if "result" in data:
                        project_requests.labels(method='POST', endpoint='/api/secondary', status='success').inc()
                        project_response_times.labels(endpoint='/api/secondary').observe(response.elapsed.total_seconds())
                    else:
                        response.failure("Secondary endpoint missing expected fields")
                        project_requests.labels(method='POST', endpoint='/api/secondary', status='invalid').inc()
                except json.JSONDecodeError:
                    response.failure("Secondary endpoint JSON error")
                    project_requests.labels(method='POST', endpoint='/api/secondary', status='json_error').inc()
            else:
                response.failure(f"Secondary endpoint failed: {response.status_code}")
                project_requests.labels(method='POST', endpoint='/api/secondary', status='error').inc()

class EnterpriseLoadTester(GenericMultiAgentLoadTester):
    """
    Enterprise variant con pattern più aggressivi
    TODO: Adatta per scenari high-load del tuo dominio
    """

    # Tempi più aggressivi per enterprise testing
    wait_time = between(0.5, 2)

    @task(3)
    def test_concurrent_stress(self):
        """
        Test stress con multiple chiamate concorrenti
        TODO: Adatta per il tuo caso d'uso enterprise
        """
        stress_queries = [
            # TODO: Update with domain-specific stress test queries
            "High priority request",
            "Urgent processing needed",
            "Critical system check"
        ]

        for query in stress_queries:
            payload = {
                # TODO: Update payload structure
                "message": query,
                "session_id": f"stress_{self.session_id}_{random.randint(1, 9999)}",
                "priority": "high"  # TODO: Add priority if your system supports it
            }

            # Non blocking request per stress test
            # TODO: Update endpoint
            self.client.post("/api/chat", json=payload, catch_response=False)  # TODO: Your stress test endpoint

# Event listeners per monitoring avanzato (KEEP AS IS - UNIVERSALI)
@events.request.add_listener
def request_handler(request_type, name, response_time, response_length, response, context, exception, start_time, url, **kwargs):
    """Universal request handler for monitoring"""
    if exception:
        logger.error(f"❌ Request failed: {request_type} {name} - {exception}")
    else:
        # Log only slow requests to avoid spam
        if response_time > 2000:  # 2+ seconds
            logger.warning(f"⚠️ Slow request: {request_type} {name} - {response_time:.0f}ms")

@events.spawning_complete.add_listener
def on_spawning_complete(environment, **kwargs):
    """Callback quando tutti gli user sono spawned"""
    user_count = environment.runner.user_count
    logger.info(f"🚀 Load test active with {user_count} concurrent users")
    project_concurrent_users.set(user_count)

@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """Cleanup al termine del test"""
    logger.info("🏁 Load test completed - generating final report")

if __name__ == "__main__":
    """
    Entry point per esecuzione diretta
    TODO: Update project info
    """
    print("🚀 Generic Multi-Agent LLM Load Testing Template")
    print("=" * 50)
    print("Target host:", "http://localhost:8000")  # TODO: Update default
    print("Project:", "YOUR_PROJECT_NAME")  # TODO: Update project name
    print("=" * 50)
    print("✅ Template ready for customization")
    print("📋 See LOAD_TESTING_FRAMEWORK.md for adaptation guide")