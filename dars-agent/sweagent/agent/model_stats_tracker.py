"""Model statistics tracking - Single Responsibility Principle."""
from __future__ import annotations
from dataclasses import dataclass, fields
from typing import Dict, Any, Optional
from sweagent.utils.log import get_logger

logger = get_logger("model_stats")


@dataclass
class ModelStats:
    """Statistics for model usage."""
    total_cost: float = 0
    instance_cost: float = 0
    tokens_sent: int = 0
    tokens_received: int = 0
    api_calls: int = 0

    def __add__(self, other):
        if not isinstance(other, ModelStats):
            raise TypeError("Can only add ModelStats with ModelStats")
        return ModelStats(
            **{field.name: getattr(self, field.name) + getattr(other, field.name) for field in fields(self)}
        )

    def replace(self, other):
        if not isinstance(other, ModelStats):
            raise TypeError("Can only replace ModelStats with ModelStats")
        return ModelStats(**{field.name: getattr(other, field.name) for field in fields(self)})

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "total_cost": self.total_cost,
            "instance_cost": self.instance_cost,
            "tokens_sent": self.tokens_sent,
            "tokens_received": self.tokens_received,
            "api_calls": self.api_calls,
        }


class CostLimitChecker:
    """Checks cost limits - Single Responsibility."""

    def __init__(self, total_limit: float = 0.0, instance_limit: float = 0.0):
        self.total_limit = total_limit
        self.instance_limit = instance_limit

    def check_limits(self, stats: ModelStats) -> None:
        """Check if cost limits are exceeded and raise exception if so."""
        if 0 < self.total_limit <= stats.total_cost:
            logger.warning(f"Cost {stats.total_cost:.4f} exceeds limit {self.total_limit:.4f}")
            from sweagent.agent.models import CostLimitExceededError
            raise CostLimitExceededError("Total cost limit exceeded")

        if 0 < self.instance_limit <= stats.instance_cost:
            logger.warning(f"Cost {stats.instance_cost:.4f} exceeds limit {self.instance_limit:.4f}")
            from sweagent.agent.models import CostLimitExceededError
            raise CostLimitExceededError("Instance cost limit exceeded")


class ModelStatsTracker:
    """Tracks and updates model usage statistics."""

    def __init__(self, total_cost_limit: float = 0.0, per_instance_cost_limit: float = 0.0):
        self.stats = ModelStats()
        self.cost_checker = CostLimitChecker(total_cost_limit, per_instance_cost_limit)

    def reset(self, other: Optional[ModelStats] = None) -> None:
        """Reset or update statistics."""
        if other is None:
            self.stats = ModelStats(total_cost=self.stats.total_cost)
            logger.info("Resetting model stats")
        else:
            self.stats = other

    def update(
        self,
        input_tokens: int,
        output_tokens: int,
        cost: float
    ) -> float:
        """Update statistics and check limits."""
        self.stats.total_cost += cost
        self.stats.instance_cost += cost
        self.stats.tokens_sent += input_tokens
        self.stats.tokens_received += output_tokens
        self.stats.api_calls += 1

        logger.info(
            f"input_tokens={input_tokens:,}, "
            f"output_tokens={output_tokens:,}, "
            f"instance_cost={self.stats.instance_cost:.4f}, "
            f"cost={cost:.4f}"
        )
        logger.info(
            f"total_tokens_sent={self.stats.tokens_sent:,}, "
            f"total_tokens_received={self.stats.tokens_received:,}, "
            f"total_cost={self.stats.total_cost:.4f}, "
            f"total_api_calls={self.stats.api_calls:,}"
        )

        self.cost_checker.check_limits(self.stats)
        return cost

    def get_stats(self) -> ModelStats:
        """Get current statistics."""
        return self.stats


class CostCalculator:
    """Calculates costs for different model types - Single Responsibility."""

    @staticmethod
    def calculate_standard_cost(
        input_tokens: int,
        output_tokens: int,
        metadata: Dict[str, Any]
    ) -> float:
        """Calculate cost for standard pricing."""
        return (
            metadata["cost_per_input_token"] * input_tokens +
            metadata["cost_per_output_token"] * output_tokens
        )

    @staticmethod
    def calculate_tiered_cost(
        input_tokens: int,
        output_tokens: int,
        metadata: Dict[str, Any]
    ) -> float:
        """Calculate cost for tiered pricing."""
        tier = (
            "extended"
            if input_tokens > metadata["pricing_tiers"]["standard"]["max_tokens"]
            else "standard"
        )
        return (
            metadata["pricing_tiers"][tier]["cost_per_input_token"] * input_tokens +
            metadata["pricing_tiers"][tier]["cost_per_output_token"] * output_tokens
        )

    @staticmethod
    def calculate_cached_cost(
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int,
        cache_minutes: int,
        metadata: Dict[str, Any]
    ) -> float:
        """Calculate cost including caching."""
        return (
            metadata["cost_per_input_token"] * (input_tokens - cached_tokens) +
            metadata["cost_per_cached_input_token"] * cached_tokens +
            metadata.get("cost_for_caching_input_token_per_min", 0) * cached_tokens * cache_minutes +
            metadata["cost_per_output_token"] * output_tokens
        )
