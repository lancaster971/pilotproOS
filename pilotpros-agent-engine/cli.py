#!/usr/bin/env python3
"""
Agent Engine CLI - Versione con uscite chiare da ogni contesto
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
from rich.markdown import Markdown
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

console = Console()


class AgentCLI:
    """Interactive CLI for Agent Engine"""

    def __init__(self):
        self.console = console
        self.api_url = "http://localhost:8000/api/v1"
        self.redis_client = None
        self.in_docker = os.path.exists("/.dockerenv")
        self.redis_host = "redis-dev" if self.in_docker else "localhost"

    async def initialize(self):
        """Initialize connections"""
        if not REDIS_AVAILABLE:
            self.console.print("[yellow]Redis non installato - Modalità standalone[/yellow]")
            self.console.print("[green]✅ Milhena disponibile in modalità standalone[/green]")
            return True

        try:
            for host in [self.redis_host, "redis-dev", "localhost", "127.0.0.1"]:
                try:
                    self.redis_client = await redis.from_url(
                        f"redis://{host}:6379/0",
                        encoding="utf-8",
                        decode_responses=True,
                        socket_connect_timeout=2
                    )
                    await self.redis_client.ping()
                    self.console.print(f"[green]Redis connesso a {host}[/green]")
                    return True
                except:
                    continue

            self.console.print("[yellow]Redis non raggiungibile - Modalità standalone[/yellow]")
            self.console.print("[green]✅ Milhena disponibile in modalità standalone[/green]")
            return True

        except Exception as e:
            self.console.print(f"[yellow]Errore Redis: {e} - Modalità standalone[/yellow]")
            return True

    def print_header(self):
        """Print CLI header"""
        header = Panel.fit(
            "[bold cyan]PilotProOS Agent Engine CLI[/bold cyan]\n"
            "[dim]Sistema Multi-Agent AI Interattivo[/dim]",
            border_style="cyan"
        )
        self.console.print(header)
        self.console.print()

        # Istruzioni globali per uscire
        self.console.print("[bold yellow]========= COME USCIRE DA OGNI SEZIONE =========[/bold yellow]")
        self.console.print("[bold white]1. Scrivi: exit, quit, q, uscire, stop[/bold white]")
        self.console.print("[bold white]2. Premi: CTRL+C (interrompe qualsiasi operazione)[/bold white]")
        self.console.print("[bold white]3. Dal menu principale: q per chiudere tutto[/bold white]")
        self.console.print("[bold yellow]===============================================[/bold yellow]\n")

    def print_menu(self):
        """Print main menu"""
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan", width=5)
        table.add_column("Description")

        table.add_row("1", "[bold]Chat Assistant[/bold] - Parla con l'assistente AI")
        table.add_row("2", "[bold]Business Analysis[/bold] - Analisi processo con multi-agent")
        table.add_row("3", "[bold]Quick Insights[/bold] - Insights rapidi su domande business")
        table.add_row("4", "[bold magenta]🤖 Milhena Assistant[/bold magenta] - Assistente business PilotProOS")
        table.add_row("5", "[bold]Demo[/bold] - Visualizza gli agent al lavoro")
        table.add_row("6", "[bold]Status[/bold] - Stato del sistema")
        table.add_row("q", "[bold red]ESCI DAL PROGRAMMA[/bold red]")

        self.console.print(Panel(table, title="Menu Principale", border_style="blue"))

    async def chat_assistant(self):
        """Interactive chat with assistant"""
        self.console.print("\n[bold cyan]======= CHAT CON ASSISTANT =======[/bold cyan]")
        self.console.print("[bold red]PER USCIRE DALLA CHAT:[/bold red]")
        self.console.print("  - Scrivi: exit, quit, q, uscire, stop, basta")
        self.console.print("  - Premi: CTRL+C")
        self.console.print("  - Invio vuoto: ti ricorda come uscire")
        self.console.print("[bold cyan]===================================[/bold cyan]\n")

        while True:
            try:
                question = Prompt.ask("\n[bold green]Tu[/bold green]")

                # Check for empty input
                if not question:
                    self.console.print("\n[bold yellow]>>> Input vuoto! Scrivi 'exit' per uscire dalla chat <<<[/bold yellow]")
                    continue

                # Check for exit commands
                if question.lower() in ['exit', 'quit', 'q', 'uscire', 'esci', 'stop', 'basta', 'fine']:
                    self.console.print("[green]Uscita dalla chat...[/green]")
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

                # Ricorda come uscire ogni 3 domande
                self.console.print("\n[dim](Ricorda: scrivi 'exit' per uscire)[/dim]")

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Chat interrotta con CTRL+C. Torno al menu...[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]Errore: {e}[/red]")
                self.console.print("[yellow]Scrivi 'exit' per uscire o continua con una nuova domanda[/yellow]")

    async def business_analysis(self):
        """Run business analysis with multi-agent system"""
        self.console.print("\n[bold cyan]======= BUSINESS ANALYSIS =======[/bold cyan]")
        self.console.print("[bold yellow]Puoi uscire in qualsiasi momento con CTRL+C[/bold yellow]\n")

        try:
            process = Prompt.ask("[bold]Descrivi il processo da analizzare[/bold]\n(scrivi 'exit' per annullare)")

            if process.lower() in ['exit', 'quit', 'q', 'uscire', 'annulla']:
                self.console.print("[yellow]Analisi annullata. Torno al menu...[/yellow]")
                return

            context = Prompt.ask("[bold]Contesto aggiuntivo[/bold]\n(premi INVIO per saltare o 'exit' per annullare)", default="")

            if context.lower() in ['exit', 'quit', 'q', 'uscire', 'annulla']:
                self.console.print("[yellow]Analisi annullata. Torno al menu...[/yellow]")
                return

            with self.console.status("[bold yellow]Analisi in corso... (CTRL+C per interrompere)[/bold yellow]"):
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

                self.console.print("\n[bold yellow]Premi INVIO per tornare al menu[/bold yellow]")
                input()
            else:
                self.console.print(f"[red]Analisi fallita: {result.get('error', 'Timeout')}[/red]")

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Analisi interrotta con CTRL+C. Torno al menu...[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Errore: {e}[/red]")

    async def quick_insights(self):
        """Get quick insights"""
        self.console.print("\n[bold cyan]======= QUICK INSIGHTS =======[/bold cyan]")
        self.console.print("[bold yellow]Puoi uscire in qualsiasi momento con CTRL+C[/bold yellow]\n")

        try:
            question = Prompt.ask("[bold]Qual è la tua domanda business?[/bold]\n(scrivi 'exit' per annullare)")

            if question.lower() in ['exit', 'quit', 'q', 'uscire', 'annulla']:
                self.console.print("[yellow]Richiesta annullata. Torno al menu...[/yellow]")
                return

            context = Prompt.ask("[bold]Contesto[/bold]\n(premi INVIO per saltare o 'exit' per annullare)", default="")

            if context.lower() in ['exit', 'quit', 'q', 'uscire', 'annulla']:
                self.console.print("[yellow]Richiesta annullata. Torno al menu...[/yellow]")
                return

            with self.console.status("[bold yellow]Generando insights... (CTRL+C per interrompere)[/bold yellow]"):
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

                self.console.print("\n[bold yellow]Premi INVIO per tornare al menu[/bold yellow]")
                input()
            else:
                self.console.print(f"[red]Errore: {result.get('error', 'Sconosciuto')}[/red]")

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Richiesta interrotta con CTRL+C. Torno al menu...[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Errore: {e}[/red]")

    async def milhena_assistant(self):
        """Interactive chat with Milhena Multi-Agent System"""
        self.console.print("\n[bold magenta]🤖 ======= MILHENA ASSISTANT =======[/bold magenta]")
        self.console.print("[magenta]Assistente business specializzata per PilotProOS[/magenta]")
        self.console.print("[bold red]PER USCIRE:[/bold red]")
        self.console.print("  - Scrivi: exit, quit, q, uscire, stop, basta")
        self.console.print("  - Premi: CTRL+C")
        self.console.print("[bold yellow]MODALITÀ:[/bold yellow]")
        self.console.print("  - Scrivi 'quick:' all'inizio per modalità veloce")
        self.console.print("  - Altrimenti usa il sistema multi-agent completo")
        self.console.print("[bold magenta]====================================[/bold magenta]\n")

        while True:
            try:
                question = Prompt.ask("\n[bold green]Domanda per Milhena[/bold green]")

                # Check for empty input
                if not question:
                    self.console.print("[bold red]Come uscire dalla chat:[/bold red]")
                    self.console.print("  - exit, quit, q, uscire, stop, basta")
                    self.console.print("  - CTRL+C")
                    continue

                # Check for exit commands
                if question.lower().strip() in ['exit', 'quit', 'q', 'uscire', 'stop', 'basta']:
                    self.console.print("[bold yellow]Uscita da Milhena. Torno al menu...[/bold yellow]")
                    break

                # Determine mode
                quick_mode = question.lower().startswith('quick:')
                if quick_mode:
                    question = question[6:].strip()  # Remove 'quick:' prefix
                    mode_display = "[yellow](Quick Mode)[/yellow]"
                else:
                    mode_display = "[cyan](Multi-Agent Mode)[/cyan]"

                self.console.print(f"\n[magenta]🤖 Milhena {mode_display} sta elaborando...[/magenta]")

                # Process with Milhena system
                try:
                    from agents.crews.milhena_orchestrator_agents import MilhenaOrchestratorCrew, QuickMilhenaAgent
                    from model_selector import ModelSelector

                    model_selector = ModelSelector()

                    if quick_mode:
                        # Quick mode con intelligence
                        quick_milhena = QuickMilhenaAgent(model_selector)
                        result = quick_milhena.quick_answer(question)
                    else:
                        # Orchestrator multi-agent mode
                        milhena_orchestrator = MilhenaOrchestratorCrew(model_selector)
                        result = milhena_orchestrator.analyze_business_question_orchestrator(question)

                    # Display result
                    if result.get("success"):
                        response = result.get("response", "Risposta non disponibile")
                        system = result.get("system", "Milhena")
                        agents_used = result.get("agents_used", [])

                        self.console.print(f"\n[bold magenta]🤖 {system}:[/bold magenta]")
                        if agents_used:
                            agents_str = " → ".join(agents_used)
                            self.console.print(f"[dim cyan]Agenti usati: {agents_str}[/dim cyan]")

                        # Display response in a nice panel
                        response_panel = Panel(
                            response,
                            title="Risposta Milhena",
                            border_style="magenta",
                            padding=(1, 2)
                        )
                        self.console.print(response_panel)
                    else:
                        error_msg = result.get("error", "Errore sconosciuto")
                        fallback = result.get("fallback_response", "Mi dispiace, non posso elaborare la richiesta al momento.")
                        self.console.print(f"[red]❌ Errore: {error_msg}[/red]")
                        self.console.print(f"[yellow]💬 {fallback}[/yellow]")

                except ImportError as e:
                    self.console.print(f"[red]❌ Milhena non disponibile: {e}[/red]")
                    self.console.print("[yellow]Sistema in aggiornamento. Riprova più tardi.[/yellow]")
                except Exception as e:
                    self.console.print(f"[red]❌ Errore sistema Milhena: {e}[/red]")

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Chat con Milhena interrotta con CTRL+C. Torno al menu...[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]Errore: {e}[/red]")

    async def run_demo(self):
        """Run interactive demo"""
        self.console.print("\n[bold cyan]Demo Agent Engine[/bold cyan]")
        self.console.print("[bold yellow]La demo può essere interrotta con CTRL+C[/bold yellow]\n")

        try:
            from cli_demo import main as demo_main
            await demo_main()
            self.console.print("\n[bold yellow]Demo completata. Premi INVIO per tornare al menu[/bold yellow]")
            input()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Demo interrotta con CTRL+C[/yellow]")
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

        try:
            async with httpx.AsyncClient() as client:
                # Try both possible health endpoints
                for endpoint in ["/health", "/api/v1/health"]:
                    try:
                        response = await client.get(f"http://localhost:8000{endpoint}", timeout=2.0)
                        if response.status_code == 200:
                            api_status = "Online"
                            break
                    except:
                        continue
                else:
                    api_status = "Issues"
        except:
            api_status = "Offline"

        status_table.add_row("API Engine", api_status, "http://localhost:8000")
        redis_status = "Connected" if self.redis_client else "Disconnected"
        status_table.add_row("Redis Queue", redis_status, f"{self.redis_host}:6379")
        status_table.add_row("Worker Process", "Running", "Background processor")

        self.console.print(status_table)

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

        self.console.print("\n[bold yellow]Premi INVIO per tornare al menu[/bold yellow]")
        input()

    async def run(self):
        """Main CLI loop"""
        self.print_header()
        await self.initialize()

        while True:
            try:
                self.print_menu()

                choice = Prompt.ask("\n[bold]Scegli opzione (q per uscire completamente)[/bold]", default="1")

                if choice == "1":
                    await self.chat_assistant()
                elif choice == "2":
                    await self.business_analysis()
                elif choice == "3":
                    await self.quick_insights()
                elif choice == "4":
                    await self.milhena_assistant()
                elif choice == "5":
                    await self.run_demo()
                elif choice == "6":
                    await self.system_status()
                elif choice.lower() in ['q', 'quit', 'exit', 'uscire']:
                    self.console.print("\n[bold green]Chiusura programma...[/bold green]")
                    self.console.print("[cyan]Arrivederci![/cyan]")
                    break
                else:
                    self.console.print("[red]Scelta non valida. Riprova.[/red]")

                if choice not in ['q', 'quit', 'exit']:
                    self.console.print("\n" + "="*50 + "\n")

            except KeyboardInterrupt:
                self.console.print("\n[bold yellow]Ricevuto CTRL+C. Vuoi uscire? (s/n)[/bold yellow]")
                if Prompt.ask("", default="n").lower() in ['s', 'si', 'y', 'yes']:
                    self.console.print("[cyan]Arrivederci![/cyan]")
                    break
            except Exception as e:
                self.console.print(f"[red]Errore nel menu: {e}[/red]")


async def main():
    """Entry point"""
    cli = AgentCLI()
    try:
        await cli.run()
    except KeyboardInterrupt:
        console.print("\n[bold red]Programma terminato con CTRL+C[/bold red]")
        console.print("[yellow]Arrivederci![/yellow]")
    except Exception as e:
        console.print(f"[red]Errore fatale: {e}[/red]")
    finally:
        if cli.redis_client:
            await cli.redis_client.close()


if __name__ == "__main__":
    asyncio.run(main())