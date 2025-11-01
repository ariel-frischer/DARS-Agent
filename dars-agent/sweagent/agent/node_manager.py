"""
Node management for tree-based agent exploration.

Following Single Responsibility Principle: Only handles node creation and tree structure.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sweagent.agent.interfaces import INodeManager


class DARSNode:
    """
    Tree node for DARS exploration.

    Encapsulates all node-specific data and relationships.
    """

    def __init__(
            self,
            role: str,
            content: str,
            agent: str,
            thought: Optional[str] = None,
            action: Optional[str] = None,
            parent: Optional[DARSNode] = None,
            is_demo: bool = False,
            is_terminal: bool = False,
            _depth: Optional[int] = None
    ):
        """Initialize a DARS node."""
        self.role = role
        self.content = content
        self.thought = thought
        self.action = action
        self.agent = agent
        self.parent = parent
        self.is_demo = is_demo
        self.children: List[DARSNode] = []
        self.is_terminal = is_terminal
        self._depth = 0 if parent is None else parent._depth + 1
        self._action_expansion_limit = None
        self.expansion_history = []

        if _depth is not None:
            self._depth = _depth

        # Metadata fields
        self.node_id = None
        self.codegraph_keyword = None
        self.codegraph_context = None
        self.expansion_candidates = None
        self.critic_prompt = None
        self.critic_response = None
        self.expansion_prompt = None

    @property
    def depth(self) -> int:
        """Get node depth in tree."""
        return self._depth

    def add_child(self, child: 'DARSNode') -> None:
        """
        Add a child node.

        Args:
            child: Child node to add
        """
        child.parent = self
        child._depth = self._depth + 1
        child.expansion_history = self.expansion_history.copy()
        if self._action_expansion_limit:
            child._action_expansion_limit = self._action_expansion_limit.copy()
        self.children.append(child)

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "role": self.role,
            "content": self.content,
            "thought": self.thought,
            "action": self.action,
            "agent": self.agent,
            "is_demo": self.is_demo,
            "is_terminal": self.is_terminal,
            "children": [child.to_dict() for child in self.children],
            "_depth": self._depth,
            "node_id": self.node_id,
            "expansion_history": self.expansion_history,
            "_action_expansion_limit": self._action_expansion_limit,
            "codegraph_keyword": self.codegraph_keyword,
            "codegraph_context": self.codegraph_context,
            "expansion_prompt": self.expansion_prompt,
            "critic_prompt": self.critic_prompt,
            "critic_response": self.critic_response,
            "expansion_candidates": self.expansion_candidates
        }


class NodeManager(INodeManager):
    """
    Manages tree node creation and operations.

    Single Responsibility: Only handles node lifecycle and structure.
    """

    def __init__(self):
        """Initialize node manager."""
        self._root_node: Optional[DARSNode] = None
        self._node_counter = 0

    def create_node(self, **kwargs) -> DARSNode:
        """
        Create a new node with auto-incrementing ID.

        Args:
            **kwargs: Node initialization parameters

        Returns:
            Newly created node
        """
        node = DARSNode(**kwargs)
        node.node_id = self._node_counter
        self._node_counter += 1
        return node

    def add_child(self, parent: DARSNode, child: DARSNode) -> None:
        """
        Add child to parent node.

        Args:
            parent: Parent node
            child: Child node to add
        """
        parent.add_child(child)

    def get_root(self) -> Optional[DARSNode]:
        """Get the root node."""
        return self._root_node

    def set_root(self, node: DARSNode) -> None:
        """Set the root node."""
        self._root_node = node

    def get_node_count(self) -> int:
        """Get total number of nodes created."""
        return self._node_counter

    def reset_counter(self) -> None:
        """Reset node counter."""
        self._node_counter = 0

    def build_node_map(self, root: Optional[DARSNode] = None) -> Dict[int, DARSNode]:
        """
        Build a map of node IDs to nodes.

        Args:
            root: Root node to start from (uses internal root if None)

        Returns:
            Dictionary mapping node IDs to nodes
        """
        if root is None:
            root = self._root_node

        if root is None:
            return {}

        node_map = {}
        self._build_node_map_recursive(root, node_map)
        return node_map

    def _build_node_map_recursive(self, node: DARSNode, node_map: Dict[int, DARSNode]) -> None:
        """Recursively build node map."""
        if node.node_id is not None:
            node_map[node.node_id] = node

        for child in node.children:
            self._build_node_map_recursive(child, node_map)

    def create_from_dict(self, data: Dict[str, Any], parent: Optional[DARSNode] = None) -> DARSNode:
        """
        Reconstruct node tree from dictionary.

        Args:
            data: Dictionary representation of node
            parent: Parent node for reconstruction

        Returns:
            Reconstructed node with all children
        """
        # Extract children before creating node
        children_data = data.pop('children', [])

        # Create the node
        node = DARSNode(
            role=data.get('role', ''),
            content=data.get('content', ''),
            agent=data.get('agent', ''),
            thought=data.get('thought'),
            action=data.get('action'),
            parent=parent,
            is_demo=data.get('is_demo', False),
            is_terminal=data.get('is_terminal', False),
            _depth=data.get('_depth')
        )

        # Set metadata
        node.node_id = data.get('node_id')
        node.expansion_history = data.get('expansion_history', [])
        node._action_expansion_limit = data.get('_action_expansion_limit', {})
        node.codegraph_keyword = data.get('codegraph_keyword')
        node.codegraph_context = data.get('codegraph_context')
        node.expansion_prompt = data.get('expansion_prompt', '')
        node.critic_prompt = data.get('critic_prompt', '')
        node.critic_response = data.get('critic_response', '')
        node.expansion_candidates = data.get('expansion_candidates', [])

        # Recursively create children
        for child_data in children_data:
            child_node = self.create_from_dict(child_data, parent=node)
            node.children.append(child_node)

        return node

    def get_path_to_node(self, target_node: DARSNode) -> List[DARSNode]:
        """
        Get path from root to target node.

        Args:
            target_node: Target node

        Returns:
            List of nodes from root to target
        """
        path = []
        current = target_node

        while current is not None:
            path.append(current)
            current = current.parent

        path.reverse()
        return path

    def get_leftmost_path(self, root: Optional[DARSNode] = None) -> List[DARSNode]:
        """
        Get leftmost path from root to leaf.

        Args:
            root: Starting node (uses internal root if None)

        Returns:
            List of nodes in leftmost path
        """
        if root is None:
            root = self._root_node

        if root is None:
            return []

        path = []
        current = root

        while current:
            if current.action:  # Only include nodes with actions
                path.append(current)
            current = current.children[0] if current.children else None

        return path
