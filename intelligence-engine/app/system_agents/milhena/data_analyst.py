"""
Data Analyst Agent - Business Intelligence LLM
===============================================
Trasforma dati RAW in risposte business comprensibili
Risponde SOLO alla domanda specifica senza leak tecnici
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os


class DataAnalystAgent:
    """
    Agent LLM specializzato in Business Intelligence
    Elabora dati RAW e risponde in linguaggio business
    """

    def __init__(self):
        """Initialize Data Analyst with LLM"""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_retries=3,
            openai_api_key=os.environ.get("OPENAI_API_KEY")
        )

        self.system_prompt = """Sei un Data Analyst specializzato in Business Intelligence.

REGOLE FERREE:
1. Rispondi SOLO alla domanda specifica dell'utente
2. NON rivelare mai dettagli tecnici (workflow_id, node_id, execution_id, etc.)
3. USA SOLO linguaggio business comprensibile al cliente
4. Se i dati contengono campi tecnici, IGNORALI completamente
5. Rispondi in 1-2 frasi concise

TRADUZIONI OBBLIGATORIE:
- workflow → Business Process
- execution → Process Run
- node → Process Step
- email_sender → mittente
- email_subject → oggetto

VIETATO mostrare:
- ID tecnici (workflow_id, node_id, execution_id)
- Nomi tecnici (n8n-nodes-base, microsoftOutlookTrigger)
- Strutture database (JSON, colonne, tabelle)

ESEMPIO:
Domanda: "Quanti nodi ha il workflow?"
Dati RAW: [{id: 1, workflow_id: "abc", node_name: "Email", node_type: "n8n-trigger"}]
Risposta corretta: "Il processo ha 1 step."
Risposta VIETATA: "Il workflow abc ha 1 nodo di tipo n8n-trigger chiamato Email"
"""

    def analyze(self, user_question: str, raw_data: str) -> str:
        """
        Analizza dati e restituisce risposta business

        Args:
            user_question: Domanda specifica dell'utente
            raw_data: Dati RAW dal database

        Returns:
            Risposta concisa in linguaggio business
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""Domanda utente: {user_question}

Dati dal database:
{raw_data}

Rispondi SOLO alla domanda specifica in 1-2 frasi usando linguaggio business.
NON rivelare dettagli tecnici o ID.""")
        ]

        response = self.llm.invoke(messages)
        return response.content


# Singleton instance
_instance = None

def get_data_analyst() -> DataAnalystAgent:
    """Get or create singleton Data Analyst"""
    global _instance
    if _instance is None:
        _instance = DataAnalystAgent()
    return _instance