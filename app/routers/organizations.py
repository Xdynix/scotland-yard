from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from ..models import Organization as OrganizationDB

router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
)


class Organization(BaseModel):
    id: int
    create_time: datetime
    update_time: datetime
    name: str


@router.get("/", response_model=list[Organization])
async def list_organizations() -> list[OrganizationDB]:
    return await OrganizationDB.all()
