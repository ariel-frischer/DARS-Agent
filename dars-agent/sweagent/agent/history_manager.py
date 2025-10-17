"""History management abstraction for agents."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class IHistoryManager(ABC):
    """Interface for managing agent conversation history."""

    @abstractmethod
    def append(self, item: dict) -> None:
        """Add an item to history."""
        pass

    @abstractmethod
    def get_history(self) -> List[Dict[str, Any]]:
        """Get the full history."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear the history."""
        pass


class ListHistoryManager(IHistoryManager):
    """Simple list-based history manager for linear agents."""

    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def append(self, item: dict) -> None:
        """Add an item to history."""
        self._history.append(item)

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the full history."""
        return self._history.copy()

    def clear(self) -> None:
        """Clear the history."""
        self._history.clear()

    def __len__(self) -> int:
        return len(self._history)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        return self._history[index]
