"""
Action parsing and validation following Single Responsibility Principle.

This module handles only action parsing, validation, and transformation.
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from sweagent.agent.interfaces import IActionParser


class ActionParser(IActionParser):
    """
    Parses and validates agent actions.

    Single Responsibility: Only handles action parsing logic.
    """

    def __init__(self, config, logger):
        """
        Initialize action parser.

        Args:
            config: Agent configuration with commands and patterns
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self._command_patterns: Dict[str, re.Pattern] = {}
        self._subroutine_patterns: Dict[str, re.Pattern] = {}
        self._initialize_patterns()

    def _initialize_patterns(self) -> None:
        """Initialize regex patterns for commands and subroutines."""
        # Build command patterns
        for command in self.config._commands:
            if command.end_name is not None:
                pat = re.compile(
                    rf"^\s*({command.name})\s*(.*?)^({command.end_name})\s*$",
                    re.DOTALL | re.MULTILINE,
                )
            else:
                pat = re.compile(rf"^\s*({command.name})\s*(.*?)$", re.MULTILINE)
            self._command_patterns[command.name] = pat

        # Build subroutine patterns
        for _, subroutine in self.config._subroutines.items():
            if subroutine.end_name is None:
                pat = re.compile(rf"^\s*({subroutine.name})\s*(.*?)$", re.MULTILINE)
            else:
                pat = re.compile(
                    rf"^\s*({subroutine.name})\s*(.*?)^({subroutine.end_name})\s*$",
                    re.DOTALL | re.MULTILINE,
                )
            self._subroutine_patterns[subroutine.name] = pat

        # Build submit pattern
        if hasattr(self.config, "submit_command_end_name"):
            submit_pat = re.compile(
                rf"^\s*({self.config.submit_command})\s*(.*?)^({self.config.submit_command_end_name})\s*$",
                re.DOTALL | re.MULTILINE,
            )
        else:
            submit_pat = re.compile(
                rf"^\s*({self.config.submit_command})(\s*)$",
                re.MULTILINE
            )

        self._subroutine_patterns[self.config.submit_command] = submit_pat
        self._command_patterns[self.config.submit_command] = submit_pat

    def parse(self, action: str, pattern_type: str = "subroutine") -> List[Dict[str, Any]]:
        """
        Parse action string into executable components.

        Args:
            action: Action string to parse
            pattern_type: Type of patterns to use ('subroutine' or other)

        Returns:
            List of parsed action dictionaries
        """
        parsed_actions = []
        remaining = action

        while remaining.strip():
            first_match = self._get_first_match(remaining, pattern_type)

            if first_match:
                pre_action = remaining[:first_match.start()]
                match_action = remaining[first_match.start():first_match.end()]
                remaining = remaining[first_match.end():]

                if pre_action.strip():
                    parsed_actions.append({
                        "agent": self.config.name if hasattr(self.config, 'name') else "unknown",
                        "action": pre_action,
                        "cmd_name": None
                    })

                if match_action.strip():
                    if match_action.split()[0] == self.config.submit_command:
                        parsed_actions.append({
                            "agent": self.config.name if hasattr(self.config, 'name') else "unknown",
                            "action": match_action,
                            "cmd_name": first_match.group(1),
                        })
                    else:
                        parsed_actions.append({
                            "agent": first_match.group(1),
                            "args": first_match.group(2),
                            "action": match_action,
                            "cmd_name": first_match.group(1),
                        })
            else:
                parsed_actions.append({
                    "agent": self.config.name if hasattr(self.config, 'name') else "unknown",
                    "action": remaining,
                    "cmd_name": None
                })
                remaining = ""

        return parsed_actions

    def _get_first_match(self, action: str, pattern_type: str) -> Optional[re.Match]:
        """
        Find first pattern match in action string.

        Args:
            action: Action string
            pattern_type: Type of patterns to search

        Returns:
            First regex match or None
        """
        if pattern_type == "subroutine":
            patterns = self._subroutine_patterns
        elif pattern_type == "multi_line":
            patterns = {
                k: v for k, v in self._command_patterns.items()
                if k in self.config.multi_line_command_endings or k == self.config.submit_command
            }
            patterns.update({
                k: v for k, v in self._subroutine_patterns.items()
                if k in self.config.multi_line_command_endings
            })
        elif pattern_type == "multi_line_no_subroutines":
            patterns = {
                k: v for k, v in self._command_patterns.items()
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

        matches.sort(key=lambda x: x.start())
        return matches[0]

    def validate(self, action: str) -> bool:
        """
        Validate if action is allowed.

        Args:
            action: Action to validate

        Returns:
            True if action is allowed, False otherwise
        """
        names = action.strip().split()
        if len(names) == 0:
            return True

        name = names[0]

        # Check blocklist
        if name in self.config.blocklist:
            self.logger.warning(f"Action '{name}' is in blocklist")
            return False

        # Check standalone blocklist
        if name in self.config.blocklist_standalone and name == action.strip():
            self.logger.warning(f"Standalone action '{name}' is not allowed")
            return False

        return True

    def guard_multiline(self, action: str) -> str:
        """
        Guard multiline inputs with heredoc syntax.

        Args:
            action: Action string to guard

        Returns:
            Guarded action string
        """
        parsed_actions = []
        remaining = action

        while remaining.strip():
            first_match = self._get_first_match(remaining, "multi_line_no_subroutines")

            if first_match:
                pre_action = remaining[:first_match.start()]
                match_action = remaining[first_match.start():first_match.end()]
                remaining = remaining[first_match.end():]

                if pre_action.strip():
                    parsed_actions.append(pre_action)

                if match_action.strip():
                    eof = first_match.group(3).strip()
                    if not match_action.split("\n")[0].strip().endswith(f"<< '{eof}'"):
                        guarded_command = match_action
                        first_line = guarded_command.split("\n")[0]
                        guarded_command = guarded_command.replace(
                            first_line,
                            first_line + f" << '{eof}'",
                            1
                        )
                        parsed_actions.append(guarded_command)
                    else:
                        parsed_actions.append(match_action)
            else:
                parsed_actions.append(remaining)
                remaining = ""

        return "\n".join(parsed_actions)


class ActionValidator:
    """
    Validates actions against blocklists and policies.

    Separate from parser following SRP.
    """

    def __init__(self, blocklist: tuple, blocklist_standalone: tuple, logger):
        """
        Initialize validator.

        Args:
            blocklist: Tuple of blocked command names
            blocklist_standalone: Tuple of commands blocked when standalone
            logger: Logger instance
        """
        self.blocklist = blocklist
        self.blocklist_standalone = blocklist_standalone
        self.logger = logger

    def is_blocked(self, action: str) -> bool:
        """
        Check if action is blocked.

        Args:
            action: Action to check

        Returns:
            True if action is blocked
        """
        names = action.strip().split()
        if len(names) == 0:
            return False

        name = names[0]

        if name in self.blocklist:
            self.logger.warning(f"Blocked command: {name}")
            return True

        if name in self.blocklist_standalone and name == action.strip():
            self.logger.warning(f"Blocked standalone command: {name}")
            return True

        return False

    def get_blocklist_error(self, action: str, error_template: str) -> str:
        """
        Get blocklist error message.

        Args:
            action: Blocked action
            error_template: Error message template

        Returns:
            Formatted error message
        """
        name = action.strip().split()[0]
        return error_template.format(name=name)
