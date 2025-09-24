"""
Esempio di Multi-Agent System con diversi modelli AI
Ogni agent può usare un modello/provider diverso
"""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
import os


class MultiModelAgents:
    """Sistema multi-agent con modelli diversi per ogni agent"""

    def __init__(self):
        """Inizializza i diversi LLM per gli agent"""

        # Agent 1: GPT-4o per analisi complesse
        self.gpt4o = ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        ) if os.getenv("OPENAI_API_KEY") else None

        # Agent 2: Groq Llama per velocità (GRATIS!)
        self.groq_llama = ChatGroq(
            model_name="llama-3.2-90b-vision-preview",
            temperature=0.5,
            api_key=os.getenv("GROQ_API_KEY")
        ) if os.getenv("GROQ_API_KEY") else None

        # Agent 3: Claude via OpenRouter per creatività
        self.claude = ChatOpenAI(
            model_name="anthropic/claude-3.5-sonnet",
            temperature=0.8,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        ) if os.getenv("OPENROUTER_API_KEY") else None

        # Agent 4: Gemini per analisi multimodale
        self.gemini = ChatGoogleGenerativeAI(
            model="gemini-pro-1.5",
            temperature=0.6,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        ) if os.getenv("GOOGLE_API_KEY") else None

        # Agent 5: Qwen via OpenRouter (GRATIS!)
        self.qwen = ChatOpenAI(
            model_name="qwen/qwen-2.5-72b-instruct",
            temperature=0.5,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        ) if os.getenv("OPENROUTER_API_KEY") else None

    def create_analysis_crew(self):
        """Crea una crew con diversi modelli per analisi business"""

        # Agent Strategico con GPT-4o (più intelligente)
        strategic_analyst = Agent(
            role="Analista Strategico Senior",
            goal="Analizzare strategicamente il business e identificare opportunità",
            backstory="""Sei un consulente strategico con 20 anni di esperienza
            in trasformazione digitale e ottimizzazione dei processi aziendali.""",
            verbose=True,
            allow_delegation=False,
            llm=self.gpt4o or self.claude  # Usa GPT-4o o Claude come fallback
        )

        # Agent Dati con Groq Llama (veloce e gratis)
        data_analyst = Agent(
            role="Data Analyst",
            goal="Analizzare rapidamente grandi volumi di dati e pattern",
            backstory="""Specialista in analisi dati con competenze in
            statistica, machine learning e visualizzazione dati.""",
            verbose=True,
            allow_delegation=False,
            llm=self.groq_llama or self.qwen  # Usa Groq o Qwen (entrambi gratis)
        )

        # Agent Creativo con Claude (migliore per creatività)
        creative_advisor = Agent(
            role="Innovation Advisor",
            goal="Proporre soluzioni innovative e creative ai problemi",
            backstory="""Esperto di innovazione e design thinking,
            specializzato nel trovare soluzioni non convenzionali.""",
            verbose=True,
            allow_delegation=False,
            llm=self.claude or self.gemini  # Usa Claude o Gemini
        )

        # Agent Tecnico con Qwen Coder (ottimizzato per codice)
        technical_advisor = Agent(
            role="Technical Architect",
            goal="Valutare fattibilità tecnica e proporre architetture",
            backstory="""Architetto software con esperienza in sistemi
            distribuiti, cloud e automazione.""",
            verbose=True,
            allow_delegation=False,
            llm=self.qwen or self.groq_llama  # Usa Qwen o Groq
        )

        return [strategic_analyst, data_analyst, creative_advisor, technical_advisor]

    def analyze_business(self, process_description: str):
        """Esegue analisi business con multi-agent e diversi modelli"""

        agents = self.create_analysis_crew()

        # Task per ogni agent
        tasks = []

        # Task 1: Analisi strategica (GPT-4o)
        if agents[0].llm:
            tasks.append(Task(
                description=f"Analizza strategicamente: {process_description}",
                expected_output="Analisi strategica dettagliata con opportunità e rischi",
                agent=agents[0]
            ))

        # Task 2: Analisi dati (Groq - GRATIS)
        if agents[1].llm:
            tasks.append(Task(
                description=f"Analizza i pattern e metriche per: {process_description}",
                expected_output="Metriche chiave, KPI e pattern identificati",
                agent=agents[1]
            ))

        # Task 3: Soluzioni creative (Claude)
        if agents[2].llm:
            tasks.append(Task(
                description=f"Proponi soluzioni innovative per: {process_description}",
                expected_output="3-5 soluzioni creative e non convenzionali",
                agent=agents[2]
            ))

        # Task 4: Valutazione tecnica (Qwen)
        if agents[3].llm:
            tasks.append(Task(
                description=f"Valuta fattibilità tecnica per: {process_description}",
                expected_output="Architettura proposta e stack tecnologico",
                agent=agents[3]
            ))

        if not tasks:
            return {
                "success": False,
                "error": "Nessun modello AI disponibile. Configura almeno una API key."
            }

        # Crea ed esegui la crew
        crew = Crew(
            agents=[a for a in agents if a.llm is not None],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()

        # Estrai output
        if hasattr(result, 'output'):
            output = result.output
        elif hasattr(result, 'raw_output'):
            output = result.raw_output
        else:
            output = str(result)

        # Info sui modelli usati
        models_used = []
        for agent in agents:
            if agent.llm:
                if hasattr(agent.llm, 'model_name'):
                    models_used.append(agent.llm.model_name)
                elif hasattr(agent.llm, 'model'):
                    models_used.append(agent.llm.model)

        return {
            "success": True,
            "analysis": output,
            "models_used": models_used,
            "agents_count": len([a for a in agents if a.llm is not None])
        }


# Esempio di utilizzo
if __name__ == "__main__":
    # Configura le API keys che hai
    # os.environ["OPENAI_API_KEY"] = "sk-..."
    # os.environ["GROQ_API_KEY"] = "gsk-..."  # GRATIS!
    # os.environ["OPENROUTER_API_KEY"] = "sk-or-..."

    agents = MultiModelAgents()
    result = agents.analyze_business(
        "Ottimizzazione del processo di onboarding clienti per ridurre il tempo da 3 giorni a 1 ora"
    )

    print("\n=== RISULTATI ANALISI ===")
    print(f"Successo: {result.get('success')}")
    print(f"Modelli usati: {result.get('models_used')}")
    print(f"Numero agent: {result.get('agents_count')}")
    print(f"\nAnalisi:\n{result.get('analysis')}")