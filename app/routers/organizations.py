"""
Endpoints for listing and retrieving organizations.
"""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Path
from pydantic import BaseModel

from ..models import Organization as OrganizationDB
from ..pagination import Page, PaginationQuery, paginate
from ..types import Id
from ..utils import get_object_or_404

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
)


class Organization(BaseModel):
    id: int
    create_time: datetime
    update_time: datetime
    name: str


@router.get(
    "/",
    summary="List Organizations",
    description="Retrieve a paginated list of all organizations.",
    response_model=Page[Organization],
)
async def list_organizations(page_query: PaginationQuery) -> Any:
    query = OrganizationDB.all()
    return await paginate(query, cursor=page_query.cursor, limit=page_query.limit)


@router.get(
    "/{organization_id}",
    summary="Get an Organization",
    description="Retrieve details of a single organization by its ID.",
    response_model=Organization,
)
async def get_organization(
    organization_id: Annotated[
        Id,
        Path(description="ID of the organization to retrieve."),
    ],
) -> Any:
    return await get_object_or_404(OrganizationDB, id=organization_id)
