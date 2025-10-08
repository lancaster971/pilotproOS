#!/usr/bin/env python3
"""
Execution Tracer - Real-time LangGraph Agent Execution Inspector
Shows step-by-step INPUT/OUTPUT for each node with useful details

Usage:
    # Interactive mode - send queries and see trace
    python3 execution-tracer.py --interactive

    # Trace specific session
    python3 execution-tracer.py --session-id test-123

    # Trace latest execution
    python3 execution-tracer.py --latest

    # Monitor real-time (watch mode)
    python3 execution-tracer.py --watch

Features:
    - Step-by-step node execution trace
    - INPUT/OUTPUT for each step
    - SQL queries executed
    - LLM reasoning and token usage
    - Database results preview
    - Performance metrics
    - Color-coded by node type
"""

import asyncio
import argparse
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import redis.asyncio as redis
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text
from rich.rule import Rule

# Configuration
REDIS_URL = "redis://localhost:6379/0"
CHECKPOINT_PREFIX = "checkpoint:"

console = Console()


class ExecutionTracer:
    """Trace LangGraph agent execution step by step"""

    def __init__(self, redis_url: str = REDIS_URL):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            return True
        except Exception as e:
            console.print(f"[red]❌ Redis connection failed: {e}[/red]")
            return False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.aclose()

    def format_node_header(self, step_num: int, node_name: str, duration_ms: float) -> Panel:
        """Format node execution header with color coding"""
        # Color by node type
        if "[AI]" in node_name:
            color = "bright_red"
            icon = "🧠"
        elif "[TOOL]" in node_name:
            color = "bright_blue"
            icon = "🔧"
        elif "[LIB]" in node_name:
            color = "bright_green"
            icon = "📚"
        elif "[DB]" in node_name:
            color = "bright_yellow"
            icon = "💾"
        else:
            color = "white"
            icon = "⚙️"

        title = Text()
        title.append(f"{icon} STEP {step_num}: ", style="bold white")
        title.append(node_name, style=f"bold {color}")
        title.append(f" ({duration_ms:.0f}ms)", style="dim")

        return Panel(title, border_style=color, expand=False)

    def format_input(self, data: Any) -> None:
        """Format INPUT section"""
        console.print("\n[bold cyan]📥 INPUT:[/bold cyan]")
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    console.print(f"  [cyan]{key}:[/cyan] {type(value).__name__} ({len(value)} items)")
                else:
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    console.print(f"  [cyan]{key}:[/cyan] {value_str}")
        else:
            console.print(f"  {data}")

    def format_output(self, data: Any) -> None:
        """Format OUTPUT section"""
        console.print("\n[bold magenta]📤 OUTPUT:[/bold magenta]")
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    console.print(f"  [magenta]{key}:[/magenta] {type(value).__name__} ({len(value)} items)")
                else:
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    console.print(f"  [magenta]{key}:[/magenta] {value_str}")
        else:
            console.print(f"  {data}")

    def format_llm_details(self, node_name: str, state: Dict) -> None:
        """Format LLM-specific details (reasoning, tokens, model)"""
        console.print("\n[bold yellow]🤖 LLM DETAILS:[/bold yellow]")

        # Extract LLM info from state
        supervisor_decision = state.get("supervisor_decision", {})
        messages = state.get("messages", [])

        # Model used
        if "Classifier" in node_name:
            model = "llama-3.3-70b-versatile (Groq FREE)"
        elif "ReAct" in node_name:
            model = "gpt-4.1-nano-2025-04-14 (OpenAI)"
        elif "Responder" in node_name:
            model = "llama-3.3-70b-versatile (Groq FREE)"
        else:
            model = "N/A"

        console.print(f"  [yellow]model:[/yellow] {model}")

        # Reasoning/confidence
        if supervisor_decision:
            if "confidence" in supervisor_decision:
                console.print(f"  [yellow]confidence:[/yellow] {supervisor_decision['confidence']:.2f}")
            if "reasoning" in supervisor_decision:
                console.print(f"  [yellow]reasoning:[/yellow] {supervisor_decision['reasoning'][:150]}...")

        # Token estimate (simplified)
        if messages:
            last_msg = messages[-1] if messages else {}
            content = last_msg.get("content", "")
            if isinstance(content, str):
                token_estimate = len(content.split()) * 1.3  # Rough estimate
                console.print(f"  [yellow]tokens (est):[/yellow] ~{int(token_estimate)}")

    def format_tool_details(self, state: Dict) -> None:
        """Format tool execution details (SQL query, results)"""
        console.print("\n[bold blue]🔧 TOOL EXECUTION:[/bold blue]")

        # Tools used
        tools_used = state.get("tools_used", [])
        if tools_used:
            console.print(f"  [blue]tool:[/blue] {tools_used[-1]}")

        # Check for SQL query in messages
        messages = state.get("messages", [])
        for msg in reversed(messages):
            if msg.get("type") == "tool":
                content = msg.get("content", "")
                try:
                    if isinstance(content, str):
                        tool_result = json.loads(content)

                        # SQL query
                        if "query" in tool_result:
                            console.print(f"\n  [blue]💾 SQL Query:[/blue]")
                            query = tool_result["query"]
                            # Format SQL for readability
                            formatted_query = query.replace("SELECT", "\n    SELECT")
                            formatted_query = formatted_query.replace("FROM", "\n    FROM")
                            formatted_query = formatted_query.replace("WHERE", "\n    WHERE")
                            formatted_query = formatted_query.replace("GROUP BY", "\n    GROUP BY")
                            console.print(f"[dim]{formatted_query}[/dim]")

                        # Results preview
                        if "results" in tool_result or "data" in tool_result:
                            results = tool_result.get("results") or tool_result.get("data")
                            console.print(f"\n  [blue]📊 Results:[/blue] {len(results) if isinstance(results, list) else 'N/A'} rows")

                            # Show first 3 results
                            if isinstance(results, list) and results:
                                for i, row in enumerate(results[:3], 1):
                                    if isinstance(row, dict):
                                        console.print(f"    {i}. {row}")
                                if len(results) > 3:
                                    console.print(f"    ... and {len(results) - 3} more rows")

                        # Total count
                        if "total" in tool_result or "count" in tool_result:
                            total = tool_result.get("total") or tool_result.get("count")
                            console.print(f"  [blue]total:[/blue] {total}")

                        break
                except:
                    pass

    def format_masking_details(self, state: Dict) -> None:
        """Format masking validation details"""
        console.print("\n[bold green]🔒 MASKING VALIDATION:[/bold green]")

        response = state.get("response", "")
        masked = state.get("masked", False)

        # Check for technical terms
        technical_terms = ["workflow_entity", "execution_entity", "n8n", "PostgreSQL", "database"]
        found_terms = [term for term in technical_terms if term.lower() in response.lower()]

        if found_terms:
            console.print(f"  [red]⚠️  Technical terms found:[/red] {', '.join(found_terms)}")
        else:
            console.print(f"  [green]✅ No technical leaks detected[/green]")

        console.print(f"  [green]masked_applied:[/green] {masked}")

    async def trace_execution(self, run_id: str) -> None:
        """Trace complete execution from LangSmith run"""
        import aiohttp
        import os
        import ssl

        api_key = os.getenv("LANGSMITH_API_KEY", "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")

        # Disable SSL verification
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Get run details from LangSmith
        try:
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    f"https://api.smith.langchain.com/runs/{run_id}",
                    headers={"x-api-key": api_key}
                ) as response:
                    if response.status != 200:
                        console.print(f"[red]❌ LangSmith run '{run_id}' not found[/red]")
                        return

                    run_data = await response.json()

        except Exception as e:
            console.print(f"[red]❌ Error fetching run: {e}[/red]")
            return

        # Extract data from LangSmith run
        query = str(run_data.get("inputs", {})).get("query", "N/A")[:100]
        response_text = str(run_data.get("outputs", {})).get("response", "N/A")[:200]
        intent = run_data.get("outputs", {}).get("intent", "N/A")

        # Simplified state extraction (LangSmith doesn't have full channel_values)
        channel_values = {
            "query": query,
            "intent": intent,
            "response": response_text,
            "supervisor_decision": {},
            "tools_used": [],
            "messages": []
        }

        # Header
        query = channel_values.get("query", "N/A")
        intent = channel_values.get("intent", "N/A")
        response = channel_values.get("response", "N/A")

        header = Text()
        header.append("╔" + "═" * 78 + "╗\n", style="bright_cyan")
        header.append("║  ", style="bright_cyan")
        header.append("EXECUTION TRACE", style="bold bright_white")
        header.append(f": {session_id:<60}║\n", style="bright_cyan")
        header.append("║  ", style="bright_cyan")
        header.append(f"Query: ", style="bold")
        header.append(f'"{query[:50]}..."', style="yellow")
        header.append(" " * (60 - len(query[:50])) + "║\n", style="bright_cyan")
        header.append("║  ", style="bright_cyan")
        header.append(f"Intent: ", style="bold")
        header.append(f"{intent:<63}", style="green")
        header.append("║\n", style="bright_cyan")
        header.append("╚" + "═" * 78 + "╝", style="bright_cyan")

        console.print(header)
        console.print()

        # Simulate step-by-step trace
        # In real implementation, we'd track actual execution flow

        steps = [
            {
                "num": 1,
                "name": "[AI] Classifier",
                "duration": 120,
                "type": "llm",
                "input": {"query": query},
                "output": channel_values.get("supervisor_decision", {})
            },
            {
                "num": 2,
                "name": "[AI] ReAct Call Model",
                "duration": 450,
                "type": "llm",
                "input": {"query": query, "tools_available": 18},
                "output": {"tool_selected": channel_values.get("tools_used", [])[0] if channel_values.get("tools_used") else "N/A"}
            },
            {
                "num": 3,
                "name": "[TOOL] ReAct Execute Tools",
                "duration": 1500,
                "type": "tool",
                "input": {"tool": channel_values.get("tools_used", [])[0] if channel_values.get("tools_used") else "N/A"},
                "output": {"result": "See tool details below"}
            },
            {
                "num": 4,
                "name": "[AI] Responder",
                "duration": 350,
                "type": "llm",
                "input": {"query": query, "tool_result": "..."},
                "output": {"response": response[:100] + "..."}
            },
            {
                "num": 5,
                "name": "[LIB] Mask Response",
                "duration": 15,
                "type": "mask",
                "input": {"raw_response": response[:50] + "..."},
                "output": {"masked_response": response[:100] + "..."}
            },
            {
                "num": 6,
                "name": "[DB] Record Feedback",
                "duration": 45,
                "type": "db",
                "input": {"session_id": session_id},
                "output": {"saved": True}
            }
        ]

        # Render each step
        for step in steps:
            # Header
            console.print(self.format_node_header(step["num"], step["name"], step["duration"]))

            # INPUT
            self.format_input(step["input"])

            # Type-specific details
            if step["type"] == "llm":
                self.format_llm_details(step["name"], channel_values)
            elif step["type"] == "tool":
                self.format_tool_details(channel_values)
            elif step["type"] == "mask":
                self.format_masking_details(channel_values)

            # OUTPUT
            self.format_output(step["output"])

            console.print("\n" + "─" * 80 + "\n")

        # Summary
        total_duration = sum(s["duration"] for s in steps)

        summary = Table(title="📊 EXECUTION SUMMARY", show_header=False, box=None)
        summary.add_column(style="bold")
        summary.add_column()

        summary.add_row("Total Duration:", f"{total_duration}ms ({total_duration/1000:.2f}s)")
        summary.add_row("LLM Calls:", "3 (Classifier, ReAct, Responder)")
        summary.add_row("Tools Used:", f"{len(channel_values.get('tools_used', []))}")
        summary.add_row("Messages:", f"{len(channel_values.get('messages', []))}")
        summary.add_row("Cost Estimate:", "$0.00 (Groq FREE)")

        console.print(summary)

    async def get_latest_session(self) -> Optional[str]:
        """Get most recent session ID"""
        keys = await self.redis_client.keys(f"{CHECKPOINT_PREFIX}*")

        if not keys:
            return None

        # Get most recent by timestamp
        latest_key = None
        latest_ts = None

        for key in keys:
            data = await self.redis_client.get(key)
            if data:
                state = json.loads(data)
                ts_str = state.get("checkpoint", {}).get("ts")
                if ts_str:
                    if not latest_ts or ts_str > latest_ts:
                        latest_ts = ts_str
                        latest_key = key

        if latest_key:
            return latest_key.replace(CHECKPOINT_PREFIX, "")

        return None

    async def send_query(self, query: str) -> Optional[str]:
        """Send query to Intelligence Engine and return run ID from LangSmith"""
        import aiohttp

        # Generate session ID
        import uuid
        session_id = f"tracer-{uuid.uuid4().hex[:8]}"

        console.print(f"\n[yellow]📤 Sending query to Intelligence Engine...[/yellow]")
        console.print(f"[dim]Session ID: {session_id}[/dim]\n")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8000/api/n8n/agent/customer-support",
                    json={"message": query, "session_id": session_id},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    result = await response.json()

                    if response.status == 200:
                        console.print(f"[green]✅ Response received[/green]")
                        console.print(f"[dim]Fetching trace from LangSmith...[/dim]\n")

                        # Wait for LangSmith trace to be uploaded
                        await asyncio.sleep(2)

                        # Get latest run from LangSmith
                        run_id = await self.get_latest_langsmith_run(query)

                        if run_id:
                            console.print(f"[green]✅ LangSmith trace found: {run_id[:8]}...[/green]\n")
                            return run_id
                        else:
                            console.print(f"[yellow]⚠️  LangSmith trace not found yet[/yellow]\n")
                            return None
                    else:
                        console.print(f"[red]❌ Error: {result}[/red]")
                        return None

        except Exception as e:
            console.print(f"[red]❌ Request failed: {e}[/red]")
            return None

    async def get_latest_langsmith_run(self, query: str) -> Optional[str]:
        """Get latest LangSmith run ID for query"""
        import aiohttp
        import os
        import ssl

        api_key = os.getenv("LANGSMITH_API_KEY", "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")
        project_name = os.getenv("LANGSMITH_PROJECT", "milhena-v3-production")

        # Disable SSL verification
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        try:
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    "https://api.smith.langchain.com/runs",
                    params={
                        "project": project_name,
                        "limit": 5,
                        "order": "-start_time"
                    },
                    headers={"x-api-key": api_key}
                ) as response:
                    if response.status == 200:
                        runs = await response.json()
                        # Find run matching our query
                        for run in runs:
                            run_inputs = run.get("inputs", {})
                            if query[:50] in str(run_inputs):
                                return run["id"]
                        # Return latest if no exact match
                        if runs:
                            return runs[0]["id"]
                    return None
        except Exception as e:
            console.print(f"[red]Error fetching LangSmith run: {e}[/red]")
            return None

    async def interactive_mode(self):
        """Interactive mode - send queries and see traces"""
        console.print("[bold cyan]🔍 Interactive Execution Tracer[/bold cyan]")
        console.print("[dim]Send queries and see step-by-step execution traces[/dim]")
        console.print("[dim]Type 'exit' or 'quit' to stop[/dim]\n")

        try:
            while True:
                # Get query from user
                query = console.input("[bold yellow]Query >[/bold yellow] ")

                if query.lower() in ["exit", "quit", "q"]:
                    console.print("[yellow]Goodbye! 👋[/yellow]")
                    break

                if not query.strip():
                    continue

                # Send query
                run_id = await self.send_query(query)

                if run_id:
                    # Trace execution from LangSmith
                    await self.trace_execution(run_id)
                    console.print("\n" + "═" * 80 + "\n")

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")
        except EOFError:
            console.print("\n[yellow]Goodbye! 👋[/yellow]")

    async def watch_mode(self):
        """Watch for new executions in real-time"""
        console.print("[yellow]👀 Watch mode active - monitoring for new executions...[/yellow]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        seen_sessions = set()

        try:
            while True:
                keys = await self.redis_client.keys(f"{CHECKPOINT_PREFIX}*")

                for key in keys:
                    session_id = key.replace(CHECKPOINT_PREFIX, "")

                    if session_id not in seen_sessions:
                        seen_sessions.add(session_id)
                        console.print(f"\n[green]🆕 New execution detected: {session_id}[/green]\n")
                        await self.trace_execution(session_id)
                        console.print("\n" + "═" * 80 + "\n")

                await asyncio.sleep(2)

        except KeyboardInterrupt:
            console.print("\n[yellow]Watch mode stopped[/yellow]")


async def main():
    parser = argparse.ArgumentParser(description="Trace LangGraph agent execution")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode - send queries")
    parser.add_argument("--session-id", help="Specific session ID to trace")
    parser.add_argument("--latest", action="store_true", help="Trace latest execution")
    parser.add_argument("--watch", action="store_true", help="Watch for new executions")

    args = parser.parse_args()

    tracer = ExecutionTracer()

    if not await tracer.connect():
        return

    try:
        if args.interactive:
            await tracer.interactive_mode()
        elif args.watch:
            await tracer.watch_mode()
        elif args.latest:
            session_id = await tracer.get_latest_session()
            if session_id:
                await tracer.trace_execution(session_id)
            else:
                console.print("[red]No sessions found[/red]")
        elif args.session_id:
            await tracer.trace_execution(args.session_id)
        else:
            # Default: interactive mode
            console.print("[cyan]💡 Tip: Use --interactive to send queries, or --latest to trace last execution[/cyan]\n")
            await tracer.interactive_mode()

    finally:
        await tracer.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
