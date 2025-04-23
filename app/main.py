from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from tortoise.contrib.fastapi import register_tortoise

from . import auth, settings
from .routers import organizations

app = FastAPI()

app.include_router(auth.router)
app.include_router(organizations.router)

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
