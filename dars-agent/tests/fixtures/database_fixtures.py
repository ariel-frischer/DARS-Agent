"""Database record fixtures for testing."""
from __future__ import annotations

from typing import Dict, List, Optional
from tests.fixtures.factories import DataFactory


def repository_factory(
    repo_id: Optional[int] = None,
    name: Optional[str] = None,
    owner: Optional[str] = None,
    full_name: Optional[str] = None,
    **kwargs,
) -> Dict:
    """Create a mock repository record."""
    if repo_id is None:
        repo_id = DataFactory.random_int(1, 100000)

    if name is None:
        name = DataFactory.random_string(12, prefix="repo-")

    if owner is None:
        owner = DataFactory.random_string(10, prefix="owner-")

    if full_name is None:
        full_name = f"{owner}/{name}"

    repo = {
        "id": repo_id,
        "name": name,
        "owner": owner,
        "full_name": full_name,
        "description": DataFactory.random_string(100),
        "private": DataFactory.random_bool(),
        "url": f"https://github.com/{full_name}",
        "clone_url": f"https://github.com/{full_name}.git",
        "default_branch": "main",
        "language": DataFactory.random_choice(["Python", "JavaScript", "TypeScript", "Go", "Rust"]),
        "stars": DataFactory.random_int(0, 10000),
        "forks": DataFactory.random_int(0, 1000),
        "open_issues": DataFactory.random_int(0, 500),
        "created_at": DataFactory.random_datetime().isoformat(),
        "updated_at": DataFactory.random_datetime().isoformat(),
    }

    repo.update(kwargs)
    return repo


def code_file_factory(
    file_id: Optional[int] = None,
    path: Optional[str] = None,
    content: Optional[str] = None,
    **kwargs,
) -> Dict:
    """Create a mock code file record."""
    if file_id is None:
        file_id = DataFactory.random_int(1, 10000)

    if path is None:
        filename = DataFactory.random_string(10)
        extension = DataFactory.random_choice([".py", ".js", ".ts", ".java", ".go"])
        path = f"src/{filename}{extension}"

    if content is None:
        # Generate realistic code content
        content = f"""def {DataFactory.random_string(8)}():
    \"\"\"Sample function for testing.\"\"\"
    result = {DataFactory.random_int(1, 100)}
    return result

class {DataFactory.random_string(10).capitalize()}:
    \"\"\"Sample class for testing.\"\"\"

    def __init__(self):
        self.value = {DataFactory.random_int(1, 100)}

    def method(self):
        return self.value
"""

    file_data = {
        "id": file_id,
        "path": path,
        "content": content,
        "size": len(content),
        "lines": len(content.split("\n")),
        "language": path.split(".")[-1],
        "created_at": DataFactory.random_datetime().isoformat(),
        "updated_at": DataFactory.random_datetime().isoformat(),
    }

    file_data.update(kwargs)
    return file_data


def commit_record_factory(
    commit_id: Optional[str] = None,
    message: Optional[str] = None,
    author: Optional[str] = None,
    **kwargs,
) -> Dict:
    """Create a mock commit record."""
    if commit_id is None:
        commit_id = DataFactory.random_string(40)

    if message is None:
        message = DataFactory.random_string(50, prefix="Commit: ")

    if author is None:
        author = DataFactory.random_string(12)

    commit = {
        "id": commit_id,
        "sha": commit_id,
        "message": message,
        "author": author,
        "author_email": DataFactory.random_email(),
        "timestamp": DataFactory.random_datetime().isoformat(),
        "files_changed": DataFactory.random_int(1, 20),
        "insertions": DataFactory.random_int(10, 500),
        "deletions": DataFactory.random_int(5, 200),
    }

    commit.update(kwargs)
    return commit


def swe_env_factory(
    env_id: Optional[str] = None,
    repo: Optional[str] = None,
    **kwargs,
) -> Dict:
    """Create a mock SWE environment record."""
    if env_id is None:
        env_id = DataFactory.random_uuid()

    if repo is None:
        repo = f"{DataFactory.random_string(10)}/{DataFactory.random_string(10)}"

    env = {
        "id": env_id,
        "repo": repo,
        "base_commit": DataFactory.random_string(40),
        "container_id": DataFactory.random_string(64),
        "container_name": DataFactory.random_string(12, prefix="swe_"),
        "status": DataFactory.random_choice(["running", "stopped", "error"]),
        "created_at": DataFactory.random_datetime().isoformat(),
        "updated_at": DataFactory.random_datetime().isoformat(),
    }

    env.update(kwargs)
    return env


def task_record_factory(
    task_id: Optional[str] = None,
    title: Optional[str] = None,
    **kwargs,
) -> Dict:
    """Create a mock task record."""
    if task_id is None:
        task_id = DataFactory.random_uuid()

    if title is None:
        title = DataFactory.random_string(50, prefix="Task: ")

    task = {
        "id": task_id,
        "title": title,
        "description": DataFactory.random_string(200),
        "status": DataFactory.random_choice(["pending", "in_progress", "completed", "failed"]),
        "priority": DataFactory.random_choice(["low", "medium", "high", "critical"]),
        "assigned_to": DataFactory.random_string(10),
        "created_by": DataFactory.random_string(10),
        "created_at": DataFactory.random_datetime().isoformat(),
        "updated_at": DataFactory.random_datetime().isoformat(),
        "due_date": DataFactory.random_datetime().isoformat(),
    }

    task.update(kwargs)
    return task


def trajectory_record_factory(
    trajectory_id: Optional[str] = None,
    instance_id: Optional[str] = None,
    **kwargs,
) -> Dict:
    """Create a mock trajectory record."""
    if trajectory_id is None:
        trajectory_id = DataFactory.random_uuid()

    if instance_id is None:
        instance_id = f"instance_{DataFactory.random_int(1, 9999)}"

    trajectory = {
        "id": trajectory_id,
        "instance_id": instance_id,
        "agent_name": DataFactory.random_string(10, prefix="agent_"),
        "model_name": DataFactory.random_choice(["gpt-4", "gpt-3.5-turbo", "claude-2"]),
        "steps": DataFactory.random_int(5, 50),
        "total_cost": round(DataFactory.random_float(0.01, 5.0), 4),
        "duration_seconds": DataFactory.random_int(30, 3600),
        "status": DataFactory.random_choice(["success", "failure", "timeout"]),
        "created_at": DataFactory.random_datetime().isoformat(),
        "completed_at": DataFactory.random_datetime().isoformat(),
    }

    trajectory.update(kwargs)
    return trajectory


# Predefined database fixtures
MOCK_REPOSITORIES = [
    {
        "id": 1,
        "name": "swe-agent",
        "owner": "princeton-nlp",
        "full_name": "princeton-nlp/swe-agent",
        "description": "An agent for solving software engineering tasks",
        "private": False,
        "url": "https://github.com/princeton-nlp/swe-agent",
        "clone_url": "https://github.com/princeton-nlp/swe-agent.git",
        "default_branch": "main",
        "language": "Python",
        "stars": 1500,
        "forks": 200,
        "open_issues": 45,
        "created_at": "2023-06-01T10:00:00Z",
        "updated_at": "2024-10-17T08:30:00Z",
    },
    {
        "id": 2,
        "name": "test-repo",
        "owner": "testorg",
        "full_name": "testorg/test-repo",
        "description": "A test repository for unit testing",
        "private": True,
        "url": "https://github.com/testorg/test-repo",
        "clone_url": "https://github.com/testorg/test-repo.git",
        "default_branch": "main",
        "language": "Python",
        "stars": 10,
        "forks": 2,
        "open_issues": 3,
        "created_at": "2024-01-15T12:00:00Z",
        "updated_at": "2024-10-15T16:45:00Z",
    },
]

MOCK_CODE_FILES = [
    {
        "id": 1,
        "path": "src/agent/main.py",
        "content": '''"""Main agent module."""
from typing import Dict, List

class Agent:
    """Main agent class."""

    def __init__(self, name: str):
        self.name = name
        self.history = []

    def run(self, task: Dict) -> Dict:
        """Execute a task."""
        return {"status": "success"}
''',
        "size": 250,
        "lines": 15,
        "language": "py",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-10-10T14:30:00Z",
    },
]
