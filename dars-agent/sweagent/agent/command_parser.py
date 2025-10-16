"""Command parsing abstraction - Single Responsibility Principle."""
from __future__ import annotations
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ParsedAction:
    """Data class for parsed action results."""
    agent: str
    action: str
    cmd_name: Optional[str] = None
    args: Optional[str] = None


class ICommandParser(ABC):
    """Abstract interface for command parsing - Dependency Inversion Principle."""

    @abstractmethod
    def parse_command_patterns(self, config: Any) -> None:
        """Parse and store command patterns from configuration."""
        pass

    @abstractmethod
    def get_first_match(self, action: str, pattern_type: str) -> Optional[re.Match]:
        """Get first matching pattern in action string."""
        pass

    @abstractmethod
    def guard_multiline_input(self, action: str) -> str:
        """Add heredoc guards to multiline commands."""
        pass

    @abstractmethod
    def split_actions(self, action: str, pattern_type: str = "subroutine") -> List[ParsedAction]:
        """Split action string into list of parsed actions."""
        pass


class RegexCommandParser(ICommandParser):
    """Regex-based implementation of command parsing."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.command_patterns: Dict[str, re.Pattern] = {}
        self.subroutine_patterns: Dict[str, re.Pattern] = {}
        self.config = None

    def parse_command_patterns(self, config: Any) -> None:
        """Parse and compile regex patterns from configuration."""
        self.config = config
        self.command_patterns.clear()
        self.subroutine_patterns.clear()

        # Parse command patterns
        for command in config._commands:
            if command.end_name is not None:
                pat = re.compile(
                    rf"^\s*({command.name})\s*(.*?)^({command.end_name})\s*$",
                    re.DOTALL | re.MULTILINE,
                )
            else:
                pat = re.compile(rf"^\s*({command.name})\s*(.*?)$", re.MULTILINE)
            self.command_patterns[command.name] = pat

        # Parse subroutine patterns
        for _, subroutine in config._subroutines.items():
            if subroutine.end_name is None:
                pat = re.compile(rf"^\s*({subroutine.name})\s*(.*?)$", re.MULTILINE)
            else:
                pat = re.compile(
                    rf"^\s*({subroutine.name})\s*(.*?)^({subroutine.end_name})\s*$",
                    re.DOTALL | re.MULTILINE,
                )
            self.subroutine_patterns[subroutine.name] = pat

        # Parse submit command pattern
        if hasattr(config, "submit_command_end_name"):
            submit_pat = re.compile(
                rf"^\s*({config.submit_command})\s*(.*?)^({config.submit_command_end_name})\s*$",
                re.DOTALL | re.MULTILINE,
            )
        else:
            submit_pat = re.compile(rf"^\s*({config.submit_command})(\s*)$", re.MULTILINE)

        self.subroutine_patterns[config.submit_command] = submit_pat
        self.command_patterns[config.submit_command] = submit_pat

    def get_first_match(self, action: str, pattern_type: str) -> Optional[re.Match]:
        """Return the first match of a command pattern in the action string."""
        if pattern_type == "subroutine":
            patterns = {k: v for k, v in self.subroutine_patterns.items()}
        elif pattern_type == "multi_line":
            patterns = {
                k: v for k, v in self.command_patterns.items()
                if k in self.config.multi_line_command_endings or k == self.config.submit_command
            }
            patterns.update({
                k: v for k, v in self.subroutine_patterns.items()
                if k in self.config.multi_line_command_endings
            })
        elif pattern_type == "multi_line_no_subroutines":
            patterns = {
                k: v for k, v in self.command_patterns.items()
                if k in self.config.multi_line_command_endings
            }
        else:
            raise ValueError(f"Unknown pattern type: {pattern_type}")

        matches = []
        for _, pat in patterns.items():
            match = pat.search(action)
            if match:
                matches.append(match)

        if not matches:
            return None

        return sorted(matches, key=lambda x: x.start())[0]

    def guard_multiline_input(self, action: str) -> str:
        """Add heredoc guards to multiline commands."""
        parsed_action = []
        rem_action = action

        while rem_action.strip():
            first_match = self.get_first_match(rem_action, "multi_line_no_subroutines")
            if first_match:
                pre_action = rem_action[: first_match.start()]
                match_action = rem_action[first_match.start() : first_match.end()]
                rem_action = rem_action[first_match.end() :]

                if pre_action.strip():
                    parsed_action.append(pre_action)

                if match_action.strip():
                    eof = first_match.group(3).strip()
                    if not match_action.split("\n")[0].strip().endswith(f"<< '{eof}'"):
                        guarded_command = match_action[first_match.start() :]
                        first_line = guarded_command.split("\n")[0]
                        guarded_command = guarded_command.replace(first_line, first_line + f" << '{eof}'", 1)
                        parsed_action.append(guarded_command)
                    else:
                        parsed_action.append(match_action)
            else:
                parsed_action.append(rem_action)
                rem_action = ""

        return "\n".join(parsed_action)

    def split_actions(self, action: str, pattern_type: str = "subroutine") -> List[ParsedAction]:
        """Split an action into a list of parsed actions."""
        parsed_actions = []
        rem_action = action

        while rem_action.strip():
            first_match = self.get_first_match(rem_action, pattern_type)
            if first_match:
                pre_action = rem_action[: first_match.start()]
                match_action = rem_action[first_match.start() : first_match.end()]
                rem_action = rem_action[first_match.end() :]

                if pre_action.strip():
                    parsed_actions.append(ParsedAction(
                        agent=self.agent_name,
                        action=pre_action,
                        cmd_name=None
                    ))

                if match_action.strip():
                    if match_action.split()[0] == self.config.submit_command:
                        parsed_actions.append(ParsedAction(
                            agent=self.agent_name,
                            action=match_action,
                            cmd_name=first_match.group(1)
                        ))
                    else:
                        parsed_actions.append(ParsedAction(
                            agent=first_match.group(1),
                            action=match_action,
                            cmd_name=first_match.group(1),
                            args=first_match.group(2)
                        ))
            else:
                parsed_actions.append(ParsedAction(
                    agent=self.agent_name,
                    action=rem_action,
                    cmd_name=None
                ))
                rem_action = ""

        # Convert ParsedAction objects to dicts for backward compatibility
        return [
            {
                "agent": pa.agent,
                "action": pa.action,
                "cmd_name": pa.cmd_name,
                **({"args": pa.args} if pa.args is not None else {})
            }
            for pa in parsed_actions
        ]
