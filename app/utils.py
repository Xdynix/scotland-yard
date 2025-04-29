from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from fastapi import HTTPException, status
from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q
from tortoise.models import Model
from tortoise.queryset import QuerySet

from app import settings

ModelT = TypeVar("ModelT", bound=Model)

P = ParamSpec("P")
R = TypeVar("R")


async def get_object_or_404(
    query: QuerySet[ModelT] | type[ModelT],
    *args: Q,
    **kwargs: Any,
) -> ModelT:
    """
    Retrieve a single object or raise HTTP 404 if not found.

    Parameters:

    - query: either a Tortoise QuerySet or a Model class.
    - *args, **kwargs: filters to pass into QuerySet.get().

    Returns:

    - The model instance if found.

    Raises:

    - HTTPException(status_code=404) if no matching object exists.
    """

    if not isinstance(query, QuerySet):
        query = query.all()
    try:
        return await query.get(*args, **kwargs)
    except DoesNotExist as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from e


def with_tortoise(
    func: Callable[P, Coroutine[Any, Any, R]],
) -> Callable[P, Coroutine[Any, Any, R]]:  # pragma: no cover
    """Wrap an async function with Tortoise ORM setup and teardown.

    Args:
        func: Async function requiring a Tortoise connection.

    Returns:
        Async wrapper that manages Tortoise lifecycle.
    """

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        await Tortoise.init(
            db_url=settings.POSTGRES.url,
            modules={"models": ["app.models"]},
        )
        await Tortoise.generate_schemas()

        try:
            return await func(*args, **kwargs)
        finally:
            await Tortoise.close_connections()

    return wrapper
