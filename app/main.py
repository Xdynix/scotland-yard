from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from . import settings

app = FastAPI()

register_tortoise(
    app,
    config=settings.TORTOISE_ORM,
    generate_schemas=True,
)


@app.get("/")
async def hello_world() -> dict[str, str]:
    return {"message": "Hello World!"}
