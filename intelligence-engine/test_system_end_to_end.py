#!/usr/bin/env python3
"""
TEST END-TO-END RIGOROSO DEL SISTEMA MULTI-AGENT
=================================================
Test completo con dati REALI e validazione di tutti i componenti
NO MOCK DATA - SOLO DATI REALI DAL DATABASE
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Configuration
API_BASE = "http://localhost:8000"
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

class EndToEndTester:
    """Comprehensive end-to-end testing with real data validation"""

    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "warnings": [],
            "performance": {}
        }
        self.session = requests.Session()

    def print_header(self, title: str):
        """Print formatted test header"""
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}{Style.BRIGHT}{title}{Style.RESET_ALL}")
        print("=" * 80)

    def print_test(self, name: str):
        """Print test name"""
        print(f"\n{Fore.YELLOW}🧪 TEST: {name}{Style.RESET_ALL}")

    def print_success(self, message: str):
        """Print success message"""
        print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
        self.results["passed"] += 1

    def print_error(self, message: str):
        """Print error message"""
        print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
        self.results["failed"] += 1
        self.results["errors"].append(message)

    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")
        self.results["warnings"].append(message)

    def validate_response(self, response: Dict, required_fields: List[str]) -> bool:
        """Validate response has required fields"""
        for field in required_fields:
            if field not in response:
                self.print_error(f"Missing required field: {field}")
                return False
        return True

    def test_health_check(self) -> bool:
        """Test 1: Health check with all components"""
        self.print_test("Health Check - All Components")

        try:
            response = self.session.get(f"{API_BASE}/health")
            data = response.json()

            # Validate response structure
            required = ["status", "service", "components"]
            if not self.validate_response(data, required):
                return False

            # Check all components
            components = data.get("components", {})
            for component, status in components.items():
                if status in ["connected", "active", "ready"]:
                    self.print_success(f"Component {component}: {status}")
                else:
                    self.print_error(f"Component {component}: {status}")

            return data.get("status") == "healthy"

        except Exception as e:
            self.print_error(f"Health check failed: {e}")
            return False

    def test_agent_registration(self) -> bool:
        """Test 2: Verify all agents are registered"""
        self.print_test("Agent Registration - Real Agents")

        try:
            response = self.session.get(f"{API_BASE}/api/agents/status")
            data = response.json()

            if not data.get("success"):
                self.print_error("Agent status endpoint failed")
                return False

            status = data.get("status", {})
            agents = status.get("agents", {})

            # Verify required agents
            required_agents = ["milhena", "n8n_expert", "data_analyst"]
            for agent_name in required_agents:
                agent_info = agents.get(agent_name, {})
                if agent_info.get("registered"):
                    self.print_success(f"Agent {agent_name}: Registered with {agent_info.get('model', 'unknown')}")
                else:
                    self.print_error(f"Agent {agent_name}: NOT registered")
                    return False

            # Check routing rules
            routing_rules = status.get("routing_rules", 0)
            if routing_rules > 0:
                self.print_success(f"Routing rules configured: {routing_rules}")
            else:
                self.print_warning("No routing rules configured")

            return True

        except Exception as e:
            self.print_error(f"Agent registration test failed: {e}")
            return False

    def test_chat_routing(self) -> bool:
        """Test 3: Test agent routing with different queries"""
        self.print_test("Chat Routing - Real Agent Selection")

        test_cases = [
            {
                "message": "ciao milhena",
                "expected_agent": "milhena",
                "description": "Greeting to Milhena"
            },
            {
                "message": "mostra ultimo messaggio del workflow",
                "expected_agent": "n8n_expert",
                "description": "Workflow query"
            },
            {
                "message": "analizza le performance di oggi",
                "expected_agent": "data_analyst",
                "description": "Data analysis query"
            }
        ]

        all_passed = True
        for test in test_cases:
            print(f"\n  Testing: {test['description']}")

            try:
                start_time = time.time()
                response = self.session.post(
                    f"{API_BASE}/api/chat",
                    json={
                        "message": test["message"],
                        "user_id": f"test-user-{int(time.time())}"
                    }
                )
                elapsed = time.time() - start_time

                if response.status_code != 200:
                    self.print_error(f"HTTP {response.status_code}: {response.text}")
                    all_passed = False
                    continue

                data = response.json()

                # Check routing
                metadata = data.get("metadata", {})
                routing = metadata.get("routing", {})
                selected_agent = routing.get("agent", "")

                if selected_agent == test["expected_agent"]:
                    self.print_success(f"Correctly routed to {selected_agent} ({elapsed:.2f}s)")
                else:
                    self.print_error(f"Wrong routing: expected {test['expected_agent']}, got {selected_agent}")
                    all_passed = False

                # Check masking
                masking = metadata.get("masking", {})
                if masking.get("leaks_detected", 1) == 0:
                    self.print_success("No technical leaks detected")
                else:
                    self.print_warning(f"Potential leaks: {masking.get('leaks_detected')}")

                # Performance tracking
                self.results["performance"][test["description"]] = {
                    "time": elapsed,
                    "tokens": metadata.get("tokens_used", 0),
                    "cost": metadata.get("cost", 0)
                }

            except Exception as e:
                self.print_error(f"Chat test failed: {e}")
                all_passed = False

        return all_passed

    def test_token_tracking(self) -> bool:
        """Test 4: Verify token usage tracking"""
        self.print_test("Token Usage Tracking")

        try:
            response = self.session.get(f"{API_BASE}/api/tokens/usage?period=24h")
            data = response.json()

            # Validate structure
            required = ["total_tokens", "cost_estimate", "by_agent", "period"]
            if not self.validate_response(data, required):
                return False

            # Check by agent breakdown
            by_agent = data.get("by_agent", {})
            for agent, stats in by_agent.items():
                if "tokens" in stats and "cost" in stats:
                    self.print_success(f"Agent {agent}: {stats['tokens']} tokens, ${stats['cost']:.4f}")
                else:
                    self.print_warning(f"Agent {agent}: incomplete stats")

            # Total cost check
            total_cost = data.get("cost_estimate", 0)
            self.print_success(f"Total estimated cost: ${total_cost:.4f}")

            return True

        except Exception as e:
            self.print_error(f"Token tracking test failed: {e}")
            return False

    def test_capabilities(self) -> bool:
        """Test 5: Verify agent capabilities"""
        self.print_test("Agent Capabilities")

        try:
            response = self.session.get(f"{API_BASE}/api/agents/capabilities")
            data = response.json()

            if not data.get("success"):
                self.print_error("Capabilities endpoint failed")
                return False

            capabilities = data.get("capabilities", {})
            agents = capabilities.get("agents", {})

            # Verify each agent has capabilities
            for agent_name, agent_info in agents.items():
                caps = agent_info.get("capabilities", [])
                if len(caps) > 0:
                    self.print_success(f"Agent {agent_name}: {len(caps)} capabilities")
                    for cap in caps[:2]:  # Show first 2
                        print(f"    - {cap}")
                else:
                    self.print_error(f"Agent {agent_name}: No capabilities defined")
                    return False

            # Check total capabilities
            total = capabilities.get("total_capabilities", 0)
            if total >= 12:  # Expected minimum
                self.print_success(f"Total capabilities: {total}")
            else:
                self.print_warning(f"Low capability count: {total}")

            return True

        except Exception as e:
            self.print_error(f"Capabilities test failed: {e}")
            return False

    def test_prometheus_metrics(self) -> bool:
        """Test 6: Verify Prometheus metrics"""
        self.print_test("Prometheus Metrics")

        try:
            response = self.session.get(f"{API_BASE}/metrics")

            if response.status_code != 200:
                self.print_error(f"Metrics endpoint returned {response.status_code}")
                return False

            content = response.text

            # Check for key metrics
            metrics_to_check = [
                "agents_registered",
                "system_health_score",
                "tokens_used_total",
                "requests_total"
            ]

            found_metrics = 0
            for metric in metrics_to_check:
                if metric in content:
                    self.print_success(f"Metric found: {metric}")
                    found_metrics += 1
                else:
                    self.print_warning(f"Metric missing: {metric}")

            return found_metrics >= 3  # At least 3 of 4 metrics

        except Exception as e:
            self.print_error(f"Prometheus metrics test failed: {e}")
            return False

    def test_error_handling(self) -> bool:
        """Test 7: Test error handling and resilience"""
        self.print_test("Error Handling & Resilience")

        # Test invalid input
        try:
            response = self.session.post(
                f"{API_BASE}/api/chat",
                json={"message": "", "user_id": "test"}
            )

            if response.status_code == 422:
                self.print_success("Empty message correctly rejected")
            else:
                self.print_warning(f"Empty message returned {response.status_code}")

        except Exception as e:
            self.print_error(f"Error handling test failed: {e}")
            return False

        # Test SQL injection attempt
        try:
            response = self.session.post(
                f"{API_BASE}/api/chat",
                json={
                    "message": "'; DROP TABLE users; --",
                    "user_id": "test-injection"
                }
            )

            if response.status_code == 200:
                data = response.json()
                if "DROP TABLE" not in str(data):
                    self.print_success("SQL injection sanitized")
                else:
                    self.print_error("SQL injection not properly sanitized!")
                    return False

        except Exception as e:
            self.print_error(f"Injection test failed: {e}")
            return False

        return True

    def run_all_tests(self):
        """Run all end-to-end tests"""
        self.print_header("🚀 END-TO-END SYSTEM TEST - REAL DATA ONLY")
        print(f"API Base: {API_BASE}")
        print(f"Timestamp: {datetime.now().isoformat()}")

        # Check server is running
        try:
            self.session.get(f"{API_BASE}/health", timeout=5)
            print(f"{Fore.GREEN}✅ Server is running{Style.RESET_ALL}")
        except:
            print(f"{Fore.RED}❌ Server not responding at {API_BASE}{Style.RESET_ALL}")
            print("Please ensure the Intelligence Engine is running")
            return

        # Run all tests
        tests = [
            ("Health Check", self.test_health_check),
            ("Agent Registration", self.test_agent_registration),
            ("Chat Routing", self.test_chat_routing),
            ("Token Tracking", self.test_token_tracking),
            ("Capabilities", self.test_capabilities),
            ("Prometheus Metrics", self.test_prometheus_metrics),
            ("Error Handling", self.test_error_handling)
        ]

        for name, test_func in tests:
            try:
                if not test_func():
                    self.results["warnings"].append(f"{name} had issues")
            except Exception as e:
                self.print_error(f"{name} crashed: {e}")

        # Print summary
        self.print_header("📊 TEST SUMMARY")
        print(f"Passed: {Fore.GREEN}{self.results['passed']}{Style.RESET_ALL}")
        print(f"Failed: {Fore.RED}{self.results['failed']}{Style.RESET_ALL}")

        if self.results["errors"]:
            print(f"\n{Fore.RED}Errors:{Style.RESET_ALL}")
            for error in self.results["errors"][:5]:  # Show first 5
                print(f"  - {error}")

        if self.results["warnings"]:
            print(f"\n{Fore.YELLOW}Warnings:{Style.RESET_ALL}")
            for warning in self.results["warnings"][:5]:
                print(f"  - {warning}")

        # Performance summary
        if self.results["performance"]:
            print(f"\n{Fore.CYAN}Performance:{Style.RESET_ALL}")
            total_cost = 0
            total_tokens = 0
            for test, perf in self.results["performance"].items():
                print(f"  - {test}: {perf['time']:.2f}s, {perf['tokens']} tokens, ${perf['cost']:.6f}")
                total_cost += perf["cost"]
                total_tokens += perf["tokens"]
            print(f"  Total: {total_tokens} tokens, ${total_cost:.6f}")

        # Final verdict
        success_rate = (self.results["passed"] /
                       (self.results["passed"] + self.results["failed"]) * 100
                       if self.results["passed"] + self.results["failed"] > 0 else 0)

        print(f"\n{Fore.CYAN}Success Rate: {success_rate:.1f}%{Style.RESET_ALL}")

        if success_rate >= 80:
            print(f"{Fore.GREEN}🎉 SYSTEM TEST PASSED{Style.RESET_ALL}")
        elif success_rate >= 60:
            print(f"{Fore.YELLOW}⚠️  SYSTEM PARTIALLY WORKING{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ SYSTEM TEST FAILED{Style.RESET_ALL}")

        return success_rate >= 80

if __name__ == "__main__":
    tester = EndToEndTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)