"""
Pagination utilities for cursor-based paging of Tortoise ORM QuerySets.
"""

from typing import Annotated, Any, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field
from tortoise.models import Model
from tortoise.queryset import QuerySet

from .types import Id

T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=Model)


class PaginationParam(BaseModel):
    cursor: Id | None = None
    limit: int = Field(10, ge=1, le=100)


PaginationQuery = Annotated[PaginationParam, Query()]


class Page(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: Id | None = None


async def paginate(
    query: QuerySet[ModelT],
    cursor: Id | None = None,
    limit: int = 10,
    pk_field: str = "id",
) -> Any:
    """
    Apply cursor-based pagination to a Tortoise ORM QuerySet.

    - **query**: the QuerySet of ModelT to paginate.
    - **cursor**: return objects with primary key ≤ this value, if provided.
    - **limit**: maximum number of objects to return.

    Returns a dict with:

    - **items**: list of fetched model instances.
    - **next_cursor**: the PK for the next page, or None if no further pages.
    """
    query = query.order_by(f"-{pk_field}")
    if cursor is not None:
        query = query.filter(**{f"{pk_field}__lte": cursor})

    items = await query.limit(limit + 1)

    next_cursor: str | None
    if len(items) > limit:
        next_cursor = getattr(items[-1], pk_field)
        items = items[:limit]
    else:
        next_cursor = None

    return {"items": items, "next_cursor": next_cursor}
