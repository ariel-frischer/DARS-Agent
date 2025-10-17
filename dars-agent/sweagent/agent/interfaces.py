"""
SOLID-compliant interfaces for the agent system.

This module defines abstract base classes following Interface Segregation Principle.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from sweagent.agent.models import APIStats


class IHistoryManager(ABC):
    """Interface for managing agent conversation history."""

    @abstractmethod
    def append(self, item: dict) -> None:
        """Add an item to history."""
        pass

    @abstractmethod
    def get_local_history(self) -> list[dict[str, str]]:
        """Get the filtered local history."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear the history."""
        pass


class INodeManager(ABC):
    """Interface for managing tree nodes (DARS-specific)."""

    @abstractmethod
    def create_node(self, **kwargs) -> Any:
        """Create a new node."""
        pass

    @abstractmethod
    def add_child(self, parent: Any, child: Any) -> None:
        """Add a child node to a parent."""
        pass

    @abstractmethod
    def get_root(self) -> Optional[Any]:
        """Get the root node."""
        pass


class IExpansionStrategy(ABC):
    """Interface for different expansion strategies."""

    @abstractmethod
    def should_expand(self, node: Any, config: Any) -> bool:
        """Determine if a node should be expanded."""
        pass

    @abstractmethod
    def get_expansion_candidates(self, node: Any, num_samples: int) -> List[tuple]:
        """Generate expansion candidates."""
        pass

    @abstractmethod
    def select_best_expansion(self, candidates: List[Any]) -> int:
        """Select the best expansion from candidates."""
        pass


class ITrajectoryBuilder(ABC):
    """Interface for building and managing trajectories."""

    @abstractmethod
    def add_step(self, action: str, observation: str, thought: str, **kwargs) -> None:
        """Add a step to the trajectory."""
        pass

    @abstractmethod
    def get_trajectory(self) -> List[Dict[str, Any]]:
        """Get the complete trajectory."""
        pass

    @abstractmethod
    def save(self, path: str, **metadata) -> None:
        """Save trajectory to file."""
        pass


class IActionParser(ABC):
    """Interface for parsing and validating actions."""

    @abstractmethod
    def parse(self, action: str) -> List[Dict[str, Any]]:
        """Parse action into executable components."""
        pass

    @abstractmethod
    def validate(self, action: str) -> bool:
        """Validate if action is allowed."""
        pass

    @abstractmethod
    def guard_multiline(self, action: str) -> str:
        """Guard multiline inputs."""
        pass


class IModelInterface(ABC):
    """Interface for interacting with language models."""

    @abstractmethod
    def query(self, messages: List[Dict], temperature: Optional[float] = None) -> str:
        """Query the model with messages."""
        pass

    @abstractmethod
    def get_stats(self) -> APIStats:
        """Get current API statistics."""
        pass

    @abstractmethod
    def reset_stats(self, initial_stats: Optional[APIStats] = None) -> None:
        """Reset API statistics."""
        pass


class IEnvironmentInterface(ABC):
    """Interface for environment interactions."""

    @abstractmethod
    def step(self, action: str) -> tuple[str, Any, bool, Dict]:
        """Execute action in environment."""
        pass

    @abstractmethod
    def communicate(self, command: str) -> str:
        """Send command to environment."""
        pass

    @abstractmethod
    def reset(self, **kwargs) -> None:
        """Reset the environment."""
        pass


class IAgentHookObserver(ABC):
    """Observer interface for agent lifecycle events."""

    @abstractmethod
    def update(self, event: str, **kwargs) -> None:
        """Handle event notification."""
        pass


class IStepHook(ABC):
    """Interface for step-level hooks."""

    def on_step_start(self) -> None:
        """Called when a step starts."""
        pass

    def on_step_done(self, **kwargs) -> None:
        """Called when a step completes."""
        pass


class IRunHook(ABC):
    """Interface for run-level hooks."""

    def on_run_start(self) -> None:
        """Called when a run starts."""
        pass

    def on_run_done(self) -> None:
        """Called when a run completes."""
        pass


class IModelQueryHook(ABC):
    """Interface for model query hooks."""

    def on_model_query(self, **kwargs) -> None:
        """Called when model is queried."""
        pass

    def on_query_message_added(self, **kwargs) -> None:
        """Called when a message is added to query."""
        pass
