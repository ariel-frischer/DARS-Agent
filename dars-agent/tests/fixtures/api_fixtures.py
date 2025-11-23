"""API response fixtures for testing."""
from __future__ import annotations

from typing import Dict, List, Optional
from tests.fixtures.factories import DataFactory, issue_id_sequence, pr_id_sequence


def github_issue_factory(
    issue_id: Optional[int] = None,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: str = "open",
    **kwargs,
) -> Dict:
    """Create a mock GitHub issue."""
    if issue_id is None:
        issue_id = issue_id_sequence.next()

    if title is None:
        title = DataFactory.random_string(30, prefix="Issue: ")

    if body is None:
        body = DataFactory.random_string(200, prefix="Description: ")

    issue = {
        "id": issue_id,
        "number": issue_id,
        "title": title,
        "body": body,
        "state": state,
        "user": {
            "login": DataFactory.random_string(10),
            "id": DataFactory.random_int(1, 100000),
            "avatar_url": f"https://avatars.githubusercontent.com/u/{DataFactory.random_int(1, 100000)}",
        },
        "labels": [
            {"name": label, "color": DataFactory.random_string(6)}
            for label in DataFactory.random_choice([
                ["bug"],
                ["enhancement"],
                ["bug", "high-priority"],
                ["documentation"],
                ["question"],
            ])
        ],
        "created_at": DataFactory.random_datetime().isoformat(),
        "updated_at": DataFactory.random_datetime().isoformat(),
        "comments": DataFactory.random_int(0, 20),
    }

    issue.update(kwargs)
    return issue


def github_pr_factory(
    pr_id: Optional[int] = None,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: str = "open",
    **kwargs,
) -> Dict:
    """Create a mock GitHub pull request."""
    if pr_id is None:
        pr_id = pr_id_sequence.next()

    if title is None:
        title = DataFactory.random_string(30, prefix="PR: ")

    if body is None:
        body = DataFactory.random_string(200, prefix="Changes: ")

    pr = {
        "id": pr_id,
        "number": pr_id,
        "title": title,
        "body": body,
        "state": state,
        "user": {
            "login": DataFactory.random_string(10),
            "id": DataFactory.random_int(1, 100000),
        },
        "head": {
            "ref": DataFactory.random_string(15, prefix="feature/"),
            "sha": DataFactory.random_string(40),
        },
        "base": {
            "ref": "main",
            "sha": DataFactory.random_string(40),
        },
        "created_at": DataFactory.random_datetime().isoformat(),
        "updated_at": DataFactory.random_datetime().isoformat(),
        "merged_at": None if state == "open" else DataFactory.random_datetime().isoformat(),
        "draft": False,
        "mergeable": True,
        "additions": DataFactory.random_int(10, 500),
        "deletions": DataFactory.random_int(5, 200),
        "changed_files": DataFactory.random_int(1, 20),
    }

    pr.update(kwargs)
    return pr


def github_commit_factory(
    sha: Optional[str] = None,
    message: Optional[str] = None,
    **kwargs,
) -> Dict:
    """Create a mock GitHub commit."""
    if sha is None:
        sha = DataFactory.random_string(40)

    if message is None:
        message = DataFactory.random_string(50, prefix="Commit: ")

    commit = {
        "sha": sha,
        "commit": {
            "message": message,
            "author": {
                "name": DataFactory.random_string(15),
                "email": DataFactory.random_email(),
                "date": DataFactory.random_datetime().isoformat(),
            },
        },
        "author": {
            "login": DataFactory.random_string(10),
            "id": DataFactory.random_int(1, 100000),
        },
        "stats": {
            "additions": DataFactory.random_int(10, 200),
            "deletions": DataFactory.random_int(5, 100),
            "total": DataFactory.random_int(15, 300),
        },
    }

    commit.update(kwargs)
    return commit


def docker_container_factory(
    container_id: Optional[str] = None,
    name: Optional[str] = None,
    image: str = "sweagent/swe-agent:latest",
    status: str = "running",
    **kwargs,
) -> Dict:
    """Create a mock Docker container."""
    if container_id is None:
        container_id = DataFactory.random_string(64)

    if name is None:
        name = DataFactory.random_string(12, prefix="container_")

    container = {
        "Id": container_id,
        "Name": f"/{name}",
        "Image": image,
        "Status": status,
        "State": {
            "Status": status,
            "Running": status == "running",
            "Paused": False,
            "Restarting": False,
            "OOMKilled": False,
            "Dead": False,
            "Pid": DataFactory.random_int(1000, 99999) if status == "running" else 0,
            "ExitCode": 0,
        },
        "Created": DataFactory.random_datetime().isoformat(),
        "Ports": [
            {
                "PrivatePort": 8000,
                "Type": "tcp",
            }
        ],
        "Labels": {},
    }

    container.update(kwargs)
    return container


def swebench_instance_factory(
    instance_id: Optional[str] = None,
    repo: str = "testorg/testrepo",
    **kwargs,
) -> Dict:
    """Create a mock SWE-bench instance."""
    if instance_id is None:
        instance_id = f"{repo.replace('/', '__')}-{DataFactory.random_int(1, 9999)}"

    instance = {
        "instance_id": instance_id,
        "repo": repo,
        "base_commit": DataFactory.random_string(40),
        "problem_statement": DataFactory.random_string(300, prefix="Bug: "),
        "hints_text": "",
        "created_at": DataFactory.random_datetime().isoformat(),
        "version": "1.0",
        "FAIL_TO_PASS": [f"test_case_{i}" for i in range(1, DataFactory.random_int(2, 5))],
        "PASS_TO_PASS": [f"test_case_{i}" for i in range(10, DataFactory.random_int(15, 20))],
        "environment_setup_commit": DataFactory.random_string(40),
    }

    instance.update(kwargs)
    return instance


def api_error_response_factory(
    error_code: int = 500,
    error_message: Optional[str] = None,
    **kwargs,
) -> Dict:
    """Create a mock API error response."""
    if error_message is None:
        error_messages = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            429: "Rate Limit Exceeded",
            500: "Internal Server Error",
            503: "Service Unavailable",
        }
        error_message = error_messages.get(error_code, "Unknown Error")

    response = {
        "error": {
            "code": error_code,
            "message": error_message,
            "details": DataFactory.random_string(100),
        },
        "status": "error",
        "timestamp": DataFactory.random_datetime().isoformat(),
    }

    response.update(kwargs)
    return response


# Predefined API response fixtures
MOCK_GITHUB_ISSUES = [
    {
        "id": 100,
        "number": 100,
        "title": "Fix authentication bug in login flow",
        "body": "Users are experiencing authentication failures when logging in with special characters in passwords.",
        "state": "open",
        "user": {"login": "reporter_user", "id": 12345},
        "labels": [{"name": "bug", "color": "d73a4a"}, {"name": "high-priority", "color": "ff0000"}],
        "created_at": "2024-10-01T10:00:00Z",
        "updated_at": "2024-10-15T14:30:00Z",
        "comments": 5,
    },
    {
        "id": 101,
        "number": 101,
        "title": "Add dark mode support",
        "body": "Feature request to add dark mode to the UI for better user experience.",
        "state": "open",
        "user": {"login": "feature_requester", "id": 67890},
        "labels": [{"name": "enhancement", "color": "a2eeef"}],
        "created_at": "2024-09-20T08:15:00Z",
        "updated_at": "2024-10-10T12:00:00Z",
        "comments": 12,
    },
]

MOCK_GITHUB_PRS = [
    {
        "id": 1000,
        "number": 1000,
        "title": "Fix login authentication bug",
        "body": "This PR fixes the authentication bug reported in issue #100",
        "state": "open",
        "user": {"login": "contributor", "id": 11111},
        "head": {"ref": "feature/fix-auth", "sha": "abc123def456"},
        "base": {"ref": "main", "sha": "def456abc123"},
        "created_at": "2024-10-16T09:00:00Z",
        "updated_at": "2024-10-16T15:30:00Z",
        "merged_at": None,
        "draft": False,
        "mergeable": True,
        "additions": 45,
        "deletions": 12,
        "changed_files": 3,
    },
]
