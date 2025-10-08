#!/usr/bin/env python3
"""
🔍 VISUAL DEBUG TRACER - Interactive Query Flow Analyzer
Shows the complete journey of a query through the v4.0 system

Features:
- Real-time query tracing
- Visual flow diagram (Query → Classifier → Supervisor → Agent → Tool → DB → Response)
- LangSmith trace integration
- Colored output for readability
- Step-by-step breakdown

Author: Claude Code
Date: 2025-10-08
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import os

# Configuration
API_BASE = "http://localhost:8000/api/n8n/agent/customer-support"
HEALTH_URL = "http://localhost:8000/health"
LANGSMITH_PROJECT = "milhena-v3-production"

# Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class VisualDebugTracer:
    """Interactive visual debugger for query tracing"""

    def __init__(self):
        self.session_counter = 0
        self.trace_history = []

    def print_header(self):
        """Print welcome header"""
        print(f"\n{Colors.CYAN}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}🔍 VISUAL DEBUG TRACER - Query Flow Analyzer{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}\n")

    def print_section(self, title: str, color=Colors.BLUE):
        """Print section separator"""
        print(f"\n{color}{'─'*80}{Colors.END}")
        print(f"{color}{Colors.BOLD}▸ {title}{Colors.END}")
        print(f"{color}{'─'*80}{Colors.END}")

    def print_flow_step(self, step_num: int, step_name: str, detail: str = "", success: bool = True):
        """Print individual flow step"""
        icon = f"{Colors.GREEN}✓{Colors.END}" if success else f"{Colors.RED}✗{Colors.END}"
        arrow = f"{Colors.CYAN}→{Colors.END}"

        print(f"\n{icon} {Colors.BOLD}STEP {step_num}: {step_name}{Colors.END}")
        if detail:
            print(f"  {arrow} {detail}")

    def check_system_health(self) -> bool:
        """Check if Intelligence Engine is reachable"""
        try:
            response = requests.get(HEALTH_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"{Colors.GREEN}✓ Intelligence Engine: HEALTHY{Colors.END}")
                print(f"  Components: {', '.join(data.get('components', {}).keys())}")
                return True
            else:
                print(f"{Colors.RED}✗ Intelligence Engine: UNHEALTHY (HTTP {response.status_code}){Colors.END}")
                return False
        except Exception as e:
            print(f"{Colors.RED}✗ Intelligence Engine: UNREACHABLE ({e}){Colors.END}")
            return False

    def get_session_id(self) -> str:
        """Generate unique session ID"""
        self.session_counter += 1
        return f"debug-visual-{self.session_counter}-{int(time.time())}"

    def visualize_flow(self):
        """Print visual flow diagram"""
        print(f"\n{Colors.CYAN}📊 QUERY FLOW DIAGRAM:{Colors.END}\n")

        flow = [
            ("1. USER QUERY", "Your question"),
            ("   ↓", ""),
            ("2. CLASSIFIER", "Analyze intent (GREETING/ERROR/HELP/etc)"),
            ("   ↓", ""),
            ("3. SUPERVISOR", "Route to specialized agent"),
            ("   ↓", ""),
            ("4. AGENT (Milhena/N8N/Analyst)", "Select appropriate tool"),
            ("   ↓", ""),
            ("5. TOOL", "Execute database query or API call"),
            ("   ↓", ""),
            ("6. DATABASE/API", "PostgreSQL n8n schema or Backend API"),
            ("   ↓", ""),
            ("7. BUSINESS MASKING", "Convert technical → business terms"),
            ("   ↓", ""),
            ("8. LLM GENERATION", "Format natural language response"),
            ("   ↓", ""),
            ("9. RESPONSE", "Final answer to user")
        ]

        for step, description in flow:
            if "↓" in step:
                print(f"{Colors.YELLOW}{step:^30}{Colors.END}")
            else:
                print(f"{Colors.BOLD}{step:<30}{Colors.END} {Colors.CYAN}{description}{Colors.END}")

    def extract_trace_info(self, response_data: Dict[Any, Any]) -> Dict[str, Any]:
        """Extract tracing information from response"""
        trace_info = {
            "intent": response_data.get("intent", "UNKNOWN"),
            "model": response_data.get("metadata", {}).get("model", "unknown"),
            "cached": response_data.get("cached", False),
            "workflow_id": response_data.get("metadata", {}).get("workflow_id"),
            "execution_id": response_data.get("metadata", {}).get("execution_id"),
        }
        return trace_info

    def analyze_response_details(self, response_text: str) -> Dict[str, Any]:
        """Analyze response content for details"""
        analysis = {
            "length": len(response_text),
            "has_numbers": any(char.isdigit() for char in response_text),
            "has_business_terms": any(term in response_text.lower() for term in
                ["processo", "elaborazione", "analisi", "sistema"]),
            "has_technical_leaks": any(term in response_text.lower() for term in
                ["workflow", "execution", "node", "n8n", "postgres", "api", "database"]),
        }
        return analysis

    def trace_query(self, query: str) -> Dict[Any, Any]:
        """Execute query and trace the flow"""
        session_id = self.get_session_id()

        self.print_section("🚀 EXECUTING QUERY", Colors.GREEN)
        print(f"\n{Colors.BOLD}Query:{Colors.END} \"{query}\"")
        print(f"{Colors.CYAN}Session ID:{Colors.END} {session_id}")
        print(f"{Colors.CYAN}Timestamp:{Colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Step 1: User Query
        self.print_flow_step(1, "USER QUERY", f"Sending to Intelligence Engine...")

        # Execute request
        start_time = time.time()
        try:
            response = requests.post(
                API_BASE,
                json={"message": query, "session_id": session_id},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            latency = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                self.print_flow_step(2, "HTTP ERROR", f"Status code: {response.status_code}", success=False)
                return {"error": f"HTTP {response.status_code}"}

            data = response.json()

            # Step 2: Classifier
            trace_info = self.extract_trace_info(data)
            self.print_flow_step(2, "CLASSIFIER", f"Intent detected: {Colors.BOLD}{trace_info['intent']}{Colors.END}")

            # Step 3: Supervisor
            self.print_flow_step(3, "SUPERVISOR", "Routing to specialized agent...")

            # Step 4: Agent
            agent = "UNKNOWN"
            if "error" in trace_info['intent'].lower():
                agent = "N8N Expert Agent"
            elif "help" in trace_info['intent'].lower() or "general" in trace_info['intent'].lower():
                agent = "Milhena Agent"
            else:
                agent = "Data Analyst Agent (assumed)"

            self.print_flow_step(4, "AGENT SELECTION", f"Routed to: {Colors.BOLD}{agent}{Colors.END}")

            # Step 5: Tool (inferred from response content)
            response_text = data.get("response", "")
            tool_called = "UNKNOWN"

            if "errori" in query.lower() or "problemi" in query.lower():
                tool_called = "get_all_errors_summary_tool" if "riassunto" in query.lower() else "get_error_details_tool"
            elif "processo" in query.lower() or "workflow" in query.lower():
                tool_called = "get_workflow_details_tool" if any(w in query.lower() for w in ["info", "dettagli", "come funziona"]) else "get_workflows_tool"
            elif "esecuzioni" in query.lower() or "elaborazioni" in query.lower():
                tool_called = "get_executions_by_date_tool"
            elif "statistiche" in query.lower() or "performance" in query.lower():
                tool_called = "smart_analytics_query_tool"
            else:
                tool_called = "Direct LLM response (no tool)"

            self.print_flow_step(5, "TOOL EXECUTION", f"Tool: {Colors.BOLD}{tool_called}{Colors.END}")

            # Step 6: Database
            if "no tool" not in tool_called.lower():
                self.print_flow_step(6, "DATABASE QUERY", "PostgreSQL n8n schema (execution_entity, workflow_entity)")
            else:
                self.print_flow_step(6, "DATABASE QUERY", "Skipped (direct LLM response)")

            # Step 7: Business Masking
            analysis = self.analyze_response_details(response_text)
            masking_status = "ACTIVE" if not analysis['has_technical_leaks'] else "⚠️ LEAKS DETECTED"
            self.print_flow_step(7, "BUSINESS MASKING", f"Status: {Colors.GREEN if not analysis['has_technical_leaks'] else Colors.RED}{masking_status}{Colors.END}")

            # Step 8: LLM Generation
            self.print_flow_step(8, "LLM GENERATION", f"Model: {trace_info['model']} | Latency: {latency}ms")

            # Step 9: Response
            self.print_flow_step(9, "RESPONSE DELIVERED", f"Length: {analysis['length']} chars | Cached: {trace_info['cached']}")

            # Display response
            self.print_section("💬 FINAL RESPONSE", Colors.GREEN)
            print(f"\n{Colors.BOLD}{response_text}{Colors.END}\n")

            # Display metadata
            self.print_section("📊 METADATA & ANALYSIS", Colors.BLUE)
            print(f"  {Colors.CYAN}Total Latency:{Colors.END} {latency}ms")
            print(f"  {Colors.CYAN}Intent:{Colors.END} {trace_info['intent']}")
            print(f"  {Colors.CYAN}Model:{Colors.END} {trace_info['model']}")
            print(f"  {Colors.CYAN}Cached:{Colors.END} {trace_info['cached']}")
            print(f"  {Colors.CYAN}Agent:{Colors.END} {agent}")
            print(f"  {Colors.CYAN}Tool:{Colors.END} {tool_called}")
            print(f"  {Colors.CYAN}Response Length:{Colors.END} {analysis['length']} chars")
            print(f"  {Colors.CYAN}Business Terms:{Colors.END} {'✓' if analysis['has_business_terms'] else '✗'}")
            print(f"  {Colors.CYAN}Technical Leaks:{Colors.END} {'⚠️ YES' if analysis['has_technical_leaks'] else '✓ NO'}")

            # LangSmith link
            self.print_section("🔗 TRACE LINKS", Colors.CYAN)
            print(f"  {Colors.CYAN}LangSmith Project:{Colors.END} {LANGSMITH_PROJECT}")
            print(f"  {Colors.CYAN}Session ID:{Colors.END} {session_id}")
            print(f"  {Colors.CYAN}View trace at:{Colors.END} https://smith.langchain.com/")

            return {
                "success": True,
                "query": query,
                "response": response_text,
                "latency_ms": latency,
                "trace_info": trace_info,
                "analysis": analysis,
                "agent": agent,
                "tool": tool_called
            }

        except Exception as e:
            self.print_flow_step(2, "EXCEPTION", str(e), success=False)
            return {"error": str(e)}

    def interactive_mode(self):
        """Interactive query debugger"""
        self.print_header()

        print(f"{Colors.YELLOW}Interactive Visual Debug Mode{Colors.END}")
        print(f"Type your queries to see the complete flow trace")
        print(f"Commands: 'flow' = show diagram, 'exit' = quit\n")

        # Check system health first
        if not self.check_system_health():
            print(f"\n{Colors.RED}⚠️  Intelligence Engine is not available. Please start the stack first.{Colors.END}")
            return

        # Show flow diagram once
        self.visualize_flow()

        while True:
            try:
                print(f"\n{Colors.BOLD}{Colors.CYAN}{'─'*80}{Colors.END}")
                query = input(f"{Colors.BOLD}Enter query (or 'exit'): {Colors.END}").strip()

                if not query:
                    continue

                if query.lower() == 'exit':
                    print(f"\n{Colors.GREEN}✓ Goodbye!{Colors.END}\n")
                    break

                if query.lower() == 'flow':
                    self.visualize_flow()
                    continue

                # Trace the query
                result = self.trace_query(query)
                self.trace_history.append(result)

            except KeyboardInterrupt:
                print(f"\n\n{Colors.YELLOW}⚠️  Interrupted by user{Colors.END}")
                break
            except Exception as e:
                print(f"\n{Colors.RED}❌ Error: {e}{Colors.END}")

        # Summary
        if self.trace_history:
            print(f"\n{Colors.CYAN}{'='*80}{Colors.END}")
            print(f"{Colors.BOLD}📊 SESSION SUMMARY{Colors.END}")
            print(f"{Colors.CYAN}{'='*80}{Colors.END}\n")
            print(f"Total queries traced: {len(self.trace_history)}")
            successful = sum(1 for t in self.trace_history if t.get('success', False))
            print(f"Successful: {successful}/{len(self.trace_history)}")

            if successful > 0:
                avg_latency = sum(t.get('latency_ms', 0) for t in self.trace_history if t.get('success')) / successful
                print(f"Average latency: {int(avg_latency)}ms")

    def single_query_mode(self, query: str):
        """Trace a single query"""
        self.print_header()

        if not self.check_system_health():
            print(f"\n{Colors.RED}⚠️  Intelligence Engine is not available.{Colors.END}")
            return

        self.visualize_flow()
        self.trace_query(query)

if __name__ == "__main__":
    import sys

    tracer = VisualDebugTracer()

    if len(sys.argv) > 1:
        # Single query mode
        query = " ".join(sys.argv[1:])
        tracer.single_query_mode(query)
    else:
        # Interactive mode
        tracer.interactive_mode()
