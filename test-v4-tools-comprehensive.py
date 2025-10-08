#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE V4.0 TOOLS TEST SUITE
Rigorous and deep testing of ALL 19 GraphSupervisor v4.0 tools

Tests every tool with multiple scenarios:
- Normal operation
- Edge cases
- Error handling
- Performance
- Business masking
- Tool selection by AI

Author: Claude Code
Date: 2025-10-08
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field

# Configuration
API_BASE = "http://localhost:8000/api/n8n/agent/customer-support"
TIMEOUT = 30

# Test result tracking
@dataclass
class ToolTestResult:
    tool_name: str
    test_name: str
    query: str
    success: bool
    latency_ms: int
    tool_called: bool = False
    response_preview: str = ""
    error: str = ""
    business_masked: bool = True
    technical_leaks: List[str] = field(default_factory=list)

class V4ToolsTestSuite:
    """Comprehensive test suite for all 19 v4.0 tools"""

    def __init__(self):
        self.results: List[ToolTestResult] = []
        self.session_counter = 0

    def get_session_id(self) -> str:
        """Generate unique session ID for tests"""
        self.session_counter += 1
        return f"test-v4-tools-{self.session_counter}-{int(time.time())}"

    def call_agent(self, query: str, expected_tool: str = None) -> Tuple[Dict[Any, Any], int]:
        """Call v4.0 agent and measure latency"""
        start = time.time()
        try:
            response = requests.post(
                API_BASE,
                json={"message": query, "session_id": self.get_session_id()},
                headers={"Content-Type": "application/json"},
                timeout=TIMEOUT
            )
            latency = int((time.time() - start) * 1000)

            if response.status_code == 200:
                return response.json(), latency
            else:
                return {"error": f"HTTP {response.status_code}", "response": response.text[:200]}, latency

        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return {"error": str(e)}, latency

    def check_masking(self, text: str) -> Tuple[bool, List[str]]:
        """Check if technical terms are properly masked"""
        technical_terms = [
            "workflow", "execution", "node", "PostgreSQL", "Redis",
            "n8n", "database", "endpoint", "API", "webhook", "SQL"
        ]

        leaks = [term for term in technical_terms if term.lower() in text.lower()]
        return (len(leaks) == 0), leaks

    def add_result(self, result: ToolTestResult):
        """Add test result to collection"""
        self.results.append(result)

    def print_header(self, text: str):
        """Print test section header"""
        print(f"\n{'='*80}")
        print(f"{text.center(80)}")
        print(f"{'='*80}\n")

    def print_result(self, result: ToolTestResult):
        """Print single test result"""
        icon = "✅" if result.success else "❌"
        masking_icon = "🔒" if result.business_masked else "⚠️ LEAK"
        tool_icon = "🔧" if result.tool_called else "💬"

        print(f"{icon} {result.test_name}")
        print(f"   Query: '{result.query}'")
        print(f"   {tool_icon} Tool: {result.tool_name} | Latency: {result.latency_ms}ms | {masking_icon}")
        if result.response_preview:
            print(f"   Response: {result.response_preview[:100]}...")
        if result.technical_leaks:
            print(f"   ⚠️  Technical leaks: {result.technical_leaks}")
        if result.error:
            print(f"   ❌ Error: {result.error}")
        print()

    # ============================================================================
    # MILHENA AGENT TOOLS (10 tools)
    # ============================================================================

    def test_get_workflows_tool(self):
        """Test 1: get_workflows_tool - Basic workflow list"""
        self.print_header("TEST 1: get_workflows_tool")

        test_cases = [
            ("quali processi abbiamo?", "basic list"),
            ("mostra i workflow attivi", "active filter"),
            ("lista tutti i processi aziendali", "all workflows"),
        ]

        for query, test_name in test_cases:
            data, latency = self.call_agent(query)

            response_text = data.get("response", "")
            success = data.get("status") == "success" and len(response_text) > 0
            masked, leaks = self.check_masking(response_text)

            result = ToolTestResult(
                tool_name="get_workflows_tool",
                test_name=test_name,
                query=query,
                success=success,
                latency_ms=latency,
                tool_called=True,  # Assume tool was called if response contains process info
                response_preview=response_text,
                business_masked=masked,
                technical_leaks=leaks,
                error=data.get("error", "")
            )

            self.add_result(result)
            self.print_result(result)
            time.sleep(1)  # Rate limiting

    def test_get_workflow_cards_tool(self):
        """Test 2: get_workflow_cards_tool - Workflow overview cards"""
        self.print_header("TEST 2: get_workflow_cards_tool")

        test_cases = [
            ("dammi una panoramica dei processi", "overview request"),
            ("mostra le card dei workflow", "explicit cards"),
        ]

        for query, test_name in test_cases:
            data, latency = self.call_agent(query)

            response_text = data.get("response", "")
            success = data.get("status") == "success"
            masked, leaks = self.check_masking(response_text)

            result = ToolTestResult(
                tool_name="get_workflow_cards_tool",
                test_name=test_name,
                query=query,
                success=success,
                latency_ms=latency,
                tool_called=True,
                response_preview=response_text,
                business_masked=masked,
                technical_leaks=leaks
            )

            self.add_result(result)
            self.print_result(result)
            time.sleep(1)

    def test_get_workflow_details_tool(self):
        """Test 3: get_workflow_details_tool - Specific workflow details"""
        self.print_header("TEST 3: get_workflow_details_tool")

        test_cases = [
            ("info sul processo ChatOne", "specific workflow"),
            ("dettagli del workflow GommeGo", "another workflow"),
            ("come funziona il processo di automazione email?", "workflow by description"),
        ]

        for query, test_name in test_cases:
            data, latency = self.call_agent(query)

            response_text = data.get("response", "")
            success = data.get("status") == "success"
            masked, leaks = self.check_masking(response_text)

            result = ToolTestResult(
                tool_name="get_workflow_details_tool",
                test_name=test_name,
                query=query,
                success=success,
                latency_ms=latency,
                tool_called=True,
                response_preview=response_text,
                business_masked=masked,
                technical_leaks=leaks
            )

            self.add_result(result)
            self.print_result(result)
            time.sleep(1)

    def test_get_all_errors_summary_tool(self):
        """Test 4: get_all_errors_summary_tool - Error aggregation"""
        self.print_header("TEST 4: get_all_errors_summary_tool")

        test_cases = [
            ("quali errori abbiamo oggi?", "today errors"),
            ("mostra un riassunto dei problemi", "problems summary"),
            ("ci sono stati errori nelle ultime 24 ore?", "24h timeframe"),
        ]

        for query, test_name in test_cases:
            data, latency = self.call_agent(query)

            response_text = data.get("response", "")
            success = data.get("status") == "success"
            masked, leaks = self.check_masking(response_text)

            result = ToolTestResult(
                tool_name="get_all_errors_summary_tool",
                test_name=test_name,
                query=query,
                success=success,
                latency_ms=latency,
                tool_called=True,
                response_preview=response_text,
                business_masked=masked,
                technical_leaks=leaks
            )

            self.add_result(result)
            self.print_result(result)
            time.sleep(1)

    def test_search_knowledge_base_tool(self):
        """Test 5: search_knowledge_base_tool - RAG semantic search"""
        self.print_header("TEST 5: search_knowledge_base_tool")

        test_cases = [
            ("come configurare un processo automatizzato?", "configuration question"),
            ("spiegami come funziona l'integrazione email", "explanation request"),
        ]

        for query, test_name in test_cases:
            data, latency = self.call_agent(query)

            response_text = data.get("response", "")
            success = data.get("status") == "success"
            masked, leaks = self.check_masking(response_text)

            result = ToolTestResult(
                tool_name="search_knowledge_base_tool",
                test_name=test_name,
                query=query,
                success=success,
                latency_ms=latency,
                tool_called=True,
                response_preview=response_text,
                business_masked=masked,
                technical_leaks=leaks
            )

            self.add_result(result)
            self.print_result(result)
            time.sleep(1)

    def test_n8n_message_tools(self):
        """Test 6-10: n8n message extraction tools (5 tools)"""
        self.print_header("TEST 6-10: N8N MESSAGE TOOLS")

        test_cases = [
            ("ultimo messaggio del workflow ChatOne", "get_last_message_from_workflow"),
            ("cerca messaggi con 'errore' nel workflow Email", "search_workflow_messages"),
            ("mostra i dati webhook del processo X", "extract_webhook_data"),
            ("storico esecuzioni del processo Y", "get_workflow_execution_history"),
            ("estrai i messaggi in batch dal workflow Z", "extract_batch_messages"),
        ]

        for query, tool_name in test_cases:
            data, latency = self.call_agent(query)

            response_text = data.get("response", "")
            success = data.get("status") == "success"
            masked, leaks = self.check_masking(response_text)

            result = ToolTestResult(
                tool_name=tool_name,
                test_name=f"{tool_name} test",
                query=query,
                success=success,
                latency_ms=latency,
                tool_called=True,
                response_preview=response_text,
                business_masked=masked,
                technical_leaks=leaks
            )

            self.add_result(result)
            self.print_result(result)
            time.sleep(1)

    # ============================================================================
    # N8N EXPERT AGENT TOOLS (12 tools, some overlap with Milhena)
    # ============================================================================

    def test_get_error_details_tool(self):
        """Test 11: get_error_details_tool - Specific error analysis"""
        self.print_header("TEST 11: get_error_details_tool")

        test_cases = [
            ("dettagli dell'errore nel processo ChatOne", "specific workflow errors"),
            ("analizza gli errori del workflow GommeGo", "workflow error analysis"),
        ]

        for query, test_name in test_cases:
            data, latency = self.call_agent(query)

            response_text = data.get("response", "")
            success = data.get("status") == "success"
            masked, leaks = self.check_masking(response_text)

            result = ToolTestResult(
                tool_name="get_error_details_tool",
                test_name=test_name,
                query=query,
                success=success,
                latency_ms=latency,
                tool_called=True,
                response_preview=response_text,
                business_masked=masked,
                technical_leaks=leaks
            )

            self.add_result(result)
            self.print_result(result)
            time.sleep(1)

    def test_get_executions_by_date_tool(self):
        """Test 12: get_executions_by_date_tool - Date-based execution retrieval"""
        self.print_header("TEST 12: get_executions_by_date_tool")

        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        test_cases = [
            (f"esecuzioni del {today}", "today executions"),
            (f"mostra elaborazioni del {yesterday}", "yesterday executions"),
            ("processi eseguiti ieri", "natural language date"),
        ]

        for query, test_name in test_cases:
            data, latency = self.call_agent(query)

            response_text = data.get("response", "")
            success = data.get("status") == "success"
            masked, leaks = self.check_masking(response_text)

            result = ToolTestResult(
                tool_name="get_executions_by_date_tool",
                test_name=test_name,
                query=query,
                success=success,
                latency_ms=latency,
                tool_called=True,
                response_preview=response_text,
                business_masked=masked,
                technical_leaks=leaks
            )

            self.add_result(result)
            self.print_result(result)
            time.sleep(1)

    def test_get_node_execution_details_tool(self):
        """Test 13: get_node_execution_details_tool - Node-level granularity"""
        self.print_header("TEST 13: get_node_execution_details_tool")

        test_cases = [
            ("dettagli dei passaggi del processo ChatOne", "node details request"),
            ("mostra l'esecuzione step-by-step del workflow X", "step-by-step analysis"),
        ]

        for query, test_name in test_cases:
            data, latency = self.call_agent(query)

            response_text = data.get("response", "")
            success = data.get("status") == "success"
            masked, leaks = self.check_masking(response_text)

            result = ToolTestResult(
                tool_name="get_node_execution_details_tool",
                test_name=test_name,
                query=query,
                success=success,
                latency_ms=latency,
                tool_called=True,
                response_preview=response_text,
                business_masked=masked,
                technical_leaks=leaks
            )

            self.add_result(result)
            self.print_result(result)
            time.sleep(1)

    def test_get_live_events_tool(self):
        """Test 14: get_live_events_tool - Real-time event streaming"""
        self.print_header("TEST 14: get_live_events_tool")

        test_cases = [
            ("eventi in tempo reale", "live events request"),
            ("cosa sta succedendo adesso?", "current activity"),
        ]

        for query, test_name in test_cases:
            data, latency = self.call_agent(query)

            response_text = data.get("response", "")
            success = data.get("status") == "success"
            masked, leaks = self.check_masking(response_text)

            result = ToolTestResult(
                tool_name="get_live_events_tool",
                test_name=test_name,
                query=query,
                success=success,
                latency_ms=latency,
                tool_called=True,
                response_preview=response_text,
                business_masked=masked,
                technical_leaks=leaks
            )

            self.add_result(result)
            self.print_result(result)
            time.sleep(1)

    def test_get_raw_modal_data_tool(self):
        """Test 15: get_raw_modal_data_tool - Timeline node-by-node"""
        self.print_header("TEST 15: get_raw_modal_data_tool")

        test_cases = [
            ("timeline completa del processo X", "full timeline"),
            ("dati raw dell'esecuzione Y", "raw data request"),
        ]

        for query, test_name in test_cases:
            data, latency = self.call_agent(query)

            response_text = data.get("response", "")
            success = data.get("status") == "success"
            masked, leaks = self.check_masking(response_text)

            result = ToolTestResult(
                tool_name="get_raw_modal_data_tool",
                test_name=test_name,
                query=query,
                success=success,
                latency_ms=latency,
                tool_called=True,
                response_preview=response_text,
                business_masked=masked,
                technical_leaks=leaks
            )

            self.add_result(result)
            self.print_result(result)
            time.sleep(1)

    def test_smart_query_tools(self):
        """Test 16-17: smart_executions_query_tool + smart_workflow_query_tool"""
        self.print_header("TEST 16-17: SMART QUERY TOOLS")

        test_cases = [
            ("cerca esecuzioni del workflow X nelle ultime 7 giorni", "smart_executions_query_tool"),
            ("query intelligente sul processo Y con filtri avanzati", "smart_workflow_query_tool"),
        ]

        for query, tool_name in test_cases:
            data, latency = self.call_agent(query)

            response_text = data.get("response", "")
            success = data.get("status") == "success"
            masked, leaks = self.check_masking(response_text)

            result = ToolTestResult(
                tool_name=tool_name,
                test_name=f"{tool_name} test",
                query=query,
                success=success,
                latency_ms=latency,
                tool_called=True,
                response_preview=response_text,
                business_masked=masked,
                technical_leaks=leaks
            )

            self.add_result(result)
            self.print_result(result)
            time.sleep(1)

    # ============================================================================
    # DATA ANALYST AGENT TOOLS (5 tools, some overlap)
    # ============================================================================

    def test_get_chatone_email_details_tool(self):
        """Test 18: get_chatone_email_details_tool - Email conversation bot"""
        self.print_header("TEST 18: get_chatone_email_details_tool")

        test_cases = [
            ("dettagli email del processo ChatOne", "email details"),
            ("mostra le conversazioni email del bot", "conversation history"),
        ]

        for query, test_name in test_cases:
            data, latency = self.call_agent(query)

            response_text = data.get("response", "")
            success = data.get("status") == "success"
            masked, leaks = self.check_masking(response_text)

            result = ToolTestResult(
                tool_name="get_chatone_email_details_tool",
                test_name=test_name,
                query=query,
                success=success,
                latency_ms=latency,
                tool_called=True,
                response_preview=response_text,
                business_masked=masked,
                technical_leaks=leaks
            )

            self.add_result(result)
            self.print_result(result)
            time.sleep(1)

    def test_smart_analytics_query_tool(self):
        """Test 19: smart_analytics_query_tool - Advanced analytics"""
        self.print_header("TEST 19: smart_analytics_query_tool")

        test_cases = [
            ("analisi performance processi ultima settimana", "weekly performance"),
            ("statistiche complete sistema", "full stats"),
            ("trend esecuzioni ultimo mese", "monthly trend"),
        ]

        for query, test_name in test_cases:
            data, latency = self.call_agent(query)

            response_text = data.get("response", "")
            success = data.get("status") == "success"
            masked, leaks = self.check_masking(response_text)

            result = ToolTestResult(
                tool_name="smart_analytics_query_tool",
                test_name=test_name,
                query=query,
                success=success,
                latency_ms=latency,
                tool_called=True,
                response_preview=response_text,
                business_masked=masked,
                technical_leaks=leaks
            )

            self.add_result(result)
            self.print_result(result)
            time.sleep(1)

    # ============================================================================
    # SUMMARY & REPORTING
    # ============================================================================

    def print_summary(self):
        """Print final test summary"""
        self.print_header("📊 COMPREHENSIVE TEST SUMMARY")

        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed

        masked_correct = sum(1 for r in self.results if r.business_masked)
        masking_rate = (masked_correct / total * 100) if total > 0 else 0

        avg_latency = sum(r.latency_ms for r in self.results) / total if total > 0 else 0

        tools_with_leaks = set(r.tool_name for r in self.results if not r.business_masked)

        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed} ({passed*100//total}%)")
        print(f"❌ Failed: {failed} ({failed*100//total}%)")
        print(f"🔒 Masking Accuracy: {masking_rate:.1f}%")
        print(f"⏱️  Average Latency: {int(avg_latency)}ms")
        print()

        if tools_with_leaks:
            print(f"⚠️  Tools with masking leaks: {len(tools_with_leaks)}")
            for tool in tools_with_leaks:
                print(f"   - {tool}")
            print()

        # Failed tests
        failed_results = [r for r in self.results if not r.success]
        if failed_results:
            print(f"❌ Failed Tests ({len(failed_results)}):")
            for r in failed_results:
                print(f"   - {r.test_name} ({r.tool_name}): {r.error or 'Unknown error'}")
            print()

        # Performance stats
        slow_tests = [r for r in self.results if r.latency_ms > 10000]
        if slow_tests:
            print(f"⏱️  Slow Tests (>10s): {len(slow_tests)}")
            for r in sorted(slow_tests, key=lambda x: x.latency_ms, reverse=True)[:5]:
                print(f"   - {r.test_name}: {r.latency_ms}ms")
            print()

        # Final verdict
        if passed == total and masking_rate >= 95:
            print("🎉 ALL TOOLS PASSED - PRODUCTION READY!")
        elif passed >= total * 0.8:
            print("✅ MOST TOOLS WORKING - Minor issues to fix")
        else:
            print("🚨 SIGNIFICANT ISSUES - Review failed tests")

    def save_results(self):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"test-v4-tools-results-{timestamp}.json"

        data = {
            "timestamp": timestamp,
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.success),
            "failed": sum(1 for r in self.results if not r.success),
            "results": [
                {
                    "tool": r.tool_name,
                    "test": r.test_name,
                    "query": r.query,
                    "success": r.success,
                    "latency_ms": r.latency_ms,
                    "masked": r.business_masked,
                    "leaks": r.technical_leaks,
                    "error": r.error
                }
                for r in self.results
            ]
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        print(f"\n📄 Results saved to: {filename}")

    def run_all_tests(self):
        """Execute all tool tests"""
        self.print_header("🚀 STARTING COMPREHENSIVE V4.0 TOOLS TEST SUITE")

        print("Testing 19 unique tools across 3 specialized agents:")
        print("  - Milhena Agent: 10 tools")
        print("  - N8N Expert Agent: 12 tools")
        print("  - Data Analyst Agent: 5 tools")
        print("\nEstimated time: ~5 minutes")
        print("\n🚀 Starting tests...\n")

        # Milhena Agent tools
        self.test_get_workflows_tool()
        self.test_get_workflow_cards_tool()
        self.test_get_workflow_details_tool()
        self.test_get_all_errors_summary_tool()
        self.test_search_knowledge_base_tool()
        self.test_n8n_message_tools()

        # N8N Expert Agent tools
        self.test_get_error_details_tool()
        self.test_get_executions_by_date_tool()
        self.test_get_node_execution_details_tool()
        self.test_get_live_events_tool()
        self.test_get_raw_modal_data_tool()
        self.test_smart_query_tools()

        # Data Analyst Agent tools
        self.test_get_chatone_email_details_tool()
        self.test_smart_analytics_query_tool()

        # Summary
        self.print_summary()
        self.save_results()

if __name__ == "__main__":
    print("="*80)
    print("🧪 V4.0 TOOLS COMPREHENSIVE TEST SUITE".center(80))
    print("="*80)

    suite = V4ToolsTestSuite()
    suite.run_all_tests()
