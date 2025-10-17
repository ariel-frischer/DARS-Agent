"""Agent-related fixtures for testing."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from tests.fixtures.factories import DataFactory


def agent_arguments_factory(
    model_name: str = "gpt-4",
    config_file: Optional[str] = None,
    **kwargs,
) -> Dict:
    """Create mock agent arguments."""
    args = {
        "model": {
            "model_name": model_name,
            "per_instance_cost_limit": 2.0,
            "total_cost_limit": 10.0,
            "temperature": 0.0,
            "top_p": 0.95,
        },
        "config": {
            "command_docs": "Commands documentation",
            "env_variables": {
                "WINDOW": 100,
                "OVERLAP": 2,
                "CURRENT_LINE": 0,
                "CURRENT_FILE": "",
                "SEARCH_RESULTS": [],
                "SEARCH_FILES": [],
                "SEARCH_INDEX": 0,
            },
            "_commands": ["submit", "search", "edit", "create", "append"],
            "subroutine_types": ["edit", "search"],
        },
    }

    if config_file:
        args["config_file"] = config_file

    args.update(kwargs)
    return args


def trajectory_step_factory(
    action: Optional[str] = None,
    observation: Optional[str] = None,
    thought: Optional[str] = None,
    **kwargs,
) -> Dict:
    """Create a mock trajectory step."""
    if action is None:
        actions = [
            "search_dir test",
            "open main.py",
            "edit 10:20",
            "submit",
            "create new_file.py",
        ]
        action = DataFactory.random_choice(actions)

    if observation is None:
        observations = [
            "File opened successfully",
            "Search found 5 results",
            "Edit completed",
            "File created",
            "Command executed",
        ]
        observation = DataFactory.random_choice(observations)

    if thought is None:
        thought = DataFactory.random_string(50, prefix="I need to ")

    step = {
        "action": action,
        "observation": observation,
        "thought": thought,
        "step_number": DataFactory.random_int(1, 100),
        "timestamp": DataFactory.random_datetime().isoformat(),
    }

    step.update(kwargs)
    return step


def api_stats_factory(
    total_cost: Optional[float] = None,
    instance_cost: Optional[float] = None,
    tokens_sent: Optional[int] = None,
    tokens_received: Optional[int] = None,
    **kwargs,
) -> Dict:
    """Create mock API statistics."""
    if total_cost is None:
        total_cost = DataFactory.random_float(0.01, 5.0)

    if instance_cost is None:
        instance_cost = DataFactory.random_float(0.01, 2.0)

    if tokens_sent is None:
        tokens_sent = DataFactory.random_int(100, 10000)

    if tokens_received is None:
        tokens_received = DataFactory.random_int(50, 5000)

    stats = {
        "total_cost": round(total_cost, 4),
        "instance_cost": round(instance_cost, 4),
        "tokens_sent": tokens_sent,
        "tokens_received": tokens_received,
        "api_calls": DataFactory.random_int(1, 50),
    }

    stats.update(kwargs)
    return stats


def agent_factory(
    name: Optional[str] = None,
    model_name: str = "gpt-4",
    **kwargs,
) -> Dict:
    """Create a mock agent."""
    if name is None:
        name = DataFactory.random_string(8, prefix="agent_")

    agent = {
        "name": name,
        "model": model_name,
        "history": [],
        "codegraph_history": [],
        "last_container_id": None,
        "stats": api_stats_factory(),
    }

    agent.update(kwargs)
    return agent


def model_response_factory(
    content: Optional[str] = None,
    role: str = "assistant",
    **kwargs,
) -> Dict:
    """Create a mock model response."""
    if content is None:
        content = DataFactory.random_string(100)

    response = {
        "role": role,
        "content": content,
        "finish_reason": "stop",
        "model": "gpt-4",
        "usage": {
            "prompt_tokens": DataFactory.random_int(100, 1000),
            "completion_tokens": DataFactory.random_int(50, 500),
            "total_tokens": DataFactory.random_int(150, 1500),
        },
    }

    response.update(kwargs)
    return response


def command_output_factory(
    command: Optional[str] = None,
    output: Optional[str] = None,
    exit_code: int = 0,
    **kwargs,
) -> Dict:
    """Create mock command output."""
    if command is None:
        command = DataFactory.random_choice([
            "ls -la",
            "git status",
            "python test.py",
            "grep -r 'pattern'",
            "cat file.txt",
        ])

    if output is None:
        output = DataFactory.random_string(200)

    result = {
        "command": command,
        "output": output,
        "exit_code": exit_code,
        "timestamp": DataFactory.random_datetime().isoformat(),
    }

    result.update(kwargs)
    return result


# Predefined agent fixtures
MOCK_AGENT_TRAJECTORIES = [
    {
        "trajectory_id": "traj_001",
        "steps": [
            {
                "action": "search_dir test",
                "observation": "Found 3 files: test_main.py, test_utils.py, test_models.py",
                "thought": "I need to find the test files to understand the codebase",
                "step_number": 1,
            },
            {
                "action": "open test_main.py",
                "observation": "File opened with 150 lines",
                "thought": "Let me examine the main test file",
                "step_number": 2,
            },
            {
                "action": "edit 45:50",
                "observation": "Edit completed successfully",
                "thought": "Fixing the failing test case",
                "step_number": 3,
            },
            {
                "action": "submit",
                "observation": "Changes submitted",
                "thought": "The fix is complete",
                "step_number": 4,
            },
        ],
    },
]
