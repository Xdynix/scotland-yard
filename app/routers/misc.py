from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter(
    prefix="",
    tags=["misc"],
)


@router.get("/")
def ping() -> datetime:
    return datetime.now(tz=UTC)
