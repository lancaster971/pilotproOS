"""
Worker process for Agent Engine job queue
Processes async jobs from Redis queue
"""

import asyncio
import json
import logging
import signal
import sys
from typing import Optional
import redis.asyncio as redis
# RQ imports removed - not needed for our async implementation

from config.settings import Settings
from services.llm_manager import LLMManager, TaskComplexity
from services.agent_orchestrator import AgentOrchestrator
from simple_assistant import SimpleAssistant
from agents.crews.simple_agents import SimpleAssistantAgents
from agents.crews.business_analysis_agents import BusinessAnalysisAgents, QuickInsightsAgent
# Agent Engine with multiple agent systems

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentEngineWorker:
    """
    Worker for processing Agent Engine jobs
    """

    def __init__(self):
        self.settings = Settings()
        self.redis_client = None
        self.llm_manager = None
        self.orchestrator = None
        self.running = True

    async def initialize(self):
        """Initialize worker components"""
        try:
            # Connect to Redis
            self.redis_client = await redis.from_url(
                self.settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("✅ Redis connected")

            # Initialize LLM Manager
            self.llm_manager = LLMManager(self.settings)
            logger.info(f"✅ LLM Manager initialized with {len(self.llm_manager.available_models)} models")

            # Initialize Orchestrator
            self.orchestrator = AgentOrchestrator(self.settings, self.redis_client)
            logger.info("✅ Agent Orchestrator initialized")

        except Exception as e:
            logger.error(f"❌ Worker initialization failed: {e}")
            raise

    async def process_job(self, job_data: dict) -> dict:
        """
        Process a single job

        Args:
            job_data: Job data from queue

        Returns:
            Processing result
        """
        job_type = job_data.get("type")
        job_id = job_data.get("id")

        logger.info(f"📋 Processing job {job_id} of type {job_type}")

        try:
            # Analyze task complexity
            prompt = job_data.get("prompt", "")
            complexity = self.llm_manager.analyze_task_complexity(prompt)
            logger.info(f"📊 Task complexity: {complexity.value}")

            # Select appropriate model
            model_name = self.llm_manager.select_model_for_task(
                complexity,
                prefer_free=True  # Prefer free models for development
            )
            logger.info(f"🤖 Selected model: {model_name}")

            # Get LLM client
            llm = self.llm_manager.get_llm_client(model_name)

            # Process based on job type
            if job_type == "assistant":
                result = await self._process_assistant_job(job_data, llm)
            elif job_type == "analysis":
                result = await self._process_analysis_job(job_data, llm)
            elif job_type == "business_analysis":
                result = await self._process_business_analysis_job(job_data)
            elif job_type == "quick_insights":
                result = await self._process_quick_insights_job(job_data)
            elif job_type == "report":
                result = await self._process_report_job(job_data, llm)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown job type: {job_type}"
                }

            logger.info(f"✅ Job {job_id} completed successfully")
            return result

        except Exception as e:
            logger.error(f"❌ Job {job_id} failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "job_id": job_id
            }

    async def _process_assistant_job(self, job_data: dict, llm) -> dict:
        """Process PilotPro Assistant job"""
        # Use SimpleAssistant directly - it works better
        assistant = SimpleAssistant()
        question = job_data.get("question", "")
        language = job_data.get("language", "italian")
        result = assistant.answer_question(question, language)

        # If SimpleAssistant works, return result
        if result.get("success"):
            return result

        # Otherwise try CrewAI system as fallback
        try:
            agent_system = SimpleAssistantAgents()
            return agent_system.answer_question(question, language)
        except Exception as e:
            logger.error(f"Both assistant systems failed: {e}")
            return {
                "success": False,
                "answer": "Assistente temporaneamente non disponibile. Riprova tra poco.",
                "confidence": 0.0,
                "error": str(e)
            }

    async def _process_analysis_job(self, job_data: dict, llm) -> dict:
        """Process analysis job"""
        # Disabled for now - CrewAI Pydantic compatibility issues
        return {
            "success": False,
            "error": "Analysis agents temporarily disabled"
        }

    async def _process_report_job(self, job_data: dict, llm) -> dict:
        """Process report generation job"""
        # Disabled for now - CrewAI Pydantic compatibility issues
        return {
            "success": False,
            "error": "Report agents temporarily disabled"
        }

    async def _process_business_analysis_job(self, job_data: dict) -> dict:
        """Process business analysis with multi-agent system"""
        try:
            agents = BusinessAnalysisAgents()
            process_description = job_data.get("process_description", "")
            data_context = job_data.get("data_context", "")
            return agents.analyze_business(process_description, data_context)
        except Exception as e:
            logger.error(f"Business analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _process_quick_insights_job(self, job_data: dict) -> dict:
        """Process quick insights request"""
        try:
            agent = QuickInsightsAgent()
            question = job_data.get("question", "")
            context = job_data.get("context", "")
            return agent.get_insights(question, context)
        except Exception as e:
            logger.error(f"Quick insights failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def run(self):
        """Main worker loop"""
        await self.initialize()

        logger.info("🚀 Agent Engine Worker started")
        logger.info(f"📊 Available models: {self.llm_manager.get_model_info()['available_models']} models")

        # Process jobs from Redis queue
        while self.running:
            try:
                # Get job from queue (blocking pop with timeout)
                job_data = await self.redis_client.brpop(
                    ["agent-engine-jobs:high", "agent-engine-jobs:normal", "agent-engine-jobs:low"],
                    timeout=5
                )

                if job_data:
                    _, job_json = job_data
                    job = json.loads(job_json)

                    # Process job
                    result = await self.process_job(job)

                    # Store result
                    await self.redis_client.setex(
                        f"job:result:{job['id']}",
                        86400,  # 24 hours TTL
                        json.dumps(result)
                    )

                    # Publish completion event
                    await self.redis_client.publish(
                        f"job:complete:{job['id']}",
                        json.dumps(result)
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing job: {e}")
                await asyncio.sleep(1)

        logger.info("Worker shutting down...")
        if self.redis_client:
            await self.redis_client.close()

    def shutdown(self, signum, frame):
        """Handle shutdown signal"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False


async def main():
    """Main entry point"""
    worker = AgentEngineWorker()

    # Setup signal handlers
    signal.signal(signal.SIGINT, worker.shutdown)
    signal.signal(signal.SIGTERM, worker.shutdown)

    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())