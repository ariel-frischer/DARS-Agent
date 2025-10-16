"""Agent hook interfaces applying Interface Segregation Principle.

Instead of one large AgentHook interface with many methods,
we split into smaller, focused interfaces.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict


class ILifecycleHook(ABC):
    """Hook for agent lifecycle events."""

    @abstractmethod
    def on_init(self) -> None:
        """Called when agent is initialized."""
        pass

    @abstractmethod
    def on_run_start(self) -> None:
        """Called when agent run starts."""
        pass

    @abstractmethod
    def on_run_done(self) -> None:
        """Called when agent run completes."""
        pass


class IStepHook(ABC):
    """Hook for agent step events."""

    @abstractmethod
    def on_step_start(self) -> None:
        """Called when a step starts."""
        pass

    @abstractmethod
    def on_step_done(self, trajectory_step: Any, model_stats: Any) -> None:
        """Called when a step completes."""
        pass


class IActionHook(ABC):
    """Hook for action-related events."""

    @abstractmethod
    def on_actions_generated(self, thought: str, action: str, output: str) -> None:
        """Called when actions are generated."""
        pass

    @abstractmethod
    def on_sub_action_started(self, sub_action: str) -> None:
        """Called when a sub-action starts."""
        pass

    @abstractmethod
    def on_sub_action_executed(self, obs: str, done: bool) -> None:
        """Called when a sub-action is executed."""
        pass


class IModelHook(ABC):
    """Hook for model query events."""

    @abstractmethod
    def on_model_query(self, query: str, agent: str) -> None:
        """Called when model is queried."""
        pass


class IHistoryHook(ABC):
    """Hook for history events."""

    @abstractmethod
    def on_query_message_added(
        self,
        role: str,
        content: str,
        agent: str,
        is_demo: bool = False,
        thought: str = "",
        action: str = "",
    ) -> None:
        """Called when a message is added to history."""
        pass


class CompositeAgentHook(
    ILifecycleHook,
    IStepHook,
    IActionHook,
    IModelHook,
    IHistoryHook
):
    """Composite hook that implements all interfaces for backward compatibility."""

    def on_init(self) -> None:
        pass

    def on_run_start(self) -> None:
        pass

    def on_run_done(self) -> None:
        pass

    def on_step_start(self) -> None:
        pass

    def on_step_done(self, trajectory_step: Any, model_stats: Any) -> None:
        pass

    def on_actions_generated(self, thought: str, action: str, output: str) -> None:
        pass

    def on_sub_action_started(self, sub_action: str) -> None:
        pass

    def on_sub_action_executed(self, obs: str, done: bool) -> None:
        pass

    def on_model_query(self, query: str, agent: str) -> None:
        pass

    def on_query_message_added(
        self,
        role: str,
        content: str,
        agent: str,
        is_demo: bool = False,
        thought: str = "",
        action: str = "",
    ) -> None:
        pass


class HookManager:
    """Manages and dispatches to multiple hooks - Open/Closed Principle."""

    def __init__(self):
        self.lifecycle_hooks: list[ILifecycleHook] = []
        self.step_hooks: list[IStepHook] = []
        self.action_hooks: list[IActionHook] = []
        self.model_hooks: list[IModelHook] = []
        self.history_hooks: list[IHistoryHook] = []

    def add_lifecycle_hook(self, hook: ILifecycleHook) -> None:
        """Add a lifecycle hook."""
        self.lifecycle_hooks.append(hook)

    def add_step_hook(self, hook: IStepHook) -> None:
        """Add a step hook."""
        self.step_hooks.append(hook)

    def add_action_hook(self, hook: IActionHook) -> None:
        """Add an action hook."""
        self.action_hooks.append(hook)

    def add_model_hook(self, hook: IModelHook) -> None:
        """Add a model hook."""
        self.model_hooks.append(hook)

    def add_history_hook(self, hook: IHistoryHook) -> None:
        """Add a history hook."""
        self.history_hooks.append(hook)

    def add_composite_hook(self, hook: CompositeAgentHook) -> None:
        """Add a composite hook to all relevant lists."""
        self.lifecycle_hooks.append(hook)
        self.step_hooks.append(hook)
        self.action_hooks.append(hook)
        self.model_hooks.append(hook)
        self.history_hooks.append(hook)

    def notify_init(self) -> None:
        """Notify all lifecycle hooks of init."""
        for hook in self.lifecycle_hooks:
            hook.on_init()

    def notify_run_start(self) -> None:
        """Notify all lifecycle hooks of run start."""
        for hook in self.lifecycle_hooks:
            hook.on_run_start()

    def notify_run_done(self) -> None:
        """Notify all lifecycle hooks of run done."""
        for hook in self.lifecycle_hooks:
            hook.on_run_done()

    def notify_step_start(self) -> None:
        """Notify all step hooks of step start."""
        for hook in self.step_hooks:
            hook.on_step_start()

    def notify_step_done(self, trajectory_step: Any, model_stats: Any) -> None:
        """Notify all step hooks of step done."""
        for hook in self.step_hooks:
            hook.on_step_done(trajectory_step, model_stats)

    def notify_actions_generated(self, thought: str, action: str, output: str) -> None:
        """Notify all action hooks of actions generated."""
        for hook in self.action_hooks:
            hook.on_actions_generated(thought=thought, action=action, output=output)

    def notify_sub_action_started(self, sub_action: str) -> None:
        """Notify all action hooks of sub-action started."""
        for hook in self.action_hooks:
            hook.on_sub_action_started(sub_action=sub_action)

    def notify_sub_action_executed(self, obs: str, done: bool) -> None:
        """Notify all action hooks of sub-action executed."""
        for hook in self.action_hooks:
            hook.on_sub_action_executed(obs=obs, done=done)

    def notify_model_query(self, query: str, agent: str) -> None:
        """Notify all model hooks of model query."""
        for hook in self.model_hooks:
            hook.on_model_query(query=query, agent=agent)

    def notify_query_message_added(
        self,
        role: str,
        content: str,
        agent: str,
        is_demo: bool = False,
        thought: str = "",
        action: str = "",
    ) -> None:
        """Notify all history hooks of message added."""
        for hook in self.history_hooks:
            hook.on_query_message_added(
                role=role,
                content=content,
                agent=agent,
                is_demo=is_demo,
                thought=thought,
                action=action,
            )
