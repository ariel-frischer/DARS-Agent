"""Environment installation abstraction for SWE-agent.

This module provides environment setup and package installation functionality
extracted from SWEEnv to follow the Single Responsibility and Open/Closed Principles.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from swebench.harness.utils import get_environment_yml, get_requirements

from sweagent.environment.utils import copy_file_to_container
from sweagent.utils.log import get_logger


PATH_TO_REQS = "/root/requirements.txt"
PATH_TO_ENV_YML = "/root/environment.yml"
LONG_TIMEOUT = 500


@dataclass
class InstallConfig:
    """Configuration for environment installation."""

    python: str
    packages: str = ""  # 'requirements.txt', 'environment.yml', or package list
    pip_packages: list[str] | None = None
    pre_install: list[str] | None = None
    install: str | None = None
    post_install: list[str] | None = None
    no_use_env: bool = False
    shell_script_path: str | None = None


class IInstallationStrategy(ABC):
    """Abstract strategy for different installation methods (Open/Closed Principle).

    This allows adding new installation methods without modifying existing code.
    """

    @abstractmethod
    def install(
        self,
        env_name: str,
        config: InstallConfig,
        command_executor: ICommandExecutor,
    ) -> None:
        """Install environment using this strategy.

        Args:
            env_name: Name of the conda environment
            config: Installation configuration
            command_executor: Executor for running commands
        """
        pass


class ICommandExecutor(ABC):
    """Abstract interface for executing commands."""

    @abstractmethod
    def execute(self, command: str, error_msg: str, timeout_duration: float | None = None) -> str:
        """Execute a command."""
        pass

    @abstractmethod
    def execute_simple(self, command: str) -> str:
        """Execute a simple command without error handling."""
        pass


class RequirementsTxtInstallation(IInstallationStrategy):
    """Installation strategy for requirements.txt-based environments."""

    def __init__(self, container_obj: Any, record: dict[str, Any], logger: logging.Logger):
        self.container_obj = container_obj
        self.record = record
        self.logger = logger

    def install(
        self,
        env_name: str,
        config: InstallConfig,
        command_executor: ICommandExecutor,
    ) -> None:
        """Install environment from requirements.txt."""
        self.logger.info(f"Installing environment {env_name} from requirements.txt")

        # Create conda environment
        command_executor.execute(
            f"conda create -n {env_name} python={config.python} -y",
            error_msg="Failed to create conda environment",
            timeout_duration=LONG_TIMEOUT,
        )
        self.logger.debug("Created conda environment")

        # Copy requirements.txt to container
        content_reqs = get_requirements(self.record)
        copy_file_to_container(self.container_obj, content_reqs, PATH_TO_REQS)

        # Activate environment and install requirements
        command_executor.execute(
            f"conda activate {env_name}",
            error_msg="Failed to activate conda environment",
        )
        command_executor.execute(
            f"pip install -r {PATH_TO_REQS}",
            error_msg="Failed to install requirements.txt",
            timeout_duration=LONG_TIMEOUT,
        )
        self.logger.debug("Installed requirements from requirements.txt")

        # Cleanup
        command_executor.execute_simple(f"rm {PATH_TO_REQS}")


class EnvironmentYmlInstallation(IInstallationStrategy):
    """Installation strategy for environment.yml-based environments."""

    def __init__(self, container_obj: Any, record: dict[str, Any], logger: logging.Logger):
        self.container_obj = container_obj
        self.record = record
        self.logger = logger

    def install(
        self,
        env_name: str,
        config: InstallConfig,
        command_executor: ICommandExecutor,
    ) -> None:
        """Install environment from environment.yml."""
        self.logger.info(f"Installing environment {env_name} from environment.yml")

        # Prepare environment.yml content
        content_env_yml = get_environment_yml(self.record, env_name)
        if not config.no_use_env:
            content_env_yml += f'\n  - python={config.python}\n'

        copy_file_to_container(self.container_obj, content_env_yml, PATH_TO_ENV_YML)

        if config.no_use_env:
            # Create environment first, then update
            command_executor.execute(
                f"conda create -c conda-forge -n {env_name} python={config.python} -y",
                error_msg="Failed to create conda environment",
                timeout_duration=LONG_TIMEOUT,
            )
            self.logger.debug("Created conda environment")

            command_executor.execute(
                f"conda env update -f {PATH_TO_ENV_YML}",
                error_msg="Failed to install environment.yml",
                timeout_duration=LONG_TIMEOUT,
            )
            self.logger.debug("Installed packages from environment.yml")
        else:
            # Create environment and install packages in one step
            command_executor.execute(
                f"conda env create --file {PATH_TO_ENV_YML}",
                error_msg="Failed to create conda environment with environment.yml",
                timeout_duration=LONG_TIMEOUT,
            )
            self.logger.debug("Created conda environment with environment.yml")

        # Cleanup
        command_executor.execute_simple(f"rm {PATH_TO_ENV_YML}")


class CondaPackagesInstallation(IInstallationStrategy):
    """Installation strategy for direct conda package installation."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def install(
        self,
        env_name: str,
        config: InstallConfig,
        command_executor: ICommandExecutor,
    ) -> None:
        """Install environment from conda packages."""
        self.logger.info(f"Installing environment {env_name} with conda packages")

        # Try to clone existing python environment
        python_env = f"python{config.python}"
        env_exists = self._check_environment_exists(python_env, command_executor)

        if env_exists:
            command_executor.execute(
                f"conda create --name {env_name} --clone {python_env}",
                error_msg="Failed to clone conda environment",
                timeout_duration=LONG_TIMEOUT,
            )
            self.logger.debug("Cloned python conda environment")
        else:
            self.logger.debug(f"Could not find {python_env}, creating new environment")
            command_executor.execute(
                f"conda create -n {env_name} python={config.python} -y",
                error_msg="Failed to create conda environment",
                timeout_duration=LONG_TIMEOUT,
            )

        # Activate environment
        command_executor.execute(
            f"conda activate {env_name}",
            error_msg="Failed to activate conda environment",
        )

        # Install packages if specified
        if config.packages.strip():
            command_executor.execute(
                f"conda install {config.packages} -y",
                error_msg="Failed to install packages",
                timeout_duration=LONG_TIMEOUT,
            )
            self.logger.debug("Installed conda packages")

    def _check_environment_exists(
        self,
        env_name: str,
        command_executor: ICommandExecutor,
    ) -> bool:
        """Check if conda environment exists."""
        try:
            output = command_executor.execute_simple(f"conda env list | grep {env_name}")
            return bool(output and env_name in output)
        except Exception:
            return False


class EnvironmentInstaller:
    """Manages environment installation operations (Single Responsibility + Open/Closed Principles).

    This class uses the Strategy pattern to support different installation methods,
    making it easy to add new methods without modifying existing code.
    """

    def __init__(
        self,
        command_executor: ICommandExecutor,
        container_obj: Any = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize EnvironmentInstaller.

        Args:
            command_executor: Implementation of ICommandExecutor for running commands
            container_obj: Container object for file operations
            logger: Logger instance (defaults to module logger)
        """
        self.command_executor = command_executor
        self.container_obj = container_obj
        self.logger = logger or get_logger("EnvironmentInstaller")
        self._strategies: dict[str, IInstallationStrategy] = {}

    def register_strategy(self, package_type: str, strategy: IInstallationStrategy) -> None:
        """Register an installation strategy (Open/Closed Principle).

        Args:
            package_type: Type identifier (e.g., 'requirements.txt', 'environment.yml')
            strategy: Installation strategy implementation
        """
        self._strategies[package_type] = strategy

    def install_environment(
        self,
        env_name: str,
        config: InstallConfig,
        record: dict[str, Any] | None = None,
    ) -> None:
        """Install environment based on configuration.

        Args:
            env_name: Name of the conda environment to create
            config: Installation configuration
            record: Optional record with metadata

        Raises:
            ValueError: If installation type is not supported
        """
        # Handle shell script installation
        if config.shell_script_path:
            self._run_shell_script(Path(config.shell_script_path))
            return

        # Check if environment already exists
        if self._conda_environment_exists(env_name):
            self.logger.info(f"Environment {env_name} already exists")
        else:
            self.logger.info(f"Creating environment {env_name}...")
            self._create_environment(env_name, config, record)

        # Activate environment
        self.command_executor.execute(
            f"conda activate {env_name}",
            error_msg="Failed to activate conda environment",
        )

        # Run installation lifecycle hooks
        self._run_installation_lifecycle(config)

    def _create_environment(
        self,
        env_name: str,
        config: InstallConfig,
        record: dict[str, Any] | None,
    ) -> None:
        """Create the conda environment using appropriate strategy."""
        # Auto-register strategies if not already registered
        if not self._strategies and record:
            self._register_default_strategies(record)

        strategy = self._get_strategy(config.packages)
        strategy.install(env_name, config, self.command_executor)

        # Install extra pip packages if specified
        if config.pip_packages:
            self.command_executor.execute(
                f"source activate {env_name} && pip install {' '.join(config.pip_packages)}",
                error_msg="Failed to install pip packages",
                timeout_duration=LONG_TIMEOUT,
            )
            self.logger.debug("Installed extra pip dependencies")

    def _get_strategy(self, package_type: str) -> IInstallationStrategy:
        """Get the appropriate installation strategy.

        Args:
            package_type: Type of package installation

        Returns:
            Installation strategy

        Raises:
            ValueError: If no strategy found for package type
        """
        if package_type in self._strategies:
            return self._strategies[package_type]

        # Default strategy for direct package names
        if package_type not in ["requirements.txt", "environment.yml"]:
            if "conda_packages" in self._strategies:
                return self._strategies["conda_packages"]

        raise ValueError(f"No installation strategy found for: {package_type}")

    def _register_default_strategies(self, record: dict[str, Any]) -> None:
        """Register default installation strategies."""
        self.register_strategy(
            "requirements.txt",
            RequirementsTxtInstallation(self.container_obj, record, self.logger),
        )
        self.register_strategy(
            "environment.yml",
            EnvironmentYmlInstallation(self.container_obj, record, self.logger),
        )
        self.register_strategy(
            "conda_packages",
            CondaPackagesInstallation(self.logger),
        )

    def _run_installation_lifecycle(self, config: InstallConfig) -> None:
        """Run pre-install, install, and post-install commands."""
        if config.pre_install:
            self.logger.info("Running pre-install commands...")
            for cmd in config.pre_install:
                self.command_executor.execute(
                    cmd,
                    error_msg="Pre-install command failed",
                    timeout_duration=LONG_TIMEOUT,
                )
            self.logger.debug("Ran pre-install commands")

        if config.install:
            self.logger.info("Running install command...")
            self.command_executor.execute(
                config.install,
                error_msg="Install command failed",
                timeout_duration=LONG_TIMEOUT,
            )
            self.logger.debug("Ran install command")

        if config.post_install:
            self.logger.info("Running post-install commands...")
            for cmd in config.post_install:
                self.command_executor.execute(
                    cmd,
                    error_msg="Post-install command failed",
                )
            self.logger.debug("Ran post-install commands")

    def _conda_environment_exists(self, env_name: str) -> bool:
        """Check if a conda environment exists."""
        try:
            output = self.command_executor.execute_simple("conda env list")
            return env_name in output
        except Exception:
            return False

    def _run_shell_script(self, script_path: Path) -> None:
        """Run a shell script for environment setup."""
        self.logger.info(f"Running shell script: {script_path}")
        # This would need implementation based on how scripts are executed
        raise NotImplementedError("Shell script execution not yet implemented")
