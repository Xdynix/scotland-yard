import random
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from tortoise.contrib.fastapi import register_tortoise

from . import auth, settings
from .routers import items, misc, organizations, users

app = FastAPI()

app.include_router(misc.router)
app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(users.router)
app.include_router(items.router)

if not settings.TESTING:  # pragma: no cover
    register_tortoise(
        app,
        config=settings.TORTOISE_ORM,
        generate_schemas=True,
    )


@app.exception_handler(auth.OAuthException)
async def oauth_exception_handler(
    request: Request,  # noqa: ARG001
    exc: auth.OAuthException,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": exc.error},
    )


@app.middleware("http")
async def random_error(request: Request, call_next: Callable[..., Any]) -> Any:
    """Middleware that simulates random 500 Internal Server Errors.

    With probability settings.RANDOM_ERROR_RATE, this middleware
    will raise an HTTPException with status 500 instead of calling
    the downstream handler.
    """
    if random.random() < settings.RANDOM_ERROR_RATE:  # noqa: S311
        return JSONResponse(
            content="This is a simulated error. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return await call_next(request)
