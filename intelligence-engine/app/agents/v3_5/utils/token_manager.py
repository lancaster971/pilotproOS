"""
TokenManager - Track and manage token usage for OpenAI models
Ensures we don't exceed the 10M token budget from offerta speciale
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path
import asyncio
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class TokenUsage:
    """Track token usage per model"""
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    requests: int = 0
    last_reset: datetime = field(default_factory=datetime.now)

@dataclass
class TokenBudget:
    """Token budget configuration"""
    model: str
    max_tokens: int
    daily_limit: int
    warning_threshold: float = 0.8  # Warn at 80% usage

class TokenManager:
    """
    Manages token usage across all LLM models
    Tracks usage to stay within 10M token budgets
    """

    # Token budgets from offerta speciale
    BUDGETS = {
        # 10M Token Group (2.5M for usage tiers 1-2)
        "gpt-4.1-mini-2025-04-14": TokenBudget("gpt-4.1-mini-2025-04-14", 10_000_000, 500_000),
        "gpt-4.1-nano-2025-04-14": TokenBudget("gpt-4.1-nano-2025-04-14", 10_000_000, 500_000),
        "gpt-4o-mini-2024-07-18": TokenBudget("gpt-4o-mini-2024-07-18", 10_000_000, 500_000),
        "o4-mini-2025-04-16": TokenBudget("o4-mini-2025-04-16", 10_000_000, 500_000),

        # 1M Token Group (250K for usage tiers 1-2)
        "gpt-4o-2024-11-20": TokenBudget("gpt-4o-2024-11-20", 1_000_000, 50_000),
        "o1-2024-12-17": TokenBudget("o1-2024-12-17", 1_000_000, 50_000),
    }

    # Approximate costs per 1K tokens (for tracking)
    COSTS = {
        "gpt-4.1-nano-2025-04-14": {"input": 0.00015, "output": 0.0006},
        "gpt-4.1-mini-2025-04-14": {"input": 0.00015, "output": 0.0006},
        "gpt-4o-mini-2024-07-18": {"input": 0.00015, "output": 0.0006},
        "gpt-4o-2024-11-20": {"input": 0.0025, "output": 0.01},
    }

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "/tmp/milhena_token_usage.json"
        self.usage: Dict[str, TokenUsage] = {}
        self._load_usage()
        self._setup_auto_save()

    def _load_usage(self):
        """Load token usage from persistent storage"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for model, usage_data in data.items():
                        usage_data['last_reset'] = datetime.fromisoformat(usage_data['last_reset'])
                        self.usage[model] = TokenUsage(**usage_data)
                logger.info(f"Loaded token usage for {len(self.usage)} models")
            except Exception as e:
                logger.error(f"Failed to load token usage: {e}")
                self.usage = {}
        else:
            self.usage = {}

    def _save_usage(self):
        """Save token usage to persistent storage"""
        try:
            data = {}
            for model, usage in self.usage.items():
                usage_dict = asdict(usage)
                usage_dict['last_reset'] = usage_dict['last_reset'].isoformat()
                data[model] = usage_dict

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Token usage saved")
        except Exception as e:
            logger.error(f"Failed to save token usage: {e}")

    def _setup_auto_save(self):
        """Setup automatic saving every 5 minutes"""
        async def auto_save():
            while True:
                await asyncio.sleep(300)  # 5 minutes
                self._save_usage()

        # Start auto-save task in background
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(auto_save())
        except RuntimeError:
            # No event loop running yet
            pass

    def track_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Any]:
        """
        Track token usage for a model

        Returns:
            Dict with usage stats and warnings
        """
        if model not in self.usage:
            self.usage[model] = TokenUsage(model=model)

        usage = self.usage[model]

        # Check if we need to reset daily usage
        if datetime.now() - usage.last_reset > timedelta(days=1):
            logger.info(f"Resetting daily usage for {model}")
            usage.input_tokens = 0
            usage.output_tokens = 0
            usage.total_tokens = 0
            usage.requests = 0
            usage.last_reset = datetime.now()

        # Update usage
        usage.input_tokens += input_tokens
        usage.output_tokens += output_tokens
        usage.total_tokens += input_tokens + output_tokens
        usage.requests += 1

        # Calculate cost
        if model in self.COSTS:
            cost = self.COSTS[model]
            usage.cost_usd += (input_tokens / 1000) * cost["input"]
            usage.cost_usd += (output_tokens / 1000) * cost["output"]

        # Check limits
        warnings = []
        budget = self.BUDGETS.get(model)

        if budget:
            # Check daily limit
            if usage.total_tokens > budget.daily_limit:
                warnings.append(f"DAILY LIMIT EXCEEDED for {model}: {usage.total_tokens}/{budget.daily_limit}")
                logger.warning(warnings[-1])

            # Check warning threshold
            daily_usage_percent = usage.total_tokens / budget.daily_limit
            if daily_usage_percent > budget.warning_threshold:
                warnings.append(f"HIGH USAGE WARNING for {model}: {daily_usage_percent:.1%} of daily limit")
                logger.warning(warnings[-1])

            # Check total budget
            total_usage_percent = usage.total_tokens / budget.max_tokens
            if total_usage_percent > budget.warning_threshold:
                warnings.append(f"BUDGET WARNING for {model}: {total_usage_percent:.1%} of 10M tokens used")
                logger.warning(warnings[-1])

        # Save usage
        self._save_usage()

        return {
            "model": model,
            "usage": asdict(usage),
            "warnings": warnings,
            "can_continue": len(warnings) == 0 or "EXCEEDED" not in str(warnings)
        }

    def get_usage_stats(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage statistics

        Args:
            model: Specific model or None for all

        Returns:
            Usage statistics
        """
        if model:
            if model in self.usage:
                usage = self.usage[model]
                budget = self.BUDGETS.get(model)

                stats = asdict(usage)
                if budget:
                    stats["daily_limit"] = budget.daily_limit
                    stats["max_tokens"] = budget.max_tokens
                    stats["daily_usage_percent"] = usage.total_tokens / budget.daily_limit
                    stats["total_usage_percent"] = usage.total_tokens / budget.max_tokens

                return stats
            else:
                return {"error": f"No usage data for model {model}"}
        else:
            # Return all models
            all_stats = {}
            for model_name, usage in self.usage.items():
                budget = self.BUDGETS.get(model_name)
                stats = asdict(usage)

                if budget:
                    stats["daily_limit"] = budget.daily_limit
                    stats["max_tokens"] = budget.max_tokens
                    stats["daily_usage_percent"] = usage.total_tokens / budget.daily_limit
                    stats["total_usage_percent"] = usage.total_tokens / budget.max_tokens

                all_stats[model_name] = stats

            return all_stats

    def can_use_model(self, model: str, estimated_tokens: int = 1000) -> bool:
        """
        Check if we can use a model without exceeding limits

        Args:
            model: Model name
            estimated_tokens: Estimated tokens for next request

        Returns:
            True if within limits
        """
        if model not in self.BUDGETS:
            # No budget tracking for this model (e.g., GROQ)
            return True

        budget = self.BUDGETS[model]
        usage = self.usage.get(model, TokenUsage(model=model))

        # Check if daily reset needed
        if datetime.now() - usage.last_reset > timedelta(days=1):
            # Will reset, so we can use it
            return True

        # Check if adding estimated tokens would exceed daily limit
        if usage.total_tokens + estimated_tokens > budget.daily_limit:
            logger.warning(f"Model {model} would exceed daily limit with {estimated_tokens} tokens")
            return False

        # Check if we're getting close to total budget (90% threshold)
        if usage.total_tokens + estimated_tokens > budget.max_tokens * 0.9:
            logger.warning(f"Model {model} approaching total budget limit")
            return False

        return True

    def get_best_available_model(self, complexity: str = "simple") -> Optional[str]:
        """
        Get the best available model based on complexity and usage

        Args:
            complexity: "simple", "medium", or "complex"

        Returns:
            Best available model name or None
        """
        # Model selection based on complexity
        model_preferences = {
            "simple": [
                "gpt-4.1-nano-2025-04-14",  # Fastest, cheapest
                "gpt-4.1-mini-2025-04-14",
                "gpt-4o-mini-2024-07-18"
            ],
            "medium": [
                "gpt-4.1-mini-2025-04-14",
                "gpt-4o-mini-2024-07-18",
                "o4-mini-2025-04-16"
            ],
            "complex": [
                "gpt-4o-2024-11-20",  # Most capable
                "o1-2024-12-17",
                "gpt-4.1-mini-2025-04-14"  # Fallback
            ]
        }

        models = model_preferences.get(complexity, model_preferences["simple"])

        # Find first available model
        for model in models:
            if self.can_use_model(model):
                logger.info(f"Selected model {model} for {complexity} task")
                return model

        logger.error(f"No models available for {complexity} task")
        return None

    def reset_model_usage(self, model: str):
        """
        Manually reset usage for a specific model

        Args:
            model: Model name to reset
        """
        if model in self.usage:
            self.usage[model] = TokenUsage(model=model)
            self._save_usage()
            logger.info(f"Reset usage for model {model}")

    def get_usage_report(self) -> str:
        """
        Generate a human-readable usage report

        Returns:
            Formatted usage report
        """
        report = "=== Token Usage Report ===\n\n"

        total_cost = 0.0
        total_tokens = 0

        for model, usage in self.usage.items():
            budget = self.BUDGETS.get(model)

            report += f"Model: {model}\n"
            report += f"  Requests: {usage.requests}\n"
            report += f"  Total Tokens: {usage.total_tokens:,}\n"
            report += f"  Cost: ${usage.cost_usd:.4f}\n"

            if budget:
                daily_pct = (usage.total_tokens / budget.daily_limit) * 100
                total_pct = (usage.total_tokens / budget.max_tokens) * 100
                report += f"  Daily Usage: {daily_pct:.1f}% ({usage.total_tokens:,}/{budget.daily_limit:,})\n"
                report += f"  Total Budget: {total_pct:.2f}% ({usage.total_tokens:,}/{budget.max_tokens:,})\n"

            report += f"  Last Reset: {usage.last_reset.strftime('%Y-%m-%d %H:%M')}\n\n"

            total_cost += usage.cost_usd
            total_tokens += usage.total_tokens

        report += f"=== Summary ===\n"
        report += f"Total Tokens Used: {total_tokens:,}\n"
        report += f"Total Cost: ${total_cost:.4f}\n"

        return report