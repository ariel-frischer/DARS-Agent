"""User account fixtures for testing."""
from __future__ import annotations

from typing import Dict, Optional
from tests.fixtures.factories import DataFactory, user_id_sequence


def user_factory(
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    is_active: bool = True,
    is_admin: bool = False,
    **kwargs,
) -> Dict:
    """Create a mock user account."""
    if user_id is None:
        user_id = user_id_sequence.next()

    if username is None:
        username = DataFactory.random_string(8, prefix="user_").lower()

    if email is None:
        email = DataFactory.random_email()

    if full_name is None:
        first_name = DataFactory.random_choice([
            "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"
        ])
        last_name = DataFactory.random_choice([
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller"
        ])
        full_name = f"{first_name} {last_name}"

    user_data = {
        "id": user_id,
        "username": username,
        "email": email,
        "full_name": full_name,
        "is_active": is_active,
        "is_admin": is_admin,
        "created_at": DataFactory.random_datetime().isoformat(),
        "updated_at": DataFactory.random_datetime().isoformat(),
    }

    user_data.update(kwargs)
    return user_data


def admin_user_factory(**kwargs) -> Dict:
    """Create a mock admin user."""
    return user_factory(is_admin=True, **kwargs)


def inactive_user_factory(**kwargs) -> Dict:
    """Create a mock inactive user."""
    return user_factory(is_active=False, **kwargs)


def api_token_factory(
    user_id: Optional[int] = None,
    token: Optional[str] = None,
    name: Optional[str] = None,
    scopes: Optional[list] = None,
    **kwargs,
) -> Dict:
    """Create a mock API token."""
    if user_id is None:
        user_id = user_id_sequence.next()

    if token is None:
        token = f"token_{DataFactory.random_string(32)}"

    if name is None:
        name = DataFactory.random_string(10, prefix="token_")

    if scopes is None:
        scopes = ["read", "write"]

    token_data = {
        "id": DataFactory.random_int(1, 10000),
        "user_id": user_id,
        "token": token,
        "name": name,
        "scopes": scopes,
        "created_at": DataFactory.random_datetime().isoformat(),
        "last_used": DataFactory.random_datetime().isoformat(),
        "expires_at": None,
    }

    token_data.update(kwargs)
    return token_data


# Predefined user fixtures
MOCK_USERS = [
    {
        "id": 1,
        "username": "alice_dev",
        "email": "alice@example.com",
        "full_name": "Alice Developer",
        "is_active": True,
        "is_admin": False,
        "created_at": "2024-01-15T10:00:00",
        "updated_at": "2024-10-15T14:30:00",
    },
    {
        "id": 2,
        "username": "bob_admin",
        "email": "bob@example.com",
        "full_name": "Bob Administrator",
        "is_active": True,
        "is_admin": True,
        "created_at": "2023-06-01T08:00:00",
        "updated_at": "2024-10-16T09:15:00",
    },
    {
        "id": 3,
        "username": "charlie_tester",
        "email": "charlie@example.com",
        "full_name": "Charlie Tester",
        "is_active": True,
        "is_admin": False,
        "created_at": "2024-03-10T12:30:00",
        "updated_at": "2024-10-14T16:45:00",
    },
    {
        "id": 4,
        "username": "diana_inactive",
        "email": "diana@example.com",
        "full_name": "Diana Inactive",
        "is_active": False,
        "is_admin": False,
        "created_at": "2023-11-20T14:00:00",
        "updated_at": "2024-05-01T10:00:00",
    },
]


def get_mock_user_by_id(user_id: int) -> Optional[Dict]:
    """Get a predefined mock user by ID."""
    for user in MOCK_USERS:
        if user["id"] == user_id:
            return user.copy()
    return None


def get_mock_user_by_username(username: str) -> Optional[Dict]:
    """Get a predefined mock user by username."""
    for user in MOCK_USERS:
        if user["username"] == username:
            return user.copy()
    return None
