"""
Simple Agent System - Minimal working example
"""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
import os


class SimpleAssistantAgents:
    """Simple assistant using multi-agent system"""

    def __init__(self):
        """Initialize the agent system"""
        # Use OpenAI if available, otherwise use a mock
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0.7,
                api_key=api_key
            )
        else:
            # Fallback - CrewAI will handle missing LLM
            self.llm = None

    def create_agent(self, language: str = "italian"):
        """Create the assistant agent"""
        if language == "italian":
            return Agent(
                role="Assistente PilotPro",
                goal="Aiutare gli utenti con le loro domande sul sistema PilotPro, rispondendo sempre in italiano",
                backstory="""Sei un assistente AI esperto per il sistema PilotPro.
                Aiuti gli utenti a comprendere i processi aziendali, l'automazione e l'analisi dei dati.
                Rispondi SEMPRE in italiano in modo professionale, chiaro e conciso.""",
                verbose=False,
                allow_delegation=False,
                llm=self.llm
            )
        else:
            return Agent(
                role="PilotPro Assistant",
                goal="Help users with their questions about the PilotPro system",
                backstory="""You are an expert AI assistant for the PilotPro system.
                You help users understand business processes, automation, and analytics.""",
                verbose=False,
                allow_delegation=False,
                llm=self.llm
            )

    def answer_question(self, question: str, language: str = "italian") -> dict:
        """
        Answer a question using multi-agent system

        Args:
            question: User's question
            language: Response language

        Returns:
            Response dict
        """
        try:
            # Create agent with language
            agent = self.create_agent(language)

            # Create task
            if language == "italian":
                task_description = f"""Domanda dell'utente: {question}

                IMPORTANTE: Rispondi SOLO in italiano, in modo professionale, chiaro e conciso.
                Se l'utente saluta, rispondi con un saluto cordiale.
                Se chiede informazioni, fornisci una risposta utile e dettagliata."""
                expected_output = "Una risposta chiara, utile e professionale in italiano"
            else:
                task_description = f"Answer this question: {question}"
                expected_output = "A clear and helpful answer"

            task = Task(
                description=task_description,
                expected_output=expected_output,
                agent=agent
            )

            # Create and run crew
            crew = Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                verbose=False
            )

            # Execute
            result = crew.kickoff()

            # Extract the actual output text from CrewOutput
            if hasattr(result, 'output'):
                answer = result.output
            elif hasattr(result, 'raw_output'):
                answer = result.raw_output
            else:
                # Fallback to string conversion
                answer = str(result)

            return {
                "success": True,
                "answer": answer,
                "confidence": 0.95,
                "model": "agent-engine-assistant"
            }

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return {
                "success": False,
                "answer": f"Errore: {str(e)}",
                "confidence": 0.0,
                "error": error_details
            }