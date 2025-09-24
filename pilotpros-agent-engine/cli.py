#!/usr/bin/env python3
"""
Agent Engine CLI - Interactive terminal interface
Visualizes AI agent work, chat, and responses in real-time
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from typing import Optional, Dict, Any
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
import redis.asyncio as redis

console = Console()


class AgentCLI:
    """Interactive CLI for Agent Engine"""

    def __init__(self):
        self.console = console
        self.api_url = "http://localhost:8000/api/v1"
        self.redis_client = None
        self.current_job = None
        self.verbose_mode = False

    async def initialize(self):
        """Initialize connections"""
        try:
            # Connect to Redis for real-time monitoring
            self.redis_client = await redis.from_url(
                "redis://localhost:6379/0",
                encoding="utf-8",
                decode_responses=True
            )
            return True
        except Exception as e:
            self.console.print(f"[red]❌ Redis connection failed: {e}[/red]")
            return False

    def print_header(self):
        """Print CLI header"""
        header = Panel.fit(
            "[bold cyan]🤖 PilotProOS Agent Engine CLI[/bold cyan]\n"
            "[dim]Interactive Multi-Agent AI System[/dim]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()

    def print_menu(self):
        """Print main menu"""
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan", width=5)
        table.add_column("Description")

        table.add_row("1", "[bold]Chat Assistant[/bold] - Parla con l'assistente AI")
        table.add_row("2", "[bold]Business Analysis[/bold] - Analisi processo con multi-agent")
        table.add_row("3", "[bold]Quick Insights[/bold] - Insights rapidi su domande business")
        table.add_row("4", "[bold]Monitor Jobs[/bold] - Monitora job in tempo reale")
        table.add_row("5", "[bold]Agent Status[/bold] - Stato degli agent e modelli")
        table.add_row("v", "Toggle verbose mode (mostra dettagli agent)")
        table.add_row("q", "Esci")

        self.console.print(Panel(table, title="Menu Principale", border_style="blue"))

    async def chat_assistant(self):
        """Interactive chat with assistant"""
        self.console.print("\n[bold cyan]💬 Chat con PilotPro Assistant[/bold cyan]")
        self.console.print("[dim]Scrivi 'exit' per tornare al menu[/dim]\n")

        while True:
            try:
                # Get user input
                question = Prompt.ask("[bold green]Tu[/bold green]")

                if question.lower() in ['exit', 'quit', 'q']:
                    break

                # Show processing
                with self.console.status("[bold yellow]🤔 Pensando...[/bold yellow]"):
                    # Call API
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{self.api_url}/assistant",
                            json={
                                "question": question,
                                "language": "italian"
                            },
                            timeout=30.0
                        )
                        result = response.json()

                # Show response
                if result.get("success"):
                    answer_panel = Panel(
                        result.get("answer", "Nessuna risposta"),
                        title="[bold cyan]🤖 Assistant[/bold cyan]",
                        border_style="cyan",
                        expand=False
                    )
                    self.console.print(answer_panel)

                    # Show confidence if available
                    confidence = result.get("confidence", 0)
                    if confidence:
                        self.console.print(f"[dim]Confidenza: {confidence:.1%}[/dim]")
                else:
                    self.console.print(f"[red]❌ Errore: {result.get('error', 'Sconosciuto')}[/red]")

                self.console.print()

            except Exception as e:
                self.console.print(f"[red]❌ Errore: {e}[/red]")

    async def business_analysis(self):
        """Run business analysis with multi-agent crew"""
        self.console.print("\n[bold cyan]📊 Business Process Analysis[/bold cyan]")
        self.console.print("[dim]Analisi multi-agent con 3 specialisti[/dim]\n")

        # Get process description
        process = Prompt.ask("[bold]Descrivi il processo da analizzare[/bold]")
        context = Prompt.ask("[bold]Contesto aggiuntivo[/bold] (opzionale)", default="")

        # Create layout for real-time monitoring
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="agents", size=10),
            Layout(name="output")
        )

        # Header
        layout["header"].update(Panel("[bold cyan]🔄 Analisi in corso...[/bold cyan]"))

        # Start analysis
        job_id = None
        try:
            async with httpx.AsyncClient() as client:
                # Submit job
                response = await client.post(
                    f"{self.api_url}/business-analysis",
                    json={
                        "process_description": process,
                        "data_context": context
                    },
                    timeout=5.0
                )

                initial_result = response.json()
                if "job_id" in initial_result:
                    job_id = initial_result["job_id"]

                    # Monitor in real-time if verbose
                    if self.verbose_mode and job_id:
                        await self.monitor_job_progress(job_id, layout)
                    else:
                        with self.console.status("[bold yellow]⏳ Analisi in corso (fino a 60 secondi)...[/bold yellow]"):
                            # Wait for completion
                            await asyncio.sleep(2)

                            # Poll for result
                            for _ in range(30):  # Max 60 seconds
                                result_key = f"job:result:{job_id}"
                                result_data = await self.redis_client.get(result_key)
                                if result_data:
                                    initial_result = json.loads(result_data)
                                    break
                                await asyncio.sleep(2)

                # Display result
                if initial_result.get("success"):
                    self.console.print("\n[bold green]✅ Analisi Completata![/bold green]\n")

                    # Parse and display analysis
                    analysis = initial_result.get("analysis", "")

                    # Create formatted output
                    output_panel = Panel(
                        Markdown(analysis),
                        title="[bold cyan]📋 Risultati Analisi[/bold cyan]",
                        border_style="green",
                        expand=False
                    )
                    self.console.print(output_panel)

                    # Show metadata
                    self.console.print(f"\n[dim]Crew: {initial_result.get('crew', 'Unknown')}")
                    self.console.print(f"Agenti utilizzati: {initial_result.get('agents_used', 0)}")
                    self.console.print(f"Modello: {initial_result.get('model', 'Unknown')}[/dim]")
                else:
                    self.console.print(f"[red]❌ Analisi fallita: {initial_result.get('error', 'Timeout')}[/red]")

        except Exception as e:
            self.console.print(f"[red]❌ Errore: {e}[/red]")

    async def quick_insights(self):
        """Get quick insights"""
        self.console.print("\n[bold cyan]💡 Quick Business Insights[/bold cyan]")

        question = Prompt.ask("[bold]Qual è la tua domanda business?[/bold]")
        context = Prompt.ask("[bold]Contesto[/bold] (opzionale)", default="")

        with self.console.status("[bold yellow]🔍 Generando insights...[/bold yellow]"):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.api_url}/quick-insights",
                        json={
                            "question": question,
                            "context": context
                        },
                        timeout=30.0
                    )
                    result = response.json()

                if result.get("success"):
                    self.console.print("\n[bold green]✅ Insights Generati![/bold green]\n")

                    insights_panel = Panel(
                        Markdown(result.get("insights", "")),
                        title="[bold cyan]💡 Insights[/bold cyan]",
                        border_style="yellow",
                        expand=False
                    )
                    self.console.print(insights_panel)
                else:
                    self.console.print(f"[red]❌ Errore: {result.get('error', 'Sconosciuto')}[/red]")

            except Exception as e:
                self.console.print(f"[red]❌ Errore: {e}[/red]")

    async def monitor_job_progress(self, job_id: str, layout: Layout):
        """Monitor job progress in real-time"""
        agents_status = {
            "Process Analyst": "⏳ In attesa",
            "Data Analyst": "⏳ In attesa",
            "Strategy Advisor": "⏳ In attesa"
        }

        output_lines = []

        with Live(layout, refresh_per_second=2, console=self.console):
            start_time = time.time()

            while time.time() - start_time < 60:  # Max 60 seconds
                # Update agents status (simulated)
                elapsed = int(time.time() - start_time)

                if elapsed > 5:
                    agents_status["Process Analyst"] = "🔄 Analizzando processo..."
                if elapsed > 15:
                    agents_status["Process Analyst"] = "✅ Completato"
                    agents_status["Data Analyst"] = "🔄 Estraendo insights..."
                if elapsed > 25:
                    agents_status["Data Analyst"] = "✅ Completato"
                    agents_status["Strategy Advisor"] = "🔄 Formulando strategie..."
                if elapsed > 35:
                    agents_status["Strategy Advisor"] = "✅ Completato"

                # Update agents panel
                agents_table = Table(show_header=True, box=None)
                agents_table.add_column("Agent", style="cyan")
                agents_table.add_column("Status")

                for agent, status in agents_status.items():
                    agents_table.add_row(agent, status)

                layout["agents"].update(Panel(agents_table, title="Agent Status"))

                # Check for result
                result_key = f"job:result:{job_id}"
                result_data = await self.redis_client.get(result_key)
                if result_data:
                    layout["output"].update(Panel(
                        "[bold green]✅ Analisi completata![/bold green]",
                        title="Output"
                    ))
                    break

                # Update output
                if elapsed % 5 == 0:
                    output_lines.append(f"[dim]{datetime.now().strftime('%H:%M:%S')} - Processing...[/dim]")
                    layout["output"].update(Panel(
                        "\n".join(output_lines[-10:]),  # Show last 10 lines
                        title="Output"
                    ))

                await asyncio.sleep(1)

    async def monitor_jobs(self):
        """Monitor all jobs in real-time"""
        self.console.print("\n[bold cyan]📊 Monitor Jobs[/bold cyan]")

        with self.console.status("[bold yellow]Monitorando jobs...[/bold yellow]"):
            try:
                # Get all job keys
                job_keys = []
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(
                        cursor, match="job:*", count=100
                    )
                    job_keys.extend([k for k in keys if not k.startswith("job:result:")])
                    if cursor == 0:
                        break

                if not job_keys:
                    self.console.print("[yellow]Nessun job trovato[/yellow]")
                    return

                # Display jobs table
                table = Table(title="Jobs Attuali")
                table.add_column("Job ID", style="cyan")
                table.add_column("Type")
                table.add_column("Status")
                table.add_column("Created")

                for key in job_keys[-10:]:  # Show last 10
                    job_data = await self.redis_client.get(key)
                    if job_data:
                        job = json.loads(job_data)
                        job_id = key.split(":")[-1]

                        # Check if result exists
                        result_exists = await self.redis_client.exists(f"job:result:{job_id}")
                        status = "✅ Completato" if result_exists else "🔄 In corso"

                        table.add_row(
                            job_id[:8] + "...",
                            job.get("type", "unknown"),
                            status,
                            job.get("created_at", "unknown")[:19]
                        )

                self.console.print(table)

            except Exception as e:
                self.console.print(f"[red]❌ Errore: {e}[/red]")

    async def agent_status(self):
        """Show agent and model status"""
        self.console.print("\n[bold cyan]🤖 Agent Status[/bold cyan]")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/health/llm", timeout=5.0)
                status = response.json()

                # Status panel
                status_panel = Panel(
                    f"[bold green]✅ {status.get('status', 'unknown').upper()}[/bold green]",
                    title="System Status",
                    expand=False
                )
                self.console.print(status_panel)

                # Models table
                table = Table(title="Modelli Disponibili")
                table.add_column("Provider", style="cyan")
                table.add_column("Models")
                table.add_column("Type")

                models_by_provider = status.get("models_by_provider", {})
                for provider, models in models_by_provider.items():
                    model_list = ", ".join(models) if models else "None"
                    table.add_row(
                        provider,
                        model_list,
                        "FREE" if provider in ["groq", "google", "ollama"] else "PAID"
                    )

                self.console.print(table)

                # Free models
                free_models = status.get("free_models", [])
                if free_models:
                    self.console.print(f"\n[green]Free models disponibili: {len(free_models)}[/green]")

        except Exception as e:
            self.console.print(f"[red]❌ Errore: {e}[/red]")

    async def run(self):
        """Main CLI loop"""
        self.print_header()

        # Initialize connections
        if not await self.initialize():
            self.console.print("[red]Failed to initialize. Check if Redis is running.[/red]")
            return

        while True:
            self.print_menu()

            choice = Prompt.ask("\n[bold]Scegli opzione[/bold]", default="1")

            if choice == "1":
                await self.chat_assistant()
            elif choice == "2":
                await self.business_analysis()
            elif choice == "3":
                await self.quick_insights()
            elif choice == "4":
                await self.monitor_jobs()
            elif choice == "5":
                await self.agent_status()
            elif choice.lower() == "v":
                self.verbose_mode = not self.verbose_mode
                mode = "ON" if self.verbose_mode else "OFF"
                self.console.print(f"[yellow]Verbose mode: {mode}[/yellow]")
            elif choice.lower() == "q":
                self.console.print("[cyan]👋 Arrivederci![/cyan]")
                break

            if choice not in ["q"]:
                self.console.print("\n" + "="*50 + "\n")


async def main():
    """Entry point"""
    cli = AgentCLI()
    try:
        await cli.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
    finally:
        if cli.redis_client:
            await cli.redis_client.close()


if __name__ == "__main__":
    asyncio.run(main())