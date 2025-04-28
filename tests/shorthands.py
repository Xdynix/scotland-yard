from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar, cast

import pytest

T = TypeVar("T")


def uses_db(func: T) -> T:
    """Decorator to mark a test as using the database fixture."""
    decorator = pytest.mark.usefixtures("db")
    return cast(T, decorator(func))


class AnyValue:
    """Helper class for asserting the type of the given value.

    This can be helpful when you're comparing complex objects like `dict`and only care
    about the types of some of the fields.

    >>> assert AnyValue(int) == 42
    >>> assert AnyValue(str) == "foo"
    >>> assert AnyValue(list, tuple) == [1, 2, 3]
    """

    def __init__(self, *types: type[Any]) -> None:
        self.types = types

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.types)

    def __repr__(self) -> str:
        return f"AnyValue({', '.join(t.__name__ for t in self.types)})"


any_bool = AnyValue(bool)
any_number = AnyValue(int, float)
any_str = AnyValue(str)
any_list = AnyValue(list)
any_dict = AnyValue(dict)


@dataclass
class ApproxDatetime:
    """Roughly matches a time or time string.

    >>> ApproxDatetime(datetime(2025, 1, 1)) == datetime(2025, 1, 1, microsecond=50_000)
    True
    >>> ApproxDatetime(datetime(2025, 1, 1)) == "2025-01-01T00:00:00.050000"
    True
    >>> ApproxDatetime() == "non-time string"
    False
    """

    expected: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    tolerance: timedelta = timedelta(milliseconds=100)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            with suppress(ValueError):
                other = datetime.fromisoformat(other)
        if not isinstance(other, datetime):
            return False
        diff = abs(self.expected - other)
        return diff < self.tolerance


def approx_now() -> ApproxDatetime:
    """Shorthand for comparing a time or time string to approximately equal to now."""
    return ApproxDatetime()
