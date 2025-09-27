"""
Data Analyst Agent - Business Intelligence con LLM
===================================================
Elabora dati RAW dal database e li trasforma in risposte business-friendly
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os


class DataAnalystAgent:
    """
    Data Analyst Agent
    Usa LLM per trasformare dati tecnici in risposte business comprensibili
    """

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0):
        """Initialize Data Analyst with LLM"""
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        # Prompt template per analisi business
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Sei un Business Analyst professionale.

Il tuo compito è trasformare dati tecnici dal database in risposte business comprensibili.

REGOLE FERREE:
1. Rispondi SOLO alla domanda specifica dell'utente
2. NON rivelare dati tecnici (workflow_id, node_id, execution_id, etc.)
3. USA SOLO terminologia business
4. Sii conciso - max 2-3 righe
5. NON inventare o speculare

TERMINOLOGIA BUSINESS OBBLIGATORIA:
- "Business Process" invece di "workflow"
- "Process Run" invece di "execution"
- "Process Step" invece di "node"
- "Integration Endpoint" invece di "webhook"
- "Automation Platform" invece di "n8n"

Se i dati contengono informazioni irrilevanti per la domanda, IGNORALE.
Estrai SOLO il dato numerico o l'informazione richiesta."""),
            ("human", """Domanda utente: {user_query}

Dati dal database:
{database_data}

Fornisci una risposta business concisa che risponda SOLO alla domanda.""")
        ])

        self.chain = self.prompt | self.llm | StrOutputParser()

    def analyze(self, user_query: str, database_data: str) -> str:
        """
        Analizza dati e genera risposta business

        Args:
            user_query: Domanda originale dell'utente
            database_data: Dati RAW dal database

        Returns:
            Risposta business-friendly concisa
        """
        try:
            response = self.chain.invoke({
                "user_query": user_query,
                "database_data": database_data
            })
            return response.strip()
        except Exception as e:
            return f"Errore nell'analisi dati: {str(e)}"


# Singleton instance
_instance = None

def get_data_analyst(model: str = "gpt-4o-mini") -> DataAnalystAgent:
    """Get or create singleton Data Analyst instance"""
    global _instance
    if _instance is None:
        _instance = DataAnalystAgent(model=model)
    return _instance