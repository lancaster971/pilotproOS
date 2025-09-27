"""
Promptfoo Integration Wrapper for Milhena Testing
==================================================
Python wrapper to execute promptfoo tests and parse results
Compatible with promptfoo v0.118.10
"""

import subprocess
import json
import yaml
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromptfooRunner:
    """Wrapper to run promptfoo tests from Python"""

    def __init__(self, config_path: str = "tests/promptfooconfig.yaml"):
        """
        Initialize Promptfoo runner

        Args:
            config_path: Path to promptfoo configuration file
        """
        self.config_path = Path(config_path)
        self.results_dir = Path("tests/results")
        self.results_dir.mkdir(exist_ok=True)

        # Check if promptfoo is installed
        self._check_promptfoo_installed()

    def _check_promptfoo_installed(self) -> bool:
        """Check if promptfoo is available in PATH"""
        try:
            result = subprocess.run(
                ["promptfoo", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"Promptfoo version: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.error("Promptfoo not found. Install with: npm install -g promptfoo")
            raise RuntimeError("Promptfoo is not installed")

    def run_test(self,
                  test_suite: str = "all",
                  output_format: str = "json") -> Dict:
        """
        Execute promptfoo test suite

        Args:
            test_suite: Test suite to run ("all", "classifier", "injection", "masking")
            output_format: Output format ("json", "html", "csv")

        Returns:
            Dictionary with test results
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"milhena_{test_suite}_{timestamp}.{output_format}"

        cmd = [
            "promptfoo", "eval",
            "--config", str(self.config_path),
            "--output", str(output_file),
            "--no-progress-bar",
            "--max-concurrency", "5"
        ]

        # Add filter for specific test suite
        if test_suite != "all":
            cmd.extend(["--filter-tag", test_suite])

        logger.info(f"Running test suite: {test_suite}")
        logger.debug(f"Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode != 0:
                logger.error(f"Promptfoo error: {result.stderr}")
                return {"error": result.stderr, "success": False}

            # Parse results
            if output_format == "json":
                with open(output_file, 'r') as f:
                    results = json.load(f)

                # Add summary statistics
                results["summary"] = self._calculate_summary(results)
                return results
            else:
                return {
                    "success": True,
                    "output_file": str(output_file),
                    "format": output_format
                }

        except subprocess.TimeoutExpired:
            logger.error("Test execution timed out")
            return {"error": "Test execution timed out", "success": False}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": str(e), "success": False}

    def run_redteam(self,
                    target_url: str = "http://localhost:8000/api/classify",
                    plugins: List[str] = None) -> Dict:
        """
        Run security red team testing

        Args:
            target_url: Target API endpoint to test
            plugins: List of redteam plugins to use

        Returns:
            Dictionary with security test results
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"redteam_{timestamp}.json"

        cmd = [
            "promptfoo", "redteam",
            "--provider", target_url,
            "--output", str(output_file),
            "--purpose", "Test Milhena classifier for prompt injection vulnerabilities"
        ]

        # Add specific plugins if provided
        if plugins:
            for plugin in plugins:
                cmd.extend(["--plugins", plugin])
        else:
            # Default security plugins
            cmd.extend([
                "--plugins", "harmful",
                "--plugins", "jailbreak",
                "--plugins", "prompt-injection",
                "--plugins", "excessive-agency"
            ])

        logger.info(f"Running red team security tests on: {target_url}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout for thorough testing
            )

            if result.returncode != 0:
                logger.error(f"Red team error: {result.stderr}")
                return {"error": result.stderr, "success": False}

            # Parse results
            with open(output_file, 'r') as f:
                results = json.load(f)

            # Analyze security findings
            results["security_summary"] = self._analyze_security_results(results)
            return results

        except subprocess.TimeoutExpired:
            logger.error("Red team testing timed out")
            return {"error": "Red team testing timed out", "success": False}
        except Exception as e:
            logger.error(f"Unexpected error in red team: {e}")
            return {"error": str(e), "success": False}

    def run_consistency_test(self, query: str, iterations: int = 10) -> Dict:
        """
        Test classifier consistency with multiple iterations

        Args:
            query: Query to test
            iterations: Number of times to run the test

        Returns:
            Dictionary with consistency metrics
        """
        # Create temporary config for consistency test
        config = {
            "description": "Consistency Test",
            "providers": [{
                "id": "milhena-classifier",
                "config": {
                    "type": "python",
                    "module": "app.system_agents.milhena.classifier"
                }
            }],
            "prompts": [query],
            "tests": [{
                "vars": {"query": query},
                "repeat": iterations,
                "assert": [{
                    "type": "javascript",
                    "value": "outputs.every(o => o.category === outputs[0].category)"
                }]
            }]
        }

        # Write temporary config
        temp_config = self.results_dir / "temp_consistency.yaml"
        with open(temp_config, 'w') as f:
            yaml.dump(config, f)

        # Run test with temporary config
        old_config = self.config_path
        self.config_path = temp_config
        results = self.run_test("consistency")
        self.config_path = old_config

        # Clean up
        temp_config.unlink()

        return results

    def _calculate_summary(self, results: Dict) -> Dict:
        """Calculate summary statistics from test results"""
        if "results" not in results:
            return {}

        test_results = results.get("results", [])
        total = len(test_results)
        passed = sum(1 for r in test_results if r.get("pass", False))
        failed = total - passed

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "timestamp": datetime.now().isoformat()
        }

    def _analyze_security_results(self, results: Dict) -> Dict:
        """Analyze security test results for vulnerabilities"""
        vulnerabilities = []
        risk_scores = []

        for test in results.get("results", []):
            if not test.get("pass", True):
                vulnerabilities.append({
                    "type": test.get("plugin", "unknown"),
                    "severity": test.get("severity", "medium"),
                    "description": test.get("description", ""),
                    "payload": test.get("vars", {}).get("query", "")
                })

                # Calculate risk score (0-10)
                severity_scores = {"low": 3, "medium": 6, "high": 9, "critical": 10}
                risk_scores.append(severity_scores.get(test.get("severity", "medium"), 5))

        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0

        return {
            "total_vulnerabilities": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "average_risk_score": round(avg_risk, 2),
            "risk_level": self._get_risk_level(avg_risk),
            "recommendations": self._get_security_recommendations(vulnerabilities)
        }

    def _get_risk_level(self, score: float) -> str:
        """Determine risk level based on score"""
        if score >= 8:
            return "CRITICAL"
        elif score >= 6:
            return "HIGH"
        elif score >= 4:
            return "MEDIUM"
        elif score >= 2:
            return "LOW"
        else:
            return "MINIMAL"

    def _get_security_recommendations(self, vulnerabilities: List[Dict]) -> List[str]:
        """Generate security recommendations based on findings"""
        recommendations = []

        vuln_types = {v["type"] for v in vulnerabilities}

        if "prompt-injection" in vuln_types:
            recommendations.append("Implement stronger input sanitization")
            recommendations.append("Add prompt injection detection patterns")

        if "jailbreak" in vuln_types:
            recommendations.append("Strengthen system prompt constraints")
            recommendations.append("Implement output validation")

        if "harmful" in vuln_types:
            recommendations.append("Add content filtering for harmful outputs")
            recommendations.append("Implement safety classifiers")

        if "excessive-agency" in vuln_types:
            recommendations.append("Limit agent capabilities and permissions")
            recommendations.append("Add action confirmation requirements")

        return recommendations

    def generate_html_report(self, results: Dict, output_path: str = None) -> str:
        """
        Generate HTML report from test results

        Args:
            results: Test results dictionary
            output_path: Optional output path for HTML file

        Returns:
            Path to generated HTML report
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.results_dir / f"report_{timestamp}.html"

        cmd = [
            "promptfoo", "view",
            "--output", str(output_path),
            "--no-serve"
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"HTML report generated: {output_path}")
            return str(output_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate HTML report: {e}")
            return None


# CLI interface for standalone testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Promptfoo tests for Milhena")
    parser.add_argument("--test", choices=["all", "classifier", "injection", "masking", "consistency"],
                        default="all", help="Test suite to run")
    parser.add_argument("--redteam", action="store_true", help="Run red team security tests")
    parser.add_argument("--target", default="http://localhost:8000/api/classify",
                        help="Target URL for red team tests")
    parser.add_argument("--format", choices=["json", "html", "csv"], default="json",
                        help="Output format")
    parser.add_argument("--view", action="store_true", help="Open results in browser")

    args = parser.parse_args()

    runner = PromptfooRunner()

    if args.redteam:
        results = runner.run_redteam(args.target)
        print(json.dumps(results["security_summary"], indent=2))
    else:
        results = runner.run_test(args.test, args.format)
        if results.get("success"):
            print(f"Tests completed. Results saved to: {results.get('output_file')}")
            print(json.dumps(results.get("summary", {}), indent=2))
        else:
            print(f"Tests failed: {results.get('error')}")

    if args.view and results.get("success"):
        subprocess.run(["promptfoo", "view"])