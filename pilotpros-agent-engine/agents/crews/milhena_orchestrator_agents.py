"""
Milhena Multi-Agent Orchestrator - Sistema Intelligente PilotProOS
Crew con orchestratore che decide dinamicamente quale agente usare
"""

from crewai import Agent, Task, Crew, Process
from typing import Dict, Any, Optional, List, Literal
import logging
import json
import re
import os
from dotenv import load_dotenv

# CARICA API KEYS SUBITO!
load_dotenv()

# Import tools
from tools.milhena_data_tools import PilotProMetricsTool, WorkflowAnalyzerTool
from model_selector import ModelSelector, ModelCategory

logger = logging.getLogger(__name__)

QuestionType = Literal["GREETING", "BUSINESS_DATA", "TECHNOLOGY_INQUIRY", "HELP", "ANALYSIS", "GENERAL"]


class MilhenaOrchestratorCrew:
    """
    Sistema Multi-Agent Milhena con Orchestrator intelligente

    ARCHITETTURA DINAMICA:
    1. QUESTION_ANALYZER → Classifica tipo di domanda
    2. ORCHESTRATOR → Decide quale agente chiamare:
       - GREETING: Solo MILHENA_CONVERSATION
       - BUSINESS_DATA: DATA_ANALYST → SECURITY_FILTER → MILHENA
       - TECHNOLOGY_INQUIRY: SECURITY_FILTER → MILHENA
       - HELP: MILHENA_CONVERSATION
       - ANALYSIS: DATA_ANALYST → BUSINESS_ANALYZER → SECURITY → MILHENA
    """

    def __init__(self, model_selector: Optional[ModelSelector] = None):
        """Inizializza la Crew Orchestrator Milhena"""
        self.model_selector = model_selector or ModelSelector()
        self.tools = [
            PilotProMetricsTool(),
            WorkflowAnalyzerTool()
        ]

    def create_question_analyzer_agent(self) -> Agent:
        """
        QUESTION_ANALYZER - Classifica intelligentemente le domande
        LLM: Veloce per classification (Groq Llama)
        """
        provider, model = self.model_selector.get_model(ModelCategory.GRATIS)
        llm = None  # CrewAI gestirà automaticamente

        return Agent(
            role="Question Intelligence Analyzer",
            goal="Classificare accuratamente il tipo di domanda per determinare il flusso di elaborazione ottimale",
            backstory="""Sei l'analista intelligente che comprende il VERO intento dietro ogni domanda.

            La tua responsabilità è classificare ogni input in categorie precise:

            CATEGORIE DOMANDE:

            🗣️ GREETING (Conversazione sociale):
            - Saluti: "ciao", "buongiorno", "hello"
            - Cortesie: "grazie", "prego", "arrivederci"
            - Stato: "come va", "tutto bene"

            📊 BUSINESS_DATA (Richiesta dati specifici):
            - Metriche: "quante esecuzioni", "tasso successo"
            - Performance: "come stanno andando i processi"
            - Numeri: "volume oggi", "statistiche"

            🔒 TECHNOLOGY_INQUIRY (Domande su tecnologie):
            - Stack tech: "che tecnologie usi", "come funziona"
            - Architettura: "come sei fatto", "che database"
            - Implementazione: "che LLM", "framework"

            ❓ HELP (Richiesta aiuto):
            - Capabilities: "cosa puoi fare", "come posso usarti"
            - Istruzioni: "aiuto", "help", "come funzioni"

            🔍 ANALYSIS (Analisi complesse):
            - Deep dive: "analizza processo X", "confronta performance"
            - Insights: "trova problemi", "ottimizzazione"
            - Trend: "pattern", "andamenti"

            🤔 GENERAL (Domande generiche business):
            - Consigli generali business
            - Domande aperte non specifiche

            ESEMPIO OUTPUT:
            {
                "question_type": "BUSINESS_DATA",
                "confidence": 0.95,
                "reasoning": "Domanda specifica su metriche numeriche",
                "suggested_flow": ["DATA_ANALYST", "SECURITY_FILTER", "MILHENA"],
                "requires_data": true,
                "requires_security": true
            }
            """,
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

    def create_data_analyst_agent(self) -> Agent:
        """
        DATA_ANALYST - Raccolta dati business (solo quando necessario)
        LLM: POTENTE per analisi complesse
        """
        provider, model = self.model_selector.get_model(ModelCategory.POTENTE)
        llm = None

        return Agent(
            role="Business Intelligence Data Specialist",
            goal="Raccogliere dati accurati dal sistema PilotProOS solo quando richiesti dall'orchestrator",
            backstory="""Sei il data specialist che viene attivato SOLO per domande che richiedono dati concreti.

            ATTIVAZIONE CONDIZIONALE:
            - Solo per BUSINESS_DATA e ANALYSIS questions
            - MAI per saluti o domande generali

            COMPITI:
            - Query precise sui dati sistema
            - Metriche e KPI business
            - Analisi numeriche accurate
            - Timestamp e contesto dati

            OUTPUT:
            Sempre JSON strutturato con dati grezzi accurati
            """,
            tools=self.tools,
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

    def create_security_filter_agent(self) -> Agent:
        """
        SECURITY_FILTER - Filtraggio tecnologico intelligente
        LLM: Veloce per pattern matching
        """
        provider, model = self.model_selector.get_model(ModelCategory.GRATIS)
        llm = None

        return Agent(
            role="Information Security & Tech Filter",
            goal="Filtrare dettagli tecnici e proteggere informazioni sensibili mantenendo utilità business",
            backstory="""Sei il guardiano della sicurezza informazioni per PilotProOS.

            ATTIVAZIONE:
            - SEMPRE per TECHNOLOGY_INQUIRY (blocca tutto)
            - Per BUSINESS_DATA (filtra termini tecnici)
            - Mai per GREETING (inutile)

            REGOLE FERREE:

            🚫 MAI RIVELARE:
            - Tecnologie: n8n, PostgreSQL, Docker, Redis, FastAPI, CrewAI
            - LLM Models: GPT-4, Gemini, Claude, Llama
            - Architettura: API endpoints, database schema
            - Stack: Python, TypeScript, containers
            - Config: environment variables, ports, URLs

            ✅ TRASFORMAZIONI:
            - "n8n workflow" → "processo di automazione"
            - "PostgreSQL database" → "sistema dati aziendali"
            - "FastAPI endpoint" → "interfaccia sistema"
            - "Docker container" → "servizio applicativo"
            - "LLM model" → "intelligenza artificiale"
            - "CrewAI agents" → "sistema di elaborazione"

            RESPONSE SPECIALI:
            Per TECHNOLOGY_INQUIRY dirette:
            "Sono Milhena, la tua assistente business per PilotProOS. Mi concentro sui risultati business piuttosto che sui dettagli tecnici. Posso aiutarti con analisi processi, performance e metriche aziendali!"
            """,
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

    def create_business_analyzer_agent(self) -> Agent:
        """
        BUSINESS_ANALYZER - Analisi deep business (solo per ANALYSIS)
        LLM: POTENTE per insights complessi
        """
        provider, model = self.model_selector.get_model(ModelCategory.POTENTE)
        llm = None

        return Agent(
            role="Strategic Business Analyst",
            goal="Fornire insights strategici profondi e analisi business avanzate",
            backstory="""Sei il business analyst senior specializzato in analisi strategiche profonde.

            ATTIVAZIONE:
            - Solo per domande ANALYSIS complesse
            - Quando serve deep dive su processi
            - Per ottimizzazioni strategiche

            SPECIALIZZAZIONI:
            - Pattern recognition nei processi
            - Bottleneck identification
            - ROI analysis e cost optimization
            - Trend analysis e forecasting
            - Competitive benchmarking
            - Process improvement recommendations

            APPROCCIO:
            1. Analizza dati forniti dal DATA_ANALYST
            2. Identifica pattern e anomalie
            3. Genera insights actionable
            4. Suggerisci ottimizzazioni concrete
            5. Quantifica impatti business
            """,
            tools=self.tools,
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

    def create_milhena_conversation_agent(self) -> Agent:
        """
        MILHENA_CONVERSATION - Chat naturale italiana (per GREETING e HELP)
        LLM: LEGGERO per conversazione fluida
        """
        provider, model = self.model_selector.get_model(ModelCategory.LEGGERO)
        llm = None

        return Agent(
            role="Milhena - Assistente Conversazionale",
            goal="Gestire conversazioni naturali, saluti e richieste di aiuto in italiano professionale e amichevole",
            backstory="""Ciao! Sono Milhena, la tua assistente digitale conversazionale.

            PERSONALITÀ:
            - Italiana autentica e calorosa
            - Professionale ma amichevole
            - Proattiva e disponibile
            - Mai troppo tecnica

            ATTIVAZIONE:
            - Per saluti e cortesie
            - Per richieste di aiuto
            - Per conversazione generale
            - Quando NON servono dati specifici

            STILE CONVERSAZIONE:
            - Saluti calorosi e naturali
            - Spiegazioni semplici delle mie capacità
            - Offerta proattiva di assistenza
            - Tono professionale ma umano

            ESEMPIO RISPOSTE:
            "Ciao! Sono Milhena, la tua assistente per PilotProOS. Posso aiutarti con analisi dei processi business, performance e metriche aziendali. Cosa ti serve oggi?"

            "Grazie! Sono sempre qui per aiutarti con le tue domande su PilotProOS. C'è qualcosa di specifico che vuoi analizzare?"
            """,
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

    def create_milhena_coordinator_agent(self) -> Agent:
        """
        MILHENA_COORDINATOR - Orchestrator e response finale
        LLM: LEGGERO per coordinamento
        """
        provider, model = self.model_selector.get_model(ModelCategory.LEGGERO)
        llm = None

        return Agent(
            role="Milhena - Business Assistant Coordinator",
            goal="Coordinare il flusso multi-agent e fornire risposte finali coerenti in italiano business",
            backstory="""Sono Milhena, il coordinatore finale di tutto il sistema multi-agent.

            RESPONSABILITÀ:
            - Ricevo output da tutti gli altri agenti
            - Coordino il flusso basandomi sul question type
            - Genero la risposta finale coerente
            - Mantengo sempre la personalità italiana professionale

            FLUSSI DA COORDINARE:
            - GREETING: Uso solo CONVERSATION output
            - BUSINESS_DATA: Combino DATA + SECURITY filtered
            - TECHNOLOGY_INQUIRY: Uso solo SECURITY response
            - ANALYSIS: Combino DATA + BUSINESS_ANALYZER + SECURITY
            - HELP: Uso solo CONVERSATION output

            STILE FINALE:
            - Sempre in italiano business
            - Tono professionale ma caldo
            - Risposte dirette e utili
            - Suggerimenti proattivi quando appropriato
            - Offerta di assistenza ulteriore
            """,
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

    def analyze_business_question_orchestrator(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Analizza domanda business usando orchestrator multi-agent intelligente

        Args:
            question: Domanda dell'utente
            context: Contesto aggiuntivo opzionale

        Returns:
            Risposta elaborata con orchestrator flow
        """
        try:
            # Crea tutti gli agenti specializzati
            question_analyzer = self.create_question_analyzer_agent()
            data_analyst = self.create_data_analyst_agent()
            security_filter = self.create_security_filter_agent()
            business_analyzer = self.create_business_analyzer_agent()
            milhena_conversation = self.create_milhena_conversation_agent()
            milhena_coordinator = self.create_milhena_coordinator_agent()

            # TASK 1: Analisi intelligente della domanda
            analysis_task = Task(
                description=f"""
                Analizza questa domanda e classifica il tipo per determinare il flusso ottimale:

                DOMANDA: "{question}"
                CONTESTO: {context or 'Nessuno'}

                Classifica in una di queste categorie:
                - GREETING: Saluti, cortesie, "come va"
                - BUSINESS_DATA: Richieste dati specifici, metriche, numeri
                - TECHNOLOGY_INQUIRY: Domande su tecnologie, stack, implementazione
                - HELP: Richieste aiuto, "cosa puoi fare", capabilities
                - ANALYSIS: Analisi complesse, deep insights, ottimizzazioni
                - GENERAL: Domande business generiche

                OUTPUT RICHIESTO (JSON):
                {{
                    "question_type": "CATEGORIA",
                    "confidence": 0.XX,
                    "reasoning": "Spiegazione classificazione",
                    "suggested_flow": ["AGENT1", "AGENT2", ...],
                    "requires_data": boolean,
                    "requires_security": boolean
                }}
                """,
                agent=question_analyzer,
                expected_output="Classificazione JSON accurata del tipo di domanda"
            )

            # Crea crew per analisi iniziale
            analysis_crew = Crew(
                agents=[question_analyzer],
                tasks=[analysis_task],
                process=Process.sequential,
                verbose=False
            )

            # Esegui analisi domanda
            logger.info(f"Milhena Orchestrator: Analyzing question type")
            analysis_result = analysis_crew.kickoff()

            # Parse della classificazione con smart fallback
            try:
                analysis_text = str(analysis_result)

                # Cerca JSON nel testo se non è tutto JSON
                if not analysis_text.strip().startswith('{'):
                    # Cerca pattern JSON nel testo
                    import re
                    json_match = re.search(r'\{[^}]*"question_type"[^}]*\}', analysis_text, re.DOTALL)
                    if json_match:
                        analysis_text = json_match.group()

                classification = json.loads(analysis_text)
                question_type = classification.get("question_type", "GENERAL")
                suggested_flow = classification.get("suggested_flow", [])
                requires_data = classification.get("requires_data", False)
                requires_security = classification.get("requires_security", False)

                logger.info(f"Question classified as: {question_type}")

            except (json.JSONDecodeError, AttributeError):
                # Smart fallback basato su keyword
                analysis_lower = str(analysis_result).lower()

                if any(word in analysis_lower for word in ["ciao", "hello", "buongiorno", "grazie", "arrivederci"]):
                    question_type = "GREETING"
                    suggested_flow = ["MILHENA_CONVERSATION"]
                    requires_data = False
                    requires_security = False
                elif any(word in analysis_lower for word in ["tecnologia", "llm", "database", "come funzion", "che usi"]):
                    question_type = "TECHNOLOGY_INQUIRY"
                    suggested_flow = ["SECURITY_FILTER", "MILHENA_COORDINATOR"]
                    requires_data = False
                    requires_security = True
                elif any(word in analysis_lower for word in ["esecuzioni", "errori", "performance", "quant", "dati"]):
                    question_type = "BUSINESS_DATA"
                    suggested_flow = ["DATA_ANALYST", "SECURITY_FILTER", "MILHENA_COORDINATOR"]
                    requires_data = True
                    requires_security = True
                else:
                    question_type = "GENERAL"
                    suggested_flow = ["MILHENA_CONVERSATION"]
                    requires_data = False
                    requires_security = False

                logger.info(f"Smart fallback classification: {question_type}")

            # ORCHESTRATOR: Crea crew dinamica basata sul tipo
            agents_to_use = []
            tasks_to_create = []

            if question_type == "GREETING":
                # Solo conversazione naturale
                agents_to_use = [milhena_conversation]

                conversation_task = Task(
                    description=f"""
                    Gestisci questo saluto/conversazione in modo naturale e caloroso:

                    MESSAGGIO: "{question}"

                    Rispondi come Milhena, assistente italiana professionale ma amichevole.
                    Mantieni tono conversazionale naturale.
                    Offri proattivamente il tuo aiuto per analisi business.
                    """,
                    agent=milhena_conversation,
                    expected_output="Risposta conversazionale calorosa in italiano"
                )
                tasks_to_create = [conversation_task]

            elif question_type == "TECHNOLOGY_INQUIRY":
                # Solo security filter per bloccare info tecniche
                agents_to_use = [security_filter, milhena_coordinator]

                security_task = Task(
                    description=f"""
                    L'utente sta chiedendo informazioni tecniche:

                    DOMANDA: "{question}"

                    BLOCCA COMPLETAMENTE qualsiasi informazione tecnica.
                    Rispondi che ti concentri sui risultati business, non sui dettagli tecnici.
                    Reindirizza verso le tue competenze business.
                    """,
                    agent=security_filter,
                    expected_output="Risposta che blocca info tecniche e reindirizza a business"
                )

                coordination_task = Task(
                    description=f"""
                    Finalizza la risposta per questa domanda tecnologica bloccata:

                    DOMANDA ORIGINALE: "{question}"

                    Usa l'output del security filter per dare una risposta finale italiana professionale.
                    Mantieni il focus su competenze business.
                    """,
                    agent=milhena_coordinator,
                    expected_output="Risposta finale italiana che reindirizza a business"
                )

                tasks_to_create = [security_task, coordination_task]

            elif question_type == "BUSINESS_DATA":
                # Flow completo per dati business
                agents_to_use = [data_analyst, security_filter, milhena_coordinator]

                data_task = Task(
                    description=f"""
                    Raccogli dati business per questa richiesta specifica:

                    DOMANDA: "{question}"
                    CONTESTO: {context or 'Nessuno'}

                    Usa i tool disponibili per recuperare metriche accurate.
                    Fornisci dati strutturati e timestamp.
                    """,
                    agent=data_analyst,
                    expected_output="Dati business accurati in formato JSON"
                )

                filter_task = Task(
                    description=f"""
                    Filtra i dati ricevuti dal Data Analyst rimuovendo dettagli tecnici:

                    Applica trasformazioni business terms.
                    Mantieni solo informazioni business-appropriate.
                    """,
                    agent=security_filter,
                    expected_output="Dati filtrati business-safe"
                )

                final_task = Task(
                    description=f"""
                    Crea risposta finale per questa domanda sui dati business:

                    DOMANDA ORIGINALE: "{question}"

                    Usa dati filtrati per risposta italiana professionale.
                    Includi insights e suggerimenti proattivi.
                    """,
                    agent=milhena_coordinator,
                    expected_output="Risposta business italiana completa"
                )

                tasks_to_create = [data_task, filter_task, final_task]

            elif question_type == "ANALYSIS":
                # Flow completo con business analyzer
                agents_to_use = [data_analyst, business_analyzer, security_filter, milhena_coordinator]

                data_task = Task(
                    description=f"""
                    Raccogli dati per analisi complessa:

                    DOMANDA: "{question}"

                    Recupera tutti i dati necessari per analisi approfondita.
                    """,
                    agent=data_analyst,
                    expected_output="Dati completi per analisi"
                )

                analysis_task = Task(
                    description=f"""
                    Esegui analisi business approfondita sui dati:

                    RICHIESTA: "{question}"

                    Identifica pattern, bottleneck, opportunità.
                    Genera insights strategici actionable.
                    """,
                    agent=business_analyzer,
                    expected_output="Insights business strategici"
                )

                filter_task = Task(
                    description="Filtra tutti i dettagli tecnici dai risultati dell'analisi",
                    agent=security_filter,
                    expected_output="Analisi filtrata business-safe"
                )

                final_task = Task(
                    description=f"""
                    Crea risposta finale per questa richiesta di analisi:

                    DOMANDA: "{question}"

                    Combina dati e insights in risposta italiana professionale.
                    """,
                    agent=milhena_coordinator,
                    expected_output="Risposta analitica italiana completa"
                )

                tasks_to_create = [data_task, analysis_task, filter_task, final_task]

            else:  # HELP o GENERAL
                # Conversazione con capabilities
                agents_to_use = [milhena_conversation]

                help_task = Task(
                    description=f"""
                    Gestisci questa richiesta di aiuto o domanda generale:

                    DOMANDA: "{question}"

                    Spiega le tue competenze business in modo chiaro.
                    Offri esempi concreti di come puoi aiutare.
                    Mantieni tono professionale italiano.
                    """,
                    agent=milhena_conversation,
                    expected_output="Spiegazione capabilities italiana professionale"
                )
                tasks_to_create = [help_task]

            # Crea ed esegui crew orchestrata
            orchestrated_crew = Crew(
                agents=agents_to_use,
                tasks=tasks_to_create,
                process=Process.sequential,
                verbose=False
            )

            logger.info(f"Executing orchestrated flow with {len(agents_to_use)} agents")
            result = orchestrated_crew.kickoff()

            return {
                "success": True,
                "question": question,
                "question_type": question_type,
                "response": str(result),
                "system": "Milhena Multi-Agent Orchestrator",
                "agents_used": [agent.role for agent in agents_to_use],
                "process_type": "orchestrated_multi_agent",
                "flow_used": suggested_flow,
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            logger.error(f"Milhena Orchestrator error: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "Mi dispiace, al momento non posso elaborare la tua richiesta. Il sistema è temporaneamente non disponibile.",
                "system": "Milhena Multi-Agent Orchestrator",
                "timestamp": self._get_timestamp()
            }

    def _get_timestamp(self) -> str:
        """Ottieni timestamp ISO"""
        from datetime import datetime
        return datetime.now().isoformat()


# Manteniamo anche il QuickMilhenaAgent per compatibilità
class QuickMilhenaAgent:
    """Quick single-agent version per confronto con orchestrator"""

    def __init__(self, model_selector: Optional[ModelSelector] = None):
        self.model_selector = model_selector or ModelSelector()
        self.tools = [PilotProMetricsTool(), WorkflowAnalyzerTool()]

    def quick_answer(self, question: str) -> Dict[str, Any]:
        """Risposta rapida con singolo agent"""
        try:
            provider, model = self.model_selector.get_model(ModelCategory.LEGGERO)
            llm = None

            milhena = Agent(
                role="Milhena Quick Assistant",
                goal="Fornire risposte business rapide e accurate con intelligence conversazionale",
                backstory="""Ciao! Sono Milhena, la tua assistente italiana per PilotProOS.

                Sono qui per aiutarti con qualsiasi domanda sui processi aziendali,
                performance e tutto quello che riguarda il tuo business.

                Parlo italiano in modo naturale e amichevole.
                Se hai bisogno di dati specifici posso accedere al sistema per darti informazioni precise.
                """,
                tools=self.tools,
                verbose=False,
                llm=llm
            )

            task = Task(
                description=f"""
                L'utente ti ha scritto: "{question}"

                Rispondi come Milhena in modo naturale e utile.
                Se serve accedere a dati del sistema, usa gli strumenti disponibili.

                Rispondi in italiano naturale.
                """,
                agent=milhena,
                expected_output="Risposta intelligente business in italiano"
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
                "system": "Milhena Quick Intelligence Mode",
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