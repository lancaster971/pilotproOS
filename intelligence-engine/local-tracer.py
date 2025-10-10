#!/usr/bin/env python3
"""
Local Execution Tracer - NO LangSmith, solo Docker logs
Esegui query e vedi i log in tempo reale
"""
import asyncio
import subprocess
import aiohttp
import uuid
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from datetime import datetime

console = Console()

async def send_query_and_trace(query: str):
    """Invia query e mostra log Docker in tempo reale"""

    session_id = f"local-{uuid.uuid4().hex[:8]}"

    console.print(f"\n[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]")
    console.print(f"[bold yellow]Query:[/bold yellow] {query}")
    console.print(f"[dim]Session: {session_id}[/dim]")
    console.print(f"[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]\n")

    # Start log follower in background
    log_process = subprocess.Popen(
        ["docker", "logs", "-f", "--tail", "0", "pilotpros-intelligence-engine-dev"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Wait a moment for log stream to start
    await asyncio.sleep(0.5)

    # Send query
    console.print("[yellow]📤 Invio query...[/yellow]\n")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/api/n8n/agent/customer-support",
                json={"message": query, "session_id": session_id},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                result = await response.json()

                # Give logs time to finish
                await asyncio.sleep(1)

                # Stop log follower
                log_process.terminate()

                # Read collected logs
                logs = []
                while True:
                    line = log_process.stdout.readline()
                    if not line:
                        break
                    logs.append(line.strip())

                # Display logs with nice formatting
                console.print("\n[bold green]═══ EXECUTION TRACE ═══[/bold green]\n")

                step_num = 1
                current_step_name = None
                tool_executed = False  # Track if we just executed a tool

                for line in logs:
                    if not line:
                        continue

                    # Parse interesting log lines
                    if "[SUPERVISOR]" in line and "Analyzing query" in line:
                        query_text = line.split('query: ')[1].replace('...', '') if 'query: ' in line else 'N/A'
                        console.print(f"\n[bold cyan]━━ STEP {step_num}: ANALISI QUERY ━━[/bold cyan]")
                        console.print(f"  🏢 AGENTE: [yellow]Supervisor (Classifier)[/yellow]")
                        console.print(f"  📥 INPUT: [yellow]\"{query_text}\"[/yellow]")
                        current_step_name = "SUPERVISOR"
                        step_num += 1

                    elif "INSTANT MATCH" in line:
                        # Extract category and details
                        parts = line.split("INSTANT MATCH: ")
                        if len(parts) > 1:
                            category = parts[1].split(" -")[0]
                            needs_db = "needs_db=True" in line
                            console.print(f"  🔄 PROCESSING: Pattern matching su keywords")
                            console.print(f"  📤 OUTPUT: Categoria=[green]{category}[/green], DB={'Sì' if needs_db else 'No'}")
                            console.print(f"  ⚡ Fast-path attivo (0ms classificazione)")

                    elif "[ROUTING v3.1]" in line and "Using ReAct" in line:
                        console.print(f"\n[bold yellow]━━ STEP {step_num}: ROUTING DECISIONE ━━[/bold yellow]")
                        console.print(f"  🏢 AGENTE: [yellow]Router (Orchestrator)[/yellow]")
                        console.print(f"  📥 INPUT: Categoria=SIMPLE_METRIC, needs_db=True")
                        console.print(f"  🔄 PROCESSING: Scelta agente appropriato")
                        console.print(f"  📤 OUTPUT: [cyan]Route to ReAct Agent[/cyan]")
                        step_num += 1

                    elif "[REACT]" in line and "Call Model" in line:
                        # Distinguish between initial call and post-tool call
                        if not tool_executed:
                            console.print(f"\n[bold magenta]━━ STEP {step_num}: AI TOOL SELECTION ━━[/bold magenta]")
                            console.print(f"  🏢 AGENTE: [yellow]ReAct Agent[/yellow]")
                            console.print(f"  🤖 LLM: [cyan]gpt-4o-mini (OpenAI)[/cyan]")
                            console.print(f"  📥 INPUT: Query utente + 12 tools disponibili")
                            console.print(f"  🔄 PROCESSING: LLM sceglie tool ottimale...")
                            current_step_name = "REACT_CALL"
                            step_num += 1
                        else:
                            # This is the post-tool analysis - skip printing a new step
                            tool_executed = False  # Reset for next iteration

                    elif "[REACT]" in line and "Routing to execute_tools" in line:
                        # Extract tool count and names
                        if "(" in line and "tools):" in line:
                            tool_names = line.split("): ")[1] if "): " in line else "N/A"
                            console.print(f"  📤 OUTPUT: Tool=[cyan]{tool_names}[/cyan]")

                    elif "[TOOL EXECUTED]" in line:
                        console.print(f"\n[bold blue]━━ STEP {step_num}: ESECUZIONE TOOL ━━[/bold blue]")
                        # Extract tool name and result
                        if " → " in line:
                            parts = line.split("[TOOL EXECUTED] ")[1].split(" → ")
                            tool_name = parts[0] if parts else "unknown"
                            result = parts[1] if len(parts) > 1 else "N/A"

                            # Make tool name more readable
                            friendly_name = tool_name.replace("_tool", "").replace("_", " ").title()
                            console.print(f"  🏢 TOOL: [yellow]{friendly_name}[/yellow]")
                            console.print(f"  🗄️  DATABASE: [cyan]PostgreSQL (n8n schema)[/cyan]")
                            console.print(f"  📥 INPUT: SQL query su workflow_entity/execution_entity")
                            console.print(f"  🔄 PROCESSING: Estrazione + aggregazione dati...")
                            console.print(f"  📤 OUTPUT (primi 300 caratteri):")
                            # Show full result with line breaks
                            result_lines = result[:300].split('\n')
                            for rline in result_lines[:5]:  # Max 5 lines
                                console.print(f"     {rline}")
                            if len(result) > 300:
                                console.print(f"     [dim]... (risultato completo inviato a ReAct Agent)[/dim]")
                        tool_executed = True  # Mark that we executed a tool
                        step_num += 1

                    elif "[REACT]" in line and "Model response:" in line:
                        # Extract response preview (only show if meaningful)
                        response = line.split("Model response: ")[1] if "Model response: " in line else ""
                        # Skip empty responses or tool call responses
                        if response and len(response) > 15 and "tool" not in response.lower():
                            console.print(f"\n[bold magenta]━━ STEP {step_num}: AI ANALISI RISULTATI ━━[/bold magenta]")
                            console.print(f"  🏢 AGENTE: [yellow]ReAct Agent[/yellow]")
                            console.print(f"  🤖 LLM: [cyan]gpt-4o-mini (OpenAI)[/cyan]")
                            console.print(f"  📥 INPUT: Dati grezzi da database")
                            console.print(f"  🔄 PROCESSING: Interpretazione + sintesi dati...")
                            console.print(f"  📤 OUTPUT: \"{response[:150]}...\"")
                            step_num += 1

                    elif "[RESPONDER]" in line and "Synthesizing response" in line:
                        console.print(f"\n[bold green]━━ STEP {step_num}: RESPONSE GENERATION ━━[/bold green]")
                        console.print(f"  🏢 AGENTE: [yellow]Responder[/yellow]")
                        console.print(f"  🤖 LLM: [cyan]llama-3.3-70b (Groq FREE)[/cyan]")
                        console.print(f"  📥 INPUT: Bozza risposta + context conversazione")
                        console.print(f"  🔄 PROCESSING: Formattazione linguaggio naturale...")
                        step_num += 1

                    elif "[RESPONDER]" in line and "GROQ response:" in line:
                        response = line.split("GROQ response: ")[1] if "GROQ response: " in line else ""
                        console.print(f"  📤 OUTPUT: \"{response[:150]}...\"" if response else "  📤 OUTPUT: Risposta generata")

                    elif "Response masked" in line:
                        console.print(f"\n[bold white]━━ STEP {step_num}: BUSINESS MASKING ━━[/bold white]")
                        console.print(f"  🏢 LIBRERIA: [yellow]BusinessTerminologyParser[/yellow]")
                        console.print(f"  📥 INPUT: Risposta con termini tecnici")
                        console.print(f"  🔄 PROCESSING: Regex replacement (67 patterns)")
                        console.print(f"  📤 OUTPUT: Risposta business-friendly")
                        console.print(f"  ✅ Pronto per utente finale!")
                        step_num += 1

                    elif "Duration:" in line and "Request:" in line:
                        duration = line.split("Duration: ")[1] if "Duration: " in line else "N/A"
                        console.print(f"\n[bold dim]⏱️  Total execution time: {duration}[/bold dim]")

                # Show final response
                console.print(f"\n[bold green]═══ RESPONSE ═══[/bold green]")
                if isinstance(result, dict):
                    console.print(Panel(result.get("response", "N/A"), title="Final Answer", border_style="green"))
                    console.print(f"\n[dim]Intent: {result.get('intent', 'N/A')}[/dim]")
                    console.print(f"[dim]Masked: {result.get('metadata', {}).get('masked', False)}[/dim]")
                else:
                    console.print(Panel(str(result), title="Final Answer", border_style="green"))

    except Exception as e:
        log_process.terminate()
        console.print(f"[red]❌ Error: {e}[/red]")

async def interactive():
    """Modalità interattiva"""
    console.print("\n[bold cyan]🔍 Local Execution Tracer[/bold cyan]")
    console.print("[dim]Legge i log Docker in tempo reale - NO LangSmith[/dim]\n")

    while True:
        query = console.input("[bold yellow]Query >[/bold yellow] ")

        if query.lower() in ["exit", "quit", "q"]:
            console.print("\n[yellow]Goodbye! 👋[/yellow]")
            break

        if not query.strip():
            continue

        await send_query_and_trace(query)
        console.print("\n")

if __name__ == "__main__":
    try:
        asyncio.run(interactive())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
