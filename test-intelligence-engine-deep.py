#!/usr/bin/env python3
"""
🧪 DEEP TEST: Intelligence Engine - Comprehensive Testing Suite
Test completo e approfondito del motore Intelligence Engine

Usage:
    python3 test-intelligence-engine-deep.py
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class IntelligenceEngineDeepTest:
    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "total_time": 0
        }
        self.test_details = []

    def print_header(self, text: str):
        """Print test section header"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}{text.center(70)}{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")

    def print_test(self, name: str, status: str, detail: str = "", time_ms: int = 0):
        """Print individual test result"""
        if status == "PASS":
            icon = f"{GREEN}✅{RESET}"
            self.results["passed"] += 1
        elif status == "FAIL":
            icon = f"{RED}❌{RESET}"
            self.results["failed"] += 1
        else:
            icon = f"{YELLOW}⚠️{RESET}"
            self.results["warnings"] += 1

        time_str = f"({time_ms}ms)" if time_ms > 0 else ""
        print(f"{icon} {name:.<50} {status} {time_str}")
        if detail:
            print(f"   {detail}")

        self.test_details.append({
            "name": name,
            "status": status,
            "detail": detail,
            "time_ms": time_ms
        })

    def test_health_check(self) -> bool:
        """Test 1: Health Check Endpoint"""
        self.print_header("TEST 1: HEALTH CHECK")

        try:
            start = time.time()
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            elapsed = int((time.time() - start) * 1000)

            if response.status_code != 200:
                self.print_test("Health endpoint reachable", "FAIL",
                              f"Status code: {response.status_code}", elapsed)
                return False

            data = response.json()
            self.print_test("Health endpoint reachable", "PASS", "", elapsed)

            # Check status
            if data.get("status") == "healthy":
                self.print_test("Service status", "PASS", "Status: healthy")
            else:
                self.print_test("Service status", "FAIL", f"Status: {data.get('status')}")

            # Check components
            components = data.get("components", {})
            for component, status in components.items():
                if status in ["active", "connected", "ready"]:
                    self.print_test(f"Component: {component}", "PASS", f"Status: {status}")
                else:
                    self.print_test(f"Component: {component}", "FAIL", f"Status: {status}")

            return True

        except Exception as e:
            self.print_test("Health endpoint reachable", "FAIL", str(e))
            return False

    def test_stats_endpoint(self) -> bool:
        """Test 2: Statistics Endpoint"""
        self.print_header("TEST 2: STATISTICS & CONFIGURATION")

        try:
            start = time.time()
            response = requests.get(f"{BASE_URL}/api/stats", timeout=5)
            elapsed = int((time.time() - start) * 1000)

            if response.status_code != 200:
                self.print_test("Stats endpoint", "FAIL",
                              f"Status code: {response.status_code}", elapsed)
                return False

            data = response.json()
            self.print_test("Stats endpoint", "PASS", "", elapsed)

            # Check framework
            framework = data.get("framework", "")
            if "langchain" in framework.lower():
                self.print_test("Framework", "PASS", f"Framework: {framework}")
            else:
                self.print_test("Framework", "WARN", f"Unexpected framework: {framework}")

            # Check models
            models = data.get("models_available", [])
            self.print_test("Available models", "PASS" if len(models) > 0 else "WARN",
                          f"Models: {', '.join(models)}")

            # Check tools
            tools = data.get("tools_available", [])
            expected_tools = ["business_data", "workflows", "metrics"]
            has_tools = any(tool in str(tools) for tool in expected_tools)
            self.print_test("Available tools", "PASS" if has_tools else "WARN",
                          f"Tools: {', '.join(tools)}")

            return True

        except Exception as e:
            self.print_test("Stats endpoint", "FAIL", str(e))
            return False

    def test_agent_simple_query(self) -> bool:
        """Test 3: Agent Simple Query"""
        self.print_header("TEST 3: AGENT SIMPLE QUERY")

        try:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/n8n/agent/customer-support",
                json={"message": "Hello, are you working?", "session_id": "test-simple"},
                headers={"Content-Type": "application/json"},
                timeout=TIMEOUT
            )
            elapsed = int((time.time() - start) * 1000)

            if response.status_code != 200:
                self.print_test("Simple query execution", "FAIL",
                              f"Status code: {response.status_code}", elapsed)
                return False

            data = response.json()
            self.print_test("Simple query execution", "PASS", "", elapsed)

            # Check success
            if data.get("success"):
                self.print_test("Query success status", "PASS")
            else:
                self.print_test("Query success status", "FAIL",
                              f"Error: {data.get('error', 'Unknown')}")
                return False

            # Check response
            response_text = data.get("agent_response", "")
            if len(response_text) > 0:
                self.print_test("Response generated", "PASS",
                              f"Response length: {len(response_text)} chars")
            else:
                self.print_test("Response generated", "FAIL", "Empty response")

            # Check response time
            response_time = data.get("response_time", 0)
            if response_time < 5:
                self.print_test("Response time", "PASS", f"{response_time:.2f}s")
            elif response_time < 10:
                self.print_test("Response time", "WARN", f"{response_time:.2f}s (slow)")
            else:
                self.print_test("Response time", "FAIL", f"{response_time:.2f}s (too slow)")

            return True

        except Exception as e:
            self.print_test("Simple query execution", "FAIL", str(e))
            return False

    def test_agent_database_query(self) -> bool:
        """Test 4: Agent Database Query"""
        self.print_header("TEST 4: AGENT DATABASE INTEGRATION")

        try:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/n8n/agent/customer-support",
                json={
                    "message": "How many users are in the system?",
                    "session_id": "test-database"
                },
                headers={"Content-Type": "application/json"},
                timeout=TIMEOUT
            )
            elapsed = int((time.time() - start) * 1000)

            if response.status_code != 200:
                self.print_test("Database query execution", "FAIL",
                              f"Status code: {response.status_code}", elapsed)
                return False

            data = response.json()
            self.print_test("Database query execution", "PASS", "", elapsed)

            # Check success
            if not data.get("success"):
                self.print_test("Database query success", "FAIL",
                              f"Error: {data.get('error', 'Unknown')}")
                return False

            # Check if database was used
            db_used = data.get("database_used", False)
            if db_used:
                self.print_test("Database tools used", "PASS")
            else:
                self.print_test("Database tools used", "WARN",
                              "Agent didn't use database tools")

            # Check response contains numbers (user count)
            response_text = data.get("agent_response", "")
            has_numbers = any(char.isdigit() for char in response_text)
            if has_numbers:
                self.print_test("Response contains data", "PASS",
                              f"Response includes numeric data")
            else:
                self.print_test("Response contains data", "WARN",
                              "No numeric data in response")

            return True

        except Exception as e:
            self.print_test("Database query execution", "FAIL", str(e))
            return False

    def test_agent_session_memory(self) -> bool:
        """Test 5: Agent Session Memory"""
        self.print_header("TEST 5: SESSION MEMORY")

        session_id = f"test-memory-{int(time.time())}"

        try:
            # First message
            start = time.time()
            response1 = requests.post(
                f"{BASE_URL}/api/n8n/agent/customer-support",
                json={
                    "message": "My name is TestUser",
                    "session_id": session_id
                },
                headers={"Content-Type": "application/json"},
                timeout=TIMEOUT
            )
            elapsed1 = int((time.time() - start) * 1000)

            if response1.status_code != 200:
                self.print_test("First message", "FAIL",
                              f"Status code: {response1.status_code}", elapsed1)
                return False

            self.print_test("First message", "PASS", "", elapsed1)

            # Wait a moment
            time.sleep(1)

            # Second message asking for name
            start = time.time()
            response2 = requests.post(
                f"{BASE_URL}/api/n8n/agent/customer-support",
                json={
                    "message": "What is my name?",
                    "session_id": session_id
                },
                headers={"Content-Type": "application/json"},
                timeout=TIMEOUT
            )
            elapsed2 = int((time.time() - start) * 1000)

            if response2.status_code != 200:
                self.print_test("Second message", "FAIL",
                              f"Status code: {response2.status_code}", elapsed2)
                return False

            data2 = response2.json()
            self.print_test("Second message", "PASS", "", elapsed2)

            # Check if agent remembers the name
            response_text = data2.get("agent_response", "").lower()
            if "testuser" in response_text or "test user" in response_text:
                self.print_test("Memory retention", "PASS",
                              "Agent remembered the name")
            else:
                self.print_test("Memory retention", "WARN",
                              "Agent may not have remembered the name")

            return True

        except Exception as e:
            self.print_test("Session memory test", "FAIL", str(e))
            return False

    def test_agent_complex_query(self) -> bool:
        """Test 6: Agent Complex Query with Multiple Tools"""
        self.print_header("TEST 6: COMPLEX MULTI-TOOL QUERY")

        try:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/n8n/agent/customer-support",
                json={
                    "message": "Can you check the system status and tell me about active sessions?",
                    "session_id": "test-complex"
                },
                headers={"Content-Type": "application/json"},
                timeout=TIMEOUT
            )
            elapsed = int((time.time() - start) * 1000)

            if response.status_code != 200:
                self.print_test("Complex query execution", "FAIL",
                              f"Status code: {response.status_code}", elapsed)
                return False

            data = response.json()
            self.print_test("Complex query execution", "PASS", "", elapsed)

            # Check success
            if not data.get("success"):
                self.print_test("Complex query success", "FAIL",
                              f"Error: {data.get('error', 'Unknown')}")
                return False

            self.print_test("Complex query success", "PASS")

            # Check if database was used
            if data.get("database_used"):
                self.print_test("Database integration", "PASS")
            else:
                self.print_test("Database integration", "WARN")

            # Check response quality
            response_text = data.get("agent_response", "")
            if len(response_text) > 50:
                self.print_test("Response completeness", "PASS",
                              f"{len(response_text)} characters")
            else:
                self.print_test("Response completeness", "WARN",
                              "Short response")

            return True

        except Exception as e:
            self.print_test("Complex query execution", "FAIL", str(e))
            return False

    def test_error_handling(self) -> bool:
        """Test 7: Error Handling"""
        self.print_header("TEST 7: ERROR HANDLING & RESILIENCE")

        # Test empty message
        try:
            response = requests.post(
                f"{BASE_URL}/api/n8n/agent/customer-support",
                json={"message": "", "session_id": "test-error"},
                headers={"Content-Type": "application/json"},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success") or len(data.get("agent_response", "")) > 0:
                    self.print_test("Empty message handling", "PASS",
                                  "Handled gracefully")
                else:
                    self.print_test("Empty message handling", "WARN")
            else:
                self.print_test("Empty message handling", "PASS",
                              "Rejected appropriately")
        except Exception as e:
            self.print_test("Empty message handling", "WARN", str(e))

        # Test missing fields
        try:
            response = requests.post(
                f"{BASE_URL}/api/n8n/agent/customer-support",
                json={},
                headers={"Content-Type": "application/json"},
                timeout=5
            )

            if response.status_code in [400, 422]:
                self.print_test("Missing fields validation", "PASS",
                              "Validation working")
            else:
                self.print_test("Missing fields validation", "WARN",
                              f"Status: {response.status_code}")
        except Exception as e:
            self.print_test("Missing fields validation", "WARN", str(e))

        # Test invalid endpoint
        try:
            response = requests.get(
                f"{BASE_URL}/api/invalid-endpoint",
                timeout=5
            )

            if response.status_code == 404:
                self.print_test("404 handling", "PASS")
            else:
                self.print_test("404 handling", "WARN",
                              f"Status: {response.status_code}")
        except Exception as e:
            self.print_test("404 handling", "WARN", str(e))

        return True

    def test_concurrent_requests(self) -> bool:
        """Test 8: Concurrent Requests"""
        self.print_header("TEST 8: CONCURRENT REQUEST HANDLING")

        import concurrent.futures

        def make_request(i):
            try:
                response = requests.post(
                    f"{BASE_URL}/api/n8n/agent/customer-support",
                    json={
                        "message": f"Test concurrent request {i}",
                        "session_id": f"test-concurrent-{i}"
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=TIMEOUT
                )
                return response.status_code == 200
            except:
                return False

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                start = time.time()
                futures = [executor.submit(make_request, i) for i in range(5)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
                elapsed = int((time.time() - start) * 1000)

            successful = sum(results)
            self.print_test("Concurrent requests (5)",
                          "PASS" if successful >= 4 else "WARN",
                          f"{successful}/5 successful", elapsed)

            return successful >= 3

        except Exception as e:
            self.print_test("Concurrent requests", "FAIL", str(e))
            return False

    def print_summary(self):
        """Print final summary"""
        self.print_header("TEST SUMMARY")

        total = self.results["passed"] + self.results["failed"] + self.results["warnings"]
        passed_pct = (self.results["passed"] / total * 100) if total > 0 else 0

        print(f"{GREEN}✅ PASSED:{RESET}    {self.results['passed']}/{total}")
        print(f"{RED}❌ FAILED:{RESET}    {self.results['failed']}/{total}")
        print(f"{YELLOW}⚠️  WARNINGS:{RESET} {self.results['warnings']}/{total}")
        print(f"\n{BLUE}Overall Success Rate:{RESET} {passed_pct:.1f}%")

        if self.results["failed"] == 0:
            print(f"\n{GREEN}{'🎉 ALL TESTS PASSED! 🎉'.center(70)}{RESET}")
            return 0
        elif self.results["failed"] < 3:
            print(f"\n{YELLOW}{'⚠️  SOME ISSUES DETECTED'.center(70)}{RESET}")
            return 1
        else:
            print(f"\n{RED}{'❌ CRITICAL ISSUES DETECTED'.center(70)}{RESET}")
            return 2

    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}{'INTELLIGENCE ENGINE - DEEP TEST SUITE'.center(70)}{RESET}")
        print(f"{BLUE}{'='*70}{RESET}")
        print(f"\nBase URL: {BASE_URL}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        start_time = time.time()

        # Run all tests
        self.test_health_check()
        self.test_stats_endpoint()
        self.test_agent_simple_query()
        self.test_agent_database_query()
        self.test_agent_session_memory()
        self.test_agent_complex_query()
        self.test_error_handling()
        self.test_concurrent_requests()

        self.results["total_time"] = int((time.time() - start_time) * 1000)

        # Print summary
        print(f"\n{BLUE}Total execution time:{RESET} {self.results['total_time']/1000:.2f}s")

        return self.print_summary()


if __name__ == "__main__":
    tester = IntelligenceEngineDeepTest()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)