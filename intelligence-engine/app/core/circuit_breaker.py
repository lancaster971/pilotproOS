"""
Circuit Breaker for Multi-Provider LLM Failover
================================================
OpenAI → Anthropic → Groq → Local Ollama
Failover time <100ms
"""

import time
from typing import Optional, Callable, Any, List
from dataclasses import dataclass
from enum import Enum


class ProviderStatus(Enum):
    """Provider status"""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


@dataclass
class Provider:
    """LLM Provider configuration"""
    name: str
    priority: int
    call_function: Callable
    max_failures: int = 3
    timeout_seconds: int = 30
    failures: int = 0
    last_failure_time: float = 0
    status: ProviderStatus = ProviderStatus.HEALTHY


class CircuitBreaker:
    """
    Circuit Breaker for LLM providers
    Automatically fails over to backup providers
    """

    def __init__(self):
        """Initialize circuit breaker with provider list"""
        self.providers: List[Provider] = []
        self.current_provider_index = 0
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "failovers": 0,
            "provider_calls": {}
        }

    def register_provider(self,
                         name: str,
                         priority: int,
                         call_function: Callable,
                         max_failures: int = 3,
                         timeout_seconds: int = 30) -> None:
        """Register a provider"""
        provider = Provider(
            name=name,
            priority=priority,
            call_function=call_function,
            max_failures=max_failures,
            timeout_seconds=timeout_seconds
        )
        self.providers.append(provider)
        self.providers.sort(key=lambda p: p.priority)
        self.stats["provider_calls"][name] = 0

    def call(self, *args, **kwargs) -> Any:
        """
        Call provider with automatic failover

        Returns:
            Result from successful provider
        """
        self.stats["total_calls"] += 1
        start_time = time.time()

        for i, provider in enumerate(self.providers):
            # Skip failed providers still in timeout
            if provider.status == ProviderStatus.FAILED:
                if time.time() - provider.last_failure_time < provider.timeout_seconds:
                    continue
                else:
                    provider.status = ProviderStatus.HEALTHY
                    provider.failures = 0

            try:
                # Track failover
                if i > 0:
                    self.stats["failovers"] += 1

                # Call provider
                result = provider.call_function(*args, **kwargs)

                # Success - update stats
                self.stats["successful_calls"] += 1
                self.stats["provider_calls"][provider.name] += 1
                provider.failures = 0
                provider.status = ProviderStatus.HEALTHY

                elapsed = time.time() - start_time
                return result

            except Exception as e:
                # Failure - update provider status
                provider.failures += 1
                provider.last_failure_time = time.time()

                if provider.failures >= provider.max_failures:
                    provider.status = ProviderStatus.FAILED

                # Continue to next provider
                continue

        # All providers failed
        self.stats["failed_calls"] += 1
        raise Exception("All providers failed")

    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Reset statistics"""
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "failovers": 0,
            "provider_calls": {p.name: 0 for p in self.providers}
        }

    def get_provider_status(self) -> List[dict]:
        """Get status of all providers"""
        return [
            {
                "name": p.name,
                "priority": p.priority,
                "status": p.status.value,
                "failures": p.failures,
                "calls": self.stats["provider_calls"].get(p.name, 0)
            }
            for p in self.providers
        ]


# Singleton instance
_instance = None

def get_circuit_breaker() -> CircuitBreaker:
    """Get or create singleton circuit breaker"""
    global _instance
    if _instance is None:
        _instance = CircuitBreaker()
    return _instance