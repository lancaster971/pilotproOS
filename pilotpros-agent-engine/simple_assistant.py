"""
Simple Assistant - Direct OpenAI integration without CrewAI complexity
"""

import os
import logging
from typing import Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


class SimpleAssistant:
    """Simple assistant that works directly with OpenAI"""

    def __init__(self):
        """Initialize the assistant"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
            self.available = True
            logger.info("✅ SimpleAssistant initialized with OpenAI")
        else:
            self.client = None
            self.available = False
            logger.warning("⚠️ No OpenAI API key - SimpleAssistant unavailable")

    def answer_question(self, question: str, language: str = "italian") -> Dict[str, Any]:
        """
        Answer a question using OpenAI directly

        Args:
            question: The question to answer
            language: Language for response

        Returns:
            Response dict with answer, confidence, etc.
        """
        if not self.available:
            return {
                "success": False,
                "answer": "Assistant non disponibile. Configura OPENAI_API_KEY.",
                "confidence": 0.0
            }

        try:
            # Create system prompt based on language
            if language == "italian":
                system_prompt = """Sei PilotPro Assistant, un assistente AI per il sistema PilotProOS.
                Rispondi in italiano in modo professionale e conciso.
                Sei esperto di processi aziendali, automazione e analisi dati."""
            else:
                system_prompt = """You are PilotPro Assistant, an AI assistant for PilotProOS system.
                Answer professionally and concisely.
                You are an expert in business processes, automation, and data analysis."""

            # Call OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.7,
                max_tokens=500
            )

            answer = response.choices[0].message.content

            return {
                "success": True,
                "answer": answer,
                "confidence": 0.95,
                "model": "gpt-3.5-turbo"
            }

        except Exception as e:
            logger.error(f"SimpleAssistant error: {e}")
            return {
                "success": False,
                "answer": f"Errore: {str(e)}",
                "confidence": 0.0
            }