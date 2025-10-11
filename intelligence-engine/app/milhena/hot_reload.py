"""
Hot-Reload Pattern System for Auto-Learning
Implements Redis PubSub-based pattern reloading without container restarts

Architecture:
- Redis PubSub channel: pilotpros:patterns:reload
- Message format: {"action": "reload", "pattern_id": Optional[int]}
- Publisher: Backend admin endpoint + Auto-learning save trigger
- Subscriber: PatternReloader background task (FastAPI lifespan)

Performance:
- Reload latency: <100ms target
- Thread-safe pattern map updates
- No impact on concurrent query processing

References:
- Redis asyncio PubSub: https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html
- FastAPI lifespan events: https://fastapi.tiangolo.com/advanced/events/
- asyncpg pool best practices: https://magicstack.github.io/asyncpg/current/usage.html
"""

import asyncio
import json
import os
from typing import Optional, Callable, Dict, Any
from loguru import logger
import redis.asyncio as redis


class PatternReloader:
    """
    Manages Redis PubSub subscriber for hot-reloading auto-learned patterns.

    Usage:
        reloader = PatternReloader(
            redis_url="redis://redis-dev:6379/0",
            reload_callback=milhena_graph.reload_patterns
        )
        await reloader.start()  # Starts background subscriber task
        await reloader.stop()   # Graceful shutdown
    """

    def __init__(
        self,
        redis_url: str,
        reload_callback: Callable[[], Any],
        channel: str = "pilotpros:patterns:reload"
    ):
        """
        Initialize PatternReloader.

        Args:
            redis_url: Redis connection URL (e.g., redis://redis-dev:6379/0)
            reload_callback: Async callback to invoke when reload message received
            channel: Redis PubSub channel name (default: pilotpros:patterns:reload)
        """
        self.redis_url = redis_url
        self.reload_callback = reload_callback
        self.channel = channel

        # Async components
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.subscriber_task: Optional[asyncio.Task] = None
        self.shutdown_event = asyncio.Event()

        # Metrics
        self.total_reloads = 0
        self.failed_reloads = 0
        self.last_reload_time: Optional[float] = None

    async def start(self):
        """
        Start Redis PubSub subscriber as background task.
        Should be called from FastAPI lifespan startup.
        """
        try:
            # Create Redis async client (redis.asyncio pattern)
            # Reference: https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5.0,
                socket_keepalive=True
            )

            # Create PubSub instance
            self.pubsub = self.redis_client.pubsub()

            # Subscribe to channel
            await self.pubsub.subscribe(self.channel)
            logger.info(f"[HOT-RELOAD] Subscribed to Redis channel: {self.channel}")

            # Start background subscriber task
            self.subscriber_task = asyncio.create_task(self._subscriber_loop())
            logger.info("[HOT-RELOAD] Background subscriber task started")

        except Exception as e:
            logger.error(f"[HOT-RELOAD] Failed to start subscriber: {e}")
            await self._cleanup()
            raise

    async def stop(self):
        """
        Graceful shutdown of subscriber.
        Should be called from FastAPI lifespan shutdown.
        """
        logger.info("[HOT-RELOAD] Initiating graceful shutdown...")

        # Signal shutdown to break infinite loop
        self.shutdown_event.set()

        # Wait for subscriber task to finish (with timeout)
        if self.subscriber_task:
            try:
                await asyncio.wait_for(self.subscriber_task, timeout=5.0)
                logger.info("[HOT-RELOAD] Subscriber task stopped")
            except asyncio.TimeoutError:
                logger.warning("[HOT-RELOAD] Subscriber task timeout, cancelling...")
                self.subscriber_task.cancel()
                try:
                    await self.subscriber_task
                except asyncio.CancelledError:
                    pass

        # Cleanup Redis connections
        await self._cleanup()
        logger.info("[HOT-RELOAD] Shutdown complete")

    async def _cleanup(self):
        """Cleanup Redis connections"""
        try:
            if self.pubsub:
                await self.pubsub.unsubscribe(self.channel)
                await self.pubsub.aclose()
                self.pubsub = None

            if self.redis_client:
                await self.redis_client.aclose()
                self.redis_client = None
        except Exception as e:
            logger.error(f"[HOT-RELOAD] Cleanup error: {e}")

    async def _subscriber_loop(self):
        """
        Infinite loop listening for PubSub messages.
        Breaks on shutdown_event signal.

        Pattern from: https://gist.github.com/nicksonthc/525742d9a81d3950b443810e8899ee0e
        """
        logger.info("[HOT-RELOAD] Subscriber loop started")
        reconnect_attempts = 0
        max_reconnect_attempts = 5

        while not self.shutdown_event.is_set():
            try:
                # Get message with timeout (allows checking shutdown_event)
                # Reference: redis.asyncio PubSub pattern with listen()
                async for message in self.pubsub.listen():
                    # Check shutdown signal
                    if self.shutdown_event.is_set():
                        break

                    # Process message
                    if message and message.get("type") == "message":
                        await self._handle_message(message)

            except redis.ConnectionError as e:
                reconnect_attempts += 1
                if reconnect_attempts >= max_reconnect_attempts:
                    logger.error(f"[HOT-RELOAD] Max reconnect attempts ({max_reconnect_attempts}) reached, stopping subscriber")
                    break

                logger.warning(f"[HOT-RELOAD] Redis connection lost: {e}, reconnecting (attempt {reconnect_attempts}/{max_reconnect_attempts})...")
                await asyncio.sleep(2 ** reconnect_attempts)  # Exponential backoff

                try:
                    # Reconnect
                    await self._cleanup()
                    await self.start()
                    reconnect_attempts = 0  # Reset counter on successful reconnect
                except Exception as reconnect_err:
                    logger.error(f"[HOT-RELOAD] Reconnection failed: {reconnect_err}")

            except Exception as e:
                logger.error(f"[HOT-RELOAD] Subscriber loop error: {e}")
                await asyncio.sleep(1)  # Avoid tight loop on persistent errors

        logger.info("[HOT-RELOAD] Subscriber loop exited")

    async def _handle_message(self, message: Dict[str, Any]):
        """
        Process incoming PubSub message and trigger pattern reload.

        Message format: {"action": "reload", "pattern_id": Optional[int]}

        Args:
            message: Redis PubSub message dict with 'data' field
        """
        import time
        start_time = time.time()

        try:
            # Parse message data (JSON string)
            data = message.get("data", "{}")
            payload = json.loads(data) if isinstance(data, str) else data

            action = payload.get("action")
            pattern_id = payload.get("pattern_id")

            logger.info(f"[HOT-RELOAD] Received message: action={action}, pattern_id={pattern_id}")

            # Validate action
            if action != "reload":
                logger.warning(f"[HOT-RELOAD] Unknown action: {action}, skipping")
                return

            # Invoke reload callback
            if asyncio.iscoroutinefunction(self.reload_callback):
                await self.reload_callback()
            else:
                self.reload_callback()

            # Update metrics
            reload_duration = (time.time() - start_time) * 1000  # Convert to ms
            self.total_reloads += 1
            self.last_reload_time = time.time()

            logger.info(f"[HOT-RELOAD] Pattern reload complete in {reload_duration:.2f}ms (total_reloads={self.total_reloads})")

        except json.JSONDecodeError as e:
            logger.error(f"[HOT-RELOAD] Invalid JSON message: {e}, data={message.get('data')}")
            self.failed_reloads += 1

        except Exception as e:
            logger.error(f"[HOT-RELOAD] Error handling message: {e}")
            self.failed_reloads += 1

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get hot-reload metrics for monitoring.

        Returns:
            Dict with reload stats (total_reloads, failed_reloads, last_reload_time)
        """
        return {
            "total_reloads": self.total_reloads,
            "failed_reloads": self.failed_reloads,
            "last_reload_time": self.last_reload_time,
            "subscriber_active": self.subscriber_task is not None and not self.subscriber_task.done()
        }


# Utility function for publishing reload messages (used by backend/graph.py)
async def publish_reload_message(redis_url: str, pattern_id: Optional[int] = None):
    """
    Publish reload message to trigger pattern hot-reload.

    Usage from backend:
        await publish_reload_message(REDIS_URL, pattern_id=123)

    Usage from graph.py after learning:
        await publish_reload_message(os.getenv("REDIS_URL"), pattern_id=new_pattern_id)

    Args:
        redis_url: Redis connection URL
        pattern_id: Optional pattern ID (for single pattern reload)
    """
    client = None
    try:
        # Create temporary Redis client
        client = await redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2.0
        )

        # Prepare message
        message = json.dumps({
            "action": "reload",
            "pattern_id": pattern_id
        })

        # Publish to channel
        channel = "pilotpros:patterns:reload"
        subscribers = await client.publish(channel, message)

        logger.info(f"[HOT-RELOAD] Published reload message to {subscribers} subscriber(s)")

    except Exception as e:
        logger.error(f"[HOT-RELOAD] Failed to publish reload message: {e}")

    finally:
        if client:
            await client.aclose()
