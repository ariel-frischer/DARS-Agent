"""Factory functions for generating test data."""
from __future__ import annotations

import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4


class DataFactory:
    """Base factory for generating test data."""

    @staticmethod
    def random_string(length: int = 10, prefix: str = "") -> str:
        """Generate a random string."""
        chars = string.ascii_letters + string.digits
        return prefix + "".join(random.choice(chars) for _ in range(length))

    @staticmethod
    def random_email(domain: str = "example.com") -> str:
        """Generate a random email address."""
        username = DataFactory.random_string(8).lower()
        return f"{username}@{domain}"

    @staticmethod
    def random_int(min_val: int = 0, max_val: int = 1000) -> int:
        """Generate a random integer."""
        return random.randint(min_val, max_val)

    @staticmethod
    def random_float(min_val: float = 0.0, max_val: float = 100.0) -> float:
        """Generate a random float."""
        return random.uniform(min_val, max_val)

    @staticmethod
    def random_bool() -> bool:
        """Generate a random boolean."""
        return random.choice([True, False])

    @staticmethod
    def random_datetime(
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> datetime:
        """Generate a random datetime."""
        if start is None:
            start = datetime.now() - timedelta(days=365)
        if end is None:
            end = datetime.now()

        delta = end - start
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return start + timedelta(seconds=random_seconds)

    @staticmethod
    def random_list(factory_func, min_len: int = 1, max_len: int = 5) -> List[Any]:
        """Generate a random list using a factory function."""
        length = random.randint(min_len, max_len)
        return [factory_func() for _ in range(length)]

    @staticmethod
    def random_choice(choices: List[Any]) -> Any:
        """Select a random choice from a list."""
        return random.choice(choices)

    @staticmethod
    def random_uuid() -> str:
        """Generate a random UUID."""
        return str(uuid4())


class SequenceGenerator:
    """Generate sequential values for testing."""

    def __init__(self, start: int = 1):
        self.current = start

    def next(self) -> int:
        """Get next value in sequence."""
        value = self.current
        self.current += 1
        return value

    def reset(self, start: int = 1):
        """Reset sequence to starting value."""
        self.current = start


# Global sequence generators for common use cases
user_id_sequence = SequenceGenerator(start=1)
issue_id_sequence = SequenceGenerator(start=100)
pr_id_sequence = SequenceGenerator(start=1000)
container_id_sequence = SequenceGenerator(start=1)
