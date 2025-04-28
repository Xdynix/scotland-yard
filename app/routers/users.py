"""
Endpoints for listing and retrieving users within an organization.
"""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Path
from pydantic import BaseModel, EmailStr

from ..auth import OAuthRequestSource
from ..models import User as UserDB
from ..pagination import Page, PaginationQuery, paginate
from ..types import Id
from ..utils import get_object_or_404

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


class User(BaseModel):
    id: int
    create_time: datetime
    update_time: datetime
    organization_id: int
    username: str
    email: EmailStr
    active: bool
    role: UserDB.Role
    first_name: str
    last_name: str


@router.get(
    "/",
    summary="List Users",
    description="Retrieve a paginated list of users in your organization.",
    response_model=Page[User],
)
async def list_users(rs: OAuthRequestSource, page_query: PaginationQuery) -> Any:
    query = UserDB.filter(organization_id=rs.organization_id)
    return await paginate(query, cursor=page_query.cursor, limit=page_query.limit)


@router.get(
    "/{user_id}",
    summary="Get a User",
    description="Retrieve details of a single user by ID within your organization.",
    response_model=User,
)
async def get_user(
    rs: OAuthRequestSource,
    user_id: Annotated[
        Id,
        Path(description="ID of the user to retrieve."),
    ],
) -> Any:
    query = UserDB.filter(organization_id=rs.organization_id)
    return await get_object_or_404(query, id=user_id)
