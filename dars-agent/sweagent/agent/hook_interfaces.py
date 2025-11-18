"""Segregated hook interfaces following Interface Segregation Principle."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from sweagent.agent.models import APIStats


class ILifecycleHook(ABC):
    """Hook for agent lifecycle events."""

    @abstractmethod
    def on_init(self) -> None:
        """Called when the hook is added."""
        pass

    @abstractmethod
    def on_run_start(self) -> None:
        """Called when a run starts."""
        pass

    @abstractmethod
    def on_run_done(self) -> None:
        """Called when a run completes."""
        pass


class IStepHook(ABC):
    """Hook for individual step events."""

    @abstractmethod
    def on_step_start(self) -> None:
        """Called when a step starts."""
        pass

    @abstractmethod
    def on_step_done(self, *, trajectory_step: Any, model_stats: APIStats) -> None:
        """Called when a step completes."""
        pass


class IActionHook(ABC):
    """Hook for action-related events."""

    @abstractmethod
    def on_actions_generated(self, *, thought: str, action: str, output: str) -> None:
        """Called when actions are generated."""
        pass

    @abstractmethod
    def on_sub_action_started(self, *, sub_action: str) -> None:
        """Called when a sub-action starts."""
        pass

    @abstractmethod
    def on_sub_action_executed(self, *, obs: str, done: bool) -> None:
        """Called when a sub-action executes."""
        pass


class IQueryHook(ABC):
    """Hook for model query events."""

    @abstractmethod
    def on_model_query(self, *, query: str, agent: str) -> None:
        """Called when model is queried."""
        pass

    @abstractmethod
    def on_query_message_added(
        self,
        *,
        role: str,
        content: str,
        agent: str,
        is_demo: bool = False,
        thought: str = "",
        action: str = "",
    ) -> None:
        """Called when a message is added to query."""
        pass


class CompositeAgentHook(ILifecycleHook, IStepHook, IActionHook, IQueryHook):
    """Composite hook that implements all hook interfaces with no-op defaults.

    Clients can subclass this and override only the methods they need,
    following the Interface Segregation Principle.
    """

    def on_init(self) -> None:
        """Called when the hook is added."""
        pass

    def on_run_start(self) -> None:
        """Called when a run starts."""
        pass

    def on_run_done(self) -> None:
        """Called when a run completes."""
        pass

    def on_step_start(self) -> None:
        """Called when a step starts."""
        pass

    def on_step_done(self, *, trajectory_step: Any, model_stats: APIStats) -> None:
        """Called when a step completes."""
        pass

    def on_actions_generated(self, *, thought: str, action: str, output: str) -> None:
        """Called when actions are generated."""
        pass

    def on_sub_action_started(self, *, sub_action: str) -> None:
        """Called when a sub-action starts."""
        pass

    def on_sub_action_executed(self, *, obs: str, done: bool) -> None:
        """Called when a sub-action executes."""
        pass

    def on_model_query(self, *, query: str, agent: str) -> None:
        """Called when model is queried."""
        pass

    def on_query_message_added(
        self,
        *,
        role: str,
        content: str,
        agent: str,
        is_demo: bool = False,
        thought: str = "",
        action: str = "",
    ) -> None:
        """Called when a message is added to query."""
        pass


class IEnvLifecycleHook(ABC):
    """Hook for environment lifecycle events."""

    @abstractmethod
    def on_init(self) -> None:
        """Called when the hook is added."""
        pass

    @abstractmethod
    def on_close(self) -> None:
        """Called when the environment is closed."""
        pass


class IEnvSetupHook(ABC):
    """Hook for environment setup events."""

    @abstractmethod
    def on_copy_repo_started(self, *, repo_type: str, repo_path: str) -> None:
        """Called when repository copying starts."""
        pass

    @abstractmethod
    def on_install_env_started(self) -> None:
        """Called when environment installation starts."""
        pass


class CompositeEnvHook(IEnvLifecycleHook, IEnvSetupHook):
    """Composite environment hook with no-op defaults."""

    def on_init(self) -> None:
        """Called when the hook is added."""
        pass

    def on_close(self) -> None:
        """Called when the environment is closed."""
        pass

    def on_copy_repo_started(self, *, repo_type: str, repo_path: str) -> None:
        """Called when repository copying starts."""
        pass

    def on_install_env_started(self) -> None:
        """Called when environment installation starts."""
        pass
