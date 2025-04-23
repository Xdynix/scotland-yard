import contextlib
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg  # type: ignore[import-untyped]
import pytest_asyncio
from asyncpg import Connection
from httpx import ASGITransport, AsyncClient
from tortoise import Tortoise
from tortoise.transactions import in_transaction

from app import settings
from app.main import app

postgres_settings = settings.POSTGRES


@asynccontextmanager
async def admin_conn() -> AsyncGenerator[Connection]:
    url = postgres_settings.url.split("?")[0]  # Remove config params.
    conn = await asyncpg.connect(url)
    try:
        yield conn
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def init_test_db() -> AsyncGenerator[None]:
    test_database = postgres_settings.test_database

    async with admin_conn() as conn:
        await conn.execute(f'DROP DATABASE IF EXISTS "{test_database}";')
        await conn.execute(f'CREATE DATABASE "{test_database}";')

    yield

    async with admin_conn() as conn:
        await conn.execute(f'DROP DATABASE IF EXISTS "{test_database}";')


@pytest_asyncio.fixture
async def init_tortoise(init_test_db: None) -> AsyncGenerator[None]:  # noqa: ARG001
    await Tortoise.init(
        db_url=postgres_settings.test_url,
        modules={"models": ["app.models"]},
    )
    await Tortoise.generate_schemas()

    yield

    await Tortoise.close_connections()


class Rollback(Exception):
    pass


@pytest_asyncio.fixture
async def db(init_tortoise: None) -> AsyncGenerator[None]:  # noqa: ARG001
    await Tortoise.init(
        db_url=postgres_settings.test_url,
        modules={"models": ["app.models"]},
    )
    await Tortoise.generate_schemas()

    with contextlib.suppress(Rollback):
        async with in_transaction():
            yield
            raise Rollback

    await Tortoise.close_connections()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
