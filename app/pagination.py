from typing import Annotated, Any, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field
from tortoise.models import Model
from tortoise.queryset import QuerySet

T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=Model)


class PaginationParam(BaseModel):
    cursor: str | None = Field(None, pattern=r"\d{1,32}")
    limit: int = Field(10, ge=1, le=100)


PaginationQuery = Annotated[PaginationParam, Query()]


class Page(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None


async def paginate(
    query: QuerySet[ModelT],
    cursor: str | None = None,
    limit: int = 10,
    pk_field: str = "id",
) -> Any:
    query = query.order_by(f"-{pk_field}")
    if cursor is not None:
        query = query.filter(**{f"{pk_field}__lte": cursor})

    items = await query.limit(limit + 1)

    next_cursor: str | None
    if len(items) > limit:
        next_cursor = str(getattr(items[-1], pk_field))
        items = items[:limit]
    else:
        next_cursor = None

    return {"items": items, "next_cursor": next_cursor}
