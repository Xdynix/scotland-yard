from typing import Any, TypeVar

from fastapi import HTTPException, status
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q
from tortoise.models import Model
from tortoise.queryset import QuerySet

ModelT = TypeVar("ModelT", bound=Model)


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
