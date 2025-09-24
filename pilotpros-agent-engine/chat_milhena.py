#!/usr/bin/env python3
"""
Chat diretto con Milhena - Versione semplificata senza Redis
"""

import sys
sys.path.append('.')
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

def chat_with_milhena():
    """Chat interattiva con Milhena"""

    console.print("\n[bold magenta]🤖 ======= CHAT CON MILHENA =======[/bold magenta]")
    console.print("[magenta]Assistente business specializzata per PilotProOS[/magenta]")
    console.print("[bold red]PER USCIRE:[/bold red] scrivi 'exit', 'quit', 'q' o CTRL+C")
    console.print("[bold yellow]MODALITÀ:[/bold yellow]")
    console.print("  - Scrivi 'quick:' all'inizio per modalità veloce")
    console.print("  - Altrimenti usa il sistema multi-agent completo")
    console.print("[bold magenta]=====================================[/bold magenta]\n")

    # Importa Milhena
    try:
        from agents.crews.milhena_crew_agents import MilhenaMultiAgentCrew, QuickMilhenaAgent
        from model_selector import ModelSelector

        model_selector = ModelSelector()
        console.print("[green]✅ Milhena caricata con successo![/green]\n")

    except ImportError as e:
        console.print(f"[red]❌ Errore import Milhena: {e}[/red]")
        console.print("[yellow]Verifica che tutte le dipendenze siano installate[/yellow]")
        return
    except Exception as e:
        console.print(f"[red]❌ Errore inizializzazione: {e}[/red]")
        return

    # Loop chat principale
    while True:
        try:
            question = Prompt.ask("\n[bold green]Tu[/bold green]")

            # Check comandi uscita
            if question.lower().strip() in ['exit', 'quit', 'q', 'uscire', 'stop', 'basta', '']:
                console.print("[bold yellow]👋 Ciao! Arrivederci![/bold yellow]")
                break

            # Modalità quick o full
            quick_mode = question.lower().startswith('quick:')
            if quick_mode:
                question = question[6:].strip()
                mode_display = "[yellow](Quick Mode)[/yellow]"
            else:
                mode_display = "[cyan](Multi-Agent Mode)[/cyan]"

            console.print(f"\n[magenta]🤖 Milhena {mode_display} sta pensando...[/magenta]")

            # Elabora con Milhena
            try:
                if quick_mode:
                    quick_milhena = QuickMilhenaAgent(model_selector)
                    result = quick_milhena.quick_answer(question)
                else:
                    milhena_crew = MilhenaMultiAgentCrew(model_selector)
                    result = milhena_crew.analyze_business_question(question)

                # Mostra risultato
                if result.get("success"):
                    response = result.get("response", "Nessuna risposta disponibile")
                    system = result.get("system", "Milhena")
                    agents_used = result.get("agents_used", [])

                    # Info sistema
                    console.print(f"\n[bold magenta]🤖 {system}[/bold magenta]")
                    if agents_used:
                        agents_str = " → ".join(agents_used)
                        console.print(f"[dim cyan]Pipeline: {agents_str}[/dim cyan]")

                    # Risposta in panel
                    response_panel = Panel(
                        response,
                        title="💬 Milhena risponde",
                        border_style="magenta",
                        padding=(1, 2)
                    )
                    console.print(response_panel)

                else:
                    error_msg = result.get("error", "Errore sconosciuto")
                    fallback = result.get("fallback_response", "Mi dispiace, non posso rispondere ora.")

                    console.print(f"[red]❌ Errore: {error_msg}[/red]")
                    console.print(f"[yellow]💬 {fallback}[/yellow]")

            except Exception as e:
                console.print(f"[red]❌ Errore elaborazione: {e}[/red]")
                console.print("[yellow]💡 Prova con una domanda più semplice o 'quick: domanda'[/yellow]")

        except KeyboardInterrupt:
            console.print("\n[bold yellow]👋 CTRL+C ricevuto. Arrivederci![/bold yellow]")
            break
        except Exception as e:
            console.print(f"[red]❌ Errore inaspettato: {e}[/red]")

def main():
    """Entry point"""
    try:
        chat_with_milhena()
    except KeyboardInterrupt:
        console.print("\n[bold red]Programma terminato[/bold red]")

if __name__ == "__main__":
    main()