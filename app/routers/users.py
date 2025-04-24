from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

from ..auth import OAuthRequestSource
from ..models import User as UserDB
from ..pagination import Page, PaginationQuery, paginate
from ..types import Id
from ..utils import get_object_or_404

router = APIRouter(
    prefix="/users",
    tags=["users"],
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


@router.get("/", response_model=Page[User])
async def list_users(rs: OAuthRequestSource, page_query: PaginationQuery) -> Any:
    query = UserDB.filter(organization_id=rs.organization_id)
    return await paginate(query, cursor=page_query.cursor, limit=page_query.limit)


@router.get("/{user_id}", response_model=User)
async def get_user(rs: OAuthRequestSource, user_id: Id) -> Any:
    query = UserDB.filter(organization_id=rs.organization_id)
    return await get_object_or_404(query, id=user_id)
