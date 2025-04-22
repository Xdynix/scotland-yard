from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from . import settings
from .routers import organizations

app = FastAPI()

app.include_router(organizations.router)

register_tortoise(
    app,
    config=settings.TORTOISE_ORM,
    generate_schemas=True,
)
