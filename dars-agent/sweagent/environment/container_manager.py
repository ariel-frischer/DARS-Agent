"""Container management abstraction for SWEEnv."""
from __future__ import annotations
import hashlib
import datetime
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple
import docker
import docker.errors
import docker.models.containers
import subprocess
from sweagent.utils.log import get_logger


class IContainerManager(ABC):
    """Interface for container lifecycle management."""

    @abstractmethod
    def create_container(self, image_name: str, container_name: str) -> Tuple[Any, list]:
        """Create and initialize a container."""
        pass

    @abstractmethod
    def get_container_object(self, container_name: str) -> docker.models.containers.Container:
        """Get the docker container object."""
        pass

    @abstractmethod
    def remove_container(self, container_obj: docker.models.containers.Container) -> None:
        """Remove a container."""
        pass

    @abstractmethod
    def pause_container(self, container_obj: docker.models.containers.Container) -> None:
        """Pause a container."""
        pass


class DockerContainerManager(IContainerManager):
    """Docker-based container manager implementation."""

    def __init__(self, persistent: bool = False, volume_mount: Optional[str] = None, logger=None):
        self.persistent = persistent
        self.volume_mount = volume_mount
        self.logger = logger or get_logger("container_manager")
        self._client: Optional[docker.DockerClient] = None

    @property
    def client(self) -> docker.DockerClient:
        """Lazy initialization of docker client."""
        if self._client is None:
            try:
                self._client = docker.from_env(timeout=600)
            except docker.errors.DockerException as e:
                if "Error while fetching server API version" in str(e):
                    msg = "Docker is not running. Please start Docker and try again."
                else:
                    msg = "Unknown docker exception occurred. Are you sure docker is running?"
                raise RuntimeError(msg) from e
        return self._client

    def create_container(self, image_name: str, container_name: str) -> Tuple[Any, list]:
        """Create and initialize a container."""
        from sweagent.environment.utils import get_container
        return get_container(container_name, image_name, persistent=self.persistent, volume_mount=self.volume_mount)

    def get_container_object(self, container_name: str) -> docker.models.containers.Container:
        """Get the docker container object."""
        t0 = time.time()
        container_obj = None

        while time.time() - t0 < 60:
            try:
                container_obj = self.client.containers.get(container_name)
                break
            except docker.errors.NotFound:
                self.logger.debug("Couldn't find container. Let's wait and retry.")
                time.sleep(1)

        if container_obj is None:
            available_containers = self.client.containers.list(all=True)
            import json
            available_containers_info = json.dumps([str(c.attrs) for c in available_containers], indent=2)
            self.logger.error(f"Available containers: {available_containers_info}")
            raise RuntimeError("Failed to get container object.")

        return container_obj

    def remove_container(self, container_obj: docker.models.containers.Container) -> None:
        """Remove a container."""
        try:
            container_obj.remove(force=True)
            self.logger.info("Agent container stopped")
        except docker.errors.NotFound:
            # Container already removed
            pass
        except Exception:
            self.logger.warning("Failed to remove container", exc_info=True)

    def pause_container(self, container_obj: docker.models.containers.Container) -> None:
        """Pause a container."""
        try:
            # Refresh container status
            container_obj.reload()
            if container_obj.status not in {"paused", "exited", "dead", "stopping"}:
                container_obj.pause()
                self.logger.info("Agent container paused")
            else:
                self.logger.info(f"Agent container status: {container_obj.status}")
        except Exception:
            self.logger.warning("Failed to pause container.", exc_info=True)

    @staticmethod
    def generate_container_name(image_name: str) -> str:
        """Generate a unique container name."""
        process_id = str(os.getpid())
        current_time = str(datetime.datetime.now())
        unique_string = current_time + process_id
        hash_object = hashlib.sha256(unique_string.encode())
        image_name_sanitized = image_name.replace("/", "-").replace(":", "-")
        return f"{image_name_sanitized}-{hash_object.hexdigest()[:10]}"
