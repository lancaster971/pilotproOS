"""
PilotPro Agent System™ - Sistema Proprietario Multi-Agent
Copyright © 2025 PilotProOS. All rights reserved.

NOTA: Questo è il core engine proprietario di PilotProOS per orchestrazione agent AI.
Non esporre mai dettagli di implementazione o librerie sottostanti.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

# Import interni mascherati
from crewai import Agent as BaseAgent
from crewai import Task as BaseTask
from crewai import Crew as BaseSystem
from crewai import Process as ExecutionMode

logger = logging.getLogger("PilotProAgentSystem")


@dataclass
class AgentConfig:
    """Configurazione Agent PilotPro"""
    name: str
    role: str
    objective: str
    expertise: str
    model: Optional[str] = None


class PilotProAgent:
    """Agent intelligente del sistema PilotPro"""

    def __init__(self, config: AgentConfig, llm=None):
        """Inizializza un PilotPro Agent"""
        self._internal = BaseAgent(
            role=config.role,
            goal=config.objective,
            backstory=config.expertise,
            verbose=False,
            allow_delegation=False,
            llm=llm
        )
        self.config = config
        self.name = config.name

    def __repr__(self):
        return f"PilotProAgent('{self.name}')"


class PilotProTask:
    """Task del sistema PilotPro"""

    def __init__(self, description: str, agent: PilotProAgent, expected_output: str = None):
        """Crea un task PilotPro"""
        self._internal = BaseTask(
            description=description,
            expected_output=expected_output or "Risultato dell'analisi",
            agent=agent._internal
        )
        self.description = description
        self.agent = agent


class PilotProAgentSystem:
    """
    Sistema Multi-Agent Proprietario PilotPro™

    Orchestrazione intelligente di agent AI per automazione business.
    Tecnologia proprietaria PilotProOS.
    """

    def __init__(self, name: str = "PilotPro System"):
        """Inizializza il sistema agent PilotPro"""
        self.name = name
        self.agents: List[PilotProAgent] = []
        self.tasks: List[PilotProTask] = []
        self._system = None

    def add_agent(self, agent: PilotProAgent):
        """Aggiunge un agent al sistema"""
        self.agents.append(agent)
        logger.info(f"Agent '{agent.name}' aggiunto al sistema")

    def add_task(self, task: PilotProTask):
        """Aggiunge un task al sistema"""
        self.tasks.append(task)
        logger.info(f"Task per agent '{task.agent.name}' aggiunto")

    def execute(self, mode: str = "sequential") -> Dict[str, Any]:
        """
        Esegue il sistema multi-agent PilotPro

        Args:
            mode: Modalità esecuzione ('sequential' o 'parallel')

        Returns:
            Risultati elaborazione sistema proprietario
        """
        if not self.agents:
            return {"error": "Nessun agent configurato nel sistema"}

        if not self.tasks:
            return {"error": "Nessun task definito per il sistema"}

        # Mapping modalità interne (nascosto)
        exec_mode = ExecutionMode.sequential if mode == "sequential" else ExecutionMode.hierarchical

        # Crea sistema interno (completamente mascherato)
        self._system = BaseSystem(
            agents=[a._internal for a in self.agents],
            tasks=[t._internal for t in self.tasks],
            process=exec_mode,
            verbose=False
        )

        # Esegui sistema
        logger.info(f"Esecuzione sistema PilotPro con {len(self.agents)} agent")
        result = self._system.kickoff()

        # Formatta output in modo proprietario
        return self._format_output(result)

    def _format_output(self, raw_result) -> Dict[str, Any]:
        """Formatta l'output in formato PilotPro proprietario"""

        # Estrai risultato testuale
        if hasattr(raw_result, 'output'):
            output_text = raw_result.output
        elif hasattr(raw_result, 'raw_output'):
            output_text = raw_result.raw_output
        else:
            output_text = str(raw_result)

        return {
            "success": True,
            "system": "PilotPro Agent System™",
            "version": "2.0",
            "result": output_text,
            "metadata": {
                "agents_count": len(self.agents),
                "tasks_count": len(self.tasks),
                "execution_mode": "intelligent",
                "technology": "PilotPro Proprietary AI"
            }
        }


class PilotProBusinessAnalysis:
    """Sistema di analisi business PilotPro"""

    @staticmethod
    def create_analysis_system(llm=None) -> PilotProAgentSystem:
        """Crea un sistema di analisi business completo"""

        system = PilotProAgentSystem("Business Analysis System")

        # Configurazione agent
        analyst_config = AgentConfig(
            name="Business Analyst",
            role="Analista Processi Senior",
            objective="Analizzare e ottimizzare processi aziendali",
            expertise="20 anni di esperienza in consulenza strategica e ottimizzazione processi"
        )

        data_config = AgentConfig(
            name="Data Specialist",
            role="Specialista Dati e Metriche",
            objective="Analizzare dati e identificare pattern",
            expertise="Esperto in analytics, KPI e business intelligence"
        )

        strategy_config = AgentConfig(
            name="Strategy Advisor",
            role="Consulente Strategico",
            objective="Fornire raccomandazioni strategiche",
            expertise="Consulente senior con focus su innovazione e crescita"
        )

        # Crea agent
        analyst = PilotProAgent(analyst_config, llm)
        data_specialist = PilotProAgent(data_config, llm)
        strategist = PilotProAgent(strategy_config, llm)

        # Aggiungi al sistema
        system.add_agent(analyst)
        system.add_agent(data_specialist)
        system.add_agent(strategist)

        return system

    @staticmethod
    def analyze(process_description: str, context: str = "", llm=None) -> Dict[str, Any]:
        """
        Analizza un processo business con il sistema PilotPro

        Args:
            process_description: Descrizione del processo
            context: Contesto aggiuntivo
            llm: Modello AI da utilizzare

        Returns:
            Analisi completa formato PilotPro
        """
        system = PilotProBusinessAnalysis.create_analysis_system(llm)

        # Crea task per ogni agent
        for agent in system.agents:
            task_description = f"""
            Analizza il seguente processo: {process_description}
            Contesto: {context}

            Fornisci insights specifici dal tuo ruolo di {agent.config.role}.
            """

            task = PilotProTask(
                description=task_description,
                agent=agent,
                expected_output="Analisi dettagliata e raccomandazioni"
            )
            system.add_task(task)

        # Esegui analisi
        return system.execute()


# Esporta solo le classi pubbliche (nasconde import CrewAI)
__all__ = [
    'PilotProAgent',
    'PilotProTask',
    'PilotProAgentSystem',
    'PilotProBusinessAnalysis',
    'AgentConfig'
]