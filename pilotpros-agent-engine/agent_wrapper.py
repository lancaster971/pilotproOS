"""
Agent Wrapper - Layer minimale per nascondere CrewAI nei log/output
Mantiene compatibilità 100% per aggiornamenti futuri
"""

from crewai import Crew, Agent, Task, Process
import logging

# Configura logger per nascondere "crewai" nei log
logging.getLogger("crewai").name = "agent_engine"


class AgentSystem:
    """Wrapper minimale per Crew - solo rinomina nell'output"""

    def __init__(self, *args, **kwargs):
        """Passa tutto a Crew sottostante"""
        self._crew = Crew(*args, **kwargs)

    def execute(self):
        """Esegue il sistema (rinomina kickoff)"""
        return self._crew.kickoff()

    def __getattr__(self, name):
        """Passa tutto il resto a Crew"""
        return getattr(self._crew, name)


def format_output(result, hide_crew=True):
    """
    Formatta output rimuovendo riferimenti a CrewAI

    Args:
        result: Output da crew.kickoff()
        hide_crew: Se True, rimuove riferimenti
    """
    output = str(result)

    if hide_crew:
        # Sostituzioni minimali solo nell'output
        output = output.replace("CrewAI", "Agent Engine")
        output = output.replace("Crew", "Agent System")
        output = output.replace("crew", "agent system")

    return {
        "success": True,
        "system": "PilotPro Agent Engine",
        "output": output
    }


# Alias per import più puliti (opzionale)
PilotAgent = Agent
PilotTask = Task
PilotProcess = Process


# Esempio di utilizzo che nasconde CrewAI
def create_business_agents():
    """Crea agent system per business - nessun riferimento a Crew visibile"""

    # Usa nomi normali internamente
    agent1 = Agent(
        role="Business Analyst",
        goal="Analyze business processes",
        backstory="Expert in business optimization"
    )

    task1 = Task(
        description="Analyze the process",
        agent=agent1
    )

    # Usa AgentSystem invece di Crew (ma è solo un wrapper)
    system = AgentSystem(
        agents=[agent1],
        tasks=[task1],
        process=Process.sequential
    )

    # Esegui con nome pulito
    result = system.execute()  # invece di crew.kickoff()

    # Formatta output senza riferimenti
    return format_output(result)