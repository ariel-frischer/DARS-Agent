"""Communication handling for container interactions."""
from __future__ import annotations
import os
import time
import traceback
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from sweagent.environment.utils import (
    PROCESS_DONE_MARKER_START,
    PROCESS_DONE_MARKER_END,
    read_with_timeout,
    read_with_timeout_experimental,
)
from sweagent.utils.log import get_logger
from sweagent.utils.config import keys_config


class ICommunicationHandler(ABC):
    """Interface for container communication."""

    @abstractmethod
    def communicate(self, container: any, input: str, timeout_duration: float) -> Tuple[str, int]:
        """Send input to container and return output with exit code."""
        pass

    @abstractmethod
    def check_syntax(self, container: any, input: str) -> Tuple[str, bool]:
        """Check syntax of command."""
        pass


class BashCommunicationHandler(ICommunicationHandler):
    """Handles bash-based communication with containers."""

    def __init__(self, get_pids_callback=None, logger=None):
        self.get_pids_callback = get_pids_callback
        self.logger = logger or get_logger("comm_handler")
        self.communicate_method = keys_config.get(
            "SWE_AGENT_COMMUNICATE_METHOD", default="end-marker", choices=["end-marker", "processes"]
        )

    def communicate(self, container: any, input: str, timeout_duration: float) -> Tuple[str, int]:
        """Send input to container and return output with exit code."""
        if self.communicate_method == "end-marker":
            return self._communicate_experimental(container, input, timeout_duration)
        return self._communicate_legacy(container, input, timeout_duration)

    def _communicate_experimental(
        self, container: any, input: str, timeout_duration: float
    ) -> Tuple[str, int]:
        """Experimental communication using end markers."""
        command_suffix = (
            f'EXITSTATUS="$?"; sleep 0.01; echo {PROCESS_DONE_MARKER_START}$EXITSTATUS{PROCESS_DONE_MARKER_END}\n'
        )
        try:
            cmd = input if input.endswith("\n") else input + "\n"
            cmd += command_suffix
            os.write(container.stdin.fileno(), cmd.encode())
            time.sleep(0.03)
            container.stdin.flush()
        except BrokenPipeError:
            traceback.print_exc()
            self.logger.error("Failed to communicate with container.")
            raise RuntimeError("Failed to communicate with container")

        try:
            buffer, exit_code = read_with_timeout_experimental(container, timeout_duration)
        except Exception:
            self.logger.error(f"Read with timeout failed on input:\n---\n{input}\n---")
            raise

        if exit_code == "$EXITSTATUS":
            buffer = (
                "Unknown error occurred when running the command. "
                "Please double check syntax and that you're not running an interactive command."
            )
            self.logger.warning("Couldn't get real exit code. Setting it to 999")
            exit_code = "999"
        elif not exit_code.isdigit():
            raise RuntimeError(f"Failed to get exit code. Output:\n---\n{buffer}\n---")

        return buffer, int(exit_code)

    def _communicate_legacy(
        self, container: any, input: str, timeout_duration: float
    ) -> Tuple[str, int]:
        """Legacy communication using process monitoring."""
        try:
            cmd = input if input.endswith("\n") else input + "\n"
            os.write(container.stdin.fileno(), cmd.encode())
            time.sleep(0.1)
            container.stdin.flush()
        except BrokenPipeError:
            traceback.print_exc()
            self.logger.error("Failed to communicate with container.")
            raise RuntimeError("Failed to communicate with container")

        try:
            buffer = read_with_timeout(container, self.get_pids_callback, timeout_duration)
            container.stdin.write("echo $?\n")
            time.sleep(0.1)
            container.stdin.flush()
            exit_code = read_with_timeout(container, self.get_pids_callback, 5).strip()
        except Exception as e:
            self.logger.error(f"Read with timeout failed on input:\n---\n{input}\n---")
            raise e

        if not exit_code.isdigit():
            raise RuntimeError(f"Failed to get exit code. Output:\n---\n{buffer}\n---")

        return buffer, int(exit_code)

    def check_syntax(self, container: any, input: str) -> Tuple[str, bool]:
        """Check syntax of command."""
        output, returncode = self.communicate(
            container, f"/bin/bash -n <<'EOF'\n{input}\nEOF\n", timeout_duration=25
        )
        return output, returncode == 0
