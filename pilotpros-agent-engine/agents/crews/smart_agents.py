"""
Smart Multi-Agent System - Selezione automatica modelli
Usa automaticamente POTENTI, LEGGERI o GRATIS in base al task
"""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from model_selector import ModelSelector, ModelCategory
import os
import logging

logger = logging.getLogger(__name__)


class SmartAgents:
    """Sistema agent con selezione intelligente dei modelli"""

    def __init__(self):
        """Inizializza con i migliori modelli disponibili"""
        self.config = ModelSelector.get_quick_config()
        self.llms = {}

        # Configura LLM POTENTE (per task complessi)
        provider, model = self.config['potente']
        self.llms['potente'] = self._create_llm(provider, model)

        # Configura LLM LEGGERO (per task veloci)
        provider, model = self.config['leggero']
        self.llms['leggero'] = self._create_llm(provider, model)

        # Configura LLM GRATIS (per task standard)
        provider, model = self.config['gratis']
        self.llms['gratis'] = self._create_llm(provider, model)

        logger.info(f"Modelli configurati: {self.config}")

    def _create_llm(self, provider: str, model: str):
        """Crea LLM in base al provider"""
        try:
            if provider == "openai":
                return ChatOpenAI(
                    model_name=model,
                    temperature=0.7,
                    api_key=os.getenv("OPENAI_API_KEY")
                )
            elif provider == "groq":
                return ChatGroq(
                    model_name=model,
                    temperature=0.7,
                    api_key=os.getenv("GROQ_API_KEY")
                )
            elif provider == "google":
                return ChatGoogleGenerativeAI(
                    model=model,
                    temperature=0.7,
                    google_api_key=os.getenv("GOOGLE_API_KEY")
                )
            elif provider == "openrouter":
                return ChatOpenAI(
                    model_name=model,
                    temperature=0.7,
                    api_key=os.getenv("OPENROUTER_API_KEY"),
                    base_url="https://openrouter.ai/api/v1"
                )
            elif provider == "anthropic":
                # Via OpenRouter se disponibile
                if os.getenv("OPENROUTER_API_KEY"):
                    return ChatOpenAI(
                        model_name=f"anthropic/{model}",
                        temperature=0.7,
                        api_key=os.getenv("OPENROUTER_API_KEY"),
                        base_url="https://openrouter.ai/api/v1"
                    )
            else:
                logger.warning(f"Provider {provider} non supportato")
                return None
        except Exception as e:
            logger.error(f"Errore creazione LLM {provider}/{model}: {e}")
            return None

    def create_business_crew(self, use_premium: bool = False):
        """
        Crea crew per analisi business

        Args:
            use_premium: Se True usa modelli POTENTI, altrimenti GRATIS/LEGGERI
        """
        agents = []

        # Agent 1: Strategico (usa modello POTENTE per compiti complessi)
        if use_premium and self.llms.get('potente'):
            strategic_agent = Agent(
                role="Analista Strategico Senior",
                goal="Analizzare in profondità strategie e opportunità di business",
                backstory="Consulente con 20 anni di esperienza in trasformazione digitale",
                verbose=True,
                allow_delegation=False,
                llm=self.llms['potente']
            )
            agents.append(strategic_agent)
            logger.info(f"Agent Strategico con modello POTENTE: {self.config['potente']}")

        # Agent 2: Dati (usa modello GRATIS per analisi veloce)
        if self.llms.get('gratis'):
            data_agent = Agent(
                role="Data Analyst",
                goal="Analizzare rapidamente dati e identificare pattern",
                backstory="Esperto in analisi dati e statistica",
                verbose=True,
                allow_delegation=False,
                llm=self.llms['gratis']
            )
            agents.append(data_agent)
            logger.info(f"Agent Dati con modello GRATIS: {self.config['gratis']}")

        # Agent 3: Operativo (usa modello LEGGERO per task semplici)
        if self.llms.get('leggero'):
            operational_agent = Agent(
                role="Operations Manager",
                goal="Ottimizzare processi operativi e workflow",
                backstory="Specialista in efficienza operativa e automazione",
                verbose=True,
                allow_delegation=False,
                llm=self.llms['leggero']
            )
            agents.append(operational_agent)
            logger.info(f"Agent Operativo con modello LEGGERO: {self.config['leggero']}")

        return agents

    def analyze_process(self, description: str, use_premium: bool = False):
        """
        Analizza un processo business

        Args:
            description: Descrizione del processo
            use_premium: Se True usa modelli potenti (più costosi)

        Returns:
            Risultati analisi con info sui modelli usati
        """
        agents = self.create_business_crew(use_premium)

        if not agents:
            return {
                "success": False,
                "error": "Nessun modello disponibile. Configura almeno una API key."
            }

        tasks = []
        for agent in agents:
            task = Task(
                description=f"Analizza questo processo: {description}",
                expected_output="Analisi dettagliata con raccomandazioni",
                agent=agent
            )
            tasks.append(task)

        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )

        try:
            result = crew.kickoff()

            # Estrai output
            if hasattr(result, 'output'):
                output = result.output
            else:
                output = str(result)

            # Info sui modelli usati
            models_info = []
            if use_premium and 'potente' in self.config:
                models_info.append(f"POTENTE: {self.config['potente']}")
            if 'gratis' in self.config:
                models_info.append(f"GRATIS: {self.config['gratis']}")
            if 'leggero' in self.config:
                models_info.append(f"LEGGERO: {self.config['leggero']}")

            return {
                "success": True,
                "analysis": output,
                "models_used": models_info,
                "cost_level": "PREMIUM" if use_premium else "ECONOMICO"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Esempio di utilizzo
if __name__ == "__main__":
    # Mostra modelli disponibili
    print("=== MODELLI DISPONIBILI ===")
    available = ModelSelector.list_available_models()
    for category, models in available.items():
        if models:
            print(f"\n{category.upper()}: {len(models)} modelli")
            for model in models[:3]:  # Mostra primi 3
                print(f"  - {model}")

    # Test analisi
    agents = SmartAgents()

    # Analisi economica (usa modelli GRATIS/LEGGERI)
    print("\n=== ANALISI ECONOMICA ===")
    result = agents.analyze_process(
        "Ottimizzare processo vendite online",
        use_premium=False
    )
    print(f"Costo: {result.get('cost_level')}")
    print(f"Modelli: {result.get('models_used')}")

    # Analisi premium (usa modelli POTENTI)
    print("\n=== ANALISI PREMIUM ===")
    result = agents.analyze_process(
        "Trasformazione digitale completa azienda manifatturiera",
        use_premium=True
    )
    print(f"Costo: {result.get('cost_level')}")
    print(f"Modelli: {result.get('models_used')}")