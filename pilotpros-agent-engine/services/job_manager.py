"""
Job Manager for async processing with Redis queue
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import uuid

import redis.asyncio as redis
from rq import Queue, Job
from rq.job import JobStatus

logger = logging.getLogger(__name__)


class JobManager:
    """
    Manages async job queue for Agent Engine analysis
    """

    def __init__(self, redis_client: redis.Redis, settings):
        self.redis_client = redis_client
        self.settings = settings
        self.queue_name = "agent-engine-jobs"

    async def submit_job(
        self,
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit a new analysis job to the queue

        Args:
            job_data: Job data containing id, type, data, priority, etc.

        Returns:
            Job information including ID and status
        """
        try:
            # Use provided job_id or generate new one
            job_id = job_data.get("id") or f"job_{uuid.uuid4().hex[:12]}"
            priority = job_data.get("priority", "normal")

            # Update job data with metadata
            job_data.update({
                "id": job_id,
                "status": "queued",
                "progress": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            })

            # Store job in Redis
            await self.redis_client.hset(
                f"job:{job_id}",
                mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                        for k, v in job_data.items()}
            )

            # Add to queue based on priority
            queue_key = self._get_queue_key(priority)
            await self.redis_client.lpush(queue_key, job_id)

            # Get queue position
            position = await self._get_queue_position(job_id, priority)

            # Estimate start time
            estimated_start = self._estimate_start_time(position)

            logger.info(f"Job {job_id} submitted successfully")

            return {
                "job_id": job_id,
                "status": "queued",
                "position_in_queue": position,
                "estimated_start": estimated_start,
                "websocket_channel": f"ws://localhost:8000/ws/jobs/{job_id}",
                "status_url": f"/api/v1/jobs/{job_id}/status"
            }

        except Exception as e:
            logger.error(f"Failed to submit job: {e}")
            raise

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific job

        Args:
            job_id: Job identifier

        Returns:
            Job status information or None if not found
        """
        try:
            # Get job data from Redis
            job_data = await self.redis_client.hgetall(f"job:{job_id}")

            if not job_data:
                return None

            # Parse stored data
            result = {}
            for key, value in job_data.items():
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value

            return result

        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return None

    async def update_job_progress(
        self,
        job_id: str,
        progress: int,
        status: str,
        current_step: Optional[str] = None
    ):
        """
        Update job progress and status

        Args:
            job_id: Job identifier
            progress: Progress percentage (0-100)
            status: Current status
            current_step: Optional description of current step
        """
        try:
            updates = {
                "progress": str(progress),
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }

            if current_step:
                updates["current_step"] = current_step

            await self.redis_client.hset(
                f"job:{job_id}",
                mapping=updates
            )

            # Publish progress update for WebSocket subscribers
            await self._publish_progress(job_id, progress, status, current_step)

        except Exception as e:
            logger.error(f"Failed to update job progress for {job_id}: {e}")

    async def complete_job(
        self,
        job_id: str,
        result: Dict[str, Any],
        success: bool = True
    ):
        """
        Mark job as completed and store result

        Args:
            job_id: Job identifier
            result: Analysis result
            success: Whether job completed successfully
        """
        try:
            status = "completed" if success else "failed"

            updates = {
                "status": status,
                "progress": "100" if success else "0",
                "result": json.dumps(result),
                "completed_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            await self.redis_client.hset(
                f"job:{job_id}",
                mapping=updates
            )

            # Set TTL for completed job
            await self.redis_client.expire(
                f"job:{job_id}",
                self.settings.REDIS_RESULT_TTL
            )

            # Trigger callback if configured
            job_data = await self.get_job_status(job_id)
            if job_data and job_data.get("callback_url"):
                await self._trigger_callback(job_data["callback_url"], job_id, result)

            logger.info(f"Job {job_id} completed with status: {status}")

        except Exception as e:
            logger.error(f"Failed to complete job {job_id}: {e}")

    async def get_queue_stats(self) -> Dict[str, int]:
        """
        Get queue statistics

        Returns:
            Dictionary with queue statistics
        """
        try:
            stats = {
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0
            }

            # Count jobs in each priority queue
            for priority in ["high", "normal", "low"]:
                queue_key = self._get_queue_key(priority)
                count = await self.redis_client.llen(queue_key)
                stats["pending"] += count

            # Count jobs by status
            # TODO: Implement scanning of all jobs

            return stats

        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {"error": str(e)}

    def _get_queue_key(self, priority: str) -> str:
        """Get Redis key for priority queue"""
        return f"{self.queue_name}:{priority}"

    async def _get_queue_position(self, job_id: str, priority: str) -> int:
        """Get position of job in queue"""
        queue_key = self._get_queue_key(priority)
        jobs = await self.redis_client.lrange(queue_key, 0, -1)
        try:
            return jobs.index(job_id) + 1
        except ValueError:
            return 0

    def _estimate_start_time(self, position: int) -> datetime:
        """Estimate when job will start processing"""
        # Assume 2 minutes average per job
        minutes = position * 2
        return datetime.utcnow() + timedelta(minutes=minutes)

    async def _publish_progress(
        self,
        job_id: str,
        progress: int,
        status: str,
        current_step: Optional[str]
    ):
        """Publish progress update to Redis pubsub"""
        channel = f"job:progress:{job_id}"
        message = {
            "job_id": job_id,
            "progress": progress,
            "status": status,
            "current_step": current_step,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.redis_client.publish(channel, json.dumps(message))

    async def _trigger_callback(self, callback_url: str, job_id: str, result: Dict):
        """Trigger webhook callback on job completion"""
        # TODO: Implement webhook callback
        logger.info(f"Would trigger callback to {callback_url} for job {job_id}")
        pass

    async def wait_for_result(
        self,
        job_id: str,
        timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for job result with timeout

        Args:
            job_id: Job identifier
            timeout: Maximum wait time in seconds

        Returns:
            Job result or None if timeout
        """
        import asyncio

        try:
            start_time = datetime.utcnow()

            while (datetime.utcnow() - start_time).total_seconds() < timeout:
                # Check if result exists
                result_json = await self.redis_client.get(f"job:result:{job_id}")

                if result_json:
                    return json.loads(result_json)

                # Check job status
                status = await self.get_job_status(job_id)
                if status and status.get("status") in ["completed", "failed"]:
                    return status.get("result", {})

                # Wait before next check
                await asyncio.sleep(0.5)

            logger.warning(f"Timeout waiting for job {job_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to wait for job result {job_id}: {e}")
            return None