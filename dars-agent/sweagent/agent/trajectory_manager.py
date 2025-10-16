"""Trajectory management abstraction - Single Responsibility Principle."""
from __future__ import annotations
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class ITrajectoryManager(ABC):
    """Abstract interface for trajectory management - Dependency Inversion Principle."""

    @abstractmethod
    def save_trajectory(
        self,
        trajectory: List[Dict[str, Any]],
        log_path: Path,
        env_name: str,
        info: Dict[str, Any],
        history: List[Dict[str, Any]] = None,
    ) -> None:
        """Save trajectory to file."""
        pass

    @abstractmethod
    def load_trajectory(self, log_path: Path) -> Dict[str, Any]:
        """Load trajectory from file."""
        pass


class JSONTrajectoryManager(ITrajectoryManager):
    """JSON-based implementation of trajectory management."""

    def save_trajectory(
        self,
        trajectory: List[Dict[str, Any]],
        log_path: Path,
        env_name: str,
        info: Dict[str, Any],
        history: List[Dict[str, Any]] = None,
    ) -> None:
        """Save trajectory as JSON."""
        log_dict = {
            "environment": env_name,
            "trajectory": trajectory,
            "info": info,
        }

        if history is not None:
            log_dict["history"] = history

        log_path.write_text(json.dumps(log_dict, indent=2))

    def load_trajectory(self, log_path: Path) -> Dict[str, Any]:
        """Load trajectory from JSON file."""
        return json.loads(log_path.read_text())
