"""
Miscellaneous utility endpoints.
"""

from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter(
    prefix="",
    tags=["Misc"],
)


@router.get(
    "/",
    summary="Ping Service",
    description="Health-check endpoint, returns server time in UTC.",
)
def ping() -> datetime:
    return datetime.now(tz=UTC)
