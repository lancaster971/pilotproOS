"""
Agent Orchestrator - Main service for managing Agent Engine
Handles LLM initialization and crew orchestration
"""

import logging
from typing import Dict, Any, Optional
from services.llm_provider import LLMService
from services.job_manager import JobManager
# from agents.process_analysis_crew import ProcessAnalysisAgents
# from agents.pilotpro_assistant_crew import PilotProAssistantAgents
# Disabled - Pydantic compatibility issues
import json

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Main orchestrator for Agent Engine
    Manages LLM providers and crew execution
    """

    def __init__(self, settings, redis_client=None):
        """
        Initialize Agent Orchestrator

        Args:
            settings: Application settings
            redis_client: Redis client for job queue
        """
        self.settings = settings
        self.redis_client = redis_client
        self.llm_service = LLMService(settings)
        self.job_manager = JobManager(redis_client, settings) if redis_client else None
        self.llm = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize LLM provider"""
        try:
            self.llm = self.llm_service.get_llm()
            provider_info = self.llm_service.get_provider_info()

            logger.info(f"✅ LLM initialized: {provider_info['current_provider']}")

            if provider_info['current_provider'] == 'mock':
                logger.warning("⚠️ Using Mock LLM - limited functionality!")
                logger.info("💡 For full features, setup Ollama (FREE):")
                logger.info("   1. Install: https://ollama.ai")
                logger.info("   2. Run: ollama serve")
                logger.info("   3. Pull model: ollama pull llama2")

        except Exception as e:
            logger.error(f"❌ LLM initialization failed: {e}")
            # Use mock as fallback
            from services.llm_provider import MockLLM
            self.llm = MockLLM()
            logger.warning("Using Mock LLM as fallback")

    async def process_assistant_request(
        self,
        request_type: str,
        data: Dict[str, Any],
        jwt_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a request through PilotPro Assistant

        Args:
            request_type: Type of request (question, report, analysis)
            data: Request data
            jwt_token: JWT for backend access

        Returns:
            Processing result
        """
        try:
            # Create assistant crew
            crew = PilotProAssistantAgents(
                jwt_token=jwt_token,
                backend_url=self.settings.DATABASE_URL.replace("postgresql", "http").split("@")[1].split("/")[0]
            )

            # Process based on request type
            if request_type == "question":
                result = crew.answer_question(data.get("question", ""))
            elif request_type == "report":
                result = crew.generate_report(data.get("report_type", "daily"))
            elif request_type == "analysis":
                result = crew.analyze_performance(data.get("timeframe", "7d"))
            else:
                result = {
                    "success": False,
                    "error": f"Unknown request type: {request_type}"
                }

            return result

        except Exception as e:
            logger.error(f"Assistant request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": self._get_fallback_response(request_type, data)
            }

    async def process_analysis_job(
        self,
        analysis_type: str,
        data: Dict[str, Any],
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an analysis job

        Args:
            analysis_type: Type of analysis
            data: Analysis data
            job_id: Optional job ID for tracking

        Returns:
            Analysis result
        """
        try:
            # Update job progress if job_id provided
            if job_id and self.job_manager:
                await self.job_manager.update_job_progress(
                    job_id, 10, "processing", "Initializing analysis"
                )

            # Create appropriate crew
            if analysis_type == "process_analysis":
                crew = ProcessAnalysisAgents(llm=self.llm, verbose=False)
                result = crew.analyze(data)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown analysis type: {analysis_type}"
                }

            # Update job completion
            if job_id and self.job_manager:
                await self.job_manager.complete_job(
                    job_id, result, success=result.get("success", False)
                )

            return result

        except Exception as e:
            logger.error(f"Analysis job failed: {e}")

            # Update job failure
            if job_id and self.job_manager:
                await self.job_manager.complete_job(
                    job_id, {"error": str(e)}, success=False
                )

            return {
                "success": False,
                "error": str(e)
            }

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get Agent Engine system status

        Returns:
            System status information
        """
        provider_info = self.llm_service.get_provider_info()

        return {
            "status": "operational",
            "llm_provider": provider_info,
            "capabilities": self._get_capabilities(provider_info),
            "recommendations": self._get_recommendations(provider_info)
        }

    def _get_capabilities(self, provider_info: Dict) -> Dict[str, bool]:
        """
        Get system capabilities based on LLM provider

        Args:
            provider_info: Provider information

        Returns:
            Capabilities dictionary
        """
        is_mock = provider_info['current_provider'] == 'mock'

        return {
            "assistant": not is_mock,
            "analysis": not is_mock,
            "reports": not is_mock,
            "real_time_insights": provider_info['has_paid_api'],
            "local_processing": provider_info['has_local'],
            "fallback_available": True  # Always true due to Mock
        }

    def _get_recommendations(self, provider_info: Dict) -> list:
        """
        Get recommendations based on current setup

        Args:
            provider_info: Provider information

        Returns:
            List of recommendations
        """
        recommendations = []

        if provider_info['current_provider'] == 'mock':
            recommendations.append({
                "priority": "high",
                "action": "Setup Ollama for free local LLM",
                "benefit": "Full Agent Engine functionality without API costs"
            })

        if not provider_info['has_local']:
            recommendations.append({
                "priority": "medium",
                "action": "Install Ollama as backup",
                "benefit": "Fallback when API is down or rate limited"
            })

        if not provider_info['has_paid_api']:
            recommendations.append({
                "priority": "low",
                "action": "Consider OpenAI/Anthropic for production",
                "benefit": "Better performance and reliability"
            })

        return recommendations

    def _get_fallback_response(self, request_type: str, data: Dict) -> str:
        """
        Get fallback response when processing fails

        Args:
            request_type: Type of request
            data: Request data

        Returns:
            Fallback response
        """
        responses = {
            "question": "Il sistema è temporaneamente limitato. Per favore, consulta la dashboard per i dati aggiornati.",
            "report": "Report non disponibile. Il sistema sta utilizzando risposte di fallback.",
            "analysis": "Analisi limitata disponibile. Configura un provider LLM per analisi complete."
        }
        return responses.get(request_type, "Funzionalità limitata. Configura un provider LLM.")