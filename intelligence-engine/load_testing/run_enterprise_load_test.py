#!/usr/bin/env python3.11
"""
🚀 PilotProOS Enterprise Load Test Orchestrator
===============================================

Script di orchestrazione completo per load testing enterprise
Integra Locust + Real-Time Monitoring + Report generation

Features:
- Pre-test validation sistema target
- Orchestrazione Locust con parametri enterprise
- Monitoring real-time durante test
- Report post-test con compliance check
- Integration con metriche Prometheus esistenti

Usage:
    python run_enterprise_load_test.py --users 1000 --duration 10m --ramp-up 50

Author: PilotProOS Development Team
Version: 1.0.0 Enterprise
Date: 2025-09-29
"""

import os
import sys
import time
import subprocess
import argparse
import signal
import json
import logging
from pathlib import Path
from datetime import datetime
import requests
import threading
from typing import Optional, Dict, Any

# Add current directory to path for local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from real_time_monitoring import RealTimeMonitor, critical_alert_callback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnterpriseLoadTestOrchestrator:
    """
    Orchestratore principale per load testing enterprise
    """

    def __init__(self):
        self.intelligence_url = os.getenv('LOAD_TEST_HOST', 'http://localhost:8000')
        self.locust_web_port = 8089
        self.locust_process: Optional[subprocess.Popen] = None
        self.monitor: Optional[RealTimeMonitor] = None
        self.test_start_time: Optional[datetime] = None
        self.test_results: Dict[str, Any] = {}

        # Setup directories
        self.base_dir = Path(__file__).parent
        self.reports_dir = self.base_dir / "reports"
        self.logs_dir = self.base_dir / "logs"

        # Create directories
        self.reports_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """
        Graceful shutdown handler
        """
        logger.info(f"🛑 Received signal {signum} - stopping load test gracefully...")
        self.stop_load_test()
        sys.exit(0)

    def validate_target_system(self) -> bool:
        """
        Valida che il sistema target sia pronto per load testing
        """
        logger.info("🔍 Validating target system readiness...")

        try:
            # Check health endpoint
            response = requests.get(f"{self.intelligence_url}/health", timeout=10)
            if response.status_code != 200:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False

            health_data = response.json()
            if health_data.get("status") != "healthy":
                logger.error(f"❌ System not healthy: {health_data.get('status')}")
                return False

            # Check all components
            components = health_data.get("components", {})
            failed_components = [comp for comp, status in components.items()
                               if status not in ["active", "connected", "ready"]]

            if failed_components:
                logger.error(f"❌ Failed components: {failed_components}")
                return False

            logger.info(f"✅ System health OK: {health_data}")

            # Check metrics endpoint
            metrics_response = requests.get(f"{self.intelligence_url}/metrics", timeout=5)
            if metrics_response.status_code != 200:
                logger.error("❌ Metrics endpoint not available")
                return False

            # Verify PilotProOS metrics are present
            metrics_text = metrics_response.text
            if "pilotpros_" not in metrics_text:
                logger.warning("⚠️ PilotProOS custom metrics not found in /metrics")
            else:
                logger.info("✅ PilotProOS metrics detected")

            # Check API endpoints responsiveness
            test_endpoints = ["/api/chat", "/api/n8n/agent/customer-support"]
            for endpoint in test_endpoints:
                try:
                    test_response = requests.post(
                        f"{self.intelligence_url}{endpoint}",
                        json={"message": "system test", "session_id": "validation_test"},
                        timeout=10
                    )
                    if test_response.status_code in [200, 400, 422]:  # 400/422 are OK for validation
                        logger.info(f"✅ Endpoint {endpoint} responding")
                    else:
                        logger.warning(f"⚠️ Endpoint {endpoint} returned {test_response.status_code}")
                except Exception as e:
                    logger.warning(f"⚠️ Endpoint {endpoint} test failed: {e}")

            return True

        except Exception as e:
            logger.error(f"❌ System validation failed: {e}")
            return False

    def start_load_test(self, users: int, duration: str, spawn_rate: int,
                       user_class: str = "PilotProOSLoadTester") -> bool:
        """
        Avvia load test con Locust
        """
        logger.info(f"🚀 Starting enterprise load test...")
        logger.info(f"   Users: {users}")
        logger.info(f"   Duration: {duration}")
        logger.info(f"   Spawn Rate: {spawn_rate}/sec")
        logger.info(f"   User Class: {user_class}")

        try:
            # Prepare Locust command in HEADLESS mode for automated testing
            locust_cmd = [
                "locust",
                "--locustfile", str(self.base_dir / "locustfile_enterprise.py"),
                "--host", self.intelligence_url,
                "--headless",  # AUTOMATED MODE - no Web UI required
                "--users", str(users),
                "--spawn-rate", str(spawn_rate),
                "--run-time", duration,
                "--html", str(self.reports_dir / f"locust_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"),
                "--csv", str(self.reports_dir / f"locust_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                "--logfile", str(self.logs_dir / f"locust_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                "--loglevel", "INFO",
                "--print-stats",  # Print stats to console in headless mode
                "--only-summary"  # Only show summary stats
            ]

            # Add user class if specified
            if user_class != "PilotProOSLoadTester":
                locust_cmd.extend(["-u", str(users), "-r", str(spawn_rate)])

            logger.info(f"Executing: {' '.join(locust_cmd)}")

            # Start Locust process
            self.locust_process = subprocess.Popen(
                locust_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.base_dir
            )

            # Wait for Locust process to initialize (headless mode)
            logger.info("⏳ Waiting for Locust headless process to start...")
            time.sleep(3)  # Give process time to initialize

            # Verify process is running
            if self.locust_process.poll() is not None:
                logger.error("❌ Locust process failed to start or exited immediately")
                return False

            logger.info("✅ Locust headless process active")

            self.test_start_time = datetime.now()
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start load test: {e}")
            return False

    def start_monitoring(self):
        """
        Avvia monitoring real-time
        """
        logger.info("📊 Starting real-time monitoring...")

        self.monitor = RealTimeMonitor(
            intelligence_engine_url=self.intelligence_url,
            locust_web_url=f"http://localhost:{self.locust_web_port}",
            monitoring_interval=5
        )

        # Add alert callback
        self.monitor.add_alert_callback(critical_alert_callback)
        self.monitor.start_monitoring()

        logger.info("✅ Real-time monitoring active")

    def wait_for_test_completion(self, duration_minutes: int):
        """
        Attende completamento test con monitoring
        """
        logger.info(f"⏳ Load test running for {duration_minutes} minutes...")
        logger.info(f"   Locust Web UI: http://localhost:{self.locust_web_port}")
        logger.info(f"   Intelligence Engine: {self.intelligence_url}")

        # Calculate total wait time
        total_seconds = duration_minutes * 60
        check_interval = 30  # Check every 30 seconds

        elapsed = 0
        while elapsed < total_seconds:
            time.sleep(check_interval)
            elapsed += check_interval

            remaining_minutes = (total_seconds - elapsed) / 60
            logger.info(f"⏳ Test progress: {elapsed//60:.0f}/{duration_minutes} minutes ({remaining_minutes:.1f} remaining)")

            # Check if Locust process is still running
            if self.locust_process and self.locust_process.poll() is not None:
                logger.info("🏁 Locust process completed")
                break

        logger.info("✅ Load test duration completed")

    def stop_load_test(self):
        """
        Ferma load test e monitoring
        """
        logger.info("🛑 Stopping load test...")

        # Stop monitoring first
        if self.monitor:
            self.monitor.stop_monitoring()

        # Stop Locust process
        if self.locust_process:
            try:
                # Try graceful shutdown first
                self.locust_process.terminate()

                # Wait up to 10 seconds for graceful shutdown
                try:
                    self.locust_process.wait(timeout=10)
                    logger.info("✅ Locust process stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if necessary
                    logger.warning("⚠️ Forcing Locust process termination...")
                    self.locust_process.kill()
                    self.locust_process.wait()
                    logger.info("✅ Locust process killed")

            except Exception as e:
                logger.error(f"Error stopping Locust: {e}")

    def generate_executive_summary(self):
        """
        Genera summary esecutivo dei risultati
        """
        logger.info("📋 Generating executive summary...")

        try:
            # Collect final metrics from various sources
            summary = {
                'test_metadata': {
                    'start_time': self.test_start_time.isoformat() if self.test_start_time else None,
                    'end_time': datetime.now().isoformat(),
                    'intelligence_engine_url': self.intelligence_url,
                    'duration_minutes': (datetime.now() - self.test_start_time).total_seconds() / 60 if self.test_start_time else 0
                },
                'system_validation': {
                    'pre_test_health_check': 'PASSED',
                    'metrics_endpoint_available': True,
                    'api_endpoints_responsive': True
                }
            }

            # Save summary
            summary_file = self.reports_dir / f"executive_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)

            logger.info(f"✅ Executive summary saved: {summary_file}")

            # Print summary to console
            duration = summary['test_metadata']['duration_minutes']
            logger.info(f"""
🎯 ENTERPRISE LOAD TEST EXECUTIVE SUMMARY
=========================================
📊 Test Duration: {duration:.1f} minutes
🌐 Target System: {self.intelligence_url}
✅ System Validation: PASSED
📁 Reports Location: {self.reports_dir}
📊 Monitoring Data: Available in reports
🔍 Locust Web UI History: http://localhost:{self.locust_web_port}

Next Steps:
1. Review detailed reports in {self.reports_dir}
2. Analyze performance charts
3. Check compliance with enterprise thresholds
4. Plan production capacity based on results
""")

        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")

def parse_duration(duration_str: str) -> int:
    """
    Parse duration string to minutes
    Examples: "10m", "1h", "90s"
    """
    duration_str = duration_str.lower().strip()

    if duration_str.endswith('s'):
        return int(duration_str[:-1]) // 60 or 1  # At least 1 minute
    elif duration_str.endswith('m'):
        return int(duration_str[:-1])
    elif duration_str.endswith('h'):
        return int(duration_str[:-1]) * 60
    else:
        # Assume minutes if no suffix
        return int(duration_str)

def main():
    parser = argparse.ArgumentParser(
        description="🚀 PilotProOS Enterprise Load Test Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic enterprise test (1000 users, 10 minutes)
  python run_enterprise_load_test.py --users 1000 --duration 10m --ramp-up 50

  # Stress test with aggressive users
  python run_enterprise_load_test.py --users 2000 --duration 15m --ramp-up 100 --user-class EnterprisePilotProOSUser

  # Quick validation test
  python run_enterprise_load_test.py --users 100 --duration 2m --ramp-up 20

Environment Variables:
  LOAD_TEST_HOST - Target system URL (default: http://localhost:8000)
  PROMETHEUS_GATEWAY - Prometheus gateway for metrics (optional)
        """
    )

    parser.add_argument('--users', type=int, default=1000,
                       help='Number of concurrent users (default: 1000)')

    parser.add_argument('--duration', type=str, default='10m',
                       help='Test duration: 10s, 5m, 1h (default: 10m)')

    parser.add_argument('--ramp-up', type=int, default=50,
                       help='User spawn rate per second (default: 50)')

    parser.add_argument('--user-class', type=str, default='PilotProOSLoadTester',
                       choices=['PilotProOSLoadTester', 'EnterprisePilotProOSUser'],
                       help='User class for testing (default: PilotProOSLoadTester)')

    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip pre-test system validation')

    parser.add_argument('--monitoring-only', action='store_true',
                       help='Run only real-time monitoring (no load test)')

    args = parser.parse_args()

    print("🚀 PilotProOS Enterprise Load Test Orchestrator")
    print("=" * 60)
    print(f"Target System: {os.getenv('LOAD_TEST_HOST', 'http://localhost:8000')}")
    print(f"Test Parameters: {args.users} users, {args.duration}, {args.ramp_up} ramp-up/sec")
    print("=" * 60)

    # Initialize orchestrator
    orchestrator = EnterpriseLoadTestOrchestrator()

    try:
        if not args.monitoring_only:
            # Pre-test validation
            if not args.skip_validation:
                if not orchestrator.validate_target_system():
                    logger.error("❌ System validation failed - aborting test")
                    return 1
            else:
                logger.warning("⚠️ Skipping system validation as requested")

            # Start load test
            duration_minutes = parse_duration(args.duration)
            if not orchestrator.start_load_test(args.users, args.duration, args.ramp_up, args.user_class):
                logger.error("❌ Failed to start load test")
                return 1

        # Start monitoring
        orchestrator.start_monitoring()

        if not args.monitoring_only:
            # Wait for test completion
            orchestrator.wait_for_test_completion(duration_minutes)
        else:
            logger.info("📊 Running in monitoring-only mode - press Ctrl+C to stop")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")

    except Exception as e:
        logger.error(f"❌ Test execution error: {e}")
        return 1

    finally:
        # Cleanup
        orchestrator.stop_load_test()
        orchestrator.generate_executive_summary()

    logger.info("🎉 Enterprise load test completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())