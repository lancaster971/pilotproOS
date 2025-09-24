"""
Simple CrewAI Crew - Minimal working example
"""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
import os


class SimpleAssistantCrew:
    """Simple assistant using CrewAI"""

    def __init__(self):
        """Initialize the crew"""
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

    def create_agent(self):
        """Create the assistant agent"""
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
        Answer a question using CrewAI

        Args:
            question: User's question
            language: Response language

        Returns:
            Response dict
        """
        try:
            # Create agent
            agent = self.create_agent()

            # Create task
            task_description = f"Answer this question in {language}: {question}"
            if language == "italian":
                task_description += "\nRispondi in italiano in modo professionale e conciso."

            task = Task(
                description=task_description,
                expected_output=f"A clear and helpful answer in {language}",
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

            return {
                "success": True,
                "answer": str(result),
                "confidence": 0.95,
                "model": "crewai-assistant"
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