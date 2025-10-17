"""Command parsing functionality extracted from Agent."""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod


class ICommandParser(ABC):
    """Interface for parsing commands and actions."""

    @abstractmethod
    def parse_command_patterns(self, config: Any) -> None:
        """Parse and initialize command patterns from config."""
        pass

    @abstractmethod
    def get_first_match(self, action: str, pattern_type: str) -> re.Match | None:
        """Return the first match of a command pattern in the action string."""
        pass

    @abstractmethod
    def split_actions(self, action: str, agent_name: str, pattern_type: str = "subroutine") -> List[Dict[str, Any]]:
        """Split an action into a list of actions."""
        pass

    @abstractmethod
    def guard_multiline_input(self, action: str) -> str:
        """Guard multiline commands with heredoc syntax."""
        pass


class RegexCommandParser(ICommandParser):
    """Regex-based command parser implementation."""

    def __init__(self):
        self.command_patterns: Dict[str, re.Pattern] = {}
        self.subroutine_patterns: Dict[str, re.Pattern] = {}
        self.config = None

    def parse_command_patterns(self, config: Any) -> None:
        """Parse and initialize command patterns from config."""
        self.config = config
        self.command_patterns = {}

        for command in config._commands:
            if command.end_name is not None:
                pat = re.compile(
                    rf"^\s*({command.name})\s*(.*?)^({command.end_name})\s*$",
                    re.DOTALL | re.MULTILINE,
                )
                self.command_patterns[command.name] = pat
            else:
                pat = re.compile(rf"^\s*({command.name})\s*(.*?)$", re.MULTILINE)
                self.command_patterns[command.name] = pat

        self.subroutine_patterns = {}
        for _, subroutine in config._subroutines.items():
            if subroutine.end_name is None:
                pat = re.compile(rf"^\s*({subroutine.name})\s*(.*?)$", re.MULTILINE)
                self.subroutine_patterns[subroutine.name,] = pat
            else:
                pat = re.compile(
                    rf"^\s*({subroutine.name})\s*(.*?)^({subroutine.end_name})\s*$",
                    re.DOTALL | re.MULTILINE,
                )
                self.subroutine_patterns[subroutine.name] = pat

        if hasattr(config, "submit_command_end_name"):
            submit_pat = re.compile(
                rf"^\s*({config.submit_command})\s*(.*?)^({config.submit_command_end_name})\s*$",
                re.DOTALL | re.MULTILINE,
            )
        else:
            submit_pat = re.compile(rf"^\s*({config.submit_command})(\s*)$", re.MULTILINE)

        self.subroutine_patterns[config.submit_command] = submit_pat
        self.command_patterns[config.submit_command] = submit_pat

    def get_first_match(self, action: str, pattern_type: str) -> re.Match | None:
        """Return the first match of a command pattern in the action string."""
        if pattern_type == "subroutine":
            patterns = {k: v for k, v in self.subroutine_patterns.items()}
        elif pattern_type == "multi_line":
            patterns = {
                k: v
                for k, v in self.command_patterns.items()
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

        if len(matches) == 0:
            return None

        matches = sorted(matches, key=lambda x: x.start())
        return matches[0]

    def guard_multiline_input(self, action: str) -> str:
        """Split action by multiline commands, then append heredoc syntax."""
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
                        guarded_command = guarded_command.replace(
                            first_line, first_line + f" << '{eof}'", 1
                        )
                        parsed_action.append(guarded_command)
                    else:
                        parsed_action.append(match_action)
            else:
                parsed_action.append(rem_action)
                rem_action = ""

        return "\n".join(parsed_action)

    def split_actions(
        self, action: str, agent_name: str, pattern_type: str = "subroutine"
    ) -> List[Dict[str, Any]]:
        """Split an action into a list of actions in a greedy manner."""
        parsed_action = []
        rem_action = action

        while rem_action.strip():
            first_match = self.get_first_match(rem_action, pattern_type)
            if first_match:
                pre_action = rem_action[: first_match.start()]
                match_action = rem_action[first_match.start() : first_match.end()]
                rem_action = rem_action[first_match.end() :]

                if pre_action.strip():
                    parsed_action.append({
                        "agent": agent_name,
                        "action": pre_action,
                        "cmd_name": None
                    })

                if match_action.strip():
                    if match_action.split()[0] == self.config.submit_command:
                        parsed_action.append({
                            "agent": agent_name,
                            "action": match_action,
                            "cmd_name": first_match.group(1),
                        })
                    else:
                        parsed_action.append({
                            "agent": first_match.group(1),
                            "args": first_match.group(2),
                            "action": match_action,
                            "cmd_name": first_match.group(1),
                        })
            else:
                parsed_action.append({
                    "agent": agent_name,
                    "action": rem_action,
                    "cmd_name": None
                })
                rem_action = ""

        return parsed_action
