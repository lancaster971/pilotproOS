#!/usr/bin/env python3
"""
Milhena Orchestrator SIMPLIFIED - Flusso Consistente 4 Agenti
Sistema enterprise con focus su consistenza e anti-allucinazione
"""

from crewai import Agent, Task, Crew, Process
from typing import Dict, Any, Optional, List
import logging
import json
import time
import os
from datetime import datetime

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
    Orchestrator semplificato con flusso consistente 4 agenti

    Principi:
    - Consistenza > Performance
    - Anti-allucinazione by design
    - Business language sempre
    - Nessun branch condizionale
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

    def create_entry_agent(self) -> Agent:
        """
        Entry Agent - Solo classificazione
        Output: Una parola tra BUSINESS_DATA, HELP, GREETING, TECHNOLOGY
        """
        llm = get_llm_for_crewai("classifier") if LLM_CONFIG_AVAILABLE else "gpt-4o-mini"

        return Agent(
            role="Question Classifier",
            goal="Classify the user question into exactly one category",
            backstory="""You are the entry point of Milhena. Your ONLY job is to classify
            questions into one of these categories:
            - BUSINESS_DATA: Questions about workflows, executions, metrics
            - HELP: Questions about how to use the system
            - GREETING: Greetings and small talk
            - TECHNOLOGY: Questions about technical implementation""",
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

    def create_data_analyst_agent(self) -> Agent:
        """
        Data Analyst - Solo query reali
        MAI supposizioni, solo dati dal database
        """
        llm = get_llm_for_crewai("data_analyst") if LLM_CONFIG_AVAILABLE else "gpt-4o-mini"

        return Agent(
            role="Data Analyst",
            goal="Query ONLY real data from database using tools",
            backstory="""You are a data analyst with access to business metrics.
            CRITICAL RULES:
            1. NEVER make assumptions or guesses
            2. ONLY report numbers you get from tools
            3. If data is not available, say 'Data not available'
            4. Every number must come from a tool query""",
            verbose=False,
            allow_delegation=False,
            tools=self.tools,
            llm=llm
        )

    def create_validator_agent(self) -> Agent:
        """
        Validator - Anti-allucinazione
        Verifica OGNI numero e affermazione
        """
        llm = get_llm_for_crewai("security_filter") if LLM_CONFIG_AVAILABLE else "gpt-4o-mini"

        return Agent(
            role="Fact Validator",
            goal="Verify the data analyst's output and ensure accuracy",
            backstory="""You receive data from the data analyst. Your job:
            1. Take the input data provided to you
            2. Check EVERY number is realistic
            3. Remove ANY speculation or assumption
            4. Output the SAME data but validated
            5. If input is empty, say 'No data provided'""",
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

    def create_masking_agent(self) -> Agent:
        """
        Masking Agent - Business language
        Traduce TUTTO in linguaggio non tecnico
        """
        llm = get_llm_for_crewai("technology_masking") if LLM_CONFIG_AVAILABLE else "gpt-4o"

        return Agent(
            role="Business Language Translator",
            goal="Translate the validated data into business language",
            backstory="""You receive validated data from the validator. Your job:
            1. Take the validated input provided to you
            2. Replace 'workflow' with 'business process'
            3. Replace 'execution' with 'process run'
            4. Replace 'node' with 'step'
            5. Replace 'n8n' with 'automation system'
            6. Keep ALL numbers and facts intact
            7. Make it understandable for a CEO""",
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

    async def process_business_data(self, question: str) -> str:
        """
        Processo standard per BUSINESS_DATA
        Sempre 4 agenti, sempre stesso ordine
        """
        logger.info("BUSINESS_DATA: Starting 4-agent pipeline")

        # Create agents
        entry_agent = self.create_entry_agent()
        data_analyst = self.create_data_analyst_agent()
        validator = self.create_validator_agent()
        masking_agent = self.create_masking_agent()

        # Create tasks WITH EXPLICIT DATA FLOW
        classification_task = Task(
            description=f"Classify this question: {question}",
            agent=entry_agent,
            expected_output="One word: BUSINESS_DATA, HELP, GREETING, or TECHNOLOGY",
            output_key="classification"
        )

        analysis_task = Task(
            description=f"Answer using ONLY database data: {question}",
            agent=data_analyst,
            expected_output="Data-based answer with real numbers from tools",
            output_key="raw_data"
        )

        validation_task = Task(
            description="Take the output from the data analyst and verify it. Remove all assumptions and speculation.",
            agent=validator,
            expected_output="Validated version of the data",
            context=[analysis_task],  # Prende output dal task precedente
            output_key="validated_data"
        )

        masking_task = Task(
            description="Take the validated data and translate it to business language. Remove all technical terms.",
            agent=masking_agent,
            expected_output="Business-friendly response",
            context=[validation_task]  # Prende output dal validator
        )

        # Create crew with sequential process and VERBOSE for debug
        crew = Crew(
            agents=[entry_agent, data_analyst, validator, masking_agent],
            tasks=[classification_task, analysis_task, validation_task, masking_task],
            process=Process.sequential,
            verbose=True  # Temporaneo per debug
        )

        # Execute with debug logging
        start_time = time.time()
        result = crew.kickoff()
        elapsed = (time.time() - start_time) * 1000

        # Debug: log outputs
        logger.info(f"BUSINESS_DATA: Completed in {elapsed:.0f}ms")
        logger.debug(f"Raw data: {analysis_task.output if hasattr(analysis_task, 'output') else 'N/A'}")
        logger.debug(f"Validated: {validation_task.output if hasattr(validation_task, 'output') else 'N/A'}")
        logger.debug(f"Final: {result}")

        return str(result)

    async def process_greeting(self, question: str) -> str:
        """Processo semplice per GREETING"""
        responses = [
            "Ciao! Sono Milhena, il tuo assistente per i processi aziendali. Come posso aiutarti?",
            "Buongiorno! Sono qui per aiutarti con i tuoi processi business. Cosa posso fare per te?",
            "Salve! Sono Milhena, specializzata nell'analisi dei processi aziendali. Di cosa hai bisogno?"
        ]
        import random
        return random.choice(responses)

    async def process_help(self, question: str) -> str:
        """Processo semplice per HELP"""
        return """Posso aiutarti con:

• **Monitoraggio Processi**: Visualizzare processi attivi e le loro esecuzioni
• **Analisi Performance**: Analizzare metriche e trend dei tuoi processi
• **Report Attività**: Generare report su cosa è successo oggi o nell'ultima settimana
• **Risoluzione Problemi**: Identificare processi con errori o rallentamenti

Esempi di domande:
- "Quanti processi attivi abbiamo?"
- "Cosa è successo oggi?"
- "Quali processi hanno avuto errori?"
- "Mostrami le performance dell'ultima settimana"
"""

    async def process_technology(self, question: str) -> str:
        """Processo per TECHNOLOGY - sempre mascherato"""
        return """I dettagli tecnici dell'implementazione non sono accessibili per motivi di sicurezza.

Il sistema utilizza tecnologie moderne per:
• Automazione dei processi aziendali
• Integrazione con sistemi esterni
• Elaborazione dati in tempo reale
• Reportistica automatizzata

Per informazioni specifiche sui tuoi processi, chiedimi dei dati o delle metriche."""

    async def analyze_question(self,
                              question: str,
                              user_id: str = "default") -> Dict[str, Any]:
        """
        Entry point principale - Routing semplificato

        1. Classifica sempre con entry_agent
        2. Route al processo appropriato
        3. Ritorna risposta consistente
        """
        start_time = time.time()

        try:
            # Step 1: Classificazione (sempre)
            logger.info(f"Processing question: {question[:50]}...")

            # Quick classification with entry agent
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

            # Step 2: Route al processo appropriato
            if classification == "BUSINESS_DATA":
                response = await self.process_business_data(question)
            elif classification == "GREETING":
                response = await self.process_greeting(question)
            elif classification == "HELP":
                response = await self.process_help(question)
            elif classification == "TECHNOLOGY":
                response = await self.process_technology(question)
            else:
                # Default fallback
                response = await self.process_help(question)
                classification = "HELP"

            # Step 3: Return consistente
            elapsed = (time.time() - start_time) * 1000

            return {
                "success": True,
                "response": response,
                "question_type": classification,
                "response_time_ms": elapsed,
                "user_id": user_id,
                "agents_used": 4 if classification == "BUSINESS_DATA" else 1,
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
            print(f"   Response: {result.get('response')[:100]}...")

    asyncio.run(test())