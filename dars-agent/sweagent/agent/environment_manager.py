"""Environment management abstraction - Single Responsibility Principle."""
from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class IEnvironmentManager(ABC):
    """Abstract interface for environment management - Dependency Inversion Principle."""

    @abstractmethod
    def initialize_environment(self, env: Any, config: Any) -> None:
        """Initialize environment with configuration."""
        pass

    @abstractmethod
    def set_environment_variables(self, env: Any, variables: Dict[str, Any]) -> None:
        """Set environment variables."""
        pass

    @abstractmethod
    def get_environment_variables(self, env: Any, variable_names: List[str]) -> Dict[str, Any]:
        """Get environment variables."""
        pass

    @abstractmethod
    def add_command_files(self, env: Any, command_files: List[str]) -> None:
        """Add command files to environment."""
        pass


class DefaultEnvironmentManager(IEnvironmentManager):
    """Default implementation of environment management."""

    def __init__(self, logger=None):
        self.logger = logger

    def initialize_environment(self, env: Any, config: Any) -> None:
        """Initialize environment with state command and variables."""
        commands_to_execute = (
            [config.state_command.code] +
            [f"{k}={v}" for k, v in config.env_variables.items()]
        )
        commands = "\n".join(commands_to_execute)

        try:
            output = env.communicate(commands)
            if env.returncode != 0:
                raise RuntimeError(
                    f"Nonzero return code: {env.returncode}\nOutput: {output}"
                )
        except KeyboardInterrupt:
            raise
        except Exception as e:
            if self.logger:
                self.logger.warning("Failed to set environment variables")
            raise e

        self.add_command_files(env, config.command_files)

    def set_environment_variables(self, env: Any, variables: Dict[str, Any]) -> None:
        """Set environment variables in the environment."""
        for key, value in variables.items():
            env.communicate(f"{key}={value}")

    def get_environment_variables(self, env: Any, variable_names: List[str]) -> Dict[str, Any]:
        """Get environment variables from the environment."""
        env_vars = {}
        for var in variable_names:
            env_vars[var] = env.communicate(f"echo ${var}").strip()
        return env_vars

    def add_command_files(self, env: Any, command_files: List[str]) -> None:
        """Add command files to environment."""
        command_file_data = []

        for file in command_files:
            datum = {}
            with open(file) as f:
                contents = f.read()

            datum["contents"] = contents
            filename = Path(file).name

            if not contents.strip().startswith("#!"):
                if filename.endswith(".sh"):
                    datum["name"] = Path(file).name
                    datum["type"] = "source_file"
                elif filename.startswith("_"):
                    datum["name"] = Path(file).name
                    datum["type"] = "utility"
                else:
                    raise ValueError(
                        f"Non-shell script file {file} does not start with shebang.\n"
                        "Either add a shebang (#!) or change the file extension to .sh if you want to source it.\n"
                        "You can override this behavior by adding an underscore to the file name (e.g. _utils.py)."
                    )
            else:
                datum["name"] = Path(file).name.rsplit(".", 1)[0].lstrip('_')
                datum["type"] = "script"

            command_file_data.append(datum)

        env.add_commands(command_file_data)
