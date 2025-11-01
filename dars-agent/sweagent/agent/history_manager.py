"""
History management implementation following Single Responsibility Principle.

This module handles conversation history tracking and processing.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sweagent.agent.interfaces import IHistoryManager, IAgentHookObserver


class HistoryManager(IHistoryManager):
    """
    Manages conversation history for agents.

    Single Responsibility: Only handles history storage and retrieval.
    """

    def __init__(self, history_processor=None, hooks: Optional[List[IAgentHookObserver]] = None):
        """
        Initialize history manager.

        Args:
            history_processor: Function to process history before retrieval
            hooks: List of observers to notify on history changes
        """
        self._history: List[Dict[str, Any]] = []
        self._history_processor = history_processor or (lambda x: x)
        self._hooks = hooks or []

    def append(self, item: dict) -> None:
        """
        Add an item to history and notify observers.

        Args:
            item: Dictionary containing history entry
        """
        # Notify hooks before appending
        for hook in self._hooks:
            hook.update('query_message_added', **item)

        self._history.append(item)

    def get_local_history(self, agent_name: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Get filtered and processed history.

        Args:
            agent_name: Filter by specific agent name if provided

        Returns:
            Processed history entries
        """
        if agent_name:
            filtered = [entry for entry in self._history if entry.get("agent") == agent_name]
        else:
            filtered = self._history

        return self._history_processor(filtered)

    def clear(self) -> None:
        """Clear all history."""
        self._history.clear()

    def get_raw_history(self) -> List[Dict[str, Any]]:
        """Get unprocessed history."""
        return self._history.copy()

    def add_hook(self, hook: IAgentHookObserver) -> None:
        """Add a history observer."""
        self._hooks.append(hook)

    def remove_hook(self, hook: IAgentHookObserver) -> None:
        """Remove a history observer."""
        if hook in self._hooks:
            self._hooks.remove(hook)


class TreeHistoryManager(IHistoryManager):
    """
    History manager that works with tree-based node structures.

    Used for DARS agents with tree exploration.
    """

    def __init__(self, root_node=None, history_processor=None, hooks: Optional[List] = None):
        """
        Initialize tree-based history manager.

        Args:
            root_node: Root node of the tree
            history_processor: Function to process history
            hooks: List of observers
        """
        self._root_node = root_node
        self._history_processor = history_processor or (lambda x: x)
        self._hooks = hooks or []

    def append(self, item: dict) -> None:
        """
        Append is handled differently in tree structure.
        Use create_node instead.
        """
        raise NotImplementedError("Use create_node for tree-based history")

    def get_local_history(self, node=None, agent_name: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Reconstruct history by backtracking from a node.

        Args:
            node: Node to backtrack from (uses root if None)
            agent_name: Filter by agent name

        Returns:
            History entries from root to node
        """
        if node is None:
            node = self._root_node

        history = []
        self._backtrack_history(node, history)

        if agent_name:
            history = [entry for entry in history if entry.get("agent") == agent_name]

        return self._history_processor(history)

    def _backtrack_history(self, node, history: List[Dict]) -> None:
        """Recursively backtrack to build history."""
        if node is None:
            return

        if hasattr(node, 'parent'):
            self._backtrack_history(node.parent, history)

        # Build history entry from node
        if hasattr(node, 'is_demo') and node.is_demo:
            history.append({
                "agent": node.agent,
                "content": node.content,
                "is_demo": True,
                "role": node.role,
            })
        elif hasattr(node, 'thought') and node.thought is not None:
            history.append({
                "role": node.role,
                "content": node.content,
                "thought": node.thought,
                "action": node.action,
                "agent": node.agent
            })
        else:
            history.append({
                "role": node.role,
                "content": node.content,
                "agent": node.agent
            })

    def clear(self) -> None:
        """Clear by setting root to None."""
        self._root_node = None

    def set_root(self, node) -> None:
        """Set the root node."""
        self._root_node = node

    def get_root(self):
        """Get the root node."""
        return self._root_node

    def add_hook(self, hook: IAgentHookObserver) -> None:
        """Add observer hook."""
        self._hooks.append(hook)
