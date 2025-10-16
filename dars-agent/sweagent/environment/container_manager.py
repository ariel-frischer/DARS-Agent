"""Container management abstraction for SWE-agent.

This module provides container management functionality extracted from SWEEnv
to follow the Single Responsibility Principle and Dependency Inversion Principle.
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import docker
import docker.errors
import docker.models.containers

from sweagent.environment.utils import get_container
from sweagent.utils.log import get_logger


class IContainerClient(ABC):
    """Abstract interface for container client operations (Dependency Inversion Principle).

    This abstraction allows different container backends (Docker, Podman, etc.)
    to be used without modifying the core logic.
    """

    @abstractmethod
    def get_container(self, container_name: str) -> Any:
        """Get a container by name.

        Args:
            container_name: Name of the container to retrieve

        Returns:
            Container object

        Raises:
            ContainerNotFoundError: If container doesn't exist
        """
        pass

    @abstractmethod
    def list_containers(self, all: bool = False) -> list[Any]:
        """List available containers.

        Args:
            all: If True, include stopped containers

        Returns:
            List of container objects
        """
        pass


class DockerClient(IContainerClient):
    """Docker implementation of IContainerClient."""

    def __init__(self, timeout: int = 600):
        """Initialize Docker client.

        Args:
            timeout: Connection timeout in seconds

        Raises:
            RuntimeError: If Docker is not running or cannot connect
        """
        try:
            self.client = docker.from_env(timeout=timeout)
        except docker.errors.DockerException as e:
            if "Error while fetching server API version" in str(e):
                msg = "Docker is not running. Please start Docker and try again."
            else:
                msg = "Unknown docker exception occurred. Are you sure docker is running?"
            raise RuntimeError(msg) from e

    def get_container(self, container_name: str) -> docker.models.containers.Container:
        """Get a container by name."""
        try:
            return self.client.containers.get(container_name)
        except docker.errors.NotFound as e:
            raise ContainerNotFoundError(f"Container '{container_name}' not found") from e

    def list_containers(self, all: bool = False) -> list[docker.models.containers.Container]:
        """List available containers."""
        return self.client.containers.list(all=all)


class ContainerNotFoundError(Exception):
    """Raised when a container cannot be found."""
    pass


class ContainerManager:
    """Manages container lifecycle and operations (Single Responsibility Principle).

    This class extracts container-related responsibilities from SWEEnv,
    making the code more maintainable and testable.
    """

    def __init__(
        self,
        container_client: IContainerClient | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize ContainerManager.

        Args:
            container_client: Container client implementation (defaults to DockerClient)
            logger: Logger instance (defaults to module logger)
        """
        self.client = container_client or DockerClient()
        self.logger = logger or get_logger("ContainerManager")
        self.container_obj: Any | None = None
        self.container: Any | None = None
        self.parent_pids: list[int] = []

    def initialize_container(
        self,
        container_name: str,
        image_name: str,
        persistent: bool = False,
        volume_mount: str | None = None,
        retry_timeout: int = 60,
    ) -> tuple[Any, list[int]]:
        """Initialize and retrieve container.

        Args:
            container_name: Name for the container
            image_name: Docker image to use
            persistent: Whether to use persistent container
            volume_mount: Optional volume mount string
            retry_timeout: How long to wait for container to be available (seconds)

        Returns:
            Tuple of (container handle, parent PIDs)

        Raises:
            RuntimeError: If container cannot be initialized
        """
        self.logger.info(f"Initializing container '{container_name}' with image '{image_name}'")

        # Create the container
        self.container, self.parent_pids = get_container(
            container_name,
            image_name,
            persistent=persistent,
            volume_mount=volume_mount,
        )

        # Wait for container to be available
        t0 = time.time()
        self.container_obj = None

        while time.time() - t0 < retry_timeout:
            try:
                self.container_obj = self.client.get_container(container_name)
                self.logger.info(f"✓ Container '{container_name}' initialized successfully")
                break
            except ContainerNotFoundError:
                self.logger.debug("Container not found yet. Waiting...")
                time.sleep(1)
        else:
            # Timeout reached - provide debugging information
            self._log_container_initialization_failure(persistent)
            raise RuntimeError(f"Failed to initialize container '{container_name}' within {retry_timeout}s")

        return self.container, self.parent_pids

    def _log_container_initialization_failure(self, persistent: bool) -> None:
        """Log detailed information when container initialization fails."""
        self.logger.error(f"Container initialization failed. Persistent mode: {persistent}")
        try:
            available_containers = self.client.list_containers(all=True)
            containers_info = json.dumps(
                [str(c.attrs) for c in available_containers],
                indent=2,
            )
            self.logger.error(f"Available containers:\n{containers_info}")
        except Exception as e:
            self.logger.error(f"Could not list available containers: {e}")

    def get_container_object(self) -> Any:
        """Get the container object.

        Returns:
            Container object

        Raises:
            RuntimeError: If container hasn't been initialized
        """
        if self.container_obj is None:
            raise RuntimeError("Container not initialized. Call initialize_container() first.")
        return self.container_obj

    def is_initialized(self) -> bool:
        """Check if container is initialized.

        Returns:
            True if container is ready, False otherwise
        """
        return self.container_obj is not None
