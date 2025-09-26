"""
Performance & Cost Tracker
Tracks response time, token usage, and costs for EACH model in real-time
"""

import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics

@dataclass
class ModelMetrics:
    """Metrics for a single model call"""
    model_id: str
    provider: str
    timestamp: datetime
    response_time_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    success: bool
    error: Optional[str] = None

class PerformanceTracker:
    """
    Track performance and costs for all models
    Updates DYNAMICALLY as new models are added
    """

    def __init__(self, data_path: str = "/app/data/metrics.json"):
        self.data_path = data_path
        self.metrics: List[ModelMetrics] = []
        self.cost_table = self.load_cost_table()
        self.load_metrics()

    def load_cost_table(self) -> Dict:
        """
        Dynamic cost table - updates as new models appear
        Costs in $ per 1M tokens
        """
        return {
            # FREE models
            "groq": {
                "default": {"input": 0, "output": 0},  # FREE!
            },
            "google": {
                "gemini-2.0-flash-exp": {"input": 0, "output": 0},  # FREE tier
                "gemini-1.5-flash": {"input": 0, "output": 0},  # FREE tier
                "gemini-1.5-flash-8b": {"input": 0, "output": 0},  # FREE tier
                "gemini-1.5-pro": {"input": 0, "output": 0},  # FREE tier limited
            },
            # CHEAP models via OpenRouter
            "openrouter": {
                "google/gemini-2.0-flash-exp": {"input": 0.075, "output": 0.30},
                "deepseek/deepseek-r1": {"input": 0.14, "output": 2.80},
                "meta-llama/llama-3.3-70b": {"input": 0.60, "output": 0.60},
                "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
                "anthropic/claude-3.5-haiku": {"input": 1.00, "output": 5.00},
            },
            # DIRECT APIs
            "anthropic": {
                "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
                "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
                "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
            },
            "openai": {
                "gpt-4o-mini": {"input": 0.15, "output": 0.60},
                "gpt-4o": {"input": 2.50, "output": 10.00},
                "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            }
        }

    def calculate_cost(self, model_id: str, provider: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost based on model and token usage
        Returns cost in USD
        """
        # Get provider costs
        provider_costs = self.cost_table.get(provider, {})

        # Find model costs
        model_costs = None
        if model_id in provider_costs:
            model_costs = provider_costs[model_id]
        elif "default" in provider_costs:
            model_costs = provider_costs["default"]
        else:
            # Unknown model - assume mid-tier pricing
            model_costs = {"input": 1.00, "output": 2.00}

        # Calculate cost (convert from per 1M tokens)
        input_cost = (input_tokens / 1_000_000) * model_costs["input"]
        output_cost = (output_tokens / 1_000_000) * model_costs["output"]

        return round(input_cost + output_cost, 6)

    def track_call(self, model_id: str, provider: str, start_time: float,
                   input_tokens: int, output_tokens: int,
                   success: bool = True, error: str = None):
        """Track a model call with performance and cost"""

        response_time_ms = (time.time() - start_time) * 1000
        total_tokens = input_tokens + output_tokens
        estimated_cost = self.calculate_cost(model_id, provider, input_tokens, output_tokens)

        metric = ModelMetrics(
            model_id=model_id,
            provider=provider,
            timestamp=datetime.now(),
            response_time_ms=round(response_time_ms, 2),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            success=success,
            error=error
        )

        self.metrics.append(metric)

        # Keep only last 1000 metrics in memory
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]

        # Save periodically
        if len(self.metrics) % 10 == 0:
            self.save_metrics()

        return metric

    def get_model_stats(self, model_id: str = None, hours: int = 24) -> Dict:
        """
        Get performance statistics for a model or all models
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        # Filter metrics
        filtered = [
            m for m in self.metrics
            if m.timestamp > cutoff and (model_id is None or m.model_id == model_id)
        ]

        if not filtered:
            return {"message": "No data available"}

        # Group by model
        by_model = defaultdict(list)
        for metric in filtered:
            by_model[metric.model_id].append(metric)

        stats = {}
        for model, metrics_list in by_model.items():
            response_times = [m.response_time_ms for m in metrics_list if m.success]
            costs = [m.estimated_cost for m in metrics_list]
            tokens = [m.total_tokens for m in metrics_list]
            errors = [m for m in metrics_list if not m.success]

            stats[model] = {
                "calls": len(metrics_list),
                "success_rate": round((len(response_times) / len(metrics_list)) * 100, 1) if metrics_list else 0,
                "response_time": {
                    "avg": round(statistics.mean(response_times), 1) if response_times else 0,
                    "p50": round(statistics.median(response_times), 1) if response_times else 0,
                    "p95": round(statistics.quantiles(response_times, n=20)[18], 1) if len(response_times) > 1 else 0,
                    "min": round(min(response_times), 1) if response_times else 0,
                    "max": round(max(response_times), 1) if response_times else 0,
                },
                "tokens": {
                    "total": sum(tokens),
                    "avg": round(statistics.mean(tokens), 0) if tokens else 0,
                },
                "cost": {
                    "total": round(sum(costs), 4),
                    "avg": round(statistics.mean(costs), 6) if costs else 0,
                    "per_1k_tokens": round((sum(costs) / sum(tokens)) * 1000, 4) if sum(tokens) > 0 else 0,
                },
                "errors": len(errors),
                "last_error": errors[-1].error if errors else None,
            }

        return stats

    def get_comparison_table(self, hours: int = 24) -> List[Dict]:
        """
        Get comparison table of all models
        Perfect for seeing which is fastest/cheapest
        """
        stats = self.get_model_stats(hours=hours)

        comparison = []
        for model_id, model_stats in stats.items():
            comparison.append({
                "model": model_id,
                "calls": model_stats["calls"],
                "avg_response_ms": model_stats["response_time"]["avg"],
                "p95_response_ms": model_stats["response_time"]["p95"],
                "success_rate": model_stats["success_rate"],
                "total_cost": model_stats["cost"]["total"],
                "cost_per_1k_tokens": model_stats["cost"]["per_1k_tokens"],
                "total_tokens": model_stats["tokens"]["total"],
            })

        # Sort by cost per token (cheapest first)
        comparison.sort(key=lambda x: x["cost_per_1k_tokens"])

        return comparison

    def get_recommendations(self) -> Dict:
        """
        Get recommendations based on performance and cost
        """
        stats = self.get_model_stats(hours=24)

        if not stats:
            return {"message": "Not enough data for recommendations"}

        # Find best models
        fastest = None
        cheapest = None
        most_reliable = None

        for model_id, model_stats in stats.items():
            # Skip if too few calls
            if model_stats["calls"] < 10:
                continue

            # Fastest
            if not fastest or model_stats["response_time"]["p50"] < stats[fastest]["response_time"]["p50"]:
                fastest = model_id

            # Cheapest
            if not cheapest or model_stats["cost"]["per_1k_tokens"] < stats[cheapest]["cost"]["per_1k_tokens"]:
                cheapest = model_id

            # Most reliable
            if not most_reliable or model_stats["success_rate"] > stats[most_reliable]["success_rate"]:
                most_reliable = model_id

        recommendations = {
            "fastest": {
                "model": fastest,
                "p50_ms": stats[fastest]["response_time"]["p50"] if fastest else None,
            },
            "cheapest": {
                "model": cheapest,
                "cost_per_1k": stats[cheapest]["cost"]["per_1k_tokens"] if cheapest else None,
            },
            "most_reliable": {
                "model": most_reliable,
                "success_rate": stats[most_reliable]["success_rate"] if most_reliable else None,
            },
            "suggested_chain": [],
        }

        # Build suggested fallback chain
        if cheapest and cheapest not in recommendations["suggested_chain"]:
            recommendations["suggested_chain"].append(cheapest)
        if fastest and fastest not in recommendations["suggested_chain"]:
            recommendations["suggested_chain"].append(fastest)
        if most_reliable and most_reliable not in recommendations["suggested_chain"]:
            recommendations["suggested_chain"].append(most_reliable)

        return recommendations

    def save_metrics(self):
        """Save metrics to disk"""
        try:
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)

            # Convert to dict for JSON
            data = {
                "metrics": [
                    {**asdict(m), "timestamp": m.timestamp.isoformat()}
                    for m in self.metrics[-500:]  # Save last 500
                ],
                "last_updated": datetime.now().isoformat()
            }

            with open(self.data_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Failed to save metrics: {e}")

    def load_metrics(self):
        """Load metrics from disk"""
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r') as f:
                    data = json.load(f)

                self.metrics = []
                for m in data.get("metrics", []):
                    m["timestamp"] = datetime.fromisoformat(m["timestamp"])
                    self.metrics.append(ModelMetrics(**m))

        except Exception as e:
            print(f"Failed to load metrics: {e}")
            self.metrics = []

# Singleton instance
_tracker = None

def get_tracker() -> PerformanceTracker:
    """Get singleton performance tracker"""
    global _tracker
    if _tracker is None:
        _tracker = PerformanceTracker()
    return _tracker