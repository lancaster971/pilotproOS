#!/usr/bin/env python3
"""
Milhena Orchestrator SIMPLIFIED - Flusso Consistente
Sistema enterprise con focus su consistenza e anti-allucinazione
"""

from crewai import Agent, Task, Crew, Process
from typing import Dict, Any
import logging
import time
import os

# Setup logger
logger = logging.getLogger(__name__)

# Import tools
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from tools.business_intelligent_query_tool import BusinessIntelligentQueryTool
    from tools.workflow_analyzer_tool import WorkflowAnalyzerTool
    from tools.pilotpro_metrics_tool import PilotProMetricsTool
    TOOLS_AVAILABLE = True
except ImportError as e:
    TOOLS_AVAILABLE = False
    logger.warning(f"Tools not available: {e}")

# Import LLM config
try:
    from agent_llm_config import get_llm_for_crewai
    LLM_CONFIG_AVAILABLE = True
except ImportError:
    LLM_CONFIG_AVAILABLE = False
    logger.warning("LLM config not available, using defaults")


class MilhenaSimplifiedOrchestrator:
    """
    Orchestrator semplificato con flusso consistente
    """

    def __init__(self):
        """Inizializza orchestrator con tools"""
        self.tools = []
        if TOOLS_AVAILABLE:
            self.tools = [
                BusinessIntelligentQueryTool(),
                WorkflowAnalyzerTool(),
                PilotProMetricsTool()
            ]
            logger.info(f"Loaded {len(self.tools)} tools")

        logger.info("INIT: Milhena Simplified Orchestrator ready")

    # === AGENT FACTORIES ===

    def create_entry_agent(self) -> Agent:
        llm = get_llm_for_crewai("classifier") if LLM_CONFIG_AVAILABLE else "gpt-4o-mini"
        return Agent(
            role="Question Classifier",
            goal="Classify the user question into exactly one category",
            backstory="""Classify into one of:
            - BUSINESS_DATA
            - HELP
            - GREETING
            - TECHNOLOGY""",
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

    def create_data_analyst_agent(self) -> Agent:
        llm = get_llm_for_crewai("data_analyst") if LLM_CONFIG_AVAILABLE else "gpt-4o-mini"
        return Agent(
            role="Data Analyst",
            goal="Query ONLY real data from database using tools",
            backstory="""Rules:
            1. NEVER guess
            2. ONLY report numbers from tools
            3. If unavailable, say 'Data not available'""",
            verbose=False,
            allow_delegation=False,
            tools=self.tools,
            llm=llm
        )

    def create_validator_agent(self) -> Agent:
        llm = get_llm_for_crewai("security_filter") if LLM_CONFIG_AVAILABLE else "gpt-4o-mini"
        return Agent(
            role="Fact Validator",
            goal="Verify the data analyst's output and ensure accuracy",
            backstory="""Rules:
            1. Check EVERY number
            2. Remove speculation
            3. If input is empty, say 'No data provided'""",
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

    def create_masking_agent(self) -> Agent:
        llm = get_llm_for_crewai("technology_masking") if LLM_CONFIG_AVAILABLE else "gpt-4o"
        return Agent(
            role="Business Language Translator",
            goal="Translate the validated data into business language",
            backstory="""Rules:
            1. Replace 'workflow' with 'business process'
            2. Replace 'execution' with 'process run'
            3. Replace 'node' with 'step'
            4. Replace 'n8n' with 'automation system'
            5. Keep ALL numbers and facts intact
            6. Make it understandable for a CEO""",
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

    # === PROCESSORS ===

    async def process_business_data(self, question: str) -> str:
        """
        Processo standard per BUSINESS_DATA
        Data Analyst → Validator → Masker
        """
        logger.info("BUSINESS_DATA: Starting pipeline")

        data_analyst = self.create_data_analyst_agent()
        validator = self.create_validator_agent()
        masking_agent = self.create_masking_agent()

        # Task pipeline con explicit keys
        analysis_task = Task(
            description=f"Answer using ONLY database data: {question}",
            agent=data_analyst,
            expected_output="Data-based answer with real numbers from tools",
            output_key="raw_data"
        )

        validation_task = Task(
            description="Verify the output of the data analyst. Remove speculation and unverified data.",
            agent=validator,
            expected_output="Validated data only",
            context=[analysis_task],  # Task object, non stringa!
            output_key="validated_data"
        )

        masking_task = Task(
            description="Translate the validated data into business language. Remove all technical terms.",
            agent=masking_agent,
            expected_output="Business-friendly response",
            context=[validation_task],  # Task object, non stringa!
            output_key="final_output"
        )

        crew = Crew(
            agents=[data_analyst, validator, masking_agent],
            tasks=[analysis_task, validation_task, masking_task],
            process=Process.sequential,
            verbose=True
        )

        start_time = time.time()
        result = crew.kickoff()
        elapsed = (time.time() - start_time) * 1000

        logger.info(f"BUSINESS_DATA: Completed in {elapsed:.0f}ms")
        logger.debug(f"Outputs: {result}")

        # result from CrewAI is already a string
        return str(result)

    async def process_greeting(self, question: str) -> str:
        responses = [
            "Ciao! Sono Milhena, il tuo assistente per i processi aziendali.",
            "Buongiorno! Sono qui per aiutarti con i tuoi processi business.",
            "Salve! Sono Milhena, specializzata nell'analisi dei processi aziendali."
        ]
        import random
        return random.choice(responses)

    async def process_help(self, question: str) -> str:
        return """Posso aiutarti con:

• **Monitoraggio Processi**: Visualizzare processi attivi e le loro esecuzioni
• **Analisi Performance**: Analizzare metriche e trend dei tuoi processi
• **Report Attività**: Generare report su cosa è successo oggi o nell'ultima settimana
• **Risoluzione Problemi**: Identificare processi con errori o rallentamenti
"""

    async def process_technology(self, question: str) -> str:
        return """I dettagli tecnici non sono accessibili per motivi di sicurezza.

Il sistema utilizza tecnologie moderne per:
• Automazione dei processi aziendali
• Integrazione con sistemi esterni
• Elaborazione dati in tempo reale
• Reportistica automatizzata
"""

    async def analyze_question(self, question: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Entry point principale
        """
        start_time = time.time()

        try:
            logger.info(f"Processing question: {question[:50]}...")

            entry_agent = self.create_entry_agent()
            classify_task = Task(
                description=f"Classify: {question}",
                agent=entry_agent,
                expected_output="One word: BUSINESS_DATA, HELP, GREETING, or TECHNOLOGY"
            )

            classify_crew = Crew(
                agents=[entry_agent],
                tasks=[classify_task],
                verbose=False
            )

            classification = str(classify_crew.kickoff()).strip().upper()
            logger.info(f"Classification: {classification}")

            if classification == "BUSINESS_DATA":
                response = await self.process_business_data(question)
                agents_used = 3
            elif classification == "GREETING":
                response = await self.process_greeting(question)
                agents_used = 1
            elif classification == "HELP":
                response = await self.process_help(question)
                agents_used = 1
            elif classification == "TECHNOLOGY":
                response = await self.process_technology(question)
                agents_used = 1
            else:
                response = await self.process_help(question)
                classification = "HELP"
                agents_used = 1

            elapsed = (time.time() - start_time) * 1000

            return {
                "success": True,
                "response": response,
                "question_type": classification,
                "response_time_ms": elapsed,
                "user_id": user_id,
                "agents_used": agents_used,
                "simplified": True
            }

        except Exception as e:
            logger.error(f"Error in simplified orchestrator: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Mi dispiace, si è verificato un errore nell'elaborazione della richiesta.",
                "user_id": user_id
            }


# Test
if __name__ == "__main__":
    import asyncio

    async def test():
        orchestrator = MilhenaSimplifiedOrchestrator()

        test_questions = [
            "Ciao!",
            "Come funziona il sistema?",
            "Quanti workflow attivi abbiamo?",
            "Quali tecnologie usate?"
        ]

        for q in test_questions:
            print(f"\n📝 Question: {q}")
            result = await orchestrator.analyze_question(q)
            print(f"   Type: {result.get('question_type')}")
            print(f"   Time: {result.get('response_time_ms', 0):.0f}ms")
            print(f"   Response: {result.get('response')[:120]}...")

    asyncio.run(test())
