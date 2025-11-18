"""Environment installation and setup abstraction."""
from __future__ import annotations
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from swebench.harness.constants import MAP_REPO_VERSION_TO_SPECS
from swebench.harness.utils import get_environment_yml, get_requirements
from sweagent.utils.log import get_logger
from sweagent.environment.utils import copy_file_to_container


LONG_TIMEOUT = 500
PATH_TO_REQS = "/root/requirements.txt"
PATH_TO_ENV_YML = "/root/environment.yml"


class IEnvironmentInstaller(ABC):
    """Interface for environment installation."""

    @abstractmethod
    def install(self, record: Dict[str, Any]) -> None:
        """Install the environment for the given record."""
        pass

    @abstractmethod
    def get_install_config(self, record: Dict[str, Any]) -> Optional[Dict]:
        """Get installation configuration."""
        pass


class CondaEnvironmentInstaller(IEnvironmentInstaller):
    """Conda-based environment installer."""

    def __init__(self, communicate_callback, container_obj, repo_name: str,
                 environment_setup: Optional[str] = None, logger=None):
        self.communicate = communicate_callback
        self.container_obj = container_obj
        self.repo_name = repo_name
        self.environment_setup = environment_setup
        self.logger = logger or get_logger("env_installer")

    def get_install_config(self, record: Dict[str, Any]) -> Optional[Dict]:
        """Get installation configuration."""
        if (
            record["problem_statement_source"] != "swe-bench" or record["repo_type"] == "local"
        ) and self.environment_setup is None:
            self.logger.warning(
                "install_environment is set to True, but no environment config provided. "
                "Skipping conda environment installation."
            )
            return None

        if self.environment_setup is not None:
            if Path(self.environment_setup).suffix in [".yml", ".yaml"]:
                try:
                    return yaml.safe_load(Path(self.environment_setup).read_text())
                except Exception as e:
                    raise ValueError("Environment config file needs to be a yaml file") from e
            elif Path(self.environment_setup).suffix == ".sh":
                return {"shell_script_path": self.environment_setup}
            else:
                raise ValueError("Environment config file needs to be a yaml file or shell script")
        else:
            try:
                return MAP_REPO_VERSION_TO_SPECS[record["repo"]][str(record["version"])]
            except KeyError as e:
                raise ValueError(
                    "Tried to look up install configs in swe-bench, but failed. "
                    "You can set a custom environment config."
                ) from e

    def conda_environment_exists(self, env_name: str) -> bool:
        """Check if conda environment exists."""
        env_check = self.communicate(f"conda env list | grep {env_name}", timeout_duration=LONG_TIMEOUT)
        return env_check.strip() != ""

    def install(self, record: Dict[str, Any]) -> None:
        """Install the environment for the given record."""
        t0 = time.perf_counter()
        install_configs = self.get_install_config(record)

        if not install_configs:
            return

        if "shell_script_path" in install_configs:
            self._install_from_script(Path(install_configs["shell_script_path"]))
            return

        env_name = f"{self.repo_name}__{record['version']}"
        if not self.conda_environment_exists(env_name):
            self._create_conda_environment(env_name, install_configs, record)

        # Activate environment
        self.communicate(f"conda activate {env_name}", error_msg="Failed to activate conda environment")

        # Run pre-install, install, and post-install commands
        self._run_install_commands(install_configs)

        self.logger.info("Installation step took %.2f seconds", time.perf_counter() - t0)

    def _install_from_script(self, script_path: Path) -> None:
        """Install from shell script."""
        if not script_path.is_file():
            raise FileNotFoundError(f"Script not found at {script_path}")

        shell_commands = script_path.read_text().splitlines(keepends=True)
        for i, cmd in enumerate(shell_commands):
            self.communicate(
                cmd,
                error_msg=f"Failed to execute line {i}.",
                timeout_duration=LONG_TIMEOUT,
            )

    def _create_conda_environment(self, env_name: str, install_configs: Dict, record: Dict) -> None:
        """Create conda environment based on configuration."""
        self.logger.info(f"{env_name} conda env not found, creating...")
        packages = install_configs.get("packages", "")

        if packages == "requirements.txt":
            self._create_from_requirements(env_name, install_configs, record)
        elif packages == "environment.yml":
            self._create_from_environment_yml(env_name, install_configs, record)
        else:
            self._create_from_packages(env_name, install_configs, packages)

    def _create_from_requirements(self, env_name: str, install_configs: Dict, record: Dict) -> None:
        """Create environment from requirements.txt."""
        self.communicate(
            f"conda create -n {env_name} python={install_configs['python']} -y",
            error_msg="Failed to create conda environment",
            timeout_duration=LONG_TIMEOUT,
        )
        self.logger.debug("Created conda environment")

        content_reqs = get_requirements(record)
        copy_file_to_container(self.container_obj, content_reqs, PATH_TO_REQS)

        self.communicate(f"conda activate {env_name}", error_msg="Failed to activate conda environment")
        self.communicate(
            f"pip install -r {PATH_TO_REQS}",
            error_msg="Failed to install requirements.txt",
            timeout_duration=LONG_TIMEOUT,
        )
        self.logger.debug("Installed requirements from requirements.txt")
        self.communicate(f"rm {PATH_TO_REQS}")

    def _create_from_environment_yml(self, env_name: str, install_configs: Dict, record: Dict) -> None:
        """Create environment from environment.yml."""
        content_env_yml = get_environment_yml(record, env_name)
        if not install_configs.get("no_use_env"):
            content_env_yml += f'\n  - python={install_configs["python"]}\n'

        copy_file_to_container(self.container_obj, content_env_yml, PATH_TO_ENV_YML)

        if install_configs.get("no_use_env"):
            self.communicate(
                f"conda create -c conda-forge -n {env_name} python={install_configs['python']} -y",
                error_msg="Failed to create conda environment",
                timeout_duration=LONG_TIMEOUT,
            )
            self.logger.debug("Created conda environment")
            self.communicate(
                f"conda env update -f {PATH_TO_ENV_YML}",
                error_msg="Failed to install environment.yml",
                timeout_duration=LONG_TIMEOUT,
            )
            self.logger.debug("Installed packages from environment.yml")
        else:
            self.communicate(
                f"conda env create --file {PATH_TO_ENV_YML}",
                error_msg="Failed to create conda environment with environment.yml",
                timeout_duration=LONG_TIMEOUT,
            )
            self.logger.debug("Created conda environment with environment.yml")

        self.communicate(f"rm {PATH_TO_ENV_YML}")

    def _create_from_packages(self, env_name: str, install_configs: Dict, packages: str) -> None:
        """Create environment from package list."""
        python_env = f"python{install_configs['python']}"
        if self.conda_environment_exists(python_env):
            self.communicate(
                f"conda create --name {env_name} --clone {python_env}",
                error_msg="Failed to clone conda environment",
                timeout_duration=LONG_TIMEOUT,
            )
            self.logger.debug("Cloned python conda environment")
        else:
            self.logger.debug(f"Could not find {python_env}, creating new environment")
            self.communicate(
                f"conda create -n {env_name} python={install_configs['python']} -y",
                error_msg="Failed to create conda environment",
                timeout_duration=LONG_TIMEOUT,
            )

        self.communicate(f"conda activate {env_name}", error_msg="Failed to activate conda environment")

        if packages.strip():
            self.communicate(
                f"conda install {packages} -y",
                error_msg="Failed to install packages",
                timeout_duration=LONG_TIMEOUT,
            )
            self.logger.debug("Installed conda packages")

        # Install extra pip packages
        if install_configs.get("pip_packages"):
            self.communicate(
                f"source activate {env_name} && pip install {' '.join(install_configs['pip_packages'])}",
                error_msg="Failed to install pip packages",
                timeout_duration=LONG_TIMEOUT,
            )
            self.logger.debug("Installed extra pip dependencies")

    def _run_install_commands(self, install_configs: Dict) -> None:
        """Run pre-install, install, and post-install commands."""
        if install_configs.get("pre_install"):
            self.logger.info("Running pre-install commands...")
            for cmd in install_configs["pre_install"]:
                self.communicate(
                    cmd,
                    error_msg="Pre-install commands failed",
                    timeout_duration=LONG_TIMEOUT,
                )
            self.logger.debug("Ran pre-install commands")

        if install_configs.get("install"):
            self.logger.info(f"Installing {self.repo_name} at base commit...")
            self.communicate(
                install_configs["install"],
                error_msg="Install command failed",
                timeout_duration=LONG_TIMEOUT,
            )
            self.logger.debug("Ran install command")

        if install_configs.get("post_install"):
            self.logger.info("Running post-install commands...")
            for cmd in install_configs["post_install"]:
                self.communicate(
                    cmd,
                    error_msg="Post-install commands failed",
                )
            self.logger.debug("Ran post-install commands")
