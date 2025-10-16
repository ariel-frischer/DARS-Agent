"""Model interfaces applying Interface Segregation Principle."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IAPIConfigManager(ABC):
    """Interface for API configuration - Interface Segregation Principle."""

    @abstractmethod
    def setup_api_config(self) -> None:
        """Configure API keys and endpoints."""
        pass


class IMessageFormatter(ABC):
    """Interface for message formatting - Interface Segregation Principle."""

    @abstractmethod
    def history_to_messages(
        self,
        history: List[Dict[str, str]],
        is_demonstration: bool = False,
    ) -> List[Dict[str, str]] | str:
        """Convert chat history to provider-specific message format."""
        pass


class IModelQuerier(ABC):
    """Interface for model querying - Interface Segregation Principle."""

    @abstractmethod
    def query(
        self,
        history: List[Dict[str, str]],
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """Query the language model."""
        pass


class IStatsTracker(ABC):
    """Interface for statistics tracking - Interface Segregation Principle."""

    @abstractmethod
    def update_stats(self, input_tokens: int, output_tokens: int, **kwargs) -> float:
        """Update usage statistics and check limits."""
        pass

    @abstractmethod
    def reset_stats(self, other: Optional[Any] = None) -> None:
        """Reset or update statistics."""
        pass

    @abstractmethod
    def get_stats(self) -> Any:
        """Get current statistics."""
        pass


class IModelMetadataProvider(ABC):
    """Interface for model metadata - Interface Segregation Principle."""

    @abstractmethod
    def get_model_metadata(self, model_name: str) -> Dict[str, Any]:
        """Get metadata for a specific model."""
        pass

    @abstractmethod
    def resolve_model_name(self, model_name: str) -> str:
        """Resolve shortcuts to full model names."""
        pass
