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
        """Trace complete execution from LangSmith run using REAL child runs"""
        import os
        from langsmith import Client

        api_key = os.getenv("LANGSMITH_API_KEY", "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")
        os.environ["LANGSMITH_API_KEY"] = api_key

        # Get run details from LangSmith
        try:
            client = Client()
            run = client.read_run(run_id)

        except Exception as e:
            console.print(f"[red]❌ Error fetching run: {e}[/red]")
            return

        # Wait for LangSmith to save all runs
        import time
        from datetime import datetime, timedelta
        time.sleep(2)

        # Get ALL runs in the project from last minute (includes LLM, tools, etc)
        all_runs = []
        try:
            run_start_time = run.start_time if hasattr(run, 'start_time') else datetime.now()

            # List ALL recent runs (not just children)
            recent_runs = list(client.list_runs(
                project_name="milhena-v3-production",
                start_time=run_start_time - timedelta(seconds=5),  # 5s before to catch everything
                limit=200
            ))

            # Filter to runs that are likely part of this execution
            for r in recent_runs:
                if hasattr(r, 'start_time') and r.start_time and r.start_time >= run_start_time:
                    all_runs.append(r)

            console.print(f"[yellow]🔍 Found {len(all_runs)} runs in execution timeline[/yellow]")

        except Exception as e:
            console.print(f"[yellow]⚠️  Error fetching runs: {e}[/yellow]")

        # Use these as "children" for processing
        children = all_runs

        # Extract query and response from main run
        inputs = run.inputs if hasattr(run, 'inputs') else {}
        outputs = run.outputs if hasattr(run, 'outputs') else {}

        # Try to get query from inputs
        query = "N/A"
        if isinstance(inputs, dict):
            # Priority 1: Direct "query" field
            if "query" in inputs and isinstance(inputs["query"], str):
                query = inputs["query"][:100]
            # Priority 2: messages array
            elif "messages" in inputs and isinstance(inputs["messages"], list) and inputs["messages"]:
                # Find last HumanMessage
                for msg in reversed(inputs["messages"]):
                    content = None
                    if isinstance(msg, dict):
                        # LangChain serialized format
                        if "kwargs" in msg and isinstance(msg["kwargs"], dict):
                            content = msg["kwargs"].get("content")
                        elif "content" in msg:
                            content = msg["content"]

                    if content and isinstance(content, str):
                        query = content[:100]
                        break

        response_text = str(outputs.get("response", "N/A"))[:200] if isinstance(outputs, dict) else "N/A"
        intent = outputs.get("intent", "N/A") if isinstance(outputs, dict) else "N/A"

        # Header
        header = Text()
        header.append("╔" + "═" * 78 + "╗\n", style="bright_cyan")
        header.append("║  ", style="bright_cyan")
        header.append("EXECUTION TRACE", style="bold bright_white")
        header.append(f": {run_id[:30]:<47}║\n", style="bright_cyan")
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

        # Build steps from REAL child runs OR fallback to state extraction
        steps = []

        if not children and hasattr(run, 'inputs') and isinstance(run.inputs, dict) and 'state' in run.inputs:
            # FALLBACK: Extract from state when no child runs (checkpointer=None)
            state = run.inputs['state']
            output_state = run.outputs.get('output', {}) if hasattr(run, 'outputs') and isinstance(run.outputs, dict) else {}

            # Build pseudo-steps from state messages
            messages = state.get('messages', []) if isinstance(state, dict) else []

            for i, msg in enumerate(messages, start=1):
                if isinstance(msg, dict):
                    msg_type = msg.get('type', 'unknown')
                    content = msg.get('kwargs', {}).get('content', '') if 'kwargs' in msg else msg.get('content', '')

                    steps.append({
                        "num": i,
                        "name": f"[{msg_type.upper()}] Message",
                        "duration": 0,  # No duration from state
                        "type": msg_type,
                        "input": {"content": str(content)[:100]},
                        "output": {}
                    })

        # Process REAL child runs if available
        for i, child in enumerate(sorted(children, key=lambda x: x.start_time if hasattr(x, 'start_time') else 0), start=len(steps) + 1):
            # Calculate duration
            duration_ms = 0
            if hasattr(child, 'total_time') and child.total_time:
                duration_ms = child.total_time * 1000  # Convert to ms
            elif hasattr(child, 'end_time') and hasattr(child, 'start_time') and child.end_time and child.start_time:
                duration_ms = (child.end_time - child.start_time).total_seconds() * 1000

            # Extract clean inputs
            child_inputs = {}
            if hasattr(child, 'inputs') and isinstance(child.inputs, dict):
                for key, value in child.inputs.items():
                    # Handle HumanMessage/AIMessage objects
                    if isinstance(value, list) and value and isinstance(value[0], dict) and 'content' in value[0]:
                        child_inputs[key] = value[0]['content'][:100]
                    elif isinstance(value, dict) and 'content' in value:
                        child_inputs[key] = value['content'][:100]
                    elif isinstance(value, (str, int, float, bool)):
                        child_inputs[key] = value
                    else:
                        child_inputs[key] = str(value)[:100]

            # Extract clean outputs
            child_outputs = {}
            if hasattr(child, 'outputs') and isinstance(child.outputs, dict):
                for key, value in child.outputs.items():
                    if isinstance(value, list) and value and isinstance(value[0], dict) and 'content' in value[0]:
                        child_outputs[key] = value[0]['content'][:200]
                    elif isinstance(value, dict) and 'content' in value:
                        child_outputs[key] = value['content'][:200]
                    elif isinstance(value, (str, int, float, bool)):
                        child_outputs[key] = value
                    else:
                        child_outputs[key] = str(value)[:200]

            steps.append({
                "num": i,
                "name": child.name if hasattr(child, 'name') else f"Step {i}",
                "duration": int(duration_ms),
                "type": child.run_type if hasattr(child, 'run_type') else "unknown",
                "input": child_inputs,
                "output": child_outputs
            })

        # Render each step
        for step in steps:
            # Header
            console.print(self.format_node_header(step["num"], step["name"], step["duration"]))

            # INPUT
            self.format_input(step["input"])

            # OUTPUT
            self.format_output(step["output"])

            console.print("\n" + "─" * 80 + "\n")

        # Summary
        total_duration = sum(s["duration"] for s in steps) if steps else 0

        summary = Table(title="📊 EXECUTION SUMMARY", show_header=False, box=None)
        summary.add_column(style="bold")
        summary.add_column()

        summary.add_row("Total Duration:", f"{total_duration}ms ({total_duration/1000:.2f}s)" if total_duration else "N/A")
        summary.add_row("Total Steps:", f"{len(steps)}")
        summary.add_row("LLM Calls:", f"{sum(1 for s in steps if s['type'] in ['llm', 'chat'])}")
        summary.add_row("Tool Calls:", f"{sum(1 for s in steps if s['type'] == 'tool')}")

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
                    timeout=aiohttp.ClientTimeout(total=60)  # Increased to 60s
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
            import traceback
            console.print(f"[red]❌ Request failed: {e}[/red]")
            console.print(f"[red]{traceback.format_exc()}[/red]")
            return None

    async def get_latest_langsmith_run(self, query: str) -> Optional[str]:
        """Get latest LangSmith run ID for query using LangSmith SDK"""
        import os
        from langsmith import Client

        api_key = os.getenv("LANGSMITH_API_KEY", "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")
        project_name = os.getenv("LANGSMITH_PROJECT", "milhena-v3-production")

        try:
            # Set environment for SDK
            os.environ["LANGSMITH_API_KEY"] = api_key

            client = Client()
            runs = list(client.list_runs(project_name=project_name, limit=10))

            if not runs:
                return None

            # Find run matching query (check inputs)
            for run in runs:
                run_inputs = str(run.inputs) if hasattr(run, 'inputs') else ""
                if query[:30].lower() in run_inputs.lower():
                    return str(run.id)

            # Return latest run
            return str(runs[0].id)

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
