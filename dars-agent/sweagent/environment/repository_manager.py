"""Repository management abstraction for SWE-agent.

This module provides repository cloning and management functionality extracted from SWEEnv
to follow the Single Responsibility Principle.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from sweagent.environment.utils import copy_anything_to_container
from sweagent.utils.config import keys_config
from sweagent.utils.log import get_logger


@dataclass
class RepositoryConfig:
    """Configuration for repository operations."""

    repo_path: str
    repo_type: str  # 'local' or 'github'
    repo_name: str
    base_commit: str | None = None
    github_token: str | None = None
    use_mirror: bool = True
    problem_statement_source: str | None = None
    clone_method: str = "shallow"  # 'shallow' or 'full'


class ICommandExecutor(ABC):
    """Abstract interface for executing commands in the environment.

    This allows the RepositoryManager to be decoupled from the specific
    execution environment (container, local, etc.).
    """

    @abstractmethod
    def execute(self, command: str, error_msg: str, timeout_duration: float | None = None) -> str:
        """Execute a command.

        Args:
            command: Command to execute
            error_msg: Error message if command fails
            timeout_duration: Optional timeout in seconds

        Returns:
            Command output

        Raises:
            RuntimeError: If command fails
        """
        pass


class RepositoryManager:
    """Manages repository cloning and setup operations (Single Responsibility Principle).

    This class extracts repository-related responsibilities from SWEEnv,
    making the code more maintainable and testable.
    """

    def __init__(
        self,
        command_executor: ICommandExecutor,
        container_obj: any = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize RepositoryManager.

        Args:
            command_executor: Implementation of ICommandExecutor for running commands
            container_obj: Container object for file operations
            logger: Logger instance (defaults to module logger)
        """
        self.command_executor = command_executor
        self.container_obj = container_obj
        self.logger = logger or get_logger("RepositoryManager")

    def clone_repository(
        self,
        config: RepositoryConfig,
        data_length: int = 1,
        persistent: bool = False,
    ) -> str:
        """Clone or copy repository to the environment.

        Args:
            config: Repository configuration
            data_length: Number of data instances (affects clone method)
            persistent: Whether using persistent container

        Returns:
            Name of the cloned repository folder

        Raises:
            RuntimeError: If cloning fails
        """
        if config.repo_type == "local":
            return self._copy_local_repo(config)
        elif config.repo_type == "github":
            return self._clone_github_repo(config, data_length, persistent)
        else:
            raise ValueError(f"Unknown repository type: {config.repo_type}")

    def _copy_local_repo(self, config: RepositoryConfig) -> str:
        """Copy a local repository to the container.

        Args:
            config: Repository configuration

        Returns:
            Repository name
        """
        if self.container_obj is None:
            raise RuntimeError("Container object not set")

        self.logger.info(f"Copying local repository to /{config.repo_name}")

        local_path = config.repo_path.removeprefix("local://")
        copy_anything_to_container(
            self.container_obj,
            local_path,
            "/" + config.repo_name,
        )

        # Fix permissions
        self.command_executor.execute(
            command=f"chown -R root:root {config.repo_name}",
            error_msg="Failed to change permissions on copied repository",
        )

        return config.repo_name

    def _clone_github_repo(
        self,
        config: RepositoryConfig,
        data_length: int,
        persistent: bool,
    ) -> str:
        """Clone a GitHub repository.

        Args:
            config: Repository configuration
            data_length: Number of data instances
            persistent: Whether using persistent container

        Returns:
            Repository name
        """
        clone_url = self._build_clone_url(config)
        clone_method = self._determine_clone_method(config, data_length, persistent)

        if clone_method == "full":
            self._clone_full(config.repo_name, clone_url)
        else:
            self._clone_shallow(config.repo_name, clone_url, config.base_commit)

        return config.repo_name

    def _build_clone_url(self, config: RepositoryConfig) -> str:
        """Build the clone URL with optional authentication token.

        Args:
            config: Repository configuration

        Returns:
            Clone URL
        """
        token_prefix = ""
        if config.github_token:
            token_prefix = f"{config.github_token}@"

        # Use mirror for SWE-bench unless disabled
        if not config.use_mirror and config.problem_statement_source == "swe-bench":
            self.logger.info(f"Cloning {config.repo_name} from swe-bench mirror...")
            return f"https://{token_prefix}github.com/swe-bench/{config.repo_name}.git"
        else:
            self.logger.info(f"Cloning {config.repo_name} from original repository...")
            return f"https://{token_prefix}github.com/{config.repo_path}.git"

    def _determine_clone_method(
        self,
        config: RepositoryConfig,
        data_length: int,
        persistent: bool,
    ) -> str:
        """Determine which clone method to use.

        Args:
            config: Repository configuration
            data_length: Number of data instances
            persistent: Whether using persistent container

        Returns:
            Clone method: 'shallow' or 'full'
        """
        clone_method = config.clone_method

        # Force full clone for multiple instances or persistent containers
        if data_length > 1 or persistent:
            self.logger.debug(
                "Using full clone method due to multiple instances or persistent container"
            )
            clone_method = "full"

        return clone_method

    def _clone_full(self, repo_name: str, clone_url: str, timeout: float = 500) -> None:
        """Perform a full git clone.

        Args:
            repo_name: Name for the repository folder
            clone_url: URL to clone from
            timeout: Timeout duration in seconds
        """
        self.logger.info(f"Performing full clone of {repo_name}")
        self.command_executor.execute(
            command=f"git clone {clone_url} {repo_name}",
            error_msg="Failed to clone repository (full method)",
            timeout_duration=timeout,
        )

    def _clone_shallow(
        self,
        repo_name: str,
        clone_url: str,
        base_commit: str | None,
        timeout: float = 500,
    ) -> None:
        """Perform a shallow git clone (depth=1).

        Args:
            repo_name: Name for the repository folder
            clone_url: URL to clone from
            base_commit: Specific commit to checkout
            timeout: Timeout duration in seconds
        """
        if not base_commit:
            raise ValueError("base_commit is required for shallow cloning")

        self.logger.info(f"Performing shallow clone of {repo_name} at {base_commit}")

        commands = [
            f"mkdir {repo_name}",
            f"cd {repo_name}",
            "git init",
            f"git remote add origin {clone_url}",
            f"git fetch --depth 1 origin {base_commit}",
            "git checkout FETCH_HEAD",
            "cd ..",
        ]

        self.command_executor.execute(
            command="&&".join(commands),
            error_msg="Failed to clone repository (shallow method)",
            timeout_duration=timeout,
        )

    def checkout_commit(self, repo_name: str, commit: str) -> None:
        """Checkout a specific commit.

        Args:
            repo_name: Repository folder name
            commit: Commit hash to checkout
        """
        self.logger.info(f"Checking out commit {commit} in {repo_name}")
        self.command_executor.execute(
            command=f"cd {repo_name} && git checkout {commit}",
            error_msg=f"Failed to checkout commit {commit}",
        )

    def reset_repository(self, repo_name: str) -> None:
        """Reset repository to clean state.

        Args:
            repo_name: Repository folder name
        """
        self.logger.info(f"Resetting repository {repo_name}")
        commands = [
            f"cd {repo_name}",
            "git reset --hard",
            "git clean -fdx",
        ]
        self.command_executor.execute(
            command=" && ".join(commands),
            error_msg=f"Failed to reset repository {repo_name}",
        )
