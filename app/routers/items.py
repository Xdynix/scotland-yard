from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from ..auth import OAuthRequestSource
from ..models import Item as ItemDB
from ..models import SharingLink as SharingLinkDB
from ..models import User as UserDB
from ..pagination import Page, PaginationQuery, paginate
from ..types import Id
from ..utils import get_object_or_404

router = APIRouter(
    prefix="",
    tags=["items"],
)


class Item(BaseModel):
    id: int
    create_time: datetime
    update_time: datetime
    owner_id: int
    parent_id: int | None
    name: str
    type: ItemDB.Type
    file_size: int


class SharingLink(BaseModel):
    id: int
    create_time: datetime
    update_time: datetime
    item_id: int
    token: UUID
    permission: SharingLinkDB.Permission
    expire_time: datetime | None


@router.get("/users/{user_id}/items/", response_model=Page[Item])
async def list_user_items(
    rs: OAuthRequestSource,
    user_id: Id,
    page_query: PaginationQuery,
) -> Any:
    users = UserDB.filter(organization_id=rs.organization_id)
    user = await get_object_or_404(users, id=user_id)

    query = user.items.filter(parent=None)
    return await paginate(query, cursor=page_query.cursor, limit=page_query.limit)


@router.get("/folders/{folder_id}/items/", response_model=Page[Item])
async def list_folder_items(
    rs: OAuthRequestSource,
    folder_id: Id,
    page_query: PaginationQuery,
) -> Any:
    folders = ItemDB.filter(
        owner__organization_id=rs.organization_id,
        type=ItemDB.Type.FOLDER,
    )
    folder = await get_object_or_404(folders, id=folder_id)

    query = folder.children.all()
    return await paginate(query, cursor=page_query.cursor, limit=page_query.limit)


@router.get("/items/{item_id}/sharing-links/", response_model=Page[SharingLink])
async def list_item_sharing_links(
    rs: OAuthRequestSource,
    item_id: Id,
    page_query: PaginationQuery,
) -> Any:
    items = ItemDB.filter(owner__organization_id=rs.organization_id)
    item = await get_object_or_404(items, id=item_id)

    query = item.sharing_links.all()
    return await paginate(query, cursor=page_query.cursor, limit=page_query.limit)
