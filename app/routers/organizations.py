from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from ..models import Organization as OrganizationDB
from ..pagination import Page, PaginationQuery, paginate
from ..types import Id
from ..utils import get_object_or_404

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


@router.get("/{organization_id}", response_model=Organization)
async def get_organization(organization_id: Id) -> Any:
    return await get_object_or_404(OrganizationDB, id=organization_id)
