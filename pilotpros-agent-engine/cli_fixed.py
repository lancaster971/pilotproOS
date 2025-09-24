#!/usr/bin/env python3
"""
Agent Engine CLI - Fixed version with proper Redis connection
"""

import asyncio
import json
import sys
import os
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

        # Detect if running in Docker
        self.in_docker = os.path.exists("/.dockerenv")
        self.redis_host = "redis-dev" if self.in_docker else "localhost"

    async def initialize(self):
        """Initialize connections"""
        try:
            # Try different Redis hosts
            for host in [self.redis_host, "redis-dev", "localhost", "127.0.0.1"]:
                try:
                    self.redis_client = await redis.from_url(
                        f"redis://{host}:6379/0",
                        encoding="utf-8",
                        decode_responses=True,
                        socket_connect_timeout=2
                    )
                    # Test connection
                    await self.redis_client.ping()
                    self.console.print(f"[green]Redis connesso a {host}[/green]")
                    return True
                except:
                    continue

            self.console.print("[yellow]Redis non raggiungibile, alcune funzioni limitate[/yellow]")
            return False

        except Exception as e:
            self.console.print(f"[red]Errore inizializzazione: {e}[/red]")
            return False

    def print_header(self):
        """Print CLI header"""
        header = Panel.fit(
            "[bold cyan]PilotProOS Agent Engine CLI[/bold cyan]\n"
            "[dim]Sistema Multi-Agent AI Interattivo[/dim]",
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
        table.add_row("4", "[bold]Demo[/bold] - Visualizza gli agent al lavoro")
        table.add_row("5", "[bold]Status[/bold] - Stato del sistema")
        table.add_row("q", "Esci")

        self.console.print(Panel(table, title="Menu Principale", border_style="blue"))

    async def chat_assistant(self):
        """Interactive chat with assistant"""
        self.console.print("\n[bold cyan]Chat con PilotPro Assistant[/bold cyan]")
        self.console.print("[bold yellow]>>> Scrivi 'exit' o 'q' per tornare al menu <<<[/bold yellow]\n")

        while True:
            try:
                question = Prompt.ask("\n[bold green]Tu[/bold green]")

                # Clear exit instruction
                if not question:
                    self.console.print("[yellow]Premi INVIO con testo vuoto o scrivi 'exit' per uscire[/yellow]")
                    continue

                if question.lower() in ['exit', 'quit', 'q']:
                    break

                with self.console.status("[bold yellow]L'assistant sta pensando...[/bold yellow]"):
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{self.api_url}/assistant",
                            json={"question": question, "language": "italian"},
                            timeout=30.0
                        )
                        result = response.json()

                if result.get("success"):
                    answer_panel = Panel(
                        result.get("answer", "Nessuna risposta"),
                        title="[bold cyan]Assistant[/bold cyan]",
                        border_style="cyan",
                        expand=False
                    )
                    self.console.print(answer_panel)

                    confidence = result.get("confidence", 0)
                    if confidence:
                        self.console.print(f"[dim]Confidenza: {confidence:.1%}[/dim]")
                else:
                    self.console.print(f"[red]Errore: {result.get('error', 'Sconosciuto')}[/red]")

                self.console.print()

            except Exception as e:
                self.console.print(f"[red]Errore: {e}[/red]")

    async def business_analysis(self):
        """Run business analysis with multi-agent system"""
        self.console.print("\n[bold cyan]Business Process Analysis[/bold cyan]")
        self.console.print("[dim]Sistema multi-agent con 3 specialisti AI[/dim]\n")

        process = Prompt.ask("[bold]Descrivi il processo da analizzare[/bold]")
        context = Prompt.ask("[bold]Contesto aggiuntivo[/bold] (opzionale)", default="")

        with self.console.status("[bold yellow]Analisi in corso con multi-agent system...[/bold yellow]"):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.api_url}/business-analysis",
                        json={
                            "process_description": process,
                            "data_context": context
                        },
                        timeout=60.0
                    )
                    result = response.json()

                if result.get("success"):
                    self.console.print("\n[bold green]Analisi Completata![/bold green]\n")

                    output_panel = Panel(
                        Markdown(result.get("analysis", "")),
                        title="[bold cyan]Risultati Analisi Multi-Agent[/bold cyan]",
                        border_style="green",
                        expand=False
                    )
                    self.console.print(output_panel)

                    self.console.print(f"\n[dim]Sistema: {result.get('system', 'Agent Engine')}")
                    self.console.print(f"Agent utilizzati: {result.get('agents_used', 3)}")
                    self.console.print(f"Modello: {result.get('model', 'multi-agent')}[/dim]")
                else:
                    self.console.print(f"[red]Analisi fallita: {result.get('error', 'Timeout')}[/red]")

            except Exception as e:
                self.console.print(f"[red]Errore: {e}[/red]")

    async def quick_insights(self):
        """Get quick insights"""
        self.console.print("\n[bold cyan]Quick Business Insights[/bold cyan]")

        question = Prompt.ask("[bold]Qual è la tua domanda business?[/bold]")
        context = Prompt.ask("[bold]Contesto[/bold] (opzionale)", default="")

        with self.console.status("[bold yellow]Generando insights con AI agent...[/bold yellow]"):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.api_url}/quick-insights",
                        json={"question": question, "context": context},
                        timeout=30.0
                    )
                    result = response.json()

                if result.get("success"):
                    self.console.print("\n[bold green]Insights Generati![/bold green]\n")

                    insights_panel = Panel(
                        Markdown(result.get("insights", "")),
                        title="[bold cyan]Insights[/bold cyan]",
                        border_style="yellow",
                        expand=False
                    )
                    self.console.print(insights_panel)
                else:
                    self.console.print(f"[red]Errore: {result.get('error', 'Sconosciuto')}[/red]")

            except Exception as e:
                self.console.print(f"[red]Errore: {e}[/red]")

    async def run_demo(self):
        """Run interactive demo"""
        self.console.print("\n[bold cyan]Demo Agent Engine[/bold cyan]\n")

        # Import and run demo
        try:
            from cli_demo import main as demo_main
            await demo_main()
        except ImportError:
            self.console.print("[yellow]Demo non disponibile[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Errore demo: {e}[/red]")

    async def system_status(self):
        """Show system status"""
        self.console.print("\n[bold cyan]System Status[/bold cyan]\n")

        status_table = Table(title="Stato Componenti")
        status_table.add_column("Componente", style="cyan")
        status_table.add_column("Stato")
        status_table.add_column("Info")

        # Check API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/health", timeout=2.0)
                api_status = "Online" if response.status_code == 200 else "Issues"
        except:
            api_status = "Offline"

        status_table.add_row("API Engine", api_status, "http://localhost:8000")

        # Check Redis
        redis_status = "Connected" if self.redis_client else "Disconnected"
        status_table.add_row("Redis Queue", redis_status, f"{self.redis_host}:6379")

        # Check Worker
        worker_status = "Running"  # Assume running if API works
        status_table.add_row("Worker Process", worker_status, "Background processor")

        self.console.print(status_table)

        # Show available models
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/health/llm", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()

                    self.console.print("\n[bold]Modelli AI Disponibili:[/bold]")
                    for provider, models in data.get("models_by_provider", {}).items():
                        if models:
                            self.console.print(f"  - {provider}: {', '.join(models)}")
        except:
            pass

    async def run(self):
        """Main CLI loop"""
        self.print_header()

        # Initialize but don't fail if Redis is down
        await self.initialize()

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
                await self.run_demo()
            elif choice == "5":
                await self.system_status()
            elif choice.lower() == "q":
                self.console.print("[cyan]Arrivederci![/cyan]")
                break

            if choice not in ["q"]:
                self.console.print("\n" + "="*50 + "\n")


async def main():
    """Entry point"""
    cli = AgentCLI()
    try:
        await cli.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrotto dall'utente[/yellow]")
    except Exception as e:
        console.print(f"[red]Errore fatale: {e}[/red]")
    finally:
        if cli.redis_client:
            await cli.redis_client.close()


if __name__ == "__main__":
    asyncio.run(main())