"""
Trajectory building and management following Single Responsibility Principle.

This module only handles trajectory creation, storage, and serialization.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from sweagent.agent.interfaces import ITrajectoryBuilder


class TrajectoryStep(Dict[str, Any]):
    """Represents a single step in the agent's trajectory."""

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize trajectory step.

        Args:
            data: Step data dictionary
        """
        super().__init__(data)
        # Ensure required keys exist
        self.setdefault('action', '')
        self.setdefault('observation', '')
        self.setdefault('response', '')
        self.setdefault('state', None)
        self.setdefault('thought', '')


class TrajectoryBuilder(ITrajectoryBuilder):
    """
    Builds and manages agent trajectories.

    Single Responsibility: Only handles trajectory construction and persistence.
    """

    def __init__(self):
        """Initialize trajectory builder."""
        self._steps: List[TrajectoryStep] = []

    def add_step(
        self,
        action: str,
        observation: str,
        thought: str,
        response: str = "",
        state: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Add a step to the trajectory.

        Args:
            action: Action taken
            observation: Observation received
            thought: Agent's reasoning
            response: Raw model response
            state: Environment state
            **kwargs: Additional metadata
        """
        step_data = {
            "action": action,
            "observation": observation,
            "thought": thought,
            "response": response,
            "state": state,
            **kwargs
        }
        step = TrajectoryStep(step_data)
        self._steps.append(step)

    def get_trajectory(self) -> List[TrajectoryStep]:
        """
        Get complete trajectory.

        Returns:
            List of trajectory steps
        """
        return self._steps.copy()

    def save(
        self,
        path: str,
        env_name: str = "",
        history: Optional[List[Dict]] = None,
        info: Optional[Dict[str, Any]] = None,
        **metadata
    ) -> None:
        """
        Save trajectory to file.

        Args:
            path: File path to save to
            env_name: Environment name
            history: Conversation history
            info: Additional info (e.g., model stats)
            **metadata: Additional metadata to save
        """
        log_dict = {
            "environment": env_name,
            "trajectory": [dict(step) for step in self._steps],
            "history": history or [],
            "info": info or {},
            **metadata
        }

        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        path_obj.write_text(json.dumps(log_dict, indent=2))

    def clear(self) -> None:
        """Clear all trajectory steps."""
        self._steps.clear()

    def get_last_step(self) -> Optional[TrajectoryStep]:
        """Get the last trajectory step."""
        return self._steps[-1] if self._steps else None

    def get_step_count(self) -> int:
        """Get number of steps in trajectory."""
        return len(self._steps)

    def load_from_file(self, path: str) -> Dict[str, Any]:
        """
        Load trajectory from file.

        Args:
            path: Path to trajectory file

        Returns:
            Dictionary containing trajectory and metadata
        """
        path_obj = Path(path)
        data = json.loads(path_obj.read_text())

        # Reconstruct trajectory steps
        self._steps = [TrajectoryStep(step) for step in data.get('trajectory', [])]

        return data

    def extend_from_checkpoint(self, checkpoint_data: Dict[str, Any]) -> None:
        """
        Extend trajectory from checkpoint data.

        Args:
            checkpoint_data: Checkpoint containing trajectory steps
        """
        for step_data in checkpoint_data.get('trajectory', []):
            self._steps.append(TrajectoryStep(step_data))


class TreeTrajectoryBuilder(ITrajectoryBuilder):
    """
    Builds trajectory from tree-based node structure.

    Used for DARS agents with tree exploration.
    """

    def __init__(self, node_manager):
        """
        Initialize tree trajectory builder.

        Args:
            node_manager: Node manager to extract trajectory from
        """
        self.node_manager = node_manager

    def add_step(self, action: str, observation: str, thought: str, **kwargs) -> None:
        """
        Not used in tree-based trajectory.

        Trajectory is built from node tree.
        """
        raise NotImplementedError("Tree trajectory is built from nodes")

    def get_trajectory(self) -> List[TrajectoryStep]:
        """
        Extract trajectory from leftmost path in tree.

        Returns:
            List of trajectory steps
        """
        path_nodes = self.node_manager.get_leftmost_path()
        trajectory = []

        for node in path_nodes:
            if node.action:  # Only include nodes with actions
                step = TrajectoryStep({
                    "action": node.action,
                    "observation": node.children[0].content if node.children else "",
                    "response": node.content,
                    "state": None,
                    "thought": node.thought or "",
                })
                trajectory.append(step)

        return trajectory

    def save(self, path: str, **metadata) -> None:
        """
        Save trajectory extracted from tree.

        Args:
            path: File path
            **metadata: Additional metadata
        """
        trajectory = self.get_trajectory()

        log_dict = {
            "environment": metadata.get("env_name", ""),
            "trajectory": [dict(step) for step in trajectory],
            "history": metadata.get("history", []),
            "info": metadata.get("info", {}),
        }

        # Add any additional metadata
        for key, value in metadata.items():
            if key not in log_dict:
                log_dict[key] = value

        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        path_obj.write_text(json.dumps(log_dict, indent=2))

    def clear(self) -> None:
        """Clear by resetting node manager."""
        # Node manager handles its own state
        pass

    def get_trajectory_from_node(self, target_node) -> List[TrajectoryStep]:
        """
        Get trajectory from root to specific node.

        Args:
            target_node: Target node to build trajectory to

        Returns:
            List of trajectory steps
        """
        path = self.node_manager.get_path_to_node(target_node)
        trajectory = []

        for node in path:
            if node.action:
                step = TrajectoryStep({
                    "action": node.action,
                    "observation": node.children[0].content if node.children else "",
                    "response": node.content,
                    "state": None,
                    "thought": node.thought or "",
                })
                trajectory.append(step)

        return trajectory


class TrajectoryCheckpoint:
    """
    Handles trajectory checkpointing and recovery.

    Separate class following SRP.
    """

    def __init__(self, checkpoint_dir: Path):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory for checkpoints
        """
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        instance_id: str,
        root_dict: Dict[str, Any],
        iterations: int,
        node_count: int,
        current_node_id: int,
        node_stack: List[int]
    ) -> None:
        """
        Save a checkpoint.

        Args:
            instance_id: Instance identifier
            root_dict: Serialized root node
            iterations: Remaining iterations
            node_count: Total node count
            current_node_id: Current node ID
            node_stack: Stack of node IDs
        """
        checkpoint = {
            "root": root_dict,
            "iterations": iterations,
            "node_count": node_count,
            "current_node_id": current_node_id,
            "node_id_stack": node_stack
        }

        # Write to temporary file first
        tmp_path = self.checkpoint_dir / f"{instance_id}.cur.tmp"
        with open(tmp_path, "w") as f:
            json.dump(checkpoint, f, indent=2)

        # Atomic replace
        cur_path = self.checkpoint_dir / f"{instance_id}.cur.root"
        prev_path = self.checkpoint_dir / f"{instance_id}.prev.root"

        tmp_path.replace(cur_path)

        # Keep previous checkpoint as backup
        if cur_path.exists():
            import shutil
            shutil.copy2(cur_path, prev_path)

    def load_checkpoint(self, path: str) -> Dict[str, Any]:
        """
        Load checkpoint from file.

        Args:
            path: Path to checkpoint

        Returns:
            Checkpoint data
        """
        with open(path, 'r') as f:
            return json.load(f)

    def get_latest_checkpoint(self, instance_id: str) -> Optional[Path]:
        """
        Get path to latest checkpoint for instance.

        Args:
            instance_id: Instance identifier

        Returns:
            Path to checkpoint or None
        """
        cur_path = self.checkpoint_dir / f"{instance_id}.cur.root"
        if cur_path.exists():
            return cur_path

        prev_path = self.checkpoint_dir / f"{instance_id}.prev.root"
        if prev_path.exists():
            return prev_path

        return None
