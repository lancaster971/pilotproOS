"""
N8N Integration - Comunicazione bidirezionale Agent Engine ↔ n8n
"""

import httpx
import asyncio
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class N8nIntegration:
    """Gestisce la comunicazione bidirezionale con n8n"""

    def __init__(self):
        # Configurazione endpoints
        self.n8n_base_url = os.getenv("N8N_URL", "http://n8n-dev:5678")
        self.backend_url = os.getenv("BACKEND_URL", "http://backend-dev:3001")
        self.webhook_secret = os.getenv("N8N_WEBHOOK_SECRET", "pilotpros_n8n_secret_2025")

    async def trigger_n8n_workflow(self, webhook_path: str, data: Dict[str, Any]) -> Dict:
        """
        Triggera un workflow n8n via webhook

        Args:
            webhook_path: Path del webhook n8n (es: "process-analysis")
            data: Dati da inviare al workflow

        Returns:
            Risposta del workflow
        """
        try:
            webhook_url = f"{self.n8n_base_url}/webhook/{webhook_path}"

            payload = {
                **data,
                "source": "agent-engine",
                "timestamp": datetime.now().isoformat(),
                "secret": self.webhook_secret
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    timeout=30.0
                )

                logger.info(f"✅ Workflow triggered: {webhook_path}")
                return response.json()

        except Exception as e:
            logger.error(f"❌ Failed to trigger workflow: {e}")
            return {"error": str(e)}

    async def receive_from_n8n(self, action: str, data: Dict[str, Any]) -> Dict:
        """
        Processa dati ricevuti da n8n

        Args:
            action: Tipo di azione richiesta
            data: Dati dal workflow

        Returns:
            Risultato elaborazione
        """
        try:
            if action == "analyze":
                # n8n chiede analisi AI
                from simple_assistant import SimpleAssistant
                assistant = SimpleAssistant()
                result = assistant.answer_question(
                    data.get("question", "Analizza questi dati"),
                    language="italian",
                    prefer_free=True
                )
                return result

            elif action == "process_data":
                # n8n invia dati da processare
                from agents.business_analysis_crew import BusinessAnalysisAgents
                agents = BusinessAnalysisAgents()
                result = agents.analyze_business(
                    data.get("process", ""),
                    data.get("context", "")
                )
                return result

            elif action == "get_insights":
                # n8n chiede insights
                from agents.business_analysis_crew import QuickInsightsAgent
                agent = QuickInsightsAgent()
                result = agent.get_insights(
                    data.get("question", ""),
                    data.get("context", "")
                )
                return result

            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"❌ Error processing n8n request: {e}")
            return {"error": str(e)}

    async def send_to_backend_webhook(self, data: Dict[str, Any]) -> Dict:
        """
        Invia dati al backend via webhook

        Args:
            data: Dati da inviare

        Returns:
            Risposta backend
        """
        try:
            webhook_url = f"{self.backend_url}/api/ai/webhook/n8n"

            payload = {
                "secret": self.webhook_secret,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    timeout=30.0
                )

                return response.json()

        except Exception as e:
            logger.error(f"❌ Failed to send to backend: {e}")
            return {"error": str(e)}


class N8nWorkflowTriggers:
    """Trigger predefiniti per workflow n8n comuni"""

    def __init__(self):
        self.integration = N8nIntegration()

    async def trigger_customer_onboarding(self, customer_data: Dict) -> Dict:
        """Triggera workflow onboarding cliente"""
        return await self.integration.trigger_n8n_workflow(
            "customer-onboarding",
            customer_data
        )

    async def trigger_invoice_processing(self, invoice_data: Dict) -> Dict:
        """Triggera workflow processamento fatture"""
        return await self.integration.trigger_n8n_workflow(
            "invoice-processing",
            invoice_data
        )

    async def trigger_data_analysis(self, analysis_request: Dict) -> Dict:
        """Triggera workflow analisi dati"""
        return await self.integration.trigger_n8n_workflow(
            "data-analysis",
            analysis_request
        )

    async def trigger_alert_notification(self, alert_data: Dict) -> Dict:
        """Triggera workflow notifiche alert"""
        return await self.integration.trigger_n8n_workflow(
            "alert-notification",
            alert_data
        )

    async def trigger_report_generation(self, report_params: Dict) -> Dict:
        """Triggera workflow generazione report"""
        return await self.integration.trigger_n8n_workflow(
            "report-generation",
            report_params
        )


# Esempio di utilizzo
if __name__ == "__main__":
    async def test():
        # Test integrazione
        integration = N8nIntegration()

        # 1. Triggera un workflow n8n
        print("=== TEST TRIGGER WORKFLOW ===")
        result = await integration.trigger_n8n_workflow(
            "test-webhook",
            {"message": "Test from Agent Engine", "value": 42}
        )
        print(f"Result: {result}")

        # 2. Processa richiesta da n8n
        print("\n=== TEST RECEIVE FROM N8N ===")
        result = await integration.receive_from_n8n(
            "analyze",
            {"question": "Come posso ottimizzare le vendite?"}
        )
        print(f"Analysis: {result}")

        # 3. Workflow trigger specifici
        print("\n=== TEST WORKFLOW TRIGGERS ===")
        triggers = N8nWorkflowTriggers()

        # Onboarding cliente
        result = await triggers.trigger_customer_onboarding({
            "customer_name": "Acme Corp",
            "email": "contact@acme.com",
            "plan": "enterprise"
        })
        print(f"Onboarding: {result}")

    asyncio.run(test())