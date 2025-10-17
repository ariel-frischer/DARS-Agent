"""Model interaction and query management."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Optional
from sweagent.agent.parsing import FormatError, ParseFunction
from sweagent.utils.log import get_logger


class IModelInteraction(ABC):
    """Interface for model query and response handling."""

    @abstractmethod
    def query_model(self, history: List[Dict[str, str]], temperature: Optional[float] = None) -> str:
        """Query the model with history."""
        pass

    @abstractmethod
    def parse_response(self, output: str) -> Tuple[str, str]:
        """Parse model response into thought and action."""
        pass


class ModelQueryHandler(IModelInteraction):
    """Handles model queries and response parsing."""

    def __init__(self, model, config, logger=None):
        self.model = model
        self.config = config
        self.logger = logger or get_logger("model_query_handler")

    def query_model(self, history: List[Dict[str, str]], temperature: Optional[float] = None) -> str:
        """Query the model with history."""
        return self.model.query(history, temperature=temperature)

    def parse_response(self, output: str) -> Tuple[str, str]:
        """Parse model response into thought and action."""
        thought, action = self.config.parse_function(
            output,
            self.config._commands + self.config.subroutine_types,
            strict=False,
        )
        return thought, action


class RetryHandler:
    """Handles retry logic for format and blocklist errors."""

    def __init__(self, model, config, logger=None):
        self.model = model
        self.config = config
        self.logger = logger or get_logger("retry_handler")

    def retry_after_format_fail(self, output: str, history: List[Dict[str, str]]) -> str:
        """Ask the model to correct after a malformatted output."""
        format_error_template = self.config.format_error_template
        self.logger.warning(f"MALFORMED OUTPUT\n{output}")
        self.logger.warning(f"FORMAT ERROR\n{format_error_template}")

        temp_history = history + [
            {"role": "assistant", "content": output, "agent": "agent"},
            {"role": "user", "content": format_error_template, "agent": "agent"},
        ]
        return self.model.query(temp_history)

    def retry_after_blocklist_fail(
        self, output: str, action: str, history: List[Dict[str, str]]
    ) -> str:
        """Ask the model to correct after a disallowed command."""
        name = action.strip().split()[0]
        blocklist_error_message = self.config.blocklist_error_template.format(name=name)

        self.logger.warning(f"BLOCKLISTED OUTPUT\n{output}")
        self.logger.warning(f"BLOCKLIST ERROR\n{blocklist_error_message}")

        temp_history = history + [
            {"role": "assistant", "content": output, "agent": "agent"},
            {"role": "user", "content": blocklist_error_message, "agent": "agent"},
        ]
        return self.model.query(temp_history)

    def should_block_action(self, action: str) -> bool:
        """Check if the command should be blocked."""
        names = action.strip().split()
        if len(names) == 0:
            return False
        name = names[0]
        if name in self.config.blocklist:
            return True
        if name in self.config.blocklist_standalone and name == action.strip():
            return True
        return False

    def check_format_and_requery(
        self, output: str, history: List[Dict[str, str]], parse_function
    ) -> Tuple[str, str, str]:
        """Parse output and retry if malformatted or blocked."""
        format_fails = blocklist_fails = 0

        while format_fails + blocklist_fails <= 2:
            try:
                thought, action = parse_function(
                    output,
                    self.config._commands + self.config.subroutine_types,
                    strict=False,
                )
            except KeyboardInterrupt:
                raise
            except FormatError:
                format_fails += 1
                output = self.retry_after_format_fail(output, history)
                continue

            if self.should_block_action(action):
                blocklist_fails += 1
                output = self.retry_after_blocklist_fail(output, action, history)
            else:
                return thought, action, output

        self.logger.warning(f"Malformat limit reached: \n{output}")
        return "Exit due to format error", "exit_format", output
