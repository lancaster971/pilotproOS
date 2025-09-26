"""
Monitoring and observability for Intelligence Engine
"""

from contextlib import contextmanager
from datetime import datetime
import time
from typing import Any, Dict
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI, Response
from loguru import logger
import json

# Prometheus metrics
request_count = Counter(
    'intelligence_engine_requests_total',
    'Total number of requests',
    ['endpoint', 'method', 'status']
)

request_duration = Histogram(
    'intelligence_engine_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint', 'method']
)

active_chains = Gauge(
    'intelligence_engine_active_chains',
    'Number of active LangChain executions'
)

cache_hits = Counter(
    'intelligence_engine_cache_hits_total',
    'Total number of cache hits'
)

llm_tokens = Counter(
    'intelligence_engine_llm_tokens_total',
    'Total number of LLM tokens used',
    ['model', 'type']
)

error_count = Counter(
    'intelligence_engine_errors_total',
    'Total number of errors',
    ['error_type']
)

def setup_monitoring(app: FastAPI):
    """Setup monitoring endpoints and middleware"""

    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(
            generate_latest(),
            media_type="text/plain"
        )

    @app.middleware("http")
    async def monitor_requests(request, call_next):
        """Monitor all HTTP requests"""
        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Record metrics
            request_count.labels(
                endpoint=request.url.path,
                method=request.method,
                status=response.status_code
            ).inc()

            request_duration.labels(
                endpoint=request.url.path,
                method=request.method
            ).observe(duration)

            # Log request
            logger.info(
                f"Request: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Duration: {duration:.3f}s"
            )

            return response

        except Exception as e:
            error_count.labels(error_type=type(e).__name__).inc()
            logger.error(f"Request failed: {str(e)}")
            raise

@contextmanager
def track_request(user_id: str, operation: str):
    """Context manager for tracking individual requests"""
    start_time = time.time()
    request_id = f"{user_id}_{operation}_{int(start_time)}"

    logger.info(f"Starting {operation} for user {user_id} (ID: {request_id})")

    try:
        yield request_id
        duration = time.time() - start_time
        logger.info(f"Completed {operation} in {duration:.3f}s (ID: {request_id})")

    except Exception as e:
        duration = time.time() - start_time
        error_count.labels(error_type=type(e).__name__).inc()
        logger.error(f"Failed {operation} after {duration:.3f}s: {str(e)} (ID: {request_id})")
        raise

def track_llm_usage(model: str, prompt_tokens: int, completion_tokens: int):
    """Track LLM token usage"""
    llm_tokens.labels(model=model, type="prompt").inc(prompt_tokens)
    llm_tokens.labels(model=model, type="completion").inc(completion_tokens)

    total_tokens = prompt_tokens + completion_tokens
    logger.debug(f"LLM usage - Model: {model}, Tokens: {total_tokens}")

def track_chain_execution(chain_name: str, start_time: float, success: bool, metadata: Dict[str, Any] = None):
    """Track LangChain execution"""
    duration = time.time() - start_time

    log_data = {
        "chain": chain_name,
        "duration": f"{duration:.3f}s",
        "success": success,
        "timestamp": datetime.utcnow().isoformat()
    }

    if metadata:
        log_data["metadata"] = metadata

    if success:
        logger.info(f"Chain executed successfully: {json.dumps(log_data)}")
    else:
        logger.error(f"Chain execution failed: {json.dumps(log_data)}")

def increment_cache_hit():
    """Track cache hit"""
    cache_hits.inc()
    logger.debug("Cache hit recorded")

def update_active_chains(delta: int):
    """Update active chains count"""
    if delta > 0:
        active_chains.inc(delta)
    else:
        active_chains.dec(abs(delta))
    logger.debug(f"Active chains: {active_chains._value.get()}")

class PerformanceTracker:
    """Track and log performance metrics"""

    def __init__(self):
        self.metrics = {}

    def start_operation(self, operation: str):
        """Start tracking an operation"""
        self.metrics[operation] = {
            "start_time": time.time(),
            "steps": []
        }

    def add_step(self, operation: str, step: str):
        """Add a step to the operation"""
        if operation in self.metrics:
            self.metrics[operation]["steps"].append({
                "name": step,
                "timestamp": time.time()
            })

    def end_operation(self, operation: str) -> Dict[str, Any]:
        """End tracking and return metrics"""
        if operation not in self.metrics:
            return {}

        end_time = time.time()
        metrics = self.metrics[operation]
        duration = end_time - metrics["start_time"]

        result = {
            "operation": operation,
            "total_duration": duration,
            "steps": []
        }

        prev_time = metrics["start_time"]
        for step in metrics["steps"]:
            step_duration = step["timestamp"] - prev_time
            result["steps"].append({
                "name": step["name"],
                "duration": step_duration
            })
            prev_time = step["timestamp"]

        del self.metrics[operation]
        return result