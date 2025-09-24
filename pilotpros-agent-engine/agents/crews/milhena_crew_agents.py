"""
Milhena Multi-Agent Crew - Sistema Intelligente PilotProOS
Crew specializzata con 3 agenti sequenziali per domande business
"""

from crewai import Agent, Task, Crew, Process
from typing import Dict, Any, Optional, List
import logging
import json
import re

# Import tools
from tools.milhena_data_tools import PilotProMetricsTool, WorkflowAnalyzerTool
from model_selector import ModelSelector, ModelCategory

logger = logging.getLogger(__name__)


class MilhenaMultiAgentCrew:
    """
    Sistema Multi-Agent Milhena per PilotProOS

    ARCHITETTURA SEQUENZIALE:
    1. DATA_ANALYST → Raccoglie dati dal sistema
    2. SECURITY_FILTER → Censura dettagli tecnici
    3. MILHENA → Interfaccia finale in italiano business
    """

    def __init__(self, model_selector: Optional[ModelSelector] = None):
        """
        Inizializza la Crew Milhena

        Args:
            model_selector: Selettore modelli LLM (opzionale)
        """
        self.model_selector = model_selector or ModelSelector()
        self.tools = [
            PilotProMetricsTool(),
            WorkflowAnalyzerTool()
        ]

    def create_data_analyst_agent(self) -> Agent:
        """
        DATA_ANALYST - Esperto raccolta e analisi dati
        LLM: ADAPTIVE (GPT-4o per analisi complesse, Groq per query semplici)
        """
        # Seleziona modello appropriato per analisi dati
        provider, model = self.model_selector.get_model(ModelCategory.POTENTE)
        llm = None  # CrewAI gestirà il modello automaticamente

        return Agent(
            role="Business Intelligence Data Analyst",
            goal="Raccogliere e analizzare dati accurati dal sistema PilotProOS per rispondere a domande business",
            backstory="""Sei un analista dati esperto specializzato nel sistema PilotProOS.
            La tua responsabilità è raccogliere dati precisi e affidabili dal database aziendale.

            COMPITI:
            - Eseguire query sui dati di processo e workflow
            - Calcolare metriche e KPI business
            - Identificare trend e anomalie
            - Fornire dati grezzi accurati per l'analisi

            REGOLE:
            - Sempre verificare l'accuratezza dei dati
            - Includere timestamp e contesto
            - Fornire dati strutturati in JSON
            - Non interpretare, solo raccogliere e organizzare""",
            tools=self.tools,
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

    def create_security_filter_agent(self) -> Agent:
        """
        SECURITY_FILTER - Guardiano sicurezza informazioni
        LLM: Groq Llama-3.2-70B (veloce + economico per pattern matching)
        """
        # Usa modello veloce ed economico per filtering
        provider, model = self.model_selector.get_model(ModelCategory.GRATIS)
        llm = None  # CrewAI gestirà il modello automaticamente

        return Agent(
            role="Information Security & Compliance Filter",
            goal="Filtrare e censurare tutti i dettagli tecnici dalle risposte mantenendo solo informazioni business-appropriate",
            backstory="""Sei il guardiano della sicurezza delle informazioni per PilotProOS.
            La tua missione è proteggere i dettagli tecnici sensibili e mantenere solo terminologia business.

            REGOLE FERREE - MAI RIVELARE:
            - Tecnologie: n8n, PostgreSQL, Docker, Redis, FastAPI
            - Architettura: database schema, API endpoints, container
            - Dettagli tecnici: query SQL, error logs, stack traces
            - Configurazioni: ports, URLs, credentials, environment
            - Nomi interni: workflow_entity, execution_entity, node types

            TRASFORMAZIONI OBBLIGATORIE:
            - "workflow" → "processo di automazione"
            - "execution" → "esecuzione processo"
            - "node" → "passaggio"
            - "database" → "sistema dati"
            - "API" → "interfaccia sistema"
            - "container" → "servizio"
            - "n8n" → "piattaforma automazione"
            - "error log" → "segnalazione sistema"

            OUTPUT:
            - Solo dati business-friendly
            - Terminologia aziendale italiana
            - Zero riferimenti tecnici""",
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

    def create_milhena_agent(self) -> Agent:
        """
        MILHENA - Assistant italiana finale per utente business
        LLM: ADAPTIVE (Gemini-Pro per italiano naturale)
        """
        # Modello bilanciato per conversazione italiana
        provider, model = self.model_selector.get_model(ModelCategory.LEGGERO)
        llm = None  # CrewAI gestirà il modello automaticamente

        return Agent(
            role="Milhena - Assistente Business PilotProOS",
            goal="Essere l'assistente aziendale italiana perfetta, professionale e proattiva per gli utenti PilotProOS",
            backstory="""Ciao! Sono Milhena, la tua assistente digitale specializzata in PilotProOS.

            PERSONALITÀ:
            - Italiana autentica, professionale ma amichevole
            - Esperta di processi aziendali e automazione business
            - Proattiva: sempre pronta a suggerire approfondimenti
            - Orientata ai risultati e al miglioramento continuo

            STILE COMUNICAZIONE:
            - Italiano business naturale e fluente
            - Risposte concise ma complete
            - Tono professionale ma caldo
            - Sempre positiva e solution-oriented

            SPECIALIZZAZIONI:
            - Metriche performance processi business
            - Analisi trend e identificazione problemi
            - Suggerimenti di ottimizzazione
            - Reporting e insights aziendali

            APPROCCIO:
            1. Rispondere direttamente alla domanda
            2. Fornire contesto e insights utili
            3. Suggerire azioni o approfondimenti
            4. Essere sempre disponibile per chiarimenti

            ESEMPIO RISPOSTA:
            "Il processo di email marketing ha elaborato 1.247 messaggi oggi, con un tasso di successo del 96.2%.
            Ottimo risultato! Ho notato un leggero miglioramento rispetto alla settimana scorsa.
            Vuoi che analizzi i dettagli delle performance per orario o vuoi vedere il confronto con gli obiettivi mensili?"
            """,
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

    def analyze_business_question(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Analizza una domanda business usando la crew multi-agent sequenziale

        Args:
            question: Domanda business dell'utente
            context: Contesto aggiuntivo opzionale

        Returns:
            Risposta processata da tutti e 3 gli agenti
        """
        try:
            # Crea gli agenti
            data_analyst = self.create_data_analyst_agent()
            security_filter = self.create_security_filter_agent()
            milhena = self.create_milhena_agent()

            # TASK 1: DATA_ANALYST - Raccolta dati
            data_task = Task(
                description=f"""
                Analizza la seguente domanda business e raccogli tutti i dati necessari:

                DOMANDA: {question}
                CONTESTO: {context or 'Nessun contesto aggiuntivo'}

                ISTRUZIONI:
                1. Identifica che tipo di dati servono per rispondere
                2. Usa i tool disponibili per raccogliere metriche appropriate
                3. Organizza i dati in formato strutturato
                4. Includi timestamp e dettagli di contesto
                5. Fornisci dati grezzi accurati senza interpretazioni

                OUTPUT RICHIESTO:
                - Dati numerici precisi
                - Contesto temporale
                - Informazioni correlate utili
                - Formato JSON strutturato
                """,
                agent=data_analyst,
                expected_output="Dati strutturati e accurati dal sistema PilotProOS in formato JSON"
            )

            # TASK 2: SECURITY_FILTER - Filtraggio sicurezza
            security_task = Task(
                description=f"""
                Filtra la risposta del Data Analyst rimuovendo TUTTI i dettagli tecnici:

                REGOLE FERREE:
                - Rimuovi qualsiasi riferimento a tecnologie (n8n, PostgreSQL, API, database)
                - Trasforma terminologia tecnica in business terms
                - Mantieni solo dati numerici e insights business
                - Usa terminologia aziendale italiana

                TRASFORMAZIONI OBBLIGATORIE:
                - "workflow" → "processo"
                - "execution" → "esecuzione"
                - "error" → "anomalia" o "necessita attenzione"
                - "database query" → "consultazione dati"
                - "API call" → "richiesta sistema"

                OUTPUT:
                Solo informazioni business-safe in italiano professionale
                """,
                agent=security_filter,
                expected_output="Informazioni filtrate e business-appropriate in italiano"
            )

            # TASK 3: MILHENA - Risposta finale
            milhena_task = Task(
                description=f"""
                Crea la risposta finale per l'utente business basandoti sui dati filtrati:

                DOMANDA ORIGINALE: {question}

                STILE RICHIESTO:
                - Italiano business naturale e professionale
                - Risposta diretta e utile
                - Includi insights e suggerimenti proattivi
                - Tono amichevole ma professionale
                - Concludi con offerta di ulteriore assistenza

                STRUTTURA RISPOSTA:
                1. Risposta diretta alla domanda
                2. Insights e contesto utile
                3. Suggerimento proattivo
                4. Disponibilità per approfondimenti

                ESEMPIO:
                "Il processo X ha elaborato Y elementi oggi con Z% di successo. [Insight]. [Suggerimento]. Posso aiutarti con altro?"
                """,
                agent=milhena,
                expected_output="Risposta finale business-friendly in italiano perfetto"
            )

            # Crea la crew sequenziale
            crew = Crew(
                agents=[data_analyst, security_filter, milhena],
                tasks=[data_task, security_task, milhena_task],
                process=Process.sequential,
                verbose=False
            )

            # Esegui la crew
            logger.info(f"Milhena Crew: Processando domanda business")
            result = crew.kickoff()

            return {
                "success": True,
                "question": question,
                "response": str(result),
                "system": "Milhena Multi-Agent System",
                "agents_used": ["DATA_ANALYST", "SECURITY_FILTER", "MILHENA"],
                "process_type": "sequential_multi_agent",
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            logger.error(f"Milhena Crew error: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "Mi dispiace, al momento non posso elaborare la tua richiesta. Il sistema è temporaneamente non disponibile.",
                "system": "Milhena Multi-Agent System",
                "timestamp": self._get_timestamp()
            }

    def _get_timestamp(self) -> str:
        """Ottieni timestamp ISO"""
        from datetime import datetime
        return datetime.now().isoformat()


class QuickMilhenaAgent:
    """
    Versione semplificata di Milhena per domande veloci
    Usa solo l'agent finale senza crew complessa
    """

    def __init__(self, model_selector: Optional[ModelSelector] = None):
        self.model_selector = model_selector or ModelSelector()
        self.tools = [PilotProMetricsTool(), WorkflowAnalyzerTool()]

    def quick_answer(self, question: str) -> Dict[str, Any]:
        """Risposta rapida con singolo agent"""
        try:
            provider, model = self.model_selector.get_model(ModelCategory.LEGGERO)
            llm = None  # CrewAI gestirà il modello automaticamente

            milhena = Agent(
                role="Milhena Quick Assistant",
                goal="Fornire risposte business rapide e accurate",
                backstory="""Sono Milhena, assistente business PilotProOS.
                Fornisco risposte rapide e precise su metriche e processi aziendali.
                Sempre in italiano professionale e business-oriented.""",
                tools=self.tools,
                verbose=False,
                llm=llm
            )

            task = Task(
                description=f"""
                Rispondi a questa domanda business in modo rapido e preciso:
                {question}

                Usa terminologia business italiana, mai dettagli tecnici.
                Risposte concise ma complete.
                """,
                agent=milhena,
                expected_output="Risposta business in italiano"
            )

            crew = Crew(
                agents=[milhena],
                tasks=[task],
                process=Process.sequential,
                verbose=False
            )

            result = crew.kickoff()

            return {
                "success": True,
                "response": str(result),
                "system": "Milhena Quick Mode",
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "Mi dispiace, problema temporaneo del sistema."
            }

    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()