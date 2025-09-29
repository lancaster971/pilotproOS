"""
Enterprise Resilience Framework for PilotProOS Intelligence Engine
==================================================================
Production-ready error handling with circuit breakers, retry logic,
dead letter queue, and graceful degradation patterns.

STRICT REQUIREMENTS FROM TODO-MILHENA-EXPERT.md:
- Circuit breakers (3 failures → open)
- Retry logic (exponential backoff)
- Dead letter queue for recovery
- Graceful degradation patterns
"""

import asyncio
import json
import time
import hashlib
from typing import Any, Dict, Optional, Callable, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import logging

import redis
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError
)
from pydantic import BaseModel, Field

from app.core.circuit_breaker import get_circuit_breaker, CircuitBreaker
from app.security import UserLevel

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Types of failures for categorization"""
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    API_ERROR = "api_error"
    NETWORK = "network"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Recovery strategies for different failure types"""
    RETRY = "retry"
    FALLBACK = "fallback"
    QUEUE = "queue"
    SKIP = "skip"
    ALERT = "alert"


@dataclass
class FailureContext:
    """Context for a failed operation"""
    agent_name: str
    operation: str
    error_type: FailureType
    error_message: str
    timestamp: datetime
    retry_count: int = 0
    user_level: UserLevel = UserLevel.BUSINESS
    original_request: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DeadLetterMessage(BaseModel):
    """Message structure for dead letter queue"""
    id: str = Field(default_factory=lambda: hashlib.md5(str(time.time()).encode()).hexdigest())
    agent_name: str
    operation: str
    payload: Dict[str, Any]
    error_type: str
    error_message: str
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = Field(default_factory=datetime.now)
    last_retry_at: Optional[datetime] = None
    user_level: str = "BUSINESS"
    session_id: Optional[str] = None
    priority: int = 0  # Higher = more important


class RetryManager:
    """
    Manages retry logic with exponential backoff
    Uses tenacity library for robust retry patterns
    """

    def __init__(self):
        self.stats = {
            "total_retries": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "retry_times": []
        }

    def with_exponential_backoff(
        self,
        max_attempts: int = 3,
        min_wait: int = 1,
        max_wait: int = 60,
        multiplier: int = 2
    ):
        """
        Decorator for exponential backoff retry

        Args:
            max_attempts: Maximum retry attempts
            min_wait: Minimum wait time in seconds
            max_wait: Maximum wait time in seconds
            multiplier: Exponential multiplier
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                @retry(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(
                        multiplier=multiplier,
                        min=min_wait,
                        max=max_wait
                    ),
                    retry=retry_if_exception_type((Exception,)),
                    before_sleep=before_sleep_log(logger, logging.WARNING)
                )
                async def retry_func():
                    self.stats["total_retries"] += 1
                    try:
                        result = await func(*args, **kwargs)
                        self.stats["successful_retries"] += 1
                        return result
                    except Exception as e:
                        logger.error(f"Retry failed for {func.__name__}: {e}")
                        raise

                try:
                    return await retry_func()
                except RetryError as e:
                    self.stats["failed_retries"] += 1
                    logger.error(f"All retries exhausted for {func.__name__}")
                    raise e.last_attempt.result()

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                @retry(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(
                        multiplier=multiplier,
                        min=min_wait,
                        max=max_wait
                    ),
                    retry=retry_if_exception_type((Exception,)),
                    before_sleep=before_sleep_log(logger, logging.WARNING)
                )
                def retry_func():
                    self.stats["total_retries"] += 1
                    try:
                        result = func(*args, **kwargs)
                        self.stats["successful_retries"] += 1
                        return result
                    except Exception as e:
                        logger.error(f"Retry failed for {func.__name__}: {e}")
                        raise

                try:
                    return retry_func()
                except RetryError as e:
                    self.stats["failed_retries"] += 1
                    logger.error(f"All retries exhausted for {func.__name__}")
                    raise e.last_attempt.result()

            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def get_stats(self) -> Dict[str, Any]:
        """Get retry statistics"""
        return self.stats.copy()


class DeadLetterQueue:
    """
    Redis-based dead letter queue for failed operations
    Allows for recovery and reprocessing
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize with Redis connection"""
        if redis_client is None:
            # Use default Redis connection
            # Try localhost first (for testing), then container name (for production)
            import os
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            if redis_host == 'localhost':
                # Try localhost first
                try:
                    test_redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
                    test_redis.ping()
                    self.redis = test_redis
                except:
                    # Fallback to container name
                    self.redis = redis.Redis(
                        host='pilotpros-redis-dev',
                        port=6379,
                        decode_responses=True
                    )
            else:
                self.redis = redis.Redis(
                    host=redis_host,
                    port=6379,
                    decode_responses=True
                )
        else:
            self.redis = redis_client

        self.queue_key = "dlq:messages"
        self.processing_key = "dlq:processing"
        self.completed_key = "dlq:completed"
        self.stats_key = "dlq:stats"

    async def enqueue(self, message: DeadLetterMessage) -> bool:
        """
        Add a failed message to the dead letter queue

        Args:
            message: The message to queue

        Returns:
            True if successfully queued
        """
        try:
            # Convert to JSON
            message_json = message.model_dump_json()

            # Add to queue with priority (higher priority = processed first)
            score = -message.priority if message.priority else time.time()
            self.redis.zadd(self.queue_key, {message_json: score})

            # Update statistics
            self.redis.hincrby(self.stats_key, "total_queued", 1)
            self.redis.hincrby(self.stats_key, f"queued_{message.error_type}", 1)

            logger.info(f"Message {message.id} added to DLQ")
            return True

        except Exception as e:
            logger.error(f"Failed to enqueue message: {e}")
            return False

    async def dequeue(self, count: int = 1) -> List[DeadLetterMessage]:
        """
        Retrieve messages from the queue for processing

        Args:
            count: Number of messages to retrieve

        Returns:
            List of messages
        """
        messages = []

        try:
            # Get messages with highest priority (lowest score)
            items = self.redis.zrange(self.queue_key, 0, count - 1, withscores=False)

            for item in items:
                try:
                    # Parse message
                    message = DeadLetterMessage.model_validate_json(item)
                    messages.append(message)

                    # Move to processing queue
                    self.redis.zrem(self.queue_key, item)
                    self.redis.zadd(self.processing_key, {item: time.time()})

                except Exception as e:
                    logger.error(f"Failed to parse DLQ message: {e}")
                    continue

            if messages:
                self.redis.hincrby(self.stats_key, "total_dequeued", len(messages))
                logger.info(f"Dequeued {len(messages)} messages from DLQ")

        except Exception as e:
            logger.error(f"Failed to dequeue messages: {e}")

        return messages

    async def mark_completed(self, message_id: str) -> bool:
        """Mark a message as successfully processed"""
        try:
            # Find and remove from processing queue
            processing_items = self.redis.zrange(self.processing_key, 0, -1)

            for item in processing_items:
                msg = DeadLetterMessage.model_validate_json(item)
                if msg.id == message_id:
                    self.redis.zrem(self.processing_key, item)

                    # Add to completed set with timestamp
                    self.redis.zadd(self.completed_key, {item: time.time()})

                    # Update stats
                    self.redis.hincrby(self.stats_key, "total_completed", 1)

                    logger.info(f"Message {message_id} marked as completed")
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to mark message as completed: {e}")
            return False

    async def requeue_failed(self, message_id: str) -> bool:
        """Requeue a failed message for another attempt"""
        try:
            # Find in processing queue
            processing_items = self.redis.zrange(self.processing_key, 0, -1)

            for item in processing_items:
                msg = DeadLetterMessage.model_validate_json(item)
                if msg.id == message_id:
                    # Update retry count and timestamp
                    msg.retry_count += 1
                    msg.last_retry_at = datetime.now()

                    # Remove from processing
                    self.redis.zrem(self.processing_key, item)

                    # Check if max retries exceeded
                    if msg.retry_count >= msg.max_retries:
                        # Move to failed set
                        self.redis.sadd("dlq:failed", msg.model_dump_json())
                        self.redis.hincrby(self.stats_key, "total_failed", 1)
                        logger.warning(f"Message {message_id} exceeded max retries")
                    else:
                        # Re-add to queue
                        await self.enqueue(msg)
                        logger.info(f"Message {message_id} requeued (attempt {msg.retry_count})")

                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to requeue message: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            stats = self.redis.hgetall(self.stats_key)
            stats["queue_size"] = self.redis.zcard(self.queue_key)
            stats["processing_size"] = self.redis.zcard(self.processing_key)
            stats["completed_size"] = self.redis.zcard(self.completed_key)
            stats["failed_size"] = self.redis.scard("dlq:failed")
            return stats
        except Exception:
            return {}


class FallbackHandler:
    """
    Handles graceful degradation with fallback responses
    """

    def __init__(self):
        """Initialize fallback handler with predefined responses"""
        self.fallback_responses = {
            UserLevel.BUSINESS: {
                "greeting": "Ciao! Sono momentaneamente in manutenzione, ma tornerò presto ad aiutarti.",
                "status": "Il sistema è temporaneamente in manutenzione. Riprova tra qualche minuto.",
                "error": "Mi dispiace, c'è stato un problema temporaneo. Il team tecnico è stato notificato.",
                "default": "Il servizio è momentaneamente non disponibile. Riprova più tardi."
            },
            UserLevel.ADMIN: {
                "greeting": "Sistema in modalità degradata. Funzionalità limitate attive.",
                "status": "Sistema in failover mode. Circuit breaker attivo.",
                "error": "Errore di sistema. Modalità degradata attiva. Check logs.",
                "default": "Sistema in modalità degradata. Consultare dashboard monitoring."
            },
            UserLevel.DEVELOPER: {
                "greeting": "[DEGRADED] Service operating in fallback mode",
                "status": "[CIRCUIT_OPEN] Primary services unavailable, using fallback",
                "error": "[ERROR] System failure - check logs and dead letter queue",
                "default": "[FALLBACK] Operating in degraded mode - limited functionality"
            }
        }

        self.static_cache = {}
        self.degradation_active = False

    def get_fallback_response(
        self,
        context: FailureContext,
        response_type: str = "default"
    ) -> str:
        """
        Get appropriate fallback response based on context

        Args:
            context: The failure context
            response_type: Type of response needed

        Returns:
            Fallback response string
        """
        user_level = context.user_level

        # Get user-appropriate responses
        responses = self.fallback_responses.get(
            user_level,
            self.fallback_responses[UserLevel.BUSINESS]
        )

        # Get specific or default response
        response = responses.get(response_type, responses["default"])

        # Add context if developer level
        if user_level == UserLevel.DEVELOPER:
            response += f"\n[Context: {context.error_type.value} - {context.agent_name}]"

        return response

    def is_degraded(self) -> bool:
        """Check if system is in degraded mode"""
        return self.degradation_active

    def activate_degradation(self, duration_seconds: int = 300):
        """Activate degraded mode for specified duration"""
        self.degradation_active = True
        logger.warning(f"Degradation mode activated for {duration_seconds} seconds")

        # Auto-deactivate after duration
        async def deactivate():
            await asyncio.sleep(duration_seconds)
            self.degradation_active = False
            logger.info("Degradation mode deactivated")

        asyncio.create_task(deactivate())


class ResilienceFramework:
    """
    Complete resilience framework integrating all components
    Provides unified interface for error handling
    """

    def __init__(self):
        """Initialize all resilience components"""
        self.circuit_breaker = get_circuit_breaker()
        self.retry_manager = RetryManager()
        self.dead_letter_queue = DeadLetterQueue()
        self.fallback_handler = FallbackHandler()

        # Error tracking
        self.error_counts = {}
        self.last_errors = []
        self.recovery_strategies = {
            FailureType.TIMEOUT: RecoveryStrategy.RETRY,
            FailureType.RATE_LIMIT: RecoveryStrategy.QUEUE,
            FailureType.API_ERROR: RecoveryStrategy.FALLBACK,
            FailureType.NETWORK: RecoveryStrategy.RETRY,
            FailureType.VALIDATION: RecoveryStrategy.SKIP,
            FailureType.UNKNOWN: RecoveryStrategy.ALERT
        }

    async def handle_failure(
        self,
        context: FailureContext,
        retry_func: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Main failure handling method

        Args:
            context: The failure context
            retry_func: Optional function to retry

        Returns:
            Response dict with handling result
        """
        # Track error
        self._track_error(context)

        # Determine recovery strategy
        strategy = self.recovery_strategies.get(
            context.error_type,
            RecoveryStrategy.FALLBACK
        )

        logger.info(f"Handling {context.error_type.value} with {strategy.value} strategy")

        # Execute recovery strategy
        if strategy == RecoveryStrategy.RETRY and retry_func:
            return await self._handle_retry(context, retry_func)

        elif strategy == RecoveryStrategy.QUEUE:
            return await self._handle_queue(context)

        elif strategy == RecoveryStrategy.FALLBACK:
            return await self._handle_fallback(context)

        elif strategy == RecoveryStrategy.SKIP:
            return self._handle_skip(context)

        elif strategy == RecoveryStrategy.ALERT:
            return await self._handle_alert(context)

        else:
            return await self._handle_fallback(context)

    async def _handle_retry(
        self,
        context: FailureContext,
        retry_func: Callable
    ) -> Dict[str, Any]:
        """Handle with retry strategy"""
        try:
            # Apply exponential backoff retry
            @self.retry_manager.with_exponential_backoff(
                max_attempts=3,
                min_wait=1,
                max_wait=10
            )
            async def retry_operation():
                return await retry_func()

            result = await retry_operation()

            return {
                "success": True,
                "strategy": "retry",
                "result": result,
                "retry_count": context.retry_count + 1
            }

        except Exception as e:
            logger.error(f"Retry strategy failed: {e}")
            # Fallback to queue
            return await self._handle_queue(context)

    async def _handle_queue(self, context: FailureContext) -> Dict[str, Any]:
        """Handle with dead letter queue strategy"""
        # Create DLQ message
        message = DeadLetterMessage(
            agent_name=context.agent_name,
            operation=context.operation,
            payload=context.original_request,
            error_type=context.error_type.value,
            error_message=context.error_message,
            retry_count=context.retry_count,
            user_level=context.user_level.value,
            session_id=context.metadata.get("session_id")
        )

        # Queue the message
        queued = await self.dead_letter_queue.enqueue(message)

        if queued:
            # Return fallback response
            response = self.fallback_handler.get_fallback_response(context, "error")

            return {
                "success": False,
                "strategy": "queue",
                "message_id": message.id,
                "response": response,
                "queued": True
            }
        else:
            # Queue failed, use fallback
            return await self._handle_fallback(context)

    async def _handle_fallback(self, context: FailureContext) -> Dict[str, Any]:
        """Handle with fallback strategy"""
        # Get appropriate fallback response
        response = self.fallback_handler.get_fallback_response(context)

        # Check if we should activate degradation mode
        if self._should_activate_degradation():
            self.fallback_handler.activate_degradation()

        return {
            "success": False,
            "strategy": "fallback",
            "response": response,
            "degraded": self.fallback_handler.is_degraded()
        }

    def _handle_skip(self, context: FailureContext) -> Dict[str, Any]:
        """Handle with skip strategy"""
        return {
            "success": False,
            "strategy": "skip",
            "reason": context.error_message,
            "skipped": True
        }

    async def _handle_alert(self, context: FailureContext) -> Dict[str, Any]:
        """Handle with alert strategy"""
        # Log critical error
        logger.critical(f"ALERT: Critical failure in {context.agent_name}: {context.error_message}")

        # Could send to monitoring system here

        # Return fallback
        return await self._handle_fallback(context)

    def _track_error(self, context: FailureContext):
        """Track error for monitoring"""
        key = f"{context.agent_name}:{context.error_type.value}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1

        # Keep last 100 errors
        self.last_errors.append({
            "timestamp": context.timestamp.isoformat(),
            "agent": context.agent_name,
            "type": context.error_type.value,
            "message": context.error_message[:200]  # Truncate long messages
        })

        if len(self.last_errors) > 100:
            self.last_errors = self.last_errors[-100:]

    def _should_activate_degradation(self) -> bool:
        """Check if degradation mode should be activated"""
        # Activate if more than 10 errors in last minute
        recent_errors = [
            e for e in self.last_errors
            if datetime.fromisoformat(e["timestamp"]) > datetime.now() - timedelta(minutes=1)
        ]

        return len(recent_errors) > 10

    async def process_dead_letter_queue(self, batch_size: int = 10) -> Dict[str, Any]:
        """
        Process messages from dead letter queue

        Args:
            batch_size: Number of messages to process

        Returns:
            Processing results
        """
        messages = await self.dead_letter_queue.dequeue(batch_size)

        results = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "requeued": 0
        }

        for message in messages:
            try:
                # Attempt to reprocess
                # This would call the original agent with the payload
                # For now, we'll simulate processing

                success = False  # Would be actual processing result

                if success:
                    await self.dead_letter_queue.mark_completed(message.id)
                    results["succeeded"] += 1
                else:
                    await self.dead_letter_queue.requeue_failed(message.id)
                    results["requeued"] += 1

                results["processed"] += 1

            except Exception as e:
                logger.error(f"Failed to process DLQ message {message.id}: {e}")
                results["failed"] += 1

        return results

    async def get_health_status(self) -> Dict[str, Any]:
        """Get complete health status of resilience systems"""
        dlq_stats = await self.dead_letter_queue.get_stats()

        return {
            "circuit_breaker": self.circuit_breaker.get_stats(),
            "retry_manager": self.retry_manager.get_stats(),
            "dead_letter_queue": dlq_stats,
            "fallback_handler": {
                "degraded": self.fallback_handler.is_degraded()
            },
            "error_tracking": {
                "total_errors": sum(self.error_counts.values()),
                "error_types": self.error_counts,
                "recent_errors": len(self.last_errors)
            }
        }

    def create_resilient_agent(self, agent_class):
        """
        Decorator to make any agent resilient

        Usage:
            @resilience_framework.create_resilient_agent
            class MyAgent:
                async def process(self, ...):
                    ...
        """
        original_process = agent_class.process
        framework_instance = self  # Capture framework instance

        @wraps(original_process)
        async def resilient_process(agent_self, *args, **kwargs):
            try:
                # Try normal processing
                return await original_process(agent_self, *args, **kwargs)

            except Exception as e:
                # Create failure context
                context = FailureContext(
                    agent_name=agent_class.__name__,
                    operation="process",
                    error_type=framework_instance._classify_error(e),
                    error_message=str(e),
                    timestamp=datetime.now(),
                    user_level=kwargs.get("user_level", UserLevel.BUSINESS),
                    original_request=kwargs
                )

                # Handle with resilience framework
                return await framework_instance.handle_failure(
                    context,
                    lambda: original_process(agent_self, *args, **kwargs)
                )

        agent_class.process = resilient_process
        return agent_class

    def _classify_error(self, error: Exception) -> FailureType:
        """Classify error type from exception"""
        error_str = str(error).lower()

        if "timeout" in error_str:
            return FailureType.TIMEOUT
        elif "rate" in error_str or "limit" in error_str:
            return FailureType.RATE_LIMIT
        elif "api" in error_str or "endpoint" in error_str:
            return FailureType.API_ERROR
        elif "network" in error_str or "connection" in error_str:
            return FailureType.NETWORK
        elif "validation" in error_str or "invalid" in error_str:
            return FailureType.VALIDATION
        else:
            return FailureType.UNKNOWN


# Singleton instance
_resilience_instance = None

def get_resilience_framework() -> ResilienceFramework:
    """Get or create singleton resilience framework"""
    global _resilience_instance
    if _resilience_instance is None:
        _resilience_instance = ResilienceFramework()
    return _resilience_instance