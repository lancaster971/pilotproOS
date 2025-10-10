#!/usr/bin/env python3
"""
Milhena Debug Console - Universal LangGraph Agent Inspector
Standalone tool for inspecting LangGraph agents with AsyncRedisSaver

Usage:
    python debug-console.py

Features:
    1. List Active Sessions - View all conversations in Redis
    2. Inspect Session State - Deep dive into conversation state
    3. Real-time Monitor - Watch agent events live
    4. Node Performance Stats - Latency analysis per node

Requirements:
    pip install rich redis
"""

import asyncio
import redis.asyncio as redis
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.tree import Tree
from rich.syntax import Syntax
from rich.prompt import Prompt, IntPrompt
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys

# Configuration
REDIS_URL = "redis://localhost:6379/0"
CHECKPOINT_PREFIX = "checkpoint:"

console = Console()


class DebugConsole:
    """Universal LangGraph Agent Debugger"""

    def __init__(self, redis_url: str = REDIS_URL):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            console.print("[green]✅ Connected to Redis[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Redis connection failed: {e}[/red]")
            return False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()

    async def list_sessions(self):
        """List all active sessions from Redis checkpoints"""
        console.print("\n[cyan]📋 Active Sessions[/cyan]\n")

        try:
            # Get all checkpoint keys
            keys = await self.redis_client.keys(f"{CHECKPOINT_PREFIX}*")

            if not keys:
                console.print("[yellow]No active sessions found[/yellow]")
                return

            # Create table
            table = Table(title=f"Found {len(keys)} Sessions")
            table.add_column("Session ID", style="cyan", no_wrap=True)
            table.add_column("Thread ID", style="green")
            table.add_column("Messages", style="yellow", justify="right")
            table.add_column("Last Update", style="magenta")

            # Process each checkpoint
            for key in sorted(keys):
                try:
                    # Get checkpoint data
                    data = await self.redis_client.get(key)
                    if not data:
                        continue

                    state = json.loads(data)

                    # Extract info
                    session_id = key.replace(CHECKPOINT_PREFIX, "")
                    thread_id = state.get("configurable", {}).get("thread_id", "N/A")
                    message_count = len(state.get("channel_values", {}).get("messages", []))
                    updated_at = state.get("checkpoint", {}).get("ts", "N/A")

                    # Format timestamp
                    if updated_at != "N/A":
                        try:
                            dt = datetime.fromisoformat(updated_at)
                            updated_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            pass

                    table.add_row(session_id, thread_id, str(message_count), updated_at)

                except Exception as e:
                    console.print(f"[red]Error processing {key}: {e}[/red]")

            console.print(table)

        except Exception as e:
            console.print(f"[red]Error listing sessions: {e}[/red]")

    async def inspect_session(self):
        """Inspect detailed state of a specific session"""
        console.print("\n[cyan]🔍 Inspect Session State[/cyan]\n")

        # Get session ID from user
        session_id = Prompt.ask("Enter session ID (or thread_id)")

        try:
            # Try as checkpoint key first
            key = f"{CHECKPOINT_PREFIX}{session_id}"
            data = await self.redis_client.get(key)

            # If not found, search by thread_id
            if not data:
                keys = await self.redis_client.keys(f"{CHECKPOINT_PREFIX}*")
                for k in keys:
                    d = await self.redis_client.get(k)
                    if d:
                        state = json.loads(d)
                        if state.get("configurable", {}).get("thread_id") == session_id:
                            data = d
                            key = k
                            break

            if not data:
                console.print(f"[red]Session '{session_id}' not found[/red]")
                return

            state = json.loads(data)

            # Display session info
            console.print(Panel(f"[bold]Session: {key.replace(CHECKPOINT_PREFIX, '')}[/bold]"))

            # Channel values (main state)
            channel_values = state.get("channel_values", {})

            # Intent and query
            console.print(f"\n[bold]Query:[/bold] {channel_values.get('query', 'N/A')}")
            console.print(f"[bold]Intent:[/bold] {channel_values.get('intent', 'N/A')}")
            console.print(f"[bold]Response:[/bold] {channel_values.get('response', 'N/A')[:200]}...")

            # Messages
            messages = channel_values.get("messages", [])
            console.print(f"\n[bold cyan]Messages ({len(messages)}):[/bold cyan]")

            for i, msg in enumerate(messages[-5:], 1):  # Last 5 messages
                msg_type = msg.get("type", "unknown")
                content = msg.get("content", "")

                # Handle tool calls
                if isinstance(content, list):
                    content = f"[{len(content)} tool calls]"
                elif isinstance(content, str):
                    content = content[:100] + "..." if len(content) > 100 else content

                console.print(f"  {i}. [{msg_type}] {content}")

            # Supervisor decision
            supervisor_decision = channel_values.get("supervisor_decision", {})
            if supervisor_decision:
                console.print(f"\n[bold magenta]Supervisor Decision:[/bold magenta]")
                console.print(f"  Action: {supervisor_decision.get('action', 'N/A')}")
                console.print(f"  Category: {supervisor_decision.get('category', 'N/A')}")
                console.print(f"  Confidence: {supervisor_decision.get('confidence', 0):.2f}")
                console.print(f"  Direct Response: {supervisor_decision.get('direct_response', False)}")

            # Tools used
            tools_used = channel_values.get("tools_used", [])
            if tools_used:
                console.print(f"\n[bold green]Tools Used ({len(tools_used)}):[/bold green]")
                for tool in tools_used:
                    console.print(f"  - {tool}")

            # Full state (optional)
            show_full = Prompt.ask("\nShow full state JSON?", choices=["y", "n"], default="n")
            if show_full == "y":
                syntax = Syntax(json.dumps(state, indent=2), "json", theme="monokai")
                console.print(syntax)

        except Exception as e:
            console.print(f"[red]Error inspecting session: {e}[/red]")

    async def realtime_monitor(self):
        """Monitor agent events in real-time using Redis PubSub"""
        console.print("\n[cyan]📡 Real-time Event Monitor[/cyan]")
        console.print("[yellow]Monitoring Redis events... (Ctrl+C to stop)[/yellow]\n")

        try:
            # Subscribe to Redis keyspace notifications
            # Requires: CONFIG SET notify-keyspace-events KEA in Redis
            pubsub = self.redis_client.pubsub()

            # Subscribe to checkpoint key changes
            await pubsub.psubscribe(f"__keyspace@0__:{CHECKPOINT_PREFIX}*")

            console.print("[green]✅ Subscribed to checkpoint events[/green]\n")

            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    # Extract key and event
                    key = message["channel"].decode() if isinstance(message["channel"], bytes) else message["channel"]
                    event = message["data"].decode() if isinstance(message["data"], bytes) else message["data"]

                    # Parse session ID
                    session_id = key.split(":")[-1]

                    # Display event
                    timestamp = datetime.now().strftime("%H:%M:%S")

                    if event == "set":
                        console.print(f"[{timestamp}] [green]✨ UPDATE[/green] Session: {session_id}")
                    elif event == "del":
                        console.print(f"[{timestamp}] [red]🗑️  DELETE[/red] Session: {session_id}")
                    else:
                        console.print(f"[{timestamp}] [{event}] Session: {session_id}")

        except KeyboardInterrupt:
            console.print("\n[yellow]Monitoring stopped[/yellow]")
        except Exception as e:
            console.print(f"[red]Monitor error: {e}[/red]")
            console.print("[yellow]Note: Redis keyspace notifications must be enabled[/yellow]")
            console.print("[yellow]Run: redis-cli CONFIG SET notify-keyspace-events KEA[/yellow]")

    async def node_performance_stats(self):
        """Analyze node performance from conversation history"""
        console.print("\n[cyan]📊 Node Performance Statistics[/cyan]\n")

        console.print("[yellow]Analyzing checkpoint data...[/yellow]\n")

        try:
            # Get all checkpoints
            keys = await self.redis_client.keys(f"{CHECKPOINT_PREFIX}*")

            if not keys:
                console.print("[red]No sessions found[/red]")
                return

            # Aggregate stats
            node_stats: Dict[str, List[float]] = {}
            total_sessions = 0

            for key in keys:
                data = await self.redis_client.get(key)
                if not data:
                    continue

                state = json.loads(data)
                total_sessions += 1

                # Extract execution metadata (if exists)
                metadata = state.get("metadata", {})
                node_durations = metadata.get("node_durations", {})

                for node, duration in node_durations.items():
                    if node not in node_stats:
                        node_stats[node] = []
                    node_stats[node].append(duration)

            # Display results
            if not node_stats:
                console.print("[yellow]No performance data found in checkpoints[/yellow]")
                console.print("[yellow]Note: This requires custom metadata tracking in your graph[/yellow]")
                return

            table = Table(title=f"Node Performance (from {total_sessions} sessions)")
            table.add_column("Node", style="cyan")
            table.add_column("Calls", style="yellow", justify="right")
            table.add_column("Avg (ms)", style="green", justify="right")
            table.add_column("Min (ms)", style="blue", justify="right")
            table.add_column("Max (ms)", style="red", justify="right")

            for node, durations in sorted(node_stats.items()):
                avg = sum(durations) / len(durations)
                min_dur = min(durations)
                max_dur = max(durations)

                table.add_row(
                    node,
                    str(len(durations)),
                    f"{avg:.2f}",
                    f"{min_dur:.2f}",
                    f"{max_dur:.2f}"
                )

            console.print(table)

        except Exception as e:
            console.print(f"[red]Error analyzing stats: {e}[/red]")

    async def run(self):
        """Main menu loop"""
        console.print("\n[bold cyan]╔════════════════════════════════════════╗[/bold cyan]")
        console.print("[bold cyan]║  Milhena Debug Console - v1.0          ║[/bold cyan]")
        console.print("[bold cyan]║  Universal LangGraph Agent Inspector   ║[/bold cyan]")
        console.print("[bold cyan]╚════════════════════════════════════════╝[/bold cyan]\n")

        # Connect to Redis
        if not await self.connect():
            return

        try:
            while True:
                console.print("\n[bold]Available Commands:[/bold]")
                console.print("  1. List Active Sessions")
                console.print("  2. Inspect Session State")
                console.print("  3. Real-time Monitor")
                console.print("  4. Node Performance Stats")
                console.print("  0. Exit\n")

                choice = Prompt.ask("Select option", choices=["0", "1", "2", "3", "4"])

                if choice == "0":
                    console.print("\n[yellow]Goodbye! 👋[/yellow]")
                    break
                elif choice == "1":
                    await self.list_sessions()
                elif choice == "2":
                    await self.inspect_session()
                elif choice == "3":
                    await self.realtime_monitor()
                elif choice == "4":
                    await self.node_performance_stats()

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
        finally:
            await self.disconnect()


async def main():
    """Entry point"""
    debugger = DebugConsole(redis_url=REDIS_URL)
    await debugger.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting...[/yellow]")
        sys.exit(0)
