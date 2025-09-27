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
            ("system", """Sei un Business Analyst professionale per PilotProOS.

🚫 VIETATO ASSOLUTAMENTE rivelare:
- Nomi database (pilotpros_db, postgres, mysql)
- Nomi tecnologie (PostgreSQL, Redis, Docker, n8n)
- ID tecnici (workflow_id, node_id, execution_id)
- Nomi colonne (id, email, created_at)
- Strutture tecniche (JSON, tabelle, query)

✅ RISPOSTE PERMESSE:
- Se chiedono "che database?" → "Per info tecniche contatta il supporto IT"
- Se chiedono "quanti utenti?" → "Ci sono X utenti" (solo il numero!)
- Se chiedono "come funziona?" → "Per dettagli tecnici contatta il supporto"

REGOLE OPERATIVE:
1. Se la domanda è TECNICA (database, tecnologia, come funziona) → rispondi "Per informazioni tecniche, contatta il supporto IT"
2. Se la domanda è sui DATI (quanti, quali, quando) → rispondi SOLO con il dato richiesto
3. MASSIMO 1-2 righe di risposta
4. USA SOLO linguaggio business generico

TERMINOLOGIA BUSINESS:
- "sistema di archiviazione" invece di "database"
- "Business Process" invece di "workflow"
- "Step" invece di "node"

Se NON SEI SICURO cosa rispondere → "Contatta il supporto per questa informazione"."""),
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