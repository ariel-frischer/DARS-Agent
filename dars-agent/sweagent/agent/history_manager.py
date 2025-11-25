"""History management abstraction for agents - Single Responsibility Principle."""
from __future__ import annotations
from typing import Any, Dict, List, Protocol
from abc import ABC, abstractmethod


class HistoryObserver(Protocol):
    """Observer interface for history changes - Interface Segregation Principle."""
    def on_history_entry_added(self, entry: Dict[str, Any]) -> None:
        """Called when a new entry is added to history."""
        ...


class IHistoryManager(ABC):
    """Abstract interface for history management - Dependency Inversion Principle."""

    @abstractmethod
    def add_entry(self, entry: Dict[str, Any]) -> None:
        """Add an entry to history."""
        pass

    @abstractmethod
    def get_history(self) -> List[Dict[str, Any]]:
        """Get full history."""
        pass

    @abstractmethod
    def get_filtered_history(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get history filtered by agent name."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear history."""
        pass

    @abstractmethod
    def attach_observer(self, observer: HistoryObserver) -> None:
        """Attach an observer."""
        pass


class SimpleHistoryManager(IHistoryManager):
    """Simple implementation of history management."""

    def __init__(self):
        self._history: List[Dict[str, Any]] = []
        self._observers: List[HistoryObserver] = []

    def add_entry(self, entry: Dict[str, Any]) -> None:
        """Add an entry to history and notify observers."""
        self._history.append(entry)
        self._notify_observers(entry)

    def get_history(self) -> List[Dict[str, Any]]:
        """Get full history."""
        return self._history.copy()

    def get_filtered_history(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get history filtered by agent name."""
        return [entry for entry in self._history if entry.get("agent") == agent_name]

    def clear(self) -> None:
        """Clear history."""
        self._history.clear()

    def attach_observer(self, observer: HistoryObserver) -> None:
        """Attach an observer to receive history updates."""
        self._observers.append(observer)

    def _notify_observers(self, entry: Dict[str, Any]) -> None:
        """Notify all observers of a new history entry."""
        for observer in self._observers:
            observer.on_history_entry_added(entry)
