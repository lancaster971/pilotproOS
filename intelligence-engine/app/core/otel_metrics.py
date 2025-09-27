"""
OpenTelemetry Metrics for Milhena
==================================
Simple metrics collection without external dependencies
"""

from typing import Dict
from collections import defaultdict
import time


class SimpleMetrics:
    """
    Simple metrics collector (NO OpenTelemetry dependencies)
    Collects basic metrics for monitoring
    """

    def __init__(self):
        """Initialize metrics"""
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        self.gauges = {}
        self.start_time = time.time()

    def increment(self, name: str, value: int = 1) -> None:
        """Increment counter"""
        self.counters[name] += value

    def record_duration(self, name: str, duration_ms: float) -> None:
        """Record duration in histogram"""
        self.histograms[name].append(duration_ms)

    def set_gauge(self, name: str, value: float) -> None:
        """Set gauge value"""
        self.gauges[name] = value

    def get_counter(self, name: str) -> int:
        """Get counter value"""
        return self.counters.get(name, 0)

    def get_percentile(self, name: str, percentile: int = 95) -> float:
        """Get percentile from histogram"""
        values = self.histograms.get(name, [])
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def get_average(self, name: str) -> float:
        """Get average from histogram"""
        values = self.histograms.get(name, [])
        return sum(values) / len(values) if values else 0.0

    def get_all_metrics(self) -> Dict:
        """Get all metrics as dictionary"""
        metrics = {
            "uptime_seconds": int(time.time() - self.start_time),
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {}
        }

        for name, values in self.histograms.items():
            if values:
                metrics["histograms"][name] = {
                    "count": len(values),
                    "avg": self.get_average(name),
                    "p95": self.get_percentile(name, 95),
                    "p99": self.get_percentile(name, 99),
                    "min": min(values),
                    "max": max(values)
                }

        return metrics

    def reset(self) -> None:
        """Reset all metrics"""
        self.counters.clear()
        self.histograms.clear()
        self.gauges.clear()
        self.start_time = time.time()


# Singleton instance
_instance = None

def get_metrics() -> SimpleMetrics:
    """Get or create singleton metrics instance"""
    global _instance
    if _instance is None:
        _instance = SimpleMetrics()
    return _instance