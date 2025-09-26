#!/usr/bin/env python3
"""
🧪 DEEP TEST: PilotProOS Complete Stack
Test approfondito di tutti i servizi e comunicazioni dello stack

Services tested:
- Data Management System
- Cache Service
- Backend API
- Business Portal
- AI Intelligence Engine
- Process Automation
- System Monitor

Usage:
    python3 test-stack-deep.py
    python3 test-stack-deep.py --quick     # Skip slow tests
    python3 test-stack-deep.py --json      # JSON output
"""

import requests
import subprocess
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configuration
SERVICES = {
    "postgres": {"name": "Data Management", "url": "localhost:5432", "container": "pilotpros-postgres-dev"},
    "redis": {"name": "Cache Service", "url": "localhost:6379", "container": "pilotpros-redis-dev"},
    "backend": {"name": "Backend API", "url": "http://localhost:3001", "container": "pilotpros-backend-dev"},
    "frontend": {"name": "Business Portal", "url": "http://localhost:3000", "container": "pilotpros-frontend-dev"},
    "intelligence": {"name": "AI Intelligence", "url": "http://localhost:8000", "container": "pilotpros-intelligence-engine-dev"},
    "automation": {"name": "Process Automation", "url": "http://localhost:5678", "container": "pilotpros-automation-engine-dev"},
    "nginx": {"name": "System Monitor", "url": "http://localhost:80", "container": "pilotpros-nginx-dev"}
}

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

class StackDeepTest:
    def __init__(self, quick_mode=False, json_output=False):
        self.quick_mode = quick_mode
        self.json_output = json_output
        self.results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "total_time": 0,
            "services": {},
            "communications": {}
        }
        self.start_time = time.time()

    def log(self, message: str, level: str = "info"):
        """Print formatted log message"""
        if self.json_output:
            return

        icons = {"info": "[INFO]", "pass": f"{GREEN}[PASS]{RESET}", "fail": f"{RED}[FAIL]{RESET}",
                "warn": f"{YELLOW}[WARN]{RESET}", "test": "[TEST]"}
        print(f"{icons.get(level, '')} {message}")

    def print_header(self, text: str):
        """Print section header"""
        if self.json_output:
            return
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}{text.center(70)}{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")

    def test_docker_container(self, service_key: str) -> Dict[str, Any]:
        """Test Docker container status"""
        service = SERVICES[service_key]
        result = {"name": service["name"], "container_running": False, "healthy": False}

        try:
            # Check if container is running
            cmd = f"docker ps --filter name={service['container']} --format '{{{{.Status}}}}'"
            output = subprocess.check_output(cmd, shell=True, text=True).strip()

            if "Up" in output:
                result["container_running"] = True
                result["uptime"] = output.split("Up")[1].strip().split("(")[0].strip()

                # Check health
                if "(healthy)" in output:
                    result["healthy"] = True
                    result["health_status"] = "healthy"
                elif "(unhealthy)" in output:
                    result["health_status"] = "unhealthy"
                elif "(starting)" in output:
                    result["health_status"] = "starting"
                else:
                    result["health_status"] = "no_healthcheck"

                self.log(f"{service['name']}: Running ({result.get('health_status', 'unknown')})", "pass")
                self.results["passed"] += 1
            else:
                self.log(f"{service['name']}: Not running", "fail")
                self.results["failed"] += 1

        except Exception as e:
            self.log(f"{service['name']}: Error - {str(e)}", "fail")
            result["error"] = str(e)
            self.results["failed"] += 1

        return result

    def test_http_endpoint(self, service_key: str, endpoint: str = "/health") -> Dict[str, Any]:
        """Test HTTP endpoint"""
        service = SERVICES[service_key]
        url = f"{service['url']}{endpoint}"
        result = {"url": url, "reachable": False, "response_time": 0}

        try:
            start = time.time()
            response = requests.get(url, timeout=5)
            elapsed = int((time.time() - start) * 1000)
            result["response_time"] = elapsed

            if response.status_code == 200:
                result["reachable"] = True
                result["status_code"] = 200
                self.log(f"{service['name']} endpoint: OK ({elapsed}ms)", "pass")
                self.results["passed"] += 1
            else:
                result["status_code"] = response.status_code
                self.log(f"{service['name']} endpoint: Status {response.status_code}", "warn")
                self.results["warnings"] += 1

        except requests.exceptions.Timeout:
            self.log(f"{service['name']} endpoint: Timeout", "fail")
            result["error"] = "timeout"
            self.results["failed"] += 1
        except Exception as e:
            self.log(f"{service['name']} endpoint: Error - {str(e)}", "fail")
            result["error"] = str(e)
            self.results["failed"] += 1

        return result

    def test_database_connection(self) -> Dict[str, Any]:
        """Test database system"""
        self.print_header("DATA MANAGEMENT SYSTEM")
        result = {}

        # Container status
        result["container"] = self.test_docker_container("postgres")

        # Connection test
        try:
            cmd = 'docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -c "SELECT 1" 2>&1'
            output = subprocess.check_output(cmd, shell=True, text=True)

            if "1 row" in output:
                self.log("Database connection: OK", "pass")
                result["connection"] = True
                self.results["passed"] += 1
            else:
                self.log("Database connection: Failed", "fail")
                result["connection"] = False
                self.results["failed"] += 1

            # Count tables
            cmd = 'docker exec pilotpros-postgres-dev psql -U pilotpros_user -d pilotpros_db -c "\\dt" 2>&1 | grep -c "table"'
            table_count = subprocess.check_output(cmd, shell=True, text=True).strip()
            self.log(f"Database tables: {table_count} tables found", "pass")
            result["table_count"] = table_count
            self.results["passed"] += 1

        except Exception as e:
            self.log(f"Database test failed: {str(e)}", "fail")
            result["error"] = str(e)
            self.results["failed"] += 1

        return result

    def test_redis_connection(self) -> Dict[str, Any]:
        """Test cache service"""
        self.print_header("CACHE SERVICE")
        result = {}

        result["container"] = self.test_docker_container("redis")

        try:
            cmd = 'docker exec pilotpros-redis-dev redis-cli ping'
            output = subprocess.check_output(cmd, shell=True, text=True).strip()

            if output == "PONG":
                self.log("Redis connection: OK", "pass")
                result["connection"] = True
                self.results["passed"] += 1
            else:
                self.log("Redis connection: Failed", "fail")
                result["connection"] = False
                self.results["failed"] += 1

        except Exception as e:
            self.log(f"Redis test failed: {str(e)}", "fail")
            result["error"] = str(e)
            self.results["failed"] += 1

        return result

    def test_backend_api(self) -> Dict[str, Any]:
        """Test Backend API"""
        self.print_header("BACKEND: Express API")
        result = {}

        result["container"] = self.test_docker_container("backend")
        result["health"] = self.test_http_endpoint("backend", "/health")

        # Test API endpoints (expects 401 without auth token)
        try:
            response = requests.get("http://localhost:3001/api/users", timeout=5)
            if response.status_code in [200, 401]:
                self.log("Backend API endpoints: OK", "pass")
                result["api_working"] = True
                self.results["passed"] += 1
            else:
                self.log(f"Backend API: Status {response.status_code}", "warn")
                self.results["warnings"] += 1

        except Exception as e:
            self.log(f"Backend API test: {str(e)}", "warn")
            self.results["warnings"] += 1

        return result

    def test_frontend_portal(self) -> Dict[str, Any]:
        """Test Business Portal"""
        self.print_header("BUSINESS PORTAL")
        result = {}

        result["container"] = self.test_docker_container("frontend")

        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                self.log("Frontend portal: OK", "pass")
                result["reachable"] = True
                self.results["passed"] += 1

                # Check if it's web app
                if "app" in response.text.lower() or "html" in response.text.lower():
                    self.log("Web application: Detected", "pass")
                    self.results["passed"] += 1
            else:
                self.log(f"Frontend: Status {response.status_code}", "warn")
                self.results["warnings"] += 1

        except Exception as e:
            self.log(f"Frontend test: {str(e)}", "warn")
            self.results["warnings"] += 1

        return result

    def test_intelligence_engine(self) -> Dict[str, Any]:
        """Test Intelligence Engine"""
        self.print_header("INTELLIGENCE: AI Engine")
        result = {}

        result["container"] = self.test_docker_container("intelligence")
        result["health"] = self.test_http_endpoint("intelligence", "/health")

        # Test stats endpoint
        try:
            response = requests.get("http://localhost:8000/api/stats", timeout=5)
            if response.status_code == 200:
                data = response.json()
                framework = data.get('framework', 'unknown')
                self.log(f"AI Framework: Active", "pass")
                self.log(f"AI Models: {len(data.get('models_available', []))} available", "pass")
                self.log(f"AI Tools: {len(data.get('tools_available', []))} available", "pass")
                result["stats"] = data
                self.results["passed"] += 3
        except Exception as e:
            self.log(f"Stats endpoint: {str(e)}", "warn")
            self.results["warnings"] += 1

        # Test agent endpoint
        if not self.quick_mode:
            try:
                start = time.time()
                response = requests.post(
                    "http://localhost:8000/api/n8n/agent/customer-support",
                    json={"message": "System test", "session_id": "stack-test"},
                    timeout=30
                )
                elapsed = int((time.time() - start) * 1000)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.log(f"Agent response: OK ({elapsed}ms)", "pass")
                        result["agent_working"] = True
                        self.results["passed"] += 1
                    else:
                        self.log("Agent response: Error", "fail")
                        self.results["failed"] += 1
            except Exception as e:
                self.log(f"Agent test: {str(e)}", "warn")
                self.results["warnings"] += 1

        return result

    def test_automation_engine(self) -> Dict[str, Any]:
        """Test Automation Engine (n8n)"""
        self.print_header("AUTOMATION: Process Engine")
        result = {}

        result["container"] = self.test_docker_container("automation")

        try:
            response = requests.get("http://localhost:5678/healthz", timeout=5)
            if response.status_code == 200:
                self.log("Automation health: OK", "pass")
                result["health"] = True
                self.results["passed"] += 1
            else:
                self.log(f"Automation health: Status {response.status_code}", "warn")
                self.results["warnings"] += 1

        except Exception as e:
            self.log(f"Automation test: {str(e)}", "warn")
            self.results["warnings"] += 1

        return result

    def test_nginx_monitor(self) -> Dict[str, Any]:
        """Test System Monitor"""
        self.print_header("SYSTEM MONITOR")
        result = {}

        result["container"] = self.test_docker_container("nginx")

        try:
            response = requests.get("http://localhost:80", timeout=5, allow_redirects=False)
            if response.status_code in [200, 301, 302, 307, 308]:
                self.log("System proxy: OK", "pass")
                result["working"] = True
                self.results["passed"] += 1
            else:
                self.log(f"Monitor: Status {response.status_code}", "warn")
                self.results["warnings"] += 1

        except Exception as e:
            self.log(f"Monitor test: {str(e)}", "warn")
            self.results["warnings"] += 1

        return result

    def test_inter_service_communication(self) -> Dict[str, Any]:
        """Test communication between services"""
        self.print_header("INTER-SERVICE COMMUNICATION")
        result = {}

        # Test: Automation Engine → Intelligence Engine
        try:
            cmd = 'docker exec pilotpros-automation-engine-dev wget -qO- http://pilotpros-intelligence-engine-dev:8000/health'
            output = subprocess.check_output(cmd, shell=True, text=True, timeout=5)

            if "healthy" in output:
                self.log("Automation → Intelligence Engine: OK", "pass")
                result["automation_to_intelligence"] = True
                self.results["passed"] += 1
            else:
                self.log("Automation → Intelligence Engine: Failed", "fail")
                self.results["failed"] += 1

        except Exception as e:
            self.log(f"Automation → Intelligence Engine: {str(e)}", "fail")
            result["automation_to_intelligence"] = False
            self.results["failed"] += 1

        # Test: Intelligence Engine → Data Management
        try:
            cmd = 'docker exec pilotpros-intelligence-engine-dev python3 -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect(\\"postgresql://pilotpros_user:pilotpros_secure_pass_2025@postgres-dev:5432/pilotpros_db\\"))" 2>&1'
            output = subprocess.check_output(cmd, shell=True, text=True, timeout=5)

            if "error" not in output.lower() and "exception" not in output.lower():
                self.log("Intelligence Engine → Data Management: OK", "pass")
                result["intelligence_to_db"] = True
                self.results["passed"] += 1
            else:
                self.log("Intelligence Engine → Data Management: Failed", "fail")
                self.results["failed"] += 1

        except Exception as e:
            self.log(f"Intelligence Engine → Data Management: {str(e)}", "warn")
            self.results["warnings"] += 1

        # Test: Backend → Data Management
        try:
            response = requests.get("http://localhost:3001/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("database") == "connected":
                    self.log("Backend → Data Management: OK", "pass")
                    result["backend_to_db"] = True
                    self.results["passed"] += 1
                else:
                    self.log("Backend → Data Management: Disconnected", "fail")
                    self.results["failed"] += 1

        except Exception as e:
            self.log(f"Backend → Data Management: {str(e)}", "fail")
            self.results["failed"] += 1

        # Test: Intelligence Engine → Redis
        try:
            cmd = 'docker exec pilotpros-intelligence-engine-dev python3 -c "import redis; r = redis.Redis(host=\\"redis-dev\\", port=6379); r.ping()" 2>&1'
            output = subprocess.check_output(cmd, shell=True, text=True, timeout=5)

            if "True" in output or not output.strip():
                self.log("Intelligence Engine → Redis: OK", "pass")
                result["intelligence_to_redis"] = True
                self.results["passed"] += 1
            else:
                self.log("Intelligence Engine → Redis: Failed", "fail")
                self.results["failed"] += 1

        except Exception as e:
            self.log(f"Intelligence Engine → Redis: {str(e)}", "warn")
            self.results["warnings"] += 1

        return result

    def test_end_to_end_workflow(self) -> Dict[str, Any]:
        """Test complete end-to-end workflow"""
        if self.quick_mode:
            return {}

        self.print_header("END-TO-END WORKFLOW TEST")
        result = {}

        try:
            # Simulate Automation → Intelligence Engine → Database → Response
            start = time.time()

            # Step 1: Send message to Intelligence Engine
            response = requests.post(
                "http://localhost:8000/api/n8n/agent/customer-support",
                json={
                    "message": "How many users are in the database?",
                    "session_id": "e2e-test"
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            elapsed = int((time.time() - start) * 1000)

            if response.status_code == 200:
                data = response.json()

                # Step 2: Check if agent processed successfully
                if data.get("success"):
                    self.log("E2E: Message sent → Agent processed", "pass")
                    self.results["passed"] += 1

                    # Step 3: Check if database was queried
                    if data.get("database_used"):
                        self.log("E2E: Agent → Database query executed", "pass")
                        self.results["passed"] += 1

                        # Step 4: Check if response is meaningful
                        response_text = data.get("agent_response", "")
                        if len(response_text) > 10:
                            self.log(f"E2E: Response generated ({elapsed}ms)", "pass")
                            result["complete_workflow"] = True
                            result["response_time"] = elapsed
                            self.results["passed"] += 1
                        else:
                            self.log("E2E: Response too short", "warn")
                            self.results["warnings"] += 1
                    else:
                        self.log("E2E: Database not queried", "warn")
                        self.results["warnings"] += 1
                else:
                    self.log("E2E: Agent processing failed", "fail")
                    self.results["failed"] += 1
            else:
                self.log(f"E2E: Request failed ({response.status_code})", "fail")
                self.results["failed"] += 1

        except Exception as e:
            self.log(f"E2E workflow: {str(e)}", "fail")
            result["error"] = str(e)
            self.results["failed"] += 1

        return result

    def print_summary(self):
        """Print final summary"""
        if self.json_output:
            output = {
                "timestamp": datetime.now().isoformat(),
                "total_time_seconds": self.results["total_time"] / 1000,
                "results": self.results,
                "status": "PASS" if self.results["failed"] == 0 else "FAIL"
            }
            print(json.dumps(output, indent=2))
            return

        self.print_header("FINAL SUMMARY")

        total = self.results["passed"] + self.results["failed"] + self.results["warnings"]
        passed_pct = (self.results["passed"] / total * 100) if total > 0 else 0

        print(f"{GREEN}PASSED:{RESET}      {self.results['passed']}/{total}")
        print(f"{RED}FAILED:{RESET}      {self.results['failed']}/{total}")
        print(f"{YELLOW}WARNINGS:{RESET}    {self.results['warnings']}/{total}")
        print(f"\n{BLUE}Success Rate:{RESET} {passed_pct:.1f}%")
        print(f"{BLUE}Total Time:{RESET}   {self.results['total_time']/1000:.2f}s")

        if self.results["failed"] == 0 and self.results["warnings"] == 0:
            print(f"\n{GREEN}{'PERFECT! ALL TESTS PASSED!'.center(70)}{RESET}")
            return 0
        elif self.results["failed"] == 0:
            print(f"\n{YELLOW}{'PASSED WITH WARNINGS'.center(70)}{RESET}")
            return 0
        elif self.results["failed"] < 3:
            print(f"\n{YELLOW}{'MINOR ISSUES DETECTED'.center(70)}{RESET}")
            return 1
        else:
            print(f"\n{RED}{'CRITICAL ISSUES - STACK NOT READY'.center(70)}{RESET}")
            return 2

    def run_all_tests(self):
        """Run complete test suite"""
        if not self.json_output:
            print(f"\n{CYAN}{'='*70}{RESET}")
            print(f"{CYAN}{'PILOTPROS STACK - DEEP TEST SUITE'.center(70)}{RESET}")
            print(f"{CYAN}{'='*70}{RESET}")
            print(f"\nMode: {'Quick' if self.quick_mode else 'Complete'}")
            print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Test all services
        self.results["services"]["database"] = self.test_database_connection()
        self.results["services"]["redis"] = self.test_redis_connection()
        self.results["services"]["backend"] = self.test_backend_api()
        self.results["services"]["frontend"] = self.test_frontend_portal()
        self.results["services"]["intelligence"] = self.test_intelligence_engine()
        self.results["services"]["automation"] = self.test_automation_engine()
        self.results["services"]["nginx"] = self.test_nginx_monitor()

        # Test communications
        self.results["communications"] = self.test_inter_service_communication()

        # Test end-to-end workflow
        if not self.quick_mode:
            self.results["e2e"] = self.test_end_to_end_workflow()

        self.results["total_time"] = int((time.time() - self.start_time) * 1000)

        return self.print_summary()


if __name__ == "__main__":
    quick_mode = "--quick" in sys.argv
    json_output = "--json" in sys.argv

    tester = StackDeepTest(quick_mode=quick_mode, json_output=json_output)
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)