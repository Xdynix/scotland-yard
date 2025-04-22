from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from ..models import Organization as OrganizationDB
from ..pagination import Page, PaginationQuery, paginate

router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
)


class Organization(BaseModel):
    id: int
    create_time: datetime
    update_time: datetime
    name: str


@router.get("/", response_model=Page[Organization])
async def list_organizations(page_query: PaginationQuery) -> Any:
    query = OrganizationDB.all()
    return await paginate(query, cursor=page_query.cursor, limit=page_query.limit)
