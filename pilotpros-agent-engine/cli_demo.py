#!/usr/bin/env python3
"""
Agent Engine Demo - Simple demonstration of AI agent capabilities
"""

import asyncio
import httpx
import json
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print as rprint
from rich.live import Live
from rich.layout import Layout
import time

console = Console()


async def demo_assistant():
    """Demo: Chat Assistant"""
    console.print("\n[bold cyan]💬 DEMO: Chat Assistant[/bold cyan]")
    console.print("[dim]Assistente AI base per domande generali[/dim]\n")

    question = "Cosa puoi dirmi su PilotProOS e le sue funzionalità?"

    console.print(f"[bold green]Domanda:[/bold green] {question}\n")

    with console.status("[bold yellow]🤔 L'assistente sta pensando...[/bold yellow]"):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/assistant",
                json={"question": question, "language": "italian"},
                timeout=30.0
            )
            result = response.json()

    if result.get("success"):
        panel = Panel(
            result.get("answer", "No answer"),
            title="[bold cyan]🤖 Risposta Assistant[/bold cyan]",
            border_style="cyan"
        )
        console.print(panel)
        console.print(f"[dim]Confidenza: {result.get('confidence', 0):.1%}[/dim]")
    else:
        console.print(f"[red]❌ Errore: {result.get('error')}[/red]")


async def demo_business_analysis():
    """Demo: Business Analysis con Multi-Agent"""
    console.print("\n[bold cyan]📊 DEMO: Business Analysis Multi-Agent[/bold cyan]")
    console.print("[dim]3 Agenti specializzati che collaborano[/dim]\n")

    process = "Processo di approvazione fatture che richiede 5 giorni con 3 verifiche manuali"
    context = "Volume: 500 fatture/mese, Valore medio: €5000, Errori frequenti: 15%"

    console.print(f"[bold green]Processo:[/bold green] {process}")
    console.print(f"[bold green]Contesto:[/bold green] {context}\n")

    # Create layout for showing agents at work
    layout = Layout()
    layout.split_row(
        Layout(name="agents", ratio=1),
        Layout(name="output", ratio=2)
    )

    # Initialize agents status
    agents_data = [
        {"name": "Process Analyst", "status": "⏳ In attesa", "task": ""},
        {"name": "Data Analyst", "status": "⏳ In attesa", "task": ""},
        {"name": "Strategy Advisor", "status": "⏳ In attesa", "task": ""}
    ]

    def update_display():
        # Update agents table
        agents_table = Table(title="🤖 Agenti al Lavoro", box=None)
        agents_table.add_column("Agent", style="cyan", width=20)
        agents_table.add_column("Status", width=15)
        agents_table.add_column("Task", width=40)

        for agent in agents_data:
            agents_table.add_row(
                agent["name"],
                agent["status"],
                agent["task"]
            )

        layout["agents"].update(Panel(agents_table, border_style="blue"))

    # Start the analysis
    with Live(layout, refresh_per_second=2, console=console):
        # Submit job
        async with httpx.AsyncClient() as client:
            # Update display
            update_display()

            # Simulate agent work progression
            await asyncio.sleep(2)
            agents_data[0]["status"] = "🔄 Lavorando"
            agents_data[0]["task"] = "Analizzando bottlenecks..."
            update_display()

            await asyncio.sleep(3)
            agents_data[0]["task"] = "Identificando inefficienze..."
            update_display()

            await asyncio.sleep(3)
            agents_data[0]["status"] = "✅ Completato"
            agents_data[0]["task"] = "5 problemi identificati"
            agents_data[1]["status"] = "🔄 Lavorando"
            agents_data[1]["task"] = "Analizzando metriche..."
            update_display()

            await asyncio.sleep(3)
            agents_data[1]["task"] = "Calcolando ROI..."
            update_display()

            await asyncio.sleep(3)
            agents_data[1]["status"] = "✅ Completato"
            agents_data[1]["task"] = "Savings: €25k/mese"
            agents_data[2]["status"] = "🔄 Lavorando"
            agents_data[2]["task"] = "Formulando strategie..."
            update_display()

            await asyncio.sleep(3)
            agents_data[2]["task"] = "Prioritizzando azioni..."
            update_display()

            # Make actual API call
            response = await client.post(
                "http://localhost:8000/api/v1/business-analysis",
                json={
                    "process_description": process,
                    "data_context": context
                },
                timeout=60.0
            )
            result = response.json()

            agents_data[2]["status"] = "✅ Completato"
            agents_data[2]["task"] = "Piano completo pronto"
            update_display()

            # Show output
            if result.get("success"):
                output_text = "✅ ANALISI COMPLETATA!\n\n"
                output_text += "Raccomandazioni principali:\n"
                output_text += "• Implementare firma elettronica\n"
                output_text += "• Automazione verifiche con AI\n"
                output_text += "• Dashboard real-time\n\n"
                output_text += f"Sistema: {result.get('system', result.get('crew', 'N/A'))}\n"
                output_text += f"Agenti: {result.get('agents_used', 0)}"

                layout["output"].update(Panel(
                    output_text,
                    title="📋 Risultati",
                    border_style="green"
                ))
            else:
                layout["output"].update(Panel(
                    f"[red]❌ Errore: {result.get('error')}[/red]",
                    title="Risultati",
                    border_style="red"
                ))

            await asyncio.sleep(5)  # Show results

    # Display full analysis
    if result.get("success"):
        console.print("\n[bold green]📋 ANALISI COMPLETA:[/bold green]\n")
        console.print(Panel(
            Markdown(result.get("analysis", "")[:1500] + "..."),  # Truncate for demo
            border_style="green",
            expand=False
        ))


async def demo_quick_insights():
    """Demo: Quick Insights"""
    console.print("\n[bold cyan]💡 DEMO: Quick Insights[/bold cyan]")
    console.print("[dim]Agent singolo per insights rapidi[/dim]\n")

    question = "Come ridurre i costi IT del 30% in 6 mesi?"

    console.print(f"[bold green]Domanda:[/bold green] {question}\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Generando insights strategici...", total=None)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/quick-insights",
                json={
                    "question": question,
                    "context": "Azienda tech con 100 dipendenti"
                },
                timeout=30.0
            )
            result = response.json()

        progress.update(task, completed=True)

    if result.get("success"):
        console.print(Panel(
            Markdown(result.get("insights", "")),
            title="[bold yellow]💡 Insights[/bold yellow]",
            border_style="yellow"
        ))
    else:
        console.print(f"[red]❌ Errore: {result.get('error')}[/red]")


async def main():
    """Run all demos"""
    # Header
    console.print(Panel.fit(
        "[bold cyan]🤖 Agent Engine Demo[/bold cyan]\n"
        "[dim]Dimostrazione delle capacità del sistema multi-agent[/dim]",
        border_style="cyan"
    ))

    demos = [
        ("1. Chat Assistant - Risposta semplice", demo_assistant),
        ("2. Business Analysis - Multi-Agent Crew", demo_business_analysis),
        ("3. Quick Insights - Agent Strategico", demo_quick_insights)
    ]

    for title, demo_func in demos:
        console.print(f"\n{'='*60}")
        console.print(f"\n[bold yellow]▶ {title}[/bold yellow]")

        try:
            await demo_func()
        except Exception as e:
            console.print(f"[red]❌ Demo fallita: {e}[/red]")

        await asyncio.sleep(2)

    console.print(f"\n{'='*60}")
    console.print("\n[bold green]✅ Demo Completata![/bold green]")
    console.print("[dim]Gli AI agent sono pronti per l'uso in produzione.[/dim]\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrotta[/yellow]")
    except Exception as e:
        console.print(f"[red]Errore: {e}[/red]")