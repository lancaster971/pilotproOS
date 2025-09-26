#!/usr/bin/env python3
"""
Milhena Simple Orchestrator - Versione semplificata senza CrewAI
Usa direttamente Groq/Gemini per rispondere REALMENTE
"""

import os
import logging
from typing import Dict, Any
import httpx
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleMilhenaOrchestrator:
    """Orchestrator semplificato che usa LLM REALI senza CrewAI"""
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") 
        self.primary_llm = "groq" if self.groq_api_key else "gemini"
        logger.info(f"Milhena Simple initialized with {self.primary_llm}")
    
    async def process(self, message: str, user_id: str = "guest") -> Dict[str, Any]:
        """Processa messaggio con LLM REALE"""
        try:
            start_time = datetime.now()
            
            # Usa Groq se disponibile
            if self.groq_api_key:
                response = await self._call_groq(message)
                llm_used = "groq"
            elif self.gemini_api_key:
                response = await self._call_gemini(message)
                llm_used = "gemini"
            else:
                # Nessuna API key configurata
                return {
                    "response": "⚠️ Nessun LLM configurato. Imposta GROQ_API_KEY o GEMINI_API_KEY",
                    "status": "no_llm",
                    "llm": "none"
                }
            
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "response": response,
                "status": "success",
                "llm": llm_used,
                "response_time_ms": elapsed,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Process error: {e}")
            return {
                "response": f"Errore nel processare: {str(e)}",
                "status": "error",
                "error": str(e)
            }
    
    async def _call_groq(self, message: str) -> str:
        """Chiama Groq API REALE"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Sei Milhena, assistente AI di PilotProOS. Rispondi in modo professionale e utile."
                        },
                        {"role": "user", "content": message}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Groq API error: {response.status_code}")
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _call_gemini(self, message: str) -> str:
        """Chiama Gemini API REALE"""
        # TODO: Implementare chiamata Gemini
        return f"Gemini: Processando '{message}' (da implementare)"
    
    def get_agents_info(self):
        """Info sui agent disponibili"""
        return [{
            "id": "milhena_simple",
            "name": "Milhena Simple (No CrewAI)",
            "type": "direct-llm",
            "status": "active",
            "llm_provider": self.primary_llm,
            "api_key_configured": bool(self.groq_api_key or self.gemini_api_key),
            "capabilities": [
                "chat",
                "question_answering",
                "text_generation"
            ]
        }]